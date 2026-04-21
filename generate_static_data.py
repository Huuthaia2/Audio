import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOMTAT_DIR = os.path.join(BASE_DIR, "Tóm tắt")
RAW_DIR = os.path.join(BASE_DIR, "truyencogiaothao")

CATEGORIES = {
    "1-Mẹ Con": "Mẹ Con",
    "2-Cha Chồng - Con Dâu": "Cha Chồng - Con Dâu",
    "3-Cave": "Cave / Gái Gọi",
    "5-Chị dâu": "Chị Dâu",
    "6-Anh Em - Chị Em": "Anh Em - Chị Em",
    "8-Loạn Luân": "Loạn Luân",
}

def get_title_from_file(fpath, fallback_slug):
    """Đọc tiêu đề có dấu từ nội dung file"""
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            # Chỉ đọc 10 dòng đầu để tìm tiêu đề
            for _ in range(10):
                line = f.readline()
                if not line: break
                line = line.strip()
                # Tìm dòng "TÓM TẮT TRUYỆN: ..."
                match = re.search(r'TÓM TẮT TRUYỆN:\s*(.*)', line, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if title: return title.title()
    except:
        pass
    
    # Fallback: Chuyển slug file thành tên không dấu (như cũ)
    name = re.sub(r'-\d+\.txt$', '', fallback_slug)
    name = name.replace('-', ' ')
    return name.title()

def generate_stories_json():
    stories = []
    for folder, cat_name in CATEGORIES.items():
        path = os.path.join(TOMTAT_DIR, folder)
        if not os.path.isdir(path):
            continue
        for fname in sorted(os.listdir(path)):
            if not fname.endswith('.txt'):
                continue
            fpath = os.path.join(path, fname)
            size = os.path.getsize(fpath)
            
            raw_fname = fname
            raw_path = os.path.join(RAW_DIR, folder, raw_fname)
            has_raw = os.path.exists(raw_path)
            
            stories.append({
                "id": f"{folder}/{fname}",
                "file": fname,
                "folder": folder,
                "category": cat_name,
                "title": get_title_from_file(fpath, fname),
                "size": size,
                "has_raw": has_raw,
            })
    
    output_path = os.path.join(BASE_DIR, "stories.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(stories, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã tạo {output_path} với {len(stories)} truyện.")

if __name__ == "__main__":
    generate_stories_json()
