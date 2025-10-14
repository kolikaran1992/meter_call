from dynaconf import Dynaconf
import mysql.connector
import asyncmy
import json
import traceback as tb
from meter_call.metric_logging.base import MetricLoggerBase
from meter_call.omniconfig import logger


class MySQLMetricLogger(MetricLoggerBase):
    """
    Handles all MySQL-related metric logging, both sync and async.
    """

    def __init__(self, config: Dynaconf):
        super().__init__()
        self._mysql_sync_conn = None
        self._mysql_async_pool = None
        self._sync_available = False
        self._async_available = False
        self.config = config
        self.init_sync_connection()

    def init_sync_connection(self):
        """Initializes synchronous MySQL connection."""
        try:
            self._mysql_sync_conn = mysql.connector.connect(
                **self.config.as_dict()["MYSQL"]
            )
            self._sync_available = True
            logger.info("Sync MySQL connection available")
        except mysql.connector.Error:
            self._mysql_sync_conn = None
            logger.exception("Failed to initialize Sync MySQL client")
            logger.exception(tb.format_exc())

    async def init_async_connection(self):
        """Initializes asynchronous MySQL connection pool."""
        try:
            self._mysql_async_pool = await asyncmy.create_pool(
                **self.config.as_dict()["MYSQL"]
            )
            self._async_available = True
            logger.info("Async MySQL connection available")
        except Exception:
            self._mysql_async_pool = None
            self._async_available = False
            logger.exception("Failed to initialize async MySQL client")
            logger.exception(tb.format_exc())

    def log_metrics_sync(self, **metrics):
        """Logs metrics to MySQL synchronously."""
        if not self._sync_available or self._mysql_sync_conn is None:
            logger.warning("MySQL sync not available, metric not logged")
            return

        metrics_data = self._prepare_metrics(**metrics)
        columns = ", ".join(metrics_data.keys())
        placeholders = ", ".join(["%s"] * len(metrics_data))
        sql = f"INSERT INTO model_usage ({columns}) VALUES ({placeholders})"
        values = [int(v) if isinstance(v, bool) else v for v in metrics_data.values()]
        try:
            cursor = self._mysql_sync_conn.cursor()
            cursor.execute(sql, values)
            self._mysql_sync_conn.commit()
            logger.info(f"logged metrics {json.dumps(metrics_data)} to MySQL")
            cursor.close()
        except mysql.connector.Error as e:
            self._mysql_sync_conn.rollback()
            logger.exception(f"MySQL insert failed: {e}, {json.dumps(metrics_data)}")

    async def log_metrics_async(self, **metrics):
        """Logs metrics to MySQL asynchronously."""
        if not self._async_available or self._mysql_async_pool is None:
            logger.warning("MySQL async not available, metric not logged")
            return

        metrics_data = self._prepare_metrics(**metrics)
        columns = ", ".join(metrics_data.keys())
        placeholders = ", ".join(["%s"] * len(metrics_data))
        sql = f"INSERT INTO model_usage ({columns}) VALUES ({placeholders})"
        values = [int(v) if isinstance(v, bool) else v for v in metrics_data.values()]
        try:
            async with self._mysql_async_pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(sql, values)
                await conn.commit()
            logger.info(f"logged metrics {json.dumps(metrics_data)} to MySQL")
        except Exception as e:
            logger.exception(
                f"MySQL error while logging metrics: {e}, {json.dumps(metrics_data)}"
            )

    def close_sync_connection(self):
        """Closes the synchronous MySQL connection and cursor."""
        if self._mysql_sync_conn:
            self._mysql_sync_conn.close()
            self._mysql_sync_conn = None
            self._sync_available = False

    async def close_async_connection(self):
        """Closes the asynchronous MySQL connection pool."""
        if self._mysql_async_pool:
            self._mysql_async_pool.close()
            await self._mysql_async_pool.wait_closed()
            self._mysql_async_pool = None
            self._async_available = False

    # Transfer methods
    def transfer_metrics(self):
        """Transfers metrics from JSON files using the synchronous logger."""
        self._transfer_metrics(self.log_metrics_sync)
