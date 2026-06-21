"""Differential Privacy wrapper for FL aggregation."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from flwr.common import NDArray

logger = logging.getLogger(__name__)


@dataclass
class DPConfig:
    """Differential Privacy configuration."""
    
    epsilon: float = 1.0  # Privacy budget
    delta: float = 1e-6   # Failure probability
    gradient_clipping_norm: float = 1.0  # L2 norm clipping threshold
    noise_injection_enabled: bool = True


class DifferentialPrivacyWrapper:
    """Wrapper to manage DP protections during FL aggregation.
    
    Validates incoming gradients, tracks DP budget consumption, and logs
    privacy metrics for monitoring and debugging.
    """
    
    def __init__(self, config: DPConfig):
        """Initialize DP wrapper.
        
        Args:
            config: DifferentialPrivacyConfig object
        """
        self.config = config
        self.epsilon_consumed = 0.0
        self.num_rounds = 0
        self.history: List[Dict] = []
    
    def validate_and_wrap_gradient(
        self,
        gradient: NDArray,
        client_id: str,
        round_num: int,
    ) -> Tuple[NDArray, Dict]:
        """Validate incoming gradient and check DP budget.
        
        Args:
            gradient: Gradient update from client
            client_id: Client identifier
            round_num: Current FL round number
            
        Returns:
            Tuple of (gradient, metrics_dict)
            
        Raises:
            RuntimeError: If DP budget exceeded
        """
        metrics = {
            "client_id": client_id,
            "round": round_num,
            "gradient_shape": gradient.shape,
            "gradient_norm": float(np.linalg.norm(gradient)),
        }
        
        # Check if gradient has already been DP-protected (from backend)
        # Backend applies DP before sending, so we mainly validate here
        
        # Compute gradient norm
        grad_norm = np.linalg.norm(gradient)
        metrics["original_norm"] = float(grad_norm)
        
        # Apply clipping if norm exceeds threshold
        if grad_norm > self.config.gradient_clipping_norm:
            clipping_scale = self.config.gradient_clipping_norm / grad_norm
            gradient = gradient * clipping_scale
            metrics["clipped"] = True
            metrics["clipping_scale"] = float(clipping_scale)
        else:
            metrics["clipped"] = False
        
        # Estimate privacy cost
        privacy_cost = self._estimate_privacy_cost(gradient)
        metrics["privacy_cost_epsilon"] = privacy_cost
        
        # Check if budget exceeded
        if self.epsilon_consumed + privacy_cost > self.config.epsilon:
            logger.warning(
                f"DP budget exceeded: {self.epsilon_consumed + privacy_cost:.4f} > "
                f"{self.config.epsilon:.4f}. Rejecting client {client_id} update."
            )
            metrics["rejected"] = True
            raise RuntimeError(
                f"Differential privacy budget exceeded. "
                f"Current: {self.epsilon_consumed:.4f}, "
                f"Required: {privacy_cost:.4f}, "
                f"Limit: {self.config.epsilon:.4f}"
            )
        
        # Update consumed budget
        self.epsilon_consumed += privacy_cost
        metrics["rejected"] = False
        
        self.history.append(metrics)
        
        return gradient, metrics
    
    def _estimate_privacy_cost(self, gradient: NDArray) -> float:
        """Estimate privacy cost of gradient using RDP accounting.
        
        Uses Gaussian DP accounting with q = 0.01 (1% sampling rate assumed).
        
        Args:
            gradient: Gradient tensor
            
        Returns:
            Estimated epsilon cost
        """
        # Simplified privacy accounting
        # Assuming Gaussian DP with q=0.01, alpha=2
        q = 0.01  # Sampling rate
        sigma = self.config.gradient_clipping_norm * 2.0  # Noise scale
        
        grad_norm = np.linalg.norm(gradient)
        
        # RDP cost at alpha=2: epsilon = (q * grad_norm / (2 * sigma))^2
        if sigma > 0:
            epsilon_rdp = (q * grad_norm / (2.0 * sigma)) ** 2
        else:
            epsilon_rdp = 0.0
        
        return float(epsilon_rdp)
    
    def get_privacy_metrics(self) -> Dict:
        """Get current privacy metrics.
        
        Returns:
            Dict with privacy statistics
        """
        if not self.history:
            return {
                "epsilon_consumed": 0.0,
                "epsilon_budget": self.config.epsilon,
                "rounds_completed": 0,
                "num_rejected": 0,
            }
        
        num_rejected = sum(1 for m in self.history if m.get("rejected", False))
        
        return {
            "epsilon_consumed": self.epsilon_consumed,
            "epsilon_budget": self.config.epsilon,
            "epsilon_remaining": self.config.epsilon - self.epsilon_consumed,
            "rounds_completed": self.num_rounds,
            "num_gradients_processed": len(self.history),
            "num_rejected": num_rejected,
            "average_gradient_norm": float(
                np.mean([m["original_norm"] for m in self.history])
            ) if self.history else 0.0,
        }
    
    def log_privacy_stats(self, logger_obj=None):
        """Log privacy statistics.
        
        Args:
            logger_obj: Optional logger object (defaults to module logger)
        """
        if logger_obj is None:
            logger_obj = logger
        
        metrics = self.get_privacy_metrics()
        logger_obj.info(f"Privacy Metrics: {metrics}")
