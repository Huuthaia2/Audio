# Đồng bộ 4 nguồn truyện đã dịch trong Documents/zzz/alicesw (anh Thai thêm 2026-11-27) sang web, giống sync_alicesw.py:
#   18av.mm-cg/txt            ⇒ Truyện/5-18av      (bỏ txt/trung = bản trùng)
#   fsnovel.com/downloaded/*  ⇒ Truyện/6-fsnovel   (thư mục con = thể loại)
#   langyou4.langyou895/txt   ⇒ Truyện/7-langyou   (bỏ temp/ = bản sao, txt/trung_da_co = trùng)
#   sosing.com/txt/_mecon     ⇒ Truyện/8-sosing    (bỏ txt/_da_co = đã có ở nguồn khác)
# - Mỗi truyện ⇒ <id>.txt.gz, id = 10 ký tự đầu sha1 của link Nguồn ⇒ ổn định khi file gốc đổi tên (lịch sử nghe không mất)
# - BỎ khối thông tin đầu file (==== … ====) ⇒ giọng đọc không đọc "Tên gốc: <chữ Hán>", "Nguồn: https://…"
# - sosing "[ Phần 1/9 ]" + dòng "-----" ⇒ dòng mốc "==== Phần 1 ====" (web chia chương theo mốc này)
# - Tag: dịch theo từ điển chung alicesw_dich.json, bỏ tag còn chữ Hán / "Featured"
# - KHÔNG đưa lên web truyện về trẻ vị thành niên: thư mục fsnovel "hoc-sinh-thay-co" + truyện có tag / tên rõ ràng như vậy
# - Chỉ nén lại file gốc đã đổi (so size + mtime); truyện không còn ⇒ xoá .gz. Ghi <thư mục>/index.json cho update_index.py
import os
import re
import sys
import json
import gzip
import hashlib
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(HERE))
ALICE_DIR = os.path.join(os.path.dirname(ROOT_DIR), "alicesw")
DICH = os.path.join(HERE, "alicesw_dich.json")

# (khoá nguồn, thư mục đích, thư mục gốc, có lấy thư mục con không, thư mục con bỏ qua)
SOURCES = [
    ("18av", "Truyện/5-18av", "18av.mm-cg/txt", False, set()),
    ("fsnovel", "Truyện/6-fsnovel", "fsnovel.com/downloaded", True, {"hoc-sinh-thay-co"}),
    ("langyou", "Truyện/7-langyou", "langyou4.langyou895/txt", False, set()),
    ("sosing", "Truyện/8-sosing", "sosing.com/txt/_mecon", False, set()),
]
# Thư mục thể loại fsnovel ⇒ tên hiển thị
FS_CAT = {
    "anh-chi-em": "Anh chị em", "bac-si-y-ta-canh-sat": "Bác sĩ, y tá, cảnh sát", "ban-gai-nguoi-yeu": "Bạn gái, người yêu",
    "bo-con-gai": "Bố con gái", "bo-me-chong-con-dau-re": "Bố mẹ chồng, con dâu rể", "co-di-chu-cau-chau": "Cô dì chú cậu cháu",
    "cuong-hiep": "Cưỡng hiếp", "gai-mai-dam": "Gái mại dâm", "hang-xom-dong-nghiep": "Hàng xóm, đồng nghiệp", "khac": "Khác",
    "me-va-con-trai": "Mẹ con", "minh-tinh-nguoi-mau": "Minh tinh, người mẫu", "ngoai-tinh": "Ngoại tình",
    "no-le-sm-dieu-giao": "Nô lệ, SM, điều giáo", "noi-cong-cong-du-lich": "Nơi công cộng, du lịch",
    "phu-nu-truong-thanh": "Phụ nữ chín chắn", "sieu-nhien-ma-quy": "Siêu nhiên, ma quỷ", "thoi-mien-me-thuoc": "Thôi miên, mê thuốc",
    "trinh-tiet-lan-dau": "Lần đầu", "vo-chong": "Vợ chồng",
}
SKIP_TAGS = {"R-18", "Tiếng Trung", "Featured", "(không rõ)", "không rõ"}
HAN = re.compile(r"[一-鿿぀-ヿ]")
# Truyện về trẻ vị thành niên ⇒ không đưa lên web
MINOR = re.compile(r"loli|lolita|ấu dâm|ấu nữ|ấu đồng|trẻ em|trẻ con|học sinh|nữ sinh|nam sinh|cấp (1|2|3)|tiểu học|trung học|shota|chính thái|"
                   r"vị thành niên|萝莉|幼女|幼童|正太|小学|初中|中学生", re.I)


def field(head, *names):
    for name in names:
        m = re.search(r"^\s*" + name + r"\s*:\s*(.+?)\s*$", head, re.M)
        if m:
            return m.group(1)
    return ""


def load_tag_map():
    try:
        with open(DICH, encoding="utf-8") as f:
            return json.load(f).get("tags", {})
    except FileNotFoundError:
        return {}


def clean_tags(raw, tmap):
    out = []
    for t in re.split(r"[,，、;]", raw):
        t = t.strip().lstrip("#").strip()
        if not t:
            continue
        t = tmap.get(t, t)
        for p in t.split(" / "):
            p = p.strip()
            p = p[:1].upper() + p[1:] if p else p
            if p and p not in SKIP_TAGS and not HAN.search(p) and p not in out:
                out.append(p)
    return out


def split_head(text):
    """Tách khối thông tin đầu file (giữa 2 dòng ====) ⇒ (khối đầu, nội dung)."""
    m = re.match(r"\s*={20,}\s*\n(.*?)\n\s*={20,}\s*\n", text, re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def body_for_web(body):
    # sosing: "-----" + "[ Phần 1/9 ]" + "-----" ⇒ "==== Phần 1 ===="
    body = re.sub(r"^\s*\[\s*Phần\s+(\d+)\s*/\s*\d+\s*\]\s*$", r"==================== Phần \1 ====================", body, flags=re.M)
    body = re.sub(r"^\s*-{10,}\s*$\n?", "", body, flags=re.M)
    return body.strip() + "\n"


def read_info(path, src, cat, tmap):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    head, body = split_head(text)
    url = field(head, "Nguồn")
    title = next((l.strip() for l in head.splitlines() if l.strip() and ":" not in l[:14]), "") or os.path.splitext(os.path.basename(path))[0]
    # fsnovel: dòng "Tags" là tag chung của CẢ trang (truyện nào cũng y hệt "Loạn luân, Công sở, Nhân thê…") ⇒ bỏ, chỉ dùng thể loại theo thư mục
    tags = [] if src == "fsnovel" else clean_tags(field(head, "Tags", "Thể loại"), tmap)
    if cat and cat not in tags:
        tags.insert(0, cat)
    author = field(head, "Tác giả") or (re.search(r"^\s*Tác giả\s*:\s*(.{1,60}?)\s*$", body[:600], re.M) or [None, ""])[1]
    ch = re.search(r"\d+", field(head, "Số chương", "Chương"))
    day = field(head, "Ngày")
    st = os.stat(path)
    key = url or os.path.relpath(path, ALICE_DIR)
    return {
        "id": hashlib.sha1(key.encode("utf-8")).hexdigest()[:10],
        "title": title, "author": author.strip(), "tags": tags,
        "ch": int(ch.group()) if ch else 0,
        "t": day if re.fullmatch(r"\d{4}-\d{2}-\d{2}", day or "") else datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
        "file": os.path.relpath(path, ALICE_DIR).replace("\\", "/"),
        "src_size": st.st_size, "src_mtime": int(st.st_mtime),
        "_body": body,
    }


def sync_one(src, out_rel, in_rel, recursive, skip_dirs, tmap):
    in_dir = os.path.join(ALICE_DIR, in_rel)
    out_dir = os.path.join(ROOT_DIR, out_rel)
    if not os.path.isdir(in_dir):
        print(f"[!] {src}: không thấy {in_dir}")
        return
    os.makedirs(out_dir, exist_ok=True)
    idx_path = os.path.join(out_dir, "index.json")
    try:
        with open(idx_path, encoding="utf-8") as f:
            old = json.load(f)
    except FileNotFoundError:
        old = {}

    files = []
    if recursive:
        for d in sorted(os.listdir(in_dir)):
            p = os.path.join(in_dir, d)
            if os.path.isdir(p) and d not in skip_dirs:
                files += [(os.path.join(p, n), FS_CAT.get(d, d)) for n in os.listdir(p) if n.endswith(".txt")]
    else:
        files = [(os.path.join(in_dir, n), "") for n in os.listdir(in_dir) if n.endswith(".txt")]

    best, minor, dup = {}, 0, 0
    for path, cat in files:
        info = read_info(path, src, cat, tmap)
        if MINOR.search(info["title"]) or any(MINOR.search(t) for t in info["tags"]):
            minor += 1
            continue
        if not info["_body"].strip():
            continue
        cur = best.get(info["id"])
        if cur:
            dup += 1
            if info["src_size"] <= cur["src_size"]:
                continue
        best[info["id"]] = info

    changed = 0
    for nid, info in best.items():
        gz = os.path.join(out_dir, nid + ".txt.gz")
        o = old.get(nid)
        body = info.pop("_body")
        if o and o.get("src_size") == info["src_size"] and o.get("src_mtime") == info["src_mtime"] and os.path.exists(gz):
            info["size"] = o["size"]
            if not info["ch"]: info["ch"] = o.get("ch", 0)  # số chương đã đếm lần trước
            continue
        web = body_for_web(body)
        if not info["ch"]:
            info["ch"] = count_ch(web)
        data = web.encode("utf-8")
        with open(gz, "wb") as f:
            with gzip.GzipFile(fileobj=f, mode="wb", compresslevel=9, mtime=0) as z:
                z.write(data)
        info["size"] = len(data)
        changed += 1
    removed = 0
    for name in os.listdir(out_dir):
        if name.endswith(".txt.gz") and name[:-7] not in best:
            os.remove(os.path.join(out_dir, name))
            removed += 1
    index = {nid: {k: v for k, v in info.items() if k not in ("id", "_body")} for nid, info in sorted(best.items())}
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    mb = sum(os.path.getsize(os.path.join(out_dir, n)) for n in os.listdir(out_dir) if n.endswith(".gz")) / 1e6
    print(f"[OK] {src}: {len(best)} truyện | nén mới {changed} | xoá {removed} | bỏ {minor} truyện về trẻ vị thành niên"
          f" | trùng {dup} | {mb:.0f} MB")


_SPLIT = None
def count_ch(text):
    """Số chương = đếm bằng CHÍNH hàm chia chương của web (reader.js, qua Node) ⇒ khớp lúc mở truyện; không có Node ⇒ 1."""
    global _SPLIT
    import subprocess, tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(text)
    try:
        js = ("const fs=require('fs');const src=fs.readFileSync(process.argv[1],'utf8');"
              "const f=new Function(src.slice(src.indexOf('function splitIntoChapters'),src.indexOf('// Chia 1 đoạn văn'))+';return splitIntoChapters;')();"
              "process.stdout.write(String(f(fs.readFileSync(process.argv[2],'utf8'),'x').length))")
        r = subprocess.run(["node", "-e", js, os.path.join(ROOT_DIR, "reader.js"), tf.name], capture_output=True, text=True, timeout=60)
        return int(r.stdout) if r.returncode == 0 and r.stdout.strip().isdigit() else 1
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return 1
    finally:
        os.remove(tf.name)


def main():
    tmap = load_tag_map()
    for s in SOURCES:
        sync_one(*s, tmap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
