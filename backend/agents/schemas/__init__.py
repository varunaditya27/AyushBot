# =============================================================================
# AyushBot Backend — Agent Schemas Package
# =============================================================================
#
# This package contains Pydantic models (schemas) that define the strict data
# contracts passed between agents. Every inter-agent communication uses one of
# these schemas — no unstructured data flows between agents.
#
# The schemas enforce type safety, validation, and serialization boundaries,
# ensuring that malformed data from one agent cannot corrupt another agent's
# processing pipeline.
# =============================================================================
