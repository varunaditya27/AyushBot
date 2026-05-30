"""Post-aggregation callbacks for FL server."""

import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PostAggregationCallback:
    """Callback executed after each FL aggregation round.
    
    Handles post-round actions such as:
    - Saving aggregated model to storage
    - Writing metrics to time-series database
    - Logging aggregation statistics
    """
    
    def __init__(
        self,
        model_registry=None,
        influxdb_client=None,
        s3_client=None,
    ):
        """Initialize callback.
        
        Args:
            model_registry: ModelRegistry instance for model persistence
            influxdb_client: InfluxDB client for metrics storage
            s3_client: AWS S3 client for model backup (optional)
        """
        self.model_registry = model_registry
        self.influxdb_client = influxdb_client
        self.s3_client = s3_client
    
    def on_round_end(
        self,
        round_num: int,
        aggregated_model: np.ndarray,
        num_clients: int,
        aggregation_strategy: str,
        metrics: Optional[Dict] = None,
    ):
        """Called after aggregation round completes.
        
        Args:
            round_num: Current FL round number
            aggregated_model: Aggregated model weights
            num_clients: Number of clients in this round
            aggregation_strategy: Strategy used (e.g., "FedAvg")
            metrics: Optional dict with round metrics
        """
        metrics = metrics or {}
        
        # Save model to registry
        if self.model_registry:
            try:
                version = self.model_registry.save_model(
                    model_bytes=aggregated_model,
                    round_num=round_num,
                    num_clients=num_clients,
                    aggregation_strategy=aggregation_strategy,
                    metrics=metrics,
                )
                logger.info(f"Model saved as version {version}")
            except Exception as e:
                logger.error(f"Failed to save model: {e}")
        
        # Write metrics to InfluxDB
        if self.influxdb_client:
            try:
                self._write_metrics_to_influxdb(
                    round_num=round_num,
                    num_clients=num_clients,
                    aggregation_strategy=aggregation_strategy,
                    metrics=metrics,
                )
            except Exception as e:
                logger.error(f"Failed to write metrics to InfluxDB: {e}")
        
        # Backup model to S3 (optional)
        if self.s3_client:
            try:
                self._backup_model_to_s3(
                    round_num=round_num,
                    aggregated_model=aggregated_model,
                )
            except Exception as e:
                logger.warning(f"Failed to backup model to S3: {e}")
        
        logger.info(f"Post-aggregation callback completed for round {round_num}")
    
    def _write_metrics_to_influxdb(
        self,
        round_num: int,
        num_clients: int,
        aggregation_strategy: str,
        metrics: Dict,
    ):
        """Write aggregation metrics to InfluxDB.
        
        Args:
            round_num: FL round number
            num_clients: Number of clients
            aggregation_strategy: Strategy name
            metrics: Metrics dictionary
        """
        try:
            from influxdb_client import Point
            from influxdb_client.client.write_api import SYNCHRONOUS
            
            # Prepare point
            point = (
                Point("fl_aggregation")
                .tag("strategy", aggregation_strategy)
                .tag("round", str(round_num))
                .field("num_clients", num_clients)
                .field("total_examples", metrics.get("total_examples", 0))
                .field("avg_loss", float(metrics.get("avg_loss", 0.0)))
            )
            
            # Add any additional metrics
            for key, value in metrics.items():
                if key not in ["total_examples", "avg_loss", "num_clients"]:
                    if isinstance(value, (int, float)):
                        point.field(key, float(value))
            
            # Write to InfluxDB
            self.influxdb_client.write_api(SYNCHRONOUS).write(
                bucket="cloud_metrics",
                record=point
            )
            
            logger.debug(f"Wrote metrics to InfluxDB for round {round_num}")
        except Exception as e:
            logger.error(f"InfluxDB write failed: {e}")
            raise
    
    def _backup_model_to_s3(
        self,
        round_num: int,
        aggregated_model: np.ndarray,
    ):
        """Backup model to S3 with exponential backoff retry.
        
        Args:
            round_num: FL round number
            aggregated_model: Model to backup
        """
        import io
        import time
        
        max_retries = 3
        base_delay = 1.0
        
        # Serialize model to bytes
        buffer = io.BytesIO()
        np.save(buffer, aggregated_model)
        model_bytes = buffer.getvalue()
        
        # Try to upload with exponential backoff
        for attempt in range(max_retries):
            try:
                key = f"models/round_{round_num}/model.npy"
                self.s3_client.put_object(
                    Bucket="ayushbot-models",
                    Key=key,
                    Body=model_bytes,
                )
                logger.info(f"Backed up model to S3: {key}")
                return
            except Exception as e:
                delay = base_delay * (2 ** attempt)
                if attempt < max_retries - 1:
                    logger.warning(
                        f"S3 backup failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"S3 backup failed after {max_retries} attempts: {e}")
                    raise
