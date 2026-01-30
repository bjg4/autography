#!/usr/bin/env python3
"""
Index all markdown content into Chroma with embeddings.

Two-level chunking strategy:
- Retrieval chunks: ~200 tokens (optimized for embedding model, no truncation)
- Parent spans: ~1000-1200 tokens (what gets returned to LLM for context)

Usage:
    python index_corpus.py [--reset]

Options:
    --reset    Clear existing collection and re-index everything
"""

import argparse
import re
import os
from pathlib import Path
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer


# Chunking parameters (token-based)
RETRIEVAL_CHUNK_TOKENS = 200  # Small chunks for precise retrieval
CHUNK_OVERLAP_TOKENS = 40    # ~20% overlap
PARENT_SPAN_CHUNKS = 5       # ~5 retrieval chunks per parent span (~1000 tokens)


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

    if '/blake-graham/' in path_str:
        return 'Blake Graham'
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


def chunk_text_by_tokens(
    text: str,
    tokenizer,
    chunk_tokens: int = RETRIEVAL_CHUNK_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS
) -> list[dict]:
    """
    Split text into overlapping chunks by token count.
    Returns list of dicts with 'text', 'start_char', 'end_char'.

    Uses paragraph-aware splitting when possible.
    """
    # Split into paragraphs first for cleaner boundaries
    paragraphs = re.split(r'\n\n+', text)

    chunks = []
    current_chunk_tokens = []
    current_chunk_text = []
    current_start_char = 0
    char_pos = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            char_pos += 2  # Account for \n\n
            continue

        para_tokens = tokenizer.tokenize(para)

        # If adding this paragraph exceeds chunk size
        if len(current_chunk_tokens) + len(para_tokens) > chunk_tokens:
            # Save current chunk if it has content
            if current_chunk_text:
                chunk_text = '\n\n'.join(current_chunk_text)
                chunks.append({
                    'text': chunk_text,
                    'start_char': current_start_char,
                    'end_char': char_pos
                })

                # Calculate overlap: keep last N tokens worth of text
                overlap_text = []
                overlap_token_count = 0
                for t in reversed(current_chunk_text):
                    t_tokens = len(tokenizer.tokenize(t))
                    if overlap_token_count + t_tokens <= overlap_tokens:
                        overlap_text.insert(0, t)
                        overlap_token_count += t_tokens
                    else:
                        break

                current_chunk_text = overlap_text
                current_chunk_tokens = []
                for t in overlap_text:
                    current_chunk_tokens.extend(tokenizer.tokenize(t))
                current_start_char = char_pos - len('\n\n'.join(overlap_text)) if overlap_text else char_pos

        # If single paragraph is too long, split it by sentences
        if len(para_tokens) > chunk_tokens:
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sent in sentences:
                sent_tokens = tokenizer.tokenize(sent)
                if len(current_chunk_tokens) + len(sent_tokens) > chunk_tokens and current_chunk_text:
                    chunk_text = '\n\n'.join(current_chunk_text)
                    chunks.append({
                        'text': chunk_text,
                        'start_char': current_start_char,
                        'end_char': char_pos
                    })
                    current_chunk_text = []
                    current_chunk_tokens = []
                    current_start_char = char_pos

                if current_chunk_text and not current_chunk_text[-1].endswith(('.', '!', '?')):
                    current_chunk_text[-1] += ' ' + sent
                else:
                    current_chunk_text.append(sent)
                current_chunk_tokens.extend(sent_tokens)
        else:
            current_chunk_text.append(para)
            current_chunk_tokens.extend(para_tokens)

        char_pos += len(para) + 2  # +2 for \n\n

    # Don't forget the last chunk
    if current_chunk_text:
        chunk_text = '\n\n'.join(current_chunk_text)
        chunks.append({
            'text': chunk_text,
            'start_char': current_start_char,
            'end_char': char_pos
        })

    return chunks


def assign_parent_spans(chunks: list[dict], chunks_per_span: int = PARENT_SPAN_CHUNKS) -> list[dict]:
    """
    Assign parent span IDs to chunks.
    Parent spans group multiple retrieval chunks for richer LLM context.
    """
    for i, chunk in enumerate(chunks):
        chunk['parent_span_index'] = i // chunks_per_span
        chunk['chunk_in_span'] = i % chunks_per_span

    # Calculate total spans
    total_spans = (len(chunks) + chunks_per_span - 1) // chunks_per_span
    for chunk in chunks:
        chunk['total_spans'] = total_spans

    return chunks


def collect_documents(data_dir: Path, tokenizer) -> list[dict]:
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

        if len(body.strip()) < 100:
            continue

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

        # Chunk the body text by tokens
        chunks = chunk_text_by_tokens(body, tokenizer)

        # Assign parent spans
        chunks = assign_parent_spans(chunks)

        for i, chunk in enumerate(chunks):
            if len(chunk['text'].strip()) < 50:
                continue

            # Parent span ID combines file path and span index
            parent_span_id = f"{md_file.relative_to(data_dir)}::span_{chunk['parent_span_index']}"

            doc = {
                'id': f"{md_file.relative_to(data_dir)}::chunk_{i}",
                'content': chunk['text'],
                'chunk_index': i,
                'total_chunks': len(chunks),
                'parent_span_id': parent_span_id,
                'parent_span_index': chunk['parent_span_index'],
                'chunk_in_span': chunk['chunk_in_span'],
                'total_spans': chunk['total_spans'],
                'start_char': chunk['start_char'],
                'end_char': chunk['end_char'],
                **base_meta
            }
            documents.append(doc)

    return documents


def index_documents(
    documents: list[dict],
    collection: chromadb.Collection,
    model: SentenceTransformer,
    batch_size: int = 64
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
            'chunk_index': doc['chunk_index'],
            'total_chunks': doc['total_chunks'],
            'parent_span_id': doc['parent_span_id'],
            'parent_span_index': doc['parent_span_index'],
            'chunk_in_span': doc['chunk_in_span'],
            'total_spans': doc['total_spans'],
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

        if (i + batch_size) % 1000 < batch_size:
            print(f"  Indexed {min(i + batch_size, total)}/{total} documents")

    print(f"  Indexed {total}/{total} documents")


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
    print(f"\nChunking strategy:")
    print(f"  Retrieval chunks: {RETRIEVAL_CHUNK_TOKENS} tokens")
    print(f"  Overlap: {CHUNK_OVERLAP_TOKENS} tokens")
    print(f"  Parent span: {PARENT_SPAN_CHUNKS} chunks (~{RETRIEVAL_CHUNK_TOKENS * PARENT_SPAN_CHUNKS} tokens)")

    # Initialize Chroma
    client = chromadb.PersistentClient(path=str(chroma_dir))

    # Handle reset
    if args.reset:
        try:
            client.delete_collection('autography')
            print("\nDeleted existing collection")
        except Exception:
            pass

    # Get CPU count for HNSW threading
    cpu_count = os.cpu_count() or 4

    # Get or create collection with optimized HNSW settings
    collection = client.get_or_create_collection(
        name='autography',
        metadata={
            'hnsw:space': 'cosine',
            'hnsw:M': 16,                    # Connections per node (default, good balance)
            'hnsw:construction_ef': 100,     # Build-time quality (default)
            'hnsw:search_ef': 80,            # Query-time quality (~4x typical n_results of 20)
            'hnsw:num_threads': cpu_count,   # Parallel search
            'hnsw:sync_threshold': 10000,    # Fewer disk syncs during bulk insert
        }
    )

    existing_count = collection.count()
    print(f"\nExisting documents in collection: {existing_count}")

    # Load embedding model
    print(f"\nLoading embedding model: {args.model}")
    model = SentenceTransformer(args.model)
    print(f"Embedding dimension: {model.get_sentence_embedding_dimension()}")
    print(f"Max sequence length: {model.max_seq_length} tokens")

    # Collect documents using tokenizer for accurate token counting
    print("\nCollecting documents...")
    documents = collect_documents(data_dir, model.tokenizer)
    print(f"Found {len(documents)} retrieval chunks")

    # Show breakdown by type
    by_type = {}
    for doc in documents:
        t = doc['source_type']
        by_type[t] = by_type.get(t, 0) + 1
    print("\nBy source type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")

    # Count unique parent spans
    unique_spans = len(set(doc['parent_span_id'] for doc in documents))
    print(f"\nParent spans (return units): {unique_spans}")
    print(f"Avg chunks per span: {len(documents) / unique_spans:.1f}")

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
    print(f"\nFinal collection size: {final_count} retrieval chunks")

    # Test query
    print("\n--- Test Query ---")
    test_query = "What is a feature factory?"
    query_embedding = model.encode([test_query])[0].tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )

    print(f"Query: '{test_query}'")
    print("Top 5 results (retrieval chunks):")
    seen_spans = set()
    for i, (doc_id, metadata, doc) in enumerate(zip(
        results['ids'][0],
        results['metadatas'][0],
        results['documents'][0]
    )):
        span_id = metadata['parent_span_id']
        is_new_span = span_id not in seen_spans
        seen_spans.add(span_id)
        print(f"  {i+1}. {metadata['title']} ({metadata['author']})")
        print(f"     Span: {metadata['parent_span_index']}/{metadata['total_spans']}, "
              f"Chunk: {metadata['chunk_in_span']}, "
              f"{'[NEW SPAN]' if is_new_span else '[SAME SPAN]'}")
        print(f"     Preview: {doc[:100]}...")


if __name__ == '__main__':
    main()
