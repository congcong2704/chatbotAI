import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://watv.org"
CATEGORIES = [
    "sermons",
    "news",
    "media",
    "truth",
    "church"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

def get_links(category_url):
    """Lấy tất cả link bài viết trong 1 category"""
    links = []
    page = 1
    while True:
        url = f"{category_url}?page={page}"
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            break
        soup = BeautifulSoup(res.text, "html.parser")

        # tìm các link bài viết
        found = False
        for a in soup.select("a"):
            href = a.get("href")
            if href and "/content/" in href:
                full = BASE_URL + href if href.startswith("/") else href
                if full not in links:
                    links.append(full)
                    found = True

        # nếu trang này không còn link mới → dừng
        if not found:
            break

        page += 1
        time.sleep(1)

    return links

def get_article(url):
    """Lấy nội dung bài viết"""
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else "No Title"
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        content = " ".join(paragraphs)

        return {"url": url, "title": title, "content": content}
    except Exception as e:
        return {"url": url, "title": "Error", "content": str(e)}

def crawl_all():
    all_articles = []
    for cat in CATEGORIES:
        cat_url = f"{BASE_URL}/{cat}/"
        print(f"Đang crawl category: {cat_url}")
        links = get_links(cat_url)
        print(f"  -> Tim thay {len(links)} bai viet")
        for i, link in enumerate(links, 1):
            article = get_article(link)
            all_articles.append(article)
            print(f"    [{i}/{len(links)}] {article['title']}")
            time.sleep(1)

    with open("watv_articles.json", "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    print("✅ Đã lưu tất cả bài viết vào watv_articles.json")

if __name__ == "__main__":
    crawl_all()
