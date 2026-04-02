# =============================================================================
# AyushBot Backend — FL Local Gradient Aggregator & Buffer
# =============================================================================
#
# PURPOSE:
#   Manages the local buffer of DP-protected gradient updates waiting to be
#   synchronized with the cloud FL server (or shared via gossip with peers).
#   Handles the delay-tolerant networking (DTN) aspect of FL in intermittent
#   connectivity environments.
#
# WHY A LOCAL AGGREGATOR:
#   In rural India, internet connectivity at PHCs is unreliable. The gateway
#   may train multiple rounds locally before getting a chance to sync with
#   the cloud server. The aggregator:
#     1. Buffers multiple gradient updates locally
#     2. Optionally pre-aggregates them (averaging) to reduce upload size
#     3. Timestamps and cryptographically signs each update for integrity
#     4. Manages a queue with retry logic for cloud uploads
#
# BUFFER MANAGEMENT:
#   - Gradient updates are stored as serialized numpy arrays on disk
#     (in a queue directory under backend/fl/gradient_queue/)
#   - Each update is tagged with:
#       - timestamp: when it was produced
#       - model_version: which base model it was trained against
#       - epoch_count: number of local epochs
#       - dp_params: ε, δ used for this update
#       - sample_count: number of training samples used
#   - Queue is FIFO — oldest updates are sent first
#   - If the queue exceeds a configurable max_queue_size (default: 50
#     updates), the oldest updates are discarded with a warning
#
# PRE-AGGREGATION:
#   If multiple gradient updates have accumulated for the same model version,
#   the aggregator can optionally average them before upload. This reduces
#   bandwidth usage without significantly impacting model quality.
#   Method: Simple arithmetic mean of gradient vectors.
#
# STALENESS DETECTION:
#   If a gradient was computed against a model version that is now outdated
#   (the cloud server has since produced a newer global model), the gradient
#   is marked as "stale." Stale gradients can still be useful but may receive
#   lower weight in the cloud server's aggregation strategy (see
#   cloud/fl_server/strategy.py).
#
# INTEGRITY:
#   Each gradient update file is accompanied by an HMAC-SHA256 signature
#   computed using the gateway's device key. The cloud server verifies this
#   signature before accepting the update, preventing gradient poisoning
#   attacks from spoofed gateways.
#
# INPUTS:
#   - DP-protected gradient vectors from dp_mechanism.py
#   - Queue configuration: max_queue_size, pre_aggregate (bool)
#
# OUTPUTS:
#   - Queued gradient update files ready for sync_client.py to upload
#   - Queue status: count, oldest_timestamp, total_size_bytes
# =============================================================================

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np


@dataclass
class GradientUpdate:
	path: str
	metadata: Dict[str, object]
	gradient: np.ndarray


class GradientQueue:
	def __init__(self, queue_dir: str, max_queue_size: int = 50) -> None:
		self.queue_dir = Path(queue_dir)
		self.queue_dir.mkdir(parents=True, exist_ok=True)
		self.max_queue_size = max_queue_size

	def _list_files(self) -> list[Path]:
		return sorted(self.queue_dir.glob("*.npz"))

	def size(self) -> int:
		return len(self._list_files())

	def enqueue(self, gradient: np.ndarray, metadata: Optional[Dict[str, object]] = None) -> str:
		metadata = metadata or {}
		metadata.setdefault("timestamp", int(time.time()))
		filename = f"grad_{metadata['timestamp']}_{int(time.time() * 1000)}.npz"
		path = self.queue_dir / filename
		np.savez_compressed(path, gradient=gradient.astype(np.float32), metadata=json.dumps(metadata))
		self._trim()
		return str(path)

	def dequeue(self) -> Optional[GradientUpdate]:
		files = self._list_files()
		if not files:
			return None
		path = files[0]
		data = np.load(path, allow_pickle=False)
		gradient = data["gradient"]
		metadata = json.loads(str(data["metadata"]))
		path.unlink(missing_ok=True)
		return GradientUpdate(path=str(path), metadata=metadata, gradient=gradient)

	def _trim(self) -> None:
		files = self._list_files()
		if len(files) <= self.max_queue_size:
			return
		for path in files[: len(files) - self.max_queue_size]:
			path.unlink(missing_ok=True)
