# Đề tài 20 - Cập nhật firmware an toàn cho thiết bị IoT

Repository mô phỏng cục bộ quy trình cập nhật firmware có xác thực nguồn gốc,
kiểm tra toàn vẹn, bảo mật payload, chống rollback và khôi phục khi bản mới
không vượt qua self-test. Đây là lab dùng dữ liệu giả lập; không kết nối hoặc
kiểm thử trên hệ thống thật.

## Thành viên và học phần

- Sinh viên: Trần Thị Hà Vy - MSSV 231A010297
- Lớp học phần: 253INT441001
- Học phần: Bảo mật trong IoT
- Giảng viên hướng dẫn: ThS. Hồ Nhựt Minh

## Cấu trúc repository

```text
configs/                    Chính sách bảo mật của bản demo
data/                       Firmware giả lập v1, v2 và bản lỗi self-test
references/                 Danh mục tài liệu tham khảo và phần đã sử dụng
report/                     Báo cáo tiểu luận Word
results/logs/               Nhật ký chạy thử
results/packages/           Gói cập nhật sinh tự động khi chạy demo
results/device_state/       Trạng thái thiết bị giả lập
slides/                     Slide trình bày
src/                        Mã nguồn demo
update_so_do_hinh_anh/      Sơ đồ và hình minh chứng
```

## Mô hình bảo vệ

1. Máy chủ tạo manifest gồm thiết bị đích, phiên bản, sequence, kích thước và SHA-256.
2. Nhà phát hành ký manifest bằng RSA-PSS/SHA-256.
3. Firmware được mã hóa và xác thực bằng AES-256-GCM; khóa AES dùng một lần được bọc bằng RSA-OAEP/SHA-256.
4. Thiết bị kiểm tra chữ ký, thiết bị đích và sequence trước khi giải mã.
5. Thiết bị xác minh AES-GCM, kích thước và SHA-256, sau đó ghi vào vùng staging.
6. Bản mới chỉ được kích hoạt khi self-test thành công; nếu thất bại, thiết bị giữ/khôi phục bản trước.

Chữ ký số mới là cơ chế xác thực nguồn phát hành. HTTPS/mTLS là lớp bảo vệ kênh
truyền bổ sung, không thay thế kiểm tra chữ ký trên thiết bị.

## Cách chạy demo

Yêu cầu Python 3.11+ và thư viện trong `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
python src/code_demo.py --demo
```

Kết quả mong đợi: 4/4 ca kiểm thử đạt. Ma trận được ghi vào
`results/test_matrix.csv`; log chi tiết nằm tại
`results/logs/secure_update_demo.log`.

## Ca kiểm thử

| Ca kiểm thử | Kỳ vọng | Kiểm soát được xác minh |
|---|---:|---|
| Bản v2 hợp lệ | Chấp nhận | Chữ ký, target, sequence, AES-GCM, SHA-256, self-test |
| Payload bị sửa 1 bit | Từ chối | Xác thực AES-GCM |
| Bản v1 có sequence cũ | Từ chối | Chống rollback |
| Bản v3 lỗi self-test | Từ chối | Staging và rollback |

## Giới hạn an toàn

- Khóa riêng trong demo được sinh trong bộ nhớ khi chạy; repository không chứa khóa triển khai thật.
- Đây là mô phỏng Python, chưa thay thế bootloader, eFuse, secure element hoặc flash thật.
- Demo chưa triển khai HTTPS/mTLS, quản lý vòng đời khóa, thu hồi khóa, cập nhật vi sai và mất điện giữa quá trình ghi flash.
- Không dùng mã nguồn này để cập nhật thiết bị sản xuất nếu chưa có threat model, kiểm thử độc lập và quy trình quản lý khóa phù hợp.

## Tài liệu

Danh mục nguồn bắt buộc từ đề bài và các nguồn bổ sung nằm tại
`references/link_nguon.txt`. Báo cáo ghi rõ tổ chức, URL, ngày truy cập,
branch/tag (nếu là GitHub) và phần nội dung đã sử dụng.
