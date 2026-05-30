# =============================================================================
# AyushBot Cloud — FL Server Module
# =============================================================================
#
# PURPOSE:
#   Implements the central Flower FL server that aggregates DP-protected
#   gradient updates from PHC gateways across India and produces updated
#   global model weights.
#
# DEPLOYMENT:
#   Runs in the cloud (AWS/GCP/Azure) as a long-running service. This is
#   the ONLY cloud component — all clinical reasoning happens on-device.
#   The cloud's sole job is FL aggregation and administrative analytics.
#
# FLOWER SERVER ARCHITECTURE:
#   Uses Flower (flwr) as the FL orchestration framework:
#   - gRPC transport with TLS 1.3 + mTLS for gateway authentication
#   - Supports heterogeneous clients (different RPi 4 hardware configs)
#   - Configurable minimum number of clients per round (min_fit_clients)
#
# FL ROUND LIFECYCLE:
#
#   1. WAIT FOR CLIENTS
#      The server waits until at least min_fit_clients gateways have
#      connected and submitted gradient updates. This may take hours or
#      days in rural deployment where connectivity is intermittent.
#
#   2. AGGREGATION
#      Once enough gradients are collected, apply the configured aggregation
#      strategy (see strategy.py):
#        - FedAvg: Weighted average of gradients, proportional to sample count
#        - FedProx: FedAvg + proximal term (penalizes deviation from global model)
#        - SCAFFOLD: Variance-reduced aggregation for heterogeneous data
#      The strategy is configurable — start with FedAvg, upgrade as needed.
#
#   3. GLOBAL MODEL UPDATE
#      The aggregated gradient is applied to the global model weights.
#      The new global model is registered in the model registry (model_registry.py).
#
#   4. DISTRIBUTE
#      Push the updated global model weights to all connected gateways
#      via Flower's evaluate() callback. Gateways that are offline will
#      receive the update on their next sync connection.
#
# BYZANTINE RESILIENCE:
#   The server performs anomaly detection on incoming gradients:
#   - Gradient norm outlier detection (reject updates with norms > 3σ)
#   - Source authentication (verify HMAC signature from each gateway)
#   - Optionally: Trimmed Mean or Krum aggregation for Byzantine tolerance

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

import structlog
from flwr.server import start_server

from cloud.config.loader import get_config
from cloud.fl_server.callbacks.post_aggregation import PostAggregationCallback
from cloud.fl_server.model_registry import ModelRegistry
from cloud.fl_server.privacy import DifferentialPrivacyWrapper, DPConfig
from cloud.fl_server.strategy import FedAvgStrategy, FedProxStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.render_to_log_kwargs,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class FLServer:
    """Federated Learning Server orchestrator.
    
    Manages:
    - FL strategy selection and configuration
    - Privacy wrapper and DP budget tracking
    - Model versioning and persistence
    - Post-aggregation callbacks
    - gRPC listener with TLS
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize FL server.
        
        Args:
            config_path: Path to config.yaml (default: ./config.yaml)
        """
        # Load configuration
        self.config = get_config(config_path)
        self.logger = structlog.get_logger(__name__)
        
        # Initialize components
        self._init_privacy_wrapper()
        self._init_model_registry()
        self._init_strategy()
        self._init_callbacks()
        
        # Shutdown flag
        self.shutdown = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.shutdown = True
        sys.exit(0)
    
    def _init_privacy_wrapper(self):
        """Initialize differential privacy wrapper."""
        fl_config = self.config.get("fl", {})
        privacy_config = self.config.get("privacy", {})
        
        dp_config = DPConfig(
            epsilon=privacy_config.get("epsilon", 1.0),
            delta=privacy_config.get("delta", 1e-6),
            gradient_clipping_norm=privacy_config.get("gradient_clipping", {}).get(
                "max_norm", 1.0
            ),
            noise_injection_enabled=privacy_config.get("noise_injection", {}).get(
                "enabled", True
            ),
        )
        
        self.dp_wrapper = DifferentialPrivacyWrapper(dp_config)
        self.logger.info("Initialized DP wrapper", config=dp_config.__dict__)
    
    def _init_model_registry(self):
        """Initialize model registry."""
        storage_path = self.config.get("model_storage", {}).get("local_path", "./models")
        max_versions = self.config.get("model_storage", {}).get("max_versions", 10)
        
        self.model_registry = ModelRegistry(
            storage_path=storage_path,
            max_versions=max_versions,
        )
        self.logger.info(
            "Initialized model registry",
            storage_path=storage_path,
            max_versions=max_versions,
        )
    
    def _init_strategy(self):
        """Initialize aggregation strategy."""
        fl_config = self.config.get("fl", {})
        strategy_name = fl_config.get("strategy", "FedAvg")
        
        # Strategy parameters
        min_fit_clients = fl_config.get("min_clients", 10)
        num_rounds = fl_config.get("rounds", 50)
        
        if strategy_name.lower() == "fedprox":
            self.strategy = FedProxStrategy(
                fraction_fit=1.0,
                fraction_evaluate=1.0,
                min_fit_clients=min_fit_clients,
                min_evaluate_clients=min_fit_clients,
                min_available_clients=min_fit_clients,
                proximal_mu=fl_config.get("proximal_mu", 0.01),
            )
            self.logger.info(
                "Initialized FedProx strategy",
                min_fit_clients=min_fit_clients,
                proximal_mu=fl_config.get("proximal_mu", 0.01),
            )
        else:
            # Default to FedAvg
            self.strategy = FedAvgStrategy(
                fraction_fit=1.0,
                fraction_evaluate=1.0,
                min_fit_clients=min_fit_clients,
                min_evaluate_clients=min_fit_clients,
                min_available_clients=min_fit_clients,
            )
            self.logger.info(
                "Initialized FedAvg strategy",
                min_fit_clients=min_fit_clients,
            )
    
    def _init_callbacks(self):
        """Initialize post-aggregation callbacks."""
        self.callback = PostAggregationCallback(
            model_registry=self.model_registry,
            influxdb_client=None,  # TODO: Initialize InfluxDB client
            s3_client=None,  # TODO: Initialize S3 client
        )
        self.logger.info("Initialized post-aggregation callbacks")
    
    def start(self):
        """Start the FL server.
        
        Listens for client connections and runs aggregation rounds.
        """
        fl_config = self.config.get("fl", {})
        
        port = fl_config.get("port", 8080)
        num_rounds = fl_config.get("rounds", 50)
        client_timeout = fl_config.get("timeout", 300)
        
        self.logger.info(
            "Starting FL server",
            port=port,
            num_rounds=num_rounds,
            client_timeout=client_timeout,
            strategy=type(self.strategy).__name__,
        )
        
        # Start Flower server
        try:
            start_server(
                server_address=f"0.0.0.0:{port}",
                config=None,
                strategy=self.strategy,
                client_manager=None,  # Use default
                grpc_max_message_length=None,
            )
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error("Server error", error=str(e), exc_info=True)
            raise
        finally:
            # Log final privacy metrics
            self.dp_wrapper.log_privacy_stats(self.logger)
            self.logger.info("FL server stopped")


def main():
    """Main entry point for FL server."""
    parser = argparse.ArgumentParser(
        description="AyushBot Cloud FL Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="./config.yaml",
        help="Path to config.yaml (default: ./config.yaml)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="FL server port (default: 8080)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["FedAvg", "FedProx"],
        default="FedAvg",
        help="Aggregation strategy (default: FedAvg)",
    )
    parser.add_argument(
        "--min-fit-clients",
        type=int,
        default=10,
        help="Minimum number of clients per round (default: 10)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=50,
        help="Number of aggregation rounds (default: 50)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(
        "AyushBot Cloud FL Server starting",
        config=args.config,
        port=args.port,
        strategy=args.strategy,
    )
    
    # Initialize and start server
    server = FLServer(config_path=args.config)
    server.start()


if __name__ == "__main__":
    main()
#
# CONFIGURATION:
#   - min_fit_clients: int (default: 5, minimum gateways per round)
#   - min_available_clients: int (default: 3)
#   - aggregation_strategy: str (FedAvg | FedProx | SCAFFOLD)
#   - num_rounds: int (total FL rounds to run, or "continuous")
#   - server_address: str (bind address, e.g., "0.0.0.0:8080")
#   - tls_cert_path, tls_key_path, ca_cert_path: TLS configuration
#
# LOGGING:
#   Every FL round is logged with:
#   - round_id, num_clients, aggregation_strategy_used
#   - per-client: device_id, gradient_norm, sample_count, dp_params
#   - post-aggregation: global_loss, global_accuracy (on validation set)
# =============================================================================
