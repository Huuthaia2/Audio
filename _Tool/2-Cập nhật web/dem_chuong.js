// Đếm số chương THẬT của các file truyện bằng chính hàm chia chương của web (reader.js: splitIntoChapters)
// ⇒ số chương ghi trong stories.json luôn khớp 100% với lúc mở truyện. update_index.py gọi:
//   node dem_chuong.js <file danh sách đường dẫn .json>   ⇒ in ra JSON {đường dẫn: số chương}
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..', '..');
const src = fs.readFileSync(path.join(root, 'reader.js'), 'utf8');
const body = src.slice(src.indexOf('function splitIntoChapters'), src.indexOf('// Chia 1 đoạn văn'));
const splitIntoChapters = new Function(body + '; return splitIntoChapters;')();
const files = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = {};
for (const f of files) {
  try { out[f] = splitIntoChapters(fs.readFileSync(path.join(root, f), 'utf8'), f).length; } catch (e) { /* bỏ qua file lỗi */ }
}
process.stdout.write(JSON.stringify(out));
