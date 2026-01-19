#!/usr/bin/env python3
"""
Chunked transcription for long audio files using Parakeet MLX.
Splits audio into segments, transcribes each, then merges results.

Usage:
    python chunked_transcribe.py audio.mp3 --output transcript.md
    python chunked_transcribe.py audio.mp3 --chunk-minutes 20 --output transcript.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

try:
    from parakeet_mlx import from_pretrained
except ImportError:
    print("Error: parakeet_mlx not installed. Run: pip install parakeet-mlx")
    sys.exit(1)


def get_audio_duration(file_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(file_path)
        ],
        capture_output=True,
        text=True
    )
    return float(result.stdout.strip())


def split_audio(file_path: Path, chunk_seconds: int, output_dir: Path) -> list[tuple[Path, float]]:
    """Split audio into chunks, returns list of (chunk_path, start_offset) tuples."""
    duration = get_audio_duration(file_path)
    chunks = []

    start = 0
    chunk_num = 0

    while start < duration:
        chunk_path = output_dir / f"chunk_{chunk_num:03d}.mp3"

        # Use ffmpeg to extract chunk
        cmd = [
            "ffmpeg", "-y", "-v", "quiet",
            "-i", str(file_path),
            "-ss", str(start),
            "-t", str(chunk_seconds),
            "-c", "copy",  # Fast copy without re-encoding
            str(chunk_path)
        ]

        subprocess.run(cmd, check=True)
        chunks.append((chunk_path, start))

        start += chunk_seconds
        chunk_num += 1

    return chunks


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


def transcribe_chunk(model, chunk_path: Path, offset: float) -> list[dict]:
    """Transcribe a single chunk and return sentences with adjusted timestamps."""
    result = model.transcribe(str(chunk_path))

    sentences = []
    for sent in result.sentences:
        sentences.append({
            "text": sent.text.strip(),
            "start": sent.start + offset,
            "end": sent.end + offset,
        })

    return sentences


def merge_sentences_to_chunks(sentences: list[dict], speaker: str, chunk_seconds: float = 30) -> list[str]:
    """Group sentences into ~30 second speaker chunks for readability."""
    transcript_lines = []
    current_chunk = []
    chunk_start = 0

    for sent in sentences:
        if not sent["text"]:
            continue

        if not current_chunk:
            chunk_start = sent["start"]

        current_chunk.append(sent["text"])

        # Start new chunk every ~30 seconds
        if sent["end"] - chunk_start >= chunk_seconds:
            timestamp = format_timestamp(chunk_start)
            text = " ".join(current_chunk)
            transcript_lines.append(f"{speaker} ({timestamp}):\n{text}\n")
            current_chunk = []

    # Don't forget the last chunk
    if current_chunk:
        timestamp = format_timestamp(chunk_start)
        text = " ".join(current_chunk)
        transcript_lines.append(f"{speaker} ({timestamp}):\n{text}\n")

    return transcript_lines


def chunked_transcribe(
    file_path: Path,
    output_path: Path,
    chunk_minutes: int = 20,
    speaker: str = "Speaker",
    metadata: dict | None = None,
) -> bool:
    """Transcribe a long audio file using chunked processing."""

    print(f"Processing: {file_path.name}")
    total_start = time.time()

    # Get total duration
    total_duration = get_audio_duration(file_path)
    print(f"  Total duration: {format_duration(total_duration)} ({total_duration:.0f}s)")

    chunk_seconds = chunk_minutes * 60
    num_chunks = int(total_duration / chunk_seconds) + 1
    print(f"  Splitting into {num_chunks} chunks of {chunk_minutes} minutes each")

    # Create temp directory for chunks
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Split audio
        print("  Splitting audio...")
        split_start = time.time()
        chunks = split_audio(file_path, chunk_seconds, temp_path)
        print(f"  Split complete in {time.time() - split_start:.1f}s")

        # Load model once
        print("  Loading Parakeet model...")
        model = from_pretrained("mlx-community/parakeet-tdt-0.6b-v2")
        print("  Model loaded!")

        # Transcribe each chunk
        all_sentences = []

        for i, (chunk_path, offset) in enumerate(chunks):
            chunk_start = time.time()
            print(f"  [{i+1}/{len(chunks)}] Transcribing chunk at {format_timestamp(offset)}...", end=" ", flush=True)

            sentences = transcribe_chunk(model, chunk_path, offset)
            all_sentences.extend(sentences)

            chunk_time = time.time() - chunk_start
            chunk_duration = get_audio_duration(chunk_path)
            rtf = chunk_duration / chunk_time if chunk_time > 0 else 0
            print(f"done in {chunk_time:.1f}s ({rtf:.1f}x realtime)")

    # Merge into transcript
    print("  Merging transcript...")
    transcript_lines = merge_sentences_to_chunks(all_sentences, speaker)

    # Build metadata
    if metadata:
        subject = metadata.get("subject", file_path.stem)
        title = metadata.get("title", file_path.stem)
        youtube_url = metadata.get("youtube_url", "")
        video_id = metadata.get("id", "")
        publish_date = metadata.get("publish_date", "")
        channel = metadata.get("channel", "Podcast")
    else:
        subject = file_path.stem
        title = file_path.stem
        youtube_url = ""
        video_id = ""
        publish_date = time.strftime("%Y-%m-%d")
        channel = "Podcast"

    frontmatter = {
        "subject": subject,
        "title": title,
        "youtube_url": youtube_url,
        "video_id": video_id,
        "publish_date": publish_date,
        "duration_seconds": round(total_duration, 1),
        "duration": format_duration(total_duration),
        "channel": channel,
        "keywords": [],
    }

    # Build markdown
    markdown = f"""---
{yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False).strip()}
---

# {title}

## Transcript

{"".join(transcript_lines)}"""

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(markdown)

    total_time = time.time() - total_start
    rtf = total_duration / total_time

    print(f"\n  Completed!")
    print(f"  Total time: {format_duration(total_time)}")
    print(f"  Overall RTF: {rtf:.1f}x realtime")
    print(f"  Output: {output_path}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Chunked transcription for long audio files")
    parser.add_argument("input", type=Path, help="Input audio file")
    parser.add_argument("--output", "-o", type=Path, help="Output markdown file")
    parser.add_argument("--chunk-minutes", "-c", type=int, default=20, help="Chunk size in minutes (default: 20)")
    parser.add_argument("--speaker", "-s", type=str, default="Speaker", help="Speaker name")
    parser.add_argument("--metadata", "-m", type=Path, help="Metadata JSON file")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Default output path
    if not args.output:
        args.output = args.input.with_suffix(".md")

    # Load metadata if provided
    metadata = None
    if args.metadata and args.metadata.exists():
        with open(args.metadata) as f:
            metadata = json.load(f)

    success = chunked_transcribe(
        args.input,
        args.output,
        chunk_minutes=args.chunk_minutes,
        speaker=args.speaker,
        metadata=metadata,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
