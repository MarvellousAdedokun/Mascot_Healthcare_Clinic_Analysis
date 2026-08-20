"""
Mascot Healthcare Clinic — "Are These Reviews Real?" analysis
"""

import pandas as pd
import re
from difflib import SequenceMatcher
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

CSV_PATH = "/mnt/user-data/uploads/mascot_reviews.csv"

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

    return dupes, len(texts)


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


# ---------------------------------------------------------------------
if __name__ == "__main__":
    df = load()

    print("=== BASIC ===")
    print(df["rating"].value_counts())
    print(f"Reviews with written text: {(df['text'].str.strip() != '').sum()} / {len(df)}")

    duplicate_check(df)
    wordcount_chart(df)
    specificity_check(df)
    complaint_scan(df)
