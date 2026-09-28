# Day 076 · 🗄️ Local ChatGPT Clone with Memory

> 볼륨 6 💾 LLM Apps with Memory · 난이도 ★★☆ · 예상 소요 75분(mem0ai가 오늘 기준으로 두 가지 실패를 겪어, 두 번 다 직접 재현하고 원인을 소스로 확인하는 시간을 포함합니다) · API 비용 무료(로컬 — 채팅·임베딩·메모리 벡터 저장까지 전부 Ollama와 Qdrant로 처리하고, 이 문서는 클라우드 API를 하나도 호출하지 않습니다) · 원본 앱: `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory`

## 오늘 만들 것

오늘 앱(`local_chatgpt_memory.py`, 137줄 — 마지막 줄에 개행이 없어 `wc -l`은 136으로 세지만 편집기·GitHub에서는 137번째 줄까지 보입니다, 직접 확인)은 이 볼륨에서 처음으로 채팅 모델과 mem0의 사실 추출·임베딩까지 전부 **Ollama** 하나로 돌리는 앱입니다. Day 073의 `llm_app_memory.py`는 mem0 config에 `llm`·`embedder`를 지정하지 않아 기본값인 OpenAI를 그대로 썼지만, 오늘 config는 `vector_store`(Qdrant)뿐 아니라 `llm`과 `embedder`도 명시적으로 `"provider": "ollama"`로 지정합니다(6~34행) — 그래서 원본 앱 README가 내세우는 "Fully local implementation with no external API dependencies"라는 문구가, 적어도 이 config가 가리키는 서비스들에 대해서는 소스로 확인됩니다. 사용자는 사이드바에 아무 이름이나 입력해 "로그인"하고(별도 인증 없음, 47~53행), 채팅창에 메시지를 보내면 앱은 그 메시지를 먼저 mem0에 저장한 뒤(88행), 같은 사용자의 과거 메모리 전체를 `get_all()`로 가져와(91행) 컨텍스트 문자열로 붙이고, `litellm.completion(model="ollama/llama3.1:latest", ...)`로 스트리밍 응답을 받습니다(105~113행). 이 문서를 쓰며 오늘(2026-09-28) `uv pip install -r requirements.txt`로 설치했을 때 **streamlit 1.64.0**, **litellm 1.80.0**, **mem0ai 0.1.29**, **qdrant-client 1.19.1**이 그대로 받아졌고 파일도 문제없이 컴파일됩니다(직접 확인, Step 1). 하지만 mem0ai 0.1.29의 Ollama LLM/임베더 provider는 `ollama`라는 별도 PyPI 패키지에 `from ollama import Client`로 직접 의존하는데, 이 패키지는 `requirements.txt` 4줄에도, mem0ai가 선언한 의존성에도 없습니다(직접 확인, Step 1) — 그 결과 사이드바에 사용자명을 입력하는 순간(=`Memory.from_config(config)` 호출, 59행) 앱은 깔끔한 `ImportError`가 아니라 표준입력이 없는 Streamlit 프로세스에서 즉시 `EOFError`로 죽습니다(직접 재현, Step 2). `ollama` 패키지를 따로 설치해도 두 번째 문제가 남습니다 — mem0ai 0.1.29가 "모델이 이미 있는지" 확인하는 코드는 오늘 설치되는 `ollama` 0.6.2의 응답 스키마와 필드 이름이 어긋나 있어, 모델이 이미 로컬에 있어도 매번 무조건 `pull`을 시도합니다(직접 재현, Step 2). 이 두 버그를 우회하면 앱 자체의 로직(v1.1 형식의 `get_all()`, 컨텍스트 구성, 스트리밍 응답 처리)은 설계대로 동작한다는 것도 로컬 스텁 서버로 직접 확인했습니다(Step 6~8) — Day 073에서 본 `get_all()` dict/list 불일치는 오늘 config가 `"version": "v1.1"`을 명시하기 때문에 이 앱에는 없습니다. 완성하면 브라우저에는 제목, 사이드바의 사용자명 입력창과 "View My Memory" 버튼, 그리고 채팅 입력창이 뜹니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Ollama | `llama3.1:latest`로 채팅, `nomic-embed-text:latest`로 임베딩을 로컬로 서빙(`localhost:11434`) | https://ollama.com/download 설치 후 `ollama pull llama3.1`·`ollama pull nomic-embed-text` — 이 문서는 두 모델을 내려받지 않고 로컬 스텁 서버로 재현합니다 |
| ollama (PyPI 패키지) | mem0ai 0.1.29의 Ollama LLM/임베더 provider가 직접 의존 — `requirements.txt`와 mem0ai 의존성 어디에도 없음(Step 1에서 직접 확인) | `uv pip install ollama` (pip: `pip install ollama`) |
| Qdrant | mem0가 사용자별 벡터를 저장하는 벡터 저장소, `local-chatgpt-memory` 컬렉션 | Docker: `docker run -p 6333:6333 qdrant/qdrant` — 이 문서는 Docker 대신 `qdrant-client`의 로컬 파일 모드(`path=`)로 벡터 저장소 계층만 재현합니다 |
| MEM0_DIR·MEM0_TELEMETRY 환경변수 | `import mem0`가 홈 디렉터리에 `.mem0/`를 만들고 PostHog로 익명 통계를 보내는 것을 막음(Day 073에서 직접 확인한 것과 같은 동작) | 이 문서의 모든 명령은 import 전에 `MEM0_DIR=<스크래치 경로>`·`MEM0_TELEMETRY=False`를 지정합니다 |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 참고 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 사용자 (브라우저) | 사용자명·메시지 입력, 답변과 사이드바 메모리 확인 | 코드 없음 (외부 UI) |
| Streamlit UI | 제목·세션 상태·사이드바·채팅 렌더링 | `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:36-43`, `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:45-69`, `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:71-86` |
| mem0 Memory 계층 | 메시지에서 사실을 뽑아 사용자별 벡터로 저장·조회하는 오케스트레이션(mem0ai 0.1.29, 패키지 소스로 확인) | `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:6-34`, `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:59`, `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:88`, `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:91` |
| LiteLLM 완성 호출 | Ollama의 `/api/generate`에 스트리밍 채팅 완성 요청(litellm 1.80.0, 패키지 소스로 확인) | `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:105-113`, `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:116-121` |
| Qdrant 벡터 저장소 (외부, 로컬) | mem0가 뽑은 메모리 벡터를 `local-chatgpt-memory` 컬렉션에 저장 | 코드 없음 (외부 프로세스, `localhost:6333`) |
| Ollama 로컬 서버 (외부, 로컬) | `llama3.1`(챗)·`nomic-embed-text`(임베딩)를 로컬로 서빙 | 코드 없음 (외부 프로세스, `localhost:11434`) |

## 단계별 진행

### Step 1. 환경 만들기 — mem0ai가 무엇을 당기고, 무엇을 빠뜨리는지 확인

**목적.** 격리된 가상환경에 `streamlit`·`openai`·`mem0ai`·`litellm`을 설치하고, 파일이 그대로 컴파일되는지, 그리고 mem0ai가 Ollama를 쓰려면 실제로 무엇이 더 필요한지 확인합니다.

**할 일.**

```bash
cd advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory
uv venv
uv pip install -r requirements.txt
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Windows PowerShell은 활성화만 `.venv\Scripts\Activate.ps1`로 바꿉니다.) 이 저장소는 루트에 `pyproject.toml`이 있어 `uv run`이 방금 만든 환경 대신 루트 `.venv`를 쓰므로, 이후 `uv run` 명령에는 모두 `--no-project`를 붙입니다.

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/requirements.txt:1-4`

```text
streamlit
openai
mem0ai==0.1.29
litellm
```

(4줄이지만 마지막 줄에 개행이 없어 `wc -l`은 3으로 셉니다. 1행 끝에는 공백이 하나 더 있습니다.) 이 4줄 중 버전이 고정된 것은 `mem0ai`뿐입니다. `openai`는 이 파일이 직접 import하지 않지만(3개 import는 `streamlit`·`mem0.Memory`·`litellm.completion`뿐입니다) litellm 1.80.0 자신이 `openai>=1.99.5`를 의존성으로 선언하므로 어차피 함께 설치됩니다(배포 메타데이터로 확인). 이 목록에는 mem0ai가 Ollama LLM/임베더 provider에서 직접 요구하는 `ollama` 패키지가 빠져 있습니다 — Step 2에서 이게 왜 문제가 되는지 직접 확인합니다.

Day 073에서 이미 확인했듯이 `import mem0`만 해도 홈 디렉터리에 `.mem0/`가 생기고 PostHog로 익명 통계가 나가므로, 이 문서의 모든 명령은 import 전에 `MEM0_DIR=<스크래치 경로>`와 `MEM0_TELEMETRY=False`를 지정합니다.

![Step 1까지의 구성](diagrams/step1.svg)

**확인.**

```bash
uv run --no-project python -m py_compile local_chatgpt_memory.py && echo compiled
uv run --no-project python -c "
import streamlit, litellm, mem0
import importlib.metadata as m
print('streamlit', streamlit.__version__)
print('litellm', m.version('litellm'))
print('mem0ai', m.version('mem0ai'))
print('qdrant-client', m.version('qdrant-client'))
"
uv run --no-project python -c "import ollama"
```

직접 확인한 출력(2026-09-28 기준, 버전을 고정하지 않은 패키지들은 오늘 기준 최신):

```
compiled
streamlit 1.64.0
litellm 1.80.0
mem0ai 0.1.29
qdrant-client 1.19.1
```

마지막 명령(`import ollama`)은:

```
ModuleNotFoundError: No module named 'ollama'
```

mem0ai 0.1.29의 배포 메타데이터(`Requires-Dist`)를 봐도 `openai`·`posthog`·`pydantic`·`pytz`·`qdrant-client`·`sqlalchemy`만 있고 `ollama`는 없습니다(직접 확인) — Ollama provider를 실제로 쓰려면 이 패키지를 별도로 설치해야 합니다.

### Step 2. mem0 Memory 설정 — Qdrant + Ollama, 그리고 두 가지 실패

**목적.** config가 벡터 저장소·LLM·임베더를 어떻게 나누는지 확인하고, `Memory.from_config(config)`가 오늘 기준 설치에서 실제로 어디서 어떻게 실패하는지 재현합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:1-34`

```python
import streamlit as st
from mem0 import Memory
from litellm import completion

# Configuration for Memory
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "local-chatgpt-memory",
            "host": "localhost",
            "port": 6333,
            "embedding_model_dims": 768,
        },
    },
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.1:latest",
            "temperature": 0,
            "max_tokens": 8000,
            "ollama_base_url": "http://localhost:11434",  # Ensure this URL is correct
        },
    },
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text:latest",
            # Alternatively, you can use "snowflake-arctic-embed:latest"
            "ollama_base_url": "http://localhost:11434",
        },
    },
    "version": "v1.1"
}
```

Day 073의 config와 달리 이 config는 `llm`과 `embedder`를 모두 명시적으로 `"provider": "ollama"`로 지정하고, `"version": "v1.1"`도 명시합니다 — 그래서 Day 073에서 본 `get_all()`의 dict/list 불일치는 이 앱에는 없습니다(Step 6에서 직접 확인). 22행의 주석("Ensure this URL is correct")은 코드에 아무 검증도 없다는 뜻으로 읽힙니다 — 실제로 URL이 틀려도 이 시점에는 아무 예외도 나지 않습니다(연결은 나중에, 값을 실제로 쓸 때 시도됩니다).

mem0/memory/main.py 소스로 확인한 `Memory.__init__` 순서는 임베더 → 벡터 저장소 → LLM입니다. 그래서 Qdrant나 Ollama 서버가 있고 없고와 무관하게, 임베더 생성이 가장 먼저 걸립니다.

**확인.** 아무도 듣지 않는 로컬 프록시로 외부 네트워크를 막고, 이 config 그대로 `Memory.from_config()`를 불러봤습니다(Qdrant·Ollama 서버 없이).

```bash
MEM0_DIR="$(pwd)/.mem0_local_a" MEM0_TELEMETRY=False HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 \
ALL_PROXY=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1 \
  uv run --no-project python -c "
from mem0 import Memory
config = {'vector_store': {'provider': 'qdrant', 'config': {'collection_name': 'local-chatgpt-memory', 'host': 'localhost', 'port': 6333, 'embedding_model_dims': 768}}, 'llm': {'provider': 'ollama', 'config': {'model': 'llama3.1:latest', 'ollama_base_url': 'http://localhost:11434'}}, 'embedder': {'provider': 'ollama', 'config': {'model': 'nomic-embed-text:latest', 'ollama_base_url': 'http://localhost:11434'}}, 'version': 'v1.1'}
m = Memory.from_config(config)
"
```

직접 확인한 출력(발췌, `ollama` 패키지가 없는 상태):

```
    user_input = input(\"The 'ollama' library is required. Install it now? [y/N]: \")
EOFError: EOF when reading a line
```

mem0ai 0.1.29의 `mem0/embeddings/ollama.py`는 `ollama` 패키지가 없을 때 깔끔한 `ImportError`를 올리는 대신 `input()`으로 설치 여부를 묻습니다(패키지 소스로 확인). Streamlit처럼 표준입력이 터미널에 연결되지 않은 프로세스에서 `input()`은 즉시 `EOFError`가 됩니다 — 즉 이 앱은 사이드바에 사용자명을 입력해 55행의 `if user_id:`를 통과하는 순간(`Memory.from_config(config)`가 무조건 실행되는 지점) 이 에러로 죽습니다. (`mem0/llms/ollama.py` 쪽은 같은 상황에서 깔끔한 `ImportError`를 올리지만, 임베더가 먼저 생성되므로 여기까지 도달하지 않습니다.)

`ollama` 패키지를 설치하면 이 `EOFError`는 사라지지만, 두 번째 문제가 남습니다. mem0ai 0.1.29의 `_ensure_model_exists()`(`mem0/llms/ollama.py`·`mem0/embeddings/ollama.py` 양쪽에 같은 코드가 있음, 패키지 소스로 확인)는 이렇게 모델이 이미 있는지 봅니다:

```python
local_models = self.client.list()["models"]
if not any(model.get("name") == self.config.model for model in local_models):
    self.client.pull(self.config.model)
```

오늘 설치되는 `ollama` 0.6.2의 `list()`는 각 모델을 `name`이 아니라 `model` 필드를 가진 pydantic 객체로 돌려줍니다 — `.get("name")`은 항상 `None`이라 비교가 절대 참이 될 수 없습니다.

```bash
uv pip install ollama --python <스크래치 venv>/Scripts/python.exe
uv run --no-project python -c "
from ollama._types import ListResponse
m = ListResponse.Model(model='llama3.1:latest')
print('get(name):', m.get('name'))
print('get(model):', m.get('model'))
"
```

직접 확인한 출력:

```
get(name): None
get(model): llama3.1:latest
```

즉 `llama3.1:latest`가 로컬에 이미 있어도 `_ensure_model_exists()`는 항상 `self.client.pull(...)`을 호출합니다 — 사용자를 바꿔 사이드바가 다시 `Memory.from_config()`를 부를 때마다(51~53행) 반복됩니다. 이 문서는 이 왕복을 임의의 높은 포트(127.0.0.1:61076)에 `/api/tags`·`/api/pull`·`/api/chat`·`/api/embeddings`·`/api/generate`를 흉내 내는 로컬 스텁 서버로 안전하게 재현했습니다(진짜 Ollama 모델을 내려받지 않습니다) — `/api/tags`가 두 모델이 이미 있다고 정확히 답해도, `/api/pull`을 구현하지 않은 첫 시도는 다음처럼 실패해 `pull()`이 실제로 불린다는 것을 보여줍니다.

```
ollama._types.ResponseError: not found (status code: 404)
```

`/api/pull`에 성공 응답을 추가하면 `Memory.from_config(config)`는 정상적으로 끝납니다(Step 6에서 이어서 씁니다).

![Step 2까지의 구성](diagrams/step2.svg)

### Step 3. Streamlit 페이지 뼈대와 세션 상태

**목적.** 제목·캡션이 무엇을 보여주는지, 그리고 대화 기록과 "이전 사용자" 추적이 어떤 세션 상태 키에 담기는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:36-43`

```python
st.title("Local ChatGPT using Llama 3.1 with Personal Memory 🧠")
st.caption("Each user gets their own personalized memory space!")

# Initialize session state for chat history and previous user ID
if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_user_id" not in st.session_state:
    st.session_state.previous_user_id = None
```

`messages`는 화면에 보이는 대화 기록(리스트)이고, `previous_user_id`는 사이드바에서 사용자명이 바뀌었는지 비교하는 데만 쓰입니다(Step 4). 둘 다 mem0와는 별개의, 브라우저 세션 동안만 사는 상태입니다 — mem0/Qdrant에 저장되는 "기억"과 화면에 보이는 "대화 기록"은 서로 다른 저장소라는 뜻입니다.

![Step 3까지의 구성](diagrams/step3.svg)

**확인.**

```bash
grep -n "st.session_state" local_chatgpt_memory.py
```

직접 확인한 출력(발췌):

```
40:if "messages" not in st.session_state:
41:    st.session_state.messages = []
42:if "previous_user_id" not in st.session_state:
43:    st.session_state.previous_user_id = None
```

### Step 4. 사이드바 — 사용자별 메모리 공간

**목적.** 사용자명이 바뀔 때 화면 대화 기록이 어떻게 초기화되는지, 그리고 "View My Memory" 버튼이 무엇을 부르는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:45-69`

```python
# Sidebar for user authentication
with st.sidebar:
    st.title("User Settings")
    user_id = st.text_input("Enter your Username", key="user_id")
    
    # Check if user ID has changed
    if user_id != st.session_state.previous_user_id:
        st.session_state.messages = []  # Clear chat history
        st.session_state.previous_user_id = user_id  # Update previous user ID
    
    if user_id:
        st.success(f"Logged in as: {user_id}")
        
        # Initialize Memory with the configuration
        m = Memory.from_config(config)
        
        # Memory viewing section
        st.header("Memory Context")
        if st.button("View My Memory"):
            memories = m.get_all(user_id=user_id)
            if memories and "results" in memories:
                st.write(f"Memory history for **{user_id}**:")
                for memory in memories["results"]:
                    if "memory" in memory:
                        st.write(f"- {memory['memory']}")
```

48행의 `user_id`는 로그인이 아니라 텍스트 입력창일 뿐입니다 — 같은 이름을 입력하면 다른 브라우저에서도 같은 메모리에 접근합니다(별도 인증 없음, 소스로 확인). 51행은 Streamlit이 매 상호작용마다 스크립트를 처음부터 다시 실행한다는 점을 이용합니다 — 입력값이 이전 실행 때와 다르면(사용자를 바꾸면) 화면 대화 기록만 비웁니다. **mem0에 저장된 메모리는 지워지지 않습니다** — `user_id`로 스코프될 뿐 Qdrant 컬렉션에는 예전 사용자의 메모리도 그대로 남습니다. 59행은 매 재실행마다 새 `Memory` 객체를 만듭니다 — Step 2에서 본 두 버그(누락된 `ollama` 패키지, 항상 시도되는 `pull`) 모두 사용자명을 입력하는 이 순간 발생합니다.

![Step 4까지의 구성](diagrams/step4.svg)

**확인.**

```bash
grep -n "st.text_input\|st.button" local_chatgpt_memory.py
```

직접 확인한 출력:

```
48:    user_id = st.text_input("Enter your Username", key="user_id")
63:        if st.button("View My Memory"):
```

### Step 5. 채팅 히스토리 렌더와 사용자 입력

**목적.** 로그인 후 메인 영역이 무엇을 보여주고, 새 메시지가 어디서 들어오는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:71-86`

```python
# Main chat interface
if user_id:  # Only show chat interface if user is "logged in"
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("What is your message?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

```

72행의 `if user_id:`는 55행과 별개의 검사이지만 같은 값을 봅니다 — 사용자명이 없으면 이 블록 전체(74~134행)를 건너뛰고 else 블록만 실행됩니다(Step 8). 79행의 바다코끼리 연산자(`:=`)는 `chat_input`이 새 메시지를 돌려줄 때만 안쪽 블록을 실행합니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.**

```bash
grep -n "st.chat_message\|st.chat_input" local_chatgpt_memory.py
```

직접 확인한 출력:

```
75:        with st.chat_message(message["role"]):
79:    if prompt := st.chat_input("What is your message?"):
84:        with st.chat_message("user"):
99:        with st.chat_message("assistant"):
```

### Step 6. 프롬프트를 메모리에 저장하고 컨텍스트 구성

**목적.** 사용자 메시지가 mem0에 어떻게 들어가고, 과거 메모리가 어떻게 컨텍스트 문자열로 바뀌는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:87-96`

```python
        # Add to memory
        m.add(prompt, user_id=user_id)
        
        # Get context from memory
        memories = m.get_all(user_id=user_id)
        context = ""
        if memories and "results" in memories:
            for memory in memories["results"]:
                if "memory" in memory:
                    context += f"- {memory['memory']}\n"
```

88행의 `m.add(prompt, ...)`가 91행의 `m.get_all(...)`보다 먼저 실행되므로, 방금 보낸 메시지에서 뽑힌 사실이 같은 턴의 컨텍스트에 곧바로 포함될 수 있습니다 — 첫 메시지도 예외가 아닙니다. 93행의 `"results" in memories`는 config가 `"version": "v1.1"`이므로 항상 dict를 받는다는 전제 위에서만 안전합니다(Day 073의 config는 이 키가 없어 기본값 `"v1.0"`이 되고 `get_all()`이 리스트를 돌려줘 이 검사가 항상 거짓이 됐습니다).

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** Step 2의 두 버그를 우회한 상태(`ollama` 패키지 설치 + 스텁 서버가 `/api/pull`에 성공 응답)에서, Qdrant Docker 대신 로컬 파일 모드(`path=`)와 Ollama 대신 같은 스텁 서버(127.0.0.1:61076)로 이 왕복을 그대로 재현했습니다.

```bash
uv run --no-project python -c "
from mem0.memory.main import Memory
config = {
    'vector_store': {'provider': 'qdrant', 'config': {'collection_name': 'local-chatgpt-memory', 'path': './.qdrant_local', 'embedding_model_dims': 768}},
    'llm': {'provider': 'ollama', 'config': {'model': 'llama3.1:latest', 'ollama_base_url': 'http://localhost:61076'}},
    'embedder': {'provider': 'ollama', 'config': {'model': 'nomic-embed-text:latest', 'ollama_base_url': 'http://localhost:61076'}},
    'version': 'v1.1',
}
m = Memory.from_config(config)
print(m.add('I love hiking on weekends', user_id='alice'))
print(m.get_all(user_id='alice'))
"
```

직접 확인한 출력(발췌):

```
{'results': [{'id': '817c6a9a-...', 'memory': 'User loves hiking on weekends', 'event': 'ADD'}], 'relations': []}
{'results': [{'id': '817c6a9a-...', 'memory': 'User loves hiking on weekends', 'hash': '...', 'metadata': None, 'created_at': '...', 'updated_at': None, 'user_id': 'alice'}]}
```

두 응답 모두 `"results"` 키를 가진 dict입니다 — 93행의 검사가 실제로 통과한다는 뜻입니다.

### Step 7. LiteLLM로 Ollama 스트리밍 응답 생성

**목적.** `completion(...)`이 정확히 어느 엔드포인트를 부르는지, 그리고 스트리밍 청크를 어떻게 텍스트로 모으는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:98-128`

```python
        # Generate assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            try:
                response = completion(
                    model="ollama/llama3.1:latest",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant with access to past conversations. Use the context provided to give personalized responses."},
                        {"role": "user", "content": f"Context from previous conversations with {user_id}: {context}\nCurrent message: {prompt}"}
                    ],
                    api_base="http://localhost:11434",
                    stream=True
                )
                
                # Process streaming response
                for chunk in response:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        content = chunk.choices[0].delta.get('content', '')
                        if content:
                            full_response += content
                            message_placeholder.markdown(full_response + "▌")
                
                # Final update
                message_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
                full_response = "I apologize, but I encountered an error generating the response."
                message_placeholder.markdown(full_response)
```

106행의 `model="ollama/"` 접두사는 litellm의 "ollama" provider를 고릅니다 — litellm 1.80.0 소스(`llms/ollama/completion/transformation.py`)로 확인하면 이 provider는 `/api/generate`(텍스트 완성용 엔드포인트)를 부릅니다. `ollama_chat/` 접두사였다면 `/api/chat`을 불렀을 것입니다. 이 경로는 mem0와 달리 `ollama` PyPI 패키지에 의존하지 않습니다 — litellm이 직접 HTTP 요청을 만들기 때문에, Step 2의 두 버그와 무관하게 동작합니다. 117~118행의 스트리밍 파싱도 소스로 확인했습니다 — litellm은 `done: true`인 마지막 청크의 텍스트를 항상 빈 문자열로 처리하므로(정상 동작), 마지막 청크에서 `content`가 비어 있는 것은 버그가 아닙니다.

![Step 7까지의 구성](diagrams/step7.svg)

**확인.** 같은 스텁 서버(127.0.0.1:61076)의 `/api/generate`가 `done: false`인 청크 하나(텍스트 포함)와 `done: true`인 마지막 청크를 순서대로 보내도록 하고, 이 코드를 그대로 실행했습니다.

```bash
uv run --no-project python -c "
from litellm import completion
response = completion(
    model='ollama/llama3.1:latest',
    messages=[{'role': 'user', 'content': 'hi'}],
    api_base='http://localhost:61076',
    stream=True,
)
full_response = ''
for chunk in response:
    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
        content = chunk.choices[0].delta.get('content', '')
        if content:
            full_response += content
print(repr(full_response))
"
```

직접 확인한 출력:

```
'FAKE_OLLAMA_GENERATE_REPLY'
```

### Step 8. 응답을 다시 메모리에 저장

**목적.** 어시스턴트 응답이 화면 기록과 mem0 양쪽에 어떻게 반영되는지, 그리고 로그인 전 화면은 무엇을 보여주는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:130-137`

```python
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        # Add response to memory
        m.add(f"Assistant: {full_response}", user_id=user_id)

else:
    st.info("👈 Please enter your username in the sidebar to start chatting!")
```

134행은 88행과 같은 패턴으로, 이번에는 어시스턴트의 답변 앞에 `"Assistant: "`를 붙여 저장합니다 — mem0의 사실 추출 프롬프트에는 화자 구분이 없으므로, 이 접두사가 사실 추출 결과에 어떤 영향을 주는지는 모델 출력에 달려 있습니다(소스로는 확인했지만 실제 사실 추출 결과까지 결정하지는 못했습니다). 136~137행은 72행의 조건이 거짓일 때(사용자명 미입력)만 실행됩니다.

![Step 8까지의 구성](diagrams/step8.svg)

**확인.** Step 6·7의 스텁 서버로 두 번째 `add()`까지 이어서 실행했습니다.

```bash
uv run --no-project python -c "
# Step 6에서 만든 m, alice의 컨텍스트를 이어서 사용
m.add('Assistant: FAKE_OLLAMA_GENERATE_REPLY', user_id='alice')
print(m.get_all(user_id='alice'))
"
```

직접 확인한 출력(발췌, `results` 배열에 항목이 2개로 늘어남):

```
{'results': [{'id': '817c6a9a-...', 'memory': 'User loves hiking on weekends', ...}, {'id': '9b7de5b2-...', 'memory': 'User loves hiking on weekends', ...}]}
```

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

사용자가 메시지를 보내면 Streamlit UI는 먼저 mem0에 `add(prompt, user_id)`를 넘깁니다. mem0는 내부적으로 Ollama에 사실 추출을 요청하고, 뽑힌 사실을 Qdrant에 임베딩·저장합니다. 이어서 UI는 `get_all(user_id)`로 그 사용자의 전체 메모리를 Qdrant에서 다시 조회해 컨텍스트 문자열을 만듭니다. UI는 이 컨텍스트와 프롬프트를 LiteLLM의 `completion(stream=True)` 호출에 넘기고, LiteLLM은 Ollama의 `POST /api/generate`로 요청해 토큰 스트림을 받아 UI에 청크 단위로 돌려줍니다. UI는 완성된 답변을 렌더링한 뒤, 그 답변을 다시 `add(assistant 응답, user_id)`로 mem0에 넘기고, mem0는 같은 절차(사실 추출 → Qdrant 저장)를 반복합니다. Step 2에서 직접 확인했듯, 오늘 기준 설치에서는 이 그림의 첫 화살표(mem0 → Ollama)에 이르기 전에 이미 `Memory.from_config()` 자체가 `EOFError`(또는 우회 후 항상 시도되는 `pull`)로 막히므로, 실제로는 이 왕복 전체가 두 버그를 우회해야만 완주됩니다 — 그림은 코드가 원래 의도한 구조를 보여줍니다.

## 실행 체크리스트

- [ ] `uv venv && uv pip install -r requirements.txt`만으로 `streamlit`·`litellm`·`mem0ai` 임포트가 성공하고 파일이 그대로 컴파일된다는 것을 확인했다
- [ ] `requirements.txt`와 mem0ai 배포 메타데이터 어디에도 `ollama` 패키지가 없어 `import ollama`가 실패한다는 것을 직접 확인했다
- [ ] `ollama` 패키지가 없으면 사용자명을 입력하는 순간(`Memory.from_config`) `EOFError`로 앱이 죽는다는 것을 직접 재현했다(mem0/embeddings/ollama.py가 ImportError 대신 input()을 씀)
- [ ] `ollama` 0.6.2의 응답 객체가 `name`이 아니라 `model` 필드를 써서, mem0ai 0.1.29의 `_ensure_model_exists()`가 모델이 이미 있어도 항상 `pull`을 시도한다는 것을 직접 확인했다
- [ ] config의 `"version": "v1.1"` 덕분에 `get_all()`이 dict를 돌려주고, Day 073에서 본 dict/list 불일치가 이 앱에는 없다는 것을 직접 확인했다
- [ ] litellm의 `ollama/` provider가 `/api/generate`를 부르고, `ollama` PyPI 패키지 없이도 동작한다는 것을 소스와 재현으로 확인했다
- [ ] 로컬 스텁 서버로 `add → get_all → completion → add` 전체 왕복이 설계대로 동작한다는 것을 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| 사이드바에 사용자명을 입력하자마자 `EOFError: EOF when reading a line`로 앱이 죽음 | mem0ai 0.1.29의 `mem0/embeddings/ollama.py`가 `ollama` 패키지 부재 시 `ImportError` 대신 `input()`으로 설치 여부를 묻는데, `requirements.txt`에 이 패키지가 없고 Streamlit 프로세스는 표준입력이 연결돼 있지 않음(직접 확인) | 리포 코드는 고치지 않음 — `uv pip install ollama`로 별도 설치 |
| `ollama` 패키지 설치 후에도, 사용자를 바꿀 때마다(=`Memory` 재생성) 이미 있는 모델에 대해 `pull` 요청이 나감 | mem0ai 0.1.29의 `_ensure_model_exists()`가 `model.get("name")`으로 모델 존재를 확인하는데, 오늘 설치되는 `ollama` 0.6.2의 응답 객체는 `name`이 아니라 `model` 필드를 씀 — 비교가 항상 거짓이 되어 매번 pull 시도(직접 확인) | 리포 코드는 고치지 않음 — 진짜 Ollama와 함께 쓰면 매번 재검증 트래픽이 생긴다는 것만 유의 |
| 스트리밍 응답의 마지막 청크에서 `content`가 항상 빈 문자열 | litellm 1.80.0의 `ollama/` provider는 `done: true`인 마지막 청크의 텍스트를 무조건 빈 문자열로 처리함(소스로 확인) — 버그가 아니라 정상 동작 | 코드 변경 불필요 |

## 더 해보기

- 진짜 Ollama를 설치하고(`ollama pull llama3.1`·`ollama pull nomic-embed-text`) `uv pip install ollama`까지 마친 뒤, 실제 Qdrant Docker와 함께 앱을 띄워 두 사용자명으로 전환하며 메모리가 사용자별로 분리되는지 확인해보기
- mem0ai 0.1.29의 `mem0/llms/ollama.py`·`mem0/embeddings/ollama.py`를 로컬에서 몽키패치해 `model.get("name")`을 `model.get("model")`로 고치고, `_ensure_model_exists()`가 더 이상 불필요한 `pull`을 하지 않는지 확인해보기
- `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/local_chatgpt_memory.py:106`의 모델 이름을 로컬에 실제로 있는 다른 Ollama 모델로 바꿔, 코드의 나머지 부분을 고치지 않고도 동작하는지 확인해보기

## 다음 날 예고

[Day 077 · 🎯 AI Career Coach with Memory (ADK Multi-Agent)](../day077-adk-career-coach-agent-memory/README.md) — 이 볼륨의 마지막 날로, Google ADK 멀티에이전트가 진로 상담에 메모리를 사용하는 앱을 다룹니다.
