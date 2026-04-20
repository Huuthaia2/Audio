import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

def get_core_slug_mp3(name):
    name = name.lower().replace(".mp3", "")
    # Xóa các hậu tố phổ biến
    name = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', name)
    name = name.strip("-_+ ")
    return name

def get_core_slug_txt(name):
    name = name.lower().replace(".txt", "")
    # Xóa hậu tố số chương (ví dụ: -0001)
    name = re.sub(r'(-\d+)$', '', name)
    return name

def main():
    # 1. Load MP3 Slugs
    mp3_mapping = {}
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m_name = line.strip()
            if m_name:
                slug = get_core_slug_mp3(m_name)
                if slug not in mp3_mapping:
                    mp3_mapping[slug] = []
                mp3_mapping[slug].append(m_name)

    mp3_slug_list = list(mp3_mapping.keys())

    # 2. Quét file Text
    matches = []
    print("[*] Scanning text files...")
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                txt_slug = get_core_slug_txt(f)
                matched_mp3s = []
                
                # Ưu tiên khớp chính xác 100%
                if txt_slug in mp3_mapping:
                    matched_mp3s = mp3_mapping[txt_slug]
                else:
                    # Khớp mờ có chọn lọc để nhanh hơn
                    # Chỉ kiểm tra mờ nếu độ dài slug > 8
                    if len(txt_slug) >= 8:
                        for m_slug in mp3_slug_list:
                            # Điều kiện 1: Phải bắt đầu giống nhau (prefix matching)
                            # Hoặc một thằng là con của thằng kia với tỉ lệ chiều dài gần nhau
                            if txt_slug.startswith(m_slug) or m_slug.startswith(txt_slug):
                                len_diff = abs(len(txt_slug) - len(m_slug))
                                # Nếu chênh lệch quá 4 ký tự (ví dụ loan-luan vs loan-luan-ky-su là chênh 6 ký tự)
                                # thì không cho khớp trừ khi tỉ lệ rất cao
                                if len_diff <= 4:
                                    matched_mp3s = mp3_mapping[m_slug]
                                    break
                            
                            # Điều kiện 2: Fuzzy Match cao
                            # Chỉ chạy SequenceMatcher nếu 2 chuỗi có độ dài sàn sàn nhau
                            if abs(len(txt_slug) - len(m_slug)) < 5:
                                if SequenceMatcher(None, txt_slug, m_slug).ratio() > 0.9:
                                    matched_mp3s = mp3_mapping[m_slug]
                                    break
                
                if matched_mp3s:
                    matches.append({
                        'txt_name': f,
                        'txt_path': os.path.join(root, f),
                        'mp3_samples': matched_mp3s[:2]
                    })

    # 3. Ghi log
    print(f"[*] Found {len(matches)} matches. Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (STRICT V2) - Tổng: {len(matches)}\n")
        log.write("=" * 100 + "\n")
        for m in matches:
            mp3_str = ", ".join(m['mp3_samples'])
            log.write(f"TXT: {m['txt_name']}\n")
            log.write(f"PATH: {m['txt_path']}\n")
            log.write(f"MATCHED MP3: {mp3_str}\n")
            log.write("-" * 50 + "\n")

    print(f"\n[DONE] Log updated. Total matches: {len(matches)}")

if __name__ == "__main__":
    main()
