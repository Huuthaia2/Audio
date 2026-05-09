import os, json, re, unicodedata

BASE_DIR = r"c:\Users\Windows\Documents\MEGA\Audio"
uid = "Text Mp3/M3/me-con-nha-thang-hieu.txt"
query = "Chuyển qua mục video tôi vuốt lên trên cùng để xem video đầu tiên"

def remove_accents(input_str):
    if not input_str: return ""
    s1 = unicodedata.normalize('NFD', input_str)
    s1 = ''.join([c for c in s1 if unicodedata.category(c) != 'Mn'])
    return s1.replace('đ', 'd').replace('Đ', 'D')

path = os.path.join(BASE_DIR, uid)
print(f"Checking path: {path}")
print(f"Exists: {os.path.exists(path)}")

if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    print(f"Content length: {len(content)}")
    
    q_low = query.lower()
    c_low = content.lower()
    
    print(f"Query low in Content low: {q_low in c_low}")
    
    q_clean = remove_accents(query).lower()
    c_clean = remove_accents(content).lower()
    
    print(f"Query clean: {q_clean}")
    print(f"Match clean: {q_clean in c_clean}")
    
    # Try normalization
    q_nfc = unicodedata.normalize('NFC', query).lower()
    c_nfc = unicodedata.normalize('NFC', content).lower()
    print(f"Match NFC: {q_nfc in c_nfc}")
