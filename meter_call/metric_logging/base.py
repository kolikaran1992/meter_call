from pathlib import Path
import getpass
import json
import traceback as tb
import asyncio
from meter_call.omniconfig import logger, config


class MetricLoggerBase:
    """
    Base class for all metric loggers.
    Contains common methods and properties for metric preparation and file handling.
    """

    def __init__(self):
        self.available = False
        self.json_metric_dir = Path(config.metric_logging.json.json_store_dir)

    def _prepare_metrics(self, **metrics):
        """Prepares a metrics dictionary with common data."""
        metrics_data = metrics.copy()
        metrics_data["insert_ts_utc"] = config.metric_logging.ts_now_iso
        metrics_data["user"] = getpass.getuser()
        return metrics_data

    def _transfer_metrics(self, log_method, is_async=False):
        """
        Common method to transfer metrics from JSON files.
        It uses a provided log_method (sync or async) to log the data.
        """
        if not self.available:
            logger.warning("Database not available, cannot transfer metrics")
            return

        for filename in self.json_metric_dir.rglob("*.json"):
            logger.info(f'Transferring metrics from "{filename.as_posix()}"')
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for entry in data:
                    if is_async:
                        asyncio.get_event_loop().create_task(log_method(**entry))
                    else:
                        log_method(**entry)

                filename.unlink()
            except Exception as e:
                logger.error(f"Failed to transfer metrics from {filename}: {e}")
                logger.exception(tb.format_exc())
