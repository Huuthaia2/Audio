import os
import re

LOG_FILE = r"d:\z\Audio\_Tool\Audio\DacCoMp3.txt"

def main():
    if not os.path.exists(LOG_FILE):
        print("Log not found.")
        return

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get version from header
    header = content.split('\n')[0]
    print(f"Current Log: {header}")
    
    # Extract TXT names
    txt_names = re.findall(r'TXT: (.*?)\n', content)
    
    # I will compare with a set of names I remember from V5.2 (if I had them)
    # Since I don't have V5.2 log anymore, I'll just analyze V5.3 for "new" types of matches
    
    print(f"\nTop matches in V5.3:")
    for name in txt_names[:20]:
        print(f" - {name}")

if __name__ == "__main__":
    main()
