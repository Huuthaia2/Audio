from google import genai
import sys

# Đảm bảo console hiển thị được tiếng Việt
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "AIzaSyCJWY4EXp--S2HU26wm590pOB4xxSSYDOc"
client = genai.Client(api_key=API_KEY)

print("[*] Đang kết nối với Gemini API (New SDK)...")
try:
    response = client.models.generate_content(
        model='gemini-1.5-flash', 
        contents='Tóm tắt ngắn gọn lợi ích của việc dùng AI trong lập trình game puzzle.'
    )
    print("[OK] API hoạt động tốt!")
    print(f"Phản hồi: {response.text}")
except Exception as e:
    print(f"[!] Lỗi: {e}")
