import requests
from bs4 import BeautifulSoup
import time
import os
import re
import difflib
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- CẤU HÌNH ---
CHECK_DIR = r"C:\Users\Windows\Documents\MEGA\Audio\Text Mp3"
MAX_WORKERS = 10  # Tải 10 chương cùng lúc
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://google.com'
}

session = requests.Session()
session.headers.update(HEADERS)

# --- CACHE TOÀN CỤC ---
EXISTING_TITLES = set() # Lưu tên file đã chuẩn hóa
FINGERPRINT_MAP = {}    # {normalized_fingerprint: original_file_path}

def remove_vietnamese_marks(s):
    marks = {
        'a': 'áàảãạăắằẳẵặâấầẩẫậ',
        'e': 'éèẻẽẹêếềểễệ',
        'i': 'íìỉĩị',
        'o': 'óòỏõọôốồổỗộơớờởỡợ',
        'u': 'úùủũụưứừửữự',
        'y': 'ýỳỷỹỵ',
        'd': 'đ'
    }
    for char, group in marks.items():
        for m in group:
            s = s.replace(m, char)
            s = s.replace(m.upper(), char.upper())
    return s

def normalize_simple(s):
    """Chuẩn hóa để so khớp tên và nội dung"""
    if not s: return ""
    s = remove_vietnamese_marks(s).lower()
    return re.sub(r'[^a-z0-9]', '', s)

def pre_scan_storage():
    """Index toàn bộ kho truyện để check trùng siêu tốc"""
    if not os.path.exists(CHECK_DIR): return
    print(f"[*] Đang index kho truyện tại {CHECK_DIR} (Chỉ chạy 1 lần)...")
    count = 0
    for root, _, files in os.walk(CHECK_DIR):
        for f in files:
            if f.lower().endswith(".txt"):
                name_key = normalize_simple(os.path.splitext(f)[0])
                EXISTING_TITLES.add(name_key)
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore') as file_obj:
                        content_head = file_obj.read(500)
                        finger = normalize_simple(content_head[:150])
                        if len(finger) > 50:
                            FINGERPRINT_MAP[finger] = os.path.join(root, f)
                except: pass
                count += 1
    print(f"[*] Đã index {count} truyện. Sẵn sàng tải!")

def get_story_info(url):
    print(f"[*] Đang lấy thông tin truyện từ: {url}")
    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_tag = soup.select_one('.post-title h1') or soup.select_one('h1')
        title = title_tag.get_text().strip() if title_tag else "Truyen_Leech"
        url_slug = url.strip('/').split('/')[-1]
        
        chapter_list = []
        links = soup.select('li.wp-manga-chapter a')
        
        if not links:
            ajax_url = url.rstrip('/') + "/ajax/chapters/"
            try:
                ajax_res = session.post(ajax_url, timeout=10)
                if ajax_res.status_code == 200:
                    ajax_soup = BeautifulSoup(ajax_res.text, 'html.parser')
                    links = ajax_soup.select('li.wp-manga-chapter a')
            except: pass

        for a in links:
            c_url = a.get('href')
            c_title = a.get_text().strip()
            if c_url:
                if c_url.rstrip('/') == url.rstrip('/'):
                    # Link bị lỗi (trỏ về trang chủ truyện), thử đoán link từ title
                    num_match = re.search(r'(\d+)', c_title)
                    if num_match:
                        num = num_match.group(1)
                        prefix = "chuong" if "Chương" in c_title else "phan"
                        c_url = url.rstrip('/') + f"/{prefix}-{num}/"
                
                chapter_list.append({'title': c_title, 'url': c_url})
        
        if not chapter_list:
            for i in range(1, 6):
                chapter_list.append({'title': f'Phần {i}', 'url': url.rstrip('/') + f"/phan-{i}/"})
        else:
            chapter_list = chapter_list[::-1]
            
        return title, url_slug, chapter_list
    except Exception as e:
        print(f"[!] Lỗi khi lấy thông tin: {e}")
        return None, "error", []

def download_chapter_worker(index, title, url):
    """Worker tải từng chương"""
    try:
        response = session.get(url, timeout=10)
        if response.status_code != 200: return index, title, None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content_boxes = [soup.select_one('.text-left'), soup.select_one('.reading-content'), soup.select_one('.entry-content')]
        content_box = None
        for box in content_boxes:
            if box and box.get_text(strip=True):
                content_box = box
                break

        
        if content_box:
            for s in content_box(['script', 'style', 'iframe', 'header', 'footer']):
                s.decompose()
            return index, title, content_box.get_text(separator='\n').strip()
    except: pass
    return index, title, None

def leech_story(url_input):
    if not url_input.endswith('/'): url_input += '/'

    title, slug, chapters = get_story_info(url_input)
    if not chapters: return

    if normalize_simple(title) in EXISTING_TITLES:
        print(f"[-] Bỏ qua (Trùng tên): {title}")
        return

    # Check nội dung chương 1 (Check Fingerprint)
    _, _, first_text = download_chapter_worker(1, "Check", chapters[0]['url'])
    if first_text:
        finger = normalize_simple(first_text[:150])
        if finger in FINGERPRINT_MAP:
            matched_name = os.path.basename(FINGERPRINT_MAP[finger])
            print(f"[*] CẢNH BÁO: Trùng nội dung với: {matched_name}")
            with open(f"_{slug}-=-{matched_name}", "w", encoding="utf-8") as f:
                f.write(f"SKIP (Trung Noi Dung): {FINGERPRINT_MAP[finger]}")
            return

    print(f"\n[+] Truyện mới: {title} ({len(chapters)} chương)")
    
    results = {}
    failed_chapters = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_chapter_worker, i+1, chap['title'], chap['url']): i+1 for i, chap in enumerate(chapters)}
        for future in as_completed(futures):
            idx, c_title, text = future.result()
            if text:
                results[idx] = (c_title, text)
                print(f"\r      -> Đã tải xong {len(results)}/{len(chapters)} chương...", end="", flush=True)
            else:
                failed_chapters.append(str(idx))

    # Tên file
    file_name = f"{slug}-{len(chapters):04d}.txt"
    if failed_chapters:
        file_name = "_" + file_name
        failed_chapters.sort(key=int)

    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"{'='*30}\n TITLE: {title}\n{'='*30}\n\n")
        
        if failed_chapters:
            f.write(f" [!!!] CẢNH BÁO: Có {len(failed_chapters)} chương bị lỗi tải.\n")
            f.write(f" [!] DANH SÁCH CHƯƠNG LỖI: {', '.join(failed_chapters)}\n")
            f.write(f"\n{'='*30}\n\n")

        for i in range(1, len(chapters) + 1):
            if i in results:
                c_title, c_text = results[i]
                f.write(f"\n\n{'='*20} {c_title} {'='*20}\n\n")
                f.write(c_text + "\n\n")
            else:
                f.write(f"\n\n{'='*20} CHƯƠNG {i} (LỖI TẢI) {'='*20}\n\n")
    
    print(f"\n[OK] Đã lưu: {file_name}")

def main():
    pre_scan_storage()
    print("\n--- Tool Leech Truyện (Super Speed) ---")
    print("1. Tải 1 truyện")
    print("2. Tải hàng loạt (Dán list URL)")
    choice = input("Chọn (1/2): ").strip()

    if choice == "1":
        url = input("Nhập URL: ").strip()
        if url: leech_story(url)
    elif choice == "2":
        print("\nDán danh sách URL (Mỗi URL một dòng. Nhấn Ctrl+Z rồi Enter để chạy):\n")
        try: input_data = sys.stdin.read()
        except EOFError: input_data = ""
        urls = [u.strip() for u in input_data.replace(',', ' ').split() if u.strip()]
        for i, url in enumerate(urls):
            print(f"\n[STORY {i+1}/{len(urls)}]")
            leech_story(url)
            time.sleep(1)

if __name__ == "__main__":
    main()