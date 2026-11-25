# Sửa tên truyện Text Mp3 (dòng "TITLE: ..." đầu file). Tên cũ do tool đoán dấu từ tên file không dấu ⇒ hay sai
# ("Bị Mắt Kinh Doanh", "May Bảy", "Nàng Dâu Dâm Dang+0008"). Cách mới: KHÔNG đoán — tìm đúng cụm chữ đó trong nội dung
# truyện (tên file bi-mat-kinh-doanh ⇒ cụm 4 từ bỏ dấu ra "bi mat kinh doanh") rồi lấy nguyên cách viết có dấu.
# Không tìm thấy cả cụm ⇒ mỗi từ lấy cách viết có dấu hay gặp nhất trong toàn bộ kho Text Mp3 (khi đi cùng từ trước / sau).
# Chạy thử (mặc định, in kết quả):  python sua_ten_text_mp3.py
# Chạy thật (ghi dòng TITLE):       python sua_ten_text_mp3.py --chay
import os
import re
import sys
import json
import unicodedata
from collections import Counter, defaultdict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT_DIR, "Truyện", "1-Text Mp3")
WORD = re.compile(r"[0-9A-Za-zÀ-ỹĐđ]+")
HEAD = 4000            # tìm trước ở đầu truyện (thường có tên truyện)
SCAN = 400_000         # rồi tới 400 KB đầu


def strip(t):
    t = unicodedata.normalize("NFD", t)
    return "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D").lower()


def slug_words(name):
    """Tên file ⇒ các từ không dấu của tên truyện (bỏ _1, +0010, +Chuong-0053-0084, -0063, -full)"""
    s = re.sub(r"\.txt$", "", name)
    s = re.sub(r"(_\d+)+$", "", s)
    s = re.sub(r"[+\-_](chuong|chapter|part|phan)[\s\-_]*\d+.*$", "", s, flags=re.I)
    s = re.sub(r"\+\d+.*$", "", s)
    s = re.sub(r"-\d{3,}$", "", s)
    s = re.sub(r"-full$", "", s, flags=re.I)
    return [w for w in re.split(r"[-_+ ]+", s.lower()) if w]


def cap(w):
    return w[:1].upper() + w[1:] if w else w


def find_phrase(words, text):
    """Cụm từ trong nội dung có dạng bỏ dấu = words ⇒ các từ gốc có dấu (ưu tiên đầu truyện)"""
    toks = WORD.findall(text)
    low = [strip(t) for t in toks]
    n = len(words)
    for i in range(len(toks) - n + 1):
        if low[i:i + n] == words:
            return toks[i:i + n]
    return None


def sub_find(words, toks, low):
    """Đoạn words có trong toks (so bỏ dấu) ⇒ các từ gốc"""
    n = len(words)
    first = words[0]
    for i in range(len(low) - n + 1):
        if low[i] == first and low[i:i + n] == words:
            return toks[i:i + n]
    return None


def main():
    run = "--chay" in sys.argv
    files = [os.path.join(r, f) for r, _, fs in os.walk(SRC) for f in fs if f.endswith(".txt")]
    vocab = set()
    for p in files:
        vocab.update(slug_words(os.path.basename(p)))
    texts = {}
    # Đếm cách viết có dấu của các từ trong tên truyện, theo từ đứng trước (L) / sau (R) — CHỈ từ truyện viết có dấu
    # (truyện viết không dấu làm "phieu" thắng "phiêu")
    L, R, U = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    for p in files:
        with open(p, encoding="utf-8", errors="replace") as f:
            t = f.read(SCAN)
        texts[p] = t
        toks = WORD.findall(t[:80000])
        if not toks:
            continue
        low = [strip(x) for x in toks]
        accented = sum(1 for x, y in zip(toks, low) if x.lower() != y) / len(toks)
        if accented < 0.3:
            continue
        for i, (tk, w) in enumerate(zip(toks, low)):
            if w not in vocab:
                continue
            f_ = tk.lower()
            U[w][f_] += 1
            if i: L[(low[i - 1], w)][f_] += 1
            if i + 1 < len(low): R[(w, low[i + 1])][f_] += 1

    def plain(seg):
        """Đoạn viết không dấu mà các từ đó có cách viết có dấu ⇒ không dùng (lấy dấu từ truyện khác)"""
        return all(x.lower() == strip(x) for x in seg) and any(any(f != strip(x) for f in U.get(strip(x), ())) for x in seg)

    def pick(words, i):
        w = words[i]
        sc = Counter()
        if i: sc.update(L.get((words[i - 1], w), {}))
        if i + 1 < len(words): sc.update(R.get((w, words[i + 1]), {}))
        if not sc: sc = U.get(w, Counter())
        return sc.most_common(1)[0][0] if sc else w

    res = Counter(); changes = []
    for p in sorted(files):
        name = os.path.basename(p)
        t = texts[p]
        first, rest = (t.split("\n", 1) + [""])[:2]
        old = first[6:].strip() if first.startswith("TITLE:") else ""
        words = slug_words(name)
        if not words:
            res["không có tên"] += 1
            continue
        toks = WORD.findall(rest)
        low = [strip(x) for x in toks]
        # Truyện viết không dấu (< 30% từ có dấu) ⇒ không lấy chữ trong chính nó, chỉ lấy dấu từ các truyện khác
        if toks and sum(1 for x, y in zip(toks[:20000], low[:20000]) if x.lower() != y) / len(toks[:20000]) < 0.3:
            toks, low = [], []
        hit = sub_find(words, toks, low)
        # Truyện viết không dấu ⇒ cụm tìm thấy cũng không dấu ⇒ bỏ, dùng cách ghép (lấy dấu từ các truyện khác)
        if hit and plain(hit):
            hit = None
        if hit:
            out, how = list(hit), "trong truyện"
        else:
            # Ghép: lấy đoạn DÀI NHẤT (≥ 2 từ) của tên có trong truyện; từ lẻ còn lại chọn theo từ trước + sau
            out, i, how = [], 0, "ghép đoạn"
            while i < len(words):
                got = None
                for j in range(len(words), i + 1, -1):
                    got = sub_find(words[i:j], toks, low)
                    if got and plain(got):
                        got = None  # đoạn viết không dấu ⇒ thử đoạn ngắn hơn / chọn theo từ trước + sau
                    if got:
                        break
                if got:
                    out += got
                    i += len(got)
                else:
                    out.append(pick(words, i))
                    i += 1
            if not any(len(o) for o in out):
                how = "ghép từ"
        new = " ".join(cap(w.lower() if how != "trong truyện" else w) for w in out)
        res[how] += 1
        if new != old:
            changes.append((p, old, new, how))
            res["đổi"] += 1
            if run:
                with open(p, encoding="utf-8", errors="replace") as f:
                    full = f.read()
                body = full.split("\n", 1)[1] if full.startswith("TITLE:") else full
                with open(p, "w", encoding="utf-8") as f:
                    f.write(f"TITLE: {new}\n" + body)
    print(f"[*] {len(files)} truyện | cả cụm trong truyện: {res['trong truyện']} | ghép đoạn: {res['ghép đoạn']} | đổi tên: {res['đổi']}"
          + ("" if run else "  (CHẠY THỬ — thêm --chay để ghi)"))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sua_ten_ketqua.json"), "w", encoding="utf-8") as f:
        json.dump([{"file": os.path.relpath(p, SRC).replace("\\", "/"), "cu": o, "moi": n, "cach": h} for p, o, n, h in changes], f, ensure_ascii=False, indent=1)
    return changes


if __name__ == "__main__":
    main()
