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

HERE = Path(__file__).resolve().parent.parent
VOICES_DIR = HERE.parent / "voices"
AUDIO_OUT = HERE / "audio"
DATA_OUT = HERE / "data" / "voices.json"

MP3_BITRATE = "64k"
SCRIPT_PREVIEW_CHARS = 400


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

    DATA_OUT.write_text(
        json.dumps({"voices": voices}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    total_mb = sum(v["sizeKb"] for v in voices) / 1024
    print(f"\nXong: {len(voices)} giong, tong audio {total_mb:.1f} MB -> {DATA_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
