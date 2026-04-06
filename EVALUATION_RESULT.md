# EVALUATION_RESULT

## Token Efficiency
- Not enough LLM_METRIC events to compute token efficiency

## Latency
- Not enough LLM_METRIC events to compute latency

## Loop count
- Average Thought->Action cycles per run: 3.5

## Termination Quality
- Success rate: 1/1 (100%)

## Failure Analysis
- InvalidFormat: 2

## How to use the logs
- To reproduce baseline run: `python -m src.telemetry.chatbot_baseline`
- To run the agent (entrypoint): `python main.py`
- To analyze logs and write `EVALUATION_RESULT.md`: `python -m src.telemetry.analyze_logs`
- Latest log used: logs\2026-04-06.log