import os
import re

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
TARGET_DIR = r"d:\z\Audio\_Tool\Audio\zDaCoMp3"
EXCLUDE_DIR = "zzzzLoi"

def get_core_slug_mp3(name):
    # Xóa đuôi .mp3
    name = name.lower().replace(".mp3", "")
    # Xóa các hậu tố phổ biến
    name = re.sub(r'(_\d+|\(\d+\)|\+chuong.*| - copy.*| - Copy.*)$', '', name)
    # Xóa các ký tự đặc biệt ở cuối
    name = name.strip("-_+ ")
    return name

def get_core_slug_txt(name):
    # Xóa đuôi .txt
    name = name.lower().replace(".txt", "")
    # Xóa hậu tố số chương (ví dụ: -0001, -123)
    name = re.sub(r'(-\d+)$', '', name)
    return name

def main():
    if not os.path.exists(MP3_LIST_FILE):
        print(f"Error: {MP3_LIST_FILE} not found.")
        return

    # 1. Load MP3 Slugs
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        mp3_names = [line.strip() for line in f if line.strip()]
    
    mp3_slugs = set()
    for m in mp3_names:
        mp3_slugs.add(get_core_slug_mp3(m))

    # 2. Quét file Text
    matches = []
    total_txt = 0
    
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root:
            continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                total_txt += 1
                txt_slug = get_core_slug_txt(f)
                
                # Kiểm tra khớp Core Slug
                if txt_slug in mp3_slugs:
                    matches.append((f, root))
                else:
                    # Thử khớp "chứa trong" (Partial Match)
                    # Ví dụ: me-con khớp với me-con-loan-luan
                    for m_slug in mp3_slugs:
                        if txt_slug in m_slug or m_slug in txt_slug:
                            if len(txt_slug) > 5: # Chỉ khớp nếu slug đủ dài để tránh trùng bậy
                                matches.append((f, root))
                                break

    # 3. Hiển thị kết quả preview
    print(f"Total TXT files scanned: {total_txt}")
    print(f"Matches found: {len(matches)}")
    print("-" * 50)
    
    if matches:
        # Show first 50 matches as preview
        for i, (f_name, f_root) in enumerate(matches[:50]):
            rel_path = os.path.relpath(f_root, TEXT_DIR)
            print(f"[{i+1}] {f_name} (in {rel_path})")
        
        if len(matches) > 50:
            print(f"... and {len(matches)-50} more matches.")
            
        print("-" * 50)
        print(f"Summary: Ready to move {len(matches)} files to {TARGET_DIR}")
    else:
        print("No matches found.")

if __name__ == "__main__":
    main()
