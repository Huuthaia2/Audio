import os
import json
import re

base_dir = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"
script_path = r"d:\z\Audio\_Tool\Audio\_Tool\auto_sort_giaothao.py"

# 1. Quét subfolders
subfolders_map = {}
folders = os.listdir(base_dir)
for f in folders:
    f_path = os.path.join(base_dir, f)
    if os.path.isdir(f_path) and '-' in f:
        prefix = f.split('-')[0]
        if prefix.isdigit():
            sf_list = [sf.lower() for sf in os.listdir(f_path) if os.path.isdir(os.path.join(f_path, sf))]
            subfolders_map[int(prefix)] = sf_list

# 2. Đọc script hiện tại
with open(script_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 3. Định nghĩa lại CATEGORY_MAP chuẩn
# Chúng ta sẽ giữ lại các root keywords quan trọng và merge với subfolders
ROOT_KEYWORDS = {
    1: ["mẹ con", "mẹ kế", "mẹ nuôi", "mẹ và con"],
    2: ["cha chồng - con dâu", "cha chồng", "con dâu", "bố chồng", "nàng dâu", "ba chồng"],
    3: ["cave", "gái gọi", "phò", "chơi gái", "gái bán hoa"],
    4: ["he", "happy ending", "ngôn tình"],
    5: ["chi dâu", "chị dâu", "anh rể", "em dâu"],
    6: ["anh em - chị em", "anh em", "chị em", "em gái", "anh trai", "em ruột"],
    7: ["hàng xóm", "vợ hàng xóm", "cạnh nhà"],
    8: ["loạn luân", "loan luan", "huyết thống", "gia đình loạn"],
    9: ["mẹ bạn", "me ban"],
    10: ["mẹ vợ", "con rể", "me vo"],
    11: ["6 múi", "sáu múi"],
    12: ["máy bay", "phi công", "milf", "u40", "u50"],
    13: ["cô giáo - học sinh", "cô giáo", "học sinh", "gia sư", "thầy giáo", "mái trường", "học đường"],
    14: ["ngoại tình", "cắm sừng", "ntr", "cuckold", "vợ ngoại tình"],
    15: ["y tá - bác sĩ", "y tá", "bác sĩ", "bệnh viện", "phụ khoa"],
    16: ["bạo dâm", "slave", "hiếp dâm", "cưỡng hiếp", "bdsm", "bồn chứa", "no lệ", "cưỡng dâm", "ác mộng", "cưỡng", "sát"],
    17: ["vợ dâm", "gái dâm", "gái xinh", "vợ bạn", "vợ đảm", "kiều nữ", "khỏa thân", "tân hôn"],
    18: ["chuyện cũ", "quá khứ", "hồi ức", "kỷ niệm", "chuyện tình", "chuyện"],
    19: ["ghen tuông"],
    20: ["dâm thư trung quốc", "trung quốc", "dâm thư", "china"],
    21: ["truyện trung"],
    22: ["truyện dâm hiệp", "dâm hiệp", "tiên hiệp", "huyền huyễn", "tu tiên"],
    23: ["kỹ năng & hành động", "kỹ năng", "hành động", "doggy", "vét máng", "bú cu", "thế xác", "mày mò", "làm tình", "húp sò", "chịch", "đụ"],
    24: ["địa điểm & đối tượng", "sinh viên", "nhân viên", "địa điểm", "công sở", "thư ký", "văn phòng", "giám đốc", "xóm trọ", "khách sạn", "xe bus", "tàu", "máy bay", "nhà trọ", "tour"],
    25: ["dị thường & thế giới khác", "dị thường", "thế giới khác", "harem", "phiêu lưu", "lesbian", "thu vật", "xuyên không", "mario", "ngọc rồng", "doremon", "bạch tuyết", "sơn tinh", "truyện cổ tích", "emmanuelle", "toy", "con giáp", "loli", "tấm"],
    26: ["phong cách & cảm xúc", "phong cách", "cảm xúc", "slice of life", "thiếu niên", "người tình", "tình đơn phương", "mảnh ghép", "sắc màu", "ngày đầu", "mùa hạ", "gác", "góc khuất", "ra đời", "đàn bà"]
}

final_map = []
for cid in sorted(ROOT_KEYWORDS.keys()):
    kws = ROOT_KEYWORDS[cid]
    sfs = subfolders_map.get(cid, [])
    # Merge and remove duplicates
    all_kws = list(dict.fromkeys(kws + sfs))
    final_map.append(f"    ({cid}, {json.dumps(all_kws, ensure_ascii=False)})")

new_map_str = "CATEGORY_MAP = [\n" + ",\n".join(final_map) + "\n]"

# 4. Thay thế trong content
# Tìm block CATEGORY_MAP hiện tại
pattern = r"CATEGORY_MAP = \[.*?\]"
new_content = re.sub(pattern, new_map_str, content, flags=re.DOTALL)

with open(script_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updated CATEGORY_MAP successfully with all subfolder keywords!")
