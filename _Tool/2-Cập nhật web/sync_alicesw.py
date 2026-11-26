# Đồng bộ nguồn truyện alicesw (Documents/zzz/alicesw/downloaded/translated) sang Truyện/4-alicesw (file nén gzip:
# 2.1 GB chữ còn ~600 MB). Tạm để chung repo Audio (anh Thai chốt 2026-11-25); sau tách repo riêng nếu Pages quá tải.
# - Mỗi truyện ⇒ Truyện/4-alicesw/<id>.txt.gz (id = số trong link Nguồn alicesw ⇒ uid ổn định khi file gốc đổi tên)
# - Chỉ nén lại file gốc đã đổi (so size + mtime); truyện không còn cả bản dịch lẫn bản gốc (origin/) ⇒ xoá .gz
# - Ghi Truyện/4-alicesw/index.json: {id: {title, author, tags, ch, done, size, t, file, src_size, src_mtime}} cho update_index.py
import os
import re
import sys
import json
import gzip
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # _Tool/2-Cập nhật web/ -> gốc
SRC_DIR = os.path.join(os.path.dirname(ROOT_DIR), "alicesw", "downloaded", "translated")
ORIGIN_DIR = os.path.join(os.path.dirname(SRC_DIR), "origin")  # bản gốc tiếng Trung (id còn ở đây ⇒ không xoá .gz)
OUT_DIR = os.path.join(ROOT_DIR, "Truyện", "4-alicesw")
TXT_DIR = OUT_DIR
INDEX = os.path.join(OUT_DIR, "index.json")
SKIP_TAGS = {"R-18", "Tiếng Trung"}  # không phải thể loại (anh Thai chốt 2026-11-25)
# Tag + tên tác giả trong file bị Google dịch nửa vời ("榨 Tinh", "Vô 聊 Nhật Nhật 陈") ⇒ từ điển do AI dịch lại
# (anh Thai yêu cầu 2026-11-26): {"tags": {gốc: mới}, "authors": {gốc: mới}}. Tag / tên mới chưa có trong từ điển ⇒ giữ nguyên
# và in ra cuối lần chạy để bổ sung.
DICH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alicesw_dich.json")


def load_dich():
    try:
        with open(DICH, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("tags", {}), d.get("authors", {})
    except FileNotFoundError:
        return {}, {}


def apply_dich(info, tmap, amap, missing, tvals):
    tags = []
    for t in info["tags"]:
        n = tmap.get(t)
        if n is None:
            if t not in tvals:  # đã là tag dịch rồi (mục cũ giữ lại từ index) thì không báo thiếu
                missing["tags"].add(t)
            n = t
        # Tag gộp "Sa đọa / Huấn luyện" ⇒ tách thành từng tag riêng (lọc được từng cái)
        for p in n.split(" / "):
            p = p.strip()
            if p and p not in SKIP_TAGS and p not in tags:
                tags.append(p)
    info["tags"] = tags
    a = info.get("author", "")
    if a in amap:
        info["author"] = amap[a]
    elif a and a not in amap.values():
        missing["authors"].add(a)


def field(head, name):
    m = re.search(r"^\s*" + name + r"\s*:\s*(.+?)\s*$", head, re.M)
    return m.group(1) if m else ""


def read_info(path, folder):
    with open(path, encoding="utf-8", errors="replace") as f:
        head = f.read(4000)
    m = re.search(r"alicesw\.com/novel/(\d+)", head)
    if not m:
        return None
    # Tên = dòng đầu tiên có chữ sau dòng "=====" mở đầu khối thông tin
    title = ""
    for line in head.splitlines():
        t = line.strip()
        if t and not t.startswith("="):
            title = t
            break
    tags = []
    for t in field(head, "Tag").split(","):
        t = t.strip().lstrip("#").strip()
        if t and t not in SKIP_TAGS and t not in tags:
            tags.append(t)
    if folder and folder not in tags:  # thư mục con Lục Mẫu / NTR cũng là 1 tag
        tags.append(folder)
    ch = re.search(r"\d+", field(head, "Chương"))
    st = os.stat(path)
    return {
        "id": m.group(1),
        "title": title or os.path.splitext(os.path.basename(path))[0],
        "author": field(head, "Tác giả"),
        "tags": tags,
        "ch": int(ch.group()) if ch else 0,
        "done": "hoàn thành" in field(head, "Tình trạng").lower(),
        "t": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
        "file": os.path.relpath(path, SRC_DIR).replace("\\", "/"),
        "src_size": st.st_size,
        "src_mtime": int(st.st_mtime),
    }


def origin_novel_ids():
    """id mọi truyện còn trong alicesw/downloaded/origin (đọc link Nguồn ở đầu file). None = không thấy thư mục."""
    if not os.path.isdir(ORIGIN_DIR):
        return None
    ids = set()
    for name in os.listdir(ORIGIN_DIR):
        if not name.endswith(".txt"):
            continue
        with open(os.path.join(ORIGIN_DIR, name), encoding="utf-8", errors="replace") as f:
            m = re.search(r"alicesw\.com/novel/(\d+)", f.read(2000))
        if m:
            ids.add(m.group(1))
    return ids


def main():
    if not os.path.isdir(SRC_DIR):
        print(f"[!] Không thấy thư mục nguồn: {SRC_DIR}")
        return 1
    os.makedirs(TXT_DIR, exist_ok=True)
    try:
        with open(INDEX, encoding="utf-8") as f:
            old = json.load(f)
    except FileNotFoundError:
        old = {}

    # 1) Đọc thông tin mọi file; trùng id ⇒ giữ bản nhiều chương hơn (bằng nhau ⇒ file mới hơn)
    best, total, no_id = {}, 0, 0
    for root, _, files in os.walk(SRC_DIR):
        rel = os.path.relpath(root, SRC_DIR)
        folder = "" if rel == "." else rel.split(os.sep)[0]
        for name in files:
            if not name.endswith(".txt"):
                continue
            total += 1
            info = read_info(os.path.join(root, name), folder)
            if not info:
                no_id += 1
                continue
            cur = best.get(info["id"])
            if not cur or (info["ch"], info["src_mtime"]) > (cur["ch"], cur["src_mtime"]):
                best[info["id"]] = info
    print(f"[*] {total} file ⇒ {len(best)} truyện (bỏ {total - len(best) - no_id} file trùng, {no_id} file không có id)")

    # Dịch lại tag + tác giả theo từ điển (trước bước gộp hoa / thường)
    tmap, amap = load_dich()
    tvals = set(tmap.values())
    missing = {"tags": set(), "authors": set()}
    for info in best.values():
        apply_dich(info, tmap, amap, missing, tvals)

    # Tag chỉ khác hoa / thường ("NTR" / "Ntr") ⇒ gộp, lấy cách viết phổ biến nhất (tránh 2 chip giống nhau khi lọc)
    forms = {}
    for info in best.values():
        for t in info["tags"]:
            forms.setdefault(t.lower(), {}).setdefault(t, 0)
            forms[t.lower()][t] += 1
    canon = {k: max(v, key=v.get) for k, v in forms.items()}
    for info in best.values():
        tags = []
        for t in info["tags"]:
            c = canon[t.lower()]
            if c not in tags:
                tags.append(c)
        info["tags"] = tags

    # 2) Nén file đổi / mới
    changed = 0
    for i, (nid, info) in enumerate(sorted(best.items())):
        gz = os.path.join(TXT_DIR, nid + ".txt.gz")
        o = old.get(nid)
        if o and o.get("src_size") == info["src_size"] and o.get("src_mtime") == info["src_mtime"] and os.path.exists(gz):
            info["size"] = o["size"]
            continue
        with open(os.path.join(SRC_DIR, info["file"]), "rb") as f:
            data = f.read()
        # mtime cố định = 0 ⇒ nén lại cùng nội dung ra file y hệt (git không thấy đổi)
        with open(gz, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", compresslevel=9, mtime=0) as z:
                z.write(data)
        info["size"] = len(data)
        changed += 1
        if changed % 100 == 0:
            print(f"    -> đã nén {changed} truyện...")

    # 3) Xoá .gz của truyện không còn. Không thấy bản dịch lần quét này (bộ dịch đang ghi dở / dịch lỗi / đổi tên)
    #    nhưng id còn trong origin/ ⇒ giữ .gz + mục index cũ; chỉ xoá khi id không còn cả trong origin/
    origin_ids = origin_novel_ids()
    removed, kept = 0, 0
    for name in os.listdir(TXT_DIR):
        nid = name[:-7]
        if not name.endswith(".txt.gz") or nid in best:
            continue
        if origin_ids is None or nid in origin_ids:
            if nid in old:
                best[nid] = {"id": nid, **old[nid]}
                apply_dich(best[nid], tmap, amap, missing, tvals)
            kept += 1
        else:
            os.remove(os.path.join(TXT_DIR, name))
            removed += 1
    if kept:
        print(f"[*] Giữ {kept} truyện chưa có bản dịch lần này (id còn trong origin/)")

    index = {nid: {k: v for k, v in info.items() if k != "id"} for nid, info in sorted(best.items())}
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    gz_mb = sum(os.path.getsize(os.path.join(TXT_DIR, n)) for n in os.listdir(TXT_DIR) if n.endswith(".txt.gz")) / 1e6
    print(f"[OK] alicesw: {len(best)} truyện | nén mới {changed} | xoá {removed} | tổng .gz {gz_mb:.0f} MB")
    if missing["tags"] or missing["authors"]:
        print(f"[!] Chưa có trong alicesw_dich.json (giữ nguyên bản Google): {len(missing['tags'])} tag, "
              f"{len(missing['authors'])} tác giả — vd: {', '.join(sorted(missing['tags'])[:8])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
