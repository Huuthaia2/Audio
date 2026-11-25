import os
import re

# --- CẤU HÌNH ---
TARGET_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao\zzzzLoi"
ERROR_KEYWORDS = ["loading", "retry", "ajax", "error", "chưa có nội dung", "đang cập nhật", "not found"]
MIN_LENGTH = 300 

def check_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex CHỈ BẮT tiêu đề chương thực thụ (có từ khóa)
        # Bắt: ==================== Chương/Phần/Tiết... ====================
        pattern = r'(==================== (?:Chương|Phần|Tiết|Tập|Episode|Quyển).*? ====================)'
        parts = re.split(pattern, content)
        
        if len(parts) < 2:
            return f"{os.path.basename(file_path)}: Skipped (No real chapter markers found)."

        header = parts[0]
        chapter_data = parts[1:] 
        
        error_chapters = []
        
        for i in range(0, len(chapter_data), 2):
            title_line = chapter_data[i]
            body = chapter_data[i+1] if i+1 < len(chapter_data) else ""
            
            clean_body = body.strip()
            is_error = False
            
            # Kiểm lỗi
            if len(clean_body) < MIN_LENGTH:
                is_error = True
            else:
                lower_body = clean_body.lower()
                if any(kw in lower_body for kw in ERROR_KEYWORDS):
                    is_error = True
            
            if is_error:
                label = title_line.strip('= ')
                error_chapters.append(label)

        # Xóa các Note lỗi cũ trước khi ghi note mới
        content = re.sub(r'\n\{Lỗi tải chương: .*?\}\n', '', content)

        if error_chapters:
            error_note = f"\n{{Lỗi tải chương: {', '.join(error_chapters)}}}\n"
            
            new_content = ""
            title_match = re.search(r'(TITLE: .*?\n=+\n)', content)
            if title_match:
                pos = title_match.end()
                new_content = content[:pos] + error_note + content[pos:]
            else:
                new_content = error_note + content

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return f"{os.path.basename(file_path)}: FOUND {len(error_chapters)} real errors."
        else:
            # Nếu sạch lỗi, ghi đè lại file gốc đã xóa note cũ
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"{os.path.basename(file_path)}: CLEAN (False alarms removed)."

    except Exception as e:
        return f"ERROR on {os.path.basename(file_path)}: {str(e)}"

def main():
    files = [f for f in os.listdir(TARGET_DIR) if f.startswith("_") and f.endswith(".txt")]
    print(f"[*] Analyzing {len(files)} files in zzzzLoi (v2.1 Precision Mode)...")
    
    for f_name in files:
        result = check_file(os.path.join(TARGET_DIR, f_name))
        print(f"  > {result}")

if __name__ == "__main__":
    main()
