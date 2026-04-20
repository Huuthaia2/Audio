W = {
    get() {
        let me = this;
        let l = jQuery('.main.version-chap a');
        let t = window.location.pathname.split('/').filter(Boolean);
        t = t[t.length - 1];
        if (l.length) {
            var st = [];
            for (var i = l.length-1; i >=0; i--) {
                st.push(l[i].outerHTML.trim());
            }
            me.cp(`<html><head><title>${t}</title></head><body>  ${st.join('\r\n')}</body></html>`);
        } else {
			console.clear();
            console.log("Vui lòng quay về trang có danh sách chương và chờ danh sách chương load xong.");
        }
    },
    cp(s) {
        var e = document.createElement('textarea');
        var p = document.createElement('p');
        e.style.width = "100%";
        e.style.height = "200px";
        p.style.fontWeight = "900";
        p.style.fontSize = "24px";
        p.innerHTML = 'Chép nội dung ở textbox dưới vào GetManual(CTRL + A, CTRL + C)';
        var fl = function (s) {
            console.clear();
            let f = `color: ${(s?'green':'red')};font-size:36px`;
            console.info("%cSao chép " + (s ? "thành công" : "thất bại"), f);
            if (s) {
                console.info('%cQuay lại MANUALGET -> CTRL + V, hoặc Chuột phải -> Dán HTML.', f);
            }
            if (!s) {
                console.info("%cTự động sao chép vào Clipboard không thành công, bạn cần tự chép từ textbox vào phần mềm.", f);
            }
        };
        e.value = s;
        document.body.appendChild(p);
        document.body.appendChild(e);
        e.select();
        e.focus();
        var s = document.execCommand("copy");
        window.scroll(0, 999999);
        fl(s);
    },
};
W.get();
