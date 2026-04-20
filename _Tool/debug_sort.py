import os, re

file_name = '12-con-giap-0031.txt'
slug = file_name.lower().replace('.txt', '')
slug = re.sub(r'-\d{3,4}$', '', slug)
clean_slug = re.sub(r'^\d+-', '', slug)
slug_clean = slug.replace('-', ' ')

print(f'Slug: "{slug}"')
print(f'Clean Slug: "{clean_slug}"')
print(f'Slug with spaces: "{slug_clean}"')

# Thử match với keywords mục 25
keywords_25 = ["dị thường & thế giới khác", "dị thường", "thế giới khác", "harem", "phiêu lưu", "lesbian", "thu vật", "xuyên không", "mario", "ngọc rồng", "doremon", "bạch tuyết", "sơn tinh", "truyện cổ tích", "emmanuelle", "toy", "con giáp", "loli", "tấm"]

found = False
for kw in keywords_25:
    if kw in slug_clean:
        print(f'MATCHED keyword: "{kw}"')
        found = True
        break

if not found:
    print('NO MATCH FOUND')
