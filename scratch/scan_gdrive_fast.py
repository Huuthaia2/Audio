import requests
import re
import os

folder_id = '1W1867yxPZdNmiV1sEaXzyHnaQXsHmFdu'
# The embedded view is often easier to scrape
url = f'https://drive.google.com/embeddedfolderview?id={folder_id}#list'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"Scanning folder: {folder_id} ...")

try:
    res = requests.get(url, headers=headers)
    content = res.text

    # Search for MP3 names in the rendered JS/HTML
    # Pattern 1: JS arrays in embedded view
    mp3s = re.findall(r'\"([^\"]+\.mp3)\"', content)
    
    unique_mp3s = sorted(list(set(mp3s)))
    
    output_file = r"d:\z\Audio\_Tool\Audio\mp3_list_fast.txt"
    if unique_mp3s:
        with open(output_file, 'w', encoding='utf-8') as f:
            for name in unique_mp3s:
                # Clean name
                clean_name = name.encode('utf-8').decode('unicode-escape') if '\\u' in name else name
                f.write(clean_name + '\n')
                print(f"Found: {clean_name}")
        print(f"\nSuccess! Wrote {len(unique_mp3s)} files to {output_file}")
    else:
        print("No MP3 files found in embedded view source. This folder might be empty or private.")

except Exception as e:
    print(f"Error: {e}")
