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
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

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

class StoryHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # tắt log

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
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == '/' or path == '/index.html':
            with open(os.path.join(BASE_DIR, 'story_reader.html'), 'r', encoding='utf-8') as f:
                self.send_html(f.read())

        elif path == '/api/stories':
            stories = get_all_stories()
            self.send_json(stories)

        elif path == '/api/story':
            sid = qs.get('id', [''])[0]
            sid = unquote(sid)
            content = read_story_file(sid)
            if content is None:
                self.send_json({'error': 'Not found'}, 404)
            else:
                self.send_json({'id': sid, 'content': content})

        elif path == '/api/categories':
            cats = [{"id": k, "name": v} for k, v in CATEGORIES.items()]
            self.send_json(cats)

        elif path == '/api/rawstory':
            sid = qs.get('id', [''])[0]
            sid = unquote(sid)
            result = read_raw_file(sid)
            if result is None:
                self.send_json({'error': 'Không tìm thấy file gốc'}, 404)
            else:
                content, total_size = result
                self.send_json({'id': sid, 'content': content, 'total_size': total_size})

        else:
            self.send_json({'error': 'Not found'}, 404)

if __name__ == '__main__':
    port = 8765
    server = HTTPServer(('localhost', port), StoryHandler)
    print(f"🌟 Story Reader đang chạy tại: http://localhost:{port}")
    print("   Nhấn Ctrl+C để dừng server")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer đã dừng.")
