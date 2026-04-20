import os
import time
import google.generativeai as genai

# ================= CẤU HÌNH =================
# BẠN CẦN ĐIỀN API KEY CỦA BẠN VÀO ĐÂY
API_KEY = "AIzaSyD0WBwGovIv-5dVqtyfjjRQmkwrL9V3vpU"

SOURCE_DIRS = [
    r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao",
    r"c:\Users\Windows\Documents\MEGA\Audio\zDaCoMp3"
]
TARGET_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\Tóm tắt"
DELAY_BETWEEN_FILES = 5  # Nghỉ 5 giây để tránh bị giới hạn API miễn phí

# Khởi tạo AI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def summarize_story(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(20000)

        prompt = f"""
        Bạn là trợ lý tóm tắt truyện chuyên nghiệp. Hãy đọc nội dung truyện và tóm tắt theo định dạng CHÍNH XÁC như sau:

        ==================================================
        TÓM TẮT TRUYỆN: [Tên Truyện Viết Hoa]
        File gốc: {os.path.basename(file_path)}
        Thể loại: [Thể loại truyện]
        Nhân vật chính: [Tên và mô tả ngắn]
        ==================================================

        🔹 Phần 1: [Tiêu đề phần]
        (Chương X-Y)
        Nội dung: [Tóm tắt chi tiết diễn biến từ 3-5 câu]

        (Tiếp tục thêm các phần khác nếu truyện dài)

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

    # Lấy danh sách các file đã tóm tắt để tránh làm lại
    processed_files = set(os.listdir(TARGET_DIR))

    for s_dir in SOURCE_DIRS:
        print(f"--- Đang quét thư mục: {s_dir} ---")
        for root, _, files in os.walk(s_dir):
            for file in files:
                if file.endswith(".txt") and file not in processed_files:
                    full_path = os.path.join(root, file)
                    print(f"--- Đang tóm tắt: {file} ---")
                    
                    summary = summarize_story(full_path)
                    
                    # Lưu file tóm tắt
                    target_path = os.path.join(TARGET_DIR, file)
                    with open(target_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(summary)
                    
                    print(f"Hoàn thành: {file}")
                    time.sleep(DELAY_BETWEEN_FILES)

if __name__ == "__main__":
    main()
