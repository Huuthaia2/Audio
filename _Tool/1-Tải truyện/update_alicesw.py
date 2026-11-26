# Tự động cập nhật nguồn alicesw (https://www.alicesw.com, tiếng Trung → dịch Google) — chạy bằng
# "_Tool/5. Tải truyện alicesw.bat" (--chi-tai) và "_Tool/6. Dịch truyện alicesw.bat" (--chi-dich). Tải + dịch nằm ở repo riêng Documents/zzz/alicesw (thư mục cạnh repo Audio),
# repo Audio chỉ nhận bản dịch qua sync_alicesw.py. Chạy TUẦN TỰ 4 bước (downloader và translator ghi chung file
# trạng thái trong alicesw/downloaded ⇒ không được chạy song song):
#   1. Quét trang danh sách tag 母子 1 lần + tải truyện mới (như alicesw_downloader.py --all của run_download.bat)
#   2. Truyện đang ra (origin chưa _end) có "ngày cập nhật" trên danh sách khác lần trước ⇒ đếm chương; có chương
#      mới ⇒ tách file cũ ra cache chương (gốc + bản dịch) rồi tải lại ⇒ chỉ tải chương mới, bước 3 chỉ dịch chương mới
#   3. Dịch Google (alicesw_translate.py, đúng lệnh run_translate.bat)
#   4. sync_alicesw.py + update_index.py (KHÔNG push) — luôn chạy, kể cả khi bấm Dừng
# alicesw CHẶN khi truy cập nhanh ⇒ mọi request tuần tự, nghỉ DELAY giữa các request, tải chương 1 luồng.
# Bước 1+2 chạy chính file này ở tiến trình con (dùng chung 1 lần quét danh sách):
#   python update_alicesw.py --tai [--chi-kiem] [--vpn auto|warp|protonvpn|none]
#   --chi-kiem: chỉ quét danh sách, in số truyện mới / ứng viên chương mới, không tải, không ghi gì
import os
import re
import sys
import json
import time
import threading
import subprocess

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(TOOL_DIR))  # _Tool/1-Tải truyện/ -> gốc repo Audio
ALICE_DIR = os.path.join(os.path.dirname(ROOT_DIR), "alicesw")  # repo tải + dịch (cạnh repo Audio)
WEB_TOOL_DIR = os.path.join(os.path.dirname(TOOL_DIR), "2-Cập nhật web")
# {"dates": {id: ngày cập nhật trên danh sách lúc đã kiểm xong}} — ngày đổi ⇒ truyện có thể có chương mới
STATE_FILE = os.path.join(TOOL_DIR, "alicesw_update_state.json")
SITE = "https://www.alicesw.com"
# tag "mẹ con" như run_download.bat, sắp theo NGÀY CẬP NHẬT mới trước (anh Thai chốt 2026-11-26) ⇒ gặp trang toàn truyện
# cập nhật trước mốc thì dừng quét (~20 trang thay vì 228 trang). Mốc = ngày HÔM TRƯỚC của lần tải trót lọt gần nhất
# (state "last_run", anh Thai chốt 2026-11-26 — lùi 1 ngày cho thư thả); chưa có last_run ⇒ STOP_BEFORE.
LIST_URL = SITE + "/search?q=母子&f=tag&sort=update_time_DESC"
STOP_BEFORE = "2026-05-01"
OUT_REL = os.path.join("Truyện", "4-alicesw")
STEPS = 4
DL_WORKERS = 4  # 4 luồng như run_download.bat (anh Thai chốt 2026-11-26: 1 luồng quá chậm); bị chặn ⇒ downloader tự đổi IP WARP
MAX_FAILS = 5  # lỗi liền 5 truyện khi kiểm chương ⇒ coi như bị chặn, dừng bước 2 (lần sau làm tiếp)
CHAPTER_LINE = re.compile(r"\[\s*\d+/\s*\d+\]")  # dòng tiến độ từng chương "[  3/20] OK ..." ⇒ chỉ hiện ở dòng đang làm


def save_json(path, data):
    """Ghi JSON kiểu .tmp + os.replace; Windows hay báo PermissionError khi file đích bị mở thoáng qua
    (diệt virus, VS Code — lỗi thật 2026-11-25) ⇒ thử lại 20 lần × 0,25s rồi ghi thẳng"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    for _ in range(20):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.25)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    try: os.remove(tmp)
    except OSError: pass


# =====================================================================
# Bước 2 (tiến trình con, cwd = thư mục alicesw): truyện đang ra có chương mới ⇒ tải lại
# In "@@prog a b" / "@@cur text" / "@@count key n" cho GUI; dòng khác ⇒ nhật ký.
# =====================================================================
def read_origin(path):
    """Đầu file origin ⇒ (id truyện, số chương) — (None, 0) nếu không đọc được"""
    with open(path, encoding="utf-8", errors="replace") as f:
        head = f.read(2000)
    m = re.search(r"alicesw\.com/novel/(\d+)", head)
    n = re.search(r"^\s*Chương\s*:\s*(\d+)", head, re.M) or re.search(r"\+(\d+) Chuong_origin", os.path.basename(path))
    return (m.group(1) if m else None), (int(n.group(1)) if n else 0)


def scan_ongoing(origin_dir, origin_done):
    """{id: (số chương, tên file)} các truyện chưa _end. id nào đã có bản _end ⇒ bỏ.
    Trùng id (2 file khác tên do dịch tên 2 lần) ⇒ ưu tiên file ghi trong _origin_progress, rồi file nhiều chương hơn."""
    ongoing, ended = {}, set()
    for name in os.listdir(origin_dir):
        if "_origin" not in name or not name.endswith(".txt"):
            continue  # bỏ file "_khong_lay_duoc_chuong.txt"
        nid, n = read_origin(os.path.join(origin_dir, name))
        if not nid:
            continue
        if name.endswith("_origin_end.txt"):
            ended.add(nid)
            continue
        cur = ongoing.get(nid)
        if not cur or (origin_done.get(nid) == name, n) > (origin_done.get(nid) == cur[1], cur[0]):
            ongoing[nid] = (n, name)
    for nid in ended:
        ongoing.pop(nid, None)
    return ongoing


SEP_CHAPTER = "\n\n" + "─" * 50 + "\n"  # write_full_book(separators=True) ghi dòng này trước mỗi chương


def split_book(path):
    """File origin / bản dịch (write_full_book separators=True) ⇒ [nội dung chương 1..N] đúng từng ký tự như
    lúc tool ghi vào cache: "<tên chương>\\n────(40)\\n\\n<nội dung>\\n" (origin) / "<tên>\\n\\n<nội dung>\\n" (bản dịch).
    Đọc text mode (CRLF ⇒ \\n) giống read_text của tool."""
    with open(path, encoding="utf-8") as f:
        return f.read().split(SEP_CHAPTER)[1:]


def translated_by_id(trans_dir):
    """{id: [(số chương, đường dẫn)]} mọi bản dịch (cả thư mục con Lục Mẫu/, NTR/)"""
    found = {}
    for root, _, files in os.walk(trans_dir):
        for name in files:
            if name.endswith(".txt") and not name.startswith("_"):
                nid, n = read_origin(os.path.join(root, name))
                if nid:
                    found.setdefault(nid, []).append((n, os.path.join(root, name)))
    return found


def seed_cache(out, nid, origin_name, n, translations):
    """File cũ có đủ N chương ⇒ tách ra cache chương của downloader (.cache/<id>/000001_orig.txt...) và của
    bộ dịch (.cache_translate/<id>/000001_trans.txt...) ⇒ chỉ tải + dịch chương mới. Số chương tách ra ≠ N ⇒ không
    ghi (tool tải / dịch lại cả truyện như cũ). Cache đã có file ⇒ để nguyên."""
    cache = out / ".cache" / nid
    if not any(cache.glob("*_orig.txt")):
        chs = split_book(out / "origin" / origin_name)
        if len(chs) == n:
            cache.mkdir(parents=True, exist_ok=True)
            for i, c in enumerate(chs, 1):
                (cache / f"{i:06d}_orig.txt").write_text(c, encoding="utf-8")
            print(f"  [cache] Tách {n} chương cũ từ bản gốc ⇒ chỉ tải chương mới.")
        else:
            print(f"  [!] Bản gốc tách được {len(chs)} chương ≠ {n} ⇒ tải lại cả truyện.")
    tcache = out / ".cache_translate" / nid
    path = next((p for k, p in translations if k == n), None)
    if path and not any(tcache.glob("*_trans.txt")):
        chs = split_book(path)
        if len(chs) == n:
            tcache.mkdir(parents=True, exist_ok=True)
            for i, c in enumerate(chs, 1):
                (tcache / f"{i:06d}_trans.txt").write_text(c, encoding="utf-8")
            print(f"  [cache] Tách {n} chương đã dịch ⇒ chỉ dịch chương mới.")
        else:
            print(f"  [!] Bản dịch tách được {len(chs)} chương ≠ {n} ⇒ dịch lại cả truyện.")
    elif not path:
        print(f"  [!] Không thấy bản dịch {n} chương ⇒ dịch lại cả truyện.")


def tai_truyen(only_check=False, vpn="auto"):
    """Bước 1 + 2 trong 1 tiến trình con (cwd = thư mục alicesw), quét danh sách đúng 1 lần."""
    from pathlib import Path
    os.chdir(ALICE_DIR)
    sys.path.insert(0, ALICE_DIR)
    import alicesw_downloader as dl

    out = Path("downloaded")
    if vpn == "auto":  # như downloader --vpn auto
        vpn = ("protonvpn" if (dl.PROTON_CLI or dl.PROTON_SERVICE) else
               "warp" if os.path.exists(r"C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe") else "none")
    dl.VPN_TYPE = "none" if only_check else vpn
    if dl.VPN_TYPE != "none":
        print(f"[*] Bị chặn / CAPTCHA ⇒ tool tự đổi IP qua {dl.VPN_TYPE}.")
    delay = dl.DELAY
    st = dl.load_state(out)
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
    except (FileNotFoundError, ValueError):
        state = {}
    dates = state.setdefault("dates", {})
    from datetime import datetime, timedelta
    run_start = datetime.now().strftime("%Y-%m-%d %H:%M")
    last = state.get("last_run")
    stop_before = ((datetime.strptime(last[:10], "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                   if last else STOP_BEFORE)
    print(f"[*] Lần tải trót lọt gần nhất: {last or 'chưa có'} ⇒ chỉ quét truyện cập nhật từ {stop_before}.", flush=True)
    had_err = False  # có lỗi ⇒ KHÔNG dời mốc last_run (lần sau còn quét lại đoạn này)

    # ---------- Bước 1: truyện lỗi lần trước + quét danh sách + tải truyện mới ----------
    print("@@step 1 Quét danh sách + tải truyện mới", flush=True)
    if not only_check:
        dl.retry_failed(out, delay, False, st, out, workers=DL_WORKERS)  # như downloader làm lúc bắt đầu
    seen, pages_ok, total_pages, k, new = {}, set(), 0, 0, 0
    for page, total_pages, novels in dl.iter_listing_pages(LIST_URL):
        pages_ok.add(page)
        print(f"\n── Trang {page}/{total_pages} ({len(novels)} truyen) ──", flush=True)
        for stub in novels:
            m = re.search(r"/novel/(\d+)", stub["novel_url"])
            if not m:
                continue
            seen[m.group(1)] = stub.get("update_date") or "?"
            k += 1
            if dl._is_fully_done(m.group(1), st, False):
                print(f"[#{k}] (da xong) {stub['title'][:40]} - bo qua")
            elif only_check:
                new += 1
                print(f"[#{k}] (moi) {stub['title']}")
            else:
                dl._process_stubs([stub], out, delay, False, st, out, label=f"#{k}", workers=DL_WORKERS)
                if m.group(1) in st["origin_done"] and m.group(1) not in st["origin_fail"]:
                    dates[m.group(1)] = seen[m.group(1)]  # vừa tải đủ ⇒ bước 2 khỏi kiểm lại
                    save_json(STATE_FILE, state)
                else:
                    had_err = True
        page_dates = [(s.get("update_date") or "?")[:10] for s in novels]
        if page_dates and all(d[:4].isdigit() and d < stop_before for d in page_dates):
            by_date = True
            print(f"[*] Trang {page}: mọi truyện cập nhật trước {stop_before} ⇒ dừng quét danh sách.", flush=True)
            break
    else:
        by_date = False
    # Dừng theo ngày ⇒ truyện không thấy trong danh sách = không cập nhật từ STOP_BEFORE, không phải "không có trong tag"
    full_scan = total_pages > 0 and len(pages_ok) == total_pages and not by_date
    print(f"\n[*] Danh sách: {len(pages_ok)}/{total_pages} trang, {len(seen)} truyện"
          + (f", {new} truyện mới chưa tải" if only_check else "")
          + ("" if full_scan or by_date else " — CHƯA quét đủ trang (lỗi mạng / bị chặn)") + ".", flush=True)

    # ---------- Bước 2: truyện đang ra có ngày cập nhật khác lần kiểm trước ⇒ đếm chương ----------
    print("@@step 2 Kiểm truyện đang ra có chương mới", flush=True)
    if not seen:
        print("[!] Không đọc được trang danh sách nào (mạng lỗi / bị chặn) ⇒ bỏ qua bước 2, lần sau chạy lại.", flush=True)
        print("@@count err 1", flush=True)
        return 0
    ongoing = scan_ongoing(out / "origin", st["origin_done"])
    missing = [nid for nid in ongoing if nid not in seen] if full_scan else []
    cand = sorted((nid for nid in ongoing if nid in seen and (seen[nid] == "?" or dates.get(nid) != seen[nid])),
                  key=lambda i: ongoing[i][1])
    print(f"[*] {len(ongoing)} truyện đang ra (chưa _end): {len(cand)} có ngày cập nhật khác lần kiểm trước ⇒ đếm chương"
          + (f"; {len(missing)} truyện không có trong danh sách tag 母子 ⇒ bỏ qua" if missing else "") + ".", flush=True)
    if only_check:
        for nid in cand[:20]:
            print(f"    {ongoing[nid][1]}  (web cập nhật {seen[nid]}, lần trước {dates.get(nid, 'chưa kiểm')})")
        return 0

    translations, fails = None, 0
    for i, nid in enumerate(cand, 1):
        old_n, name = ongoing[nid]
        print(f"@@prog {i - 1} {len(cand)}", flush=True)
        print(f"@@cur Kiểm {i}/{len(cand)}: {name[:100]}", flush=True)
        chapters = dl.get_chapter_list(nid)
        time.sleep(delay)
        if not chapters:
            fails += 1
            had_err = True
            print(f"  [!] {name}: không lấy được danh sách chương ({fails} lần liền).", flush=True)
            if fails >= MAX_FAILS:
                print(f"[!] Lỗi {MAX_FAILS} truyện liền ⇒ có thể đang bị chặn, dừng bước 2 (lần sau làm tiếp).", flush=True)
                print("@@count err 1", flush=True)
                break
            time.sleep(30 * fails)  # lùi dần: 30s, 60s, 90s...
            continue
        fails = 0
        if len(chapters) <= old_n:
            dates[nid] = seen[nid]  # không có chương mới ⇒ ghi nhận ngày, lần sau không kiểm lại
            if i % 10 == 0:
                save_json(STATE_FILE, state)
            continue

        print(f"\n[{i}/{len(cand)}] {name} ({old_n} → {len(chapters)} chương)", flush=True)
        info = dl.get_novel_info(f"{dl.BASE_URL}/novel/{nid}.html")
        if not info:
            print("  [!] Không lấy được thông tin truyện — lần sau thử lại.", flush=True)
            print("@@count err 1", flush=True)
            had_err = True
            continue
        # Giữ đúng tên Việt cũ: cache tên đã mất ⇒ downloader dịch lại tên, ra tên khác ⇒ thành 2 file cùng truyện
        # (bản cũ không bị dọn). Ghi sẵn tên cũ vào cache ⇒ file mới cùng tên, downloader tự xoá bản cũ.
        m = re.match(r"^(.*?)\+\d+\s+Chuong_origin", name)
        title_cache = out / ".cache" / nid / "title_vi.txt"
        if m and not title_cache.exists():
            title_cache.parent.mkdir(parents=True, exist_ok=True)
            title_cache.write_text(m.group(1).strip(), encoding="utf-8")
        if translations is None:
            translations = translated_by_id(out / "translated")
        seed_cache(out, nid, name, old_n, translations.get(nid, []))
        dl._record_result(info, out, delay, False, st, out, workers=DL_WORKERS, skip_translated=False,
                          label=f"{i}/{len(cand)}")
        if nid in st["origin_done"] and nid not in st["origin_fail"]:
            dates[nid] = seen[nid]
            save_json(STATE_FILE, state)
            print(f"  [+] {st['origin_done'][nid]}", flush=True)
            print("@@count upd 1", flush=True)
        else:
            print("@@count err 1", flush=True)  # không ghi ngày ⇒ lần sau kiểm lại
            had_err = True
        time.sleep(delay)
    if (full_scan or by_date) and not had_err:  # trót lọt ⇒ lần sau chỉ quét từ hôm trước ngày này
        state["last_run"] = run_start
        print(f"[*] Ghi mốc lần tải: {run_start} (lần sau quét truyện cập nhật từ hôm trước ngày này).", flush=True)
    else:
        print(f"[*] Có lỗi / chưa quét đủ ⇒ giữ mốc cũ ({last or 'chưa có'}) để lần sau quét lại.", flush=True)
    save_json(STATE_FILE, state)
    print(f"@@prog {len(cand)} {len(cand)}", flush=True)
    return 0


# =====================================================================
# Luồng chạy chính của GUI (luồng nền): chạy từng bước bằng tiến trình con, đọc stdout từng dòng
# =====================================================================
class AliceUpdater:
    def __init__(self, ui):
        self.ui = ui  # ui(kind, *args): log / step / prog / cur / count
        self.stop = threading.Event()
        self.count = {"new": 0, "upd": 0, "trans": 0, "err": 0}
        self.proc = None
        self.killable = False  # chỉ bước 1–3 bị tắt khi bấm Dừng (bước 4 ngắn, để chạy xong)
        self.lock = threading.Lock()
        self.trans_total = self.trans_done = 0
        self.cur_step = 0

    def log(self, msg):
        self.ui("log", msg)

    def bump(self, k, n=1):
        self.count[k] += n
        self.ui("count", dict(self.count))

    def step(self, i, text):
        self.cur_step = i
        self.ui("step", f"Bước {i}/{STEPS}: {text}")

    def run(self):
        if not os.path.isfile(os.path.join(ALICE_DIR, "alicesw_downloader.py")):
            self.log(f"[!] Không thấy repo alicesw ở {ALICE_DIR} (phải nằm cạnh thư mục Audio).")
            self.ui("step", "Lỗi: không thấy thư mục alicesw")
            return
        self.log(f"[*] Thư mục tải + dịch: {ALICE_DIR}")
        self.log("[*] Lưu ý VPN: khi bị chặn, tool đổi IP WARP ⇒ mạng cả máy rớt vài giây.")
        py = [sys.executable, "-u"]

        # Tải và dịch tách 2 bat (anh Thai chốt 2026-11-26): bat 5 "--chi-tai" = bước 1–2, bat 6 "--chi-dich" = bước 3–4
        mode = "tai" if "--chi-tai" in sys.argv else "dich" if "--chi-dich" in sys.argv else "all"
        if mode != "dich" and not self.stop.is_set():  # bước 1 + 2: 1 tiến trình con, quét danh sách 1 lần (báo bước qua "@@step")
            self.step(1, "Quét danh sách + tải truyện mới")
            self.run_proc(py + [os.path.abspath(__file__), "--tai", "--vpn", "auto"], ALICE_DIR,
                          self.on_download, killable=True)
        if mode == "tai":
            c = self.count
            self.ui("step", ("Đã dừng" if self.stop.is_set() else "Tải xong") + f" — {c['new']} truyện mới, "
                    f"{c['upd']} truyện có chương mới, {c['err']} lỗi")
            self.log("[OK] Tải xong bản gốc. Muốn dịch + đưa lên web: chạy \"6. Dịch truyện alicesw.bat\".")
            return
        if not self.stop.is_set():
            self.step(3, "Dịch Google")
            self.ui("prog", 0, 1)
            self.run_proc(py + ["alicesw_translate.py", "--file-workers", "3", "--engine", "google", "--retry-failed",
                                "--vpn", "warp"], ALICE_DIR, self.on_translate, killable=True)

        stopped = self.stop.is_set()
        self.step(4, "Đồng bộ Truyện\\4-alicesw + làm lại stories.json")
        self.ui("cur", "")
        for script in ("sync_alicesw.py", "update_index.py"):
            self.log(f"\n[*] Chạy {script}...")
            self.run_proc(py + [os.path.join(WEB_TOOL_DIR, script)], ROOT_DIR, lambda line: self.log("    " + line))
        c = self.count
        self.ui("step", ("Đã dừng" if stopped else "Xong") + f" — {c['new']} truyện mới, {c['upd']} truyện có chương mới, "
                f"{c['trans']} truyện đã dịch, {c['err']} lỗi")
        self.log("[OK] Xong. Muốn đưa lên web online: chạy \"2. Cập nhật web.bat\" (bước push).")

    def run_proc(self, args, cwd, on_line, killable=False):
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with self.lock:
            if killable and self.stop.is_set():
                return
            self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                         text=True, encoding="utf-8", errors="replace", cwd=cwd,
                                         env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"},
                                         creationflags=flags)
            self.killable = killable
        p = self.proc
        for line in p.stdout:  # text mode: "\r" (dòng tiến độ in đè) cũng tách thành dòng riêng
            line = line.rstrip()
            if line.strip():
                on_line(line)
        p.wait()
        with self.lock:
            self.proc, self.killable = None, False
        if p.returncode and not self.stop.is_set():
            self.log(f"[!] {os.path.basename(args[2])} báo lỗi (mã {p.returncode}).")
            self.bump("err")

    def kill(self):
        """Tắt cả cây tiến trình con (python + warp-cli...) đang chạy ở bước 1–3"""
        with self.lock:
            p = self.proc if self.killable else None
        if p and p.poll() is None:
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    # --- đọc dòng của từng bước ---
    def on_download(self, line):
        """Bước 1 + 2 (update_alicesw.py --tai)"""
        s = line.strip()
        if s.startswith("@@"):
            kind, _, rest = s[2:].partition(" ")
            if kind == "step":
                i, _, text = rest.partition(" ")
                self.step(int(i), text)
                self.ui("prog", 0, 1)
            elif kind == "prog":
                a, b = rest.split()
                self.ui("prog", int(a), int(b))
            elif kind == "cur":
                self.ui("cur", rest)
            elif kind == "count":
                k, n = rest.split()
                self.bump(k, int(n))
            return
        m = re.match(r"── Trang (\d+)/(\d+)", s)
        if m:
            self.ui("prog", int(m.group(1)), int(m.group(2)))
            self.step(1, f"Quét danh sách + tải truyện mới — trang {m.group(1)}/{m.group(2)}")
            self.ui("cur", s)
            return
        if "(da xong)" in s or "Dang tai trang" in s or s.startswith("[Loi]") or CHAPTER_LINE.search(s):
            self.ui("cur", s)
            return
        if "Ban goc :" in s and self.cur_step == 1:  # bước 1: tải xong 1 truyện mới (bước 2 tự đếm qua @@count)
            self.bump("new")
        self.log(line)

    def on_translate(self, line):
        s = line.strip()
        m = re.search(r"Hang doi dich: (\d+) file", s)
        if m:
            self.trans_total = int(m.group(1))
            self.ui("prog", 0, max(1, self.trans_total))
        if s.startswith("[>] "):
            self.ui("cur", "Đang dịch: " + s[4:])
        elif "Ban dich:" in s:
            self.trans_done += 1
            self.bump("err" if "con loi" in s else "trans")
            self.ui("prog", self.trans_done, max(1, self.trans_total))
            self.step(3, f"Dịch Google — {self.trans_done}/{self.trans_total} truyện")
        elif CHAPTER_LINE.search(s) or "Dang dich" in s:
            self.ui("cur", s)
            return
        self.log(line)


# =====================================================================
# GUI: dùng lại khung cửa sổ của update_truyencogiaothao.py (màu, nhật ký, Dừng / Đóng)
# =====================================================================
def make_app(root):
    sys.path.insert(0, TOOL_DIR)
    import update_truyencogiaothao as G

    class AliceApp(G.App):
        def __init__(self, root):
            super().__init__(root, AliceUpdater)
            root.title("Tự động cập nhật truyện — alicesw")
            self.source.config(text=f"Nguồn: alicesw — {SITE} (tiếng Trung → dịch Google)  →  {OUT_REL}")
            self.show_count(self.worker.count)

        def show_count(self, c):
            self.counts.config(text=f"Truyện mới: {c.get('new', 0)}   ·   Truyện có chương mới: {c.get('upd', 0)}   ·   "
                                    f"Đã dịch: {c.get('trans', 0)}   ·   Lỗi: {c.get('err', 0)}")

        def on_stop(self):
            # Tắt ngay tiến trình đang chạy (downloader tự lưu tiến độ sau mỗi truyện; truyện đang tải dở thì
            # lần sau tải lại), rồi vẫn chạy bước 4 để web khớp với bản dịch đang có
            if self.running():
                self.worker.stop.set()
                self.stop_btn.config(state="disabled")
                self.add_log("[*] Dừng: tắt tiến trình đang chạy, rồi đồng bộ web (bước 4)...")
                threading.Thread(target=self.worker.kill, daemon=True).start()

    return AliceApp(root)


def main():
    if "--tai" in sys.argv:
        vpn = sys.argv[sys.argv.index("--vpn") + 1] if "--vpn" in sys.argv else "auto"
        sys.exit(tai_truyen(only_check="--chi-kiem" in sys.argv, vpn=vpn))
    import tkinter as tk
    root = tk.Tk()
    app = make_app(root)
    app.start()
    root.mainloop()


if __name__ == "__main__":
    main()
