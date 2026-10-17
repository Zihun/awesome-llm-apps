# Day 147 · 🎛️ AI Shadcn Component Generator

> 볼륨 12 🖼️ Generative UI · 난이도 ★★★ ⚠ 원본의 `pnpm dev`는 에이전트를 `0.0.0.0`에 `reload=True`로 열고(`main.py:61-66`), 화면·런타임의 `pnpm install`·`vite`·`tsx`는 이 문서가 실행하지 않았습니다. 화면이 하는 일(스키마 만들기, 부분 JSON 그리기, 코드 내보내기)은 소스로만 읽었고 두 가지는 파이썬으로 옮겨 써 돌려 봤습니다 · 예상 소요 180분(소스 읽기가 여러 JS 패키지에 걸치고, 파이썬 파일 열둘을 직접 저장해 터미널 셋 이상을 오가며 요청 기록과 이벤트를 맞대 읽는 손 시간이 본문 읽는 시간보다 큽니다) · API 비용 대략 이 문서의 따라 하기는 $0(가짜 서버만 부릅니다. 실제 OpenAI·Tavily는 한 번도 부르지 않았습니다). 진짜 키로 첫 질문 하나를 보내면 모델 호출이 한두 번 나가고, 어림으로 $0.05~0.2입니다(⚠ 추정, 아래 사전 준비) · 원본 앱: `generative_ui_agents/ai-shadcn-component-generator`

## 오늘 만들 것

말로 "이런 화면"을 설명하면 shadcn/ui 부품으로 짠 화면이 채팅 안에 그려지고, 그 화면을 React 코드로 내보내는 앱입니다. 프로세스는 셋입니다. Vite 화면(포트 5173, React·CopilotKit·hashbrown), Hono로 만든 CopilotKit 런타임(4000), 파이썬 LangGraph 에이전트(8123). 앱 README는 이것을 "스키마로 부품을 조립하는 생성 UI"라고 부르고, "shadcn 컴포넌트 스키마 전체를 에이전트 문맥으로 넘긴다"고 말합니다. 소스를 읽어 보면 뜻이 조금 다릅니다. 화면이 넘기는 것은 shadcn 전체가 아니라 화면이 직접 고른 부품 열여섯 개(`components/ui/`에는 파일 60개)의 스키마이고, 그 스키마는 문맥 글로 한 번, 모델의 구조화 출력 형식(`response_format`)으로 또 한 번, 두 번 실립니다. 에이전트는 화면을 그리는 도구를 부르지 않습니다. 모델의 마지막 답이 곧 부품 트리 JSON이고, 화면이 스트림으로 오는 그 글을 반쯤 온 채로 파싱해 진짜 React 부품으로 그립니다. Day 143의 A2UI는 연산을 담은 도구 호출이 화면을 만들었으니 방식이 다릅니다.

이 문서는 파이썬 쪽만 실제로 돌렸습니다. 화면과 런타임은 `npm install`·`pnpm install`·`npx`·`vite`·`tsx`를 실행하지 않고 소스로만 읽었습니다. 읽은 JS 패키지(`@copilotkit/*` 1.54.0, `@hashbrownai/*` 0.5.0-beta.4, `@ag-ui/*` 0.0.47)는 npm 레지스트리에서 압축 파일을 내려받아 sha512 값을 맞춘 뒤 풀어서 파일로만 열어 본 것입니다. 브라우저는 한 번도 띄우지 않았으므로 카드와 차트가 실제로 어떻게 보이는지는 보여 드리지 못합니다. 화면이 하는 일 중 둘은 파이썬으로 옮겨 써서 돌렸습니다. `ui_schema.py`는 `chat-kit.tsx`의 부품 목록이 만드는 JSON Schema(hashbrown의 `toJsonSchema` 알고리즘을 따라 씀)이고, `tree_to_jsx.py`는 Export Code가 하는 일입니다. 둘 다 제가 소스를 보고 손으로 옮긴 것이어서 실제 화면의 출력과 글자 하나까지 같다고는 보장하지 못합니다. 모델 자리에는 `127.0.0.1`의 가짜 서버가 있고 그 답은 모두 제가 쓴 대본입니다. 그래서 실제 `gpt-5.5`가 이 스키마를 얼마나 잘 따르는지는 확인하지 못했습니다. OpenAI의 Structured Outputs 문서(2026-10-17에 읽음)는 루트가 `anyOf`가 아닌 객체여야 하고, `anyOf`·`$defs`·`#` 재귀를 지원하며, 객체 속성 5000개·중첩 10단계·이름과 열거값 글자 합 12만 자가 한도라고 적습니다. 이 스키마는 그 안에 있어 보이지만(루트는 객체입니다) `$schema` 키는 문서에 언급이 없어서, 진짜 OpenAI가 strict 모드로 받아 주는지는 확인하지 못했습니다.

![완성 아키텍처](diagrams/overview.svg)

그림의 묶음 안 화살표는 묶음 전체의 것입니다. 묶음 안의 이어짐은 보조 구조 그림이 보여 줍니다. 에이전트 묶음은 Step 2의 `extra-agent`와 Step 5의 `extra-agent-out`, 화면 묶음은 Step 6의 `extra-ui`, 그래프의 노드와 갈래는 Step 4의 `extra-graph`·`extra-branch`, 스키마가 두 번 실리는 길은 Step 3·4의 `extra-schema`·`extra-twice`, 원본의 실행 경로는 Step 8의 `extra-dev`에 있습니다. 그림 오른쪽의 `글꼴` 구름은 화면이 `index.html`에서 부르는 바깥 호스트입니다(Step 8). 앞 날과 이어지는 곳은 이렇습니다. 같은 LangGraph `create_agent`·CopilotKit 미들웨어·AG-UI 서버는 [Day 143](../day143-genui-generative-ui-starter-project/README.md)의 Step 2~3이 가드·가짜 서버·그래프 읽기로 다뤘고, 같은 스택의 다른 앱과 Next.js 쪽 소스 읽기는 [Day 141](../day141-genui-deep-research-agent/README.md)의 Step 4·6이 다뤘습니다. 오늘 새로 나오는 것은 `response_format`을 요청마다 갈아 끼우는 미들웨어, 반쯤 온 JSON을 그리는 hashbrown, 그리고 이 앱이 ag-ui-langgraph에 덧대는 패치 셋입니다.

직접 돌려 알게 된 것이 일곱입니다. 첫째, 잠금 파일대로 설치되고 키가 없으면 `main.py:30`에서 멈춥니다(Step 1). 둘째, 원본 `main.py`를 건드리지 않고 `127.0.0.1`에만 열 수 있고, 헬스 체크 주소는 `/health`가 아니라 `//health`입니다(Step 2). 셋째, 화면의 스키마는 약 1만 자이고(Step 3), 모델 요청에 문맥 글(약 1.2만 자)과 `response_format`(약 1.1만 자)으로 두 번 실립니다(Step 4). 넷째, 같은 스레드의 다음 턴마다 문맥 글이 하나씩 쌓입니다(Step 7). 다섯째, `crawl_site`는 `instructions`를 `max_depth` 자리에 넘깁니다(Step 5). 여섯째, 모델의 마지막 답이 JSON이 아니면 에이전트 서버의 스트림이 오류 신호 없이 끊깁니다(Step 5). 일곱째, `BoundedMemorySaver`는 오래된 스레드의 `storage`만 지우고 `writes`·`blobs`는 남깁니다(Step 7).

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 참고 |
| Python | 이 문서는 3.13.3으로 확인했다. `pyproject.toml`은 `>=3.12`이고 `.python-version`은 없다 | 공통 사전 준비와 같음 |
| OpenAI API 키 | 진짜로 쓸 때만. 이 문서는 가짜 서버와 가짜 값으로 확인한다 | https://platform.openai.com/api-keys |
| Tavily API 키 | 진짜로 쓸 때만. 검색 도구가 쓴다 | https://app.tavily.com |
| Node.js 20 이상 + pnpm | 앱 화면·런타임용. **이 문서는 설치도 실행도 하지 않았다.** 앱 README는 `pnpm install`·`pnpm dev`를 적고, `render.yaml`은 Node 20을 쓴다 | 직접 준비(이 문서는 실행하지 않았음) |
| 터미널 셋 | 가짜 서버(A), 에이전트 서버(B), 요청을 보내는 쪽(C). 셋 다 `shadify-work` 폴더에서 연다 | 별도 설치 없음 |

명령은 Git Bash 기준입니다. 한국어 Windows에서 파이썬 출력이 cp949로 깨지지 않도록 터미널마다 환경변수를 다시 줍니다. PowerShell 줄은 실행해 보지 못했습니다(이 문서를 쓴 하네스가 PowerShell 실행을 막습니다).

**이 앱의 모델이 아직 살아 있는지.** 앱이 쓰는 모델은 `gpt-5.5` 하나입니다(`generative_ui_agents/ai-shadcn-component-generator/apps/agent/main.py:31`, `"openai:gpt-5.5"`). OpenAI 폐기 문서(https://developers.openai.com/api/docs/deprecations)와 모델 페이지(https://developers.openai.com/api/docs/models/gpt-5.5)를 2026-10-16에 읽었습니다. 폐기 문서에 `gpt-5.5`와 그 스냅숏은 올라 있지 않고, 모델 페이지는 기본 스냅숏을 `gpt-5.5-2026-04-23`, `v1/chat/completions`를 Supported로 적습니다. 가격은 입력 $5, 캐시 입력 $0.5, 출력 $30(100만 토큰당)입니다. 비용 어림(⚠ 추정)은 이렇습니다. 첫 질문의 모델 요청 하나가 실은 글이 약 2.4만 자(Step 4에서 잰 값)이니 3~4자에 1토큰으로 어림하면 입력 6~8천 토큰, $0.03~0.04입니다. 모델 페이지는 추론 토큰(reasoning)을 지원하고 `reasoning.effort`의 기본값이 `medium`이라고 적는데 앱은 이 값을 정하지 않으므로, 눈에 보이는 출력 말고 추론 토큰도 출력 요금으로 더해집니다(얼마나 나올지는 알 수 없고 아래 어림에 넣지 못했습니다). 보이는 출력이 1~2천 토큰이면 $0.03~0.06이 더해지고, 도구를 한 번 거치면 입력이 한 번 더 들어갑니다. 같은 스레드에서 턴을 거듭하면 문맥 글이 턴마다 1.2만 자(약 3천 토큰, $0.015)씩 늘어납니다(Step 7).

## 아키텍처 한눈에 보기

이 문서가 소스를 인용하는 서드파티의 판은 이렇습니다. 파이썬: copilotkit 0.1.78(`copilotkit_lg_middleware.py`), langchain 1.2.0(`agents/factory.py`), langchain-openai 1.1.9(`chat_models/base.py`), ag-ui-langgraph 0.0.25(`agent.py`, `endpoint.py`), langgraph-checkpoint 3.0.1(`memory/__init__.py`), tavily-python 0.7.21. JS: `@copilotkit/*`·`@copilotkitnext/*` 1.54.0, `@hashbrownai/*` 0.5.0-beta.4, `@ag-ui/client` 0.0.47, `@ag-ui/langgraph` 0.0.24, `@hono/node-server` 1.19.17, `@scarf/scarf` 1.4.0.

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 에이전트와 서버 (`main.py`) | `create_agent`로 그래프를 만들고 AG-UI 엔드포인트로 노출 | `generative_ui_agents/ai-shadcn-component-generator/apps/agent/main.py:30-56` |
| 미들웨어 둘 (`middleware.py`) | 문맥 항목을 사전으로 바꾸고, 문맥에서 `output_schema`를 꺼내 모델의 `response_format`으로 씀 | `generative_ui_agents/ai-shadcn-component-generator/apps/agent/src/middleware.py:7-56` |
| 검색 도구 (`search.py`) | Tavily의 `search`·`extract`·`crawl`을 도구 셋으로 | `generative_ui_agents/ai-shadcn-component-generator/apps/agent/src/search.py:5-28` |
| 패치 (`patches.py`) | ag-ui-langgraph의 메서드 셋을 바꿔 끼움 | `generative_ui_agents/ai-shadcn-component-generator/apps/agent/src/patches.py:12-43` |
| 체크포인터 (`bounded_memory_saver.py`) | 스레드 200개까지만 메모리에 두는 `MemorySaver` | `generative_ui_agents/ai-shadcn-component-generator/apps/agent/src/bounded_memory_saver.py:30-55` |
| 런타임 (`server.ts`) | Hono 앱에 CopilotKit 단일 경로 엔드포인트를 얹고 에이전트로 프록시 | `generative_ui_agents/ai-shadcn-component-generator/apps/runtime/server.ts:11-43` |
| 화면 진입 (`App.tsx`) | `CopilotKit` 공급자, `output_schema`를 문맥으로 등록, 채팅 | `generative_ui_agents/ai-shadcn-component-generator/apps/ui/src/App.tsx:10-42` |
| UI 키트 (`chat-kit.tsx`) | 모델이 쓸 수 있는 부품 열여섯 개와 그 속성의 스키마 | `generative_ui_agents/ai-shadcn-component-generator/apps/ui/src/components/chat/chat-kit.tsx:20-185` |
| 메시지 렌더러 (`custom-message-renderer.tsx`) | 답 글을 부분 파싱해 `kit.render`로 그리고 Export 버튼을 붙임 | `generative_ui_agents/ai-shadcn-component-generator/apps/ui/src/components/custom-message-renderer.tsx:19-59` |
| 코드 내보내기 (`tree-to-jsx.ts`) | 부품 트리를 JSX 글로 바꿈 | `generative_ui_agents/ai-shadcn-component-generator/apps/ui/src/lib/tree-to-jsx.ts:1-99` |
| 직접 짠 부품 (`layout.tsx` 외) | `Row`·`Column`·`SimpleChart`·`SimpleSelect`·`CodeBlock`(shadcn 레지스트리 부품이 아니라 이 저장소의 것) | `generative_ui_agents/ai-shadcn-component-generator/apps/ui/src/components/ui/layout.tsx:1-82` |
| 원본 실행 설정 | 세 프로세스를 `concurrently`로 띄움, Render 배포 정의 | `generative_ui_agents/ai-shadcn-component-generator/package.json:5-13`, `render.yaml:1-80` |

## 단계별 진행

### Step 1. 환경 만들기와 가드 — 열쇠 없이는 가져오기에서 멈춥니다

**목적.** 원본을 건드리지 않도록 복사본 폴더를 만들고, 잠금 파일대로 설치되는지 확인하고, 바깥으로 나갈 수 있는 길을 막는 `guard.py`를 먼저 저장합니다.

**할 일.** `<저장소>`는 이 저장소를 받은 경로입니다. `apps/agent/`에는 `uv.lock`이 있어 `--locked`로 설치하면 잠금 파일과 `pyproject.toml`이 어긋날 때 멈춥니다. 앱 README는 이 단계를 적지 않고, 루트 `package.json`의 `dev:agent`가 `uv sync && uv run python main.py`를 부릅니다. 이 문서는 그 두 번째 줄을 쓰지 않습니다. `main.py:63`의 `host="0.0.0.0"`(모든 네트워크 인터페이스)과 `reload=True`가 그대로 적용되고, 그 서버에는 인증이 없어서 같은 네트워크의 누구나 열쇠로 모델을 부를 수 있기 때문입니다. 열쇠와 바깥 접속 없이 확인하는 것이 이 문서의 목적이므로 서버는 Step 2의 스크립트로 띄웁니다.

```bash
mkdir shadify-work
cd shadify-work
APP=<저장소>/generative_ui_agents/ai-shadcn-component-generator
cp -r $APP/apps/agent .
cd agent
uv sync --locked
cd ..
```

```text
Using CPython 3.13.3
Creating virtual environment at: .venv
Resolved 53 packages in 15ms
Installed 52 packages in 1.01s
```

```powershell
# 아래 PowerShell 줄은 실행해 보지 못했습니다.
mkdir shadify-work
cd shadify-work
$APP = "<저장소>\generative_ui_agents\ai-shadcn-component-generator"
Copy-Item -Recurse "$APP\apps\agent" .
cd agent
uv sync --locked
cd ..
```

(`apps/agent/.env`가 있으면 `cp -r`이 함께 복사합니다. 괜찮습니다. 아래 가드가 모델·검색 주소를 가짜로 먼저 정하고 프록시 변수를 비우며, `.env`는 이미 정해진 변수를 덮어쓰지 못합니다. 이 문서는 상위 폴더와 `agent/.env`에 진짜처럼 보이는 가짜 값(`OPENAI_PROXY`·`ALL_PROXY` 포함)을 두고 셸에도 프록시 변수를 건 독자로도 따라 해 보았습니다.) pip 대안은 시험하지 못했습니다. `python -m venv agent/.venv` 뒤 `agent/.venv/Scripts/python -m pip install "langchain==1.2.0" "langgraph==1.0.7" "ag-ui-langgraph==0.0.25" "copilotkit>=0.1.78" "tavily-python>=0.7.21" "langchain-openai>=1.1.0" "openai>=1.68.2,<2" "fastapi>=0.115.5,<1" "uvicorn>=0.29" "python-dotenv>=1.0,<2" "langsmith>=0.4.49" "pydantic>=2,<3"`처럼 `pyproject.toml`의 `dependencies`를 직접 설치하면 되겠지만 잠금 파일의 판은 쓰지 못합니다. 설치된 판을 봅니다. 이하 모든 파이썬 명령은 이 가상환경의 것으로 돌리므로 터미널마다 아래 두 줄을 먼저 합니다.

```bash
export PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
PY=agent/.venv/Scripts/python.exe     # macOS·Linux는 agent/.venv/bin/python
```

```powershell
$env:PYTHONIOENCODING = "utf-8"; $env:PYTHONUNBUFFERED = "1"; $env:PYTHONDONTWRITEBYTECODE = "1"
$PY = "agent\.venv\Scripts\python.exe"
```

```bash
$PY -c "from importlib.metadata import version as v; print(' | '.join(f'{n} {v(n)}' for n in ['copilotkit','ag-ui-langgraph','langchain','langgraph','langchain-openai','openai','tavily-python','fastapi','uvicorn']))"
```

```text
copilotkit 0.1.78 | ag-ui-langgraph 0.0.25 | langchain 1.2.0 | langgraph 1.0.7 | langchain-openai 1.1.9 | openai 1.109.1 | tavily-python 0.7.21 | fastapi 0.115.12 | uvicorn 0.40.0
```

`pyproject.toml`이 고정한 것은 `langchain==1.2.0`, `langgraph==1.0.7`(`bounded_memory_saver.py`가 `MemorySaver.storage`라는 내부 속성에 기대서 고정한다고 주석에 있음), `ag-ui-langgraph==0.0.25`뿐이고 `copilotkit`은 `>=0.1.78`입니다. 나머지는 잠금 파일이 붙듭니다. 같은 `uv sync`를 `--locked` 없이 하면 잠금 파일을 고쳐 쓸 수 있으니, 판이 다르게 나오면 이 문서의 관찰도 달라질 수 있습니다.

이제 가드입니다. 가드는 세 가지를 합니다. 환경변수를 **스크립트 안에서 직접** 덮어써서(모델 주소는 `http://127.0.0.1:<가짜 포트>/v1`, 열쇠는 가짜 값, LangSmith 트레이싱은 끔) 셸이나 `.env`에 진짜 열쇠가 있어도 무시하고, Tavily 클라이언트의 주소를 가짜 서버로 바꾸고, 소켓 연결·이름 조회·asyncio 연결 함수를 루프백 밖으로는 못 나가게 막습니다. 마지막 막기는 이차 방어선입니다. 프록시도 막습니다. 셸의 `HTTP(S)_PROXY`·`ALL_PROXY`와 `.env`에서만 올 수 있는 `OPENAI_PROXY`는 빈 값으로 덮고(`openai`·`httpx`가 이 변수들을 따라 가짜 열쇠가 실린 요청을 프록시로 보냅니다. `langchain-openai` 1.1.9의 `OPENAI_PROXY`는 명시 인자라 `NO_PROXY`로도 막히지 않습니다), `NO_PROXY`·`no_proxy`에 루프백을 겁니다. `check_env`는 이 변수들과 `LANGSMITH_ENDPOINT`까지 확인하고, `main.py`를 가져온 뒤에 한 번 더 부릅니다. `drive.py`의 `urllib`은 `ProxyHandler({})`로, 문서의 `curl`은 `--noproxy '*'`로 프록시를 거치지 않습니다. 옛 변수 `OPENAI_API_BASE`는 지우지 않고 가짜 주소로 채워 둡니다. 지우면 `main.py`가 부르는 `load_dotenv()`가 `.env`에서 다시 채우는데, `langchain-openai`는 이 변수를 `base_url` 인자로 넘겨 `OPENAI_BASE_URL`보다 우선하기 때문입니다.

```bash
cat > guard.py <<'EOF'
"""루프백 가드. 이 파일을 가장 먼저 불러온다.

1) 환경변수를 스크립트 안에서 직접 덮어쓴다(앞붙임 한 줄에 기대지 않는다).
2) Tavily 클라이언트의 주소를 가짜 서버로 바꾸고, 프록시 변수를 비운다.
3) 소켓 연결과 이름 조회를 루프백 밖으로는 못 나가게 막고, 막은 횟수를 센다.
"""
import ipaddress
import os
import socket
import sys
from urllib.parse import urlparse

LOOPBACK_NAMES = {"127.0.0.1", "localhost", "::1"}
PROXY_VARS = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy", "OPENAI_PROXY")
FAKE_PORT = None


def is_loopback_host(host: str) -> bool:
    if host in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def point_at_fake(port: int) -> str:
    """OpenAI·Tavily 클라이언트가 가짜 서버만 보도록 환경을 직접 정한다."""
    global FAKE_PORT
    FAKE_PORT = port
    base = f"http://127.0.0.1:{port}/v1"
    os.environ["OPENAI_BASE_URL"] = base
    os.environ["OPENAI_API_KEY"] = "sk-fake-shadify"
    os.environ["TAVILY_API_KEY"] = "tvly-fake-shadify"
    # 옛 이름 OPENAI_API_BASE 는 langchain-openai 가 base_url 인자로 넘겨 OPENAI_BASE_URL 을 이긴다.
    # 지우기만 하면 main.py 의 load_dotenv()가 .env 에서 다시 채우므로, 지우지 않고 가짜 주소로 채워 둔다.
    os.environ["OPENAI_API_BASE"] = base
    for name in ("OPENAI_ORG_ID", "OPENAI_ORGANIZATION", "TAVILY_HTTP_PROXY", "TAVILY_HTTPS_PROXY"):
        os.environ[name] = ""
    # 트레이싱과 텔레메트리 끄기
    for name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2", "LANGSMITH_TRACING_V2", "LANGCHAIN_TRACING"):
        os.environ[name] = "false"
    os.environ["LANGSMITH_API_KEY"] = ""
    os.environ["LANGCHAIN_API_KEY"] = ""
    os.environ["LANGGRAPH_CLI_NO_ANALYTICS"] = "1"
    os.environ["COPILOTKIT_TELEMETRY_DISABLED"] = "true"
    os.environ["DO_NOT_TRACK"] = "1"
    os.environ["SCARF_ANALYTICS"] = "false"
    # LangSmith 주소도 가짜로 채운다(추적이 꺼져 있어도 .env 가 바꿔 둔 주소가 남지 않게).
    os.environ["LANGSMITH_ENDPOINT"] = os.environ["LANGCHAIN_ENDPOINT"] = f"http://127.0.0.1:{port}"
    # 프록시: 독자 셸의 HTTP(S)_PROXY·ALL_PROXY 와 .env 의 OPENAI_PROXY 는 가짜 열쇠와 질문을 프록시로 실어 보낸다.
    # 지우기만 하면 load_dotenv()가 다시 채우므로 빈 값으로 덮고, 루프백은 프록시를 거치지 않게 NO_PROXY 를 건다.
    for name in PROXY_VARS:
        os.environ[name] = ""
    os.environ["NO_PROXY"] = os.environ["no_proxy"] = "127.0.0.1,localhost,::1"
    # Tavily: 생성자의 api_base_url 만이 주소를 바꾼다. 클래스를 감싸 가짜 서버를 가리키게 한다.
    import tavily.tavily as tv

    real_init = tv.TavilyClient.__init__

    def init(self, *args, **kwargs):
        kwargs["api_base_url"] = f"http://127.0.0.1:{port}"
        real_init(self, *args, **kwargs)

    tv.TavilyClient.__init__ = init
    return base


def check_env() -> None:
    for name in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
        host = urlparse(os.environ.get(name, "")).hostname or ""
        if not is_loopback_host(host):
            sys.exit(f"가드: {name} 호스트가 루프백이 아닙니다 ({host or '비어 있음'}). 중단합니다.")
    if not os.environ.get("OPENAI_API_KEY", "").startswith("sk-fake"):
        sys.exit("가드: OPENAI_API_KEY가 가짜 값이 아닙니다. 중단합니다.")
    if not os.environ.get("TAVILY_API_KEY", "").startswith("tvly-fake"):
        sys.exit("가드: TAVILY_API_KEY가 가짜 값이 아닙니다. 중단합니다.")
    for name in ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2"):
        if os.environ.get(name, "").lower() in ("1", "true", "yes"):
            sys.exit(f"가드: {name}이 켜져 있습니다. 중단합니다.")
    for name in PROXY_VARS:
        if os.environ.get(name):
            sys.exit(f"가드: 프록시 변수 {name}이 비어 있지 않습니다. 중단합니다.")
    for name in ("NO_PROXY", "no_proxy"):
        if "127.0.0.1" not in os.environ.get(name, "").split(","):
            sys.exit(f"가드: {name}에 127.0.0.1이 없습니다. 중단합니다.")
    for name in ("LANGSMITH_ENDPOINT", "LANGCHAIN_ENDPOINT"):
        if not is_loopback_host(urlparse(os.environ.get(name, "")).hostname or ""):
            sys.exit(f"가드: {name}이 루프백이 아닙니다. 중단합니다.")
    import tavily.tavily as tv

    probe = tv.TavilyClient()
    tavily_host = urlparse(probe.base_url).hostname or ""
    if not is_loopback_host(tavily_host):
        sys.exit(f"가드: Tavily 주소 호스트가 루프백이 아닙니다 ({tavily_host}). 중단합니다.")


BLOCKED = []


def _note(kind: str, host: str) -> None:
    """막은 시도를 메모리와 blocked.log 에 남긴다(서버는 끝날 때 보고하지 못할 수 있다)."""
    BLOCKED.append((kind, host))
    with open("blocked.log", "a", encoding="utf-8", newline="\n") as f:
        f.write(f"{kind} {host}\n")


_real_connect = socket.socket.connect
_real_getaddrinfo = socket.getaddrinfo


def _host_of(address):
    return address[0] if isinstance(address, tuple) else str(address)


def _guarded_connect(self, address):
    host = _host_of(address)
    if self.family in (socket.AF_INET, socket.AF_INET6) and not is_loopback_host(host):
        _note("connect", host)
        raise ConnectionRefusedError(f"가드: 루프백 밖 연결을 막았습니다 ({host})")
    return _real_connect(self, address)


def _guarded_getaddrinfo(host, *args, **kwargs):
    if isinstance(host, (str, bytes)):
        name = host.decode() if isinstance(host, bytes) else host
        if name and not is_loopback_host(name):
            _note("dns", name)
            raise socket.gaierror(f"가드: 루프백 밖 이름 조회를 막았습니다 ({name})")
    return _real_getaddrinfo(host, *args, **kwargs)


def install_socket_guard() -> None:
    socket.socket.connect = _guarded_connect
    socket.getaddrinfo = _guarded_getaddrinfo
    # asyncio는 Windows에서 socket.connect를 거치지 않을 수 있어 연결 함수도 막는다.
    import asyncio.base_events as be

    real_create_connection = be.BaseEventLoop.create_connection

    async def guarded_create_connection(self, protocol_factory, host=None, port=None, **kw):
        if isinstance(host, str) and host and not is_loopback_host(host):
            _note("asyncio", host)
            raise ConnectionRefusedError(f"가드: 루프백 밖 연결을 막았습니다 ({host})")
        return await real_create_connection(self, protocol_factory, host, port, **kw)

    be.BaseEventLoop.create_connection = guarded_create_connection


def report() -> None:
    print(f"가드: 루프백 밖으로 나가려던 시도 {len(BLOCKED)}건 {BLOCKED[:5]}")
EOF
```

열쇠가 없으면 어디서 멈추는지도 봅니다. 아래 스크립트는 열쇠 변수를 이 프로세스에서 지우고, `main.py`의 `load_dotenv()`가 상위 폴더 `.env`에서 되살리지 못하게 `PYTHON_DOTENV_DISABLED`를 켠 채 `main.py`를 가져옵니다. 독자 셸에 진짜 열쇠가 있어도 지워진 채로 돕니다.

```bash
cat > nokey.py <<'EOF'
"""열쇠가 없을 때 main.py 를 가져오면 어디서 멈추는지 본다. 어떤 요청도 보내지 않는다."""
import os
import sys

import guard

guard.install_socket_guard()
os.environ["PYTHON_DOTENV_DISABLED"] = "1"  # main.py 의 load_dotenv()가 상위 폴더 .env 에서 열쇠를 다시 채우지 못하게 한다
os.environ.pop("OPENAI_API_KEY", None)      # 독자 셸에 진짜 열쇠가 있어도 이 프로세스에서는 지운다
os.environ.pop("OPENAI_BASE_URL", None)
AGENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent")
sys.path.insert(0, AGENT)

try:
    import main  # noqa: F401
except Exception as e:  # noqa: BLE001
    print(f"{type(e).__name__}: {str(e)[:70]}...")
    frames = []
    t = e.__traceback__
    while t:
        frames.append((os.path.dirname(os.path.abspath(t.tb_frame.f_code.co_filename)), t.tb_lineno))
        t = t.tb_next
    print("멈춘 곳(agent/main.py 줄):", [l for d, l in frames if d == AGENT])
guard.report()
EOF
```

```bash
$PY nokey.py
```

```text
OpenAIError: The api_key client option must be set either by passing api_key to the...
멈춘 곳(agent/main.py 줄): [30]
가드: 루프백 밖으로 나가려던 시도 0건 []
```

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** `main.py:30`이 `create_agent(...)`를 부르는 줄이고, `model="openai:gpt-5.5"`가 가져오기만으로 클라이언트를 만들기 때문에 서버도 열쇠 없이는 뜨지 못합니다(앞 날의 같은 모양은 [Day 143 Step 1](../day143-genui-generative-ui-starter-project/README.md)).

### Step 2. 가짜 서버와 에이전트 서버 — 원본 main.py는 그대로

**목적.** 모델과 검색 자리에 가짜 서버를 세우고, 원본 `main.py`를 `127.0.0.1`에만 열어 띄웁니다.

**할 일.** `main.py:58-66`은 이렇습니다.

```python
def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8123"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
```

`python main.py`로 띄우면 모든 인터페이스에 열리고 파일이 바뀔 때마다 서버가 다시 뜹니다. 이 문서는 `main.py`를 고치지 않고 `run_agent.py`가 `main`을 가져와(`load_dotenv()`와 패치 적용이 여기서 돕니다) 가드를 한 번 더 확인한 뒤 `uvicorn.run(main.app, host="127.0.0.1")`을 부릅니다. `.env`가 값을 바꿨을 수도 있어서 가져온 뒤에 다시 확인하는 것입니다. `main`을 가져오는 순간 `apply_patches()`(`main.py:21`)도 돌아서 `ag-ui-langgraph`의 메서드 셋이 바뀝니다(무엇을 막는지는 Step 7). 묶음 안의 이어짐은 이 그림과 같습니다. 패치가 엔드포인트의 `LangGraphAgent` 메서드를 바꾸고(`patches.py:39-43`), 엔드포인트가 그래프를 부르고(`main.py:48-56`), 그래프가 체크포인터에 상태를 둡니다(`main.py:36`).

![에이전트 묶음 안 (1)](diagrams/extra-agent.svg)

```bash
cat > run_agent.py <<'EOF'
"""원본 main.py 를 루프백에만 연다. 원본의 uvicorn.run(host="0.0.0.0", reload=True)는 실행되지 않는다.

사용법: python run_agent.py <가짜 서버 포트> <에이전트 포트>
"""
import os
import sys

import guard

fake_port = int(sys.argv[1])
agent_port = int(sys.argv[2])
guard.point_at_fake(fake_port)
guard.check_env()
guard.install_socket_guard()

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "agent"))
import main  # noqa: E402  (main.py 의 load_dotenv()가 여기서 돈다)

guard.check_env()          # .env 가 값을 바꿨을 수도 있으니 서버를 열기 전에 한 번 더 확인한다

import uvicorn  # noqa: E402

uvicorn.run(main.app, host="127.0.0.1", port=agent_port, log_level="warning")
guard.report()
EOF
```

가짜 서버 하나가 두 가지를 맡습니다. OpenAI `/v1/chat/completions`(스트리밍과 비스트리밍)와 Tavily `/search`·`/extract`·`/crawl`입니다. 모델 자리의 답은 요청에 `response_format`이 있으면 부품 트리 JSON, 없으면 짧은 글이고, 사용자의 마지막 말에서 고른 낱말("pizza", "crawl", "bad json", "dashboard")로 장면을 바꿉니다. 받은 요청은 모두 기록 파일에 한 줄씩 남습니다. 이 대본은 제가 쓴 것이며 실제 모델의 판단과 다릅니다.

```bash
cat > fake_servers.py <<'EOF'
"""localhost 가짜 서버 하나가 OpenAI(chat.completions)와 Tavily(/search·/extract·/crawl)를 함께 맡는다.
답은 모두 이 파일에 적힌 대본이다. 받은 요청은 기록 파일에 한 줄씩 남는다.

사용법: python fake_servers.py <포트> <기록파일>
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1])
LOG = sys.argv[2]


def md(text):
    return {"Markdown": {"props": {"children": text}}}


def chart(kind, labels, values, label, color):
    return {"chart": {"props": {"type": kind, "labels": labels, "values": values, "label": label, "color": color}}}


def row(*kids):
    return {"row": {"props": {"gap": "4", "align": "stretch", "justify": "start"}, "children": list(kids)}}


def card(*kids):
    return {"card": {"props": {}, "children": list(kids)}}


MENU = {"menubar": {"props": {}, "children": [{"menubar_menu": {"props": {}, "children": [
    {"menubar_trigger": {"props": {}, "children": "File"}},
    {"menubar_content": {"props": {}, "children": [{"menubar_item": {"props": {}, "children": "New"}}]}}]}}]}}
DASHBOARD = {"ui": [card(
    md("## Sales dashboard\nRevenue and signups by quarter."),
    MENU,
    row(chart("bar", ["Q1", "Q2", "Q3", "Q4"], [120, 150, 170, 210], "Revenue ($K)", "var(--sunshine-yellow)"),
        chart("line", ["Q1", "Q2", "Q3", "Q4"], [30, 42, 51, 66], "Signups", "#64b0b5")))]}
FOUR_CHARTS = {"ui": [card(row(*[chart("bar", ["a", "b"], [1, 2], f"s{i}", "#EB6C36") for i in range(4)]))]}


def write_log(entry):
    with open(LOG, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def text_of(m):
    c = m.get("content")
    return c if isinstance(c, str) else json.dumps(c)


def decide(body):
    """('text', 문장) 또는 ('tool', 이름, 인자) 를 돌려준다. 키 words 는 사용자 마지막 말에서 찾는다."""
    messages = body["messages"]
    wants_ui = bool(body.get("response_format"))            # 에이전트가 response_format 을 붙였는가
    user = next((text_of(m) for m in reversed(messages) if m["role"] == "user"), "").lower()
    last = messages[-1]

    def ui(tree):
        return ("text", json.dumps(tree, ensure_ascii=False)) if wants_ui else ("text", "plain: " + user[:40])

    if last["role"] == "tool":
        try:
            results = json.loads(last["content"]).get("results", [])
        except (ValueError, AttributeError):
            results = []
        titles = [r.get("title", "?") for r in results[:2]]
        if "crawl" in user:
            return ui({"ui": [md("Crawl finished: " + ", ".join(titles or ["(no pages)"]))]})
        return ui({"ui": [card(md("## Pizza in San Francisco\n" + "\n".join(f"- {t}" for t in titles)),
                               chart("bar", ["Tony's", "Golden Boy"], [4.6, 4.4], "Rating", "#EB6C36"))]})
    if "pizza" in user:
        return ("tool", "search_internet", {"query": "best pizza in San Francisco"})
    if "crawl" in user:
        return ("tool", "crawl_site", {"website": "https://example.com", "instructions": "find the pricing pages"})
    if "four charts" in user:
        return ui(FOUR_CHARTS)
    if "bad json" in user:
        return ("text", "this is not json")
    if "dashboard" in user:
        return ui(DASHBOARD)
    return ui({"ui": [md("Hello from the fake model.")]})


def chunk(cid, delta, finish=None):
    return {"id": cid, "object": "chat.completion.chunk", "created": int(time.time()), "model": "gpt-5.5",
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply_json(self, obj):
        data = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        write_log({"path": self.path, "auth": self.headers.get("authorization", "")[:14], "body": body})
        if self.path == "/search":                           # Tavily
            return self.reply_json({"query": body.get("query"), "results": [
                {"title": "Tony's Pizza Napoletana", "url": "https://example.test/tonys", "content": "Coal-fired and wood-fired pies.", "score": 0.9},
                {"title": "Golden Boy Pizza", "url": "https://example.test/golden", "content": "Square slices in North Beach.", "score": 0.8}]})
        if self.path in ("/extract", "/crawl"):
            return self.reply_json({"base_url": body.get("url"), "results": [{"url": "https://example.test/a", "raw_content": "page text"}]})
        if not self.path.endswith("/chat/completions"):
            self.send_response(404)
            self.end_headers()
            return
        action = decide(body)
        cid = "chatcmpl-fake-%d" % int(time.time() * 1000)
        if action[0] == "text":
            message, finish = {"role": "assistant", "content": action[1]}, "stop"
        else:
            message = {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_" + action[1], "type": "function", "function": {"name": action[1], "arguments": json.dumps(action[2])}}]}
            finish = "tool_calls"
        if not body.get("stream"):
            return self.reply_json({"id": cid, "object": "chat.completion", "created": int(time.time()), "model": "gpt-5.5",
                                    "choices": [{"index": 0, "message": message, "finish_reason": finish}],
                                    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}})
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.end_headers()
        events = [chunk(cid, {"role": "assistant", "content": ""})]
        if action[0] == "text":
            text = action[1]
            for i in range(0, len(text), 24):                 # 24자씩 흘려 보낸다(화면이 반쯤 온 JSON 을 읽는 모양을 보려고)
                events.append(chunk(cid, {"content": text[i:i + 24]}))
        else:
            args = message["tool_calls"][0]["function"]["arguments"]
            events.append(chunk(cid, {"tool_calls": [{"index": 0, "id": message["tool_calls"][0]["id"], "type": "function",
                                                       "function": {"name": action[1], "arguments": ""}}]}))
            for i in range(0, len(args), 40):
                events.append(chunk(cid, {"tool_calls": [{"index": 0, "function": {"arguments": args[i:i + 40]}}]}))
        events.append(chunk(cid, {}, finish))
        for e in events:
            self.wfile.write(b"data: " + json.dumps(e).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")


class Server(ThreadingHTTPServer):
    allow_reuse_address = False


if __name__ == "__main__":
    Server(("127.0.0.1", PORT), Handler).serve_forever()
EOF
```

포트는 49152~65535 사이에서 골라 쓰세요. 예시로 가짜 서버 `57131`, 에이전트 서버 `57132`를 씁니다. 터미널 A에서 가짜 서버를, 터미널 B에서 에이전트 서버를 띄웁니다. 둘 다 위의 환경변수 두 줄을 먼저 합니다.

```bash
# 터미널 A
$PY fake_servers.py 57131 fake.jsonl
```

```bash
# 터미널 B (셸에 진짜 열쇠가 있는 독자를 흉내 내려고 변수 둘을 앞에 붙임. 진짜 열쇠가 있는 셸이라면 붙이지 않아도 같음)
OPENAI_API_KEY=sk-pretend-real-key LANGSMITH_TRACING=true $PY run_agent.py 57131 57132 2>&1 | tee agent.out
```

```powershell
# 터미널 A (실행해 보지 못했습니다)
& $PY fake_servers.py 57131 fake.jsonl
# 터미널 B (실행해 보지 못했습니다. 진짜 열쇠가 있는 셸을 흉내 내려고 변수 둘을 앞에 둠)
$env:OPENAI_API_KEY = "sk-pretend-real-key"; $env:LANGSMITH_TRACING = "true"
& $PY run_agent.py 57131 57132
```

가드가 정말 막는지 먼저 봅니다. 터미널 C에서 `guard_selftest.py`를 돌립니다. 문서 예약 주소 `192.0.2.1`과 `example.com`으로 연결을 시도하지만 연결 함수 앞에서 거절되어 패킷은 나가지 않습니다.

```bash
cat > guard_selftest.py <<'EOF'
"""가드가 루프백 밖 연결을 막는지 확인한다. 실제로는 패킷이 한 개도 나가지 않는다(연결 함수 앞에서 거절)."""
import asyncio
import socket

import guard

guard.install_socket_guard()
for host in ("192.0.2.1", "example.com"):
    try:
        socket.create_connection((host, 80), timeout=2)
    except Exception as e:
        print("동기 ", host, "->", type(e).__name__)


async def main():
    for host in ("192.0.2.1", "example.com"):
        try:
            await asyncio.open_connection(host, 80)
        except Exception as e:
            print("비동기", host, "->", type(e).__name__)


asyncio.run(main())
guard.report()
EOF
```

```bash
$PY guard_selftest.py
rm blocked.log
```

```text
동기  192.0.2.1 -> gaierror
동기  example.com -> gaierror
비동기 192.0.2.1 -> ConnectionRefusedError
비동기 example.com -> ConnectionRefusedError
가드: 루프백 밖으로 나가려던 시도 4건 [('dns', '192.0.2.1'), ('dns', 'example.com'), ('asyncio', '192.0.2.1'), ('asyncio', 'example.com')]
```

서버가 루프백에만 열렸는지, 헬스 체크가 어느 주소인지 봅니다. `main.py:48-56`의 `add_langgraph_fastapi_endpoint(..., path="/")`는 POST를 `/`에 달고, 헬스 체크를 `f"{path}/health"`로 만들어서 `//health`가 됩니다.

```bash
netstat -ano | grep -E ":5713[12] .*LISTENING"
curl --noproxy '*' -s http://127.0.0.1:57132//health
echo
curl --noproxy '*' -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:57132/health
```

```text
  TCP    127.0.0.1:57131        0.0.0.0:0              LISTENING       18708
  TCP    127.0.0.1:57132        0.0.0.0:0              LISTENING       46508
{"status":"ok","agent":{"name":"sample_agent"}}
404
```

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** `0.0.0.0`이 아니라 `127.0.0.1`이어야 합니다. 이 문서는 "진짜 키가 있는 독자"로도 따라 해 보았습니다. 터미널 B를 위처럼 띄우고, 셸에 `HTTP(S)_PROXY`·`ALL_PROXY`를 걸고, 상위 폴더와 `agent/.env`에 `OPENAI_API_KEY`·`OPENAI_API_BASE=https://api.openai.com/v1`·`OPENAI_PROXY`·`ALL_PROXY`·`TAVILY_API_KEY`·`LANGSMITH_TRACING=true`를 진짜처럼 보이는 가짜 값으로 둔 채 이어지는 Step의 요청을 모두 보낸 뒤, 가짜 서버 기록(`fake.jsonl`)의 `Authorization` 앞머리는 모델 요청에서 `Bearer sk-fake`, Tavily 요청에서 `Bearer tvly-fa`뿐이었고 `.env`와 셸의 값은 한 번도 나타나지 않았습니다. 모든 요청이 프록시를 거치지 않고 가짜 서버에 직접 닿았고(가드가 프록시 변수를 비웠기 때문입니다), `blocked.log`(가드가 막은 시도)는 생기지 않았습니다.

### Step 3. 화면이 보내는 것 — 부품 열여섯 개가 스키마가 됩니다

**목적.** 화면이 에이전트에 무엇을 실어 보내는지, 특히 `output_schema`가 어떻게 만들어지는지 소스와 옮겨 쓴 스크립트로 봅니다.

**할 일.** `generative_ui_agents/ai-shadcn-component-generator/apps/ui/src/App.tsx:25-31`의 `Page`가 핵심입니다.

```tsx
export function Page() {
  const chatKit = useChatKit();
  useAgentContext({ description: "output_schema", value: s.toJsonSchema(chatKit.schema) });
  useInitialSuggestions();

  return <Chat />;
}
```

`useChatKit()`(`chat-kit.tsx:104-184`)은 hashbrown의 `useUiKit`에 부품 목록을 줍니다. 목록은 `Markdown`(`exposeMarkdown()`), `card`, `calendar`, `row`, `column`, `chart`, `menubar`와 그 부품 넷(`menubar_menu`·`menubar_trigger`·`menubar_content`·`menubar_item`), `code_block`, `input`, `button`, `select`, `label`로 열여섯 개입니다. 각 부품은 `exposeComponent(컴포넌트, {name, description, props, children})`로 이름·설명·속성 스키마·자식 규칙(`"any"`, `"text"`, 지정한 부품 목록, 없음)을 가집니다. `createUiKit`(`@hashbrownai/core`)은 부품마다 `{이름: {props, children?}}` 모양의 객체 하나를 만들고 전체를 `anyOf`로 묶어 `{ui: [...]}`을 루트로 씁니다. 부품 안의 부품(`card`의 `children: "any"` 등)은 같은 `anyOf`를 다시 가리키므로 `toJsonSchema`가 두 번 나온 조각을 `$defs`로 빼고 `$ref`로 잇습니다. `useAgentContext`는 값이 문자열이 아니면 `JSON.stringify`해서 `{description, value}` 항목으로 등록합니다(`@copilotkitnext/react`의 `use-agent-context`).

이 변환을 파이썬으로 옮겨 쓴 것이 `ui_schema.py`입니다. 부품 열여섯 개의 이름·설명·속성은 `chat-kit.tsx`에서 글자 그대로 가져왔고, `@hashbrownai/core` 0.5.0-beta.4의 `createUiKit`·`createComponentSchema`·`toJsonSchema`(`index.esm.js`)가 하는 일을 따랐습니다. 모든 객체가 `additionalProperties: false`와 모든 키를 `required`로(순서는 스트리밍 속성을 뒤로 정렬한 뒤의 순서), 두 번 이상 나온 조각은 설명을 camelCase로 바꾼 이름의 `$defs`로, 루트 설명은 예제가 없을 때 `createUiKit`이 쓰는 문장(`Return a JSON object with a single key "ui" ...`)이고, `children: "text"`의 문자열은 스트리밍 판입니다. 손으로 옮겼으므로 실제 출력과 글자까지 같다고는 하지 못합니다.

```bash
cat > ui_schema.py <<'EOF'
"""화면이 에이전트에 보내는 output_schema 를 파이썬으로 옮겨 쓴 것(손으로 옮김, 브라우저 코드는 실행하지 않았다).

원본: apps/ui/src/components/chat/chat-kit.tsx 의 컴포넌트 열여섯 개(Markdown 포함)를
@hashbrownai/core 0.5.0-beta.4 의 createComponentSchema·toJsonSchema 가 하는 대로 draft-07 JSON Schema 로 만든다.
사용법: python ui_schema.py            (요약을 찍는다)
        python ui_schema.py --json     (스키마 JSON 한 줄을 찍는다)
"""
import json
import re
import sys


class T:                       # hashbrown 의 HashbrownType 한 가지. kind 로 구분한다.
    def __init__(self, kind, desc, streaming=False, **kw):
        self.kind, self.desc, self.streaming = kind, desc, streaming
        self.__dict__.update(kw)


def string(desc, streaming=False):         return T("string", desc, streaming)
def number(desc):                          return T("number", desc)
def enum(desc, entries):                   return T("enum", desc, entries=entries)
def array(desc, element, streaming=False): return T("array", desc, streaming, element=element)
def obj(desc, shape, streaming=False):     return T("object", desc, streaming, shape=shape)
def any_of(options):                       return T("anyOf", "any-of", options=options)
def node(inner):                           return T("node", inner.desc, True, inner=inner)


MARKDOWN_DESC = ("Render markdown content for the user.\n\nWrite all markdown into the `children` prop.\n"
                 "Use standard markdown for headings, lists, links, tables, and code blocks.")
TW_GAP = "Tailwind gap size, e.g. '2', '4', '6'"
TW_ALIGN = "Tailwind items-* alignment: 'start', 'center', 'end', 'stretch'"
TW_JUSTIFY = "Tailwind justify-* alignment: 'start', 'center', 'end', 'between', 'around'"


class C:                       # exposeComponent(...) 한 개. children: None | "text" | "any" | [C, ...]
    def __init__(self, name, desc, props=None, children=None):
        self.name, self.desc, self.props, self.children = name, desc, props or {}, children


item = C("menubar_item", "A single clickable item inside a menu dropdown.", children="text")
content = C("menubar_content", "The dropdown content panel of a menu.", children=[item])
trigger = C("menubar_trigger", "The clickable label that opens a menu dropdown.", children="text")
menu = C("menubar_menu", "A single menu within the menubar, containing a trigger and dropdown content.", children=[trigger, content])
menubar = C("menubar", "A horizontal menu bar with dropdown menus. Contains one or more menus.", children=[menu])
row = C("row", "Horizontal flex row for laying out children side by side.",
        {"gap": string(TW_GAP), "align": string(TW_ALIGN), "justify": string(TW_JUSTIFY)}, "any")
column = C("column", "Vertical flex column for stacking children.",
           {"gap": string(TW_GAP), "align": string(TW_ALIGN), "justify": string(TW_JUSTIFY)}, "any")
chart = C("chart", "A chart that visualizes data. Supports bar, line, and area chart types. Provide parallel arrays of labels (x-axis) and values (y-axis).",
          {"type": enum("Chart type", ["bar", "line", "area"]),
           "labels": array("Category labels for the x-axis", string("A label")),
           "values": array("Numeric values for the y-axis, same length as labels", number("A value")),
           "label": string("Name for the data series, shown in tooltip"),
           "color": string("CSS color for the chart, e.g. 'var(--sunshine-yellow)' or '#ff0000'")})
markdown = C("Markdown", MARKDOWN_DESC, {"children": node(string("Markdown content to render", True))})  # 이름이 대문자 M 이다
COMPONENTS = [
    markdown,
    C("card", "Card to wrap generative UI content. For only Markdown, don't wrap it in this.", children="any"),
    C("calendar", "Calendar to display events."),
    row, column, chart, menubar, menu, trigger, content, item,
    C("code_block", "A syntax-highlighted code block for displaying code snippets.",
      {"code": string("The code to display", True),
       "language": string("Programming language for syntax highlighting, e.g. 'tsx', 'python', 'json'")}),
    C("input", "A text input field for forms.",
      {"placeholder": string("Placeholder text shown when empty"),
       "type": string("Input type: 'text', 'email', 'password', 'number', 'url'")}),
    C("button", "A clickable button. Use variant to control style.",
      {"variant": enum("Button style", ["default", "destructive", "outline", "secondary", "ghost", "link"]),
       "size": enum("Button size", ["default", "sm", "lg", "icon"])}, "text"),
    C("select", "A dropdown select with a list of string options.",
      {"placeholder": string("Placeholder text shown when nothing is selected"),
       "options": array("The selectable options", string("An option"))}),
    C("label", "A text label for form fields.", children="text"),
]


def build_ui_type(components):
    """createUiKit + createComponentSchema: 컴포넌트마다 { 이름: { props, children? } } 객체 하나, 전체를 anyOf 로."""
    flat, seen = [], set()

    def add(c):
        if c.name not in seen:
            seen.add(c.name)
            flat.append(c)
        if isinstance(c.children, list):
            for ch in c.children:
                add(ch)

    for c in components:
        add(c)
    cache = {}
    elements = any_of([])

    def make(c):
        if id(c) in cache:
            return cache[id(c)]
        shape = {"props": node(obj("Component Props", c.props))}
        if c.children == "any":
            shape["children"] = array("Child Elements", elements, True)
        elif c.children == "text":
            shape["children"] = string("Content", True)       # createComponentSchema 의 string 은 스트리밍 판이다
        elif isinstance(c.children, list):
            shape["children"] = array("Child Elements", any_of([make(ch) for ch in c.children]), True)
        out = obj(c.desc, {c.name: obj(f"{c.name} node", shape, True)}, True)
        cache[id(c)] = out
        return out

    elements.options = [make(c) for c in flat]
    # 예제가 없으면 createUiKit 은 루트 설명을 이 문장으로 둔다(index.esm.js 7922-7923)
    root_desc = 'Return a JSON object with a single key "ui" that matches the schema below. Use only these components.'
    return obj(root_desc, {"ui": array("List of elements", elements, True)})


def camel(desc):
    words = [w.lower() for w in re.sub(r"[^a-zA-Z0-9]+", " ", desc).split()]
    if not words:
        return ""
    core = words[0] + "".join(w[0].upper() + w[1:] for w in words[1:])
    return "_" + core if core[0].isdigit() else core


def basic(n):
    if n.kind == "string":
        return {"type": "string", "description": n.desc}
    if n.kind == "number":
        return {"type": "number", "description": n.desc}
    if n.kind == "enum":
        return {"type": "string", "enum": n.entries, "description": n.desc}
    if n.kind == "array":
        return {"type": "array", "items": [], "description": n.desc}
    if n.kind == "object":
        return {"type": "object", "properties": {}, "required": list(n.shape), "additionalProperties": False, "description": n.desc}
    return {"anyOf": []}


def to_json_schema(root):
    """@hashbrownai/core 의 toJsonSchema: 두 번 이상 나온 조각은 $defs 로 빼고 $ref 로 가리킨다."""
    seen, repeats = set(), []

    def visit(n):
        if id(n) in seen:
            if n not in repeats:
                repeats.append(n)
            return
        seen.add(id(n))
        if n.kind == "node":
            visit(n.inner)
        elif n.kind == "object":
            for child in n.shape.values():
                visit(child)
        elif n.kind == "array":
            visit(n.element)
        elif n.kind == "anyOf":
            for o in n.options:
                visit(o)

    visit(root)
    repeats = [r for r in repeats if r is not root]
    names, used, anon = {}, set(), 1
    for n in repeats:
        if n.desc:
            desc = n.desc
        else:
            desc, anon = f"def{anon}", anon + 1
        name = camel(desc) or f"def{anon}"
        if name in used:
            i = 1
            while f"{name}{i}" in used:
                i += 1
            name = f"{name}{i}"
        used.add(name)
        names[id(n)] = name

    def pr(n, in_def=None, path=()):
        if id(n) in names and n is not in_def:
            return {"$ref": "#/$defs/" + names[id(n)]}
        if id(n) in path:
            return {"$ref": "#/$defs/" + names[id(n)]} if id(n) in names else {"$ref": "#"}
        path = path + (id(n),)
        if n.kind == "node":
            return pr(n.inner, in_def, path)
        out = basic(n)
        if n.kind == "object":
            entries = sorted(n.shape.items(), key=lambda kv: kv[1].streaming)   # 스트리밍 속성은 뒤로(안정 정렬)
            out["properties"] = {k: pr(v, in_def, path) for k, v in entries}
            out["required"] = list(out["properties"])                           # printNode 가 정렬 뒤의 키로 다시 쓴다
        elif n.kind == "array":
            out["items"] = pr(n.element, in_def, path)
        elif n.kind == "anyOf":
            out["anyOf"] = [pr(o, in_def, path) for o in n.options]
        return out

    defs = {names[id(n)]: pr(n, n) for n in repeats}
    schema = {"$schema": "http://json-schema.org/draft-07/schema#", **pr(root)}
    if defs:
        schema["$defs"] = defs
    return schema


def output_schema() -> dict:
    return to_json_schema(build_ui_type(COMPONENTS))


if __name__ == "__main__":
    sch = output_schema()
    text = json.dumps(sch, ensure_ascii=False, separators=(",", ":"))     # JSON.stringify 와 같은 모양
    if "--json" in sys.argv:
        print(text)
    else:
        print("컴포넌트:", [c.name for c in COMPONENTS])
        print("루트 키:", list(sch), "| ui 항목:", sch["properties"]["ui"]["items"])
        print("$defs 이름:", list(sch["$defs"]))
        print("글자 수:", len(text))
EOF
```

```bash
$PY ui_schema.py
```

```text
컴포넌트: ['Markdown', 'card', 'calendar', 'row', 'column', 'chart', 'menubar', 'menubar_menu', 'menubar_trigger', 'menubar_content', 'menubar_item', 'code_block', 'input', 'button', 'select', 'label']
루트 키: ['$schema', 'type', 'properties', 'required', 'additionalProperties', 'description', '$defs'] | ui 항목: {'$ref': '#/$defs/anyOf'}
$defs 이름: ['anyOf', 'aSingleMenuWithinTheMenubarContainingATriggerAndDropdownContent', 'theClickableLabelThatOpensAMenuDropdown', 'theDropdownContentPanelOfAMenu', 'aSingleClickableItemInsideAMenuDropdown']
글자 수: 10562
```

![스키마가 만들어지는 길](diagrams/extra-schema.svg)

요청을 대신 보내는 스크립트도 이 Step에서 저장합니다. 화면처럼 앞 턴의 메시지를 `MESSAGES_SNAPSHOT`으로 교체해 들고 있다가(`@ag-ui/client`의 스냅숏 처리 소스를 따름) 다음 요청에 함께 보냅니다. `urllib`이 셸의 프록시 변수를 따르지 않도록 `ProxyHandler({})`로 엽니다. Step 4부터 씁니다.

```bash
cat > drive.py <<'EOF'
"""화면 대신 AG-UI 요청을 보내고 이벤트를 읽는다. 루프백 주소가 아니면 아무것도 보내지 않는다.

화면(CopilotChat)이 보내는 RunAgentInput 의 모양을 따랐다: threadId·runId·state·messages·tools·context·forwardedProps.
context 에는 App.tsx 의 useAgentContext({ description: "output_schema", value }) 가 만든 항목 하나가 들어간다.
화면처럼 앞 턴의 메시지를 들고 있다가(MESSAGES_SNAPSHOT 으로 교체) 다음 요청에 함께 보낸다 — threads/<스레드>.json.

사용법: python drive.py <에이전트 포트> "<말>" [--thread 이름] [--no-schema] [--short-history] [--raw]
"""
import json
import os
import sys
import uuid
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

import guard
import ui_schema

port = int(sys.argv[1])
text = sys.argv[2]
thread = sys.argv[sys.argv.index("--thread") + 1] if "--thread" in sys.argv else "t-" + uuid.uuid4().hex[:6]
url = f"http://127.0.0.1:{port}/"
if not guard.is_loopback_host(urlparse(url).hostname or ""):
    sys.exit("가드: 루프백이 아닌 주소입니다. 중단합니다.")
guard.install_socket_guard()

os.makedirs("threads", exist_ok=True)
store = os.path.join("threads", thread + ".json")
messages = json.load(open(store, encoding="utf-8")) if os.path.exists(store) else []
if "--short-history" in sys.argv:       # 도구·시스템 메시지를 빼고 보낸다(기록을 자기 저장소에서 되살리는 클라이언트를 흉내)
    messages = [m for m in messages if m["role"] in ("user", "assistant") and not m.get("toolCalls")]
messages.append({"id": "u-" + uuid.uuid4().hex[:8], "role": "user", "content": text})
context = [] if "--no-schema" in sys.argv else [
    {"description": "output_schema", "value": json.dumps(ui_schema.output_schema(), ensure_ascii=False, separators=(",", ":"))}]
body = {"threadId": thread, "runId": "r-" + uuid.uuid4().hex[:8], "state": {}, "messages": messages,
        "tools": [], "context": context, "forwardedProps": {}}

req = Request(url, data=json.dumps(body).encode(), headers={"content-type": "application/json", "accept": "text/event-stream"})
events = []
opener = build_opener(ProxyHandler({}))      # 루프백 호출은 프록시를 거치지 않는다(셸의 HTTP(S)_PROXY 를 따르지 않음)
with opener.open(req, timeout=60) as resp:
    for line in resp:
        line = line.decode("utf-8").strip()
        if line.startswith("data:"):
            events.append(json.loads(line[5:]))

content, snapshot = "", None
for ev in events:
    t = ev["type"]
    if t == "TEXT_MESSAGE_CONTENT":
        content += ev["delta"]
    if t == "MESSAGES_SNAPSHOT":
        snapshot = ev["messages"]
    info = {"TEXT_MESSAGE_CONTENT": lambda: f'{len(ev["delta"])}자',
            "TOOL_CALL_START": lambda: ev["toolCallName"],
            "TOOL_CALL_ARGS": lambda: ev["delta"],
            "TOOL_CALL_RESULT": lambda: ev["content"][:60],
            "STEP_STARTED": lambda: ev["stepName"],
            "MESSAGES_SNAPSHOT": lambda: " ".join(m["role"] for m in ev["messages"]),
            "RUN_ERROR": lambda: ev["message"][:120]}.get(t, lambda: "")()
    if t != "RAW":
        print(f"{t:22} {info}")
print("이벤트", len(events), "건, 그중 RAW", sum(e["type"] == "RAW" for e in events))
print("글 길이:", len(content))
try:
    tree = json.loads(content)
    names = []

    def walk(n, depth=0):
        for k, v in n.items():
            names.append("  " * depth + k)
            for c in v.get("children", []) if isinstance(v.get("children"), list) else []:
                walk(c, depth + 1)

    for n in tree["ui"]:
        walk(n)
    print("ui 트리:\n" + "\n".join(names))
except (ValueError, KeyError, TypeError, AttributeError):
    print("글(JSON 아님):", content[:80])
if snapshot is not None:
    json.dump(snapshot, open(store, "w", encoding="utf-8", newline="\n"), ensure_ascii=False)
if "--raw" in sys.argv:
    print(json.dumps(events, ensure_ascii=False)[:3000])
guard.report()
EOF
```

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 결과에서 몇 가지가 보입니다. `Markdown`의 이름은 대문자 M입니다(hashbrown `exposeMarkdown`의 기본 이름). 소문자 `markdown`을 찾는 화면 코드가 있는데 Step 6에서 봅니다. 부품 네 개(`menubar_*`)가 `ui` 최상위에도 후보로 나옵니다. 부품 하나의 모든 속성이 `required`이므로 `row`는 `gap`·`align`·`justify`를 매번 채워야 하고, 이 속성들의 형식은 문자열일 뿐이라 `"large"`도 통과합니다(화면이 모르는 값은 기본값으로 처리합니다. Step 6). 화면이 보내는 요청 전체는 이렇습니다. `@copilotkitnext/core`의 `ProxiedCopilotRuntimeAgent`가 `{method: "agent/run", params: {agentId}, body: RunAgentInput}` 봉투를 런타임 주소에 POST하고(`useSingleEndpoint`의 기본값 `true`는 `@copilotkit/react-core` 1.54.0의 `CopilotKit` 공급자의 것이고 `copilotkit-Yh_Ld_FX.mjs:1554`, 이 앱이 쓰는 것도 이쪽입니다. `@copilotkitnext/react`의 `CopilotKitProvider`는 기본이 `false`입니다), `RunAgentInput`은 `threadId`·`runId`·`tools`·`context`·`forwardedProps`·`state`·`messages`입니다(`@ag-ui/client` 0.0.47의 `prepareRunAgentInput`). 이 앱의 소스에는 프런트엔드 도구 등록이 없으므로 `tools`는 비어 있을 것이고 `context`에는 위 항목 하나뿐일 것입니다. 화면은 `agent/run` 전에도 요청을 둘 보냅니다. CopilotKit이 시작하며 `{method: "info"}`로 런타임이 가진 에이전트 목록을 묻고(`@copilotkitnext/core` 1.54.0 `index.mjs:337-350`), `CopilotChat`이 마운트하며 `agent/connect`를 보냅니다(`@copilotkitnext/react`의 `CopilotChat.mjs`). 이 문서는 두 요청의 응답을 보지 못했습니다. 이 구성은 소스를 읽어 정한 것이고 실제 브라우저 요청을 보지는 못했습니다.

### Step 4. 에이전트 그래프와 첫 요청 — 모델이 받은 것

**목적.** 그래프의 노드가 무엇인지, 미들웨어 셋이 어디에 끼는지, 첫 요청에서 모델이 정확히 무엇을 받는지 봅니다.

**할 일.** `main.py:30-36`은 이렇습니다.

```python
agent = create_agent(
    model="openai:gpt-5.5",
    middleware=[normalize_context, CopilotKitMiddleware(), apply_structured_output_schema],
    context_schema=AgentContext,
    tools=[*search_tools],
    state_schema=AgentState,
    checkpointer=BoundedMemorySaver(max_threads=200),
```

미들웨어는 셋입니다. `normalize_context`(`middleware.py:45-56`, `@before_agent`)는 상태의 문맥 항목이 Pydantic 객체면 사전으로 바꿉니다. `CopilotKitMiddleware`는 `before_agent`에서 문맥을 `App Context:\n<JSON>`이라는 **시스템 메시지**로 대화에 넣고, 화면이 보낸 프런트엔드 도구가 있으면 모델 도구에 합치되 서버에서 실행하지 않도록 떼어 놓습니다(copilotkit 0.1.78의 `copilotkit_lg_middleware.py`를 소스로 확인). `apply_structured_output_schema`(`middleware.py:7-43`, `@wrap_model_call`)는 노드가 아니라 모델 호출을 감쌉니다. 런타임 문맥 또는 `state["copilotkit"]["context"]`에서 `description == "output_schema"`인 항목을 찾아, 값이 문자열이면 `json.loads`하고, 사전이면 `ProviderStrategy(schema=schema, strict=True)`를 `response_format`으로 걸어 요청을 바꿉니다. 그래서 같은 스키마가 문맥 글로, 또 `response_format`으로 두 번 실립니다.

```bash
cat > inspect_graph.py <<'EOF'
"""에이전트 그래프를 가져와 구조만 출력한다(모델은 부르지 않는다). 사용법: python inspect_graph.py"""
import os
import sys

import guard

guard.point_at_fake(9)          # 닫힌 포트: 실수로 호출돼도 어디에도 닿지 않는다
guard.check_env()
guard.install_socket_guard()
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent"))

import main  # noqa: E402

guard.check_env()               # main.py 의 load_dotenv() 뒤에 한 번 더
g = main.agent.get_graph()
print("노드:", [n for n in g.nodes])
for e in g.edges:
    print(f"  {e.source} -> {e.target}" + (" (조건부)" if e.conditional else ""))
print("체크포인터:", type(main.agent.checkpointer).__name__, "max_threads =", main.agent.checkpointer.max_threads)
print("도구:", [t.name for t in main.search_tools])
print("엔드포인트:", sorted((sorted(r.methods), r.path) for r in main.app.routes if hasattr(r, "methods") and r.path in ("/", "//health")))
guard.report()
EOF
```

```bash
$PY inspect_graph.py
```

```text
노드: ['__start__', 'model', 'tools', 'normalize_context.before_agent', 'CopilotKitMiddleware.before_agent', 'CopilotKitMiddleware.after_model', 'CopilotKitMiddleware.after_agent', '__end__']
  CopilotKitMiddleware.after_model -> CopilotKitMiddleware.after_agent (조건부)
  CopilotKitMiddleware.after_model -> model (조건부)
  CopilotKitMiddleware.after_model -> tools (조건부)
  CopilotKitMiddleware.before_agent -> model
  __start__ -> normalize_context.before_agent
  model -> CopilotKitMiddleware.after_model
  normalize_context.before_agent -> CopilotKitMiddleware.before_agent
  tools -> model (조건부)
  CopilotKitMiddleware.after_agent -> __end__
체크포인터: BoundedMemorySaver max_threads = 200
도구: ['search_internet', 'extract_site', 'crawl_site']
엔드포인트: [(['GET'], '//health'), (['POST'], '/')]
가드: 루프백 밖으로 나가려던 시도 0건 []
```

![그래프의 노드 이어짐](diagrams/extra-graph.svg)

![after_model의 갈래](diagrams/extra-branch.svg)

그림에서 `CK`는 `CopilotKitMiddleware`입니다. 노드는 `model`, `tools`, 그리고 미들웨어의 훅 넷입니다. `after_model`에서 갈라지는 세 갈래는 [Day 143 Step 3](../day143-genui-generative-ui-starter-project/README.md)이 같은 모양의 그래프로 이미 설명했고, 여기서는 이 앱에 맞춘 말만 적습니다(`extra-branch`). 처리할 도구 호출이 있으면 `tools`로, 도구 호출이 없으면 `after_agent`로 끝나고, 호출은 있는데 처리할 것이 남지 않았으면(결과 메시지가 이미 붙었음) `model`로 되돌아갑니다(langchain 1.2.0 `agents/factory.py`의 `_make_model_to_tools_edge`를 소스로 확인). 프런트엔드 도구뿐이던 호출은 `after_model`이 떼어 내서 둘째 갈래(끝)로 갑니다. 체크포인터는 `create_agent`에 직접 붙어 있습니다(Day 143은 서버 파일이 따로 붙였습니다). 이제 요청을 하나 보냅니다. 화면 제안 문구 "Make a dashboard"(`suggestions.ts:7-9`)의 글입니다. 터미널 C에서 환경변수 두 줄을 한 뒤 보냅니다.

```bash
$PY drive.py 57132 "Generate a simple dashboard with a title, menu and 2 chart columns." --thread dash1 | grep -v "TEXT_MESSAGE_CONTENT\|STEP_FINISHED"
```

```text
RUN_STARTED            
STEP_STARTED           normalize_context.before_agent
STATE_SNAPSHOT         
STEP_STARTED           CopilotKitMiddleware.before_agent
STATE_SNAPSHOT         
STEP_STARTED           model
TEXT_MESSAGE_START     
TEXT_MESSAGE_END       
STATE_SNAPSHOT         
STEP_STARTED           CopilotKitMiddleware.after_model
STEP_STARTED           CopilotKitMiddleware.after_agent
STATE_SNAPSHOT         
MESSAGES_SNAPSHOT      user system assistant
RUN_FINISHED           
이벤트 114 건, 그중 RAW 62
글 길이: 787
ui 트리:
card
  Markdown
  menubar
    menubar_menu
      menubar_trigger
      menubar_content
        menubar_item
  row
    chart
    chart
가드: 루프백 밖으로 나가려던 시도 0건 []
```

`TEXT_MESSAGE_CONTENT`는 모델의 글 조각이 도착하는 대로 한 건씩 나오고(24자씩, 가짜 서버가 그렇게 흘립니다), 이어 붙이면 부품 트리 JSON입니다. 가짜 서버가 받은 모델 요청을 봅니다.

```bash
cat > show_requests.py <<'EOF'
"""가짜 서버 기록(fake.jsonl)에서 모델 요청이 무엇을 실었는지 요약한다. 사용법: python show_requests.py [기록파일]"""
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "fake.jsonl"
rows = [json.loads(line) for line in open(path, encoding="utf-8")]
n = 0
for r in rows:
    b = r["body"]
    if not r["path"].endswith("/chat/completions"):
        print(f'{r["path"]:<8} {r["auth"]:<15} {json.dumps(b, ensure_ascii=False)[:110]}')
        continue
    n += 1
    msgs = b["messages"]
    chars = [len(m["content"]) if isinstance(m["content"], str) else len(json.dumps(m["content"])) for m in msgs]
    ctx = sum(1 for m in msgs if m["role"] == "system" and isinstance(m["content"], str) and m["content"].startswith("App Context"))
    rf = b.get("response_format")
    print(f'모델 요청 {n}: {r["auth"]} stream={b.get("stream")} 메시지 {[m["role"][0] for m in msgs]} 글자 {chars}')
    print(f'   App Context {ctx}개 | 도구 {[(t["function"]["name"], t["function"].get("strict")) for t in b.get("tools", [])]}'
          f' | response_format {rf["type"] + "/" + rf["json_schema"]["name"] + " strict=" + str(rf["json_schema"].get("strict")) + " " + str(len(json.dumps(rf["json_schema"]["schema"]))) + "자" if rf else "없음"}')
EOF
```

```bash
$PY show_requests.py
```

```text
모델 요청 1: Bearer sk-fake stream=True 메시지 ['s', 'u', 's'] 글자 [455, 67, 11979]
   App Context 1개 | 도구 [('search_internet', True), ('extract_site', True), ('crawl_site', True)] | response_format json_schema/StructuredOutput strict=True 11171자
```

![Step 4까지의 구성](diagrams/step4.svg)

![스키마가 두 번 실리는 길](diagrams/extra-twice.svg)

**확인.** 메시지 순서가 `system, user, system`입니다. `App Context` 시스템 메시지가 사용자 말 **뒤**에 붙었습니다. `before_agent`가 돌려준 메시지 목록을 LangGraph의 `add_messages`가 합칠 때 아이디가 없는 새 메시지는 끝에 붙기 때문입니다(`MESSAGES_SNAPSHOT`도 `user system assistant` 순서입니다). 첫 메시지(455자)는 `main.py:37-43`의 시스템 프롬프트입니다. 도구 셋 모두 `strict=True`로 묶였고(`create_agent`가 구조화 출력에 `bind_tools(..., strict=True)`를 씁니다), 요청은 `stream=True`입니다. 글자 수는 시스템 프롬프트 455 + 사용자 67 + `App Context` 약 1.2만 + `response_format` 약 1.1만입니다. 같은 스키마가 두 번 실려 첫 질문부터 약 2.4만 자입니다.

### Step 5. 도구가 끼는 요청 — 검색, 스트림, 그리고 두 가지 고장

**목적.** 모델이 검색 도구를 부르는 요청, 그 이벤트, 그리고 소스를 읽다 찾은 `crawl_site`의 인자와 모델이 JSON이 아닌 답을 낼 때의 모양을 봅니다.

**할 일.** `search.py`는 도구 셋을 만듭니다(`search_internet`, `extract_site`, `crawl_site`). Tavily 클라이언트는 첫 도구 호출 때 `os.environ["TAVILY_API_KEY"]`로 만들어집니다(`search.py:7-11`). 열쇠가 없으면 가져오기가 아니라 이 호출에서 `KeyError`가 납니다(소스로 확인, 실행하지 않았습니다). "pizza"가 들어간 말은 가짜 모델이 `search_internet`을 부르게 합니다(화면의 두 번째 제안 문구와 같은 뜻입니다).

```bash
$PY drive.py 57132 "Research the best pizza in San Francisco and make a report about it with the data you find." --thread pizza1 | grep -v "TEXT_MESSAGE_CONTENT\|STEP_FINISHED\|STATE_SNAPSHOT\|STEP_STARTED"
```

```text
RUN_STARTED            
TOOL_CALL_START        search_internet
TOOL_CALL_END          
TOOL_CALL_RESULT       {"query": "best pizza in San Francisco", "results": [{"title
TEXT_MESSAGE_START     
TEXT_MESSAGE_END       
MESSAGES_SNAPSHOT      user system assistant tool assistant
RUN_FINISHED           
이벤트 110 건, 그중 RAW 67
글 길이: 298
ui 트리:
card
  Markdown
  chart
가드: 루프백 밖으로 나가려던 시도 0건 []
```

`TOOL_CALL_START`와 `TOOL_CALL_END`는 있는데 `TOOL_CALL_ARGS`가 없습니다. 이유는 아래에서 보고, 먼저 이 요청이 가짜 서버에 남긴 기록을 봅니다. 모델 요청은 이제 셋입니다. 둘째·셋째 요청과 그 사이의 검색 요청입니다.

```bash
$PY show_requests.py | tail -n 5
```

```text
모델 요청 2: Bearer sk-fake stream=True 메시지 ['s', 'u', 's'] 글자 [455, 91, 11979]
   App Context 1개 | 도구 [('search_internet', True), ('extract_site', True), ('crawl_site', True)] | response_format json_schema/StructuredOutput strict=True 11171자
/search  Bearer tvly-fa  {"query": "best pizza in San Francisco"}
모델 요청 3: Bearer sk-fake stream=True 메시지 ['s', 'u', 's', 'a', 't'] 글자 [455, 91, 11979, 4, 315]
   App Context 1개 | 도구 [('search_internet', True), ('extract_site', True), ('crawl_site', True)] | response_format json_schema/StructuredOutput strict=True 11171자
```

둘째 모델 요청은 첫 질문과 같은 모양이고, 셋째에는 도구 결과(`ToolMessage`)가 들어 있으며 둘 다 `response_format`이 그대로입니다. 이제 스키마를 빼고(`--no-schema`, 곧 `response_format` 없이) 같은 질문을 보내 비교합니다.

```bash
$PY drive.py 57132 "Research the best pizza in San Francisco" --thread ns1 --no-schema | grep -E "^TOOL_CALL" | cut -c1-70
```

```text
TOOL_CALL_START        search_internet
TOOL_CALL_ARGS         {"query": "best pizza in San Francisco"}
TOOL_CALL_END          
TOOL_CALL_RESULT       {"query": "best pizza in San Francisco", "resul
```

이 문서의 재현에서는 `response_format`이 있을 때만 인자 조각이 없습니다. 소스로 보면 이유가 이렇습니다. `response_format`이 붙으면 `langchain-openai`는 `beta.chat.completions.stream` 도우미로 스트림을 받고(`base.py`의 `_astream`), 도우미가 사이사이에 내놓는 이벤트는 빈 조각이 되며, `ag-ui-langgraph`는 도구 호출 중에 도구 데이터 없는 조각이 오면 호출이 끝난 것으로 읽습니다(`agent.py`의 `is_tool_call_end_event`). 이 앱의 화면 소스는 도구 호출의 인자를 쓰지 않으므로(도구 렌더러 등록이 없음) 영향이 없어 보이지만 화면은 실행하지 못했습니다.

![Step 5까지의 구성](diagrams/step5.svg)

다음은 `crawl_site`입니다. 에이전트 묶음에서 그래프가 도구를 부르고 도구가 Tavily를 부르는 길은 그림과 같습니다.

![에이전트 묶음 안 (2)](diagrams/extra-agent-out.svg)

`search.py:24-26`은 `_get_client().crawl(website, instructions)`를 부르는데, `tavily-python` 0.7.21의 시그니처는 `crawl(self, url, max_depth=None, max_breadth=None, limit=None, instructions=None, ...)`입니다. 두 번째 자리 인자는 `instructions`가 아니라 `max_depth`입니다.

```bash
$PY drive.py 57132 "Crawl example.com for pricing" --thread crawl1 > /dev/null
grep '"/crawl"' fake.jsonl | $PY -c "import sys, json; print(json.dumps(json.loads(sys.stdin.readline())['body'], ensure_ascii=False))"
```

```text
{"url": "https://example.com", "max_depth": "find the pricing pages", "timeout": 150}
```

`"max_depth": "find the pricing pages"`로 갔고 `instructions`는 없습니다. 진짜 Tavily가 이 요청을 거절하는지 무시하는지는 확인하지 못했습니다(가짜 서버는 검증하지 않습니다). 마지막으로 모델이 JSON이 아닌 답을 내는 경우입니다.

```bash
$PY drive.py 57132 "bad json please" --thread bad1 | grep -v "TEXT_MESSAGE_CONTENT\|STEP_FINISHED\|STATE_SNAPSHOT"
grep -m1 StructuredOutputValidationError agent.out | cut -c1-200
```

```text
RUN_STARTED            
STEP_STARTED           normalize_context.before_agent
STEP_STARTED           CopilotKitMiddleware.before_agent
STEP_STARTED           model
TEXT_MESSAGE_START     
TEXT_MESSAGE_END       
이벤트 29 건, 그중 RAW 18
글 길이: 16
글(JSON 아님): this is not json
가드: 루프백 밖으로 나가려던 시도 0건 []
langchain.agents.structured_output.StructuredOutputValidationError: Failed to parse structured output for tool 'response_format': Native structured output expected valid JSON for response_format, but 
```

글이 JSON이 아니면 `StructuredOutputValidationError`가 서버 쪽 로그에 남고(`agent.out`의 그 줄), 에이전트 서버의 스트림은 `RUN_ERROR`도 `RUN_FINISHED`도 없이 끝납니다. 다만 실제 화면 경로에는 CopilotKit 런타임이 끼어 있고, 그 기본 러너(`InMemoryAgentRunner`, `@copilotkitnext/runtime` 1.54.0)는 스트림이 끝났는데 종료 이벤트가 없으면 `finalizeRunEvents`(`@copilotkitnext/shared`)로 `RUN_ERROR`(code `INCOMPLETE_STREAM`, "Run ended without emitting a terminal event")를 붙입니다(소스로 확인, 실행하지 못했습니다). 그러니 화면이 받는 것은 오류 이벤트일 것이고, 그것을 어떻게 보여 주는지는 확인하지 못했습니다. strict 모드의 진짜 OpenAI가 JSON을 어기는 일이 드물더라도, 이 앱의 에이전트 쪽에는 마지막 답이 JSON인지 확인하거나 오류를 내보내는 곳이 없습니다.

**확인.** 위 출력에서 세 가지를 확인합니다. 도구를 거친 요청이 모델 요청 둘과 `/search` 하나를 남기고(`show_requests.py`), `/crawl` 본문의 `max_depth`에 지시문이 들어가 있고, 마지막 답이 JSON이 아닐 때 서버 로그에 `StructuredOutputValidationError`가 남으며 스트림에 `RUN_FINISHED`가 없습니다.

### Step 6. 화면이 그리고 내보내는 법 — 소스로 읽었습니다

**목적.** JSON 글이 어떻게 부품이 되고, Export Code가 무엇을 만드는지 봅니다.

**할 일.** `custom-message-renderer.tsx:19-59`가 답 메시지마다 `useJsonParser(message.content ?? "", kit.schema)`로 반쯤 온 글을 파싱하고 `kit.render(value)`로 그립니다. `kit.render`(`@hashbrownai/react`의 `useUiKit`)는 `value.ui`의 노드를 부품 레지스트리로 렌더하고, 노드가 모두 완성됐을 때 스키마 검증을 합니다. 덜 온 부품은 `exposeComponent`의 `fallback`, 곧 "👨‍🍳 Cooking..."으로 나옵니다(`chat-kit.tsx:14-16`). 파싱이 끝나면(`parserState.isComplete`) 그리고 `ui`에 마크다운이 아닌 노드가 있으면 Export Code 버튼이 붙습니다. 그 "마크다운이 아닌" 판단이 `keys[0] !== "markdown"`(`custom-message-renderer.tsx:37`)이고, `tree-to-jsx.ts:35`도 `tagName === "markdown"`을 소문자로 비교합니다. 그런데 Step 3에서 본 대로 키트의 이름은 `Markdown`입니다. 소스를 읽은 결론은 이렇습니다. 마크다운만 있는 답에도 Export 버튼이 붙을 것이고, 내보내는 코드에는 `Markdown` 줄이 남을 것입니다. 그 줄은 노드 감싸개(`complete`·`partialValue`·`value`를 가진 객체)가 그대로 직렬화돼 `children={{"complete":…,"partialValue":…,"value":…}}` 모양일 것입니다(소스로 읽은 추정). 실제 화면에서 보지는 못했습니다. 화면 묶음 안의 이어짐은 그림과 같습니다. `CopilotChat`이 `assistantMessage`로 이 렌더러를 쓰고(`chat-theme.ts:12`), 렌더러가 키트로 글을 파싱·렌더하고(`custom-message-renderer.tsx:24-25`), 트리를 내보내기로 넘깁니다.

![화면 묶음 안](diagrams/extra-ui.svg)

화면 쪽 부품에도 읽을 만한 곳이 있습니다. `layout.tsx:45`의 `Row`에는 `[&>*:nth-child(n+4)]:hidden`이 있어 자식 넷째부터 숨깁니다(시스템 프롬프트의 "2 columns max"와 맞물립니다). `gap`·`align`·`justify`는 표에 없는 값이면 기본값으로 돌아갑니다(`layout.tsx:46-48`). Export가 만드는 코드가 무엇인지는 `tree_to_jsx.py`로 봅니다. 옮겨 쓴 것이므로 실제 버튼의 출력과 같다고 보장하지 못합니다. 입력은 `props.value`로 감싼 파서 모양을 가정했습니다(`tree-to-jsx.ts:46-47`이 읽는 필드).

```bash
cat > tree_to_jsx.py <<'EOF'
"""화면의 Export Code 가 하는 일(apps/ui/src/lib/tree-to-jsx.ts)을 파이썬으로 옮겨 쓴 것. 브라우저 코드는 실행하지 않았다.

입력은 화면의 파서가 만든 트리다. tree-to-jsx.ts 가 읽는 필드(props.value, children)를 따라 같은 모양으로 감싼다.
사용법: python tree_to_jsx.py
"""
import json

COMPONENT_MAP = {
    "card": ("Card", "@/components/ui/card"), "row": ("Row", "@/components/ui/layout"),
    "column": ("Column", "@/components/ui/layout"), "chart": ("SimpleChart", "@/components/ui/simple-chart"),
    "calendar": ("Calendar", "@/components/ui/calendar"), "code_block": ("CodeBlock", "@/components/ui/code-block"),
    "menubar": ("Menubar", "@/components/ui/menubar"), "menubar_menu": ("MenubarMenu", "@/components/ui/menubar"),
    "menubar_trigger": ("MenubarTrigger", "@/components/ui/menubar"), "menubar_content": ("MenubarContent", "@/components/ui/menubar"),
    "menubar_item": ("MenubarItem", "@/components/ui/menubar"), "input": ("Input", "@/components/ui/input"),
    "button": ("Button", "@/components/ui/button"), "select": ("SimpleSelect", "@/components/ui/simple-select"),
    "label": ("Label", "@/components/ui/label"),
}


def fmt(v):
    if isinstance(v, str):
        return f'"{v}"'                                  # 따옴표를 이스케이프하지 않는다(원본도 그렇다)
    if isinstance(v, bool):
        return "{" + ("true" if v else "false") + "}"
    if isinstance(v, (int, float)):
        return "{" + str(v) + "}"
    return "{" + json.dumps(v, ensure_ascii=False, separators=(",", ":")) + "}"


def node_to_jsx(node, indent, imports):
    if isinstance(node, str):
        return "  " * indent + node
    if not isinstance(node, dict) or not node:
        return ""
    tag, data = next(iter(node.items()))
    if tag == "markdown":                                # 소문자 m — 화면의 Markdown 이름은 대문자 M 이다
        return ""
    if not isinstance(data, dict):
        return ""
    mapping = COMPONENT_MAP.get(tag)
    name = mapping[0] if mapping else tag
    if mapping:
        if (mapping[1], mapping[0]) not in imports:
            imports.append((mapping[1], mapping[0]))
    props = data.get("props") or {}
    values = props.get("value") or props.get("partialValue") or {}
    props_str = "".join(f" {k}={fmt(v)}" for k, v in values.items() if v is not None)
    pad = "  " * indent
    children = data.get("children")
    if not children:
        return f"{pad}<{name}{props_str} />"
    if isinstance(children, str):
        return f"{pad}<{name}{props_str}>{children}</{name}>"
    inner = "\n".join(filter(None, (node_to_jsx(c, indent + 1, imports) for c in children)))
    return f"{pad}<{name}{props_str}>\n{inner}\n{pad}</{name}>"


def tree_to_jsx(tree):
    imports = []                                         # JS Set 처럼 처음 나온 순서를 지킨다
    body = "\n".join(filter(None, (node_to_jsx(n, 2, imports) for n in tree)))
    by_path = {}
    for path, comp in imports:
        by_path.setdefault(path, []).append(comp)
    block = "\n".join(f'import {{ {", ".join(c)} }} from "{p}";' for p, c in by_path.items())
    head = block + "\n\n" if block else ""
    return head + "export default function GeneratedComponent() {\n  return (\n    <>\n" + body + "\n    </>\n  );\n}"


def wrap(n):                                             # 에이전트가 보낸 { 이름: { props, children } } 의 props 를 파서 모양으로 감싼다
    (tag, data), = n.items()
    out = {"props": {"value": data["props"]}}
    if "children" in data:
        out["children"] = data["children"] if isinstance(data["children"], str) else [wrap(c) for c in data["children"]]
    return {tag: out}


SAMPLE = {"ui": [{"card": {"props": {}, "children": [
    {"column": {"props": {"gap": "4", "align": "stretch", "justify": "start"}, "children": [
        {"row": {"props": {"gap": "4", "align": "center", "justify": "between"}, "children": [
            {"chart": {"props": {"type": "bar", "labels": ["Q1", "Q2"], "values": [120, 150], "label": "Revenue", "color": "#EB6C36"}}},
            {"button": {"props": {"variant": "outline", "size": "sm"}, "children": "Refresh"}}]}}]}}]}}]}

if __name__ == "__main__":
    print(tree_to_jsx([wrap(n) for n in SAMPLE["ui"]]))
EOF
```

```bash
$PY tree_to_jsx.py
```

```text
import { Card } from "@/components/ui/card";
import { Column, Row } from "@/components/ui/layout";
import { SimpleChart } from "@/components/ui/simple-chart";
import { Button } from "@/components/ui/button";

export default function GeneratedComponent() {
  return (
    <>
    <Card>
      <Column gap="4" align="stretch" justify="start">
        <Row gap="4" align="center" justify="between">
          <SimpleChart type="bar" labels={["Q1","Q2"]} values={[120,150]} label="Revenue" color="#EB6C36" />
          <Button variant="outline" size="sm">Refresh</Button>
        </Row>
      </Column>
    </Card>
    </>
  );
}
```

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** 내보낸 글의 import 경로는 `@/components/ui/layout`·`simple-chart` 같은 이 저장소 안의 경로입니다. `Row`·`Column`·`SimpleChart`·`SimpleSelect`·`CodeBlock`은 shadcn 레지스트리의 부품이 아니라 이 앱이 직접 짠 파일이므로, 다른 프로젝트에 붙이려면 그 파일도 함께 가져가야 합니다. 문자열 속성은 따옴표를 이스케이프하지 않고 그대로 넣습니다(`tree-to-jsx.ts:20`).

### Step 7. 두 번째 턴과 패치 — 쌓이는 문맥, 지켜지지 않는 상한

**목적.** 같은 스레드의 다음 요청에서 일어나는 일과, `patches.py`·`BoundedMemorySaver`가 하는 일을 재현으로 봅니다.

**할 일.** 같은 스레드(`pizza1`)에 두 번째 말을 보냅니다. 첫 턴에서 만든 메시지가 `threads/pizza1.json`에 있으니 화면처럼 함께 갑니다.

```bash
$PY drive.py 57132 "Now generate a simple dashboard" --thread pizza1 | grep -E "MESSAGES_SNAPSHOT|^글 길이"
$PY show_requests.py | tail -n 2
```

```text
MESSAGES_SNAPSHOT      user system assistant tool assistant user system assistant
글 길이: 787
모델 요청 9: Bearer sk-fake stream=True 메시지 ['s', 'u', 's', 'a', 't', 'a', 'u', 's'] 글자 [455, 91, 11979, 4, 315, 298, 31, 11979]
   App Context 2개 | 도구 [('search_internet', True), ('extract_site', True), ('crawl_site', True)] | response_format json_schema/StructuredOutput strict=True 11171자
```

`MESSAGES_SNAPSHOT`에 시스템 메시지가 둘이고, 두 번째 모델 요청의 `App Context`가 **둘**입니다. `CopilotKitMiddleware.before_agent`는 이미 있는 문맥 메시지를 새 메시지로 "바꾸는" 코드를 가졌지만(`existing_context_index`), 새 `SystemMessage`에 아이디가 없어 LangGraph가 교체가 아니라 추가로 받아들입니다. 그 결과 턴마다 약 1.2만 자가 쌓입니다(5턴이면 6만 자). 스키마가 바뀌지 않아도 마찬가지입니다. 이제 패치입니다. `patches.py:12-43`은 `ag_ui_langgraph.agent.LangGraphAgent`의 메서드 셋(`prepare_stream`, `get_checkpoint_before_message`, `set_message_in_progress`)을 가져오기 때문에 `ag-ui-langgraph==0.0.25`로 고정해야 합니다(파일 머리 주석이 세 버그를 설명합니다). 첫째·둘째 패치가 함께 막는 경우를 재현해 봅니다. 서버 체크포인트의 메시지 수가 클라이언트가 보낸 수보다 많으면 `ag-ui-langgraph`는 "다시 만들기"로 읽고 `get_checkpoint_before_message`가 `ValueError`("Message ID not found in history")를 던집니다. 클라이언트가 도구·시스템 메시지 없이 기록만 보내면 그렇게 됩니다(`drive.py --short-history`). 패치를 끈 서버(`run_unpatched.py`, 포트 57133)와 비교합니다.

```bash
cat > run_unpatched.py <<'EOF'
"""패치(src/patches.py)를 끈 채로 같은 서버를 띄운다 — 패치가 무엇을 막는지 보려는 실험용.
사용법: python run_unpatched.py <가짜 서버 포트> <에이전트 포트>"""
import os
import sys

import guard

fake_port = int(sys.argv[1])
agent_port = int(sys.argv[2])
guard.point_at_fake(fake_port)
guard.check_env()
guard.install_socket_guard()

here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, "agent"))
import src.patches as patches  # noqa: E402

patches.apply = lambda: None          # main.py 의 `from src.patches import apply` 가 이 빈 함수를 받는다

import main  # noqa: E402

guard.check_env()

import uvicorn  # noqa: E402

uvicorn.run(main.app, host="127.0.0.1", port=agent_port, log_level="warning")
guard.report()
EOF
```

```bash
# 터미널 D (패치를 끈 서버)
OPENAI_API_KEY=sk-pretend-real-key LANGSMITH_TRACING=true $PY run_unpatched.py 57131 57133 2>&1 | tee agent_unpatched.out
```

```powershell
# 터미널 D (실행해 보지 못했습니다)
$env:OPENAI_API_KEY = "sk-pretend-real-key"; $env:LANGSMITH_TRACING = "true"
& $PY run_unpatched.py 57131 57133
```

```bash
for port in 57132 57133; do
  $PY drive.py $port "Research the best pizza in San Francisco" --thread sh-$port > /dev/null
  echo "== 포트 $port (끝 줄)"
  $PY drive.py $port "Generate a simple dashboard" --thread sh-$port --short-history | grep -E "^이벤트|^글 길이"
done
tail -n 1 agent_unpatched.out
```

```text
== 포트 57132 (끝 줄)
이벤트 114 건, 그중 RAW 62
글 길이: 787
== 포트 57133 (끝 줄)
이벤트 0 건, 그중 RAW 0
글 길이: 0
ValueError: Message ID not found in history
```

![Step 7까지의 구성](diagrams/step7.svg)

패치가 있는 서버(57132)는 요청을 받아 끝까지 달렸고, 패치를 끈 서버(57133)는 이벤트 0건입니다. 서버 로그에 `ValueError: Message ID not found in history`가 남습니다. 셋째 패치(`set_message_in_progress`의 `None` 처리)가 막는 경우는 재현하지 못했습니다. 마지막은 `BoundedMemorySaver`입니다. `bounded_memory_saver.py:46-54`는 스레드가 `max_threads`를 넘으면 가장 오래된 스레드를 `del self.storage[oldest_thread]`로 지웁니다. 파일 머리 주석은 Render 512MB 플랜의 메모리 폭주를 막으려는 것이라고 합니다. `MemorySaver`는 `storage` 말고도 `writes`와 `blobs`에 스레드별 데이터를 담습니다(`delete_thread`는 셋 다 지웁니다). 한도를 3으로 낮춰 같은 그래프를 여섯 스레드에 돌려 봅니다.

```bash
cat > saver_test.py <<'EOF'
"""BoundedMemorySaver 가 오래된 스레드를 밀어낼 때 무엇이 남는지 본다.
같은 프로세스에서 가짜 모델 서버를 부른다. 사용법: python saver_test.py <가짜 서버 포트>"""
import asyncio
import os
import sys

import guard

guard.point_at_fake(int(sys.argv[1]))
guard.check_env()
guard.install_socket_guard()
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent"))

import main  # noqa: E402

guard.check_env()                          # main.py 의 load_dotenv() 뒤에 한 번 더

saver = main.agent.checkpointer
saver.max_threads = 3                      # 200 번 돌리지 않으려고 이 실험에서만 낮춘다


def sizes():
    return f"storage 스레드 {len(saver.storage)} | writes 키 {len(saver.writes)} | blobs 키 {len(saver.blobs)}"


async def run():
    for i in range(1, 7):
        await main.agent.ainvoke({"messages": [("user", f"hello {i}")]}, {"configurable": {"thread_id": f"t{i}"}})
        print(f"스레드 {i}개 돌린 뒤:", sizes())
    print("남은 스레드:", sorted(saver.storage))
    print("writes 가 가리키는 스레드:", sorted({k[0] for k in saver.writes}))
    print("blobs 가 가리키는 스레드:", sorted({k[0] for k in saver.blobs}))


asyncio.run(run())
guard.report()
EOF
```

```bash
$PY saver_test.py 57131
```

```text
스레드 1개 돌린 뒤: storage 스레드 1 | writes 키 6 | blobs 키 14
스레드 2개 돌린 뒤: storage 스레드 2 | writes 키 12 | blobs 키 28
스레드 3개 돌린 뒤: storage 스레드 3 | writes 키 18 | blobs 키 42
스레드 4개 돌린 뒤: storage 스레드 3 | writes 키 24 | blobs 키 56
스레드 5개 돌린 뒤: storage 스레드 3 | writes 키 30 | blobs 키 70
스레드 6개 돌린 뒤: storage 스레드 3 | writes 키 36 | blobs 키 84
남은 스레드: ['t4', 't5', 't6']
writes 가 가리키는 스레드: ['t1', 't2', 't3', 't4', 't5', 't6']
blobs 가 가리키는 스레드: ['t1', 't2', 't3', 't4', 't5', 't6']
가드: 루프백 밖으로 나가려던 시도 0건 []
```

**확인.** `storage`는 3에서 멈추지만 `writes`와 `blobs`는 스레드마다 계속 늘고, 밀려난 스레드 `t1`~`t3`의 데이터가 그대로 남았습니다. `blobs`는 채널 값, 곧 메시지가 들어가는 곳이므로 이 상한은 메모리를 묶어 두지 못합니다. 이 판의 `langgraph-checkpoint` 3.0.1 기준이고 서버에서 200스레드까지 돌려 보지는 않았습니다.

### Step 8. 런타임과 원본 실행 경로 — 읽기만 했습니다

**목적.** 이 문서가 실행하지 않은 부분, 곧 런타임·화면·원본 실행 명령이 무엇을 하는지 소스로 정리합니다.

**할 일.** 루트 `package.json:6`의 `pnpm dev`는 `concurrently`로 `ui`(vite), `runtime`(`tsx watch server.ts`), `agent`(`cd apps/agent && uv sync && uv run python main.py`)를 한꺼번에 띄웁니다.

![원본 실행 경로](diagrams/extra-dev.svg)

런타임 `server.ts:11-43`은 이렇습니다. `new LangGraphHttpAgent({url: process.env.LANGGRAPH_DEPLOYMENT_URL || "http://localhost:8123"})`(`@ag-ui/langgraph` 0.0.24의 `LangGraphHttpAgent`는 `@ag-ui/client`의 `HttpAgent`에 이름만 붙인 것)를 `default` 에이전트로 등록하고, `createCopilotEndpointSingleRoute({basePath: "/api/copilotkit"})`를 Hono 앱에 얹습니다. 소스에서 확인한 것은 이렇습니다. `serve({fetch, port})`에는 `hostname`이 없어서(`@hono/node-server` 1.19.17의 `listen`에 호스트가 `undefined`로 갑니다) Node 기본대로 모든 인터페이스에 열립니다. CORS는 두 곳에서 모든 출처를 허용합니다(`server.ts:25`의 `cors()`와 엔드포인트 자체의 `origin: "*"`). 파이썬 에이전트에도 인증이 없어서 두 포트 중 하나에 닿을 수 있는 사람은 앱 주인의 열쇠로 모델과 Tavily를 부를 수 있습니다. `localhost`가 IPv6 `::1`로 먼저 풀리는 환경에서는 에이전트를 `127.0.0.1`에만 열면 연결이 어긋날 수 있어서, 이렇게 띄운다면 런타임에 `LANGGRAPH_DEPLOYMENT_URL=http://127.0.0.1:8123`을 주는 것이 안전합니다(실행하지 못한 제안입니다). 같은 이유로 `hostname: "127.0.0.1"` 한 줄을 복사본 `server.ts`에 더하는 것도 제안일 뿐 시험하지 못했습니다. 앱 README는 `apps/runtime/.env`에 `OPENAI_API_KEY`를 두라고 하고 `render.yaml`도 그 변수를 만들지만, `server.ts`와 `@copilotkitnext/runtime` 1.54.0 안에는 그 변수를 읽는 곳이 없습니다(소스에서 찾지 못했습니다). 런타임은 열쇠를 쓰지 않는 길로 보입니다.

화면 쪽에서 눈여겨볼 것입니다. `vite.config.ts:14-23`은 `/api/copilotkit`와 `/realtime/session`을 4000으로 프록시하는데 런타임에는 `/realtime/session` 경로가 없습니다. 쓰이지 않는 흔적으로 보입니다. `apps/ui/src/components/chat/input.tsx`와 `weather.tsx`도 어디에서도 가져오지 않고(`grep`으로 확인), `package.json`의 `@frenchfryai/*` 셋도 소스가 가져오지 않습니다. `index.html:8-22`는 Google Fonts와 `cdn.fonts.net`의 스크립트·스타일을 부르므로 화면을 열면 브라우저가 그 호스트에 접속하고, 그 스크립트는 페이지 안에서 실행됩니다. 이 문서는 화면을 띄우지 않았습니다. JS 쪽에는 잠금 파일이 없습니다. 앱의 `.gitignore`가 `pnpm-lock.yaml`을 제외해서, `pnpm install`은 `^` 범위를 그날 가장 새 판으로 풉니다(정확히 고정한 것은 `@copilotkit/*` 1.54.0, `@hashbrownai/*` 0.5.0-beta.4, `@frenchfryai/*` 0.1.1, `recharts` 2.15.4뿐). 이 문서가 읽은 것은 고정된 판들이고 나머지 판은 모릅니다. 설치할 때 주의할 점이 하나 더 있습니다. `@copilotkit/runtime`·`@copilotkit/react-core`가 `@scarf/scarf`(`^1.3.0`)를 의존하고, 이 패키지는 `postinstall`에서 `node ./report.js`를 돌려 `scarf.sh`에 설치 통계를 보냅니다(1.4.0 소스로 확인). 환경변수 `SCARF_ANALYTICS=false`나 `DO_NOT_TRACK=1`이면 보내지 않습니다(`report.js`가 읽음). pnpm 쪽은 공식 문서(2026-10-17에 읽음)로 갈립니다. pnpm 10.0.0 릴리스 노트는 "Lifecycle scripts of dependencies are not executed during installation by default!"라고 적고, 현재 설정 문서는 `allowBuilds`(v10.26.0에 생김)에 올리지 않은 패키지의 스크립트를 기본으로 허용하지 않고 검토 전으로 취급하며, `strictDepBuilds`(v10.3.0에 생김, 현재 문서의 기본값 `true`)가 켜져 있으면 검토 전 빌드 스크립트가 있을 때 설치가 0이 아닌 코드로 끝난다고 적습니다. 그러니 `scarf`의 `postinstall`은 pnpm 9 이하에서만 기본으로 돌고, 최근 pnpm에서는 오히려 설치가 승인 요구로 멈출 수 있습니다. 앱에는 `packageManager` 필드가 없어서 독자의 pnpm 판에 따라 갈립니다. 어느 쪽이든 설치할 독자는 두 변수를 먼저 거는 것이 안전합니다. 텔레메트리는 `@copilotkit/runtime`의 `v2`·`langgraph` 진입점이 가져오는 파일에서 찾지 못했고(가져오기 목록을 읽음), `@copilotkit/react-core` 1.54.0의 `dist`에는 `telemetry`·`scarf`·`segment`·`analytics`라는 글자가 없었습니다. `@copilotkit/shared`는 열어 보지 않았습니다.

마지막으로 저장소 맨 위의 `.mcp.json`은 Claude Code가 이 폴더를 열면 `npx shadcn@latest mcp`를 MCP 서버로 쓰자고 제안하는 설정입니다(`npx`가 패키지를 내려받아 실행합니다). 앱의 일부가 아니라 개발 도구용이고, 이 문서는 어떤 경로로도 실행하지 않았습니다. `.claude/settings.json`은 `render` 플러그인을 켭니다. `render.yaml`은 에이전트를 `uv run uvicorn main:app --host 0.0.0.0 --port $PORT`로 띄우고 Python 3.12.6을 고정합니다(읽기만 했고 배포하지 않았습니다).

![Step 8까지의 구성](diagrams/step8.svg)

**확인.** 이 Step에는 실행한 것이 없습니다. 이 문서에는 화면까지 안전하게 띄우는 명령이 없습니다. 원본의 `pnpm dev`는 그대로 쓰지 마세요. `dev:agent`가 에이전트를 `0.0.0.0`에 `reload=True`로 열고 런타임도 모든 인터페이스에 열리며 둘 다 인증이 없습니다. 화면까지 시험하려면 에이전트와 런타임을 루프백으로만 열도록 직접 바꿔야 하는데 이 문서는 그것을 시험하지 못했습니다. 설치만 할 독자는 `pnpm install` 앞에 `SCARF_ANALYTICS=false DO_NOT_TRACK=1`을 겁니다.

## 요청 한 건이 흐르는 과정

요청 하나가 에이전트 서버 안에서 거치는 일을 코드 순서대로 여섯 그림에 나눠 그렸습니다. 사용자가 "Research the best pizza in San Francisco..."를 보내면, 화면(`CopilotChat`)은 단일 경로 봉투 `{method: "agent/run", params, body: RunAgentInput}`을 런타임에 POST하고, 런타임은 `RunAgentInput`만 에이전트 서버 `/`에 POST합니다. 에이전트는 시작할 때 체크포인터에서 이 스레드의 기록을 읽고(`aget_state`), 그래프의 단계마다 체크포인터에 상태를 저장합니다. 저장은 두 가지입니다. `put`은 단계마다 체크포인트를 쓰고, `put_writes`는 그 단계에서 일한 노드의 결과(쓰기)를 씁니다. 첫 그림은 요청이 들어와 모델을 부르기 직전까지입니다.

![요청 시퀀스](diagrams/sequence.svg)

둘째 그림은 첫 모델 호출입니다. 모델이 `search_internet`을 부르면 에이전트는 호출의 시작과 끝 이벤트를 런타임을 거쳐 화면으로 내보내고, 모델의 결과를 저장한 뒤 도구 호출을 예약합니다(`__pregel_tasks`).

![요청 시퀀스: 모델 호출](diagrams/extra-model.svg)

셋째 그림은 도구입니다. 도구가 Tavily를 부르고 결과가 `ToolMessage`로 돌아오면 에이전트는 `TOOL_CALL_RESULT`를 내보내고 결과를 저장합니다.

![요청 시퀀스: 도구](diagrams/extra-tool.svg)

넷째 그림은 두 번째 모델 호출입니다. 응답은 부품 트리 JSON의 글 조각이고, 에이전트는 이를 `TEXT_MESSAGE_*` 이벤트로 내려보내며, 화면은 반쯤 온 JSON을 파싱해 `kit.render`로 그립니다. 사용자 눈에 카드가 보이는 것은 이 스트림이 도는 동안입니다. 런타임과 화면 쪽 줄은 소스를 읽은 것이고 실행하지 못했습니다. 화면에서 부품이 그려지는 모양은 보지 못했습니다.

![요청 시퀀스: 답](diagrams/extra-answer.svg)

다섯째 그림은 모델 응답이 끝난 뒤 그래프가 마무리하는 저장입니다. 마지막 메시지와 `structured_response`를 저장하고(`put_writes`), `after_agent`를 거쳐 끝납니다.

![요청 시퀀스: 마무리 저장](diagrams/extra-put.svg)

여섯째 그림은 끝입니다. 에이전트는 최종 상태를 다시 읽어(`aget_state`) `MESSAGES_SNAPSHOT`과 `RUN_FINISHED`를 내려보냅니다.

![요청 시퀀스: 끝](diagrams/extra-finish.svg)

이 저장 횟수를 직접 세 봅니다. 같은 그래프를 `ainvoke`로 한 번 돌리면서 체크포인터의 `put`·`put_writes`를 세는 스크립트입니다. 가짜 서버가 떠 있어야 합니다.

```bash
cat > count_put.py <<'EOF'
"""pizza 장면 한 번(ainvoke)에서 체크포인터 put·put_writes 가 도구 호출 사이 어디에 끼는지 센다. 사용법: python count_put.py <가짜 서버 포트>"""
import asyncio, json, os, sys
import guard
guard.point_at_fake(int(sys.argv[1]))
guard.check_env()
guard.install_socket_guard()
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent"))
import main
guard.check_env()
import ui_schema
saver = main.agent.checkpointer
events = []
real_put, real_pw = saver.put, saver.put_writes
def put(config, checkpoint, metadata, new_versions):
    events.append(f"put step={metadata.get('step')} source={metadata.get('source')}")
    return real_put(config, checkpoint, metadata, new_versions)
def put_writes(config, writes, task_id, task_path=""):
    events.append(f"put_writes {[w[0] for w in writes][:3]}")
    return real_pw(config, writes, task_id, task_path)
saver.put, saver.put_writes = put, put_writes
import src.search as s
for t in s.search_tools:
    orig = t.func
    def wrap(*a, _o=orig, _n=t.name, **k):
        events.append(f"도구 {_n}")
        return _o(*a, **k)
    t.func = wrap
ctx = {"copilotkit": {"context": [{"description": "output_schema", "value": json.dumps(ui_schema.output_schema())}], "actions": []}}
async def run():
    await main.agent.ainvoke({"messages": [("user", "Research the best pizza in San Francisco")], **ctx}, {"configurable": {"thread_id": "cnt1"}})
asyncio.run(run())
for i, e in enumerate(events, 1):
    print(i, e)
print("put", sum(e.startswith("put ") for e in events), "put_writes", sum(e.startswith("put_writes") for e in events))
guard.report()
EOF
```

```bash
$PY count_put.py 57131
```

```text
1 put step=-1 source=input
2 put_writes ['messages', 'copilotkit', 'branch:to:normalize_context.before_agent']
3 put step=0 source=loop
4 put_writes ['copilotkit', 'branch:to:CopilotKitMiddleware.before_agent']
5 put step=1 source=loop
6 put_writes ['messages', 'copilotkit', 'branch:to:model']
7 put step=2 source=loop
8 put_writes ['messages', 'branch:to:CopilotKitMiddleware.after_model']
9 put step=3 source=loop
10 put_writes ['__pregel_tasks']
11 put step=4 source=loop
12 도구 search_internet
13 put_writes ['messages', 'branch:to:model']
14 put step=5 source=loop
15 put_writes ['messages', 'structured_response', 'branch:to:CopilotKitMiddleware.after_model']
16 put step=6 source=loop
17 put_writes ['branch:to:CopilotKitMiddleware.after_agent']
18 put step=7 source=loop
19 put_writes ['__no_writes__']
20 put step=8 source=loop
put 10 put_writes 9
가드: 루프백 밖으로 나가려던 시도 0건 []
```

`put` 10번과 `put_writes` 9번입니다. 입력 단계(step -1)와 루프 단계 0~8에서 한 번씩 `put`이 있고, 도구 호출을 예약하는 `__pregel_tasks` 쓰기와 마지막 `__no_writes__` 쓰기도 `put_writes`에 들어 있습니다. 위 여섯 그림의 `put`·`put_writes` 화살표를 세면 이 수와 같습니다. 이 값은 pizza 장면(모델 둘, 도구 하나) 기준이고, 도구를 더 부르면 단계가 늘어납니다. 그래서 Step 7의 `BoundedMemorySaver`가 스레드 하나에 남기는 `writes`·`blobs`도 이 횟수에 비례해 쌓입니다.

## 실행 체크리스트

- [ ] `agent/`에서 `uv sync --locked`가 끝나고 `copilotkit 0.1.78`·`ag-ui-langgraph 0.0.25`·`langchain 1.2.0`·`langgraph 1.0.7`이 나온다
- [ ] 열쇠를 지운 `nokey.py`가 `main.py:30`에서 멈추고 가드가 0건을 센다
- [ ] 가짜 서버와 에이전트 서버가 `127.0.0.1`에만 열려 있고 `//health`가 `{"status":"ok"...}`를 준다
- [ ] `ui_schema.py`가 부품 16개와 `$defs` 5개를 보여 준다
- [ ] 첫 요청에서 모델 요청의 메시지 순서가 `system, user, system`이고 `response_format`이 `strict=True`다
- [ ] 도구를 거친 요청이 모델 호출 두 번과 `/search` 한 번을 남기고, `/crawl`의 `max_depth`에 지시문이 들어간 것을 확인했다
- [ ] 두 번째 턴의 모델 요청에 `App Context`가 둘이다
- [ ] 패치를 끈 서버에서만 `ValueError: Message ID not found in history`가 난다
- [ ] 가짜 서버 기록에 `Bearer sk-fake`·`Bearer tvly-fa` 말고 다른 열쇠가 없고 `blocked.log`가 없다(셸에 프록시 변수를 건 채로도 같다)
- [ ] 띄운 서버(57131·57132·57133)를 모두 멈췄다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `OpenAIError: The api_key client option must be set...`, 멈춘 곳 `[30]` | `main.py:30`이 가져오는 순간 모델 클라이언트를 만든다 | 직접 확인. 서버는 `run_agent.py`로 띄운다(가드가 가짜 열쇠를 먼저 정한다) |
| `curl .../health`가 404 | 헬스 체크 주소가 `//health`다(`path="/"`에 `/health`를 이어 붙임) | 직접 확인. `//health`로 부른다 |
| `curl .../health`가 빈 줄과 `403` | 셸의 `HTTP(S)_PROXY`를 따라 프록시로 갔다 | 직접 확인. `curl --noproxy '*'`로 부른다(`drive.py`는 `ProxyHandler({})`로 이미 거치지 않는다) |
| 같은 스레드의 다음 요청(기록이 서버보다 짧을 때)에서 이벤트 0건, 서버 로그에 `ValueError: Message ID not found in history` | 클라이언트가 보낸 기록이 서버 체크포인트보다 짧아 "다시 만들기" 경로로 갔는데 패치가 꺼져 있다 | 직접 확인. `src/patches.py`의 `apply()`를 지우지 않는다(`run_unpatched.py`가 일부러 끈 것) |
| 모델의 답이 JSON이 아니면 서버 로그에 `StructuredOutputValidationError`, 스트림이 오류 신호 없이 끝남 | 마지막 답이 `response_format`을 따르지 않음 | 직접 확인. 앱에는 이를 처리하는 곳이 없다. 가짜 서버의 "bad json" 장면 |
| 같은 스레드에서 턴이 늘수록 요청이 커진다 | 턴마다 `App Context` 시스템 메시지가 하나씩 쌓인다 | 직접 확인. 더 해보기 참고 |
| 포트가 이미 쓰이고 있다고 나온다 | 흔한 포트와 겹침 | 49152~65535의 다른 번호로 바꾼다(문서의 57131~57133은 예시) |
| 파이썬 출력이 cp949로 깨진다 | 한국어 Windows 콘솔 | `PYTHONIOENCODING=utf-8`(Step 1) |
| `Row` 안의 부품이 넷째부터 안 보인다 | `layout.tsx:45`의 `[&>*:nth-child(n+4)]:hidden` | 소스로 확인(화면은 실행하지 못했다). 열 수를 셋 이하로 |

## 더 해보기

- `search.py:26`을 `crawl(website, instructions=instructions)`로 고친 복사본으로 `/crawl` 본문이 어떻게 바뀌는지 가짜 서버 기록에서 확인해 보세요. `extract_site`가 `urls` 인자로 문자열을 받는 것도 시그니처로 확인하세요.
- `App Context` 시스템 메시지가 쌓이지 않게 하려면 `normalize_context`에 이미 있는 `App Context:` 메시지를 상태에서 지우는 로직을 넣거나, 새 메시지에 이전 메시지의 `id`를 주면 됩니다. 어느 쪽이든 두 번째 턴의 모델 요청에서 `App Context`가 하나만 남는지 `show_requests.py`로 확인해 보세요.
- `BoundedMemorySaver.put`의 제거 부분을 `self.delete_thread(oldest_thread)`로 바꾸면 `writes`·`blobs`도 지워집니다. `saver_test.py`로 확인해 보세요. 그런 뒤에도 "그 스레드의 진행 중 요청"이 있을 때 안전한지는 따로 따져야 합니다.

## 다음 날 예고

[Day 148 · 📰 Always-on Hacker News Briefing Agent](../day148-always-on-hn-briefing-agent/README.md) — 볼륨 13 "🛰️ Always-on Agents"의 첫날입니다. `always_on_agents/always_on_hn_briefing_agent`는 Google ADK 에이전트(`agent.py` 46줄, `gemini-3-flash-preview`가 25행)가 Hacker News를 훑어 브리핑을 만들고, 수집·순위 코드(`scout.py` 388줄), 발송 코드(`delivery.py` 202줄), FastAPI 스케줄러 훅(`scheduler_api.py` 116줄)이 이를 받칩니다. 사람이 열어 둔 화면 없이 스케줄러가 깨우는 백엔드라는 점이 볼륨 12와 다르고, 앱 README는 기본이 dry-run이라 자격 증명을 따로 설정하지 않으면 발송하지 않는다고 적습니다.
