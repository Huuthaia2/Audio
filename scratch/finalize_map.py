import os
import json
import re

base_dir = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
script_path = r"d:\z\Audio\_Tool\Audio\_Tool\auto_sort_giaothao.py"

ROOT_MAP = {
    1: ['mẹ con', 'mẹ kế', 'mẹ nuôi', 'mẹ và con'],
    2: ['cha chồng - con dâu', 'cha chồng', 'con dâu', 'bố chồng', 'nàng dâu', 'ba chồng'],
    3: ['cave', 'gái gọi', 'phò', 'chơi gái', 'gái bán hoa'],
    4: ['he', 'happy ending', 'ngôn tình'],
    5: ['chi dâu', 'chị dâu', 'anh rể', 'em dâu'],
    6: ['anh em - chị em', 'anh em', 'chị em', 'em gái', 'anh trai', 'em ruột'],
    7: ['hàng xóm', 'vợ hàng xóm', 'cạnh nhà'],
    8: ['loạn luân', 'loan luan', 'huyết thống', 'gia đình loạn'],
    9: ['mẹ bạn', 'me ban'],
    10: ['mẹ vợ', 'con rể', 'me vo'],
    11: ['6 múi', 'sáu múi'],
    12: ['máy bay', 'phi công', 'milf', 'u40', 'u50'],
    13: ['cô giáo - học sinh', 'cô giáo', 'học sinh', 'gia sư', 'thầy giáo', 'mái trường', 'học đường'],
    14: ['ngoại tình', 'cắm sừng', 'ntr', 'cuckold', 'vợ ngoại tình'],
    15: ['y tá - bác sĩ', 'y tá', 'bác sĩ', 'bệnh viện', 'phụ khoa'],
    16: ['bạo dâm', 'slave', 'hiếp dâm', 'cưỡng hiếp', 'bdsm', 'bồn chứa', 'no lệ', 'cưỡng dâm', 'ác mộng', 'cưỡng', 'sát'],
    17: ['vợ dâm', 'gái dâm', 'gái xinh', 'vợ bạn', 'vợ đảm', 'kiều nữ', 'khỏa thân', 'tân hôn'],
    18: ['chuyện cũ', 'quá khứ', 'hồi ức', 'kỷ niệm', 'chuyện tình', 'chuyện'],
    19: ['ghen tuông'],
    20: ['dâm thư trung quốc', 'trung quốc', 'dâm thư', 'china'],
    21: ['truyện trung'],
    22: ['truyện dâm hiệp', 'dâm hiệp', 'tiên hiệp', 'huyền huyễn', 'tu tiên'],
    23: ['kỹ năng & hành động', 'kỹ năng', 'hành động', 'doggy', 'vét máng', 'bú cu', 'thế xác', 'mày mò', 'làm tình', 'húp sò', 'chịch', 'đụ'],
    24: ['địa điểm & đối tượng', 'sinh viên', 'nhân viên', 'địa điểm', 'công sở', 'thư ký', 'văn phòng', 'giám đốc', 'xóm trọ', 'khách sạn', 'xe bus', 'tàu', 'máy bay', 'nhà trọ', 'tour'],
    25: ['dị thường & thế giới khác', 'dị thường', 'thế giới khác', 'harem', 'phiêu lưu', 'lesbian', 'thu vật', 'xuyên không', 'mario', 'ngọc rồng', 'doremon', 'bạch tuyết', 'sơn tinh', 'truyện cổ tích', 'emmanuelle', 'toy', 'con giáp', 'loli', 'tấm'],
    26: ['phong cách & cảm xúc', 'phong cách', 'cảm xúc', 'slice of life', 'thiếu niên', 'người tình', 'tình đơn phương', 'mảnh ghép', 'sắc màu', 'ngày đầu', 'mùa hạ', 'gác', 'góc khuất', 'ra đời', 'đàn bà']
}

result = {}
folders = os.listdir(base_dir)
for f in folders:
    f_path = os.path.join(base_dir, f)
    if os.path.isdir(f_path) and '-' in f:
        prefix_str = f.split('-')[0]
        if prefix_str.isdigit():
            prefix = int(prefix_str)
            subfolders = [sf.lower() for sf in os.listdir(f_path) if os.path.isdir(os.path.join(f_path, sf))]
            root_kws = ROOT_MAP.get(prefix, [])
            all_kws = list(dict.fromkeys(root_kws + subfolders))
            result[prefix] = all_kws

# Fallback for missing IDs in folders but present in ROOT_MAP
for cid in ROOT_MAP:
    if cid not in result:
        result[cid] = ROOT_MAP[cid]

# Generate CATEGORY_MAP string
map_entries = []
for cid in sorted(result.keys()):
    entry = f'    ({cid}, {json.dumps(result[cid], ensure_ascii=False)})'
    map_entries.append(entry)

map_str = "CATEGORY_MAP = [\n" + ",\n".join(map_entries) + "\n]"

with open(script_path, 'r', encoding='utf-8') as f:
    script_content = f.read()

new_content = re.sub(r'CATEGORY_MAP = \[.*?\]', map_str, script_content, flags=re.DOTALL)

with open(script_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated auto_sort_giaothao.py with full mapping successfully!")
