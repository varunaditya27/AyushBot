# =============================================================================
# AyushBot Cloud — Anonymized Statistics Aggregator
# =============================================================================
#
# PURPOSE:
#   Processes the anonymized aggregate health statistics uploaded by PHC
#   gateways during FL sync. Computes national-level and district-level
#   statistics for the analytics dashboard.
#
# WHAT DATA REACHES THE CLOUD:
#   ONLY aggregate counts and distributions — NEVER individual patient data.
#   Each gateway periodically uploads a statistics summary:
#     - phc_id: Which PHC this data is from
#     - period: Time range (e.g., "2024-W03" for week 3 of 2024)
#     - total_encounters: int (how many triage sessions occurred)
#     - risk_distribution: dict (LOW: 45, MEDIUM: 30, HIGH: 15, CRITICAL: 10)
#     - top_conditions: list of (condition_name, count) tuples
#     - referral_count: int (how many patients were referred)
#     - outcome_feedback_count: int (how many doctor feedbacks received)
#     - avg_pipeline_latency_ms: float (system performance metric)
#     - model_version: str (which model version produced these results)
#
# AGGREGATION PIPELINE:
#   1. Receive statistics summaries from the FL sync API
#   2. Validate schema and check for duplicates (same phc_id + period)
#   3. Store in the cloud database (PostgreSQL)
#   4. Compute multi-level aggregations:
#      - District level: Sum/average across all PHCs in a district
#      - State level: Sum/average across all districts in a state
#      - National level: Sum/average across all states
#   5. Update materialized views for the dashboard
#
# PRIVACY GUARANTEE:
#   The k-anonymity constraint is enforced: if a district has fewer than k
#   PHCs (default: k=5), its data is rolled up to the state level to prevent
#   re-identification of specific PHCs or their patient populations.
#
# OUTPUTS:
#   - Aggregated statistics tables in PostgreSQL
#   - Pre-computed dashboard views (refreshed hourly)
#   - CSV export endpoint for researchers (anonymized, aggregated only)
# =============================================================================
