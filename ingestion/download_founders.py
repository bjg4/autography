#!/usr/bin/env python3
"""
Download Founders Podcast episodes from YouTube with metadata.

Usage:
    python download_founders.py --output ./data/founders/audio
    python download_founders.py --priority 100 --output ./data/founders/audio
    python download_founders.py --list-only
"""

from __future__ import annotations

import argparse
import json
import re
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


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')[:50]


def extract_subject_from_title(title: str) -> str:
    """Extract the subject (person/company) from episode title."""
    # Common patterns in Founders titles:
    # "#123 Steve Jobs" -> "Steve Jobs"
    # "#45 The Founder of IKEA" -> "IKEA" or try to extract name
    # "What I Learned From Sam Walton" -> "Sam Walton"

    # Remove episode number prefix
    title = re.sub(r'^#?\d+\s*[-:]?\s*', '', title)

    # Check for known subjects in title
    for keyword in PRIORITY_KEYWORDS:
        if keyword.lower() in title.lower():
            return keyword

    # Fallback: first part before common separators
    for sep in [' - ', ': ', ' | ']:
        if sep in title:
            return title.split(sep)[0].strip()

    return title[:50]


def get_video_list(channel_url: str) -> list[dict]:
    """Get list of all videos from a YouTube channel with full metadata."""
    print(f"Fetching video list from {channel_url}...")

    result = subprocess.run(
        [
            "yt-dlp",
            "--flat-playlist",
            "--print", "%(id)s\t%(title)s\t%(duration)s\t%(upload_date)s",
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
            video_id = parts[0]
            title = parts[1]
            duration_secs = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            upload_date = parts[3] if len(parts) > 3 else ""

            # Format duration as HH:MM:SS
            hours, remainder = divmod(duration_secs, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"

            # Format publish date as YYYY-MM-DD
            publish_date = ""
            if upload_date and len(upload_date) == 8:
                publish_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"

            subject = extract_subject_from_title(title)

            videos.append({
                "id": video_id,
                "title": title,
                "subject": subject,
                "slug": slugify(subject),
                "duration_seconds": duration_secs,
                "duration": duration_str,
                "publish_date": publish_date,
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": "Founders Podcast",
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
    """Download videos as audio files with metadata sidecars."""
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_file = output_dir / "downloaded.txt"
    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(exist_ok=True)

    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] Downloading: {video['title'][:60]}...")

        # Save metadata as sidecar JSON
        metadata_file = metadata_dir / f"{video['id']}.json"
        with open(metadata_file, "w") as f:
            json.dump(video, f, indent=2)

        cmd = [
            "yt-dlp",
            video["youtube_url"],
            "-o", str(output_dir / f"{video['id']}.%(ext)s"),
            "--download-archive", str(archive_file),
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  Warning: {result.stderr[:100]}")
        else:
            print(f"  Done! Metadata: {metadata_file.name}")


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
            print(f"  {i}. [{v['subject']}] {v['title'][:50]}")

        with open("founders_episodes.json", "w") as f:
            json.dump(videos, f, indent=2)
        print(f"\nSaved to founders_episodes.json")
    else:
        print(f"\nDownloading {len(videos)} episodes to {args.output}...")
        download_videos(videos, args.output)
        print("\nDone!")


if __name__ == "__main__":
    main()
