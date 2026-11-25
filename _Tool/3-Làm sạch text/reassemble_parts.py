# -*- coding: utf-8 -*-
"""
Nối các file bị cắt (_1, _2, ...) thành file gốc.
Xóa các file phần sau khi nối thành công.
"""
import os, re

DIR = r'c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao\2-Cha Chồng - Con Dâu'

files = os.listdir(DIR)
parts_map = {}

for f in files:
    m = re.match(r'^(.+?)_(\d+)\.txt$', f)
    if m:
        base, num = m.group(1), int(m.group(2))
        if base not in parts_map:
            parts_map[base] = []
        parts_map[base].append((num, f))

print(f"Tìm thấy {len(parts_map)} file bị cắt:\n")

for base, parts in sorted(parts_map.items()):
    parts.sort(key=lambda x: x[0])
    output_name = base + '.txt'
    output_path = os.path.join(DIR, output_name)
    part_names = [p[1] for p in parts]
    total_size = sum(os.path.getsize(os.path.join(DIR, p)) for p in part_names)
    print(f"  [{base}]  {len(parts)} phần → {output_name}  ({total_size//1024} KB)")

    # Nối nội dung
    combined = []
    for _, fname in parts:
        fpath = os.path.join(DIR, fname)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        combined.append(content)

    # Ghi file gốc
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(combined))

    # Xóa các file phần
    for _, fname in parts:
        os.remove(os.path.join(DIR, fname))
        print(f"    ✓ Đã xóa {fname}")
    print(f"    ✅ Đã tạo {output_name} ({os.path.getsize(output_path)//1024} KB)\n")

print("Hoàn thành!")
