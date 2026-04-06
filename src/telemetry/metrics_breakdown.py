import os
import glob
import json
from collections import defaultdict

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'logs')
# fallback to workspace logs
if not os.path.exists(LOG_DIR):
    LOG_DIR = os.path.join(os.getcwd(), 'logs')

metrics = []
for fp in glob.glob(os.path.join(LOG_DIR, '*.log')):
    with open(fp, 'r', encoding='utf-8') as f:
        for line in f:
            i = line.find('{')
            if i == -1:
                continue
            try:
                obj = json.loads(line[i:])
            except Exception:
                continue
            if obj.get('event') == 'LLM_METRIC':
                metrics.append(obj['data'])

# compute breakdowns
by_key = defaultdict(lambda: {'count':0, 'prompt_tokens':0, 'completion_tokens':0, 'total_tokens':0, 'latency_sum':0, 'cost_sum':0})
by_run_type = defaultdict(lambda: {'count':0, 'prompt_tokens':0, 'completion_tokens':0, 'total_tokens':0, 'latency_sum':0, 'cost_sum':0})

for m in metrics:
    provider = m.get('provider', 'unknown')
    model = m.get('model', 'unknown')
    run_type = m.get('run_type', 'unknown')
    key = f"{provider}|{model}|{run_type}"
    k = by_key[key]
    k['count'] += 1
    k['prompt_tokens'] += m.get('prompt_tokens', 0)
    k['completion_tokens'] += m.get('completion_tokens', 0)
    k['total_tokens'] += m.get('total_tokens', 0)
    k['latency_sum'] += m.get('latency_ms', 0)
    k['cost_sum'] += m.get('cost_estimate', 0)

    r = by_run_type[run_type]
    r['count'] += 1
    r['prompt_tokens'] += m.get('prompt_tokens', 0)
    r['completion_tokens'] += m.get('completion_tokens', 0)
    r['total_tokens'] += m.get('total_tokens', 0)
    r['latency_sum'] += m.get('latency_ms', 0)
    r['cost_sum'] += m.get('cost_estimate', 0)

print('\nDetailed prompt/completion breakdown per provider|model|run_type:\n')
for key, v in sorted(by_key.items()):
    if v['count'] == 0:
        continue
    avg_prompt = v['prompt_tokens'] / v['count']
    avg_completion = v['completion_tokens'] / v['count']
    avg_total = v['total_tokens'] / v['count']
    avg_lat = v['latency_sum'] / v['count']
    avg_cost = v['cost_sum'] / v['count']
    prompt_ratio = avg_prompt / avg_total if avg_total else 0
    comp_ratio = avg_completion / avg_total if avg_total else 0
    print(f"{key}: count={v['count']}, avg_prompt={avg_prompt:.1f}, avg_completion={avg_completion:.1f}, avg_total={avg_total:.1f}, prompt_ratio={prompt_ratio:.2f}, completion_ratio={comp_ratio:.2f}, avg_latency_ms={avg_lat:.1f}, avg_cost={avg_cost:.6f}")

print('\nOverall breakdown by run_type:\n')
for rt, v in sorted(by_run_type.items()):
    if v['count'] == 0:
        continue
    avg_prompt = v['prompt_tokens'] / v['count']
    avg_completion = v['completion_tokens'] / v['count']
    avg_total = v['total_tokens'] / v['count']
    avg_lat = v['latency_sum'] / v['count']
    avg_cost = v['cost_sum'] / v['count']
    prompt_ratio = avg_prompt / avg_total if avg_total else 0
    comp_ratio = avg_completion / avg_total if avg_total else 0
    print(f"{rt}: count={v['count']}, avg_prompt={avg_prompt:.1f}, avg_completion={avg_completion:.1f}, avg_total={avg_total:.1f}, prompt_ratio={prompt_ratio:.2f}, completion_ratio={comp_ratio:.2f}, avg_latency_ms={avg_lat:.1f}, avg_cost={avg_cost:.6f}")

print('\nDone.')
