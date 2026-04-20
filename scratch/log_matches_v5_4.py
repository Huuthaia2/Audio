import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

# Chỉ giữ lại các từ thực sự là "rác" không ảnh hưởng đến nội dung truyện
STOP_WORDS = {"truyen", "sex", "audio", "tap"}

def extract_part(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match: return f"p{match.group(2)}"
    match_end = re.search(r'-(\d+)$', slug)
    if match_end: return f"p{match_end.group(1)}"
    return "p1"

def clean_slug_v54(slug):
    part_info = extract_part(slug)
    
    # KHÔNG xóa con-, em- nữa theo yêu cầu của user
    # CHỈ xóa các từ cực kỳ chung chung
    for tag in STOP_WORDS:
        slug = slug.replace(tag, "")
        
    # Xóa thông tin phần để so sánh tên gốc
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part_info

def main():
    print("[*] Mapping MP3 files with V5.4 (Strict Prefixes & Parts)...")
    mp3_map = {}
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m_orig = line.strip()
            if not m_orig: continue
            
            m_clean = m_orig.lower().replace(".mp3", "")
            m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
            
            base, part = clean_slug_v54(m_clean)
            key = (base, part)
            if key not in mp3_map: mp3_map[key] = []
            mp3_map[key].append(m_orig)

    matches = []
    print("[*] Scanning text files...")
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                t_clean = re.sub(r'(-\d+)?\.txt$', '', f.lower())
                t_base, t_part = clean_slug_v54(t_clean)
                
                matched_origs = []
                key = (t_base, t_part)
                if key in mp3_map:
                    matched_origs = mp3_map[key]
                else:
                    # Khớp mờ cực kỳ hạn chế
                    for (m_base, m_part), m_origs in mp3_map.items():
                        if t_part == m_part:
                            # Tỉ lệ khớp phải cực cao (>95%) để tránh nhầm prefix
                            if SequenceMatcher(None, t_base, m_base).ratio() > 0.95:
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
        log.write(f"DANH SÁCH ĐỐI CHIẾU (ULTRA STRICT V5.4) - Tổng: {len(matches)}\n")
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
