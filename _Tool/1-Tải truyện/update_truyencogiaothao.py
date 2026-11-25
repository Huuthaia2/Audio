# Tự động cập nhật nguồn truyencogiaothao (https://truyencogiaothaox.net) — chạy bằng "_Tool/4. Tự động cập nhật truyện.bat".
# Nối chương mới cho truyện đã có trong kho + tải truyện mới đăng, lưu thông tin truyện (ngày, tag, tác giả...) vào
# giaothao_meta.json, xong tự chia thể loại + làm lại stories.json (KHÔNG push). Cửa sổ tkinter hiện tiến độ.
# Dùng lại hàm tải của leech_truyencogiaothao.py (cách dán link cũ của bat 1 vẫn chạy như trước).
import os
import re
import sys
import json
import queue
import threading
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOL_DIR)
import leech_truyencogiaothao as L  # noqa: E402

# --- CẤU HÌNH ---
SITE = "https://truyencogiaothaox.net"
SRC_DIR = L.OUT_DIR  # Truyện/2-truyencogiaothao
SUM_DIR = os.path.join(L.ROOT_DIR, "Truyện", "3-Tóm tắt", "2-truyencogiaothao")
META_FILE = os.path.join(TOOL_DIR, "giaothao_meta.json")
WEB_TOOL_DIR = os.path.join(os.path.dirname(TOOL_DIR), "2-Cập nhật web")
INFO_WORKERS = 8  # lấy thông tin 8 truyện cùng lúc
STEPS = 5
FILE_RE = re.compile(r'^(.+)-(\d+)\.txt$', re.I)
MARK_RE = re.compile(r'^={20} (.*?) ={20}$', re.M)  # dòng mốc chương tool leech ghi (web tách chương theo mốc này)

# Bộ màu theo web Kho Truyện
BG, BG2, BG3, FG, MUTED, ACCENT = "#18181b", "#27272a", "#3f3f46", "#e4e4e7", "#a1a1aa", "#fe628e"


# =====================================================================
# File meta: {slug: {title, author, tags, genres, status, year, updated, posted, chapters, last, skip?, was?}}
# Khoá "_done" = lần chạy trước chạy hết, không lỗi ⇒ lần này được dừng quét sớm.
# =====================================================================
def load_meta():
    try:
        with open(META_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_meta(meta):
    tmp = META_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    # Windows: file meta đang bị chương trình khác mở thoáng qua (diệt virus, VS Code...) ⇒ os.replace báo
    # "Access is denied" (lỗi thật 2026-11-25, làm dừng cả lần tải) ⇒ thử lại vài lần, vẫn không được thì ghi thẳng
    for _ in range(20):
        try:
            os.replace(tmp, META_FILE)
            return
        except PermissionError:
            time.sleep(0.25)
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    try: os.remove(tmp)
    except OSError: pass


def set_meta(meta, e, info=None, **extra):
    """Ghi thông tin 1 truyện. e = mục trên trang danh sách (slug, title, last, date)"""
    m = meta.setdefault(e["slug"], {})
    m["title"] = (info or {}).get("title") or e["title"]
    if info:
        m.update(author=info["author"], tags=info["tags"], genres=info["genres"], status=info["status"],
                 year=info["year"], posted=info["posted"], chapters=len(info["chapters"]))
    m["updated"] = (info and info["updated"]) or e["date"] or m.get("updated")
    m["last"] = e["last"]
    m.update(extra)


# =====================================================================
# Bước 1: quét kho
# =====================================================================
def scan_kho():
    """kho = {slug: (số chương, đường dẫn)} các file cập nhật được; known = mọi slug đã có.
    File "_..." (tải lỗi / đánh dấu trùng) và thư mục z* (zDaCoMp3, zzzzLoi) chỉ tính là đã có, không cập nhật."""
    kho, known = {}, set()
    for root, dirs, files in os.walk(SRC_DIR):
        rel = os.path.relpath(root, SRC_DIR)
        frozen = rel != "." and rel.split(os.sep)[0].startswith("z")
        for f in files:
            if not f.lower().endswith(".txt"):
                continue
            name = f[1:] if f.startswith("_") else f
            if "-=-" in name:  # _slug-=-tên truyện trùng.txt
                slug, n = name.split("-=-")[0], 0
            else:
                m = FILE_RE.match(name)
                if not m:
                    continue
                slug, n = m.group(1), int(m.group(2))
            known.add(slug)
            if f.startswith("_") or frozen:
                continue
            if slug not in kho or n > kho[slug][0]:
                kho[slug] = (n, os.path.join(root, f))
    return kho, known


# =====================================================================
# Bước 2: quét trang danh sách + phân loại
# =====================================================================
def fetch_list_page(n):
    """Trang danh sách n (1 = trang chủ) ⇒ ([{slug, title, url, last, date}], tổng số trang)"""
    url = SITE + "/" if n == 1 else f"{SITE}/page/{n}/"
    r = L.session.get(url, timeout=20)
    if r.status_code == 404:
        return [], 0
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for it in soup.select(".page-item-detail"):
        a = it.select_one(".post-title a")
        if not a or not a.get("href"):
            continue
        ci = it.select_one(".chapter-item")
        ca = ci.select_one("a") if ci else None
        po = ci.select_one(".post-on") if ci else None
        date_txt = ""
        if po:
            pa = po.select_one("a[title]")
            date_txt = pa["title"] if pa else po.get_text(" ", strip=True)
        items.append({
            "slug": a["href"].rstrip("/").split("/")[-1], "title": a.get_text(strip=True), "url": a["href"],
            "last": ca["href"] if ca and ca.get("href") else "", "date": L.parse_site_date(date_txt),
        })
    nums = [int(x) for p in soup.select('a[href*="/page/"]') for x in re.findall(r"/page/(\d+)/?$", p["href"])]
    return items, max(nums + [n])


def page_all_seen(items, meta):
    """Mọi truyện trên trang đều trùng "link chương mới nhất" đã lưu ⇒ các trang sau cũng không đổi (trang xếp theo ngày cập nhật)"""
    return bool(items) and all(meta.get(e["slug"], {}).get("last") == e["last"] for e in items)


def find_cutoff(entries, known):
    """Lần chạy đầu: trang đầu tiên có ≥ nửa số truyện đã có trong kho = mốc đợt tải gần nhất (None = không thấy)"""
    by_page = {}
    for e in entries:
        by_page.setdefault(e["page"], []).append(e)
    for p in sorted(by_page):
        items = by_page[p]
        if sum(e["slug"] in known for e in items) * 2 >= len(items):
            return p
    return None


def classify(entries, kho, known, meta, first_run):
    """⇒ (new, changed, passive, cutoff)
    new     = truyện chưa có, chưa từng thấy ⇒ tải
    changed = truyện đã có trong kho, link chương mới nhất khác lần trước (lần đầu = tất cả) ⇒ lấy thông tin + so số chương
    passive = chỉ ghi nhận vào meta (truyện đã biết nhưng không cập nhật được; lần đầu: truyện cũ hơn mốc ⇒ skip)"""
    cutoff = find_cutoff(entries, known) if first_run else None
    new, changed, passive = [], [], []
    for e in entries:
        s, m = e["slug"], meta.get(e["slug"])
        if s in kho:
            if not m or m.get("last") != e["last"]:
                changed.append(e)
        elif s in known or m:
            if not m or m.get("last") != e["last"]:
                passive.append(e)
        elif first_run and (cutoff is None or e["page"] >= cutoff):
            e["skip"] = True
            passive.append(e)
        else:
            new.append(e)
    return new, changed, passive, cutoff


# =====================================================================
# Bước 4: nối chương mới vào file đã có
# =====================================================================
def norm(s):
    return " ".join((s or "").split())


def append_chapters(slug, path, old_n, info, on_progress=None):
    """Tải chapters[old_n:] rồi ghi file mới slug-<tổng>.txt = nội dung cũ (giữ nguyên từng byte) + chương mới, xoá file cũ,
    đổi tên file tóm tắt cùng tên (nếu có). ⇒ ('ok', tên file mới, số chương mới) / ('fail', [chương lỗi]) / ('mismatch', lý do)"""
    chapters = info["chapters"]
    with open(path, "rb") as f:
        old = f.read()
    marks = MARK_RE.findall(old.decode("utf-8", errors="replace").replace("\r\n", "\n"))
    if len(marks) != old_n:
        return "mismatch", f"file có {len(marks)} mốc chương, tên file ghi {old_n}"
    if norm(marks[-1]) != norm(chapters[old_n - 1]["title"]):
        return "mismatch", f"chương cuối trong file '{marks[-1]}' ≠ chương {old_n} trên web '{chapters[old_n - 1]['title']}'"

    todo = chapters[old_n:]
    results, failed = {}, []
    with ThreadPoolExecutor(max_workers=L.MAX_WORKERS) as ex:
        futs = [ex.submit(L.download_chapter_worker, old_n + i + 1, c["title"], c["url"]) for i, c in enumerate(todo)]
        for fut in as_completed(futs):
            idx, c_title, text = fut.result()
            if text:
                results[idx] = (c_title, text)
                if on_progress:
                    on_progress(len(results), len(todo))
            else:
                failed.append(idx)
    if failed:
        return "fail", sorted(failed)

    # Đúng dạng tool leech ghi: "\n\n==== tên chương ====\n\n" + nội dung + "\n\n"
    add = "".join(f"\n\n{'=' * 20} {results[i][0]} {'=' * 20}\n\n{results[i][1]}\n\n" for i in sorted(results))
    nl = "\r\n" if b"\r\n" in old else "\n"
    add = add.replace("\r\n", "\n").replace("\n", nl)

    new_name = f"{slug}-{len(chapters):04d}.txt"
    new_path = os.path.join(os.path.dirname(path), new_name)
    tmp = new_path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(old + add.encode("utf-8"))
    os.replace(tmp, new_path)
    if os.path.normcase(new_path) != os.path.normcase(path):
        os.remove(path)
    # File tóm tắt cùng tên ⇒ đổi tên theo (web tìm tóm tắt theo đúng đường dẫn file truyện)
    sum_path = os.path.join(SUM_DIR, os.path.relpath(path, SRC_DIR))
    sum_new = os.path.join(os.path.dirname(sum_path), new_name)
    if os.path.exists(sum_path) and not os.path.exists(sum_new):
        os.rename(sum_path, sum_new)
    return "ok", new_name, len(todo)


# =====================================================================
# Luồng chạy chính (chạy ở luồng nền, báo GUI qua ui(...))
# =====================================================================
class Updater:
    def __init__(self, ui):
        self.ui = ui  # ui(kind, *args): log / step / prog / cur / count
        self.stop = threading.Event()
        self.count = {"new": 0, "upd": 0, "chap": 0, "err": 0}
        self.retry_err = 0  # lỗi cần thử lại ⇒ lần sau quét hết trang (không dừng sớm)

    def log(self, msg):
        self.ui("log", msg)

    def bump(self, k, n=1):
        self.count[k] += n
        self.ui("count", dict(self.count))

    def step(self, i, text):
        self.ui("step", f"Bước {i}/{STEPS}: {text}")

    def run(self):
        meta = load_meta()
        # 1. Quét kho
        self.step(1, "Quét kho truyện")
        kho, known = scan_kho()
        self.log(f"[*] Kho có {len(kho)} truyện cập nhật được, {len(known)} truyện đã biết.")
        first_run = not any(not k.startswith("_") for k in meta)
        can_stop_early = bool(meta.get("_done"))
        meta["_done"] = False
        if first_run:
            self.log("[*] Lần chạy đầu: quét hết mọi trang danh sách.")

        # 2. Quét trang danh sách
        entries, seen, pages, n = [], set(), 1, 1
        complete = False  # quét tới hết / dừng sớm đúng cách (không phải bị lỗi mạng hay bấm Dừng)
        while not self.stop.is_set():
            if n > pages:
                complete = True
                break
            self.step(2, f"Quét trang web — trang {n}/{pages}" if n > 1 else "Quét trang web — trang 1")
            self.ui("prog", n, pages)
            try:
                items, total = fetch_list_page(n)
            except Exception as ex:
                self.log(f"[!] Lỗi tải trang danh sách {n}: {ex} — dừng quét ở đây.")
                self.retry_err += 1
                break
            if not items:
                complete = True
                break
            pages = max(pages, total)
            for e in items:
                if e["slug"] not in seen:
                    seen.add(e["slug"])
                    e["page"] = n
                    entries.append(e)
            if can_stop_early and page_all_seen(items, meta):
                self.log(f"[*] Trang {n}: không có gì mới ⇒ dừng quét.")
                complete = True
                break
            n += 1
        if first_run and not complete:
            # Lần đầu phải quét đủ mới tìm đúng mốc ⇒ quét dở thì không ghi gì (tránh đánh dấu bỏ qua nhầm truyện mới)
            self.log("[!] Lần chạy đầu chưa quét hết trang danh sách ⇒ không ghi gì, chạy lại để quét từ đầu.")
            self.ui("step", "Đã dừng — chưa quét hết trang danh sách")
            return
        new, changed, passive, cutoff = classify(entries, kho, known, meta, first_run)
        if first_run:
            self.log(f"[*] Mốc đợt tải gần nhất: trang {cutoff}. Truyện chưa có từ trang này trở đi ⇒ bỏ qua, lần sau không tải."
                     if cutoff else "[!] Không thấy mốc đợt tải gần nhất ⇒ lần này không tải truyện mới.")
        for e in passive:
            set_meta(meta, e, **({"skip": True} if e.get("skip") else {}))
        save_meta(meta)
        self.log(f"[*] Quét {len(entries)} truyện: {len(new)} truyện mới, {len(changed)} truyện đã có cần kiểm tra.")

        # 3. Lấy thông tin (song song)
        to_append, to_new = [], []
        work = [(e, "chg") for e in changed] + [(e, "new") for e in new]
        if work and not self.stop.is_set():
            self.step(3, f"Lấy thông tin {len(work)} truyện")
            done = 0
            with ThreadPoolExecutor(max_workers=INFO_WORKERS) as ex:
                futs = {ex.submit(L.fetch_story, e["url"]): (e, kind) for e, kind in work}
                for fut in as_completed(futs):
                    if self.stop.is_set():
                        for f in futs:
                            f.cancel()
                        break
                    e, kind = futs[fut]
                    done += 1
                    self.ui("prog", done, len(work))
                    self.ui("cur", e["title"])
                    try:
                        info = fut.result()
                    except Exception as ex2:
                        info = None
                        self.log(f"[!] Lỗi lấy thông tin {e['slug']}: {ex2}")
                    if not info or info["guessed"]:
                        if info:
                            self.log(f"[!] {e['slug']}: không đọc được danh sách chương — lần sau thử lại.")
                        self.bump("err")
                        self.retry_err += 1
                        continue
                    if kind == "new":
                        to_new.append((e, info))
                    elif len(info["chapters"]) > kho[e["slug"]][0]:
                        to_append.append((e, info))
                    else:
                        set_meta(meta, e, info)
                        if done % 25 == 0:  # lần đầu ~1600 truyện ⇒ ghi file meta mỗi 25 truyện, không phải mỗi truyện
                            save_meta(meta)
            save_meta(meta)
        self.log(f"[*] {len(to_append)} truyện có chương mới, {len(to_new)} truyện mới cần tải.")

        # 4. Tải (từng truyện; mỗi truyện tải 10 chương song song)
        jobs = [(e, info, "chg") for e, info in to_append] + [(e, info, "new") for e, info in to_new]
        indexed = False
        for i, (e, info, kind) in enumerate(jobs):
            if self.stop.is_set():
                break
            self.step(4, f"Tải truyện {i + 1}/{len(jobs)}")
            self.ui("prog", i, len(jobs))
            self.ui("cur", info["title"])
            try:
                if kind == "chg":
                    self.do_append(meta, e, info, kho[e["slug"]])
                else:
                    if not indexed:
                        L.pre_scan_storage()  # bảng check trùng tên / nội dung của tool leech
                        indexed = True
                    name = L.leech_story(e["url"], info)
                    set_meta(meta, e, info)
                    if name:
                        self.bump("new")
                        self.bump("chap", len(info["chapters"]))
                        if name.startswith("_"):
                            self.bump("err")
                            self.log(f"[!] {name}: có chương tải lỗi (file tên bắt đầu bằng _).")
            except Exception as ex:
                self.log(f"[!] Lỗi tải {e['slug']}: {ex}")
                self.bump("err")
                self.retry_err += 1
            save_meta(meta)
        if jobs:
            self.ui("prog", len(jobs), len(jobs))

        # 5. Chia thể loại truyện mới + làm lại stories.json (luôn chạy: file đổi tên ⇒ stories.json phải theo)
        self.step(5, "Chia thể loại + làm lại stories.json")
        self.ui("cur", "")
        for script in ("auto_sort_giaothao.py", "update_index.py"):
            self.run_script(os.path.join(WEB_TOOL_DIR, script))

        stopped = self.stop.is_set()
        meta["_done"] = not stopped and not self.retry_err
        save_meta(meta)
        c = self.count
        self.ui("step", ("Đã dừng" if stopped else "Xong") + f" — {c['new']} truyện mới, {c['upd']} truyện có chương mới, "
                f"{c['chap']} chương đã tải, {c['err']} lỗi")
        self.log("[OK] Xong. Muốn đưa lên web online: chạy \"2. Cập nhật web.bat\" (bước push).")

    def do_append(self, meta, e, info, kho_item):
        old_n, path = kho_item
        res = append_chapters(e["slug"], path, old_n, info,
                              lambda a, b: self.ui("cur", f"{info['title']} — chương mới {a}/{b}"))
        if res[0] == "ok":
            m = meta.get(e["slug"], {})
            was = m.get("was", []) + [os.path.basename(path)]
            set_meta(meta, e, info, was=was)
            self.bump("upd")
            self.bump("chap", res[2])
            self.log(f"[+] {os.path.basename(path)} → {res[1]} (+{res[2]} chương)")
        elif res[0] == "fail":
            self.log(f"[!] {e['slug']}: lỗi tải chương {', '.join(map(str, res[1]))} — giữ nguyên file, lần sau thử lại.")
            self.bump("err")
            self.retry_err += 1
        else:
            # Mốc chương không khớp ⇒ không nối (tránh ghép sai thứ tự). Ghi nhận để lần sau không thử lại mãi.
            self.log(f"[!] {os.path.basename(path)}: không nối chương — {res[1]}.")
            set_meta(meta, e, info, nomerge=True)
            self.bump("err")

    def run_script(self, path):
        self.log(f"\n[*] Chạy {os.path.basename(path)}...")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        p = subprocess.Popen([sys.executable, "-u", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace", cwd=L.ROOT_DIR,
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"}, creationflags=flags)
        for line in p.stdout:
            line = line.rstrip()
            if line and not line.strip().startswith("Progress:"):
                self.log("    " + line)
        p.wait()
        if p.returncode:
            self.log(f"[!] {os.path.basename(path)} báo lỗi (mã {p.returncode}).")
            self.bump("err")


# =====================================================================
# GUI
# =====================================================================
class QueueWriter:
    """Thay sys.stdout: gom dòng print của tool leech vào nhật ký; dòng tiến độ in bằng \\r ⇒ hiện ở dòng "đang tải"."""
    def __init__(self, q):
        self.q, self.buf = q, ""

    def write(self, s):
        try:
            if sys.__stdout__:
                sys.__stdout__.write(s)
        except Exception:
            pass
        self.buf += s
        *lines, self.buf = self.buf.split("\n")
        for line in lines:
            line = line.split("\r")[-1].rstrip()
            if line:
                self.q.put(("log", line))
        if "\r" in self.buf:
            self.buf = self.buf.split("\r")[-1]
            if self.buf.strip():
                self.q.put(("cur", self.buf.strip()))
        return len(s)

    def flush(self):
        pass


class App:
    def __init__(self, root, make_worker=Updater):
        import tkinter as tk
        from tkinter import ttk
        from tkinter.scrolledtext import ScrolledText
        self.root, self.q = root, queue.Queue()
        self.closing = False
        self.worker = make_worker(lambda *a: self.q.put(a))
        root.title("Tự động cập nhật truyện — truyencogiaothao")
        root.geometry("820x560")
        root.configure(bg=BG)
        st = ttk.Style(root)
        st.theme_use("clam")
        st.configure("P.Horizontal.TProgressbar", troughcolor=BG2, background=ACCENT, bordercolor=BG2, lightcolor=ACCENT, darkcolor=ACCENT)
        font = ("Segoe UI", 10)

        def lbl(text="", fg=FG, size=10, bold=False):
            w = tk.Label(root, text=text, bg=BG, fg=fg, font=("Segoe UI", size, "bold" if bold else "normal"), anchor="w", justify="left")
            w.pack(fill="x", padx=14, pady=(6, 0))
            return w

        src = os.path.relpath(SRC_DIR, L.ROOT_DIR)
        self.source = lbl(f"Nguồn: truyencogiaothao — {SITE}  →  {src}", ACCENT, 11, True)  # update_alicesw.py đổi chữ dòng này
        self.step = lbl("Đang khởi động...", FG, 11, True)
        self.bar = ttk.Progressbar(root, style="P.Horizontal.TProgressbar", mode="determinate")
        self.bar.pack(fill="x", padx=14, pady=(8, 0))
        self.cur = lbl("", MUTED)
        self.counts = lbl("", FG)
        self.show_count({"new": 0, "upd": 0, "chap": 0, "err": 0})
        bar = tk.Frame(root, bg=BG)  # hàng nút xếp trước khung nhật ký ⇒ thu nhỏ cửa sổ không bị che
        bar.pack(side="bottom", fill="x", padx=14, pady=(0, 12))
        self.text = ScrolledText(root, bg=BG2, fg=FG, insertbackground=FG, font=("Consolas", 9), relief="flat", wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, padx=14, pady=8)
        btn = dict(bg=BG3, fg=FG, activebackground=ACCENT, activeforeground="#fff", relief="flat", font=font, padx=16, pady=4, cursor="hand2")
        self.close_btn = tk.Button(bar, text="Đóng", command=self.on_close, **btn)
        self.close_btn.pack(side="right")
        self.stop_btn = tk.Button(bar, text="Dừng", command=self.on_stop, **btn)
        self.stop_btn.pack(side="right", padx=8)
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.poll()

    def _run(self):
        try:
            self.worker.run()
        except Exception as ex:
            import traceback
            self.q.put(("log", traceback.format_exc()))
            self.q.put(("step", f"Lỗi: {ex}"))
        self.q.put(("end",))

    def show_count(self, c):
        self.counts.config(text=f"Truyện mới: {c['new']}   ·   Truyện có chương mới: {c['upd']}   ·   Chương đã tải: {c['chap']}   ·   Lỗi: {c['err']}")

    def add_log(self, line):
        self.text.config(state="normal")
        self.text.insert("end", line + "\n")
        self.text.see("end")
        self.text.config(state="disabled")

    def poll(self):
        try:
            while True:
                kind, *a = self.q.get_nowait()
                if kind == "log": self.add_log(a[0])
                elif kind == "step": self.step.config(text=a[0])
                elif kind == "cur": self.cur.config(text=a[0][:150])
                elif kind == "count": self.show_count(a[0])
                elif kind == "prog": self.bar.config(maximum=max(1, a[1]), value=a[0])
                elif kind == "end":
                    self.stop_btn.config(state="disabled")
                    if self.closing:
                        self.root.destroy()
                        return
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def on_stop(self):
        if self.running():
            self.worker.stop.set()
            self.stop_btn.config(state="disabled")
            self.add_log("[*] Sẽ dừng sau truyện đang tải...")

    def on_close(self):
        # Đang tải ⇒ dừng sau truyện đang tải rồi mới đóng (tắt ngang lúc ghi file ⇒ file truyện dở dang)
        if self.running():
            self.closing = True
            self.on_stop()
            self.close_btn.config(state="disabled", text="Đang dừng...")
        else:
            self.root.destroy()


def main():
    import tkinter as tk
    root = tk.Tk()
    app = App(root)
    sys.stdout = QueueWriter(app.q)
    app.start()
    root.mainloop()


if __name__ == "__main__":
    main()
