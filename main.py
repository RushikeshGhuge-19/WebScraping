import requests
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# =====================================================
# CONFIG
# =====================================================

BASE_URL = "https://books.toscrape.com/"
START_PAGE = "catalogue/page-1.html"
MAX_PAGES = 3              # increase slowly while learning
OUTPUT_FILE = "books.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================================================
# FETCH
# =====================================================

def fetch(url):
    print(f"FETCH → {url}")
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text

# =====================================================
# LISTING PAGE PARSER
# Pattern: cards on a page
# =====================================================

def extract_book_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for book in soup.select("article.product_pod h3 a"):
        href = book["href"]
        full_url = urljoin(BASE_URL, href)
        links.append(full_url)

    print(f"Found {len(links)} book links")
    return links

# =====================================================
# DETAIL PAGE PARSER
# Pattern: detail page fields
# =====================================================

def extract_book_details(html, url):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1").text.strip()
    price = soup.select_one(".price_color").text.strip()
    availability = soup.select_one(".availability").text.strip()
    description_tag = soup.select_one("#product_description")

    if description_tag:
        description = description_tag.find_next_sibling("p").text.strip()
    else:
        description = ""

    return {
        "url": url,
        "title": title,
        "price": price,
        "availability": availability,
        "description": description
    }

# =====================================================
# SCRAPER ENGINE
# =====================================================

def scrape_books():
    all_books = []
    current_page = START_PAGE

    for page in range(1, MAX_PAGES + 1):
        page_url = urljoin(BASE_URL, current_page)
        print(f"\n=== PAGE {page} ===")

        html = fetch(page_url)
        book_links = extract_book_links(html)

        for link in book_links:
            detail_html = fetch(link)
            book = extract_book_details(detail_html, link)
            all_books.append(book)
            print("  →", book["title"])

        # find next page
        soup = BeautifulSoup(html, "html.parser")
        next_btn = soup.select_one("li.next a")
        if not next_btn:
            break

        current_page = next_btn["href"]

    return all_books

# =====================================================
# CSV SAVE
# =====================================================

def save_to_csv(rows):
    if not rows:
        print("No data to save")
        return

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} books to {OUTPUT_FILE}")

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":
    data = scrape_books()
    save_to_csv(data)
