import os
import re
import shutil
from difflib import SequenceMatcher

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
TARGET_DIR = r"d:\z\Audio\_Tool\Audio\zDaCoMp3"
MOVE_LOG = r"d:\z\Audio\_Tool\Audio\move_execution.log"
EXCLUDE_DIR = "zzzzLoi"

STOP_WORDS = {"truyen", "sex", "audio", "tap"}

def extract_part(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match: return f"p{match.group(2)}"
    match_end = re.search(r'-(\d+)$', slug)
    if match_end: return f"p{match_end.group(1)}"
    return "p1"

def clean_v55(slug):
    part = extract_part(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    if len(slug) > 10:
        slug_alt = re.sub(r'^(con-|em-)', '', slug)
        if len(slug_alt) > 8: return slug_alt, part
    return slug, part

def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    # 1. Load MP3 Map
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        mp3_origs = [line.strip() for line in f if line.strip()]

    mp3_map = {}
    for m in mp3_origs:
        m_clean = m.lower().replace(".mp3", "")
        m_clean = re.sub(r'(_\d+|\(\d+\)|\+chuong.*|\+Chuong.*| - copy.*| - Copy.*)$', '', m_clean)
        base, part = clean_v55(m_clean)
        key = (base, part)
        if key not in mp3_map: mp3_map[key] = []
        mp3_map[key].append(m)

    # 2. Tìm và Di chuyển
    print("[*] Starting Move Execution (V5.5 logic)...")
    count = 0
    with open(MOVE_LOG, 'w', encoding='utf-8') as log:
        log.write("LOG DI CHUYỂN FILE (V5.5)\n" + "="*50 + "\n")
        
        for root, dirs, files in os.walk(TEXT_DIR):
            if EXCLUDE_DIR in root: continue
            
            # Lấy tên thư mục cha (ví dụ: 1-Mẹ Con)
            parent_folder = os.path.basename(root)
            if parent_folder == "truyencogiaothao": continue # Skip root
            
            for f in files:
                if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                    t_clean = re.sub(r'(-\d+)?\.txt$', '', f.lower())
                    base, part = clean_v55(t_clean)
                    
                    is_match = False
                    if (base, part) in mp3_map:
                        is_match = True
                    else:
                        candidates = [ (mb, mo[0]) for (mb, mp), mo in mp3_map.items() if mp == part ]
                        for mb, mo in candidates:
                            if SequenceMatcher(None, base, mb).ratio() > 0.95:
                                if base.split("-")[-1] == mb.split("-")[-1]:
                                    is_match = True
                                    break
                    
                    if is_match:
                        # Thực hiện di chuyển
                        src_path = os.path.join(root, f)
                        dest_folder = os.path.join(TARGET_DIR, parent_folder)
                        if not os.path.exists(dest_folder):
                            os.makedirs(dest_folder)
                        
                        dest_path = os.path.join(dest_folder, f)
                        
                        try:
                            shutil.move(src_path, dest_path)
                            log.write(f"MOVED: {f} -> {parent_folder}\n")
                            count += 1
                        except Exception as e:
                            log.write(f"ERROR: {f} ({str(e)})\n")

    print(f"\n[DONE] Successfully moved {count} files to {TARGET_DIR}")
    print(f"Details recorded in {MOVE_LOG}")

if __name__ == "__main__":
    main()
