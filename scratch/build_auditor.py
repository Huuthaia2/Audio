import os, json, sys
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

# Load data
with open(r'd:\z\Audio\_Tool\Audio\scratch\library_data_inline.json', 'r', encoding='utf-8') as f:
    data_str = f.read()

count = len(json.loads(data_str))

html_top = '''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Library Auditor - Premium</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@300;600&display=swap');
:root{--glass:rgba(255,255,255,0.1);--glass-border:rgba(255,255,255,0.2);--accent:#00f2fe;--accent-glow:rgba(0,242,254,0.5);--bg:#0f172a}
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}
body{background:var(--bg);background-image:radial-gradient(at 0% 0%,hsla(253,16%,7%,1) 0,transparent 50%),radial-gradient(at 50% 0%,hsla(225,39%,30%,1) 0,transparent 50%),radial-gradient(at 100% 0%,hsla(339,49%,30%,1) 0,transparent 50%);color:#fff;min-height:100vh;padding:2rem;overflow-x:hidden}
.container{max-width:1200px;margin:0 auto}
header{text-align:center;margin-bottom:3rem}
h1{font-family:'Outfit',sans-serif;font-size:3.5rem;font-weight:600;background:linear-gradient(to right,#00f2fe,#4facfe);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem}
.search-box{position:relative;margin:2rem auto;max-width:600px}
.search-box input{width:100%;padding:1rem 1.5rem;background:var(--glass);border:1px solid var(--glass-border);border-radius:15px;color:#fff;font-size:1.1rem;backdrop-filter:blur(10px);outline:none;transition:all .3s}
.search-box input:focus{border-color:var(--accent);box-shadow:0 0 15px var(--accent-glow)}
.file-grid{display:flex;flex-direction:column;gap:4px}
.file-card{background:var(--glass);border:1px solid transparent;padding:0.5rem 1rem;border-radius:8px;transition:all .15s;display:flex;align-items:center;gap:0.8rem;cursor:pointer}
.file-card:hover{background:rgba(255,255,255,0.12);border-color:var(--accent)}
.file-card.selected{border-color:#22c55e;background:rgba(34,197,94,0.08)}
.cb{width:24px;height:24px;min-width:24px;border:2px solid var(--glass-border);border-radius:6px;display:flex;align-items:center;justify-content:center;transition:all .3s}
.file-card.selected .cb{background:#22c55e;border-color:#22c55e}
.cb::after{content:"\\2713";color:#fff;display:none;font-weight:bold}
.file-card.selected .cb::after{display:block}
.fi{flex:1;overflow:hidden}
.fn{font-weight:600;font-size:1rem;margin-bottom:.2rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fp{font-size:.8rem;opacity:.6}
.mo{position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.85);backdrop-filter:blur(10px);display:none;justify-content:center;align-items:center;z-index:10000;cursor:pointer}
.mo.active{display:flex}
.mc{background:#1e293b;width:85%;max-width:1000px;height:85vh;border-radius:30px;padding:3rem;position:relative;box-shadow:0 50px 100px -20px rgba(0,0,0,0.6);border:1px solid var(--glass-border);display:flex;flex-direction:column;cursor:default;animation:modalIn .4s cubic-bezier(.34,1.56,.64,1)}
@keyframes modalIn{from{opacity:0;transform:translateY(30px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}
.mh{margin-bottom:1.5rem;border-bottom:1px solid var(--glass-border);padding-bottom:1rem}
.mt-title{font-size:1.6rem;font-weight:600;color:var(--accent)}
.mb{flex:1;overflow-y:auto;white-space:pre-wrap;line-height:1.8;font-size:1.05rem;padding-right:1rem;color:#e2e8f0}
.mb::-webkit-scrollbar{width:8px}
.mb::-webkit-scrollbar-thumb{background:var(--glass-border);border-radius:10px}
.xb{position:absolute;top:1.5rem;right:1.5rem;width:45px;height:45px;background:rgba(255,255,255,0.05);border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:.3s;font-size:1.2rem}
.xb:hover{background:rgba(255,50,50,0.4);transform:rotate(90deg)}
.fa{position:fixed;bottom:2rem;right:2rem;display:flex;gap:1rem}
.btn{padding:1.1rem 2.2rem;border-radius:50px;border:none;font-weight:600;cursor:pointer;transition:.3s;box-shadow:0 10px 30px rgba(0,0,0,0.3);background:linear-gradient(45deg,#00f2fe,#4facfe);color:#0f172a}
.btn:hover{transform:translateY(-3px) scale(1.05);box-shadow:0 15px 35px var(--accent-glow)}
.stats{margin-top:1rem;opacity:.7;font-size:.95rem}
</style>
</head>
<body>
<div class="container">
<header>
<h1>Library Auditor</h1>
<p>Total TXT files in truyencogiaothao</p>
<div class="stats" id="stats">Loading...</div>
<div class="search-box"><input type="text" id="search" placeholder="Search..."></div>
</header>
<div class="file-grid" id="fg"></div>
</div>
<div class="mo" id="mo">
<div class="mc">
<div class="xb" id="closeBtn">&#10005;</div>
<div class="mh"><div class="mt-title" id="mtitle"></div></div>
<div class="mb" id="mbb"></div>
</div>
</div>
<div class="fa"><button class="btn" id="exportBtn">Export Selected</button></div>
<script>
const D='''

html_bottom = ''';
let sel=new Set();
const fg=document.getElementById("fg");
const mo=document.getElementById("mo");
const mtitle=document.getElementById("mtitle");
const mbb=document.getElementById("mbb");
const stats=document.getElementById("stats");
const searchInput=document.getElementById("search");

function render(d){
  fg.innerHTML="";
  d.forEach(function(f){
    var c=document.createElement("div");
    c.className="file-card"+(sel.has(f.name)?" selected":"");
    var cbDiv=document.createElement("div");
    cbDiv.className="cb";
    cbDiv.addEventListener("click",function(e){
      e.stopPropagation();
      if(sel.has(f.name)){sel.delete(f.name);c.classList.remove("selected")}
      else{sel.add(f.name);c.classList.add("selected")}
      updateStats();
    });
    var fiDiv=document.createElement("div");
    fiDiv.className="fi";
    var fnDiv=document.createElement("div");
    fnDiv.className="fn";
    fnDiv.textContent=f.name;
    var fpDiv=document.createElement("div");
    fpDiv.className="fp";
    fpDiv.textContent=f.path;
    fiDiv.appendChild(fnDiv);
    fiDiv.appendChild(fpDiv);
    c.appendChild(cbDiv);
    c.appendChild(fiDiv);
    c.addEventListener("click",function(){openModal(f)});
    fg.appendChild(c);
  });
}

function openModal(f){
  mtitle.textContent=f.name;
  mbb.textContent=f.content;
  mo.classList.add("active");
  document.body.style.overflow="hidden";
}

function closeModal(){
  mo.classList.remove("active");
  document.body.style.overflow="auto";
}

// Click vung den (overlay) de dong
mo.addEventListener("click",function(e){
  if(e.target===mo) closeModal();
});

// Nut X dong
document.getElementById("closeBtn").addEventListener("click",function(e){
  e.stopPropagation();
  closeModal();
});

// Chặn click trong modal content lan ra overlay
document.querySelector(".mc").addEventListener("click",function(e){
  e.stopPropagation();
});

// Tim kiem
searchInput.addEventListener("input",function(e){
  var q=e.target.value.toLowerCase();
  render(D.filter(function(f){return f.name.toLowerCase().indexOf(q)>=0||f.path.toLowerCase().indexOf(q)>=0}));
});

function updateStats(){
  stats.textContent="Total: "+D.length+" files | Selected: "+sel.size;
}

// Export
document.getElementById("exportBtn").addEventListener("click",function(){
  if(!sel.size){alert("Please select files first!");return}
  var b=new Blob([JSON.stringify(Array.from(sel),null,2)],{type:"application/json"});
  var a=document.createElement("a");
  a.href=URL.createObjectURL(b);
  a.download="audit_results.json";
  a.click();
});

render(D);
updateStats();
</script>
</body>
</html>'''

with open(r'd:\z\Audio\_Tool\Audio\scratch\library_auditor.html', 'w', encoding='utf-8') as f:
    f.write(html_top)
    f.write(data_str)
    f.write(html_bottom)

print(f'Done! Built HTML with {count} files inline.')
