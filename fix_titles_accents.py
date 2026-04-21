import os
import re

# Comprehensive map for common Vietnamese words in these titles
ACCENT_MAP = {
    "bo": "Bố", "chong": "Chồng", "hiep": "Hiếp", "con": "Con", "dau": "Dâu",
    "lam": "Làm", "du": "Đụ", "nang": "Nàng", "tuoi": "Tuổi", "phan": "Phận",
    "so": "Số", "tin": "Tin", "vao": "Vào", "lon": "Lồn", "bay": "Bảy",
    "ngay": "Ngày", "voi": "Với", "bi": "Bí", "mat": "Mật", "dai": "Đại",
    "gia": "Gia", "dinh": "Đình", "co": "Có", "hoi": "Hỏi", "ngay": "Ngây",
    "tho": "Thơ", "truyen": "Truyện", "kieu": "Kiều", "nu": "Nữ", "sinh": "Sinh",
    "dam": "Dâm", "dang": "Đãng", "nga": "Nga", "yen": "Yến", "cho": "Chó",
    "be": "Bé", "nha": "Nhà", "ben": "Bên", "cu": "Cu", "vo": "Vô", "dich": "Địch",
    "dan": "Đàn", "ba": "Bà", "do": "Đồ", "rieng": "Riêng", "ruot": "Ruột",
    "bac": "Bác", "hai": "Hai", "de": "Đẻ", "moi": "Mới", "lon": "Lớn",
    "muon": "Muốn", "la": "Là", "lai": "Lai", "chu": "Chủ", "tich": "Tịch",
    "nung": "Nứng", "xin": "Xin", "loi": "Lỗi", "di": "Dì", "chung": "Chung",
    "to": "Tổ", "am": "Ấm", "luc": "Lúc", "nhung": "Những", "chan": "Chân",
    "tay": "Tay", "bon": "Bốn", "thanh": "Thành", "than": "Thân", "tam": "Tâm",
    "day": "Dạy", "tap": "Tập", "boi": "Bơi", "luc": "Lúc", "nao": "Nào",
    "khong": "Không", "hay": "Hay", "nguyen": "Nguyện", "no": "Nô", "le": "Lệ",
    "tan": "Tân", "hon": "Hôn", "trang": "Trăng", "mai": "Mai", "tinh": "Tình",
    "thu": "Thu", "it": "Ít", "ut": "Út", "duoc": "Được", "giang": "Giang",
    "ho": "Họ", "nhu": "Như", "y": "Ý", "quan": "Quan", "he": "Hệ", "len": "Lén",
    "lut": "Lút", "tro": "Trọ", "quynh": "Quỳnh", "ranh": "Ranh", "gioi": "Giới",
    "cam": "Cấm", "ky": "Kỵ", "sang": "Sáng", "an": "Ăn", "nuoi": "Nuôi",
    "mua": "Mùa", "he": "Hè", "dang": "Đáng", "nho": "Nhớ", "dung": "Dung",
    "noi": "Nội", "nga": "Ngã", "ba": "Ba", "song": "Sông", "ngoai": "Ngoại",
    "chau": "Cháu", "go": "Gõ", "mo": "Mõ", "bong": "Bóng", "goa": "Góa",
    "kiep": "Kiếp", "truoc": "Trước", "nhan": "Nhân", "nhat": "Nhật", "ky": "Ký",
    "tho": "Thơ", "nhin": "Nhìn", "ke": "Kế", "thu": "Thủ", "hu": "Hư",
    "hong": "Hỏng", "ngo": "Ngơ", "ngao": "Ngáo", "than": "Thần", "xinh": "Xinh",
    "dep": "Đẹp", "nuoc": "Nước", "mat": "Mắt", "mua": "Mùa", "thu": "Thu",
    "o": "Ở", "pha": "Phá", "trinh": "Trinh", "du": "Dư", "hy": "Hỷ",
    "phu": "Phụ", "trad": "Trần", "truong": "Trường", "gia": "Gia", "thong": "Thông",
    "buon": "Buồn", "dam": "Đắm", "co": "Cô", "nuong": "Nương", "ve": "Về",
    "doi": "Đời", "tho": "Thơ", "ngay": "Ngây", "tre": "Trẻ", "lan": "Lan",
    "que": "Quê", "vet": "Vết", "loi": "Lỗi", "dung": "Đừng", "vung": "Vùng",
    "heo": "Hẻo", "lanh": "Lánh", "binh": "Bình", "trom": "Trộm", "vuot": "Vượt",
    "xe": "Xem", "trai": "Trai", "yeu": "Yêu", "em": "Em", "chi": "Chị", "at": "Ất", "mui": "Mùi",
    "massage": "Massage", "khach": "Khách", "vien": "Viên",
    "chinh": "Chinh", "phuc": "Phục", "gai": "Gái"
}

def fix_title_text(text):
    # Split by spaces and keep case
    words = text.split()
    fixed_words = []
    for w in words:
        # Check lowercase version in map
        key = w.lower().strip(",.!?()+-")
        if key in ACCENT_MAP:
            # Try to match case (Capitalized or lower)
            fixed_w = ACCENT_MAP[key]
            if w[0].islower():
                fixed_w = fixed_w.lower()
            fixed_words.append(fixed_w)
        else:
            fixed_words.append(w)
    return " ".join(fixed_words)

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    if not lines:
        return

    content = "".join(lines)
    
    # Try to find the accented title in the text body (often at "Bạn đang đọc truyện...")
    # This is much more reliable than the map
    pattern = re.compile(r"Bạn đang đọc truyện\s+(.*?)\s+tại nguồn", re.IGNORECASE)
    match = pattern.search(content)
    
    if match:
        accented_title = match.group(1).strip()
        # Sanity check: shouldn't be too long or contain URLs
        if 2 < len(accented_title) < 100 and "http" not in accented_title.lower():
            # Update the first line
            if lines[0].startswith("TITLE:"):
                lines[0] = f"TITLE: {accented_title}\n"
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                return

    # Fallback: Use the map to fix the first line
    if lines[0].startswith("TITLE:"):
        original_title = lines[0].replace("TITLE:", "").strip()
        # If it's already got many accents, maybe don't touch it? 
        # Actually, let's try to fix it anyway if it looks like it needs it.
        fixed_title = fix_title_text(original_title)
        if fixed_title != original_title:
            lines[0] = f"TITLE: {fixed_title}\n"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(lines)

def main():
    root_dir = r"c:\Users\Windows\Documents\MEGA\Audio\Text Mp3"
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".txt"):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
