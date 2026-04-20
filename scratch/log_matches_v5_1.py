import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

STOP_WORDS = {"truyen", "sex", "loan-luan", "ll", "ntr", "llntr", "audio", "cau-chuyen", "tinh-yeu", "chuyen"}

def extract_part(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?)(\d+)', slug)
    if match: return f"part{match.group(2)}"
    return "part1"

def clean_slug_strict(slug):
    part_info = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?)\d+', '', slug)
    for tag in STOP_WORDS:
        slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part_info

def main():
    # 1. Pre-calculate MP3 Slugs
    print("[*] Pre-calculating MP3 slugs...")
    mp3_data = []
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m_name = line.strip()
            if m_name:
                m_no_ext = m_name.lower().replace(".mp3", "")
                m_no_ext = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_no_ext)
                base, part = clean_slug_strict(m_no_ext)
                mp3_data.append((base, part, m_name))

    # 2. Quét file Text
    matches = []
    print("[*] Scanning text files (Optimized V5.1)...")
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                txt_no_ext = re.sub(r'(-\d+)?\.txt$', '', f.lower())
                txt_base, txt_part = clean_slug_strict(txt_no_ext)
                
                matched_mp3s = []
                for m_base, m_part, m_orig in mp3_data:
                    # Ràng buộc 1: Phải cùng Phần
                    if txt_part != m_part:
                        continue
                        
                    # Ràng buộc 2: Tên gốc phải khớp
                    is_match = False
                    if txt_base == m_base:
                        is_match = True
                    elif SequenceMatcher(None, txt_base, m_base).ratio() > 0.95:
                        is_match = True
                    
                    # Ràng buộc 3: Kiểm tra hậu tố tên (tránh nhầm Hue vs Ho)
                    if is_match:
                        w1 = txt_base.split("-")
                        w2 = m_base.split("-")
                        if w1 and w2 and w1[-1] != w2[-1] and len(w1) == len(w2):
                            is_match = False
                            
                    if is_match:
                        matched_mp3s.append(m_orig)
                        if txt_base == m_base: break
                
                if matched_mp3s:
                    matches.append({
                        'txt_name': f,
                        'txt_path': os.path.join(root, f),
                        'mp3_samples': matched_mp3s[:2]
                    })

    # 3. Ghi log
    print(f"[*] Found {len(matches)} matches. Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (STRICT V5.1) - Tổng: {len(matches)}\n")
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
