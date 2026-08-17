# found a easier library to use
from playwright.sync_api import sync_playwright
import time
import csv

def scrape_reviews(place_url, max_reviews=250)
    reviews = []

    with sync_playwright() as p: