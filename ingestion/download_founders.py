#!/usr/bin/env python3
"""
Download Founders Podcast episodes from YouTube.

Usage:
    python download_founders.py --output ./data/founders/audio
    python download_founders.py --priority 100 --output ./data/founders/audio
    python download_founders.py --list-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

FOUNDERS_CHANNEL = "https://www.youtube.com/@FoundersPodcast"

# Priority episodes based on curated lists and research
PRIORITY_KEYWORDS = {
    # Tier 1: Top 30 from curated lists
    "Charlie Munger", "Sam Zell", "Rockefeller", "Daniel Ludwig",
    "Sam Zemurray", "Samuel Zemurray", "David Ogilvy", "Ed Thorp",
    "James Dyson", "Estée Lauder", "Estee Lauder", "Anna Wintour",
    "Les Schwab", "Jim Simons", "Todd Graves", "Jensen Huang",
    "Elon Musk", "Bill Gates", "Bernard Arnault", "Kobe Bryant",
    "Brunello Cucinelli", "Edwin Land", "Sam Walton", "Jeff Bezos",
    "Jimmy Iovine", "Ken Griffin", "Enzo Ferrari", "Michael Jordan",
    "Chung Ju-yung", "Hyundai",

    # Tier 2: High value
    "Henry Ford", "Steve Jobs", "Walt Disney", "Larry Ellison",
    "Bruce Springsteen", "Rick Rubin", "Yvon Chouinard", "Warren Buffett",
    "Phil Knight", "Howard Schultz", "Ray Kroc", "Andrew Carnegie",
    "J.P. Morgan", "Thomas Edison", "Benjamin Franklin", "Napoleon",
    "Jony Ive", "Edward Bernays", "Working Backwards", "Leonardo Del Vecchio",
    "Tamara Mellon", "Koenigsegg", "Jiro Ono", "Michael Dell",
    "Daniel Ek", "Richard Branson", "Oprah", "Sara Blakely",
    "Reed Hastings", "Marc Andreessen",

    # Tier 3: Tech pioneers
    "Paul Graham", "Peter Thiel", "Larry Page", "Sergey Brin",
    "Mark Zuckerberg", "Jack Dorsey", "Travis Kalanick", "Brian Chesky",
    "Drew Houston", "Stewart Butterfield",

    # Tier 3: Finance
    "George Soros", "Ray Dalio", "Carl Icahn", "Michael Milken",
    "John Paulson", "David Tepper", "Stanley Druckenmiller",
    "Paul Tudor Jones", "Seth Klarman", "Howard Marks",

    # Tier 3: Consumer/Retail
    "Ralph Lauren", "Coco Chanel", "Ingvar Kamprad", "IKEA",
    "Herb Kelleher", "Southwest", "Fred Smith", "FedEx",
    "John Mackey", "Whole Foods", "Chip Wilson", "Lululemon",
    "James Sinegal", "Costco", "Sol Price", "Les Wexner",

    # Tier 3: International
    "Akio Morita", "Sony", "Konosuke Matsushita", "Soichiro Honda",
    "Honda", "Toyota", "Jack Ma", "Masayoshi Son", "Ratan Tata",
    "Li Ka-shing",
}


def get_video_list(channel_url: str) -> list[dict]:
    """Get list of all videos from a YouTube channel."""
    print(f"Fetching video list from {channel_url}...")

    result = subprocess.run(
        [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s\t%(title)s\t%(duration)s",
            f"{channel_url}/videos"
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            videos.append({
                "id": parts[0],
                "title": parts[1],
                "duration": parts[2] if len(parts) > 2 else "unknown"
            })

    return videos


def filter_priority(videos: list[dict], keywords: set[str]) -> list[dict]:
    """Filter videos to only priority episodes."""
    priority = []
    for video in videos:
        title_lower = video["title"].lower()
        for keyword in keywords:
            if keyword.lower() in title_lower:
                priority.append(video)
                break
    return priority


def download_videos(videos: list[dict], output_dir: Path):
    """Download videos as audio files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_file = output_dir / "downloaded.txt"

    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] Downloading: {video['title'][:60]}...")

        cmd = [
            "yt-dlp",
            f"https://www.youtube.com/watch?v={video['id']}",
            "-o", str(output_dir / "%(title)s.%(ext)s"),
            "--download-archive", str(archive_file),
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  Warning: {result.stderr[:100]}")
        else:
            print(f"  Done!")


def main():
    parser = argparse.ArgumentParser(description="Download Founders Podcast episodes")
    parser.add_argument("--output", "-o", type=Path, default=Path("./data/founders/audio"))
    parser.add_argument("--priority", type=int, help="Only download top N priority episodes")
    parser.add_argument("--list-only", action="store_true", help="Just list episodes")
    parser.add_argument("--all", action="store_true", help="Download all episodes")
    args = parser.parse_args()

    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: yt-dlp not installed. Run: pip install yt-dlp")
        sys.exit(1)

    videos = get_video_list(FOUNDERS_CHANNEL)
    print(f"Found {len(videos)} total videos")

    if not args.all:
        videos = filter_priority(videos, PRIORITY_KEYWORDS)
        print(f"Filtered to {len(videos)} priority episodes")

    if args.priority:
        videos = videos[:args.priority]
        print(f"Limited to top {args.priority}")

    if args.list_only:
        print("\nEpisodes:")
        for i, v in enumerate(videos, 1):
            print(f"  {i}. {v['title']}")

        with open("founders_episodes.json", "w") as f:
            json.dump(videos, f, indent=2)
        print(f"\nSaved to founders_episodes.json")
    else:
        print(f"\nDownloading {len(videos)} episodes to {args.output}...")
        download_videos(videos, args.output)
        print("\nDone!")


if __name__ == "__main__":
    main()
