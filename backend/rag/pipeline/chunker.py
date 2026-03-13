# =============================================================================
# AyushBot Backend — RAG Pipeline Stage 1: Document Chunker
# =============================================================================
#
# PURPOSE:
#   Splits raw clinical documents (PDFs of treatment guidelines, IMCI
#   protocols, drug formularies) into semantically coherent chunks suitable
#   for embedding and retrieval. This runs OFFLINE during index build time,
#   not during live queries.
#
# WHY CHUNKING MATTERS:
#   Clinical guidelines are long (hundreds of pages). Embedding entire
#   documents would destroy fine-grained retrievability. Embedding individual
#   sentences would lose clinical context. The chunker must find the right
#   granularity — typically 200-400 token chunks — that capture a complete
#   clinical concept (e.g., one treatment protocol for one condition).
#
# CHUNKING STRATEGY:
#   Uses a hierarchical, structure-aware chunking approach:
#
#   1. PDF → Structured Text Extraction
#      - Extract text from PDFs using a layout-aware parser (e.g., PyMuPDF)
#      - Preserve section headings, tables, and bullet lists as metadata
#      - Handle multi-column layouts common in Indian government documents
#
#   2. Section-Boundary Splitting
#      - Primary split points: section headings (H1, H2, H3 levels)
#      - This ensures that "Diagnosis" and "Treatment" for the same condition
#        stay in separate chunks (so retrieval can target treatment-specific
#        chunks vs. diagnostic criteria independently)
#
#   3. Sliding-Window Sub-Chunking
#      - Within each section, apply overlapping sliding windows:
#        window_size = 300 tokens, overlap = 50 tokens
#      - Overlap prevents retrieval failures when a relevant concept spans
#        a chunk boundary
#
#   4. Metadata Tagging
#      Each chunk is tagged with provenance metadata:
#        - source_document: filename / guideline name
#        - page_number: original page in the PDF
#        - section_heading: the containing section title
#        - chunk_index: position within the document
#        - token_count: number of tokens in this chunk
#
# INPUTS:
#   - Directory of cleaned text files (from data/corpus/cleaned_text/)
#   - Chunking configuration: window_size, overlap, min_chunk_tokens
#
# OUTPUTS:
#   - List of Chunk objects, each with text + metadata
#   - Chunk manifest JSON (summary of all chunks for auditing)
#
# EDGE CASES:
#   - Tables: Serialized as pipe-delimited text with column headers preserved
#   - Bullet lists: Each list item becomes a mini-chunk if it exceeds the
#     minimum token threshold; otherwise, adjacent items are merged
#   - Very short sections: Merged with the next section to avoid tiny chunks
#     that would be semantically weak
# =============================================================================
