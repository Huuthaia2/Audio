import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
MOVED_DIR = r"d:\z\Audio\_Tool\Audio\zDaCoMp3"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

STOP_WORDS_V4 = {"gia-dinh", "truyen", "sex", "loan-luan", "ll", "ntr", "llntr", "audio", "cau-chuyen", "tinh-yeu", "chuyen"}
STOP_WORDS_V55 = {"truyen", "sex", "audio", "tap"}

def extract_part_v55(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match: return f"p{match.group(2)}"
    match_end = re.search(r'-(\d+)$', slug)
    if match_end: return f"p{match_end.group(1)}"
    return "p1"

def clean_v4(slug):
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = slug.replace("loan-luan", "").replace("llntr", "").replace("ll", "").replace("ntr", "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug

def is_valid_match_v4(s1, s2):
    if s1 == s2: return True
    w1, w2 = set(s1.split("-")), set(s2.split("-"))
    u1, u2 = w1 - STOP_WORDS_V4, w2 - STOP_WORDS_V4
    if not u1.intersection(u2): return False
    if u1 == u2 and u1: return True
    if s1 in s2 or s2 in s1:
        diff = (u1 | u2) - (u1 & u2)
        if not diff: return True
        return SequenceMatcher(None, s1, s2).ratio() > 0.85
    return SequenceMatcher(None, s1, s2).ratio() > 0.9

def clean_v55(slug):
    part = extract_part_v55(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS_V55: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    if len(slug) > 10:
        slug_alt = re.sub(r'^(con-|em-)', '', slug)
        if len(slug_alt) > 8: return slug_alt, part
    return slug, part

def run_v4(mp3_origs, text_files):
    mp3_slugs = []
    for m in mp3_origs:
        m_clean = m.lower().replace(".mp3", "")
        m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
        mp3_slugs.append((clean_v4(m_clean), m))
    matches = {}
    for t_name in text_files:
        t_clean = re.sub(r'(-\d+)?\.txt$', '', t_name.lower())
        t_slug = clean_v4(t_clean)
        for m_slug, m_orig in mp3_slugs:
            if is_valid_match_v4(t_slug, m_slug):
                matches[t_name] = m_orig
                break
    return matches

def run_v55(mp3_origs, text_files):
    mp3_map = {}
    for m in mp3_origs:
        m_clean = m.lower().replace(".mp3", "")
        m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
        base, part = clean_v55(m_clean)
        key = (base, part)
        if key not in mp3_map: mp3_map[key] = []
        mp3_map[key].append(m)
    matches = {}
    for t_name in text_files:
        t_clean = re.sub(r'(-\d+)?\.txt$', '', t_name.lower())
        base, part = clean_v55(t_clean)
        if (base, part) in mp3_map:
            matches[t_name] = mp3_map[(base, part)][0]
        else:
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
    # Quét cả 2 thư mục
    for d in [TEXT_DIR, MOVED_DIR]:
        if not os.path.exists(d): continue
        for root, dirs, files in os.walk(d):
            if EXCLUDE_DIR in root: continue
            for f in files:
                if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                    text_files.append(f)

    print(f"[*] Total text files found: {len(text_files)}")
    print("[*] Comparing V4 vs V5.5...")
    v4 = run_v4(mp3_origs, text_files)
    v55 = run_v55(mp3_origs, text_files)

    kept = set(v4.keys()) & set(v55.keys())
    added = set(v55.keys()) - set(v4.keys())
    removed = set(v4.keys()) - set(v55.keys())

    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"BÁO CÁO ĐỐI CHIẾU LOGIC V4 vs V5.5 (Đã tính cả file di chuyển)\n")
        log.write(f"Trạng thái: V4 ({len(v4)} file) | V5.5 ({len(v55)} file)\n")
        log.write(f"Kết quả: Giữ ({len(kept)}) | Tăng (+{len(added)}) | Giảm (-{len(removed)})\n")
        log.write("=" * 100 + "\n")
        if added:
            log.write("\n[+] CÁC FILE MỚI (V5.5 Tìm thấy thêm - Chặt chẽ và thông minh hơn):\n")
            for a in sorted(added): log.write(f" + {a} -> {v55[a]}\n")
        if removed:
            log.write("\n[-] CÁC FILE BỊ LOẠI BỎ (V4 Nhận nhầm - V5.5 Đã lọc sạch):\n")
            for r in sorted(removed): log.write(f" - {r} (Từng bị V4 khớp với: {v4[r]})\n")
        log.write("\n" + "=" * 100 + "\n")
        log.write("[=] DANH SÁCH GIỮ NGUYÊN (Khớp chuẩn ở cả 2 bản):\n")
        for k in sorted(kept): log.write(f" = {k} -> {v55[k]}\n")

    print(f"DONE. Report at {LOG_FILE}")

if __name__ == "__main__":
    main()
