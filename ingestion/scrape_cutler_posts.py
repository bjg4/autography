#!/usr/bin/env python3
"""
Scrape John Cutler posts from various sources (Substack, Medium, Amplitude, GitHub Pages).
Saves each post as markdown with YAML frontmatter.
"""

import os
import re
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import subprocess

# Check for required packages
try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "lxml"])
    import requests
    from bs4 import BeautifulSoup

# Rate limiting
REQUEST_DELAY = 1.5  # seconds between requests

def parse_curated_posts(filepath: str) -> list[dict]:
    """Parse the curated-posts.md file to extract URLs and titles."""
    posts = []
    current_category = "Uncategorized"

    with open(filepath, 'r') as f:
        content = f.read()

    # Find all numbered entries with URLs
    pattern = r'\d+\.\s+\*\*(.+?)\*\*.*?\n\s+(https?://[^\s]+)'
    matches = re.findall(pattern, content)

    for title, url in matches:
        # Clean up title
        title = title.strip()
        url = url.strip()

        # Determine source type
        if 'substack.com' in url:
            source = 'substack'
        elif 'medium.com' in url:
            source = 'medium'
        elif 'amplitude.com' in url:
            source = 'amplitude'
        elif 'github.io' in url:
            source = 'tbm2020'
        elif 'cutle.fish' in url:
            source = 'cutlefish'
        else:
            source = 'unknown'

        posts.append({
            'title': title,
            'url': url,
            'source': source
        })

    return posts


def fetch_substack(url: str) -> dict:
    """Fetch content from Substack post."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    # Get title
    title_elem = soup.find('h1', class_='post-title') or soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

    # Get date
    date_elem = soup.find('time')
    publish_date = date_elem.get('datetime', '')[:10] if date_elem else ""

    # Get content - Substack uses div.body or article
    content_elem = soup.find('div', class_='body') or soup.find('article')

    if content_elem:
        # Remove subscription prompts and footers
        for elem in content_elem.find_all(['div', 'section'], class_=lambda x: x and ('subscribe' in x.lower() or 'footer' in x.lower())):
            elem.decompose()

        content = extract_markdown_content(content_elem)
    else:
        content = ""

    return {
        'title': title,
        'content': content,
        'publish_date': publish_date,
        'url': url
    }


def fetch_medium(url: str) -> dict:
    """Fetch content from Medium post using freedium proxy to bypass paywall."""
    # Medium blocks scrapers, use freedium.cfd proxy
    parsed = urlparse(url)
    freedium_url = f"https://freedium.cfd/{url}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        response = requests.get(freedium_url, headers=headers, timeout=30)
        response.raise_for_status()
    except:
        # Fall back to direct Medium (will likely fail but try anyway)
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    # Get title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

    # Get date from meta
    date_meta = soup.find('meta', {'property': 'article:published_time'})
    publish_date = date_meta['content'][:10] if date_meta else ""

    # Get article content
    article = soup.find('article')

    if article:
        # Remove claps, follow buttons, etc.
        for elem in article.find_all(['button', 'aside']):
            elem.decompose()

        content = extract_markdown_content(article)
    else:
        content = ""

    return {
        'title': title,
        'content': content,
        'publish_date': publish_date,
        'url': url
    }


def fetch_amplitude(url: str) -> dict:
    """Fetch content from Amplitude blog."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    # Get title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

    # Try to find publish date
    publish_date = ""

    # Get main content - Amplitude blogs vary in structure
    content_elem = soup.find('article') or soup.find('main') or soup.find('div', class_='content')

    if content_elem:
        content = extract_markdown_content(content_elem)
    else:
        content = ""

    return {
        'title': title,
        'content': content,
        'publish_date': publish_date,
        'url': url
    }


def fetch_tbm2020(url: str) -> dict:
    """Fetch content from TBM 2020 GitHub pages (johnpcutler.github.io)."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    # The TBM 2020 site is a single-page book with many sections
    # We'll extract the whole thing or specific sections
    title = "TBM 2020 - The Beautiful Mess"

    content_elem = soup.find('main') or soup.find('article') or soup.find('body')

    if content_elem:
        content = extract_markdown_content(content_elem)
    else:
        content = ""

    return {
        'title': title,
        'content': content,
        'publish_date': '2020-01-01',
        'url': url
    }


def fetch_cutlefish(url: str) -> dict:
    """Fetch content from cutle.fish blog."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    # Get title
    title_elem = soup.find('h1')
    title = title_elem.get_text(strip=True) if title_elem else "Untitled"

    # Get main content
    content_elem = soup.find('article') or soup.find('main') or soup.find('div', class_='post')

    if content_elem:
        content = extract_markdown_content(content_elem)
    else:
        content = ""

    return {
        'title': title,
        'content': content,
        'publish_date': '',
        'url': url
    }


def extract_markdown_content(element) -> str:
    """Convert HTML element to markdown-ish text."""
    lines = []

    for child in element.descendants:
        if child.name == 'h1':
            lines.append(f"\n# {child.get_text(strip=True)}\n")
        elif child.name == 'h2':
            lines.append(f"\n## {child.get_text(strip=True)}\n")
        elif child.name == 'h3':
            lines.append(f"\n### {child.get_text(strip=True)}\n")
        elif child.name == 'h4':
            lines.append(f"\n#### {child.get_text(strip=True)}\n")
        elif child.name == 'p':
            text = child.get_text(strip=True)
            if text:
                lines.append(f"\n{text}\n")
        elif child.name == 'li':
            text = child.get_text(strip=True)
            if text:
                lines.append(f"- {text}")
        elif child.name == 'blockquote':
            text = child.get_text(strip=True)
            if text:
                lines.append(f"\n> {text}\n")

    # Clean up the text
    content = '\n'.join(lines)
    # Remove multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def save_post(post_data: dict, output_dir: Path, post_id: str):
    """Save post as markdown with YAML frontmatter."""
    frontmatter = f"""---
title: "{post_data['title'].replace('"', "'")}"
author: John Cutler
source_url: {post_data['url']}
publish_date: '{post_data.get('publish_date', '')}'
scraped_date: '{datetime.now().strftime("%Y-%m-%d")}'
---

"""
    content = frontmatter + post_data['content']

    output_file = output_dir / f"{post_id}.md"
    with open(output_file, 'w') as f:
        f.write(content)

    return output_file


def url_to_id(url: str, title: str) -> str:
    """Generate a clean ID from URL or title."""
    # Try to extract from URL path
    parsed = urlparse(url)
    path = parsed.path.strip('/')

    if path:
        # Get last segment
        slug = path.split('/')[-1]
        # Clean up
        slug = re.sub(r'[^\w\-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-').lower()
        if slug and len(slug) > 3:
            return slug[:60]

    # Fall back to title
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s]+', '-', slug)
    return slug[:60]


def main():
    parser = argparse.ArgumentParser(description='Scrape John Cutler posts')
    parser.add_argument('--curated-file', '-c',
                        default='data/john-cutler/curated-posts.md',
                        help='Path to curated posts file')
    parser.add_argument('--output-dir', '-o',
                        default='data/john-cutler/posts',
                        help='Output directory for scraped posts')
    parser.add_argument('--skip-existing', action='store_true',
                        help='Skip posts that already exist')
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit number of posts to scrape (0 = all)')
    parser.add_argument('--source', choices=['substack', 'medium', 'amplitude', 'tbm2020', 'cutlefish', 'all'],
                        default='all', help='Only scrape specific source')

    args = parser.parse_args()

    # Setup paths
    script_dir = Path(__file__).parent.parent
    curated_file = script_dir / args.curated_file
    output_dir = script_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse posts list
    print(f"Reading curated posts from {curated_file}...")
    posts = parse_curated_posts(curated_file)
    print(f"Found {len(posts)} posts")

    # Filter by source if specified
    if args.source != 'all':
        posts = [p for p in posts if p['source'] == args.source]
        print(f"Filtered to {len(posts)} {args.source} posts")

    # Apply limit
    if args.limit > 0:
        posts = posts[:args.limit]
        print(f"Limited to {len(posts)} posts")

    # Scrape each post
    scraped = 0
    failed = 0
    skipped = 0

    fetchers = {
        'substack': fetch_substack,
        'medium': fetch_medium,
        'amplitude': fetch_amplitude,
        'tbm2020': fetch_tbm2020,
        'cutlefish': fetch_cutlefish,
    }

    for i, post in enumerate(posts, 1):
        post_id = url_to_id(post['url'], post['title'])
        output_file = output_dir / f"{post_id}.md"

        if args.skip_existing and output_file.exists():
            print(f"[{i}/{len(posts)}] Skipping (exists): {post['title'][:50]}...")
            skipped += 1
            continue

        print(f"[{i}/{len(posts)}] {post['source']}: {post['title'][:50]}...")

        fetcher = fetchers.get(post['source'])
        if not fetcher:
            print(f"  Warning: No fetcher for source '{post['source']}', skipping")
            failed += 1
            continue

        try:
            post_data = fetcher(post['url'])

            if not post_data['content']:
                print(f"  Warning: No content extracted")
                failed += 1
                continue

            saved_path = save_post(post_data, output_dir, post_id)
            print(f"  Saved: {saved_path.name} ({len(post_data['content'])} chars)")
            scraped += 1

            # Rate limit
            time.sleep(REQUEST_DELAY)

        except Exception as e:
            print(f"  Error: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Complete!")
    print(f"  Scraped: {scraped}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print(f"  Output:  {output_dir}")


if __name__ == '__main__':
    main()
