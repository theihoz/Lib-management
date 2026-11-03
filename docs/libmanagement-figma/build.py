from pathlib import Path
import json, html, math

OUT=Path('/private/tmp/libmanagement-figma')
C={'bg':'#F7F5EF','white':'#FFFFFF','ink':'#17212B','muted':'#53616B','blue':'#174B73','nav':'#142C35','border':'#D8DCD8','accent':'#9B4B2F','green':'#146C43','amber':'#8A4B08','red':'#B42318'}
def esc(s):return html.escape(str(s))
def rect(x,y,w,h,c='white',r=0,stroke=None):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{C.get(c,c)}"'+(f' stroke="{C.get(stroke,stroke)}"' if stroke else '')+'/>'
def text(x,y,s,size=14,c='ink',bold=False,serif=False):
    return f'<text x="{x}" y="{y}" font-family="{ "Georgia" if serif else "Arial"}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{C.get(c,c)}">{esc(s)}</text>'
def lines(x,y,s,width=75,size=14,c='muted',step=23):
    import textwrap
    return ''.join(text(x,y+i*step,t,size,c) for i,t in enumerate(textwrap.wrap(s,width=width)))
def btn(x,y,s,primary=True,w=None):
    w=w or max(104,len(s)*8+32)
    return rect(x,y,w,44,'blue' if primary else 'white',8,None if primary else 'border')+text(x+16,y+28,s,14,'white' if primary else 'blue',True)
def badge(x,y,s,c='green'):
    return rect(x,y,max(90,len(s)*7+22),28,{'green':'#E8F3ED','amber':'#FFF1DC','red':'#FCEDEA','blue':'#EAF0F5'}.get(c,'#EAF0F5'),6)+text(x+10,y+19,s,12,c,True)
def field(x,y,label,val='',w=490):
    return text(x,y,label,13,'muted',True)+rect(x,y+12,w,48,'white',8,'border')+text(x+14,y+42,val or 'Nhập '+label.lower(),14,'ink' if val else 'muted')
def table(x,y,w,headers,rows,widths=None):
    widths=widths or [1/len(headers)]*len(headers)
    a=rect(x,y,w,44,'#EDF0EC',6)
    xx=x
    for h,f in zip(headers,widths):a+=text(xx+14,y+28,h.upper(),11,'muted',True);xx+=w*f
    for i,row in enumerate(rows):
        yy=y+44+i*58;a+=rect(x,yy,w,58,'white')+rect(x,yy+57,w,1,'border');xx=x
        for j,(v,f) in enumerate(zip(row,widths)):
            a+=text(xx+14,yy+33,v,13,'blue' if j==0 else 'ink',j==0);xx+=w*f
    return a
def panel(x,y,w,h,title,sub=''):
    a=rect(x,y,w,h,'white',12,'border')+text(x+24,y+36,title,20,'ink',True,True)
    if sub:a+=text(x+24,y+62,sub,13,'muted')
    return a
BOOKS=[['BK-0184','Bến không chồng','Dương Hướng','2023','3 / 5'],['BK-0207','Mùa lá rụng trong vườn','Ma Văn Kháng','2022','1 / 4'],['BK-0321','Dế Mèn phiêu lưu ký','Tô Hoài','2024','0 / 6'],['BK-0455','Nỗi buồn chiến tranh','Bảo Ninh','2021','2 / 3']]
LOANS=[['PM-1024','Nguyễn Minh An','19/10/2026','23/10/2026','2 cuốn · Đang mượn'],['PM-1023','Trần Hà Linh','13/10/2026','17/10/2026','1 cuốn · Quá hạn']]
HOLDS=[['DC-208','Nguyễn Minh An','Dế Mèn phiêu lưu ký','QUEUED · Vị trí 2','—'],['DC-207','Lê Thu Hương','Bến không chồng','READY','22/10/2026 10:00']]
READERS=[['DG-001','Nguyễn Minh An','Còn hiệu lực','0 ₫','Đủ điều kiện'],['DG-002','Trần Hà Linh','Còn hiệu lực','12.000 ₫','Có dư nợ'],['DG-003','Lê Thu Hương','Hết hạn','0 ₫','Thẻ hết hạn'],['DG-004','Phạm Khánh Vy','Còn hiệu lực','0 ₫','Phí chờ xác nhận']]
LEDGER=[['PH-091','Quá hạn','12.000 ₫','0 ₫','0 ₫','12.000 ₫'],['PH-082','Quá hạn','4.000 ₫','4.000 ₫','0 ₫','0 ₫']]
JOBS=[['JOB-120','CSV báo cáo','Hoàn tất','1','—'],['JOB-119','Gửi email','Chờ thử lại','2','19/10/2026 08:10'],['JOB-118','Sao lưu','Đang chạy','1','—']]
S=[]
def add(group,name,kind='list',**kw):S.append(dict(group=group,name=name,kind=kind,**kw))

# Every screen has explicit domain content. No cross-domain table fallback.
for name,desc,act in [('Đăng nhập thư viện','Sử dụng tài khoản được nhân viên cấp hoặc liên kết.','Tiếp tục với SSO'),('Đang xác minh phiên','Đang chuyển về trang làm việc của bạn.','Chờ xác minh'),('Phiên đăng nhập hết hạn','Đăng nhập lại để tiếp tục. Dữ liệu biểu mẫu chưa gửi được giữ lại.','Đăng nhập lại'),('Bạn chưa có quyền truy cập','Tài khoản hiện tại không có quyền thực hiện thao tác này.','Về trang làm việc'),('Tài khoản đã bị khóa','Liên hệ quản trị viên để kiểm tra trạng thái tài khoản.','Về danh mục sách'),('Không thể kết nối','Kiểm tra kết nối mạng rồi thử lại. Không cần nhập lại biểu mẫu.','Thử lại'),('Đăng xuất khỏi thư viện?','Bạn sẽ kết thúc phiên làm việc trên trình duyệt này.','Xác nhận đăng xuất')]:add('01',name,'auth',desc=desc,action=act)
add('02','Khám phá sách','catalog')
add('02','Bến không chồng','book')
add('02','Danh mục ấn bản',headers=['Mã','Nhan đề','Tác giả','Năm','Khả dụng'],rows=BOOKS,action='Thêm ấn bản')
add('02','Tạo / sửa ấn bản','form',fields=[('Nhan đề','Bến không chồng'),('Tác giả','Dương Hướng'),('Nhà xuất bản','NXB Trẻ'),('Năm xuất bản','2023'),('ISBN','978-604-000000-1'),('Thể loại','Văn học')],note='Năm xuất bản từ năm hiện tại − 8 đến năm hiện tại, gồm cả hai biên.',action='Lưu ấn bản')
add('02','Bản sách và mã vạch',headers=['Barcode','Ấn bản','Tình trạng','Lưu thông'],rows=[['BC-0184-01','Bến không chồng','Tốt','Sẵn có'],['BC-0184-02','Bến không chồng','Tốt','Đang mượn'],['BC-0184-03','Bến không chồng','Hỏng','Chờ xử lý']],action='Thêm bản sách')
add('02','Tác giả',headers=['Tác giả','Giới thiệu','Trạng thái'],rows=[['Dương Hướng','Tác giả văn học Việt Nam','Hoạt động'],['Tô Hoài','Nhà văn Việt Nam','Hoạt động'],['Bảo Ninh','Tác giả văn học Việt Nam','Hoạt động']],action='Thêm tác giả',mini=[('Tên tác giả','Dương Hướng'),('Giới thiệu','Tác giả văn học Việt Nam')])
add('02','Nhà xuất bản',headers=['Tên nhà xuất bản','Địa chỉ','Trạng thái'],rows=[['NXB Trẻ','TP. Hồ Chí Minh','Hoạt động'],['NXB Kim Đồng','Hà Nội','Hoạt động']],action='Thêm nhà xuất bản',mini=[('Tên nhà xuất bản','NXB Trẻ'),('Địa chỉ','TP. Hồ Chí Minh')])
add('02','Phân loại sách','tree')
add('02','Ảnh bìa ấn bản','upload')
add('03','Độc giả và thẻ',headers=['Mã độc giả','Họ tên','Thẻ','Dư nợ','Điều kiện'],rows=READERS,action='Thêm độc giả')
add('03','Hồ sơ độc giả','profile')
add('03','Tạo / sửa hồ sơ độc giả','form',fields=[('Họ tên','Nguyễn Minh An'),('Ngày sinh','21/08/2004'),('Email','an@example.com'),('Điện thoại','0900 000 001'),('Địa chỉ','Địa chỉ minh họa'),('Loại độc giả','Sinh viên')],action='Lưu hồ sơ',note='Thông tin trong bản thiết kế là dữ liệu minh họa.')
add('03','Cấp thẻ thư viện','form',fields=[('Độc giả','DG-001 · Nguyễn Minh An'),('Ngày cấp','19/10/2026'),('Hạn thẻ','Xem trước từ hệ thống'),('Mã thẻ','Tạo sau khi xác nhận')],action='Xác nhận cấp thẻ',note='Ngày hết hạn lấy từ kết quả xem trước; không tự đặt thời hạn thẻ.')
add('03','Cấp / liên kết tài khoản','form',fields=[('Độc giả có sẵn','DG-001 · Nguyễn Minh An'),('Tên tài khoản','minhan'),('Liên kết hiện tại','Chưa liên kết'),('Phương án','Cấp tài khoản độc giả')],action='Xác nhận liên kết',note='Không cấp vai trò nhân viên hoặc quản trị tại luồng này. Có trạng thái trùng, chờ xử lý, thành công và lỗi.')
add('04','Quầy mượn sách','checkout')
add('04','Chưa đủ điều kiện mượn','checkout',blocked=True)
add('04','Bản sách không còn khả dụng','checkout',conflict=True)
add('04','Phiếu mượn',headers=['Số phiếu','Độc giả','Ngày mượn','Hạn trả','Trạng thái'],rows=LOANS,action='Lập phiếu mượn')
add('04','Chi tiết phiếu PM-1024','loan')
add('05','Tiếp nhận trả sách','returns')
add('05','Đánh giá tình trạng sách','returns',condition=True)
add('05','Đề xuất phí hỏng / mất','form',fields=[('Khoản mượn','PM-1024 · BC-0184-02'),('Tình trạng','Hỏng'),('Số tiền đề xuất','80.000 ₫'),('Lý do bắt buộc','Bìa rách, cần sửa chữa')],action='Ghi nhận trả & gửi đề xuất',note='Sách được nhận trả ngay. Đề xuất chưa phải dư nợ; Quản lý xác nhận số tiền hoặc kết thúc không thu.')
add('05','Biên nhận trả sách','receipt',receipt='PT-1024',items=[['BC-0184-02','Bến không chồng','Đã trả · Tốt'],['BC-0207-01','Mùa lá rụng trong vườn','Đã trả · Hỏng']],note='Khoản phí hỏng đang chờ Quản lý xác nhận. Thu tiền là thao tác riêng.')
add('06','Hàng đợi giữ chỗ',headers=['Mã đặt','Độc giả','Ấn bản','Trạng thái','Hạn nhận'],rows=HOLDS,action='Hỗ trợ đặt trước')
add('06','Chi tiết đặt trước DC-207','hold')
add('06','Nhận sách / hết hạn giữ chỗ','hold',expired=True)
add('06','Xem trước gia hạn','renew')
add('06','Biên nhận gia hạn','receipt',receipt='GH-1024',items=[['BC-0184-02','Hạn cũ: 23/10/2026','Hạn mới: 27/10/2026'],['BC-0207-01','Hạn cũ: 23/10/2026','Hạn mới: 27/10/2026']],note='Đã gia hạn toàn bộ khoản OPEN một lần. Không gia hạn từng phần.')
add('07','Sổ tài chính độc giả','finance')
add('07','Thu tiền và phân bổ','payment')
add('07','Phí chờ xác nhận',headers=['Mã đề xuất','Độc giả','Bản sách','Đề xuất','Trạng thái'],rows=[['DGPH-021','Phạm Khánh Vy','BC-0207-01','80.000 ₫','PENDING'],['DGPH-020','Nguyễn Minh An','BC-0184-04','120.000 ₫','CLOSED_NO_CHARGE']],action='Xem đề xuất')
add('07','Xác nhận phí hỏng / mất','assessment')
add('07','Miễn / đảo khoản ghi nhận','form',fields=[('Khoản phí','PH-091 · Quá hạn'),('Số tiền còn phải thu','12.000 ₫'),('Thao tác','Miễn khoản phí'),('Lý do bắt buộc','Ghi rõ căn cứ miễn hoặc đảo')],action='Xem lại & xác nhận',note='Chỉ Quản lý có quyền. Lưu lịch sử trước/sau; không sửa hoặc xóa giao dịch cũ.')
add('07','Lịch sử tài chính',headers=['Thời điểm','Người thực hiện','Sự kiện','Đối tượng','Số tiền'],rows=[['19/10 09:12','Thủ thư A','Ghi nhận thu','TT-091','4.000 ₫'],['19/10 09:00','Hệ thống','Ghi phí quá hạn','PH-091','12.000 ₫'],['18/10 15:20','Quản lý B','Kết thúc không thu','DGPH-020','0 ₫']],note='Sổ ghi nhận chỉ thêm; không có thao tác xóa lịch sử.')
add('08','Của tôi','portal')
add('08','Sách đang mượn','ownloans')
add('08','Đặt trước của tôi','ownholds')
add('08','Lịch sử mượn và thanh toán','history')
add('08','Tài chính của tôi','ownfinance')
add('08','Hồ sơ và thẻ của tôi','ownprofile')
add('08','Thông báo của tôi','notifications')
add('08','Tùy chọn nhận email','preferences')
add('09','Danh sách quá hạn',headers=['Phiếu mượn','Độc giả','Hạn trả','Số cuốn','Phí đã ghi'],rows=[['PM-1023','Trần Hà Linh','17/10/2026','1','12.000 ₫'],['PM-1018','Phạm Khánh Vy','18/10/2026','2','2.000 ₫']],note='Bấm số phiếu hoặc độc giả để mở hồ sơ phục vụ xử lý.')
add('09','Báo cáo quản lý','reports')
add('09','Chi tiết báo cáo mượn trả','reports',detail=True)
add('09','Xuất báo cáo CSV',headers=['Tác vụ','Tệp','Trạng thái','Hết hạn','Thao tác'],rows=[['CSV-042','muon-tra-10-2026.csv','Hoàn tất','20/10/2026','Tải CSV'],['CSV-041','qua-han-09-2026.csv','Hết hạn','18/10/2026','Tạo yêu cầu mới']],action='Tạo yêu cầu CSV',note='Chỉ Quản lý được xuất CSV. Kiểm tra lại quyền trước tải; tệp hết hạn cần tạo lại.')
add('09','Phiên bản quy định',headers=['Phiên bản','Trạng thái','Hiệu lực','Người duyệt'],rows=[['QD-2026-01','ACTIVE · Chỉ đọc','01/10/2026','Quản lý B'],['QD-2026-02','DRAFT','Chưa áp dụng','—']],action='Tạo bản nháp')
add('09','Quy định — bản nháp và so sánh','policy')
add('10','Tài khoản hệ thống',headers=['Tài khoản','Độc giả liên kết','Vai trò','Trạng thái','Thao tác'],rows=[['minhan','DG-001','Độc giả','ACTIVE','Chi tiết'],['thuthu.a','—','Thủ thư','ACTIVE','Khóa'],['quanly.b','—','Quản lý','ACTIVE','Chi tiết'],['account.demo','DG-003','Độc giả','LOCKED','Mở khóa']],action='Cấp / liên kết tài khoản')
add('10','Vai trò và phân quyền','permissions')
add('10','Phiếu nhập sách',headers=['Số phiếu','Ngày lập','Người lập','Số mục','Trạng thái'],rows=[['PN-084','19/10/2026','Thủ thư A','2','DRAFT'],['PN-083','18/10/2026','Thủ thư A','3','POSTED']],action='Lập phiếu nhập')
add('10','Lập phiếu nhập nhiều ấn bản','acquisition')
add('10','Duyệt và ghi nhận nhập kho','acquisition',approval=True)
add('10','Biên nhận nhập kho','receipt',receipt='PN-083',items=[['Bến không chồng','BC-0184-06 → 08','3 bản sách'],['Dế Mèn phiêu lưu ký','BC-0321-07 → 08','2 bản sách']],note='POSTED · Chỉ đọc. Người lập: Thủ thư A. Người duyệt: Quản lý B.')
add('10','Thanh lý bản sách',headers=['Barcode','Ấn bản','Tình trạng','Điều kiện','Thao tác'],rows=[['BC-0184-03','Bến không chồng','Hỏng','Không còn khoản mượn','Chọn'],['BC-0207-01','Mùa lá rụng','Tốt','Đang mượn · Chặn','Không khả dụng']],action='Đề nghị thanh lý')
add('10','Xác nhận tác động thanh lý','form',fields=[('Bản sách','BC-0184-03 · Bến không chồng'),('Kiểm tra khoản mượn','Không có khoản mượn đang mở'),('Kiểm tra giữ chỗ','Không có giữ chỗ liên quan'),('Lý do bắt buộc','Hư hỏng không thể sửa chữa')],action='Xác nhận thanh lý',note='Quản lý thực hiện theo quyền. Ghi lại lịch sử; chặn nếu đang mượn hoặc có giữ chỗ.')
add('11','Tác vụ nền',headers=['Mã tác vụ','Loại','Trạng thái','Lần thử','Lần thử tiếp'],rows=JOBS,action='Xem chi tiết')
add('11','Chi tiết tác vụ JOB-119','job')
add('11','Tác vụ lỗi và chạy lại',headers=['Tác vụ','Loại','Lần thử','Lỗi đã lọc','Thao tác'],rows=[['JOB-117','Email','5','Không thể kết nối nhà cung cấp','Xem / Chạy lại']],action='Xem điều kiện chạy lại',note='Xác nhận trước replay; kiểm tra quyền và loại job cho phép. Không hiển thị secrets.')
add('11','Sao lưu dữ liệu',headers=['Mã bản sao','Thời điểm','Kích thước','Trạng thái','Kiểm chứng'],rows=[['BKUP-019','19/10/2026 02:00','248 MB','Hoàn tất','Checksum hợp lệ'],['BKUP-018','18/10/2026 02:00','245 MB','Hoàn tất','Checksum hợp lệ']],action='Tạo bản sao lưu')
add('11','Chi tiết bản sao lưu','backup')
add('11','Yêu cầu khôi phục cô lập','form',fields=[('Bản sao lưu','BKUP-019'),('Target cho phép','restore-sandbox-01'),('Checksum','SHA-256 · Khớp manifest'),('Lý do bắt buộc','Diễn tập kiểm tra khả năng khôi phục')],action='Gửi đề nghị duyệt',note='Chỉ target cô lập trong allowlist. Không ghi đè hoặc tự chuyển sang DB đang phục vụ.')
add('11','Duyệt và kết quả khôi phục','restore')
add('11','Nhật ký kiểm toán',headers=['Thời điểm','Người thực hiện','Hành động','Đối tượng','Kết quả'],rows=[['19/10 10:20','Admin vận hành','Duyệt khôi phục','RST-019','Chờ chạy'],['19/10 10:10','Admin vận hành','Đề nghị khôi phục','RST-019','PENDING'],['19/10 09:30','Admin hệ thống','Khóa tài khoản','account.demo','Thành công']])

NAMES={'01':'Xác thực','02':'Danh mục','03':'Độc giả & thẻ','04':'Mượn sách','05':'Trả sách','06':'Giữ chỗ & gia hạn','07':'Tài chính','08':'Portal độc giả','09':'Báo cáo & quy định','10':'Quản trị & kho','11':'Vận hành'}
def shell(s,m=False):
    if m:
        nav=['Tìm sách','Của tôi','Thông báo'] if s['group'] in ('02','08') else ['Tác nghiệp','Độc giả','Danh mục']
        return rect(0,0,390,844,'bg')+rect(0,0,390,72)+text(20,43,'LIB / THƯ VIỆN',18,'blue',True)+text(337,43,'≡',24,'blue')+lines(20,106,s['name'],29,21,'ink',26)+rect(0,780,390,64)+text(25,817,nav[0],13,'blue',True)+text(150,817,nav[1],13,'blue')+text(270,817,nav[2],13,'blue')
    a=rect(0,0,1440,1024,'bg')+rect(0,0,232,1024,'nav')+text(24,48,'LIB / MANAGEMENT',17,'white',True)+text(24,73,'THƯ VIỆN ĐƯƠNG ĐẠI',10,'#AFC2C8',True)+rect(232,0,1208,72)
    a+=text(270,43,'Không gian làm việc',14,'muted')+text(1165,43,'19/10/2026',13,'muted')+badge(1290,22,'Nhân viên','blue')
    for i,(g,n) in enumerate(NAMES.items()):
        y=118+i*54
        if g==s['group']:a+=rect(12,y-27,208,44,'#234650',8)+rect(12,y-20,3,30,'#A5C6D4',1)
        a+=text(27,y,n,14,'white' if g==s['group'] else '#BACBD0',g==s['group'])
    a+=text(24,940,'THỦ THƯ A',11,'#BACBD0',True)+text(24,965,'Phiên làm việc hiện tại',11,'#BACBD0')
    a+=text(272,112,'Thư viện  /  '+NAMES[s['group']],12,'muted')+text(272,162,s['name'],32,'ink',True,True)+text(272,193,'Dữ liệu minh họa · Mọi thao tác phụ thuộc quyền hiện tại',12,'muted')
    a+=text(272,994,'LIB-MANAGEMENT  /  '+s.get('id',''),11,'muted')+text(1140,994,'BẢN THIẾT KẾ · 19.10.2026',10,'muted')
    return a
def content(s):
    k=s['kind'];a='';x=272;y=228;w=1128
    if k=='auth':
        a+=panel(510,274,620,460,'Một tài khoản. Cả thư viện.')+text(550,384,s['name'],24,'ink',True,True)+lines(550,430,s['desc'],60,16)+btn(550,535,s['action'],True,420)+text(550,625,'Cần hỗ trợ? Liên hệ nhân viên thư viện.',13,'muted')
    elif k=='list':
        a+=field(x,y+12,'Tìm kiếm','Tên, mã hoặc nội dung liên quan',560)+btn(850,y+23,'Bộ lọc',False,140)+btn(1110,y+23,s.get('action','Xem chi tiết'),True,280)
        a+=table(x,y+100,w,s['headers'],s['rows'])
        end=y+144+58*len(s['rows'])
        if s.get('mini'):
            a+=panel(x,end+32,w,220,'Thông tin danh mục')
            for i,(l,v) in enumerate(s['mini']):a+=field(x+24+i*550,end+116,l,v,515)
            a+=btn(x+24,end+185,'Lưu thông tin',True,180)
        else:a+=text(x,end+35,f"Hiển thị {len(s['rows'])} mục",12,'muted')+btn(1170,end+16,'Trang trước',False,110)+btn(1290,end+16,'Sau',False,100)
        if s.get('note'):a+=lines(x,end+100,s['note'],110)
    elif k=='form':
        a+=panel(x,y,w,550,'Thông tin cần ghi nhận','Các trường bắt buộc được kiểm tra trước khi xác nhận.')
        for i,(l,v) in enumerate(s['fields']):a+=field(x+24+(i%2)*550,y+110+(i//2)*105,l,v,515)
        a+=btn(x+24,y+470,s.get('action','Lưu thông tin'),True,310)+btn(x+350,y+470,'Hủy',False,120)
        a+=lines(x+24,y+600,s.get('note','Lỗi cạnh trường · Lưu không thành công giữ nguyên nội dung · Xung đột cần tải lại bản mới.'),105)
    elif k in ('catalog','book'):
        if k=='catalog':
            a+=field(x,y+12,'Tìm sách','Tên sách, tác giả, thể loại…',760)+btn(1060,y+23,'Thể loại ▾',False,160)+btn(1230,y+23,'Sẵn có ▾',False,160)
            for i,b in enumerate(BOOKS):
                xx=x+i*286;yy=y+116;a+=rect(xx,yy,252,340,['#DDC7A6','#C7D4CA','#D5A381','#A9BFD0'][i],4)+text(xx+24,yy+42,'ẤN BẢN / '+b[3],11,'nav',True)
                a+=lines(xx+24,yy+134,b[1],20,25,'nav',34)+text(xx+24,yy+298,b[2],14,'nav')+text(xx,yy+375,b[1][:28],16,'ink',True)+text(xx,yy+404,b[2],13,'muted')+badge(xx,yy+423,b[4]+' bản khả dụng','green' if i!=2 else 'amber')
        else:
            a+=rect(x,y,270,390,'#DDC7A6',6)+text(x+28,y+50,'DƯƠNG HƯỚNG',15,'nav')+lines(x+28,y+150,'Bến không chồng',15,34,'nav',45)+text(x+28,y+344,'ẤN BẢN 2023',13,'nav')
            a+=text(x+320,y+40,'Bến không chồng',32,'ink',True,True)+text(x+320,y+80,'Dương Hướng  ·  NXB Trẻ  ·  2023',16,'muted')+badge(x+320,y+110,'3 bản sẵn có','green')+lines(x+320,y+180,'Một ấn bản văn học Việt Nam trong danh mục thư viện. Xem thông tin bản sách và điều kiện đặt trước ở bên dưới.',75,16)
            a+=btn(x+320,y+285,'Đặt trước ấn bản',True,245)+table(x,y+450,w,['Barcode','Tình trạng','Khả dụng'],[['BC-0184-01','Tốt','Sẵn có'],['BC-0184-02','Tốt','Đang mượn']])
    elif k=='tree':
        a+=panel(x,y,530,560,'Cây thể loại')
        for i,(n,ind) in enumerate([('Văn học',0),('Văn học Việt Nam',1),('Tiểu thuyết',2),('Thiếu nhi',0),('Khoa học & công nghệ',0)]):a+=rect(x+24,y+80+i*68,482,52,'bg',6)+text(x+44+ind*26,y+112+i*68,('▾ ' if ind<2 else '— ')+n,15,'blue',True)
        a+=panel(830,y,570,560,'Thông tin thể loại')+field(854,y+110,'Tên thể loại','Văn học Việt Nam',520)+field(854,y+215,'Thể loại cha','Văn học',520)+field(854,y+320,'Mô tả','Sách văn học Việt Nam',520)+btn(854,y+430,'Lưu thể loại',True,200)
    elif k=='upload':
        a+=panel(x,y,w,580,'Bìa sách — Bến không chồng')+rect(x+30,y+90,330,440,'#DDC7A6',8)+text(x+54,y+200,'Bến không chồng',24,'nav',True,True)+panel(x+400,y+90,690,250,'Kéo ảnh vào đây hoặc chọn tệp','Xem trước ảnh bìa trước khi lưu.')+btn(x+430,y+210,'Chọn ảnh',False,180)+btn(x+430,y+410,'Lưu ảnh bìa',True,220)+lines(x+430,y+320,'Lỗi loại tệp hoặc dung lượng hiển thị tại đây. Giữ ảnh cũ nếu tải lên không thành công.',60)
    elif k in ('profile','ownprofile'):
        a+=panel(x,y,w,150,'Nguyễn Minh An','DG-001 · Tài khoản độc giả đã liên kết')+badge(x+30,y+95,'Thẻ còn hiệu lực')+text(x+350,y+115,'Dư nợ: 0 ₫',17,'green',True)+text(x+650,y+115,'Không có phí chờ duyệt',14,'muted')
        a+=text(x,y+205,'Cá nhân     Thẻ     Đang mượn     Giữ chỗ     Tài chính     Lịch sử',15,'blue',True)+table(x,y+245,w,['Thông tin','Giá trị'],[['Họ tên','Nguyễn Minh An'],['Email','an@example.com'],['Loại độc giả','Sinh viên'],['Tình trạng thẻ','Còn hiệu lực · theo hồ sơ cấp thẻ']])
    elif k=='checkout':
        for i,n in enumerate(['1  Xác định độc giả','2  Chọn sách','3  Xác nhận','4  Biên nhận']):a+=badge(x+i*284,y,n,'blue' if i<=1 else 'green')
        a+=panel(x,y+60,760,160,'Độc giả')+field(x+24,y+155,'Quét thẻ / tìm độc giả','DG-001 · Nguyễn Minh An',700)
        a+=panel(x,y+244,760,370,'Chọn sách để mượn','Tối đa 4 cuốn mỗi phiếu · Barcode không trùng')+field(x+24,y+350,'Quét barcode','BC-0184-01',700)+table(x+24,y+430,712,['Barcode','Tên sách','Hạn trả'],[['BC-0184-01','Bến không chồng','23/10/2026'],['BC-0207-02','Mùa lá rụng','23/10/2026']])
        a+=panel(x+784,y+60,344,554,'Điều kiện mượn')+text(x+808,y+157,'Nguyễn Minh An',20,'ink',True)+badge(x+808,y+185,'Chưa đủ điều kiện' if s.get('blocked') else 'Đủ điều kiện','amber' if s.get('blocked') else 'green')
        for i,t in enumerate(['Thẻ: Còn hiệu lực','Dư nợ: '+('12.000 ₫' if s.get('blocked') else '0 ₫'),'Phí chờ duyệt: Không','Đã chọn: 2 / 4 cuốn','Hạn trả: 23/10/2026']):a+=text(x+808,y+265+i*42,t,14,'ink')
        a+=btn(x+808,y+510,'Xem lại phiếu mượn',True,296)
        if s.get('conflict'):a+=rect(x,y+640,w,68,'#FCEDEA',8)+text(x+20,y+680,'BC-0184-01 vừa hết khả dụng. Danh sách đã quét được giữ lại để bạn sửa.',15,'red',True)
    elif k in ('loan','ownloans','renew'):
        a+=panel(x,y,w,130,'PM-1024 · Nguyễn Minh An','Ngày mượn: 19/10/2026  ·  Hạn trả hiện tại: 23/10/2026')+badge(x+30,y+88,'2 khoản đang mở','blue')
        a+=table(x,y+165,w,['Barcode','Nhan đề','Hạn hiện tại','Hạn sau gia hạn' if k=='renew' else 'Tình trạng'],[['BC-0184-02','Bến không chồng','23/10/2026','27/10/2026' if k=='renew' else 'Đang mượn'],['BC-0207-01','Mùa lá rụng','23/10/2026','27/10/2026' if k=='renew' else 'Đang mượn']])
        if k=='renew':a+=lines(x,y+400,'Gia hạn toàn bộ khoản OPEN. Tối đa 1 lần, thêm 4 ngày từ hạn cũ. Nếu một mục không hợp lệ, không thay đổi hạn của bất kỳ mục nào.',110,16)+btn(x,y+500,'Xác nhận gia hạn tất cả',True,290)
        elif k=='loan':a+=btn(x,y+400,'Nhận trả sách',True,200)+btn(x+220,y+400,'Xem trước gia hạn',False,230)
    elif k=='returns':
        a+=field(x,y+12,'Quét barcode / tìm khoản mượn','BC-0184-02 · PM-1024',760)+btn(x+790,y+24,'Tra cứu',True,200)+panel(x,y+110,w,410,'Bến không chồng','Nguyễn Minh An · Hạn trả 23/10/2026')
        for i,(t,c) in enumerate([('Tốt','green'),('Hỏng','amber'),('Mất','red')]):a+=badge(x+24+i*180,y+215,t,c)
        a+=field(x+24,y+310,'Số tiền đề xuất (nếu hỏng / mất)','Chờ nhập theo đánh giá thực tế',510)+field(x+570,y+310,'Lý do','Bắt buộc khi đề xuất phí',530)+text(x+24,y+420,'Phí quá hạn dự kiến: 0 ₫  ·  Phí hỏng/mất: chờ xác nhận',15,'muted')+btn(x+24,y+455,'Ghi nhận trả sách',True,260)+lines(x,y+580,'Nhận trả dù có nợ, thẻ hết hạn hoặc phí chờ duyệt. Thu tiền là bước riêng; chưa ghi phí hỏng/mất khi chưa được Quản lý xác nhận.',110,16)
    elif k=='receipt':
        a+=panel(430,y,800,650,'Đã ghi nhận thành công',s.get('receipt','Biên nhận'))+badge(462,y+90,'Hoàn tất')+text(462,y+160,'Nguyễn Minh An · DG-001',20,'ink',True)+table(462,y+195,736,['Đối tượng','Chi tiết','Kết quả'],s['items'])+lines(462,y+440,s['note'],79,15)+btn(462,y+550,'In biên nhận',True,200)+btn(682,y+550,'Tiếp tục',False,160)
    elif k in ('hold','ownholds'):
        a+=panel(x,y,w,160,'DC-207 · Bến không chồng','Lê Thu Hương · READY từ 19/10/2026 10:00')+badge(x+24,y+100,'Đã hết hạn' if s.get('expired') else 'Sẵn sàng nhận','red' if s.get('expired') else 'green')+text(x+420,y+120,'Hạn nhận: 22/10/2026 10:00',17,'amber',True)
        for i,(t,d) in enumerate([('Đặt trước','18/10/2026 09:00'),('Sẵn sàng','19/10/2026 10:00'),('Nhận tại quầy','Trước hạn nhận được hiển thị')]):a+=badge(x,y+220+i*90,str(i+1),'blue')+text(x+120,y+241+i*90,t,18,'ink',True)+text(x+410,y+241+i*90,d,15,'muted')
        a+=btn(x,y+540,'Xác nhận nhận sách' if k=='hold' else 'Hủy đặt trước',True,270)+btn(x+290,y+540,'Hủy giữ chỗ' if k=='hold' else 'Tìm sách khác',False,210)+text(x,y+630,'READY hết hạn sau 3 ngày từ readyAt, không phụ thuộc email.',14,'muted')
    elif k in ('finance','ownfinance'):
        a+=panel(x,y,w,130,'Trần Hà Linh · DG-002','Phí đã ghi nhận khác với đề xuất đang chờ duyệt.')+text(x+30,y+95,'Còn phải thu: 12.000 ₫',25,'accent',True,True)+badge(x+750,y+64,'Thẻ còn hiệu lực','green')+table(x,y+170,w,['Khoản phí','Loại','Gốc','Đã thu','Đã miễn','Còn phải thu'],LEDGER)+text(x,y+410,'Đề xuất hỏng/mất chưa xác nhận không cộng vào dư nợ.',14,'muted')
        if k=='finance':a+=btn(x,y+465,'Thu tiền',True,180)+btn(x+200,y+465,'Xem lịch sử',False,200)
    elif k=='payment':
        a+=panel(x,y,w,155,'Thu tiền — Trần Hà Linh','Tổng còn phải thu: 12.000 ₫')+field(x+24,y+110,'Số tiền nhận','8.000 ₫',520)+table(x,y+195,w,['Khoản phí','Còn phải thu','Phân bổ lần này'],[['PH-091 · Quá hạn','12.000 ₫','8.000 ₫']])+text(x,y+360,'Còn lại sau thu: 4.000 ₫',24,'accent',True,True)+btn(x,y+420,'Xem lại & thu tiền',True,270)+lines(x,y+510,'Kiểm tra tổng phân bổ bằng số tiền nhận. Biên nhận hiển thị sau khi ghi nhận thành công.',100)
    elif k=='assessment':
        a+=panel(x,y,w,200,'DGPH-021 · Bản sách hỏng','Phạm Khánh Vy · BC-0207-01 · Đề xuất bởi Thủ thư A')+badge(x+24,y+100,'Chờ xác nhận','amber')+text(x+24,y+162,'Đề xuất: 80.000 ₫  ·  Lý do: Bìa rách, cần sửa chữa',17,'ink')+field(x,y+255,'Số tiền Quản lý xác nhận','80.000 ₫',530)+field(x+570,y+255,'Lý do quyết định','Đánh giá chi phí sửa chữa thực tế',550)+btn(x,y+380,'Xác nhận ghi phí',True,240)+btn(x+260,y+380,'Kết thúc không thu',False,260)+lines(x,y+490,'Chỉ Quản lý quyết định. Người xác nhận và thời điểm do hệ thống ghi; form xung đột giữ lại nội dung để đối chiếu.',110,16)
    elif k=='portal':
        a+=text(x,y+35,'Chào An, hôm nay bạn đọc gì?',28,'ink',True,True)+panel(x,y+80,550,200,'2 cuốn đang mượn','Hạn gần nhất: 23/10/2026')+btn(x+24,y+190,'Xem sách đang mượn',True,260)+panel(x+578,y+80,550,200,'Đặt trước của bạn','DC-208 · Đang chờ · Vị trí 2')+btn(x+602,y+190,'Xem giữ chỗ',False,220)+panel(x,y+310,w,150,'Thẻ thư viện','Còn hiệu lực · Dư nợ: 0 ₫ · Không có phí chờ xác nhận')+btn(x,y+510,'Khám phá danh mục',True,260)
    elif k=='history':a+=table(x,y,w,['Ngày','Sự kiện','Đối tượng','Kết quả'],[['19/10/2026','Mượn sách','PM-1024','2 cuốn'],['18/10/2026','Thanh toán','TT-082','4.000 ₫'],['17/10/2026','Trả sách','PT-1002','Hoàn tất']])
    elif k=='notifications':
        a+=text(x,y+20,'Tất cả     Chưa đọc     Đã đọc',15,'blue',True)
        for i,(t,d) in enumerate([('Sách đã sẵn sàng để nhận','Bến không chồng · Nhận trước 22/10/2026 10:00'),('Nhắc hạn trả sách','PM-1024 · Hạn trả 23/10/2026'),('Đã ghi nhận thanh toán','Biên nhận TT-082 · 4.000 ₫')]):a+=panel(x,y+55+i*165,w,145,t,d)+btn(x+850,y+115+i*165,'Đánh dấu đã đọc',False,240)
    elif k=='preferences':a+=panel(x,y,w,300,'Thông báo qua email','Bạn có thể thay đổi lựa chọn nhận email bất kỳ lúc nào.')+badge(x+24,y+110,'Đã đồng ý','green')+text(x+24,y+180,'Nhắc quá hạn và thông báo sách sẵn sàng theo lựa chọn của bạn.',16,'ink')+btn(x+24,y+220,'Lưu lựa chọn',True,220)
    elif k=='reports':
        a+=field(x,y+8,'Khoảng thời gian','01/10/2026 — 19/10/2026',590)+btn(x+620,y+20,'Áp dụng',True,180)+btn(x+820,y+20,'Yêu cầu CSV',False,280)
        for i,(n,v) in enumerate([('Phiếu mượn trong kỳ','128'),('Lượt trả trong kỳ','106'),('Khoản mượn quá hạn','12')]):a+=panel(x+i*384,y+110,360,130,n)+text(x+24+i*384,y+205,v,36,'blue',True,True)
        a+=panel(x,y+270,w,230,'Mượn và trả theo tuần')
        for i,h in enumerate([65,100,80,120,95,130,100]):a+=rect(x+60+i*140,y+460-h,40,h,'blue',4)+rect(x+106+i*140,y+460-h*.8,30,h*.8,'#9B4B2F',4)
        a+=table(x,y+530,w,['Kỳ','Phiếu mượn','Lượt trả','Quá hạn'],[['Tuần 1','40','35','3'],['Tuần 2','48','39','4'],['Tuần 3','40','32','5']])
    elif k=='policy':
        a+=panel(x,y,w,110,'Bản nháp quy định · Chưa có hiệu lực','Đối chiếu trước / sau trước khi duyệt phiên bản mới.')
        vals=[['Số cuốn tối đa / phiếu','4','4'],['Hạn mượn ban đầu','4 ngày','4 ngày'],['Số lần gia hạn','1 lần','1 lần'],['Thời gian gia hạn','4 ngày từ hạn cũ','4 ngày từ hạn cũ'],['Phí quá hạn','1.000 ₫ / ngày / cuốn','1.000 ₫ / ngày / cuốn'],['Hạn nhận READY','3 ngày từ readyAt','3 ngày từ readyAt']]
        a+=table(x,y+135,w,['Quy định','Hiện hành','Bản nháp'],vals)+field(x,y+575,'Có hiệu lực từ','Chọn sau khi xác nhận',530)+btn(x+620,y+593,'Xem lại & duyệt',True,260)
    elif k=='permissions':
        a+=table(x,y,w,['Quyền','Độc giả','Thủ thư','Quản lý','Admin HT','Admin VH'],[['Xem danh mục','Có','Có','Có','Có','Có'],['Nhận trả sách','—','Có','Cấp rõ','—','—'],['Xác nhận phí','—','—','Có','—','—'],['Xuất CSV','—','—','Có','—','—'],['Quản lý tài khoản','—','—','—','Có','—'],['Khôi phục dữ liệu','—','—','—','—','Có']])+btn(x,y+470,'Xem thay đổi trước khi lưu',True,330)+lines(x,y+560,'Vai trò là tập quyền độc lập. Admin hệ thống không tự có quyền thu tiền, duyệt phí hoặc khôi phục dữ liệu.',110,16)
    elif k=='acquisition':
        a+=panel(x,y,w,120,'PN-084 · '+('Chờ Quản lý duyệt' if s.get('approval') else 'Bản nháp'),'Người lập: Thủ thư A · Ngày lập 19/10/2026')+table(x,y+155,w,['Ấn bản','Số lượng','Barcode dự kiến','Kết quả kiểm tra'],[['Bến không chồng','3','BC-0184-06 → 08','Hợp lệ'],['Dế Mèn phiêu lưu ký','2','BC-0321-07 → 08','Hợp lệ']])+btn(x,y+380,'Duyệt & ghi nhận nhập kho' if s.get('approval') else 'Thêm ấn bản',True,330)+btn(x+350,y+380,'Trả lại bản nháp' if s.get('approval') else 'Gửi duyệt',False,260)+lines(x,y+490,'Không tạo tồn một phần khi có barcode xung đột. Phiếu đã POSTED chỉ đọc và có người duyệt trong lịch sử.',110,16)
    elif k in ('job','backup','restore'):
        title={'job':'JOB-119 · Thông báo email','backup':'BKUP-019 · Bản sao lưu','restore':'RST-019 · Khôi phục cô lập'}[k]
        a+=panel(x,y,w,170,title)+badge(x+24,y+90,'Chờ duyệt' if k=='restore' else 'Hoàn tất' if k=='backup' else 'Chờ thử lại','amber' if k!='backup' else 'green')
        rows={'job':[['Loại tác vụ','Gửi email'],['Lần thử','2'],['Lần thử tiếp','19/10/2026 08:10'],['Lỗi đã lọc','Không thể kết nối nhà cung cấp']], 'backup':[['Thời điểm','19/10/2026 02:00'],['Kích thước','248 MB'],['Manifest','BKUP-019.manifest.json'],['Checksum','SHA-256 · Đã đối chiếu']], 'restore':[['Target','restore-sandbox-01'],['Bản sao','BKUP-019 · Checksum hợp lệ'],['Phê duyệt','PENDING · Chưa chạy'],['Lý do','Diễn tập khôi phục']]}[k]
        a+=table(x,y+205,w,['Thuộc tính','Giá trị'],rows)+btn(x,y+530,'Duyệt chạy trên target cô lập' if k=='restore' else 'Xem manifest' if k=='backup' else 'Xem lịch sử thử lại',True,350)+lines(x,y+620,'Không có phần trăm tiến độ giả. Kết quả và lỗi hiển thị theo trạng thái tác vụ; không lộ secrets.',110,15)
    else:raise ValueError(k)
    return a

def mobile(s):
    a=shell(s,True);x=20;y=160;w=350;k=s['kind']
    if k=='catalog':
        a+=field(x,y,'Tìm sách','Tên sách, tác giả…',350)
        for i,b in enumerate(BOOKS):
            xx=20+(i%2)*182;yy=235+(i//2)*245;a+=rect(xx,yy,168,176,['#DDC7A6','#C7D4CA','#D5A381','#A9BFD0'][i],6)+lines(xx+14,yy+58,b[1],15,19,'nav',26)+text(xx,yy+200,b[2],12,'muted')+text(xx,yy+222,b[4]+' bản khả dụng',12,'green')
    elif k in ('checkout','returns','renew','payment','assessment','acquisition','restore'):
        a+=badge(x,y,'Đang thực hiện','blue')+panel(x,y+48,w,140,'Nguyễn Minh An' if k in ('checkout','returns','renew') else s['name'][:25],'Thông tin được giữ khi chuyển bước')
        pairs={'checkout':[('Thẻ độc giả','DG-001 · Còn hiệu lực'),('Barcode','BC-0184-01'),('Sách đã chọn','2 / 4 cuốn'),('Hạn trả','23/10/2026')],'returns':[('Khoản mượn','PM-1024 · BC-0184-02'),('Tình trạng','Hỏng'),('Phí đề xuất','80.000 ₫'),('Lý do','Bìa rách, cần sửa chữa')],'renew':[('Phiếu mượn','PM-1024 · 2 khoản OPEN'),('Hạn cũ','23/10/2026'),('Hạn mới','27/10/2026'),('Lần gia hạn','1 / 1')],'payment':[('Độc giả','Trần Hà Linh'),('Còn phải thu','12.000 ₫'),('Số tiền nhận','8.000 ₫'),('Còn lại','4.000 ₫')],'assessment':[('Đề xuất','DGPH-021 · Hỏng'),('Số tiền đề xuất','80.000 ₫'),('Số tiền xác nhận','80.000 ₫'),('Lý do','Chi phí sửa chữa thực tế')],'acquisition':[('Phiếu nhập','PN-084 · DRAFT'),('Ấn bản','Bến không chồng'),('Số lượng','3 bản'),('Barcode','BC-0184-06 → 08')],'restore':[('Bản sao','BKUP-019'),('Target cô lập','restore-sandbox-01'),('Checksum','Đã đối chiếu'),('Trạng thái','Chờ duyệt')]}[k]
        for i,(l,v) in enumerate(pairs):a+=field(x,y+220+i*88,l,v,350)
        a+=btn(x,720,'Xem lại & tiếp tục',True,350)
    elif k=='auth':a+=panel(x,y+70,w,370,'Thư viện của bạn')+lines(x+20,y+150,s['desc'],33,16)+btn(x+20,y+300,s['action'],True,310)
    elif k=='form':
        for i,(l,v) in enumerate(s['fields'][:5]):a+=field(x,y+20+i*100,l,v,350)
        a+=btn(x,710,s.get('action','Lưu thông tin')[:30],True,350)
    elif k=='preferences':a+=panel(x,y,w,260,'Email thông báo')+lines(x+20,y+80,'Bạn tự chọn đồng ý nhận nhắc quá hạn và thông báo sẵn sàng nhận sách.',32,16)+badge(x+20,y+170,'Đã đồng ý')+btn(x,y+310,'Lưu lựa chọn',True,350)
    elif k=='notifications':
        for i,(t,d) in enumerate([('Sách sẵn sàng nhận','Hạn nhận: 22/10/2026 10:00'),('Nhắc hạn trả','PM-1024 · 23/10/2026'),('Đã ghi nhận thanh toán','TT-082 · 4.000 ₫')]):a+=panel(x,y+i*180,w,155,t,d)+text(x+24,y+116+i*180,'Xem chi tiết →',14,'blue',True)
    elif k in ('finance','ownfinance'):
        a+=panel(x,y,w,150,'Còn phải thu')+text(x+24,y+100,'12.000 ₫',34,'accent',True,True)
        for i,row in enumerate(LEDGER):a+=panel(x,y+180+i*170,w,145,row[0]+' · '+row[1], 'Gốc: '+row[2]+' · Đã thu: '+row[3])+text(x+24,y+280+i*170,'Còn: '+row[-1],18,'blue',True)
    elif k=='portal':
        a+=text(x,y+20,'Chào An, hôm nay bạn đọc gì?',20,'ink',True,True)
        for i,(t,d) in enumerate([('2 cuốn đang mượn','Hạn gần nhất: 23/10/2026'),('Đặt trước DC-208','Đang chờ · Vị trí 2'),('Thẻ thư viện','Còn hiệu lực · Dư nợ 0 ₫')]):a+=panel(x,y+55+i*175,w,150,t,d)+text(x+24,y+165+i*175,'Xem chi tiết →',14,'blue',True)
    elif k in ('profile','ownprofile'):a+=panel(x,y,w,155,'Nguyễn Minh An','DG-001 · Sinh viên')+badge(x+24,y+100,'Thẻ còn hiệu lực')+table(x,y+190,w,['Thông tin','Giá trị'],[['Email','an@example.com'],['Dư nợ','0 ₫'],['Đang mượn','2 cuốn']])
    elif k in ('ownloans','loan','renew','ownholds','hold'):
        for i,b in enumerate(BOOKS[:2]):a+=panel(x,y+i*245,w,220,b[1][:24],b[2])+text(x+24,y+115+i*245,'Hạn trả: 23/10/2026' if k not in ('hold','ownholds') else 'READY · Nhận trước 22/10/2026',14,'amber',True)+btn(x+24,y+145+i*245,'Xem chi tiết',False,300)
    elif k=='book':
        a+=rect(x,y,128,185,'#DDC7A6',6)+lines(x+14,y+65,'Bến không chồng',11,20,'nav',27)+text(170,y+35,'Dương Hướng',17,'ink',True)+text(170,y+70,'NXB Trẻ · 2023',13,'muted')+badge(170,y+100,'3 bản sẵn có')+btn(x,y+220,'Đặt trước ấn bản',True,350)+table(x,y+300,w,['Barcode','Lưu thông'],[['BC-0184-01','Sẵn có'],['BC-0184-02','Đang mượn']])
    elif k=='tree':
        for i,(t,indent) in enumerate([('Văn học',0),('Văn học Việt Nam',1),('Tiểu thuyết',2),('Thiếu nhi',0)]):a+=rect(x,y+i*62,w,54,'white',6,'border')+text(x+16+indent*18,y+34+i*62,t,15,'blue',True)
        a+=field(x,y+290,'Tên thể loại','Văn học Việt Nam',350)+field(x,y+380,'Thể loại cha','Văn học',350)+btn(x,y+480,'Lưu thể loại',True,350)
    elif k=='upload':a+=rect(x,y,w,280,'#DDC7A6',8)+text(x+30,y+130,'Bến không chồng',27,'nav',True,True)+btn(x,y+320,'Chọn ảnh bìa',False,350)+lines(x,y+410,'Xem trước ảnh đã chọn. Lỗi loại tệp và dung lượng hiển thị cạnh vùng tải ảnh.',34,15)+btn(x,y+500,'Lưu ảnh bìa',True,350)
    elif k=='receipt':
        a+=badge(x,y,'Đã ghi nhận thành công')+text(x,y+80,s.get('receipt','Biên nhận'),28,'blue',True,True)
        for i,row in enumerate(s['items']):a+=panel(x,y+120+i*155,w,135,row[0][:25],row[1][:40])+text(x+24,y+217+i*155,row[2][:35],13,'green',True)
        a+=lines(x,y+465,s['note'],36,14)+btn(x,720,'In biên nhận',True,350)
    elif k=='history':a+=table(x,y,w,['Ngày','Sự kiện','Kết quả'],[['19/10','Mượn PM-1024','2 cuốn'],['18/10','Thu TT-082','4.000 ₫'],['17/10','Trả PT-1002','Hoàn tất']])
    elif k=='reports':
        a+=field(x,y,'Khoảng thời gian','01/10 — 19/10/2026',350)+panel(x,y+95,w,130,'128 phiếu mượn','106 lượt trả · 12 khoản quá hạn')
        for i,h in enumerate([75,110,90,130]):a+=rect(x+28+i*80,y+410-h,28,h,'blue',3)+rect(x+60+i*80,y+410-h*.8,20,h*.8,'accent',3)
        a+=table(x,y+455,w,['Tuần','Mượn','Trả'],[['1','40','35'],['2','48','39']])+btn(x,720,'Yêu cầu CSV',True,350)
    elif k=='policy':
        a+=badge(x,y,'DRAFT · Chưa áp dụng','amber')
        for i,(l,v) in enumerate([('Tối đa mỗi phiếu','4 cuốn'),('Thời hạn mượn','4 ngày'),('Gia hạn','1 lần · thêm 4 ngày'),('Phí quá hạn','1.000 ₫ / ngày / cuốn'),('Hạn nhận READY','3 ngày từ readyAt')]):a+=text(x,y+75+i*90,l,13,'muted')+text(x,y+107+i*90,v,18,'blue',True)
        a+=btn(x,720,'Xem so sánh & duyệt',True,350)
    elif k=='permissions':
        a+=badge(x,y,'Vai trò: Quản lý','blue')
        for i,(n,v) in enumerate([('Xem danh mục','Có'),('Xác nhận phí','Có'),('Xuất CSV','Có'),('Quản lý tài khoản','Không'),('Khôi phục dữ liệu','Không')]):a+=rect(x,y+60+i*85,w,74,'white',6,'border')+text(x+16,y+91+i*85,n,15,'ink',True)+text(x+16,y+116+i*85,v,13,'blue')
        a+=btn(x,720,'Xem thay đổi',True,350)
    elif k in ('job','backup'):
        pairs=([('Mã tác vụ','JOB-119'),('Loại','Thông báo email'),('Trạng thái','Chờ thử lại'),('Lần thử','2'),('Lần thử tiếp','19/10/2026 08:10')] if k=='job' else [('Bản sao','BKUP-019'),('Thời điểm','19/10/2026 02:00'),('Kích thước','248 MB'),('Checksum','Đã đối chiếu'),('Manifest','BKUP-019.manifest.json')])
        for i,(l,v) in enumerate(pairs):a+=text(x,y+24+i*92,l,13,'muted')+text(x,y+55+i*92,v,18,'blue',True)
        a+=btn(x,720,'Xem lịch sử' if k=='job' else 'Xem manifest',True,350)
    else:
        # Specific rows are preserved as mobile stacked records, never an unrelated generic list.
        if s.get('rows'):
            for i,row in enumerate(s['rows'][:3]):
                yy=y+i*188;a+=panel(x,yy,w,170,row[0])
                for j,v in enumerate(row[1:4]):a+=text(x+24,yy+70+j*27,s['headers'][j+1]+': '+v,13,'muted')
        else:raise ValueError('Missing mobile content: '+k)
    return a

def svg(body,w,h):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'
boards=[]
for g in NAMES:
    items=[s for s in S if s['group']==g]
    body=rect(0,0,6064,220+math.ceil(len(items)/4)*1140,'#E6E9E4')+text(32,60,'LIB–MANAGEMENT / '+g+'  '+NAMES[g],38,'nav',True,True)+text(32,100,'ÉCRAN ATLAS · Desktop 1440 × 1024 · Dữ liệu minh họa · Thiết kế theo tài liệu dự án',16,'muted')
    for i,s in enumerate(items):
        s['id']=f'FE{g}.{i+1:02}'; xx=32+(i%4)*1508; yy=180+(i//4)*1140
        body+=text(xx,yy-22,s['id']+'  '+s['name'],20,'nav',True)+f'<g id="{s["id"]}" transform="translate({xx} {yy})">'+shell(s)+content(s)+'</g>'
    data=svg(body,6064,220+math.ceil(len(items)/4)*1140);(OUT/f'{g}-desktop.svg').write_text(data)
    boards.append(dict(name=f'{g} / {NAMES[g]} / Desktop',svg=data,w=6064,h=220+math.ceil(len(items)/4)*1140))
    # Every module has mobile designs for every screen, not just priority routes.
    body=rect(0,0,math.ceil(min(6,len(items)))*430+40,160+math.ceil(len(items)/6)*940,'#E6E9E4')+text(20,55,'LIB / '+NAMES[g]+' — Mobile 390',28,'nav',True,True)
    for i,s in enumerate(items):
        xx=20+(i%6)*430;yy=140+(i//6)*940
        body+=text(xx,yy-22,s['id']+' / '+s['name'][:25],14,'nav',True)+f'<g id="M-{s["id"]}" transform="translate({xx} {yy})">'+mobile(s)+'</g>'
    data=svg(body,min(6,len(items))*430+40,160+math.ceil(len(items)/6)*940);(OUT/f'{g}-mobile.svg').write_text(data)
    boards.append(dict(name=f'{g} / {NAMES[g]} / Mobile',svg=data,w=min(6,len(items))*430+40,h=160+math.ceil(len(items)/6)*940))

# Foundations / components / interaction specification, made of editable text and vector layers.
b=rect(0,0,3600,2400,'bg')+text(60,90,'LIB–MANAGEMENT',56,'nav',True,True)+text(60,145,'Thư viện đương đại / Hệ thống giao diện',28,'muted')
for i,(n,c) in enumerate(C.items()):
    xx=60+(i%6)*570;yy=220+(i//6)*170;b+=rect(xx,yy,530,100,c,8)+text(xx,yy+132,n+' · '+c,16,'ink',True)
b+=text(60,640,'Aa  Thư viện của những câu chuyện',48,'ink',True,True)+text(60,700,'Arial 16 / 14 · Tiếng Việt có dấu · 12.000 ₫ · 23/10/2026',24,'ink')
for i,t in enumerate(['Lưu thay đổi','Hủy','Xác nhận','Đang gửi…']):b+=btn(60+i*350,780,t,i%2==0,300)
for i,(t,c) in enumerate([('Sẵn có','green'),('Chờ xác nhận','amber'),('Không khả dụng','red'),('Đang xử lý','blue')]):b+=badge(60+i*350,860,t,c)
b+=field(60,970,'Nhãn trường bắt buộc','Giá trị hiện tại',650)+rect(60,1040,650,3,'blue')+text(60,1080,'Focus vòng 2px, offset 3px · Target ≥44px',17,'blue')
b+=panel(800,950,850,330,'Xác nhận thao tác','Đối tượng, tác động và lý do phải rõ trước khi xác nhận.')+field(824,1060,'Lý do','Nêu căn cứ nghiệp vụ',800)+btn(824,1180,'Xác nhận',True,300)+btn(1144,1180,'Quay lại',False,280)
b+=text(60,1400,'Motion để định hướng',36,'ink',True,True)
for i,(t,d) in enumerate([('120ms / hover, focus','Chỉ đổi màu hoặc phản hồi trạng thái'),('180ms / dòng vừa quét','Fade + y4px; không lấy focus scanner'),('240ms / drawer, dialog','Scale .98 → 1; focus trap và return focus'),('280ms / portal route','Fade + y8px; shell giữ nguyên'),('Reduced motion','Bỏ translate / scale / stagger; giữ chữ và icon'),('Polling & pending','Không replay hiệu ứng; không giả phần trăm')]):
    xx=60+(i%3)*1160;yy=1460+(i//3)*220;b+=panel(xx,yy,1100,180,t,d)
b+=text(60,2030,'Bộ trạng thái dùng chung',36,'ink',True,True)
for i,(t,c) in enumerate([('Đang tải · giữ kích thước','blue'),('Chưa có dữ liệu · hành động tiếp','blue'),('Lỗi · thử lại tại vùng lỗi','red'),('Đang gửi · khóa action liên quan','amber'),('Thành công · biên nhận bền vững','green'),('409 · giữ nội dung đã nhập','amber')]):b+=badge(60+(i%3)*1160,2100+(i//3)*100,t,c)
boards.insert(0,dict(name='00 / Foundations · Components · Motion',svg=svg(b,3600,2400),w=3600,h=2400))
(OUT/'boards.json').write_text(json.dumps(boards,ensure_ascii=False))
(OUT/'screens.json').write_text(json.dumps(S,ensure_ascii=False,indent=2))
def inner(v):return v[v.index('>')+1:v.rindex('</svg>')]
for mode in ['Desktop','Mobile']:
    selected=[b for b in boards if b['name'].endswith(mode)]
    body='';yy=0
    for b in selected:
        body+=f'<g id="{esc(b["name"])}" transform="translate(0 {yy})">'+inner(b['svg'])+'</g>';yy+=b['h']+240
    (OUT/f'atlas-{mode.lower()}.svg').write_text(svg(body,max(b['w'] for b in selected),yy))
(OUT/'foundations.svg').write_text(boards[0]['svg'])
print(json.dumps({'screens':len(S),'mobile':len(S),'boards':len(boards),'bytes':(OUT/'boards.json').stat().st_size}))
