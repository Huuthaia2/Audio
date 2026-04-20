import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

STOP_WORDS = {"truyen", "sex", "audio", "tap", "loan-luan", "ll", "ntr", "llntr", "cau-chuyen", "tinh-yeu", "chuyen"}

def extract_part(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match: return f"p{match.group(2)}"
    match_end = re.search(r'-(\d+)$', slug)
    if match_end: return f"p{match_end.group(1)}"
    return "p1"

def clean_slug_v53(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'^(con-|em-)', '', slug) # V5.3 XÓA
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

def clean_slug_v54(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    # V5.4 KHÔNG XÓA con-, em-
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
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
        
        # Exact match (FAST)
        if (base, part) in mp3_map:
            matches[t_name] = mp3_map[(base, part)][0]
        else:
            # Fuzzy match only if same part
            for (m_base, m_part), m_origs in mp3_map.items():
                if part == m_part:
                    if SequenceMatcher(None, base, m_base).ratio() > 0.95:
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

    print("[*] Running V5.3 Logic...")
    v53 = run_logic(mp3_origs, text_files, clean_slug_v53)
    
    print("[*] Running V5.4 Logic...")
    v54 = run_logic(mp3_origs, text_files, clean_slug_v54)

    added = set(v54.keys()) - set(v53.keys())
    removed = set(v53.keys()) - set(v54.keys())

    print(f"[*] Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (ULTRA STRICT V5.4) - Tổng: {len(v54)}\n")
        log.write(f"So với V5.3: Thêm {len(added)}, Bớt {len(removed)}\n")
        log.write("=" * 100 + "\n")
        if added:
            log.write("\n[+] CÁC FILE MỚI ĐƯỢC THÊM VÀO:\n")
            for a in sorted(added): log.write(f" + {a}\n")
        if removed:
            log.write("\n[-] CÁC FILE BỊ LOẠI BỎ (DO KHÁC PREFIX HOẶC SAI PHẦN):\n")
            for r in sorted(removed): log.write(f" - {r} (Từng khớp với: {v53[r]})\n")
        log.write("\n" + "=" * 100 + "\n")
        log.write("DANH SÁCH CHI TIẾT:\n")
        for t in sorted(v54.keys()):
            log.write(f"TXT: {t}\nMATCHED MP3: {v54[t]}\n" + "-"*30 + "\n")

    print(f"DONE: V5.3: {len(v53)} | V5.4: {len(v54)} | Diff: +{len(added)}/-{len(removed)}")

if __name__ == "__main__":
    main()
