import time
import os
from typing import Dict, Any, List, Optional
from src.telemetry.logger import logger


class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.

    Enhancements:
    - Includes optional `run_type` (e.g., 'chatbot' or 'agent') so logs can be
      compared across run types.
    - Cost calculation uses configurable per-provider rates (env vars) with
      sensible defaults.
    """

    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int, run_type: Optional[str] = None):
        """
        Logs a single request metric to our telemetry and emits a structured
        `LLM_METRIC` event to the logger.

        Args:
            provider: short provider id (e.g., 'openai', 'google', 'local')
            model: model identifier or path
            usage: dict with token counts (prompt_tokens, completion_tokens, total_tokens)
            latency_ms: measured latency in milliseconds
            run_type: optional tag to distinguish 'chatbot' vs 'agent' runs
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(provider, model, {"total_tokens": total_tokens}),
            "run_type": run_type
        }

        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, provider: str, model: str, usage: Dict[str, int]) -> float:
        """
        Estimate cost using simple per-1k-token rates. Rates can be overridden
        with environment variables for reproducible experiments.

        Environment variables (optional):
          - COST_PER_1K_OPENAI
          - COST_PER_1K_GOOGLE
          - COST_PER_1K_LOCAL

        Returns a float cost rounded to 6 decimal places.
        """
        # sensible defaults (in USD per 1000 tokens) for lab purposes
        defaults = {
            "openai": float(os.getenv("COST_PER_1K_OPENAI", "0.02")),
            "google": float(os.getenv("COST_PER_1K_GOOGLE", "0.015")),
            "local": float(os.getenv("COST_PER_1K_LOCAL", "0.002")),
        }

        price_per_1k = defaults.get(provider, float(os.getenv("COST_PER_1K_DEFAULT", "0.01")))
        total_tokens = usage.get("total_tokens", 0)
        cost = (total_tokens / 1000.0) * price_per_1k
        return round(cost, 6)


# Global tracker instance
tracker = PerformanceTracker()
