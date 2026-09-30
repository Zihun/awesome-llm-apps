# Day 097 · 📡 Earnings Call Analyst Agent

> 볼륨 7 🚀 Advanced AI Agents · 난이도 ★★★ · 예상 소요 125분(그림이 서른 장이고 확인 명령이 열다섯 개라 읽고 돌려 보는 시간이 깁니다) · API 비용 대략 (키 없이는 무료 — 이 문서의 확인은 모두 그렇습니다. 키가 있으면 분석 한 번에 Gemini를 세 번 안팎 부릅니다: 회사 정체 추론 1회, 뉴스 검색 1회(티커를 찾았을 때만), 분석가 카드 1회, 자막이 없으면 오디오 5분 조각마다 1회 더. 대략치이고 단가는 확인하지 못했습니다) · 원본 앱: `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent`

## 오늘 만들 것

실적 발표(earnings call) YouTube 영상의 URL을 붙여 넣으면 서버가 자막을 가져오고(없으면 오디오를 Gemini로 전사) 회사·티커·회계기간을 추정해 SEC 제출 목록과 뉴스를 모은 "리서치 팩"을 만듭니다. 그다음 분석가 에이전트가 자막에서 투자자에게 의미 있는 발언을 골라 시각과 인용문이 붙은 카드로 돌려주고, 브라우저는 영상이 그 시각에 닿을 때 카드를 공개합니다.

이름은 "단일 에이전트"지만 ADK `LlmAgent`가 넷 있고(직접 확인, Step 1) 서로를 부르지 않습니다. 순수 파이썬 코드가 `adk_runtime.py`의 실행 함수로 하나씩 돌립니다. 이 볼륨의 여섯 번째 google-adk 앱(088·091·092·094·095 다음)이라 `LlmAgent`는 [Day 014](../day014-adk-1-starter-agent/README.md), `Runner`는 [Day 018](../day018-adk-5-memory-agent/README.md)에 맡기고, 오늘은 이 앱만의 것 — 조용히 물러나는 자격증명 문지기, 소리 없이 버려지는 카드, 검증 없는 인용문 앵커링, 폴링 서버 — 을 봅니다.

이 문서의 확인 명령은 YouTube·SEC·Gemini에 요청을 보내지 않습니다(Step 7에서 브라우저로 화면을 여는 일만 예외이고, 그 절에 적었습니다). 확인은 손으로 쓴 가짜 자막과 가짜 응답으로 했고 "Example Corp(EXM)"은 지어낸 회사입니다. 카드는 LLM이 쓴 글이라 권위가 없고, 앱의 코드·화면·README 어디에도 투자 조언이 아니라는 문구가 없습니다(`advice`·`disclaim`·`not financial`을 소스에서 검색해 확인). 이 앱의 출력을 투자 판단에 쓰지 마세요.

![완성 아키텍처](diagrams/overview.svg)

이 그림은 관계마다 화살표를 하나만 그렸습니다. 사용자 쪽은 화면이 보여 주는 방향, 서버 쪽은 요청 방향입니다. 되돌아오는 방향까지 화살표 넷으로 그린 그림은 아래 "아키텍처 한눈에 보기"에 있습니다.

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Gemini 인증 (선택) | 정체 추론·뉴스 검색·분석 카드·오디오 전사, 네 호출의 인증. 없어도 서버는 뜨고 이 문서의 확인은 모두 되지만 카드는 0장입니다(Step 2·6) | `GOOGLE_API_KEY`(`GEMINI_API_KEY`도 받습니다) — https://aistudio.google.com/ 에서 발급. 또는 Vertex AI: `GOOGLE_GENAI_USE_VERTEXAI=True` + `GOOGLE_CLOUD_PROJECT` |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| ffmpeg (선택) | 자막이 없을 때 오디오를 300초 조각으로 자릅니다. 없으면 원본 오디오를 한 조각으로 보냅니다(`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/youtube_ingest.py:307-309`) | https://ffmpeg.org/ 에서 설치 |
| 브라우저 + 인터넷 | 화면이 `https://www.youtube.com/iframe_api`를 브라우저에서 직접 불러옵니다(`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/index.html:90`). 실제로 영상을 분석하면 YouTube·SEC·Gemini에 요청이 나갑니다 | 별도 설치 없음 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 프런트엔드 (app.js) | URL 제출, 1.5초 폴링, YouTube 플레이어 마운트, 재생 시각에 맞춘 카드 공개 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/app.js:73-136`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/app.js:250-266` |
| FastAPI 세션 서버 (server.py) | 세션 생성·조회 API, 백그라운드 분석 `_run_session`, `.env` 로더, 정적 파일 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/server.py:24-36`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/server.py:102-132`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/server.py:135-192` |
| 세션 저장소 (sessions) | 프로세스 메모리의 dict와 `RuntimeSession` — 재시작하면 사라지고 지워지지도 않음 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/server.py:60-73` |
| 영상 수집 (youtube_ingest.py) | URL→영상 ID, oEmbed 메타데이터, 자막, 자막이 없으면 yt-dlp + Gemini 전사, 청크 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/youtube_ingest.py:52-132`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/youtube_ingest.py:148-234`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/youtube_ingest.py:261-289` |
| 리서치 팩 (research.py) | 회사 정체 추론, SEC 제출 목록, 뉴스 검색 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/research.py:50-85`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/research.py:88-231` |
| 분석가 (agent.py) | 청크 고르기, 카드 생성·검증, 인용문 시각 맞추기 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/agent.py:41-145`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/agent.py:216-277` |
| ADK 실행기 (adk_runtime.py) | 에이전트를 한 번 돌려 마지막 텍스트를 돌려주는 래퍼, 자격증명 판정, JSON 파서 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/adk_runtime.py:23-67`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/adk_runtime.py:81-110` |
| ADK 에이전트 4개 | `root_agent`·`identity_agent`·`market_news_agent`·`transcription_agent`, 각각 임포트 때 만들어짐 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/agent.py:23-38`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/research.py:20-47`, `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/youtube_ingest.py:32-49` |
| 스키마 (schemas.py) | 세그먼트·청크·카드·리서치 팩·세션의 pydantic 모델 | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/schemas.py:20-115` |
| Gemini · YouTube · SEC EDGAR · YouTube 플레이어 | 외부 서비스. 앱은 요청만 보내고 결과는 검증하지 않습니다 | 코드 없음 (외부 서비스) |

개요 그림은 화면 쪽 관계를 한 방향씩만 그렸습니다. 서로 다른 데이터를 나르는 두 방향을 화살표 넷으로 따로 그리면 아래와 같습니다. 사용자는 URL과 버튼 클릭을 화면에 넣고, 화면은 진행 막대·리서치 팩·카드를 보여 줍니다. 화면은 `/health`와 세션 API를 요청하고, 서버는 화면 파일과 JSON으로 답합니다.

![화면과 서버가 주고받는 것](diagrams/extra-structure.svg)

개요 그림에서 Gemini로 가는 세 화살표(ADK)는 모두 아래 경로를 지납니다. 에이전트 넷은 `run_adk_agent_text`·`run_adk_agent_content`를 거치고, 이 함수가 호출마다 새 `InMemorySessionService`와 `Runner`를 만듭니다. 서버도 같은 모듈의 `has_adk_credentials()`·`adk_auth_mode()`를 불러 `/health` 응답과 결과 진단 값을 정합니다(Step 2, Step 6).

![ADK 에이전트 배선](diagrams/extra-agents.svg)

## 단계별 진행

### Step 1. 환경 만들기 — 패키지는 부모 폴더에서 임포트한다

**목적.** 앱 폴더에 가상환경을 만들고, 소스가 컴파일되며 에이전트 넷이 임포트만으로 만들어지는 것을 확인합니다.

**할 일.**

```bash
cd advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent
uv venv
uv pip install -r requirements.txt
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Windows PowerShell은 활성화만 `.venv\Scripts\Activate.ps1`로 바꿉니다.)

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/requirements.txt:1-9`

```text
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
requests>=2.31.0
youtube-transcript-api>=0.6.2
yt-dlp>=2025.12.8
google-genai>=1.0.0
google-adk>=1.0.0
pytest>=8.0.0
```

전부 `>=`뿐이라 설치 시점의 최신이 들어옵니다(받은 버전은 아래 출력의 첫 줄). 이 저장소는 루트에 `pyproject.toml`이 있어 이후 `uv run`에는 모두 `--no-project`를 붙입니다.

소스는 `from .adk_runtime import …`처럼 상대 임포트라 앱 폴더 안에서는 임포트할 수 없습니다 — `python -c "import agent"`는 `ImportError: attempted relative import with no known parent package`로 멈춥니다(직접 확인). 부모 폴더 `single_agent_apps`에서 실행하고, 자식 폴더의 가상환경은 Day 088처럼 `--python`으로 가리킵니다.

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 앱 폴더에서 컴파일하고, 부모 폴더로 나가 에이전트를 임포트합니다.

```bash
uv run --no-project python -m py_compile __init__.py adk_runtime.py agent.py research.py schemas.py youtube_ingest.py live_demo/server.py
```

`py_compile`은 아무것도 출력하지 않습니다(직접 확인).

```bash
cd ..
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
from importlib.metadata import version
from earnings_call_analyst_agent import agent, research, youtube_ingest

print(*[name + ' ' + version(name) for name in ['google-adk', 'google-genai', 'fastapi', 'youtube-transcript-api']])
for a in (agent.root_agent, research.identity_agent, research.market_news_agent, youtube_ingest.transcription_agent):
    print(type(a).__name__, a.name, a.model)
"
```

직접 확인한 출력(첫 줄은 이 문서를 쓰며 실제로 설치된 버전):

```text
google-adk 2.10.0 google-genai 2.25.0 fastapi 0.141.1 youtube-transcript-api 1.2.4
LlmAgent earnings_call_analyst_agent gemini-3-flash-preview
LlmAgent earnings_identity_agent gemini-3-flash-preview
LlmAgent earnings_market_news_agent gemini-2.5-flash
LlmAgent earnings_audio_transcription_agent gemini-3-flash-preview
```

임포트만으로 `LlmAgent`가 넷 만들어집니다 — `agent.py`에 하나, `research.py`에 둘, `youtube_ingest.py`에 하나. 모델은 `EARNINGS_GEMINI_MODEL`(기본 `gemini-3-flash-preview`), 뉴스 검색만 `EARNINGS_SEARCH_GEMINI_MODEL`(`gemini-2.5-flash`), 오디오 전사는 `EARNINGS_TRANSCRIPT_MODEL`로 바꿉니다. 세 파일 모두 생성을 `try/except Exception`으로 감싸, 실패하면 예외 없이 `None`이 되고 그 기능이 조용히 꺼집니다(`agent.py:23-38`).

### Step 2. 자격증명 문지기와 ADK 실행기

**목적.** 모든 Gemini 호출이 지나가는 `adk_runtime.py`를 읽고, 자격증명이 없을 때 앱이 어떻게 조용히 물러나는지, `.env` 기본값이 이 문지기를 어떻게 속이는지 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/adk_runtime.py:81-96`

```python
def has_adk_credentials() -> bool:
    _ensure_google_api_key_alias()
    if os.getenv("GOOGLE_API_KEY"):
        return True
    if not _env_truthy("GOOGLE_GENAI_USE_VERTEXAI"):
        return False
    return bool(os.getenv("GOOGLE_CLOUD_PROJECT"))


def adk_auth_mode() -> str:
    _ensure_google_api_key_alias()
    if os.getenv("GOOGLE_API_KEY"):
        return "api_key"
    if _env_truthy("GOOGLE_GENAI_USE_VERTEXAI") and os.getenv("GOOGLE_CLOUD_PROJECT"):
        return "vertex_ai"
    return "missing"
```

`GOOGLE_API_KEY`(`GEMINI_API_KEY`도 별칭, `adk_runtime.py:76-78`)가 있거나 Vertex 플래그가 참이고 `GOOGLE_CLOUD_PROJECT`가 비어 있지 않으면 통과입니다. **값이 진짜인지는 보지 않습니다.** 거짓이면 앱이 조용히 물러납니다. 정체 추론은 휴리스틱으로(`research.py:90-91`), 뉴스와 분석 카드는 빈 목록으로(`research.py:169-170`, `agent.py:48-52`) 가고 오디오 전사만 예외를 던집니다(`youtube_ingest.py:151-154`). 키 없는 서버가 에러 없이 카드 0장짜리 "완료"를 내는 까닭입니다(Step 6). 키가 있어도 모델 호출이 실패하면 같은 모양이 됩니다(Step 5).

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/.env.example:1-4`

```text
# Option 1: Vertex AI / Google Cloud
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=your-google-cloud-project-id
GOOGLE_CLOUD_LOCATION=global
```

기본 파일은 Vertex AI(Option 1)가 **켜져** 있고 프로젝트가 자리표시자입니다. 그대로 복사해도 문지기는 통과합니다(아래 첫 출력). `.env`는 python-dotenv 없이 `server.py`가 읽는데 `setdefault`라 같은 키가 두 번이면 **첫 줄이 이깁니다**.

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/server.py:24-36`

```python
def _load_env() -> None:
    env_path = APP_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env()
```

이 로더는 `agent.py` 등을 임포트하기 전에(`server.py:38-49`) 돌아야 합니다. 세 파일이 모델 이름과 조각 길이를 임포트 시점에 한 번만 읽기 때문입니다.

실행은 `run_adk_agent_content_async`(`adk_runtime.py:23-63`)가 맡습니다. 호출마다 새 `InMemorySessionService`와 `Runner`를 만들고 `run_async`를 돌며 텍스트가 든 **마지막 이벤트**의 글을 돌려줍니다(Runner는 Day 018, `run_async` 소비는 Day 094에서 다뤘습니다). 동기 `run_adk_agent_text`는 `asyncio.run`으로 감싸(`adk_runtime.py:66-67`) 이벤트 루프가 도는 스레드에서는 부를 수 없습니다. 서버가 모든 단계를 `asyncio.to_thread`로 부르는 까닭입니다(Step 6). 이 실행기는 개요 그림에 없고 위 "ADK 에이전트 배선" 그림의 가운데 상자입니다. 아래 그림에서 새로 켜지는 것은 실행기가 부르는 Gemini입니다.

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** 세 명령입니다. 환경 조합별 판정, 임시 폴더의 `.env`로 첫 줄 우선 확인(앱 폴더의 `.env`는 건드리지 않습니다), LLM 없이 로컬 에이전트를 이 래퍼에 통과시키기. 모두 부모 폴더에서 실행합니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
import os
from earnings_call_analyst_agent.adk_runtime import has_adk_credentials, adk_auth_mode

cases = [{}, {'GEMINI_API_KEY': 'x'}, {'GOOGLE_GENAI_USE_VERTEXAI': 'True', 'GOOGLE_CLOUD_PROJECT': 'your-google-cloud-project-id'}]
for env in cases:
    for name in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_GENAI_USE_VERTEXAI', 'GOOGLE_CLOUD_PROJECT']:
        os.environ.pop(name, None)
    os.environ.update(env)
    print(sorted(env), '->', has_adk_credentials(), adk_auth_mode())
"
```

직접 확인한 출력:

```text
[] -> False missing
['GEMINI_API_KEY'] -> True api_key
['GOOGLE_CLOUD_PROJECT', 'GOOGLE_GENAI_USE_VERTEXAI'] -> True vertex_ai
```

`.env.example` 값 그대로도 `True vertex_ai`입니다. 자리표시자 프로젝트도 통과합니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
import os, tempfile
from pathlib import Path
from earnings_call_analyst_agent.live_demo import server

with tempfile.TemporaryDirectory() as tmp:
    Path(tmp, '.env').write_text('GOOGLE_GENAI_USE_VERTEXAI=True\nGOOGLE_API_KEY=fixture-key\nGOOGLE_GENAI_USE_VERTEXAI=False\n')
    server.APP_DIR = Path(tmp)
    for name in ['GOOGLE_GENAI_USE_VERTEXAI', 'GOOGLE_API_KEY']:
        os.environ.pop(name, None)
    server._load_env()
print(os.environ['GOOGLE_GENAI_USE_VERTEXAI'], os.environ['GOOGLE_API_KEY'])
"
```

직접 확인한 출력:

```text
True fixture-key
```

뒤의 `False`가 무시되어 Vertex 플래그가 `True`로 남습니다. google-genai 2.25.0 소스(`BaseApiClient.__init__`)는 환경변수의 프로젝트와 API 키가 함께 있으면 프로젝트를 고르므로, 이 상태에서는 키를 넣어도 Vertex로 가는데 `adk_auth_mode()`는 `api_key`라고 답합니다(소스로 확인).

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types
from earnings_call_analyst_agent.adk_runtime import run_adk_agent_text

class Echo(BaseAgent):
    async def _run_async_impl(self, ctx):
        text = ctx.user_content.parts[0].text
        for label in ['draft', 'final']:
            yield Event(author=self.name, content=types.Content(role='model', parts=[types.Part(text=label + ': ' + text)]))

print(run_adk_agent_text(Echo(name='echo_agent'), 'hello'))
"
```

직접 확인한 출력:

```text
final: hello
```

첫 이벤트(`draft: hello`)는 버려지고 마지막 이벤트의 글이 돌아옵니다. 네 에이전트 모두 이 반환값을 `parse_json_object`로 JSON으로 읽습니다(`adk_runtime.py:99-110`).

### Step 3. 영상 수집 — URL에서 자막과 청크까지

**목적.** URL이 영상 ID·자막·청크가 되는 길을 확인하고, 이 앱이 의존하는 `youtube-transcript-api`가 1.2.0 이상(오늘 설치된 1.2.4)일 때 코드의 두 경로 중 어느 쪽이 도는지 봅니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/youtube_ingest.py:98-132`

```python
def fetch_transcript(video_id: str) -> list[TranscriptSegment]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise RuntimeError(
            "Missing youtube-transcript-api. Install requirements.txt before running the app."
        ) from exc

    try:
        items = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
    except AttributeError:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "en-US"])
        items = [
            {
                "start": snippet.start,
                "duration": snippet.duration,
                "text": snippet.text,
            }
            for snippet in fetched
        ]
    except Exception as exc:
        raise RuntimeError(
            "Could not load captions for this video. Try a YouTube earnings call with English captions."
        ) from exc

    return [
        TranscriptSegment(
            start=float(item.get("start", 0)),
            duration=float(item.get("duration", 0)),
            text=" ".join(str(item.get("text", "")).replace("\n", " ").split()),
        )
        for item in items
        if str(item.get("text", "")).strip()
    ]
```

`extract_video_id`(`youtube_ingest.py:52-73`)는 11자 ID나 `watch?v=`·`youtu.be`·`/live/`·`/embed/`·`/shorts/` URL만 받고 아니면 `ValueError`를 냅니다. 호스트 검사가 `endswith("youtube.com")`이라 `evilyoutube.com`도 통과합니다. oEmbed 요청이 실패하면 예외를 삼키고 제목을 "Untitled earnings call"로 두니(`youtube_ingest.py:76-95`) 제목이 없어도 파이프라인은 계속됩니다.

자막은 위 발췌대로 옛 `get_transcript`를 먼저 시도하고 `AttributeError`면 새 `fetch`로 갑니다. `requirements.txt`가 `>=0.6.2`라 오늘은 1.2.4가 설치되고, 여기에는 `get_transcript`가 없어 언제나 둘째 경로입니다. 그런데 `fetch`가 던진 예외는 `except AttributeError:` 핸들러 **안에서** 난 것이라 같은 `try`의 `except Exception`에 잡히지 않습니다. "자막을 못 불렀다"는 친절한 `RuntimeError`(`youtube_ingest.py:119-122`)는 1.2.0 이상에서는 나올 수 없고 원래 예외가 나갑니다. 1.2.0 미만은 다릅니다. 1.0.3(`_api.py:268`)과 1.1.1(`_api.py:255`) 휠에는 폐기 예고된 `get_transcript`가 남아 있어 첫 경로가 돌고, 그 안의 실패는 `except Exception`이 잡아 이 `RuntimeError`가 나옵니다(두 휠을 받아 소스를 읽고, 같은 스텁으로 두 경우를 돌려 확인). `>=0.6.2`라 오래된 환경에는 1.2.0 미만이 남아 있을 수 있습니다. 서버는 어떤 예외든 잡아 오디오 전사로 넘어갑니다(`server.py:146`).

`chunk_transcript`(`youtube_ingest.py:261-289`)는 조각을 `window_seconds`(서버는 42, 기본 45)를 넘기 전까지 묶습니다. 오디오 폴백 `transcribe_audio_with_adk`(`youtube_ingest.py:148-234`)는 YouTube 다운로드와 Gemini 호출이 필요해 이 문서에서 실행하지 않았습니다(흐름은 아래 시퀀스 그림). 같은 폴백을 한 함수로 묶은 `load_transcript`(`youtube_ingest.py:135-145`)는 서버가 부르지 않고 테스트만 부릅니다(소스 검색으로 확인).

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 부모 폴더에서 실행합니다. 첫 명령은 URL 검사, `get_transcript` 유무, 손으로 쓴 조각을 `fetch` 대신 끼워 넣은 결과, 청크 자르기를 한 번에 봅니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
from types import SimpleNamespace as NS
from youtube_transcript_api import YouTubeTranscriptApi
from earnings_call_analyst_agent import youtube_ingest as yi

for value in ['https://youtu.be/abcDEF12345?t=120', 'https://www.youtube.com/live/abcDEF12345', 'https://evilyoutube.com/watch?v=abcDEF12345', 'https://example.com/x']:
    try:
        print(yi.extract_video_id(value))
    except ValueError as exc:
        print('ValueError:', exc)

print(hasattr(YouTubeTranscriptApi, 'get_transcript'), hasattr(YouTubeTranscriptApi, 'fetch'))
YouTubeTranscriptApi.fetch = lambda self, video_id, languages=('en',): [
    NS(text='Revenue grew\nfast', start=12.0, duration=4.5),
    NS(text='   ', start=17.0, duration=1.0),
    NS(text='Margins  expanded', start=18.0, duration=3.0),
]
segments = yi.fetch_transcript('abcDEF12345')
for s in segments:
    print(s.start, s.duration, repr(s.text))
for c in yi.chunk_transcript(segments, window_seconds=5):
    print(c.start, c.end, len(c.segments))
"
```

직접 확인한 출력:

```text
abcDEF12345
abcDEF12345
abcDEF12345
ValueError: Enter a valid YouTube URL or 11-character video id.
False True
12.0 4.5 'Revenue grew fast'
18.0 3.0 'Margins expanded'
12.0 16.5 1
18.0 21.0 1
```

앞 네 줄이 URL 검사(셋째 줄이 `evilyoutube.com`), `False True`가 옛 메서드는 없고 새 메서드는 있다는 뜻입니다. 공백뿐인 조각은 버려지고 나머지는 줄바꿈·이중 공백이 정리되며, 마지막 두 줄은 5초 창으로 자른 청크의 시작·끝·조각 수입니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
from youtube_transcript_api import YouTubeTranscriptApi
from earnings_call_analyst_agent import youtube_ingest as yi

def unreachable(self, *args, **kwargs):
    raise ConnectionError('captions endpoint unreachable (stub)')

YouTubeTranscriptApi.fetch = unreachable
try:
    yi.fetch_transcript('abcDEF12345')
except Exception as exc:
    print(type(exc).__name__, '|', exc)
"
```

직접 확인한 출력:

```text
ConnectionError | captions endpoint unreachable (stub)
```

설치된 1.2.4에서는 친절한 `RuntimeError` 대신 스텁이 던진 원래 예외가 나옵니다.

### Step 4. 리서치 팩 — 정체 추론, SEC, 뉴스

**목적.** `build_research_pack`이 회사 정체 → SEC 제출 목록 → 뉴스를 모으고, 무엇이든 풀리지 않으면 예외 대신 `notes`를 남기는 것을 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/research.py:50-85`

```python
def build_research_pack(
    metadata: VideoMetadata, transcript: list[TranscriptSegment], max_news: int = 8
) -> ResearchPack:
    sample = " ".join(segment.text for segment in transcript[:24])
    identity = infer_company_identity(metadata.title, metadata.author_name, sample)
    ticker = str(identity.get("ticker") or "").upper().strip()
    company = str(identity.get("company") or "").strip() or _clean_company_name(metadata)

    documents: list[ResearchDocument] = []
    notes: list[str] = []

    if ticker:
        sec_docs, sec_notes = fetch_sec_documents(ticker)
        documents.extend(sec_docs)
        notes.extend(sec_notes)

    news = fetch_market_news(ticker, company, max_news=max_news) if ticker else []
    peers = identity.get("peers", [])
    if not isinstance(peers, list):
        peers = []

    if not documents:
        notes.append("No SEC filing links were resolved automatically.")
    if not news:
        notes.append("No recent market headlines were resolved automatically.")

    return ResearchPack(
        company=company,
        ticker=ticker,
        fiscal_period=str(identity.get("fiscal_period") or ""),
        confidence=float(identity.get("confidence", 0.35)),
        documents=documents,
        peers=[str(peer).upper().strip() for peer in peers if str(peer).strip()][:8],
        news=news,
        notes=notes,
    )
```

정체 추론은 두 겹입니다. 정규식이 제목·채널·자막 앞 1,200자에서 티커(`(EXM)`, `NYSE: EXM`, `NASDAQ: EXM`)와 분기를 뽑고(`research.py:260-279`), 자격증명이 있으면 `identity_agent`의 답이 그 위에 덮어씁니다(`research.py:88-110`). 정규식은 괄호 안 대문자 1~5자를 전부 티커로 보므로 "Jane Doe (CFO)"의 `CFO`도 티커가 됩니다(아래 확인).

티커가 나오면 `fetch_sec_documents`(`research.py:113-159`)가 SEC 티커 표(`lru_cache`로 한 번만)에서 CIK를 찾고 10-K·10-Q·8-K 각각 가장 최근 것 하나씩, 최대 셋의 URL을 만듭니다. 뉴스는 `market_news_agent`가 `google_search` 그라운딩으로 찾은 항목 중 URL이 있고 겹치지 않는 것만 남기며(`research.py:166-231`) 제목 끝이 ` - moomoo`·` - reddit`·` - stocktwits`인 것을 거릅니다(`research.py:234-237`). `google_search`가 `GoogleSearchTool` 객체라는 것은 [Day 017](../day017-adk-4-tool-using-agent/README.md) Step 2에서 확인했습니다. `notes`는 화면에 나오지 않고(`app.js`에 `notes` 참조가 없음 — 소스 검색으로 확인) 분석가 프롬프트의 `Notes:` 줄로만 갑니다(`agent.py:177-188`).

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 부모 폴더에서 실행합니다. 첫 명령은 진짜 함수 그대로이고, 티커가 없어 SEC·뉴스 조회가 건너뛰어지므로 네트워크가 필요 없습니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
import os
from earnings_call_analyst_agent import research
from earnings_call_analyst_agent.schemas import TranscriptSegment, VideoMetadata

for name in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_GENAI_USE_VERTEXAI', 'GOOGLE_CLOUD_PROJECT']:
    os.environ.pop(name, None)
meta = VideoMetadata(video_id='abcDEF12345', title='Weekly market chat', author_name='Some Channel')
pack = research.build_research_pack(meta, [TranscriptSegment(start=0, duration=3, text='Hello everyone')])
print(pack.model_dump())
print(research._infer_identity_heuristically('Example Q3 call', 'IR', 'Thanks Jane Doe (CFO) and good afternoon')['ticker'])
"
```

직접 확인한 출력:

```text
{'company': 'Weekly market chat', 'ticker': '', 'fiscal_period': '', 'confidence': 0.25, 'documents': [], 'peers': [], 'news': [], 'notes': ['No SEC filing links were resolved automatically.', 'No recent market headlines were resolved automatically.']}
CFO
```

`notes` 두 줄만 남았고, 마지막 줄 `CFO`가 오탐 예시입니다. 둘째 명령은 SEC 응답을 손으로 쓴 가짜 데이터로 바꿔 끼워(`requests.get`을 `MagicMock`으로) 파싱만 확인합니다. 회사와 CIK는 지어낸 값입니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
from unittest.mock import MagicMock, patch
from earnings_call_analyst_agent import research

filings = {'filings': {'recent': {
    'form': ['8-K', '10-Q', '8-K', '10-K', 'S-8'],
    'accessionNumber': ['0000012345-25-000031', '0000012345-25-000030', '0000012345-25-000020', '0000012345-25-000010', '0000012345-25-000005'],
    'primaryDocument': ['ex99.htm', 'q3.htm', 'old8k.htm', 'annual.htm', 's8.htm'],
    'filingDate': ['2025-11-04', '2025-11-03', '2025-08-01', '2025-02-20', '2025-01-10'],
}}}
response = MagicMock()
response.json.return_value = filings
with patch.object(research, 'ticker_to_cik', return_value='0000012345'), patch.object(research.requests, 'get', return_value=response) as get:
    docs, notes = research.fetch_sec_documents('EXM')
print(get.call_args.args[0])
for d in docs:
    print(d.kind, d.url)
print(notes)
"
```

직접 확인한 출력:

```text
https://data.sec.gov/submissions/CIK0000012345.json
8-K https://www.sec.gov/Archives/edgar/data/12345/000001234525000031/ex99.htm
10-Q https://www.sec.gov/Archives/edgar/data/12345/000001234525000030/q3.htm
10-K https://www.sec.gov/Archives/edgar/data/12345/000001234525000010/annual.htm
[]
```

요청 URL은 10자리 CIK이고, 8-K는 가장 최근 것 하나만(`old8k.htm` 제외) 남고 `S-8`은 무시되며, 문서 URL의 CIK는 `int()`로 앞의 0을 뗍니다.

### Step 5. 분석가 — 청크 고르기, 카드 검증, 인용문 시각 맞추기

**목적.** 카드가 만들어지는 세 단계를 가짜 모델 응답으로 확인하고, "인용문에 앵커된 카드"가 무엇을 보증하고 무엇을 보증하지 않는지 봅니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/agent.py:41-52`

```python
def generate_insights(
    metadata: VideoMetadata,
    research: ResearchPack,
    chunks: list[TranscriptChunk],
    max_chunks: int = 64,
) -> list[InsightEvent]:
    selected = select_signal_chunks(chunks, limit=max_chunks)
    if has_adk_credentials() and root_agent is not None:
        insights = _generate_with_adk(metadata, research, selected)
        if insights:
            return sorted(_realign_event_times(insights, selected))
    return []
```

자격증명이 없으면 곧바로 `[]`입니다(테스트가 못 박습니다 — `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/tests/test_core_contracts.py:209-222`). 청크는 `select_signal_chunks`(`agent.py:55-63`)가 고릅니다. 청크마다 `revenue`·`guidance`·`margin` 같은 스무 개 키워드가 나온 횟수와 숫자 8개당 1점(최대 6)으로 점수를 매기고(`agent.py:148-174`) 앞 네 청크에 3점을 더해 상위 64개를 시간순으로 되돌립니다. 키워드는 `lower.count(term)`이라 낱말 경계 없이 세므로 `ai`는 "remain" 안의 `ai`도 셉니다(소스로 확인, 더 해보기).

모델은 프롬프트(`agent.py:77-110`)대로 `{"insights": [...]}` JSON만 돌려주어야 하고, 아래 발췌가 그 답을 받습니다. 소리 없이 물러나는 곳이 둘 있습니다.

첫째는 모델 호출입니다(`agent.py:111-114`). 호출이 예외를 던지면(키나 프로젝트가 틀렸거나, 모델 이름이 폐기됐거나, 할당량이 찼거나) `except Exception: return []`가 삼켜 카드 0장이 됩니다. 응답이 JSON이 아니어도 `parse_json_object`가 `{}`를 돌려줘 결과가 같습니다. 문지기는 이미 통과한 뒤라 이때도 진단의 `analysis_engine`은 `adk`입니다(아래 확인과 Step 6). 정체 추론(`research.py:103-108`)과 뉴스 검색(`research.py:196-199`)의 모델 호출도 같은 식으로 삼켜져, 각각 휴리스틱 결과만, 빈 뉴스만 남습니다.

둘째는 카드마다 pydantic 모델(`schemas.py:37-77`)로 검증하는 `except Exception: continue`(`agent.py:143-144`)입니다. 검증에 걸린 카드는 예외도 로그도 없이 사라집니다. 소스로 보면 `severity`가 `high`·`medium`·`low`가 아닌 것, `confidence`가 0~1 밖인 것, `mini_viz.rows`에 숫자가 든 것(문자열이어야 합니다), `citations`에 `label`이 없는 것, `start_time`이 숫자가 아닌 것이 여기서 버려집니다. 제목이나 인용문이 비었거나(`agent.py:145`) (에이전트, 반올림한 시각, 소문자 제목)이 같은 카드는(`agent.py:191-200`) 그 뒤에서 걸러집니다. 반대로 `agent`는 여섯 이름이 아니어도 통과합니다(`Union[AgentName, str]`).

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/agent.py:111-145`

```python
    try:
        payload = parse_json_object(run_adk_agent_text(root_agent, prompt))
    except Exception:
        return []

    raw_insights = payload.get("insights", [])
    if not isinstance(raw_insights, list):
        return []

    events: list[InsightEvent] = []
    for raw in raw_insights:
        if not isinstance(raw, dict):
            continue
        try:
            event_id = raw.get("id") or _event_id(raw)
            mini_raw = raw.get("mini_viz") if isinstance(raw.get("mini_viz"), dict) else {}
            citations_raw = raw.get("citations") if isinstance(raw.get("citations"), list) else []
            events.append(
                InsightEvent(
                    id=event_id,
                    start_time=float(raw.get("start_time", 0)),
                    end_time=float(raw.get("end_time", raw.get("start_time", 0))),
                    agent=str(raw.get("agent", "market_narrator")),
                    severity=raw.get("severity", "low"),
                    headline=str(raw.get("headline", "")).strip()[:180],
                    quote=str(raw.get("quote", "")).strip()[:500],
                    confidence=float(raw.get("confidence", 0.5)),
                    explanation=str(raw.get("explanation", "")).strip()[:600],
                    mini_viz=MiniVisualization(**mini_raw),
                    citations=[Citation(**item) for item in citations_raw if isinstance(item, dict)],
                )
            )
        except Exception:
            continue
    return _dedupe_events([event for event in events if event.headline and event.quote])
```

살아남은 카드의 시각은 모델이 준 값이 아니라 `_realign_event_times`(`agent.py:216-242`)가 자막 조각에 맞춰 다시 정합니다. `_best_quote_segment`(`agent.py:245-277`)가 인용문과 각 조각의 낱말 겹침·앞부분 일치·시각 차이 등으로 가장 좋은 조각을 고르면 카드의 시작이 그 조각 시작보다 0.35초 앞으로, 끝이 조각 끝으로 옮겨집니다. 점수가 0.22 미만이면 모델이 준 시각에서 가장 가까운 조각으로 갑니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 부모 폴더에서 실행합니다. 모델 호출(`run_adk_agent_text`)을 손으로 쓴 JSON을 돌려주는 가짜로 바꿔 끼우므로 Gemini 요청은 나가지 않습니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
import json
from unittest.mock import patch
from earnings_call_analyst_agent import agent
from earnings_call_analyst_agent.schemas import ResearchPack, TranscriptSegment, VideoMetadata
from earnings_call_analyst_agent.youtube_ingest import chunk_transcript

lines = [(0, 4, 'Welcome to the Example Corp third quarter 2025 earnings call.'),
         (12, 6, 'Revenue grew twelve percent year over year to 4.2 billion dollars.'),
         (19, 6, 'Gross margin expanded eighty basis points as pricing held up.')]
chunks = chunk_transcript([TranscriptSegment(start=s, duration=d, text=t) for s, d, t in lines], window_seconds=42)

def card(kind, headline, quote, start=0, **extra):
    return {'start_time': start, 'end_time': start + 4, 'agent': kind, 'severity': 'medium', 'headline': headline, 'quote': quote, 'confidence': 0.8, **extra}

fake = {'insights': [
    card('numbers_reconciler', 'Revenue growth called out', 'Revenue grew twelve percent year over year'),
    card('cfo_tone', 'Severity outside the Literal', 'Gross margin expanded', severity='critical'),
    card('surprise_detector', 'Row value is a number', 'Gross margin expanded', mini_viz={'rows': [['Margin', 80]]}),
    card('filing_grounder', 'Quote that is not in the transcript', 'Guidance was raised to fifteen percent', start=20),
    card('filing_grounder', 'QUOTE THAT IS NOT IN THE TRANSCRIPT', 'duplicate of the card above', start=20.2),
]}
with patch.object(agent, 'has_adk_credentials', return_value=True), patch.object(agent, 'run_adk_agent_text', return_value=json.dumps(fake)):
    cards = agent.generate_insights(VideoMetadata(video_id='abcDEF12345', title='Example Q3 earnings call'), ResearchPack(company='Example Co', ticker='EXM'), chunks)
print(len(cards), 'of', len(fake['insights']))
for c in cards:
    print(round(c.start_time, 2), round(c.end_time, 2), c.agent, '|', c.quote)
"
```

직접 확인한 출력:

```text
2 of 5
11.65 18.0 numbers_reconciler | Revenue grew twelve percent year over year
11.65 18.0 filing_grounder | Guidance was raised to fifteen percent
```

카드 다섯 장 중 둘만 남았습니다. 사라진 셋은 `severity: critical`, 숫자가 든 `rows`, 앞 카드와 제목이 같은 카드입니다. 남은 `numbers_reconciler` 카드의 인용문은 자막에 실제로 있어서 11.65~18.0초(`Revenue grew…` 조각의 12초 − 0.35, 조각 끝 18초)에 앉았습니다. 그런데 `filing_grounder` 카드의 "Guidance was raised to fifteen percent"는 **자막에 없는 문장**인데도 같은 조각에 앉았습니다. 낱말 `percent` 하나가 겹쳤을 뿐입니다. 코드는 인용문이 자막에 있는지 검증하지 않고 어딘가에 앵커합니다. 그래서 "인용문에 앵커된 카드"는 가장 비슷한 조각에 시각이 맞춰진 카드이지 검증된 인용문이 아닙니다. 화면도 출처(`citations`)가 없는 카드마다 `Transcript anchored`라고 적어(`app.js:486`) 이 오해를 거듭니다. 숫자·인용·피어·제출 서류는 모두 모델의 주장이니 영상과 SEC 원문으로 대조해야 하고, 이 앱은 투자 조언 도구가 아닙니다.

모델 호출이 실패하는 경우도 같은 방식으로 확인합니다. 이번에는 문지기를 참으로 두고 `run_adk_agent_text`를 예외를 던지는 가짜로 바꿔 끼웁니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -c "
from unittest.mock import patch
from earnings_call_analyst_agent import agent
from earnings_call_analyst_agent.schemas import ResearchPack, TranscriptSegment, VideoMetadata
from earnings_call_analyst_agent.youtube_ingest import chunk_transcript

chunks = chunk_transcript([TranscriptSegment(start=0, duration=6, text='Revenue grew twelve percent.')], window_seconds=42)

def failing_call(*args, **kwargs):
    error = RuntimeError('API key not valid (stub)')
    print('model call raised:', type(error).__name__, '|', error)
    raise error

with patch.object(agent, 'has_adk_credentials', return_value=True), patch.object(agent, 'run_adk_agent_text', failing_call):
    cards = agent.generate_insights(VideoMetadata(video_id='abcDEF12345', title='Example Q3 earnings call'), ResearchPack(company='Example Co', ticker='EXM'), chunks)
print('cards:', cards)
"
```

직접 확인한 출력:

```text
model call raised: RuntimeError | API key not valid (stub)
cards: []
```

첫 줄은 가짜가 예외를 던지며 스스로 찍은 것이고, 앱은 아무것도 찍지 않은 채 `[]`를 돌려줍니다. 앱에는 이 예외를 보여 주는 곳이 없습니다. 실제 서버에서 보려면 `agent.py:113`의 `except Exception:` 바로 아래에 `import traceback; traceback.print_exc()` 한 줄을 임시로 넣고 서버 터미널을 봅니다. 카드가 검증에서 버려지는 곳(`agent.py:143`)에도 같은 줄을 넣으면 탈락 사유가 찍힙니다(위 카드 다섯 장이면 `ValidationError` 둘). 스크래치 사본에서 두 곳 모두 이 줄로 예외가 찍히는 것을 확인했습니다.

### Step 6. FastAPI 세션 서버 — 응답은 먼저, 분석은 뒤에서

**목적.** `server.py`가 요청을 받자마자 세션 ID를 돌려주고 분석은 백그라운드에서 돌리는 구조와 진행률 상태 기계를 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/server.py:135-167`

```python
async def _run_session(session_id: str) -> None:
    runtime = sessions[session_id]
    try:
        await _set_status(runtime, "metadata", 10, "Resolving YouTube video")
        video_id = extract_video_id(runtime.youtube_url)
        metadata = await asyncio.to_thread(fetch_video_metadata, runtime.youtube_url, video_id)

        await _set_status(runtime, "transcript", 25, "Loading YouTube captions")
        try:
            transcript = await asyncio.to_thread(fetch_transcript, video_id)
            transcript_source = "youtube_captions"
        except Exception:
            await _set_status(
                runtime,
                "transcript",
                32,
                "Captions unavailable; transcribing audio with ADK",
            )
            transcript = await asyncio.to_thread(
                transcribe_audio_with_adk,
                video_id,
                lambda progress, message: _set_status_from_thread(runtime, progress, message),
            )
            transcript_source = "adk_audio"
        if not transcript:
            raise RuntimeError("This video did not return usable transcript segments.")
        chunks = chunk_transcript(transcript, window_seconds=42)

        await _set_status(runtime, "research", 45, "Building company research pack")
        research = await asyncio.to_thread(build_research_pack, metadata, transcript)

        await _set_status(runtime, "analysis", 70, "Curating high-signal analyst cards")
        insights = await asyncio.to_thread(generate_insights, metadata, research, chunks)
```

`POST /api/sessions`(`server.py:102-114`)는 URL만 `extract_video_id`로 검사해 틀리면 400을, 맞으면 `RuntimeSession`을 딕셔너리에 넣고 `BackgroundTasks`로 `_run_session`을 예약한 뒤 `session_id`를 곧바로 돌려줍니다. 분석은 위 함수가 응답 **뒤에** 돌립니다. 단계마다 동기 함수를 `asyncio.to_thread`로 스레드에 내보내고 `_set_status`로 진행률을 쌓습니다. 10(영상 확인) → 25(자막) → 45(리서치) → 70(분석) → 100(완료)이고, 오디오로 넘어가면 32와 34·38 이상·62가 끼어듭니다. 브라우저는 `GET /api/sessions/{id}`를 1.5초마다 불러 이 필드를 읽습니다.

결과 조립(`server.py:169-186`)에서 눈여겨볼 것이 셋입니다. 카드가 없으면 `AnalysisSession.status`는 `partial`인데 폴링 응답 맨 위의 `status`는 그래도 `ready`입니다(`server.py:187`). `diagnostics`에 `analysis_engine`과 `auth_mode`가 담기지만 화면은 그리지 않고(`app.js`에 `diagnostics` 참조가 없음 — 소스 검색으로 확인), `analysis_engine`은 문지기 `has_adk_credentials()`만 본 값이라 모델 호출이 실패했는지는 말해 주지 않습니다(`server.py:183`). 그리고 `sessions`는 프로세스 메모리의 dict라 서버를 재시작하면 사라지고, 지우는 코드가 없어 쌓이기만 합니다.

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** 부모 폴더에서 실행합니다. `server`가 이름으로 임포트해 둔 네트워크 함수 셋(`fetch_video_metadata`·`fetch_transcript`·`build_research_pack`)을 가짜로 바꿔 끼우고, FastAPI `TestClient`로 진짜 라우트를 부릅니다. `_set_status`를 감싸 상태 전이도 기록합니다. `generate_insights`는 진짜이고 키가 없으니 `[]`를 돌려줍니다. 마지막 세션은 키가 있는데 모델 호출이 실패하는 경우로, `GOOGLE_API_KEY`에 가짜 값을 넣고 `agent.run_adk_agent_text`를 예외를 던지는 가짜로 바꿉니다. `-W ignore`는 `TestClient`가 내는 경고를 숨깁니다(문제 해결 참고).

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -W ignore -c "
import os
from fastapi.testclient import TestClient
from earnings_call_analyst_agent import agent
from earnings_call_analyst_agent.live_demo import server
from earnings_call_analyst_agent.schemas import ResearchPack, TranscriptSegment, VideoMetadata

for name in ['GEMINI_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_GENAI_USE_VERTEXAI', 'GOOGLE_CLOUD_PROJECT']:
    os.environ.pop(name, None)
server.fetch_video_metadata = lambda url, video_id: VideoMetadata(video_id=video_id, title='Example Corp (EXM) Q3 2025 Earnings Call')
server.fetch_transcript = lambda video_id: [TranscriptSegment(start=0, duration=4, text='Welcome to the call.'), TranscriptSegment(start=12, duration=6, text='Revenue grew twelve percent.')]
server.build_research_pack = lambda meta, transcript: ResearchPack(company='Example Corp', ticker='EXM')

trace = []
original = server._set_status
async def record(runtime, status, progress, message):
    trace.append((status, progress))
    await original(runtime, status, progress, message)
server._set_status = record

client = TestClient(server.app)
print(client.get('/health').json())
print(client.post('/api/sessions', json={'youtube_url': 'https://example.com/nope'}).status_code)
session_id = client.post('/api/sessions', json={'youtube_url': 'https://youtu.be/abcDEF12345'}).json()['session_id']
print(trace)
body = client.get('/api/sessions/' + session_id).json()
print(body['status'], body['progress'], body['data']['status'], body['data']['diagnostics'])
print(repr(body['error']), body['message'])

os.environ['GOOGLE_API_KEY'] = 'fake-key'
def failing_call(*args, **kwargs):
    raise RuntimeError('API key not valid (stub)')
agent.run_adk_agent_text = failing_call
session_id = client.post('/api/sessions', json={'youtube_url': 'https://youtu.be/abcDEF12345'}).json()['session_id']
body = client.get('/api/sessions/' + session_id).json()
print(body['status'], body['progress'], body['data']['status'], body['data']['diagnostics'])
print(repr(body['error']), body['message'])
"
```

직접 확인한 출력:

```text
{'ok': True, 'has_adk_credentials': False, 'has_google_key': False, 'auth_mode': 'missing'}
400
[('metadata', 10), ('transcript', 25), ('research', 45), ('analysis', 70), ('ready', 100)]
ready 100 partial {'transcript_segments': 2, 'transcript_source': 'youtube_captions', 'chunks': 1, 'insights': 0, 'analysis_engine': 'adk_unavailable', 'auth_mode': 'missing'}
'' Ready with transcript and research; no high-signal insights were emitted.
ready 100 partial {'transcript_segments': 2, 'transcript_source': 'youtube_captions', 'chunks': 1, 'insights': 0, 'analysis_engine': 'adk', 'auth_mode': 'api_key'}
'' Ready with transcript and research; no high-signal insights were emitted.
```

첫 줄은 `/health`, 둘째 줄은 잘못된 URL의 400, 셋째 줄은 진행률 전이입니다. 넷째 줄에서 폴링 응답은 `ready 100`인데 `data.status`는 `partial`이고 진단 값이 `adk_unavailable`·`missing`을 말합니다. 다섯째 줄은 화면 아래 상태 문구가 되는 `message`이고 `error`는 빈 문자열입니다. 여섯째·일곱째 줄은 가짜 키와 실패하는 모델 호출을 넣은 두 번째 세션입니다. 키가 없을 때와 같은 `ready 100`·`partial`·같은 문구에 `error`도 비어 있고, 달라진 것은 진단이 `analysis_engine: adk`·`auth_mode: api_key`라고 말하는 것뿐입니다. 실패한 모델 호출은 응답 어디에도 남지 않습니다.

### Step 7. 프런트엔드와 실행 — 재생 시각에 맞춘 공개

**목적.** 브라우저 쪽이 상태를 읽어 카드를 공개하는 방식을 보고, 앱을 띄워 확인하고, 앱 자체 테스트를 돌립니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/app.js:250-266`

```javascript
function syncPlayback() {
  if (!sessionData || !player || typeof player.getCurrentTime !== "function") return;
  const current = player.getCurrentTime();
  timecode.textContent = formatTime(current);
  revealDueInsights(current);
  updateTimelinePlayback(current);
}

function revealDueInsights(currentTime) {
  const due = sessionData.insights
    .filter((insight) => insight.start_time <= currentTime && !revealed.has(insight.id))
    .sort((a, b) => a.start_time - b.start_time);

  if (!due.length) return;
  due.forEach((insight) => revealed.add(insight.id));
  updateRevealState({ scrollToId: due[due.length - 1].id });
}
```

`checkHealth`(`app.js:138-151`)가 `/health`로 헤더의 한 줄을 정합니다. 자격증명이 없으면 "No ADK credentials detected; analyst cards disabled"입니다. 분석이 끝나 `data`가 오면 `renderSession`이 YouTube 플레이어를 붙이고, 500ms마다 위 `syncPlayback`이 `getCurrentTime()`을 읽어 `start_time`이 현재 시각 이하인 카드를 공개합니다. 아직 안 열린 카드는 화면에서만 가려질 뿐 내용은 이미 응답 JSON에 들어 있고(`app.js:319-347`, `server.py:130-131`), 한 번 연 카드는 되감아도 다시 접히지 않습니다(`revealed`는 `resetWorkspace`에서만 비워집니다). "Reveal next signal"·"Show all" 버튼은 플레이어 없이도 동작합니다(`app.js:268-282`). 이 문서는 브라우저를 열지 않았고 화면 동작은 소스로만 확인했습니다. `/static` 마운트가 `live_demo/` 폴더 전체를 서빙하므로(`server.py:82`) `server.py`도 `/static/server.py`로 내려받아집니다(소스로 확인). `.env`는 부모 폴더에 있어 노출되지 않습니다.

![Step 7까지의 구성](diagrams/step7.svg)

**확인.** 앱을 띄우는 명령은 한 줄입니다. 부모 폴더 `single_agent_apps`에서 실행합니다. 앱 README의 `PYTHONPATH=.. python -m uvicorn …`은 앱 폴더 안에서 쓰는 bash 형태이고, 부모 폴더에서는 `PYTHONPATH`가 필요 없어 PowerShell에서도 같은 줄이 돌 것입니다. 이 문서의 명령은 bash에서 돌려 확인했고 PowerShell에서는 실행해 보지 못했습니다.

```bash
uv run --no-project --python earnings_call_analyst_agent/.venv python -m uvicorn earnings_call_analyst_agent.live_demo.server:app --host 127.0.0.1 --port 4188
```

브라우저로 http://127.0.0.1:4188 에 접속해 URL을 붙여 넣습니다(키가 없으면 카드는 0장이고 헤더에 위 문구가 보입니다). 여기서부터는 밖으로 요청이 나갑니다. 화면을 여는 것만으로 브라우저가 YouTube의 `iframe_api`를 받고, 실제 URL을 넣으면 YouTube(oEmbed·자막)에, 티커를 찾으면 SEC에도 요청이 나갑니다. 셸이나 `.env`에 키(또는 Vertex 설정)가 있으면 분석 때 Gemini도 불러 과금됩니다. 다른 터미널에서 두 응답을 봅니다. Windows PowerShell은 `curl`을 `Invoke-WebRequest`의 별칭으로 미리 정의해 두므로 `curl.exe`로 씁니다(macOS/Linux는 `curl`).

```bash
curl.exe -s -w "\n" http://127.0.0.1:4188/health
curl.exe -s -w "\n" http://127.0.0.1:4188/api/sessions/nope
```

직접 확인한 출력(4188 대신 다른 포트로 띄워 확인했고, 출력에 포트는 나오지 않습니다):

```text
{"ok":true,"has_adk_credentials":false,"has_google_key":false,"auth_mode":"missing"}
{"detail":"Unknown analysis session."}
```

마지막으로 앱 폴더 `earnings_call_analyst_agent`에서 앱 자체 테스트를 돌립니다.

```bash
uv run --no-project python -m pytest -q
```

직접 확인한 출력(시간은 다릅니다):

```text
....................                                                     [100%]
20 passed in 0.70s
```

20개가 모두 통과합니다. 테스트는 네트워크 함수와 ADK 호출을 `monkeypatch`로 바꿔 끼우며, DNS와 소켓을 막은 채 돌려도 통과했습니다.

## 요청 한 건이 흐르는 과정

시간 경계를 따라 그림을 나눴습니다. 그림 순서가 시간 순서이고, 서버·모듈·외부 서비스 사이의 호출은 어느 그림에도 정확히 한 번씩, 원래 순서로 있습니다. 화살표가 제자리로 돌아오는 메시지는 그 모듈 안에서 도는 처리입니다. 단계마다 서버가 세션 저장소에 `status:`를 쓰고, 프런트엔드는 1.5초마다 폴링하지만 같은 메시지라 첫 폴링과 결과를 받는 마지막 폴링만 그렸습니다. 키가 있고 티커를 찾았을 때의 정상 경로라서, 모듈이 시작할 때 부르는 문지기는 `True`로 돌아오는 쪽만 그렸습니다. 문지기 호출은 모듈 네 곳(정체 추론 `research.py:90`, 뉴스 `research.py:169`, 분석 `agent.py:48`, 오디오 전사 `youtube_ingest.py:151`)과 서버 두 곳(`/health`, 결과 진단) 모두 그렸습니다. 실행기가 안에서 세션 서비스를 만드는 호출만은 시퀀스 대신 위 "ADK 에이전트 배선" 그림의 화살표가 맡습니다.

### 1. 화면 열기와 요청 접수

브라우저가 화면 파일 셋과 YouTube의 `iframe_api` 스크립트를 받습니다. `index.html`에 적힌 순서(`styles.css`, `iframe_api`, `app.js`)로 그렸고 실제로는 병렬로 받을 수 있으며, 주소 뒤의 `?v=…` 꼬리표는 뺐습니다.

![화면 열기](diagrams/extra-load.svg)

이어서 프런트엔드가 `/health`로 헤더의 한 줄을 정합니다. 서버는 응답을 만들면서 실행기의 문지기를 둘 다 부릅니다(`server.py:92-93`).

![/health와 문지기](diagrams/extra-health.svg)

Analyze를 누르면 프런트엔드가 진행 막대를 4%로 올리고 `POST`를 보냅니다. 서버는 URL을 검사하고 세션을 만든 뒤 `session_id`를 곧바로 돌려줍니다.

![요청 시퀀스](diagrams/sequence.svg)

응답이 나간 직후 백그라운드 태스크가 시작되어 자기 세션을 꺼내 `metadata` 상태를 쓰고, 프런트엔드는 첫 폴링으로 받은 상태를 진행 막대로 그립니다. 두 일은 동시에 일어나므로 이 그림의 순서는 한 가지 예입니다.

![백그라운드 시작과 첫 폴링](diagrams/extra-polling.svg)

### 2. 영상 정보와 자막

`_run_session`이 `extract_video_id`를 한 번 더 부르고(`server.py:139`) oEmbed로 제목·채널을 가져옵니다.

![영상 메타데이터](diagrams/extra-metadata.svg)

이어서 자막을 가져와 청크를 만듭니다. 마지막 `status: research (45%)`는 다음 단계의 시작 표시입니다.

![자막과 청크](diagrams/extra-captions.svg)

<details>
<summary>자막이 없을 때 — 오디오 전사(그림 4장)</summary>

자막 요청이 실패하면 서버가 32%로 올리고 `transcribe_audio_with_adk`를 스레드에서 부릅니다. 이 함수는 먼저 실행기의 문지기를 확인하고(`youtube_ingest.py:151`, 거짓이면 예외를 던집니다) 34%를 알립니다. 스레드의 `on_progress` 콜백은 서버의 `_set_status_from_thread`(`server.py:207-210`)로 세션 상태를 갱신합니다.

![오디오 전사 시작](diagrams/extra-audio-start.svg)

yt-dlp가 오디오를 받고 이 PC의 ffmpeg가 300초 조각으로 자릅니다. 마지막 두 메시지는 조각을 시작할 때마다 되풀이됩니다.

![오디오 내려받기와 분할](diagrams/extra-audio-download.svg)

조각마다 `transcription_agent`가 Gemini에 오디오를 보내고 JSON 세그먼트를 돌려받습니다. 돌려받은 글은 `parse_transcribed_segments`가 `parse_json_object`로 읽어 세그먼트로 만듭니다.

![조각 전사](diagrams/extra-audio-chunks.svg)

모든 조각이 끝나면 62%를 알리고 시각이 이어 붙은 세그먼트 목록을 서버에 돌려줍니다.

![오디오 전사 마무리](diagrams/extra-audio-done.svg)

</details>

### 3. 리서치 팩

`build_research_pack`이 먼저 휴리스틱으로 회사를 추정하고, 문지기(`research.py:90`)가 참이면 `identity_agent`에 묻습니다. 첫 그림은 모델의 답이 실행기에서 돌아오는 데까지입니다.

![정체 추론](diagrams/extra-identity.svg)

답을 `parse_json_object`로 읽어 휴리스틱 위에 덮어쓰고, 티커가 나오면 SEC에 두 번 묻습니다.

![정체 확정과 SEC 제출 목록](diagrams/extra-filings.svg)

그다음 뉴스입니다. 여기도 문지기(`research.py:169`)가 먼저이고, 참이면 `market_news_agent`가 `google_search`로 뉴스를 찾습니다. 그림이 길어져 모델의 답이 돌아오는 데서 둘로 나눴습니다.

![뉴스 검색](diagrams/extra-news.svg)

답을 `parse_json_object`로 읽어 URL·중복·제목 끝 출처를 거르고, 조립된 `ResearchPack`이 서버로 돌아갑니다.

![뉴스 거르기](diagrams/extra-news-result.svg)

### 4. 분석

분석가가 청크를 고르고 문지기(`agent.py:48`)를 확인합니다. 모델을 부르기 전과 후로 그림을 나눴습니다.

![청크 고르기](diagrams/extra-analysis.svg)

문지기가 참이면 분석가가 프롬프트를 만들어 `root_agent`에 보냅니다.

![카드 생성](diagrams/extra-analysis-call.svg)

돌아온 글은 `parse_json_object`로 읽고 검증·중복 제거·인용문 재정렬을 거쳐 서버로 갑니다.

![카드 검증](diagrams/extra-analysis-done.svg)

서버는 결과를 조립하면서 진단 값을 만들려고 문지기를 다시 부르고(`server.py:183-184`), 저장한 뒤 `ready`로 올립니다.

![결과 저장](diagrams/extra-analysis-save.svg)

### 5. 결과와 재생

다음 폴링이 `ready`와 `data`를 받으면 프런트엔드가 플레이어를 붙이고 리서치 팩과 카드 목록을 그립니다. 아직 열리지 않은 카드는 잠긴 채입니다.

![결과 받기](diagrams/extra-result.svg)

그 뒤로는 500ms마다 재생 시각을 읽어 카드를 공개하고, "Jump to quote"를 누르면 그 시각으로 감습니다.

![재생과 공개](diagrams/extra-playback.svg)

## 실행 체크리스트

- [ ] 앱 폴더에 가상환경을 만들고 `requirements.txt`를 설치했다
- [ ] 부모 폴더에서 `--python earnings_call_analyst_agent/.venv`로 패키지를 임포트하고 `LlmAgent` 넷을 확인했다
- [ ] `has_adk_credentials()`가 `.env.example`의 자리표시자 값도 통과시키고, `.env`는 첫 줄이 이긴다는 것을 확인했다
- [ ] 로컬 `BaseAgent`로 `run_adk_agent_text`가 마지막 텍스트 이벤트를 돌려주는 것을 확인했다
- [ ] `youtube-transcript-api` 1.2.0 이상(오늘은 1.2.4)에는 `get_transcript`가 없어 `fetch` 경로로 가고, 친절한 `RuntimeError`가 나오지 않는 것을 확인했다(1.0.3·1.1.1에서는 다르다는 것은 휠 소스로 확인)
- [ ] 티커가 없으면 SEC·뉴스를 건너뛰고 `notes`만 남는다는 것을 확인했다
- [ ] 가짜 모델 응답 카드 다섯 장 중 둘만 남고, 자막에 없는 인용문도 어딘가에 앵커된다는 것을 확인했다
- [ ] 모델 호출이 실패하면 `generate_insights`가 예외를 삼키고 `[]`를 돌려주며, 그때도 서버 진단이 `analysis_engine: adk`라고 답하는 것을 확인했다
- [ ] `TestClient`로 진행률이 10→25→45→70→100으로 흐르고 카드가 없으면 `partial`이라는 것을 확인했다
- [ ] 앱을 띄워 `/health`와 없는 세션의 404 본문을 확인했다
- [ ] `pytest -q`에서 20개가 통과했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| 앱 폴더 안에서 임포트하면 `ImportError: attempted relative import with no known parent package`(직접 확인) | 소스가 상대 임포트라 패키지의 부모 폴더에서 임포트해야 합니다 | 부모 폴더 `single_agent_apps`에서 `--python earnings_call_analyst_agent/.venv`로 실행 |
| 한국어 Windows에서 `.env`에 한글 주석을 쓰면 서버가 뜨지 않고 `uvicorn`이 `UnicodeDecodeError: 'cp949' codec can't decode byte 0xed in position 2: illegal multibyte sequence`를 찍고 끝납니다(직접 확인. 바이트와 위치는 주석이 `# 한글 주석`일 때의 값이고 내용에 따라 달라집니다) | `_load_env`가 `read_text()`를 인코딩 없이 불러(`advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/live_demo/server.py:28`) 로케일 인코딩(cp949)으로 읽습니다 | `.env`를 ASCII로만 쓰거나 실행 전에 `PYTHONUTF8=1`(PowerShell은 `$env:PYTHONUTF8=1`) |
| `cp .env.example .env`만 했는데 `has_adk_credentials()`가 True, `adk_auth_mode()`가 `vertex_ai`(Step 2, 직접 확인) | 기본 파일의 Vertex 블록이 켜져 있고 문지기는 값을 확인하지 않습니다 | 쓰지 않을 방식의 줄은 지우고 하나만 남기기 |
| Option 2(API 키)를 주석 해제했는데 `GOOGLE_GENAI_USE_VERTEXAI`가 여전히 `True`(Step 2, 직접 확인) | `setdefault`라 같은 키가 두 번이면 첫 줄이 이깁니다. google-genai 2.25.0 소스상 프로젝트와 키가 함께 있으면 프로젝트가 이깁니다(소스로 확인) | Option 1의 세 줄을 지우거나 주석 처리 |
| 분석이 "완료"인데 카드가 0장 — `data.status`가 `partial`, 메시지가 `Ready with transcript and research; no high-signal insights were emitted.`(Step 6, 직접 확인) | 셋 중 하나입니다. (1) 자격증명이 없어 `generate_insights`가 `[]`입니다(Step 2). (2) 자격증명은 통과했는데 모델 호출이 실패했습니다. 키나 프로젝트가 틀렸거나 자리표시자이거나(위 두 행), 모델 이름이 폐기됐거나, 할당량이 찼을 때입니다. `agent.py:111-114`가 예외를 삼켜 `[]`를 돌려주고 `analysis_engine`은 문지기만 본 값이라 `adk`로 남습니다(Step 5·6, 직접 확인). (3) 모델 카드가 검증에서 전부 버려졌습니다(Step 5) | `/health`의 `auth_mode`가 `missing`이 아닌지 먼저 봅니다(1). 키가 있는데도 0장이면 `agent.py:113`의 `except Exception:` 바로 아래에 `import traceback; traceback.print_exc()`를 임시로 넣고 서버 터미널에서 예외를 봅니다(2). (3)은 `agent.py:143`의 `except Exception:` 아래에 같은 줄을 넣습니다. 확인한 뒤 줄은 지우세요 |
| `TestClient`를 임포트하면 ``StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.``(직접 확인) | 설치된 starlette 1.7.0이 httpx 기반 `TestClient`를 폐기 예고합니다 | 경고일 뿐 동작은 정상입니다. Step 6은 `-W ignore`로 숨깁니다 |
| `--port`에 고른 번호에서 `[winerror 10013]`(Windows에서 60649로 직접 확인) | Windows가 예약해 둔 포트 범위입니다 | `netsh int ipv4 show excludedportrange protocol=tcp`로 범위를 보고 피하기 |

## 더 해보기

- 인용문 검증기를 붙여 보세요. `_generate_with_adk`가 카드를 만든 뒤(`agent.py:120-145`) `_normalize_text`(`agent.py:288-289`)로 정규화한 인용문이 자막 전체에 있는지 보고, 없으면 카드를 버리거나 `confidence`를 낮춥니다. Step 5의 가짜 응답으로 "자막에 없는 문장" 카드가 사라지는지 확인합니다.
- `agent._chunk_signal_score('We remain calm')`이 몇 점인지 찍어 보고 0이 아니면 왜인지 찾아보세요(`agent.py:148-174`의 `count`). 낱말 경계를 지키게 고친 뒤 점수를 비교합니다.
- `_is_low_quality_news_title`(`research.py:234-237`)은 제목 끝의 ` - reddit` 같은 접미사만 봅니다. 모델이 `source: 'Reddit'`만 채우고 제목에는 붙이지 않으면 어떻게 될까요? Step 5처럼 `research`의 `has_adk_credentials`와 `run_adk_agent_text`를 바꿔 끼우고 `research.fetch_adk_grounded_news('EXM', 'Example Corp')`를 불러 확인한 뒤 `source`도 보게 고쳐 보세요.

## 다음 날 예고

[Day 098 · 🎧 AI Social Media News and Podcast Agent](../day098-ai-news-and-podcast-agents/README.md) — 다음은 신뢰하는 기사·소셜 미디어 소스를 모아 팟캐스트 대본과 음성으로 만드는 멀티 에이전트 앱(Beifong)입니다.
