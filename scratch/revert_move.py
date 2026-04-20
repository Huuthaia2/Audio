import os
import shutil

LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"
TARGET_DIR = r"d:\z\Audio\_Tool\Audio\zDaCoMp3"

def main():
    if not os.path.exists(LOG_FILE):
        print("Log file not found.")
        return

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find TXT and PATH
    matches = re.findall(r'TXT: (.*?)\nPATH: (.*?)\n', content)
    
    print(f"[*] Reverting {len(matches)} files...")
    count = 0
    for txt_name, txt_original_path in matches:
        current_path = os.path.join(TARGET_DIR, txt_name)
        if os.path.exists(current_path):
            # Ensure target directory exists
            os.makedirs(os.path.dirname(txt_original_path), exist_ok=True)
            try:
                shutil.move(current_path, txt_original_path)
                count += 1
            except Exception as e:
                print(f"    [ERR] Could not revert {txt_name}: {e}")
    
    print(f"\n[DONE] Reverted {count} files.")

if __name__ == "__main__":
    import re
    main()
