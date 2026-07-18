# Vienounce Core

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Language: Vietnamese](https://img.shields.io/badge/Readme-VN-brightgreen.svg)](#)
[![Language: English](https://img.shields.io/badge/Readme-EN-lightgrey.svg)](README_EN.md)

---

Vienounce Core là một thư viện Python mã nguồn mở được thiết kế để phân tích phát âm tiếng Anh và phát hiện các lỗi ngôn ngữ L1 transfer phổ biến ở người nói tiếng Việt. Thư viện sử dụng không gian ngữ âm song ngữ thống nhất để căn biên (align) các bản ghi âm của người dùng và tạo phản hồi mức độ chuẩn phát âm (GOP - Goodness of Pronunciation) ở cấp độ âm tố (phone).

---

## 🖥️ Giao diện Gradio GUI 

Thư viện đi kèm với một giao diện Gradio tích hợp (`gui_local.py`) phục vụ cho việc luyện tập offline độc lập. Nó cho phép bạn nhập câu đích, ghi âm lượt thử của mình và xem các điểm nổi bật ở cấp độ âm tố cùng với điểm phát âm tổng thể ngay trên máy tính:

![Xem trước Gradio GUI cục bộ](assets/example-local.png)

---

## ☁️ Giao diện Cloud 

Trong phiên bản Web, mô hình được huấn luyện tùy chỉnh của chúng tôi cũng so sánh với các bản tham chiếu giọng bản xứ chuẩn (Kokoro TTS) để giúp người học nghe rõ sự khác biệt do ảnh hưởng ngữ âm tiếng Việt:

![Xem trước giao diện Cloud](assets/example-cloud.png)

---

## Tính năng chính

*   **Ánh xạ âm vị song ngữ**: Chuyển đổi các từ tiếng Anh mục tiêu một cách mượt mà bằng bộ phiên âm song ngữ `sea-g2p`.
*   **Chẩn đoán cấp độ âm tố**: Sử dụng mô hình căn biên âm học Wav2Vec2 (`facebook/wav2vec2-xlsr-53-espeak-cv-ft`) để căn khớp âm thanh với các âm tố IPA.
*   **Đánh giá mức độ chuẩn phát âm (GOP)**: Tính toán xác suất hậu nghiệm logarit (posterior log-probabilities) trên từng âm tố để chấm điểm độ chính xác.
*   **Ngưỡng đánh giá chuẩn hóa**: Ánh xạ điểm GOP sang các chỉ dấu trực quan trực quan:
    *   🟢 **Xanh lá (Chính xác)**: $\text{GOP} \ge -2.5$
    *   🟡 **Vàng (Giọng địa phương/Gần đạt)**: $-5.0 \le \text{GOP} < -2.5$
    *   🔴 **Đỏ (Nuốt âm/Sai)**: $\text{GOP} < -5.0$
*   **Ưu tiên chạy ngoại tuyến & Thân thiện với CPU**: Hoạt động hoàn toàn cục bộ, tải các mô hình trên CPU mà không cần cơ sở dữ liệu hay phụ thuộc vào lưu trữ đám mây.
*   **Giao diện Gradio GUI**: Giao diện web tương tác (`gui_local.py`) để thử nghiệm đánh giá trên bất kỳ câu nào.

---

## Cài đặt

### Yêu cầu hệ thống
Đảm bảo đã cài đặt `ffmpeg` trên hệ thống của bạn để hỗ trợ chuyển đổi định dạng âm thanh:
```bash
# Trên Ubuntu/Debian:
sudo apt-get install ffmpeg
```

### Thiết lập môi trường Python
Chúng tôi khuyên dùng `uv` hoặc `pip` trong môi trường ảo:
```bash
# Nhân bản kho lưu trữ và di chuyển đến thư mục core
cd vienounce-core

# Cài đặt ở chế độ chỉnh sửa trực tiếp (editable mode)
pip install -e .
```

---

## Bắt đầu nhanh


Chạy giao diện Gradio:
```bash
python gui_local.py
```
Mở `http://127.0.0.1:7860` trong trình duyệt web, nhập câu đích, ghi âm lượt thử và nhấp vào **Chẩn đoán phát âm của tôi** (Diagnose My Pronunciation).


---

## Đánh giá hiệu quả (Benchmarks)

Vienounce Core được kiểm thử và tối ưu trực tiếp dựa trên các bản ghi âm thực tế từ người Việt học tiếng Anh (sử dụng bộ cơ sở dữ liệu chuẩn L2-ARCTIC). Kết quả đo lường thực tế cho thấy:

*   **Khả năng bắt lỗi phát âm (Recall - 28.9%)**: Nhận diện chính xác 28.9% các âm bị nuốt hoặc phát âm sai. Trong phiên bản đám mây (Cloud), tỷ lệ này được cải thiện lên **40.3%** nhờ mô hình adapter đặc thù.
*   **Độ chính xác của cảnh báo (Precision - 50.6%)**: Khoảng một nửa số âm tố bị hệ thống gắn nhãn đỏ/vàng đại diện chính xác cho các lỗi phát âm thực tế của người dùng, giúp hạn chế cảnh báo sai làm phiền quá trình luyện tập.
*   **Biên độ phân tách (1.07)**: Khả năng phân biệt rõ ràng giữa âm phát âm đúng và âm bị phát âm sai của người Việt trên các âm cuối quan trọng (như phụ âm cuối `/k, t, p/` hay âm gió `/s, z/`).

Để xem báo cáo hiệu năng đầy đủ và so sánh chi tiết với mô hình phiên bản đám mây, vui lòng đọc [BENCHMARKS.md](BENCHMARKS.md).

---

## Ghi nhận

*   **Kokoro TTS**: Được sử dụng để tạo các đoạn âm thanh tham chiếu giọng bản xứ chuẩn [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M).
*   **VieNeu-TTS** và **sea-g2p**: Được sử dụng để tạo âm thanh phát âm tiếng Anh giọng Việt nhằm làm nổi bật các lỗi chuyển di ngôn ngữ (L1 transfer) [pnnbao/97sea-g2p](https://github.com/pnnbao97/sea-g2p)  [pnnbao97/VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS). 

---

## Giấy phép

Dự án này được cấp phép theo Giấy phép Apache 2.0.
