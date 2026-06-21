"""Database connection helpers for dashboard."""

import os
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


class InfluxDBConnection:
    """InfluxDB connection wrapper."""

    def __init__(
        self,
        url: str = "http://localhost:8086",
        bucket: str = "ayushbot",
        org: str = "ayushbot",
        token: Optional[str] = None,
    ):
        """Initialize InfluxDB connection.

        Args:
            url: InfluxDB server URL
            bucket: Target bucket name
            org: Organization name
            token: API token (optional, can be env var INFLUXDB_TOKEN)
        """
        self.url = url
        self.bucket = bucket
        self.org = org
        self.token = token or os.getenv("INFLUXDB_TOKEN", "")
        self.client = None

        try:
            from influxdb_client import InfluxDBClient

            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
            logger.info("InfluxDB client initialized", url=self.url)
        except ImportError:
            logger.warning("influxdb_client not installed, skipping connection")
        except Exception as e:
            logger.error("Failed to initialize InfluxDB client", error=str(e))

    def query_metrics(self, measurement: str, filters: dict = None) -> list:
        """Query metrics from InfluxDB.

        Args:
            measurement: Measurement name (e.g., "phc_metrics")
            filters: Optional filters (e.g., {"phc_id": "PHC001"})

        Returns:
            List of metric records
        """
        if not self.client:
            logger.warning("InfluxDB client not available")
            return []

        try:
            query_api = self.client.query_api()
            query = (
                f'from(bucket:"{self.bucket}") '
                f'|> range(start: -24h) '
                f'|> filter(fn: (r) => r._measurement == "{measurement}")'
            )

            if filters:
                for key, value in filters.items():
                    query += f' |> filter(fn: (r) => r.{key} == "{value}")'

            result = query_api.query(query)
            metrics = []
            for table in result:
                for record in table.records:
                    metrics.append(
                        {
                            "time": record.get_time(),
                            "field": record.field,
                            "value": record.value,
                            "tags": record.tags,
                        }
                    )
            return metrics
        except Exception as e:
            logger.error("InfluxDB query failed", error=str(e), measurement=measurement)
            return []


class PostgreSQLConnection:
    """PostgreSQL connection wrapper."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "ayushbot",
        user: str = "ayushbot",
        password: Optional[str] = None,
    ):
        """Initialize PostgreSQL connection.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password (can be env var POSTGRES_PASSWORD)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password or os.getenv("POSTGRES_PASSWORD", "")
        self.conn = None

        try:
            import psycopg2
            from psycopg2.pool import SimpleConnectionPool

            self.conn = SimpleConnectionPool(
                1,
                20,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            logger.info("PostgreSQL connection pool initialized", host=self.host)
        except ImportError:
            logger.warning("psycopg2 not installed, skipping connection")
        except Exception as e:
            logger.error("Failed to initialize PostgreSQL", error=str(e))

    def query_audit_logs(self, limit: int = 100) -> list:
        """Query audit logs from PostgreSQL.

        Args:
            limit: Maximum number of records

        Returns:
            List of audit log records
        """
        if not self.conn:
            logger.warning("PostgreSQL connection not available")
            return []

        try:
            connection = self.conn.getconn()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id, timestamp, event_type, details FROM audit_logs ORDER BY timestamp DESC LIMIT %s",
                (limit,),
            )
            records = cursor.fetchall()
            self.conn.putconn(connection)
            return records
        except Exception as e:
            logger.error("PostgreSQL query failed", error=str(e))
            return []
