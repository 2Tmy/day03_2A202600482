import os
import glob
import json
from collections import defaultdict
from typing import Any, Dict, List, Tuple

LOG_DIR = "logs"


def parse_json_from_line(line: str) -> Any:
    i = line.find('{')
    if i == -1:
        return None
    try:
        return json.loads(line[i:])
    except Exception:
        return None


def find_latest_log(log_dir: str = LOG_DIR) -> str:
    files = glob.glob(os.path.join(log_dir, "*.log"))
    if not files:
        return ""
    return max(files, key=os.path.getmtime)


def load_all_events(log_dir: str = LOG_DIR) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    metrics = []
    errors = []
    steps = []
    finals = []
    for fp in glob.glob(os.path.join(log_dir, "*.log")):
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                obj = parse_json_from_line(line)
                if not obj:
                    continue
                ev = obj.get("event")
                data = obj.get("data", {})
                if ev == "LLM_METRIC":
                    metrics.append(data)
                elif ev == "AGENT_ERROR":
                    errors.append(data)
                elif ev == "AGENT_STEP":
                    steps.append(data)
                elif ev == "AGENT_FINAL":
                    finals.append(data)
    return metrics, errors, steps, finals


def aggregate_metrics(metrics: List[Dict[str, Any]]) -> Tuple[Dict[Tuple[str, str, str], Dict[str, float]], Dict[str, Dict[str, float]]]:
    per = {}
    by_run = {}
    for m in metrics:
        provider = m.get('provider') or 'unknown'
        model = m.get('model') or 'unknown'
        run_type = m.get('run_type') or 'unknown'
        key = (provider, model, run_type)
        st = per.setdefault(key, {"count": 0, "latency_sum": 0.0, "total_tokens_sum": 0.0, "prompt_sum": 0.0, "completion_sum": 0.0, "cost_sum": 0.0})
        st['count'] += 1
        st['latency_sum'] += float(m.get('latency_ms', 0))
        st['total_tokens_sum'] += float(m.get('total_tokens', 0))
        st['prompt_sum'] += float(m.get('prompt_tokens', 0))
        st['completion_sum'] += float(m.get('completion_tokens', 0))
        st['cost_sum'] += float(m.get('cost_estimate', 0))

        rr = by_run.setdefault(run_type, {"count": 0, "latency_sum": 0.0, "total_tokens_sum": 0.0, "prompt_sum": 0.0, "completion_sum": 0.0, "cost_sum": 0.0})
        rr['count'] += 1
        rr['latency_sum'] += float(m.get('latency_ms', 0))
        rr['total_tokens_sum'] += float(m.get('total_tokens', 0))
        rr['prompt_sum'] += float(m.get('prompt_tokens', 0))
        rr['completion_sum'] += float(m.get('completion_tokens', 0))
        rr['cost_sum'] += float(m.get('cost_estimate', 0))

    per_avg = {}
    for k, v in per.items():
        c = v['count']
        per_avg[k] = {
            'count': c,
            'avg_latency': v['latency_sum'] / c if c else 0.0,
            'avg_total_tokens': v['total_tokens_sum'] / c if c else 0.0,
            'avg_prompt': v['prompt_sum'] / c if c else 0.0,
            'avg_completion': v['completion_sum'] / c if c else 0.0,
            'avg_cost': v['cost_sum'] / c if c else 0.0,
        }

    run_avg = {}
    for k, v in by_run.items():
        c = v['count']
        run_avg[k] = {
            'count': c,
            'avg_latency': v['latency_sum'] / c if c else 0.0,
            'avg_total_tokens': v['total_tokens_sum'] / c if c else 0.0,
            'avg_prompt': v['prompt_sum'] / c if c else 0.0,
            'avg_completion': v['completion_sum'] / c if c else 0.0,
            'avg_cost': v['cost_sum'] / c if c else 0.0,
        }

    return per_avg, run_avg


def write_evaluation_result(latest_log: str, per_avg: Dict, run_avg: Dict, errors: List[Dict], steps: List[Dict], finals: List[Dict]):
    lines = []
    lines.append('# EVALUATION_RESULT')
    lines.append('')

    lines.append('## Token Efficiency')
    chatbot = run_avg.get('chatbot')
    agent = run_avg.get('agent')
    if chatbot and agent:
        chatbot_pct = (chatbot['avg_prompt']/chatbot['avg_total_tokens']*100) if chatbot['avg_total_tokens'] else 0
        agent_pct = (agent['avg_prompt']/agent['avg_total_tokens']*100) if agent['avg_total_tokens'] else 0
        lines.append(f"- Chatbot avg_total_tokens: {chatbot['avg_total_tokens']:.1f}, avg_prompt: {chatbot['avg_prompt']:.1f} ({chatbot_pct:.0f}% )")
        lines.append(f"- Agent avg_total_tokens: {agent['avg_total_tokens']:.1f}, avg_prompt: {agent['avg_prompt']:.1f} ({agent_pct:.0f}% )")
        ratio = agent['avg_total_tokens'] / chatbot['avg_total_tokens'] if chatbot['avg_total_tokens'] else float('inf')
        cost_ratio = agent['avg_cost'] / chatbot['avg_cost'] if chatbot['avg_cost'] else float('inf')
        lines.append(f"- Agent uses {ratio:.2f}x tokens and costs {cost_ratio:.2f}x compared to Chatbot")
    else:
        lines.append('- Not enough LLM_METRIC events to compute token efficiency')

    lines.append('')
    lines.append('## Latency')
    if chatbot and agent:
        lines.append(f"- Chatbot avg_latency_ms: {chatbot['avg_latency']:.1f} ms")
        lines.append(f"- Agent avg_latency_ms: {agent['avg_latency']:.1f} ms")
        speed_ratio = agent['avg_latency']/chatbot['avg_latency'] if chatbot['avg_latency'] else float('inf')
        lines.append(f"- Agent is {speed_ratio:.2f}x slower")
    else:
        lines.append('- Not enough LLM_METRIC events to compute latency')

    lines.append('')
    lines.append('## Loop count')
    if steps:
        counts = {}
        for s in steps:
            rid = s.get('run_id', 'unknown')
            counts[rid] = counts.get(rid, 0) + 1
        avg_steps = sum(counts.values()) / len(counts) if counts else 0
        lines.append(f"- Average Thought->Action cycles per run: {avg_steps:.1f}")
    else:
        lines.append('- Not available in logs. Add `AGENT_STEP` events to the agent to capture loop count')

    lines.append('')
    lines.append('## Termination Quality')
    if finals:
        succ = sum(1 for f in finals if f.get('status') == 'success')
        total = len(finals)
        lines.append(f"- Success rate: {succ}/{total} ({(succ/total*100):.0f}%)")
    else:
        lines.append('- Not available in logs. Add `AGENT_FINAL` events to record termination status')

    lines.append('')
    lines.append('## Failure Analysis')
    if errors:
        types = {}
        for e in errors:
            t = e.get('error_type', 'unknown')
            types[t] = types.get(t, 0) + 1
        for t, c in types.items():
            lines.append(f"- {t}: {c}")
    else:
        lines.append('- No `AGENT_ERROR` entries found in logs')

    lines.append('')
    lines.append('## How to use the logs')
    lines.append('- To reproduce baseline run: `python -m src.telemetry.chatbot_baseline`')
    lines.append('- To run the agent (entrypoint): `python main.py`')
    lines.append('- To analyze logs and write `EVALUATION_RESULT.md`: `python -m src.telemetry.analyze_logs`')
    lines.append(f"- Latest log used: {latest_log}")

    with open('EVALUATION_RESULT.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('EVALUATION_RESULT.md written (concise answers).')


def main():
    metrics, errors, steps, finals = load_all_events()
    per_avg, run_avg = aggregate_metrics(metrics)
    latest = find_latest_log()
    # Print summary (existing behavior)
    print('\nPer provider/model/run_type summary:\n')
    base_keys = set((p, m) for (p, m, r) in per_avg.keys())
    for base in sorted(base_keys):
        p, m = base
        print(f"=== {p}|{m} ===")
        run_types = [k[2] for k in per_avg.keys() if k[0] == p and k[1] == m]
        for rt in sorted(set(run_types)):
            v = per_avg.get((p, m, rt))
            if not v:
                continue
            print(f"{rt}: count={v['count']}, avg_latency_ms={round(v['avg_latency'],1)}, avg_total_tokens={round(v['avg_total_tokens'],1)}, avg_cost={round(v['avg_cost'],6)}")
        print()

    print('Overall by run_type:\n')
    for rt, v in run_avg.items():
        print(f"{rt}: count={v['count']}, avg_latency_ms={round(v['avg_latency'],1)}, avg_total_tokens={round(v['avg_total_tokens'],1)}, avg_cost={round(v['avg_cost'],6)}")

    # write concise evaluation
    write_evaluation_result(latest, per_avg, run_avg, errors, steps, finals)


if __name__ == '__main__':
    main()
