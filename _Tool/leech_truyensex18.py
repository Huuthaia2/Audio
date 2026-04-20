import os
import sys
import re
import requests
import time
import json
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CẤU HÌNH ---
BASE_URL = "https://truyensex18.com"
NEW_STORIES_URL = "https://truyensex18.com/truyen-moi"
CHECK_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\Text Mp3"
MAX_WORKERS = 10  # Số lượng luồng (Tải 10 chương cùng lúc)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
}

# Bảng mã xóa dấu tiếng Việt
MARK_MAP = {
    'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a', 'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a', 'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
    'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e', 'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
    'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o', 'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o', 'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
    'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u', 'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
    'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    'đ': 'd', 'Á': 'A', 'À': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A', 'Ă': 'A', 'Ắ': 'A', 'Ằ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A', 'Â': 'A', 'Ấ': 'A', 'Ầ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
    'É': 'E', 'È': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E', 'Ê': 'E', 'Ế': 'E', 'Ề': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
    'Í': 'I', 'Ì': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
    'Ó': 'O', 'Ò': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O', 'Ô': 'O', 'Ố': 'O', 'Ồ': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O', 'Ơ': 'O', 'Ớ': 'O', 'Ờ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
    'Ú': 'U', 'Ù': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U', 'Ư': 'U', 'Ứ': 'U', 'Ừ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
    'Ý': 'Y', 'Ỳ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y', 'Đ': 'D'
}
TRANSTAB = str.maketrans(MARK_MAP)
NON_ALPHANUM_RE = re.compile(r'[^a-z0-9]')

session = requests.Session()
session.headers.update(HEADERS)

# --- CACHE ---
EXISTING_NAMES_CACHE = set()

def normalize_match(s):
    if not s: return ""
    return NON_ALPHANUM_RE.sub('', s.translate(TRANSTAB).lower())

def pre_scan_storage():
    """Quét kho truyện 1 lần duy nhất để tạo cache, tăng tốc độ check trùng 100 lần"""
    if not os.path.exists(CHECK_DIR): return
    print(f"[*] Đang index kho truyện tại {CHECK_DIR}...")
    for root, _, files in os.walk(CHECK_DIR):
        for f in files:
            if f.lower().endswith(".txt"):
                normalized_f = normalize_match(os.path.splitext(f)[0])
                EXISTING_NAMES_CACHE.add(normalized_f)
    print(f"[*] Đã index {len(EXISTING_NAMES_CACHE)} file.")

def get_soup(url):
    try:
        res = session.get(url, timeout=15)
        if res.status_code == 200:
            return BeautifulSoup(res.text, 'html.parser')
    except: pass
    return None

def download_chapter(chapter_num, url):
    """Hàm tải 1 chương đơn lẻ"""
    soup = get_soup(url)
    if not soup: return chapter_num, None
    
    content_box = soup.select_one('.reading-content') or soup.select_one('.entry-content') or soup
    for r in content_box(['script', 'style', 'iframe', 'header', 'footer']): r.decompose()
    text = content_box.get_text(separator='\n').strip()
    return chapter_num, text

def leech_truyensex18():
    pre_scan_storage()
    
    print(f"[*] Đang lấy danh sách truyện mới...")
    soup = get_soup(NEW_STORIES_URL)
    if not soup: return

    story_links = []
    for h3 in soup.select('h3'):
        a = h3.find('a')
        if a and a.get('href'):
            url = a['href']
            if not url.startswith('http'): url = BASE_URL + url
            story_links.append({'title': a.get_text().strip(), 'url': url})

    for item in story_links:
        title, url = item['title'], item['url']
        slug = url.strip('/').split('/')[-1]
        
        # 1. Check trùng tên nhanh từ cache
        if normalize_match(title) in EXISTING_NAMES_CACHE:
            print(f"[-] Bỏ qua (Đã có): {title}")
            continue

        print(f"\n>>> Đang tải: {title}")
        story_soup = get_soup(url)
        if not story_soup: continue

        chapter_list = []
        chapters_div = story_soup.select_one('.listing-chapters-list') or story_soup
        all_links = chapters_div.find_all('a', href=re.compile(r'/chapter-'))
        
        seen_hrefs = set()
        for a in reversed(all_links):
            href = a['href']
            if href not in seen_hrefs:
                if not href.startswith('http'): href = BASE_URL + href
                chapter_list.append(href)
                seen_hrefs.add(href)

        if not chapter_list:
            print("    [!] Không tìm thấy danh sách chương.")
            continue

        print(f"    [*] Tìm thấy {len(chapter_list)} chương. Đang tải đa luồng...")
        
        results = {}
        failed_chapters = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_url = {executor.submit(download_chapter, i+1, c_url): i+1 for i, c_url in enumerate(chapter_list)}
            for future in as_completed(future_to_url):
                c_num, c_text = future.result()
                if c_text:
                    results[c_num] = c_text
                    print(f"\r      -> Đã tải xong {len(results)}/{len(chapter_list)} chương...", end="", flush=True)
                else:
                    failed_chapters.append(str(c_num))

        # Xây dựng nội dung file
        final_file_name = f"{slug}-{len(chapter_list):03d}.txt"
        if failed_chapters:
            final_file_name = "_" + final_file_name
            failed_chapters.sort(key=int)

        with open(final_file_name, "w", encoding="utf-8") as f:
            f.write(f"{'='*30}\n TITLE: {title}\n{'='*30}\n\n")
            
            # Ghi Note nếu có lỗi
            if failed_chapters:
                f.write(f" [!!!] CẢNH BÁO: Có {len(failed_chapters)} chương bị lỗi tải.\n")
                f.write(f" [!] DANH SÁCH CHƯƠNG LỖI: {', '.join(failed_chapters)}\n")
                f.write(f"\n{'='*30}\n\n")

            # Ghép nội dung theo thứ tự
            for i in range(1, len(chapter_list) + 1):
                if i in results:
                    f.write(f"\n\n{'='*20} CHƯƠNG {i} {'='*20}\n\n")
                    f.write(results[i])
                else:
                    f.write(f"\n\n{'='*20} CHƯƠNG {i} (LỖI TẢI) {'='*20}\n\n")
        
        print(f"\n    [DONE] Đã lưu: {final_file_name}")

if __name__ == "__main__":
    leech_truyensex18()
