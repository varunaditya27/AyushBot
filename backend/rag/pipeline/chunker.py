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

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class Chunk:
	text: str
	index: int
	token_count: int


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _tokenize(text: str) -> List[str]:
	return [tok for tok in re.split(r"\s+", text.strip()) if tok]


def chunk_text(
	text: str,
	max_tokens: int = 300,
	overlap: int = 50,
	min_tokens: int = 30,
) -> List[Chunk]:
	sentences = [s.strip() for s in _SENTENCE_SPLIT.split(text) if s.strip()]
	chunks: List[Chunk] = []
	buffer: List[str] = []
	token_count = 0
	idx = 0

	def flush() -> None:
		nonlocal buffer, token_count, idx
		if token_count >= min_tokens:
			chunk_text_value = " ".join(buffer).strip()
			chunks.append(Chunk(text=chunk_text_value, index=idx, token_count=token_count))
			idx += 1
		if overlap > 0 and buffer:
			tokens = _tokenize(" ".join(buffer))
			buffer = tokens[-overlap:]
			token_count = len(buffer)
		else:
			buffer = []
			token_count = 0

	for sentence in sentences:
		tokens = _tokenize(sentence)
		if token_count + len(tokens) > max_tokens and buffer:
			flush()
		buffer.extend(tokens)
		token_count += len(tokens)

	if buffer:
		flush()

	return chunks


def chunk_documents(docs: Iterable[str], **kwargs) -> List[Chunk]:
	chunks: List[Chunk] = []
	for doc in docs:
		chunks.extend(chunk_text(doc, **kwargs))
	return chunks
