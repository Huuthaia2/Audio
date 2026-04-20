import os
import shutil
import sys
import io

# Fix encoding cho terminal
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SOURCE_DIRS = [
    r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao",
    r"c:\Users\Windows\Documents\MEGA\Audio\zDaCoMp3"
]
TARGET_DIR = r"c:\Users\Windows\Documents\MEGA\Audio\Tóm tắt"

def find_source_rel_path(filename):
    """Tim duong dan tuong doi cua file trong cac thu muc nguon"""
    for s_dir in SOURCE_DIRS:
        for root, _, files in os.walk(s_dir):
            if filename in files:
                return os.path.relpath(root, s_dir)
    return None

def cleanup():
    print("--- DANG DON DEP VA SAP XEP FILE TOM TAT ---")
    
    # 1. Quet tat ca file trong TARGET_DIR (bao gom ca folder con)
    for root, dirs, files in os.walk(TARGET_DIR, topdown=False):
        for file in files:
            if not file.endswith(".txt"):
                continue
                
            file_path = os.path.join(root, file)
            
            # Kiem tra file loi
            is_error = False
            try:
                # Neu file qua nho (duoi 500 bytes) thi kha nang cao la file loi hoac trong
                if os.path.getsize(file_path) < 500:
                    is_error = True
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(1000)
                        error_keywords = ["Error AI:", "Quota exceeded", "quota_metric", "Lỗi xử lý", "models/"]
                        if any(kw in content for kw in error_keywords):
                            is_error = True
            except:
                pass

            if is_error:
                print(f"Deleting error file: {file}")
                os.remove(file_path)
                continue

            # 2. Sap xep file vao dung folder neu no dang nam o root cua Tóm tắt
            if root == TARGET_DIR:
                rel_path = find_source_rel_path(file)
                if rel_path and rel_path != ".":
                    dest_dir = os.path.join(TARGET_DIR, rel_path)
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    
                    dest_path = os.path.join(dest_dir, file)
                    print(f"Moving to category [{rel_path}]: {file}")
                    # Neu file dich da ton tai thi xoa file cu o root
                    if os.path.exists(dest_path):
                        os.remove(file_path)
                    else:
                        shutil.move(file_path, dest_path)

    # Xoa thu muc rong
    for root, dirs, files in os.walk(TARGET_DIR, topdown=False):
        if not dirs and not files and root != TARGET_DIR:
            os.rmdir(root)

    print("--- DA HOAN THANH DON DEP ---")

if __name__ == "__main__":
    cleanup()
