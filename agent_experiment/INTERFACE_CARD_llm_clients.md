# INTERFACE CARD — llm_clients.FrontierClient (fable-5 via Bedrock; GPT 5.6 sol via Bedrock Mantle), 확인 2026-11-10

소스: `/Users/jihwanw/.kiro/agents/ICAIF_files/llm_clients.py` (읽음, 2026-11-10). 프로브: `agent_experiment/probes/probe_clients_20261110.json`.

## 입력
- `FrontierClient(model_key, workers=6, reasoning_effort='low')`; `MODELS['fable'] = us.anthropic.claude-fable-5 (bedrock-runtime, us-east-1)`, `MODELS['gpt56'] = openai.gpt-5.6-sol (bedrock-mantle Responses API, us-east-2)`. 출처: 파일 상단 `MODELS` dict.
- `call(prompt, max_tokens=64000)`: 단일 user 메시지만 보낸다. **system 프롬프트 없음, temperature·top_p 지정 없음**(제공자 기본값으로 샘플링). 출처: bedrock 분기 `body=json.dumps({'anthropic_version':..., 'max_tokens':..., 'messages':[{'role':'user','content':prompt}]})`; mantle 분기 `json={'model':..., 'input':[{'role':'user','content':prompt}], 'reasoning':{'effort':self.effort}, 'text':{'verbosity':'low'}}`.
- Mantle 토큰은 600초마다 갱신(`self._state['ts']`). fable는 `max_tokens`가 thinking 블록을 포함하므로 ≥4000 권장(파일 docstring).
- 재시도: boto3 `retries={'max_attempts': 6, 'mode': 'adaptive'}`; mantle은 `raise_for_status()` 뒤 예외.

## 출력
- `call()`은 **텍스트 블록만 이어 붙인 문자열**: bedrock은 `content` 중 `type == 'text'`만(thinking 블록 제외), mantle은 `output_text` 또는 `output[].content[].text`. 출처: 해당 줄.
- `call_json(prompt, retries=4)`: 응답에서 **첫 `{` ~ 마지막 `}`를 정규식(`\{.*\}`, DOTALL)으로 잘라 `json.loads`**. 실패 시 3·6·9·12·15초 대기 후 재호출, 끝까지 실패하면 `{'error': ...}` dict. ⇒ 응답에 JSON이 둘 있으면 바깥 괄호로 묶여 깨질 수 있고, `error` 키가 섞인 dict가 **정상 응답처럼 돌아온다** → 실험 코드는 (a) 자체 파서로 필수 키·허용값을 검증하고, (b) `error` 키가 있으면 결측으로 기록·보존(버리지 않음), (c) 재시도 횟수를 로그에 남긴다.
- 프로브(2026-11-10, 한국어 JSON-only 지시): 두 모델 모두 유효 JSON 한 개를 반환(fable 73자, gpt56 52자; 1.5~3.5초). **반복 4회에서 fable은 4/4 'A', gpt56은 3/4 'A'** — 첫 번째 선택지 선호(위치 편향)가 있다. 비네트에서는 행동 선택지의 제시 순서를 무작위화하고 순서를 기록해 위치 효과를 추정·보고해야 한다.

## 난수
- 클라이언트 쪽 시드 없음(제공자 샘플링). 실험의 무작위성(처치 배정, 선택지 순서, 프로필 추출)은 전부 **우리 코드의 `numpy.random.default_rng(seed)`** 에서 나오고 호출별 로그에 기록된다. 같은 프롬프트의 반복 응답은 모델 쪽 샘플링 때문에 달라질 수 있다(gpt56 프로브에서 확인) → 셀당 반복 호출로 평균하고, 응답 변동을 결과에 보고.

## 비용·속도
- 프로브 기준 호출당 1.5~3.5초. `workers` 병렬. 비용 상한 없음(`POLICY_NO_BUDGET_CAP`), 호출 수는 설계 파일에 기록.

## 통제 실험(Stage A 실행 전; `results/04_agent_controls.json`)
1. 드라이런(모의 클라이언트): 배정 균형, 파싱 실패→결측 보존, seed 재현.
2. 파서 테스트: 정상 JSON / 앞뒤 설명문 포함 / 허용값 밖 / `error` dict / 빈 문자열 → 기대 분류.
3. 위치 편향 추정: 실제 호출에서 선택지 순서 더미의 효과(위약 처치와 함께 보고).
4. 위약 처치(무관 속성: 사무실 이전 여부)의 효과 = 0 확인(죽이기 기준 iii).

## 미확인 [UNVERIFIED]
- 제공자 기본 temperature 값(문서에 없음; 결과 해석에 수치로 쓰지 않음).
- 모델 가중치/버전의 시점 고정 여부(모델 id만 기록; 재현 패키지에 호출 일시를 남긴다).
