import requests
import re
import os

url = 'https://drive.google.com/drive/folders/1W1867yxPZdNmiV1sEaXzyHnaQXsHmFdu?usp=sharing'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    res = requests.get(url, headers=headers)
    content = res.text

    # Extract strings that look like mp3 filenames
    # Google Drive often embeds data in JS arrays like ["filename.mp3", ...]
    # Or in JSON strings.
    matches = re.findall(r'\"([^\"]+\.mp3)\"', content)
    
    unique_mp3s = sorted(list(set(matches)))
    
    output_file = r"d:\z\Audio\_Tool\Audio\mp3_list.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for name in unique_mp3s:
            # Clean up the name (Google Drive sometimes escapes characters)
            clean_name = name.encode('utf-8').decode('unicode-escape') if '\\u' in name else name
            f.write(clean_name + '\n')
            print(clean_name)
            
    if unique_mp3s:
        print(f"\nSuccessfully wrote {len(unique_mp3s)} MP3 files to {output_file}")
    else:
        print("No MP3 files found in the page source. Google Drive may require a real browser session to load the file list.")

except Exception as e:
    print(f"Error: {e}")
