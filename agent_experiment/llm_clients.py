"""
llm_clients.py — battle-tested Bedrock frontier-model callers for ICAIF agent
==============================================================================
Validated 2026-07 on account 507119077431:
  - fable-5 via bedrock-runtime (us-east-1): emits a `thinking` block first;
    parse all `text` blocks; max_tokens must be large enough (>=4000).
  - GPT 5.6 sol via bedrock-mantle OpenAI Responses API (us-east-2):
    bearer token from aws_bedrock_token_generator, refresh ~10 min.

Usage:
    from llm_clients import FrontierClient
    fc = FrontierClient('fable')      # or 'gpt56'
    text = fc.call("your prompt")     # returns model text (str)
    js   = fc.call_json("prompt asking for JSON")  # parsed dict or {'error':...}

Batch helper:
    from llm_clients import batch_score
    batch_score(items, prompt_fn, model='fable', out_csv='results/scores.csv',
                key_fn=lambda it: {'id': it['id']}, workers=6)
"""
import json, re, time, threading

MODELS = {
    'fable': {'provider': 'bedrock', 'id': 'us.anthropic.claude-fable-5',
              'region': 'us-east-1'},
    'gpt56': {'provider': 'mantle', 'id': 'openai.gpt-5.6-sol',
              'region': 'us-east-2'},
}


class FrontierClient:
    def __init__(self, model_key, workers=6, reasoning_effort='low'):
        self.cfg = MODELS[model_key]
        self.model_key = model_key
        self.effort = reasoning_effort
        if self.cfg['provider'] == 'bedrock':
            import boto3
            from botocore.config import Config
            self._client = boto3.client(
                'bedrock-runtime', region_name=self.cfg['region'],
                config=Config(retries={'max_attempts': 6, 'mode': 'adaptive'},
                              read_timeout=600,
                              max_pool_connections=workers * 2))
        else:
            import requests
            from aws_bedrock_token_generator import provide_token
            self._requests = requests
            self._provide_token = provide_token
            self._state = {'token': provide_token(region=self.cfg['region']),
                           'ts': time.time()}
            self._url = (f"https://bedrock-mantle.{self.cfg['region']}"
                         f".api.aws/openai/v1/responses")

    def call(self, prompt, max_tokens=64000):  # POLICY_NO_BUDGET_CAP
        if self.cfg['provider'] == 'bedrock':
            r = self._client.invoke_model(
                modelId=self.cfg['id'], contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': max_tokens,
                    'messages': [{'role': 'user', 'content': prompt}]}))
            out = json.loads(r['body'].read())
            return '\n'.join(b.get('text', '') for b in out['content']
                             if b.get('type') == 'text')
        # mantle
        if time.time() - self._state['ts'] > 600:
            self._state['token'] = self._provide_token(
                region=self.cfg['region'])
            self._state['ts'] = time.time()
        r = self._requests.post(
            self._url,
            headers={'Authorization': f"Bearer {self._state['token']}",
                     'Content-Type': 'application/json'},
            json={'model': self.cfg['id'],
                  'input': [{'role': 'user', 'content': prompt}],
                  'reasoning': {'effort': self.effort},
                  'text': {'verbosity': 'low'}},
            timeout=600)
        r.raise_for_status()
        out = r.json()
        if out.get('output_text'):
            return out['output_text']
        parts = []
        for item in out.get('output', []):
            if isinstance(item, dict):
                for c in item.get('content') or []:
                    if c.get('type') in ('output_text', 'text'):
                        parts.append(c.get('text', ''))
        return '\n'.join(parts)

    def call_json(self, prompt, retries=4, **kw):
        for a in range(retries + 1):
            try:
                raw = self.call(prompt, **kw)
                m = re.search(r'\{.*\}', raw, re.DOTALL)
                if m:
                    return json.loads(m.group())
            except Exception as e:
                if a == retries:
                    return {'error': str(e)[:150]}
            time.sleep(3 * (a + 1))
        return {'error': 'no_json_in_response'}


def batch_score(items, prompt_fn, model, out_csv, key_fn,
                workers=6, checkpoint=50):
    """Parallel, resume-capable batch scoring.
    items: iterable; prompt_fn(item)->prompt; key_fn(item)->dict of id cols.
    Appends model JSON fields to each row; writes/resumes out_csv."""
    import os
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor, as_completed
    fc = FrontierClient(model, workers=workers)
    lock = threading.Lock()
    done, results = set(), []
    if os.path.exists(out_csv):
        prev = pd.read_csv(out_csv)
        keycols = list(key_fn(items[0]).keys())
        done = set(tuple(str(r[c]) for c in keycols)
                   for _, r in prev.iterrows())
        results = prev.to_dict('records')
    todo = [it for it in items
            if tuple(str(v) for v in key_fn(it).values()) not in done]
    print(f"[{model}] todo={len(todo)} (resumed {len(results)})", flush=True)

    def work(it):
        js = fc.call_json(prompt_fn(it))
        return {**key_fn(it), **js}

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(work, it) for it in todo]
        for i, f in enumerate(as_completed(futs)):
            with lock:
                results.append(f.result())
                if (i + 1) % checkpoint == 0:
                    pd.DataFrame(results).to_csv(out_csv, index=False)
                    print(f"  {len(results)} ({(time.time()-t0)/60:.1f} min)",
                          flush=True)
    pd.DataFrame(results).to_csv(out_csv, index=False)
    print(f"[{model}] done: {len(results)} -> {out_csv}", flush=True)
    return results
