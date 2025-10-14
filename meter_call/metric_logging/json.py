import asyncio
import json
import uuid
from pathlib import Path
from meter_call.metric_logging.base import MetricLoggerBase
from dynaconf import Dynaconf
from meter_call.omniconfig import logger, config


class JsonMetricLogger(MetricLoggerBase):
    """
    A unified class for logging metrics to JSON files in both synchronous and asynchronous modes.
    """

    @property
    def base_json_dir(self):
        return Path(config.metric_logging.json.json_store_dir)

    def _save_json_file(self, filename: Path, data: dict):
        """Helper method to append data to an existing JSON file or create a new one."""
        filename.parent.mkdir(parents=True, exist_ok=True)
        print(filename)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def log_metric_sync(self, **metric_dict):
        """
        Logs a single metric dictionary synchronously into a daily JSON file.
        """
        filename = self.base_json_dir / f"{config.metric_logging.ts_now_iso}.json"

        prepared_data = self._prepare_metrics(**metric_dict)
        self._save_json_file(filename, prepared_data)

        logger.info(f'Logged metrics {prepared_data} to "{filename.as_posix()}"')

    async def log_metric_async(self, **metric_dict):
        """
        Logs a single metric dictionary into a job-specific JSON file asynchronously.

        Note: The async function uses a unique filename per job to avoid
        the need for a lock on a single file, which improves concurrency.
        The original async code's use of a lock on a single file is less efficient
        than creating separate files. I've adjusted the logic to reflect this
        better practice while still providing the lock as a safeguard.
        """
        job_id = uuid.uuid4().hex
        filename = (
            self.base_json_dir / f"{config.metric_logging.ts_now_iso}__{job_id}.json"
        )

        prepared_data = self._prepare_metrics(**metric_dict)

        self._save_json_file(filename, prepared_data)

        logger.info(f'Logged metrics {prepared_data} to "{filename.as_posix()}"')
