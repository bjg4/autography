#!/usr/bin/env python3
"""Batch transcribe remaining David Senra episodes: Michael Dell, Daniel Ek"""

from batch_david_senra import (
    download_episode, save_metadata, transcribe_episode, cleanup_audio,
    format_duration, EPISODES_DIR
)
import time

REMAINING = [
    {
        "id": "michael-dell",
        "title": "Michael Dell, Dell Technologies | David Senra",
        "subject": "Michael Dell",
        "slug": "michael-dell",
        "url": "https://traffic.megaphone.fm/SCIM5779563224.mp3",
        "duration_seconds": 5439,
        "publish_date": "2025-10-12",
        "channel": "David Senra Podcast",
    },
    {
        "id": "daniel-ek",
        "title": "Daniel Ek, Spotify | David Senra",
        "subject": "Daniel Ek",
        "slug": "daniel-ek",
        "url": "https://traffic.megaphone.fm/SCIM1812315285.mp3",
        "duration_seconds": 7751,
        "publish_date": "2025-09-28",
        "channel": "David Senra Podcast",
    },
]

def main():
    print("=" * 60)
    print("Remaining David Senra Episodes")
    print("=" * 60)

    total_duration = sum(ep["duration_seconds"] for ep in REMAINING)
    print(f"\nEpisodes: {len(REMAINING)}")
    print(f"Total duration: {format_duration(total_duration)}")
    print()

    start_time = time.time()

    for i, episode in enumerate(REMAINING, 1):
        print(f"\n[{i}/{len(REMAINING)}] {episode['subject']}")
        print("-" * 40)

        ep_start = time.time()

        audio_path = download_episode(episode)
        if not audio_path:
            continue

        metadata_path = save_metadata(episode)
        transcript_path = transcribe_episode(audio_path, metadata_path, episode)

        if transcript_path:
            cleanup_audio(audio_path)

        ep_time = time.time() - ep_start
        print(f"  Completed in {format_duration(int(ep_time))}")

    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"COMPLETE - Total time: {format_duration(int(total_time))}")
    print(f"Transcripts: {EPISODES_DIR}")

if __name__ == "__main__":
    main()
