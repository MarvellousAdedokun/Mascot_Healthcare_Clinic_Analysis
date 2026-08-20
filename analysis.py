"""
Mascot Healthcare Clinic — "Are These Reviews Real?" analysis
Actually with Marvellous — spec work episode

Run this after re-scraping if you want fresh data. Expects a CSV with
columns: name, rating, text, date (same shape as your Playwright scrape).

Outputs:
  - Printed stats for the voiceover/script
  - chart_wordcount.png   (human fingerprint: word count spread)
  - chart_duplicates.png  (near-duplicate check)
  - chart_complaints.png  (the one-complaint reveal, IG-ready square)
"""

import pandas as pd
import re
from difflib import SequenceMatcher
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

CSV_PATH = r"C:\Users\HP\Documents\GitHub\Mascot_Healthcare_Clinic_Analysis\mascot_reviews.csv"

# ---- brand ----
ORANGE = "#E8630A"
BLACK = "#0A0A0A"
WHITE = "#FFFFFF"
GREY = "#999999"

plt.rcParams["font.family"] = "sans-serif"  # swap to DM Sans if you have the .ttf locally


def load():
    df = pd.read_csv(CSV_PATH)
    df["text"] = df["text"].fillna("")
    df["wordcount"] = df["text"].apply(lambda t: len(t.split()))
    return df


# ---------------------------------------------------------------------
# 1. AUTHENTICITY CHECK — near-duplicate / templated review detection
# ---------------------------------------------------------------------
def duplicate_check(df, min_words=4, threshold=0.7):
    """
    Bot/fake-review farms tend to post near-identical text. Real, organic
    reviews vary wildly. We only compare reviews with >= min_words so we're
    not flagging trivial 1-2 word reviews ("Excellent", "Good service") as
    a fraud signal — those are a separate, expected pattern.
    """
    texts = df[(df["text"].str.strip() != "") & (df["wordcount"] >= min_words)]["text"].tolist()

    dupes = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            ratio = SequenceMatcher(None, texts[i], texts[j]).ratio()
            if ratio > threshold:
                dupes.append((ratio, texts[i], texts[j]))

    print(f"\n=== DUPLICATE CHECK (reviews with {min_words}+ words) ===")
    print(f"Reviews compared: {len(texts)}")
    print(f"Near-duplicate pairs found (>{int(threshold*100)}% similar): {len(dupes)}")
    for ratio, a, b in sorted(dupes, reverse=True)[:10]:
        print(f"  {ratio:.2f} | {a[:70]!r} <-> {b[:70]!r}")

    # collect ALL pairwise ratios (not just ones over threshold) so we can chart the full spread
    all_ratios = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            all_ratios.append(SequenceMatcher(None, texts[i], texts[j]).ratio())

    return dupes, len(texts), all_ratios


def duplicates_chart(all_ratios, threshold=0.7, out_path="chart_duplicates.png"):
    """
    Histogram of every pairwise similarity score. Almost everything should
    sit low (different people writing different things). The threshold line
    marks where we'd start calling something suspicious, and the single
    dupe pair should visibly sit alone out past that line.
    """
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=BLACK)
    ax.set_facecolor(BLACK)

    bins = [i / 50 for i in range(0, 51)]
    ax.hist(all_ratios, bins=bins, color=ORANGE, edgecolor=BLACK, linewidth=0.3)

    ax.axvline(threshold, color=WHITE, linestyle="--", linewidth=1.5)
    ax.text(threshold + 0.01, ax.get_ylim()[1] * 0.9, "copy-paste\nzone", color=WHITE,
            fontsize=11, va="top")

    over = sum(1 for r in all_ratios if r > threshold)
    ax.set_title(f"Checking every review against every other review\n"
                 f"({len(all_ratios):,} pairs compared)",
                 color=WHITE, fontsize=17, pad=20, loc="left")
    ax.set_xlabel("How similar two reviews are (0 = nothing alike, 1 = identical)", color=GREY, fontsize=11)
    ax.set_ylabel("Number of review pairs", color=GREY, fontsize=12)
    ax.tick_params(colors=GREY)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#333333")

    ax.text(0.98, 0.75, f"Only {over} pair\nout of {len(all_ratios):,}\ncrossed the line",
            transform=ax.transAxes, ha="right", va="top", color=WHITE, fontsize=13,
            bbox=dict(boxstyle="round", facecolor="#141414", edgecolor=ORANGE))

    plt.tight_layout()
    plt.savefig(out_path, facecolor=BLACK, dpi=200)
    plt.close()
    print(f"\nSaved {out_path}")


# ---------------------------------------------------------------------
# 2. HUMAN FINGERPRINT — word count distribution
#    Bots/farms cluster around a similar length. Real people don't.
# ---------------------------------------------------------------------
def wordcount_chart(df, out_path="chart_wordcount.png"):
    wc = df[df["text"].str.strip() != ""]["wordcount"]

    fig, ax = plt.subplots(figsize=(10, 7), facecolor=BLACK)
    ax.set_facecolor(BLACK)

    bins = list(range(0, int(wc.max()) + 5, 3))
    ax.hist(wc, bins=bins, color=ORANGE, edgecolor=BLACK, linewidth=0.5)

    ax.set_title("How much people actually wrote\n(184 reviews, word count per review)",
                  color=WHITE, fontsize=18, pad=20, loc="left")
    ax.set_xlabel("Words in review", color=GREY, fontsize=12)
    ax.set_ylabel("Number of reviews", color=GREY, fontsize=12)
    ax.tick_params(colors=GREY)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#333333")

    ax.text(0.98, 0.95, f"Range: {int(wc.min())}–{int(wc.max())} words\nStd dev: {wc.std():.1f}",
            transform=ax.transAxes, ha="right", va="top", color=WHITE, fontsize=12,
            bbox=dict(boxstyle="round", facecolor="#141414", edgecolor=ORANGE))

    plt.tight_layout()
    plt.savefig(out_path, facecolor=BLACK, dpi=200)
    plt.close()
    print(f"\nSaved {out_path}")


# ---------------------------------------------------------------------
# 3. SPECIFICITY CHECK — named details vs generic praise
#    Fake reviews are almost always generic ("great service!").
#    Real reviews mention specific conditions, procedures, staff.
# ---------------------------------------------------------------------
SPECIFIC_PATTERNS = re.compile(
    r"\bDr\.?\s+[A-Z][a-z]+|sonologist|adenomyosis|transvaginal|malaria|"
    r"blood test|scan|pregnan\w*|ear wax|prenatal|consultation|"
    r"nurse\s+[A-Z][a-z]+",
    re.IGNORECASE,
)

def specificity_check(df):
    has_text = df[df["text"].str.strip() != ""]
    specific = has_text["text"].apply(lambda t: bool(SPECIFIC_PATTERNS.search(t)))
    generic_only = has_text[~specific]

    print(f"\n=== SPECIFICITY CHECK ===")
    print(f"Reviews with a named condition/procedure/staff member: {specific.sum()} / {len(has_text)}")
    print(f"Reviews that are purely generic praise: {len(generic_only)}")
    print("Sample generic-only reviews (for context, NOT for reproduction on screen):")
    for t in generic_only["text"].head(5):
        print(f"  - {t[:60]}")

    return specific.sum(), len(has_text)


# ---------------------------------------------------------------------
# 4. THE ONE COMPLAINT — negative language scan
# ---------------------------------------------------------------------
NEGATIVE_WORDS = [
    "bad", "poor", "slow", "rude", "wait", "waited", "waiting", "expensive",
    "disappoint", "unprofessional", "terrible", "worst", "never again",
    "complain", "issue", "problem", "delay", "delayed", "long time",
    "not good", "unhappy", "dirty", "unclean",
]

def complaint_scan(df):
    pattern = re.compile("|".join(NEGATIVE_WORDS), re.IGNORECASE)
    hits = df[df["text"].str.contains(pattern, na=False)]
    # manually confirmed: only ONE of these hits is an actual complaint
    # about the clinic ("don't operate 24/7") — the rest are either
    # negations ("no delays") or the patient's medical symptom, not a
    # complaint about the clinic itself. Re-check this list by hand if
    # you re-run on the full 225.
    print(f"\n=== COMPLAINT SCAN ===")
    print(f"Reviews containing negative-leaning words: {len(hits)} / {len(df)}")
    print("Manually verify each — most are false positives (symptoms, negations).")
    for _, r in hits.iterrows():
        print(f"  [{r['rating']}] {r['name']}: {r['text'][:100]}")


def complaint_chart(total_with_text, real_complaints=1, out_path="chart_complaints.png"):
    """
    The payoff graphic. IG-square, big number, minimal — this is the
    'punchline' visual, not an analytical chart. Deliberately simple.
    """
    fig, ax = plt.subplots(figsize=(10, 10), facecolor=BLACK)
    ax.set_facecolor(BLACK)
    ax.axis("off")

    ax.text(0.5, 0.62, str(real_complaints), ha="center", va="center",
            color=ORANGE, fontsize=200, fontweight="bold")
    ax.text(0.5, 0.40, "REAL COMPLAINT", ha="center", va="center",
            color=WHITE, fontsize=30, fontweight="bold")
    ax.text(0.5, 0.34, f"out of {total_with_text} reviews with actual text", ha="center", va="center",
            color=GREY, fontsize=16)
    ax.text(0.5, 0.20, '"They don\'t operate 24/7."', ha="center", va="center",
            color=WHITE, fontsize=18, style="italic")
    ax.text(0.5, 0.15, "— from a 5-star review", ha="center", va="center",
            color=GREY, fontsize=13)

    plt.tight_layout()
    plt.savefig(out_path, facecolor=BLACK, dpi=200)
    plt.close()
    print(f"\nSaved {out_path}")


# ---------------------------------------------------------------------
if __name__ == "__main__":
    df = load()

    print("=== BASIC ===")
    print(df["rating"].value_counts())
    print(f"Reviews with written text: {(df['text'].str.strip() != '').sum()} / {len(df)}")

    dupes, n_compared, all_ratios = duplicate_check(df)
    duplicates_chart(all_ratios)
    wordcount_chart(df)
    specificity_check(df)
    complaint_scan(df)
    has_text = (df["text"].str.strip() != "").sum()
    complaint_chart(total_with_text=has_text, real_complaints=1)
