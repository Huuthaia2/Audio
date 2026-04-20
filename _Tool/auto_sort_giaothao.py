import os
import re
import requests
import shutil
import unicodedata
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

def remove_accents(input_str):
    if not input_str: return ""
    # Chuyển Sang NFKD để tách các dấu ra khỏi chữ cái gốc
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    # Lọc bỏ các dấu (combining characters)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D').lower()

# --- CẤU HÌNH ---
BASE_DIR = r"d:\z\Audio\_Tool\Audio\truyencogiaothao"

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
MAX_WORKERS = 15 # Tăng tốc độ xử lý hàng loạt

# Bảng Mapping (Ưu tiên số nhỏ trước)
CATEGORY_MAP = [
    (1, ["mẹ con", "mẹ kế", "mẹ nuôi", "mẹ và con", "bú cặc con trai", "bú lồn mẹ", "bú vú me", "con bú vú mẹ", "con chồng", "con riêng", "con trai", "con đụ mẹ", "móc lồn mẹ", "mẹ bú cu con", "mẹ con", "mẹ con khẩu dâm", "mẹ con đảo hoang", "mẹ con ở chung", "mẹ dâm", "mẹ kế", "mẹ đụ con", "địt lén mẹ ruột", "đụ mẹ", "đụ mẹ kế", "đụ mẹ ruột"]),
    (2, ["cha chồng - con dâu", "cha chồng", "con dâu", "bố chồng", "nàng dâu", "ba chồng", "bố chồng con dâu", "bố chồng nàng dâu", "bố chồng đụ con dâu", "con dâu nhật bản"]),
    (3, ["cave", "gái gọi", "phò", "chơi gái", "gái bán hoa", "gái massage", "trai gọi"]),
    # (4, ["he", "happy ending", "ngôn tình"]),
    (5, ["chi dâu", "chị dâu", "anh rể", "em dâu", "anh rể bóp vú em vợ", "bú cặc anh rể", "đụ em dâu"]),
    (6, ["anh em - chị em", "anh em", "chị em", "em gái", "anh trai", "em ruột", "anh em đụ nhau", "chị em loạn luân", "chị gái", "em gái mưa", "em nuôi", "đụ chị bạn"]),
    (7, ["hàng xóm", "vợ hàng xóm", "cạnh nhà", "đụ hàng xóm"]),
    (8, ["loạn luân", "loan luan", "huyết thống", "gia đình loạn", "anh trai bóp vú em gái", "bố con", "cha con", "cha con gái", "cha dượng", "cha ruột đụ con gái", "cha đụ con gái", "cháu thím", "cháu địt cô", "chú cháu", "con gái", "dượng cháu", "gia đình", "l luân", "loạn giao", "loạn luân cha và con gái", "đụ bà", "đụ cháu gái"]),
    (9, ["mẹ bạn", "me ban"]),
    (10, ["mẹ vợ", "con rể", "me vo"]),
    (11, ["6 múi", "sáu múi"]),
    (12, ["máy bay", "phi công", "milf", "u40", "u50", "bà chủ - ô sin", "dì cháu", "địt bà chủ", "đụ bà chủ", "đụ máy bay", "đụ thím", "đụ trai trẻ", "gái 1 con", "gái một con", "máy bay dâm", "máy bay móc lồn", "máy bay rên rỉ", "mbbg", "mẹ chồng", "ông chủ", "ông già", "phụ nữ có chồng", "single mom", "thiếu phụ", "thím dâu", "trâu già gặm cỏ non"]),
    (13, ["cô giáo - học sinh", "cô giáo", "học sinh", "gia sư", "thầy giáo", "mái trường", "học đường", "bú lồn cô giáo", "cô giáo khẩu dâm", "du học sinh", "học sinh đụ cô giáo", "học trò", "nữ gia sư", "thầy đụ học sinh", "trò chơi", "vụng trộm với cô giáo"]),
    (14, ["ngoại tình", "cắm sừng", "ntr", "cuckold", "vợ ngoại tình", "3p", "4p", "chơi some", "hoang lạc", "hưởng lạc", "khẩu dâm tập thể", "np", "npc", "some", "some 3", "some vợ bạn", "swap", "threesome", "thác loạn", "truyện sex ngoại tình", "tập thể", "tập thể (3p-4p)", "tập thể đụ", "vụng trộm", "địt bạn cùng phòng người yêu", "đổi người yêu", "đụ bạn của người yêu", "đụ người yêu của bạn", "đụ some"]),
    (15, ["y tá - bác sĩ", "y tá", "bác sĩ", "bệnh viện", "phụ khoa", "bác sĩ đụ"]),
    (16, ["bạo dâm", "slave", "hiếp dâm", "cưỡng hiếp", "bdsm", "bồn chứa", "no lệ", "cưỡng dâm", "ác mộng", "cưỡng", "sát", "bdms", "biến thái", "bạo hành", "bạo lực", "bồn chưa", "bồn chứa tinh", "chuốc thuốc", "cường thủ hào đoạt", "cấm kỵ", "huấn luyện", "hành hạ", "khế ước tình nhân", "khổ dâm", "loli", "lét lút", "mạnh bạo", "nam cặn bã", "nô lệ", "nô lệ tình dục", "nữ trơ trẽn", "phô dâm", "rình lén", "sa đọa", "salve dog", "sex bts", "sm mạnh", "sát thủ", "sỉ nhục", "thôi miên", "truyện 18 bts", "truyện nặng đô", "tà giao", "tét mông", "vụng tộm", "đánh roi", "đấm đá", "đụ mạnh"]),
    (17, ["vợ dâm", "gái dâm", "gái xinh", "vợ bạn", "vợ đảm", "kiều nữ", "khỏa thân", "tân hôn", "bú lồn gái dâm", "bố vợ", "cuồng dâm", "công chúa thủ dâm", "dâm dục", "dâm hiệp", "dâm loạn", "dâm nữ", "dâm thư", "dâm thư trung quốc", "dâm thủy", "dâm đãng", "em chồng", "em vợ", "gái có chồng", "gái dâm thủ dâm", "gái thủ dâm", "gái đỉ dâm", "hàng xom dâm", "khẩu dâm liên tục", "khẩu dâm mạnh", "khẩu dâm mạnh bao", "khẩu dâm rên rỉ", "les dâm", "lồn dâm", "lồn thâm", "móc lồn dâm", "quý bà dâm", "sắc dâm", "thủ dâm", "thủ dâm nữ", "thủ dâm trên xe", "truyện dâm", "tự thủ dâm nữ", "vú to", "vợ bị người khác đụ", "vợ bị đụ", "vợ chú", "vợ chồng", "vợ dâm bị đụ", "vợ đụ trai", "đụ gái dâm", "đụ khẩu dâm", "đụ vợ chú"]),
    (18, ["chuyện cũ", "quá khứ", "hồi ức", "kỷ niệm", "chuyện tình", "chuyện"]),
    (19, ["ghen tuông"]),
    (20, ["dâm thư trung quốc", "trung quốc", "dâm thư", "china", "truyện trung", "truyện trung quốc", "truyện trung quốc 18+", "truyện trung quốc dịch", "côn lôn quật", "dâm thư hán việt", "hán việt", "quý tộc", "sắc hiệp", "trung đại"]),
    (21, ["truyện trung", "truyện dịch", "tổng tài"]),
    (22, ["truyện dâm hiệp", "dâm hiệp", "tiên hiệp", "huyền huyễn", "tu tiên"]),
    (23, ["kỹ năng & hành động", "kỹ năng", "hành động", "doggy", "vét máng", "bú cu", "thế xác", "mày mò", "làm tình", "húp sò", "chịch", "đụ", "6 múi đụ", "anal", "anal sex", "bánh mì kẹp xúc xích", "bóp vú", "bú cu sữa chua", "bú cặc", "bú cặc chó", "bú lồn", "bú lồn non", "bú vú", "bạn gái bị đụ", "bắn tinh", "bắn tinh lên mặt", "bắn tinh lên ngực", "bắn trong", "bị đụ", "chat sex", "cho chó liếm lồn", "chó liếm lồn", "chơi 69", "chơi trần", "chơi đỉ", "chảy nước lồn", "cukcold", "có bầu", "có thai", "cô dâu đụ", "cặc to", "cặc tây", "dirtytalk", "dp", "futa", "gay sex", "gymer", "gái có cu", "gái dùng tay sục cặc cho nam", "gái nứng", "gái nứng lồn", "gái vú to", "găm bi", "hj", "hôn vú", "hậu cung", "không mặc quần lót khi ra đường", "khẩu dâm", "kích dục", "liếm cặc", "liếm tinh trùng", "liềm lồn", "làm tình buổi sớm", "làm tình nhẹ nhàng", "làm tình tay ba", "làm tình với đồng nghiệp", "lên đỉnh", "lưỡng tính", "lồn múp", "lồn rộng", "lỗ đít", "mang thai", "masage", "mò vú", "móc lồn", "mơn trớn", "nhậu xong đụ", "nút lưỡi", "nước bọt", "nước lồn", "nứng lồn", "phá trinh", "phá trinh lỗ đít", "phô dâm", "phô tả", "quần lót lọt khe", "ra khí", "rên la", "rên rỉ", "rên rỉ đụ", "se đầu ti", "sex", "sex hay", "sextoy", "sexy", "sinh viên đụ gái", "some", "squirt", "sung sướng", "sóc lọ", "sờ lồn loli", "sục cu", "sục cặc", "thuốc kích dục", "thác loạn tập thể", "thông đít", "thọc tay vô đít", "truyện bóp vú", "truyện bú cặc", "truyện bú lồn", "truyện bú vú", "truyện day lồn", "truyện liếm chân", "truyện liếm cặc", "truyện liếm lồn", "truyện liếm đít", "truyện móc lồn", "truyện mút chân", "truyện mút lồn", "truyện nuốt tinh trùng", "truyện sex phá trinh", "truyện swing", "truyện sờ lồn", "trứng rung", "uống nước đái", "vua chúa đụ", "vú có sữa", "vú khủng", "vú đẹp", "vừa gọi điện vừa làm tình", "vừa tình vừa khẩu dâm", "xuất tinh sớm", "xuất tinh trong", "xuất tinh vào lồn", "xuất trong", "xuất vào lồn", "xả đồ", "đâm sâu", "đĩ đực", "địt bạn học", "địt gái bầu", "địt mạnh", "đụ a kha", "đụ bạn gái", "đụ bạn thân", "đụ chi", "đụ chó", "đụ cô long", "đụ công khai", "đụ dì", "đụ gái", "đụ gái chửa", "đụ gái cổ trang", "đụ khi đi công tác", "đụ kiểu doggy", "đụ lén", "đụ lỗ đít", "đụ massage", "đụ mạn", "đụ mạnh bạo", "đụ ngựa", "đụ nhân viên", "đụ nát lồn", "đụ public", "đụ quý phi", "đụ song nhi", "đụ trâu", "đụ trên xe", "đụ trên đảo", "đụ tập thể", "đụ vú", "đụ wonder woman", "đụ đít", "đụ ở quán cà phe"]),
    (24, ["địa điểm & đối tượng", "sinh viên", "nhân viên", "địa điểm", "công sở", "thư ký", "văn phòng", "giám đốc", "xóm trọ", "khách sạn", "xe bus", "tàu", "máy bay", "nhà trọ", "tour", "banker", "bạn cùng giường", "chuyện tình nơi công sở", "chó cái", "chăn rau", "chức nghiệp tinh anh", "coi phim sex", "cosplay", "cứu nét", "em ngọc dâm đãng", "gen z", "giảng viên", "gái cơ quan", "gái non", "gái non tơ", "gái quê", "hiệp dâm nữ sinh", "hào môn thế gia", "làm tình nơi công cộng", "lão già bẩn bựa", "massage", "nam sinh", "nhân viên công sở", "nữ cảnh sát", "nữ giám đốc", "nữ sinh", "nữ vận động viên", "nữ đế", "public", "quý bà", "raper", "sex học đường", "sex ni cô", "sex public", "sex trong rạp chiếu phim", "sex với người đưa thư", "sgbb", "sgdd", "sugar baby", "sugar daddy", "thái giám", "thị giác nữ chủ", "tiểu tam", "tra nam", "trai đảm đang", "truyen sex 9x", "truyện người lớn", "truyện sex diễn viên", "truyện sex người lớn", "truyện sex sinh viên", "tên trộm", "tổng tài", "vườn trường", "xem phim sex", "đàn bà", "địt tiếp viên karaoke", "đồng nghiệp", "đụ giúp việc", "đụ khách hàng", "đụ thư ký", "đụ trong toilet", "đụ trên tàu", "đụ ở công viên", "đụ ở sân thượng", "ảnh hậu", "ở đợ"]),
    (25, ["dị thường & thế giới khác", "dị thường", "thế giới khác", "harem", "phiêu lưu", "lesbian", "thu vật", "xuyên không", "mario", "ngọc rồng", "doremon", "bạch tuyết", "sơn tinh", "truyện cổ tích", "emmanuelle", "toy", "con giáp", "loli", "tấm", "bùa chú", "châu âu", "chúc anh đài", "công chúa", "công chúa ngủ trong rừng sex", "công chúa sex", "cưỡi ngựa", "cổ trang", "cổ tích", "cổ tích 1+", "cổ tích sex", "doãn chí bình", "dương khang", "goblin", "gái cổ trang", "gái mới nhú", "hoang đảo", "hoàng dung", "hoàng hậu", "hoàng tử", "huyền huyễn", "hắc bang", "hệ thông", "khoa học viễn tưởng", "linh dị", "làm tình với chó", "lương sơn bá", "mai siêu phong", "mục niệm từ", "người chuyển giới", "người và thú (sex thú)", "phan kim liên", "pháp sư", "quách tình", "quái vật", "sex thú", "siêu nhiên", "siêu năng lực", "thú giao", "thực tế ảo", "tiên tử", "trung đại", "truyện cổ trang", "truyện les", "truyện loli", "truyện tiên hiệp", "truyện xuyên không", "tâm linh", "tôn giáo", "tương lai", "tận thế", "vi tiểu bảo", "viễn tưởng", "võ tong", "võng du", "wonder woman sex", "xúc tu", "đu nhau family", "địt nhau with ngựa", "đụ kiểu chó"]),
    (26, ["phong cách & cảm xúc", "phong cách", "cảm xúc", "slice of life", "thiếu niên", "người tình", "tình đơn phương", "mảnh ghép", "sắc màu", "ngày đầu", "mùa hạ", "gác", "góc khuất", "ra đời", "đàn bà", "18+", "18+ nhẹ", "19+", "1v1", "2 nam 1 nữ", "bỏ nhà đi bụi", "cao h", "caoh", "comic", "cái chai em cầm", "có thật", "cẩu huyết", "cận thuỷ lâu dài", "cổ đại", "cực khoái", "duyên trời tác hợp", "dụ nhau", "ghen tuông", "gái trinh", "h tục", "h văn", "h+", "he", "hiện đại", "hoàn thành", "htuc", "hài hước", "hư cấu", "hải tặc 18+", "hằng ngày", "hệ thống 18+", "hồi xuân", "không tam quan", "kinh dị", "kinh dị cơ thể", "kinh nghiệm làm tình", "kích thích", "lãng du 2772", "lãng mạn", "lôi", "lọ lem 18+", "nguyên bản", "nguyên san", "nguyên tác", "ngôn tình", "người đẹp quái vật 18+", "ngọt", "ngọt sủng", "nhật ký mây mưa", "nhẹ nhàng", "niên thượng", "nữ cường", "nữ sa đọa", "nữ sạch", "nữ viết", "nữ viết truyện", "phản anh hùng", "pt", "seri", "siêu anh hùng 18+", "song tình", "sp", "sảy thai", "sắc", "sắc 18+", "sắc hiệp", "sắc hiệp viện", "sắc hoàn", "sắc nặng", "sủng", "thi muội 1", "thi muội 2", "thi muội 3", "thi muội 4", "thô tục", "thần điêu 18+", "trinh thám", "truyện 18+", "truyện 21+", "truyện dịch", "truyện femdom", "truyện hàn", "truyện ma 18+", "truyện ngắn", "truyện ntr", "truyện nữ kể", "truyện sex . xxx", "truyện sex cuckold", "truyện sex có hình ảnh", "truyện sex có thật", "truyện sex cắm sừng", "truyện sex gangbang", "truyện sex hay", "truyện sex khổ dâm", "truyện sex kinh dị", "truyện sex lén lút", "truyện sex nhẹ nhàng", "truyện sex nặng", "truyện sex tình cảm", "truyện sex tưởng tưởng", "truyện sex ông già", "truyện sex đồng tính luyến ái", "truyện sắc", "truyện sắc hiệp", "truyện teen", "truyện tưởng tượng", "truyện đô thị", "tu tiên đô thị", "tâm lý", "tâm sự bạn đọc", "tình cảm", "tình dục", "tình một đêm", "tình văn", "tưởng tượng", "tấm cám 18+", "từ ngữ thô tục", "tự kể", "áo dài", "đô thị", "đô thị tình duyên", "đụ người yêu cũ", "ảnh nude"])
]

def get_folder_by_id(folder_id):
    for folder_name in os.listdir(BASE_DIR):
        if folder_name.startswith(f"{folder_id}-"):
            return folder_name
    return None

def get_tags_from_web(url, slug):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Lấy tag từ .genres-content
        tags = [a.get_text().lower().strip() for a in soup.select('.genres-content a')]
        # Lấy tag từ .post-content_item (Category)
        cats = [a.get_text().lower().strip() for a in soup.select('.post-content_item a')]
        # Lấy title
        titles = [h1.get_text().lower().strip() for h1 in soup.select('h1')]
        
        return list(set(tags + cats + titles))
    except:
        return []

def extract_url_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_lines = "".join([f.readline() for _ in range(10)])
            match = re.search(r'https://truyencogiaothao\.site/truyen/[a-zA-Z0-9-]+/', first_lines)
            if match:
                return match.group(0)
    except:
        pass
    return None

def process_file_with_path(file_name, file_dir):
    file_path = os.path.join(file_dir, file_name)
    slug = file_name.rsplit('-', 1)[0]
    
    url = extract_url_from_file(file_path)
    if not url:
        url = f"https://truyencogiaothao.site/truyen/{slug}/"
    
    all_tags = get_tags_from_web(url, slug)
    
    # Check mapping
    target_id = None
    for fid, keywords in CATEGORY_MAP:
        # Kiểm tra qua Tags từ web
        for tag in all_tags:
            if any(kw in tag for kw in keywords):
                target_id = fid
                break
        if target_id: break
        
        # Nếu không thấy tag, kiểm tra qua Slug
        if any(kw in slug.replace('-', ' ') for kw in keywords):
            target_id = fid
            break
            
    if target_id:
        target_folder_name = get_folder_by_id(target_id)
        if target_folder_name:
            dst_dir = os.path.join(BASE_DIR, target_folder_name)
            dst_path = os.path.join(dst_dir, file_name)
            
            # Chỉ xử lý nếu thư mục đích khác thư mục hiện tại
            if os.path.normpath(file_path) == os.path.normpath(dst_path):
                return f"[*] {file_name} already in {target_folder_name}"

            try:
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                shutil.move(file_path, dst_dir)
                return f"[OK] {file_name} -> {target_folder_name}"
            except Exception as e: return f"[ERR] {file_name} move error: {e}"

    return f"[-] {file_name} no match"

def main():
    # Quét đệ quy toàn bộ thư mục gốc, trừ zzzzLoi
    files_to_process = []
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Loại bỏ zzzzLoi khỏi danh sách duyệt
        if "zzzzLoi" in root:
            continue
            
        for f in files:
            if f.lower().endswith(".txt") and f != "truyencogiaothao.txt":
                files_to_process.append((f, root))

    if not files_to_process: return print("No files to sort.")

    print(f"[*] Sorting {len(files_to_process)} files with {MAX_WORKERS} workers...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_file = {executor.submit(process_file_with_path, f_name, f_dir): f_name for f_name, f_dir in files_to_process}
        count = 0
        for future in as_completed(future_to_file):
            count += 1
            res = future.result()
            print(f"  Progress: {count}/{len(files_to_process)}")
            print(f"      {res}")

    print("\n[DONE] Finished!")

if __name__ == "__main__":
    main()
