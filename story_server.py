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
from gtts import gTTS
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote, quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOMTAT_DIR = os.path.join(BASE_DIR, "Tóm tắt")
RAW_DIR = os.path.join(BASE_DIR, "truyencogiaothao")

CATEGORIES = {
    "1-Mẹ Con": "Mẹ Con",
    "2-Cha Chồng - Con Dâu": "Cha Chồng - Con Dâu",
    "3-Cave": "Cave / Gái Gọi",
    "5-Chị dâu": "Chị Dâu",
    "6-Anh Em - Chị Em": "Anh Em - Chị Em",
    "8-Loạn Luân": "Loạn Luân",
}

def slug_to_title(slug):
    """Chuyển slug file thành tên hiển thị"""
    # Xóa số chương ở cuối như -0049
    name = re.sub(r'-\d+\.txt$', '', slug)
    name = name.replace('-', ' ')
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

def read_story_file(story_id):
    safe_id = story_id.replace('..', '')
    fpath = os.path.join(TOMTAT_DIR, safe_id)
    if not os.path.exists(fpath):
        return None
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def read_raw_file(story_id):
    safe_id = story_id.replace('..', '')
    fpath = os.path.join(RAW_DIR, safe_id)
    if not os.path.exists(fpath):
        return None
    # Giới hạn 500KB để tránh quá tải browser
    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(600000)
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

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

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
