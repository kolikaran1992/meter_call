"""
MeterCall: A module for reliable LLM API calling, fallback, and usage metrics logging.

This library provides the LLMFallbackCaller for resilient interaction with various
LLM providers via litellm, alongside concrete implementations for metric logging.
"""

# Import core classes and functions for direct access
from .llm_fallback_call import LLMFallbackCaller
from .metric_logging import MySQLMetricLogger, JsonMetricLogger, MetricLoggerBase

# --- Public API Definition ---
__all__ = [
    "LLMFallbackCaller",
    "MySQLMetricLogger",
    "JsonMetricLogger",
    "MetricLoggerBase",
]
