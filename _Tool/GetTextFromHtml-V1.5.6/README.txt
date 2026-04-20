╔═════════════════════════════════════════════════════════════╗
║                      WRITTEN BY MKBYME                       
╚═════════════════════════════════════════════════════════════╝
#           __      __                                    
#   /'\_/`\/\ \    /\ \                                   
#  /\      \ \ \/'\\ \ \____  __  __    ___ ___      __   
#  \ \ \__\ \ \ , < \ \ '__`\/\ \/\ \ /' __` __`\  /'__`\ 
#   \ \ \_/\ \ \ \\`\\ \ \M\ \ \ \_\ \/\ \/\ \/\ \/\  __/ 
#    \ \_\\ \_\ \_\ \_\ \_,__/\/`____ \ \_\ \_\ \_\ \____\
#     \/_/ \/_/\/_/\/_/\/___/  `/___/> \/_/\/_/\/_/\/____/
#                                 /\___/                  
#                                 \/__/                   
#
#	Phần mềm tải truyện chữ đa năng.
#	Link project: https://sourceforge.net/p/gethtmlfromurl/
#		Dropbox: https://www.dropbox.com/sh/dr87vbfn3y9uyt3/AACQ9q1UtgK--e53lfeerOZBa?dl=0
#
#	Hỗ trợ lấy truyện từ các trang đọc truyện online thành dạng HTML
#	Dùng làm ebook PRC bằng phần mềm MobiPRC Creator
#	Thêm mẫu trang mới thông qua mục Quản Lý HOST(Host Manager)
#------------------------------------
#	FANPAGE: https://www.facebook.com/gethtmlfromurl/?rc=p
#------------------------------------
#	Hướng dẫn sử dụng: 
#	- Post: http://forum.truyencv.com/showthread.php?t=2125
#	- Video: 
#	 - Tải và sử dụng
#		fb: https://www.facebook.com/gethtmlfromurl/videos/1865950080346966/
#		yt: https://www.youtube.com/watch?v=2xLOKHM6uyY
#	 - Video tạo ebook: 
#		fb: https://www.facebook.com/gethtmlfromurl/videos/1868069856801655/
#		yt: https://www.youtube.com/watch?v=9Zd2L1YJW2w
#
#------------------------------------
#Liên hệ:
#	mail: mkbyme@gmail.com.
#	facebook: fb.com/mkbyme
#	
╔═════════════════════════════════════════════════════════════╗
║                           LOGS                              
╚═════════════════════════════════════════════════════════════╝
[1.5.6][2020-12-01]
	- Tự động loại bỏ link chương truyện bị trùng, tránh tải trùng
	- Fix lỗi cập nhật ứng dụng (vẫn bị chậm)
	- ManualGet bổ sung thêm tính năng Mỗi Chương 1 Tệp
	- ManualGet bổ sung filter để lọc tìm host dễ hơn
	- AutoGet giờ hiển thị cả host manual, khi bấm vào hướng dẫn sẽ có thông báo để điều hướng dang manualget
	- HostManager sửa lỗi binding thông tin ManualGet
[1.5.5][2020-03-21]
	- Fix lỗi download truyện vip trên truyenyy
[1.5.4][2019.07.29]
	- sửa lỗi down trên host truyenfull.vn
	- sửa lỗi down trên host truyencv
	- sửa lỗi down trên host truyendich.org
	- thêm cơ chế bypass cloudflare(sau này các trang có bảo vệ ddos qua cloudflare sẽ xử lý như thường)
	- thay đổi lại giao diện trang Quản lý host
	- Tạo thêm bug mới (chờ mọi người tìm...)
[1.5.3][2019.01.31]
	- Sửa lỗi tải trên các trang sử dụng ajax(truyenyy,truyencv...) bị báo timeout.
[1.5.2][2019.01.28]
	- Thêm tính năng  đăng nhập từ cookies(do đăng nhập bằng 
	trình duyệt của app trên vài host khó khăn vd:truyencv...
	Menu -> Đăng Nhập Từ Cookies và làm theo hướng dẫn)
	- Sửa host: 
		truyendich.org(ajax), 
		tangthucac.com(website này đang lỗi SQL), 
		wikidich.com(thiếu danh sách chương)
	- Thêm thiết lập không chèn thêm text (Chương có nội dung ảnh Tệp > Cài Đặt > Tải xuống)
	- Lưu tệp từng file giữ nguyên được số chương ở cuối file(Trước khi luôn bị reset từ 1)
[1.5.1]
	- Thêm tính năng ghi Mục Lục 2 Cấp qua tùy chọn tải "CHÈN THÔNG TIN EBOOK"
[1.5.0]
	- Sửa lỗi download trên host truyencv.com
	- Xử lý download truyện VIP trên host truyenyy.com
	- Thêm popup hướng dẫn khi tải thiếu chương
	- Thêm cài đặt mở lại cảnh báo đã tắt
[1.4.9]
	- Thêm tính năng login trên tất cả các trang
	- Lưu dữ liệu người dùng tại máy(thông tin đăng nhập, thư mục, thói quen sử dung...)
	- chuyển dữ liệu sang JSON giảm dung lượng
	- Hỗ trợ tải chương vip trên truyenyy 
[1.4.8]
	- Hot fix không thể mở app do host sourceforce bị bảo trì.
[1.4.7]
	- tích hợp thêm script js khi thêm hướng dẫn trên quản lý host
	- bổ sung thu gọn mở rộng trên tính năng quản lý host
[1.4.6]
	- Sửa lỗi resume download.
[1.4.5]
	- Cập nhật thư viện GET
	- Update lại config mặc định dùng JSOUP để get, sửa lỗi font khi tải host china.
[1.4.4]
	- Thêm plugin hỗ trợ host https://tangthucac.com/
	- Thêm tính năng lọc host theo vị trí (Việt Nam hoặc quốc tế)
[1.4.3]
	- Thêm plugin hỗ trợ host https://truyen.tangthuvien.vn/
	- Thêm nhãn đếm số host trong phần mềm
[1.4.2]
	- Thay đổi cơ chế cập nhật
	- Tính năng nhập thông tin ebook bổ sung thêm live view
[1.4.1]
	- Cập nhật tính năng get theo mẫu host mới dạng *.tên_host.tên_miền
	- Sửa lỗi xóa file tạm
	- Chú ý sau mỗi bản update sẽ phải set lại tính năng Bỏ chặn TruyenCV để có thể tải trên trang này.
[1.4.01]
	- Sửa lỗi khi lưu chọn định dạng txt trắng file
[1.4.0]
	- Thêm tính năng trình duyệt
	- Fix lỗi tải trên truyencv, wikidich
	- Thêm tính năng chia nhỏ file thành từng chương khi lưu
[1.3.91]
	- Sửa lỗi host truyencv.com
	- thêm host mới cho converter.
[1.3.9]
	- fix bugs không download được trang bị chuyển hướng https
[1.3.8]
	- Fix bugs
[1.3.7]
	- Fix bugs
	- Chuyển tất cả text sang file.
[1.3.6]
	- Fix bugs
[1.3.5]
	- Thay đổi regex $ sang regex ;
	- thêm tính năng lọc/tìm kiếm host mà phần mềm hỗ trợ, để đọc hướng dẫn tải
	- thêm tính năng lọc nội dung tải xuống / chỉnh sửa trong text filter của Quản Lý Host
[1.3.4]
	- Fix bugs tải truyện bị lỗi encoding trên truyencv và sstruyen
[1.3.3]
	- Fix lỗi mã hóa khi tải trên trang có text trung
	- Tự động nhận dạng mã hóa khi tải xuống
	- Thêm chức năng hiện lỗi tới người dùng và report.
[1.3.2]
	- Fix lỗi cập nhật tự động
	- Fix lỗi 1.3.1 không mở được giao diện
	- Giảm dung lượng file chạy.
[1.3.1]
	- Fix lỗi cập nhật tự động
	- Tăng số kết nối tối đa lên 32.
[1.3.0]
	- Cải thiện tính năng get trên loại @Forum(diễn đàn)
	fix lỗi bị lặp chương.
	- File html tải từ forum sẽ mịn và đẹp hơn.
	- Fix bugs update
[1.2.9]
	- Hỗ trợ tải từ trang có giao thức https khi chứng chỉ trên trang chưa có
	Sau khi fix xong thì mở lại phần mềm để cập nhật thay đổi.
[1.2.8]
	- Fix lỗi liền tiêu đề chương với đoạn trước khi
	lưu dưới dạng text.
	- Fix update
[1.2.7]
	- Thêm tính năng thiết lập độ trễ đa luồng
	- Thêm thiết lập thời gian chờ
	Nhằm fix với những host chậm (tăng thông số trên lên cao để sửa lỗi)
	Truy cập TỆP > CÀI ĐẶT > Tải Xuống 
[1.2.6.1]
	- Fix module update
[1.2.6]
	- Fix lại tính năng cập nhật (hoạt động trở lại)
	- Fix một số lỗi nhỏ
	- Xuất ra truyện dạng Text
	- Thêm cài đặt dãn dòng
[1.2.52]
	- Fix lỗi nút Cửa Sổ Mới không hoạt động.
	- Thêm nút lọc trang và kiểm tra khi thêm HOST trong 
	Menu Quản Lý HOST.
	- Thêm đường dẫn trợ giúp về sử dụng tính năng Quản Lý Host.
[1.2.5]
	- Fix lỗi filter các phiên bản trước
	- Hỗ trợ site dạng diễn đàn(forum)
	- Fix config một số trang việt bị thay đổi bởi chủ web.
	- Cải thiện tính năng get.
[1.2.4]
	- Fix lỗi cập nhật file thiết lập (bản 1.2.3 không cập nhật được file config tự động, mà phải cập
nhập bằng tay).
[1.2.3]
	- Nâng cấp khả năng GET 
	- Sửa những host thủ công sang tự động
	- Thêm pattern mới có CSSQuery : $replace=(replace)&with=(replacment) cho địa chỉ của chapter.
khi là đường đẫn tương đối (trước kia ghép đường dẫn tương đối theo kiểu host + path, nay có thể linh động hơn, tìm kiếm đường dẫn và
thay thế để ghép nối).
[1.2.2]
	- Tự động xóa file cũ sau update.
[1.2.1][08/01/2017]
	- Thêm màn hình load, trước kia chạy 4s là do nó kiểm tra cập nhật mà không hiện ra.
	- Fix lỗi Khi tải link ở china, lỗi ngẫu nhiên báo đường dẫn không hợp lệ dù là nhập đúng
	- Fix Crash khi mở HostManager trong tiếng anh
	- Thêm menu truy cập trang chủ của phần mềm trong menu TRỢ GIÚP
[1.2.0][07/01/2017]                                                        
 	- Fix lỗi khi nhấn nút tải xuống mà không hoạt động.
[1.1.9] 
	- Thêm tính năng cập nhật file config tự động.
	- Thêm tính năng chọn số chương để tải trong phạm vi 
     định trước
 	- Fix mutilthread issue, improve get function
 	- Công cụ sửa text cho ManualGet
[1.1.8] 
 	- Tăng tính năng get - thêm host qidian,uukansu
[1.1.7] 
 	- Update option
[1.1.6] 
 	- Fix lỗi không tải được trong manual GET.
[1.1.5] 
 	- Thêm tính năng tự động cập nhật
 	- Cải thiện module get
[1.1.4]  
 	- Thêm chức năng tải đa luồng x8 tốc độ (max to 8 thread per/story)
 	- Thêm tính năng nhập thông tin bản quyền ebook
 	- Giảm tải sử dụng bộ nhớ RAM (đệm thẳng xuống ổ HDD)
[1.1.3] 
 	- Thêm tính năng CSS Filter, loại bỏ nội dung không mong muốn khỏi trang
 	- Tự động tải file ghfuConfig.data nếu không có.
[1.1.2]
 	- Sửa lỗi không lưu được tệp tin khi truyện hơn 2K chapter, giảm tải sử dụng bộ nhớ.
[1.1.1]
 	- Cải thiện tính năng, thêm chức năng hướng dẫn tải cho từng host.
[1.1.0]
 	- Thêm 2 regex cho pagePattern(dạng text{số_trang}text, thêm regex {start=0&end=n} cho 
 		cssGetListChapterQuery dùng cho truy vấn
 		document.querySelectorAll() trên DOM.
[1.0.9]
 	- Thêm menu context chuột phải tại textbox (để dán hoặc truy cập nhanh),UX.
[1.0.8]
 	- Cải thiện tính năng tải manual cho trang có link chapter trộn giữa tuyệt đối & tương đối.
[1.0.7]
 	- Ổn định hóa.
[1.0.6]
	- Thêm tính năng tải tiếp khi gặp lỗi hoặc hủy,biểu tượng mới.
[1.0.5]
	- Thêm tính năng mới hỗ trợ nhiều trang hơn, fix lỗi 403
[1.0.4]
	- Fix lỗi tag h2, thêm tính năng sửa ảnh thành link để xem khi đọc dưới dạng PRC.
[1.0.2] 
	- Fix lỗi khi tải bị lỗi font chữ.
[1.0.1] 
	- Phiên bản đầu tiên.