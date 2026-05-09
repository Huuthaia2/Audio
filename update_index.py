import os
import json
import re

ROOT_DIR = r"c:\Users\Windows\Documents\MEGA\Audio"
TRUYEN_DIR = os.path.join(ROOT_DIR, "truyencogiaothao")
TEXT_MP3_DIR = os.path.join(ROOT_DIR, "Text Mp3")
TOM_TAT_DIR = os.path.join(ROOT_DIR, "Tóm tắt")
OUTPUT_JSON = os.path.join(ROOT_DIR, "stories.json")

# Mapping Text Mp3 folders to categories
FOLDER_MAPPING = {
    "AnhChi": "6-Anh Em - Chị Em",
    "BcNd": "2-Cha Chồng - Con Dâu",
    "BsiYta": "15-Y Tá - Bác Sĩ",
    "Cave": "3-Cave",
    "Cd": "5-Chị dâu",
    "Hx": "7-Hàng xóm",
    "Mb": "12-Máy Bay",
    "MeBan": "9-Mẹ bạn",
    "MeVo": "10-Mẹ vợ",
    "NgoaiT": "14-Ngoại Tình",
    "Ntr": "14-Ngoại Tình",
    "ll": "8-Loạn Luân",
    "ll2": "8-Loạn Luân",
    "Short": "18-Chuyện cũ",
    "Long": "Truyện dài",
    "M3": "1-Mẹ Con",
    "M4": "1-Mẹ Con",
    "M5": "1-Mẹ Con",
}

def clean_title(filename):
    # Remove extension
    name = os.path.splitext(filename)[0]
    # Remove chapter suffixes like -0001, +chuong 0001, -part 1, +123
    # Matches + or - followed by optional 'chuong'/'part'/'chapter' and then digits
    name = re.sub(r'[\-\+](chuong|part|chapter|chương)?\s*\d+.*$', '', name, flags=re.IGNORECASE)
    # Remove any trailing numbers
    name = re.sub(r'-\d+$', '', name)
    name = re.sub(r'\+\d+$', '', name)
    
    name = name.replace('-', ' ').replace('_', ' ').replace('+', ' ')
    # Remove multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

def extract_title_from_file(filepath, fallback_title):
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(20):  # Check first 20 lines
                line = f.readline()
                if not line: break
                line = line.strip()
                # Look for TITLE: or Tên truyện: or even = TITLE: =
                match = re.search(r'(TITLE|Tiêu đề|Tên truyện|TÊN TRUYỆN)\s*:\s*([^=]*[^=\s])', line, re.IGNORECASE)
                if match:
                    title = match.group(2).strip()
                    if title: return title
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return fallback_title

def get_stories_from_dir(base_path, relative_to):
    stories = []
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith(".txt"):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, relative_to)
                
                # Determine folder and category
                parts = rel_path.split(os.sep)
                if len(parts) < 2: continue
                
                folder = parts[0]
                category = folder
                
                # If it's from Text Mp3, map the category
                if "Text Mp3" in relative_to:
                    category = FOLDER_MAPPING.get(folder, folder)

                # Clean category name (remove leading numbers if any)
                clean_cat = re.sub(r'^\d+-', '', category)
                
                fallback = clean_title(f)
                real_title = extract_title_from_file(full_path, fallback)

                stories.append({
                    "id": rel_path.replace("\\", "/"),
                    "file": f,
                    "folder": folder,
                    "category": clean_cat,
                    "title": real_title,
                    "size": os.path.getsize(full_path),
                    "base": os.path.basename(relative_to)
                })
    return stories

def main():
    print("Scanning truyencogiaothao...")
    stories_raw = get_stories_from_dir(TRUYEN_DIR, TRUYEN_DIR)
    
    print("Scanning Text Mp3...")
    stories_mp3 = get_stories_from_dir(TEXT_MP3_DIR, TEXT_MP3_DIR)
    
    all_stories = stories_raw + stories_mp3
    
    # Check for summaries
    for s in all_stories:
        sum_path = os.path.join(TOM_TAT_DIR, s["id"])
        s["has_raw"] = True
        s["has_sum"] = os.path.exists(sum_path)

    # Dedup by id? No, id is relative to base.
    # We should probably use a unique id.
    for s in all_stories:
        s["uid"] = f"{s['base']}/{s['id']}"

    print(f"Total stories found: {len(all_stories)}")
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_stories, f, ensure_ascii=False, indent=2)
    
    print(f"Updated {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
