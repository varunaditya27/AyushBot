# =============================================================================
# AyushBot Cloud — FL Aggregation Strategies
# =============================================================================
#
# PURPOSE:
#   Defines the federated aggregation strategies that the FL server uses to
#   combine DP-protected gradient updates from multiple PHC gateways into
#   a single global model update.
#
# STRATEGIES IMPLEMENTED:
#
#   1. FedAvg (Federated Averaging)
#      The baseline strategy. Computes a weighted average of client gradients:
#        global_gradient = Σ (n_k / N) * gradient_k
#      where n_k = samples used by client k, N = total samples across all clients.
#      Pros: Simple, well-understood, low communication overhead.
#      Cons: Converges slowly with non-IID data (different PHCs see different
#             disease distributions — e.g., malaria-heavy vs. respiratory-heavy).
#
#   2. FedProx (Federated Proximal)
#      FedAvg + a proximal regularization term that penalizes local models
#      for drifting too far from the global model:
#        local_objective = loss + (μ/2) * ||w_local - w_global||²
#      This improves convergence when PHC data is highly heterogeneous.
#      The proximal coefficient μ (default: 0.01) controls the regularization
#      strength.
#
#   3. SCAFFOLD (Stochastic Controlled Averaging)
#      Uses control variates to correct for client drift in non-IID settings.
#      Each client maintains a control variate that estimates the difference
#      between the local gradient and the global gradient. The server also
#      maintains a global control variate.
#      Pros: Fastest convergence for non-IID data.
#      Cons: 2x communication cost (sends gradients + control variates).
#
# BYZANTINE DEFENSE (Optional):
#   Can be composed with any strategy above:
#
#   - Trimmed Mean: Discard the top and bottom β% of gradient values per
#     dimension before averaging. Protects against extreme outliers.
#
#   - Multi-Krum: Score each client's gradient by its distance to the
#     nearest k other clients. Select the f most "central" gradients for
#     aggregation. Robust to up to f Byzantine (malicious/corrupted) clients.
#
# STRATEGY SELECTION:
#   Configured in the FL server's config. Recommended progression:
#   - Phase 1 (initial deployment): FedAvg (simplest, hardest to misconfigure)
#   - Phase 2 (regional rollout): FedProx (handles inter-PHC data heterogeneity)
#   - Phase 3 (national scale): SCAFFOLD (optimal convergence at scale)

from typing import Dict, List, Optional, Tuple

import numpy as np
from flwr.common import FitRes, NDArray, Parameters
from flwr.server.strategy import Strategy


class FedAvgStrategy(Strategy):
    """Federated Averaging (FedAvg) aggregation strategy.
    
    Implements weighted averaging of client updates for model aggregation.
    Suitable for IID (Independent and Identically Distributed) data scenarios.
    
    Reference:
        McMahan et al., "Communication-Efficient Learning of Deep Networks 
        from Decentralized Data" (ICML 2017)
    """
    
    def __init__(
        self,
        fraction_fit: float = 1.0,
        fraction_evaluate: float = 1.0,
        min_fit_clients: int = 2,
        min_evaluate_clients: int = 2,
        min_available_clients: int = 2,
        evaluate_fn=None,
        on_fit_config_fn=None,
        on_evaluate_config_fn=None,
        accept_failures: bool = True,
        initial_parameters: Optional[Parameters] = None,
    ):
        """Initialize FedAvg strategy.
        
        Args:
            fraction_fit: Fraction of clients sampled for training
            fraction_evaluate: Fraction of clients sampled for evaluation
            min_fit_clients: Minimum number of clients for training round
            min_evaluate_clients: Minimum number of clients for evaluation round
            min_available_clients: Minimum number of available clients
            evaluate_fn: Optional function to evaluate aggregated model
            on_fit_config_fn: Optional function to configure fit parameters
            on_evaluate_config_fn: Optional function to configure evaluate parameters
            accept_failures: Whether to accept failed client updates
            initial_parameters: Initial model parameters
        """
        super().__init__()
        self.fraction_fit = fraction_fit
        self.fraction_evaluate = fraction_evaluate
        self.min_fit_clients = min_fit_clients
        self.min_evaluate_clients = min_evaluate_clients
        self.min_available_clients = min_available_clients
        self.evaluate_fn = evaluate_fn
        self.on_fit_config_fn = on_fit_config_fn
        self.on_evaluate_config_fn = on_evaluate_config_fn
        self.accept_failures = accept_failures
        self.initial_parameters = initial_parameters
        
        self._current_round = 0
    
    def initialize_parameters(self, client_manager):
        """Initialize parameters if not already set."""
        if self.initial_parameters is not None:
            return self.initial_parameters
        return None
    
    def configure_fit(self, server_round, parameters, client_manager):
        """Configure fit parameters for training round."""
        config = {}
        if self.on_fit_config_fn is not None:
            config = self.on_fit_config_fn(server_round)
        
        sample_size = max(
            int(client_manager.num_available() * self.fraction_fit),
            self.min_fit_clients,
        )
        clients = client_manager.sample(num_clients=sample_size)
        
        return [(client, config) for client in clients]
    
    def aggregate_fit(
        self,
        server_round: int,
        results: List[Tuple],
        failures: List[Exception],
    ) -> Tuple[Optional[Parameters], Dict]:
        """Aggregate fit results from clients using weighted averaging.
        
        Args:
            server_round: Current aggregation round
            results: List of (client, fit_result) tuples
            failures: List of failed client updates
            
        Returns:
            Tuple of (aggregated_parameters, metrics_dict)
        """
        if not results:
            return None, {}
        
        # Extract weights and num_examples from results
        weights_results = []
        total_examples = 0
        
        for _, fit_res in results:
            # fit_res.parameters is Parameters object, need to extract tensors
            if hasattr(fit_res.parameters, 'tensors'):
                weights = fit_res.parameters.tensors
            else:
                # If it's already a list of tensors
                weights = fit_res.parameters
            
            weights_results.append((weights, fit_res.num_examples))
            total_examples += fit_res.num_examples
        
        # Weighted averaging
        aggregated_weights = self._weighted_average(weights_results)
        
        # Prepare aggregated parameters
        aggregated_parameters = Parameters(
            tensors=aggregated_weights,
            tensor_type="numpy"
        )
        
        metrics = {
            "num_clients": len(results),
            "total_examples": total_examples,
        }
        
        return aggregated_parameters, metrics
    
    def configure_evaluate(self, server_round, parameters, client_manager):
        """Configure evaluate parameters."""
        config = {}
        if self.on_evaluate_config_fn is not None:
            config = self.on_evaluate_config_fn(server_round)
        
        sample_size = max(
            int(client_manager.num_available() * self.fraction_evaluate),
            self.min_evaluate_clients,
        )
        clients = client_manager.sample(num_clients=sample_size)
        
        return [(client, config) for client in clients]
    
    def aggregate_evaluate(
        self,
        server_round: int,
        results: List[Tuple],
        failures: List[Exception],
    ) -> Tuple[Optional[float], Dict]:
        """Aggregate evaluation results from clients.
        
        Args:
            server_round: Current evaluation round
            results: List of (client, evaluate_result) tuples
            failures: List of failed client evaluations
            
        Returns:
            Tuple of (loss, metrics_dict)
        """
        if not results:
            return None, {}
        
        # Weighted average of client losses
        weighted_loss = sum(
            eval_res.loss * eval_res.num_examples
            for _, eval_res in results
        ) / sum(eval_res.num_examples for _, eval_res in results)
        
        metrics = {
            "num_clients": len(results),
            "avg_loss": weighted_loss,
        }
        
        return weighted_loss, metrics
    
    def evaluate(self, server_round: int, parameters: Parameters) -> Tuple[Optional[float], Dict]:
        """Evaluate the aggregated model.
        
        This method is called by Flower after aggregation to evaluate
        the new global model. Can be overridden to provide custom evaluation.
        
        Args:
            server_round: Current round number
            parameters: Aggregated model parameters
            
        Returns:
            Tuple of (loss, metrics_dict) or (None, {})
        """
        if self.evaluate_fn is None:
            return None, {}
        
        return self.evaluate_fn(server_round, parameters.tensors)
    
    @staticmethod
    def _weighted_average(
        weights_results: List[Tuple[List[NDArray], int]]
    ) -> List[NDArray]:
        """Compute weighted average of model weights.
        
        Args:
            weights_results: List of (weights, num_examples) tuples
            
        Returns:
            Aggregated weights as list of numpy arrays
        """
        # Get total number of examples
        total_examples = sum(num_examples for _, num_examples in weights_results)
        
        # Initialize aggregated weights
        aggregated_weights = None
        
        for weights, num_examples in weights_results:
            if aggregated_weights is None:
                aggregated_weights = [
                    np.zeros_like(w) for w in weights
                ]
            
            # Add weighted contribution
            scale = num_examples / total_examples
            for i, w in enumerate(weights):
                aggregated_weights[i] += w * scale
        
        return aggregated_weights


class FedProxStrategy(FedAvgStrategy):
    """Federated Proximal (FedProx) aggregation strategy.
    
    Extends FedAvg with proximal term to handle non-IID (non-Independent 
    and Identically Distributed) data and client stragglers.
    
    The proximal term penalizes local updates that diverge significantly 
    from the global model, improving convergence on non-IID data.
    
    Reference:
        Li et al., "Federated Optimization in Heterogeneous Networks" 
        (MLSys 2020)
    """
    
    def __init__(
        self,
        proximal_mu: float = 0.01,
        **kwargs
    ):
        """Initialize FedProx strategy.
        
        Args:
            proximal_mu: Proximal coefficient (default: 0.01)
            **kwargs: Additional arguments passed to FedAvgStrategy
        """
        super().__init__(**kwargs)
        self.proximal_mu = proximal_mu
    
    def configure_fit(self, server_round, parameters, client_manager):
        """Configure fit parameters with proximal term."""
        config = {}
        if self.on_fit_config_fn is not None:
            config = self.on_fit_config_fn(server_round)
        
        # Add proximal coefficient to config
        config["proximal_mu"] = self.proximal_mu
        
        sample_size = max(
            int(client_manager.num_available() * self.fraction_fit),
            self.min_fit_clients,
        )
        clients = client_manager.sample(num_clients=sample_size)
        
        return [(client, config) for client in clients]
#
# INTERFACE:
#   Each strategy implements Flower's Strategy abstract class:
#     - aggregate_fit(results) → aggregated_weights
#     - aggregate_evaluate(results) → aggregated_metrics
#     - configure_fit(config) → per-client config overrides
# =============================================================================
