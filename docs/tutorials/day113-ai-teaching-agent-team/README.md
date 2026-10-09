# Day 113 · 👨‍🏫 AI Teaching Agent Team

> 볼륨 8 🤝 Multi-agent Teams · 난이도 ★★★ · 예상 소요 120분(앱은 207줄이지만 이 앱은 설치만으로는 import가 막혀 고쳐야 하고, 시퀀스가 스물네 장이라 따라 읽는 데도 시간이 들고, Step 7에서 가짜 서버와 구동 스크립트를 직접 저장해 터미널 둘로 돌려 봐야 해서 읽는 시간보다 손으로 돌려 보는 시간이 더 걸립니다) · API 비용 대략 Start 한 번에 OpenAI 약 $0.01~0.02(`gpt-4o-mini`는 모델 요청이 대본 기준 10번입니다. 문서 하나가 도구 인자로 나가므로 문서당 출력 2,000~3,000토큰, 도구 결과가 다음 요청에 다시 실리는 것까지 더해 입력 합계 25,000~35,000토큰·출력 합계 10,000~14,000토큰으로 어림하고, 모델 페이지의 입력 $0.15·출력 $0.6(1M 토큰당, https://developers.openai.com/api/docs/models/gpt-4o-mini, 2026-10-09 확인)을 대입한 대략치이며 키가 없어 실제 토큰 수는 확인하지 못했습니다. Composio와 SerpAPI의 요금은 확인하지 못했습니다. 이 문서의 가짜 서버 실험은 무료) · 원본 앱: `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team`

## 오늘 만들 것

주제를 하나 적고 Start를 누르면 에이전트 넷(Professor, Academic Advisor, Research Librarian, Teaching Assistant)이 `gpt-4o-mini`로 차례로 일해 지식 정리·학습 로드맵·자료 목록·연습 문제를 각각 Google Docs 문서로 만들고, 화면에 문서 링크와 답을 보여 주는 Streamlit 앱입니다. 한 파일(`teaching_agent_team.py`, 편집기 기준 207줄)에 agno `Agent`가 넷 나오고, 문서를 만드는 도구는 Composio가 정의를 내려 주고 실행도 대신 하며, 검색은 SerpAPI입니다. 이름은 "팀"이지만 agno의 `Team`은 이 파일 어디에도 없습니다. `Team`을 쓴 앱은 어제의 Day 112입니다(처음은 Day 079). 오늘은 화면 코드가 네 에이전트의 `run()`을 한 줄씩 차례로 부르고, 넷은 서로의 출력을 보지 못합니다(Step 5).

직접 돌려 보고 알게 된 것이 여섯입니다. 첫째, `requirements.txt`를 그대로 설치하면 `openai` 핀(1.58.1)이 너무 낮아 `OpenAIChat`을 불러오는 4행에서 막히고, 그것을 고쳐도 7행의 `ArxivTools` 때문에 `arxiv`와 `pypdf`가 더 필요합니다. 이 도구는 파일 어디에서도 쓰이지 않습니다(Step 1). 둘째, Day 107에서 문제였던 `composio`와 `composio-core`의 파일 겹침은 여기서는 없습니다. 핀한 `composio==0.1.1`은 파일이 없는 껍데기이기 때문입니다(Step 1). 셋째, 키 셋을 넣어 둔 동안은 화면이 다시 그려질 때마다 Composio에 요청 4건이 나갑니다(Step 3). 넷째, 도구를 둘 만들지만 둘째(`google_docs_tool_update`)는 어느 에이전트도 쓰지 않습니다(Step 3). 다섯째, Academic Advisor의 지시문은 "knowledge base"를, Teaching Assistant의 지시문은 "roadmap"을 이어받는다고 말하지만 모델로 가는 요청에는 앞 에이전트의 결과가 없습니다(Step 5). 여섯째, 문서 링크를 뽑는 함수는 `).`나 `**`를 링크에 달아 내보내고, 링크가 없는 답은 화면에서 조용히 빠집니다(Step 7).

이 문서는 OpenAI·Composio·SerpAPI·`os-api.agno.com` 어디에도 요청을 보내지 않았습니다. 세 서비스의 주소를 내 PC의 가짜 서버로 돌리고 프록시를 막아 두었고, 막은 요청 목록은 Step 7에 있습니다. 그래서 문서의 모델 답과 도구 결과는 가짜 서버의 고정 응답이고, 실제 `gpt-4o-mini`가 도구를 이 순서로 부르는지, 실제 Composio가 이 모양으로 답하는지는 확인하지 못했습니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| Python | 이 저장소의 기준은 3.11~3.13이다. 이 문서는 3.13.3으로 확인했다 | 공통 사전 준비와 같음 |
| OpenAI API 키 | 네 에이전트의 `gpt-4o-mini` 호출 인증. 화면 사이드바의 비밀번호 칸에 붙여넣는다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:27`). 앱은 같은 값을 `os.environ["OPENAI_API_KEY"]`에도 쓴다(같은 파일 40행). 이 모델 ID는 OpenAI 공식 폐기 문서(https://developers.openai.com/api/docs/deprecations)에 올라 있지 않다(2026-10-09 공식 문서로 확인. 같은 문서에는 `gpt-4o-mini-transcribe`처럼 이름이 비슷한 다른 ID가 있다) | https://platform.openai.com/api-keys |
| Composio API 키와 Google Docs 연결 | 문서 만들기 도구의 정의를 받고 실행을 맡긴다(`teaching_agent_team.py:28`, 43~45행). 계정이 연결돼 있지 않으면 화면이 오류로 멈춘다(Step 3). 앱 README는 터미널에서 `composio add googledocs`를 시키고(앱 README 57행), 이 명령은 `composio-core`가 설치한다(entry point를 소스로 확인). 실행해 보지 못했다 | https://composio.ai (앱의 안내) |
| SerpAPI 키 | 검색 도구의 인증. 키 칸은 비어 있으면 화면이 멈추는 관문이기도 하다(`teaching_agent_team.py:29`, 35행) | https://serpapi.com/ (앱 README의 안내) |
| Google 계정 | 문서가 만들어지는 곳. 네 에이전트의 지시문이 모두 "DONT FORGET TO CREATE THE GOOGLE DOCUMENT."를 담고 있어 Start 한 번이 문서 넷으로 이어지게 설계됐다(Step 4). 이 문서는 가짜 서버만 써서 실제 문서를 만들지 않았다 | 별도 설치 없음 |
| 인터넷 연결 | PyPI 설치. 앱을 실제로 쓸 때는 OpenAI API, Composio API(그 뒤의 Google Docs), SerpAPI, agno 사용 통계 서버(`os-api.agno.com`)에 접속한다. `composio_agno`를 import하기만 해도 `backend.composio.dev`와 `pypi.org`에 접속하려 한다(Step 2, Day 107 Step 3과 같은 사실). 브라우저가 화면을 열 때 Streamlit의 사용 통계도 나간다(Day 054가 소스로 확인했고, `--browser.gatherUsageStats false`로 끈다) | 별도 설치 없음 |

이 문서의 확인 명령은 `composio`가 홈에 만드는 캐시를 임시 폴더로 돌리려고 `COMPOSIO_CACHE_DIR`를 씁니다(Day 107 사전 준비와 같습니다). 셸에 먼저 한 번 걸어 두세요.

```bash
export COMPOSIO_CACHE_DIR="$(mktemp -d)"
```

```powershell
$env:COMPOSIO_CACHE_DIR = Join-Path $env:TEMP "composio-cache"
```

PowerShell 줄은 실행해 보지 못했습니다.

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 사용자 | 브라우저에서 키 셋과 주제를 적고 Start를 누른다 | 코드 없음 (브라우저) |
| Streamlit 화면 | 사이드바 키 칸 셋, 키가 비면 멈추는 관문, 주제 입력, Start 버튼, 에이전트 넷을 차례로 부르는 블록, 링크 뽑기와 결과 표시 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:24-37`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:119-207` |
| Composio 도구 준비 | `ComposioToolSet`을 만들고 `get_tools`를 두 번 불러 도구 둘을 받는다. 화면이 다시 그려질 때마다 돈다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:42-48` |
| 문서 만들기 도구 | `GOOGLEDOCS_CREATE_DOCUMENT`를 감싼 `Toolkit`. 네 에이전트가 같은 객체를 쥔다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:44` |
| 문서 고치기 도구 | `GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT`를 감싼 `Toolkit`. 만들어지기만 하고 어느 에이전트에도 연결되지 않는다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:45` |
| 검색 도구 (`SerpApiTools`) | Research Librarian과 Teaching Assistant이 각자 새로 만들어 쥔다. 함수는 `search_google` 하나다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:89`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:106` |
| Professor | 주제의 기초 지식을 정리해 문서로 만든다. 도구는 문서 만들기 하나 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:50-64` |
| Academic Advisor | 학습 로드맵을 문서로 만든다. 도구는 문서 만들기 하나 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:66-82` |
| Research Librarian | 검색으로 학습 자료를 모아 문서로 만든다. 도구는 문서 만들기와 검색 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:84-99` |
| Teaching Assistant | 검색으로 예제를 찾아 연습 자료를 문서로 만든다. 도구는 문서 만들기와 검색 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:101-117` |
| 링크 뽑기 함수 (`extract_google_doc_link`) | 응답 본문에서 `https://docs.google.com` 뒤를 공백까지 잘라 돌려준다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:156-161` |
| OpenAI API | 네 에이전트의 모델. `gpt-4o-mini` | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:54`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:70`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:88`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:105` |
| Composio API | 도구 정의를 내려 주고 도구 실행을 대신한다. 그 뒤에서 Google Docs를 부른다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:43-45` |
| PyPI | `composio`를 import한 프로세스가 끝날 때 버전을 확인하러 접속한다. import 때는 `backend.composio.dev`에 sentry 설정도 조회한다 | 코드 없음 (`composio` 내부) |
| SerpAPI | `search_google`의 검색 서비스 | 코드 없음 (외부 서비스, agno `SerpApiTools`가 부름) |
| Agno 사용 통계 API | 성공한 `run`마다 agno가 익명 메타데이터를 보내려 한다 | 코드 없음 (agno 내부) |

한 파일 안의 부품은 한 묶음으로 두고 묶음에서 나가는 화살표만 그렸습니다. 안쪽 호출은 보조 구조 그림 다섯 장에 있습니다. 첫째는 도구 준비입니다.

![도구 준비](diagrams/extra-prepare.svg)

둘째는 화면이 에이전트 넷을 부르고, 에이전트가 도구를 쥐는 관계입니다.

![에이전트와 도구](diagrams/extra-agents.svg)

셋째는 도구가 외부 서비스로 가는 길입니다.

![도구가 닿는 곳](diagrams/extra-tools.svg)

넷째와 다섯째는 에이전트마다 나가는 모델 요청과 통계입니다.

![모델 요청](diagrams/extra-models.svg)

![사용 통계](diagrams/extra-agno.svg)

## 단계별 진행

### Step 1. 환경 만들기 — 설치만으로는 import 셋이 막힙니다

**목적.** 앱 폴더에 독립 가상환경을 만들고, 파일이 컴파일되고 임포트가 통과하는지 확인합니다. 오늘은 통과하지 않습니다.

**할 일.** 저장소 루트에서 시작합니다.

```bash
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team
uv venv
uv pip install -r requirements.txt
```

(pip 대안: bash는 `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`입니다. PowerShell 5.1은 `&&`를 받지 않으므로(PowerShell 7부터 지원) 세 줄로 `python -m venv .venv`, `.venv\Scripts\Activate.ps1`, `pip install -r requirements.txt`를 차례로 씁니다. 실행해 보지 못했습니다.) 이후 `uv run`에는 모두 `--no-project`를 붙입니다. 이유는 [공통 사전 준비](../README.md#공통-사전-준비-한-번만)에 있습니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/requirements.txt:1-9`

```text
streamlit==1.41.1
openai==1.58.1
duckduckgo-search>=6.4.2,<9
typing-extensions>=4.5.0
agno>=2.2.10
composio-agno==0.7.20
composio_core
composio==0.1.1
google-search-results==2.4.2
```

9줄이고 마지막 줄에 개행이 없어 `wc -l`은 8로 셉니다. 버전을 못 박은 것은 `streamlit`(1.41.1), `openai`(1.58.1), `composio-agno`(0.7.20), `composio`(0.1.1), `google-search-results`(2.4.2)입니다. 오늘(2026-10-09) Python 3.13.3에서 패키지 104개가 깔렸고 agno 3.1.2, composio-core 0.7.21, duckduckgo-search 8.1.1이 풀렸습니다(직접 확인). 눈여겨볼 것이 넷입니다.

하나, `composio==0.1.1`은 파일이 없는 껍데기입니다. 메타데이터의 요약이 "Shim for composio-core."이고 `composio-core`에 의존할 뿐이며, 설치된 파일 목록에는 `.dist-info` 파일만 있습니다(직접 확인, 아래). `composio/` 폴더는 `composio-core`(0.7.21)가 설치합니다. Day 107은 버전 없는 `composio`가 0.22.0으로 풀려 `composio-core`와 같은 파일 12개를 겹쳐 쓰는 문제를 다뤘는데(Day 107 Step 1), 핀한 이 앱에서는 그 겹침이 없습니다. 둘, `duckduckgo-search`와 `typing-extensions`는 이 앱 어디에서도 쓰이지 않습니다(`grep`으로 소스에서 확인). 셋, `openai==1.58.1`은 오늘의 agno와 맞지 않습니다. agno의 `OpenAIChat`이 있는 `agno.models.openai`는 불러올 때 `openai.types.responses`도 불러오는데(`agno/models/openai/responses.py` 26행) 1.58.1에는 이 모듈이 없습니다. agno 3.1.2의 `openai` extra는 `openai>=1.106.0`을 요구합니다(패키지 메타데이터로 확인). 요구 파일의 하한인 agno 2.2.10으로 설치해도 같은 오류가 났습니다(직접 확인). 넷, 7행의 `ArxivTools`를 불러오려면 `arxiv`와 `pypdf`가 필요한데(`agno/tools/arxiv.py` 8~16행) 요구 파일에 없습니다.

**확인.** 앱 폴더에서 실행합니다. 먼저 설치된 버전과 컴파일입니다.

```bash
uv run --no-project python -c "
import sys
from importlib.metadata import version
print(sys.version.split()[0])
for name in ('agno', 'streamlit', 'openai', 'composio', 'composio-agno', 'composio-core', 'google-search-results', 'duckduckgo-search'):
    print(name, version(name))
"
uv run --no-project python -m py_compile teaching_agent_team.py && echo compiled
uv pip show -f composio
```

직접 확인한 출력(버전은 설치하는 날의 최신입니다. `uv pip show`의 `Location` 줄은 환경마다 다릅니다):

```
3.13.3
agno 3.1.2
streamlit 1.41.1
openai 1.58.1
composio 0.1.1
composio-agno 0.7.20
composio-core 0.7.21
google-search-results 2.4.2
duckduckgo-search 8.1.1
compiled
Name: composio
Version: 0.1.1
Requires: composio-core
Files:
  composio-0.1.1.dist-info/INSTALLER
  composio-0.1.1.dist-info/METADATA
  composio-0.1.1.dist-info/RECORD
  composio-0.1.1.dist-info/REQUESTED
  composio-0.1.1.dist-info/WHEEL
  composio-0.1.1.dist-info/top_level.txt
```

(출력의 `Location`·`Required-by` 줄은 줄였습니다.) PowerShell은 둘째 줄을 `uv run --no-project python -m py_compile teaching_agent_team.py; if ($?) { echo compiled }`로 씁니다(실행해 보지 못했습니다). 컴파일은 통과합니다. 이제 앱의 1~9행이 하는 임포트를 그대로 해 봅니다.

```bash
uv run --no-project python -c "
import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.models.openai import OpenAIChat
from composio_agno import Action, ComposioToolSet
import os
from agno.tools.arxiv import ArxivTools
from agno.utils.pprint import pprint_run_response
from agno.tools.serpapi import SerpApiTools
print('all imports OK')
" 2>&1 | tail -1
```

(PowerShell은 `2>&1 | Select-Object -Last 1`입니다. 여러 줄 `python -c "..."`는 안쪽에 작은따옴표만 써서 같은 형태로 쓸 수 있습니다. 실행해 보지 못했습니다.) 첫 실행의 직접 확인한 출력의 마지막 줄입니다. 설치된 `openai`가 있는데도 "not installed"라고 하는 것은 agno가 이 임포트 실패를 하나로 뭉뚱그려 던지기 때문입니다.

```
ImportError: `openai` not installed. Please install using `pip install openai -U`
```

고치는 법은 `openai`를 올리는 것입니다. 그러면 다음 오류가 나오고, 그것을 하나씩 채웁니다.

```bash
uv pip install --upgrade openai
# 위 임포트 확인을 다시 하면 마지막 줄이 ImportError: `arxiv` not installed. Please install using `pip install arxiv`
uv pip install arxiv
# 다시 하면 ImportError: `pypdf` not installed. Please install using `pip install pypdf`
uv pip install pypdf
# 다시 하면 all imports OK
```

직접 확인한 설치 결과는 `openai` 3.26.1, `arxiv` 4.0.1, `pypdf` 6.19.0이고(`httpx2`·`httpcore2`·`truststore`가 함께 들어와 패키지는 109개), `uv pip check`는 "All installed packages are compatible"을 냈습니다. 한 번에 하려면 `uv pip install --upgrade openai arxiv pypdf`입니다. 이 문서는 이후 이 환경으로 확인했습니다.

![Step 1까지의 구성](diagrams/step1.svg)

### Step 2. 화면 뼈대와 키 셋 — 하나라도 비면 나머지는 그려지지 않습니다

**목적.** 화면에 처음 뜨는 것과, 키 셋이 모두 있어야 나머지가 그려지는 구조를 확인합니다.

**할 일.**

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:24-37`

```python
# Streamlit sidebar for API keys
with st.sidebar:
    st.title("API Keys Configuration")
    st.session_state['openai_api_key'] = st.text_input("Enter your OpenAI API Key", type="password").strip()
    st.session_state['composio_api_key'] = st.text_input("Enter your Composio API Key", type="password").strip()
    st.session_state['serpapi_api_key'] = st.text_input("Enter your SerpAPI Key", type="password").strip()
    
    # Add info about terminal responses
    st.info("Note: You can also view detailed agent responses\nin your terminal after execution.")

# Validate API keys
if not st.session_state['openai_api_key'] or not st.session_state['composio_api_key'] or not st.session_state['serpapi_api_key']:
    st.error("Please enter OpenAI, Composio, and SerpAPI keys in the sidebar.")
    st.stop()
```

사이드바에 비밀번호 칸이 셋이고, 값은 `.strip()`으로 앞뒤 공백을 떼어 `st.session_state`에 저장합니다. 세 값 가운데 하나라도 비면 `st.error` 뒤 `st.stop()`이 나머지 스크립트를 멈춥니다. 14~22행은 이 키 넷(키 셋과 주제)의 초기값을 빈 문자열로 만드는 세션 상태 설정이고, 12행의 `st.set_page_config`는 화면 이름과 가운데 배치를 정합니다. 이어서 같은 값을 환경변수에도 씁니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:39-40`

```python
# Set the OpenAI API key and Composio API key from session state
os.environ["OPENAI_API_KEY"] = st.session_state['openai_api_key']
```

뒤의 `OpenAIChat`이 `api_key=`로 같은 값을 따로 받으므로(Step 4) 이 환경변수는 겹치는 설정입니다. 앱 README는 "Enter your OpenAI API key in the sidebar (if not set in environment)"라고 하지만(앱 README 73행) 이 파일에는 환경변수를 읽는 줄이 없고(`os.getenv`·`environ` 읽기가 0건, `grep`으로 확인) 칸의 기본값은 빈 문자열입니다. 환경변수에 키가 있어도 칸에 직접 넣어야 합니다. 같은 안내는 버튼 이름도 "Generate Learning Plan"(76행)이라 하지만 실제 버튼은 `Start`(130행)이고, 키는 Composio까지 둘만 말하지만 화면은 SerpAPI 키까지 셋을 요구합니다(35행).

**확인.** 키 없이 화면을 `AppTest`로 한 번 그려 봅니다. 첫 실행은 import 때문에 느려서 시간 제한을 늘립니다. 앱 폴더에서 실행합니다.

```bash
uv run --no-project python -c "
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('teaching_agent_team.py', default_timeout=120)
at.run()
print([e.value for e in at.error])
print(len(at.sidebar.text_input), [t.label for t in at.sidebar.text_input])
" 2>/dev/null
```

직접 확인한 출력:

```
['Please enter OpenAI, Composio, and SerpAPI keys in the sidebar.']
3 ['Enter your OpenAI API Key', 'Enter your Composio API Key', 'Enter your SerpAPI Key']
```

`composio`를 import하는 프로세스는 처음이든 아니든 매번 `backend.composio.dev`(sentry 설정)에 접속을 시도하고, 끝날 때 `pypi.org`(버전 확인)에도 시도합니다(프록시로 막은 상태에서 같은 캐시 폴더로 세 번 돌려도 매번 두 호스트의 연결 시도가 기록됐습니다). Day 107 Step 3이 소스로 설명한 같은 사실입니다. `COMPOSIO_DISABLE_VERSION_CHECK=true`를 걸면 `pypi.org` 시도가 사라지고 `backend.composio.dev`는 남았습니다(직접 확인). 두 접속은 위 "요청 한 건이 흐르는 과정"의 첫 그림에 있습니다. 명령 끝의 `2>/dev/null`은 PowerShell에서 `2>$null`이고(Step 3도 같습니다), 실행해 보지 못했습니다.

![Step 2까지의 구성](diagrams/step2.svg)

### Step 3. Composio 도구 준비 — 화면이 다시 그려질 때마다 서버에 묻습니다

**목적.** 문서 만들기 도구를 어디서 어떻게 받는지, 연결 계정이 없으면 어떻게 되는지, 그리고 이 코드가 화면이 다시 그려질 때마다 도는 것을 확인합니다.

**할 일.**

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:42-48`

```python
try:
    composio_toolset = ComposioToolSet(api_key=st.session_state['composio_api_key'])
    google_docs_tool = composio_toolset.get_tools(actions=[Action.GOOGLEDOCS_CREATE_DOCUMENT])[0]
    google_docs_tool_update = composio_toolset.get_tools(actions=[Action.GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT])[0]
except Exception as e:
    st.error(f"Error initializing ComposioToolSet: {e}")
    st.stop()
```

`composio_agno.ComposioToolSet`은 `composio.ComposioToolSet`을 확장한 클래스이고, `get_tools(actions=[...])`는 액션마다 agno `Toolkit` 객체 하나씩을 담은 목록을 돌려줘서 `[0]`이 그것입니다(`composio_agno/toolset.py` 31~40행·109~143행을 소스로 확인했습니다). 모두 `try`로 감싸서 어떤 예외든 `st.error` 뒤 `st.stop()`입니다. Google Docs 계정이 연결돼 있지 않으면 Composio가 `ConnectedAccountNotFoundError`를 던지고, 화면은 이렇게 멈춥니다(가짜 서버가 연결 계정 목록을 빈 목록으로 답하게 하고 직접 확인).

```
Error initializing ComposioToolSet: No connected account found for app `GOOGLEDOCS`; Run `composio add googledocs` to fix this
```

두 가지가 눈에 띕니다. 하나, 45행의 `google_docs_tool_update`는 이 파일에서 한 번도 쓰이지 않습니다(`grep`으로 확인). 서버에 한 번 더 묻고도 에이전트에 연결되지 않습니다. 둘, 이 블록은 함수가 아니라 스크립트 본문이라 키가 있는 동안 화면이 다시 그려질 때마다 돕니다. Streamlit은 입력 칸의 값이 확정되거나 버튼을 누를 때마다 스크립트를 처음부터 다시 돌립니다(Day 012 Step 2가 설명했습니다). 가짜 서버에 보낸 요청을 세어 보면(Step 7) 다시 그릴 때마다 Composio에 GET 4건(연결 계정 조회 둘, 액션 스키마 조회 둘)이 나갔습니다. 프로세스에서 처음 한 번은 클라이언트 확인(`client_info`) 1건이 더 나가고, `COMPOSIO_CACHE_DIR`가 비어 있는 처음에는 카탈로그(앱 목록, 전체 액션 목록, 트리거 목록) 3건이 더 나갑니다. 이 카탈로그는 캐시 폴더에 파일로 저장돼서 두 번째부터는 나가지 않습니다(직접 확인. 캐시 폴더에는 `actions`·`apps`·`output`·`tags`·`triggers` 폴더와 `user_data.json`이 생겼습니다). 기본 캐시 폴더는 홈의 `.composio`이고 환경변수 이름은 `COMPOSIO_CACHE_DIR`입니다(`composio/constants.py` 24~34행, 소스로 확인). 또 하나, 도구를 만든 쪽에서 앱을 띄운 작업 폴더에 `.composio.lock`(내용 `{}`)이 생깁니다(`composio/constants.py` 136행, 직접 확인). 이 파일은 저장소의 `.gitignore`에 없어 앱 폴더에서 띄우면 `git status`에 새 파일로 나옵니다.

**확인.** 키 없이 되는 확인은 액션 이름이 있는지입니다. 앱 폴더에서 실행합니다.

```bash
uv run --no-project python -c "
from composio_agno import Action
print(Action.GOOGLEDOCS_CREATE_DOCUMENT, Action.GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT)
" 2>/dev/null
```

직접 확인한 출력:

```
GOOGLEDOCS_CREATE_DOCUMENT GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT
```

서버를 부르는 쪽의 시퀀스는 아래 "요청 한 건이 흐르는 과정"의 첫 두 그림입니다. 이 단계에서 Composio 서버와 두 도구가 그림에 붙습니다.

![Step 3까지의 구성](diagrams/step3.svg)

### Step 4. 에이전트 넷 — 지시문과 도구를 나눕니다

**목적.** 네 에이전트가 무엇을 갖고 태어나는지, 어떤 도구가 누구에게 가는지 확인합니다.

**할 일.** 첫 에이전트는 이렇습니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:50-64`

```python
# Create the Professor agent (formerly KnowledgeBuilder)
professor_agent = Agent(
    name="Professor",
    role="Research and Knowledge Specialist", 
    model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool],
    instructions=[
        "Create a comprehensive knowledge base that covers fundamental concepts, advanced topics, and current developments of the given topic.",
        "Exlain the topic from first principles first. Include key terminology, core principles, and practical applications and make it as a detailed report that anyone who's starting out can read and get maximum value out of it.",
        "Make sure it is formatted in a way that is easy to read and understand. DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    debug_mode=True,
    markdown=True,
)
```

나머지 셋도 같은 모양이고 이름·역할·지시문과 도구만 다릅니다(66~117행). 모델은 모두 `OpenAIChat(id="gpt-4o-mini", api_key=...)`이고 `debug_mode=True`라 실행하는 터미널에 대화가 길게 찍힙니다. 도구는 이렇게 나뉩니다. Professor와 Academic Advisor는 `[google_docs_tool]` 하나이고, Research Librarian과 Teaching Assistant는 `[google_docs_tool, SerpApiTools(api_key=...)]`입니다. 두 에이전트는 `SerpApiTools`를 각자 새로 만들지만 `google_docs_tool`은 넷이 같은 객체입니다. 지시문마다 "DONT FORGET TO CREATE THE GOOGLE DOCUMENT."가 들어 있고 마지막 줄은 넷이 똑같습니다. 새 Google 문서를 열어 답을 쓰고 그 링크를 답에 넣으라는 것입니다. 사서 쪽 정의의 앞부분은 이렇습니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:84-99`

```python
# Create the Research Librarian agent (formerly ResourceCurator)
research_librarian_agent = Agent(
    name="Research Librarian",
    role="Learning Resource Specialist",
    model=OpenAIChat(id="gpt-4o-mini", api_key=st.session_state['openai_api_key']),
    tools=[google_docs_tool, SerpApiTools(api_key=st.session_state['serpapi_api_key']) ],
    instructions=[
        "Make a list of high-quality learning resources for the given topic.",
        "Use the SerpApi search tool to find current and relevant learning materials.",
        "Using SerpApi search tool, Include technical blogs, GitHub repositories, official documentation, video tutorials, and courses.",
        "Present the resources in a curated list with descriptions and quality assessments. DONT FORGET TO CREATE THE GOOGLE DOCUMENT.",
        "Open a new Google Doc and write down the response of the agent neatly with great formatting and structure in it. **Include the Google Doc link in your response.**",
    ],
    debug_mode=True,
    markdown=True,
)
```

**확인.** 키 없이 에이전트를 하나 만들어 봅니다. 만들기만 하고 부르지 않으므로 서버에 닿지 않습니다. 앱 폴더에서 실행합니다.

```bash
uv run --no-project python -c "
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.serpapi import SerpApiTools
tool = SerpApiTools(api_key='x')
a = Agent(name='Research Librarian', role='Learning Resource Specialist', model=OpenAIChat(id='gpt-4o-mini', api_key='x'), tools=[tool], debug_mode=True, markdown=True)
print(a.name, '|', a.role, '|', a.model.id, '|', list(tool.functions))
" 2>&1 | tail -1
```

(PowerShell은 `2>&1 | Select-Object -Last 1`, 실행해 보지 못했습니다.) 직접 확인한 출력:

```
Research Librarian | Learning Resource Specialist | gpt-4o-mini | ['search_google']
```

`SerpApiTools`가 모델에 내놓는 함수는 `search_google` 하나입니다. 문서 만들기 도구의 함수 이름은 액션 이름을 소문자로 한 `googledocs_create_document`입니다(가짜 서버가 받은 모델 요청의 `tools`에서 직접 확인).

![Step 4까지의 구성](diagrams/step4.svg)

### Step 5. Start — 넷을 차례로 부르고, 서로 모릅니다

**목적.** 버튼 하나가 모델 요청 몇 번이 되는지, 네 에이전트가 어떤 입력을 받는지 확인합니다.

**할 일.**

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:129-153`

```python
# Start button
if st.button("Start"):
    if not st.session_state['topic']:
        st.error("Please enter a topic.")
    else:
        # Display loading animations while generating responses
        with st.spinner("Generating Knowledge Base..."):
            professor_response: RunOutput = professor_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response."
            )
            
        with st.spinner("Generating Learning Roadmap..."):
            academic_advisor_response: RunOutput = academic_advisor_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response."
            )
            
        with st.spinner("Curating Learning Resources..."):
            research_librarian_response: RunOutput = research_librarian_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response."
            )
            
        with st.spinner("Creating Practice Materials..."):
            teaching_assistant_response: RunOutput = teaching_assistant_agent.run(
                f"the topic is: {st.session_state['topic']},Don't forget to add the Google Doc link in your response."
            )
```

주제가 비어 있으면 `st.error`로 끝납니다(132행). 주제가 있으면 `with st.spinner(...)` 네 블록이 위에서 아래로 한 에이전트씩 `run()`을 부르고, 앞의 `run()`이 끝나야 다음이 시작됩니다. 넷에게 가는 사용자 메시지는 같은 문장이고 주제만 끼웁니다. 가짜 서버가 받은 네 에이전트의 첫 요청에 들어 있던 사용자 메시지는 모두 이것이었습니다(직접 확인).

```
the topic is: LoRA,Don't forget to add the Google Doc link in your response.
```

그리고 네 첫 요청의 메시지 역할은 모두 `developer`와 `user` 둘뿐이었습니다. 즉 Academic Advisor의 요청에는 Professor가 만든 지식 정리가 들어 있지 않고, Teaching Assistant의 요청에는 로드맵이 들어 있지 않습니다. 지시문이 말하는 "Using the knowledge base"(73행)와 "Ensure the materials align with the roadmap progression"(111행)은 모델이 알 수 없는 것을 요구합니다. 넷은 같은 주제를 받아 따로 일하는 독립된 에이전트이고, `Team`처럼 서로 일을 넘기거나 이어받지 않습니다.

대본으로 돌렸을 때 Start 한 번이 만든 요청은 이랬습니다. 모델 요청 10건(Professor 2, Academic Advisor 2, Research Librarian 3, Teaching Assistant 3), 에이전트마다 `os-api.agno.com`으로의 통계 접속 시도 1건씩 모두 4건입니다. 모델 요청이 둘 이상인 것은 첫 요청의 답이 도구 호출이어서 도구 결과를 실어 다시 보내기 때문입니다. 진짜 모델은 도구를 이 횟수대로 부르지 않을 수 있습니다.

**확인.** 키가 있으면 Start를 눌러 보면 됩니다. 키 없이는 Step 7의 가짜 서버 실행이 이 단계의 숫자를 확인합니다.

![Step 5까지의 구성](diagrams/step5.svg)

### Step 6. 도구가 닿는 곳 — 문서는 Composio가, 검색은 SerpAPI가

**목적.** 모델이 도구를 부르면 요청이 어디로 가는지 확인합니다.

**할 일.** 코드는 따로 없습니다. 모델이 `googledocs_create_document`를 부르면 `composio_agno`가 감싼 함수가 돌고, 그 함수는 `execute_action`을 부릅니다(`composio_agno/toolset.py` 68~80행, 소스로 확인). 가짜 서버의 기록에서는 실행 요청(POST) 바로 앞에 연결 계정 조회(GET)가 한 번 있었습니다. 실행 요청의 본문은 이랬습니다(직접 확인. `title`·`text`라는 인자 이름은 가짜 서버가 정의한 것이라 진짜 Composio의 이름인지는 확인하지 못했습니다).

```
POST /api/v2/actions/GOOGLEDOCS_CREATE_DOCUMENT/execute
{"connectedAccountId": "acc_googledocs", "entityId": "default", "appName": "GOOGLEDOCS", "input": {"title": "FAKE professor", "text": "fake body"}, ...}
```

그 뒤 Google Docs를 실제로 부르는 것은 Composio 서버이고, 이 문서는 그 부분을 볼 수 없습니다(시퀀스의 "대신 호출"은 구조 설명이며 관측한 것이 아닙니다). 검색은 다릅니다. `SerpApiTools.search_google`이 파이썬 프로세스에서 `serpapi.GoogleSearch`를 만들어 `https://serpapi.com`에 `requests.get`으로 요청하고(`agno/tools/serpapi.py` 61~63행, `serpapi/serp_api_client.py` 32행·59행, 소스로 확인), 검색어와 키와 개수가 쿼리 문자열로 갑니다. 가짜 서버가 받은 검색 요청은 `q=['fake query'] num=['3']`이고 키는 실려 있었습니다(직접 확인. SerpAPI 주소는 환경변수로 바꿀 수 없어서 구동 스크립트가 `serpapi.SerpApiClient.BACKEND`를 파이썬에서 바꿨습니다).

이 앱이 바깥에 남기는 것은 Google 계정의 새 문서와 SerpAPI의 검색 기록입니다. 대본에서 Start 한 번은 문서 만들기 실행 요청이 4건, 검색이 2건이었습니다.

**확인.** 이 단계도 Step 7의 구동으로 확인합니다.

![Step 6까지의 구성](diagrams/step6.svg)

### Step 7. 링크 뽑기와 결과 표시, 그리고 가짜 서버로 끝까지

**목적.** 문서 링크가 어떻게 뽑혀 화면에 나오는지 보고, 키 없이 앱을 끝까지 돌려 요청을 센 뒤 서버가 뜨는지 확인합니다.

**할 일.** 네 응답이 모이면 링크를 뽑습니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py:155-177`

```python
        # Extract Google Doc links from the responses
        def extract_google_doc_link(response_content):
            # Assuming the Google Doc link is embedded in the response content
            # You may need to adjust this logic based on the actual response format
            if "https://docs.google.com" in response_content:
                return response_content.split("https://docs.google.com")[1].split()[0]
            return None

        professor_doc_link = extract_google_doc_link(professor_response.content)
        academic_advisor_doc_link = extract_google_doc_link(academic_advisor_response.content)
        research_librarian_doc_link = extract_google_doc_link(research_librarian_response.content)
        teaching_assistant_doc_link = extract_google_doc_link(teaching_assistant_response.content)

        # Display Google Doc links at the top of the Streamlit UI
        st.markdown("### Google Doc Links:")
        if professor_doc_link:
            st.markdown(f"- **Professor Document:** [View Document](https://docs.google.com{professor_doc_link})")
        if academic_advisor_doc_link:
            st.markdown(f"- **Academic Advisor Document:** [View Document](https://docs.google.com{academic_advisor_doc_link})")
        if research_librarian_doc_link:
            st.markdown(f"- **Research Librarian Document:** [View Document](https://docs.google.com{research_librarian_doc_link})")
        if teaching_assistant_doc_link:
            st.markdown(f"- **Teaching Assistant Document:** [View Document](https://docs.google.com{teaching_assistant_doc_link})")
```

링크 뽑기 함수는 본문에서 `https://docs.google.com`이 나오는 첫 자리 뒤를 공백까지 잘라 돌려줍니다. 그래서 링크 끝의 문장부호나 마크다운이 그대로 딸려 옵니다. 함수 156~161행을 잘라 내 직접 돌려 본 결과입니다.

| 응답 본문 | 함수가 돌려준 값 |
|---|---|
| `Doc: https://docs.google.com/document/d/AAA/edit` | `/document/d/AAA/edit` |
| `[Open](https://docs.google.com/document/d/BBB/edit).` | `/document/d/BBB/edit).` |
| `**Link:** **https://docs.google.com/document/d/CCC/edit**` | `/document/d/CCC/edit**` |
| `I forgot to paste the link.` | `None` (링크 줄이 아예 안 나옴) |
| 링크 둘 | 첫 링크만 |
| `None` (모델이 내용을 비운 답) | `TypeError: argument of type 'NoneType' is not iterable` |

마지막 줄은 함수에 `None`을 직접 넣어 본 것이고, 진짜 `RunOutput.content`가 `None`이 되는 경우가 있는지는 확인하지 못했습니다. 이어서 화면에 나오는 것은 링크 목록, 에이전트 넷의 답(`st.markdown`), 같은 답의 터미널 출력(`pprint_run_response`)입니다(179~198행).

이제 키 없이 끝까지 돌립니다. 가짜 서버는 OpenAI 방식 채팅과 Composio REST, SerpAPI 검색을 한 포트에서 받고, 프록시 요청(`CONNECT`)은 기록만 하고 502로 거절합니다. 에이전트는 시스템 메시지의 문구로 구별해 지시문이 말한 순서(검색, 문서 만들기, 최종 답)대로 도구를 부르는 대본을 돌려줍니다. 앱 폴더 밖의 빈 폴더에 두 파일을 저장합니다.

`fake_servers.py`

```python
"""Localhost fake for Day 113 scratch runs: OpenAI chat + Composio REST + SerpAPI /search + refusing proxy recorder.
One JSON line per request in LOG. Never forwards anything."""
import json, sys, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(sys.argv[1]); LOG = sys.argv[2]
lock = threading.Lock()
def log(rec):
    with lock:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

STR = lambda t: {"type": "string", "title": t, "description": t}
APPS = {
    "GOOGLEDOCS_CREATE_DOCUMENT": ("googledocs", "GOOGLEDOCS", "Create a Google Doc", {"title": STR("Title"), "text": STR("Text")}),
    "GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT": ("googledocs", "GOOGLEDOCS", "Update a Google Doc", {"document_id": STR("Document id"), "editDocs": STR("Edits")}),
}
def action_json(name):
    app_id, app_name, desc, props = APPS[name]
    return {"name": name, "description": desc, "parameters": {"title": "P", "type": "object", "properties": props, "required": list(props)},
            "response": {"title": "R", "type": "object", "properties": {}}, "appName": app_id, "appId": app_id,
            "version": "1.0.0", "available_versions": ["1.0.0"], "tags": [], "enabled": True}
def account_json(app_id, app_name):
    return {"id": f"acc_{app_id}", "status": "ACTIVE", "createdAt": "2026-10-09T00:00:00Z", "updatedAt": "2026-10-09T00:00:00Z",
            "appUniqueId": app_id, "appName": app_name, "clientUniqueUserId": "default", "integrationId": f"int_{app_id}",
            "connectionParams": {"scope": "", "base_url": "", "client_id": "", "token_type": "", "access_token": "", "client_secret": "", "consumer_id": "", "consumer_secret": "", "headers": {}, "queryParams": {}}}

LINKS = {
    "professor": "Done. Document: https://docs.google.com/document/d/FAKE-PROFESSOR/edit",
    "advisor": "Roadmap ready: https://docs.google.com/document/d/FAKE-ADVISOR/edit and nothing else.",
    "librarian": "Resources compiled. [Open the Google Doc](https://docs.google.com/document/d/FAKE-LIBRARIAN/edit).",
    "assistant": "Practice materials written, but I forgot to paste the link.",
}
def who(text):
    if "knowledge base that covers" in text: return "professor"
    if "detailed learning roadmap" in text: return "advisor"
    if "high-quality learning resources" in text: return "librarian"
    if "comprehensive practice materials" in text: return "assistant"
    return "?"

class Srv(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _send(self, code, obj):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_CONNECT(self):
        log({"kind": "proxy-CONNECT", "target": self.path})
        self.send_response(502); self.send_header("Content-Length", "0"); self.send_header("Connection", "close"); self.end_headers()
        self.close_connection = True
    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}
    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/search":
            q = parse_qs(u.query)
            log({"kind": "serpapi-GET", "q": q.get("q"), "num": q.get("num"), "api_key": "<present>" if q.get("api_key") else None})
            return self._send(200, {"organic_results": [{"title": "FAKE result", "link": "https://example.invalid/x"}]})
        log({"kind": "GET", "path": u.path, "query": u.query})
        if u.path == "/api/v1/client/auth/client_info": return self._send(200, {"client": {"id": "fake"}})
        if u.path == "/api/v1/apps":
            return self._send(200, {"items": [{"name": "googledocs", "key": "googledocs", "appId": "googledocs", "description": "fake", "categories": [], "meta": {}, "no_auth": False}]})
        if u.path == "/api/v1/triggers": return self._send(200, {"items": []})
        if u.path == "/api/v2/actions":
            q = parse_qs(u.query)
            if "apps" not in q: return self._send(200, {"items": [action_json(n) for n in APPS]})
            apps = q.get("apps", [""])[0].split(",")
            return self._send(200, {"items": [action_json(n) for n, v in APPS.items() if v[0].upper() in apps]})
        if u.path == "/api/v1/connectedAccounts":
            have = [a for a in os.environ.get("FAKE_ACCOUNTS", "googledocs").split(",") if a]
            items = [account_json("googledocs", "GOOGLEDOCS")] if "googledocs" in have else []
            return self._send(200, {"items": items, "totalPages": 1, "page": 1})
        self._send(404, {"error": "fake: unknown path"})
    def do_POST(self):
        u = urlparse(self.path); body = self._body()
        if u.path.endswith("/chat/completions"): return self.chat(body)
        log({"kind": "POST", "path": u.path, "body": body})
        if u.path.startswith("/api/v2/actions/") and u.path.endswith("/execute"):
            return self._send(200, {"data": {"response_data": {"documentId": "FAKE-ID", "title": "fake"}}, "successful": True, "error": None})
        self._send(404, {"error": "fake: unknown path"})
    def chat(self, body):
        msgs = body.get("messages", [])
        tools = [t["function"]["name"] for t in body.get("tools", [])]
        def txt(m):
            c = m.get("content"); return c if isinstance(c, str) else json.dumps(c)
        system = " ".join(txt(m) for m in msgs if m.get("role") in ("system", "developer"))
        user = " ".join(txt(m) for m in msgs if m.get("role") == "user")
        w = who(system)
        ntool = sum(1 for m in msgs if m.get("role") == "tool")
        log({"kind": "chat", "agent": w, "model": body.get("model"), "tools": tools, "n_messages": len(msgs),
             "roles": [m.get("role") for m in msgs], "user": user, "n_tool_results": ntool,
             "auth": "present" if self.headers.get("Authorization") else "absent"})
        def reply(content=None, tool=None):
            msg = {"role": "assistant", "content": content}; fin = "stop"
            if tool:
                msg["tool_calls"] = [{"id": f"call_{ntool}", "type": "function", "function": {"name": tool[0], "arguments": json.dumps(tool[1])}}]; fin = "tool_calls"
            self._send(200, {"id": "x", "object": "chat.completion", "created": 0, "model": body.get("model"), "choices": [{"index": 0, "message": msg, "finish_reason": fin}],
                             "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
        plan = (["search_google"] if w in ("librarian", "assistant") else []) + ["googledocs_create_document"]
        if ntool < len(plan):
            name = plan[ntool]
            args = {"query": "fake query", "num_results": 3} if name == "search_google" else {"title": f"FAKE {w}", "text": "fake body"}
            return reply(None, (name, args))
        reply(LINKS.get(w, "FAKE default"))

if __name__ == "__main__":
    Srv(("127.0.0.1", PORT), H).serve_forever()
```

`drive.py`

```python
import json, os
from collections import Counter
from streamlit.testing.v1 import AppTest
import serpapi

PORT = os.environ["PORT"]
serpapi.SerpApiClient.BACKEND = f"http://127.0.0.1:{PORT}"   # SerpAPI는 주소를 바꾸는 환경변수가 없어 파이썬에서 바꾼다
LOG = "fake.log"
OUT = open("drive.out", "w", encoding="utf-8")   # 에이전트가 터미널에 찍는 긴 로그와 섞이지 않게 요약은 파일로

def p(*a):
    print(*a, file=OUT, flush=True)

def lines():
    try:
        return open(LOG, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return []

def show(since):
    c = Counter()
    for l in lines()[since:]:
        r = json.loads(l)
        c[(r["kind"], r.get("target") or r.get("path") or r.get("agent"))] += 1
    for (kind, what), n in sorted(c.items()):
        p(f"   {n:>2} x {kind} {what}")

at = AppTest.from_file(os.environ["APPFILE"], default_timeout=120)
at.run()
p("[1] 키 없이 첫 화면:", [e.value for e in at.error])

for i, v in enumerate(["sk-test", "ck-test", "sp-test"]):
    at.sidebar.text_input[i].set_value(v)
n = len(lines()); at.run()
p("[2] 키 셋을 넣은 화면: 버튼", [b.label for b in at.button])
show(n)

n = len(lines()); at.button[0].click().run()
p("[3] 주제 없이 Start:", [e.value for e in at.error])
show(n)

at.text_input[0].set_value("LoRA")
n = len(lines()); at.run()
p("[4] 주제만 적음 (Start 안 누름)")
show(n)

n = len(lines()); at.button[0].click().run()
p("[5] Start: 예외", [str(e.value) for e in at.exception])
for m in at.markdown:
    if m.value.startswith("- **") and "Document" in m.value:
        p("   ", m.value)
show(n)
```

폴더를 정해 두 터미널로 돌립니다. 포트는 49152~65535의 비어 있는 번호를 고릅니다(예: 62085). 첫 터미널에서 서버를 띄웁니다.

```bash
python fake_servers.py 62085 fake.log
```

두 번째 터미널에서 구동 스크립트를 앱 파일 경로와 함께 돌립니다. 아래 환경변수는 이 한 명령에만 붙는 접두이고 셸에 export하지 않습니다. 모델 요청 주소는 `OPENAI_BASE_URL`, Composio 주소는 `COMPOSIO_BASE_URL`, 프록시는 agno 통계와 `composio`의 import 때 접속을 서버가 기록하고 거절하게 합니다. 앱 폴더의 가상환경 파이썬으로 돌립니다.

```bash
COMPOSIO_CACHE_DIR="$(mktemp -d)" OPENAI_BASE_URL=http://127.0.0.1:62085/v1 COMPOSIO_BASE_URL=http://127.0.0.1:62085/api HTTP_PROXY=http://127.0.0.1:62085 HTTPS_PROXY=http://127.0.0.1:62085 NO_PROXY=localhost,127.0.0.1 PORT=62085 APPFILE=<저장소 경로>/advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/teaching_agent_team.py <앱 폴더>/.venv/bin/python drive.py
```

Windows의 파이썬은 `.venv\Scripts\python.exe`입니다. PowerShell은 환경변수를 `$env:`로 따로 걸어야 하고, 이 변수들은 그 창에 남아 다음 `uv pip install`이나 다른 앱을 깨뜨릴 수 있으니(`HTTP_PROXY`가 가짜 서버를 가리킵니다) 끝나면 반드시 지웁니다. 서버는 같은 `python fake_servers.py 62085 fake.log`입니다.

```powershell
$env:COMPOSIO_CACHE_DIR = Join-Path $env:TEMP "composio-cache-drive"
$env:OPENAI_BASE_URL = "http://127.0.0.1:62085/v1"
$env:COMPOSIO_BASE_URL = "http://127.0.0.1:62085/api"
$env:HTTP_PROXY = "http://127.0.0.1:62085"
$env:HTTPS_PROXY = "http://127.0.0.1:62085"
$env:NO_PROXY = "localhost,127.0.0.1"
$env:PORT = "62085"
$env:APPFILE = "<저장소 경로>\advanced_ai_agents\multi_agent_apps\agent_teams\ai_teaching_agent_team\teaching_agent_team.py"
& "<앱 폴더>\.venv\Scripts\python.exe" drive.py
Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY, Env:NO_PROXY, Env:OPENAI_BASE_URL, Env:COMPOSIO_BASE_URL, Env:PORT, Env:APPFILE
```

PowerShell 줄은 실행해 보지 못했습니다. 요약은 `drive.out`에 쓰이고 터미널에는 에이전트의 긴 로그가 찍힙니다. 직접 확인한 `drive.out`입니다.

```
[1] 키 없이 첫 화면: ['Please enter OpenAI, Composio, and SerpAPI keys in the sidebar.']
[2] 키 셋을 넣은 화면: 버튼 ['Start']
    1 x GET /api/v1/apps
    1 x GET /api/v1/client/auth/client_info
    2 x GET /api/v1/connectedAccounts
    1 x GET /api/v1/triggers
    3 x GET /api/v2/actions
[3] 주제 없이 Start: ['Please enter a topic.']
    2 x GET /api/v1/connectedAccounts
    2 x GET /api/v2/actions
[4] 주제만 적음 (Start 안 누름)
    2 x GET /api/v1/connectedAccounts
    2 x GET /api/v2/actions
[5] Start: 예외 []
    - **Professor Document:** [View Document](https://docs.google.com/document/d/FAKE-PROFESSOR/edit)
    - **Academic Advisor Document:** [View Document](https://docs.google.com/document/d/FAKE-ADVISOR/edit)
    - **Research Librarian Document:** [View Document](https://docs.google.com/document/d/FAKE-LIBRARIAN/edit).)
    6 x GET /api/v1/connectedAccounts
    2 x GET /api/v2/actions
    4 x POST /api/v2/actions/GOOGLEDOCS_CREATE_DOCUMENT/execute
    2 x chat advisor
    3 x chat assistant
    3 x chat librarian
    2 x chat professor
    2 x serpapi-GET None
```

읽는 법입니다. [2]는 캐시가 빈 첫 처리라 연결 계정 조회 2건과 액션 스키마 조회 2건에 `client_info` 1건과 카탈로그 3건(`apps`·`triggers`·전체 `actions`)이 더해졌습니다. `actions`가 3건인 것은 스키마 2건과 전체 목록 1건입니다. [3]·[4]의 다시 그리기에는 연결 계정 조회와 액션 스키마 조회가 각각 2건씩 갔습니다. [5]의 Start는 클릭이 일으킨 다시 그리기분(연결 계정 2건, 스키마 2건. 이 요청 4건은 `run()`보다 먼저 나갑니다)에 문서 만들기 도구의 연결 계정 조회 4건이 더해져 `connectedAccounts` 6건이 되고, 문서 실행 요청 4건, 모델 요청 10건, 검색 2건이 갑니다. 링크 목록에는 셋만 나왔습니다. Teaching Assistant의 대본 답이 링크를 담지 않아 넷째 줄이 빠졌고, 사서의 링크는 끝에 `).`가 붙었습니다. 서버 로그에서 센 접속 시도는 `os-api.agno.com` 4건, `backend.composio.dev` 2건, `pypi.org` 1건이고 모두 502로 거절됐습니다. 두 요청을 막는 방법이 따로 있습니다. 통계는 `AGNO_TELEMETRY=false`를 걸면 이 앱에서도 4건이 0건이 됐습니다(같은 구동, 직접 확인. 이 환경변수가 하는 일은 Day 047 Step 5가 소스로 설명합니다). 그때도 `backend.composio.dev`와 `pypi.org` 시도는 1건씩 그대로 남았습니다. 이 둘은 `composio`를 import할 때 나가는 것이라 agno의 설정과 무관합니다(Day 107 Step 3).

마지막으로 서버가 뜨는지 봅니다. 앱을 띄울 때 `--server.address localhost`를 붙여야 Streamlit이 시작하며 외부 IP를 알아내려고 `checkip.amazonaws.com`에 요청을 보내지 않습니다(Day 054). 앱 폴더에서, 비어 있는 포트로:

```bash
uv run --no-project streamlit run teaching_agent_team.py --server.headless true --server.address localhost --server.port 50232 --browser.gatherUsageStats false
```

다른 터미널에서 `curl http://localhost:50232/_stcore/health`는 `ok`를 냈습니다(직접 확인). 서버 쪽 출력은 이랬습니다.

```

  You can now view your Streamlit app in your browser.

  URL: http://localhost:50232

```

PowerShell은 `curl` 대신 `(Invoke-WebRequest -Uri http://localhost:50232/_stcore/health -UseBasicParsing).Content`를 씁니다(실행해 보지 못했습니다). 서버가 뜬다는 것만 확인한 것이고 키를 넣어 Start를 누르는 흐름은 위의 가짜 서버 구동이 대신 확인했습니다. 실제로 쓸 때는 `--server.headless`와 포트 인자 없이 `uv run --no-project streamlit run teaching_agent_team.py`로 띄우고 브라우저가 열리면 사이드바에 키를 넣습니다. 끝나면 두 터미널을 `Ctrl+C`로 멈추고, 구동을 돌린 폴더에 생긴 `.composio.lock`을 지웁니다. 키를 넣어 앱 폴더에서 앱을 쓴 경우에는 앱 폴더에도 생깁니다.

![Step 7까지의 구성](diagrams/step7.svg)

## 요청 한 건이 흐르는 과정

아래 그림들은 위 구동에서 본 순서입니다. 모델 쪽 답과 Composio 뒤의 Google Docs 호출은 가짜 서버나 구조 설명이고, 진짜 서비스가 이 모양으로 답하는지는 확인하지 못했습니다. 시간 순으로 스물네 장입니다. 먼저 프로세스가 `composio`를 import할 때의 접속입니다. 첫째는 import 때의 sentry 설정 조회이고, 둘째는 프로세스가 끝날 때 도는 버전 확인입니다(`composio/__init__.py` 56행의 `atexit`, 소스로 확인). 이 그림은 뒤의 어느 그림보다 앞에서 일어나는 일(import)과 맨 끝에서 일어나는 일(종료)을 한 장에 모았습니다.

![import와 종료 때의 접속](diagrams/extra-import.svg)

이어서 키 입력부터 도구 준비까지입니다. 첫 장은 키가 비었을 때의 오류 안내, 키 입력, `ComposioToolSet`을 만들며 서버에 키를 확인하고 캐시가 비었을 때 카탈로그(앱·전체 액션·트리거)를 요청하는 일입니다. 캐시가 따뜻하면 카탈로그 요청은 없고 키 확인은 첫 `get_tools` 때 나갑니다(직접 확인).

![요청 시퀀스](diagrams/sequence.svg)

둘째 장은 `get_tools(문서 만들기)`입니다. 활성 연결 계정, 액션 스키마, 전체 연결 계정을 차례로 묻고 첫 도구를 돌려줍니다.

![문서 만들기 도구 받기](diagrams/extra-toolkits.svg)

셋째 장은 `get_tools(문서 고치기)`입니다.

![문서 고치기 도구 받기](diagrams/extra-toolkits-update.svg)

사용자가 주제를 적고 Start를 누르면 스크립트가 처음부터 다시 돌아서 같은 도구 준비가 한 번 더 일어납니다. 주제 입력(칸 값 확정)이 일으키는 다시 그리기도 같은 요청 4건을 보내지만([4], Step 7) 그림은 Start 쪽만 그렸습니다. 따뜻한 캐시이므로 카탈로그와 키 확인은 없고 `ComposioToolSet`을 만드는 줄은 요청을 보내지 않습니다.

![Start 때의 도구 준비 1](diagrams/extra-start-prepare-1.svg)

![Start 때의 도구 준비 2](diagrams/extra-start-prepare-2.svg)

이어서 에이전트 넷이 차례로 일합니다. Professor는 모델 요청, 도구 호출 요청, 문서 만들기 도구와 Composio의 연결 계정·실행 요청까지가 첫 장입니다.

![Professor 호출](diagrams/extra-professor-call.svg)

Composio가 Google Docs를 대신 부르고 결과가 돌아와 모델이 최종 답을 내는 것이 둘째 장입니다.

![Professor 문서 만들기](diagrams/extra-professor-doc.svg)

마지막으로 통계와 화면으로 돌아가는 `RunOutput`입니다.

![Professor 마무리](diagrams/extra-professor-finish.svg)

Academic Advisor도 같은 세 장입니다. 화면이 `run()`을 부르는 데서 시작합니다.

![Advisor 호출](diagrams/extra-advisor-call.svg)

![Advisor 문서 만들기](diagrams/extra-advisor-doc.svg)

![Advisor 마무리](diagrams/extra-advisor-finish.svg)

Research Librarian은 문서를 만들기 전에 검색이 끼어 네 장입니다. 첫 장은 모델이 검색을 부르고 SerpAPI가 답하는 부분입니다.

![Librarian 검색](diagrams/extra-librarian-search.svg)

![Librarian 호출](diagrams/extra-librarian-call.svg)

![Librarian 문서 만들기](diagrams/extra-librarian-doc.svg)

![Librarian 마무리](diagrams/extra-librarian-finish.svg)

Teaching Assistant도 같습니다. 대본에서 이 에이전트의 최종 답에는 링크가 없었고, 그림의 라벨은 지시문이 링크를 요구한다는 뜻입니다.

![Assistant 검색](diagrams/extra-assistant-search.svg)

![Assistant 호출](diagrams/extra-assistant-call.svg)

![Assistant 문서 만들기](diagrams/extra-assistant-doc.svg)

![Assistant 마무리](diagrams/extra-assistant-finish.svg)

넷이 끝나면 화면 코드가 링크를 뽑아 보여 주고 응답을 한 에이전트씩 화면과 터미널에 차례로 냅니다(163~198행). 먼저 링크 뽑기 함수를 네 번 부릅니다.

![링크 뽑기](diagrams/extra-show-extract.svg)

그다음 링크 목록의 제목과, 링크를 뽑은 에이전트의 줄입니다. 링크가 없으면 그 줄은 나오지 않습니다.

![링크 목록](diagrams/extra-show-links.svg)

응답 표시는 에이전트마다 제목, 본문, 터미널 출력, 구분선이 번갈아 나옵니다. Professor와 Academic Advisor입니다.

![응답 표시 1](diagrams/extra-show-answers-1.svg)

Research Librarian과 Teaching Assistant이고, 맨 끝에 "About the Agents" 안내가 붙습니다.

![응답 표시 2](diagrams/extra-show-answers-2.svg)

## 실행 체크리스트

- [ ] 앱 폴더에서 `uv venv`와 `uv pip install -r requirements.txt` 뒤 `uv pip install --upgrade openai arxiv pypdf`까지 했다
- [ ] `uv pip check`가 "All installed packages are compatible"을 냈다
- [ ] 앱의 1~9행 임포트가 `all imports OK`를 냈다
- [ ] 키 없이 화면을 `AppTest`로 그리면 키 안내 오류가 하나 나온다
- [ ] `COMPOSIO_CACHE_DIR`를 임시 폴더로 걸었다
- [ ] (키가 있다면) Composio 계정에 Google Docs가 연결돼 있다
- [ ] (가짜 서버) `drive.out`에서 모델 요청 10건, 문서 실행 요청 4건, 검색 2건이 나왔다
- [ ] 끝나고 구동을 돌린 폴더(키를 넣어 썼다면 앱 폴더)의 `.composio.lock`을 지웠다
- [ ] 띄운 서버와 가짜 서버를 멈췄다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| ``ImportError: `openai` not installed``인데 `openai`는 설치돼 있다 | 요구 파일의 `openai==1.58.1`에 `openai.types.responses`가 없어 agno의 `OpenAIChat` 임포트가 실패한다(agno가 실패를 한 문구로 던진다) | `uv pip install --upgrade openai`. agno의 `openai` extra는 `openai>=1.106.0`을 요구한다 |
| ``ImportError: `arxiv` not installed`` 또는 ``ImportError: `pypdf` not installed`` | 7행의 `ArxivTools`는 쓰이지 않지만 임포트되고, 그 모듈이 `arxiv`와 `pypdf`를 요구한다. 요구 파일에 둘 다 없다 | `uv pip install arxiv pypdf`. 또는 7행을 지우면 필요 없다(원본은 고치지 않았다) |
| 화면에 ``Error initializing ComposioToolSet: No connected account found for app `GOOGLEDOCS`...`` | Composio에 Google Docs 연결 계정이 없다 | 터미널에서 `composio add googledocs`를 하고 Composio 사이트에서 연결을 만든다(앱 README 54~61행. 실행해 보지 못했다) |
| 키를 넣은 뒤 입력 칸을 건드릴 때마다 Composio에 요청이 나간다 | 42~48행이 스크립트 본문이라 다시 그릴 때마다 Composio에 GET 4건을 보낸다 | 키를 확정한 뒤에는 입력 칸을 건드리지 않는다. 고치려면 도구 준비를 `@st.cache_resource` 함수로 빼야 하지만 원본은 고치지 않았다 |
| 앱 폴더에 `.composio.lock`이 생겨 `git status`에 나온다 | `composio`가 작업 폴더에 잠금 파일을 만든다 | 앱을 끝낸 뒤 지운다. `.gitignore`에 넣지 않았다 |
| 링크 줄 끝에 `.)`가 남고(`...edit).`), 답이 `**`로 감싼 링크면 주소에 `**`가 붙어 열리지 않는다(`...edit**`) | 링크 뽑기 함수가 공백까지 자르므로 마침표와 마크다운 기호가 딸려 온다. 마크다운은 첫 `)`에서 링크를 닫으므로 `).` 쪽은 주소가 맞고 글자만 남는다(CommonMark 파서로 확인, Streamlit 화면은 띄워 보지 못했다) | 화면 링크 대신 아래 "답" 본문의 링크를 쓴다 |
| 에이전트의 문서가 4개인데 화면 링크는 3개 | 모델이 링크를 답에 쓰지 않으면 함수가 `None`이라 줄이 아예 안 나온다 | 터미널에 찍힌 답이나 Google Drive에서 찾는다 |
| 터미널에 `DEBUG`로 대화가 길게 찍힌다 | 네 에이전트가 `debug_mode=True`다 | 의도된 동작이다. 앱 안내도 "터미널에서 상세 응답을 볼 수 있다"고 말한다(32행) |
| agno 통계 접속이 막힌 환경에서 `Could not send telemetry event ... ProxyError`가 DEBUG로 찍힌다 | 성공한 `run`마다 통계를 보내려다 실패한다. 앱은 계속 돈다 | `AGNO_TELEMETRY=false`를 걸면 보내지 않는다 |

## 더 해보기

- 쓰이지 않는 `google_docs_tool_update`를 쓰는 다섯째 에이전트를 만들어, 앞의 문서에 내용을 덧붙이게 해 보세요. 문서 id를 어떻게 넘길지가 과제입니다. 오늘 앱은 에이전트끼리 결과를 넘기지 않으므로 화면 코드가 `run()`의 답에서 id를 꺼내 다음 입력에 끼워야 합니다.
- Academic Advisor의 입력에 Professor의 답을, Teaching Assistant의 입력에 Advisor의 답을 끼워 보세요(`run()`의 입력 문자열을 고치는 것이 전부입니다). 같은 주제를 가짜 서버로 돌려 두 번째 요청의 메시지 수가 어떻게 달라지는지 비교하세요.
- 링크 뽑기 함수를 `re.search(r"https://docs\.google\.com/[^\s)\]*]+", content)`처럼 정규식으로 바꾸고, 위의 표 여섯 줄을 모두 통과시켜 보세요.

## 다음 날 예고

[Day 114 · ✨ Multimodal Design Agent Team](../day114-multimodal-design-agent-team/README.md) — 같은 볼륨의 다음 앱입니다. 원본 소스(`agent_teams/multimodal_design_agent_team/design_agent_team.py`, 편집기 기준 264줄)는 Gemini(`gemini-2.0-flash-exp`)를 모델로 시각 분석·UX 분석·시장 조사를 맡은 `Agent` 셋(21·34·47행)을 만들고, 이미지를 올려 분석시킵니다. 오늘 앱과 달리 키는 Gemini 하나이고, 시장 조사 에이전트만 `DuckDuckGoTools`를 쥡니다.
