#!/usr/bin/env python3
"""
Extract PDF books to markdown chapters with YAML frontmatter.

Usage:
    python extract_book.py <pdf_path> <output_dir> [--book-title "Title"]

Example:
    python extract_book.py data/books/shape-up.pdf data/books/extracted/shape-up --book-title "Shape Up"
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import pymupdf4llm
import pymupdf


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


def extract_toc(doc: pymupdf.Document) -> list[dict]:
    """Extract table of contents with page numbers."""
    toc = doc.get_toc()
    chapters = []
    for level, title, page in toc:
        if level <= 2:  # Only top-level and second-level entries
            chapters.append({
                'level': level,
                'title': title,
                'page': page - 1  # 0-indexed
            })
    return chapters


def split_by_chapters(md_text: str, chapters: list[dict]) -> list[dict]:
    """Split markdown text into chapters based on TOC headers."""
    if not chapters:
        # No TOC, return entire document as single chapter
        return [{'title': 'Full Text', 'content': md_text, 'number': 1}]

    # Find chapter boundaries using header patterns
    chapter_contents = []
    lines = md_text.split('\n')

    current_chapter = None
    current_content = []
    chapter_num = 0

    for line in lines:
        # Check if this line matches a chapter title
        is_chapter_header = False
        for ch in chapters:
            # Match both # Header and **Header** formats
            title_clean = ch['title'].strip()
            if (line.strip().startswith('#') and title_clean.lower() in line.lower()) or \
               (line.strip() == f"**{title_clean}**") or \
               (line.strip() == title_clean and len(line.strip()) > 3):

                # Save previous chapter
                if current_chapter and current_content:
                    chapter_contents.append({
                        'title': current_chapter,
                        'content': '\n'.join(current_content).strip(),
                        'number': chapter_num
                    })

                chapter_num += 1
                current_chapter = title_clean
                current_content = [line]
                is_chapter_header = True
                break

        if not is_chapter_header and current_chapter:
            current_content.append(line)

    # Save last chapter
    if current_chapter and current_content:
        chapter_contents.append({
            'title': current_chapter,
            'content': '\n'.join(current_content).strip(),
            'number': chapter_num
        })

    # If no chapters were detected, fall back to header-based splitting
    if not chapter_contents:
        return split_by_headers(md_text)

    return chapter_contents


def split_by_headers(md_text: str) -> list[dict]:
    """Fallback: split by top-level headers."""
    # Pattern for # headers
    pattern = r'^(#\s+.+)$'
    parts = re.split(pattern, md_text, flags=re.MULTILINE)

    chapters = []
    chapter_num = 0

    i = 0
    while i < len(parts):
        if parts[i].startswith('# '):
            title = parts[i].replace('# ', '').strip()
            content = parts[i]
            if i + 1 < len(parts):
                content += parts[i + 1]
                i += 1
            chapter_num += 1
            chapters.append({
                'title': title,
                'content': content.strip(),
                'number': chapter_num
            })
        elif parts[i].strip() and chapter_num == 0:
            # Content before first header
            chapter_num += 1
            chapters.append({
                'title': 'Introduction',
                'content': parts[i].strip(),
                'number': chapter_num
            })
        i += 1

    return chapters if chapters else [{'title': 'Full Text', 'content': md_text, 'number': 1}]


def create_frontmatter(chapter: dict, book_title: str, author: str) -> str:
    """Create YAML frontmatter for a chapter."""
    return f"""---
title: "{chapter['title']}"
author: {author}
source_type: book_chapter
book_title: "{book_title}"
chapter_number: {chapter['number']}
scraped_date: '{date.today().isoformat()}'
---

"""


def extract_book(pdf_path: str, output_dir: str, book_title: str = None, author: str = "Unknown"):
    """Extract a PDF book to markdown chapters."""
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not book_title:
        book_title = pdf_path.stem.replace('-', ' ').replace('_', ' ').title()

    print(f"Extracting: {pdf_path.name}")
    print(f"Book title: {book_title}")

    # Open PDF to get TOC
    doc = pymupdf.open(pdf_path)
    chapters_toc = extract_toc(doc)
    print(f"Found {len(chapters_toc)} TOC entries")

    # Extract full markdown using pymupdf4llm
    md_text = pymupdf4llm.to_markdown(pdf_path)
    print(f"Extracted {len(md_text)} characters of markdown")

    # Split into chapters
    chapters = split_by_chapters(md_text, chapters_toc)
    print(f"Split into {len(chapters)} chapters")

    # Write each chapter to a file
    for ch in chapters:
        filename = f"ch{ch['number']:02d}-{slugify(ch['title'])}.md"
        filepath = output_dir / filename

        frontmatter = create_frontmatter(ch, book_title, author)
        content = frontmatter + ch['content']

        filepath.write_text(content)
        print(f"  Written: {filename} ({len(ch['content'])} chars)")

    # Also write full book as single file for reference
    full_path = output_dir / "full-book.md"
    full_frontmatter = f"""---
title: "{book_title}"
author: {author}
source_type: book
scraped_date: '{date.today().isoformat()}'
---

"""
    full_path.write_text(full_frontmatter + md_text)
    print(f"  Written: full-book.md ({len(md_text)} chars)")

    doc.close()
    print(f"\nExtraction complete! {len(chapters)} chapters written to {output_dir}")
    return chapters


def main():
    parser = argparse.ArgumentParser(description='Extract PDF book to markdown chapters')
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('output_dir', help='Output directory for markdown files')
    parser.add_argument('--book-title', '-t', help='Book title (default: inferred from filename)')
    parser.add_argument('--author', '-a', default='Unknown', help='Book author')

    args = parser.parse_args()

    extract_book(args.pdf_path, args.output_dir, args.book_title, args.author)


if __name__ == '__main__':
    main()
