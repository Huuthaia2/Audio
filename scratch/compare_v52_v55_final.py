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

# LOGIC V5.2
def clean_v52(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    # V5.2 KHÔNG có logic xử lý tiền tố con-, em- linh hoạt
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

# LOGIC V5.5
def clean_v55(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    
    # Logic V5.5: Chỉ bỏ tiền tố nếu tên đủ dài
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
    for t_name in text_files:
        t_clean = re.sub(r'(-\d+)?\.txt$', '', t_name.lower())
        base, part = clean_func(t_clean)
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
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                text_files.append(f)

    print("[*] Running V5.2 vs V5.5 Comparison...")
    v52 = run_logic(mp3_origs, text_files, clean_v52)
    v55 = run_logic(mp3_origs, text_files, clean_v55)

    kept = set(v52.keys()) & set(v55.keys())
    added = set(v55.keys()) - set(v52.keys())
    removed = set(v52.keys()) - set(v55.keys())

    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"BÁO CÁO ĐỐI CHIẾU LOGIC V5.2 vs V5.5\n")
        log.write(f"Trạng thái: V5.2 ({len(v52)} file) | V5.5 ({len(v55)} file)\n")
        log.write(f"Kết quả: Giữ ({len(kept)}) | Tăng (+{len(added)}) | Giảm (-{len(removed)})\n")
        log.write("=" * 100 + "\n")
        
        if added:
            log.write("\n[+] CÁC FILE TĂNG LÊN (V5.5 Tìm thấy thêm - Do nhận diện tiền tố thông minh):\n")
            for a in sorted(added): log.write(f" + {a} -> {v55[a]}\n")
            
        if removed:
            log.write("\n[-] CÁC FILE GIẢM ĐI (V5.5 Loại bỏ - Do nghi ngờ sai tên ngắn/sai phần):\n")
            for r in sorted(removed): log.write(f" - {r} (Từng khớp với: {v52[r]})\n")

        log.write("\n" + "=" * 100 + "\n")
        log.write("[=] DANH SÁCH GIỮ NGUYÊN (Khớp chuẩn ở cả 2 bản):\n")
        for k in sorted(kept): log.write(f" = {k} -> {v55[k]}\n")

    print(f"DONE. Log generated at {LOG_FILE}")

if __name__ == "__main__":
    main()
