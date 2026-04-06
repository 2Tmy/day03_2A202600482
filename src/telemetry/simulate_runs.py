# Generates fake/synthetic LLM_METRIC events for demos or when you can't call real APIs.

import time
import random
import uuid

from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

RUN_ID = str(uuid.uuid4())[:8]


def simulate(provider: str, model: str, num_runs: int, run_type: str, base_latency_ms: int, base_total_tokens: int):
    print(f"Simulating {num_runs} runs for {run_type} ({provider}/{model})")
    for i in range(num_runs):
        latency = max(10, int(random.gauss(base_latency_ms, base_latency_ms * 0.15)))
        total_tokens = max(1, int(random.gauss(base_total_tokens, base_total_tokens * 0.2)))
        prompt_tokens = int(total_tokens * 0.3)
        completion_tokens = total_tokens - prompt_tokens
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

        # Log a run-specific event
        logger.log_event(f"SIM_{run_type.upper()}", {
            "run_id": RUN_ID,
            "provider": provider,
            "model": model,
            "iteration": i + 1,
            "latency_ms": latency,
            "total_tokens": total_tokens,
        })

        # Track LLM metric (this writes an LLM_METRIC event as well)
        tracker.track_request(provider, model, usage, latency, run_type=run_type)

        time.sleep(0.05)


if __name__ == "__main__":
    # Two simulated providers/models to compare. Adjust counts as needed.
    # Use Gemini labels for simulated remote-provider runs (no fake gpt-sim-1)
    simulate("google", "gemini-1.5-flash", num_runs=8, run_type="chatbot", base_latency_ms=220, base_total_tokens=140)
    simulate("google", "gemini-1.5-flash", num_runs=8, run_type="agent", base_latency_ms=900, base_total_tokens=520)
    simulate("local", "Phi-3-mini-4k", num_runs=6, run_type="chatbot", base_latency_ms=450, base_total_tokens=300)
    simulate("local", "Phi-3-mini-4k", num_runs=6, run_type="agent", base_latency_ms=1200, base_total_tokens=900)

    print("Simulation complete. Run src.telemetry.analyze_logs.py to see aggregated comparisons.")
