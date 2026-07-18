# Ghi chú về khóa mật mã

Repository không lưu khóa riêng triển khai thật.

- Khóa nhà phát hành và khóa thiết bị được sinh tạm thời trong bộ nhớ khi chạy demo.
- Chỉ khóa công khai minh chứng được xuất ra `results/demo_vendor_public.pem`.
- Không commit khóa riêng, tệp `.key`, `.p12` hoặc `.pfx` vào repository.
- Hệ thống sản xuất cần dùng secure element, HSM hoặc vùng lưu trữ khóa được bảo vệ.
