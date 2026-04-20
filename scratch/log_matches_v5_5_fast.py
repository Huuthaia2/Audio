import os
import re
from difflib import SequenceMatcher

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

def clean_v53(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'^(con-|em-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

def clean_v55(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    
    if len(slug) > 10:
        slug_alt = re.sub(r'^(con-|em-)', '', slug)
        if len(slug_alt) > 8:
            return slug_alt, part
            
    return slug, part

def run_logic_fast(mp3_origs, text_files, clean_func):
    # Pre-map MP3 by (base, part)
    mp3_map = {}
    for m in mp3_origs:
        m_clean = m.lower().replace(".mp3", "")
        m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
        base, part = clean_func(m_clean)
        key = (base, part)
        if key not in mp3_map: mp3_map[key] = []
        mp3_map[key].append(m)

    matches = {}
    for t_name in text_files:
        t_clean = re.sub(r'(-\d+)?\.txt$', '', t_name.lower())
        base, part = clean_func(t_clean)
        
        # 1. Exact match (VERY FAST)
        if (base, part) in mp3_map:
            matches[t_name] = mp3_map[(base, part)][0]
        else:
            # 2. Fuzzy match only for same part
            # Filter mp3_map to only same part
            candidates = [ (mb, mo[0]) for (mb, mp), mo in mp3_map.items() if mp == part ]
            for mb, mo in candidates:
                if SequenceMatcher(None, base, mb).ratio() > 0.95:
                    if base.split("-")[-1] == mb.split("-")[-1]:
                        matches[t_name] = mo
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
                text_files.append(f)

    print("[*] Running logics...")
    v53 = run_logic_fast(mp3_origs, text_files, clean_v53)
    v55 = run_logic_fast(mp3_origs, text_files, clean_v55)

    removed = set(v53.keys()) - set(v55.keys())
    added = set(v55.keys()) - set(v53.keys())

    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (HYBRID V5.5) - Tổng: {len(v55)}\n")
        log.write(f"So với V5.3: Thêm {len(added)}, Bớt {len(removed)}\n")
        log.write("=" * 100 + "\n")
        if removed:
            log.write("\n[-] CÁC FILE ĐÃ BỊ LOẠI BỎ (Do tên ngắn - Dễ sai nghĩa):\n")
            for r in sorted(removed): log.write(f" - {r} (Từng khớp với: {v53[r]})\n")
        log.write("\n" + "=" * 100 + "\n")
        log.write("DANH SÁCH CHI TIẾT HIỆN TẠI:\n")
        for t in sorted(v55.keys()): log.write(f"TXT: {t}\nMATCHED MP3: {v55[t]}\n" + "-"*30 + "\n")

    print(f"DONE. V5.5: {len(v55)}")

if __name__ == "__main__":
    main()
