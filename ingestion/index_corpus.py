#!/usr/bin/env python3
"""
Index all markdown content into Chroma with embeddings.

Usage:
    python index_corpus.py [--reset]

Options:
    --reset    Clear existing collection and re-index everything
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter and return (metadata, body)."""
    if not content.startswith('---'):
        return {}, content

    end = content.find('---', 3)
    if end == -1:
        return {}, content

    yaml_text = content[3:end].strip()
    body = content[end + 3:].strip()

    metadata = {}
    current_key = None
    current_value = []

    for line in yaml_text.split('\n'):
        if ':' in line and not line.startswith(' '):
            # Save previous key if exists
            if current_key:
                metadata[current_key] = ' '.join(current_value).strip().strip('"\'')

            key, value = line.split(':', 1)
            current_key = key.strip()
            current_value = [value.strip()]
        elif current_key and line.startswith(' '):
            current_value.append(line.strip())

    # Don't forget last key
    if current_key:
        metadata[current_key] = ' '.join(current_value).strip().strip('"\'')

    return metadata, body


def get_source_type(filepath: Path) -> str:
    """Determine source type from file path."""
    path_str = str(filepath)

    if '/books/extracted/' in path_str:
        return 'book_chapter'
    elif '/episodes/' in path_str:
        return 'podcast_transcript'
    elif '/posts/' in path_str:
        return 'essay'
    else:
        return 'unknown'


def get_author_from_path(filepath: Path) -> str:
    """Extract author from directory structure."""
    path_str = str(filepath)

    if '/blake-green/' in path_str:
        return 'Blake Green'
    elif '/john-cutler/' in path_str:
        return 'John Cutler'
    elif '/lennys/' in path_str:
        return "Lenny's Podcast"
    elif '/david-senra/' in path_str:
        return 'David Senra'
    elif '/books/extracted/' in path_str:
        # Try to get from parent directory name
        parts = filepath.parts
        for i, part in enumerate(parts):
            if part == 'extracted' and i + 1 < len(parts):
                book_dir = parts[i + 1]
                return book_dir.replace('-', ' ').title()
    return 'Unknown'


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(' '.join(chunk_words))
        start = end - overlap  # Overlap for context continuity

    return chunks


def collect_documents(data_dir: Path, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """Collect all markdown documents with metadata, chunked for retrieval."""
    documents = []

    # Find all markdown files (excluding full-book.md files)
    for md_file in data_dir.rglob('*.md'):
        # Skip full-book files (we index chapters instead)
        if md_file.name == 'full-book.md':
            continue

        # Skip any hidden files
        if any(part.startswith('.') for part in md_file.parts):
            continue

        content = md_file.read_text()
        metadata, body = parse_frontmatter(content)

        # Base metadata for all chunks from this file
        base_meta = {
            'file_path': str(md_file),
            'title': metadata.get('title', md_file.stem),
            'author': metadata.get('author', get_author_from_path(md_file)),
            'source_type': metadata.get('source_type', get_source_type(md_file)),
            'source_url': metadata.get('source_url', ''),
            'publish_date': metadata.get('publish_date', ''),
            'book_title': metadata.get('book_title', ''),
            'chapter_number': metadata.get('chapter_number', ''),
        }

        # Chunk the body text
        chunks = chunk_text(body, chunk_size=chunk_size, overlap=overlap)

        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue

            doc = {
                'id': f"{md_file.relative_to(data_dir)}::chunk_{i}",
                'content': chunk,
                'chunk_index': i,
                'total_chunks': len(chunks),
                **base_meta
            }
            documents.append(doc)

    return documents


def index_documents(
    documents: list[dict],
    collection: chromadb.Collection,
    model: SentenceTransformer,
    batch_size: int = 32
):
    """Index documents into Chroma collection."""
    total = len(documents)
    print(f"Indexing {total} documents...")

    for i in range(0, total, batch_size):
        batch = documents[i:i + batch_size]

        # Prepare batch data
        ids = [doc['id'] for doc in batch]
        texts = [doc['content'] for doc in batch]
        metadatas = [{
            'title': doc['title'],
            'author': doc['author'],
            'source_type': doc['source_type'],
            'source_url': doc['source_url'],
            'publish_date': doc['publish_date'],
            'book_title': doc['book_title'],
            'chapter_number': str(doc['chapter_number']),
            'file_path': doc['file_path'],
            'char_count': len(doc['content']),
            'chunk_index': doc.get('chunk_index', 0),
            'total_chunks': doc.get('total_chunks', 1),
        } for doc in batch]

        # Generate embeddings
        embeddings = model.encode(texts, show_progress_bar=False).tolist()

        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(f"  Indexed {min(i + batch_size, total)}/{total} documents")


def main():
    parser = argparse.ArgumentParser(description='Index markdown corpus into Chroma')
    parser.add_argument('--reset', action='store_true', help='Clear and re-index')
    parser.add_argument('--model', default='all-MiniLM-L6-v2',
                        help='Sentence transformer model (default: all-MiniLM-L6-v2)')
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    chroma_dir = project_root / 'chroma_db'

    print(f"Project root: {project_root}")
    print(f"Data directory: {data_dir}")
    print(f"Chroma directory: {chroma_dir}")

    # Initialize Chroma
    client = chromadb.PersistentClient(path=str(chroma_dir))

    # Handle reset
    if args.reset:
        try:
            client.delete_collection('autography')
            print("Deleted existing collection")
        except Exception:
            pass

    # Get or create collection
    collection = client.get_or_create_collection(
        name='autography',
        metadata={'hnsw:space': 'cosine'}
    )

    existing_count = collection.count()
    print(f"Existing documents in collection: {existing_count}")

    # Collect documents
    print("\nCollecting documents...")
    documents = collect_documents(data_dir)
    print(f"Found {len(documents)} documents")

    # Show breakdown by type
    by_type = {}
    for doc in documents:
        t = doc['source_type']
        by_type[t] = by_type.get(t, 0) + 1
    print("\nBy source type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")

    # Load embedding model
    print(f"\nLoading embedding model: {args.model}")
    model = SentenceTransformer(args.model)
    print(f"Embedding dimension: {model.get_sentence_embedding_dimension()}")

    # Index documents
    if args.reset or existing_count == 0:
        index_documents(documents, collection, model)
    else:
        # Only index new documents
        existing_ids = set(collection.get()['ids'])
        new_docs = [d for d in documents if d['id'] not in existing_ids]
        if new_docs:
            print(f"\nIndexing {len(new_docs)} new documents...")
            index_documents(new_docs, collection, model)
        else:
            print("\nNo new documents to index")

    # Final stats
    final_count = collection.count()
    print(f"\nFinal collection size: {final_count} documents")

    # Test query
    print("\n--- Test Query ---")
    test_query = "What is a feature factory?"
    query_embedding = model.encode([test_query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    print(f"Query: '{test_query}'")
    print("Top 3 results:")
    for i, (doc_id, metadata) in enumerate(zip(results['ids'][0], results['metadatas'][0])):
        print(f"  {i+1}. {metadata['title']} ({metadata['author']})")
        print(f"     Type: {metadata['source_type']}, Chars: {metadata['char_count']}")


if __name__ == '__main__':
    main()
