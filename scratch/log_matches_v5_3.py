import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

STOP_WORDS = {"truyen", "sex", "loan-luan", "ll", "ntr", "llntr", "audio", "cau-chuyen", "tinh-yeu", "chuyen", "tap"}

def extract_part(slug):
    # Tìm các dấu hiệu về phần: phan-2, quyen-1, v2, p3, hoặc số đứng lẻ loi ở cuối -2
    # Ưu tiên tìm các từ khóa đi kèm số trước
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match:
        return f"p{match.group(2)}"
    
    # Tìm số đứng lẻ loi ở cuối slug (ví dụ: duc-vong-gia-dinh-2)
    match_end = re.search(r'-(\d+)$', slug)
    if match_end:
        return f"p{match_end.group(1)}"
        
    return "p1" # Mặc định

def clean_slug_final(slug):
    # 1. Trích xuất thông tin phần
    part_info = extract_part(slug)
    
    # 2. Xóa các tiền tố rác
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    
    # 3. Xóa các hậu tố rác và thông tin phần đã trích xuất
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug) # Xóa số lẻ ở cuối
    
    # 4. Xóa stopwords
    for tag in STOP_WORDS:
        slug = slug.replace(tag, "")
        
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part_info

def main():
    # 1. Load và phân loại MP3
    print("[*] Mapping MP3 files with V5.3 logic...")
    mp3_map = {} # (base_slug, part) -> [original_names]
    
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m_orig = line.strip()
            if not m_orig: continue
            
            # Xử lý tên MP3 để lấy slug sạch
            m_clean = m_orig.lower().replace(".mp3", "")
            m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
            
            base, part = clean_slug_final(m_clean)
            key = (base, part)
            if key not in mp3_map: mp3_map[key] = []
            mp3_map[key].append(m_orig)

    # 2. Quét file Text
    matches = []
    print("[*] Scanning text files...")
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                # Lấy tên file Text sạch
                t_clean = re.sub(r'(-\d+)?\.txt$', '', f.lower())
                t_base, t_part = clean_slug_final(t_clean)
                
                matched_origs = []
                
                # Ưu tiên 1: Khớp chính xác (base, part)
                key = (t_base, t_part)
                if key in mp3_map:
                    matched_origs = mp3_map[key]
                else:
                    # Ưu tiên 2: Khớp mờ tên gốc nhưng PHẢI CÙNG PHẦN
                    for (m_base, m_part), m_origs in mp3_map.items():
                        if t_part == m_part:
                            # Độ tương đồng cao và cùng từ cuối (tránh Hue vs Ho)
                            if SequenceMatcher(None, t_base, m_base).ratio() > 0.9:
                                w1 = t_base.split("-")
                                w2 = m_base.split("-")
                                if w1 and w2 and w1[-1] == w2[-1]:
                                    matched_origs = m_origs
                                    break
                
                if matched_origs:
                    matches.append({
                        'txt_name': f,
                        'txt_path': os.path.join(root, f),
                        'mp3_samples': matched_origs[:2]
                    })

    # 3. Ghi log
    print(f"[*] Found {len(matches)} matches. Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (STRICT V5.3) - Tổng: {len(matches)}\n")
        log.write("=" * 100 + "\n")
        for m in matches:
            mp3_str = ", ".join(m['mp3_samples'])
            log.write(f"TXT: {m['txt_name']}\n")
            log.write(f"PATH: {m['txt_path']}\n")
            log.write(f"MATCHED MP3: {mp3_str}\n")
            log.write("-" * 50 + "\n")

    print(f"\n[DONE] Log updated. Total: {len(matches)} matches. Review {LOG_FILE}")

if __name__ == "__main__":
    main()
