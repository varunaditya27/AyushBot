# =============================================================================
# AyushBot Cloud — FL Model Registry
# =============================================================================
#
# PURPOSE:
#   Maintains a versioned history of all global model weights produced by
#   FL aggregation rounds. Enables model versioning, rollback, and
#   distribution to PHC gateways.
#
# WHY A REGISTRY:
#   - Different gateways may be running different model versions (due to
#     intermittent connectivity). The registry tracks which version each
#     gateway last downloaded.
#   - If a new global model performs worse than the previous version (detected
#     via the validation set), the server can roll back to the last known-good
#     version.
#   - Audit trail: regulators can trace which model version was active at
#     any given time (important for healthcare AI compliance).
#
# REGISTRY STRUCTURE:
#   Each model version entry contains:
#     - version_id: Auto-incrementing integer (monotonically increasing)
#     - created_at: ISO timestamp of when the model was produced
#     - fl_round_id: Which FL round produced this version
#     - num_contributing_clients: How many gateways contributed gradients
#     - total_training_samples: Aggregate sample count across all clients
#     - aggregation_strategy: Which strategy was used (FedAvg/FedProx/SCAFFOLD)
#     - validation_metrics: dict (accuracy, precision, recall, F1 on held-out set)
#     - model_file_path: Path to the serialized model weights file
#     - model_file_hash: SHA-256 hash of the model file (integrity verification)
#     - status: Enum (ACTIVE, ARCHIVED, ROLLED_BACK)
#
# STORAGE:
#   - Model weights: Stored as binary files on cloud object storage (S3/GCS)
#   - Registry metadata: Stored in a PostgreSQL database (or SQLite for dev)
#   - Only the ACTIVE model is distributed to gateways by default
#
# ROLLBACK POLICY:
#   If the validation accuracy of a new model drops by more than a configurable
#   threshold (default: 2%) compared to the previous version:
#     1. Mark the new model as ROLLED_BACK
#     2. Re-activate the previous version
#     3. Alert the admin (email/Slack notification)
#     4. Log the rollback event for audit
#
# GATEWAY COMPATIBILITY:
#   The registry also tracks the minimum client software version required
#   for each model version. If a gateway is running outdated software,
#   it receives the latest compatible model, not the absolute latest.
# =============================================================================
