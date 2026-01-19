#!/usr/bin/env python3
"""
Query the PM knowledge base using hybrid search.

Usage:
    python query.py "What does Cutler say about feature factories?"
    python query.py --interactive
    python query.py --type essay "one-pagers"
    python query.py --author "Ryan Singer" "shaping"

Options:
    -n, --num         Number of results (default: 5)
    -t, --type        Filter by source type (essay, book_chapter, podcast_transcript)
    -a, --author      Filter by author name
    -i, --interactive Interactive mode
    --semantic-only   Use only semantic search
    --bm25-only       Use only BM25 search
    --verbose         Show full content
"""

import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.hybrid_search import HybridSearch


def format_result(result: dict, index: int, verbose: bool = False) -> str:
    """Format a search result for display."""
    meta = result['metadata']
    lines = [
        f"\n{'─'*60}",
        f"  [{index}] {meta['title']}",
        f"      Author: {meta['author']}",
        f"      Type: {meta['source_type']} | Score: {result['score']:.4f}",
    ]

    if meta.get('book_title'):
        lines.append(f"      Book: {meta['book_title']} (Ch. {meta.get('chapter_number', '?')})")

    if meta.get('source_url'):
        lines.append(f"      URL: {meta['source_url']}")

    lines.append(f"      File: {result['id']}")

    if verbose:
        lines.append(f"\n{result['content'][:2000]}")
        if len(result['content']) > 2000:
            lines.append(f"\n... [{len(result['content']) - 2000} more chars]")
    else:
        snippet = result['content'][:300].replace('\n', ' ')
        lines.append(f"\n      {snippet}...")

    return '\n'.join(lines)


def run_query(
    search: HybridSearch,
    query: str,
    n_results: int = 5,
    source_type: str = None,
    author: str = None,
    semantic_only: bool = False,
    bm25_only: bool = False,
    verbose: bool = False
):
    """Run a query and display results."""
    print(f"\n🔍 Query: \"{query}\"")

    if semantic_only:
        print("   (semantic search only)")
        results = search.semantic_only(query, n_results)
    elif bm25_only:
        print("   (BM25 search only)")
        results = search.bm25_only(query, n_results)
    else:
        print("   (hybrid: 70% semantic + 30% BM25)")
        results = search.search(
            query,
            n_results=n_results,
            source_type=source_type,
            author=author
        )

    if not results:
        print("\n   No results found.")
        return

    print(f"\n📚 Found {len(results)} results:")

    for i, result in enumerate(results, 1):
        print(format_result(result, i, verbose))

    print(f"\n{'─'*60}\n")


def interactive_mode(search: HybridSearch):
    """Run interactive query loop."""
    print("\n" + "="*60)
    print("  PM Knowledge Base - Interactive Query Mode")
    print("="*60)
    print("\nCommands:")
    print("  /q or /quit     Exit")
    print("  /h or /help     Show help")
    print("  /essay <query>  Search essays only")
    print("  /book <query>   Search books only")
    print("  /pod <query>    Search podcasts only")
    print("  /sem <query>    Semantic search only")
    print("  /bm25 <query>   BM25 search only")
    print("\n" + "="*60)

    while True:
        try:
            query = input("\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not query:
            continue

        if query in ('/q', '/quit', '/exit'):
            print("Goodbye!")
            break

        if query in ('/h', '/help'):
            print("\nEnter a natural language query to search the knowledge base.")
            print("Use /essay, /book, /pod to filter by type.")
            print("Use /sem, /bm25 to change search method.")
            continue

        # Parse special commands
        source_type = None
        semantic_only = False
        bm25_only = False

        if query.startswith('/essay '):
            source_type = 'essay'
            query = query[7:]
        elif query.startswith('/book '):
            source_type = 'book_chapter'
            query = query[6:]
        elif query.startswith('/pod '):
            source_type = 'podcast_transcript'
            query = query[5:]
        elif query.startswith('/sem '):
            semantic_only = True
            query = query[5:]
        elif query.startswith('/bm25 '):
            bm25_only = True
            query = query[6:]

        run_query(
            search,
            query,
            n_results=5,
            source_type=source_type,
            semantic_only=semantic_only,
            bm25_only=bm25_only
        )


def main():
    parser = argparse.ArgumentParser(
        description='Query the PM knowledge base',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query.py "What is a feature factory?"
  python query.py --type book_chapter "six week cycles"
  python query.py --author "Teresa Torres" "discovery"
  python query.py --interactive
        """
    )

    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('-n', '--num', type=int, default=5, help='Number of results')
    parser.add_argument('-t', '--type', dest='source_type',
                        choices=['essay', 'book_chapter', 'podcast_transcript'],
                        help='Filter by source type')
    parser.add_argument('-a', '--author', help='Filter by author name')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Interactive mode')
    parser.add_argument('--semantic-only', action='store_true',
                        help='Use only semantic search')
    parser.add_argument('--bm25-only', action='store_true',
                        help='Use only BM25 search')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show full content')

    args = parser.parse_args()

    # Initialize search
    print("Loading search index...")
    search = HybridSearch()
    print(f"Ready! ({search.collection.count()} documents)")

    if args.interactive:
        interactive_mode(search)
    elif args.query:
        run_query(
            search,
            args.query,
            n_results=args.num,
            source_type=args.source_type,
            author=args.author,
            semantic_only=args.semantic_only,
            bm25_only=args.bm25_only,
            verbose=args.verbose
        )
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
