# Autography: Session Catchup

> Last updated: 2026-01-19 (Session 3)

## What is Autography?

**Autography** (A-U-T-O-G-R-A-P-H-Y) is an indexable chatbot for product management knowledge - like "Open Evidence" but for PM, founders, and design content. Users ask long-tail questions and get back **citable evidence** with sources (podcast timestamps, book pages, article links).

**Tagline**: "The open evidence of product management"

---

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Name** | Autography | Play on "autobiography" - founder stories |
| **Vector DB** | ChromaDB | Native hybrid search (RRF), free, good docs |
| **Transcription** | Parakeet MLX (local) | Free, 6% WER, 50x faster than Whisper, runs on Mac |
| **Embeddings** | text-embedding-3-large | Start here, can switch to voyage-3 later |
| **RAG Framework** | LlamaIndex | Better for citation-heavy retrieval vs LangChain |
| **Frontend** | Next.js 15 + Vercel AI SDK | Streaming, Server Components, modern |
| **Search** | Hybrid (70% semantic / 30% BM25) | Best retrieval quality per 2025 research |
| **Books format** | EPUB preferred over PDF | Cleaner text extraction, no OCR issues |
| **Founders episodes** | Priority 100 first | Quality over quantity, curated list created |
| **Audio speed** | Normal (1x) only | 2x speed degrades proper noun accuracy unacceptably |
| **Chunk size** | 10 minutes | Stays under Metal 12GB limit with headroom |

---

## Data Sources

| Source | Status | Volume | Notes |
|--------|--------|--------|-------|
| **Lenny's Podcast** | ✅ Ready | 269 episodes | [GitHub repo](https://github.com/ChatPRD/lennys-podcast-transcripts) with markdown + YAML frontmatter |
| **Founders Podcast** | 🔄 Need to download + transcribe | ~100 priority | Use yt-dlp + Parakeet. [Tapesearch](https://www.tapesearch.com/podcast/founders/1141877104) has 439 eps if bulk available |
| **David Senra Podcast** | ✅ 7/9 done | 9 episodes | Tobi Lütke, John Mackey, Patrick O'Shaughnessy, James Dyson, Michael Ovitz, Todd Graves, Brad Jacobs done. Remaining: Michael Dell, Daniel Ek |
| **John Cutler** | ⏳ Need to curate | ~1000 posts | Blog posts, articles, Twitter threads |
| **Top 20 PM Books** | ⏳ User will provide EPUBs | 20 books | Fair-use excerpts only |

### Priority Founders Episodes (Top 30)

Charlie Munger, Sam Zell, Rockefeller, Daniel Ludwig, Sam Zemurray, David Ogilvy, Ed Thorp, James Dyson, Estée Lauder, Anna Wintour, Les Schwab, Jim Simons, Todd Graves, Jensen Huang, Elon Musk, Bill Gates, Bernard Arnault, Kobe Bryant, Brunello Cucinelli, Edwin Land, Sam Walton, Jeff Bezos, Jimmy Iovine, Ken Griffin, Enzo Ferrari, Michael Jordan, Hyundai founder

Full list in `plans/founders-priority-episodes.md`

---

## Files Created

```
/Users/bjg/Documents/GullyGorge/tries/2026-01-19-autobiography/
├── README.md                     # Project overview
├── PLAN.md                       # Original comprehensive plan
├── CATCHUP.md                    # This file
├── .gitignore                    # Excludes data/, node_modules/, etc.
├── founders-priority-episodes.md # (duplicate - can delete)
├── ingestion/
│   ├── batch_transcribe.py       # Parakeet batch transcription script
│   ├── chunked_transcribe.py     # Long audio chunked processing (10-min segments)
│   └── download_founders.py      # yt-dlp wrapper with priority filtering
└── plans/
    ├── feat-autography-pm-knowledge-base.md  # Full technical spec
    └── founders-priority-episodes.md         # Curated top 100 episodes
```

---

## Tech Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND: Next.js 15 + Vercel AI SDK                       │
│  - Streaming chat with useChat hook                         │
│  - Citation cards with expand/collapse                      │
│  - Warm cream/terracotta design                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  BACKEND: Python (FastAPI) + LlamaIndex                     │
│  - Query understanding (LLM rewrite)                        │
│  - condense_plus_context chat mode                          │
│  - Citation extraction                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  RETRIEVAL: ChromaDB Hybrid Search                          │
│  - RRF: 70% dense embeddings + 30% sparse (BM25)            │
│  - Cross-encoder reranking (bge-reranker-v2-m3)             │
│  - Metadata filtering (source, speaker, date)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  INGESTION: Parakeet MLX + Chunking                         │
│  - 512-token chunks, 100-token overlap                      │
│  - Speaker-aware boundaries for transcripts                 │
│  - Rich metadata per chunk (timestamp, source, speaker)     │
└─────────────────────────────────────────────────────────────┘
```

---

## What's Been Researched

### Context7 Documentation Pulled
- ✅ ChromaDB hybrid search API (RRF, Knn, metadata filtering)
- ✅ Next.js 15 streaming with Vercel AI SDK
- ✅ LlamaIndex chat engine with citation tracking

### Best Practices Researched
- ✅ RAG chunking strategies (512 tokens optimal for transcripts)
- ✅ Hybrid search fusion (RRF with k=60)
- ✅ Embedding models comparison (OpenAI vs Voyage vs BGE)
- ✅ Cross-encoder reranking (20-35% accuracy improvement)

### Data Source Research
- ✅ Lenny's podcast repo structure (269 eps, markdown, YAML frontmatter)
- ✅ Founders Podcast transcript options (Tapesearch, yt-dlp + Parakeet)
- ✅ NVIDIA Parakeet capabilities (free, local, 6% WER, 50x realtime)
- ✅ PDF vs EPUB for books (EPUB strongly preferred)

---

## Next Steps

### Immediate (To Do Now)
1. [x] **Set up GitHub repo**: https://github.com/bjg4/autography (private)
2. [x] **Clone Lenny's transcripts**: 303 episodes in `data/lennys/`
3. [x] **Install yt-dlp**: Done (via pip3)
4. [x] **Test transcription pipeline**: Working with David Senra / Tobi Lütke episode

### Short-term (This Week)
5. [x] **Add chunked processing** for long episodes (>30 min) to avoid memory limits
6. [ ] Download priority Founders episodes via RSS (bypass YouTube restrictions)
7. [ ] Batch transcribe with Parakeet
8. [ ] Build ChromaDB ingestion script (chunk_and_embed.py)
9. [ ] Create basic search API endpoint

### Medium-term
9. [ ] Build Next.js frontend with chat UI
10. [ ] Add citation card components
11. [ ] Implement follow-up question generation
12. [ ] Add user memory/personalization

---

## Open Questions

| Question | Options | Notes |
|----------|---------|-------|
| **Auth model?** | Anonymous / Optional / Required | Recommend: Optional (anon search OK, save requires login) |
| **Tapesearch bulk?** | Check if available | Could save transcription time |
| **Book excerpts?** | Fair use quotes vs summaries | Legal consideration - keep quotes short |
| **Hosting?** | Vercel + Railway / Self-hosted | Vercel for frontend, Railway for Python backend? |

---

## Useful Commands

```bash
# Navigate to project
cd /Users/bjg/Documents/GullyGorge/tries/2026-01-19-autobiography

# List Founders episodes (requires yt-dlp)
python ingestion/download_founders.py --list-only

# Download priority 100
python ingestion/download_founders.py --priority 100 -o data/founders/audio

# Batch transcribe (requires parakeet_mlx)
python ingestion/batch_transcribe.py data/founders/audio -o data/founders/transcripts --skip-existing

# Clone Lenny's transcripts
git clone https://github.com/ChatPRD/lennys-podcast-transcripts.git data/lennys
```

---

## Key URLs

- **Lenny's Transcripts**: https://github.com/ChatPRD/lennys-podcast-transcripts
- **Founders Podcast**: https://www.founderspodcast.com
- **Tapesearch (Founders)**: https://www.tapesearch.com/podcast/founders/1141877104
- **Parakeet Model**: https://huggingface.co/nvidia/parakeet-tdt-0.6b-v2
- **ChromaDB Docs**: https://docs.trychroma.com

---

## Session Notes

### Session 1
- Started with broad vision, narrowed to specific tech choices
- Parakeet chosen over Whisper API to avoid ~$600 transcription cost
- Priority 100 episodes curated from multiple "best of" lists + David Senra's stated favorites
- Existing parakeet-transcribe app at `../2026-01-18-parakeet/` is for real-time dictation, not batch processing
- Bash commands failing in Claude session - user may need to run git/gh commands manually

### Session 2
- **GitHub repo created**: https://github.com/bjg4/autography (private)
- **Lenny's transcripts cloned**: 303 episodes in `data/lennys/`
- **Standardized transcript format**: Using `subject` instead of `guest` for both sources
- **Tested full pipeline**: Downloaded Tobi Lütke episode from RSS, transcribed 10-min clip with Parakeet
- **Parakeet performance**: ~15x realtime on M-series Mac (10 min audio in 40 sec)
- **Issue found**: Full 2.4hr episodes exceed Metal memory limit - need chunked processing

#### Transcript Format (Lenny's-style)
```markdown
---
subject: Tobi Lütke
title: Full Episode Title
youtube_url: https://youtube.com/watch?v=...
video_id: abc123
publish_date: '2026-01-18'
duration_seconds: 599.8
duration: '9:59'
channel: David Senra Podcast
keywords: []
---

# Episode Title

## Transcript

Speaker Name (00:00:02):
Transcript text here grouped in ~30 second chunks...
```

#### Dependencies Installed
- `yt-dlp` (via pip3)
- `parakeet-mlx` (via python3.11)
- `ffmpeg` (via homebrew)

### Session 3
- **Chunked transcription implemented**: `chunked_transcribe.py` splits audio into 10-min segments
- **Full episode transcription working**: 2.4hr Tobi Lütke episode transcribed in 11 min (~13x realtime)
- **Metal memory limit**: 12GB buffer max, 10-min chunks stay safely under limit
- **2x speed testing**: Tested James Dyson episode at normal vs 2x speed

#### 2x Speed Comparison Results

| Passage | Normal Speed | 2x Speed | Verdict |
|---------|--------------|----------|---------|
| Education | "Latin, Greek, and ancient history" ✓ | "last in Greek in ancient history" ✗ | Normal wins |
| Project name | "autobiography" ✓ | "autography" ✗ | Normal wins |
| Person name | "Charlie Munger" ✓ | "Sherlinger" ✗ | Normal wins (critical) |
| Person name | "Jeff Bezos" ✓ | "Just praise us" ✗ | Normal wins (critical) |

**Conclusion**: 2x speed saves ~38% processing time but introduces unacceptable errors, especially for proper nouns (names, companies). For a citation-focused knowledge base, accuracy is paramount. **Use normal speed only.**

#### Performance Benchmarks

| Episode | Duration | Process Time | RTF | Notes |
|---------|----------|--------------|-----|-------|
| Tobi Lütke (full) | 2:24:00 | 11 min | 13x | 15 chunks |
| James Dyson (normal) | 1:38:20 | 7:51 | 12.5x | Good quality |
| James Dyson (2x) | 0:49:10 | 4:51 | 10x | Poor quality |

#### Useful Commands (Session 3)

```bash
# Chunked transcription for long episodes
/opt/homebrew/bin/python3.11 ingestion/chunked_transcribe.py \
  data/david-senra/audio/episode.mp3 \
  --output data/david-senra/episodes/episode-name/transcript.md \
  --metadata data/david-senra/audio/metadata/episode.json \
  --speaker "David Senra" \
  --chunk-minutes 10

# Create 2x speed audio (NOT recommended for transcription)
ffmpeg -i input.mp3 -filter:a "atempo=2.0" output-2x.mp3
```

---

*To resume: Read this file, then check the plans/ directory for detailed specs.*
