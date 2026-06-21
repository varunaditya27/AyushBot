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

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for storing and retrieving FL model versions.
    
    Maintains a local filesystem-based registry of model weights and metadata.
    Each model version is stored with metadata about the aggregation round,
    performance metrics, and privacy information.
    """
    
    def __init__(
        self,
        storage_path: str = "./models",
        max_versions: int = 10,
    ):
        """Initialize model registry.
        
        Args:
            storage_path: Path to store models (default: ./models)
            max_versions: Maximum number of model versions to keep (default: 10)
        """
        self.storage_path = Path(storage_path)
        self.max_versions = max_versions
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.storage_path / "registry.json"
        self.versions: Dict[str, Dict] = self._load_metadata()
    
    def save_model(
        self,
        model_bytes: np.ndarray,
        round_num: int,
        num_clients: int,
        aggregation_strategy: str,
        metrics: Optional[Dict] = None,
    ) -> str:
        """Save a model version to registry.
        
        Args:
            model_bytes: Model weights as numpy array
            round_num: Aggregation round number
            num_clients: Number of clients in this round
            aggregation_strategy: Strategy name (e.g., "FedAvg", "FedProx")
            metrics: Optional dict with additional metrics
            
        Returns:
            Version string (e.g., "v_1_2026_05_30_120000")
        """
        timestamp = datetime.now(timezone.utc)
        version = self._generate_version_string(timestamp)
        
        # Save model weights
        model_file = self.storage_path / f"{version}.npy"
        np.save(model_file, model_bytes)
        
        # Create metadata
        metadata = {
            "version": version,
            "timestamp": timestamp.isoformat(),
            "round_num": round_num,
            "num_clients": num_clients,
            "aggregation_strategy": aggregation_strategy,
            "model_file": str(model_file),
            "model_size_bytes": model_bytes.nbytes,
            "metrics": metrics or {},
        }
        
        # Add to registry
        self.versions[version] = metadata
        
        # Persist metadata
        self._save_metadata()
        
        # Prune old versions
        self._prune_old_versions()
        
        logger.info(f"Saved model version {version}")
        return version
    
    def get_latest_model(self) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """Get the latest model and its metadata.
        
        Returns:
            Tuple of (model_bytes, metadata_dict) or (None, None) if no models exist
        """
        if not self.versions:
            return None, None
        
        # Get latest by timestamp
        latest_version = max(
            self.versions.items(),
            key=lambda x: x[1]["timestamp"]
        )
        
        version_str, metadata = latest_version
        model_bytes = self._load_model_bytes(metadata["model_file"])
        
        return model_bytes, metadata
    
    def get_model_by_version(self, version: str) -> Tuple[Optional[np.ndarray], Optional[Dict]]:
        """Get a specific model version.
        
        Args:
            version: Version string
            
        Returns:
            Tuple of (model_bytes, metadata_dict) or (None, None) if not found
        """
        if version not in self.versions:
            logger.warning(f"Version {version} not found in registry")
            return None, None
        
        metadata = self.versions[version]
        model_bytes = self._load_model_bytes(metadata["model_file"])
        
        return model_bytes, metadata
    
    def list_versions(self, limit: int = 10) -> List[Dict]:
        """List model versions.
        
        Args:
            limit: Maximum number of versions to return (default: 10)
            
        Returns:
            List of metadata dicts, sorted by timestamp (newest first)
        """
        sorted_versions = sorted(
            self.versions.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )
        
        return [metadata for _, metadata in sorted_versions[:limit]]
    
    def delete_model(self, version: str) -> bool:
        """Delete a model version.
        
        Args:
            version: Version string to delete
            
        Returns:
            True if deleted, False if not found
        """
        if version not in self.versions:
            return False
        
        metadata = self.versions[version]
        model_file = Path(metadata["model_file"])
        
        # Delete file
        if model_file.exists():
            model_file.unlink()
        
        # Remove from registry
        del self.versions[version]
        self._save_metadata()
        
        logger.info(f"Deleted model version {version}")
        return True
    
    @staticmethod
    def _generate_version_string(timestamp: datetime) -> str:
        """Generate a version string from timestamp.
        
        Args:
            timestamp: datetime object
            
        Returns:
            Version string in format "v_1_YYYY_MM_DD_HHMMSS_ffffff" (microsecond precision)
        """
        return timestamp.strftime("v_1_%Y_%m_%d_%H%M%S_%f")
    
    @staticmethod
    def _load_model_bytes(model_file: str) -> Optional[np.ndarray]:
        """Load model bytes from file.
        
        Args:
            model_file: Path to model file
            
        Returns:
            Numpy array or None if file doesn't exist
        """
        model_path = Path(model_file)
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_file}")
            return None
        
        try:
            return np.load(model_path)
        except Exception as e:
            logger.error(f"Failed to load model from {model_file}: {e}")
            return None
    
    def _load_metadata(self) -> Dict[str, Dict]:
        """Load metadata from file.
        
        Returns:
            Dictionary of version -> metadata
        """
        if not self.metadata_file.exists():
            return {}
        
        try:
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {}
    
    def _save_metadata(self):
        """Save metadata to file."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.versions, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _prune_old_versions(self):
        """Remove old versions to stay within max_versions limit."""
        if len(self.versions) <= self.max_versions:
            return
        
        # Sort by timestamp and keep only the newest
        sorted_versions = sorted(
            self.versions.items(),
            key=lambda x: x[1]["timestamp"],
            reverse=True
        )
        
        versions_to_keep = dict(sorted_versions[:self.max_versions])
        versions_to_delete = [v for v in self.versions if v not in versions_to_keep]
        
        for version in versions_to_delete:
            self.delete_model(version)
        
        logger.info(f"Pruned {len(versions_to_delete)} old model versions")
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
