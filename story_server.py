#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server phục vụ trang web đọc truyện tóm tắt
Run: python story_server.py
Sau đó mở: http://localhost:8765
"""

import os
import json
import re
import requests
import socketserver
import uuid
import io
import time
from gtts import gTTS
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote, quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOMTAT_DIR = os.path.join(BASE_DIR, "Tóm tắt")
RAW_DIR = os.path.join(BASE_DIR, "truyencogiaothao")

def remove_accents(input_str):
    if not input_str: return ""
    import unicodedata
    s1 = unicodedata.normalize('NFD', input_str)
    s1 = ''.join([c for c in s1 if unicodedata.category(c) != 'Mn'])
    return s1.replace('đ', 'd').replace('Đ', 'D')

def get_categories():
    categories = {}
    if not os.path.isdir(TOMTAT_DIR): return categories
    for d in os.listdir(TOMTAT_DIR):
        if os.path.isdir(os.path.join(TOMTAT_DIR, d)):
            display_name = re.sub(r'^\d+-', '', d)
            categories[d] = display_name
    return categories

CATEGORIES = get_categories()

def slug_to_title(slug):
    """Chuyển slug file thành tên hiển thị"""
    name = os.path.splitext(slug)[0]
    # Loại bỏ hậu tố chương như -0001, +chuong 0001, -part 1, +123
    name = re.sub(r'[\-\+](chuong|part|chapter|chương)?\s*\d+.*$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'-\d+$', '', name)
    name = re.sub(r'\+\d+$', '', name)
    
    name = name.replace('-', ' ').replace('_', ' ').replace('+', ' ')
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

def get_all_stories():
    stories = []
    for folder, cat_name in CATEGORIES.items():
        path = os.path.join(TOMTAT_DIR, folder)
        if not os.path.isdir(path):
            continue
        for fname in sorted(os.listdir(path)):
            if not fname.endswith('.txt'):
                continue
            fpath = os.path.join(path, fname)
            size = os.path.getsize(fpath)
            # Kiểm tra có file truyện gốc không
            raw_path = os.path.join(RAW_DIR, folder, fname)
            has_raw = os.path.exists(raw_path)
            stories.append({
                "id": f"{folder}/{fname}",
                "file": fname,
                "folder": folder,
                "category": cat_name,
                "title": slug_to_title(fname),
                "size": size,
                "has_summary": size > 1000,
                "has_raw": has_raw,
            })
    return stories

def read_any_file(uid):
    if not uid: return None
    # Nếu uid đã có base (vd: "Text Mp3/M3/...")
    path = os.path.join(BASE_DIR, uid)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(800 * 1024) # 800KB
        except: pass
    return None

def read_story_file(story_id):
    # Trử về summary
    path = os.path.join(TOMTAT_DIR, story_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    return None

def read_raw_file(story_id):
    # Story_id ở đây thường là folder/file.txt
    fpath = os.path.join(RAW_DIR, story_id)
    if not os.path.exists(fpath):
        return None, 0
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(800000)
    total_size = os.path.getsize(fpath)
    return content, total_size

# --- HỖ TRỢ ĐA LUỒNG (THREADING) ---
class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True

class StoryHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # tắt log

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200):
        body = html.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Requested-With, Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)
            
            if path.startswith('/api/'):
                print(f"[*] API Request: {path} - Query: {qs}")

            # Phục vụ file tĩnh mặc định
            if path == '/' or path == '/index.html':
                fpath = os.path.join(BASE_DIR, 'index.html')
                if os.path.exists(fpath):
                    with open(fpath, 'r', encoding='utf-8') as f:
                        self.send_html(f.read())
                    return
            
            if path == '/reader.html':
                fpath = os.path.join(BASE_DIR, 'reader.html')
                if os.path.exists(fpath):
                    with open(fpath, 'r', encoding='utf-8') as f:
                        self.send_html(f.read())
                    return

            # TTS PROXY: DÙNG GOOGLE TTS (SỬ DỤNG BYTESIO)
            elif path == '/tts':
                text = qs.get('q', [''])[0]
                if not text:
                    self.send_response(400); self.end_headers(); return
                
                print(f"[*] Đang lấy giọng Chị Google: {text[:30]}...")
                
                try:
                    mp3_fp = io.BytesIO()
                    tts = gTTS(text=text, lang='vi')
                    tts.write_to_fp(mp3_fp)
                    audio_data = mp3_fp.getvalue()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'audio/mpeg')
                    self.send_header('Content-Length', len(audio_data))
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    try:
                        self.wfile.write(audio_data)
                        print("    -> Thành công!")
                    except:
                        print("    -> Client ngắt kết nối")
                except Exception as e:
                    print(f"    -> Lỗi gTTS: {e}")
                    try: self.send_response(500); self.end_headers()
                    except: pass
                return

            # Các API khác
            if path == '/api/stories':
                self.send_json(get_all_stories()); return
            
            if path == '/api/search':
                query = qs.get('q', [''])[0].strip()
                if not query:
                    self.send_json([]); return
                
                print(f"[*] Đang tìm kiếm sâu cho: '{query[:50]}...'")
                import time
                
                # Tiền xử lý query: Bỏ dấu, viết thường, chuẩn hóa khoảng trắng
                q_norm = " ".join(remove_accents(query).lower().split())
                q_words = [w for w in q_norm.split() if len(w) > 1]
                
                # Từ mốc để lọc nhanh (chọn 2 từ dài nhất)
                anchors = sorted(q_words, key=len, reverse=True)[:2] if q_words else []
                
                start_time = time.time()
                results = []
                
                stories_path = os.path.join(BASE_DIR, "stories.json")
                if os.path.exists(stories_path):
                    with open(stories_path, 'r', encoding='utf-8') as f:
                        all_stories = json.load(f)
                else:
                    all_stories = get_all_stories()

                print(f"    -> Đã nạp {len(all_stories)} truyện. Bắt đầu quét chính xác...")

                for i, s in enumerate(all_stories):
                    if i % 1000 == 0 and i > 0:
                        print(f"    -> Đã quét {i}/{len(all_stories)} truyện...")
                        
                    title = s.get('title','')
                    # 1. Tìm trong tiêu đề (Vẫn giữ logic cũ vì tiêu đề ngắn)
                    if q_norm in remove_accents(title).lower():
                        s['match_type'] = 'title'
                        results.append(s)
                        if len(results) >= 50: break
                        continue
                    
                    # 2. Tìm trong nội dung
                    uid = s.get('uid')
                    if not uid: continue
                    
                    content = read_any_file(uid)
                    if not content: continue
                    
                    # Chỉ lấy 300KB đầu để tìm kiếm cho nhanh
                    content_sample = content[:300000].lower()
                    
                    # LỌC NHANH: Nếu các từ mốc không xuất hiện (cả có dấu/không dấu) thì bỏ qua luôn
                    quick_fail = False
                    for anchor in anchors:
                        if anchor not in content_sample and anchor not in remove_accents(content_sample):
                            quick_fail = True
                            break
                    if quick_fail: continue
                    
                    # KIỂM TRA CHÍNH XÁC CỤM TỪ (Phrase Match)
                    # Chuẩn hóa nội dung truyện
                    content_norm = " ".join(remove_accents(content_sample).split())
                    
                    if q_norm in content_norm:
                        print(f"    [+] Tìm thấy: {title}")
                        s['match_type'] = 'content'
                        results.append(s)
                        if len(results) >= 50: break
                    elif len(q_words) <= 3:
                        # Nếu query ngắn (<= 3 từ), thử kiểm tra xem tất cả các từ có xuất hiện không
                        if all(w in content_norm for w in q_words):
                            s['match_type'] = 'content_loose'
                            results.append(s)
                            if len(results) >= 50: break
                
                print(f"[*] Hoàn tất trong {time.time() - start_time:.2f}s. Kết quả: {len(results)}")
                self.send_json(results); return

            if path == '/api/story':
                sid = unquote(qs.get('id', [''])[0])
                content = read_story_file(sid)
                if content: self.send_json({'id': sid, 'content': content})
                else: self.send_json({'error': 'Not found'}, 404)
                return

            # Nếu không khớp cái nào thì dùng trình phục vụ file mặc định
            return super().do_GET()

        except Exception as e:
            print(f"!!! LỖI SERVER: {e}")
            self.send_response(500); self.end_headers()

        else:
            self.send_json({'error': 'Not found'}, 404)

if __name__ == '__main__':
    port = 9999
    server = ThreadedHTTPServer(('0.0.0.0', port), StoryHandler)
    print("========================================")
    print(f"🌟 TTS PROXY - ĐA LUỒNG SIÊU ỔN ĐỊNH")
    print(f"🌟 Đang chạy tại: http://localhost:{port}")
    print("========================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer đã dừng.")
