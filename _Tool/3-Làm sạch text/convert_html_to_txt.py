import os
from bs4 import BeautifulSoup
import re

# --- CONFIG ---
SOURCE_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\Text Mp3"

def clean_html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Loại bỏ các thành phần thừa trước khi quét
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
        tag.decompose()

    # 2. Tìm nội dung truyện theo các class phổ biến
    content_box = soup.select_one('.content, .entry-content, .post-content, .chapter-content, #chapter-c, .read-content, .reading-content, .content-truyen, .post-body')
    
    if content_box:
        text = content_box.get_text(separator='\n')
    else:
        # 3. FALLBACK: Nếu không thấy class nào, lấy nội dung trong body nhưng lọc bớt div rác
        # Đây là phần giúp xử lý các file như "Cực phẩm loạn luân"
        body = soup.find('body')
        if body:
            # Loại bỏ menu/comment thường gặp nếu có
            for garbage in body.select('.comment, .sidebar, .menu, .ads, .advertisement'):
                garbage.decompose()
            text = body.get_text(separator='\n')
        else:
            text = soup.get_text(separator='\n')

    # 4. Hậu xử lý văn bản
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            # Lọc bỏ các dòng trắng quá nhiều hoặc các dòng quảng cáo ngắn (tùy chọn)
            lines.append(line)
            
    return '\n'.join(lines)

def convert_recursive(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.html', '.htm', '.php')):
                html_path = os.path.join(root, file)
                txt_path = os.path.splitext(html_path)[0] + ".txt"
                
                # Nếu file txt chưa tồn tại hoặc bạn muốn convert lại
                try:
                    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                        html_content = f.read()
                    
                    clean_text = clean_html_to_text(html_content)
                    
                    if clean_text.strip():
                        with open(txt_path, 'w', encoding='utf-8') as f:
                            f.write(clean_text)
                        print(f"[OK] Converted: {file} -> {os.path.basename(txt_path)}")
                        count += 1
                    else:
                        print(f"[!] Warning: No content found in {file}")
                except Exception as e:
                    print(f"[ERROR] Failed to convert {file}: {e}")
    
    return count

if __name__ == "__main__":
    print(f"[*] Đang bắt đầu quét và convert tại: {SOURCE_DIR}")
    total = convert_recursive(SOURCE_DIR)
    print(f"\n[XONG] Đã hoàn thành convert {total} file mới.")
    print("="*50)
