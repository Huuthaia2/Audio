import os
import re

# Regex patterns for cleaning
AD_PATTERN = re.compile(
    r"Website chuyển qua tên miền mới là:\s*.*?\s*,\s*các bạn nhớ tên miền mới để tiện truy cập nhé!",
    re.IGNORECASE | re.DOTALL
)

# Pattern for source info and title extraction
# Handles both multi-line and single-line variants, with optional leading '…'
SOURCE_PATTERN = re.compile(
    r"(?:…\s*)?Bạn đang đọc truyện\s+(.*?)\s+tại nguồn:\s+https?://\S+",
    re.IGNORECASE | re.DOTALL
)

# Pattern for "Bạn đang đọc Chương X..." blocks
CHAPTER_LINK_PATTERN = re.compile(
    r"Bạn đang đọc Chương \d+.*?tại đây:\s*https?://\S+",
    re.IGNORECASE | re.DOTALL
)

# A simple dictionary to help with accenting titles from slugs if not found in text
ACCENT_MAP = {
    "ve": "Về", "que": "Quê", "vo": "Vợ", "ba": "Bà", "di": "Dì", "tuoi": "Tuổi", "at": "Ất", "mui": "Mùi",
    "cave": "Cave", "an": "Ấn", "do": "Độ", "co": "Cô", "em": "Em", "nuoi": "Nuôi", "ac": "Ác", "gia": "Giả",
    "bao": "Báo", "am": "Ám", "anh": "Ảnh", "loan": "Loạn", "luan": "Luân", "hang": "Hàng", "xom": "Xóm",
    "ho": "Họ", "viet": "Việt", "kieu": "Kiều", "re": "Rể", "oi": "Ơi", "ngua": "Ngứa", "lung": "Lưng",
    "trai": "Trai", "chuyen": "Chuyện", "that": "Thật", "cuoc": "Cuộc", "doi": "Đời", "toi": "Tôi",
    "chi": "Chị", "hung": "Hừng", "tinh": "Tình", "de": "Đẻ", "tho": "Thơ", "lam": "Làm", "gi": "Gì",
    "con": "Con", "ngoai": "Ngoại", "ten": "Tên", "trom": "Trộm", "may": "May", "man": "Mắn", "hieu": "Hiếu",
    "be": "Bé", "han": "Hận", "them": "Thèm", "du": "Đụ", "nhi": "Nhí", "hai": "Hai", "best": "Best",
    "dam": "Dâm", "he": "Hệ", "thong": "Thống", "bi": "Bị", "cua": "Của", "ban": "Bạn", "cuong": "Cuồng",
    "cha": "Cha", "duong": "Dượng", "boc": "Bóc", "zin": "Zin", "mat": "Mật", "gia": "Gia", "dinh": "Đình",
    "ruot": "Ruột", "nuoc": "Nước", "mat": "Mắt", "mua": "Mùa", "thu": "Thu", "o": "Ở", "nha": "Nhà",
    "voi": "Với", "nho": "Nhờ", "re": "Rể", "pha": "Phá", "trinh": "Trinh", "ca": "Cả", "lan": "Lẫn",
    "dung": "Dung", "linh": "Linh", "hoakhoi": "Hoa Khôi", "cong": "Công", "ty": "Ty", "nhu": "Như", "y": "Ý",
    "quan": "Quan", "he": "Hệ", "len": "Lén", "lut": "Lút", "tro": "Trọ", "hanh": "Hạnh", "phuc": "Phúc",
    "quynh": "Quỳnh", "ranh": "Ranh", "gioi": "Giới", "cam": "Cấm", "ky": "Kỵ", "sang": "Sáng", "chieu": "Chiều",
    "an": "Ăn", "sm": "SM", "song": "Sóng", "gio": "Gió", "toc": "Tộc", "su": "Sự", "thong": "Thông",
    "dong": "Đồng", "tam": "Tâm", "su": "Sự", "tan": "Tàn", "tro": "Trò", "doi": "Đời", "thang": "Thằng",
    "cu": "Cu", "nho": "Nhỏ", "ti": "Tí", "the": "Thế", "duc": "Dục", "thi": "Thị", "tran": "Trấn",
    "thim": "Thím", "gui": "Gửi", "ma": "Má", "dau": "Dâu", "truyen": "Truyện", "buon": "Buồn", "nguyen": "Nguyên",
    "tu": "Tự", "ve": "Về", "lan": "Lan", "vet": "Vết", "nho": "Nhơ", "loi": "Lỗi", "dung": "Đừng", "di": "Đi",
    "vung": "Vùng", "que": "Quê", "heo": "Hẻo", "lanh": "Lánh", "yen": "Yên", "binh": "Bình", "trom": "Trộm",
    "vuot": "Vượt", "qua": "Qua", "xem": "Xem", "yeu": "Yêu", "bac": "Bác", "mo": "Mợ", "nguoi": "Người",
    "vong": "Vọng", "chu": "Chú", "lao": "Lão", "hac": "Hạc", "chay": "Chảy", "cam": "Cảm", "xuc": "Xúc",
}

def accent_slug(slug):
    words = slug.replace('-full', '').replace('.txt', '').split('-')
    accented_words = [ACCENT_MAP.get(w.lower(), w.capitalize()) for w in words]
    return " ".join(accented_words)

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    # 1. Extract title from SOURCE_PATTERN before removing it
    title = None
    match = SOURCE_PATTERN.search(content)
    if match:
        title = match.group(1).strip()
        # Basic sanity check for title length
        if len(title) > 100 or len(title) < 2:
            title = None
    
    # 2. Remove patterns
    content = AD_PATTERN.sub("", content)
    content = SOURCE_PATTERN.sub("", content)
    content = CHAPTER_LINK_PATTERN.sub("", content)
    
    # 3. Clean up leading/trailing whitespace and multiple newlines
    content = content.strip()
    
    # 4. If title not found in content, use accented slug
    if not title:
        title = accent_slug(os.path.basename(filepath))
    
    # 5. Format title and prepend or update existing
    if content.startswith("TITLE:"):
        # If we found a title in the body, let's use it to update the existing TITLE line
        if title:
            # Replace the first line with the new title
            lines = content.split('\n', 1)
            final_content = f"TITLE: {title}\n" + (lines[1] if len(lines) > 1 else "")
        else:
            final_content = content
    else:
        final_content = f"TITLE: {title}\n\n{content}"
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(final_content)
    except Exception as e:
        print(f"Error writing {filepath}: {e}")

def main():
    root_dir = r"c:\Users\Windows\Documents\MEGA\Audio\Text Mp3"
    count = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".txt"):
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
