import google.generativeai as genai
import os
import sys

# Đảm bảo console hiển thị được tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CẤU HÌNH ---
API_KEY = "AIzaSyCJWY4EXp--S2HU26wm590pOB4xxSSYDOc"
genai.configure(api_key=API_KEY)

def test_api():
    print("[*] Đang kết nối với Gemini API...")
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Gửi yêu cầu tóm tắt thử nghiệm
        response = model.generate_content("Tóm tắt ngắn gọn lợi ích của việc dùng AI trong lập trình game puzzle.")
        
        content = response.text
        print("[OK] API hoạt động tốt!")
        print(f"Phản hồi: {content}")
        
        # Lưu nhanh vào file txt bằng quyền Always Allow đã cấp
        with open("test_gemini_result.txt", "w", encoding="utf-8") as f:
            f.write("Kết quả Test API Gemini:\n")
            f.write(content)
        print("[+] Kết quả đã được lưu vào file test_gemini_result.txt")
        
    except Exception as e:
        print(f"[!] Lỗi: API Key có vấn đề hoặc kết nối mạng bị chặn. Chi tiết: {e}")

if __name__ == "__main__":
    test_api()