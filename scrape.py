# Install first, in terminal:
# pip install playwright
# playwright install chromium
# ^ this second command downloads an actual headless Chromium browser
#   Playwright will drive — it's not optional, the library needs a browser binary to control

from playwright.sync_api import sync_playwright
import time
import csv

def scrape_reviews(place_url, max_reviews=250):
    reviews = []  # we'll fill this list with dicts, one per review

    with sync_playwright() as p:
        # Launch a headless (no visible window) Chromium browser.
        # headless=False if you want to WATCH it work while debugging — useful early on.
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(place_url, timeout=60000)  # timeout in ms = 60 sec max to load
        page.wait_for_timeout(3000)  # crude wait: give the page 3s to render JS

        # Click on the "Reviews" tab/button.
        # This selector targets a button whose visible text contains "reviews"
        # NOTE: Google changes its DOM/class names often — this exact selector
        # may break. You'll likely need to inspect the page yourself (see below).
        page.click("button[aria-label*='Reviews']")
        page.wait_for_timeout(2000)

        # Google Maps reviews live inside a scrollable <div>.
        # We need to find that div specifically (not the whole page)
        # and scroll IT, not the window.
        scrollable_div = page.query_selector("div[aria-label*='Reviews']")

        # Scroll repeatedly, pausing to let new reviews load each time.
        # This loop is what gets you past the "top 5" limit the API gave you.
        for _ in range(40):  # 40 scroll attempts ~ rough ceiling, tune as needed
            page.evaluate(
                "(el) => el.scrollTop = el.scrollHeight",
                scrollable_div
            )
            time.sleep(1.5)  # let new reviews render before scrolling again

        # Now grab every review card on the page.
        review_cards = page.query_selector_all("div[data-review-id]")

        for card in review_cards:
            try:
                name = card.query_selector(".d4r55").inner_text()
                rating_el = card.query_selector("span[role='img']")
                rating = rating_el.get_attribute("aria-label") if rating_el else None
                text_el = card.query_selector(".wiI7pd")
                text = text_el.inner_text() if text_el else ""
                date_el = card.query_selector(".rsqaWe")
                date = date_el.inner_text() if date_el else ""

                reviews.append({
                    "name": name,
                    "rating": rating,
                    "text": text,
                    "date": date
                })
            except Exception as e:
                # If one card fails (missing element etc.), log it and move on
                # rather than crashing the whole scrape.
                print("Skipped a card:", e)
                continue

        browser.close()

    return reviews


if __name__ == "__main__":
    url = "PASTE_MASCOT_CLINIC_GOOGLE_MAPS_URL_HERE"
    data = scrape_reviews(url)

    with open("mascot_reviews.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "rating", "text", "date"])
        writer.writeheader()
        writer.writerows(data)

    print(f"Pulled {len(data)} reviews.")