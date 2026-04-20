import os
import re
import shutil

# --- CẤU HÌNH ---
MP3_LIST_FILE = r"d:\z\Audio\_Tool\Audio\all_mp3_files.txt"
TEXT_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
TARGET_DIR = r"d:\z\Audio\_Tool\Audio\zDaCoMp3"
LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
EXCLUDE_DIR = "zzzzLoi"

def get_core_slug_mp3(name):
    # Xóa đuôi .mp3
    name = name.lower().replace(".mp3", "")
    # Xóa các hậu tố phổ biến
    name = re.sub(r'(_\d+|\(\d+\)|\+chuong.*| - copy.*| - Copy.*|\+Chuong.*)$', '', name)
    # Xóa các ký tự đặc biệt ở cuối
    name = name.strip("-_+ ")
    return name

def get_core_slug_txt(name):
    # Xóa đuôi .txt
    name = name.lower().replace(".txt", "")
    # Xóa hậu tố số chương (ví dụ: -0001, -123)
    name = re.sub(r'(-\d+)$', '', name)
    return name

def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    # 1. Load MP3 Slugs and map slug to original name
    mp3_mapping = {}
    with open(MP3_LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            m_name = line.strip()
            if m_name:
                slug = get_core_slug_mp3(m_name)
                if slug not in mp3_mapping:
                    mp3_mapping[slug] = []
                mp3_mapping[slug].append(m_name)

    # 2. Quét file Text và đối chiếu
    matches = []
    for root, dirs, files in os.walk(TEXT_DIR):
        if EXCLUDE_DIR in root:
            continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                txt_slug = get_core_slug_txt(f)
                matched_mp3s = []
                
                # Khớp chính xác core
                if txt_slug in mp3_mapping:
                    matched_mp3s = mp3_mapping[txt_slug]
                else:
                    # Khớp mờ / chứa trong
                    for m_slug, m_names in mp3_mapping.items():
                        if (txt_slug in m_slug or m_slug in txt_slug) and len(txt_slug) > 5:
                            matched_mp3s = m_names
                            break
                
                if matched_mp3s:
                    matches.append({
                        'txt_name': f,
                        'txt_path': os.path.join(root, f),
                        'mp3_samples': matched_mp3s[:2] # Log tối đa 2 file mp3 ví dụ
                    })

    # 3. Ghi log DacCoMp3.txt
    print(f"[*] Found {len(matches)} matches. Writing log to {LOG_FILE}...")
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write(f"DANH SÁCH FILE TEXT ĐÃ CÓ BẢN MP3 (Tổng: {len(matches)})\n")
        log.write("=" * 100 + "\n")
        for m in matches:
            mp3_str = ", ".join(m['mp3_samples'])
            log.write(f"TXT: {m['txt_name']}\n")
            log.write(f"PATH: {m['txt_path']}\n")
            log.write(f"MATCHED MP3: {mp3_str}\n")
            log.write("-" * 50 + "\n")

    # 4. Thực hiện di chuyển
    print(f"[*] Moving files to {TARGET_DIR}...")
    count = 0
    for m in matches:
        try:
            dst = os.path.join(TARGET_DIR, m['txt_name'])
            if os.path.exists(dst):
                os.remove(dst)
            shutil.move(m['txt_path'], TARGET_DIR)
            count += 1
        except Exception as e:
            print(f"    [ERR] Could not move {m['txt_name']}: {e}")

    print(f"\n[DONE] Successfully moved {count} files. Check {LOG_FILE} for details.")

if __name__ == "__main__":
    main()
