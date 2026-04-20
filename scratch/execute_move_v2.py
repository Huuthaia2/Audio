import os
import re
import shutil
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
TARGET_DIR = r"d:\z\Audio\_Tool\Audio\zDaCoMp3"
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

def is_similar(s1, s2):
    # Khớp chính xác
    if s1 == s2:
        return True
    
    # Nếu một trong hai quá ngắn, không cho khớp mờ
    if len(s1) < 8 or len(s2) < 8:
        return s1 == s2

    # Tính độ tương đồng
    ratio = SequenceMatcher(None, s1, s2).ratio()
    if ratio > 0.85:
        return True
        
    # Kiểm tra xem có chứa nhau không, nhưng phải là "đầu" của nhau
    # Ví dụ: 'loan-luan-ky-su' chứa 'loan-luan' nhưng 'loan-luan' không chứa 'ky-su'
    # Chúng ta muốn 'loan-luan-ky-su-0001.txt' tìm thấy 'loan-luan-ky-su-0012.mp3'
    # chứ không phải 'loan-luan.mp3'
    if s1.startswith(s2) or s2.startswith(s1):
        # Nếu s1 là 'loan-luan-ky-su' và s2 là 'loan-luan', tỉ lệ chiều dài phải gần nhau
        # Ở đây user nói loan-luan-ky-su ko khớp loan-luan.mp3
        # Vậy ta yêu cầu độ dài chênh lệch không quá 30%
        len_diff = abs(len(s1) - len(s2))
        if len_diff < max(len(s1), len(s2)) * 0.2:
            return True

    return False

def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

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

    # 2. Quét file Text
    matches = []
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root:
            continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                txt_slug = get_core_slug_txt(f)
                matched_mp3s = []
                
                # Ưu tiên khớp chính xác 100%
                if txt_slug in mp3_mapping:
                    matched_mp3s = mp3_mapping[txt_slug]
                else:
                    # Khớp mờ có chọn lọc
                    best_match = None
                    highest_ratio = 0
                    for m_slug, m_names in mp3_mapping.items():
                        if is_similar(txt_slug, m_slug):
                            ratio = SequenceMatcher(None, txt_slug, m_slug).ratio()
                            if ratio > highest_ratio:
                                highest_ratio = ratio
                                best_match = m_names
                    
                    if best_match:
                        matched_mp3s = best_match
                
                if matched_mp3s:
                    matches.append({
                        'txt_name': f,
                        'txt_path': os.path.join(root, f),
                        'mp3_samples': matched_mp3s[:2]
                    })

    # 3. Ghi log
    print(f"[*] Found {len(matches)} matches with updated algorithm. Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (ALGORITHM V2) - Tổng: {len(matches)}\n")
        log.write("=" * 100 + "\n")
        for m in matches:
            mp3_str = ", ".join(m['mp3_samples'])
            log.write(f"TXT: {m['txt_name']}\n")
            log.write(f"PATH: {m['txt_path']}\n")
            log.write(f"MATCHED MP3: {mp3_str}\n")
            log.write("-" * 50 + "\n")

    # 4. Di chuyển
    print(f"[*] Moving {len(matches)} files...")
    count = 0
    for m in matches:
        try:
            dst = os.path.join(TARGET_DIR, m['txt_name'])
            if os.path.exists(dst): os.remove(dst)
            shutil.move(m['txt_path'], TARGET_DIR)
            count += 1
        except Exception as e:
            print(f"    [ERR] {m['txt_name']}: {e}")

    print(f"\n[DONE] Moved {count} files. Please review {LOG_FILE}")

if __name__ == "__main__":
    main()
