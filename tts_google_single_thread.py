import os
import re
import time
import requests
import sys

# --- CẤU HÌNH ---
# Thư mục chứa các file .txt cần đọc
INPUT_DIR = r"C:\Users\Windows\Documents\MEGA\Audio\Text Mp3\txt"
# Thư mục lưu file .mp3 kết quả
OUTPUT_DIR = r"C:\Users\Windows\Documents\MEGA\Audio\Text Mp3\mp3_output"

# Đảm bảo console hiển thị được tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def clean_text(text):
    """Loại bỏ quảng cáo và các ký tự thừa"""
    # Xóa các đoạn text quảng cáo phổ biến
    ad_patterns = [
        r"Website chuyển qua tên miền mới là:.*?, các bạn nhớ tên miền mới để tiện truy cập nhé!",
        r"Bạn đang đọc truyện.*?tại nguồn: https?://\S+",
        r"Bạn đang đọc Chương \d+.*?tại đây:\s*https?://\S+",
        r"TITLE:.*",
        r"={10,}.*?={10,}"
    ]
    for pattern in ad_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    
    # Chuẩn hóa khoảng trắng
    text = re.sub(r'\n+', '\n', text)
    return text.strip()

def split_text(text, limit=180):
    """Chia nhỏ văn bản thành các đoạn dưới 180 ký tự để bypass giới hạn Google"""
    # Tách theo các dấu ngắt câu
    sentences = re.split(r'([.\n,?!])', text)
    chunks = []
    current = ""
    
    for part in sentences:
        if len(current) + len(part) < limit:
            current += part
        else:
            if current.strip():
                chunks.append(current.strip())
            current = part
            
    if current.strip():
        chunks.append(current.strip())
    return chunks

def download_tts(text, output_file):
    """Tải audio từ Google TTS và lưu vào file"""
    url = "https://translate.google.com/translate_tts"
    params = {
        "ie": "UTF-8",
        "q": text,
        "tl": "vi",
        "client": "tw-ob"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            with open(output_file, 'ab') as f:
                f.write(response.content)
            return True
        elif response.status_code == 429:
            print("[!] Lỗi 429: Bị Google chặn. Đang nghỉ 30 giây...")
            time.sleep(30)
            return False
        else:
            print(f"[!] Lỗi HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[!] Lỗi kết nối: {e}")
        return False

def process_story(filepath):
    filename = os.path.basename(filepath)
    output_name = os.path.splitext(filename)[0] + ".mp3"
    output_path = os.path.join(OUTPUT_DIR, output_name)
    
    if os.path.exists(output_path):
        print(f"[-] Đã tồn tại, bỏ qua: {output_name}")
        return

    print(f"[*] Đang xử lý: {filename}")
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    text = clean_text(content)
    chunks = split_text(text)
    
    print(f"    - Tổng cộng {len(chunks)} đoạn cần đọc.")
    
    # Xóa file cũ nếu có để ghi mới (concat)
    if os.path.exists(output_path):
        os.remove(output_path)
    
    success_count = 0
    for i, chunk in enumerate(chunks):
        print(f"\r      -> Đang tải đoạn {i+1}/{len(chunks)}...", end="", flush=True)
        
        # Thử lại tối đa 3 lần cho mỗi đoạn
        for retry in range(3):
            if download_tts(chunk, output_path):
                success_count += 1
                # NGHỈ ĐƠN LUỒNG: Quan trọng để tránh 429
                time.sleep(1.2) 
                break
            else:
                time.sleep(5)
    
    print(f"\n[OK] Hoàn tất! Đã lưu: {output_name}")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    print(f"[*] Tìm thấy {len(files)} file cần chuyển đổi sang giọng nói.")
    
    for i, file in enumerate(files):
        print(f"\n[{i+1}/{len(files)}]")
        process_story(os.path.join(INPUT_DIR, file))
        # Nghỉ giữa các file truyện
        time.sleep(2)

if __name__ == "__main__":
    main()
