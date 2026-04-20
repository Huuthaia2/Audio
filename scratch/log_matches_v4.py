import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

# Danh sách từ phổ thông cần bỏ qua hoặc yêu cầu khớp chặt hơn
STOP_WORDS = {"gia-dinh", "truyen", "sex", "loan-luan", "ll", "ntr", "llntr", "audio", "cau-chuyen", "tinh-yeu", "chuyen"}

def clean_slug(slug):
    # Loại bỏ prefix
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    # Loại bỏ tag ở bất kỳ vị trí nào
    slug = slug.replace("loan-luan", "").replace("llntr", "").replace("ll", "").replace("ntr", "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug

def get_core_slug_mp3(name):
    name = name.lower().replace(".mp3", "")
    name = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', name)
    name = name.strip("-_+ ")
    return clean_slug(name)

def get_core_slug_txt(name):
    name = name.lower().replace(".txt", "")
    name = re.sub(r'(-\d+)$', '', name)
    return clean_slug(name)

def is_valid_match(s1, s2):
    if s1 == s2: return True
    if not s1 or not s2: return False
    
    # Tách từ
    w1 = set(s1.split("-"))
    w2 = set(s2.split("-"))
    
    # Loại bỏ stop words để lấy "từ khóa thực sự"
    u1 = w1 - STOP_WORDS
    u2 = w2 - STOP_WORDS
    
    # Nếu không có từ khóa thực sự nào giống nhau, thì không khớp (tránh khớp chỉ bằng "gia-dinh")
    common_unique = u1.intersection(u2)
    if not common_unique:
        return False
        
    # Nếu khớp 100% từ khóa thực sự
    if u1 == u2 and u1:
        return True

    # Nếu một thằng chứa thằng kia và phần chứa là từ khóa thực sự quan trọng
    # Ví dụ: 'dam-loan' vs 'gia-dinh-dam-loan'
    if s1 in s2 or s2 in s1:
        # Kiểm tra xem phần khác biệt có phải là từ quan trọng không
        # Nếu khác nhau chỉ bởi stop words thì ok
        diff = (u1 | u2) - (u1 & u2)
        if not diff: # Chỉ khác nhau stop words
            return True
        # Nếu khác nhau từ quan trọng, yêu cầu độ tương đồng cao
        return SequenceMatcher(None, s1, s2).ratio() > 0.85

    # Fuzzy match cao
    return SequenceMatcher(None, s1, s2).ratio() > 0.9

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
    print("[*] Scanning text files (Strict Unique Keywords V4)...")
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                txt_slug = get_core_slug_txt(f)
                matched_mp3s = []
                
                # Ưu tiên khớp chính xác sau clean
                if txt_slug in mp3_mapping:
                    matched_mp3s = mp3_mapping[txt_slug]
                else:
                    best_match = None
                    highest_ratio = 0
                    for m_slug in mp3_slug_list:
                        if is_valid_match(txt_slug, m_slug):
                            ratio = SequenceMatcher(None, txt_slug, m_slug).ratio()
                            if ratio > highest_ratio:
                                highest_ratio = ratio
                                best_match = mp3_mapping[m_slug]
                    
                    if best_match:
                        matched_mp3s = best_match
                
                if matched_mp3s:
                    matches.append({
                        'txt_name': f,
                        'txt_path': os.path.join(root, f),
                        'mp3_samples': matched_mp3s[:2]
                    })

    # 3. Ghi log
    print(f"[*] Found {len(matches)} matches. Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (UNIQUE KEYWORDS V4) - Tổng: {len(matches)}\n")
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
