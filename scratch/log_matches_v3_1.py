import os
import re
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

def clean_slug(slug):
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = slug.replace("loan-luan", "").replace("llntr", "").replace("ll", "").replace("ntr", "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug

def get_core_slug_mp3(name):
    name = name.lower().replace(".mp3", "")
    name = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', name)
    name = name.strip("-_+ ")
    return clean_slug(name)

def get_core_slug_txt(name):
    name = name.lower().replace(".txt", "")
    name = re.sub(r'(-\d+)$', '', name)
    return clean_slug(name)

def main():
    # 1. Load MP3 Slugs
    mp3_mapping = {}
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m_name = line.strip()
            if m_name:
                slug = get_core_slug_mp3(m_name)
                if slug not in mp3_mapping:
                    mp3_mapping[slug] = []
                mp3_mapping[slug].append(m_name)

    mp3_slug_list = list(mp3_mapping.keys())
    # Pre-tokenize for faster overlap check
    mp3_tokens = {slug: set(slug.split("-")) for slug in mp3_slug_list}

    # 2. Quét file Text
    matches = []
    print("[*] Scanning text files (Optimized V3.1)...")
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root: continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                txt_slug = get_core_slug_txt(f)
                txt_set = set(txt_slug.split("-"))
                matched_mp3s = []
                
                # Ưu tiên khớp chính xác
                if txt_slug in mp3_mapping:
                    matched_mp3s = mp3_mapping[txt_slug]
                else:
                    # Khớp mờ nhanh
                    best_match = None
                    highest_ratio = 0
                    
                    for m_slug in mp3_slug_list:
                        m_set = mp3_tokens[m_slug]
                        # Heuristic: ít nhất một nửa số từ phải giống nhau
                        common = txt_set.intersection(m_set)
                        if len(common) >= min(len(txt_set), len(m_set)) * 0.6:
                            ratio = SequenceMatcher(None, txt_slug, m_slug).ratio()
                            if ratio > highest_ratio and ratio > 0.75:
                                highest_ratio = ratio
                                best_match = mp3_mapping[m_slug]
                        # Trường hợp đặc biệt: chứa nhau hoàn toàn
                        elif (txt_slug in m_slug or m_slug in txt_slug) and len(common) >= 3:
                            ratio = SequenceMatcher(None, txt_slug, m_slug).ratio()
                            if ratio > highest_ratio:
                                highest_ratio = ratio
                                best_match = mp3_mapping[m_slug]
                    
                    if best_match:
                        matched_mp3s = best_match
                
                if matched_mp3s:
                    matches.append({
                        'txt_name': f,
                        'txt_path': os.path.join(root, f),
                        'mp3_samples': matched_mp3s[:2]
                    })

    # 3. Ghi log
    print(f"[*] Found {len(matches)} matches. Writing log...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH ĐỐI CHIẾU (ADVANCED V3.1) - Tổng: {len(matches)}\n")
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
