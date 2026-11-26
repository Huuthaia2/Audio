// Trạm trung chuyển giọng đọc cho web Kho Truyện (Cloudflare Worker, gói miễn phí).
// Vì sao cần: Google translate_tts không cho trang web tải dữ liệu âm thanh (không CORS) và gửi file không báo độ dài
// (iPhone thỉnh thoảng kẹt ở 0s). Qua trạm này app được: tải sẵn nhiều câu vào bộ nhớ (kể cả lúc tắt màn hình),
// dò đúng chỗ hết tiếng của từng file để nối câu sát nhau, file có Content-Length.
// GET /tts?q=<câu ≤ 200 ký tự>  ⇒  audio/mpeg (nhớ tạm ở Cloudflare 7 ngày)

const ALLOW = ['https://huuthaia2.github.io', 'http://127.0.0.1:8765', 'http://localhost:8765', 'http://localtest.me:8765'];

function cors(origin) {
  return {
    'Access-Control-Allow-Origin': ALLOW.includes(origin) ? origin : ALLOW[0],
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Vary': 'Origin',
  };
}

export default {
  async fetch(req, env, ctx) {
    const origin = req.headers.get('Origin') || '';
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: cors(origin) });
    if (url.pathname !== '/tts') return new Response('Kho Truyện TTS', { headers: cors(origin) });

    // Chỉ phục vụ web của mình (đỡ người lạ dùng ké hết lượt miễn phí)
    const ref = req.headers.get('Referer') || '';
    if (origin ? !ALLOW.includes(origin) : !ALLOW.some((a) => ref.startsWith(a))) {
      return new Response('forbidden', { status: 403 });
    }

    const q = (url.searchParams.get('q') || '').trim();
    if (!q || q.length > 200) return new Response('bad q', { status: 400, headers: cors(origin) });

    const g = 'https://translate.googleapis.com/translate_tts?client=gtx&ie=UTF-8&tl=vi&q=' + encodeURIComponent(q);
    const cache = caches.default;
    const key = new Request(g);
    let body = null;
    const hit = await cache.match(key);
    if (hit) body = await hit.arrayBuffer();
    else {
      let up = null;
      for (let i = 0; i < 3 && !(up && up.ok); i++) {
        up = await fetch(g, { headers: { 'User-Agent': 'Mozilla/5.0' } });
      }
      if (!up.ok) return new Response('google ' + up.status, { status: 502, headers: cors(origin) });
      body = await up.arrayBuffer();
      ctx.waitUntil(cache.put(key, new Response(body.slice(0), { headers: { 'Content-Type': 'audio/mpeg', 'Cache-Control': 'public, max-age=604800' } })));
    }
    return new Response(body, {
      headers: {
        ...cors(origin),
        'Content-Type': 'audio/mpeg',
        'Content-Length': String(body.byteLength),
        'Cache-Control': 'public, max-age=86400',
        'X-Cache': hit ? 'HIT' : 'MISS',
      },
    });
  },
};
