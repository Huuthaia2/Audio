import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

# Stopwords - những từ ko dùng để xác định tính duy nhất
STOP_WORDS = {"truyen", "sex", "loan-luan", "ll", "ntr", "llntr", "audio", "cau-chuyen", "tinh-yeu", "chuyen"}

def extract_part(slug):
    # Tìm phan-2, quyen-1, v2, p3...
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?)(\d+)', slug)
    if match:
        return f"part{match.group(2)}"
    return "part1" # Mặc định là phần 1 nếu không nói gì

def clean_slug_strict(slug):
    # Lưu lại thông tin phần (phan 2, quyen 1...)
    part_info = extract_part(slug)
    
    # Loại bỏ prefix
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    
    # Loại bỏ thông tin phần để so sánh tên gốc
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?)\d+', '', slug)
    
    # Loại bỏ tag
    for tag in STOP_WORDS:
        slug = slug.replace(tag, "")
        
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part_info

def is_valid_match_v5(txt_name, mp3_name):
    # Lấy slug và part của cả 2
    txt_base, txt_part = clean_slug_strict(txt_name)
    mp3_base, mp3_part = clean_slug_strict(mp3_name)
    
    # 1. Nếu khác phần thì KHÔNG khớp
    if txt_part != mp3_part:
        return False
        
    # 2. Nếu tên gốc trùng nhau 100%
    if txt_base == mp3_base:
        return True
        
    # 3. Nếu tên gốc cực kỳ giống nhau (sai sót nhỏ i/y, dấu gạch)
    # Ví dụ: 'loan-luan-ky-su' vs 'loan-luan-ki-su'
    if SequenceMatcher(None, txt_base, mp3_base).ratio() > 0.95:
        return True
        
    # 4. Kiểm tra trường hợp tên chứa nhau nhưng phải đảm bảo không nhầm sang tên khác
    # Ví dụ: 'pha-trinh-em-hue' vs 'pha-trinh-em-ho' -> KHÔNG KHỚP vì 'hue' != 'ho'
    # Quy tắc: Nếu độ dài chênh lệch ít mà phần đuôi khác hẳn thì ko khớp
    words1 = txt_base.split("-")
    words2 = mp3_base.split("-")
    if len(words1) > 0 and len(words2) > 0:
        if words1[-1] != words2[-1] and len(words1) == len(words2):
            return False

    return False

def main():
    # 1. Load MP3 Slugs
    mp3_mapping = {}
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m_name = line.strip()
            if m_name:
                # Pre-clean for mapping
                mp3_mapping[m_name] = m_name # Store original names

    mp3_names = list(mp3_mapping.keys())

    # 2. Quét file Text
    matches = []
    print("[*] Scanning text files (Strict Parts & Names V5)...")
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                # Lấy tên file ko đuôi
                txt_name_no_ext = re.sub(r'(-\d+)?\.txt$', '', f.lower())
                
                matched_mp3s = []
                # So sánh với từng mp3
                for m_name in mp3_names:
                    mp3_name_no_ext = m_name.lower().replace(".mp3", "")
                    # Xử lý các hậu tố mp3 phức tạp
                    mp3_name_no_ext = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', mp3_name_no_ext)
                    
                    if is_valid_match_v5(txt_name_no_ext, mp3_name_no_ext):
                        matched_mp3s.append(m_name)
                        # Nếu tìm thấy khớp 100% thì dừng luôn cho nhanh
                        if txt_name_no_ext == mp3_name_no_ext:
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
        log.write(f"DANH SÁCH ĐỐI CHIẾU (STRICT V5) - Tổng: {len(matches)}\n")
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
