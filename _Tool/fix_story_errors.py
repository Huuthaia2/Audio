import os
import re
import requests
from bs4 import BeautifulSoup

# --- CẤU HÌNH ---
TARGET_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao\zzzzLoi"
BASE_URL = "https://truyencogiaothao.site/truyen/"
MAX_WORKERS = 5
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

session = requests.Session()
session.headers.update(HEADERS)

def get_chapters_from_web(slug):
    url = f"{BASE_URL}{slug}/"
    try:
        res = session.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Thử lấy link trực tiếp hoặc qua show-more
        links = soup.select('li.wp-manga-chapter a')
        chapters = {}
        for a in links:
            title = a.get_text().strip()
            link = a.get('href')
            if title and link:
                chapters[title.lower()] = link
        return chapters
    except:
        return {}

def download_content(url):
    try:
        res = session.get(url, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        content_box = soup.select_one('.reading-content') or soup.select_one('.text-left') or soup.select_one('.entry-content')
        if content_box:
            for s in content_box(['script', 'style', 'iframe', 'header', 'footer']):
                s.decompose()
            return content_box.get_text(separator='\n').strip()
    except: pass
    return None

def process_file(file_path):
    filename = os.path.basename(file_path)
    print(f"\n[+] Processing: {filename}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Kiểm tra nếu file đã sạch (không còn note lỗi thực thụ)
    error_match = re.search(r"\{Lỗi tải chương: (.*?)\}", content)
    
    if not error_match:
        # Nếu không có note lỗi, chỉ cần xóa đấu _ và note rác
        new_content = re.sub(r'\{Note vào đây\}\n', '', content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        new_filename = filename.lstrip('_')
        new_path = os.path.join(TARGET_DIR, new_filename)
        try:
            if os.path.exists(new_path): os.remove(new_path)
            os.rename(file_path, new_path)
            print(f"  [OK] File đã sạch. Đã đổi tên thành: {new_filename}")
        except: pass
        return

    # 2. Nếu có lỗi, tiến hành tải bù
    error_list_str = error_match.group(1)
    error_chapters = [c.strip() for c in error_list_str.split(',')]
    
    slug_match = re.match(r"_(.*?)-\d+\.txt", filename)
    if not slug_match: return
    slug = slug_match.group(1)
    
    web_chapters = get_chapters_from_web(slug)
    fixed_count = 0
    new_content = content
    
    for chap_name in error_chapters:
        url = web_chapters.get(chap_name.lower())
        if not url:
            for web_name, web_url in web_chapters.items():
                if chap_name.lower() in web_name:
                    url = web_url
                    break
        
        if url:
            print(f"  -> Re-downloading: {chap_name}")
            fresh_text = download_content(url)
            if fresh_text and len(fresh_text) > 300:
                title_pattern = rf"(==================== {re.escape(chap_name)} ====================)"
                parts = re.split(title_pattern, new_content)
                if len(parts) >= 3:
                    before, header, after_all = parts[0], parts[1], parts[2]
                    next_header_match = re.search(r"\n==================== .*? ==================== \n", after_all)
                    rest = after_all[next_header_match.start():] if next_header_match else ""
                    new_content = before + header + "\n\n" + fresh_text + "\n\n" + rest
                    fixed_count += 1

    # 3. Cập nhật file sau khi vá
    new_content = re.sub(r'\{Lỗi tải chương: .*?\}\n', '', new_content)
    new_content = re.sub(r'\{Note vào đây\}\n', '', new_content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    new_filename = filename.lstrip('_')
    new_path = os.path.join(TARGET_DIR, new_filename)
    try:
        if os.path.exists(new_path): os.remove(new_path)
        os.rename(file_path, new_path)
        print(f"  [OK] Đã vá {fixed_count} chương và đổi tên: {new_filename}")
    except: pass

def main():
    files = [f for f in os.listdir(TARGET_DIR) if f.startswith("_") and f.endswith(".txt")]
    for f in files:
        process_file(os.path.join(TARGET_DIR, f))

if __name__ == "__main__":
    main()
