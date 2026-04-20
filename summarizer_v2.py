import os
import time
import subprocess
import sys

# Tu cau hinh encoding cho terminal Windows
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

# Kiem tra va tu dong cai dat thu vien neu thieu
try:
    import google.generativeai as genai
except ImportError:
    print("--- Dang cai dat thu vien google-generativeai... ---")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "google-generativeai"])
    import google.generativeai as genai

# ================= CAU HINH =================
API_KEY = "AIzaSyD0WBwGovIv-5dVqtyfjjRQmkwrL9V3vpU"

SOURCE_DIRS = [
    r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao",
    r"c:\Users\Windows\Documents\MEGA\Audio\zDaCoMp3"
]
TARGET_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\Tóm tắt"
DELAY_BETWEEN_FILES = 6 # Giay

# Cau hinh AI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-lite') # Quay lai model duoc ho tro

def summarize_story(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(25000)

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
        if response.text:
            return response.text
        else:
            return "Error: AI returned empty response."
    except Exception as e:
        return f"Error AI: {str(e)}"

def main():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    print("--- BAT DAU TIEN TRINH TOM TAT TU DONG (SMART WORKFLOW) ---")
    
    for s_dir in SOURCE_DIRS:
        if not os.path.exists(s_dir):
            print(f"Warning: Source directory not found: {s_dir}")
            continue

        print(f"\nScanning: {s_dir}")
        for root, dirs, files in os.walk(s_dir):
            rel_path = os.path.relpath(root, s_dir)
            target_sub_dir = os.path.join(TARGET_DIR, rel_path)
            
            if rel_path == ".":
                target_sub_dir = TARGET_DIR

            for file in files:
                if file.endswith(".txt"):
                    if file.startswith('.') or file.startswith('_'):
                        continue
                    
                    target_path = os.path.join(target_sub_dir, file)
                    
                    # Bo qua neu da tom tat xong (dung luong > 300 bytes)
                    if os.path.exists(target_path) and os.path.getsize(target_path) > 300:
                        continue
                        
                    if not os.path.exists(target_sub_dir):
                        os.makedirs(target_sub_dir)
                        
                    full_path = os.path.join(root, file)
                    print(f"Processing: [{rel_path}] {file}...", end=" ", flush=True)
                    
                    # Vong lap Retry thong minh
                    max_retries = 100 # So lan thu lai toi da
                    retry_count = 0
                    success = False
                    
                    while retry_count < max_retries and not success:
                        summary = summarize_story(full_path)
                        
                        if "Error AI:" in summary:
                            if "429" in summary or "Quota exceeded" in summary:
                                print(f"\n[!] Rate Limit (429) hit. Dang cho 60 giay de thu lai... (Lan {retry_count+1})", end=" ")
                                time.sleep(60) # Doi 1 phut roi thu lai
                                retry_count += 1
                            else:
                                print(f"FAILED ({summary})")
                                with open(target_path, 'w', encoding='utf-8') as f_err:
                                    f_err.write(summary)
                                break # Loi khac thi break, khong retry
                        else:
                            with open(target_path, 'w', encoding='utf-8') as f_out:
                                f_out.write(summary)
                            print("SUCCESS!")
                            success = True
                            time.sleep(DELAY_BETWEEN_FILES)

    print("\n--- ALL FILES COMPLETED ---")

if __name__ == "__main__":
    main()
