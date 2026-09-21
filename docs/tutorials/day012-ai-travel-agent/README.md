# Day 012 · 🛫 AI Travel Agent (Local & Cloud)

> 볼륨 1 🌱 Starter AI Agents · 난이도 ★★☆ · 예상 소요 60분 · API 비용 대략 일정 1회 생성에 gpt-4o 호출 2회 + SerpAPI 검색 3회, 요금표 기준 수백 원대 (키가 없어 실제 과금은 확인 못함) · 원본 앱: `starter_ai_agents/ai_travel_agent`

## 오늘 만들 것

이번 튜토리얼은 **에이전트 둘을 파이프라인으로 잇는** Streamlit 앱입니다. Day 11이 같은 모델을 네 페르소나로 네 번 부르고 그 답을 합성 없이 나열했다면, 이 앱은 둘뿐인 에이전트를 순서대로 부르되 **앞 에이전트의 출력을 뒤 에이전트의 입력에 문자열로 끼워 넣습니다** — Researcher가 웹을 뒤져 만든 요약이 Planner의 프롬프트 안에 `Research Results:` 줄로 박혀 들어갑니다. 둘의 역할 분담은 프롬프트가 아니라 **도구 보유 여부**로 갈립니다. Researcher만 `SerpApiTools`를 들고 있고 Planner는 도구가 없어서, Planner는 검색을 할 수 없고 오직 넘겨받은 텍스트만 보고 일정을 씁니다(직접 확인: `planner tools: []`).

폴더에는 진입점이 둘 있습니다 — gpt-4o를 쓰는 `travel_agent.py`(158줄, 마지막 줄에 개행이 없어 `wc -l`은 157로 셉니다)와 로컬 Ollama를 쓰는 `local_travel_agent.py`(154줄, 역시 개행 없음)입니다. 두 파일은 모델 한 줄과 키 입력창 개수만 다르고 나머지는 사실상 같습니다. 다만 "로컬"이라는 이름과 달리 로컬 버전도 **SerpAPI 키는 그대로 필요합니다** — 앱 자체 README의 "without sending data to external APIs"라는 설명과 어긋나는 지점이라 "문제 해결"에 따로 정리했습니다.

Day 1~11에 없던 새 요소도 하나 있습니다. 생성된 일정 텍스트를 정규식으로 `Day N` 단위로 쪼개 **`.ics` 캘린더 파일로 내려받는** 순수 파이썬 함수 `generate_ics_content()`입니다. LLM도 네트워크도 타지 않는 코드라 키 없이 그대로 실행해 검증할 수 있었고, 실제로 돌려 본 결과와 거기서 발견한 규격 위반까지 아래에 적었습니다. 완성하면 목적지와 일수를 넣어 일정을 받고 그 일정을 캘린더 앱으로 가져갈 수 있는 화면을 로컬에서 띄우게 됩니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| OpenAI API 키 | `travel_agent.py`의 두 에이전트가 쓰는 gpt-4o 호출 인증. 환경변수가 아니라 화면 입력창에 붙여넣는다 | https://platform.openai.com/ 가입 후 발급 |
| SerpAPI 키 | Researcher가 `search_google` 도구로 실제 웹 검색을 할 때 쓴다. **클라우드·로컬 두 버전 모두 필요** | https://serpapi.com/ 가입 후 발급 |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| (선택) Ollama | `local_travel_agent.py`로 LLM만 로컬에서 돌리고 싶을 때 필요 | https://ollama.com/ 설치 후 `ollama pull llama3.2` |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 사용자 | 브라우저에서 키 2개, 목적지, 일수 입력 | 코드 없음 (브라우저) |
| Streamlit UI | 입력을 받고 버튼 클릭에 두 에이전트를 순서대로 실행 | `starter_ai_agents/ai_travel_agent/travel_agent.py:61-73` |
| Researcher Agent | 검색어 3개를 만들고 SerpAPI로 검색해 상위 10건을 요약 | `starter_ai_agents/ai_travel_agent/travel_agent.py:76-95` |
| Planner Agent | 넘겨받은 요약만 보고 일정 초안을 작성 (도구 없음) | `starter_ai_agents/ai_travel_agent/travel_agent.py:96-115` |
| 일정 저장소 | 생성된 일정을 리런 사이에 유지 | `starter_ai_agents/ai_travel_agent/travel_agent.py:143` |
| ICS 변환기 | 일정 텍스트를 `Day N` 단위 종일 일정으로 쪼개 `.ics` 생성 | `starter_ai_agents/ai_travel_agent/travel_agent.py:12-59` |
| OpenAI API (gpt-4o) | 검색어 생성·결과 분석·일정 작성 | 코드 없음 (외부 서비스) |
| SerpAPI | 실제 웹 검색 수행 | 코드 없음 (외부 서비스) |

## 단계별 진행

### Step 1. 환경 만들기

**목적.** 의존성을 설치하고, `requirements.txt`에 적혀 있지만 이 저장소 루트 환경에는 빠져 있는 두 패키지를 미리 확인합니다.

**할 일.**

```bash
cd starter_ai_agents/ai_travel_agent
uv venv
uv pip install -r requirements.txt
```

`requirements.txt`는 6줄(`streamlit`, `agno>=2.2.10`, `openai`, `ollama`, `google-search-results`, `icalendar`)이고 마지막 줄에 개행이 없습니다. 버전이 고정된 것은 `agno>=2.2.10` 하나뿐이며, 이 문서를 쓰며 확인했을 때 실제로 설치된 것은 **agno 2.3.2**였습니다(직접 확인).

여기서 이 저장소 특유의 함정을 짚습니다. 루트(`awesome-llm-apps/`)에 `pyproject.toml`과 `uv.lock`이 있어 uv는 그쪽을 프로젝트 루트로 봅니다(Day 2의 "문제 해결"에 자세히 적어 두었습니다). 그래서 루트 `.venv`를 그대로 쓰면 `agno`·`openai`·`ollama`·`streamlit`은 이미 들어 있지만 **`google-search-results`와 `icalendar`는 빠져 있습니다** — 직접 확인한 결과 두 패키지 모두 `PackageNotFoundError`였고, `uv pip install google-search-results icalendar`로 각각 2.4.2와 7.3.0을 받아 해결했습니다.

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 앱이 쓰는 import 여섯 줄을 그대로 실행해 봅니다.

```bash
uv run python -c "
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.serpapi import SerpApiTools
from agno.models.openai import OpenAIChat
from agno.models.ollama import Ollama
from icalendar import Calendar, Event
print('ok')
"
```

```
ok
```

Day 1·8·11과 달리 이번에는 여섯 줄이 한 번에 통과했습니다(직접 확인). 단 위의 두 패키지를 설치하기 **전**이라면 `from agno.tools.serpapi import SerpApiTools`에서 ``ImportError: `google-search-results` not installed.``이 납니다 — agno가 `agno/tools/serpapi.py` 맨 위에서 `import serpapi`를 try로 감싸고 그 메시지로 바꿔 던지기 때문입니다.

### Step 2. 키 두 개와 세션 상태

**목적.** 이 앱이 키를 **두 개** 받는다는 점과, 생성된 일정을 리런 사이에 살려 두는 `st.session_state`를 봅니다.

**할 일.**

`starter_ai_agents/ai_travel_agent/travel_agent.py:61-73`

```python
# Set up the Streamlit app
st.title("AI Travel Planner ")
st.caption("Plan your next adventure with AI Travel Planner by researching and planning a personalized itinerary on autopilot using GPT-4o")

# Initialize session state to store the generated itinerary
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

# Get OpenAI API key from user
openai_api_key = st.text_input("Enter OpenAI API Key to access GPT-4o", type="password")

# Get SerpAPI key from the user
serp_api_key = st.text_input("Enter Serp API Key for Search functionality", type="password")
```

Day 2·11의 앱은 키 하나만 받았지만 여기는 둘이고, 이후 코드 전체가 `if openai_api_key and serp_api_key:`(75행) 안에 들어 있어 **둘 다** 넣기 전에는 목적지 입력창조차 나타나지 않습니다.

`st.session_state`가 등장하는 이유는 Streamlit의 리런 모델 때문입니다. 버튼을 누르거나 입력이 바뀔 때마다 스크립트가 처음부터 다시 실행되므로, 일정을 평범한 지역 변수에 담아 두면 다음 리런에서 사라집니다. 66-67행이 첫 실행에서만 `None`으로 초기화하고 143행이 생성된 일정을 여기에 넣어 두는 덕분에, 일정 생성 후 리런이 일어나도 내려받기 버튼이 유지됩니다(148행의 `if st.session_state.itinerary:`).

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** 서버를 띄우고 응답을 확인합니다.

```bash
uv run streamlit run travel_agent.py --server.headless true
```

다른 터미널에서:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501
```

```
200
```

### Step 3. 도구를 가진 에이전트와 갖지 않은 에이전트

**목적.** 두 에이전트의 차이가 프롬프트가 아니라 도구 보유 여부에 있다는 것을 확인합니다.

**할 일.**

`starter_ai_agents/ai_travel_agent/travel_agent.py:75-95`

```python
if openai_api_key and serp_api_key:
    researcher = Agent(
        name="Researcher",
        role="Searches for travel destinations, activities, and accommodations based on user preferences",
        model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
        description=dedent(
            """\
        You are a world-class travel researcher. Given a travel destination and the number of days the user wants to travel for,
        generate a list of search terms for finding relevant travel activities and accommodations.
        Then search the web for each term, analyze the results, and return the 10 most relevant results.
        """
        ),
        instructions=[
            "Given a travel destination and the number of days the user wants to travel for, first generate a list of 3 search terms related to that destination and the number of days.",
            "For each search term, `search_google` and analyze the results.",
            "From the results of all searches, return the 10 most relevant results to the user's preferences.",
            "Remember: the quality of the results is important.",
        ],
        tools=[SerpApiTools(api_key=serp_api_key)],
        add_datetime_to_context=True,
    )
```

핵심은 `tools=[SerpApiTools(api_key=serp_api_key)]`(93행) 한 줄입니다. 이 줄이 있어서 Researcher는 Day 1의 도구 호출 루프를 그대로 탑니다 — 모델이 `search_google` tool_call을 돌려주면 agno가 로컬에서 SerpAPI를 실제로 호출하고, 결과를 다시 모델에 보내 최종 요약을 받습니다. `SerpApiTools`가 실제로 노출하는 도구는 `search_google`과 `search_youtube` 둘이고 기본값은 구글만 켜져 있습니다(`enable_search_google=True`, `enable_search_youtube=False`, 직접 확인). 지시문 87행이 부르는 이름도 정확히 `search_google`이라 서로 맞습니다.

반면 Planner(96-115행)에는 `tools=` 인자 자체가 없습니다. 그래서 Planner는 검색을 할 수 없고, Step 4에서 문자열로 받은 검색 요약만 근거로 일정을 씁니다. "사실을 지어내지 말라"(112행)는 지시문이 붙어 있지만 이를 강제할 수단은 없습니다.

한 가지 더 — `SerpApiTools(api_key=...)`에 키를 주지 않으면 환경변수 `SERP_API_KEY`를 찾고, 그마저 없으면 예외 대신 `No Serpapi API key provided` 경고만 남기고 넘어갑니다(소스로 확인). 즉 키가 비어도 객체 생성은 성공하고 실제 검색 단계에서야 실패합니다.

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 두 에이전트의 도구 보유 여부를 직접 찍어 봅니다. 모델은 키가 필요 없는 로컬 Ollama로 두고 도구만 비교합니다.

```bash
uv run python -c "
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.serpapi import SerpApiTools
r = Agent(name='Researcher', model=Ollama(id='llama3.2'), tools=[SerpApiTools(api_key='dummy')])
p = Agent(name='Planner', model=Ollama(id='llama3.2'))
print('researcher tools:', [type(t).__name__ for t in (r.tools or [])])
print('planner tools:', p.tools)
"
```

```
researcher tools: ['SerpApiTools']
planner tools: []
```

### Step 4. 두 번의 순차 호출과 문자열로 이어지는 파이프라인

**목적.** 앞 에이전트의 출력이 뒤 에이전트의 프롬프트에 어떻게 들어가는지 봅니다.

**할 일.**

`starter_ai_agents/ai_travel_agent/travel_agent.py:123-144`

```python
    with col1:
        if st.button("Generate Itinerary"):
            with st.spinner("Researching your destination..."):
                # First get research results
                research_results: RunOutput = researcher.run(f"Research {destination} for a {num_days} day trip", stream=False)

                # Show research progress
                st.write(" Research completed")

            with st.spinner("Creating your personalized itinerary..."):
                # Pass research results to planner
                prompt = f"""
                Destination: {destination}
                Duration: {num_days} days
                Research Results: {research_results.content}

                Please create a detailed itinerary based on this research.
                """
                response: RunOutput = planner.run(prompt, stream=False)
                # Store the response in session state
                st.session_state.itinerary = response.content
                st.write(response.content)
```

두 호출 모두 `stream=False`라 블로킹입니다. 그래서 화면에는 `st.spinner`의 문구만 바뀌며 통째로 기다리게 됩니다 — 토큰이 흐르는 모습은 보이지 않습니다.

이 앱의 구조적 요점은 137행입니다. Researcher의 결과를 객체로 넘기는 것이 아니라 `{research_results.content}`로 **f-string에 문자열 보간**해서 Planner의 프롬프트 한가운데에 박아 넣습니다. agno의 팀이나 세션 공유 기능을 전혀 쓰지 않는, 가장 단순한 형태의 에이전트 연결입니다. 장점은 읽기 쉽다는 것이고, 단점은 Researcher의 출력이 길어지면 그대로 Planner의 입력 토큰이 된다는 것 — 중간에 자르거나 요약하는 단계가 없습니다.

`RunOutput`은 agno가 `.run()`에서 돌려주는 객체이고, 이 앱이 쓰는 것은 `.content` 하나뿐입니다. 로컬 Ollama로 Planner만 떼어 실제로 돌려 본 결과 `.content`의 타입은 `str`이었고 16.6초 만에 `Day 1:` 형식의 일정 텍스트가 돌아왔습니다(직접 확인). 이 형식이 Step 5의 정규식과 맞물립니다.

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 두 키가 없어도 파이프라인의 뒷단인 Planner만 로컬 모델로 재현할 수 있습니다.

```bash
uv run python -c "
from agno.agent import Agent
from agno.models.ollama import Ollama
planner = Agent(name='Planner', model=Ollama(id='llama3.2'),
                instructions=['Label each day exactly as Day N:', 'One short line per day.'])
out = planner.run('Destination: Busan. Duration: 3 days. Create a short itinerary.', stream=False)
print(type(out.content).__name__)
print(out.content[:200])
"
```

```
str
Day 1: Arrival in Busan, check-in to hotel, visit Busan Tower for panoramic views of the city, and explore the nearby Busan International Market.

Day 2: Visit the Haedong Yonggungsa Temple, a seaside
```

### Step 5. 일정 텍스트를 캘린더 파일로

**목적.** LLM이 쓴 자유 서식 텍스트를 정규식으로 쪼개 `.ics`로 만드는 과정을 봅니다. 이 단계는 키도 네트워크도 필요 없습니다.

**할 일.**

`starter_ai_agents/ai_travel_agent/travel_agent.py:30-32`

```python
    # Split the plan into days
    day_pattern = re.compile(r'Day (\d+)[:\s]+(.*?)(?=Day \d+|$)', re.DOTALL)
    days = day_pattern.findall(plan_text)
```

`starter_ai_agents/ai_travel_agent/travel_agent.py:43-57`

```python
        # Process each day
        for day_num, day_content in days:
            day_num = int(day_num)
            current_date = start_date + timedelta(days=day_num - 1)

            # Create a single event for the entire day
            event = Event()
            event.add('summary', f"Day {day_num} Itinerary")
            event.add('description', day_content.strip())

            # Make it an all-day event
            event.add('dtstart', current_date.date())
            event.add('dtend', current_date.date())
            event.add("dtstamp", datetime.now())
            cal.add_component(event)
```

정규식은 `Day` 뒤의 숫자를 1번 그룹으로, 다음 `Day N`이 나오기 전까지의 본문을 2번 그룹으로 잡습니다. `re.DOTALL`이 있어 본문에 줄바꿈이 들어가도 그대로 이어 붙습니다. `Day N` 패턴이 하나도 없으면 34-41행 분기로 빠져 전체 텍스트를 **한 건의 종일 일정**으로 만듭니다 — LLM이 형식을 지키지 않아도 파일은 나오되 하루짜리가 됩니다(직접 확인).

날짜는 `start_date + timedelta(days=day_num - 1)`로 계산합니다. `start_date` 기본값은 오늘이고(27-28행) Streamlit 쪽에서는 인자를 주지 않으므로(150행) **일정은 항상 오늘부터 시작합니다**. 실제 여행 날짜를 고르는 입력은 앱에 없습니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 앱의 함수를 그대로 불러 3일짜리 일정을 변환해 봅니다.

```bash
uv run python -c "
import sys, datetime
sys.path.insert(0, 'starter_ai_agents/ai_travel_agent')
import travel_agent
plan = 'Day 1: Arrive in Busan.\nDay 2: Gamcheon Culture Village.\nDay 3: Day trip to Tongyeong.'
ics = travel_agent.generate_ics_content(plan, start_date=datetime.datetime(2026, 5, 1))
print('bytes:', len(ics), '| events:', ics.decode().count('BEGIN:VEVENT'))
print([l for l in ics.decode().splitlines() if l.startswith(('SUMMARY','DTSTART','DTEND'))])
"
```

```
bytes: 592 | events: 3
['SUMMARY:Day 1 Itinerary', 'DTSTART;VALUE=DATE:20260501', 'DTEND;VALUE=DATE:20260501', 'SUMMARY:Day 2 Itinerary', 'DTSTART;VALUE=DATE:20260502', 'DTEND;VALUE=DATE:20260502', 'SUMMARY:Day 3 Itinerary', 'DTSTART;VALUE=DATE:20260503', 'DTEND;VALUE=DATE:20260503']
```

세 건이 하루씩 밀려 만들어지는 것까지 직접 확인했습니다. 다만 `DTEND`가 `DTSTART`와 **같은 날짜**라는 점은 짚고 갈 문제입니다 — "문제 해결"에 적었습니다.

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

키 두 개를 넣고 목적지와 일수를 채운 뒤 "Generate Itinerary"를 누르면, 먼저 Researcher가 gpt-4o에게 "검색어 3개를 만들고 각각 검색해 상위 10건을 뽑아라"는 지시와 함께 목적지를 보냅니다. 모델이 `search_google` tool_call을 돌려주면 agno가 로컬에서 SerpAPI를 실제로 호출하고 결과를 다시 모델에 넣어 요약을 받습니다 — Day 1에서 본 도구 호출 루프와 같은 구조이며, 검색어가 3개면 이 왕복이 여러 번 일어납니다. 요약이 끝나면 화면에는 "Research completed"만 찍히고, 그 요약 텍스트가 곧바로 Planner의 프롬프트에 문자열로 삽입됩니다. Planner는 도구가 없으므로 추가 검색 없이 단 한 번의 gpt-4o 호출로 일정을 씁니다. 결과는 `st.session_state.itinerary`에 담겨 화면에 표시되고 이후 리런에서도 살아남아 오른쪽 열의 내려받기 버튼이 유지됩니다. 버튼을 누르는 순간에는 LLM이 다시 불리지 않고, 저장된 텍스트가 `generate_ics_content()`를 통해 `.ics` 바이트로 변환될 뿐입니다.

이 흐름 중 **ICS 변환과 Planner 호출은 직접 실행해 확인했고**(각각 Step 5·Step 4의 확인), Researcher의 SerpAPI 왕복과 gpt-4o 호출은 두 키가 없어 실행하지 못했습니다 — 코드와 agno의 `serpapi` 도구 구현을 읽고 정리한 것입니다.

## 실행 체크리스트

- [ ] OpenAI 키와 SerpAPI 키를 각각 발급받아 두었다 (로컬 버전도 SerpAPI 키는 필요)
- [ ] `uv pip install -r requirements.txt` 후, 루트 `.venv`를 쓴다면 `google-search-results`와 `icalendar`가 실제로 설치됐는지 확인했다
- [ ] `uv run streamlit run travel_agent.py`로 서버를 띄우고 `http://localhost:8501`에서 화면을 확인했다
- [ ] 키를 **둘 다** 넣어야 목적지 입력창이 나타나는 것을 확인했다
- [ ] Researcher만 `tools=[SerpApiTools(...)]`를 갖고 Planner는 도구가 없다는 것을 확인했다
- [ ] 일정 생성 후 내려받기 버튼이 나타나고, 내려받은 파일에 `Day N` 수만큼 `VEVENT`가 들어 있는 것을 확인했다
- [ ] (선택) `ollama pull llama3.2` 후 `uv run streamlit run local_travel_agent.py`로 LLM만 로컬로 돌려 보았다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `from agno.tools.serpapi import SerpApiTools`에서 ``ImportError: `google-search-results` not installed.`` | `agno/tools/serpapi.py`가 맨 위에서 `import serpapi`를 try로 감싸고 실패 시 이 메시지로 바꿔 던진다. 이 저장소는 루트 `uv.lock` 환경을 쓰게 되는데 거기에 이 패키지가 없다(직접 확인: 설치 전 `PackageNotFoundError`) | `uv pip install google-search-results` (직접 확인 시 2.4.2 설치로 해결) |
| `from icalendar import Calendar, Event`에서 `ModuleNotFoundError` | 위와 같은 이유로 루트 환경에 `icalendar`가 없다(직접 확인) | `uv pip install icalendar` (직접 확인 시 7.3.0) |
| 키를 넣어도 목적지·일수 입력창이 안 보임 | 75행의 가드가 `if openai_api_key and serp_api_key:`라 두 키가 모두 채워져야 그 아래가 그려진다 | 두 입력창을 모두 채운다. 로컬 버전은 SerpAPI 키 하나만 요구한다(`local_travel_agent.py:73`) |
| 앱 자체 README가 로컬 버전을 "without sending data to external APIs"라고 설명 | 실제로는 `local_travel_agent.py:71`이 SerpAPI 키를 받고 91행이 `SerpApiTools`를 Researcher에 붙인다 — 로컬인 것은 **LLM 추론뿐**이고 검색어는 그대로 SerpAPI로 나간다(소스로 확인) | 완전한 오프라인이 목적이라면 Researcher의 도구를 로컬 검색으로 바꾸거나 Researcher 단계를 빼야 한다 |
| 내려받은 `.ics`를 캘린더 앱에 넣었는데 일정이 안 보이거나 이상하게 표시됨 | 54-55행이 `dtstart`와 `dtend`에 같은 날짜를 넣는다(직접 확인: `DTSTART;VALUE=DATE:20260501`과 `DTEND;VALUE=DATE:20260501`). RFC 5545에서 날짜형 `DTEND`는 비포함이라 종일 일정 하루를 표현하려면 다음 날이어야 한다 | `event.add('dtend', (current_date + timedelta(days=1)).date())`로 고친다. 실제 캘린더 앱에서의 표시 차이는 확인하지 못했고, 규격과 생성된 바이트까지만 확인했다 |
| 일정이 하루짜리 한 건으로만 만들어짐 | LLM 응답에 `Day N` 패턴이 없으면 34-41행 분기로 빠져 전체를 한 건의 종일 일정으로 만든다(직접 확인: 패턴 없는 텍스트로 `VEVENT` 1건) | 프롬프트에 각 날을 정확히 `Day N:`으로 시작하라는 지시를 추가한다. Step 4의 확인에서 로컬 모델에도 같은 지시를 줘서 형식을 맞췄다 |
| 일정 날짜가 실제 여행일과 다름 | `start_date` 기본값이 오늘이고(27-28행) Streamlit 호출부(150행)가 인자를 주지 않아 항상 오늘부터 시작한다 | 출발일을 받는 `st.date_input`을 추가해 `generate_ics_content(..., start_date=...)`로 넘긴다 |

## 더 해보기

- 출발일을 고르는 `st.date_input`을 추가하고 150행의 호출에 `start_date`로 넘겨, 일정이 오늘이 아니라 실제 출발일부터 만들어지게 고쳐보기
- `dtend`를 하루 뒤로 바꾼 뒤 구글 캘린더에 실제로 가져와 표시가 어떻게 달라지는지 확인해보기
- Researcher의 출력을 Planner 프롬프트에 통째로 넣는 137행을, 길이를 재서 일정 길이 이상이면 잘라내거나 요약하는 단계로 바꿔보고 토큰 사용량을 비교해보기
- `local_travel_agent.py`의 `Ollama(id="llama3.2")`(77행)를 `gemma3:12b`나 `qwen3:8b` 같은 더 큰 로컬 모델로 바꿔, 같은 프롬프트에서 `Day N` 형식을 얼마나 안정적으로 지키는지 비교해보기

## 다음 날 예고

[Day 013 · 🔍 OpenAI Research Agent](../day013-openai-research-agent/README.md) — 검색과 요약을 스스로 반복하며 조사 보고서를 만드는 에이전트를 다룹니다.
