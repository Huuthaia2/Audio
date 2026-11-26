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
function splitIntoChapters(text, name = '') {
  if (/^─{10,}\s*$/m.test(text)) return splitByRule(text);
  const out = [];
  let cur = { title: 'Chương 1', content: [] };
  let found = false;
  const chapterRegex = /^Chương\s+(\d+|[IVXLCDM]+|[À-ỹ]+)/i;
  // Dòng tiêu đề "Phần 2" / "Phần 3: Tên phần" / "Chap 4" / "Tập 5" (946 truyện Text Mp3 chia theo Phần, trước đây bị bỏ qua
  // ⇒ tự cắt mỗi 5000 chữ, lệch hẳn phần thật). Bắt buộc sau số là hết dòng hoặc dấu ":" "." "-"... ⇒ câu thường
  // "Phần 2 của câu chuyện..." không bị coi là tiêu đề. Cần ≥ 2 dòng như vậy trong truyện mới tính.
  const partRegex = /^(Phần|Hồi|Tập|Quyển|Chap|Chapter|Part)\s*\.?\s*(\d+|[IVXLC]+)\s*([:.\-–—)]|$)/i;
  // Dòng mốc "==== Chương / Phần / Hồi / Quyển / Tập N ====" (tool tải truyện, tool gộp file Text Mp3)
  const markRegex = /^={3,}\s*(Chương|Phần|Hồi|Quyển|Tập)\b/i;
  const lines = text.split('\n');
  // File tool tải truyện có dòng mốc "==== Chương N ====" ⇒ CHỈ tách theo dòng mốc; dòng "Chương N: ..." trong
  // nội dung giữ làm chữ (trước đây tách cả 2 ⇒ 246 truyện bị dư 1 chương rỗng chỉ có câu phụ đề)
  const hasMarks = lines.some((l) => markRegex.test(l.trim()));
  const isPart = (t) => t.length <= 120 && partRegex.test(t);
  const useParts = !hasMarks && lines.filter((l) => isPart(l.trim())).length >= 2;
  const isHead = (t) => hasMarks ? markRegex.test(t) : chapterRegex.test(t) || (useParts && isPart(t));
  for (const line of lines) {
    const t = line.trim();
    if (!t) { cur.content.push(''); continue; }
    if (isHead(t)) {
      const title = t.replace(/^={3,}\s*/, '').replace(/\s*={3,}$/, '');
      // Khối đầu file chỉ có "=====" + "TITLE: ..." (file tool leech) thì bỏ, không tính là 1 chương
      if (cur.content.filter((l) => l.trim() && !/^=+$/.test(l) && !/^TITLE:/i.test(l)).length > 0) out.push(cur);
      // "Phần 1" ngay sau là "Chương 1" (chưa có chữ nào) ⇒ gộp tên: "Phần 1 · Chương 1"
      else if (found && useParts) { cur.title += ' · ' + title; cur.content = []; continue; }
      cur = { title, content: [] };
      found = true;
    } else cur.content.push(t);
  }
  out.push(cur);
  // Phần mở đầu trước tiêu đề đầu tiên: trước "Phần 2" ⇒ "Phần 1"; trước "Phần 1" ⇒ "Mở đầu"
  if (useParts && out.length > 1 && out[0].title === 'Chương 1') {
    const m = /^(\S+)\s*\.?\s*(\d+)/.exec(out[1].title);
    if (m && +m[2] <= 2) out[0].title = +m[2] === 2 ? `${m[1]} 1` : 'Mở đầu';
  }
  // Không có tiêu đề chương / phần ⇒ tự chia theo độ dài
  if (!found && text.length > 8000) return autoSplit(text, nameChapterCount(name));
  return out;
}

// Tên file ghi sẵn số chương: "...+Chuong-0001-0053.txt" ⇒ 53 (dùng làm số chương khi tự chia)
function nameChapterCount(name) {
  const m = /Chuong-(\d+)-(\d+)\.txt$/i.exec(name || '');
  return m && +m[2] > +m[1] ? +m[2] - +m[1] + 1 : 0;
}

// File alicesw: khối thông tin (Tác giả, Tag...) ở đầu, mỗi chương mở bằng dòng "──────" rồi dòng tên chương.
// Tên chương hay lặp 2 dòng (2 bản dịch cùng 1 tên: "Chương 1: Bắt gặp..." / "Chương 1: Phước lành...") ⇒ bỏ dòng lặp,
// TTS khỏi đọc tên 2 lần. Phần trước dòng "──────" đầu tiên (khối thông tin) không phải chương.
function splitByRule(text) {
  const out = [];
  let cur = null, wantTitle = false, skipDup = false;
  const num = (t) => (t.match(/^Chương\s+(\d+)/i) || [])[1];
  for (const line of text.split('\n')) {
    const t = line.trim();
    if (/^─{10,}$/.test(t)) {
      if (cur && cur.content.some((l) => l)) out.push(cur);
      cur = { title: `Chương ${out.length + 1}`, content: [] };
      wantTitle = true;
      continue;
    }
    if (!cur) continue;
    if (!t) { cur.content.push(''); continue; }
    if (wantTitle) {
      // "Chương 2 Chương 2 Người mẹ..." ⇒ "Chương 2: Người mẹ..."
      cur.title = t.replace(/^(Chương\s+\d+)\s*[:：.\-–]?\s*Chương\s+\d+\s*[:：.\-–]?\s*/i, '$1: ');
      wantTitle = false; skipDup = true; continue;
    }
    if (skipDup) {
      skipDup = false;
      if (t.toLowerCase() === cur.title.toLowerCase() || (num(t) && num(t) === num(cur.title))) continue;
    }
    cur.content.push(t);
  }
  if (cur && cur.content.some((l) => l)) out.push(cur);
  return out.length ? out : [{ title: 'Chương 1', content: text.split('\n') }];
}

// Truyện không có tiêu đề chương: tự chia ~5000 chữ / chương (tên file có số chương ⇒ chia đều đúng số đó).
// Chỗ cắt chọn trong khoảng 70%–140% độ dài, ưu tiên: dòng ngăn cảnh "***" / "……" ⇒ đoạn mở đầu bằng mốc thời gian
// ("Sáng hôm sau", "Mấy ngày sau"...) ⇒ hết đoạn văn gần độ dài nhất. Không cắt giữa đoạn (trừ đoạn quá dài ⇒ hết câu).
// Chỉ nhìn tới 190% phía trước ⇒ đang tải dở thì các chương (trừ 2 chương cuối) y hệt lúc tải xong (loadSession dựa vào điều này).
function autoSplit(text, count = 0) {
  const T = count ? Math.max(3000, Math.ceil(text.length / count)) : 5000;
  const SEP = /^[\s*\-~_=o0O.…·•#+]{3,}$/;
  const TIME = /^(Sáng|Trưa|Chiều|Tối|Đêm|Hôm|Mấy|Vài|Một (ngày|tuần|tháng|năm|buổi|hôm|đêm)|Sau (đó|khi|này|bữa|hôm)|Ngày hôm|Tuần|Tháng|Năm|Thời gian|Thấm thoắt|Quay (lại|trở lại))/;
  const chunks = [];
  let rest = text.trim();
  while (rest) {
    if (rest.length <= T * 1.4) { chunks.push(rest); break; }
    // Chừa lại ≥ nửa chương cho phần sau (tránh chương cuối chỉ còn vài câu)
    const max = Math.min(T * 1.4, rest.length - T * 0.5);
    let best = -1, bestScore = -Infinity;
    for (let i = rest.indexOf('\n', T * 0.7); i > 0 && i <= max; i = rest.indexOf('\n', i + 1)) {
      const next = rest.slice(i + 1, i + 200).trimStart();
      const prevLine = rest.slice(rest.lastIndexOf('\n', i - 1) + 1, i).trim();
      const dist = Math.abs(i - T) / T;          // 0..0.7
      const score = (SEP.test(prevLine) ? 3 : TIME.test(next) ? 1.5 : 0) - dist * 2;
      if (score > bestScore) { bestScore = score; best = i; }
    }
    if (best < 0) {                               // đoạn văn quá dài ⇒ cắt ở hết câu gần nhất
      best = rest.lastIndexOf('. ', max);
      best = best > T * 0.5 ? best + 1 : T;
    }
    chunks.push(rest.slice(0, best));
    rest = rest.slice(best).trim();
  }
  return chunks.map((c, i) => ({ title: `Chương ${i + 1}`, content: c.split('\n') }));
}

// Chia 1 đoạn văn thành các câu ≤ ~140 ký tự (URL đọc Google ngắn, tránh lỗi 404)
function splitSegs(text) {
  const out = [];
  let cur = '';
  for (const s of text.split(/([.\n?!])/).filter((x) => x.trim().length > 0)) {
    if (/^[.\n?!]$/.test(s)) {
      cur += s;
      if (cur.trim().length > 1 && /[a-zA-Z0-9à-ỹĐ]/.test(cur)) capSeg(cur.trim(), out);
      cur = '';
    } else {
      cur += s;
      if (cur.length > 140) { capSeg(cur.trim(), out); cur = ''; }
    }
  }
  if (cur.trim() && /[a-zA-Z0-9à-ỹĐ]/.test(cur)) capSeg(cur.trim(), out);
  return out;
}

// Google đọc tối đa 200 ký tự / lần: câu dài hơn (vd 222 ký tự toàn dấu phẩy, không dấu chấm) ⇒ HTTP 400 ⇒ trước đây
// thử lại mãi rồi DỪNG HẲN giữa truyện (anh Thai: "nghe 1-2 câu là dừng, chạm 2 lần mới tiếp" — đo trên Android thật).
// ⇒ cắt câu > 180 ký tự ở dấu phẩy / chấm phẩy / hai chấm gần nhất, không có thì ở khoảng trắng.
const SEG_MAX = 150; // ≤ 150 ⇒ luôn còn chỗ nối thêm 1 câu ngắn (< 40) mà vẫn dưới 196 (buildChapter)
function capSeg(t, out) {
  while (t.length > SEG_MAX) {
    let i = Math.max(t.lastIndexOf(', ', SEG_MAX), t.lastIndexOf('; ', SEG_MAX), t.lastIndexOf(': ', SEG_MAX));
    if (i < 60) i = t.lastIndexOf(' ', SEG_MAX);
    if (i < 1) i = SEG_MAX - 1;
    out.push(t.slice(0, i + 1).trim());
    t = t.slice(i + 1).trim();
  }
  if (t) out.push(t);
}

// Dựng hàng đợi đọc + HTML (giữ đoạn văn, mỗi câu 1 span) cho chương đang chọn của phiên.
// Câu QUÁ NGẮN (< SEG_MIN ký tự, vd thoại 2-4 từ "– Tự con hôn thôi.") ⇒ file Google < ~1,5s, iPhone hay kẹt ở 0s không phát
// (nhật ký phát của anh Thai 2026-11-26: báo "phát được" nhưng t=0 [stalled], tải lại vẫn kẹt) ⇒ KHÔNG BAO GIỜ gửi câu ngắn
// riêng: nối với câu liền kề (kể cả sang đoạn văn kế) thành 1 lượt đọc ≤ 196 ký tự (Google nhận tối đa 200).
// Trên màn hình mỗi câu vẫn 1 span riêng; các span cùng lượt đọc chung data-i (tô sáng cùng lúc).
const SEG_MIN = 40;
function buildChapter(s) {
  const paras = [];   // mỗi đoạn văn: mảng câu, hoặc chuỗi HTML có sẵn (<hr>, đoạn không có chữ để đọc)
  const all = [];     // mọi câu theo thứ tự: { t: chữ, g: số thứ tự lượt đọc }
  for (const line of s.chapters[s.ch].content) {
    const t = line.trim();
    if (!t) continue;
    if (/^={5,}/.test(t)) { paras.push('<hr>'); continue; }
    if (/^TITLE:/i.test(t)) continue; // dòng "TITLE: tên truyện" đầu file Text Mp3 (2678 truyện) ⇒ không đọc to, không hiện
    const segs = splitSegs(t);
    if (!segs.length) { paras.push(`<p>${esc(t)}</p>`); continue; }
    const items = segs.map((x) => ({ t: x, g: 0 }));
    all.push(...items); paras.push(items);
  }
  // Câu kế nhập vào lượt đang dở nếu lượt đó còn ngắn hoặc chính câu đó ngắn, và tổng không quá 196 ký tự
  const groups = [];
  for (const it of all) {
    const last = groups[groups.length - 1];
    if (last && (last.len < SEG_MIN || it.t.length < SEG_MIN) && last.len + 2 + it.t.length <= 196) { last.items.push(it); last.len += 2 + it.t.length; }
    else groups.push({ items: [it], len: it.t.length });
  }
  // Lượt còn ngắn (câu ngắn kẹp giữa 2 câu dài) ⇒ nhập vào lượt PHÍA SAU nếu vừa
  for (let i = groups.length - 2; i >= 0; i--) {
    const g = groups[i], nx = groups[i + 1];
    if (g.len < SEG_MIN && g.len + 2 + nx.len <= 196) { nx.items.unshift(...g.items); nx.len += 2 + g.len; groups.splice(i, 1); }
  }
  // Câu nối vào mà không kết bằng dấu câu ⇒ thêm dấu chấm để giọng đọc vẫn ngắt nghỉ giữa các câu
  s.queue = groups.map((g, i) => {
    g.items.forEach((it) => { it.g = i; });
    return g.items.map((it, k) => (k < g.items.length - 1 && !/[.!?…:;,”"]$/.test(it.t) ? it.t + '.' : it.t)).join(' ');
  });
  const html = paras.map((p) => (typeof p === 'string' ? p : '<p>' + p.map((it) => `<span class="seg" data-i="${it.g}">${esc(it.t)}</span>`).join(' ') + '</p>')).join('');
  s.html = html || '<div class="empty">Chương trống</div>';
  if (!(s.seg < s.queue.length)) s.seg = 0;
}

// Lưu chương + câu vào lịch sử chung (history.js ⇒ đồng bộ Gist)
// Như Local Cinema: CHỈ NGHE mới đưa truyện vào lịch sử / Đang nghe dở. Mở xem, chọn chương, tua khi chưa nghe ⇒ chỉ
// cập nhật vị trí nếu truyện đã có trong lịch sử (không tạo mục mới).
// cp = % đã nghe của từng chương (bảng chọn chương ở thanh đáy) — giữ số LỚN NHẤT (mở lại chương đã nghe xong không bị về 1%)
// played = đang phát ⇒ ghi mốc "lần nghe cuối" (p) để mở app lại thì thanh đáy hiện đúng truyện nghe gần nhất
function savePos(s, played = false) {
  const h = histGet(s.story.uid);
  if (!h && !played) return;
  const n = s.queue.length;
  const cp = { ...(h?.cp || {}) };
  if (n && played) cp[s.ch] = Math.max(cp[s.ch] || 0, Math.round((s.seg + 1) / n * 100));
  histSet(s.story.uid, { ch: s.ch, i: s.seg, n, cp, ...(played ? { p: Date.now() } : {}) });
}

// Tải truyện theo luồng: có đủ chương cần mở (chương đang nghe dở, chưa có thì chương 1) ⇒ trả phiên NGAY (s.loading = true),
// phần còn lại tải tiếp ở nền rồi gộp vào (finishLoad). Truyện 4 MB không phải chờ tải hết mới thấy chương đầu.
async function loadSession(story) {
  const s = { story, chapters: [], ch: 0, queue: [], seg: 0, html: '', loading: false };
  if (!story.has_raw) return s;
  const h = histGet(story.uid);
  const want = h ? h.ch || 0 : 0;
  const init = () => {
    // Mở lại đúng chương + câu đã nghe dở (lịch sử chung các thiết bị)
    if (h) { s.ch = Math.min(h.ch || 0, s.chapters.length - 1); s.seg = h.i || 0; }
    buildChapter(s);
  };
  return new Promise((resolve, reject) => {
    let ready = false, checked = 0;
    streamStoryText(story, (text, done) => {
      if (done) {
        const full = splitIntoChapters(text, story.uid);
        if (!ready) { s.chapters = full; init(); ready = true; resolve(s); } else finishLoad(s, full);
        return;
      }
      // Mỗi ~150 KB mới tách thử 1 lần (tách chương cả file mỗi lần nhận vài KB thì tốn CPU)
      // Tên file có số chương ⇒ độ dài chương = cả file / số chương ⇒ phải đủ file mới chia được
      if (ready || text.length - checked < 150000 || nameChapterCount(story.uid)) return;
      checked = text.length;
      const chs = splitIntoChapters(text, story.uid);
      if (chs.length > want + 2) {          // 2 chương cuối có thể chưa tải hết / còn đổi chỗ cắt ⇒ chỉ lấy các chương đã chắc
        s.chapters = chs.slice(0, -2);
        s.loading = true;
        init(); ready = true; resolve(s);
      }
    }).catch((e) => {
      if (!ready) reject(e);
      else { s.loading = false; showToast('Không tải hết được truyện: ' + e.message, 'error'); }
    });
  });
}

// Tải xong phần còn lại của truyện đang mở dở
function finishLoad(s, full) {
  const same = s.chapters.every((c, i) => full[i] && full[i].title === c.title);
  s.chapters = full;
  s.loading = false;
  if (!same) {  // hiếm: phần sau đổi hẳn cách chia chương ⇒ dựng lại chương đang mở
    s.ch = Math.min(s.ch, full.length - 1);
    const seg = s.seg; buildChapter(s); s.seg = Math.min(seg, Math.max(0, s.queue.length - 1));
  }
  if (s === view && !$('readView').hidden && $('chapList')) {
    $('chapList').innerHTML = chapListHtml(s, coverHue(s.story));
    $('chapHead').textContent = chapHeadText(s);
    if ($('metaChs')) $('metaChs').innerHTML = `${icon('fileText', 'sm')} ${full.length} chương`;
    renderContent();
  }
  paintAll();
  // Đang nghe tới chương cuối của phần đã tải ⇒ đọc tiếp chương sau
  if (s.pendingNext) { s.pendingNext = false; if (s === player && s.ch + 1 < s.chapters.length) setChapter(s, s.ch + 1); }
}

function chapHeadText(s) { return `Các chương (${s.chapters.length}${s.loading ? ', đang tải thêm…' : ''})`; }

// Bảng chọn chương: mở ⇒ cuộn sẵn tới chương đang mở; khoá cuộn trang phía sau
function openChapSheet() {
  $('chapSheet').hidden = false;
  document.documentElement.classList.add('sheet-open');
  document.querySelector('#chapList .arow.cur')?.scrollIntoView({ block: 'center' });
}
function closeChapSheet() {
  if (!$('chapSheet')) return;
  $('chapSheet').hidden = true;
  document.documentElement.classList.remove('sheet-open');
}

function chapListHtml(s, hue) {
  return s.chapters.map((c, i) => `
      <div class="arow" data-ch="${i}">
        <div class="acover" style="--h:${hue}">${icon('headphones')}<span class="eq"><i></i><i></i><i></i></span></div>
        <div class="ainfo"><div class="title">${esc(c.title)}</div><div class="sub">${fmtSize(c.content.join(' ').length * 1.4)}</div></div>
      </div>`).join('');
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
  renderReader();
  window.scrollTo(0, 0);
  if (mode === 'sum' && $('sumSec')) $('sumSec').scrollIntoView();
}
function readerLeave() { $('foldBtn').hidden = true; closeChapSheet(); closeSumSheet(); }

// Bảng tóm tắt (bật từ đáy như bảng chương); tải nội dung lần đầu mở
let sumLoaded = null;
function openSumSheet() {
  if (!$('sumSheet')) return;
  $('sumSheet').hidden = false;
  document.documentElement.classList.add('sheet-open');
  if (sumLoaded !== view.story.uid) { sumLoaded = view.story.uid; loadSummary(view.story); }
}
function closeSumSheet() {
  if (!$('sumSheet') || $('sumSheet').hidden) return;
  $('sumSheet').hidden = true;
  if (!$('chapSheet') || $('chapSheet').hidden) document.documentElement.classList.remove('sheet-open');
}

function renderReader() {
  const s = view, story = s.story;
  document.title = story.title;
  const hue = coverHue(story);
  const raw = s.chapters.length > 0;
  $('readView').innerHTML = `
    <div class="crumbs">
      <a href="#/">${icon('bookOpen', 'sm')} Kho truyện</a> <span class="sep">${icon('right', 'sm')}</span>
      <a href="#/" data-crumb-src>${esc(sourceOf(story))}</a> <span class="sep">${icon('right', 'sm')}</span>
      <a href="#/" data-crumb-tag>${esc(story.category)}</a> <span class="sep">${icon('right', 'sm')}</span> <b>${esc(story.title)}</b>
    </div>
    <div class="ad-head">
      <div class="ad-cover" style="--h:${hue}">${icon('headphones')}</div>
      <!-- Góc phải cạnh ảnh bìa: Yêu thích, dưới là Tóm tắt (bảng bật từ đáy) — anh Thai chốt 2026-11-26: đỡ tốn chỗ -->
      <div class="ad-fav">${favBtnHtml(story.uid, 'icon-btn', ' Yêu thích')}${story.has_sum && raw ? `<button class="icon-btn" id="sumBtn">${icon('fileText', 'sm')} Tóm tắt</button>` : ''}</div>
      <div class="ad-main">
        <h1>${esc(story.title)}</h1>
        <div class="meta">
          ${raw ? `<span id="metaChs">${icon('fileText', 'sm')} ${s.loading ? `${s.chapters.length}+` : s.chapters.length} chương</span>` : ''}
          <span>${icon('folder', 'sm')} ${esc(sourceOf(story))}</span>
          <span>${icon('list', 'sm')} ${esc(story.category)}</span>
          <span>${icon('drive', 'sm')} ${fmtSize(story.size)}</span>
          ${story.author ? `<span title="Tác giả">✍ ${esc(story.author)}</span>` : ''}
          ${story.t ? `<span title="Cập nhật">${icon('calendar', 'sm')} ${story.t.split('-').reverse().join('/')}</span>` : ''}
          ${story.done !== undefined ? `<span class="st-badge${story.done ? ' done' : ''}">${story.done ? 'Đã hoàn thành' : 'Đang ra'}</span>` : ''}
          ${newTag(story)}
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
        ${storyTagsHtml(story)}
      </div>
    </div>
    ${story.has_sum && !raw ? `
    <section class="summary" id="sumSec">
      <h2 class="sum-h" role="button" tabindex="0">${icon('fileText')} <span class="t">Tóm tắt</span><span class="sum-chev">${icon('chevronUp', 'sm')}</span></h2>
      <div class="sum-body"><div class="empty">Đang tải...</div></div>
    </section>` : ''}
    ${story.has_sum && raw ? `
    <div class="sheet" id="sumSheet" hidden>
      <div class="sheet-box">
        <div class="sheet-head"><span>${icon('fileText', 'sm')} Tóm tắt</span><button class="ab-btn" data-close title="Đóng">${icon('x')}</button></div>
        <div class="sheet-list sum-body sum-sheet-body"><div class="empty">Đang tải...</div></div>
      </div>
    </div>` : ''}
    ${raw ? `
    <!-- Chọn chương: nút riêng (anh Thai chốt 2026-11-26: không gộp vào khung đọc) ⇒ bảng danh sách chương bật từ đáy -->
    <button class="chap-open" id="chapOpen" title="Danh sách chương">${icon('list')}<span class="co-l">Chọn chương</span><span class="co-t" id="textTitle"></span><span class="chap-num" id="chapNum"></span>${icon('chevronUp', 'sm')}</button>
    <section class="summary closed" id="textSec">
      <!-- Tiêu đề khung: chữ "Đọc truyện" rõ ràng, bấm ⇒ gập / mở -->
      <h2 class="sum-h" role="button" tabindex="0">
        ${icon('bookOpen')} <span class="t">Đọc truyện</span>
        <!-- Trước / Sau: nút nhỏ có chữ bên phải tiêu đề, chỉ hiện khi đang mở khung đọc (anh Thai chốt 2026-11-26) -->
        <button class="icon-btn chap-step" id="navPrev" title="Chương trước">${icon('left', 'sm')} Trước</button>
        <button class="icon-btn chap-step next" id="navNext" title="Chương sau">Sau ${icon('right', 'sm')}</button>
        <span class="sum-chev">${icon('chevronUp', 'sm')}</span>
      </h2>
      <div class="sum-body">
        <p class="hint">Chạm 2 lần vào một câu để nghe từ câu đó.</p>
        <div class="content-wrap">
          <div class="content" id="storyContent"></div>
          <button class="icon-btn follow-btn" id="followBtn" hidden>${icon('volume', 'sm')} Về câu đang đọc</button>
        </div>
      </div>
    </section>
    <!-- Danh sách chương = bảng bật lên từ đáy (truyện 300 chương không phải cuộn cả trang) -->
    <div class="sheet" id="chapSheet" hidden>
      <div class="sheet-box">
        <div class="sheet-head"><span id="chapHead">${chapHeadText(s)}</span><button class="ab-btn" id="chapClose" title="Đóng">${icon('x')}</button></div>
        <div class="alist parts sheet-list" id="chapList">${chapListHtml(s, hue)}</div>
      </div>
    </div>` : ''}`;

  // Gập / mở khung; Nội dung nhớ lựa chọn
  $('readView').querySelectorAll('.sum-h').forEach((h) => h.onclick = () => toggleSection(h.parentElement));
  $('readView').querySelector('[data-fav]').onclick = (e) => onFavClick(e.currentTarget);
  // Đường dẫn: bấm nguồn ⇒ danh sách lọc nguồn đó; bấm thể loại ⇒ lọc nguồn + tag đó
  $('readView').querySelector('[data-crumb-src]').onclick = (e) => { e.preventDefault(); libFilterTag(sourceOf(story)); };
  $('readView').querySelector('[data-crumb-tag]').onclick = (e) => { e.preventDefault(); libFilterTag(sourceOf(story), story.category); };
  // Bấm tag ⇒ về danh sách lọc đúng nguồn + tag đó
  const tagBox = $('readView').querySelector('.story-tags');
  if (tagBox) tagBox.onclick = (e) => {
    const b = e.target.closest('[data-ftag]');
    if (b) libFilterTag(sourceOf(story), b.dataset.ftag);
  };
  if (story.has_sum && !raw) loadSummary(story);
  if (story.has_sum && raw) {
    $('sumBtn').onclick = openSumSheet;
    $('sumSheet').onclick = (e) => { if (e.target === $('sumSheet') || e.target.closest('[data-close]')) closeSumSheet(); };
    if (viewMode === 'sum') openSumSheet(); // bấm "Tóm tắt" ở danh sách ⇒ mở thẳng bảng tóm tắt
  }
  if (!raw) return;

  const P = (sel) => document.querySelector('#adPlayer ' + sel);
  P('.adp-play').onclick = viewTogglePlay;
  P('.adp-back').onclick = () => seekTo(view, view.seg - 1);
  P('.adp-fwd').onclick = () => seekTo(view, view.seg + 1);
  P('.adp-prev').onclick = () => setChapter(view, view.ch - 1);
  P('.adp-next').onclick = () => setChapter(view, view.ch + 1);
  // 3 nút nằm trong tiêu đề khung (bấm tiêu đề = gập / mở) ⇒ chặn nổi bọt
  $('navPrev').onclick = (e) => { e.stopPropagation(); setChapter(view, view.ch - 1); };
  $('navNext').onclick = (e) => { e.stopPropagation(); setChapter(view, view.ch + 1); };
  bindSeek(P('input'), () => view);
  $('chapList').onclick = (e) => {
    const row = e.target.closest('.arow[data-ch]');
    if (!row) return;
    closeChapSheet();
    setChapter(view, +row.dataset.ch);
  };
  $('chapOpen').onclick = (e) => { e.stopPropagation(); openChapSheet(); };
  $('chapClose').onclick = closeChapSheet;
  $('chapSheet').onclick = (e) => { if (e.target === $('chapSheet')) closeChapSheet(); }; // chạm vùng tối ⇒ đóng
  // Chạm 2 lần nhanh (< 350ms) vào 1 câu ⇒ nghe từ câu đó (iPhone không bắn dblclick ổn định ⇒ tự đo)
  // Người dùng chạm / lăn chuột trong khung rồi khung cuộn ⇒ đang tự cuộn đọc ⇒ ngừng tự theo
  const box = $('storyContent');
  const markUser = () => { userScrollT = Date.now(); };
  box.addEventListener('touchstart', markUser, { passive: true });
  box.addEventListener('touchmove', markUser, { passive: true });
  box.addEventListener('wheel', markUser, { passive: true });
  box.addEventListener('scroll', () => { if (Date.now() - userScrollT < 800 && followRead) setFollow(false); }, { passive: true });
  $('followBtn').onclick = followNow;
  setFollow(true);
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

// Tag trên trang truyện (thể loại + tag trang nguồn, bỏ R-18 / Tiếng Trung). > 12 tag ⇒ ẩn bớt, nút "+N"
function storyTagsHtml(story) {
  const tags = [...new Set([story.category, ...(story.tags || [])])].filter((t) => t && !SKIP_TAGS.has(t));
  if (tags.length < 2 && !story.tags) return '';
  // 1 dòng duy nhất, vuốt ngang xem hết (anh Thai chốt 2026-11-26)
  return `<div class="story-tags">${tags.map((t) => `<button class="tag" data-ftag="${esc(t)}">${esc(t)}</button>`).join('')}</div>`;
}

// Khung Nội dung luôn gập khi mở truyện (anh Thai chốt 2026-11-25), bấm tiêu đề để mở.
// Chữ nằm trong 1 khung cuộn riêng (cuộn chữ không kéo cả trang)
function toggleSection(sec) {
  sec.classList.toggle('closed');
  if (sec.id === 'textSec' && !sec.classList.contains('closed')) {
    setFollow(true);
    window.scrollTo(0, fitReadBox());
    paintView(true);
  }
  updateFoldBtn();
}

// Chiều cao khung chữ (anh Thai chốt 2026-11-26): cuộn trang để thanh nghe (tua + nút) nằm ngay dưới header, khung chữ
// kéo dài vừa khít tới mép trên thanh đáy ⇒ vừa thấy nút nghe vừa đọc, không phải cuộn trang, chữ không chui dưới thanh đáy.
// Không đủ chỗ (màn thấp, Tóm tắt / nhiều tag phía trên) ⇒ đưa khung lên sát header, cao gần hết màn hình.
// Trả về vị trí cuộn trang nên dùng.
function fitReadBox() {
  const sec = $('textSec'), box = $('storyContent'), adp = $('adPlayer');
  if (!sec || sec.classList.contains('closed')) return scrollY;
  const abar = $('abar').hidden ? 0 : $('abar').offsetHeight;
  const head = document.querySelector('header').offsetHeight;
  const Y = (el) => el.getBoundingClientRect().top + scrollY;
  const pad = 20;                                   // lề dưới khung Nội dung + khoảng hở trên thanh đáy
  // Thanh đáy đã có thanh tua ⇒ chỉ chừa hàng nút nghe (bỏ thanh tua trên trang khỏi màn) ⇒ khung chữ cao thêm
  let y = Math.max(0, Y(adp.querySelector('.adp-ctrls')) - head - 4);
  let h = innerHeight - abar - (Y(box) - y) - pad;
  if (h < 200) {
    y = Y(sec) - head - 4;
    h = innerHeight - abar - head - (Y(box) - Y(sec)) - pad;
  }
  box.style.height = Math.max(240, h) + 'px';
  return y;
}
window.addEventListener('resize', () => fitReadBox());
// Thanh đáy hiện / ẩn khi đang mở khung chữ ⇒ tính lại chiều cao + vị trí cuộn (không thì chữ chui dưới thanh đáy)
function refitReadBox() { if ($('textSec') && !$('textSec').classList.contains('closed')) window.scrollTo(0, fitReadBox()); }

// Tự cuộn theo câu đang đọc. Anh Thai tự cuộn đi chỗ khác ⇒ NGỪNG tự cuộn (trước đây cứ giật về mỗi câu mới) và hiện nút
// "Về câu đang đọc"; bấm nút ⇒ cuộn tới câu đang đọc + tự theo lại. Đổi chương / bấm Nghe ⇒ tự theo lại.
let followRead = true, userScrollT = 0;
function setFollow(on) {
  followRead = on;
  if ($('followBtn')) $('followBtn').hidden = on;
}
function followNow() {
  setFollow(true);
  const el = document.querySelector('#storyContent .seg.on');
  if (el) scrollSegIntoBox(el);
}

// Cuộn khung chữ (không cuộn trang) để câu đang đọc nằm giữa khung
function scrollSegIntoBox(el, smooth = true) {
  const box = $('storyContent');
  const top = el.offsetTop - box.clientHeight / 2 + el.offsetHeight / 2;
  box.scrollTo({ top: Math.max(0, top), behavior: smooth ? 'smooth' : 'auto' });
}


// Vẽ lại nội dung chương của view + hàng chương đang chọn
function renderContent() {
  if (!view || !$('storyContent')) return;
  $('storyContent').innerHTML = view.html;
  $('storyContent').scrollTop = 0;
  setFollow(true);
  $('textTitle').textContent = view.chapters[view.ch].title;
  $('chapNum').textContent = `${view.ch + 1}/${view.chapters.length}${view.loading ? '+' : ''}`;
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
  const body = document.querySelector('#sumSec .sum-body, #sumSheet .sum-body');
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
  savePos(s);
  if (s === view && !$('readView').hidden) {
    renderContent();  // khung chữ tự về đầu chương; trang đứng yên (nút ‹ › nằm ngay tiêu đề khung)
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
// Đọc TTS (Google) — màn hình sáng: 2 loa luân phiên (loa kia tải sẵn câu sau ⇒ không khựng giữa câu).
// Tắt màn hình / sang app khác: điện thoại CHẶN bắt đầu phát ở loa khác ⇒ phát tiếp trên CÙNG loa (như Local Cinema).
// Google trả file "no-store" + không CORS ⇒ không tải sẵn vào bộ nhớ được, nên không thể chỉ dùng 1 loa lúc màn sáng.
// =====================================================================
const RATES = [0.9, 1, 1.05, 1.1, 1.15, 1.2, 1.3, 1.5, 1.75, 2];
const DEFAULT_RATE = 1.15; // anh Thai chốt 2026-11-25
// Tốc độ đã lưu không có trong danh sách (vd 1.32 = mặc định bản cũ, không phải tự chọn) ⇒ về mặc định
let rate = RATES.includes(parseFloat(lsGet('ttsRate'))) ? parseFloat(lsGet('ttsRate')) : DEFAULT_RATE;
const isLocal = ['localhost', '127.0.0.1'].includes(location.hostname);
// v > 0 = lần tải lại thứ v của câu ⇒ thêm &r=v cho địa chỉ khác đi (Google vẫn trả đúng câu đó). Nhật ký iPhone 2026-11-26:
// câu kẹt ở 0s (Google gửi file không báo độ dài, iPhone thỉnh thoảng không chịu) mà tải lại ĐÚNG địa chỉ cũ thì kẹt y như cũ
// cả 3 lần ⇒ đổi địa chỉ để iPhone coi là yêu cầu mới.
const ttsUrl = (t, v = 0) => (isLocal
  ? `http://127.0.0.1:9999/tts?q=${encodeURIComponent(t)}`
  : `https://translate.googleapis.com/translate_tts?client=gtx&ie=UTF-8&tl=vi&q=${encodeURIComponent(t)}`) + (v ? `&r=${v}` : '');
let segVariant = 0, segVariantKey = null; // số lần đã tải lại câu đang đọc (đổi câu ⇒ về 0)
// Cắt im lặng có sẵn trong file Google: bỏ TTS_LEAD giây đầu + chuyển câu sớm ttsTail giây trước khi hết file.
// Muốn khoảng hở thật sự = 0 phải đọc được dữ liệu âm thanh để dò đúng chỗ im lặng của từng file (Google chặn ⇒ cần trạm trung chuyển).
// Đo trên Android thật: loa bắt đầu phát từ vị trí 0 mất ~300ms khởi động; loa đã "làm nóng" (chạy thử tắt tiếng rồi đứng ở
// TTS_LEAD) thì phát ngay ⇒ làm nóng + tua tới TTS_LEAD lúc CHƯA tới lượt; tới lượt phát thì KHÔNG tua gì nữa.
// Đo 300 lượt đọc thật (3 nguồn, 2026-11-26, ngưỡng -55dB): im lặng đầu file nhỏ nhất 0,079s; im lặng CUỐI file tuỳ chữ cuối:
//   kết bằng , ; :  ⇒ nhỏ nhất 0,82s | kết bằng . ? ! … " ” ⇒ 0,21s | kết bằng chữ (câu dài cắt đôi) ⇒ 0,166s
// ⇒ cắt chừa ~0,04s dự phòng dưới mức nhỏ nhất. Tính theo thời gian FILE; hẹn giờ chia cho tốc độ đọc ⇒ mọi tốc độ đều đúng.
const TTS_LEAD = 0.06;
const ttsTail = (t) => (/[,;:]\s*$/.test(t) ? 0.70 : /[.?!…"”'»)]\s*$/.test(t) ? 0.17 : 0.12);
let earlyT = null, earlyArmed = 0;
function armEarly(p, id) {
  clearTimeout(earlyT); earlyArmed = 0;
  // Màn tắt: timer bị hãm ⇒ để sự kiện ended tự chuyển câu. File quá ngắn (< 0,6s, file Google thật ≥ 0,9s) ⇒ không cắt.
  if (document.hidden || !isFinite(p.duration) || p.duration < 0.6 || p.paused) return;
  earlyArmed = id;
  const tail = ttsTail(player.queue[player.seg] || '');
  const ms = (p.duration - p.currentTime - tail) / (p.playbackRate || 1) * 1000;
  earlyT = setTimeout(() => {
    if (!playing || id !== reqId || p !== curP || p.paused) return;
    if (p.duration - p.currentTime > tail + 0.15) { armEarly(p, id); return; } // bị khựng giữa chừng ⇒ hẹn lại
    tlog('  → chuyển sớm (bỏ ' + tail + 's im lặng cuối)', '', p);
    p.pause();
    if (p.onended) p.onended();
  }, Math.max(0, ms));
}
// 4 loa: 1 đang đọc + 3 tải sẵn 3 câu kế (mạng chập chờn ⇒ ít khựng giữa câu). Mỗi loa nhớ câu đang giữ ở dataset.u
const PRELOAD = 3;
const pool = Array.from({ length: PRELOAD + 1 }, () => new Audio());
let curP = pool[0];

// =====================================================================
// Nhật ký phát (anh Thai 2026-11-26): iPhone dừng ở câu ngắn / khi tắt màn hình mà máy tính không tái hiện được ⇒ ghi lại
// ~150 sự kiện gần nhất (câu nào, loa nào, phát được bao lâu, lỗi gì, màn sáng / tắt) vào localStorage 'ttsLog'.
// Xem: nút tốc độ ở thanh đáy ⇒ "Nhật ký phát" ⇒ chụp màn hình / Sao chép gửi lại.
// =====================================================================
const TLOG_MAX = 150;
let tlogBuf = (() => { try { return JSON.parse(lsGet('ttsLog') || '[]'); } catch (e) { return []; } })();
let tlogSaveT = null;
function tlog(type, detail = '', a = curP) {
  const d = new Date();
  const hh = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}.${Math.floor(d.getMilliseconds() / 100)}`;
  const pos = player ? `${player.ch + 1}.${player.seg + 1}` : '-';
  const st = a ? `loa${pool.indexOf(a) + 1} t=${a.currentTime.toFixed(1)}/${isFinite(a.duration) ? a.duration.toFixed(1) : a.duration ? '∞' : '?'} rs${a.readyState} ns${a.networkState}${a.error ? ' err' + a.error.code : ''}${a.paused ? ' dừng' : ''}` : '';
  tlogBuf.push(`${hh} [${pos}] ${type}${detail ? ' ' + detail : ''} · ${st}${document.hidden ? ' · NỀN' : ''}`);
  if (tlogBuf.length > TLOG_MAX) tlogBuf = tlogBuf.slice(-TLOG_MAX);
  clearTimeout(tlogSaveT);
  tlogSaveT = setTimeout(() => lsSet('ttsLog', JSON.stringify(tlogBuf)), 500);
}
// Sự kiện của chính thẻ audio (chỉ ghi khi là loa đang đọc, đang nghe) ⇒ thấy iPhone tự dừng / chờ tải / lỗi ở đâu
for (const a of pool) {
  for (const ev of ['stalled', 'waiting', 'error', 'pause', 'ended', 'emptied', 'abort']) {
    a.addEventListener(ev, () => { if (playing && a === curP) tlog('[' + ev + ']', '', a); });
  }
  // Loa đang tải sẵn câu kế mà lỗi (Google từ chối / rớt mạng) cũng ghi lại
  a.addEventListener('error', () => { if (playing && a !== curP) tlog('[error] loa tải sẵn', `câu "${(decodeURIComponent((a.dataset.u || '').split('q=')[1] || '')).slice(0, 24)}"`, a); });
}
document.addEventListener('visibilitychange', () => tlog(document.hidden ? 'TẮT MÀN HÌNH / ẩn app' : 'MỞ MÀN HÌNH / hiện app'));
let playing = false, reqId = 0, retryTimer = null, retries = 0;
let resumeOnVisible = false; // điện thoại chặn phát (NotAllowedError) ⇒ mở lại app thì phát tiếp, không tắt hẳn
// iPhone: 1 loa CHỈ được tự phát nếu đã từng play() trong lúc người dùng chạm ⇒ loa tải sẵn chưa "mở khoá" bị chặn
// (NotAllowedError) ⇒ trước đây đọc 1-2 câu là đứng im, chạm 2 lần vào câu mới đọc tiếp. okP = loa vừa phát được;
// singleSpeaker = có loa bị chặn ⇒ từ đó đọc trên 1 loa okP (mất tải sẵn nhưng không bao giờ đứng)
let okP = null, singleSpeaker = false;
const SILENT = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
// Gọi trong lúc người dùng chạm (bấm Nghe / chạm 2 lần vào câu): play() rồi pause() ngay từng loa ⇒ iPhone ghi nhận
// loa đó đã được người dùng cho phép (chỉ cần lời gọi play() trong lúc chạm, không cần phát ra tiếng)
function unlockPool() {
  for (const a of pool) {
    if (a.dataset.unlocked) continue;
    a.dataset.unlocked = '1';
    if (!a.dataset.u) a.src = SILENT;      // loa trống ⇒ gắn 1 file im lặng để play() hợp lệ
    a.play().catch(() => {});
    a.pause();
  }
}
// iPhone (iOS 17+): báo đây là phát nhạc ⇒ nghe được khi gạt im lặng / tắt màn hình
try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) {}

// iPhone tắt màn hình vẫn dừng (anh Thai báo 2026-11-26): giữa 2 câu có 1 khoảng KHÔNG có tiếng (đang tải câu kế, màn tắt
// không tải sẵn được) ⇒ iOS coi như hết phát, treo trang ⇒ câu kế không bao giờ chạy, bộ canh (timer) cũng đứng.
// ⇒ trong lúc đang nghe luôn phát kèm 1 đoạn "im lặng" lặp vô hạn trên 1 loa riêng: phiên âm thanh không lúc nào ngắt,
// trang không bị treo. Chỉ bật trên iPhone / iPad (Android tắt màn hình vẫn đọc, đã đo trên máy thật).
const IS_IOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
let keepAlive = null, bgDenied = 0;
function keepAliveStart() {
  if (!IS_IOS) return;
  if (!keepAlive) {
    // WAV 8 kHz 16-bit mono 4 giây, IM LẶNG THẬT (toàn số 0). Bản đầu 8-bit dao động 1 nấc ⇒ anh Thai nghe tiếng tích tích liên tục
    const n = 64000, b = new Uint8Array(44 + n), v = new DataView(b.buffer);
    const str = (o, t) => { for (let i = 0; i < t.length; i++) b[o + i] = t.charCodeAt(i); };
    str(0, 'RIFF'); v.setUint32(4, 36 + n, true); str(8, 'WAVEfmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true);
    v.setUint16(22, 1, true); v.setUint32(24, 8000, true); v.setUint32(28, 16000, true); v.setUint16(32, 2, true);
    v.setUint16(34, 16, true); str(36, 'data'); v.setUint32(40, n, true);
    keepAlive = new Audio(URL.createObjectURL(new Blob([b], { type: 'audio/wav' })));
    keepAlive.loop = true;
  }
  keepAlive.play().catch((e) => tlog('⚠ loa im lặng không phát', e.name, keepAlive));
}
function keepAliveStop() { if (keepAlive) keepAlive.pause(); }

function startPlay(s) {
  if (!s || !s.queue.length) return;
  // "Đã nghe xong" do app tự đánh (nghe hết câu cuối chương cuối); nghe lại truyện đó ⇒ thành "đang nghe" lại
  if (histGet(s.story.uid)?.done) histSet(s.story.uid, { done: false });
  if (player !== s) { pauseAudio(); player = s; }
  const barWasHidden = $('abar').hidden;
  $('abar').hidden = false;
  document.documentElement.classList.add('has-abar');
  if (barWasHidden) refitReadBox();
  playing = true;
  if (s === view) setFollow(true);
  tlog('■ BẤM NGHE', `${navigator.userAgent.match(/(iPhone|iPad|Android)[^;)]*/)?.[0] || 'máy tính'} · tốc độ ${rate}`);
  unlockPool();
  keepAliveStart();
  playSeg(true);
}
function stopSegAudio() { reqId++; clearTimeout(retryTimer); pool.forEach((a) => a.pause()); curP.removeAttribute('src'); delete curP.dataset.u; }
function pauseAudio() {
  if (playing) tlog('■ DỪNG');
  playing = false;
  resumeOnVisible = false;
  reqId++;
  clearTimeout(retryTimer);
  pool.forEach((a) => a.pause());
  keepAliveStop();
  clearTimeout(earlyT);
  paintAll();
  if (sync.dirty) syncSoon(true); // dừng nghe ⇒ đẩy vị trí lên Gist sau 3s (máy kia mở là thấy đúng chỗ)
}
function togglePlay() { playing ? pauseAudio() : startPlay(player); }

function playSeg(scroll) {
  if (!playing || !player) return;
  clearTimeout(retryTimer);
  const id = ++reqId;
  const s = player;
  savePos(s, true);
  paintAll(scroll);
  const vKey = s.story.uid + ':' + s.ch + ':' + s.seg;
  if (vKey !== segVariantKey) { segVariantKey = vKey; segVariant = 0; }
  const url = ttsUrl(s.queue[s.seg], segVariant);
  // Dùng loa đã tải sẵn câu này (nếu có). iPhone tắt màn hình: GIỮ NGUYÊN loa đang phát (iPhone chặn phát ở loa khác).
  // Android tắt màn hình vẫn chuyển loa + tải sẵn được (đo trên máy thật) ⇒ hết khoảng chờ tải mỗi câu lúc tắt màn hình.
  if (!(document.hidden && IS_IOS) && !singleSpeaker) {
    const ready = pool.find((a) => a.dataset.u === url && !a.error);
    curP = ready || pool.find((a) => a !== curP && !a.dataset.u) || pool.find((a) => a !== curP) || curP;
  }
  // Loa tải sẵn câu này mà bị lỗi (Google từ chối / rớt mạng) ⇒ tải lại; trước đây phát file lỗi ⇒ dừng hẳn
  if (curP.dataset.u === url && curP.error) tlog('  loa tải sẵn câu này bị lỗi ⇒ tải lại', '', curP);
  if (curP.dataset.u !== url || curP.error) { curP.src = url; curP.dataset.u = url; }
  curP.defaultPlaybackRate = curP.playbackRate = rate;
  updateMediaSession();
  const p = curP;
  p.muted = false;
  const txt = s.queue[s.seg];
  tlog('▶ câu', `${txt.length}kt "${txt.slice(0, 28)}${txt.length > 28 ? '…' : ''}"${p.dataset.u === url && p.readyState > 0 ? (p.dataset.warm ? ' (tải sẵn, đã làm nóng)' : ' (tải sẵn, CHƯA làm nóng)') : ''}`, p);
  p.play().then(() => { okP = p; bgDenied = 0; if (id === reqId) retries = 0; tlog('  phát được', '', p); }).catch((e) => {
    tlog('  play() LỖI', e.name + (id !== reqId ? ' (cũ)' : ''), p);
    if (id !== reqId || e.name === 'AbortError') return;
    if (e.name === 'NotAllowedError') {
      if (document.hidden) {
        // Đang ở nền: thử lại 3 lần cách nhau 1,5s (loa im lặng giữ trang còn chạy) rồi mới chờ mở lại app
        tlog('⚠ bị chặn ở nền', `lần ${bgDenied + 1}`);
        if (++bgDenied <= 3) { retryTimer = setTimeout(() => { if (playing && id === reqId) playSeg(false); }, 1500); return; }
        bgDenied = 0; resumeOnVisible = true; return;
      }
      // Màn sáng mà bị chặn = loa này chưa được mở khoá ⇒ đọc tiếp trên loa vừa phát được, bỏ chế độ nhiều loa
      if (okP && okP !== p && !singleSpeaker) {
        console.warn('Loa bị iPhone chặn ⇒ chuyển sang đọc 1 loa'); tlog('⚠ chuyển sang đọc 1 loa');
        singleSpeaker = true; p.pause(); curP = okP;
        playSeg(false);
        return;
      }
      // Cả loa đó cũng bị chặn ⇒ dừng hẳn + báo rõ (trước đây đứng im mà nút vẫn hiện đang phát)
      tlog('⚠ cả loa dự phòng bị chặn ⇒ DỪNG');
      pauseAudio();
      showToast('Điện thoại chặn tự phát — bấm Nghe để đọc tiếp', 'error');
      return;
    }
    retryLater(id);
  });
  // Tải sẵn PRELOAD câu kế vào các loa rảnh (iPhone tắt màn hình / chế độ 1 loa thì không dùng tới ⇒ không tải)
  if (!(document.hidden && IS_IOS) && !singleSpeaker) {
    const want = [];
    for (let k = 1; k <= PRELOAD && s.seg + k < s.queue.length; k++) want.push(ttsUrl(s.queue[s.seg + k]));
    for (const u of want) {
      if (pool.some((a) => a.dataset.u === u && !a.error)) continue;
      const free = pool.find((a) => a !== curP && !want.includes(a.dataset.u));
      if (!free) break;
      free.src = u; free.dataset.u = u; delete free.dataset.warm; free.load();
      // Tua sẵn qua im lặng đầu file ngay khi biết độ dài ⇒ tới lượt phát ngay, không mất thời gian tua
      // Làm nóng: chạy thử TẮT TIẾNG 1 chút rồi đứng ở TTS_LEAD (bỏ im lặng đầu file) ⇒ buộc tải đủ dữ liệu + trình phát
      // đã khởi động sẵn ⇒ tới lượt phát ngay.
      const warmU = u;
      free.onloadedmetadata = () => {
        if (free === curP || free.dataset.u !== warmU) return;
        free.muted = true;
        free.play().then(() => setTimeout(() => {
          if (free === curP || free.dataset.u !== warmU) { free.muted = false; return; }
          free.pause(); free.muted = false;
          try { free.currentTime = TTS_LEAD; } catch (e) {}
          free.dataset.warm = '1';
        }, 60)).catch((e) => { free.muted = false; tlog('  làm nóng loa tải sẵn lỗi', e.name, free); });
      };
    }
  }
  curP.onended = () => {
    if (!playing || id !== reqId) return;
    if (s.seg + 1 < s.queue.length) {
      s.seg++;
      playSeg(false); // playSeg tự chọn loa đã tải sẵn câu này (màn tắt: giữ nguyên loa)
    } else if (s.loading) {
      // Hết các chương đã tải mà truyện còn đang tải ⇒ chờ tải xong đọc tiếp (KHÔNG coi là hết truyện)
      s.pendingNext = true;
      showToast('Đang tải chương tiếp...');
    } else if (s.ch + 1 < s.chapters.length) {
      showToast('Hết chương, sang chương tiếp...');
      setChapter(s, s.ch + 1);
    } else {
      pauseAudio();
      histSet(s.story.uid, { done: true });
      showToast('Đã đọc hết truyện!', 'success');
    }
  };
  curP.onerror = () => { if (playing && id === reqId) retryLater(id); };
  // Hẹn chuyển câu sớm ttsTail giây (bỏ im lặng cuối file); hẹn lại khi biết độ dài / đổi tốc độ / phát tiếp sau khựng
  curP.onplaying = curP.ondurationchange = curP.onratechange = () => { if (playing && id === reqId) armEarly(p, id); };
  // Google gửi file không báo độ dài ⇒ lúc bắt đầu phát chưa biết (∞) ⇒ vừa biết độ dài trong lúc phát là hẹn ngay
  curP.ontimeupdate = () => { if (playing && id === reqId && earlyArmed !== id && isFinite(p.duration)) armEarly(p, id); };
  armEarly(p, id);
}

// Lỗi mạng / Google từ chối ⇒ thử lại câu đó (2s, 4s, 6s...), tối đa 5 lần rồi mới dừng
function retryLater(id) {
  clearTimeout(retryTimer);
  tlog('⚠ lỗi tải câu ⇒ thử lại', `lần ${retries + 1}`);
  if (++retries > 5) {
    retries = 0;
    pauseAudio();
    showToast('Mất kết nối giọng đọc — bấm Nghe để thử lại', 'error');
    return;
  }
  retryTimer = setTimeout(() => {
    if (playing && id === reqId) { curP.removeAttribute('src'); delete curP.dataset.u; segVariant++; playSeg(false); }
  }, 2000 * retries);
}

// Bộ canh: đang phát mà âm thanh đứng yên > 8s (Google gửi chậm / nghẽn mạng: trình duyệt chờ mãi, không báo lỗi,
// không báo hết câu ⇒ trước đây kẹt tới khi chạm 2 lần vào câu) ⇒ tự tải lại câu đó
// Bộ canh âm thanh (kiểm mỗi 0,2s) — đo trên Android thật 2026-11-26:
// 1) Đứng ĐÚNG CUỐI FILE mà không có 'ended' (điện thoại hay bị ở file ngắn vài từ) ⇒ sang câu kế sau ~0,4s.
// 2) Đứng GIỮA câu (mạng khựng, hệ thống tạm ngắt tiếng) ⇒ KHÔNG được coi là hết câu (sẽ cắt mất nửa câu sau):
//    1s thử phát tiếp; 4s vẫn đứng ⇒ đọc lại câu đó từ đầu.
// 3) Chưa phát được gì ⇒ 8s tải lại. Tải lại 2 lần vẫn hỏng ⇒ bỏ qua câu đó (không kẹt cả truyện vì 1 câu).
let watchT = -1, watchStuck = 0, watchSeg = null, watchReloads = 0;
const WATCH_MS = 200;
const atAudioEnd = (a) => isFinite(a.duration) && a.duration > 0 && a.currentTime >= a.duration - 0.15;
function watchReload(why) {
  watchStuck = 0;
  if (++watchReloads > 3) {
    console.warn('Câu', player.seg + 1, 'không phát được ⇒ bỏ qua'); tlog('⚠ bộ canh: tải lại 3 lần vẫn hỏng ⇒ BỎ QUA câu');
    if (curP.onended) curP.onended();
  } else {
    segVariant++;
    console.warn(why, '⇒ tải lại câu', player.seg + 1); tlog('⚠ bộ canh: ' + why + ' ⇒ tải lại câu (địa chỉ mới r=' + segVariant + ')');
    stopSegAudio();
    playSeg(false);
  }
}
setInterval(() => {
  if (!playing || resumeOnVisible || !player || player.pendingNext) { watchStuck = 0; return; }
  const key = player.ch + ':' + player.seg;
  if (key !== watchSeg) { watchSeg = key; watchReloads = 0; }
  const t = curP.currentTime;
  if (t !== watchT) { watchT = t; watchStuck = 0; return; }
  watchStuck++;
  const sec = watchStuck * WATCH_MS / 1000;
  if (t > 0.3 && atAudioEnd(curP)) {
    if (sec >= 0.4) {
      watchStuck = 0;
      console.warn('Câu', player.seg + 1, 'hết mà không báo ⇒ sang câu kế'); tlog('⚠ bộ canh: hết câu mà không báo ⇒ sang câu kế');
      if (curP.onended) curP.onended();
    }
  } else if (t > 0.3 && !(curP.networkState === 2 && curP.readyState < 3)) {
    if (watchStuck === Math.round(1000 / WATCH_MS)) { tlog('⚠ bộ canh: đứng giữa câu ⇒ phát tiếp'); curP.play().catch(() => {}); }
    else if (sec >= 4) watchReload('Đứng giữa câu');
  } else if (t <= 0.3 && curP.readyState >= 3 && !curP.paused && sec >= 2.5) watchReload('Kẹt ở 0s dù đã có dữ liệu');
  else if (sec >= 8) watchReload('Âm thanh kẹt');
}, WATCH_MS);

// Mở lại app sau khi điện thoại chặn phát ⇒ phát tiếp đúng câu
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && playing && resumeOnVisible) {
    resumeOnVisible = false;
    playSeg(false);
  }
});

// Màn hình khoá / tai nghe: tên truyện + chương, nút phát/dừng, câu trước/sau, chương trước/sau
function updateMediaSession() {
  if (!('mediaSession' in navigator) || !player) return;
  try {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: player.story.title,
      artist: `${player.chapters[player.ch].title} · Đoạn ${player.seg + 1}/${player.queue.length}`,
      album: 'Kho Truyện',
    });
    navigator.mediaSession.playbackState = playing ? 'playing' : 'paused';
  } catch (e) {}
}
if ('mediaSession' in navigator) {
  const set = (a, fn) => { try { navigator.mediaSession.setActionHandler(a, fn); } catch (e) {} };
  set('play', () => { if (player && !playing) startPlay(player); });
  set('pause', () => { if (playing) pauseAudio(); updateMediaSession(); });
  set('seekbackward', () => player && seekTo(player, player.seg - 1));
  set('seekforward', () => player && seekTo(player, player.seg + 1));
  set('previoustrack', () => player && setChapter(player, player.ch - 1));
  set('nexttrack', () => player && setChapter(player, player.ch + 1));
}

// Thanh tua theo đoạn: kéo chỉ xem trước (tô câu + chữ), thả tay mới tua
function bindSeek(input, getS) {
  input.oninput = () => { input.dataset.drag = '1'; paintAll(false, getS(), +input.value); };
  input.onchange = () => { if (!input.dataset.drag) return; delete input.dataset.drag; seekTo(getS(), +input.value); };
  input.addEventListener('pointercancel', input.onchange);
  // Cảm ứng: thanh range của iPhone chỉ kéo được khi chạm trúng nút tròn (rất nhỏ / thanh đáy còn ẩn hẳn) ⇒ hay "mất" thanh tua.
  // Tự tính theo ngón tay: chạm chỗ nào trên thanh là tới đó, kéo tiếp được, thả tay mới tua.
  // Ô range bị tắt chạm trên cảm ứng (CSS) ⇒ nghe chạm ở khung bọc (.ab-seek / .adp-seek), không để range tự nhảy giành với tay
  const area = input.closest('.ab-seek, .adp-seek') || input;
  area.addEventListener('pointerdown', (e) => {
    if (e.pointerType === 'mouse') return;
    const r0 = input.getBoundingClientRect();
    if (e.clientX < r0.left - 16 || e.clientX > r0.right + 16) return; // chạm vào chữ "Đoạn 5" 2 bên ⇒ bỏ qua
    e.preventDefault();
    const at = (x) => {
      const r = input.getBoundingClientRect();
      input.value = Math.round(Math.min(1, Math.max(0, (x - r.left) / r.width)) * +input.max);
      input.dispatchEvent(new Event('input'));
    };
    const move = (ev) => at(ev.clientX);
    const up = () => {
      area.removeEventListener('pointermove', move);
      area.removeEventListener('pointerup', up);
      area.removeEventListener('pointercancel', up);
      input.onchange();
    };
    try { area.setPointerCapture(e.pointerId); } catch (_) {}
    area.addEventListener('pointermove', move);
    area.addEventListener('pointerup', up);
    area.addEventListener('pointercancel', up);
    at(e.clientX);
  });
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
  // 1 lượt đọc có thể gồm vài câu ngắn gộp lại (buildChapter) ⇒ tô hết các câu của lượt đó, cuộn tới câu đầu
  const els = document.querySelectorAll(`#storyContent .seg[data-i="${i}"]`);
  const el = els[0];
  if (el) {
    els.forEach((x) => x.classList.add('on'));
    if (scroll && followRead && !document.querySelector('#textSec.closed')) scrollSegIntoBox(el);
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
  // "Nhật ký phát" ở ĐẦU bảng (để cuối thì trên điện thoại bị khuất, phải cuộn mới thấy)
  $('rateMenu').innerHTML = `<button class="ab-menu-log" data-log>${icon('list', 'sm')}<span>Nhật ký phát</span><em>${tlogBuf.length}</em></button>`
    + '<div class="ab-menu-h">Tốc độ đọc</div>'
    + RATES.map((r) => `<button class="${r === rate ? 'on' : ''}" data-rate="${r}"><span>${r}x${r === 1 ? ' (thường)' : ''}</span><em>${r === rate ? icon('check', 'sm') : ''}</em></button>`).join('');
}

// Hộp xem nhật ký phát: khung chữ nhỏ, tự xuống dòng ⇒ chụp 1 màn hình là thấy đủ (ô nhập trên điện thoại bị ép chữ 16px
// ⇒ tràn ngang). Nút Sao chép dùng 1 ô ẩn tạm thời.
function openTtsLog() {
  let m = $('ttsLogModal');
  if (!m) {
    m = document.createElement('div');
    m.className = 'modal'; m.id = 'ttsLogModal';
    m.innerHTML = `<div class="modal-box log-box">
      <div class="modal-head">${icon('list')} Nhật ký phát<button class="ab-btn" data-close title="Đóng">${icon('x')}</button></div>
      <p>Khi bị dừng: mở đây, chụp màn hình (hoặc Sao chép) gửi lại. Mới nhất ở dưới cùng.</p>
      <div class="log-text" id="ttsLogText"></div>
      <div class="modal-foot">
        <button class="icon-btn" data-clear>${icon('trash', 'sm')} Xoá</button>
        <button class="icon-btn primary" data-copy>${icon('copy', 'sm')} Sao chép</button>
      </div></div>`;
    document.body.appendChild(m);
    m.onclick = (e) => {
      if (e.target === m || e.target.closest('[data-close]')) m.hidden = true;
      else if (e.target.closest('[data-clear]')) { tlogBuf = []; lsSet('ttsLog', '[]'); $('ttsLogText').textContent = ''; }
      else if (e.target.closest('[data-copy]')) {
        const ta = document.createElement('textarea'); ta.value = tlogBuf.join(String.fromCharCode(10));
        ta.setAttribute('readonly', ''); ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
        document.body.appendChild(ta); ta.focus(); ta.select(); ta.setSelectionRange(0, ta.value.length);
        let done = false; try { done = document.execCommand('copy'); } catch (er) {}
        ta.remove();
        if (!done && navigator.clipboard) navigator.clipboard.writeText(ta.value).then(() => showToast('Đã sao chép', 'success'), () => {});
        else showToast(done ? 'Đã sao chép' : 'Không sao chép được — giữ tay vào ô chữ để chọn', done ? 'success' : 'error');
      }
    };
  }
  $('ttsLogText').textContent = tlogBuf.join(String.fromCharCode(10));
  m.hidden = false;
  $('ttsLogText').scrollTop = $('ttsLogText').scrollHeight;
}

// ---- Thanh phát ở đáy (luôn điều khiển truyện đang nghe) ----
(() => {
  const AB = (sel) => document.querySelector('#abar ' + sel);
  AB('.ab-play').onclick = togglePlay;
  AB('.ab-back').onclick = () => seekTo(player, player.seg - 1);
  AB('.ab-fwd').onclick = () => seekTo(player, player.seg + 1);
  AB('.ab-prev').onclick = () => setChapter(player, player.ch - 1);
  AB('.ab-next').onclick = () => setChapter(player, player.ch + 1);
  AB('.ab-close').onclick = () => { pauseAudio(); barClosed = true; $('abar').hidden = true; document.documentElement.classList.remove('has-abar'); updateFoldBtn(); refitReadBox(); };
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
    if (e.target.closest('[data-log]')) { $('rateMenu').hidden = true; openTtsLog(); return; }
    const b = e.target.closest('[data-rate]');
    if (!b) return;
    rate = +b.dataset.rate;
    lsSet('ttsRate', rate);
    pool.forEach((a) => { a.playbackRate = rate; });
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
    document.documentElement.classList.add('has-abar'); refitReadBox();
    paintAll();
    updateFoldBtn();
  } catch (e) {}
}
restoreLastPlayed();

// Lịch sử mới tải về từ máy khác ⇒ truyện ĐANG DỪNG trên máy này lấy vị trí mới (trước đây vẫn giữ vị trí cũ trong bộ nhớ:
// bấm ▶ là đọc lại chỗ cũ rồi ghi đè vị trí mới của máy kia). Đang phát thì máy này là bản mới nhất ⇒ giữ nguyên.
function applyRemotePos(s) {
  if (!s || !s.chapters.length || (s === player && playing)) return;
  const h = histGet(s.story.uid);
  if (!h) return;
  const ch = Math.min(h.ch || 0, s.chapters.length - 1);
  if (ch === s.ch && (h.i || 0) === s.seg) return;
  if (ch !== s.ch) { s.ch = ch; buildChapter(s); }
  s.seg = Math.min(h.i || 0, Math.max(0, s.queue.length - 1));
  if (s === view && !$('readView').hidden) renderContent();
}
window.addEventListener('histchange', () => {
  applyRemotePos(player);
  if (view !== player) applyRemotePos(view);
  paintAll();
  restoreLastPlayed();
});
