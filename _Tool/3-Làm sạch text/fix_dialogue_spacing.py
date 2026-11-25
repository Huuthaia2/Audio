import os
import re

def fix_dialogue_spacing(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Normalize line endings
        content = content.replace('\r\n', '\n')
        
        # Regex to find:
        # 1. A line starting with a dash (dialogue)
        # 2. Followed by a blank line (optional spaces)
        # 3. Followed by another line starting with a dash (dialogue)
        # We use a loop or re.sub with a backreference.
        # Pattern: ^\s*[–—-].*?\n\s*\n\s*[–—-].*?
        
        # Using a more robust approach:
        lines = content.split('\n')
        new_lines = []
        
        i = 0
        modified = False
        while i < len(lines):
            new_lines.append(lines[i])
            # If current line is dialogue and next is blank and next-next is dialogue
            if i + 2 < len(lines):
                curr = lines[i].strip()
                mid = lines[i+1].strip()
                nxt = lines[i+2].strip()
                
                # Check for various types of dashes used in Vietnamese texts
                dashes = ('–', '-', '—')
                if curr.startswith(dashes) and mid == "" and nxt.startswith(dashes):
                    # Skip the blank line
                    new_lines.append(lines[i+2])
                    i += 3
                    modified = True
                    continue
            i += 1
            
        if modified:
            new_content = '\n'.join(new_lines)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    truyen_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Truyện")
    target_dirs = [
        os.path.join(truyen_dir, "1-Text Mp3"),
        os.path.join(truyen_dir, "2-truyencogiaothao"),  # đã gồm zDaCoMp3 bên trong
    ]
    
    total_processed = 0
    total_modified = 0
    
    for base_dir in target_dirs:
        if not os.path.exists(base_dir):
            continue
            
        print(f"Processing directory: {base_dir}")
        for root, dirs, files in os.walk(base_dir):
            for filename in files:
                if filename.lower().endswith('.txt'):
                    filepath = os.path.join(root, filename)
                    total_processed += 1
                    if fix_dialogue_spacing(filepath):
                        total_modified += 1

    print(f"Finished. Total files processed: {total_processed}")
    print(f"Total files modified: {total_modified}")

if __name__ == "__main__":
    main()
