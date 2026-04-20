import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

STOP_WORDS = {"truyen", "sex", "audio", "tap"}

def extract_part(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match: return f"p{match.group(2)}"
    match_end = re.search(r'-(\d+)$', slug)
    if match_end: return f"p{match_end.group(1)}"
    return "p1"

# LOGIC V5.3 (Cũ)
def clean_slug_v53(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'^(con-|em-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

# LOGIC V5.5 (Mới - Có lọc độ dài)
def clean_slug_v55(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    
    # Nếu tên đủ dài (>10), mới cho phép bỏ con- / em-
    if len(slug) > 10:
        slug_alt = re.sub(r'^(con-|em-)', '', slug)
        if len(slug_alt) > 8:
            return slug_alt, part
            
    return slug, part

def run_logic(mp3_origs, text_files, clean_func):
    mp3_map = {}
    for m in mp3_origs:
        m_clean = m.lower().replace(".mp3", "")
        m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
        base, part = clean_func(m_clean)
        key = (base, part)
        if key not in mp3_map: mp3_map[key] = []
        mp3_map[key].append(m)

    matches = {}
    for t_name, t_root in text_files:
        t_clean = re.sub(r'(-\d+)?\.txt$', '', t_name.lower())
        base, part = clean_func(t_clean)
        if (base, part) in mp3_map:
            matches[t_name] = mp3_map[(base, part)][0]
        else:
            for (m_base, m_part), m_origs in mp3_map.items():
                if part == m_part:
                    if SequenceMatcher(None, base, m_base).ratio() > 0.95:
                        if base.split("-")[-1] == m_base.split("-")[-1]:
                            matches[t_name] = m_origs[0]
                            break
    return matches

def main():
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        mp3_origs = [line.strip() for line in f if line.strip()]

    text_files = []
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                text_files.append((f, root))

    print("[*] Running V5.3 vs V5.5...")
    v53 = run_logic(mp3_origs, text_files, clean_slug_v53)
    v55 = run_logic(mp3_origs, text_files, clean_slug_v55)

    removed = set(v53.keys()) - set(v55.keys())
    added = set(v55.keys()) - set(v53.keys())

    print(f"[*] Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (HYBRID V5.5) - Tổng: {len(v55)}\n")
        log.write(f"So với V5.3: Thêm {len(added)}, Bớt {len(removed)}\n")
        log.write("=" * 100 + "\n")
        
        if removed:
            log.write("\n[-] CÁC FILE ĐÃ BỊ LOẠI BỎ (DO Tên quá ngắn - Dễ sai nghĩa):\n")
            for r in sorted(removed):
                log.write(f" - {r} (Từng khớp với: {v53[r]})\n")
        
        log.write("\n" + "=" * 100 + "\n")
        log.write("DANH SÁCH CHI TIẾT HIỆN TẠI:\n")
        for t in sorted(v55.keys()):
            log.write(f"TXT: {t}\nMATCHED MP3: {v55[t]}\n" + "-"*30 + "\n")

    print(f"DONE: V5.5: {len(v55)} | Removed: {len(removed)}")

if __name__ == "__main__":
    main()
