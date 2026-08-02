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
- Repository: <https://github.com/hv6z/n20-secure-firmware-update-iot>

## Phạm vi bản nộp cuối kỳ

Bộ nộp chính thức gồm báo cáo DOCX, bản PDF xuất từ cùng báo cáo và repository
GitHub công khai này. Theo hướng dẫn trực tiếp của giảng viên, đề tài không phải
nộp slide; repository vì vậy không chứa thư mục hoặc tệp trình chiếu.

## Cấu trúc repository

```text
configs/                    Chính sách bảo mật của bản demo
data/                       Firmware giả lập v1, v2 và bản lỗi self-test
references/                 Danh mục tài liệu tham khảo và phần đã sử dụng
report/                     Báo cáo tiểu luận DOCX và PDF cuối kỳ
results/logs/               Nhật ký chạy thử
results/                    Manifest, chữ ký, khóa công khai và ma trận kết quả
src/                        Mã nguồn demo
update_so_do_hinh_anh/      Sơ đồ và hình minh chứng
```

## Tiến độ và commit theo tuần

Bảng dưới đây ánh xạ tiến độ với lịch sử commit thực tế. Những tuần không có bản
nộp riêng được ghi rõ, không tạo commit hồi tố.

| Tuần | Trạng thái thực tế | Nội dung/minh chứng | Commit tiêu biểu |
|---|---|---|---|
| Tuần 01 | Đã thực hiện | Khởi tạo repo, README và cấu trúc ban đầu | `29ba97d`, `9499a6d` |
| Tuần 02 | Đã thực hiện | Policy, firmware giả lập, code demo, báo cáo và 5 ca kiểm thử | `8e22f6e`, `73aa4cf`, `9dac557`, `22b6697`, `382e3d9` |
| Tuần 03 | Không nộp bản riêng | Chương 2–3 được hoàn thiện tích lũy trong báo cáo cuối | `a8febb2` (minh chứng tích lũy) |
| Tuần 04 | Tích lũy trong bản cuối | Chương 4, log và ma trận kết quả | `a8febb2` |
| Tuần 05 | Tích lũy trong bản cuối | Chương 5–6 và đánh giá rủi ro | `a8febb2` |
| Tuần 06 | Hoàn thành | Rà soát mẫu, cập nhật DOCX/PDF cuối kỳ và đồng bộ repository | `1cbea67`, `933dc84`, `cf0ff9d`, `6a7efc5` |

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

Kết quả mong đợi: 5/5 ca kiểm thử đạt. Ma trận được ghi vào
`results/test_matrix.csv`; log chi tiết nằm tại
`results/logs/secure_update_demo.log`.

## Ca kiểm thử

| Ca kiểm thử | Kỳ vọng | Kiểm soát được xác minh |
|---|---:|---|
| Bản v2 hợp lệ | Chấp nhận | Chữ ký, target, sequence, AES-GCM, SHA-256, self-test |
| Chữ ký manifest bị sửa | Từ chối | Xác thực nguồn phát hành bằng RSA-PSS |
| Payload bị sửa 1 bit | Từ chối | Xác thực AES-GCM |
| Bản v1 có sequence cũ | Từ chối | Chống rollback |
| Bản v3 lỗi self-test | Từ chối | Staging và rollback |

## Minh chứng

### Sơ đồ quy trình OTA an toàn

![Quy trình OTA an toàn](update_so_do_hinh_anh/so_do_ota_an_toan.svg)

### Kết quả kiểm thử tái lập

- Ma trận kết quả: [`results/test_matrix.csv`](results/test_matrix.csv)
- Log chạy demo: [`results/logs/secure_update_demo.log`](results/logs/secure_update_demo.log)
- Manifest mẫu: [`results/manifest_v2.json`](results/manifest_v2.json)
- Manifest kèm chữ ký: [`results/signed_manifest_v2.json`](results/signed_manifest_v2.json)
- Báo cáo DOCX dùng để nộp: [`report/231A010297_TranThiHaVy_DeTai20_TieuLuan_CuoiKy.docx`](report/231A010297_TranThiHaVy_DeTai20_TieuLuan_CuoiKy.docx)
- Báo cáo PDF xuất từ DOCX: [`report/231A010297_TranThiHaVy_DeTai20_TieuLuan_CuoiKy.pdf`](report/231A010297_TranThiHaVy_DeTai20_TieuLuan_CuoiKy.pdf)

## Giới hạn an toàn

- Khóa riêng trong demo được sinh trong bộ nhớ khi chạy; repository không chứa khóa triển khai thật.
- Đây là mô phỏng Python, chưa thay thế bootloader, eFuse, secure element hoặc flash thật.
- Demo chưa triển khai HTTPS/mTLS, quản lý vòng đời khóa, thu hồi khóa, cập nhật vi sai và mất điện giữa quá trình ghi flash.
- Không dùng mã nguồn này để cập nhật thiết bị sản xuất nếu chưa có threat model, kiểm thử độc lập và quy trình quản lý khóa phù hợp.

## Tài liệu tham khảo đã sử dụng

Ngày truy cập các nguồn: **31/07/2026**. Số thứ tự dưới đây thống nhất với ký
hiệu trích dẫn `[1]` đến `[10]` trong báo cáo.

1. **RFC 9019 - A Firmware Update Architecture for Internet of Things
   Devices**, IETF, 2021.
   - URL: <https://datatracker.ietf.org/doc/html/rfc9019>
   - Phần đã sử dụng: thành phần, vai trò và yêu cầu của kiến trúc cập nhật
     firmware IoT.

2. **NIST SP 800-193 - Platform Firmware Resiliency Guidelines**, NIST, 2018.
   - URL: <https://csrc.nist.gov/pubs/sp/800/193/final>
   - Phần đã sử dụng: nguyên tắc bảo vệ, phát hiện và phục hồi firmware.

3. **RFC 9124 - A Manifest Information Model for Firmware Updates in IoT
   Devices**, IETF, 2022.
   - URL: <https://datatracker.ietf.org/doc/html/rfc9124>
   - Phần đã sử dụng: metadata manifest và điều kiện xử lý gói cập nhật.

4. **RFC 8017 - PKCS #1: RSA Cryptography Specifications Version 2.2**,
   IETF, 2016.
   - URL: <https://datatracker.ietf.org/doc/html/rfc8017>
   - Phần đã sử dụng: RSA-PSS cho chữ ký và RSA-OAEP cho bọc khóa.

5. **NIST SP 800-38D - Recommendation for Block Cipher Modes of Operation:
   GCM and GMAC**, NIST, 2007.
   - URL: <https://csrc.nist.gov/pubs/sp/800/38/d/final>
   - Phần đã sử dụng: AES-GCM và yêu cầu về IV/nonce.

6. **FIPS PUB 180-4 - Secure Hash Standard**, NIST, 2015.
   - URL: <https://csrc.nist.gov/pubs/fips/180-4/upd1/final>
   - Phần đã sử dụng: tiêu chuẩn hàm băm SHA-256.

7. **Repository của đề tài n20-secure-firmware-update-iot**.
   - URL: <https://github.com/hv6z/n20-secure-firmware-update-iot>
   - Mốc đối chiếu nội dung, mã nguồn và minh chứng trước khi tải báo cáo cuối:
     `933dc849b40244fea8a7bd68917f2cc10667cdbf`.

8. **Espressif Systems - Over The Air Updates (OTA), ESP-IDF Programming
   Guide v5.4.2**.
   - URL: <https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32/api-reference/system/ota.html>
   - Phần đã sử dụng: phân vùng OTA, trạng thái image, rollback và anti-rollback.

9. **OWASP - IoT Security Verification Standard (ISVS)**.
   - URL: <https://github.com/OWASP/IoT-Security-Verification-Standard-ISVS>
   - Phần đã sử dụng: yêu cầu kiểm tra cập nhật an toàn và bảo vệ khóa.

10. **NIST SP 800-30 Rev. 1 - Guide for Conducting Risk Assessments**, NIST,
    2012.
    - URL: <https://csrc.nist.gov/pubs/sp/800/30/r1/final>
    - Phần đã sử dụng: đánh giá khả năng xảy ra, tác động và mức ưu tiên rủi ro.

Tệp `references/link_nguon.md` lưu danh sách khảo sát ban đầu. Danh mục trích
dẫn chính thức và phần sử dụng từng nguồn được trình bày trong README này và
`report/231A010297_TranThiHaVy_DeTai20_TieuLuan_CuoiKy.docx`.
