// Service worker Kho Truyện — lưu sẵn trên máy để mở app tức thì, truyện đã đọc mở lại được cả khi mất mạng.
// - Khung web (html/js/css/icon) + stories.json: trả bản đã lưu NGAY, tải bản mới ở nền; bản mới khác ⇒ báo trang
//   "Có bản cập nhật" (chạm để tải lại)
// - File truyện (Truyện/...): trả bản đã lưu ngay + tải lại ở nền; giữ tối đa STORY_MAX truyện mở gần nhất
// - KHÔNG đụng: giọng đọc TTS (Google / proxy 9999), GitHub Gist (đồng bộ lịch sử)
const SHELL = 'kho-shell-v1';
const STORY = 'kho-story-v1';
const STORY_MAX = 40;
const SHELL_FILES = ['./', 'index.html', 'ui.css', 'icons.js', 'library.js', 'reader.js', 'history.js', 'manifest.json', 'icons/icon-192.png', 'stories.json'];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(caches.open(SHELL).then((c) => c.addAll(SHELL_FILES)).catch(() => {}));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(Promise.all([
    self.clients.claim(),
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== SHELL && k !== STORY).map((k) => caches.delete(k)))),
  ]));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || req.headers.has('range')) return;
  const url = new URL(req.url);
  if (url.origin === self.location.origin) {
    const isStory = decodeURIComponent(url.pathname).includes('/Truyện/');
    e.respondWith(staleWhileRevalidate(e, req, isStory ? STORY : SHELL, isStory));
  } else if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    e.respondWith(cacheFirst(req, SHELL));
  }
});

// Trả bản đã lưu ngay (nếu có), đồng thời tải bản mới ⇒ lưu lại; chưa lưu ⇒ chờ mạng
async function staleWhileRevalidate(e, req, cacheName, isStory) {
  const cache = await caches.open(cacheName);
  const key = isStory ? req : new Request(req.url.split('?')[0]); // khung web: bỏ ?t=... để dùng chung 1 bản lưu
  const cached = await cache.match(key);
  const fresh = fetch(req).then(async (res) => {
    if (res.ok && res.type === 'basic') {
      await cache.put(key, res.clone());
      if (isStory) trim(cache);
      else if (cached && changed(cached, res)) notify();
    }
    return res;
  }).catch(() => null);
  if (cached) {
    e.waitUntil(fresh);
    return cached;
  }
  return (await fresh) || new Response('Mất mạng và chưa lưu sẵn trang này', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}

async function cacheFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(req);
  if (cached) return cached;
  const res = await fetch(req);
  if (res.ok || res.type === 'opaque') cache.put(req, res.clone());
  return res;
}

// Bản mới khác bản đã lưu? (GitHub Pages gửi ETag / Last-Modified)
function changed(a, b) {
  const ea = a.headers.get('etag'), eb = b.headers.get('etag');
  if (ea && eb) return ea !== eb;
  const la = a.headers.get('last-modified'), lb = b.headers.get('last-modified');
  return !!(la && lb && la !== lb);
}

let notified = false;
async function notify() {
  if (notified) return;
  notified = true;
  for (const c of await self.clients.matchAll()) c.postMessage({ type: 'update' });
}

// Giữ STORY_MAX truyện mở gần nhất (mỗi lần mở / tải lại ⇒ lên cuối hàng)
async function trim(cache) {
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - STORY_MAX; i++) await cache.delete(keys[i]);
}
