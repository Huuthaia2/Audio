import requests
from bs4 import BeautifulSoup
import time

# --- CẤU HÌNH ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://google.com'
}

def get_story_info(url):
    print(f"[*] Đang lấy thông tin truyện từ: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Lấy tiêu đề truyện (vẫn lấy để ghi vào nội dung file)
        title_tag = soup.select_one('.post-title h1') or soup.select_one('h1')
        title = title_tag.get_text().strip() if title_tag else "Truyen_Leech"
        
        # Lấy slug từ URL để làm tên file cơ bản
        url_slug = url.strip('/').split('/')[-1]
        
        chapter_list = []
        
        # 1. Thử lấy từ trang chính trước
        links = soup.select('li.wp-manga-chapter a')
        
        # 2. Nếu không thấy, thử gọi AJAX POST
        if not links:
            print("[*] Đang thử lấy danh sách chương qua AJAX...")
            ajax_url = url.rstrip('/') + "/ajax/chapters/"
            try:
                ajax_res = requests.post(ajax_url, headers=HEADERS, timeout=10)
                if ajax_res.status_code == 200:
                    ajax_soup = BeautifulSoup(ajax_res.text, 'html.parser')
                    links = ajax_soup.select('li.wp-manga-chapter a')
            except Exception:
                pass

        for a in links:
            c_url = a.get('href')
            c_title = a.get_text().strip()
            if c_url and c_title:
                chapter_list.append({'title': c_title, 'url': c_url})
        
        if not chapter_list:
            print("[!] Không tìm thấy chương tự động. Tạo danh sách dự phòng Phần 1-5...")
            for i in range(1, 6):
                suffix = f"phan-{i}/"
                chapter_list.append({'title': f'Phần {i}', 'url': url + suffix})
        else:
            chapter_list = chapter_list[::-1]
            
        # Tạo tên file theo format: slug-tongsochương(4 số).txt
        file_name = f"{url_slug}-{len(chapter_list):04d}.txt"
            
        return title, file_name, chapter_list
    except Exception as e:
        print(f"[!] Lỗi khi lấy thông tin truyện: {e}")
        return None, "error.txt", []

def get_content(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 404:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        content_box = soup.select_one('.text-left') or soup.select_one('.reading-content') or soup.select_one('.entry-content')
        
        if content_box:
            for s in content_box(['script', 'style', 'iframe']):
                s.decompose()
            return content_box.get_text(separator='\n').strip()
    except Exception:
        pass
    return "--- Không tìm thấy nội dung ---"

import os
import re
import difflib

CHECK_DIR = r"C:\Users\Windows\Documents\MEGA\Audio\Text Mp3"

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

def is_similar(name1, name2, threshold=0.8):
    # Chuẩn hóa tên: bỏ dấu, viết thường, bỏ ký tự đặc biệt
    def normalize(s):
        s = remove_vietnamese_marks(s).lower()
        s = re.sub(r'[^a-z0-9\s]', ' ', s) # Thay ký tự lạ bằng khoảng trắng
        return " ".join(s.split()) # Xóa khoảng trắng thừa
    
    n1 = normalize(name1)
    n2 = normalize(name2)
    
    if not n1 or not n2: return False
    
    if n1 in n2 or n2 in n1:
        return True
    
    # Dùng SequenceMatcher để tính độ tương đồng
    ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
    return ratio >= threshold

def check_exists_in_folder(story_title):
    if not os.path.exists(CHECK_DIR):
        return None
    
    # Duyệt đệ quy qua toàn bộ thư mục con bằng os.walk
    for root, dirs, files in os.walk(CHECK_DIR):
        for f in files:
            file_name_no_ext = os.path.splitext(f)[0]
            if is_similar(story_title, file_name_no_ext):
                # Trả về đường dẫn file để log
                return os.path.join(root, f)
    return None

def check_content_match(target_text):
    if not target_text or len(target_text) < 100:
        return None
    
    # Lấy 150 ký tự đầu để làm "dấu vân tay" so sánh
    fingerprint = normalize_content(target_text[:150])
    
    if not os.path.exists(CHECK_DIR):
        return None

    for root, dirs, files in os.walk(CHECK_DIR):
        for f in files:
            if f.endswith('.txt'):
                file_path = os.path.join(root, f)
                try:
                    # Chỉ đọc 2000 ký tự đầu của file cũ để check cho nhanh
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as old_f:
                        head_content = normalize_content(old_f.read(2000))
                        if fingerprint in head_content:
                            return file_path
                except Exception:
                    continue
    return None

def normalize_content(s):
    s = remove_vietnamese_marks(s).lower()
    return re.sub(r'[^a-z0-9]', '', s) # Xóa sạch mọi thứ chỉ giữ lại ký tự/số để so khớp tuyệt đối

def leech_story(url_input):
    if not url_input.endswith('/'):
        url_input += '/'

    title, file_name, chapters = get_story_info(url_input)
    if not chapters:
        print(f"[!] Bỏ qua {url_input} do không lấy được thông tin.")
        return

    # KIỂM TRA TRÙNG LẶP THEO NỘI DUNG (CHÍNH XÁC TUYỆT ĐỐI)
    print(f"[*] Đang tải thử chương đầu để kiểm tra nội dung trùng lặp...")
    first_chap_url = chapters[0]['url']
    first_chap_text = get_content(first_chap_url)
    
    if first_chap_text and first_chap_text != "--- Không tìm thấy nội dung ---":
        match_path = check_content_match(first_chap_text)
        if match_path:
            # Lấy tên file trùng khớp (bỏ đường dẫn và đuôi .txt)
            matched_name = os.path.splitext(os.path.basename(match_path))[0]
            # Lấy slug của truyện đang định tải
            url_slug = url_input.strip('/').split('/')[-1]
            
            skip_file_name = f"_{url_slug}-=-{matched_name}.txt"
            
            print(f"[*] CẢNH BÁO: NỘI DUNG trùng với file: {match_path}")
            print(f"[*] Tạo file đánh dấu: {skip_file_name}")
            
            with open(skip_file_name, "w", encoding="utf-8") as f:
                f.write(f"SKIP: Da co tai MEGA (Trung Noi Dung): {match_path}")
            return

    print(f"\n[+] Đang tải: {title}")
    print(f"[+] File: {file_name}")
    print(f"[+] Tổng: {len(chapters)} chương")

    has_error = False
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(f"{'='*30}\n TITLE: {title}\n{'='*30}\n\n")
        
        # Ghi chương 1 đã tải vào luôn để không phải tải lại
        f.write(f"\n\n{'='*20} {chapters[0]['title']} {'='*20}\n\n")
        f.write(first_chap_text)
        f.write("\n\n")
        
        count = 1
        for chap in chapters[1:]: # Tải từ chương 2
            print(f"    - {chap['title']}...", end=" ", flush=True)
            text = get_content(chap['url'])
            
            if text is None or "Không tìm thấy nội dung" in text:
                has_error = True
                if "Không tìm thấy chương tự động" in str(chapters):
                    print("Bỏ qua.")
                    break
                print("Lỗi.")
                continue
            
            f.write(f"\n\n{'='*20} {chap['title']} {'='*20}\n\n")
            f.write(text)
            f.write("\n\n")
            print("Xong.")
            count += 1
            time.sleep(1.2)

    if has_error:
        new_file_name = "_" + file_name
        try:
            if os.path.exists(new_file_name):
                os.remove(new_file_name)
            os.rename(file_name, new_file_name)
            file_name = new_file_name
        except Exception:
            pass

    print(f"[OK] Hoàn tất truyện: {title}. Đã tải {count} chương. File: {file_name}\n")

def main():
    import sys
    print("--- Tool Leech Truyện ---")
    print("1. Tải 1 truyện duy nhất")
    print("2. Tải hàng loạt (Dán nhiều URL)")
    choice = input("Chọn chế độ (1/2): ").strip()

    if choice == "1":
        url = input("\nNhập URL truyện: ").strip()
        if url:
            leech_story(url)
    elif choice == "2":
        print("\nDán danh sách URL (Mỗi URL một dòng).")
        print("Sau khi dán xong, nhấn Enter rồi nhấn Ctrl+Z và gõ Enter lần nữa để bắt đầu:\n")
        try:
            input_data = sys.stdin.read()
        except EOFError:
            input_data = ""
        
        urls = [u.strip() for u in input_data.replace(',', ' ').split() if u.strip()]
        if not urls:
            print("[!] Không có URL nào để xử lý.")
            return

        print(f"\n[*] Tìm thấy {len(urls)} truyện cần tải.")
        for i, url in enumerate(urls):
            print(f"====== TRUYỆN {i+1}/{len(urls)} ======")
            leech_story(url)
            if i < len(urls) - 1:
                print("[*] Nghỉ 3 giây...")
                time.sleep(3)
    else:
        print("[!] Lựa chọn không hợp lệ.")

    print("\n[DONE] Đã hoàn thành!")

if __name__ == "__main__":
    main()