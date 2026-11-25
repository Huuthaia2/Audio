// Lịch sử đọc dùng chung nhiều thiết bị — lưu trên máy (localStorage) + đồng bộ qua 1 GitHub Gist bí mật.
// hist = { [uid]: { ch: chương, i: câu, n: số câu của chương, cp: {chương: % đã nghe}, t: thời điểm sửa (ms), done: nghe xong, del: đã xoá } }
// Yêu thích cũng nằm trong hist (khoá "fav:<uid>" = { on, t }) ⇒ đồng bộ chung, gộp theo t như lịch sử.
// Xoá = đánh dấu del (không xoá hẳn) ⇒ đồng bộ sang máy kia không bị máy kia đẩy ngược lại.
// Đồng bộ: tải bản trên Gist ⇒ gộp từng truyện lấy bản mới hơn (t lớn hơn) ⇒ ghi lên ⇒ 2 máy không đè nhau.
// Token GitHub (chỉ quyền "gist") lưu trên từng thiết bị, KHÔNG nằm trong code / repo.

const HIST_FILE = 'kho-truyen-history.json';
let hist = loadHist();

function loadHist() {
  try { const h = JSON.parse(lsGet('hist')); if (h) return h; } catch (e) {}
  // Lần đầu: chuyển dữ liệu cũ (progress_<uid> = {index, time}, tts_pos_<uid> = {ch, i}) sang bảng mới
  const h = {};
  try {
    for (let k = 0; k < localStorage.length; k++) {
      const key = localStorage.key(k);
      if (!key || !key.startsWith('progress_')) continue;
      const uid = key.slice(9);
      const p = JSON.parse(localStorage.getItem(key));
      if (!p) continue;
      h[uid] = { ch: p.index || 0, i: 0, t: p.time || 0 };
      const pos = JSON.parse(localStorage.getItem('tts_pos_' + uid));
      if (pos && pos.ch === h[uid].ch) h[uid].i = pos.i || 0;
    }
  } catch (e) {}
  lsSet('hist', JSON.stringify(h));
  return h;
}

const histGet = (uid) => (hist[uid] && !hist[uid].del ? hist[uid] : null);
// Các mục còn hiệu lực: [[uid, h], ...] mới nhất trước
const histList = () => Object.entries(hist).filter(([k, h]) => !h.del && !k.startsWith('fav:')).sort((a, b) => (b[1].t || 0) - (a[1].t || 0));

// ---- Yêu thích ----
const favOn = (uid) => !!(hist['fav:' + uid] && hist['fav:' + uid].on);
function favToggle(uid) {
  hist['fav:' + uid] = { on: !favOn(uid), t: Date.now() };
  lsSet('hist', JSON.stringify(hist));
  syncSoon();
  return favOn(uid);
}
// Truyện yêu thích, mới thêm trước
const favList = () => Object.entries(hist).filter(([k, h]) => k.startsWith('fav:') && h.on).sort((a, b) => b[1].t - a[1].t).map(([k]) => k.slice(4));
function histSet(uid, patch) {
  const old = hist[uid] && !hist[uid].del ? hist[uid] : { ch: 0, i: 0 };
  hist[uid] = { ...old, ...patch, t: Date.now() };
  lsSet('hist', JSON.stringify(hist));
  syncSoon();
}
function histDel(uids) {
  const t = Date.now();
  for (const uid of uids) hist[uid] = { del: true, t };
  lsSet('hist', JSON.stringify(hist));
  syncSoon();
}
// Tiến độ 0..1 của truyện: (số chương trước chương đang nghe + phần đã nghe của chương đó) / tổng chương
function histPct(h, chapters) {
  if (!h) return 0;
  if (h.done) return 1;
  if (!chapters) return 0;
  return Math.min(1, ((h.ch || 0) + (h.n ? (h.i || 0) / h.n : 0)) / chapters);
}
function histMerge(remote) {
  let changed = false;
  for (const [uid, r] of Object.entries(remote || {})) {
    const l = hist[uid];
    if (!l || (r.t || 0) > (l.t || 0)) { hist[uid] = r; changed = true; }
  }
  if (changed) {
    lsSet('hist', JSON.stringify(hist));
    window.dispatchEvent(new Event('histchange'));
  }
  return changed;
}

// =====================================================================
// Đồng bộ GitHub Gist
// =====================================================================
const sync = { token: lsGet('gistToken') || '', id: lsGet('gistId') || '', state: 'off', dirty: false, busy: null, timer: null };

async function gh(path, opt = {}) {
  const res = await fetch('https://api.github.com' + path, {
    ...opt,
    cache: 'no-store',
    headers: { Authorization: 'Bearer ' + sync.token, Accept: 'application/vnd.github+json', ...(opt.body ? { 'Content-Type': 'application/json' } : {}) },
  });
  if (!res.ok) throw new Error(res.status === 401 ? 'Token sai hoặc đã hết hạn' : `GitHub báo lỗi ${res.status}`);
  return res.json();
}

// Tìm Gist lịch sử đã có (máy thứ 2 dùng lại đúng Gist của máy 1); chưa có thì tạo Gist bí mật mới
async function findOrCreateGist() {
  for (let page = 1; page <= 5; page++) {
    const list = await gh(`/gists?per_page=100&page=${page}`);
    const g = list.find((x) => x.files && x.files[HIST_FILE]);
    if (g) return g.id;
    if (list.length < 100) break;
  }
  const g = await gh('/gists', {
    method: 'POST',
    body: JSON.stringify({ description: 'Kho Truyện — lịch sử đọc (tự đồng bộ)', public: false, files: { [HIST_FILE]: { content: JSON.stringify(hist) } } }),
  });
  return g.id;
}

async function pullHist() {
  const g = await gh('/gists/' + sync.id);
  const f = g.files[HIST_FILE];
  if (!f) return;
  let txt = f.content;
  if (f.truncated) txt = await (await fetch(f.raw_url, { cache: 'no-store' })).text();
  histMerge(JSON.parse(txt || '{}'));
}

async function pushHist(keepalive = false) {
  await gh('/gists/' + sync.id, { method: 'PATCH', keepalive, body: JSON.stringify({ files: { [HIST_FILE]: { content: JSON.stringify(hist) } } }) });
}

function setSyncState(st, msg = '') {
  sync.state = st;
  sync.msg = msg;
  const b = $('syncBtn');
  if (!b) return;
  b.className = 'icon-btn round sync-' + st;
  b.title = { off: 'Đồng bộ lịch sử: chưa bật', busy: 'Đang đồng bộ...', ok: 'Đã đồng bộ lịch sử', err: 'Lỗi đồng bộ: ' + msg }[st];
}

// Đồng bộ ngay: tải về + gộp, nếu máy này có thay đổi thì ghi lên
async function syncNow() {
  if (!sync.token || !sync.id) return;
  if (sync.busy) return sync.busy;
  sync.busy = (async () => {
    setSyncState('busy');
    try {
      await pullHist();
      if (sync.dirty) { sync.dirty = false; await pushHist(); }
      setSyncState('ok');
    } catch (e) {
      sync.dirty = true;
      setSyncState('err', e.message);
    } finally { sync.busy = null; }
  })();
  return sync.busy;
}
// Hẹn đồng bộ. KHÔNG huỷ hẹn cũ khi có thay đổi mới (trước đây mỗi câu đọc xong lại huỷ ⇒ nghe liên tục thì không bao giờ
// đẩy lên). Đang nghe ⇒ 60s / lần (mỗi lần ghi Gist = 1 phiên bản lưu trên GitHub, 8s / lần ⇒ 450 phiên bản / giờ);
// không nghe ⇒ 8s. soon = true (vd vừa bấm dừng) ⇒ đẩy sau 3s.
function syncSoon(soon = false) {
  sync.dirty = true;
  if (!sync.token) return;
  const delay = soon ? 3000 : (typeof playing !== 'undefined' && playing ? 60000 : 8000);
  if (sync.timer && !soon) return;
  clearTimeout(sync.timer);
  sync.timer = setTimeout(() => { sync.timer = null; syncNow(); }, delay);
}

// Rời tab / tắt màn hình ⇒ ghi lên ngay (keepalive: trình duyệt vẫn gửi nốt dù trang bị đóng băng)
document.addEventListener('visibilitychange', () => {
  if (!sync.token || !sync.id) return;
  if (document.visibilityState === 'hidden') {
    if (sync.dirty) { sync.dirty = false; clearTimeout(sync.timer); sync.timer = null; pushHist(true).catch(() => { sync.dirty = true; }); }
  } else syncNow();
});

// ---- Hộp cài đặt đồng bộ ----
function openSyncModal() {
  $('syncToken').value = sync.token;
  $('syncInfo').textContent = sync.id
    ? (sync.state === 'err' ? 'Lỗi: ' + sync.msg : 'Đang đồng bộ với Gist ' + sync.id.slice(0, 8) + '…')
    : 'Chưa bật đồng bộ — lịch sử chỉ lưu trên máy này.';
  $('syncOff').hidden = !sync.token;
  $('syncModal').hidden = false;
}
$('syncBtn').onclick = openSyncModal;
$('syncClose').onclick = () => { $('syncModal').hidden = true; };
$('syncModal').onclick = (e) => { if (e.target.id === 'syncModal') $('syncModal').hidden = true; };
$('syncSave').onclick = async () => {
  const tok = $('syncToken').value.trim();
  if (!tok) return;
  sync.token = tok;
  $('syncInfo').textContent = 'Đang kết nối...';
  try {
    sync.id = await findOrCreateGist();
    lsSet('gistToken', tok);
    lsSet('gistId', sync.id);
    sync.dirty = true;
    await syncNow();
    if (sync.state === 'err') throw new Error(sync.msg);
    $('syncModal').hidden = true;
    showToast('Đã bật đồng bộ lịch sử', 'success');
  } catch (e) {
    $('syncInfo').textContent = 'Lỗi: ' + e.message;
    // Dán nhầm token ⇒ giữ lại kết nối cũ (nếu có), không để máy mất đồng bộ
    sync.token = lsGet('gistToken') || '';
    sync.id = lsGet('gistId') || '';
    setSyncState(sync.id ? 'ok' : 'off');
  }
};
$('syncOff').onclick = () => {
  sync.token = sync.id = '';
  try { localStorage.removeItem('gistToken'); localStorage.removeItem('gistId'); } catch (e) {}
  setSyncState('off');
  $('syncModal').hidden = true;
  showToast('Đã tắt đồng bộ trên máy này');
};

setSyncState(sync.token && sync.id ? 'ok' : 'off');
syncNow();
