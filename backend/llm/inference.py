# =============================================================================
# AyushBot Backend — LLM Inference Engine
# =============================================================================
#
# PURPOSE:
#   Orchestrates the prompt assembly and text generation for Agent 2's
#   clinical synthesis step. This module takes the retrieved evidence chunks,
#   patient context, and a Jinja2 prompt template — then generates a
#   structured differential diagnosis response from the LLM.
#
# INFERENCE WORKFLOW:
#
#   Step 1 — Prompt Assembly
#     Load the appropriate Jinja2 template from backend/llm/prompts/:
#       - diagnosis_prompt.j2: For differential diagnosis synthesis
#       - referral_prompt.j2: For referral letter generation (future use)
#     Render the template with:
#       - system_prompt: Loaded from system_prompt.txt (role definition,
#         behavioral constraints, output format instructions)
#       - evidence_chunks: The top-5 reranked chunks from the RAG pipeline,
#         each with text and source metadata
#       - patient_context: Vital signs, symptoms, demographics from the
#         Patient State Object
#       - output_schema: JSON schema defining the expected response structure
#         (forces structured output for reliable parsing)
#
#   Step 2 — Token Budget Management
#     Before calling the LLM, verify that the assembled prompt fits within
#     the model's context window (2048 tokens):
#       - Count prompt tokens using the model's tokenizer
#       - If over budget: progressively truncate chunks (drop the 5th, then
#         4th chunk) until the prompt fits
#       - Reserve at least 300 tokens for the LLM's response
#       - Log a warning if truncation was necessary
#
#   Step 3 — LLM Generation
#     Call the loaded model with the assembled prompt:
#       - temperature: 0.1 (near-deterministic; we want consistent output)
#       - top_p: 0.9 (mild nucleus sampling)
#       - max_tokens: 300 (cap the response length)
#       - stop_tokens: ["\n\n", "</output>"] (prevent the LLM from rambling)
#     The LLM generates a JSON-structured response matching the output schema.
#
#   Step 4 — Output Parsing & Validation
#     Parse the LLM's raw text output into the DifferentialDiagnosis Pydantic
#     schema (from agents/schemas/differential.py):
#       - If valid JSON → populate the schema
#       - If malformed JSON → attempt regex extraction of key fields
#       - If completely unparseable → return fallback response:
#         "Unable to synthesize diagnosis from available evidence.
#          Top retrieved protocols: [list chunk titles]."
#
# ANTI-HALLUCINATION ENFORCEMENT:
#   The prompt is designed to constrain the LLM from generating unsupported
#   clinical claims:
#     a. "You MUST cite the source document for every clinical assertion."
#     b. "If you cannot find a matching protocol in the provided chunks,
#        state: 'No matching protocol found in available evidence.'"
#     c. "Do NOT use your training data for diagnosis. ONLY use the provided
#        evidence chunks."
#     d. Post-generation validation: check that every citation in the output
#        corresponds to a real chunk ID that was provided in the prompt.
#
# INPUTS:
#   - evidence_chunks: list of RankedChunk objects (from reranker)
#   - patient_context: dict from Patient State Object (vitals, symptoms, etc.)
#   - template_name: str (which Jinja2 template to use)
#
# OUTPUTS:
#   - DifferentialDiagnosis Pydantic object (structured, validated)
#   - Or fallback response string if parsing fails
#   - generation_metrics: dict (prompt_tokens, completion_tokens, latency_ms)
#
# LATENCY TARGET: 150-250 ms (on RPi 4 CPU with Phi-3 Mini 4-bit)
# =============================================================================
