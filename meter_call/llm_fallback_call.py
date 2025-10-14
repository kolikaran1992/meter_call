import time
import asyncio
from litellm import completion, acompletion
from litellm.exceptions import RateLimitError, ServiceUnavailableError, APIError
from meter_call.metric_logging import JsonMetricLogger
from meter_call.omniconfig import logger, config as base_config
from litellm.types.utils import ModelResponse

DEFAULT_METRIC_LOGGER = JsonMetricLogger()


class LLMFallbackCaller:
    def __init__(
        self,
        providers: list,
        max_retries: int = 10,
        backoff_seconds: int = 2,
        max_backoff_seconds: int = 60,
    ):
        """
        :param providers: List of dicts [{ 'model': str, 'api_key': str }]
        """
        self.providers = providers
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds

    def _get_backoff_time(self, attempt: int) -> float:
        """Return exponential backoff time with cap."""
        return min(self.backoff_seconds * (2**attempt), self.max_backoff_seconds)

    def _init_metrics(self, provider: dict, kwargs: dict) -> tuple[dict, dict]:
        """
        Initialize metrics dict and strip step_name/project_name from kwargs.
        Returns (metrics, cleaned_kwargs).
        """
        step_name = kwargs.pop("step_name", "default_step")
        project_name = kwargs.pop("project_name", "default_project")

        metrics = {
            "model_name": provider["model"],
            "step_name": step_name,
            "project_name": project_name,
        }

        return metrics, kwargs

    def _update_metrics_with_response(self, metrics: dict, response) -> dict:
        """Update metrics dictionary with response usage and timing."""
        end_time = base_config.metric_logging.ts_now_iso
        # metrics.update(response.usage.model_dump())
        metrics["id"] = response.id
        metrics["request_end_ts_utc"] = end_time
        metrics["failure_code"] = None
        return metrics

    def _update_metrics_with_failure(self, metrics: dict, error: Exception) -> dict:
        """Update metrics dictionary with failure details."""
        metrics["failure_code"] = error.__class__.__name__[:100]
        return metrics

    def call(
        self,
        messages: list,
        log_metric_func=DEFAULT_METRIC_LOGGER.log_metric_sync,
        **kwargs,
    ) -> ModelResponse:
        if log_metric_func is None:
            raise ValueError("A log_metric_func must be provided")

        last_exception = None

        for provider in self.providers:
            metrics, call_kwargs = self._init_metrics(provider, dict(kwargs))

            for attempt in range(self.max_retries):
                try:
                    metrics["request_start_ts_utc"] = (
                        base_config.metric_logging.ts_now_iso
                    )

                    response = completion(messages=messages, **provider, **call_kwargs)

                    metrics = self._update_metrics_with_response(metrics, response)
                    log_metric_func(**metrics)

                    return response

                except (RateLimitError, ServiceUnavailableError, APIError) as e:
                    last_exception = e
                    metrics = self._update_metrics_with_failure(metrics, e)
                    log_metric_func(**metrics)
                    logger.warning(
                        f"{provider['model']} attempt {attempt + 1} failed: {str(e)}"
                    )

                    delay = self._get_backoff_time(attempt)
                    time.sleep(delay)

                except Exception as e:
                    last_exception = e
                    metrics = self._update_metrics_with_failure(metrics, e)
                    log_metric_func(**metrics)
                    logger.exception(
                        f"{provider['model']} failed with unexpected error: {str(e)}"
                    )
                    break

            logger.info(f"Falling back from {provider['model']} to next provider...")

        raise RuntimeError(f"All providers failed. Last error: {last_exception}")

    async def acall(
        self,
        messages: list,
        log_metric_func=DEFAULT_METRIC_LOGGER.log_metric_async,
        **kwargs,
    ) -> ModelResponse:
        if log_metric_func is None:
            raise ValueError("A log_metric_func must be provided")

        last_exception = None

        for provider in self.providers:
            metrics, call_kwargs = self._init_metrics(provider, dict(kwargs))

            for attempt in range(self.max_retries):
                try:
                    metrics["request_start_ts_uct"] = (
                        base_config.metric_logging.ts_now_iso
                    )

                    response = await acompletion(
                        messages=messages, **provider, **call_kwargs
                    )

                    metrics = self._update_metrics_with_response(metrics, response)
                    await log_metric_func(**metrics)

                    return response

                except (RateLimitError, ServiceUnavailableError, APIError) as e:
                    last_exception = e
                    metrics = self._update_metrics_with_failure(metrics, e)
                    await log_metric_func(**metrics)
                    logger.warning(
                        f"{provider['model']} attempt {attempt + 1} failed: {str(e)}"
                    )

                    delay = self._get_backoff_time(attempt)
                    await asyncio.sleep(delay)

                except Exception as e:
                    last_exception = e
                    metrics = self._update_metrics_with_failure(metrics, e)
                    await log_metric_func(**metrics)
                    logger.exception(
                        f"{provider['model']} failed with unexpected error: {str(e)}"
                    )
                    break

            logger.info(f"Falling back from {provider['model']} to next provider...")

        raise RuntimeError(f"All providers failed. Last error: {last_exception}")
