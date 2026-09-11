# Day 002 · 🕸️ Web Scraping AI Agent

> 볼륨 1 🌱 Starter AI Agents · 난이도 ★☆☆ · 예상 소요 60분 · API 비용 대략 스크래핑 10건에 수백 원 이하 (OpenAI 요금표 기준, 대략치 — 키가 없어 실제 과금은 확인 못함) · 원본 앱: `starter_ai_agents/web_scraping_ai_agent`

## 오늘 만들 것

이번 튜토리얼에서는 CSS 셀렉터나 XPath를 한 줄도 쓰지 않고, 자연어 프롬프트만으로 웹페이지에서 원하는 데이터를 뽑아내는 스크래핑 에이전트를 만듭니다. 핵심은 오픈소스 라이브러리 ScrapeGraphAI가 제공하는 `SmartScraperGraph` 객체 하나뿐입니다. "상품명과 가격을 추출해줘"처럼 원하는 것을 문장으로 주면, 이 객체가 내부적으로 (1) Playwright로 헤드리스 브라우저를 띄워 대상 페이지를 실제로 로드하고, (2) 받아온 HTML을 텍스트로 정리해 프롬프트와 함께 LLM(OpenAI GPT-4o 또는 GPT-5)에 보내고, (3) 그 응답을 구조화된 결과로 돌려주는 3단계 파이프라인을 그래프 형태로 실행합니다. Day 1의 에이전트가 "질문 → 필요하면 도구 호출 → 답변"을 스스로 오가는 되묻기 루프였다면, 이 앱은 정해진 순서대로만 흐르는 단방향 파이프라인이라는 점에서 대비되는 두 번째 패턴입니다. 이 폴더에는 실행 방식이 다른 진입점이 두 개 있습니다 — OpenAI 키로 클라우드 모델을 쓰는 `ai_scrapper.py`와, 로컬에 설치한 Ollama의 Llama 3.2로 완전히 무료로 돌리는 `local_ai_scrapper.py`입니다. 이 문서는 앱 자체 README가 기본으로 안내하는 `ai_scrapper.py`를 따라가고, 로컬 버전은 "더 해보기"에서 다룹니다. 완성하면 브라우저에 URL과 추출 프롬프트를 입력해 즉시 결과를 받는 화면을 로컬에서 띄우게 됩니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| OpenAI API 키 | `ai_scrapper.py`가 스크래핑 결과 추출에 쓰는 gpt-4o/gpt-5 모델 호출 인증. Day 1과 달리 환경변수가 아니라 앱 실행 후 화면의 입력창에 직접 붙여넣는다 | https://platform.openai.com/ 가입 후 발급 |
| Playwright 브라우저 바이너리 | ScrapeGraphAI가 페이지를 실제로 렌더링할 헤드리스 Chromium. pip 패키지 설치와 별도로 받아야 한다(Step 1) | `playwright install chromium` |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| (선택) Ollama | 키 없이 로컬 Llama 3.2로 돌리고 싶다면(`local_ai_scrapper.py`) 필요. 이 문서의 기본 경로에는 필요 없음 | https://ollama.com/ 설치 후 `ollama pull llama3.2`, `ollama pull nomic-embed-text` |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 사용자 | 브라우저에서 OpenAI 키·모델·URL·추출 프롬프트 입력 | 코드 없음 (브라우저) |
| Streamlit UI | 입력을 받고 SmartScraperGraph를 실행해 결과를 표시 | `starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:6-27` |
| 스크래핑 그래프 (SmartScraperGraph) | 페이지 로드 → 텍스트 정리 → LLM 추출까지 파이프라인 실행 | `starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:30-38` |
| 대상 웹사이트 | 실제로 스크래핑할 페이지 | 코드 없음 (외부 사이트) |
| OpenAI API (gpt-4o / gpt-5) | 페이지 텍스트에서 프롬프트에 맞는 정보를 구조화해 추출 | 코드 없음 (외부 서비스). 모델 선택은 `starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:13-17` |

## 단계별 진행

### Step 1. 환경 만들기

**목적.** 격리된 가상환경에 이 앱이 쓰는 세 패키지(streamlit, scrapegraphai, playwright)를 설치하고, ScrapeGraphAI가 페이지를 실제로 렌더링할 때 쓰는 헤드리스 브라우저까지 받아둡니다.

**할 일.**

```bash
cd starter_ai_agents/web_scraping_ai_agent
uv venv
uv pip install -r requirements.txt
uv run playwright install chromium
```

(pip을 쓴다면 `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium`.)

세 번째 명령이 필요한 이유를 미리 짚습니다. `requirements.txt`가 설치하는 `playwright` 패키지는 브라우저를 제어하는 **파이썬 바인딩**일 뿐, 실제로 페이지를 띄울 Chromium 실행 파일은 들어있지 않습니다. 이 실행 파일은 `playwright install`로 따로 받아야 하는데, 앱 자체 `README.md`는 이 단계를 전혀 언급하지 않습니다 — 건너뛰면 Step 5에서 만나는 에러를 "문제 해결"에 실제로 재현해 정리해 두었습니다. 참고로 `requirements.txt`는 `streamlit`, `scrapegraphai`, `playwright` 세 줄만 있고 버전 고정이 없어서, 이 문서를 작성하며 설치했을 때는 **scrapegraphai 2.2.4**, **playwright 1.62.0**, **streamlit 1.63.0**이 받아졌습니다(직접 확인). 이 세 줄만으로 나머지 import는 모두 성공했으므로, Day 1과 달리 이 앱은 `requirements.txt`에 없는 패키지를 추가로 설치할 필요는 없습니다.

OpenAI 키는 이 단계에서 당장 쓰지 않습니다. 이 앱은 키를 환경변수가 아니라 Step 2에서 볼 Streamlit 입력창에 직접 붙여넣는 방식이라, 앱을 띄운 뒤에 입력해도 됩니다. 미리 https://platform.openai.com/ 에서 발급받아 두세요.

![Step 1까지의 구성](diagrams/step1.svg)

**확인.**

```bash
uv run python -c "from scrapegraphai.graphs import SmartScraperGraph; print('ok')"
```

```
ok
```

### Step 2. Streamlit 뼈대와 키 입력

**목적.** 앱 제목을 띄우고, OpenAI 키를 받는 입력창을 만듭니다. Day 1의 `XAI_API_KEY` 환경변수 방식과 달리, 이 앱은 키를 Streamlit의 비밀번호 입력창에서 직접 받습니다.

**할 일.**

`starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:2-3`

```python
import streamlit as st
from scrapegraphai.graphs import SmartScraperGraph
```

`starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:6-10`

```python
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using OpenAI API")

# Get OpenAI API key from user
openai_access_token = st.text_input("OpenAI API Key", type="password")
```

`st.text_input(..., type="password")`는 화면에는 입력값을 점으로 가리지만 평범한 파이썬 문자열 변수(`openai_access_token`)에 그대로 담깁니다. 이후 코드 전체가 `starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:12`의 `if openai_access_token:` 안에 들어있다는 점이 이 파일의 구조를 이해하는 열쇠입니다 — 키를 넣기 전까지는 모델 선택도, URL 입력도, 스크래핑 버튼도 화면에 나타나지 않습니다.

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** 앱 폴더에서 서버를 headless로 띄웁니다.

```bash
uv run streamlit run ai_scrapper.py --server.headless true
```

다른 터미널에서:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501
```

```
200
```

(HTTP 200은 직접 확인. 제목·설명·키 입력창만 보이고 그 아래는 비어 있으리라는 것은 `if openai_access_token:` 가드 로직으로 추론한 것이며, 화면을 직접 열어 확인하지는 못했습니다.)

### Step 3. 모델 선택과 스크래핑 대상 입력

**목적.** 키를 넣은 뒤에 나타나는 나머지 입력 — 모델 선택, 스크래핑 설정, URL, 추출 프롬프트 — 을 봅니다.

**할 일.**

`starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:12-23`

```python
if openai_access_token:
    model = st.radio(
        "Select the model",
        ["gpt-4o", "gpt-5"],
        index=0,
    )    
    graph_config = {
        "llm": {
            "api_key": openai_access_token,
            "model": model,
        },
    }
```

`starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:24-27`

```python
    # Get the URL of the website to scrape
    url = st.text_input("Enter the URL of the website you want to scrape")
    # Get the user prompt
    user_prompt = st.text_input("What you want the AI agent to scrape from the website?")
```

`graph_config`는 뒤에서 만들 `SmartScraperGraph`가 요구하는 형식 그대로입니다 — `llm` 키 아래에 `api_key`와 `model`을 중첩해 넣습니다. `st.radio`의 두 선택지는 코드에 하드코딩되어 있어 다른 모델(예: gpt-4o-mini)을 쓰려면 이 리스트 자체를 고쳐야 합니다.

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 이 코드가 실제로 만드는 딕셔너리 구조를 그대로 재현해봅니다.

```bash
uv run python -c "
openai_access_token = 'sk-...'
model = 'gpt-4o'
graph_config = {
    'llm': {
        'api_key': openai_access_token,
        'model': model,
    },
}
print(graph_config)
"
```

```
{'llm': {'api_key': 'sk-...', 'model': 'gpt-4o'}}
```

### Step 4. SmartScraperGraph 생성

**목적.** 앞서 모은 프롬프트·URL·설정으로 실제 스크래핑 파이프라인 객체를 만듭니다.

**할 일.**

`starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:30-34`

```python
    smart_scraper_graph = SmartScraperGraph(
        prompt=user_prompt,
        source=url,
        config=graph_config
    )
```

`SmartScraperGraph`는 이 시점에는 아직 아무것도 실행하지 않습니다. `prompt`(무엇을 추출할지), `source`(어디서, URL 또는 로컬 HTML), `config`(어떤 LLM으로)를 묶어 들고 있다가, 다음 Step에서 `.run()`을 호출해야 실제로 페이지를 열고 LLM을 부릅니다. 객체 생성 자체는 네트워크를 타지 않으므로 키가 유효한지도 이 시점에는 확인되지 않습니다(직접 확인: 가짜 키로도 생성 자체는 성공).

![Step 4까지의 구성](diagrams/step4.svg)

**확인.**

```bash
uv run python -c "
from scrapegraphai.graphs import SmartScraperGraph
g = SmartScraperGraph(
    prompt='Extract the page title',
    source='https://example.com',
    config={'llm': {'api_key': 'sk-...', 'model': 'gpt-4o'}}
)
print(type(g).__name__, g.prompt)
"
```

```
SmartScraperGraph Extract the page title
```

### Step 5. 실행과 결과 표시

**목적.** "Scrape" 버튼을 누르면 실제로 파이프라인이 도는 과정을 보고, 키 없이는 어디서 멈추는지 확인합니다.

**할 일.**

`starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:35-38`

```python
    # Scrape the website
    if st.button("Scrape"):
        result = smart_scraper_graph.run()
        st.write(result)
```

`.run()`은 (1) Playwright로 `source` URL을 로드하고 (2) 받아온 HTML을 텍스트로 정리해 (3) `prompt`와 함께 설정된 LLM에 보내는 세 단계를 순서대로 실행하고, 최종 결과를 돌려줍니다. 이 코드에는 `try/except`가 없으므로 도중에 예외가 나면 Streamlit이 화면에 빨간 트레이스백을 그대로 보여줍니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 키가 없어 화면의 최종 결과는 재현하지 못했습니다. 대신 같은 파이프라인을 유효하지 않은 키로 직접 호출해, 실제로 어디서 멈추는지 확인합니다(Step 1에서 `playwright install chromium`을 마쳤다는 전제입니다).

```bash
uv run python -c "
from scrapegraphai.graphs import SmartScraperGraph
smart_scraper_graph = SmartScraperGraph(
    prompt='Extract the page title',
    source='https://example.com',
    config={'llm': {'api_key': 'sk-invalid', 'model': 'gpt-4o'}}
)
try:
    result = smart_scraper_graph.run()
    print(result)
except Exception as e:
    print(f'{type(e).__name__}: {e}')
"
```

직접 확인한 출력(발췌):

```
None of the requested terms ['title'] appear in the parsed content (167 chars). The source may be an error page, may render its content with JavaScript, or the relevant section may have been dropped while parsing; the model will most likely answer NA.
OpenAIAuthenticationError: Error code: 401 - {'error': {'message': 'Incorrect API key provided: sk-invalid. You can find your API key at https://platform.openai.com/account/api-keys.', 'type': 'invalid_request_error', 'code': 'invalid_api_key', 'param': None}, 'status': 401}
```

Playwright로 `https://example.com`을 실제로 로드하는 데는 성공했고(파싱된 본문 167자), LLM 호출 단계에서 키가 거부되며 멈춘 것을 알 수 있습니다. 유효한 키를 넣으면 이 자리에서 대신 추출된 결과(리스트나 딕셔너리 형태)가 `st.write()`로 화면에 그대로 출력됩니다.

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

사용자가 화면에 입력한 URL과 추출 프롬프트는 "Scrape" 버튼 클릭과 함께, 이미 만들어져 있던 `SmartScraperGraph` 객체의 `.run()` 호출로 이어집니다. 이 지점부터는 Day 1의 도구 호출 루프와 달리 되묻는 과정 없이 정해진 순서로만 흐릅니다. 먼저 ScrapeGraphAI는 Playwright로 헤드리스 Chromium을 띄워 `source` URL을 실제로 로드합니다 — 자바스크립트로 렌더링되는 페이지도 이 단계에서 처리됩니다. 로드된 HTML은 텍스트로 정리되어 사용자의 추출 프롬프트, 그리고 `graph_config`에 지정된 모델 이름과 함께 OpenAI API로 전송됩니다. LLM은 이 텍스트에서 프롬프트가 요구한 정보만 골라 구조화된 형태로 답하고, 이 결과가 그대로 `SmartScraperGraph.run()`의 반환값이 되어 `st.write()`를 통해 화면에 표시됩니다. Day 1의 에이전트가 "도구를 부를지 말지"를 LLM이 스스로 판단했다면, 이 파이프라인은 페이지를 가져오는 것도 LLM에 보내는 것도 모두 코드에 고정된 순서라는 점이 다릅니다.

## 실행 체크리스트

- [ ] OpenAI API 키를 발급받아 두었다 (환경변수가 아니라 앱 화면에 입력)
- [ ] `uv venv && uv pip install -r requirements.txt`로 기본 의존성을 설치했다
- [ ] `uv run playwright install chromium`으로 헤드리스 브라우저를 받았다
- [ ] `uv run streamlit run ai_scrapper.py`로 서버를 띄우고 `http://localhost:8501`에서 화면을 확인했다
- [ ] OpenAI 키를 입력하자 모델 선택·URL·프롬프트 입력창이 나타나는 것을 확인했다
- [ ] URL과 프롬프트를 입력하고 "Scrape" 버튼을 눌러 결과를 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| "Scrape" 실행 시 `RuntimeError: Failed to scrape after 1 attempts: BrowserType.launch: Executable doesn't exist at ...\ms-playwright\chromium_headless_shell-1234\chrome-headless-shell-win64\chrome-headless-shell.exe`(폴더 번호 `1234`는 설치된 playwright 버전마다 다를 수 있음)와 함께 Playwright가 `playwright install` 실행을 안내하는 배너가 뜸 | `requirements.txt`의 `playwright`는 파이썬 바인딩만 설치하고, 실제 브라우저 실행 파일은 별도 다운로드가 필요하다. 앱 자체 README는 이 단계를 언급하지 않는다(직접 재현) | `uv run playwright install chromium` 실행 후 재시도 |
| 위 에러 메시지를 콘솔에 출력하는 도중 `UnicodeEncodeError: 'cp949' codec can't encode character '╔'...`까지 추가로 발생해 진짜 원인이 가려짐 | Playwright의 안내 배너가 상자 그리기 유니코드 문자(╔ 등)를 쓰는데, 한국어 Windows의 기본 콘솔 코드페이지(cp949)가 이 문자를 인코딩하지 못한다(직접 확인, 출력을 파이프로 받을 때 재현됨) | 진짜 원인(`RuntimeError`, 브라우저 없음)은 이미 나온 뒤이므로 그 줄을 찾아 위 해결을 따른다. `PYTHONIOENCODING=utf-8` 환경변수를 설정하고 재실행하면 배너까지 깨지지 않고 보인다(직접 확인) |
| "Scrape"를 눌러도 무한 대기 없이 바로 에러가 뜨고, 페이지 로드 자체는 된 것처럼 보임 | OpenAI 키가 없거나 잘못됨. `SmartScraperGraph` 생성 시점에는 키를 검증하지 않고, 실제 LLM 호출 시점(`.run()` 내부)에야 인증을 확인한다(직접 확인: 페이지는 167자를 정상 파싱한 뒤 LLM 단계에서 401로 실패) | 유효한 OpenAI 키를 앱 화면 입력창에 다시 입력 |
| 앱 자체 README의 "Getting Started"가 로컬 버전(`local_ai_scrapper.py`)을 쓸 때도 OpenAI 키가 필요한 것처럼 순서대로 안내 | 문서 구성 오류. `local_ai_scrapper.py`는 OpenAI를 전혀 쓰지 않고 `ollama/llama3.2`(`starter_ai_agents/web_scraping_ai_agent/local_ai_scrapper.py:12`)만 호출한다(직접 확인: 파일에 OpenAI 관련 import 없음) | 로컬 버전을 쓸 때는 OpenAI 키 없이 Ollama만 설치하면 된다 |

## 더 해보기

- `local_ai_scrapper.py`로 전환해 Ollama의 로컬 Llama 3.2로 완전히 무료로 돌려보기 (`ollama pull llama3.2`, `ollama pull nomic-embed-text` 필요, 설정은 `starter_ai_agents/web_scraping_ai_agent/local_ai_scrapper.py:10-22`)
- `st.radio`의 모델 목록에 `"gpt-4o-mini"`를 추가해 더 저렴한 모델로 스크래핑해보기 (`starter_ai_agents/web_scraping_ai_agent/ai_scrapper.py:15`)
- 여러 페이지를 한 번에 스크래핑하려면 `url`을 리스트로 바꾸고 `SmartScraperGraph`를 반복 생성하는 코드를 직접 추가해보기

## 다음 날 예고

[Day 003 · 🎙️ AI Blog to Podcast Agent](../day003-ai-blog-to-podcast-agent/README.md) — 블로그 글 하나를 요약해 팟캐스트 오디오로 바꾸는 에이전트를 만듭니다.
