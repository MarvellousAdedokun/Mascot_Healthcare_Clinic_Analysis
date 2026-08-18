# found a easier library to use
from playwright.sync_api import sync_playwright
import time
import csv

def scrape_reviews(place_url, max_reviews=250)
    reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto(place_url, 
        timeout=6000)
        page.wait_for_timeout(3000)
        