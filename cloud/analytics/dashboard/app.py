# =============================================================================
# AyushBot Cloud — Analytics Dashboard Application
# =============================================================================
#
# PURPOSE:
#   Web-based dashboard for AyushBot administrators to monitor the health
#   of the federated learning system, review aggregated (anonymized) health
#   statistics, and manage PHC gateway deployments.
#
# TECHNOLOGY:
#   Built with Streamlit (or Dash/Plotly) for rapid prototyping.
#   Deployed as a separate container alongside the FL server.
#
# DASHBOARD PAGES:
#
#   1. FL Training Overview
#      - Global model accuracy over FL rounds (line chart)
#      - Number of contributing gateways per round (bar chart)
#      - Cumulative privacy budget consumption per gateway (table)
#      - Current global model version and status
#
#   2. Gateway Fleet Status
#      - Map visualization of all deployed PHC gateways (pin on India map)
#      - Per-gateway: last sync time, model version, gradient queue size
#      - Connectivity heatmap (red = offline > 7 days, green = synced today)
#      - Alert list for gateways with issues (offline, model mismatch, etc.)
#
#   3. Aggregated Health Statistics (Anonymized)
#      - Disease distribution across all PHCs (bar chart by condition)
#      - Risk level distribution (pie chart: LOW/MEDIUM/HIGH/CRITICAL)
#      - Triage volume over time (cases per day/week/month)
#      - Referral outcomes (if outcome feedback is available)
#      NOTE: All data is aggregated and anonymized. No individual patient
#      data is displayed or stored in the cloud. Counts and distributions
#      are computed from de-identified encounter summaries.
#
#   4. Model Performance
#      - Per-class accuracy, precision, recall, F1 on the validation set
#      - Confusion matrix for the triage classifier
#      - Model version comparison (current vs. previous)
#      - Drift detection alerts (if data distribution has shifted)
#
# DATA SOURCES:
#   The dashboard reads from:
#   - Model registry database (PostgreSQL)
#   - FL round logs (from the Flower server)
#   - Anonymized aggregate statistics uploaded by gateways during sync
#     (counts only — no patient-level data reaches the cloud)
#
# ACCESS CONTROL:
#   Protected by username/password authentication. Only authorized
#   administrators (national health program coordinators, technical team)
#   can access the dashboard.
# =============================================================================
