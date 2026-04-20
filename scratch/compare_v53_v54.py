import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

STOP_WORDS = {"truyen", "sex", "audio", "tap", "loan-luan", "ll", "ntr", "llntr", "cau-chuyen", "tinh-yeu", "chuyen"}

# --- LOGIC V5.3 ---
def extract_part_v53(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match: return f"p{match.group(2)}"
    match_end = re.search(r'-(\d+)$', slug)
    if match_end: return f"p{match_end.group(1)}"
    return "p1"

def clean_slug_v53(slug):
    part = extract_part_v53(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    # V5.3 XÓA TIỀN TỐ con-, em-
    slug = re.sub(r'^(con-|em-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

# --- LOGIC V5.4 ---
def clean_slug_v54(slug):
    part = extract_part_v53(slug) # Dùng chung hàm extract part
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    # V5.4 KHÔNG XÓA con-, em-
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

def get_matches(mp3_data, text_files, logic_func):
    matches = {}
    for t_name, t_root in text_files:
        t_clean = re.sub(r'(-\d+)?\.txt$', '', t_name.lower())
        t_base, t_part = logic_func(t_clean)
        
        for m_base, m_part, m_orig in mp3_data[logic_func]:
            if t_part == m_part:
                if t_base == m_base or SequenceMatcher(None, t_base, m_base).ratio() > 0.95:
                    matches[t_name] = m_orig
                    break
    return matches

def main():
    # 1. Load MP3 files
    print("[*] Loading MP3 data...")
    mp3_origs = []
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        mp3_origs = [line.strip() for line in f if line.strip()]

    mp3_data = {
        clean_slug_v53: [],
        clean_slug_v54: []
    }
    for m in mp3_origs:
        m_clean = m.lower().replace(".mp3", "")
        m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
        
        for logic in mp3_data:
            base, part = logic(m_clean)
            mp3_data[logic].append((base, part, m))

    # 2. Quét file Text
    print("[*] Scanning text files...")
    text_files = []
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                text_files.append((f, root))

    # 3. Chạy cả 2 logic
    print("[*] Running Logic V5.3...")
    matches_v53 = get_matches(mp3_data, text_files, clean_slug_v53)
    
    print("[*] Running Logic V5.4...")
    matches_v54 = get_matches(mp3_data, text_files, clean_slug_v54)

    # 4. So sánh
    added = set(matches_v54.keys()) - set(matches_v53.keys())
    removed = set(matches_v53.keys()) - set(matches_v54.keys())

    # 5. Ghi log
    print(f"[*] Writing detailed log to {LOG_FILE}...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (ULTRA STRICT V5.4) - Tổng: {len(matches_v54)}\n")
        log.write(f"So với V5.3: Thêm {len(added)}, Bớt {len(removed)}\n")
        log.write("=" * 100 + "\n")
        
        if added:
            log.write("\n[+] CÁC FILE MỚI ĐƯỢC THÊM VÀO:\n")
            for a in added: log.write(f" + {a}\n")
            
        if removed:
            log.write("\n[-] CÁC FILE BỊ LOẠI BỎ (DO SAI PREFIX HOẶC SAI PHẦN):\n")
            for r in removed: log.write(f" - {r} (Từng khớp với: {matches_v53[r]})\n")
            
        log.write("\n" + "=" * 100 + "\n")
        log.write("DANH SÁCH CHI TIẾT KHỚP HIỆN TẠI:\n")
        for t_name, m_name in matches_v54.items():
            log.write(f"TXT: {t_name}\nMATCHED MP3: {m_name}\n" + "-"*30 + "\n")

    print(f"\n[DONE] Comparison complete.")
    print(f"V5.3: {len(matches_v53)} matches")
    print(f"V5.4: {len(matches_v54)} matches")
    print(f"Diff: +{len(added)} / -{len(removed)}")

if __name__ == "__main__":
    main()
