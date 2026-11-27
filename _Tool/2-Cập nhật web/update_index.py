import os
import json
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # _Tool/2-Cập nhật web/ -> gốc
# Thư mục gộp: Truyện/{1-Text Mp3, 2-truyencogiaothao, 3-Tóm tắt/{1-Text Mp3, 2-truyencogiaothao}}
# Mỗi nguồn: (tên nguồn — giữ làm tiền tố uid để không mất tiến độ đọc cũ, thư mục truyện, thư mục tóm tắt)
SOURCES = [
    ("truyencogiaothao", "Truyện/2-truyencogiaothao", "Truyện/3-Tóm tắt/2-truyencogiaothao"),
    ("Text Mp3", "Truyện/1-Text Mp3", "Truyện/3-Tóm tắt/1-Text Mp3"),
]
OUTPUT_JSON = os.path.join(ROOT_DIR, "stories.json")
# Thông tin truyện truyencogiaothao do tool tự cập nhật ghi (_Tool/1-Tải truyện/update_truyencogiaothao.py)
META_JSON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "1-Tải truyện", "giaothao_meta.json")
# Nguồn alicesw: file nén + danh sách do sync_alicesw.py ghi (tạm chung repo Audio, sau có thể tách repo riêng)
ALICE_BASE = "Truyện/4-alicesw"
ALICE_INDEX = os.path.join(ROOT_DIR, ALICE_BASE, "index.json")
EXTRA_SOURCES = [("18av", "Truyện/5-18av"), ("fsnovel", "Truyện/6-fsnovel"), ("langyou", "Truyện/7-langyou"), ("sosing", "Truyện/8-sosing")]
# Bảng gộp file Text Mp3 (ten_1/_2/... ⇒ ten.txt), ghi bởi _Tool/3-Làm sạch text/gop_file_text_mp3.py
MERGE_MAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "3-Làm sạch text", "gop_file_map.json")

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
        # Bỏ zDaCoMp3 (đã có mp3) và zzzzLoi (file lỗi) — trước khi gộp 2 thư mục này cũng không được index
        dirs[:] = [d for d in dirs if not d.startswith("z")]
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
                })
    return stories

# ---- Đếm chương THẬT (y hệt cách web chia chương trong reader.js: splitIntoChapters / splitByRule / autoSplit) ----
# Trước đây web đoán số chương từ số cuối tên file ⇒ truyện gộp (không còn số) thành "1 phần", "nghe-phong-quyen-3" thành
# "3 chương". Kết quả đếm lưu theo (size, mtime) ⇒ lần sau chỉ đếm file đã đổi.
CH_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chapter_cache.json")
RE_RULE = re.compile(r"^─{10,}\s*$", re.M)
RE_MARK = re.compile(r"^={3,}\s*(Chương|Phần|Hồi|Quyển|Tập)\b", re.I)
# KHÔNG dùng re.I: Python coi "s" ≈ "ſ" (U+017F, nằm trong dải chữ có dấu) ⇒ "Chương sau ..." thành tiêu đề chương,
# trình duyệt thì không ⇒ tự ghi hoa / thường cho giống web
RE_CHAP = re.compile(r"^[Cc][Hh][Ưư][Ơơ][Nn][Gg]\s+(\d+|[IVXLCDMivxlcdm]+|[À-ỹ]+)")


def _auto_split_count(text):
    # JS đếm độ dài theo UTF-16: emoji (ngoài BMP) = 2 ký tự ⇒ thay bằng 2 ký tự để điểm cắt 5000 khớp với web
    text = re.sub("[\U00010000-\U0010FFFF]", "￿￿", text)
    target, n, rest = 5000, 0, text
    while rest:
        if len(rest) <= target + 1000:
            return n + 1
        i = rest.rfind("\n", 0, target + 1)
        if i < target * 0.7:
            i = rest.rfind(". ", 0, target + 2)  # như lastIndexOf('. ', 5000) của JS: chỗ BẮT ĐẦU ≤ 5000
        if i <= 0:
            i = target
        n += 1
        rest = rest[i:].strip()
    return n


def count_chapters(text):
    lines = text.split("\n")
    if RE_RULE.search(text):  # kiểu alicesw: mỗi chương mở bằng dòng ────
        n, cur = 0, None
        want_title = False
        for line in lines:
            t = line.strip()
            if re.match(r"^─{10,}$", t):
                if cur: n += 1
                cur, want_title = False, True
                continue
            if cur is None or not t: continue
            if want_title: want_title = False; continue
            cur = True
        return max(1, n + (1 if cur else 0))
    has_marks = any(RE_MARK.match(l.strip()) for l in lines)
    n, content, found = 0, False, False
    for line in lines:
        t = line.strip()
        if not t: continue
        if (RE_MARK.match(t) if has_marks else RE_CHAP.match(t)):
            if content: n += 1
            content, found = False, True
        elif not re.match(r"^=+$", t) and not re.match(r"^TITLE:", t, re.I):
            content = True
    n += 1
    if not found and len(text) > 8000:
        return _auto_split_count(text)
    return n


def add_chapter_counts(stories, sources):
    """Ghi "ch" = số chương thật cho truyện chưa có (alicesw đã có sẵn). Đếm bằng chính code web (node dem_chuong.js),
    không có Node ⇒ dùng count_chapters (Python, gần đúng). Lưu theo (size, mtime) ⇒ lần sau chỉ đếm file đổi."""
    import subprocess, tempfile
    try:
        with open(CH_CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    except (FileNotFoundError, ValueError):
        cache = {}
    # Sửa cách chia chương trong reader.js ⇒ mã hàm đổi ⇒ đếm lại hết (trước đây chỉ đếm lại file đổi ⇒ số cũ sai)
    import hashlib
    with open(os.path.join(ROOT_DIR, "reader.js"), encoding="utf-8") as f:
        src_js = f.read()
    ver = hashlib.md5(src_js[src_js.find("function splitIntoChapters"):src_js.find("// Chia 1 đoạn văn")].encode()).hexdigest()[:8]
    todo, rel_of = [], {}
    for st in stories:
        if st.get("ch"):
            continue
        src, rest = st["uid"].split("/", 1)
        rel = sources[src][0] + "/" + rest
        full = os.path.join(ROOT_DIR, rel)
        if not os.path.exists(full):
            continue
        sig = f"{os.path.getsize(full)}:{int(os.path.getmtime(full))}:{ver}"
        rel_of[st["uid"]] = (rel, sig)
        if cache.get(rel, {}).get("sig") != sig:
            todo.append(rel)
    if todo:
        print(f"Đếm chương {len(todo)} truyện mới / đổi...")
        counts = {}
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
                json.dump(todo, tf, ensure_ascii=False)
            js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dem_chuong.js")
            r = subprocess.run(["node", js, tf.name], capture_output=True, encoding="utf-8", timeout=1800)
            counts = json.loads(r.stdout) if r.returncode == 0 and r.stdout else {}
            os.remove(tf.name)
        except (OSError, ValueError, subprocess.TimeoutExpired):
            counts = {}
        if not counts:
            print("(Không chạy được Node ⇒ đếm bằng Python, có thể lệch 1-2 chương ở truyện không có tiêu đề chương)")
        for rel in todo:
            n = counts.get(rel)
            if n is None:
                with open(os.path.join(ROOT_DIR, rel), encoding="utf-8", errors="replace") as f:
                    n = count_chapters(f.read())
            sig = [s for u, (r_, s) in rel_of.items() if r_ == rel][0]
            cache[rel] = {"sig": sig, "ch": n}
        with open(CH_CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))
    for st in stories:
        if st["uid"] in rel_of:
            st["ch"] = cache[rel_of[st["uid"]][0]]["ch"]


def main():
    # stories.json gọn (anh Thai chốt 2026-11-25): { sources: {tên nguồn: [thư mục truyện, thư mục tóm tắt]}, stories: [...] }
    # Mỗi truyện chỉ giữ trường web cần; id / base / sum_base / has_raw web tự tính lại từ uid + sources (index.html).
    # Truyện truyencogiaothao có thêm: t = ngày chương mới nhất (YYYY-MM-DD), tags = thẻ tag trên trang,
    # was = uid cũ trước khi file đổi tên vì nối chương mới (web chuyển lịch sử nghe + yêu thích sang uid mới)
    try:
        with open(META_JSON, encoding="utf-8") as f:
            meta = json.load(f)
    except FileNotFoundError:
        meta = {}
    try:
        with open(MERGE_MAP, encoding="utf-8") as f:
            merged = json.load(f)
    except FileNotFoundError:
        merged = {}
    all_stories = []
    for name, base, sum_base in SOURCES:
        print(f"Scanning {base}...")
        src_dir = os.path.join(ROOT_DIR, base)
        for s in get_stories_from_dir(src_dir, src_dir):
            st = {
                "uid": f"{name}/{s['id']}",
                "file": s["file"],
                "category": s["category"],
                "title": s["title"],
                "size": s["size"],
                "has_sum": os.path.exists(os.path.join(ROOT_DIR, sum_base, s["id"])),
            }
            # Text Mp3: file gộp từ ten_1.txt, ten_2.txt... (gop_file_text_mp3.py) ⇒ web chuyển lịch sử từ uid cũ
            if st["uid"] in merged:
                st["was"] = merged[st["uid"]]
            m = meta.get(re.sub(r'-\d+\.txt$', '', s["file"])) if name == "truyencogiaothao" else None
            if m:
                if m.get("updated"): st["t"] = m["updated"]
                if m.get("tags"): st["tags"] = m["tags"]
                folder = s["id"].rsplit("/", 1)[0]
                was = [f"{name}/{folder}/{w}" for w in m.get("was", []) if w != s["file"]]
                if was: st["was"] = was
            all_stories.append(st)

    # Nguồn alicesw: file nén ở Truyện/4-alicesw (sync_alicesw.py tạo). Thêm: ch = số chương, author, done = đã hoàn thành
    sources = {name: [base, sum_base] for name, base, sum_base in SOURCES}
    try:
        with open(ALICE_INDEX, encoding="utf-8") as f:
            alice = json.load(f)
    except FileNotFoundError:
        alice = {}
        print(f"(Chưa có {ALICE_BASE}/index.json — chạy sync_alicesw.py trước để có nguồn alicesw)")
    if alice:
        print(f"Scanning alicesw ({len(alice)} truyện)...")
        sources["alicesw"] = [ALICE_BASE, "", {"gz": True}]
        for nid, a in alice.items():
            tags = a["tags"]
            all_stories.append({
                "uid": f"alicesw/{nid}.txt",
                "file": a["file"].rsplit("/", 1)[-1],
                # 📁 trên hàng truyện: tag cụ thể đầu tiên (gần như truyện nào cũng có "Mẹ con")
                "category": next((t for t in tags if t != "Mẹ con"), tags[0] if tags else "alicesw"),
                "title": a["title"],
                "size": a["size"],
                "has_sum": False,
                "t": a["t"],
                "tags": tags,
                "ch": a["ch"],
                "author": a["author"],
                "done": a["done"],
            })

    # 4 nguồn thêm 2026-11-27 (sync_nguon_khac.py tạo, cùng kiểu file nén như alicesw)
    for key, base in EXTRA_SOURCES:
        try:
            with open(os.path.join(ROOT_DIR, base, "index.json"), encoding="utf-8") as f:
                idx = json.load(f)
        except FileNotFoundError:
            continue
        print(f"Scanning {key} ({len(idx)} truyện)...")
        sources[key] = [base, "", {"gz": True}]
        for nid, a in idx.items():
            tags = a["tags"]
            st = {
                "uid": f"{key}/{nid}.txt",
                "file": a["file"].rsplit("/", 1)[-1],
                "category": next((t for t in tags if t != "Mẹ con"), tags[0] if tags else key),
                "title": a["title"],
                "size": a["size"],
                "has_sum": False,
                "t": a["t"],
                "tags": tags,
                "ch": a["ch"] or 1,
            }
            if a.get("author"): st["author"] = a["author"]
            all_stories.append(st)

    add_chapter_counts(all_stories, sources)
    print(f"Total stories found: {len(all_stories)}")

    # Tag ghi 1 lần ở "tags", mỗi truyện chỉ giữ số thứ tự (alicesw ~40 tag / truyện ⇒ file nhẹ đi gần 1 nửa); web tự đổi lại
    tag_list, tag_id = [], {}
    def tag_index(t):
        if t not in tag_id:
            tag_id[t] = len(tag_list)
            tag_list.append(t)
        return tag_id[t]
    for st in all_stories:
        if st.get("tags"):
            st["tags"] = [tag_index(t) for t in st["tags"]]

    data = {"sources": sources, "tags": tag_list, "stories": all_stories}
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    
    print(f"Updated {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
