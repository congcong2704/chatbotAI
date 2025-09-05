# crawl_watv_vietnamese_filtered.py
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import time
import re
import sys
import langdetect  # pip install langdetect

sys.stdout.reconfigure(encoding='utf-8')

BASE_DOMAIN = "watv.org"
START_URL = "https://watv.org/vi/"  # Phiên bản tiếng Việt

visited = set()
to_visit = [START_URL]
sentences_data = []

def is_internal_vi(url):
    parsed = urlparse(url)
    return BASE_DOMAIN in parsed.netloc and "/vi/" in parsed.path

def normalize(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    return f"{parsed.scheme}://{parsed.netloc}{path}"

def split_into_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

def is_vietnamese(text):
    try:
        return langdetect.detect(text) == 'vi'
    except:
        return False

while to_visit:
    url = to_visit.pop(0)
    url = normalize(url)
    if url in visited:
        continue
    visited.add(url)

    try:
        res = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            continue
    except Exception as e:
        print("Lỗi tải URL:", url, e)
        continue

    soup = BeautifulSoup(res.text, "html.parser")
    title = soup.title.string.strip() if soup.title else ""

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
    for pi, para in enumerate(paragraphs, 1):
        for si, sentence in enumerate(split_into_sentences(para), 1):
            sentence = sentence.strip()
            if sentence and is_vietnamese(sentence):
                sentences_data.append({
                    "title": title,
                    "url": url,
                    "paragraph_index": pi,
                    "sentence_index": si,
                    "sentence": sentence
                })
                print(f"Câu: {sentence[:80]}...")

    # Thêm link nội bộ tiếng Việt
    for a in soup.find_all("a", href=True):
        link = urljoin(url, a["href"])
        link = normalize(link)
        if is_internal_vi(link) and link not in visited and link.startswith("http"):
            to_visit.append(link)

    time.sleep(1)

with open("watv_all_sentences_vi_filtered.json", "w", encoding="utf-8") as f:
    json.dump(sentences_data, f, ensure_ascii=False, indent=2)

print(f"Crawl xong, tổng cộng {len(sentences_data)} câu, lưu vào watv_all_sentences_vi_filtered.json")
