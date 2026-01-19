---
title: "PDF and EPUB Extraction to Markdown Chapters"
category: data-processing
tags: [pdf, epub, markdown, extraction, pymupdf, ebooklib, chunking]
problem_type: data_extraction
components: [ingestion, books]
date_solved: 2026-01-19
severity: medium
root_cause: "Different PDF structures require different extraction strategies"
---

# PDF and EPUB Extraction to Markdown Chapters

## Problem

Needed to extract 9 PM books (8 PDFs + 1 EPUB) into markdown chapters suitable for vector store indexing. Books ranged from 150k to 760k characters.

## Symptoms

1. marker-pdf failed with `TypeError: unsupported operand type(s) for |: '_GenericAlias' and 'NoneType'`
2. Some PDFs extracted as single giant files (no chapter splitting)
3. One PDF (Inspired) extracted only 594 characters from 298 pages
4. EPUB chapters had "Untitled" names

## Investigation

### marker-pdf Python Version Issue
```
surya/schema.py:143
  languages: List[str] | None = None
TypeError: unsupported operand type(s) for |: '_GenericAlias' and 'NoneType'
```
The `Type | None` union syntax requires Python 3.10+. Our environment uses Python 3.9.

### PDF Structure Variations
Checked each PDF for Table of Contents metadata:
```python
doc = pymupdf.open(pdf_path)
toc = doc.get_toc()  # Returns list of [level, title, page]
```

Results:
- Shape Up: 33 TOC entries ✓
- The Mom Test: 32 TOC entries ✓
- Hard Thing: 53 TOC entries ✓
- Design of Everyday Things: 72 TOC entries ✓
- High Output Management: 2 TOC entries (parts only)
- Good Strategy: 0 TOC entries
- Lean Startup: 0 TOC entries

### Image-Based PDF Detection
```python
page = doc[10]
print('Text:', repr(page.get_text()[:500]))  # Empty string
print('Images:', len(page.get_images()))      # 298 images
```
Inspired PDF stores pages as images - requires OCR.

## Root Cause

Three distinct issues:
1. **marker-pdf**: Dependency (surya-ocr) uses Python 3.10+ syntax
2. **No TOC PDFs**: Publisher didn't embed TOC metadata, but chapter markers exist in text
3. **Image PDFs**: Scanned or exported as images, no text layer

## Solution

### 1. Use pymupdf4llm Instead of marker-pdf

```bash
pip install pymupdf4llm
```

```python
import pymupdf4llm
import pymupdf

doc = pymupdf.open(pdf_path)
toc = doc.get_toc()  # Get chapter info
md_text = pymupdf4llm.to_markdown(pdf_path)  # Extract markdown
```

Advantages:
- Python 3.9 compatible
- Fast (~0.12s per book)
- Good markdown structure preservation

### 2. Custom Chapter Splitting Script

Created `ingestion/extract_book.py`:
- Parses TOC metadata when available
- Splits by chapter headers
- Adds YAML frontmatter to each chapter
- Handles books with or without TOC

### 3. Text Pattern Splitting for No-TOC PDFs

For books without TOC metadata, split by text patterns:

```python
# Lean Startup: ## 1START, ## 2DEFINE, ## Part One
pattern = r'^## (Part [A-Za-z]+|[0-9]+\s*[A-Z])'

# Good Strategy: ## **Chapter X Summary**
pattern = r'## \*\*Chapter \d+ Summary'
```

### 4. Size-Based Chunking for Flat Structure

High Output Management had no useful markers. Split by paragraph boundaries:

```python
TARGET_SIZE = 30000  # ~7500 tokens
for para in paragraphs:
    if current_size + len(para) > TARGET_SIZE:
        save_chunk()
        start_new_chunk()
```

### 5. EPUB Extraction

```python
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

book = epub.read_epub(epub_path)
for item in book.get_items():
    if item.get_type() == ebooklib.ITEM_DOCUMENT:
        html = item.get_content().decode('utf-8')
        markdown = html_to_markdown(html)
```

## Final Results

| Book | Method | Chapters | Characters |
|------|--------|----------|------------|
| Shape Up | TOC-based | 40 | 200k |
| The Mom Test | TOC-based | 35 | 190k |
| Hard Thing | TOC-based | 84 | 481k |
| Design of Everyday Things | TOC-based | 53 | 774k |
| Continuous Discovery Habits | EPUB | 26 | 383k |
| Lean Startup | Text patterns | 17 | 527k |
| Good Strategy | Text patterns | 19 | 153k |
| High Output Management | Size-based | 13 | 372k |
| Inspired | ❌ Needs OCR | - | - |

**Total: 287 chapters, 3.08M characters**

## Prevention Strategies

1. **Check Python version** before using marker-pdf (requires 3.10+)
2. **Always verify TOC** with `doc.get_toc()` before assuming chapter structure
3. **Test text extraction** on a few pages to detect image-based PDFs:
   ```python
   if len(doc[10].get_text()) < 100 and len(doc[10].get_images()) > 0:
       print("Warning: Image-based PDF, needs OCR")
   ```
4. **Target ~30k chars per chunk** for retrieval-friendly sizes

## Related Files

- `ingestion/extract_book.py` - PDF extraction with TOC-based splitting
- `ingestion/extract_epub.py` - EPUB to markdown conversion
- `ingestion/split_by_chapters.py` - Text pattern and size-based splitting
- `docs/decision-log.md` - Decision 006: PDF Extraction Tool

## References

- [pymupdf4llm GitHub](https://github.com/pymupdf/pymupdf4llm)
- [ebooklib Documentation](https://github.com/aerkalov/ebooklib)
- [marker-pdf](https://github.com/datalab-to/marker) (requires Python 3.10+)
