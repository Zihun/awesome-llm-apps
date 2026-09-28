# Day 084 · 📑 AI Meeting Agent

> 볼륨 7 🚀 Advanced AI Agents · 난이도 ★★☆ · 예상 소요 65분(CrewAI가 이 시리즈에 처음 등장해 `Agent`·`Task`·`Crew`·`Process.sequential` 개념을 새로 설명해야 하고, `anthropic` 패키지 부재와 모델 폐기라는 두 겹의 실패를 직접 재현하는 손 시간이 듭니다) · API 비용 대략 산정 불가(코드에 박힌 `claude-3-5-sonnet-20240620`이 2025-10-28 공식 폐기되어 그대로는 호출 자체가 되지 않습니다 — 문제 해결 참고) · 원본 앱: `advanced_ai_agents/single_agent_apps/ai_meeting_agent`

## 오늘 만들 것

이 앱은 186줄(마지막 줄에 개행이 없어 `wc -l`은 185로 세지만 편집기·GitHub에서는 186번째 줄까지 보입니다, 직접 확인) 단일 파일 Streamlit 앱으로, 이 시리즈에 CrewAI를 처음 소개합니다 — `Agent`(역할·목표·배경 이야기), `Task`(지시문과 기대 출력), `Crew`(에이전트와 Task를 묶어 실행), `Process.sequential`(Task를 순서대로 실행) 네 어휘를 오늘 처음 씁니다. 앱은 회사명·회의 목표·참석자·소요 시간·주요 관심사를 입력받아, 같은 `claude` LLM 객체를 공유하는 에이전트 4개 — 컨텍스트 분석(`context_analyzer`), 산업 분석(`industry_insights_generator`), 전략 수립(`strategy_formulator`), 경영진 브리핑(`executive_briefing_creator`) — 를 차례로 돌려 회의 준비 자료를 만듭니다. 이 중 검색 도구(`SerperDevTool`)를 쥔 것은 앞의 두 에이전트뿐이고(코드에서 `tools=[search_tool]`이 있는 것도 이 둘뿐입니다, 직접 확인), 전략·브리핑 에이전트는 도구 없이 앞 단계의 결과만으로 씁니다. `Process.sequential`은 각 Task의 `context` 필드를 명시하지 않으면(오늘 코드가 그렇습니다) 이전 Task들의 출력을 자동으로 다음 Task의 컨텍스트에 이어 붙입니다 — crewai 자신의 `NOT_SPECIFIED` 기본값과 `Crew._get_context`가 하는 일입니다(소스로 확인, crewai 1.15.22). 오늘 재현에서 겹으로 확인한 문제가 둘 있습니다. 첫째, `requirements.txt` 4줄(`streamlit`, `crewai`, `crewai-tools`, `openai`)에는 Anthropic 모델을 쓰는 코드에 정작 필요한 `anthropic` 패키지가 빠져 있습니다 — crewai의 `LLM` 팩토리는 모델 이름이 `claude-`로 시작하면 네이티브 Anthropic 공급자(`AnthropicCompletion`)로 라우팅하는데, 이 클래스를 불러오는 모듈이 `anthropic` SDK를 최상단에서 `import`하고 없으면 즉시 `ImportError`를 던집니다 — 이 오류는 `try/except`로 감싸이지 않고 `LLM.__new__` 밖으로 그대로 빠져나갑니다(소스로 확인, crewai 1.15.22). 그 결과 사이드바에 키 2개를 모두 입력하는 순간(Streamlit이 스크립트를 다시 실행하는 순간) 22행의 `LLM(...)` 생성에서 앱이 그대로 죽습니다 — 회의 정보 입력창도, Prepare Meeting 버튼도 뜨기 전입니다(직접 재현, Step 3). 둘째, `anthropic` 패키지를 따로 설치해 이 문제를 넘겨도 코드가 못박은 스냅샷 `claude-3-5-sonnet-20240620`은 Anthropic 공식 문서 기준 2025-10-28부로 **폐기(retired)** 되어 있습니다 — 권장 대체는 `claude-sonnet-4-6`입니다(Anthropic 공식 모델 폐기 문서로 확인). 앱 자체 README는 "OpenAI의 GPT-4와 Anthropic의 Claude를 함께 쓴다"고 소개하지만, `meeting_agent.py`에는 OpenAI 모델을 만드는 코드가 한 줄도 없습니다(그렙으로 확인) — `requirements.txt`의 `openai`는 crewai가 내부적으로 갖고 있는 네이티브 OpenAI 공급자용 지연 의존성일 뿐, 이 앱의 실행 경로에서는 쓰이지 않습니다. 완성하면 사이드바에 키 입력창 2개, 본문에 회의 정보 입력창 5개와 Prepare Meeting 버튼이 뜨고, 버튼을 누르면(키와 모델이 온전하다는 전제 아래) 네 에이전트가 순서대로 실행되며 마지막에 실행 결과가 마크다운으로 표시됩니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Anthropic API 키 | 네 에이전트가 공유하는 `claude` LLM 객체 인증(코드에 박힌 스냅샷은 폐기되어 최신 모델로 바꿔야 실제 호출이 됩니다 — 문제 해결) | https://console.anthropic.com 가입 후 발급, 사이드바 입력창에 붙여넣기 |
| Serper API 키 | `SerperDevTool`이 컨텍스트·산업 분석 에이전트의 웹 검색에 사용 | https://serper.dev 가입 후 발급(무료 크레디트 2,500회), 사이드바 입력창에 붙여넣기 — 이 문서는 키 없이 진행합니다 |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| 인터넷 연결 | PyPI 설치, Anthropic API 호출, Serper 검색, crewai 자체 사용 통계 전송(문제 해결) | 별도 설치 없음 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| Streamlit UI / 사이드바 키 입력 | 페이지 제목, 사이드바에 Anthropic·Serper 키 입력창 2개 | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:7-14` |
| 입력 게이트 | 키 2개가 모두 있어야 이하 코드가 실행됨 | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:17` |
| LLM (`claude`) | 4개 에이전트가 공유하는 crewai `LLM` 객체(Anthropic 네이티브 공급자로 라우팅) | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:22` |
| 검색 도구 (`SerperDevTool`) | Serper API로 웹 검색(컨텍스트·산업 분석 에이전트만 사용) | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:23` |
| 회의 정보 입력 필드 | 회사명·목표·참석자·소요 시간·포커스 5개 입력 | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:26-30` |
| 컨텍스트 분석 에이전트 (`context_analyzer`) | 회사 배경 조사(검색 도구 사용) | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:33-41` |
| 산업 분석 에이전트 (`industry_insights_generator`) | 업계 동향·경쟁 구도 분석(검색 도구 사용) | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:43-51` |
| 전략 수립 에이전트 (`strategy_formulator`) | 시간표 기반 의제·전략 수립(도구 없음, 이전 결과만 사용) | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:53-60` |
| 경영진 브리핑 에이전트 (`executive_briefing_creator`) | 최종 브리핑 작성(도구 없음, 이전 결과만 사용) | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:62-69` |
| Task 4개 | 각 에이전트에게 줄 지시문(f-string으로 입력값 삽입)과 기대 출력 | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:72-155` |
| 미팅 준비 Crew (`meeting_prep_crew`) | `Process.sequential`로 Task 4개를 순서대로 실행, 이전 출력을 자동으로 다음 컨텍스트에 전달 | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:158-163` |
| 실행 버튼 & 결과 표시 | `kickoff()` 호출과 `st.markdown(result)` | `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:166-169` |
| Claude API (Anthropic) | 4개 에이전트의 실제 추론 | 코드 없음 (외부 서비스) |
| Serper API | 웹 검색 | 코드 없음 (외부 서비스) |

## 단계별 진행

### Step 1. 환경 만들기 — `requirements.txt`에 빠진 `anthropic` 패키지

**목적.** 격리된 가상환경에 `requirements.txt`를 설치하고, 오늘 실제로 풀리는 버전에서 이 186줄이 곧바로 컴파일되는지, 그리고 Anthropic 모델을 쓰는데도 `anthropic` 패키지가 빠져 있다는 사실을 확인합니다.

**할 일.**

```bash
cd advanced_ai_agents/single_agent_apps/ai_meeting_agent
uv venv
uv pip install -r requirements.txt
```

(pip을 쓴다면 `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.)

이 저장소는 루트에 `pyproject.toml`이 있어 `uv run`이 방금 만든 환경 대신 루트의 `.venv`를 쓰므로, 이후 `uv run` 명령에는 모두 `--no-project`를 붙입니다.

![Step 1까지의 구성](diagrams/step1.svg)

**확인.**

```bash
uv run --no-project python -m py_compile meeting_agent.py && echo OK
uv run --no-project python -c "import crewai, crewai_tools, streamlit, openai; print(crewai.__version__, streamlit.__version__)"
```

직접 확인한 출력:

```
OK
1.15.22 1.64.0
```

`requirements.txt` 4줄 중 어느 것도 버전을 고정하지 않아, 이 문서를 쓰며 설치했을 때는 crewai **1.15.22**, crewai-tools **1.15.22**, streamlit **1.64.0**, openai **2.54.0**이 풀렸습니다. 눈에 띄는 점은 `anthropic` 패키지가 이 4줄 어디에도 없다는 것입니다 — 22행의 `LLM(model="claude-3-5-sonnet-20240620", ...)`은 Anthropic 모델을 쓰는데도입니다. 이 문제는 Step 3에서 실제로 재현합니다.

### Step 2. Streamlit 골격과 입력 폼 — 사이드바 키 2개, 회의 정보 5개

**목적.** 페이지 제목과 사이드바 키 입력, 그리고 키 2개가 모두 있어야 나머지 코드가 실행되는 게이트 구조를 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:1-20`

```python
import streamlit as st
from crewai import Agent, Task, Crew, LLM
from crewai.process import Process
from crewai_tools import SerperDevTool
import os

# Streamlit app setup
st.set_page_config(page_title="AI Meeting Agent 📝", layout="wide")
st.title("AI Meeting Preparation Agent 📝")

# Sidebar for API keys
st.sidebar.header("API Keys")
anthropic_api_key = st.sidebar.text_input("Anthropic API Key", type="password")
serper_api_key = st.sidebar.text_input("Serper API Key", type="password")

# Check if all API keys are set
if anthropic_api_key and serper_api_key:
    # # Set API keys as environment variables
    os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
    os.environ["SERPER_API_KEY"] = serper_api_key
```

키를 사이드바 텍스트 입력창(둘 다 `type="password"`)에서 받는 방식은 Day 083의 사이드바 키 입력과 같은 패턴입니다(되풀이하지 않습니다). `if anthropic_api_key and serper_api_key:` 게이트 안쪽(17~184행)이 이 앱의 실질적인 본문이고, 키가 하나라도 비면 186행의 `else` 경고만 뜹니다. 게이트를 통과하면 이어서 회의 정보 입력 필드 5개가 만들어집니다.

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:25-30`

```python
    # Input fields
    company_name = st.text_input("Enter the company name:")
    meeting_objective = st.text_input("Enter the meeting objective:")
    attendees = st.text_area("Enter the attendees and their roles (one per line):")
    meeting_duration = st.number_input("Enter the meeting duration (in minutes):", min_value=15, max_value=180, value=60, step=15)
    focus_areas = st.text_input("Enter any specific areas of focus or concerns:")
```

이 다섯 값은 뒤에서 Task 설명 f-string에 그대로 삽입됩니다(Step 5).

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** PATH에 저장소 루트 `.venv\Scripts`가 섞여 있으면 `streamlit`이 루트 가상환경 것을 집을 수 있으므로 먼저 빼고, 프록시 변수를 걸어 headless로 띄워 봅니다(로컬 서버만 통하게 `NO_PROXY`도 함께):

```bash
export PATH=$(echo "$PATH" | tr ":" "\n" | grep -v "/ws-llm/awesome-llm-apps/.venv" | paste -sd:)
export HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 ALL_PROXY=http://127.0.0.1:9 NO_PROXY=localhost,127.0.0.1
uv run --no-project streamlit run meeting_agent.py --server.headless true --server.address localhost --server.port 58421
```

직접 확인한 로그:

```
Uvicorn server started on localhost:58421
  You can now view your Streamlit app in your browser.
  URL: http://localhost:58421
```

`curl -s -o /dev/null -w "%{http_code}" http://localhost:58421`은 `200`을 돌려주었습니다(직접 확인) — 키 없이도 페이지 자체는 뜹니다(186행의 경고만 보입니다). `--server.address localhost`를 빼면 Streamlit이 외부 IP를 알아내려고 `checkip.amazonaws.com`에 요청을 보냅니다(Day 060에서 이미 확인한 사실, 이번 streamlit 1.64.0에서도 headless·주소 미지정 조합에서만입니다). 확인이 끝나면 프로세스를 반드시 종료하고 포트가 비었는지(`netstat -ano | grep 58421`) 봅니다.

### Step 3. 모델 연결 — 빠진 `anthropic` 패키지와 폐기된 Claude 스냅샷

**목적.** crewai의 `LLM` 팩토리가 모델 이름에서 공급자를 어떻게 추론하는지, 그리고 이 앱이 왜 두 겹으로 깨지는지(패키지 부재 → 나중에 고쳐도 모델 폐기) 소스와 재현으로 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:22-23`

```python
    claude = LLM(model="claude-3-5-sonnet-20240620", temperature= 0.7, api_key=anthropic_api_key)
    search_tool = SerperDevTool()
```

crewai 1.15.22의 `LLM.__new__`는 모델 문자열에 공급자 접두사(`anthropic/…`)가 없으면 `_infer_provider_from_model`로 넘어가는데, 이 함수는 먼저 자신의 `ANTHROPIC_MODELS` 상수 목록(오늘 버전은 `claude-sonnet-5`·`claude-opus-5` 같은 2025년 이후 모델만 담고 있어 2024년 스냅샷은 없습니다)을 보고, 없으면 `claude` 접두사 패턴으로 판정합니다 — 어느 쪽이든 결과는 `"anthropic"`입니다(소스로 확인). 이어서 `_get_native_provider("anthropic")`가 `crewai.llms.providers.anthropic.completion`에서 `AnthropicCompletion`을 불러오는데, 이 모듈은 맨 위에서 `from anthropic import Anthropic, AsyncAnthropic, ...`를 시도하고 실패하면 `ImportError('Anthropic native provider not available, to install: uv add "crewai[anthropic]"')`를 곧바로 던집니다 — 이 예외는 `LLM.__new__`의 `try/except`가 감싸는 범위 **밖**(공급자 클래스를 가져오는 줄 자체)에서 일어나므로 그대로 밖으로 전파됩니다(소스로 확인, crewai 1.15.22). 직접 재현(격리 가상환경, 프록시로 외부 요청 차단, 가짜 키만 사용):

```bash
uv run --no-project python -c "
from crewai import LLM
LLM(model='claude-3-5-sonnet-20240620', temperature=0.7, api_key='sk-fake-key-not-real')
"
```

직접 확인한 오류:

```
ImportError: Anthropic native provider not available, to install: uv add "crewai[anthropic]"
```

`uv pip install anthropic`로 패키지를 더하면(오늘 버전 **anthropic 1.8.0**) 같은 호출이 가짜 키로도 예외 없이 `LLM` 객체를 만들어 냅니다(직접 확인) — 이 시점까지는 아직 네트워크 요청이 없습니다. 하지만 패키지를 더해도 두 번째 문제가 남습니다: `claude-3-5-sonnet-20240620`은 Anthropic 공식 모델 폐기 문서 기준 **2025-08-13에 폐기 공지, 2025-10-28에 완전히 폐기(retired)** 되었고, 권장 대체는 `claude-sonnet-4-6`입니다 — "폐기(retired)"는 "요청 자체가 실패한다"는 뜻이라고 같은 문서가 명시합니다. 이 리포 코드는 고치지 않으므로, 실제로 이 앱을 돌리려면 22행의 모델 문자열을 직접 바꿔야 합니다(더 해보기).

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 위 재현 명령과 출력이 곧 확인입니다. `search_tool = SerperDevTool()`은 생성 시점에는 환경변수를 요구하지 않고, 실제 검색 호출 때 `SERPER_API_KEY`가 필요합니다(소스로 확인, `base_url="https://google.serper.dev"`).

### Step 4. 에이전트 4개 정의 — 검색 도구는 둘만

**목적.** crewai `Agent`의 `role`·`goal`·`backstory`·`llm`·`tools` 패턴을 확인하고, 4개 에이전트 중 정확히 둘만 검색 도구를 쥔다는 사실을 코드로 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:33-41`

```python
    context_analyzer = Agent(
        role='Meeting Context Specialist',
        goal='Analyze and summarize key background information for the meeting',
        backstory='You are an expert at quickly understanding complex business contexts and identifying critical information.',
        verbose=True,
        allow_delegation=False,
        llm=claude,
        tools=[search_tool]
    )
```

나머지 세 에이전트(`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:43-69`)도 같은 형태이되, `industry_insights_generator`(43-51행)만 `context_analyzer`처럼 `tools=[search_tool]`을 함께 갖고, `strategy_formulator`(53-60행)와 `executive_briefing_creator`(62-69행)는 `tools=` 자체가 없습니다 — 이 둘은 검색을 하지 않고 앞 Task들의 결과(자동 전달되는 컨텍스트)만으로 씁니다(직접 그렙으로 확인: `tools=`가 있는 줄은 2개뿐). 네 에이전트 모두 `llm=claude`로 Step 3의 같은 `LLM` 객체를 공유합니다.

![Step 4까지의 구성](diagrams/step4.svg)

**확인.**

```bash
grep -n "tools=\[search_tool\]" meeting_agent.py
```

직접 확인한 출력: 40행과 50행 두 줄만 나옵니다.

### Step 5. Task 4개와 Crew 구성 — `Process.sequential`의 자동 컨텍스트 전달

**목적.** Task 설명이 f-string으로 어떻게 입력값을 담는지, 그리고 `context`를 명시하지 않은 `Process.sequential`이 이전 Task 출력들을 어떻게 자동으로 다음 Task에 넘기는지 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:72-90`

```python
    context_analysis_task = Task(
        description=f"""
        Analyze the context for the meeting with {company_name}, considering:
        1. The meeting objective: {meeting_objective}
        2. The attendees: {attendees}
        3. The meeting duration: {meeting_duration} minutes
        4. Specific focus areas or concerns: {focus_areas}

        Research {company_name} thoroughly, including:
        1. Recent news and press releases
        2. Key products or services
        3. Major competitors

        Provide a comprehensive summary of your findings, highlighting the most relevant information for the meeting context.
        Format your output using markdown with appropriate headings and subheadings.
        """,
        agent=context_analyzer,
        expected_output="A detailed analysis of the meeting context and company background, including recent developments, financial performance, and relevance to the meeting objective, formatted in markdown with headings and subheadings."
    )
```

나머지 세 Task(`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:92-155`)도 같은 형태로, Step 2의 입력값과 `expected_output`이 각각 다릅니다. 어느 Task도 `context=`를 지정하지 않습니다 — crewai의 `Task.context` 필드 기본값은 `None`이 아니라 `NOT_SPECIFIED`라는 별도 센티널이고, `Crew._get_context`는 `task.context is NOT_SPECIFIED`일 때 그때까지 나온 모든 Task 출력을 이어붙여(`aggregate_raw_outputs_from_task_outputs`) 다음 Task의 컨텍스트로 넘깁니다(소스로 확인, crewai 1.15.22) — 그래서 세 번째·네 번째 Task는 명시적으로 참조하지 않아도 앞선 Task들의 결과를 이미 프롬프트에 포함해 받습니다. 이어서 Crew를 만듭니다.

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:157-163`

```python
    # Create the crew
    meeting_prep_crew = Crew(
        agents=[context_analyzer, industry_insights_generator, strategy_formulator, executive_briefing_creator],
        tasks=[context_analysis_task, industry_analysis_task, strategy_development_task, executive_brief_task],
        verbose=True,
        process=Process.sequential
    )
```

`agents=`와 `tasks=`는 같은 순서로 대응하고(`Process.sequential`은 `tasks` 리스트 순서대로 실행합니다), `Crew` 객체를 만드는 시점 자체는 네트워크를 쓰지 않습니다 — 직접 재현(가짜 키, 소켓·DNS 차단)에서 `Agent`·`Task`·`Crew` 생성까지 아무 요청도 나가지 않았습니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.**

```bash
uv run --no-project python -c "
from crewai import Agent, Task, Crew, LLM
from crewai.process import Process
from crewai_tools import SerperDevTool
claude = LLM(model='claude-3-5-sonnet-20240620', api_key='sk-fake-key-not-real')
a = Agent(role='x', goal='y', backstory='z', llm=claude, tools=[SerperDevTool()])
t = Task(description='d', agent=a, expected_output='e')
c = Crew(agents=[a], tasks=[t], process=Process.sequential)
print('OK', type(c).__name__)
"
```

직접 확인한 출력(사전에 `uv pip install anthropic` 필요):

```
OK Crew
```

### Step 6. 실행 버튼과 결과 표시

**목적.** `kickoff()` 호출부터 결과가 화면에 뜨기까지의 마지막 연결을 확인합니다.

**할 일.**

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:166-169`

```python
    if st.button("Prepare Meeting"):
        with st.spinner("AI agents are preparing your meeting..."):
            result = meeting_prep_crew.kickoff()        
        st.markdown(result)
```

버튼을 누르면 `meeting_prep_crew.kickoff()`가 Task 4개를 `Process.sequential`대로 실행하고(Step 5), 돌아온 `CrewOutput`을 `st.markdown(result)`가 그대로 렌더링합니다. 사이드바 아래쪽(171-184행)에는 정적인 "사용법" 안내 마크다운이 있고, 키가 하나라도 비면 185-186행의 `else` 분기가 실행됩니다.

`advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:185-186`

```python
else:
    st.warning("Please enter all API keys in the sidebar before proceeding.")
```

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** Step 2에서 headless로 띄운 페이지가 이 `else` 경고만 보여준 것이 곧 이 경로의 확인입니다(키가 없어 버튼까지는 화면에 뜨지 않습니다). `kickoff()` 자체는 유효한 키와 살아 있는 모델이 있어야 실행되므로 이 문서에서는 호출하지 않습니다.

## 요청 한 건이 흐르는 과정

한 번의 "Prepare Meeting" 클릭이 실제로는 여섯 단계를 거칩니다 — 순서대로 그렸습니다.

![1단계: 입력과 kickoff](diagrams/sequence.svg)

1단계는 사용자가 키와 회의 정보를 입력하고 `kickoff()`가 호출되는 부분만 그립니다.

![2단계: Task1 — 검색](diagrams/extra-task1a.svg)

2단계는 컨텍스트 분석 에이전트가 검색 도구로 Serper를 거쳐 회사 정보를 모으는 부분입니다.

![3단계: Task1 — Claude 호출과 반환](diagrams/extra-task1b.svg)

3단계는 모은 검색 결과를 Claude에 보내 컨텍스트 분석 markdown을 받고, Crew에 task1 출력을 돌려주는 부분입니다.

![4단계: Task2 — 검색](diagrams/extra-task2a.svg)

4단계는 산업 분석 에이전트가 같은 검색 도구로 업계 동향을 모으는 부분입니다 — Crew가 이 Task에 넘기는 지시문에는 이미 task1 출력이 컨텍스트로 포함되어 있습니다(Step 5).

![5단계: Task2 — Claude 호출과 반환](diagrams/extra-task2b.svg)

5단계는 검색 결과와 task1 출력을 함께 Claude에 보내 산업 분석 markdown을 받는 부분입니다.

![6단계: Task3](diagrams/extra-task3.svg)

6단계는 전략 수립 에이전트입니다 — 검색 도구가 없으므로 곧바로 지금까지의 출력(task1·2)을 Claude에 보내 전략·의제 markdown을 받습니다.

![7단계: Task4와 결과 표시](diagrams/extra-task4.svg)

7단계는 경영진 브리핑 에이전트가 지금까지의 출력(task1·2·3)으로 최종 브리핑을 받고, Crew가 `CrewOutput`을 Streamlit으로, Streamlit이 `st.markdown(result)`로 사용자에게 돌려주는 부분입니다.

이 일곱 그림은 소스로 읽어 구성했습니다(키가 없어 실제 실행은 확인하지 못했습니다) — `Process.sequential`이 컨텍스트를 자동으로 잇는다는 사실만 Step 5에서 crewai 소스로 직접 확인했고, 각 메시지의 정확한 타이밍(예: 검색 왕복이 끝난 뒤에만 Claude를 부르는지)은 crewai의 실행 루프 구조(`Task.execute_sync` → 에이전트 실행기 → 도구 호출 → LLM 호출) 순서를 그대로 따른 것입니다.

## 실행 체크리스트

- [ ] `uv venv && uv pip install -r requirements.txt`로 격리 환경을 만들었다
- [ ] `uv pip install anthropic`(또는 `crewai[anthropic]`)을 추가로 설치했다 — 없으면 `LLM(...)` 생성에서 바로 `ImportError`
- [ ] 22행의 `model="claude-3-5-sonnet-20240620"`을 살아 있는 모델(예: `claude-sonnet-4-6`)로 바꿨다 — 원래 스냅샷은 폐기됨
- [ ] Anthropic·Serper API 키를 발급받았다
- [ ] `uv run --no-project streamlit run meeting_agent.py`로 앱을 띄웠다(headless 확인이면 `--server.headless true --server.address localhost`)
- [ ] 사이드바에 키 2개, 본문에 회의 정보 5개를 입력했다
- [ ] Prepare Meeting을 눌러 네 에이전트가 순서대로 실행되고 결과가 마크다운으로 표시되는지 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| 키 2개를 입력하는 순간 `ImportError: Anthropic native provider not available, to install: uv add "crewai[anthropic]"` | `requirements.txt`에 `anthropic` 패키지가 빠져 있어 crewai의 네이티브 Anthropic 공급자를 불러오지 못함(직접 재현, Step 3) | `uv pip install anthropic`(리포 코드는 고치지 않음) |
| 위 문제를 고쳐도 Claude 호출 자체가 실패할 것으로 보임(키가 없어 최종 확인은 못함) | 22행에 박힌 `claude-3-5-sonnet-20240620`이 Anthropic 공식 문서 기준 2025-10-28 폐기(retired) — "요청 자체가 실패한다"고 문서가 명시 | 22행의 모델 문자열을 `claude-sonnet-4-6`(Anthropic 권장 대체) 등 살아 있는 모델로 바꿔야 함(리포 코드는 고치지 않음) |
| 앱 자체 README가 "OpenAI의 GPT-4와 Anthropic의 Claude를 함께 쓴다"고 소개하지만 실제로는 Claude만 씀 | `meeting_agent.py`에 `OpenAI(...)`나 OpenAI 모델을 만드는 코드가 없음(그렙으로 확인) — `requirements.txt`의 `openai`는 crewai의 네이티브 OpenAI 공급자용 지연 의존성일 뿐 | 리포 코드·README는 고치지 않음, 실제로는 Claude 단일 모델 앱으로 이해하면 됨 |
| `streamlit run`을 `--server.address localhost` 없이 headless로 띄우면 시작할 때 외부로 요청이 나감 | Streamlit이 headless이면서 주소를 지정하지 않으면 외부 IP를 알아내려고 `checkip.amazonaws.com`에 요청을 보냄(Day 060에서 확인, 이번 streamlit 1.64.0에서도 재확인) | headless로 띄울 때는 항상 `--server.headless true --server.address localhost`를 함께 씀 |
| 검색 결과가 비거나 도구 호출이 실패함(키가 없어 실제로는 보지 못함) | `SerperDevTool()`은 생성 시점에는 조용하지만 실제 검색 시 `SERPER_API_KEY` 환경변수를 요구함(소스로 확인) | 사이드바에 Serper 키를 입력했는지 확인 |

## 더 해보기

- `advanced_ai_agents/single_agent_apps/ai_meeting_agent/meeting_agent.py:22`의 `model="claude-3-5-sonnet-20240620"`을 `claude-sonnet-4-6`으로 바꾸고 `uv pip install anthropic` 후 실제 키로 실행해, 네 에이전트가 실제로 순서대로 도는지 확인해보기
- `strategy_formulator`와 `executive_briefing_creator`에도 `tools=[search_tool]`을 추가하면 전략·브리핑 단계가 검색 없이 앞 단계 요약만으로 쓰는 지금과 결과가 어떻게 달라지는지 비교해보기
- 네 번째 Task(`executive_brief_task`)에 `context=[context_analysis_task, executive_brief_task 자신을 뺀 나머지]`처럼 `context=`를 명시적으로 좁혀 보고, `Process.sequential`의 자동 전달과 어떻게 다른 프롬프트가 만들어지는지 비교해보기

## 다음 날 예고

[Day 085 · 🧠 AI Mental Wellbeing Agent](../day085-ai-mental-wellbeing-agent/README.md) — `advanced_ai_agents/multi_agent_apps` 폴더의 멀티 에이전트 앱으로, 여러 에이전트가 협업해 정신 건강 관련 조언을 만듭니다.
