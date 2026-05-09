import os

mp3_list_path = r'c:\Users\Windows\Documents\MEGA\Audio\all_mp3_files.txt'
raw_dir = r'c:\Users\Windows\Documents\MEGA\truyenco - Raw'

with open(mp3_list_path, 'r', encoding='utf-8') as f:
    mp3_files = {line.strip().lower() for line in f if line.strip()}

missing = []

for root, dirs, files in os.walk(raw_dir):
    for file in files:
        if file.lower().endswith('.txt'):
            base_name = file[:-4].lower()
            # Check if this base name exists in any mp3 filename
            found = False
            for mp3 in mp3_files:
                if mp3.startswith(base_name):
                    found = True
                    break
            
            if not found:
                missing.append(os.path.join(root, file))

# Sort by category (folder)
missing.sort()

print(f"Total missing: {len(missing)}")
for path in missing:
    print(path)
