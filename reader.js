// Màn đọc truyện (#/read?uid=...) + bộ đọc TTS dùng chung cả app.
// "view"   = truyện đang mở trên màn đọc.   "player" = truyện đang nghe (thanh phát ở đáy).
// Mở truyện khác ⇒ view đổi, player vẫn đọc tiếp; chỉ khi bấm Nghe ở truyện mới thì player mới chuyển sang.
// Mỗi phiên (session): { story, chapters, ch (chương), queue (các câu của chương), seg (câu đang đọc), html }

let player = null;
let view = null;
let viewMode = 'raw';

// =====================================================================
// Chia chương + chia câu
// =====================================================================
function splitIntoChapters(text) {
  const out = [];
  let cur = { title: 'Chương 1', content: [] };
  let found = false;
  const chapterRegex = /^Chương\s+(\d+|[IVXLCDM]+|[À-ỹ]+)/i;
  for (const line of text.split('\n')) {
    const t = line.trim();
    if (!t) { cur.content.push(''); continue; }
    if (chapterRegex.test(t) || /^={3,} Chương/i.test(t)) {
      // Khối đầu file chỉ có "=====" + "TITLE: ..." (file tool leech) thì bỏ, không tính là 1 chương
      if (cur.content.filter((l) => l.trim() && !/^=+$/.test(l) && !/^TITLE:/i.test(l)).length > 0) out.push(cur);
      cur = { title: t.replace(/^={3,}\s*/, '').replace(/\s*={3,}$/, ''), content: [] };
      found = true;
    } else cur.content.push(t);
  }
  out.push(cur);
  // Không có chữ "Chương" ⇒ tự chia theo độ dài
  if (!found && text.length > 8000) return autoSplit(text);
  return out;
}

function autoSplit(text) {
  const chunks = [];
  const targetLength = 5000;
  let remaining = text, count = 1;
  while (remaining.length > 0) {
    if (remaining.length <= targetLength + 1000) { chunks.push({ title: `Chương ${count}`, content: remaining.split('\n') }); break; }
    let i = remaining.lastIndexOf('\n', targetLength);
    if (i < targetLength * 0.7) i = remaining.lastIndexOf('. ', targetLength);
    if (i === -1) i = targetLength;
    chunks.push({ title: `Chương ${count}`, content: remaining.substring(0, i).split('\n') });
    remaining = remaining.substring(i).trim();
    count++;
  }
  return chunks;
}

// Chia 1 đoạn văn thành các câu ≤ ~140 ký tự (URL đọc Google ngắn, tránh lỗi 404)
function splitSegs(text) {
  const out = [];
  let cur = '';
  for (const s of text.split(/([.\n?!])/).filter((x) => x.trim().length > 0)) {
    if (/^[.\n?!]$/.test(s)) {
      cur += s;
      if (cur.trim().length > 1 && /[a-zA-Z0-9à-ỹĐ]/.test(cur)) out.push(cur.trim());
      cur = '';
    } else {
      cur += s;
      if (cur.length > 140) { out.push(cur.trim()); cur = ''; }
    }
  }
  if (cur.trim() && /[a-zA-Z0-9à-ỹĐ]/.test(cur)) out.push(cur.trim());
  return out;
}

// Dựng hàng đợi câu + HTML (giữ đoạn văn, mỗi câu 1 span) cho chương đang chọn của phiên
function buildChapter(s) {
  s.queue = [];
  let html = '';
  for (const line of s.chapters[s.ch].content) {
    const t = line.trim();
    if (!t) continue;
    if (/^={5,}/.test(t)) { html += '<hr>'; continue; }
    const segs = splitSegs(t);
    if (!segs.length) { html += `<p>${esc(t)}</p>`; continue; }
    html += '<p>' + segs.map((x) => `<span class="seg" data-i="${s.queue.push(x) - 1}">${esc(x)}</span>`).join(' ') + '</p>';
  }
  s.html = html || '<div class="empty">Chương trống</div>';
  if (!(s.seg < s.queue.length)) s.seg = 0;
}

// Lưu chương + câu vào lịch sử chung (history.js ⇒ đồng bộ Gist)
// cp = % đã nghe của từng chương (cho bảng chọn chương ở thanh đáy, như % từng phần của Local Cinema)
// played = đang phát ⇒ ghi mốc "lần nghe cuối" (p) để mở app lại thì thanh đáy hiện đúng truyện nghe gần nhất
function savePos(s, played = false) {
  const n = s.queue.length;
  const cp = { ...(histGet(s.story.uid)?.cp || {}) };
  if (n) cp[s.ch] = Math.round((s.seg + 1) / n * 100);
  histSet(s.story.uid, { ch: s.ch, i: s.seg, n, cp, ...(played ? { p: Date.now() } : {}) });
}
const saveProgress = savePos;

async function loadSession(story) {
  const s = { story, chapters: [], ch: 0, queue: [], seg: 0, html: '' };
  if (story.has_raw) {
    const res = await fetch(`${story.base}/${story.id}`);
    if (!res.ok) throw new Error(`Không tải được nội dung: HTTP ${res.status}`);
    s.chapters = splitIntoChapters(await res.text());
    // Mở lại đúng chương + câu đã nghe dở (lịch sử chung các thiết bị)
    const h = histGet(story.uid);
    if (h) { s.ch = Math.min(h.ch || 0, s.chapters.length - 1); s.seg = h.i || 0; }
    buildChapter(s);
  }
  return s;
}

// =====================================================================
// Màn đọc
// =====================================================================
let openToken = 0;
async function openReader(uid, mode) {
  viewMode = mode;
  const tk = ++openToken;
  if (!(view && view.story.uid === uid)) {
    if (player && player.story.uid === uid) view = player;
    else {
      $('readView').innerHTML = '<div class="empty"><div class="spinner"></div>Đang tải nội dung truyện...</div>';
      try {
        const story = (await STORIES).find((s) => s.uid === uid);
        if (!story) throw new Error('Không tìm thấy truyện');
        const s = await loadSession(story);
        if (tk !== openToken) return;
        view = s;
      } catch (e) {
        if (tk === openToken) $('readView').innerHTML = `<p class="err">${esc(e.message)}</p>`;
        return;
      }
    }
  }
  if (view.chapters.length) saveProgress(view); // mở truyện ⇒ lên đầu "Đang đọc dở" (như trước)
  renderReader();
  window.scrollTo(0, 0);
  if (mode === 'sum' && $('sumSec')) $('sumSec').scrollIntoView();
}
function readerLeave() { $('foldBtn').hidden = true; }

function renderReader() {
  const s = view, story = s.story;
  document.title = story.title;
  const hue = coverHue(story);
  const raw = s.chapters.length > 0;
  $('readView').innerHTML = `
    <div class="crumbs">
      <a href="#/">${icon('bookOpen', 'sm')} Kho truyện</a> <span class="sep">${icon('right', 'sm')}</span>
      <span>${esc(sourceOf(story))}</span> <span class="sep">${icon('right', 'sm')}</span>
      <span>${esc(story.category)}</span> <span class="sep">${icon('right', 'sm')}</span> <b>${esc(story.title)}</b>
    </div>
    <div class="ad-head">
      <div class="ad-cover" style="--h:${hue}">${icon('headphones')}</div>
      <div class="ad-main">
        <h1>${esc(story.title)}</h1>
        <div class="meta">
          ${raw ? `<span>${icon('fileText', 'sm')} ${s.chapters.length} chương</span>` : ''}
          <span>${icon('folder', 'sm')} ${esc(sourceOf(story))}</span>
          <span>${icon('list', 'sm')} ${esc(story.category)}</span>
          <span>${icon('drive', 'sm')} ${fmtSize(story.size)}</span>
          ${raw ? '<span id="metaPos"></span>' : ''}
        </div>
        ${raw ? `
        <div class="adp" id="adPlayer">
          <div class="adp-seek"><span class="adp-cur"></span><input class="seek" type="range" min="0" max="0" value="0" aria-label="Tua theo đoạn"><span class="adp-left"></span></div>
          <div class="adp-ctrls">
            <button class="adp-btn adp-back" title="Lùi 1 đoạn">${icon('restart')}</button>
            <button class="adp-btn adp-prev" title="Chương trước">${icon('skipBack', 'fill')}</button>
            <button class="adp-btn adp-play" title="Nghe / tạm dừng"></button>
            <button class="adp-btn adp-next" title="Chương sau">${icon('skipFwd', 'fill')}</button>
            <button class="adp-btn adp-fwd" title="Tới 1 đoạn">${icon('rotateCw')}</button>
          </div>
        </div>` : ''}
        <div class="actions">${favBtnHtml(story.uid, 'icon-btn', ' Yêu thích')}<button class="icon-btn" id="doneBtn"></button></div>
      </div>
    </div>
    ${story.has_sum ? `
    <section class="summary${viewMode === 'sum' || !raw ? '' : ' closed'}" id="sumSec">
      <h2 class="sum-h" role="button" tabindex="0">${icon('fileText')} <span class="t">Tóm tắt</span><span class="sum-chev">${icon('chevronUp', 'sm')}</span></h2>
      <div class="sum-body"><div class="empty">Đang tải...</div></div>
    </section>` : ''}
    ${raw ? `
    <section class="summary closed" id="textSec">
      <h2 class="sum-h" role="button" tabindex="0">${icon('alignJustify')} <span class="t" id="textTitle"></span><span class="sum-chev">${icon('chevronUp', 'sm')}</span></h2>
      <div class="sum-body">
        <p class="hint">Chạm 2 lần vào một câu để nghe từ câu đó.</p>
        <div class="content" id="storyContent"></div>
        <div class="chap-nav">
          <button class="icon-btn" id="navPrev">${icon('left', 'sm')} Chương trước</button>
          <button class="icon-btn next" id="navNext">Chương sau ${icon('right', 'sm')}</button>
        </div>
      </div>
    </section>
    <h2 class="section-h" style="margin-bottom:10px">Các chương (${s.chapters.length})</h2>
    <div class="alist parts" id="chapList">${s.chapters.map((c, i) => `
      <div class="arow" data-ch="${i}">
        <div class="acover" style="--h:${hue}">${icon('headphones')}<span class="eq"><i></i><i></i><i></i></span></div>
        <div class="ainfo"><div class="title">${esc(c.title)}</div><div class="sub">${fmtSize(c.content.join(' ').length * 1.4)}</div></div>
      </div>`).join('')}
    </div>` : ''}`;

  // Gập / mở khung; Nội dung nhớ lựa chọn
  $('readView').querySelectorAll('.sum-h').forEach((h) => h.onclick = () => toggleSection(h.parentElement));
  $('doneBtn').onclick = () => { histSet(story.uid, { done: !histGet(story.uid)?.done }); paintDone(); };
  $('readView').querySelector('[data-fav]').onclick = (e) => onFavClick(e.currentTarget);
  paintDone();
  if (story.has_sum) loadSummary(story);
  if (!raw) return;

  const P = (sel) => document.querySelector('#adPlayer ' + sel);
  P('.adp-play').onclick = viewTogglePlay;
  P('.adp-back').onclick = () => seekTo(view, view.seg - 1);
  P('.adp-fwd').onclick = () => seekTo(view, view.seg + 1);
  P('.adp-prev').onclick = () => setChapter(view, view.ch - 1);
  P('.adp-next').onclick = () => setChapter(view, view.ch + 1);
  $('navPrev').onclick = () => setChapter(view, view.ch - 1);
  $('navNext').onclick = () => setChapter(view, view.ch + 1);
  bindSeek(P('input'), () => view);
  $('chapList').onclick = (e) => {
    const row = e.target.closest('.arow[data-ch]');
    if (row) setChapter(view, +row.dataset.ch);
  };
  // Chạm 2 lần nhanh (< 350ms) vào 1 câu ⇒ nghe từ câu đó (iPhone không bắn dblclick ổn định ⇒ tự đo)
  let lastTap = 0;
  $('storyContent').onclick = (e) => {
    const x = e.target.closest('.seg');
    const now = Date.now();
    if (x && now - lastTap < 350) {
      e.preventDefault();
      seekTo(view, +x.dataset.i);
      if (!(player === view && playing)) startPlay(view);
    }
    lastTap = now;
  };
  renderContent();
}

// Khung Nội dung luôn gập khi mở truyện (anh Thai chốt 2026-11-25), bấm tiêu đề để mở
function toggleSection(sec) {
  sec.classList.toggle('closed');
  if (sec.id === 'textSec' && !sec.classList.contains('closed')) paintView(true);
  updateFoldBtn();
}

// Nút Đã nghe xong / Đánh dấu đã nghe xong
function paintDone() {
  const b = $('doneBtn');
  if (!b || !view) return;
  const done = !!histGet(view.story.uid)?.done;
  b.classList.toggle('active', done);
  b.innerHTML = done ? `${icon('circleCheck', 'sm')} Đã nghe xong` : `${icon('check', 'sm')} Đánh dấu đã nghe xong`;
}

// Vẽ lại nội dung chương của view + hàng chương đang chọn
function renderContent() {
  if (!view || !$('storyContent')) return;
  $('storyContent').innerHTML = view.html;
  $('textTitle').textContent = view.chapters[view.ch].title;
  $('navPrev').disabled = view.ch === 0;
  $('navNext').disabled = view.ch >= view.chapters.length - 1;
  document.querySelectorAll('#chapList .arow').forEach((r) => {
    const on = +r.dataset.ch === view.ch;
    r.classList.toggle('cur', on);
    r.querySelector('.aprog')?.remove();
    if (on) r.insertAdjacentHTML('beforeend', '<div class="aprog"></div>');
  });
  paintView(false);
}

async function loadSummary(story) {
  const body = document.querySelector('#sumSec .sum-body');
  try {
    const res = await fetch(`${story.sum_base}/${story.id}`);
    if (!res.ok) throw new Error();
    const html = summaryHtml(await res.text());
    if (view && view.story === story && body.isConnected) body.innerHTML = html;
  } catch (e) { if (body.isConnected) body.innerHTML = '<div class="empty">Không đọc được bản tóm tắt.</div>'; }
}

function summaryHtml(raw) {
  const heads = ['Khởi đầu', 'Diễn biến', 'Cao trào', 'Nút thắt', 'Hậu quả', 'Kết thúc', 'Chương'];
  const nums = ['1. Giới thiệu', '2. Tình huống', '3. Diễn biến', '4. Cao trào', '5. Đỉnh điểm', '6. Kết luận'];
  let html = '';
  for (const line of raw.split('\n')) {
    const t = line.trim();
    if (!t) continue;
    if (t.startsWith('===') || t.startsWith('---')) { html += '<hr>'; continue; }
    if (heads.some((h) => t.startsWith('🔹 ' + h))) { html += `<div class="section-head">${esc(t.replace(/^🔹\s*/, ''))}</div>`; continue; }
    if (/^(TÓM TẮT TRUYỆN|File gốc|Thể loại|Nhân vật)/.test(t)) { html += `<div class="sum-meta">${esc(t)}</div>`; continue; }
    const n = nums.find((k) => t.startsWith(k));
    if (n) {
      html += `<div class="section-head">${n}</div>`;
      const rest = t.slice(n.length).replace(/^[:.]?\s*/, '');
      if (rest) html += `<div>${esc(rest)}</div>`;
      continue;
    }
    html += `<div style="margin-bottom:8px">${esc(t)}</div>`;
  }
  return html || '<div class="empty">Trống</div>';
}

// =====================================================================
// Thao tác trên 1 phiên (dùng cho cả view lẫn player)
// =====================================================================
function setChapter(s, i) {
  if (!s || i < 0 || i >= s.chapters.length) return;
  s.ch = i;
  s.seg = 0;
  buildChapter(s);
  saveProgress(s);
  savePos(s);
  if (s === view && !$('readView').hidden) {
    renderContent();
    if (!document.querySelector('#textSec.closed')) $('textSec').scrollIntoView({ behavior: 'smooth' });
    else document.querySelector(`#chapList .arow[data-ch="${i}"]`)?.scrollIntoView({ block: 'nearest' });
  }
  if (s === player && playing) { stopSegAudio(); playSeg(true); }
  paintAll();
}

function seekTo(s, i) {
  if (!s || !s.queue.length) return;
  s.seg = Math.max(0, Math.min(s.queue.length - 1, i));
  savePos(s);
  if (s === player && playing) { stopSegAudio(); playSeg(true); }
  else paintAll(true);
}

// Bấm ô bìa ở danh sách / lịch sử ⇒ phát luôn, không mở trang (như Local Cinema). Đang nghe truyện đó ⇒ phát / dừng
async function playStory(uid) {
  if (player && player.story.uid === uid) return togglePlay();
  if (view && view.story.uid === uid) return startPlay(view);
  try {
    const story = (await STORIES).find((x) => x.uid === uid);
    if (!story || !story.has_raw) return showToast('Truyện này chỉ có tóm tắt');
    startPlay(await loadSession(story));
  } catch (e) { showToast(e.message, 'error'); }
}

// Nút Nghe trên màn đọc: truyện này đang nghe ⇒ phát / dừng; truyện khác ⇒ chuyển sang nghe truyện này
function viewTogglePlay() {
  if (player === view) togglePlay();
  else startPlay(view);
}

// =====================================================================
// Đọc TTS (Google) — 2 loa luân phiên: loa kia tải sẵn câu sau ⇒ không khựng giữa câu
// =====================================================================
const RATES = [1, 1.2, 1.32, 1.5, 1.75, 2];
let rate = parseFloat(lsGet('ttsRate')) || 1.32;
const isLocal = ['localhost', '127.0.0.1'].includes(location.hostname);
const ttsUrl = (t) => isLocal
  ? `http://127.0.0.1:9999/tts?q=${encodeURIComponent(t)}`
  : `https://translate.googleapis.com/translate_tts?client=gtx&ie=UTF-8&tl=vi&q=${encodeURIComponent(t)}`;
let curP = new Audio(), nxtP = new Audio();
let playing = false, reqId = 0, retryTimer = null;

function startPlay(s) {
  if (!s || !s.queue.length) return;
  // Nghe lại truyện đã đọc xong ⇒ thành "đang đọc" lại
  if (histGet(s.story.uid)?.done) { histSet(s.story.uid, { done: false }); paintDone(); }
  if (player !== s) { pauseAudio(); player = s; }
  $('abar').hidden = false;
  document.documentElement.classList.add('has-abar');
  playing = true;
  playSeg(true);
}
function stopSegAudio() { reqId++; clearTimeout(retryTimer); curP.pause(); nxtP.pause(); curP.removeAttribute('src'); }
function pauseAudio() {
  playing = false;
  reqId++;
  clearTimeout(retryTimer);
  curP.pause(); nxtP.pause();
  paintAll();
}
function togglePlay() { playing ? pauseAudio() : startPlay(player); }

function playSeg(scroll) {
  if (!playing || !player) return;
  clearTimeout(retryTimer);
  const id = ++reqId;
  const s = player;
  savePos(s, true);
  paintAll(scroll);
  const url = ttsUrl(s.queue[s.seg]);
  if (curP.src !== url) curP.src = url;
  curP.defaultPlaybackRate = curP.playbackRate = rate;
  curP.play().catch((e) => {
    if (id !== reqId || e.name === 'AbortError') return;
    console.warn('Không phát được:', e);
    pauseAudio();
    showToast('Không phát được — bấm Nghe lại', 'error');
  });
  if (s.seg + 1 < s.queue.length) { nxtP.src = ttsUrl(s.queue[s.seg + 1]); nxtP.load(); }
  curP.onended = () => {
    if (!playing || id !== reqId) return;
    if (s.seg + 1 < s.queue.length) {
      s.seg++;
      [curP, nxtP] = [nxtP, curP];
      playSeg(false);
    } else if (s.ch + 1 < s.chapters.length) {
      showToast('Hết chương, sang chương tiếp...');
      setChapter(s, s.ch + 1);
    } else {
      pauseAudio();
      histSet(s.story.uid, { done: true });
      paintDone();
      showToast('Đã đọc hết truyện!', 'success');
    }
  };
  curP.onerror = () => {
    if (!playing || id !== reqId) return;
    retryTimer = setTimeout(() => { if (playing && id === reqId) { curP.removeAttribute('src'); playSeg(false); } }, 3000);
  };
}

// Thanh tua theo đoạn: kéo chỉ xem trước (tô câu + chữ), thả tay mới tua
function bindSeek(input, getS) {
  input.oninput = () => { input.dataset.drag = '1'; paintAll(false, getS(), +input.value); };
  input.onchange = () => { if (!input.dataset.drag) return; delete input.dataset.drag; seekTo(getS(), +input.value); };
  input.addEventListener('pointercancel', input.onchange);
}
bindSeek(document.querySelector('#abar input'), () => player);

// =====================================================================
// Vẽ trạng thái: màn đọc (view) + thanh đáy (player) + danh sách
// =====================================================================
function paintAll(scroll = false, previewOf = null, previewI = null) {
  document.documentElement.classList.toggle('a-playing', playing);
  paintView(scroll, previewOf === view ? previewI : null);
  paintBar(previewOf === player ? previewI : null);
  if (typeof libMarkPlaying === 'function') libMarkPlaying(); // tô hàng đang nghe ở danh sách + lịch sử
}

function paintView(scroll, preview = null) {
  if (!view || !view.chapters.length || !$('adPlayer')) return;
  const s = view, i = preview ?? s.seg, n = s.queue.length;
  const pct = n > 1 ? i / (n - 1) * 100 : 0;
  const isCur = player === view;
  document.querySelector('#adPlayer .adp-play').innerHTML = icon(isCur && playing ? 'pause' : 'play', 'fill');
  document.querySelectorAll('#storyContent .seg.on').forEach((el) => el.classList.remove('on'));
  const el = document.querySelector(`#storyContent .seg[data-i="${i}"]`);
  if (el) {
    el.classList.add('on');
    if (scroll && !document.querySelector('#textSec.closed')) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  const adIn = document.querySelector('#adPlayer input');
  if (!adIn.dataset.drag) { adIn.max = Math.max(0, n - 1); adIn.value = i; }
  adIn.style.setProperty('--p', pct + '%');
  document.querySelector('#adPlayer .adp-cur').textContent = n ? `Đoạn ${i + 1}` : '';
  document.querySelector('#adPlayer .adp-left').textContent = n ? `-${n - 1 - i} đoạn` : '';
  document.querySelector('#adPlayer .adp-prev').disabled = s.ch === 0;
  document.querySelector('#adPlayer .adp-next').disabled = s.ch >= s.chapters.length - 1;
  $('metaPos').innerHTML = `${icon('list', 'sm')} Chương ${s.ch + 1}/${s.chapters.length}`;
  const prog = document.querySelector('#chapList .arow.cur .aprog');
  if (prog) prog.style.width = Math.max(2, pct) + '%';
  // 3 vạch nhảy chỉ ở hàng chương đang nghe (truyện đang mở = truyện đang nghe)
  document.querySelectorAll('#chapList .arow').forEach((r) => r.classList.toggle('playing-row', isCur && +r.dataset.ch === s.ch));
}

function paintBar(preview = null) {
  const AB = (sel) => document.querySelector('#abar ' + sel);
  AB('.ab-play').innerHTML = icon(playing ? 'pause' : 'play', 'fill');
  if (!player) return;
  const s = player, i = preview ?? s.seg, n = s.queue.length;
  const pct = n > 1 ? i / (n - 1) * 100 : 0;
  const abIn = AB('input');
  if (!abIn.dataset.drag) { abIn.max = Math.max(0, n - 1); abIn.value = i; }
  AB('.ab-fill').style.width = pct + '%';
  AB('.ab-title').textContent = s.story.title;
  AB('.ab-sub').textContent = `${s.chapters[s.ch].title} · Đoạn ${i + 1}/${n}`;
  AB('.ab-time').textContent = `${i + 1} / ${n}`;
  AB('.ab-cover').style.setProperty('--h', coverHue(s.story));
  AB('.ab-prev').disabled = s.ch === 0;
  AB('.ab-next').disabled = s.ch >= s.chapters.length - 1;
  AB('.ab-parts').innerHTML = `<span class="ab-pw">Chương </span>${s.ch + 1}/${s.chapters.length}<span class="ab-pc">${icon('chevronUp', 'sm')}</span>`;
  if (!$('chapMenu').hidden) renderChapMenu(); // bảng đang mở ⇒ cập nhật chương / % đang nghe
}

// Bảng chọn chương (như bảng chọn phần Local Cinema): Chương n · dung lượng · ▷ đang nghe / ✓ xong / % đã nghe
function renderChapMenu() {
  const s = player;
  if (!s) return;
  const cp = histGet(s.story.uid)?.cp || {};
  $('chapMenu').innerHTML = `<div class="ab-menu-h">${esc(s.story.title)}</div>` + s.chapters.map((c, i) => {
    const p = cp[i];
    const state = i === s.ch ? icon(playing ? 'volume' : 'play', 'sm') : p >= 100 ? icon('check', 'sm') : p ? `${p}%` : '';
    return `<button class="${i === s.ch ? 'on' : ''}" data-ch="${i}"><span>${esc(c.title)}</span><small>${fmtSize(c.content.join(' ').length * 1.4)}</small><em>${state}</em></button>`;
  }).join('');
  $('chapMenu').querySelector('.on')?.scrollIntoView({ block: 'center' });
}
function renderRateMenu() {
  $('rateMenu').innerHTML = '<div class="ab-menu-h">Tốc độ đọc</div>'
    + RATES.map((r) => `<button class="${r === rate ? 'on' : ''}" data-rate="${r}"><span>${r}x${r === 1 ? ' (thường)' : ''}</span><em>${r === rate ? icon('check', 'sm') : ''}</em></button>`).join('');
}

// ---- Thanh phát ở đáy (luôn điều khiển truyện đang nghe) ----
(() => {
  const AB = (sel) => document.querySelector('#abar ' + sel);
  AB('.ab-play').onclick = togglePlay;
  AB('.ab-back').onclick = () => seekTo(player, player.seg - 1);
  AB('.ab-fwd').onclick = () => seekTo(player, player.seg + 1);
  AB('.ab-prev').onclick = () => setChapter(player, player.ch - 1);
  AB('.ab-next').onclick = () => setChapter(player, player.ch + 1);
  AB('.ab-close').onclick = () => { pauseAudio(); barClosed = true; $('abar').hidden = true; document.documentElement.classList.remove('has-abar'); updateFoldBtn(); };
  // Bấm tên truyện ⇒ mở màn đọc của truyện đang nghe, mở khung Nội dung, cuộn tới câu đang đọc
  AB('.ab-info').onclick = () => {
    if (!player) return;
    const go = () => {
      const sec = $('textSec');
      if (sec && sec.classList.contains('closed')) toggleSection(sec);
      paintView(true);
    };
    if (view === player && !$('readView').hidden) go();
    else { location.hash = readLink(player.story.uid); setTimeout(go, 300); }
  };
  const paintRate = () => { AB('.ab-rate').textContent = rate + 'x'; };
  // 2 bảng chọn: bấm nút ⇒ bật / tắt; mở bảng này thì đóng bảng kia; chạm ra ngoài ⇒ đóng
  const toggleMenu = (id, render) => {
    const m = $(id), other = $(id === 'chapMenu' ? 'rateMenu' : 'chapMenu');
    other.hidden = true;
    m.hidden = !m.hidden;
    if (!m.hidden) render();
  };
  AB('.ab-parts').onclick = () => toggleMenu('chapMenu', renderChapMenu);
  AB('.ab-rate').onclick = () => toggleMenu('rateMenu', renderRateMenu);
  $('chapMenu').onclick = (e) => {
    const b = e.target.closest('[data-ch]');
    if (!b) return;
    $('chapMenu').hidden = true;
    if (+b.dataset.ch !== player.ch) setChapter(player, +b.dataset.ch);
    if (!playing) startPlay(player);
  };
  $('rateMenu').onclick = (e) => {
    const b = e.target.closest('[data-rate]');
    if (!b) return;
    rate = +b.dataset.rate;
    lsSet('ttsRate', rate);
    curP.playbackRate = nxtP.playbackRate = rate;
    $('rateMenu').hidden = true;
    paintRate();
  };
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.ab-pop')) { $('chapMenu').hidden = true; $('rateMenu').hidden = true; }
  });
  paintRate();
  paintBar();
})();

// =====================================================================
// Nút nổi "thu gọn nội dung": hiện khi khung Nội dung đang mở và đang cuộn bên trong nó
// =====================================================================
function updateFoldBtn() {
  const sec = $('textSec');
  const btn = $('foldBtn');
  if ($('readView').hidden || !sec || sec.classList.contains('closed')) { btn.hidden = true; return; }
  const r = sec.getBoundingClientRect();
  btn.hidden = !(r.top < 60 && r.bottom > window.innerHeight * 0.6);
  btn.classList.toggle('above-bar', !$('abar').hidden);
}
$('foldBtn').onclick = () => {
  const sec = $('textSec');
  if (!sec) return;
  toggleSection(sec);
  sec.scrollIntoView({ block: 'start' });
  window.scrollBy(0, -70);
};
window.addEventListener('scroll', updateFoldBtn, { passive: true });
window.addEventListener('resize', updateFoldBtn);

// =====================================================================
// Mở app ⇒ thanh đáy tự hiện truyện đang nghe dở gần nhất (đang dừng, bấm ▶ là nghe tiếp) — như Local Cinema.
// Lấy theo mốc nghe cuối (p) của lịch sử chung ⇒ máy kia vừa nghe gì thì máy này mở lên thấy đúng truyện đó.
// Đã bấm ✕ tắt thanh thì không tự hiện lại cho tới lần mở app sau.
// =====================================================================
let barClosed = false;
async function restoreLastPlayed() {
  if (player || barClosed) return;
  const last = Object.entries(hist).filter(([k, h]) => h.p && !h.done && !h.del && !k.startsWith('fav:')).sort((a, b) => b[1].p - a[1].p)[0];
  if (!last) return;
  try {
    const story = (await STORIES).find((x) => x.uid === last[0]);
    if (!story || !story.has_raw) return;
    const s = view && view.story.uid === story.uid ? view : await loadSession(story);
    if (player || barClosed || !s.queue.length) return;
    player = s;
    $('abar').hidden = false;
    document.documentElement.classList.add('has-abar');
    paintAll();
    updateFoldBtn();
  } catch (e) {}
}
restoreLastPlayed();
window.addEventListener('histchange', restoreLastPlayed); // lịch sử vừa tải về từ máy khác
