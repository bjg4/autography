#!/usr/bin/env python3
"""
Extract EPUB books to markdown chapters with YAML frontmatter.

Usage:
    python extract_epub.py <epub_path> <output_dir> [--book-title "Title"]

Example:
    python extract_epub.py data/books/continuous-discovery.epub data/books/extracted/cdh --book-title "Continuous Discovery Habits"
"""

import argparse
import re
from datetime import date
from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')[:50]


def html_to_markdown(html_content: str) -> str:
    """Convert HTML content to markdown."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'nav']):
        element.decompose()

    # Convert headers
    for i in range(1, 7):
        for tag in soup.find_all(f'h{i}'):
            tag.replace_with(f"\n{'#' * i} {tag.get_text().strip()}\n\n")

    # Convert paragraphs
    for tag in soup.find_all('p'):
        tag.replace_with(f"\n{tag.get_text().strip()}\n")

    # Convert lists
    for ul in soup.find_all('ul'):
        items = []
        for li in ul.find_all('li'):
            items.append(f"- {li.get_text().strip()}")
        ul.replace_with('\n' + '\n'.join(items) + '\n')

    for ol in soup.find_all('ol'):
        items = []
        for i, li in enumerate(ol.find_all('li'), 1):
            items.append(f"{i}. {li.get_text().strip()}")
        ol.replace_with('\n' + '\n'.join(items) + '\n')

    # Convert emphasis
    for tag in soup.find_all(['strong', 'b']):
        tag.replace_with(f"**{tag.get_text()}**")

    for tag in soup.find_all(['em', 'i']):
        tag.replace_with(f"*{tag.get_text()}*")

    # Get text and clean up
    text = soup.get_text()

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' +', ' ', text)

    return text.strip()


def extract_chapter_title(soup: BeautifulSoup) -> str:
    """Extract chapter title from HTML."""
    # Try h1 first
    h1 = soup.find('h1')
    if h1:
        return h1.get_text().strip()

    # Try h2
    h2 = soup.find('h2')
    if h2:
        return h2.get_text().strip()

    # Try title tag
    title = soup.find('title')
    if title:
        return title.get_text().strip()

    return "Untitled"


def create_frontmatter(title: str, chapter_num: int, book_title: str, author: str) -> str:
    """Create YAML frontmatter for a chapter."""
    # Escape quotes in title
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


def extract_epub(epub_path: str, output_dir: str, book_title: str = None, author: str = "Unknown"):
    """Extract an EPUB book to markdown chapters."""
    epub_path = Path(epub_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not book_title:
        book_title = epub_path.stem.replace('-', ' ').replace('_', ' ').title()

    print(f"Extracting: {epub_path.name}")
    print(f"Book title: {book_title}")

    # Open EPUB
    book = epub.read_epub(str(epub_path))

    # Get metadata
    epub_title = book.get_metadata('DC', 'title')
    if epub_title and not book_title:
        book_title = epub_title[0][0]

    epub_author = book.get_metadata('DC', 'creator')
    if epub_author and author == "Unknown":
        author = epub_author[0][0]

    print(f"Author: {author}")

    # Extract chapters
    chapters = []
    full_text = []
    chapter_num = 0

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content = item.get_content().decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')

            # Skip empty or navigation-only pages
            text_content = soup.get_text().strip()
            if len(text_content) < 100:
                continue

            chapter_num += 1
            title = extract_chapter_title(soup)
            markdown = html_to_markdown(content)

            chapters.append({
                'title': title,
                'content': markdown,
                'number': chapter_num
            })
            full_text.append(markdown)

    print(f"Found {len(chapters)} chapters")

    # Write each chapter
    for ch in chapters:
        filename = f"ch{ch['number']:02d}-{slugify(ch['title'])}.md"
        filepath = output_dir / filename

        frontmatter = create_frontmatter(ch['title'], ch['number'], book_title, author)
        content = frontmatter + ch['content']

        filepath.write_text(content)
        print(f"  Written: {filename} ({len(ch['content'])} chars)")

    # Write full book
    full_content = '\n\n---\n\n'.join(full_text)
    full_path = output_dir / "full-book.md"
    full_frontmatter = f"""---
title: "{book_title}"
author: {author}
source_type: book
scraped_date: '{date.today().isoformat()}'
---

"""
    full_path.write_text(full_frontmatter + full_content)
    print(f"  Written: full-book.md ({len(full_content)} chars)")

    print(f"\nExtraction complete! {len(chapters)} chapters written to {output_dir}")
    return chapters


def main():
    parser = argparse.ArgumentParser(description='Extract EPUB book to markdown chapters')
    parser.add_argument('epub_path', help='Path to EPUB file')
    parser.add_argument('output_dir', help='Output directory for markdown files')
    parser.add_argument('--book-title', '-t', help='Book title (default: inferred from metadata)')
    parser.add_argument('--author', '-a', default='Unknown', help='Book author')

    args = parser.parse_args()

    extract_epub(args.epub_path, args.output_dir, args.book_title, args.author)


if __name__ == '__main__':
    main()
