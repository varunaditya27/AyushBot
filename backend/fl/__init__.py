# =============================================================================
# AyushBot Backend — Federated Learning Package
# =============================================================================
#
# This package implements the privacy-preserving federated learning (FL)
# pipeline that runs asynchronously on the PHC gateway. It enables the
# local triage model (XGBoost) to continuously improve from local clinical
# data without exposing any patient records.
#
# Submodules:
#   - local_trainer.py: On-device model fine-tuning
#   - dp_mechanism.py: Differential privacy gradient protection
#   - aggregator.py: Local gradient aggregation and buffering
#   - gossip.py: Peer-to-peer gradient sharing between nearby PHC gateways
#   - sync_client.py: Cloud FL server communication (Flower client)
# =============================================================================
