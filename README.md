# TATTS — Thư viện nghe thử giọng đọc AI Tiếng Việt

Web tĩnh cho phép người dùng nghe thử toàn bộ kho giọng đọc, có menu lọc theo
ngôn ngữ / giới tính / danh mục, tìm kiếm không dấu và một trình phát chung.

🔗 Demo: `https://Tuanh4198.github.io/TATTS/`

## Tính năng

- 50 giọng Tiếng Việt, nghe thử trực tiếp trên trình duyệt (không cần cài gì)
- Menu lọc: **Ngôn ngữ**, **Giới tính**, **Danh mục** (Bình luận, MC/Tin tức, Kể chuyện, Nhân vật…)
- Tìm kiếm không dấu — gõ `bao trung` vẫn ra "Bảo Trung"
- Trình phát cố định dưới màn hình: tua, âm lượng, tốc độ 0.75×–1.5×, nút giọng trước/sau
- Xem kịch bản demo của từng giọng
- Chia sẻ link tới đúng một giọng: `...#tieng-viet--adam`
- Phím tắt: `/` tìm kiếm, `Space` phát/dừng
- Giao diện tối, chạy tốt trên điện thoại

## Cấu trúc

```
index.html            trang chính
assets/style.css      giao diện
assets/app.js         lọc, tìm kiếm, trình phát
data/voices.json      danh sách giọng (sinh tự động, có thể sửa tay)
audio/*.mp3           file nghe thử (mono 64 kbps, ~18 MB tổng)
tools/build_manifest.py  script sinh lại audio + voices.json
```

## Cập nhật khi có giọng mới

1. Thêm giọng vào `voices/<Ngôn ngữ>/<Tên giọng>/` ở thư mục gốc dự án
   (cần có `<Tên giọng>.wav` làm demo, kèm `<Tên giọng>.txt` nếu muốn hiện kịch bản).
2. Chạy:

   ```bash
   pip install numpy soundfile     # lần đầu, cần thêm ffmpeg trong PATH
   python tools/build_manifest.py
   ```

3. Commit và push — GitHub Pages tự cập nhật.

Script chỉ nén những file `.wav` chưa có `.mp3` tương ứng, nên chạy lại rất nhanh.

## Sửa thông tin giọng

Giới tính được đoán tự động theo cao độ trung vị của giọng (`pitchHz` trong
`data/voices.json`), có thể sai với vài giọng đặc biệt. Muốn sửa thì đổi trực tiếp
trường `gender` (`male` / `female`) hoặc `category` trong `data/voices.json` —
script sẽ không ghi đè nếu bạn không xoá file.

> Lưu ý: các file model `.onnx` (~63 MB/giọng, tổng ~3 GB) **không** nằm trong repo này.

## Chạy thử ở máy

```bash
python -m http.server 8000
# mở http://localhost:8000
```

Không mở trực tiếp `index.html` bằng `file://` — trình duyệt sẽ chặn `fetch()` đọc `voices.json`.
