import os
import re

def cleanup_file(filepath):
    try:
        # Read content
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Normalize line endings to \n
        content = content.replace('\r\n', '\n')
        
        # Remove trailing spaces on each line to properly detect truly "blank" lines
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        # Replace 3 or more consecutive newlines with exactly 2 newlines (one blank line)
        # This collapses multiple blank lines into one.
        new_content = re.sub(r'\n{3,}', '\n\n', content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    target_dirs = [
        r"c:\Users\Windows\Documents\MEGA\Audio\Text Mp3",
        r"c:\Users\Windows\Documents\MEGA\Audio\truyencogiaothao",
        r"c:\Users\Windows\Documents\MEGA\Audio\zDaCoMp3"
    ]
    
    total_processed = 0
    total_modified = 0
    
    for base_dir in target_dirs:
        if not os.path.exists(base_dir):
            print(f"Directory not found: {base_dir}")
            continue
            
        print(f"Processing directory: {base_dir}")
        for root, dirs, files in os.walk(base_dir):
            for filename in files:
                if filename.lower().endswith('.txt'):
                    filepath = os.path.join(root, filename)
                    total_processed += 1
                    if cleanup_file(filepath):
                        total_modified += 1
                        if total_modified % 100 == 0:
                            print(f"Modified {total_modified} files...")

    print(f"Finished. Total files processed: {total_processed}")
    print(f"Total files modified: {total_modified}")

if __name__ == "__main__":
    main()
