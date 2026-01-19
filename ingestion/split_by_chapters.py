#!/usr/bin/env python3
"""
Split full-book.md files into chapters based on text patterns.

Usage:
    python split_by_chapters.py <book_dir> --pattern "chapter|part"
"""

import argparse
import re
from datetime import date
from pathlib import Path


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')[:50]


def extract_metadata(content: str) -> dict:
    """Extract YAML frontmatter metadata."""
    if not content.startswith('---'):
        return {}

    end = content.find('---', 3)
    if end == -1:
        return {}

    yaml_text = content[3:end].strip()
    metadata = {}
    for line in yaml_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip().strip('"\'')

    return metadata


def create_frontmatter(title: str, chapter_num: int, book_title: str, author: str) -> str:
    """Create YAML frontmatter for a chapter."""
    title_escaped = title.replace('"', '\\"')
    return f"""---
title: "{title_escaped}"
author: {author}
source_type: book_chapter
book_title: "{book_title}"
chapter_number: {chapter_num}
scraped_date: '{date.today().isoformat()}'
---

"""


def split_lean_startup(book_dir: Path):
    """Split The Lean Startup by numbered chapters."""
    full_book = book_dir / 'full-book.md'
    content = full_book.read_text()

    metadata = extract_metadata(content)
    author = metadata.get('author', 'Eric Ries')
    book_title = metadata.get('title', 'The Lean Startup')

    # Remove frontmatter for processing
    if content.startswith('---'):
        content = content.split('---', 2)[2].strip()

    # Pattern: ## 1START, ## 2DEFINE, etc. or ## Part One
    pattern = r'^(## (?:Part [A-Za-z]+|[0-9]+[A-Z]+|\d+\s+[A-Z]).*?)(?=^## (?:Part|[0-9])|$)'

    # Simpler approach: split by ## followed by number or Part
    lines = content.split('\n')
    chapters = []
    current_chapter = {'title': 'Introduction', 'lines': [], 'number': 0}

    for line in lines:
        # Check for chapter header
        if re.match(r'^## (Part [A-Za-z]+|[0-9]+\s*[A-Z]|\d+[A-Z]+)', line):
            if current_chapter['lines']:
                chapters.append(current_chapter)

            # Extract title
            title = line.replace('##', '').strip()
            current_chapter = {'title': title, 'lines': [line], 'number': len(chapters) + 1}
        else:
            current_chapter['lines'].append(line)

    # Don't forget the last chapter
    if current_chapter['lines']:
        chapters.append(current_chapter)

    # Write chapters
    print(f"Found {len(chapters)} chapters in The Lean Startup")

    # Remove old single-chapter files
    for f in book_dir.glob('ch*.md'):
        f.unlink()

    for ch in chapters:
        content_text = '\n'.join(ch['lines']).strip()
        if len(content_text) < 100:
            continue

        filename = f"ch{ch['number']:02d}-{slugify(ch['title'])}.md"
        frontmatter = create_frontmatter(ch['title'], ch['number'], book_title, author)

        (book_dir / filename).write_text(frontmatter + content_text)
        print(f"  Written: {filename} ({len(content_text)} chars)")


def split_good_strategy(book_dir: Path):
    """Split Good Strategy Bad Strategy by chapter summaries."""
    full_book = book_dir / 'full-book.md'
    content = full_book.read_text()

    metadata = extract_metadata(content)
    author = metadata.get('author', 'Richard Rumelt')
    book_title = metadata.get('title', 'Good Strategy Bad Strategy')

    # Remove frontmatter for processing
    if content.startswith('---'):
        content = content.split('---', 2)[2].strip()

    # Split by "## **Chapter X Summary" pattern
    parts = re.split(r'(## \*\*Chapter \d+ Summary.*?\*\*)', content)

    chapters = []
    current_content = parts[0]  # Intro before first chapter

    if current_content.strip():
        chapters.append({'title': 'Introduction', 'content': current_content.strip(), 'number': 0})

    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            header = parts[i]
            body = parts[i + 1]

            # Extract chapter number and title
            match = re.search(r'Chapter (\d+) Summary\s*:\s*(.+?)\*\*', header)
            if match:
                num = int(match.group(1))
                title = match.group(2).strip()
                chapters.append({
                    'title': f"Chapter {num}: {title}",
                    'content': (header + body).strip(),
                    'number': num
                })

    print(f"Found {len(chapters)} chapters in Good Strategy Bad Strategy")

    # Remove old single-chapter files
    for f in book_dir.glob('ch*.md'):
        f.unlink()

    for ch in chapters:
        if len(ch['content']) < 100:
            continue

        filename = f"ch{ch['number']:02d}-{slugify(ch['title'])}.md"
        frontmatter = create_frontmatter(ch['title'], ch['number'], book_title, author)

        (book_dir / filename).write_text(frontmatter + ch['content'])
        print(f"  Written: {filename} ({len(ch['content'])} chars)")


def split_high_output(book_dir: Path):
    """Split High Output Management by PART markers."""
    full_book = book_dir / 'full-book.md'
    content = full_book.read_text()

    metadata = extract_metadata(content)
    author = metadata.get('author', 'Andy Grove')
    book_title = metadata.get('title', 'High Output Management')

    # Remove frontmatter for processing
    if content.startswith('---'):
        content = content.split('---', 2)[2].strip()

    # Split by "PART I", "PART II", etc.
    parts = re.split(r'(^PART [IVX]+.*$)', content, flags=re.MULTILINE)

    chapters = []
    current_content = parts[0]  # Intro before first part

    if current_content.strip() and len(current_content) > 500:
        chapters.append({'title': 'Introduction', 'content': current_content.strip(), 'number': 0})

    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            header = parts[i].strip()
            body = parts[i + 1]

            # Clean up the title
            title = header.replace('PART', 'Part').strip()
            chapters.append({
                'title': title,
                'content': (header + '\n\n' + body).strip(),
                'number': len(chapters)
            })

    print(f"Found {len(chapters)} parts in High Output Management")

    # Remove old single-chapter files
    for f in book_dir.glob('ch*.md'):
        f.unlink()

    for ch in chapters:
        if len(ch['content']) < 100:
            continue

        filename = f"ch{ch['number']:02d}-{slugify(ch['title'])}.md"
        frontmatter = create_frontmatter(ch['title'], ch['number'], book_title, author)

        (book_dir / filename).write_text(frontmatter + ch['content'])
        print(f"  Written: {filename} ({len(ch['content'])} chars)")


def main():
    parser = argparse.ArgumentParser(description='Split full-book.md into chapters')
    parser.add_argument('book', choices=['lean-startup', 'good-strategy', 'high-output', 'all'],
                        help='Which book to split')

    args = parser.parse_args()
    base = Path('data/books/extracted')

    if args.book == 'lean-startup' or args.book == 'all':
        split_lean_startup(base / 'lean-startup')

    if args.book == 'good-strategy' or args.book == 'all':
        split_good_strategy(base / 'good-strategy-bad-strategy')

    if args.book == 'high-output' or args.book == 'all':
        split_high_output(base / 'high-output-management')


if __name__ == '__main__':
    main()
