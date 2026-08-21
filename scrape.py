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
        browser = p.chromium.launch(headless=False, executable_path =  r"C:\Users\HP\AppData\Local\ms-playwright\chromium-1234\chrome.exe")
        page = browser.new_page()

        page.goto(place_url, timeout=60000)  # timeout in ms = 60 sec max to load
        page.wait_for_timeout(3000)  # crude wait: give the page 3s to render JS
        # Handle the consent interstitial if it appears
        try:
            page.get_by_role("button", name="Accept all").click(timeout=5000)
            page.wait_for_timeout(2000)
        except:
            pass  # no consent screen appeared, continue normally

        # Click on the "Reviews" tab/button.
        # This selector targets a button whose visible text contains "reviews"
        # NOTE: Google changes its DOM/class names often — this exact selector
        # may break. You'll likely need to inspect the page yourself (see below).
        page.get_by_role("tab", name="Reviews", exact=False).click(timeout=15000)
        page.wait_for_timeout(2000)

        # Google Maps reviews live inside a scrollable <div>.
        # We need to find that div specifically (not the whole page)
        # and scroll IT, not the window.
        scrollable_div = page.query_selector("div[aria-label*='Reviews']")

        last_count = 0
        stable_rounds = 0
        # Scroll repeatedly, pausing to let new reviews load each time.
        # This loop is what gets you past the "top 5" limit the API gave you.
        for _ in range(60):
            cards = page.query_selector_all("div.jftiEf")
            if cards:
                cards[-1].scroll_into_view_if_needed()
            page.wait_for_timeout(1200)

            new_count = len(page.query_selector_all("div.jftiEf"))
            if new_count == last_count:
                stable_rounds += 1
            if stable_rounds >= 3:
                break
            else:
                stable_rounds = 0
            last_count = new_count

        # Now grab every review card on the page.
        review_cards = page.query_selector_all("div.jftiEf")

        for card in review_cards:
            try:
                name = card.get_attribute("aria-label")
                rating_el = card.query_selector("span.kvMYJc")
                rating = rating_el.get_attribute("aria-label") if rating_el else None
                date_el = card.query_selector("span.rsqaWe")
                date = date_el.inner_text() if date_el else ""
                text_el = card.query_selector("span.wiI7pd")
                text = text_el.inner_text() if text_el else ""
                response_el = card.query_selector("div.wiI7pd") 
                response_block = response_el.inner_text() if response_el else ""
                response_date_el = card.query_selector("span.DZSIDd")
                response_date = response_date_el.inner_text() if response_date_el else ""

                has_reply = response_el is not None
                reviews.append({
                    "name": name,
                    "rating": rating,
                    "text": text,
                    "date": date,
                    "has_reply": has_reply,
                    "response_text": response_block,
                    "respose_date": response_date
                })
            except Exception as e:
                # If one card fails (missing element etc.), log it and move on
                # rather than crashing the whole scrape.
                print("Skipped a card:", e)
                continue

        browser.close()

    return reviews


if __name__ == "__main__":
    url = "https://www.google.com/maps/place/Mascot+Healthcare+Clinic/@6.5281436,3.3830707,17z/data=!3m1!4b1!4m6!3m5!1s0x103bf7349e09919d:0x98d71f08ca7aab1b!8m2!3d6.5281436!4d3.3856456!16s%2Fg%2F11vbqqtyd1?entry=ttu&g_ep=EgoyMDI2MDgxNi4wIKXMDSoASAFQAw%3D%3D"
    data = scrape_reviews(url)

    with open("mascot_reviews.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "rating", "text", "date"])
        writer.writeheader()
        writer.writerows(data)

    print(f"Pulled {len(data)} reviews.")