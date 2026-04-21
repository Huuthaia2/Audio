import os
import time
import sys
import google.generativeai as genai

# Đảm bảo console hiển thị được tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# ================= CẤU HÌNH =================
# BẠN CẦN ĐIỀN API KEY CỦA BẠN VÀO ĐÂY
API_KEY = "AIzaSyD0WBwGovIv-5dVqtyfjjRQmkwrL9V3vpU"

SOURCE_DIRS = [
    r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao\8-Loạn Luân"
]
TARGET_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\Tóm tắt\8-Loạn Luân"
DELAY_BETWEEN_FILES = 5  # Nghỉ 5 giây để tránh bị giới hạn API miễn phí

# Khởi tạo AI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def summarize_story(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(20000)

        prompt = f"""
        Bạn là trợ lý tóm tắt truyện chuyên nghiệp. Hãy đọc nội dung truyện và tóm tắt theo định dạng CHÍNH XÁC như sau:

        ==================================================
        TÓM TẮT TRUYỆN: [TÊN TRUYỆN VIẾT HOA]
        File gốc: {os.path.basename(file_path)}
        Thể loại: [Các thể loại cách nhau bằng dấu phẩy]
        Nhân vật chính: [Tên nhân vật và mô tả ngắn]
        ==================================================

        🔹 Phần 1: [Tiêu đề phần 1]
        (Chương [X])
        Nội dung: [Nội dung tóm tắt chi tiết của phần 1]

        🔹 Phần 2: [Tiêu đề phần 2]
        (Chương [X]-[Y])
        Nội dung: [Nội dung tóm tắt chi tiết của phần 2]

        🔹 Phần 3: [Tiêu đề phần 3]
        (Chương [X]-[Y])
        Nội dung: [Nội dung tóm tắt chi tiết của phần 3]

        🔹 Phần 4: [Tiêu đề phần 4]
        (Chương [X]-[Y])
        Nội dung: [Nội dung tóm tắt chi tiết của phần 4]

        🔹 Phần 5: [Tiêu đề phần 5]
        (Chương [X]-[Y])
        Nội dung: [Nội dung tóm tắt chi tiết của phần 5]

        🔹 Phần 6: [Tiêu đề phần 6]
        (Chương [X]-[Y])
        Nội dung: [Nội dung tóm tắt chi tiết của phần 6]

        ---
        Hết.

        NỘI DUNG TRUYỆN:
        {content}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi xử lý file: {str(e)}"

def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    for s_dir in SOURCE_DIRS:
        print(f"--- Đang quét thư mục: {s_dir} ---")
        for root, _, files in os.walk(s_dir):
            rel_path = os.path.relpath(root, s_dir)
            target_sub_dir = os.path.join(TARGET_DIR, rel_path)
            
            if rel_path == ".":
                target_sub_dir = TARGET_DIR
            
            if not os.path.exists(target_sub_dir):
                os.makedirs(target_sub_dir)

            for file in files:
                if file.endswith(".txt"):
                    target_path = os.path.join(target_sub_dir, file)
                    
                    # Bỏ qua nếu đã tóm tắt xong (dung lượng > 300 bytes)
                    if os.path.exists(target_path) and os.path.getsize(target_path) > 300:
                        continue
                    
                    full_path = os.path.join(root, file)
                    print(f"--- Đang tóm tắt: {file} ---")
                    
                    summary = summarize_story(full_path)
                    
                    # Lưu file tóm tắt
                    with open(target_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(summary)
                    
                    print(f"Hoàn thành: {file}")
                    time.sleep(DELAY_BETWEEN_FILES)

if __name__ == "__main__":
    main()
