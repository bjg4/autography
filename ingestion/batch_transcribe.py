#!/usr/bin/env python3
"""
Batch transcription of audio files using Parakeet MLX.
Outputs Lenny's-style markdown with YAML frontmatter.

Usage:
    python batch_transcribe.py ./audio/ --metadata ./audio/metadata --output ./episodes/
    python batch_transcribe.py ./audio/*.mp3 --output ./episodes/ --speaker "David Senra"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Iterator

import numpy as np
import yaml

try:
    from parakeet_mlx import from_pretrained
except ImportError:
    print("Error: parakeet_mlx not installed. Run: pip install parakeet-mlx")
    sys.exit(1)

# Supported audio formats
AUDIO_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".flac", ".ogg", ".webm"}


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


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def format_duration(seconds: float) -> str:
    """Format duration as human-readable string."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')[:50]


def load_metadata(metadata_dir: Path, audio_file: Path) -> dict | None:
    """Load metadata JSON for an audio file."""
    # Try video ID based filename (e.g., abc123.mp3 -> abc123.json)
    video_id = audio_file.stem
    metadata_file = metadata_dir / f"{video_id}.json"

    if metadata_file.exists():
        with open(metadata_file) as f:
            return json.load(f)

    return None


def transcribe_to_markdown(
    file_path: Path,
    model,
    output_dir: Path,
    metadata: dict | None = None,
    speaker: str = "Speaker",
    channel: str = "Podcast",
) -> bool:
    """Transcribe audio file and output as Lenny's-style markdown."""
    print(f"Processing: {file_path.name}")
    start_time = time.time()

    try:
        # Parakeet expects a file path, not numpy array
        result = model.transcribe(str(file_path))

        # Get duration from last sentence end time or estimate
        if result.sentences:
            duration_seconds = result.sentences[-1].end
        else:
            # Fallback: estimate from file size (rough estimate for mp3)
            duration_seconds = file_path.stat().st_size / (128 * 1024 / 8)  # 128kbps

        print(f"  Duration: {duration_seconds/60:.1f} minutes")

        processing_time = time.time() - start_time
        rtf = duration_seconds / processing_time if processing_time > 0 else 0
        print(f"  Transcribed in {processing_time:.1f}s (RTF: {rtf:.1f}x realtime)")

        # Build frontmatter from metadata or defaults
        if metadata:
            subject = metadata.get("subject", file_path.stem)
            title = metadata.get("title", file_path.stem)
            youtube_url = metadata.get("youtube_url", "")
            video_id = metadata.get("id", "")
            publish_date = metadata.get("publish_date", "")
            channel = metadata.get("channel", channel)
            slug = metadata.get("slug", slugify(subject))
        else:
            subject = file_path.stem
            title = file_path.stem
            youtube_url = ""
            video_id = ""
            publish_date = time.strftime("%Y-%m-%d")
            slug = slugify(subject)

        frontmatter = {
            "subject": subject,
            "title": title,
            "youtube_url": youtube_url,
            "video_id": video_id,
            "publish_date": publish_date,
            "duration_seconds": round(duration_seconds, 1),
            "duration": format_duration(duration_seconds),
            "channel": channel,
            "keywords": [],  # TODO: auto-generate keywords
        }

        # Format transcript with timestamps
        # Group sentences into ~30 second chunks for readability
        transcript_lines = []
        current_chunk = []
        chunk_start = 0

        for sent in result.sentences:
            if not sent.text.strip():
                continue

            if not current_chunk:
                chunk_start = sent.start

            current_chunk.append(sent.text.strip())

            # Start new chunk every ~30 seconds
            if sent.end - chunk_start >= 30:
                timestamp = format_timestamp(chunk_start)
                text = " ".join(current_chunk)
                transcript_lines.append(f"{speaker} ({timestamp}):\n{text}\n")
                current_chunk = []

        # Don't forget the last chunk
        if current_chunk:
            timestamp = format_timestamp(chunk_start)
            text = " ".join(current_chunk)
            transcript_lines.append(f"{speaker} ({timestamp}):\n{text}\n")

        # Build markdown document
        markdown = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()}
---

# {title}

## Transcript

{"".join(transcript_lines)}"""

        # Output to episodes/{slug}/transcript.md
        episode_dir = output_dir / slug
        episode_dir.mkdir(parents=True, exist_ok=True)
        output_file = episode_dir / "transcript.md"

        with open(output_file, "w") as f:
            f.write(markdown)

        print(f"  Saved: {output_file}")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch transcribe audio files to Lenny's-style markdown"
    )
    parser.add_argument("input", type=Path, help="Input file or directory")
    parser.add_argument(
        "--output", "-o", type=Path, default=Path("./episodes"),
        help="Output directory for episodes"
    )
    parser.add_argument(
        "--metadata", "-m", type=Path,
        help="Directory containing metadata JSON files"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true",
        help="Search recursively for audio files"
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip files already transcribed"
    )
    parser.add_argument(
        "--speaker", "-s", type=str, default="David Senra",
        help="Default speaker name for transcripts"
    )
    parser.add_argument(
        "--channel", "-c", type=str, default="Founders Podcast",
        help="Default channel name"
    )
    args = parser.parse_args()

    audio_files = list(find_audio_files(args.input, args.recursive))

    if not audio_files:
        print(f"No audio files found in {args.input}")
        sys.exit(1)

    print(f"Found {len(audio_files)} audio files")

    # Auto-detect metadata directory
    metadata_dir = args.metadata
    if not metadata_dir and args.input.is_dir():
        potential_metadata = args.input / "metadata"
        if potential_metadata.exists():
            metadata_dir = potential_metadata
            print(f"Auto-detected metadata directory: {metadata_dir}")

    if args.skip_existing:
        existing_slugs = {d.name for d in args.output.iterdir() if d.is_dir()} if args.output.exists() else set()
        # This is imperfect since we'd need metadata to know the slug, but it helps
        before = len(audio_files)
        audio_files = [f for f in audio_files if f.stem not in existing_slugs]
        skipped = before - len(audio_files)
        if skipped:
            print(f"Skipping {skipped} already transcribed")

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

        # Load metadata if available
        metadata = None
        if metadata_dir:
            metadata = load_metadata(metadata_dir, file)

        success = transcribe_to_markdown(
            file, model, args.output,
            metadata=metadata,
            speaker=args.speaker,
            channel=args.channel,
        )

        if success:
            successful += 1
        else:
            failed += 1

    total_time = time.time() - total_start
    print(f"\n{'='*50}")
    print(f"Completed: {successful} successful, {failed} failed")
    print(f"Total time: {total_time/60:.1f} minutes")


if __name__ == "__main__":
    main()
