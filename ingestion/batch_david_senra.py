#!/usr/bin/env python3
"""
Batch download and transcribe David Senra podcast episodes.
Automatically cleans up audio files after successful transcription.

Usage:
    python batch_david_senra.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

# Episode list with metadata
EPISODES = [
    {
        "id": "john-mackey",
        "title": "John Mackey, Whole Foods Market | David Senra",
        "subject": "John Mackey",
        "slug": "john-mackey",
        "url": "https://traffic.megaphone.fm/SCIM2152741022.mp3",
        "duration_seconds": 6066,
        "publish_date": "2026-01-04",
        "channel": "David Senra Podcast",
    },
    {
        "id": "patrick-oshaughnessy",
        "title": "Patrick O'Shaughnessy, Colossus & Positive Sum | David Senra",
        "subject": "Patrick O'Shaughnessy",
        "slug": "patrick-oshaughnessy",
        "url": "https://traffic.megaphone.fm/SCIM1285749366.mp3",
        "duration_seconds": 7531,
        "publish_date": "2025-12-21",
        "channel": "David Senra Podcast",
    },
    {
        "id": "michael-ovitz",
        "title": "Michael Ovitz, Creative Artists Agency (CAA) | David Senra",
        "subject": "Michael Ovitz",
        "slug": "michael-ovitz",
        "url": "https://traffic.megaphone.fm/SCIM8202300302.mp3",
        "duration_seconds": 7645,
        "publish_date": "2025-11-23",
        "channel": "David Senra Podcast",
    },
    {
        "id": "todd-graves",
        "title": "Todd Graves, Raising Cane's | David Senra",
        "subject": "Todd Graves",
        "slug": "todd-graves",
        "url": "https://traffic.megaphone.fm/SCIM4991857217.mp3",
        "duration_seconds": 7185,
        "publish_date": "2025-11-09",
        "channel": "David Senra Podcast",
    },
    {
        "id": "brad-jacobs",
        "title": "Brad Jacobs, QXO, XPO, United Rentals & United Waste | David Senra",
        "subject": "Brad Jacobs",
        "slug": "brad-jacobs",
        "url": "https://traffic.megaphone.fm/SCIM9904752131.mp3",
        "duration_seconds": 7395,
        "publish_date": "2025-10-26",
        "channel": "David Senra Podcast",
    },
]

# Paths
BASE_DIR = Path(__file__).parent.parent
AUDIO_DIR = BASE_DIR / "data" / "david-senra" / "audio"
METADATA_DIR = AUDIO_DIR / "metadata"
EPISODES_DIR = BASE_DIR / "data" / "david-senra" / "episodes"
CHUNKED_SCRIPT = BASE_DIR / "ingestion" / "chunked_transcribe.py"
PYTHON = "/opt/homebrew/bin/python3.11"


def format_duration(seconds: int) -> str:
    """Format duration as H:MM:SS."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def download_episode(episode: dict) -> Path:
    """Download episode audio file."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = AUDIO_DIR / f"{episode['id']}.mp3"

    if audio_path.exists():
        print(f"  Audio already exists: {audio_path.name}")
        return audio_path

    print(f"  Downloading from {episode['url'][:60]}...")
    result = subprocess.run(
        ["curl", "-L", "-o", str(audio_path), episode["url"]],
        capture_output=True,
    )

    if result.returncode != 0:
        print(f"  ERROR: Download failed")
        return None

    size_mb = audio_path.stat().st_size / (1024 * 1024)
    print(f"  Downloaded: {audio_path.name} ({size_mb:.1f} MB)")
    return audio_path


def save_metadata(episode: dict) -> Path:
    """Save episode metadata JSON."""
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = METADATA_DIR / f"{episode['id']}.json"

    metadata = {
        "id": episode["id"],
        "title": episode["title"],
        "subject": episode["subject"],
        "slug": episode["slug"],
        "duration_seconds": episode["duration_seconds"],
        "duration": format_duration(episode["duration_seconds"]),
        "publish_date": episode["publish_date"],
        "youtube_url": "",
        "channel": episode["channel"],
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata_path


def transcribe_episode(audio_path: Path, metadata_path: Path, episode: dict) -> Path:
    """Transcribe episode using chunked_transcribe.py."""
    output_dir = EPISODES_DIR / episode["slug"]
    output_path = output_dir / "transcript.md"

    if output_path.exists():
        print(f"  Transcript already exists: {output_path}")
        return output_path

    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        PYTHON,
        str(CHUNKED_SCRIPT),
        str(audio_path),
        "--output", str(output_path),
        "--metadata", str(metadata_path),
        "--speaker", "David Senra",
        "--chunk-minutes", "10",
    ]

    print(f"  Transcribing ({format_duration(episode['duration_seconds'])})...")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"  ERROR: Transcription failed")
        return None

    return output_path


def cleanup_audio(audio_path: Path):
    """Delete audio file to save space."""
    if audio_path and audio_path.exists():
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        audio_path.unlink()
        print(f"  Cleaned up: {audio_path.name} ({size_mb:.1f} MB freed)")


def main():
    print("=" * 60)
    print("David Senra Podcast Batch Transcription")
    print("=" * 60)

    total_duration = sum(ep["duration_seconds"] for ep in EPISODES)
    print(f"\nEpisodes to process: {len(EPISODES)}")
    print(f"Total audio duration: {format_duration(total_duration)}")
    print(f"Estimated processing time: ~{total_duration // 13 // 60} minutes")
    print()

    start_time = time.time()
    successful = 0
    failed = []

    for i, episode in enumerate(EPISODES, 1):
        print(f"\n[{i}/{len(EPISODES)}] {episode['subject']}")
        print("-" * 40)

        ep_start = time.time()

        # Download
        audio_path = download_episode(episode)
        if not audio_path:
            failed.append(episode["subject"])
            continue

        # Save metadata
        metadata_path = save_metadata(episode)

        # Transcribe
        transcript_path = transcribe_episode(audio_path, metadata_path, episode)
        if not transcript_path:
            failed.append(episode["subject"])
            continue

        # Cleanup audio
        cleanup_audio(audio_path)

        ep_time = time.time() - ep_start
        print(f"  Completed in {format_duration(int(ep_time))}")
        successful += 1

    # Summary
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print("=" * 60)
    print(f"Successful: {successful}/{len(EPISODES)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print(f"Total time: {format_duration(int(total_time))}")
    print(f"Transcripts saved to: {EPISODES_DIR}")


if __name__ == "__main__":
    main()
