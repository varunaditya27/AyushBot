# =============================================================================
# AyushBot Backend — LLM (Large Language Model) Package
# =============================================================================
#
# This package manages the on-device quantized LLM (Phi-3 Mini 4-bit or
# Gemma-3 1B) used by Agent 2 for grounded clinical synthesis. The LLM
# NEVER operates independently — it always receives evidence chunks from the
# RAG pipeline and is bound by strict prompt constraints.
#
# Submodules:
#   - loader.py: Model loading and memory management
#   - inference.py: Prompt assembly and generation
#   - prompts/: Jinja2 templates and system prompts
# =============================================================================
