import os
import sys
import time
import json
import glob

# ensure repo root is importable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib
import types
from src.core.llm_provider import LLMProvider
from src.telemetry.metrics import tracker

# We'll inject mock provider modules into sys.modules before importing `main` so
# importing `main` during tests won't attempt to use external SDKs.


def test_agent_runs_and_logs(tmp_path):
    # create a distinct run id so we can filter the log entries
    run_id = f"test-run-{int(time.time())}"
    os.environ["RUN_ID"] = run_id

    class MockProvider(LLMProvider):
        def __init__(self, model_name="mock-model"):
            super().__init__(model_name)

        def generate(self, prompt: str, system_prompt=None, run_type=None):
            usage = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            latency_ms = 10
            try:
                tracker.track_request("mock", self.model_name, usage, latency_ms, run_type=run_type)
            except Exception:
                pass
            return {"content": "Final Answer: mocked result", "usage": usage, "latency_ms": latency_ms, "provider": "mock"}

        def stream(self, prompt: str, system_prompt=None, run_type=None):
            yield "mocked"

    # create fake provider modules to satisfy imports inside main
    gem_mod = types.ModuleType('src.core.gemini_provider')
    setattr(gem_mod, 'GeminiProvider', MockProvider)
    sys.modules['src.core.gemini_provider'] = gem_mod

    loc_mod = types.ModuleType('src.core.local_provider')
    setattr(loc_mod, 'LocalProvider', MockProvider)
    sys.modules['src.core.local_provider'] = loc_mod

    # import main after injecting mocks
    main = importlib.import_module('main')

    # ensure logs folder exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # run the agent via main entrypoint
    main.main()

    # locate latest log and assert our run produced LLM_METRIC and AGENT_FINAL
    files = glob.glob(os.path.join('logs', '*.log'))
    assert files, "No log files found after running agent"
    latest = max(files, key=os.path.getmtime)

    found_metric = False
    found_final = False
    with open(latest, 'r', encoding='utf-8') as f:
        for line in f:
            i = line.find('{')
            if i == -1:
                continue
            try:
                obj = json.loads(line[i:])
            except Exception:
                continue
            ev = obj.get('event')
            data = obj.get('data', {})
            if ev == 'LLM_METRIC' and data.get('run_type') == 'agent':
                found_metric = True
            if ev == 'AGENT_FINAL' and data.get('run_id') == run_id:
                found_final = True

    assert found_metric, "No LLM_METRIC (agent) found in latest log"
    assert found_final, "No AGENT_FINAL found for our run_id in latest log"
