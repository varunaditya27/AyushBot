# =============================================================================
# AyushBot Tests — Unit: Diagnosis Agent (Agent 2)
# =============================================================================
#
# PURPOSE:
#   Unit tests for the Differential Diagnosis Agent (backend/agents/agent_diagnosis.py).
#   Verifies that the agent correctly performs EdgeRAG retrieval and LLM-based
#   differential diagnosis.
#
# TEST CASES:
#
#   test_rag_retrieval_relevant_chunks
#     Input: Symptoms = ["high_fever", "rash", "joint_pain"]
#     Expected: RAG retrieves chunks about dengue, measles, chikungunya
#       (relevant differential diagnoses for fever + rash + joint pain)
#     Mock: FAISS index with pre-loaded test chunks
#
#   test_differential_list_format
#     Input: Any valid symptom set
#     Expected: Output contains a ranked list of differential diagnoses,
#       each with (condition_name, confidence_score, supporting_evidence)
#     Schema: Must conform to schemas/differential.py
#
#   test_top_diagnosis_clinically_reasonable
#     Input: SpO2=88%, cough, chest_indrawing, fever
#     Expected: Top diagnosis should be pneumonia (classic IMCI presentation)
#     Note: This is a clinical reasonableness check, not exact match
#
#   test_rag_retrieval_with_empty_index
#     Input: Any symptoms, but FAISS index is empty
#     Expected: Agent handles gracefully — falls back to LLM-only reasoning
#       (without RAG context), flags that no guidelines were retrieved
#
#   test_llm_context_window_not_exceeded
#     Input: A case with many symptoms that retrieves many RAG chunks
#     Expected: The total prompt (system + RAG context + symptoms) fits
#       within Phi-3 Mini's 4096 token context window. Excess chunks
#       are pruned by the reranker.
#
#   test_output_includes_guideline_citations
#     Input: Any valid case
#     Expected: Each diagnosis in the output cites which ASHA guideline
#       section supports it (traceability for the doctor to verify)
#
# FIXTURES USED:
#   - sample_patient_state, mock_llm_client, mock_faiss_index
# =============================================================================
