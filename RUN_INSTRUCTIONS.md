# Run Instructions — Start to End

This file shows a minimal, repeatable sequence to set up and run the lab from start to finish.

1. Create a Python virtual environment and install dependencies

```bash
python -m venv .venv
# macOS / Linux / Git Bash
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Create a `.env` (minimal example)

Create a single `.env` file at the repo root with the following minimal contents.

```dotenv
# OPENAI SETTINGS
OPENAI_API_KEY=your_openai_api_key_here

# GEMINI SETTINGS
GEMINI_API_KEY=your_gemini_api_key_here

# LOCAL LLM SETTINGS (GGUF via llama-cpp)
# Download model from: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf

# LAB CONFIG
# Options: openai | google | local
# DEFAULT_PROVIDER=openai
DEFAULT_MODEL=./models/Phi-3-mini-4k-instruct-q4.gguf
LOG_LEVEL=INFO

DEFAULT_PROVIDER=local
# LOCAL_MODEL_PATH=./models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

3. Run baseline, optional simulation, and analyze

```bash
# Run baseline, then the demo simulator, then analyze and write EVALUATION_RESULT.md
python -m src.telemetry.run_full_eval --simulate

# Or: only analyze the latest log (no baseline or simulation)
python -m src.telemetry.run_full_eval --analyze-only
```

Direct commands (alternatives):

```bash
# Run just the baseline (calls the configured DEFAULT_PROVIDER)
python -m src.telemetry.chatbot_baseline

# Generate demo logs (standalone fake data)
python -m src.telemetry.simulate_runs

# Analyze latest log only
python -m src.telemetry.run_full_eval --analyze-only
```

4. Simulate vs your agent — how to replace `simulate_runs.py`

`src/telemetry/simulate_runs.py` only generates fake `LLM_METRIC` events for demos. To run your real agent instead, either:

- Option A — Edit the orchestrator (`src/telemetry/run_full_eval.py`):

  Find the call to `run_module('src.telemetry.simulate_runs')` and replace it with your agent runner module, for example:

  ```py
  run_module('src.agent.run_agent')
  ```

  Implement `src/agent/run_agent.py` as a small CLI that starts your agent, emits telemetry using `logger.log_event(...)` and `tracker.track_request(...)`, and exits when done.

- Option B — Run your agent manually and then analyze the latest log:

  ```bash
  python -m src.agent.run_agent
  python -m src.telemetry.run_full_eval --analyze-only
  ```

How to remove the simulator file if you want to delete it later:

```bash
rm src/telemetry/simulate_runs.py
# (PowerShell)
Remove-Item src\telemetry\simulate_runs.py
```

Telemetry your agent should emit (same schema as the simulator):

- `LLM_METRIC` with fields: `provider`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `latency_ms`, `cost_estimate`, `run_type`.
- `AGENT_STEP` for each Thought->Action cycle (optional, for loop-count analysis).
- `AGENT_FINAL` with `status` (`success`/`failure`) for termination quality.
- `AGENT_ERROR` with `error_type` for failure analysis.

5. Outputs

- Logs: `logs/` (the project appends events to the log files in `logs/`; check the latest file there).
- Evaluation: `EVALUATION_RESULT.md` will be written with concise answers after analysis.

6. Quick tips

- Ensure required packages are installed: `pip install -r requirements.txt`.
- If the baseline step errors due to missing provider SDKs (e.g., `openai`), install the relevant package or use `--analyze-only`.

That's it — create the single `.env` above, run the orchestrator, and inspect `EVALUATION_RESULT.md` for results.
