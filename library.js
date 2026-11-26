// Màn danh sách (#/) + màn lịch sử (#/history) — hiển thị theo phần Audio của Local Cinema.
// Danh sách: Đang nghe dở · Nguồn (thư mục cấp 1) · Tag (thể loại) · danh sách chia trang.
// Nguồn: 1-Text Mp3, 2-truyencogiaothao, alicesw (phần đầu uid).
// Tag của truyện = thể loại (story.category) + tag trên trang nguồn (story.tags). Chọn NHIỀU tag ⇒ truyện phải có ĐỦ.

const PER_PAGE = 50;
let allStories = [];
let byUid = new Map();
let sortedByName = [], sortedBySize = [], sortedByNew = []; // sắp sẵn 1 lần lúc tải; lọc giữ nguyên thứ tự ⇒ không phải sắp lại mỗi lần gõ
let filtered = [];
let lib = { src: 'all', tags: [], sort: 'name', page: 1, hideDone: false };
let showAllTags = false;           // "Xem tất cả tag": mặc định chỉ 2 dòng
const SKIP_TAGS = new Set(['R-18', 'Tiếng Trung']); // không phải thể loại (anh Thai chốt 2026-11-25)
let libScroll = 0;
let libReady = false;

function removeAccents(str) {
  if (!str) return '';
  return str.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
}

async function ensureStories() {
  if (libReady) return true;
  try { allStories = await STORIES; } catch (e) {
    $('loading').innerHTML = 'Không tải được danh sách truyện. Hãy đảm bảo file stories.json tồn tại!';
    return false;
  }
  byUid = new Map(allStories.map((s) => [s.uid, s]));
  // Tên + tên file + tag đã bỏ dấu tính sẵn 1 lần (trước đây mỗi lần gõ tìm bỏ dấu lại cả 4512 truyện)
  for (const s of allStories) {
    s._q = removeAccents(s.title) + '|' + removeAccents(s.file) + (s.tags ? '|' + removeAccents(s.tags.join('|')) : '');
    s._tags = new Set([s.category, ...(s.tags || [])].filter((t) => t && !SKIP_TAGS.has(t)));
  }
  sortedByName = [...allStories].sort((a, b) => a.title.localeCompare(b.title, 'vi'));
  sortedBySize = [...allStories].sort((a, b) => b.size - a.size);
  // Mới cập nhật: theo t (ngày chương mới nhất) giảm dần, truyện không có ngày xếp cuối; cùng ngày giữ thứ tự tên
  sortedByNew = [...sortedByName].sort((a, b) => (b.t || '').localeCompare(a.t || ''));
  restoreLibState();
  libReady = true;
  return true;
}

// ---- Nhớ trạng thái (tải lại trang / mở lại tab vẫn đúng chỗ) ----
function saveLibState() {
  sessionStorage.setItem('libraryState', JSON.stringify({ ...lib, search: $('searchInput').value, scroll: libScroll }));
}
function restoreLibState() {
  try {
    const st = JSON.parse(sessionStorage.getItem('libraryState'));
    if (!st) return;
    const old = st.tag || st.cat; // bản cũ chỉ lọc 1 tag (chuỗi)
    lib = { src: st.src || 'all', tags: Array.isArray(st.tags) ? st.tags : old && old !== 'all' ? [old] : [],
      sort: st.sort || 'name', page: st.page || 1, hideDone: !!st.hideDone };
    $('searchInput').value = st.search || '';
    libScroll = st.scroll || 0;
  } catch (e) {}
}

// Gọi mỗi lần hiện màn danh sách
async function libShow() {
  const first = !libReady;
  if (!(await ensureStories())) return;
  if (first || !$('storyList').children.length) applyFilter(false);
  else libRefresh();
  clampTags();
  requestAnimationFrame(() => window.scrollTo(0, libScroll));
}
function libLeave() { libScroll = window.scrollY; saveLibState(); }
// Lịch sử đổi (nghe tiếp, đồng bộ từ máy khác) ⇒ vẽ lại, giữ nguyên trang + chỗ cuộn
function libRefresh() {
  if (!libReady) return;
  if (lib.hideDone) { applyFilter(false); return; }
  renderResume();
  renderPage();
}

// ---- Nguồn + Tag ----
function renderFilters() {
  const srcCount = {};
  allStories.forEach((s) => srcCount[sourceOf(s)] = (srcCount[sourceOf(s)] || 0) + 1);
  const ORDER = ['Text Mp3', 'truyencogiaothao', 'alicesw']; // nguồn mới thêm xếp sau
  const rank = (k) => (ORDER.includes(k) ? ORDER.indexOf(k) : ORDER.length);
  const srcs = Object.keys(srcCount).sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
  $('srcHead').textContent = `Nguồn (${srcs.length})`;
  $('srcList').innerHTML = srcs.map((k) => `<button class="fcard${lib.src === k ? ' on' : ''}" data-src="${esc(k)}">
      <div class="fimg">${icon('folder')}</div>
      <div><div class="fname">${esc(k)}</div><div class="fcount">${srcCount[k]} truyện</div></div>
    </button>`).join('');

}

// Khu Tag (anh Thai chốt 2026-11-25): tối đa 2 DÒNG — "Tất cả", tag đang chọn (bấm lại để bỏ), rồi tag nhiều truyện nhất.
// Số trên tag = số truyện trong KẾT QUẢ ĐANG LỌC (chọn thêm tag là thu hẹp dần). "Xem tất cả tag" / gõ ô tìm tag ⇒ mở hết.
function renderTags(baseCount) {
  const count = new Map();
  for (const s of filtered) for (const t of s._tags) count.set(t, (count.get(t) || 0) + 1);
  const tq = removeAccents($('tagSearch').value.trim());
  const rest = [...count].filter(([t]) => !lib.tags.includes(t)).sort((a, b) => b[1] - a[1]);
  const open = showAllTags || !!tq;
  // Thu gọn: chỉ vẽ ~80 tag đầu (2 dòng không chứa nổi hơn), mở ra mới vẽ hết
  const shown = tq ? rest.filter(([t]) => removeAccents(t).includes(tq)) : open ? rest : rest.slice(0, 80);
  const box = $('tagList');
  $('tagHead').textContent = `Tag (${count.size})`;
  box.classList.toggle('open', open);
  box.innerHTML = `<button class="tag${lib.tags.length ? '' : ' on'}" data-tag="all">Tất cả <small>${baseCount}</small></button>`
    + lib.tags.map((t) => `<button class="tag on" data-tag="${esc(t)}" title="Bỏ tag này">${esc(t)} <small>${count.get(t) || 0}</small> ${icon('x', 'sm')}</button>`).join('')
    + shown.map(([t, n]) => `<button class="tag" data-tag="${esc(t)}">${esc(t)} <small>${n}</small></button>`).join('')
    + (tq && !shown.length ? '<span class="tag-none">Không có tag nào khớp</span>' : '');
  tagRest = rest.length;
  $('tagMore').innerHTML = showAllTags ? `Thu gọn ${icon('chevronUp', 'sm')}` : `Xem tất cả tag (${rest.length}) ${icon('right', 'sm')}`;
  clampTags();
}

// Cắt khu Tag còn 2 dòng: đo vị trí thật của chip (đúng ở mọi cỡ chữ / màn hình). Gọi lại khi hiện màn danh sách / đổi cỡ
// cửa sổ (lúc màn đang ẩn không đo được). Điện thoại = lưới 2 hàng vuốt ngang ⇒ bỏ qua.
let tagRest = 0;
function clampTags() {
  const box = $('tagList');
  if ($('libView').hidden || !box.children.length) return;
  const chips = [...box.children];
  chips.forEach((c) => { c.hidden = false; });
  const open = box.classList.contains('open');
  let visible = chips.filter((c) => c.dataset.tag && c.dataset.tag !== 'all' && !c.classList.contains('on')).length;
  if (!open && getComputedStyle(box).display !== 'grid') {
    const rows = [...new Set(chips.map((c) => c.offsetTop))].sort((x, y) => x - y);
    if (rows.length > 2) {
      visible = 0;
      for (const c of chips) {
        if (c.offsetTop > rows[1]) c.hidden = true;
        else if (c.dataset.tag !== 'all' && !c.classList.contains('on')) visible++;
      }
    }
  }
  $('tagMore').hidden = !!$('tagSearch').value.trim() || (!showAllTags && visible >= tagRest);
}
let clampTimer;
window.addEventListener('resize', () => { clearTimeout(clampTimer); clampTimer = setTimeout(clampTags, 150); });

function applyFilter(resetPage = true) {
  if (resetPage) lib.page = 1;
  renderFilters();
  const q = removeAccents($('searchInput').value.trim());
  const base = (lib.sort === 'size' ? sortedBySize : lib.sort === 'new' ? sortedByNew : sortedByName).filter((s) => (lib.src === 'all' || sourceOf(s) === lib.src)
    && (!lib.hideDone || !histGet(s.uid)?.done)
    && (!q || s._q.includes(q)));
  filtered = lib.tags.length ? base.filter((s) => lib.tags.every((t) => s._tags.has(t))) : base;
  renderTags(base.length);

  document.querySelectorAll('#sortChips .chip').forEach((b) => b.classList.toggle('on', b.dataset.sort === lib.sort));
  $('hideDone').checked = lib.hideDone;
  const parts = [lib.src !== 'all' ? lib.src : '', lib.tags.join(' + ')].filter(Boolean);
  $('viewTitle').textContent = q ? `Kết quả: “${$('searchInput').value.trim()}”` : (parts.join(' · ') || 'Tất cả truyện');
  $('viewCount').textContent = `${filtered.length} truyện`;
  $('statsText').textContent = `${allStories.length} truyện`;
  $('loading').style.display = 'none';
  renderResume();
  renderPage();
  saveLibState();
}

// Hàng truyện kiểu hàng audio Local Cinema:
// [ô bìa: 🎧 · rê chuột ▶ · đang phát 3 vạch] Tên + "N chương" / 📁 tag · đang nghe chương X · dung lượng  [Tóm tắt] ♡  ── thanh tiến độ
function rowHtml(s, extraSub = '') {
  const chapters = storyChapters(s);
  const h = histGet(s.uid);
  const pct = histPct(h, chapters) * 100;
  const info = h && !h.done ? `đang nghe chương ${(h.ch || 0) + 1} · ` : '';
  return `<div class="arow" data-uid="${esc(s.uid)}" data-mode="${s.has_raw ? 'raw' : 'sum'}">
    <button class="acover" style="--h:${coverHue(s)}" aria-label="Phát">${icon('headphones', 'ic-idle')}${icon('play', 'fill ic-play')}${icon('pause', 'fill ic-pause')}<span class="eq"><i></i><i></i><i></i></span></button>
    <div class="ainfo">
      <div class="title"><span class="tt" data-full="${esc(s.title)}">${esc(s.title)}</span>${newTag(s)}${chapters > 1 ? `<span class="apart">${chapters} chương</span>` : ''}</div>
      <div class="sub">${extraSub || `${icon('folder', 'sm')} ${esc(rowTags(s))} · ${s.t ? `${icon('calendar', 'sm')} ${s.t.split('-').reverse().join('/')} · ` : ''}${info}${fmtSize(s.size)}`}</div>
    </div>
    ${s.has_sum ? `<button class="abadge" data-sum="${esc(s.uid)}" title="Xem tóm tắt">${icon('fileText', 'sm')}<span>Tóm tắt</span></button>` : ''}
    ${favBtnHtml(s.uid, 'inline')}
    ${pct ? `<span class="aprog" style="width:${pct}%"></span>` : ''}
  </div>`;
}

// 📁 trên hàng: alicesw có hàng chục tag ⇒ 2 tag cụ thể đầu; nguồn khác ⇒ thể loại
function rowTags(s) {
  if (sourceOf(s) !== 'alicesw' || !s.tags) return s.category;
  return s.tags.filter((t) => t !== 'Mẹ con' && !SKIP_TAGS.has(t)).slice(0, 2).join(', ') || s.category;
}

// Bấm tag trên trang truyện ⇒ về danh sách, lọc đúng nguồn + tag đó
function libFilterTag(src, tag) {
  lib.src = src; lib.tags = tag ? [tag] : []; lib.page = 1;
  $('searchInput').value = ''; $('tagSearch').value = '';
  libScroll = 0;
  saveLibState();
  if (libReady) applyFilter();
  location.hash = '#/';
  setTimeout(() => { $('viewTitle').scrollIntoView({ block: 'start' }); window.scrollBy(0, -70); }, 50);
}

// Nút ♡ yêu thích (đồng bộ qua history.js). inline = trên hàng; icon-btn = trên trang truyện
function favBtnHtml(uid, cls, label = '') {
  return `<button class="fav ${cls}${favOn(uid) ? ' on' : ''}" data-fav="${esc(uid)}" title="Yêu thích"><span class="heart">${icon('heart')}</span>${label}</button>`;
}
// Bấm ♡ ở bất kỳ đâu ⇒ đổi mọi nút ♡ của truyện đó trên màn hình
function onFavClick(b) {
  const on = favToggle(b.dataset.fav);
  document.querySelectorAll(`.fav[data-fav="${CSS.escape(b.dataset.fav)}"]`).forEach((x) => x.classList.toggle('on', on));
  showToast(on ? 'Đã thêm vào Yêu thích' : 'Đã bỏ khỏi Yêu thích');
}

// ---- Chia trang (pager Local Cinema: ‹ 1 … 4 5 [6] 7 8 … 90 › + ô nhảy trang) ----
function pagerHtml(p, pages) {
  if (pages <= 1) return '';
  const nums = [...new Set([1, p - 2, p - 1, p, p + 1, p + 2, pages])].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
  let html = `<button data-page="${p - 1}"${p === 1 ? ' disabled' : ''} title="Trang trước">${icon('left', 'sm')}</button>`;
  nums.forEach((n, i) => {
    if (i && n - nums[i - 1] > 1) html += '<span class="gap">…</span>';
    html += `<button data-page="${n}"${n === p ? ' class="active"' : ''}>${n}</button>`;
  });
  html += `<button data-page="${p + 1}"${p === pages ? ' disabled' : ''} title="Trang sau">${icon('right', 'sm')}</button>`;
  html += `<form class="pager-jump"><input type="number" min="1" max="${pages}" placeholder="${p}/${pages}" aria-label="Tới trang"><button title="Tới trang">${icon('arrowRight', 'sm')}</button></form>`;
  return html;
}

function renderPage() {
  const pages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  lib.page = Math.min(Math.max(1, lib.page), pages);
  const start = (lib.page - 1) * PER_PAGE;
  $('storyList').innerHTML = filtered.length
    ? filtered.slice(start, start + PER_PAGE).map((s) => rowHtml(s)).join('')
    : '<div class="empty">Không tìm thấy truyện nào</div>';
  $('pager').innerHTML = pagerHtml(lib.page, pages);
  libMarkPlaying();
}

function goPage(n) {
  lib.page = n;
  renderPage();
  saveLibState();
  $('viewTitle').scrollIntoView({ block: 'start' });
  window.scrollBy(0, -70);
}

// "Đang nghe dở" (như Local Cinema): tối đa 5 truyện chưa nghe xong, mới nghe gần nhất lên đầu; "Xem tất cả" ⇒ Lịch sử
function renderResume() {
  if (!libReady) return;
  // Chọn Nguồn / Tag ⇒ vẫn hiện, chỉ lọc theo nguồn / tag đó (như "Đang nghe dở" trong thư mục của Local Cinema)
  const inView = (s) => (lib.src === 'all' || sourceOf(s) === lib.src) && lib.tags.every((t) => s._tags.has(t));
  const items = histList().filter(([uid, h]) => !h.done && byUid.has(uid) && inView(byUid.get(uid))).slice(0, 5);
  $('resumeList').innerHTML = items.map(([uid]) => rowHtml(byUid.get(uid))).join('');
  $('resumeSec').hidden = !items.length || !!$('searchInput').value.trim();
}

// Truyện đang nghe (reader.js gọi khi đổi trạng thái): tô hàng + ô bìa 3 vạch nhảy
function libMarkPlaying() {
  const uid = typeof player !== 'undefined' && player ? player.story.uid : '';
  document.querySelectorAll('#libView .arow[data-uid], #histView .arow[data-uid]').forEach((r) => r.classList.toggle('cur', r.dataset.uid === uid));
}

// =====================================================================
// Trang lịch sử — #/history?tab=all|partial|done&page=  (nhóm theo ngày như Local Cinema)
// =====================================================================
const HIST_TABS = { all: 'Tất cả', partial: 'Đang nghe dở', done: 'Đã nghe xong' };

function dayLabel(ms) {
  const d = new Date(ms); d.setHours(0, 0, 0, 0);
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const diff = Math.round((today - d) / 864e5);
  if (diff === 0) return 'Hôm nay';
  if (diff === 1) return 'Hôm qua';
  return d.toLocaleDateString('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' });
}

async function renderHistory(params) {
  if (!(await ensureStories())) return;
  document.title = 'Lịch sử nghe – Kho Truyện';
  const tab = HIST_TABS[params.get('tab')] ? params.get('tab') : 'all';
  let list = histList().filter(([uid]) => byUid.has(uid));
  const total = list.length;
  if (tab === 'partial') list = list.filter(([, h]) => !h.done);
  if (tab === 'done') list = list.filter(([, h]) => h.done);
  const pages = Math.max(1, Math.ceil(list.length / PER_PAGE));
  const cur = Math.min(Math.max(1, +params.get('page') || 1), pages);
  const items = list.slice((cur - 1) * PER_PAGE, cur * PER_PAGE);

  const groups = [];
  for (const [uid, h] of items) {
    const label = dayLabel(h.t);
    if (!groups.length || groups[groups.length - 1].label !== label) groups.push({ label, items: [] });
    groups[groups.length - 1].items.push([byUid.get(uid), h]);
  }
  const time = (ms) => new Date(ms).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  const sub = (s, h) => `${icon('folder', 'sm')} ${esc(s.category)} · `
    + (h.done ? `${icon('check', 'sm')} Đã nghe xong` : `đang nghe chương ${(h.ch || 0) + 1}${h.n ? ` · ${Math.round(histPct(h, storyChapters(s) || 1) * 100)}%` : ''}`)
    + ` · ${time(h.t)}`;

  $('histView').innerHTML = `
    <div class="crumbs"><a href="#/">${icon('bookOpen', 'sm')} Kho truyện</a> <span class="sep">${icon('right', 'sm')}</span> <b>Lịch sử nghe</b></div>
    <div class="toolbar">
      <h1>${icon('history')} Lịch sử nghe</h1><span class="count">${list.length} truyện</span>
      <span class="spacer"></span>
      <div class="tabs">${Object.entries(HIST_TABS).map(([k, l]) => `<a class="tab${k === tab ? ' active' : ''}" href="#/history?tab=${k}">${l}</a>`).join('')}</div>
      ${total ? `<button class="icon-btn" id="clearHist">${icon('trash')} Xoá tất cả</button>` : ''}
    </div>
    ${groups.length ? groups.map((g) => `<h3 class="day-h">${g.label}</h3>
      <div class="alist">${g.items.map(([s, h]) => `<div class="hcard">${rowHtml(s, sub(s, h))}<button class="rm" data-rm="${esc(s.uid)}" title="Xoá khỏi lịch sử">${icon('x', 'sm')}</button></div>`).join('')}</div>`).join('')
      : '<div class="empty">Chưa có lịch sử nghe.</div>'}
    <div class="pager" id="histPager">${pagerHtml(cur, pages)}</div>`;
  libMarkPlaying();
  window.scrollTo(0, 0);

  const go = (n) => { location.hash = `#/history?tab=${tab}&page=${n}`; };
  $('histPager').onclick = (e) => { const b = e.target.closest('button[data-page]'); if (b && !b.disabled) go(+b.dataset.page); };
  $('histPager').onsubmit = (e) => { e.preventDefault(); const v = parseInt(e.target.querySelector('input').value); if (v) go(v); };
  const clr = $('clearHist');
  if (clr) clr.onclick = () => {
    if (!confirm('Xoá toàn bộ lịch sử nghe? (xoá trên mọi thiết bị đang đồng bộ)')) return;
    histDel(histList().map(([uid]) => uid));
    renderHistory(params);
  };
}

// =====================================================================
// Trang yêu thích — #/favorites?page=  (bỏ ♡ ngay trên trang: hàng vẫn còn để bấm lại hoàn tác, lần mở sau mới mất)
// =====================================================================
async function renderFavorites(params) {
  if (!(await ensureStories())) return;
  document.title = 'Yêu thích – Kho Truyện';
  const list = favList().filter((uid) => byUid.has(uid));
  const pages = Math.max(1, Math.ceil(list.length / PER_PAGE));
  const cur = Math.min(Math.max(1, +params.get('page') || 1), pages);
  $('histView').innerHTML = `
    <div class="crumbs"><a href="#/">${icon('bookOpen', 'sm')} Kho truyện</a> <span class="sep">${icon('right', 'sm')}</span> <b>Yêu thích</b></div>
    <div class="toolbar"><h1>${icon('heart')} Yêu thích</h1><span class="count">${list.length} truyện</span></div>
    ${list.length ? `<div class="alist">${list.slice((cur - 1) * PER_PAGE, cur * PER_PAGE).map((uid) => rowHtml(byUid.get(uid))).join('')}</div>`
      : '<div class="empty">Chưa có truyện yêu thích nào.<br><small>Bấm nút ♡ trên hàng truyện để thêm vào đây.</small></div>'}
    <div class="pager" id="histPager">${pagerHtml(cur, pages)}</div>`;
  libMarkPlaying();
  window.scrollTo(0, 0);
  const go = (n) => { location.hash = `#/favorites?page=${n}`; };
  $('histPager').onclick = (e) => { const b = e.target.closest('button[data-page]'); if (b && !b.disabled) go(+b.dataset.page); };
  $('histPager').onsubmit = (e) => { e.preventDefault(); const v = parseInt(e.target.querySelector('input').value); if (v) go(v); };
}

// =====================================================================
// Sự kiện (dùng chung danh sách + lịch sử + yêu thích)
// =====================================================================
function onRowClick(e) {
  const fav = e.target.closest('[data-fav]');
  if (fav) { onFavClick(fav); return true; }
  // Bấm ô bìa ⇒ phát luôn (không mở trang), như Local Cinema
  const cover = e.target.closest('.arow[data-uid] .acover');
  if (cover) { playStory(cover.closest('.arow').dataset.uid); return true; }
  const rm = e.target.closest('[data-rm]');
  if (rm) { histDel([rm.dataset.rm]); renderHistory(new URLSearchParams(location.hash.split('?')[1] || '')); return true; }
  const sum = e.target.closest('[data-sum]');
  if (sum) { location.hash = readLink(sum.dataset.sum, 'sum'); return true; }
  const row = e.target.closest('.arow[data-uid]');
  if (row) { location.hash = readLink(row.dataset.uid, row.dataset.mode); return true; }
  return false;
}
$('histView').addEventListener('click', onRowClick);
$('libView').addEventListener('click', (e) => {
  if (onRowClick(e)) return;
  const src = e.target.closest('.fcard[data-src]');
  if (src) { lib.src = lib.src === src.dataset.src ? 'all' : src.dataset.src; applyFilter(); return; }
  const tag = e.target.closest('.tag[data-tag]');
  if (tag) {
    // "Tất cả" ⇒ bỏ hết tag; tag đã chọn ⇒ bỏ; tag khác ⇒ thêm (truyện phải có đủ các tag đã chọn)
    const t = tag.dataset.tag;
    lib.tags = t === 'all' ? [] : lib.tags.includes(t) ? lib.tags.filter((x) => x !== t) : [...lib.tags, t];
    $('tagSearch').value = '';
    applyFilter();
    $('tagList').scrollLeft = 0; // điện thoại: dải tag vuốt ngang ⇒ về đầu để thấy tag vừa chọn (đã xếp lên đầu)
    return;
  }
  const chip = e.target.closest('#sortChips .chip');
  if (chip) { lib.sort = chip.dataset.sort; applyFilter(); return; }
  const pg = e.target.closest('#pager button[data-page]');
  if (pg && !pg.disabled) goPage(+pg.dataset.page);
});
$('pager').addEventListener('submit', (e) => {
  e.preventDefault();
  const v = parseInt(e.target.querySelector('input').value);
  if (v) goPage(v);
});
$('hideDone').onchange = () => { lib.hideDone = $('hideDone').checked; applyFilter(); };
$('tagMore').onclick = () => { showAllTags = !showAllTags; applyFilter(false); };
let tqTimer;
$('tagSearch').addEventListener('input', () => { clearTimeout(tqTimer); tqTimer = setTimeout(() => applyFilter(false), 150); });
let qTimer;
$('searchInput').addEventListener('input', () => { clearTimeout(qTimer); qTimer = setTimeout(() => applyFilter(), 150); });
let sTimer;
window.addEventListener('scroll', () => {
  if ($('libView').hidden) return;
  clearTimeout(sTimer);
  sTimer = setTimeout(() => { libScroll = window.scrollY; saveLibState(); }, 150);
}, { passive: true });


// =====================================================================
// Tên truyện tối đa 2 dòng (tính cả nhãn "Mới" / "N chương"); dài quá ⇒ giữ đầu + cuối tên, cắt GIỮA bằng "…"
// (anh Thai chốt 2026-11-26: cuối tên hay có số tập / "(cuối)"). CSS không cắt giữa được ⇒ đo bằng JS, dò nhị phân
// số ký tự giữ lại. Chạy lại khi danh sách vẽ lại (MutationObserver) và khi đổi cỡ màn hình.
// =====================================================================
function fitTitle(el) {
  const tt = el.querySelector('.tt');
  if (!tt) return;
  const w = el.clientWidth;
  if (!w || el.dataset.fw === String(w)) return; // đang ẩn / đã cắt đúng độ rộng này ⇒ thôi
  const full = tt.dataset.full;
  if (tt.textContent !== full) tt.textContent = full;
  el.dataset.fw = w;
  const h0 = el.getBoundingClientRect().height;
  const max = (parseFloat(getComputedStyle(el).lineHeight) || 19) * 2 + 2;
  if (h0 <= max) { tt.removeAttribute('title'); return; }
  const set = (n) => {
    const a = Math.ceil(n * 0.55), b = n - a;
    tt.textContent = full.slice(0, a).trimEnd() + '…' + (b ? full.slice(full.length - b).trimStart() : '');
  };
  let lo = 6, hi = full.length - 1, best = 6;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    set(mid);
    if (el.getBoundingClientRect().height <= max) { best = mid; lo = mid + 1; } else hi = mid - 1;
  }
  set(best);
  tt.title = full; // giữ tay / rê chuột ⇒ thấy tên đầy đủ
}
function fitTitles(root = document) {
  root.querySelectorAll('.arow .title').forEach(fitTitle);
}
let fitRaf = 0;
const fitSoon = () => { cancelAnimationFrame(fitRaf); fitRaf = requestAnimationFrame(() => fitTitles()); };
// Chỉ theo dõi 3 khung danh sách được vẽ lại bằng innerHTML (không theo dõi cả trang: chính việc cắt tên cũng là thay đổi
// ⇒ lặp vô hạn; thanh phát đổi chữ mỗi câu ⇒ đo lại cả danh sách vô ích)
const fitObs = new MutationObserver(fitSoon);
for (const id of ['storyList', 'resumeList', 'histView']) if ($(id)) fitObs.observe($(id), { childList: true });
window.addEventListener('resize', fitSoon);
