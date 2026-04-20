import re
from difflib import SequenceMatcher

# --- LOGIC V5.2 (Simplified for comparison) ---
STOP_WORDS = {"truyen", "sex", "loan-luan", "ll", "ntr", "llntr", "audio", "cau-chuyen", "tinh-yeu", "chuyen", "tap"}

def extract_part_v52(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?)(\d+)', slug)
    if match: return f"part{match.group(2)}"
    return "part1"

def clean_slug_v52(slug):
    part = extract_part_v52(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?)\d+', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

# --- LOGIC V5.3 ---
def extract_part_v53(slug):
    match = re.search(r'(phan-|quyen-|vol-|p-|v-?|ver-?)(\d+)', slug)
    if match: return f"p{match.group(2)}"
    match_end = re.search(r'-(\d+)$', slug)
    if match_end: return f"p{match_end.group(1)}"
    return "p1"

def clean_slug_v53(slug):
    part = extract_part_v53(slug)
    slug = re.sub(r'^(truyen-sex-|truyen-|audio-truyen-|audio-)', '', slug)
    slug = re.sub(r'(phan-|quyen-|vol-|p-|v-?|ver-?)\d+', '', slug)
    slug = re.sub(r'-(\d+)$', '', slug)
    for tag in STOP_WORDS: slug = slug.replace(tag, "")
    slug = re.sub(r'-+', '-', slug).strip("-")
    return slug, part

def compare(txt_name, mp3_name):
    # V5.2 logic
    b2_t, p2_t = clean_slug_v52(txt_name)
    b2_m, p2_m = clean_slug_v52(mp3_name)
    v52_match = (p2_t == p2_m and b2_t == b2_m)
    
    # V5.3 logic
    b3_t, p3_t = clean_slug_v53(txt_name)
    b3_m, p3_m = clean_slug_v53(mp3_name)
    v53_match = (p3_t == p3_m and b3_t == b3_m)
    
    return v52_match, v53_match

# Test cases from user feedback
test_cases = [
    ("duc-vong-gia-dinh-2-0030", "duc-vong-gia-dinh"),
    ("duc-vong-gia-dinh-0085", "duc-vong-gia-dinh"),
    ("loan-luan-nu-canh-sat-dam-dang-phan-2-0004", "loan-luan-nu-canh-sat-dam-dang"),
    ("con-thay-cha-lam-chong-cua-me-0037", "thay-cha-lam-chong-cua-me")
]

print("Comparing V5.2 vs V5.3 Logic:")
print("-" * 60)
for t, m in test_cases:
    v52, v53 = compare(t, m)
    print(f"TXT: {t}")
    print(f"MP3: {m}")
    print(f"  V5.2: {'MATCH' if v52 else 'NO'}")
    print(f"  V5.3: {'MATCH' if v53 else 'NO'}")
    print("-" * 30)
