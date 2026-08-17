# TATTS — Bộ tổng hợp giọng nói Tiếng Việt chạy trên CPU

Engine text-to-speech **tiếng Việt và tiếng Anh** hoạt động **hoàn toàn offline**, **không cần GPU**,
đi kèm **71 giọng đọc sẵn sàng (53 Việt + 18 Anh)**. Biến file văn bản, phụ đề, hay bất kỳ đoạn text nào
thành audio chất lượng phát hành — trên chính máy của bạn, không giới hạn ký tự, không phí theo lượt.

### 🎧 Nghe thử toàn bộ kho giọng: **https://tuanh4198.github.io/TATTS/**

### 📦 Dùng thật: module **Giọng Đọc AI** trong app **NTA Tool**

Nghe thử ở trang trên là miễn phí. Muốn dùng để làm việc thì mua module trong app: chọn giọng
nào tải giọng đó (~64 MB), đọc không giới hạn ký tự, chạy offline trên máy bạn, và có sẵn HTTP
API để nối vào script hay công cụ khác.

---

## Vì sao dùng TATTS

| | |
|---|---|
| 🎭 **53 giọng Việt sẵn dùng** | Nam, nữ, MC, bình luận viên, kể chuyện, nhân vật — không phải đi thu âm hay train |
| ⚡ **Chạy trên CPU, nhanh gấp 16× thời gian thực** | Không CUDA, không card đồ hoạ, không driver |
| 🔒 **100% offline** | Text không rời khỏi máy. Đọc hợp đồng, bệnh án, tài liệu nội bộ mà không lo rò rỉ |
| 💸 **Chi phí biên bằng 0** | Đọc cuốn sách 500.000 ký tự cũng miễn phí. Dịch vụ cloud tính tiền từng ký tự |
| 📦 **Cài đặt gọn** | `pip install onnxruntime numpy num2words` — hết. Không cần espeak-ng, không cần build C++ |
| 🇻🇳 **Xử lý tiếng Việt đúng** | Tự tách âm tiết (âm đầu / vần / thanh điệu), đọc đúng số, sẵn 17.839 từ nước ngoài đã phiên âm |
| 🎚 **Điều khiển được** | Tốc độ 0.7–1.5×, độ biến thiên ngữ điệu, khoảng nghỉ giữa câu |

### Hiệu năng đo thật

Đo trên **AMD Ryzen 7 6800HS** (laptop, CPU-only, onnxruntime 1.28):

| Chỉ số | Kết quả |
|---|---|
| Real-time factor (RTF) | **0.060** |
| Tốc độ tổng hợp | **16.5× nhanh hơn thời gian thực** |
| Thông lượng | **~242 ký tự / giây** |
| Nạp model lần đầu | ~4 giây (sau đó giữ trong RAM) |
| RAM mỗi giọng | ~63 MB |
| Chất lượng đầu ra | 22.050 Hz, mono, 16-bit |

> Nghĩa là: một chương truyện 20 phút audio mất **~75 giây** để render. Cả cuốn sách nói
> 10 tiếng mất chưa tới **40 phút** — trên laptop, trong lúc bạn làm việc khác.

---

## Các luồng sử dụng

### 1. Đọc file văn bản → audio

Kéo file `.txt` vào là ra `.wav`. Dùng cho truyện dài, sách nói, tài liệu, bài giảng.

**Yêu cầu nghiệp vụ đi kèm:** tự chia chương theo tiêu đề, render từng chương ra file riêng,
có checkpoint để dừng giữa chừng rồi chạy tiếp, gắn thẻ ID3 (tên sách / chương / tác giả)
khi xuất MP3, và sinh sẵn file playlist.

### 2. Lồng tiếng từ phụ đề `.srt` / `.vtt` → audio khớp timeline

Đây là luồng khó nhất và cũng giá trị nhất. Mỗi dòng phụ đề có mốc bắt đầu — kết thúc, nên
audio sinh ra **phải vừa đúng khung thời gian đó**, nếu không tiếng sẽ trôi khỏi hình.

Cách xử lý:

1. Đọc từng dòng sub, tổng hợp thử ở tốc độ 1.0×
2. So thời lượng audio với độ dài khung → **tự điều chỉnh `length_scale`** cho vừa
3. Nếu co lại vẫn không kịp (câu quá dài so với khung) → cảnh báo dòng đó để người dùng rút gọn lời
4. Chèn khoảng lặng đúng bằng quãng nghỉ giữa các dòng
5. Ghép thành một track liền mạch, ghép vào video bằng `ffmpeg`

**Ứng dụng:** lồng tiếng phim/clip nước ngoài đã có Việt sub, làm bản tiếng Việt cho video
đào tạo, thuyết minh phim tài liệu.

### 3. Kịch bản nhiều nhân vật

Đánh dấu người nói ngay trong text, engine tự đổi giọng theo từng dòng:

```
[Tào Tháo] Ta thà phụ người trong thiên hạ.
[Gia Cát Lượng] Mưu sự tại nhân, thành sự tại thiên.
[Người dẫn] Hai người nhìn nhau hồi lâu.
```

Dùng cho truyện có hội thoại, audio drama, podcast phỏng vấn dựng sẵn.
**Lưu ý kỹ thuật:** cần cache nhiều model cùng lúc (63 MB × số giọng) hoặc nạp theo LRU
để không thổi bay RAM.

### 4. Video ngắn — TikTok, YouTube, Reels

Ưu tiên vòng lặp nhanh: gõ script → nghe thử **một câu** ngay → chỉnh giọng/tốc độ →
render cả bài ra MP3. Không phải chờ render toàn bộ mới biết giọng có hợp không.

### 5. Bản tin tự động / podcast từ RSS

Hẹn giờ: lấy tin → chuẩn hoá text → đọc bằng giọng MC → xuất MP3 + feed podcast.
Vận hành không cần người, chạy được trên VPS rẻ tiền vì không đòi GPU.

### 6. Tổng đài IVR, thông báo công cộng

Render sẵn câu thoại cố định ("Nhấn phím 1 để gặp tổng đài viên"), xuất định dạng
tổng đài cần (8 kHz mono, µ-law). Câu động (số dư, tên khách) gọi qua API lúc chạy.

### 7. Trợ năng và học tập

Đọc tài liệu cho người khiếm thị, người lớn tuổi; biến giáo trình thành bài nghe;
đọc truyện cho trẻ. Vì offline nên dùng được ở nơi mạng yếu và không tốn phí theo trang.

---

## Luồng tích hợp cho ứng dụng bên ngoài

Bốn cửa ngõ, đi từ dễ tới linh hoạt:

### A. CLI — cho script và automation

```bash
tatts say "Xin chào các bạn" --voice "Gia Cát Lượng" --out chao.wav
tatts read truyen.txt --voice "Ngọc Huyền Best" --speed 1.1 --format mp3
tatts srt phim.srt --voice "Nam Minh 1" --fit-timeline --out phim-vi.wav
tatts batch ./kich-ban/ --voice "MC Lại Văn Sâm" --out-dir ./audio/
tatts voices --lang vi          # liệt kê giọng đang có
```

### B. Python SDK — nhúng thẳng vào ứng dụng

```python
from tatts import Engine

engine = Engine(voice="Thảo Chi")          # nạp một lần, tái sử dụng
engine.say("Xin chào.", "chao.wav", speed=1.1)

# Xử lý phụ đề, tự co giãn cho khớp mốc thời gian
engine.dub_subtitles("phim.srt", "phim-vi.wav", fit_timeline=True)

# Lấy PCM thô để tự xử lý tiếp
samples, sample_rate = engine.synth("Một câu ngắn.")
```

### C. HTTP API cục bộ — **tương thích OpenAI**

Đây là điểm mấu chốt để app khác tích hợp mà **không phải viết lại code**. Mọi công cụ
đã hỗ trợ OpenAI TTS chỉ cần trỏ `base_url` về máy bạn là chạy:

```http
POST http://localhost:8080/v1/audio/speech
Content-Type: application/json

{
  "model": "tatts-vi",
  "voice": "Ngọc Huyền Best",
  "input": "Nội dung cần đọc.",
  "speed": 1.0,
  "response_format": "mp3"
}
```

Các endpoint đi kèm:

| Endpoint | Công dụng |
|---|---|
| `GET /v1/voices` | Danh sách giọng đang có + link mẫu nghe thử |
| `POST /v1/audio/speech` | Tổng hợp một đoạn, trả file audio |
| `POST /v1/jobs` | Việc dài (cả cuốn sách) → trả `job_id`, chạy nền |
| `GET /v1/jobs/{id}` | Tiến độ, phần trăm, link tải |
| `POST /v1/subtitles/dub` | Nhận `.srt`, trả audio đã khớp timeline |

### D. Thư mục theo dõi — cho người không lập trình

Thả file `.txt` hay `.srt` vào thư mục `input/`, vài giây sau có audio trong `output/`.
Phù hợp cho cộng tác viên nội dung không muốn đụng tới dòng lệnh.

---

## Định dạng đầu vào / đầu ra

**Vào:** `.txt` · `.srt` · `.vtt` · Markdown · chuỗi thẳng qua API
**Ra:** `.wav` (22.05 kHz) · `.mp3` · `.ogg` · PCM thô · kèm file mốc thời gian từng câu

---

## Trạng thái dự án

Repo này chứa **thư viện nghe thử giọng**. Engine và app đã có, phát hành dưới dạng
module **Giọng Đọc AI** trong app **NTA Tool**.

| Hạng mục | Trạng thái |
|---|---|
| Engine tổng hợp tiếng Việt (ONNX, CPU) | ✅ Đang chạy |
| Engine tiếng Anh (Piper + espeak-ng, CPU) | ✅ Đang chạy |
| 53 giọng Việt + 18 giọng Anh | ✅ Đang chạy |
| Web nghe thử + lọc theo ngôn ngữ | ✅ Đang chạy |
| **App desktop — module trong NTA Tool** | ✅ Đang chạy |
| **Tải giọng theo nhu cầu** (~64 MB/giọng) | ✅ Đang chạy |
| **HTTP API tương thích OpenAI** | ✅ Đang chạy |
| Đọc file `.txt` hàng loạt | 🔨 Đang làm |
| Lồng tiếng `.srt` khớp timeline | 🔨 Đang làm |
| Kịch bản nhiều nhân vật | 📋 Kế hoạch |
| Xuất MP3 kèm thẻ ID3 | 📋 Kế hoạch |
| Ngôn ngữ khác (Trung, Hàn, Nhật…) | 📋 Kế hoạch |

### Hạn chế đã biết (đang xử lý)

- ~~Từ ngoài từ điển bị bỏ qua im lặng~~ — **đã sửa 08/08/2026**. Âm tiết không tách được
  nay được đánh vần thay, và danh sách những từ đó hiện lên cho người dùng (trong app, và qua
  header `X-TTS-Unknown-Words` của API). Trước đây chữ biến mất khỏi audio mà không ai biết —
  với sách nói dài vài tiếng thì tai người không thể phát hiện.
- ~~Nạp model mất ~4 giây mỗi lần~~ — **đã sửa**. Tiến trình nền giữ ấm 2 model: lần đọc đầu
  ~4 giây, từ lần thứ hai còn 0,1–0,3 giây.
- **Chưa có streaming** — phải render xong cả câu mới phát được, chưa hợp với hội thoại thời gian thực.
- **Ngắt nghỉ mới ở mức câu** — dấu phẩy và dấu chấm phẩy chưa tạo quãng nghỉ riêng.

---

## Kho giọng

**71 giọng — 53 tiếng Việt + 18 tiếng Anh.**

**Tiếng Việt (53):** giọng đọc phổ thông, MC dẫn chương trình, bình luận viên bóng đá và
quân sự, giọng kể truyện, giọng nhân vật (Tào Tháo, Gia Cát Lượng, Hàn Tín, Châu Tinh Trì,
Thái giám Công Công…), giọng triết lý, giọng trung niên, giọng trending (THEANH28).

**Tiếng Anh (18):** Arctic, Brian, Brian wife, Bryce, Cori, Daden1, Ibrahim, Jessica,
Joe, John, Kristin, Kusal, Lessac, Libritts, Linda Johnson, Norman, Ryan, Sam.

Mỗi giọng có sẵn một đoạn demo kèm kịch bản. Nghe thử tất cả — có bộ lọc theo ngôn ngữ — tại
**[tuanh4198.github.io/TATTS](https://tuanh4198.github.io/TATTS/)**.

Các ngôn ngữ khác (Trung, Hàn, Nhật, Pháp, Tây Ban Nha, Bồ Đào Nha, Ý, Ấn Độ) đã
dựng sẵn khung thư mục, chờ bổ sung giọng.

---

## Yêu cầu hệ thống

- Windows / Linux / macOS
- Python 3.9 trở lên
- CPU x86-64 hoặc ARM64 — **không cần GPU**
- RAM: 2 GB (một giọng) · 4 GB trở lên nếu dùng nhiều giọng cùng lúc
- Ổ cứng: ~63 MB mỗi giọng

```bash
pip install onnxruntime numpy num2words
```

---

## Trang nghe thử

Thư mục web trong repo này là trang tĩnh chạy trên GitHub Pages.

```
index.html               trang chính
assets/style.css         giao diện
assets/app.js            lọc, tìm kiếm, trình phát
data/voices.json         danh sách giọng (sinh tự động, sửa tay được)
audio/*.mp3              file nghe thử (mono 64 kbps, ~18 MB tổng)
tools/build_manifest.py  script sinh lại audio + voices.json
```

Thêm giọng mới: bỏ vào `voices/<Ngôn ngữ>/<Tên giọng>/` (kèm file `.wav` demo và `.txt`
kịch bản nếu muốn), rồi chạy (cần `ffmpeg` trong PATH):

```bash
python tools/build_manifest.py
git add -A && git commit -m "feat: thêm giọng mới" && git push
```

Ngôn ngữ mới sẽ **tự xuất hiện** trong menu lọc, không cần sửa code.

Chạy thử ở máy: `python -m http.server 8000` rồi mở `http://localhost:8000`
(đừng mở thẳng `index.html` bằng `file://` — trình duyệt sẽ chặn đọc `voices.json`).

> Các file model `.onnx` (~63 MB/giọng, tổng ~3 GB) **không** nằm trong repo này.
