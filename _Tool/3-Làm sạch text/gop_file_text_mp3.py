# Gộp truyện Text Mp3 bị cắt thành nhiều file (ten_1.txt, ten_2.txt...) thành 1 file ten.txt + đánh dấu chương.
# - Các file chỉ là đoạn cắt theo dung lượng (~500 KB), chữ nối liền ⇒ ghép theo thứ tự số, bỏ dòng "TITLE: ..._N" đầu mỗi đoạn
# - Dòng tiêu đề chương trong nội dung ("Phần 1: ...", "Chương 3 – ...") ⇒ dòng mốc "==== Phần 1: ... ====" (web tách chương theo mốc)
# - Đã có sẵn ten.txt ⇒ giữ bản lớn hơn (bản kia thừa)
# - Tóm tắt bị chia theo phần ⇒ gộp theo cùng cách
# - Ghi gop_file_map.json {uid mới: [uid cũ...]} ⇒ update_index.py ghi "was" ⇒ web chuyển lịch sử nghe + yêu thích sang file gộp
# Chạy thử (mặc định, chỉ in kế hoạch):  python gop_file_text_mp3.py
# Chạy thật:                            python gop_file_text_mp3.py --chay
import os
import re
import sys
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # _Tool/3-Làm sạch text/ -> gốc
SRC = os.path.join(ROOT_DIR, "Truyện", "1-Text Mp3")
SUM = os.path.join(ROOT_DIR, "Truyện", "3-Tóm tắt", "1-Text Mp3")
MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gop_file_map.json")
# Phần có thể bị cắt thêm lần nữa: ten_2_1.txt, ten_2_2.txt = phần 2 ⇒ khoá sắp xếp (2, 1), (2, 2) nằm giữa _1 và _3
PART_RE = re.compile(r"^(.*?)((?:_\d+)+)\.txt$")
# Tiêu đề chương: ngắn, "Phần/Chương/Hồi/Quyển/Tập" + số, ngay sau số là dấu ":" "." "-" "–" "—" ")" hoặc hết dòng
HEAD_RE = re.compile(r"^(Phần|Chương|Hồi|Quyển|Tập)\s+(\d+|[IVXLCDM]+)\s*(?:[:.\-–—)]|$)", re.I)
MARK = "=" * 20


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def strip_title(text):
    """Bỏ dòng "TITLE: ..." đầu đoạn ⇒ (tiêu đề, phần còn lại)"""
    m = re.match(r"^\s*TITLE:\s*(.*)\n?", text)
    return (m.group(1).strip(), text[m.end():]) if m else ("", text)


def mark_chapters(body):
    """Dòng tiêu đề chương ⇒ dòng mốc. Ít hơn 2 dòng ⇒ không phải truyện chia chương, để nguyên"""
    lines = body.split("\n")
    idx = [i for i, l in enumerate(lines) if len(l.strip()) <= 150 and not l.strip().startswith("=") and HEAD_RE.match(l.strip())]
    if len(idx) < 2:
        return body, 0
    for i in idx:
        lines[i] = f"{MARK} {lines[i].strip()} {MARK}"
    return "\n".join(lines), len(idx)


def merge_parts(folder, parts):
    """parts = [(số, tên file)] đã sắp ⇒ (tiêu đề, nội dung ghép)"""
    title, chunks = "", []
    for _, name in parts:
        t, body = strip_title(read(os.path.join(folder, name)))
        title = title or re.sub(r"_\d+$", "", t)
        chunks.append(body.strip("\n"))
    return title, "\n".join(chunks)


def main():
    run = "--chay" in sys.argv
    groups = {}
    for root, _, files in os.walk(SRC):
        for f in files:
            m = PART_RE.match(f)
            if m:
                key = tuple(int(x) for x in m.group(2).split("_")[1:])
                groups.setdefault((root, m.group(1)), []).append((key, f))
    groups = {k: sorted(v) for k, v in groups.items() if len(v) > 1}
    print(f"[*] {len(groups)} truyện bị cắt, {sum(len(v) for v in groups.values())} file" + ("" if run else "  (CHẠY THỬ — thêm --chay để làm thật)"))

    mapping, n_marked, n_heads, warn = {}, 0, 0, []
    for (folder, base), parts in sorted(groups.items()):
        rel = os.path.relpath(folder, SRC).replace("\\", "/")
        nums = sorted({n[0] for n, _ in parts})  # số phần cấp 1 (phần 2 cắt thêm thành 2_1, 2_2 vẫn là phần 2)
        if nums != list(range(1, len(nums) + 1)):
            warn.append(f"{rel}/{base}: chỉ có phần {nums} (thiếu phần) — vẫn gộp phần đang có")
        out = os.path.join(folder, base + ".txt")
        parts_size = sum(os.path.getsize(os.path.join(folder, f)) for _, f in parts)
        keep_base = os.path.exists(out) and os.path.getsize(out) >= parts_size - 1024
        if keep_base:
            title, body = strip_title(read(out))
            note = f"giữ file gộp sẵn ({os.path.getsize(out) // 1024} KB ≥ các phần {parts_size // 1024} KB)"
        else:
            title, body = merge_parts(folder, parts)
            note = "ghi đè file gộp cũ nhỏ hơn" if os.path.exists(out) else ""
        title = title or base.replace("-", " ").title()
        body, heads = mark_chapters(body)
        if heads:
            n_marked += 1
            n_heads += heads
        text = f"TITLE: {title}\n" + body.strip("\n") + "\n"
        uid_new = f"Text Mp3/{rel}/{base}.txt"
        mapping[uid_new] = [f"Text Mp3/{rel}/{f}" for _, f in parts]
        print(f"  {rel}/{base}.txt ⇐ {len(parts)} phần | {heads} chương | {len(text.encode()) // 1024} KB {note}")
        if run:
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            for _, f in parts:
                os.remove(os.path.join(folder, f))

        # Tóm tắt cũng bị chia theo phần ⇒ gộp
        sdir = os.path.join(SUM, rel)
        sparts = [(n, f) for n, f in parts if os.path.exists(os.path.join(sdir, f))]
        if sparts:
            print(f"    + gộp {len(sparts)} bản tóm tắt")
            if run:
                with open(os.path.join(sdir, base + ".txt"), "w", encoding="utf-8") as f:
                    f.write("\n\n".join(read(os.path.join(sdir, x)).strip() for _, x in sparts) + "\n")
                for _, x in sparts:
                    os.remove(os.path.join(sdir, x))

    print(f"[*] Đánh dấu chương: {n_marked} truyện, {n_heads} chương | {len(groups) - n_marked} truyện không có tiêu đề chương (web tự chia theo độ dài)")
    for w in warn:
        print("[!]", w)
    if run:
        old = {}
        if os.path.exists(MAP_FILE):
            with open(MAP_FILE, encoding="utf-8") as f:
                old = json.load(f)
        old.update(mapping)
        with open(MAP_FILE, "w", encoding="utf-8") as f:
            json.dump(old, f, ensure_ascii=False, indent=1)
        print(f"[OK] Đã gộp. Bảng chuyển lịch sử: {MAP_FILE}")


if __name__ == "__main__":
    main()
