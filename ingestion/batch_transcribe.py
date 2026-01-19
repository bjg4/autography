#!/usr/bin/env python3
"""
Batch transcription of audio files using Parakeet MLX.

Usage:
    python batch_transcribe.py ./audio/*.mp3 --output ./transcripts/
    python batch_transcribe.py ./podcasts/ --output ./transcripts/ --recursive
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

import numpy as np
from parakeet_mlx import from_pretrained

# Supported audio formats
AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".flac", ".ogg", ".webm"}


@dataclass
class TranscriptSegment:
    """A segment of transcribed text with timing."""
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    """Full transcript with metadata."""
    source_file: str
    duration_seconds: float
    transcription: str
    segments: list[TranscriptSegment]
    model: str
    transcribed_at: str
    processing_time_seconds: float


def find_audio_files(path: Path, recursive: bool = False) -> Iterator[Path]:
    """Find all audio files in a path."""
    if path.is_file():
        if path.suffix.lower() in AUDIO_EXTENSIONS:
            yield path
    elif path.is_dir():
        pattern = "**/*" if recursive else "*"
        for file in path.glob(pattern):
            if file.is_file() and file.suffix.lower() in AUDIO_EXTENSIONS:
                yield file


def load_audio(file_path: Path, sample_rate: int = 16000) -> np.ndarray:
    """Load audio file and resample to target rate."""
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run(
            [
                "ffmpeg", "-i", str(file_path),
                "-ar", str(sample_rate),
                "-ac", "1",
                "-f", "wav",
                "-y",
                tmp_path
            ],
            capture_output=True,
            check=True
        )

        import wave
        with wave.open(tmp_path, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

        return audio
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def strip_ads(text: str) -> str:
    """Remove common podcast ad patterns from transcript."""
    ad_patterns = [
        r"this episode is brought to you by.*?(?=\.|$)",
        r"sponsored by.*?(?=\.|$)",
        r"use code \w+ for.*?(?=\.|$)",
        r"go to \w+\.com/\w+.*?(?=\.|$)",
        r"visit \w+\.com.*?(?=\.|$)",
        r"promo code.*?(?=\.|$)",
    ]

    result = text
    for pattern in ad_patterns:
        result = re.sub(pattern, "[ad removed]", result, flags=re.IGNORECASE)

    return result


def transcribe_file(
    file_path: Path,
    model,
    output_dir: Path,
    strip_ads_flag: bool = True,
) -> Transcript | None:
    """Transcribe a single audio file."""
    print(f"Processing: {file_path.name}")
    start_time = time.time()

    try:
        audio = load_audio(file_path)
        duration = len(audio) / 16000

        print(f"  Duration: {duration/60:.1f} minutes")

        result = model.transcribe(audio)
        text = result.get("transcription", "")

        if strip_ads_flag:
            text = strip_ads(text)

        segments = []
        if "segments" in result:
            for seg in result["segments"]:
                segments.append(TranscriptSegment(
                    start=seg.get("start", 0),
                    end=seg.get("end", 0),
                    text=seg.get("text", "")
                ))

        processing_time = time.time() - start_time

        transcript = Transcript(
            source_file=str(file_path),
            duration_seconds=duration,
            transcription=text,
            segments=segments,
            model="parakeet-tdt-0.6b-v2",
            transcribed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            processing_time_seconds=processing_time,
        )

        output_file = output_dir / f"{file_path.stem}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(asdict(transcript), f, indent=2)

        txt_file = output_dir / f"{file_path.stem}.txt"
        with open(txt_file, "w") as f:
            f.write(text)

        rtf = duration / processing_time if processing_time > 0 else 0
        print(f"  Done in {processing_time:.1f}s (RTF: {rtf:.1f}x realtime)")

        return transcript

    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Batch transcribe audio files with Parakeet")
    parser.add_argument("input", type=Path, help="Input file or directory")
    parser.add_argument("--output", "-o", type=Path, default=Path("./transcripts"), help="Output directory")
    parser.add_argument("--recursive", "-r", action="store_true", help="Search recursively")
    parser.add_argument("--no-strip-ads", action="store_true", help="Don't strip ad content")
    parser.add_argument("--skip-existing", action="store_true", help="Skip files already transcribed")
    args = parser.parse_args()

    audio_files = list(find_audio_files(args.input, args.recursive))

    if not audio_files:
        print(f"No audio files found in {args.input}")
        sys.exit(1)

    print(f"Found {len(audio_files)} audio files")

    if args.skip_existing:
        existing = {f.stem for f in args.output.glob("*.json")}
        audio_files = [f for f in audio_files if f.stem not in existing]
        print(f"Skipping {len(existing)} already transcribed, {len(audio_files)} remaining")

    if not audio_files:
        print("All files already transcribed!")
        sys.exit(0)

    print("Loading Parakeet model...")
    model = from_pretrained("mlx-community/parakeet-tdt-0.6b-v2")
    print("Model loaded!")

    args.output.mkdir(parents=True, exist_ok=True)

    total_start = time.time()
    successful = 0
    failed = 0

    for i, file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] ", end="")
        result = transcribe_file(file, model, args.output, strip_ads_flag=not args.no_strip_ads)
        if result:
            successful += 1
        else:
            failed += 1

    total_time = time.time() - total_start
    print(f"\n{'='*50}")
    print(f"Completed: {successful} successful, {failed} failed")
    print(f"Total time: {total_time/60:.1f} minutes")


if __name__ == "__main__":
    main()
