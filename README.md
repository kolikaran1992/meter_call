## MeterCall: LLM Fallback and Metrics Module 🚀

**MeterCall** is a Python module designed to streamline **Large Language Model (LLM) API calls** and provide robust **usage metrics and logging**.

Its core functionality includes:

1.  **Centralized LLM Calling:** Provides a unified interface for synchronous (`call`) and asynchronous (`acall`) interactions with various text-based LLMs (e.g., Mistral, OpenAI, etc., via [litellm].
2.  **Fallback Mechanism:** Implements provider-based fallback, automatically retrying calls with subsequent providers in a list upon encountering transient errors (like `RateLimitError` or `ServiceUnavailableError`).
3.  **Metrics Logging:** Captures critical usage metrics (tokens, model ID, response status, failure codes, timestamps) and persists them to configured backends (e.g., local JSON or MySQL via a custom logger).
4.  **Resilience:** Features exponential backoff and maximum retry attempts to handle temporary API instability.

In short, **MeterCall** acts as a resilient, single entry point for all LLM communication, ensuring reliability and cost tracking across different projects.

[litellm]: https://docs.litellm.ai/docs/