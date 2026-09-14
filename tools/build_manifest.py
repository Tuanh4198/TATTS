# -*- coding: utf-8 -*-
"""
Quét thư mục voices/ -> nén demo .wav sang .mp3 + sinh data/voices.json cho web.

Chạy:  python tools/build_manifest.py
Yêu cầu: ffmpeg và ffprobe trong PATH.
"""
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

# Console Windows mặc định cp1252, không in nổi tên giọng có dấu — script chết ngay
# dòng in đầu tiên dù mọi thứ khác đều đúng.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent.parent
GOC = HERE.parent

# Kho giọng đã dời vào `tts-core/voices/`; thư mục `voices/` cũ ở gốc nay rỗng. Dò theo thứ tự
# thay vì ghim một chỗ: ghim sai thì script vẫn chạy và sinh ra một danh mục RỖNG, mà trang web
# nhận danh mục rỗng thì khách mở app thấy mất sạch giọng.
VOICES_DIR = next(
    (d for d in (GOC / "tts-core" / "voices", GOC / "voices") if d.is_dir() and any(d.iterdir())),
    GOC / "voices",
)
PHAN_LOAI_FILE = GOC / "tts-core" / "phanloai_giong.json"
AUDIO_OUT = HERE / "audio"
DATA_OUT = HERE / "data" / "voices.json"

MP3_BITRATE = "64k"
SCRIPT_PREVIEW_CHARS = 400

# ── Nhận dạng giọng Kokoro ───────────────────────────────────────────────────
# Tên giọng Kokoro luôn là <chữ ngôn ngữ><f|m>_<tên>: af_bella, zf_001, jm_kumo…
# Giọng Piper (tự train tiếng Việt + 18 giọng Anh) không có dạng này, nên một biểu thức là đủ
# để tách hai họ mà không phải liệt kê tay — liệt kê tay là mỗi lần thêm giọng lại quên một cái.
RE_KOKORO = re.compile(r"^[abefhijpz][fm]_[a-z0-9]+$")

# 100 giọng Trung của bản v1.1-zh đặt tên bằng SỐ (zf_001…zm_100); 8 giọng Trung của bản v1.0
# đặt tên bằng chữ (zf_xiaobei…). Đây là cách duy nhất phân biệt chúng từ tên, và phân biệt sai
# thì app nạp giọng bằng model không khớp -> mất thanh điệu mà audio vẫn ra.
RE_ZH_V11 = re.compile(r"^z[fm]_\d{3}$")

# chữ đầu tên giọng -> (mã ngôn ngữ cho bộ phiên âm, đường phiên âm)
KOKORO_LANG = {
    "a": ("en-us", "espeak"),
    "b": ("en-gb", "espeak"),
    "e": ("es", "espeak"),
    "f": ("fr-fr", "espeak"),
    "h": ("hi", "espeak"),
    "i": ("it", "espeak"),
    "j": ("ja", "misaki-ja"),
    "p": ("pt-br", "espeak"),
    "z": ("cmn", "misaki-zh"),
}

# ── Bộ máy Kokoro ────────────────────────────────────────────────────────────
# Tải thẳng từ release CÔNG KHAI: model là mã nguồn mở (Apache-2.0), mã hoá hay đưa vào repo
# private không chặn thêm ai mà chỉ thêm 750 MB phải tự host.
#
# sha256 đo trên chính file đã tải về (17/08/2026), khớp tài liệu TICH_HOP_KOKORO.md.
KOKORO_GH = "https://github.com/thewh1teagle/kokoro-onnx/releases/download"
ENGINES = {
    "kokoro/v1.0": {
        "label": "Bộ đa ngôn ngữ (Anh, Nhật, Pháp, Ý, TBN, Bồ, Ấn + 8 giọng Trung)",
        "files": [
            {
                "as": "model.onnx",
                "url": f"{KOKORO_GH}/model-files-v1.0/kokoro-v1.0.onnx",
                "sha256": "7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5",
                "bytes": 325532387,
            },
            {
                "as": "voices.bin",
                "url": f"{KOKORO_GH}/model-files-v1.0/voices-v1.0.bin",
                "sha256": "bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d",
                "bytes": 28214398,
            },
        ],
    },
    "kokoro/v1.1-zh": {
        "label": "Bộ tiếng Trung (100 giọng)",
        "files": [
            {
                "as": "model.onnx",
                "url": f"{KOKORO_GH}/model-files-v1.1/kokoro-v1.1-zh.onnx",
                # Upstream ĐÃ THAY file này ngày 18/08/2026 (bản cũ 343.605.188 byte, sha
                # eefec708…). Hash cũ làm mọi lượt tải bị từ chối ở bước kiểm toàn vẹn —
                # phép kiểm làm đúng, chỉ là số liệu hết hạn. Bản mới nhẹ hơn và khai
                # `speed` là float nên không cần vá byte nữa. Đã đo: nạp được, 103 giọng,
                # đọc tiếng Trung sạch, 0 âm vị bị loại.
                "sha256": "859f9ded9f53be16c24857cdab3254a45da53c3afd5ba6ef134c7de3f822e326",
                "bytes": 325506167,
            },
            {
                "as": "voices.bin",
                "url": f"{KOKORO_GH}/model-files-v1.1/voices-v1.1-zh.bin",
                "sha256": "14cb6186c99e4f6016871405f62046c5df863ae27465cbdc4ee08be7dd703acd",
                "bytes": 53815880,
            },
            {
                # Vocab chú âm của riêng bản v1.1-zh. Release kokoro-onnx KHÔNG kèm file này;
                # nguồn công khai là chính repo model trên HuggingFace (Apache-2.0). Đã đối
                # chiếu: giống hệt bản đi kèm app tham chiếu.
                "as": "config.json",
                "url": "https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh/resolve/main/config.json",
                "sha256": "bc333efa5ce4ceff433c8c8e5d027a1eca0166001e4e4a62bea2d26ff7a46890",
                "bytes": 3228,
            },
        ],
    },
}


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt, giữ lại chữ cái ASCII."""
    text = text.replace("Đ", "D").replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def slugify(text: str) -> str:
    ascii_text = strip_accents(text).lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", ascii_text)).strip("-")


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(result.stdout.strip()), 1)


def encode_mp3(wav_path: Path, mp3_path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
         "-ac", "1", "-b:a", MP3_BITRATE, str(mp3_path)],
        check=True,
    )


def read_script(txt_path: Path) -> str:
    if not txt_path.exists():
        return ""
    raw = txt_path.read_text(encoding="utf-8", errors="replace").strip()
    collapsed = re.sub(r"\s+", " ", raw)
    if len(collapsed) <= SCRIPT_PREVIEW_CHARS:
        return collapsed
    return collapsed[:SCRIPT_PREVIEW_CHARS].rsplit(" ", 1)[0] + "…"


def doc_phan_loai() -> dict:
    """
    Bảng giọng Việt -> thế hệ engine (`realmap` | `espeak`), dựng bằng cách đọc thử rồi nghe lại
    bằng faster-whisper (xem `tts-core/TOM_TAT_CAP_NHAT_TTS.md`).

    Vì sao phải có bảng này thay vì đọc config trong gói: đã đo cả 53 giọng — `espeak.voice` là
    `"en-us"` thì chắc chắn realmap (25/25), nhưng `"vi"` thì lẫn lộn 21 realmap với 7 espeak.
    Không có bảng thì app đưa nhầm engine, và giọng **vẫn ra tiếng nhưng không thành câu**.
    """
    if not PHAN_LOAI_FILE.exists():
        print(f"  [!] khong thay {PHAN_LOAI_FILE.name} — moi giong Viet se mac dinh realmap")
        return {}
    return json.loads(PHAN_LOAI_FILE.read_text(encoding="utf-8"))


PHAN_LOAI = doc_phan_loai()


def piper_fields(lang_dir: Path, voice_dir: Path, name: str) -> dict:
    """
    Trường cho giọng **Piper**. Thiếu `g2p` = thế hệ realmap (đường mặc định, 46 giọng Việt).

    Giọng ngoại ngữ Piper (18 giọng Anh) luôn đi đường espeak, và mã ngôn ngữ lấy từ chính
    config của giọng — mỗi giọng một bản train khác nhau, có giọng ghi `en`, có giọng `en-us`.
    """
    if lang_dir.name == "Tiếng Việt":
        if PHAN_LOAI.get(name, {}).get("engine") != "espeak":
            return {}
        return {"g2p": "espeak", "lang": "vi"}

    cfg = voice_dir / f"{name}.onnx.json"
    ma = "en-us"
    if cfg.exists():
        try:
            ma = (json.loads(cfg.read_text(encoding="utf-8")).get("espeak") or {}).get("voice") or ma
        except Exception:  # noqa: BLE001
            pass
    return {"g2p": "espeak", "lang": ma}


def kokoro_fields(name: str) -> dict:
    """
    Các trường app cần để chạy một giọng Kokoro. Rỗng nếu đây là giọng Piper.

    App đọc `engine` để biết đơn vị tải (giọng lẻ hay bộ máy dùng chung), `model` để biết ghép
    với bộ máy nào, `ref` là tên trong bank, `lang`+`g2p` để chọn đường phiên âm. Thiếu trường
    nào thì app coi giọng đó là Piper và sẽ đi tìm một file .onnx không tồn tại.
    """
    if not RE_KOKORO.match(name):
        return {}
    lang, g2p = KOKORO_LANG[name[0]]
    model = "kokoro/v1.1-zh" if RE_ZH_V11.match(name) else "kokoro/v1.0"
    return {"engine": "kokoro", "model": model, "ref": name, "lang": lang, "g2p": g2p}


def build_voice_entry(lang_dir: Path, voice_dir: Path) -> dict | None:
    name = voice_dir.name
    wav_path = voice_dir / f"{name}.wav"
    if not wav_path.exists():
        print(f"  [bo qua] khong co demo .wav: {name}")
        return None

    slug = f"{slugify(lang_dir.name)}--{slugify(name)}"
    mp3_path = AUDIO_OUT / f"{slug}.mp3"
    if not mp3_path.exists():
        encode_mp3(wav_path, mp3_path)

    return {
        "id": slug,
        "name": name,
        "language": lang_dir.name,
        "audio": f"audio/{slug}.mp3",
        "duration": probe_duration(mp3_path),
        "sizeKb": round(mp3_path.stat().st_size / 1024),
        "script": read_script(voice_dir / f"{name}.txt"),
        # Giọng Kokoro thì không phải giọng Piper — hai nhánh loại trừ nhau.
        **(kokoro_fields(name) or piper_fields(lang_dir, voice_dir, name)),
    }


def main() -> int:
    if not VOICES_DIR.exists():
        print(f"Khong tim thay thu muc: {VOICES_DIR}")
        return 1

    AUDIO_OUT.mkdir(parents=True, exist_ok=True)
    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)

    voices = []
    for lang_dir in sorted(VOICES_DIR.iterdir()):
        if not lang_dir.is_dir():
            continue
        voice_dirs = sorted(d for d in lang_dir.iterdir() if d.is_dir())
        if not voice_dirs:
            continue
        print(f"[{lang_dir.name}] {len(voice_dirs)} giong")
        for voice_dir in voice_dirs:
            entry = build_voice_entry(lang_dir, voice_dir)
            if entry:
                voices.append(entry)
                print(f"  + {entry['name']:<32} {entry['duration']}s  {entry['sizeKb']}KB")

    # Chỉ khai bộ máy nào THẬT SỰ có giọng dùng tới. Khai thừa là app hiện một cục 350 MB cho
    # khách tải mà không giọng nào dùng.
    es = [v for v in voices if v.get("g2p") == "espeak" and not v.get("engine")]
    print(f"\n  giong Piper can espeak-ng: {len(es)}")
    for v in es:
        print(f"    {v['language']:14} {v['name']:22} lang={v['lang']}")

    dung_toi = {v["model"] for v in voices if v.get("model")}
    engines = {
        eid: {
            **cau_hinh,
            "bytes": sum(f["bytes"] for f in cau_hinh["files"]),
        }
        for eid, cau_hinh in ENGINES.items()
        if eid in dung_toi
    }

    DATA_OUT.write_text(
        json.dumps({"voices": voices, "engines": engines}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total_mb = sum(v["sizeKb"] for v in voices) / 1024
    kokoro = sum(1 for v in voices if v.get("engine") == "kokoro")
    print(f"\nXong: {len(voices)} giong ({kokoro} Kokoro, {len(voices)-kokoro} Piper)")
    for eid, e in engines.items():
        print(f"  bo may {eid}: {e['bytes']/1e6:.0f} MB, {sum(1 for v in voices if v.get('model')==eid)} giong")
    print(f"tong audio nghe thu {total_mb:.1f} MB -> {DATA_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
