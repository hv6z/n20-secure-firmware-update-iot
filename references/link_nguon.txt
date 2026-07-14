TÀI LIỆU THAM KHẢO - ĐỀ TÀI 20
Ngày truy cập chung: 14/07/2026

1. Espressif Systems, “ESP-IDF Platform Repository”.
   URL: https://github.com/espressif/esp-idf
   Phiên bản tham chiếu: release-v5.4 / tài liệu v5.4.2.
   Phần sử dụng: HTTPS OTA, phân vùng otadata, app rollback, anti-rollback và Secure Boot.

2. OWASP, “IoT Security Verification Standard (ISVS)”.
   URL: https://github.com/OWASP/IoT-Security-Verification-Standard-ISVS
   Nhánh tham chiếu: master.
   Phần sử dụng: yêu cầu xác minh cập nhật phần mềm, tính toàn vẹn, xác thực và chống rollback.

3. scriptingxss / OWASP, “Firmware Security Testing Methodology (FSTM)”.
   URL: https://github.com/scriptingxss/owasp-fstm
   Nhánh tham chiếu: master.
   Phần sử dụng: phương pháp chín giai đoạn; đặc biệt thu thập thông tin, phân tích firmware, trích xuất và phân tích filesystem.

4. OWASP, “IoTGoat - Deliberately Insecure Firmware”.
   URL: https://github.com/OWASP/IoTGoat
   Nhánh tham chiếu: master.
   Phần sử dụng: firmware cố ý không an toàn để nhận diện rủi ro và xây dựng ca kiểm thử trong lab cục bộ.

5. Espressif Systems, “ESP Encrypted Image Abstraction Layer”.
   URL: https://github.com/espressif/idf-extra-components/tree/master/esp_encrypted_img
   Nhánh tham chiếu: master.
   Phần sử dụng: tham khảo cấu trúc component xử lý ảnh firmware mã hóa và cơ chế giải mã theo luồng.

6. B. Moran, H. Tschofenig, D. Brown, M. Meriac, “A Firmware Update Architecture for Internet of Things”, RFC 9019, IETF, 2021.
   URL: https://www.rfc-editor.org/rfc/rfc9019.html
   Phần sử dụng: vai trò firmware author/server/consumer, manifest, bootloader, xác thực và chiến lược phục hồi.

7. B. Moran et al., “A Manifest Information Model for Firmware Updates in Internet of Things (IoT) Devices”, RFC 9124, IETF, 2022.
   URL: https://www.rfc-editor.org/rfc/rfc9124.html
   Phần sử dụng: trường thông tin manifest, sequence chống rollback, xác thực, bảo vệ khóa ký và điều kiện áp dụng firmware.

8. Espressif Systems, “Over The Air Updates (OTA) - ESP-IDF Programming Guide v5.4.2”.
   URL: https://docs.espressif.com/projects/esp-idf/en/v5.4.2/esp32/api-reference/system/ota.html
   Phần sử dụng: trạng thái image, xác nhận bản chạy tốt, app rollback và anti-rollback bằng security version/eFuse.
