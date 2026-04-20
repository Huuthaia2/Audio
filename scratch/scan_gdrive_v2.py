import requests
import re
import json

url = 'https://drive.google.com/drive/folders/1W1867yxPZdNmiV1sEaXzyHnaQXsHmFdu?usp=sharing'
res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
content = res.text

# Extract MP3 filenames from various possible locations in GDrive HTML
mp3s = []

# Pattern 1: AF_initDataCallback
blocks = re.findall(r'AF_initDataCallback\(\{.*?data:(.*?)\}\);', content, re.DOTALL)
for block in blocks:
    try:
        # Some blocks might not be valid JSON directly if they contain unquoted keys or single quotes
        # but let's try the simple findall inside the block first
        found = re.findall(r'\"([^\"]+\.mp3)\"', block)
        mp3s.extend(found)
    except:
        continue

# Pattern 2: Global search in HTML
found_global = re.findall(r'\"([^\"]+\.mp3)\"', content)
mp3s.extend(found_global)

unique_mp3s = sorted(list(set(mp3s)))

if unique_mp3s:
    output_path = r"d:\z\Audio\_Tool\Audio\gdrive_mp3s.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        for name in unique_mp3s:
            # Clean name from escapes
            try:
                clean = name.encode('utf-8').decode('unicode-escape')
            except:
                clean = name
            f.write(clean + '\n')
            print(clean)
    print(f"\nDone! Found {len(unique_mp3s)} files. Saved to {output_path}")
else:
    print("Could not find any MP3 files using direct source scraping.")
