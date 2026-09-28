# Day 077 · 🎯 AI Career Coach with Memory (ADK Multi-Agent)

> 볼륨 6 💾 LLM Apps with Memory · 난이도 ★★☆ · 예상 소요 65분 · API 비용 대략 $0.1 이하(이 문서는 실제 키·네트워크 호출 없이 대부분 로컬로 재현) · 원본 앱: `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory`

## 오늘 만들 것

"💾 LLM Apps with Memory" 볼륨의 마지막 날입니다. Day 072·073·075·076은 모두 `mem0ai`가 그날그날 다른 방식으로 고장 났습니다 — Day 072는 Qdrant config의 없는 필드로 즉시 `ValidationError`, Day 073·075는 `mem0ai==0.1.29`가 오늘 기준 `qdrant-client`의 `.search()` 제거로 `AttributeError`, Day 076은 Ollama provider가 별도 패키지를 요구해 `EOFError`였습니다. 오늘 앱(`adk_career_coach_agent_memory.py`, 312줄)은 `mem0ai==2.0.14`로 훨씬 최신 버전을 못박고, `llm`·`embedder`를 둘 다 명시적으로 Gemini로, `vector_store`를 Docker 없는 온디스크 Qdrant로 지정합니다 — 그 결과 `Memory.from_config(...)`가 실제로 예외 없이 성공하고 `get_all()`도 이 앱이 기대하는 `{"results": [...]}` 형태를 그대로 돌려줍니다(직접 확인, Step 4). 이 볼륨에서 mem0 설정 자체가 처음으로 별 탈 없이 맞물리는 날입니다. 대신 오늘의 진짜 주제는 **Google ADK의 멀티 에이전트**입니다 — Day 021(`8_simple_multi_agent`)에서 `sub_agents=`(전환, 복귀 보장 없음)와 `AgentTool`(호출-복귀)이 서로 다른 메커니즘이라는 것을 소스와 실행으로 확인했는데, 오늘 `career_orchestrator`는 이력서·인터뷰·스킬 로드맵·연봉 네 전문가를 **전부 `sub_agents=`로만** 붙입니다 — `AgentTool`은 코드 어디에도 없습니다(그렙 확인). 즉 오늘 앱은 Day 021이 다룬 두 메커니즘 중 한쪽만 골라 쓴, 더 단순한 라우터입니다. 여기에 mem0 기억이 끼어드는 지점이 특이합니다 — Day 073·075가 검색 결과를 프롬프트 문자열에 직접 이어 붙였다면, 오늘 앱은 그 결과를 `"Candidate email: ...\nRelevant past information:\n...\nCandidate says: ..."` 형식으로 다듬어(`format_memories`, 226-231행) ADK 메시지 자체에 실어 보냅니다. 기억을 쓰는 방향도 다릅니다: Day 073은 AI의 답변만, Day 075는 질문과 답변을 각각 별도로 `memory.add()`했지만, 오늘은 **후보자의 질문만** 저장합니다(308행) — 코드 주석이 그 이유를 "메모리는 후보자에 대한 사실만 담아야 하고, 호출을 절반으로 줄여 추출 비용도 아낀다"고 직접 밝힙니다. `requirements.txt` 4줄(버전 고정은 `mem0ai`뿐)로 오늘(2026-09-28) 설치하면 **streamlit 1.64.0**, **google-adk 2.10.0**, **mem0ai 2.0.14**, **qdrant-client 1.19.1**이 받아지고 파일도 그대로 컴파일됩니다(직접 확인, Step 1). API 키 없이도 이 문서는 `Memory.from_config`가 실제로 어디서 멈추는지, 네 에이전트가 정말 전부 형제 `sub_agents`인지, 그리고 모델 응답을 흉내 낸 콜백으로 "질문 → 위임 → 도구 호출 → 답변"이 실제로 어떻게 흐르는지를 전부 직접 실행해 확인합니다. 완성하면 브라우저에는 Google API 키 입력창 하나, 사이드바의 이메일 입력과 "View my memory" 버튼, 그리고 채팅창이 뜹니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Google API 키 (`GOOGLE_API_KEY`) | 네 에이전트의 `gemini-3.7-flash` 채팅, mem0 내부의 사실 추출(같은 모델)과 임베딩(`models/gemini-embedding-001`)까지 전부 이 키 하나로 커버 | https://aistudio.google.com/apikey 에서 발급, 화면의 "Enter Google API Key" 입력창에 붙여넣기 |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 참고 |

Qdrant는 Docker나 별도 서버가 필요 없습니다 — `MEM0_CONFIG`가 `path="./qdrant_storage"`로 지정한 온디스크 모드라, 첫 실행 시 스크립트 옆에 폴더가 자동으로 생깁니다(소스로 확인, Step 4).

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 사용자 (브라우저) | 이메일·질문 입력, 답변·사이드바 확인 | 코드 없음 (외부 UI) |
| Streamlit UI | 제목·키 입력·사이드바·채팅 렌더링 | `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:234-278` |
| `career_orchestrator` + Runner (ADK) | 메시지를 읽고 전문가 넷 중 하나에게 위임 | `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:119-223` |
| 전문가 에이전트 4개 (`LlmAgent` + 목업 도구) | 이력서·인터뷰·스킬·연봉 각각 답변 | `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:85-172` |
| mem0 Memory 계층 (Gemini LLM + Gemini 임베더) | 후보자별 과거 정보 검색·저장 | `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:19-37`, `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:208-215` |
| Qdrant 저장소 (온디스크) | 후보자별 메모리 벡터 저장 | `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:28-36` (config), 코드 없음 (로컬 폴더 `qdrant_storage/`) |
| Gemini API | 네 에이전트의 추론, mem0의 사실 추출·임베딩 | 코드 없음 (외부 서비스) |

## 단계별 진행

### Step 1. 환경 만들기 — `mem0ai`만 고정된 4줄

**목적.** 격리된 가상환경에 의존성을 설치하고, 파일이 그대로 컴파일되는지, 오늘 기준으로 어떤 버전이 받아지는지 확인합니다.

**할 일.**

```bash
cd advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory
uv venv
uv pip install -r requirements.txt
```

```powershell
cd advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory
uv venv
uv pip install -r requirements.txt
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Windows PowerShell은 활성화만 `.venv\Scripts\Activate.ps1`로 바꿉니다.) 원본 앱 README는 이 자리에서 `pip install -r requirements.txt`를 그대로 안내하지만, `uv venv`로 새로 만든 가상환경에는 `pip`이 기본으로 들어 있지 않아 그대로 치면 `No module named pip`으로 실패합니다(Day 014에서 이미 확인한 것과 같은 원인) — 그래서 `uv pip install`을 씁니다. 이 저장소는 루트에 `pyproject.toml`이 있어 `uv run`이 방금 만든 환경 대신 루트 `.venv`를 쓰므로, 이후 `uv run` 명령에는 모두 `--no-project`를 붙입니다.

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/requirements.txt:1-4`

```text
streamlit
google-adk
mem0ai==2.0.14
qdrant-client
```

4줄 중 버전이 고정된 것은 `mem0ai`뿐입니다. 이 문서를 쓰며 설치했을 때는 **streamlit 1.64.0**, **google-adk 2.10.0**, **mem0ai 2.0.14**, **qdrant-client 1.19.1**이 받아졌고, 의존성 충돌 경고는 없었습니다(직접 확인, 2026-09-28 기준).

**그림.**

![Step 1까지의 구성](diagrams/step1.svg)

**확인.**

```bash
uv run --no-project python -m py_compile adk_career_coach_agent_memory.py && echo compiled
uv run --no-project python -c "
import streamlit, google.adk, mem0
import importlib.metadata as m
print('streamlit', streamlit.__version__)
print('google-adk', google.adk.__version__)
print('mem0ai', m.version('mem0ai'))
print('qdrant-client', m.version('qdrant-client'))
"
```

직접 확인한 출력:

```
compiled
streamlit 1.64.0
google-adk 2.10.0
mem0ai 2.0.14
qdrant-client 1.19.1
```

### Step 2. 목업 데이터와 전문가별 도구 함수

**목적.** 네 전문가가 호출하는 함수 도구가 실제로는 하드코딩된 딕셔너리를 조회할 뿐이라는 것을 확인합니다. 함수를 그대로 도구로 쓰는 방식 자체는 Day 017(`4_2_function_tools`)에서 이미 다뤘으므로, 여기서는 이 앱의 데이터 모양만 봅니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:85-90`

```python
def get_candidate_resume(candidate_email: str) -> dict:
    """Fetches the resume on file for a candidate (experience, current role, skills, bullet points)."""
    resume = MOCK_RESUMES.get(candidate_email.strip().lower())
    if resume:
        return {"status": "success", "candidate_email": candidate_email, "resume": resume}
    return {"status": "error", "message": f"No resume on file for {candidate_email}."}
```

나머지 세 함수(`get_practice_question`, `get_learning_resource`, `get_salary_benchmark`, `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:93-116`)도 같은 모양입니다 — 입력을 소문자로 정규화해 딕셔너리를 찾고, 없으면 `{"status": "error", ...}`를 돌려줍니다. 원본이 되는 딕셔너리 네 개(`MOCK_INTERVIEW_QUESTIONS`·`MOCK_LEARNING_RESOURCES`·`MOCK_SALARY_DATA`·`MOCK_RESUMES`, `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:40-82`)는 앱 README도 밝히듯 실제 이력서·문제은행·연봉 데이터를 대신하는 스텁입니다. 이 모듈에는 후보자가 `demo@example.com` 단 하나뿐입니다(`MOCK_RESUMES`).

**그림.**

![Step 2까지의 구성](diagrams/step2.svg)

**확인.**

```bash
uv run --no-project python -c "
from adk_career_coach_agent_memory import get_candidate_resume, get_practice_question
print(get_candidate_resume('demo@example.com'))
print(get_candidate_resume('nobody@example.com'))
print(get_practice_question('Amazon', 'System Design'))
"
```

직접 확인한 출력(임포트 시점에 `Memory`나 `LlmAgent`를 만들지 않으므로 키 없이도 성공):

```
{'status': 'success', 'candidate_email': 'demo@example.com', 'resume': {'years_experience': 4, 'current_role': 'Backend Engineer', 'skills': ['Python', 'PostgreSQL', 'REST APIs', 'Docker'], 'bullet_points': ['Worked on the payments team maintaining backend services.', 'Helped onboard new engineers to the codebase.']}}
{'status': 'error', 'message': 'No resume on file for nobody@example.com.'}
{'status': 'success', 'company': 'Amazon', 'interview_type': 'System Design', 'question': 'Design a URL shortener that can handle millions of requests per day.'}
```

### Step 3. 전문가 네 명 + 오케스트레이터 — 전부 `sub_agents`

**목적.** `career_orchestrator`가 네 전문가를 붙이는 방식이 Day 021의 `sub_agents=`/`AgentTool` 중 어느 쪽인지, 그리고 그 결과 전환 대상이 실제로 어떻게 얽히는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:121-135`

```python
    resume_agent = LlmAgent(
        name="resume_agent",
        model=MODEL,
        description="Reviews a candidate's resume and gives feedback tailored to a target role.",
        instruction=(
            "You help candidates improve their resume. Use the get_candidate_resume tool, "
            "passing the 'Candidate email' given in the message context, to fetch their resume "
            "on file. Then give specific, tailored suggestions based on their years of "
            "experience, current role, and skills versus the target role -- don't just restate "
            "the resume back to them. If the candidate also pastes a specific bullet point or "
            "section they're drafting, give feedback on that text directly, using the fetched "
            "resume as context for consistency and experience level."
        ),
        tools=[get_candidate_resume],
    )
```

`interview_agent`·`skills_roadmap_agent`·`salary_agent`(`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:137-172`)도 이름·모델·설명·지시문·도구 하나씩만 다른, 같은 모양의 `LlmAgent`입니다. 이 넷을 묶는 자리는 오케스트레이터뿐입니다.

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:174-188`

```python
    career_orchestrator = LlmAgent(
        name="career_orchestrator",
        model=MODEL,
        description="Routes career coaching questions to the right specialist.",
        instruction=(
            "You are the first point of contact for a career coaching app. Read the "
            "candidate's message, including any 'Relevant past information' block included "
            "with it, and decide whether this is about resume feedback, interview practice, "
            "a skill gap/learning roadmap, or salary/negotiation. Delegate to the matching "
            "specialist. If it's genuinely unclear, ask a clarifying question yourself "
            "instead of guessing."
        ),
        sub_agents=[resume_agent, interview_agent, skills_roadmap_agent, salary_agent],
    )
    return career_orchestrator
```

`AgentTool`은 이 파일 어디에도 임포트되지 않습니다(그렙 확인) — Day 021의 `research_agent`(`AgentTool`, 호출-복귀)와 달리, 오늘 네 전문가는 전부 Day 021의 `summarizer_agent`·`critic_agent`와 같은 부류(전환, 복귀 보장 없음)입니다. 실제로 ADK 객체를 만들어 `google.adk.flows.llm_flows.agent_transfer._get_transfer_targets`로 확인하면, 네 전문가는 전부 `career_orchestrator`를 부모로 두고 **서로가 서로의 전환 대상**입니다 — `resume_agent`도 이론적으로는 `transfer_to_agent`로 `interview_agent`에게 넘길 수 있지만, 어느 지시문에도 그런 문장이 없어(그렙 확인) 실제로는 항상 자신이 받은 질문에 바로 답하고 끝납니다.

**그림.**

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 키 없이 에이전트 트리만 만들어 전환 대상을 확인합니다(모델 호출 없음).

```bash
uv run --no-project python -c "
from google.adk.flows.llm_flows.agent_transfer import _get_transfer_targets
from adk_career_coach_agent_memory import build_career_orchestrator

root = build_career_orchestrator()
print('root:', root.name, '| sub_agents:', [a.name for a in root.sub_agents])
for a in root.sub_agents:
    print(' -', a.name, '| parent:', a.parent_agent.name,
          '| transfer targets:', [t.name for t in _get_transfer_targets(a)])
"
```

직접 확인한 출력:

```
root: career_orchestrator | sub_agents: ['resume_agent', 'interview_agent', 'skills_roadmap_agent', 'salary_agent']
 - resume_agent | parent: career_orchestrator | transfer targets: ['career_orchestrator', 'interview_agent', 'skills_roadmap_agent', 'salary_agent']
 - interview_agent | parent: career_orchestrator | transfer targets: ['career_orchestrator', 'resume_agent', 'skills_roadmap_agent', 'salary_agent']
 - skills_roadmap_agent | parent: career_orchestrator | transfer targets: ['career_orchestrator', 'resume_agent', 'interview_agent', 'salary_agent']
 - salary_agent | parent: career_orchestrator | transfer targets: ['career_orchestrator', 'resume_agent', 'interview_agent', 'skills_roadmap_agent']
```

### Step 4. mem0 메모리 계층 — Gemini 하나로 LLM·임베더·저장소까지

**목적.** `MEM0_CONFIG`가 무엇을 지정하는지, 그리고 키가 없을 때 정확히 어느 줄에서 어떤 예외가 나는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:19-37`

```python
MEM0_CONFIG = {
    "llm": {
        "provider": "gemini",
        "config": {"model": MODEL, "temperature": 0.2},
    },
    "embedder": {
        "provider": "gemini",
        "config": {"model": "models/gemini-embedding-001", "embedding_dims": 768},
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "adk_career_coach",
            "path": "./qdrant_storage",
            "embedding_model_dims": 768,
            "on_disk": True,
        },
    },
}
```

`llm`·`embedder`를 둘 다 `"gemini"`로 명시했으므로 mem0는 OpenAI 기본값(Day 072·073·075가 썼던 조합) 대신 `mem0/llms/gemini.py`·`mem0/embeddings/gemini.py`(mem0ai 2.0.14 패키지 소스로 확인)를 씁니다. 이 두 클래스는 생성 시점에 곧바로 `genai.Client(api_key=...)`를 만듭니다 — Day 014에서 본 ADK 쪽 지연 검증(모델을 실제로 호출할 때만 키를 확인)과 달리, mem0 쪽은 `Memory.from_config(...)` 호출 **그 자리**에서 키를 확인합니다.

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:208-215`

```python
@st.cache_resource
def get_memory() -> Memory:
    # Embedded/on-disk Qdrant only allows one open client per storage path
    # per process (it takes a file lock) -- cache_resource makes this a
    # single instance shared by every browser session on this server,
    # instead of one per session, which would crash the 2nd concurrent
    # user with "Storage folder ... already accessed by another instance".
    return Memory.from_config(MEM0_CONFIG)
```

`@st.cache_resource`는 이 함수를 프로세스당 한 번만 실행해 결과를 재사용합니다 — 주석이 밝히듯, 온디스크 Qdrant는 저장 경로마다 파일 잠금을 하나만 허용하므로 세션마다 새로 만들면 두 번째 사용자부터 충돌합니다.

**그림.**

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** `GOOGLE_API_KEY`를 지정하지 않고 `Memory.from_config`만 호출해, 어느 컴포넌트가 먼저 실패하는지 봅니다(프록시로 외부 네트워크를 막았고, 생성자만 부르며 실제 요청 메서드는 부르지 않았습니다).

```bash
HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 uv run --no-project python -c "
from mem0 import Memory
from adk_career_coach_agent_memory import MEM0_CONFIG
Memory.from_config(MEM0_CONFIG)
"
```

직접 확인한 출력(발췌 — 트레이스백은 `mem0/embeddings/gemini.py`의 `genai.Client(api_key=api_key)`에서 끝남):

```
File "...\mem0\memory\main.py", line 466, in __init__
  self.embedding_model = EmbedderFactory.create(...)
File "...\mem0\embeddings\gemini.py", line 20, in __init__
  self.client = genai.Client(api_key=api_key)
ValueError: No API key was provided. Please pass a valid API key. ...
```

`llm`이 아니라 **임베더**가 먼저 만들어지다가 멈춥니다(`mem0/memory/main.py`의 `__init__` 순서, 패키지 소스로 확인). 화면에서 아무 문자열이나(가짜 키) 입력하면 이 지점은 통과합니다 — `genai.Client`는 키의 형식이나 유효성을 생성 시점에 검사하지 않기 때문입니다. 그 상태로 직접 확인해 보면 `Memory.from_config`가 예외 없이 성공하고, 스크립트 옆에 `qdrant_storage/`(`.lock`·`collection/`·`meta.json`)가 실제로 생깁니다.

```bash
GOOGLE_API_KEY=fake-key-123 HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 uv run --no-project python -c "
from mem0 import Memory
from adk_career_coach_agent_memory import MEM0_CONFIG
m = Memory.from_config(MEM0_CONFIG)
print('Memory OK:', type(m).__name__)
print(m.get_all(filters={'user_id': 'demo@example.com'}))
"
```

```
Memory OK: Memory
{'results': []}
```

`get_all(filters={"user_id": ...})`은 아직 메모리가 없을 때 `{"results": []}`를 돌려줍니다 — 사이드바 코드(`(memories or {}).get("results") or []`)가 기대하는 바로 그 형태입니다. 실제 벡터 검색·임베딩·사실 추출은 Gemini API에 진짜 요청을 보내야 하므로 이 문서에서는 호출하지 않았습니다(가짜 키로는 다음 단계에서 인증 오류가 납니다).

### Step 5. ADK Runner·세션과 호출 헬퍼

**목적.** `Runner`와 `InMemorySessionService`가 어떻게 만들어지고, 채팅 한 번이 이 둘을 통해 어떻게 텍스트로 바뀌는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:191-205`

```python
async def ensure_session(session_service, user_id, session_id):
    await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)


async def call_agent(runner, user_id, session_id, message_text) -> str:
    content = types.Content(role="user", parts=[types.Part(text=message_text)])
    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text
    return final_text


def run_agent_sync(runner, user_id, session_id, message_text) -> str:
    return asyncio.run(call_agent(runner, user_id, session_id, message_text))
```

`call_agent`는 이벤트 스트림을 끝까지 순회하며 `is_final_response()`인 이벤트의 텍스트만 남깁니다 — 중간에 전환이 몇 번 일어나든, Day 021에서 본 것처럼 **마지막으로 응답한 에이전트**의 텍스트가 결과가 됩니다. Streamlit은 동기 함수만 콜백으로 받으므로 `run_agent_sync`가 `asyncio.run`으로 감쌉니다.

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:218-223`

```python
@st.cache_resource
def get_runner():
    career_orchestrator = build_career_orchestrator()
    session_service = InMemorySessionService()
    runner = Runner(agent=career_orchestrator, app_name=APP_NAME, session_service=session_service)
    return runner, session_service
```

`get_memory()`와 마찬가지로 프로세스당 한 번만 만들어져 모든 브라우저 세션이 같은 `Runner`·`SessionService`를 공유합니다 — `InMemorySessionService`이므로 대화 기록 자체는 서버가 살아 있는 동안만 유지되는 짧은 기억이고, 후보자에 대한 긴 기억은 Step 4의 mem0가 따로 맡습니다.

**그림.**

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 콜백으로 모델 응답을 흉내 내(Day 021과 같은 기법, 실제 요청 없음) `resume_agent`가 도구를 부르고 끝까지 답하는 왕복을 직접 실행합니다.

```bash
PYTHONUNBUFFERED=1 uv run --no-project python -c "
import asyncio
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from adk_career_coach_agent_memory import build_career_orchestrator, ensure_session, call_agent, APP_NAME

def fn_call(name, args):
    return types.Content(role='model', parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))])
def text(t):
    return types.Content(role='model', parts=[types.Part(text=t)])

async def main():
    root = build_career_orchestrator()
    resume_agent = next(a for a in root.sub_agents if a.name == 'resume_agent')
    calls = {'root': 0, 'resume': 0}
    def root_cb(ctx, req):
        calls['root'] += 1
        return LlmResponse(content=fn_call('transfer_to_agent', {'agent_name': 'resume_agent'}))
    def resume_cb(ctx, req):
        calls['resume'] += 1
        if calls['resume'] == 1:
            return LlmResponse(content=fn_call('get_candidate_resume', {'candidate_email': 'demo@example.com'}))
        return LlmResponse(content=text('Your 4 years as a Backend Engineer line up well; tighten the payments bullet.'))
    root.before_model_callback = root_cb
    resume_agent.before_model_callback = resume_cb
    session_service = InMemorySessionService()
    runner = Runner(agent=root, app_name=APP_NAME, session_service=session_service)
    await ensure_session(session_service, 'demo@example.com', 'session-demo@example.com')
    answer = await call_agent(runner, 'demo@example.com', 'session-demo@example.com', 'Candidate email: demo@example.com\nCandidate says: review my resume')
    print('FINAL ANSWER:', answer)

asyncio.run(main())
"
```

직접 확인한 출력:

```
FINAL ANSWER: Your 4 years as a Backend Engineer line up well; tighten the payments bullet.
```

### Step 6. Streamlit 뼈대 — 키 게이트와 사이드바

**목적.** 키를 입력하기 전과 후 화면이 어떻게 다른지, 그리고 사이드바의 "View my memory"가 무엇을 보여주는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:234-252`

```python
# --- Streamlit app ---
st.title("🎯 AI Career Coach (ADK Multi-Agent + Memory)")
st.caption(
    "An orchestrator agent routes your question to a resume, interview, skills, "
    "or salary specialist (Google ADK), while Mem0 + Qdrant remember your career "
    "history across sessions."
)

google_api_key = st.text_input(
    "Enter Google API Key (for Gemini)",
    type="password",
    value=os.getenv("GOOGLE_API_KEY", ""),
)

if google_api_key:
    os.environ["GOOGLE_API_KEY"] = google_api_key

    memory = get_memory()
    runner, session_service = get_runner()
```

키를 입력하는 순간 `os.environ["GOOGLE_API_KEY"]`에 그대로 반영되고, 곧바로 `get_memory()`가 불립니다 — Step 4에서 본 대로 이 한 줄이 (가짜 키라도) 형식만 맞으면 성공하고, 정말 비어 있으면 여기서 `ValueError`가 납니다.

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:254-277`

```python
    st.sidebar.title("Candidate")
    previous_user_id = st.session_state.get("previous_user_id")
    user_id = st.sidebar.text_input("Your email", value="demo@example.com")

    if user_id != previous_user_id:
        st.session_state.messages = []
        st.session_state.previous_user_id = user_id
        st.session_state.pop("session_ready", None)

    if st.sidebar.button("View my memory"):
        memories = memory.get_all(filters={"user_id": user_id})
        results = (memories or {}).get("results") or []
        if results:
            for mem in results:
                st.sidebar.write(f"- {mem['memory']}")
        else:
            st.sidebar.info("No memory on file for you yet.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
```

이메일(`user_id`)은 로그인이 아니라 그냥 텍스트 입력창입니다(Day 073에서 이미 확인한 것과 같은 패턴) — 이메일을 바꾸면 대화 기록만 새로 시작하고, mem0의 기억은 `user_id` 문자열이 같으면 그대로 이어집니다.

**그림.**

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** 임포트만으로 화면 문자열과 함수 존재를 확인합니다(Streamlit 서버는 띄우지 않음).

```bash
uv run --no-project python -c "
import ast
src = open('adk_career_coach_agent_memory.py', encoding='utf-8').read()
tree = ast.parse(src)
titles = [n.args[0].value for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, 'attr', None) == 'title']
print('st.title 호출 문자열:', titles)
"
```

직접 확인한 출력:

```
st.title 호출 문자열: ['🎯 AI Career Coach (ADK Multi-Agent + Memory)']
```

### Step 7. 채팅 처리 — 검색 → 위임 → 응답 → 저장

**목적.** 메시지 한 번이 mem0 검색부터 저장까지 정확히 어떤 순서로 지나가는지, 그리고 왜 사용자의 질문만 저장되는지 확인합니다.

**할 일.**

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:279-294`

```python
    prompt = st.chat_input("Ask about your resume, an interview, a skill, or salary...")

    if prompt and user_id:
        session_id = f"session-{user_id}"
        if not st.session_state.get("session_ready"):
            asyncio.run(ensure_session(session_service, user_id, session_id))
            st.session_state.session_ready = True

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Long-term memory: pull what Mem0 knows about this candidate before routing.
        relevant_memories = memory.search(query=prompt, filters={"user_id": user_id}, top_k=5)
        context = format_memories(relevant_memories)
        full_message = f"Candidate email: {user_id}\n{context}\nCandidate says: {prompt}"
```

`memory.search(..., filters={"user_id": user_id}, top_k=5)`는 mem0ai 2.0.14의 현재 API를 그대로 씁니다 — `filters=` 딕셔너리, `top_k=` 키워드 모두 Day 073이 재현했던 옛 API(최상위 `user_id=`, `limit=`)와 다릅니다. `format_memories`(226-231행)가 이 결과를 "Relevant past information:" 블록으로 다듬고, 최종 메시지에 이메일·과거 정보·질문을 한 문자열로 합칩니다.

`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:296-312`

```python
        with st.chat_message("assistant"):
            with st.spinner("Routing to the right specialist..."):
                answer = run_agent_sync(runner, user_id, session_id, full_message)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

        # Write this exchange back to long-term memory for future sessions.
        # Only the candidate's own message goes in: one memory.add() call
        # instead of two (half the extraction latency/cost, since infer=True
        # runs an LLM call per add()), and the fact store stays candidate
        # facts only -- the coach's own advice text never gets treated as a
        # fact about the candidate.
        memory.add(prompt, user_id=user_id, metadata={"role": "user"})
    elif not user_id:
        st.error("Please enter your email to start chatting.")
else:
    st.warning("Please enter your Google API key to continue.")
```

`memory.add(prompt, ...)`는 `answer`가 아니라 `prompt`만 저장합니다 — 주석이 밝히듯 "후보자에 대한 사실"만 장기 기억에 남기려는 의도적인 선택이고, 호출도 한 번뿐이라 `infer=True`가 매 `add()`마다 돌리는 LLM 추출 호출도 절반입니다. Day 073(답변만 저장)·Day 075(질문·답변 각각 저장)와 비교하면 오늘 앱이 세 번째 선택지를 씁니다.

**그림.**

![Step 7까지의 구성](diagrams/step7.svg)

**확인.** `format_memories`가 검색 결과 유무에 따라 어떤 문자열을 만드는지 직접 봅니다.

```bash
uv run --no-project python -c "
from adk_career_coach_agent_memory import format_memories
print(repr(format_memories({'results': [{'memory': 'targets fintech backend roles'}, {'memory': 'weak at system design interviews'}]})))
print(repr(format_memories({'results': []})))
"
```

직접 확인한 출력:

```
'Relevant past information:\n- targets fintech backend roles\n- weak at system design interviews\n'
''
```

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

사용자가 채팅창에 질문을 보내면, Streamlit UI는 곧바로 mem0 Memory에 `search(query, filters={"user_id": ...})`를 호출합니다. mem0는 내부적으로 Gemini 임베딩과 Qdrant 벡터 검색을 거쳐 관련 메모리 목록을 돌려주고(Step 4), UI는 이를 `format_memories`로 다듬어 질문과 합친 메시지를 `career_orchestrator`의 Runner에 넘깁니다. 오케스트레이터는 Gemini 모델 호출로 어느 전문가가 맡을지 정하고 `transfer_to_agent`로 제어를 넘깁니다 — Day 021에서 확인했듯 이 전환에는 복귀 보장이 없고, 오늘 앱의 전문가들은 실제로도 되돌아가지 않습니다. 위 그림은 이력서 질문이 `resume_agent`로 넘어간 경우를 보여줍니다: 이 에이전트는 먼저 도구 호출을 결정하는 모델 호출을 하고, ADK가 로컬 함수 `get_candidate_resume`을 실행한 뒤, 그 결과를 포함한 두 번째 모델 호출로 최종 텍스트를 얻습니다. 이 텍스트가 그대로 UI에 최종 응답으로 돌아가 화면에 표시됩니다. 마지막으로 UI는 사용자의 **질문만**(응답은 제외) `memory.add()`로 mem0에 다시 넘기고, mem0는 Gemini로 사실을 추출·임베딩해 Qdrant에 저장합니다 — 다음에 같은 사용자가 관련 질문을 하면 이 사실이 검색 결과에 포함됩니다. Step 4·5에서 확인했듯 이 문서는 가짜 키로 `Memory.from_config`와 에이전트 구조까지만 재현했고, 실제 Gemini 응답·임베딩 요청은 보내지 않았습니다.

## 실행 체크리스트

- [ ] `uv venv && uv pip install -r requirements.txt`(원본 README의 `pip install`이 아니라)로 4개 패키지가 설치되고 파일이 그대로 컴파일된다는 것을 확인했다
- [ ] 네 전문가 에이전트가 전부 `sub_agents=`로만 붙고 `AgentTool`은 쓰지 않는다는 것을, 그리고 서로가 서로의 전환 대상이라는 것을 `_get_transfer_targets`로 확인했다
- [ ] `Memory.from_config`가 임베더 생성 시점에 `GOOGLE_API_KEY`를 확인하고, 형식만 맞는 가짜 키로는 통과한다는 것을 직접 재현했다
- [ ] `get_all(filters={"user_id": ...})`이 이 앱이 기대하는 `{"results": [...]}` 형태를 그대로 돌려준다는 것을 확인했다(Day 073의 dict/list 불일치가 오늘은 없다)
- [ ] 콜백으로 모델을 흉내 내 "질문 → 위임 → 도구 호출 → 최종 텍스트" 전체 왕복을 키 없이 재현했다
- [ ] `memory.add()`가 답변이 아니라 사용자의 질문만 저장한다는 것과 그 이유를 코드 주석으로 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `uv venv`로 만든 환경에서 원본 README대로 `pip install -r requirements.txt`를 치면 `No module named pip` | `uv venv`가 만드는 가상환경에는 `pip`이 기본으로 들어 있지 않음(Day 014와 같은 원인, 직접 확인) | `uv pip install -r requirements.txt`를 대신 사용 |
| 화면에서 아무 키도 입력하지 않았는데 "Enter Google API Key" 아래에 아무 반응이 없음 | `if google_api_key:` 게이트가 빈 문자열을 거짓으로 보고 `get_memory()`·`get_runner()`를 아예 호출하지 않음(소스로 확인, 242-252행) | 정상 동작 — 키를 입력해야 `st.warning("Please enter your Google API key to continue.")` 대신 앱 본문이 뜬다 |
| 형식만 맞는 가짜 키를 넣으면 `Memory.from_config`는 성공하지만 실제 채팅에서는 인증 오류가 남 | `genai.Client(api_key=...)`가 생성 시점에는 키의 유효성을 검사하지 않고, 실제 요청을 보낼 때만 Gemini가 거부함(직접 확인, Step 4) | 실제 Google API 키를 발급해 입력 |
| Streamlit을 두 번째 프로세스로 띄우면 `Memory.from_config`가 "Storage folder ... already accessed by another instance"로 실패할 수 있음 | 온디스크 Qdrant는 저장 경로(`./qdrant_storage`)마다 파일 잠금을 하나만 허용함(코드 주석 210-214행, `get_memory` 자체가 `@st.cache_resource`로 이를 프로세스당 한 번으로 막음) | 같은 폴더에서 Streamlit 프로세스를 하나만 띄운다 |

## 더 해보기

- `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:308`의 `memory.add(prompt, ...)` 옆에 `memory.add(answer, user_id=user_id, metadata={"role": "assistant"})`를 사본에 추가해, Day 075처럼 질문·답변을 각각 저장하도록 바꿔보고 "View my memory"에 어떤 차이가 나타나는지 비교해보기
- `advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:186`의 `sub_agents=[...]` 중 하나(예: `resume_agent`)를 Day 021처럼 `tools=[AgentTool(resume_agent)]`로 바꾼 사본을 만들어, `_get_transfer_targets`로 전환 대상이 어떻게 달라지는지 확인해보기
- 새 전문가(예: "negotiation_agent")를 추가해 `sub_agents=`에 넣고, 오케스트레이터의 지시문(`advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/adk_career_coach_agent_memory.py:178-185`)에 위임 규칙을 한 줄 보태 실제로 라우팅되는지 확인해보기(원본 앱 README의 "Notes / next steps"가 제안하는 확장과 같은 방향)

## 다음 날 예고

오늘로 "💾 LLM Apps with Memory" 볼륨이 끝납니다. 내일부터는 Day 078~111의 34일간 이어지는 "🚀 Advanced AI Agents" 볼륨입니다.

[Day 078 · 📈 AI Investment Agent](../day078-ai-investment-agent/README.md) — 새 볼륨의 첫 날로, 단일 에이전트로 돌아가 투자 정보를 다룹니다.
