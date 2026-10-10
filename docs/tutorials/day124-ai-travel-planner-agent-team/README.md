# Day 124 · 🌏 AI Travel Planner Agent Team

> 볼륨 8 🤝 Multi-agent Teams · 난이도 ★★★ ⚠(앱이 쓰는 모델 `google/gemini-2.0-flash-001`은 Google 폐기 문서에 종료일 2026-06-01로 올라 있고 OpenRouter의 오늘 모델 목록에도 없으며, `uv sync`가 오늘 풀어내는 환경은 import조차 되지 않는다) · 예상 소요 200분(앱은 `backend/`와 `client/` 두 덩어리에 파일이 92개지만 여행 계획 요청 하나가 지나가는 길만 따라가고, 설치를 세 번 고쳐야 하고, 가짜 서버 셋과 대역 DB를 세워 터미널 둘로 돌려 보고, 실패 경로 넷을 일부러 일으켜 봐야 해서 읽는 시간보다 손으로 돌려 보는 시간이 더 걸립니다) · API 비용 대략 한 번에 $0.1 이하 — 모델 부분만의 어림입니다. 가짜 서버가 받은 모델 요청 12건의 본문(`json.dumps`한 요청 전체)이 합쳐 78,164자(4자당 1토큰으로 어림잡아 입력 약 2만 토큰)였고, 대체 모델로 쓸 `google/gemini-3.6-flash`는 OpenRouter 모델 목록(https://openrouter.ai/api/v1/models, 2026-10-10 확인)에서 입력 $0.75·출력 $3.75/1M 토큰입니다. 출력 길이와 실제 Exa·Firecrawl 도구 결과의 크기, 두 서비스의 요금은 확인하지 못했습니다. 이 문서의 가짜 서버 실험은 무료 · 원본 앱: `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team`

## 오늘 만들 것

출발지·목적지·날짜·예산·여행 취향을 일곱 단계 폼에 적어 제출하면 여행 계획이 만들어지는 웹 앱입니다. 프로세스가 둘입니다. Next.js 클라이언트(`client/`)는 폼 값을 PostgreSQL에 저장하고 Python 백엔드(`backend/`, FastAPI)에 "이 계획을 만들라"고 알린 뒤 곧바로 상세 화면으로 넘어가 5초마다 DB를 읽습니다. 백엔드는 요청을 받자마자 응답을 돌려주고, 백그라운드 작업이 agno 에이전트 일곱을 **차례로** 돌립니다. 목적지 조사, 항공편, 호텔, 식당, 일정, 예산, 그리고 앞 글을 JSON으로 바꾸는 변환 에이전트입니다. 단계마다 DB의 `currentStep`을 바꾸고, 끝나면 결과를 DB에 넣습니다. 원본 폴더에는 추적되는 파일이 92개이고 잠금 파일 둘(`uv.lock`·`pnpm-lock.yaml`)을 빼도 9,180줄입니다(`git ls-files`로 직접 셈). 오늘은 요청 하나가 지나가는 길만 따라가고 나머지는 아래 컴포넌트 표에 역할만 적습니다.

직접 돌려 보고 알게 된 특이점이 아홉입니다. 첫째, 앱 이름과 달리 팀은 일하지 않습니다. `Team`은 만들어지지만 한 번도 `run`되지 않고, 계획은 에이전트 여섯을 `arun`으로 차례로 부른 결과입니다(Step 2·5). 둘째, 모델 `google/gemini-2.0-flash-001`은 내려갔습니다(Step 2). 셋째, 오늘 `uv sync`로는 앱이 import되지 않습니다. 잠금 파일은 `agno` 1.5.6에 묶여 있는데 `pyproject.toml`은 `agno>=2.3.24`를 요구하고, 고쳐 설치해도 앱의 `tools/scrape.py`와 agno의 `FirecrawlTools`가 서로 다른 `firecrawl-py`를 요구해 PyPI의 어떤 버전으로도 둘이 함께 되지 않습니다(Step 1). 넷째, DB에 닿지 못하면 서버가 아예 뜨지 않습니다(Step 4). 다섯째, 항공편 도구는 어떤 예외든 삼키고 빈 목록을 돌려주며, 기본 경로가 실패하면 조회 주소를 제3자 사이트 `try.playwright.tech`로 보냅니다(Step 3). 여섯째, 변환 에이전트가 받는 글에는 예산 에이전트의 글이 들어 있지 않습니다(Step 5). 일곱째, 모델 호출이 실패해도 agno의 `arun`은 예외를 던지지 않고, 앱은 에이전트의 "답"으로 에이전트가 받은 질문을 그대로 이어 붙입니다. 마지막에야 JSON 변환이 실패하면 오류 문구는 모델 오류가 아니라 JSON 오류로 나옵니다(Step 7). 여덟째, `Dockerfile`은 없는 폴더를 복사합니다(Step 4). 아홉째, `main.py`는 서버를 모든 네트워크 인터페이스(`0.0.0.0`)에 엽니다(Step 4).

키가 없어도 `backend/`의 Step 1~7이 모두 됩니다. 모델·Exa·Firecrawl은 내 PC의 가짜 서버가 대신하고, Google Flights 조회는 인자를 기록하는 대역 함수로, PostgreSQL은 같은 모델 정의로 만든 SQLite 파일로 바꿉니다. `client/`는 설치도 실행도 하지 않았고 소스를 읽었습니다(`npm install`·`prisma generate`를 하지 않음). 이 문서를 만들며 앱 코드가 OpenRouter·Exa·Firecrawl·Google·agno로 보낸 요청은 한 건도 없습니다(값을 확인하려고 Google·OpenAI 문서와 OpenRouter 모델 목록·PyPI 페이지는 읽었습니다). 그래서 문서에 나오는 계획 내용은 가짜 서버의 고정 문장이고 어떤 여행 정보의 근거도 아닙니다. 실제 모델이 도구를 어떤 순서로 부르는지, 실제 Exa·Firecrawl·Google Flights 응답, PostgreSQL에서의 동작, 브라우저에서 보이는 화면은 확인하지 못했습니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| Python 3.12 이상 | 앱의 `pyproject.toml`이 `requires-python = ">=3.12"`입니다. 이 문서는 3.13.3으로 확인했습니다 | 공통 사전 준비와 같음 |
| OpenRouter API 키 | 원본 그대로 쓰려면 `OPENROUTER_API_KEY`. 단, 앱의 모델 ID가 내려가 있어 바꿔야 합니다(Step 2). 이 문서의 확인에는 필요 없습니다 | https://openrouter.ai 의 계정 화면(주소는 직접 열어 보지 못했음) |
| Exa API 키 | 목적지·식당·일정 에이전트의 검색(`EXA_API_KEY`). 키가 없으면 앱이 **import 단계에서** 멈춥니다(Step 1) | https://exa.ai 의 대시보드(주소는 직접 열어 보지 못했음) |
| Firecrawl API 키 | 호텔 에이전트의 스크랩(`FIRECRAWL_API_KEY`). 키가 없으면 import 단계에서 멈춥니다(Step 1) | https://www.firecrawl.dev 의 대시보드(주소는 직접 열어 보지 못했음) |
| PostgreSQL | 클라이언트(Prisma)와 백엔드(SQLAlchemy)가 같은 DB를 씁니다. 앱이 띄워 주지 않습니다. **이 문서는 쓰지 않았고** 같은 모델 정의로 만든 SQLite 파일로 대신했습니다(Step 4) | 직접 준비(이 문서는 실행하지 않았음) |
| Node.js·pnpm | `client/` 실행용(`packageManager`가 pnpm 9.15.0). **이 문서는 설치하지 않았습니다** | 직접 준비(이 문서는 실행하지 않았음) |
| 인터넷 연결 | PyPI 설치. 앱을 실제로 쓸 때는 OpenRouter, Exa, Firecrawl, Google Flights(`www.google.com`), 경우에 따라 `try.playwright.tech`, agno 통계 서버(`api.agno.com`)에 접속합니다 | 별도 설치 없음 |

이 문서의 스크립트는 한글을 출력합니다. 한국어 Windows에서 출력을 파이프나 파일로 받으면 기본 인코딩(`cp949`)이 막힐 수 있으니 셸을 먼저 이렇게 맞춰 두세요.

```bash
export PYTHONIOENCODING=utf-8
```

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 일곱 단계 폼 (`client/app/plan/page.tsx`) | 폼 값을 모아 `/api/plan/submit`에 POST하고 1.5초 뒤 `/plan/{id}`로 넘어간다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/plan/page.tsx:285-318` |
| 제출 라우트 (`client/app/api/plan/submit/route.ts`) | 폼 값을 `trip_plan`에 저장하고, 같은 값을 백엔드 `/api/plan/trigger`로 보낸다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plan/submit/route.ts:29-154` |
| 상세 화면 (`client/app/plan/[id]/page.tsx`) | 5초마다 `/api/plans/{id}`를 읽고, 완료되면 결과 JSON을 두 번 파싱해 그린다. 실패하면 재시도 버튼 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/plan/[id]/page.tsx:224-410` |
| 폴링 라우트 (`client/app/api/plans/[id]/route.ts`) | 상세 화면이 5초마다 부르는 GET. `tripPlan.findUnique`로 계획과 상태·결과를 읽어 돌려준다(DELETE도 있음) | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plans/[id]/route.ts:4-46` |
| 로그인 가드 (`client/middleware.ts`) | `/plan`에 `matcher`가 걸려 better-auth 세션이 없으면 `/auth`로 보낸다. 폼에 닿기 전에 로그인이 필요하다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/middleware.ts:5-33` |
| 나머지 클라이언트 | 인증 화면(`app/auth/page.tsx`)·인증 라우트(`app/api/auth/[...all]/route.ts`, `lib/auth.ts`), 계획 목록(`app/plans/page.tsx`·`app/api/plans/route.ts`), 첫 화면(`app/page.tsx`), UI 부품(`components/`), 스키마 SQL(`client/schema.sql`)과 Prisma 마이그레이션(`prisma/migrations/`). 요청 경로 밖이라 다루지 않는다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/plans/page.tsx:1-389` |
| 재시도 라우트 | 상태 행을 `processing`으로 바꾸고 저장된 폼 값으로 백엔드를 다시 부른다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plans/[id]/retry/route.ts:1-139` |
| Prisma 스키마 | 사용자·세션(better-auth)과 `trip_plan`·`trip_plan_status`·`trip_plan_output`·`plan_tasks` | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/prisma/schema.prisma:1-162` |
| FastAPI 앱 (`api/app.py`) | 시작할 때 DB 풀을 만들고, CORS를 모두 허용하고, `/api/health`와 `/api/plan/trigger`를 단다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/api/app.py:12-55` |
| 라우터 (`router/plan.py`) | 작업 행을 만들고 백그라운드 작업을 띄운 뒤 곧바로 응답한다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/router/plan.py:13-84` |
| 계획 서비스 (`services/plan_service.py`) | 폼을 마크다운으로 바꾸고, 에이전트 여섯과 변환 에이전트를 차례로 부르고, 단계마다 상태를 쓰고, 결과를 저장한다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/plan_service.py:30-413` |
| 에이전트 여섯 | 목적지·항공편·호텔·식당·일정·예산. 앞 넷과 일정은 도구가 있다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/destination.py:6-67`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/flight.py:6-67`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/hotel.py:7-81`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/food.py:5-115`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/itinerary.py:11-126`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/budget.py:4-39` |
| 변환 에이전트 | 앞 다섯 글을 `TravelPlanTeamResponse` 스키마의 JSON 문자열로 바꾼다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/structured_output.py:36-127` |
| `Team` | 만들어지기만 하고 `run`되지 않는다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/team.py:22-321` |
| 모델 설정 | OpenRouter 모델 셋. 쓰이는 것은 `model` 하나 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/config/llm.py:8-12` |
| 앱 도구 넷 | 구글 항공편 조회, Kayak 호텔·항공 URL 만들기, Firecrawl 스크랩 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/google_flight.py:8-52`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/kayak_hotel.py:7-56`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/kayak_flight.py:7-59`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:7-34` |
| DB 서비스·저장소 | SQLAlchemy 비동기 엔진, 세션, 작업·상태·결과 행 읽고 쓰기 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/db_service.py:24-101`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/repository/plan_task_repository.py:11-76`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/repository/trip_plan_repository.py:11-152` |
| 마이그레이션 SQL | 백엔드 쪽 표 정의. Prisma 스키마와 겹친다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/migrations/create_plan_tasks_table.sql:1-34`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/migrations/create_trip_plan_tables.sql:1-50` |
| 곁가지 스크립트 | `broswer.py`는 호텔 에이전트를 import하자마자 돌린다(브라우저를 쓰지 않는다). `travel_planning_team.py`는 import하자마자 구글 항공편을 조회한다. 둘 다 요청 경로 밖이다 | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/broswer.py:1-54`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/travel_planning_team.py:1-14` |
| `Dockerfile`·`docker.sh` | 이미지 빌드·푸시 스크립트. 없는 폴더를 복사한다(Step 4) | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/Dockerfile:1-46`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/docker.sh:1-24` |
| OpenRouter·Exa·Firecrawl·Google Flights·`try.playwright.tech`·agno 통계 API | 모델 응답, 검색, 스크랩, 항공편 조회, 조회 대체 경로, 익명 통계 | 코드 없음 (외부 서비스) |

위 그림은 에이전트·도구를 한 묶음으로, 백엔드의 라우터와 계획 서비스를 한 묶음으로 그렸습니다. 에이전트와 도구, 도구와 외부 서비스를 하나하나 이으면 세로가 1,000px를 넘었기 때문입니다. 라우터와 서비스, DB 사이의 관계는 아래 그림에 있습니다. 라우터가 작업 행(`plan_tasks`)을 쓰고, 서비스가 상태와 결과 행을 쓰며, 서비스가 결과 문자열을 라우터에 돌려줍니다.

![라우터·서비스·DB](diagrams/extra-backend.svg)

어느 에이전트가 어느 도구를 갖는지는 아래 그림입니다. `ExaTools`를 목적지·식당·일정 에이전트가 각자 따로 만들어 쓰고, 호텔 에이전트만 앱이 만든 도구 둘을 갖고, 일정 에이전트의 `scrape_website`는 앱의 `tools/scrape.py`가 아니라 agno의 `FirecrawlTools`가 내놓는 같은 이름의 도구입니다(Step 2에서 확인).

![에이전트와 도구](diagrams/extra-tools.svg)

도구가 바깥으로 보내는 요청과, 에이전트가 OpenRouter·agno 통계 API로 보내는 요청은 아래 그림입니다. 모델 요청은 에이전트 일곱 모두에서 나가고, 통계는 `AGNO_TELEMETRY`를 끄지 않으면 에이전트 일곱 모두가 보내려 합니다(Step 7). Kayak URL 도구는 문자열만 만들어 외부로 나가는 선이 없습니다.

![도구·모델·통계와 외부 서비스](diagrams/extra-externals.svg)

`Team`이 어디에 있는지는 아래 그림입니다. 정의 파일은 import되고 멤버로 여섯을 갖지만, 서비스가 부르는 것은 `Team`이 아니라 에이전트 여섯입니다.

![Team과 에이전트](diagrams/extra-team.svg)

## 단계별 진행

### Step 1. 환경 만들기 — 설치해도 import가 막히는 세 곳

**목적.** 앱 폴더에서 의존성을 설치하고 `api.app`이 import되는 상태를 만듭니다.

**할 일.** 저장소 루트에서 시작합니다.

```bash
cd advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend
uv sync
uv pip install -U google-genai "firecrawl-py>=3"
```

(pip 대안은 `pip install -r`로 풀 수 없습니다. 이 폴더에는 `requirements.txt`가 없고 `pyproject.toml`과 `uv.lock`뿐이기 때문입니다. PowerShell도 같은 세 줄입니다. `cd`만 `\`로 쓰면 됩니다. 실행해 보지 못했습니다.) 이 문서의 출력은 저장소 안의 폴더에 `.venv`를 만들지 않으려고 폴더를 스크래치로 복사해 `UV_PROJECT_ENVIRONMENT`로 가상환경 위치를 따로 준 환경에서 얻었습니다. 같은 명령을 앱 폴더에서 돌리면 `backend/.venv`가 생기는데 이 경로는 저장소의 `.gitignore`에 있습니다(`git check-ignore`로 직접 확인). 대신 `uv.lock`이 고쳐 쓰입니다. 아래 둘째 단락의 까닭 때문입니다.

의존성은 `pyproject.toml`이 정합니다. 열다섯 개 가운데 요청 경로에 쓰이는 것은 `agno`, `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`(DB 드라이버), `exa-py`, `firecrawl-py`, `fast-flights`, `loguru`, `python-dotenv`, `pydantic`, `cuid2`입니다. `boto3`·`mem0ai`는 코드 어디에도 import되지 않고, `google-genai`는 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/config/llm.py:1`이 쓰지도 않는 Gemini 클래스를 불러오고 agno 3.1.2의 그 클래스가 새 `google-genai`를 요구해서 필요합니다(Step 2).

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/pyproject.toml:1-23`

```toml
[project]
name = "agno-hackathon"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "agno>=2.3.24",
    "asyncpg>=0.30.0",
    "boto3>=1.38.27",
    "cuid2>=2.0.1",
    "exa-py>=1.13.1",
    "fast-flights>=2.2",
    "fastapi>=0.115.12",
    "firecrawl-py>=2.7.1",
    "google-genai>=1.18.0",
    "loguru>=0.7.3",
    "mem0ai>=0.1.102",
    "pydantic>=2.11.5",
    "python-dotenv>=1.1.0",
    "sqlalchemy>=2.0.41",
    "uvicorn>=0.34.2",
]
```

문제는 `uv.lock`이 이 요구와 맞지 않는다는 것입니다. 잠금 파일에는 `agno` 1.5.6이 적혀 있는데 `pyproject.toml`은 `agno>=2.3.24`를 요구합니다. 오늘(2026-10-10) 원본 잠금 파일로 확인한 값입니다.

```bash
uv lock --check
```

```text
Resolved 91 packages in 369ms
error: The lockfile at `uv.lock` needs to be updated, but `--locked` was provided. To update the lockfile, run `uv lock`.
```

(위는 uv 0.7.2의 문구입니다. uv 0.11.33은 같은 잠금에 `error: The lockfile at uv.lock needs to be updated, but --check was provided.`와 `hint: To update the lockfile, run uv lock.`을 냅니다. 둘 다 직접 확인했습니다.)

두 길이 있고 둘 다 막힙니다. 잠금 그대로(`uv sync --frozen`) 설치하면 `agno` 1.5.6이 들어오고, 앱은 첫 에이전트 파일에서 멈춥니다(`agno` 2.x 이후의 이름 `add_datetime_to_context`를 씀: `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/destination.py:63`). 잠금을 갱신하는 `uv sync`는 `agno`를 3.1.2로 올리지만 잠금에 있던 `google-genai`·`firecrawl-py` 같은 패키지는 그대로 둡니다. 그러면 세 곳에서 막힙니다. 직접 확인한 출력입니다(`uv sync --frozen` 환경의 `import agents.destination`, `uv sync` 환경의 `import config.llm`과 `import agents.destination` 끝 줄).

```text
TypeError: Agent.__init__() got an unexpected keyword argument 'add_datetime_to_context'
ImportError: `google-genai` not installed or not at the latest version. Please install it using `pip install -U google-genai`
ImportError: `firecrawl-py` not installed. Please install using `pip install firecrawl-py`
```

첫 줄이 `--frozen`, 나머지 둘이 `uv sync` 환경입니다(첫 줄은 이 Step 끝의 가짜 키를 셸에 둔 상태에서 나오고, 키가 없으면 그보다 먼저 `ValueError: API key must be provided as an argument or in EXA_API_KEY environment variable`로 멈춥니다. 직접 확인). 둘째 줄은 `config/llm.py`의 첫 줄이 쓰지 않는 `Gemini`를 불러와서 나고(잠금의 `google-genai` 1.18.0이 agno 3.1.2가 요구하는 이름 `FileSearch`를 갖지 못함), 셋째 줄은 `agno.tools.firecrawl`이 `from firecrawl.types import ScrapeOptions`를 하는데 잠금의 `firecrawl-py` 2.7.1에 `firecrawl.types`가 없어서 납니다. 위 명령의 `uv pip install -U`가 이 둘을 올립니다. 그런데 올리면 **앱 자신의** import가 새로 막힙니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:1`

```python
from firecrawl import FirecrawlApp, ScrapeOptions
```

`firecrawl-py` 4.50.0에는 이 이름이 없고(`V1ScrapeOptions`로 바뀜) `FirecrawlApp`도 새 클래스라 `scrape_url`이 없습니다. 어느 버전이 둘을 함께 만족하는지 찾아봤습니다. 2.7.1·2.16.0·2.16.5는 앱이 쓰는 이름과 `scrape_url`이 있지만 `firecrawl.types`가 없고, 3.0.2·3.0.3·3.4.0·4.0.0·4.50.0은 `firecrawl.types`가 있지만 `from firecrawl import ScrapeOptions`와 `FirecrawlApp.scrape_url`이 없습니다(직접 확인). agno 쪽도 시험한 일곱 버전(2.0.0·2.2.10·2.3.23·2.3.24·2.6.22·3.0.0·3.1.2) 모두 `firecrawl.types`를 요구해 agno를 내려도 풀리지 않습니다(2.0.0·2.2.10·2.3.23·3.1.2는 import를 해 봤고 2.3.24·2.6.22·3.0.0은 소스를 읽어 확인). 그래서 앱 파일을 고치지 않고 풀려면 별칭이 필요합니다. 4.x에는 옛 API가 `V1FirecrawlApp`·`V1ScrapeOptions`로 남아 있습니다. 별칭 파일 `shim.py`를 `backend/`에 둡니다. 앱보다 **먼저** import해야 하고, agno가 새 `FirecrawlApp`을 먼저 잡게 하려고 `agno.tools.firecrawl`을 그 안에서 import합니다.

```python
# firecrawl-py 3.x 이상에서도 앱의 옛 import(tools/scrape.py:1)가 되게 하는 별칭이다. 앱 파일은 고치지 않는다.
import firecrawl
import agno.tools.firecrawl  # noqa: F401  agno가 새 FirecrawlApp을 먼저 잡게 한다
firecrawl.FirecrawlApp = firecrawl.V1FirecrawlApp
firecrawl.ScrapeOptions = firecrawl.V1ScrapeOptions
```

(복사본의 `tools/scrape.py` 첫 줄을 `from firecrawl import V1FirecrawlApp as FirecrawlApp, V1ScrapeOptions as ScrapeOptions`로 고쳐도 같습니다. 이 문서는 원본을 건드리지 않으려고 별칭 파일을 썼습니다.) 설치된 버전은 이렇습니다(직접 확인, 열한 줄). `uv sync`만 했을 때와 `uv pip install -U` 뒤를 나란히 적습니다.

```text
패키지          uv sync 직후   -U 뒤
agno            3.1.2          3.1.2
asyncpg         0.30.0         0.30.0
exa-py          1.13.1         1.13.1
fast-flights    2.2            2.2
fastapi         0.115.12       0.115.12
firecrawl-py    2.7.1          4.50.0
google-genai    1.18.0         2.29.0
openai          1.82.1         1.82.1
pydantic        2.11.5         2.14.0
sqlalchemy      2.0.41         2.0.41
uvicorn         0.34.2         0.34.2
```

한 가지 더, 이 환경에서는 `uv run`을 그냥 쓰면 안 됩니다. 프로젝트 환경을 잠금에 맞춰 **되돌리기** 때문입니다. 복사한 환경에서 시험하자 `uv run python …`이 `Uninstalled 25 packages`·`Installed 25 packages`를 찍고 `google-genai`를 1.18.0으로, `firecrawl-py`를 2.7.1로 되돌렸습니다(직접 확인). 이 시리즈의 명령은 `uv run --no-project`를 씁니다. 프로젝트를 찾지 않아 동기화도 하지 않고 폴더의 `.venv`를 그대로 쓰므로, 올린 패키지가 그대로 남습니다(`backend/.venv`에 같은 환경을 두고 시험: `google-genai` 2.29.0·`firecrawl-py` 4.50.0 유지, `shim`과 `api.app` import 통과).

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 이 앱은 import하는 순간 키 두 개를 요구합니다. Firecrawl는 `tools/scrape.py`가 모듈 맨 위에서 클라이언트를 만들고, Exa는 `ExaTools`가 만들어질 때 확인합니다. 모델 키(`OPENROUTER_API_KEY`)는 에이전트를 실제로 돌릴 때까지 요구하지 않습니다. 가짜 키로 import를 확인합니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:7`

```python
app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
```

```bash
export FIRECRAWL_API_KEY=fc-fake EXA_API_KEY=exa-fake OPENROUTER_API_KEY=or-fake
uv run --no-project python -c "import shim, api.app; print('api.app import OK')"
```

```powershell
$env:FIRECRAWL_API_KEY = "fc-fake"; $env:EXA_API_KEY = "exa-fake"; $env:OPENROUTER_API_KEY = "or-fake"
uv run --no-project python -c "import shim, api.app; print('api.app import OK')"
```

(PowerShell 줄은 실행해 보지 못했습니다.) 직접 확인한 출력입니다.

```text
api.app import OK
```

키를 하나씩 빼면 이렇게 끝납니다(직접 확인, 마지막 줄).

```text
ValueError: No API key provided
ValueError: API key must be provided as an argument or in EXA_API_KEY environment variable
```

앞이 `FIRECRAWL_API_KEY`, 뒤가 `EXA_API_KEY`를 뺐을 때입니다. 이 앱은 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/main.py:6`의 `load_dotenv()`로 `.env`를 읽습니다. 이 함수는 `main.py`가 있는 폴더에서 위쪽 폴더로 올라가며 `.env`를 찾습니다. 다만 `main.py`를 거치지 않고 `api.app`을 직접 import하는 위 확인에서는 호출되지 않으므로 키를 셸에 넣었습니다.

### Step 2. 에이전트 일곱과 모델 — 팀은 만들어지기만 합니다

**목적.** 에이전트의 구성, 모델 ID와 키가 들어가는 자리, 그리고 이 앱이 이름처럼 "팀"인지 확인합니다.

**할 일.** 모델은 한 파일에서 정해집니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/config/llm.py:1-12`

```python
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter

# model = Gemini(id="gemini-2.0-flash-001", temperature=0.1)
# model2 = OpenAIChat(id="gpt-4o", temperature=0.1)

model = OpenRouter(id="google/gemini-2.0-flash-001", temperature=0.3, max_tokens=8096)
model2 = OpenRouter(id="openai/gpt-4o", temperature=0.1)
model_zero = OpenRouter(
    id="google/gemini-2.0-flash-001", temperature=0.1, max_tokens=8096
)
```

주석 처리된 5·6행은 Gemini·OpenAI 직접 호출이고 실제로는 모두 OpenRouter 경유입니다. 쓰이는 것은 `model`(8행) 하나입니다. `model2`는 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/team.py:2`가 import만 하고 쓰지 않으며, `model_zero`는 아무도 쓰지 않습니다(`--exclude-dir=.venv`를 붙인 `grep`으로 직접 확인. 출력은 아래와 같고, 앞 Step에서 만든 `.venv`를 빼지 않으면 패키지 파일까지 걸립니다). `agno`의 `OpenRouter`는 `base_url`이 `https://openrouter.ai/api/v1`이고 키는 `OPENROUTER_API_KEY`에서 읽습니다(agno 3.1.2 소스로 확인).

```bash
grep -rn "model2\|model_zero" --include=*.py --exclude-dir=.venv .
```

```text
./agents/team.py:2:from config.llm import model, model2
./broswer.py:20:#     model=model2,
./config/llm.py:6:# model2 = OpenAIChat(id="gpt-4o", temperature=0.1)
./config/llm.py:9:model2 = OpenRouter(id="openai/gpt-4o", temperature=0.1)
./config/llm.py:10:model_zero = OpenRouter(
```

같은 방식으로 `.env.example`의 변수 열 개 가운데 코드가 읽는 것을 세어 봤습니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/.env.example:1-20`

```text

# Bright Data credentials
BRIGHT_DATA_API_TOKEN=your_bright_data_api_token
BRIGHT_DATA_BROWSER_AUTH=your_bright_data_browser_auth

# Database connection URL
DATABASE_URL=your_database_url

# OpenRouter API key
OPENROUTER_API_KEY=your_openrouter_api_key

# OpenAI API key
OPENAI_API_KEY=your_openai_api_key

# Cloudflare R2 configuration
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_R2_ACCESS_KEY_ID=your_r2_access_key_id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_r2_secret_access_key

EXA_API_KEY=EXA_API_KEY
```

`DATABASE_URL`(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/db_service.py:24`), `OPENROUTER_API_KEY`(agno), `EXA_API_KEY`(agno의 `ExaTools`), `FIRECRAWL_API_KEY`(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:7`) 넷만 쓰입니다. 나머지 여섯 — `OPENAI_API_KEY`, `BRIGHT_DATA_*` 둘, `CLOUDFLARE_*` 셋 — 은 어떤 `.py`에서도 읽지 않습니다(`grep -rniE "OPENAI_API_KEY|BRIGHT_DATA|CLOUDFLARE|boto3|mem0" --include=*.py --exclude-dir=.venv .`가 아무것도 내놓지 않음, 직접 확인. `--exclude-dir=.venv`를 빼면 `.venv/…/agno/cloud/aws/base.py`의 `boto3` 같은 패키지 파일이 수백 줄 걸립니다). 앱 README의 "Gemini (LLM)"도 정확하지 않습니다. 모델 제공자는 OpenRouter이고 Gemini는 그 뒤의 모델 이름입니다.

에이전트 하나는 이렇게 만들어집니다. 목적지 에이전트입니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/destination.py:6-13`

```python
destination_agent = Agent(
    name="Destination Explorer",
    model=model,
    tools=[
        ExaTools(
            num_results=10,
        ),
    ],
```

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/destination.py:62-66`

```python
    markdown=True,
    add_datetime_to_context=True,
    retries=3,
    delay_between_retries=2,
    exponential_backoff=True,
```

`retries`·`delay_between_retries`·`exponential_backoff`가 실패 때의 재시도를 정합니다(Step 7에서 몇 번 더 요청하는지 셉니다). 

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** 구성을 읽는 스크립트는 `backend/`에 둡니다. 앞 Step의 `shim`을 먼저 import합니다.

```python
# backend/ 에서 실행. 에이전트 구성을 읽기만 한다(모델은 부르지 않는다).
import shim  # noqa: F401
from agents.team import trip_planning_team as team
from agents.destination import destination_agent
from agents.flight import flight_search_agent
from agents.hotel import hotel_search_agent
from agents.food import dining_agent
from agents.itinerary import itinerary_agent
from agents.budget import budget_agent
for a in (destination_agent, flight_search_agent, hotel_search_agent, dining_agent, itinerary_agent, budget_agent):
    names = []
    for t in a.tools or []:
        names += list(getattr(t, "functions", {})) if hasattr(t, "functions") else [getattr(t, "name", str(t))]
    print(f"{a.name:24} | {a.model.id} | retries={a.retries} | tools={names}")
print("Team:", team.name, "| members:", [m.name for m in team.members], "| mode attr:", getattr(team, "mode", "없음"))
```

```bash
uv run --no-project python check_agents.py
```

직접 확인한 출력입니다(앞의 로그 줄들은 뺐습니다).

```text
Destination Explorer     | google/gemini-2.0-flash-001 | retries=3 | tools=['search_exa', 'get_contents', 'find_similar', 'exa_answer']
Flight Search Assistant  | google/gemini-2.0-flash-001 | retries=3 | tools=['get_flights']
Hotel Search Assistant   | google/gemini-2.0-flash-001 | retries=3 | tools=['scrape_website', 'kayak_hotel_url_generator']
Culinary Guide           | google/gemini-2.0-flash-001 | retries=3 | tools=['search_exa', 'get_contents', 'find_similar', 'exa_answer']
Itinerary Specialist     | google/gemini-2.0-flash-001 | retries=2 | tools=['search_exa', 'get_contents', 'find_similar', 'exa_answer', 'scrape_website', 'think', 'analyze']
Budget Optimizer         | google/gemini-2.0-flash-001 | retries=0 | tools=[]
Team: TripCraft AI Team | members: ['Destination Explorer', 'Hotel Search Assistant', 'Culinary Guide', 'Budget Optimizer', 'Flight Search Assistant', 'Itinerary Specialist'] | mode attr: coordinate
```

여섯 에이전트가 모두 같은 `model` 객체를 씁니다. 일곱째 에이전트(변환)는 목록에 없습니다. 호출할 때마다 `convert_to_model` 안에서 새로 만들어지기 때문입니다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/structured_output.py:52-74`). 앱 README는 "Specialized agents handle flights, hotels, activities, and budgeting in parallel"이라고 적었지만 이들은 병렬이 아닙니다(Step 5).

**`Team`은 일하지 않습니다.** 마지막 줄의 `TripCraft AI Team`은 `coordinate` 모드로 여섯을 멤버로 갖도록 만들어졌지만, 요청 경로에서 `run`되는 곳이 없습니다.

```bash
grep -rn "trip_planning_team" --include=*.py --exclude-dir=.venv .
```

```text
./agents/team.py:22:trip_planning_team = Team(
./check_agents.py:3:from agents.team import trip_planning_team as team
./services/plan_service.py:11:from agents.team import trip_planning_team
./services/plan_service.py:172:        # ai_response = await trip_planning_team.arun(prompt)
```

호출이 있었던 자리는 주석입니다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/plan_service.py:165-179`). 서비스는 `Team`을 쓰는 대신 에이전트를 직접 하나씩 부릅니다. 그런데도 `Team` 정의 파일은 여전히 import되므로(`plan_service.py:11`) 만들어지는 비용과 그 파일의 import 오류는 요청 경로에 남습니다. 앞 날들과 견주면, Day 079 Step 5가 `Team`의 `coordinate` 위임을, Day 109가 리더 `Team`이 멤버 넷에게 일을 넘기는 백엔드를 다뤘습니다. 오늘은 리더가 없고 순서를 서비스 함수가 정합니다.

**모델이 내려갔습니다.** Google의 폐기 문서(https://ai.google.dev/gemini-api/docs/deprecations, 2026-10-10 확인, 페이지 하단 "Last updated 2026-10-09 UTC")의 "Gemini 2.0 models" 표에 이 행이 있습니다(페이지를 내려받아 직접 찾았습니다).

```text
gemini-2.0-flash-001 | February 5, 2025 | June 1, 2026 | gemini-3.6-flash
```

머리는 `Model | Release date | Shutdown date | Recommended replacement`입니다. OpenRouter의 공개 모델 목록(https://openrouter.ai/api/v1/models, 2026-10-10 확인, 458개)에는 `google/gemini-2.0-flash-001`이 없고 `google/gemini-2.0`으로 시작하는 ID가 하나도 없습니다(직접 확인). 키가 없어 실제 요청이 어떤 오류를 돌려주는지는 보지 못했습니다. `model2`의 `openai/gpt-4o`는 목록에 있고($2.5·$10/1M) OpenAI 폐기 문서(https://developers.openai.com/api/docs/deprecations, 2026-10-10 확인)에서 `gpt-4o`는 대체 모델 칸에만 나옵니다. 쓰이는 것은 `model`뿐이라 바꿔야 하는 것은 8행의 ID 하나입니다. 복사본에서 8행과 11행의 ID를 `google/gemini-3.6-flash`로 바꾸고 같은 흐름을 돌리자 모델 요청 12건이 모두 새 ID로 나갔습니다(Step 5의 가짜 서버 로그로 직접 확인).

### Step 3. 도구 — 항공편 조회는 실패를 삼키고, 호텔 URL은 문자열일 뿐입니다

**목적.** 도구 넷이 실제로 무엇을 하는지, 바깥으로 나가는 요청이 무엇인지 확인합니다.

**할 일.** 항공편 도구는 `fast-flights` 라이브러리를 감쌉니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/google_flight.py:35-52`

```python
    try:
        result: Result = get_flights(
            flight_data=[
                FlightData(date=date, from_airport=departure, to_airport=destination)
            ],
            trip=trip,
            seat=cabin_class,
            passengers=Passengers(
                adults=adults, children=children, infants_in_seat=0, infants_on_lap=0
            ),
            fetch_mode="fallback",
        )
        logger.info(f"Flights found: {result.flights}")

        return result.flights
    except Exception as e:
        logger.error(f"Error getting flights from Google Flights: {e}")
        return []
```

두 가지를 봅니다. 첫째, `except Exception`이 **모든 예외를** 로그 한 줄로 바꾸고 빈 목록을 돌려줍니다. 모델은 "조회 실패"와 "항공편 없음"을 구별할 수 없습니다. 둘째, `fetch_mode="fallback"`이 무엇을 하는지는 설치된 `fast-flights` 2.2의 소스(`core.py`·`fallback_playwright.py`)로 확인했습니다. 먼저 `https://www.google.com/travel/flights`를 `verify=False`(TLS 인증서 검증 끔)로 가져오고, 응답이 200이 아니면 두 번째 길로 가고, 200이어도 응답에서 항공편을 읽지 못하면(`parse_response`가 `No flights found`로 `RuntimeError`) `fetch_mode`가 `fallback`일 때 같은 두 번째 길로 다시 갑니다(`core.py`·`fallback_playwright.py`). `https://try.playwright.tech/service/control/run`에 파이썬 코드와 조회 주소(출발·도착 공항, 날짜, 승객 수가 인코딩되어 들어 있음)를 POST해 제3자 서비스가 브라우저를 대신 돌리게 합니다. 이 문서는 어느 쪽도 부르지 않았습니다. `fast-flights`의 요청은 파이썬 소켓이 아니라 Rust 기반 클라이언트(`primp`)가 보내 파이썬 쪽에서 막을 수 없으므로(프록시 환경변수가 통한다는 보장도 없습니다), 실제 함수는 한 번도 부르지 않고 `get_flights`를 대역으로 바꿨습니다.

호텔 도구는 외부로 나가지 않습니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/kayak_hotel.py:38-55`

```python
    logger.info(f"Generating Kayak URL for {destination} on {check_in} to {check_out}")
    URL = f"https://www.kayak.com/hotels/{destination}/{check_in}/{check_out}"
    URL += f"/{adults}adults"
    if children > 0:
        URL += f"/{children}children"

    if rooms > 1:
        URL += f"/{rooms}rooms"


    URL += "?currency=USD"
    if sort.lower() == "price":
        URL += "&sort=price_a"
    elif sort.lower() == "rating":
        URL += "&sort=userrating_b"
    elif sort.lower() == "distance":
        URL += "&sort=distance_a"
    logger.info(f"URL: {URL}")
```

Kayak 주소를 문자열로 이어 붙일 뿐입니다. 호텔 에이전트의 지시문은 "URL 인코딩을 처리하라"(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/hotel.py:31`)고 하지만 코드에는 인코딩이 없습니다. 실제 스크랩은 `scrape_website`가 합니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:28-34`

```python
    scrape_status = app.scrape_url(
        url,
        formats=["markdown"],
        wait_for=30000,
        timeout=60000,
    )
    return scrape_status.markdown
```

`wait_for=30000`·`timeout=60000`이라 한 번에 최대 1분 넘게 걸릴 수 있습니다. `kayak_flight.py`의 항공 URL 도구는 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/flight.py:10-11`에서 주석 처리되어 에이전트가 쓰지 않습니다. 

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 도구를 모델 없이 직접 부르는 스크립트입니다. 가짜 Firecrawl 서버(아래 Step 4의 `fake_services.py`)가 떠 있어야 마지막 줄이 됩니다. 이 서버를 먼저 띄웁니다. 포트는 49152~65535 중 다른 프로그램이 쓰지 않는 번호를 고르세요(이 문서는 53417).

```bash
uv run --no-project python fake_services.py 53417 fake.jsonl mode.txt
```

```python
# backend/ 에서 실행한다. 도구 넷을 모델 없이 직접 부른다. 사용: python check_tools.py <가짜 서버 포트>
import os, sys
FAKE = f"http://127.0.0.1:{sys.argv[1]}"
os.environ["FIRECRAWL_API_URL"] = FAKE
import shim  # noqa: F401
from tools.kayak_hotel import kayak_hotel_url_generator as hotel_url
from tools.kayak_flight import kayak_flight_url_generator as flight_url
import tools.google_flight as gf
from tools.scrape import scrape_website

print("== Kayak 호텔 URL (문자열만 만든다)")
print(hotel_url.entrypoint("Singapore", "2026-12-01", "2026-12-10", 2, 1, 1, "price"))
print("== 도구 설명문의 예시 주소('City Center, Singapore')")
print(hotel_url.entrypoint("City Center, Singapore", "2026-12-01", "2026-12-10"))
print("== Kayak 항공 URL (flight.py가 주석 처리해 에이전트는 쓰지 않는다)")
print(flight_url.entrypoint("BOM", "SIN", "2026-12-01", "2026-12-10", 2, 1, "business", "cheapest"))

print("== get_google_flights: 조회가 예외를 던지면")
def boom(**kw):
    raise OSError("조회 실패를 흉내 냄")
gf.get_flights = boom
print(repr(gf.get_google_flights.entrypoint("BOM", "SIN", "2026-12-01")))

print("== scrape_website: 가짜 Firecrawl 서버에")
print(repr(scrape_website.entrypoint("https://www.kayak.com/hotels/x")))
```

다른 터미널에서 돌립니다.

```bash
export FIRECRAWL_API_KEY=fc-fake EXA_API_KEY=exa-fake
uv run --no-project python check_tools.py 53417
```

```powershell
$env:FIRECRAWL_API_KEY = "fc-fake"; $env:EXA_API_KEY = "exa-fake"
uv run --no-project python check_tools.py 53417
```

(PowerShell 줄은 실행해 보지 못했습니다.)

직접 확인한 출력입니다(앞의 `INFO` 로그 줄들은 뺐고, 오류 로그 한 줄은 맨 앞에 나왔습니다).

```text
2026-10-10 05:51:48.782 | ERROR    | tools.google_flight:get_google_flights:51 - Error getting flights from Google Flights: 조회 실패를 흉내 냄
== Kayak 호텔 URL (문자열만 만든다)
https://www.kayak.com/hotels/Singapore/2026-12-01/2026-12-10/2adults/1children?currency=USD&sort=price_a
== 도구 설명문의 예시 주소('City Center, Singapore')
https://www.kayak.com/hotels/City Center, Singapore/2026-12-01/2026-12-10/1adults?currency=USD
== Kayak 항공 URL (flight.py가 주석 처리해 에이전트는 쓰지 않는다)
https://www.kayak.com/flights/BOM-SIN/2026-12-01/2026-12-10/business/2adults/children-11?currency=USD&sort=price_a
== get_google_flights: 조회가 예외를 던지면
[]
== scrape_website: 가짜 Firecrawl 서버에
'# Fake Kayak page\n- Fake Hotel USD 100\n'
```

도구 설명문이 예시로 든 `City Center, Singapore`는 공백과 쉼표가 그대로 주소에 들어갑니다(실제 Kayak이 이 주소를 받아 주는지는 확인하지 못했습니다). 항공 URL의 `children-11`은 아이마다 나이 11을 박아 넣은 코드(`kayak_flight.py:47-50`)입니다. 가짜 Firecrawl 서버가 받은 요청 본문은 `{"url": …, "origin": "python-sdk@None", "formats": ["markdown"], "waitFor": 30000, "timeout": 60000}`였습니다(`fake.jsonl`).

### Step 4. 백엔드 입구 — DB가 없으면 서버가 뜨지 않습니다

**목적.** FastAPI 앱이 어떻게 뜨는지, `POST /api/plan/trigger`가 무엇을 하고 언제 응답하는지 확인합니다.

**할 일.** 서버를 띄우는 코드는 스무 줄입니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/main.py:1-20`

```python
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
logger.info("Loading environment variables")
load_dotenv()
logger.info("Environment variables loaded")

# Import and setup logging configuration
from config.logger import setup_logging

# Configure logging with loguru
setup_logging(console_level="INFO")

from api.app import app

if __name__ == "__main__":
    logger.info("Starting TripCraft AI API server")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

20행은 `0.0.0.0`입니다. 모든 네트워크 인터페이스에 열려 같은 네트워크의 다른 기기가 접속할 수 있습니다. CORS도 모든 출처를 허용합니다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/api/app.py:45-51`). 이 문서는 `python main.py`를 실행하지 않았고, `main`을 import한 뒤 `uvicorn.run(main.app, host="127.0.0.1", …)`로 루프백에만 엽니다. 독자도 같은 이유로 `uvicorn main:app --host 127.0.0.1 --port 8000`처럼 열기를 권합니다. 포트 8000은 흔한 번호라 이미 다른 프로그램이 쓰고 있지 않은지 `netstat -ano`로 먼저 보세요. 시작할 때 하는 일은 `lifespan`입니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/api/app.py:18-35`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("API server started")

    # Initialize database connection pool
    logger.info("Initializing database connection pool")
    await initialize_db_pool()
    logger.info("Database connection pool initialized")

    yield

    # Shutdown logic
    # Close database connection pool
    logger.info("Closing database connection pool")
    await close_db_pool()

    logger.info("API server shutting down")
```

`initialize_db_pool()`이 DB에 `SELECT 1`을 던져 보고 실패하면 예외를 그대로 올려 **서버가 뜨지 않습니다**.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/db_service.py:24-27`

```python
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL.startswith("postgresql://"):
    # Convert to asyncpg format for SQLAlchemy async
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
```

`DATABASE_URL`은 import 때 한 번 읽히고, `postgresql://`은 `postgresql+asyncpg://`로 바뀝니다. 이 문서는 PostgreSQL을 띄우지 않으므로 같은 `models/`의 정의로 SQLite 파일을 만들고 `sqlite+aiosqlite://`로 연결합니다(`aiosqlite`는 이 대역 전용 설치입니다: `uv pip install aiosqlite`). 표를 만드는 스크립트입니다. 앱의 모델을 그대로 씁니다.

```python
# 원본 모델(models/plan_task.py, models/trip_db.py)로 SQLite 파일에 표를 만든다. Postgres의 대역이다. 사용: python prep_db.py <sqlite 파일>
import sys
from sqlalchemy import create_engine
from models import plan_task, trip_db
eng = create_engine(f"sqlite:///{sys.argv[1]}")
plan_task.Base.metadata.create_all(eng)
trip_db.Base.metadata.create_all(eng)
print(sorted(plan_task.Base.metadata.tables), sorted(trip_db.Base.metadata.tables))
```

```bash
uv pip install aiosqlite
uv run --no-project python prep_db.py fake.db
```

```text
['plan_tasks'] ['trip_plan', 'trip_plan_output', 'trip_plan_status']
```

두 `Base`가 따로 있어(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/models/plan_task.py:24-25`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/models/trip_db.py:13-14`) 표 만들기가 두 번 나뉩니다. 이것이 SQLite 대역이라는 점을 분명히 합니다. 실제 PostgreSQL에서는 `trip_plan_status`·`trip_plan_output`이 `trip_plan`을 외래 키로 참조하므로(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/schema.sql:14`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/schema.sql:26`) 이 문서처럼 지어낸 `trip_plan_id`로 백엔드를 직접 부르면 `create_trip_plan_status`가 외래 키 위반으로 실패해 계획이 돌지 않습니다. `trip_plan` 행이 먼저 있어야 하고, 클라이언트의 제출 라우트가 그 행을 만듭니다. 마이그레이션의 `error_message VARCHAR(500)`(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/migrations/create_plan_tasks_table.sql:12`)도 SQLite에는 길이 제한이 없습니다. 이 문서가 보여 주는 호출 순서·누락·두 겹 JSON·`error` 잔존은 이 대체로 바뀌지 않습니다(같은 모델 정의로 재현). Postgres의 `plan_task_status` 열거형, `trip_plan_status.tripPlanId`의 UNIQUE·외래 키(Prisma 스키마의 `@unique`와 `trip_plan`으로의 참조, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/prisma/schema.prisma:79-105`)는 만들어지지 않았고, 따라서 이 문서가 보는 동작에는 들어 있지 않습니다. 이제 서버를 띄웁니다. 앞 Step의 가짜 서버가 떠 있어야 합니다. 서버를 바깥으로 안내하는 대역은 `run_backend.py`입니다. 앱의 `main`을 고치지 않고 가져온 뒤 모델·Exa·Firecrawl 주소를 가짜 서버로 돌리고, 구글 항공편 조회를 인자를 기록하는 대역으로 바꾸고, 루프백에만 엽니다.

```python
# backend/ 에서 실행한다. main.py를 고치지 않고 그대로 import한 뒤, 바깥으로 나가는 주소만 가짜 서버로 돌리고 127.0.0.1에만 연다.
# 사용: python run_backend.py <백엔드 포트> <가짜 서버 포트>
import os, sys, json, time
BACKEND_PORT, FAKE_PORT = int(sys.argv[1]), int(sys.argv[2])
FAKE = f"http://127.0.0.1:{FAKE_PORT}"
os.environ["FIRECRAWL_API_URL"] = FAKE                       # FirecrawlApp(api_key=...)가 읽는 주소
# 1) firecrawl-py 4.x: 앱의 옛 import가 되도록 별칭을 건다(shim.py)
import shim  # noqa: F401
# 2) Exa 클라이언트 주소
import exa_py.api as ea
_orig = ea.Exa.__init__
def _init(self, *a, **k):
    k.setdefault("base_url", FAKE)
    _orig(self, *a, **k)
ea.Exa.__init__ = _init
# 3) 구글 항공편: 실제 요청 대신 인자를 기록하고 가짜 결과를 돌려준다
import fast_flights
FLIGHT_LOG = os.environ.get("FLIGHT_LOG")
def fake_get_flights(**kw):
    with open(FLIGHT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"t": round(time.time(), 3), "flight_data": [repr(x) for x in kw["flight_data"]], "trip": kw["trip"], "seat": kw["seat"],
                            "passengers": repr(kw["passengers"]), "fetch_mode": kw["fetch_mode"]}, default=str) + "\n")
    time.sleep(float(os.environ.get("FLIGHT_DELAY", "0")))
    return fast_flights.Result(current_price="typical", flights=[fast_flights.Flight(True, "FakeAir", "8:00 AM", "1:00 PM", "", "5 hr", 0, None, "$300")])
# 4) 통계: AGNO_TELEMETRY를 켠 채 돌릴 때 보내려는 내용만 기록한다
if os.environ.get("TELEMETRY_SPY"):
    import agno.api.agent as aa, agno.api.team as at
    def spy(kind):
        async def a(run=None, **k):
            with open(os.environ["TELEMETRY_SPY"], "a", encoding="utf-8") as f:
                f.write(json.dumps({"kind": kind, "data": json.loads(run.model_dump_json())}, default=str) + "\n")
        return a
    aa.acreate_agent_run = spy("agent")
    def sync_spy(kind):
        def s(run=None, **k):
            with open(os.environ["TELEMETRY_SPY"], "a", encoding="utf-8") as f:
                f.write(json.dumps({"kind": kind + "-sync"}) + "\n")
        return s
    aa.create_agent_run = sync_spy("agent")
import main                                               # 원본 그대로 (load_dotenv, 로깅, app)
import config.llm as llm
for m in (llm.model, llm.model2, llm.model_zero):
    m.base_url = f"{FAKE}/api/v1"
import tools.google_flight as gf
gf.get_flights = fake_get_flights
import uvicorn
uvicorn.run(main.app, host="127.0.0.1", port=BACKEND_PORT, log_level="info")
```

가짜 서버는 모델 요청이면 에이전트의 지시문에서 누구인지 알아보고, 첫 요청에는 도구를 부르라고, 도구 결과가 오면 글을 돌려줍니다. 호텔 에이전트는 URL 도구를 부른 뒤 그 URL로 스크랩 도구를 부르게 합니다. 변환 에이전트에는 스키마에 맞는 JSON을 돌려주고, 모드 파일이 `badjson`이면 JSON이 아닌 글을, `http500`이면 500을 돌려줍니다.

```python
# OpenRouter(chat/completions)·Exa(/search)·Firecrawl(/v1/scrape)를 한 프로세스가 흉내 내는 localhost 가짜 서버.
# 사용: python fake_services.py <포트> <로그 JSONL> [모드 파일]
import json, os, re, sys, time, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT, LOG = int(sys.argv[1]), sys.argv[2]
MODE_FILE = sys.argv[3] if len(sys.argv) > 3 else None
LOCK = threading.Lock()
N = [0]

def mode():
    try:
        if not MODE_FILE:
            return "ok"
        raw = open(MODE_FILE, "rb").read()
        # PowerShell 5.1의 `>`는 UTF-16(BOM)으로 쓴다. 둘 다 읽는다.
        text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8-sig")
        return text.strip()
    except OSError:
        return "ok"

# 에이전트마다 system 메시지에 들어 있는 고유 문구로 구분한다
AGENTS = [
    ("flight", "flight search and analysis assistant"),
    ("hotel", "Hotel Search and Data Extraction Assistant"),
    ("dining", "Culinary Research and Recommendation Assistant"),
    ("itinerary", "master itinerary creator"),
    ("budget", "Budget Optimization Instructions"),
    ("destination", "destination research agent"),
    ("convert", "extracting structured travel planning information"),
]

PLAN = {
    "day_by_day_plan": [{"day": 0, "date": "2026-12-01", "morning": "Fake morning", "afternoon": "Fake afternoon", "evening": "Fake evening", "notes": "canned"}],
    "hotels": [{"hotel_name": "Fake Hotel", "price": "USD 100", "rating": "4.5", "address": "1 Fake Rd", "amenities": ["wifi"], "description": "canned", "url": "https://example.invalid/h"}],
    "attractions": [{"name": "Fake Garden", "description": "canned"}],
    "flights": [{"duration": "5h", "price": "USD 300", "departure_time": "08:00", "arrival_time": "13:00", "airline": "FakeAir", "flight_number": "FA1", "url": "", "stops": 0}],
    "restaurants": [{"name": "Fake Noodles", "description": "canned", "location": "Fake St", "url": ""}],
    "budget_insights": ["canned insight"],
    "tips": ["canned tip"],
}

def who(body):
    sys_txt = " ".join(m["content"] for m in body["messages"] if m["role"] in ("system", "developer") and isinstance(m.get("content"), str))
    for name, key in AGENTS:
        if key in sys_txt:
            return name
    first_user = next((m["content"] for m in body["messages"] if m["role"] == "user" and isinstance(m.get("content"), str)), "")
    if "Model schema" in first_user:
        return "convert"
    return "unknown"

def tool_call(i, name, args):
    return {"id": f"call_{i}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}

def chat(body):
    agent = who(body)
    tools = [t["function"]["name"] for t in body.get("tools") or []]
    tool_msgs = [m for m in body["messages"] if m["role"] == "tool"]
    n = len(tool_msgs)
    msg = {"role": "assistant", "content": None}
    if agent == "destination" and "search_exa" in tools and n == 0:
        msg["tool_calls"] = [tool_call(1, "search_exa", {"query": "top attractions in Singapore", "num_results": 3})]
    elif agent == "flight" and "get_flights" in tools and n == 0:
        msg["tool_calls"] = [tool_call(1, "get_flights", {"departure": "BOM", "destination": "SIN", "date": "2026-12-01", "trip": "round-trip", "adults": 2, "children": 1, "cabin_class": "economy"})]
    elif agent == "hotel" and n == 0:
        msg["tool_calls"] = [tool_call(1, "kayak_hotel_url_generator", {"destination": "Singapore", "check_in": "2026-12-01", "check_out": "2026-12-10", "adults": 2, "children": 1, "rooms": 1})]
    elif agent == "hotel" and n == 1:
        url = re.search(r"https://www\.kayak\.com\S+", tool_msgs[0]["content"] or "")
        msg["tool_calls"] = [tool_call(2, "scrape_website", {"url": url.group(0).strip('"') if url else "https://www.kayak.com/hotels/x"})]
    elif agent == "dining" and "search_exa" in tools and n == 0:
        msg["tool_calls"] = [tool_call(1, "search_exa", {"query": "best restaurants in Singapore", "num_results": 3})]
    elif agent == "convert":
        msg["content"] = "this is not json" if mode() == "badjson" else json.dumps(PLAN)
    else:
        msg["content"] = f"[canned {agent} answer]"
    return msg, agent, tools

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("content-length", 0)))
        try:
            body = json.loads(raw)
        except Exception:
            body = {"raw": raw[:200].decode("utf-8", "replace")}
        with LOCK:
            N[0] += 1
            seq = N[0]
        rec = {"seq": seq, "t": round(time.time(), 3), "path": self.path, "ua": self.headers.get("user-agent"),
               "auth": (self.headers.get("authorization") or self.headers.get("x-api-key") or "")[:12], "body": body}
        if self.path.endswith("/chat/completions"):
            time.sleep(float(os.environ.get("FAKE_DELAY", "0")))
            if mode() == "http500":
                rec["agent"] = who(body); rec["status"] = 500
                self._log(rec)
                return self._send(500, {"error": {"message": "fake server error", "code": 500}})
            msg, agent, tools = chat(body)
            rec.update(agent=agent, tools=tools, reply=("tool_calls:" + ",".join(t["function"]["name"] for t in msg["tool_calls"])) if msg.get("tool_calls") else "text")
            self._log(rec)
            return self._send(200, {"id": f"fake{seq}", "object": "chat.completion", "created": int(time.time()), "model": body.get("model"),
                                    "choices": [{"index": 0, "message": msg, "finish_reason": "tool_calls" if msg.get("tool_calls") else "stop"}],
                                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}})
        if self.path == "/search":
            self._log(rec)
            return self._send(200, {"requestId": "fake", "results": [{"id": "https://example.invalid/a", "title": "Fake page", "url": "https://example.invalid/a", "text": "canned page text", "publishedDate": None, "author": None}], "autopromptString": None, "resolvedSearchType": "neural"})
        if self.path == "/v1/scrape":
            self._log(rec)
            return self._send(200, {"success": True, "data": {"markdown": "# Fake Kayak page\n- Fake Hotel USD 100\n", "metadata": {"statusCode": 200}}})
        self._log(rec)
        self._send(404, {"error": "unknown path " + self.path})

    def _log(self, rec):
        with LOCK:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

ThreadingHTTPServer.allow_reuse_address = False   # 다른 프로세스가 쓰는 포트를 겹쳐 잡지 않게 한다
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
```

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 서버를 띄웁니다. 이 문서의 가짜 서버는 53417, 백엔드는 53418이었습니다.

```bash
export FIRECRAWL_API_KEY=fc-fake EXA_API_KEY=exa-fake OPENROUTER_API_KEY=or-fake AGNO_TELEMETRY=false
export DATABASE_URL="sqlite+aiosqlite:///fake.db" FLIGHT_LOG=flight.jsonl
uv run --no-project python run_backend.py 53418 53417
```

```powershell
$env:FIRECRAWL_API_KEY = "fc-fake"; $env:EXA_API_KEY = "exa-fake"; $env:OPENROUTER_API_KEY = "or-fake"; $env:AGNO_TELEMETRY = "false"
$env:DATABASE_URL = "sqlite+aiosqlite:///fake.db"; $env:FLIGHT_LOG = "flight.jsonl"
uv run --no-project python run_backend.py 53418 53417
```

(PowerShell 줄은 실행해 보지 못했습니다.) 직접 확인한 로그 끝 줄과 건강 확인입니다.

```text
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:53418 (Press CTRL+C to quit)
```

```bash
curl -s http://127.0.0.1:53418/api/health
```

```text
{"status":"healthy","timestamp":"2026-10-09T20:26:09.950077+00:00"}
```

(PowerShell 5.1에서는 `curl`이 `Invoke-WebRequest`의 별칭이라 `curl.exe`를 써야 합니다. 실행해 보지 못했습니다.) DB가 없을 때 서버가 어떻게 끝나는지는 `DATABASE_URL`을 바꿔 확인했습니다. 끝에서 두 줄씩입니다(직접 확인).

```text
sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL from given URL string
ERROR:    Application startup failed. Exiting.
```

```text
ConnectionRefusedError: [WinError 1225] 원격 컴퓨터가 네트워크 연결을 거부했습니다
ERROR:    Application startup failed. Exiting.
```

앞이 `DATABASE_URL`이 비었을 때(기본값 `""`)이고, 뒤가 `postgresql://postgres:postgres@127.0.0.1:53421/tripcraft_ai`처럼 아무도 듣지 않는 포트를 가리켰을 때입니다. 이 문서는 이 PC에서 실제로 떠 있는 PostgreSQL(5432)에 접속하지 않았습니다.

이제 요청 핸들러입니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/router/plan.py:31-77`

```python
    try:
        logger.info(f"Triggering travel plan agent for trip ID: {request.trip_plan_id}")
        logger.info(f"Travel plan details: {request.travel_plan}")

        # Create initial task
        task = await create_plan_task(
            trip_plan_id=request.trip_plan_id,
            task_type="travel_plan_generation",
            input_data=request.travel_plan.model_dump(),
        )

        logger.info(f"Task created: {task.id}")

        # Create background task for plan generation
        async def generate_plan_with_tracking():
            try:
                # Update task status to in progress when service starts
                await update_task_status(task.id, TaskStatus.in_progress)
                logger.info(f"Task updated to in progress: {task.id}")

                result = await generate_travel_plan(request)

                # Update task with success status and output
                await update_task_status(
                    task.id, TaskStatus.success, output_data={"travel_plan": result}
                )
                logger.info(f"Task updated to success: {task.id}")
            except Exception as e:
                logger.error(f"Error generating travel plan: {str(e)}")
                # Update task with error status
                await update_task_status(
                    task.id, TaskStatus.error, error_message=str(e)
                )
                logger.info(f"Task updated to error: {task.id}")
                raise

        asyncio.create_task(generate_plan_with_tracking())

        logger.info(
            f"Travel plan agent triggered successfully for trip ID: {request.trip_plan_id}"
        )

        return TravelPlanResponse(
            success=True,
            message="Travel plan agent triggered successfully",
            trip_plan_id=request.trip_plan_id,
        )
```

순서를 봅니다. 요청 본문(`TravelPlanAgentRequest`)을 받아, 작업 행을 `queued`로 만들고(36~40행), 백그라운드 작업을 만들고(67행), 곧바로 `success: True`를 돌려줍니다(73~77행). 에이전트는 응답이 나간 **뒤에** 돕니다. 73~77행의 응답에는 계획이 없고 `trip_plan_id`뿐입니다. 클라이언트가 보낼 본문은 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plan/submit/route.ts:80-109`에 있고, 값 이름을 `snake_case`로 바꿉니다. 같은 모양의 본문을 직접 만들었습니다(이름·도시는 지어낸 값입니다).

```json
{
  "trip_plan_id": "trip-demo-001",
  "travel_plan": {
    "name": "mina",
    "destination": "Singapore",
    "starting_location": "Mumbai",
    "travel_dates": {"start": "2026-12-01T00:00:00.000Z", "end": "2026-12-10T00:00:00.000Z"},
    "date_input_type": "picker",
    "duration": 9,
    "traveling_with": "Family with kids",
    "adults": 2,
    "children": 1,
    "age_groups": ["26-35", "Under 18"],
    "budget": 150000,
    "budget_currency": "INR",
    "travel_style": "comfort",
    "budget_flexible": false,
    "vibes": ["food-focused", "cultural"],
    "priorities": ["Local experiences"],
    "interests": "street food, museums",
    "rooms": 1,
    "pace": [2],
    "been_there_before": "no",
    "loved_places": "",
    "additional_info": "one child under 10"
  }
}
```

`BACKEND_API_URL`은 클라이언트의 두 라우트(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plan/submit/route.ts:114`, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plans/[id]/retry/route.ts:77`)가 읽는데 `client/.env.example`에는 없고 앱 어느 README에도 적혀 있지 않습니다(`grep -rn BACKEND_API_URL`로 직접 확인). 또 클라이언트는 폼 값과 함께 `userId`를 보내지만 라우트는 `userId: null`로 저장합니다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plan/submit/route.ts:74`).

```bash
curl -s -w "\nHTTP %{http_code} in %{time_total}s\n" -X POST http://127.0.0.1:53418/api/plan/trigger -H "Content-Type: application/json" --data-binary @request.json
```

```powershell
curl.exe -s -w "\nHTTP %{http_code} in %{time_total}s\n" -X POST http://127.0.0.1:53418/api/plan/trigger -H "Content-Type: application/json" --data-binary '@request.json'
```

(PowerShell에서는 `@request.json`을 따옴표로 감싸야 합니다. 실행해 보지 못했습니다.)

```text
{"success":true,"message":"Travel plan agent triggered successfully","trip_plan_id":"trip-demo-001"}
HTTP 200 in 0.013168s
```

응답은 0.013초였습니다. 이 사이 DB에는 작업 행이 `queued`로 만들어지고, 응답이 나간 뒤 백그라운드에서 `in_progress`가 됩니다. 계획은 Step 5에서 봅니다.

**배포 파일은 이 코드를 담지 못합니다.** `Dockerfile`이 복사하는 경로를 앱 폴더에서 찾아봤습니다(직접 확인).

```bash
for p in app/ agents/ config/ models/ routers/ services/ api.py server.py; do [ -e "$p" ] && echo "있음  $p" || echo "없음  $p"; done
```

```text
없음  app/
있음  agents/
있음  config/
있음  models/
없음  routers/
있음  services/
없음  api.py
없음  server.py
```

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/Dockerfile:33-39`에 `COPY app/ app/`, `COPY routers/ routers/`, `COPY api.py server.py ./`가 있는데 이 폴더와 파일은 없습니다(실제 폴더는 `api/`·`router/`이고 `main.py`가 진입점). `tools/`·`repository/`는 복사 목록에도 없고, `EXPOSE 8001`과 `gunicorn server:app`(44·47행)은 `main.py`의 8000과도 다릅니다. 이 문서는 Docker를 실행하지 않았고 `docker.sh`(이미지를 `mtwn105` 레지스트리에 푸시)도 실행하지 않았습니다.

### Step 5. 계획 서비스 — 여섯 에이전트를 차례로, 그리고 변환 한 번

**목적.** 요청 한 건이 에이전트를 어떤 순서로, 몇 번의 외부 요청으로 지나는지 끝까지 돌려 봅니다.

**할 일.** 서비스의 중심 함수는 `generate_travel_plan`입니다. 시작부터 봅니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/plan_service.py:131-160`

```python
async def generate_travel_plan(request: TravelPlanAgentRequest) -> str:
    """Generate a travel plan based on the request and log status/output to database."""
    trip_plan_id = request.trip_plan_id
    logger.info(f"Generating travel plan for tripPlanId: {trip_plan_id}")

    # Get or create status entry using repository functions
    status_entry = await get_trip_plan_status(trip_plan_id)
    if not status_entry:
        status_entry = await create_trip_plan_status(
            trip_plan_id=trip_plan_id, status="pending"
        )

    # Update status to processing
    status_entry = await update_trip_plan_status(
        trip_plan_id=trip_plan_id,
        status="processing",
        current_step="Initializing travel plan generation",
        started_at=datetime.now(timezone.utc),
    )

    try:
        travel_request_md = travel_request_to_markdown(request.travel_plan)
        logger.info(f"Travel request markdown: {travel_request_md}")

        # Update status for AI team generation
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Generating plan with TripCraft AI agents",
        )
```

상태 행이 없으면 만들고, `processing`으로 바꾸고, 폼 값을 마크다운으로 바꿔(`travel_request_to_markdown`, 30~128행) 모든 에이전트의 프롬프트에 붙입니다. 이름은 `title()`로, 여행 스타일·분위기·속도는 설명 문장으로 풀립니다. 아래 입력은 이 문서의 요청 본문을 이 함수에 통과시킨 앞부분입니다(목적지 에이전트가 받은 프롬프트에서 가짜 서버 로그로 꺼냈습니다).

```text
# 🧳 Travel Plan Request

## 📍 Trip Overview
- **Traveler:** Mina
- **Route:** Mumbai → Singapore
- **Duration:** 9 days (between December 01, 2026 and December 10, 2026)

## 👥 Travel Group
- **Group Size:** 2 adults, 1 children
- **Traveling With:** Family with kids
- **Age Groups:** 26-35, Under 18
- **Rooms Needed:** 1

## 💰 Budget & Preferences
- **Budget per person:** 150000 INR (Fixed)
- **Travel Style:** mid-range hotels, convenient transportation, and balanced comfort-value ratio
- **Preferred Pace:** 3-4 activities per day with balanced activity and rest periods
```

이어서 에이전트를 부르는 부분은 같은 모양이 다섯 번 반복됩니다. 목적지입니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/plan_service.py:188-211`

```python
        # Destination Research
        destionation_research_response = await destination_agent.arun(
            f"""
            Please research about the destination {request.travel_plan.destination}

            Below are user's travel request:
            {travel_request_md}

            Provide a very detailed research about the destination, its attractions, activities, and other relevant information that user might be interested in.

            Give 10 attractions/activities that user might be interested in.
            """
        )

        logger.info(
            f"Destination research response: {destionation_research_response.messages[-1].content}"
        )

        last_response_content = f"""
        ## Destination Attractions:
        ---
        {destionation_research_response.messages[-1].content}
        ---
"""
```

`await 에이전트.arun(프롬프트)`를 하고, 결과의 **마지막 메시지의 `content`**를 `last_response_content`에 이어 붙입니다. 항공·호텔·식당·일정이 같은 모양이고(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/plan_service.py:219-330`), 달라지는 점은 일정(313~321행)이 지금까지 쌓인 글을 프롬프트에 함께 받는다는 것, 그리고 그 뒤에 예산 에이전트를 부른다는 것입니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/plan_service.py:338-364`

```python
        # Budget
        budget_response = await budget_agent.arun(
            f"""
            Please optimize the budget according to the user's travel request:
            {travel_request_md}

            Based on the following information:
            {last_response_content}
            """
        )

        logger.info(f"Budget response: {budget_response.messages[-1].content}")

        time_end = time.time()
        logger.info(f"Total time taken: {time_end - time_start:.2f} seconds")

        # Update status for response conversion
        await update_trip_plan_status(
            trip_plan_id=trip_plan_id,
            status="processing",
            current_step="Adding finishing touches",
        )

        json_response_output = await convert_to_model(
            last_response_content, TravelPlanTeamResponse
        )
        logger.info(f"Converted Structured Response: {json_response_output[:500]}...")
```

예산 에이전트의 글은 `budget_response`에만 담기고 **`last_response_content`에는 이어 붙지 않습니다.** 변환(361~363행)이 받는 것은 그 변수라 예산 글은 변환 입력에 없습니다. ![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 에이전트 일곱을 한 번 끝까지 돌려 확인합니다. 진행을 지켜볼 스크립트와 로그 요약 스크립트입니다.

```python
# SQLite 파일을 읽기 전용으로 0.2초마다 보고, trip_plan_status.currentStep/status와 plan_tasks.status가 바뀔 때마다 한 줄씩 찍는다.
import sqlite3, sys, time
db, secs = sys.argv[1], float(sys.argv[2])
t0 = time.time(); last = None
while time.time() - t0 < secs:
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=1)
        s = c.execute("select status, currentStep from trip_plan_status").fetchall()
        t = c.execute("select status from plan_tasks").fetchall()
        o = c.execute("select count(*) from trip_plan_output").fetchone()[0]
        c.close()
        cur = (tuple(s), tuple(t), o)
        if cur != last:
            print(f"{time.time()-t0:6.2f}s status={s} task={t} output_rows={o}", flush=True)
            last = cur
        if s and s[0][0] in ("completed", "failed") and t and t[0][0] in ("success", "error"):
            break
    except sqlite3.OperationalError as e:
        pass
    time.sleep(0.2)
```

```python
# 가짜 서버 로그(JSONL)를 한 줄씩 요약한다. 사용: python summarize_log.py <로그> 
import json, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
t0 = rows[0]["t"]
for r in rows:
    if r["path"].endswith("/chat/completions"):
        b = r["body"]
        if r.get("status") == 500:
            what = f'{r["agent"]:<11} chat  -> HTTP 500'
        else:
            what = f'{r["agent"]:<11} chat  model={b["model"]} messages={len(b["messages"])} tools={len(r["tools"])} -> {r["reply"]}'
    elif r["path"] == "/search":
        what = f'{"":<11} exa   {json.dumps(r["body"], ensure_ascii=False)}'
    else:
        what = f'{"":<11} fire  {r["path"]} url={r["body"]["url"]}'
    print(f'{r["seq"]:>2} +{r["t"] - t0:4.1f}s {what}')
```

가짜 서버를 `FAKE_DELAY=0.3`(모델 요청마다 0.3초 지연)으로 다시 띄운 뒤 한 터미널에서 지켜보고, 다른 터미널에서 요청을 보냈습니다.

앞 Step에서 띄운 가짜 서버를 끄고(Ctrl+C), Step 3의 확인이 쌓아 둔 요청 기록을 비운 뒤 다시 띄웁니다. 기록을 비우지 않으면 `summarize_log.py`의 첫 줄이 Step 3의 Firecrawl 요청이 되고 시각도 거기서부터 잽니다.

```bash
rm -f fake.jsonl flight.jsonl
FAKE_DELAY=0.3 uv run --no-project python fake_services.py 53417 fake.jsonl mode.txt
```

```powershell
Remove-Item fake.jsonl, flight.jsonl -ErrorAction SilentlyContinue
$env:FAKE_DELAY = "0.3"
uv run --no-project python fake_services.py 53417 fake.jsonl mode.txt
```

(PowerShell 줄은 실행해 보지 못했습니다. 끝나면 `Remove-Item Env:FAKE_DELAY`.)

```bash
uv run --no-project python watch_db.py fake.db 60
```

`watch_db.py`는 상태가 바뀔 때마다 한 줄씩 찍습니다. 요청을 보낸 뒤 직접 확인한 출력입니다(앞 확인에서와 같은 요청 본문).

```text
  0.00s status=[] task=[] output_rows=0
  0.61s status=[] task=[('in_progress',)] output_rows=0
  0.81s status=[('processing', 'Researching about the destination')] task=[('in_progress',)] output_rows=0
  2.42s status=[('processing', 'Searching for the best flights')] task=[('in_progress',)] output_rows=0
  3.02s status=[('processing', 'Searching for the best hotels')] task=[('in_progress',)] output_rows=0
  4.03s status=[('processing', 'Searching for the best restaurants')] task=[('in_progress',)] output_rows=0
  4.63s status=[('processing', 'Creating the day-by-day itinerary')] task=[('in_progress',)] output_rows=0
  4.84s status=[('processing', 'Optimizing the budget')] task=[('in_progress',)] output_rows=0
  5.24s status=[('processing', 'Adding finishing touches')] task=[('in_progress',)] output_rows=0
  5.44s status=[('processing', 'Adding finishing touches')] task=[('in_progress',)] output_rows=1
  5.64s status=[('completed', 'Plan generated and saved')] task=[('success',)] output_rows=1
```

작업 행이 먼저 `in_progress`가 되고(0.61초), 상태 행이 처음 보이는 것은 0.81초에 이미 `processing`·`Researching about the destination`입니다. 앞의 두 단계 이름(`Initializing travel plan generation`, `Generating plan with TripCraft AI agents`)은 0.2초 사이에 지나가 이 폴링에는 잡히지 않았습니다. 결과 행은 5.44초에 먼저 생기고 0.2초 뒤에 `completed`가 됩니다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/services/plan_service.py:387-399`의 순서). 같은 구성으로 한 번 더 돌린 실행의 가짜 서버 로그 요약입니다(`FAKE_DELAY=0.3`).

```bash
uv run --no-project python summarize_log.py fake.jsonl
```

```text
 1 + 0.0s destination chat  model=google/gemini-2.0-flash-001 messages=2 tools=4 -> tool_calls:search_exa
 2 + 0.3s             exa   {"query": "top attractions in Singapore", "numResults": 10, "contents": {"text": true, "summary": false}}
 3 + 0.3s destination chat  model=google/gemini-2.0-flash-001 messages=4 tools=4 -> text
 4 + 0.7s flight      chat  model=google/gemini-2.0-flash-001 messages=2 tools=1 -> tool_calls:get_flights
 5 + 1.0s flight      chat  model=google/gemini-2.0-flash-001 messages=4 tools=1 -> text
 6 + 1.3s hotel       chat  model=google/gemini-2.0-flash-001 messages=2 tools=2 -> tool_calls:kayak_hotel_url_generator
 7 + 1.6s hotel       chat  model=google/gemini-2.0-flash-001 messages=4 tools=2 -> tool_calls:scrape_website
 8 + 1.9s             fire  /v1/scrape url=https://www.kayak.com/hotels/Singapore/2026-12-01/2026-12-10/2adults/1children?currency=USD
 9 + 1.9s hotel       chat  model=google/gemini-2.0-flash-001 messages=6 tools=2 -> text
10 + 2.2s dining      chat  model=google/gemini-2.0-flash-001 messages=2 tools=4 -> tool_calls:search_exa
11 + 2.5s             exa   {"query": "best restaurants in Singapore", "numResults": 3, "contents": {"text": true, "summary": false}}
12 + 2.5s dining      chat  model=google/gemini-2.0-flash-001 messages=4 tools=4 -> text
13 + 2.9s itinerary   chat  model=google/gemini-2.0-flash-001 messages=2 tools=7 -> text
14 + 3.2s budget      chat  model=google/gemini-2.0-flash-001 messages=2 tools=0 -> text
15 + 3.5s convert     chat  model=google/gemini-2.0-flash-001 messages=2 tools=0 -> text
```

모델 요청이 12건(목적지 2, 항공 2, 호텔 3, 식당 2, 일정 1, 예산 1, 변환 1), Exa가 2건, Firecrawl가 1건이고, 항공편 조회 대역이 한 번 불렸습니다. 이 호출 수는 **가짜 서버가 시킨 순서**의 값입니다. 실제 모델은 도구를 더 부르거나 하나도 안 부를 수 있고, 일정 에이전트는 도구 일곱을 갖고 있지만 가짜 서버가 하나도 시키지 않았습니다. 모델이 한 요청에 담아 보낸 항공편 조회 인자는 `FLIGHT_LOG`에 남았습니다.

```text
{"flight_data": ["FlightData(date='2026-12-01', from_airport=BOM, to_airport=SIN, max_stops=None)"], "trip": "round-trip", "seat": "economy", "passengers": "Passengers((2, 1, 0, 0))", "fetch_mode": "fallback"}
```

(가짜 서버가 시킨 인자입니다. 앞 줄 한 건만 인용합니다. 한 줄이 한 번의 조회입니다.) 이제 저장된 결과와 변환 입력을 봅니다.

```python
# 한 번 돌린 뒤의 로그와 DB를 읽어 세 가지를 본다. 사용: python check_flow.py <가짜 서버 로그 JSONL> <SQLite 파일>
import json, sqlite3, sys
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
conv = next(r for r in rows if r.get("agent") == "convert")
text = next(m["content"] for m in conv["body"]["messages"] if m["role"] == "user")
print("== 변환 에이전트가 받은 입력에 각 에이전트의 글이 들어 있는가")
for name in ["destination", "flight", "hotel", "dining", "itinerary", "budget"]:
    print(f"{name:<12}", f"[canned {name} answer]" in text)

db = sqlite3.connect(sys.argv[2])
out = json.loads(db.execute("select itinerary from trip_plan_output").fetchone()[0])
print("== trip_plan_output.itinerary 바깥 JSON의 키와 값 모양")
for k, v in out.items():
    print(f"{k:<26}", type(v).__name__)
inner = json.loads(out["itinerary"])
print("== 안쪽 itinerary 문자열을 한 번 더 파싱한 키")
print(list(inner))
task_out = json.loads(db.execute("select output_data from plan_tasks").fetchone()[0])
print("== plan_tasks.output_data의 키 / 같은 문자열인가")
print(list(task_out), task_out["travel_plan"] == db.execute("select itinerary from trip_plan_output").fetchone()[0])
```

```bash
uv run --no-project python check_flow.py fake.jsonl fake.db
```

```text
== 변환 에이전트가 받은 입력에 각 에이전트의 글이 들어 있는가
destination  True
flight       True
hotel        True
dining       True
itinerary    True
budget       False
== trip_plan_output.itinerary 바깥 JSON의 키와 값 모양
itinerary                  str
budget_agent_response      str
destination_agent_response str
flight_agent_response      str
hotel_agent_response       str
restaurant_agent_response  str
itinerary_agent_response   str
== 안쪽 itinerary 문자열을 한 번 더 파싱한 키
['day_by_day_plan', 'hotels', 'attractions', 'flights', 'restaurants', 'budget_insights', 'tips']
== plan_tasks.output_data의 키 / 같은 문자열인가
['travel_plan'] True
```

세 가지를 읽습니다. 첫째, 변환 에이전트의 입력에는 예산 에이전트의 글이 없습니다(`budget False`). 그래서 `TravelPlanTeamResponse`의 `budget_insights`는 예산 에이전트의 최적화가 아니라 앞 다섯 글에서 모델이 뽑은 것입니다. 예산 글은 JSON 맨 밖의 `budget_agent_response` 문자열로만 저장됩니다. 둘째, 저장된 JSON은 두 겹입니다. 바깥 객체의 `itinerary`는 객체가 아니라 **JSON 문자열**이고(`str`), 클라이언트는 그래서 두 번 파싱합니다(Step 6). 셋째, 같은 문자열이 `plan_tasks.output_data`에도 한 번 더 저장됩니다. 이 JSON을 만드는 곳은 `plan_service.py:369-384`입니다. 호텔 에이전트의 글은 `hotel_agent_response`로 저장되지만 클라이언트는 읽지 않습니다(`client/app/plan/[id]/page.tsx:263-282`에 이 키가 없음).

### Step 6. 상태 추적과 클라이언트 — 서버는 막히지 않고, 오류 문구는 화면에 닿지 않습니다

**목적.** 계획이 도는 동안 백엔드가 다른 요청에 응답하는지, 클라이언트가 상태를 어떻게 읽고 보여 주는지, 재시도가 DB에 무엇을 남기는지 확인합니다. 클라이언트는 소스로 읽었고 실행하지 않았습니다.

**할 일.** 제출 라우트는 폼 값을 저장하고 백엔드를 부릅니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/api/plan/submit/route.ts:48-76`

```ts
    const savedTripPlan = await prisma.tripPlan.create({
      data: {
        name: tripData.name,
        destination: tripData.destination,
        startingLocation: tripData.startingLocation,
        travelDatesStart: tripData.travelDates.start,
        travelDatesEnd: tripData.travelDates.end || null,
        dateInputType: tripData.dateInputType || "picker",
        duration: tripData.duration || null,
        travelingWith: tripData.travelingWith,
        adults: tripData.adults || 1,
        children: tripData.children || 0,
        ageGroups: tripData.ageGroups || [],
        budget: tripData.budget,
        budgetCurrency: tripData.budgetCurrency || "USD",
        travelStyle: tripData.travelStyle,
        budgetFlexible: tripData.budgetFlexible || false,
        vibes: tripData.vibes || [],
        priorities: tripData.priorities || [],
        interests: tripData.interests || null,
        rooms: tripData.rooms || 1,
        pace: tripData.pace || [3],
        beenThereBefore: tripData.beenThereBefore || null,
        lovedPlaces: tripData.lovedPlaces || null,
        additionalInfo: tripData.additionalInfo || null,
        // userId can be added later when auth is implemented
        userId: null
      }
    });
```

백엔드 호출은 114~120행입니다. 그 응답이 실패(`!backendResponse.ok`)이면 500을 돌려줍니다(122~131행). 이때 방금 만든 `trip_plan` 행은 지우지 않아 남습니다(소스로 확인). 상세 화면은 완료될 때까지 5초마다 읽습니다.

`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/plan/[id]/page.tsx:396-413`

```tsx
    if (!trip) return;

    // Check if we should poll
    const shouldPoll = trip.status !== "completed" && trip.status !== "failed";

    if (shouldPoll) {
      setPolling(true);
      const pollInterval = setInterval(fetchTripDetails, 5000);

      return () => {
        clearInterval(pollInterval);
        setPolling(false);
      };
    } else {
      setPolling(false);
    }
  }, [trip, trip?.status, tripId, fetchTripDetails]);

```

백엔드 상태 문자열이 화면 상태로 바뀌는 곳은 243~254행(`completed`→완료, `processing`→진행 중, `failed`→실패, 그 밖은 `pending`)입니다. 백엔드가 쓰는 `processing`·`completed`·`failed`와 맞습니다. `trip_plan_status`의 `error` 열은 클라이언트 어디서도 읽지 않습니다(`grep`으로 `status.error`·`.error`를 찾아 직접 확인: 인증 화면과 삭제 토스트의 `error`뿐). 즉 백엔드가 `error`에 쓰는 오류 문구는 화면에 닿지 않고, 실패 화면은 "Failed to Generate Trip Plan"이라는 고정 문구와 재시도 버튼뿐입니다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/client/app/plan/[id]/page.tsx:739-781`).

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** **계획이 도는 동안 서버는 다른 요청에 응답합니다.** 항공편 도구(`get_google_flights`)는 동기 함수입니다. 이 함수가 오래 걸리면 비동기 서버가 막힐지 시험했습니다. 대역 함수가 4초 자는 동안(`FLIGHT_DELAY=4`) 0.25초마다 건강 확인을 불렀습니다.

```python
# 0.25초마다 /api/health를 불러 응답 시간을 기록한다. 사용: python probe_health.py <포트> <초>
import sys, time, urllib.request
port, secs = sys.argv[1], float(sys.argv[2]); t0 = time.time(); slow = []; n = 0
while time.time() - t0 < secs:
    a = time.time()
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=30).read()
        dt = time.time() - a
    except Exception as e:
        dt = -1
    n += 1
    if dt > 0.5 or dt < 0:
        slow.append((round(a - t0, 2), round(dt, 2)))
    time.sleep(0.25)
print("calls:", n, "slow(>0.5s) [시작초, 걸린초]:", slow)
```

백엔드를 `FLIGHT_DELAY=4`로 다시 띄웁니다(가짜 서버는 그대로).

```bash
FLIGHT_DELAY=4 uv run --no-project python run_backend.py 53418 53417
```

```powershell
$env:FLIGHT_DELAY = "4"
uv run --no-project python run_backend.py 53418 53417
```

다른 터미널에서 `probe_health.py`를 돌리고, 곧바로 또 다른 터미널에서 요청을 보냅니다(Step 4의 `request.json`).

```bash
uv run --no-project python probe_health.py 53418 14
```

```bash
curl -s -X POST http://127.0.0.1:53418/api/plan/trigger -H "Content-Type: application/json" --data-binary @request.json
```

```powershell
curl.exe -s -X POST http://127.0.0.1:53418/api/plan/trigger -H "Content-Type: application/json" --data-binary '@request.json'
```

(PowerShell 줄은 실행해 보지 못했습니다. 끝나면 `Remove-Item Env:FLIGHT_DELAY`.)

```text
calls: 51 slow(>0.5s) [시작초, 걸린초]: [(1.36, 0.76)]
```

14초 동안 51번 불렀고 0.5초를 넘긴 응답은 한 번(0.76초, 요청을 보낸 직후)뿐이었습니다. 같은 실행의 로그에서 항공편 모델 요청의 간격은 0.26초(도구 호출 지시)에서 4.37초(도구 결과를 받은 두 번째 요청)로 4초 넘게 벌어졌으니 도구는 실제로 4초를 썼습니다. 4초짜리 호출이 서버를 막지 않았으므로, agno가 동기 도구를 별도 실행 흐름에서 돌린다고 읽을 수 있습니다(소스까지는 따라가지 않았습니다). 실제 `fast-flights` 호출이 같다는 보장은 없습니다. 그 호출은 하지 않았습니다.

**재시도.** 실패한 계획을 같은 `trip_plan_id`로 다시 부르면 어떻게 되는지 보려고, 변환 단계를 일부러 실패시킨 뒤(`echo badjson > mode.txt`, PowerShell은 `Set-Content mode.txt badjson -Encoding ascii`) 모드를 되돌리고(`echo ok > mode.txt`, PowerShell은 `Set-Content mode.txt ok -Encoding ascii`) 같은 요청을 다시 보냈습니다. 순서는 이렇습니다. 먼저 `request.json`(`trip-demo-001`)을 한 번 성공시키고, `sed 's/trip-demo-001/trip-demo-002/' request.json > request2.json`으로 만든 요청(`trip-demo-002`)을 `badjson`일 때 한 번, `ok`일 때 한 번 보냅니다. 결과를 읽는 쿼리는 `trip-demo-002`만 고릅니다. 직접 확인한 값입니다.

```python
import sqlite3
c = sqlite3.connect("fake.db")
print(c.execute("select tripPlanId,status,currentStep,error from trip_plan_status where tripPlanId='trip-demo-002'").fetchall())
print(c.execute("select id,trip_plan_id,status,error_message from plan_tasks where trip_plan_id='trip-demo-002'").fetchall())
print(c.execute("select count(*) from trip_plan_output where tripPlanId='trip-demo-002'").fetchall())
```

```text
[('trip-demo-002', 'completed', 'Plan generated and saved', 'Failed to parse response into TravelPlanTeamResponse: Invalid JSON response: Expecting value: line 1 column 1 (char 0)')]
[(2, 'trip-demo-002', 'error', 'Failed to parse response into TravelPlanTeamResponse: Invalid JSON response: Expecting value: line 1 column 1 (char 0)'), (3, 'trip-demo-002', 'success', None)]
[(1,)]
```

세 가지가 보입니다. 같은 계획의 상태 행은 하나이고 그대로 `completed`가 되지만, `error` 열에는 앞 실패의 문구가 **그대로 남습니다**(`update_trip_plan_status`는 `error`를 `None`이 아닐 때만 씁니다: `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/repository/trip_plan_repository.py:38-67`). 작업 행은 요청마다 새로 쌓입니다(번호 1은 앞서 성공시킨 `trip-demo-001`의 것이라 이 계획에는 2·3, 둘). 결과 행은 하나입니다. 완료 때 `delete_trip_plan_outputs`가 먼저 지우기 때문이고(`plan_service.py:366-367`), Prisma 스키마의 `trip_plan_output.tripPlanId @unique`와도 맞습니다. 클라이언트가 `error`를 읽지 않으므로 이 남은 문구는 화면에는 보이지 않습니다.

### Step 7. 실패와 통계 — 모델이 죽어도 `arun`은 예외를 던지지 않습니다

**목적.** 모델 호출이 실패하는 세 가지 경우에 앱이 어떻게 끝나는지, 그리고 agno가 보내려는 통계가 무엇인지 확인합니다.

**할 일.** 앱이 모델 응답을 쓰는 곳은 서비스의 `.messages[-1].content` 읽기(Step 5의 발췌)와 `router/plan.py`의 `except`입니다. 모델이 실패했을 때 그 읽기가 무엇을 받는지, 실패가 DB에 어떤 문구로 남는지, agno가 무엇을 통계로 보내려 하는지를 아래에서 봅니다.

![Step 7까지의 구성](diagrams/step7.svg)

**확인.** 먼저 `agent.arun()`이 모델 실패를 어떻게 다루는지 한 에이전트로 봅니다(예산 에이전트: `retries=0`). 가짜 서버를 `http500` 모드로 둔 채 돌립니다.

```python
# 모델 서버가 오류를 돌려줄 때 agent.arun()이 무엇을 돌려주는지 본다. 사용: python probe_fail.py <가짜 서버 포트>
import asyncio, sys, time
import config.llm as llm
llm.model.base_url = f"http://127.0.0.1:{sys.argv[1]}/api/v1"
from agents.budget import budget_agent

async def main():
    t = time.time()
    r = await budget_agent.arun("hello budget")
    print("걸린 시간:", round(time.time() - t, 1), "초")
    print("type:", type(r).__name__, "| status:", r.status, "| content:", repr(r.content)[:60])
    print("roles:", [m.role for m in r.messages], "| messages[-1].content:", repr(r.messages[-1].content))

asyncio.run(main())
```

```bash
echo http500 > mode.txt
uv run --no-project python probe_fail.py 53417
echo ok > mode.txt
```

```powershell
Set-Content mode.txt http500 -Encoding ascii
uv run --no-project python probe_fail.py 53417
Set-Content mode.txt ok -Encoding ascii
```

(PowerShell 5.1의 `>`는 파일을 UTF-16으로 씁니다. 이 문서의 `fake_services.py`는 UTF-16도 읽도록 되어 있어, UTF-16으로 쓴 `badjson`이 먹는 것을 직접 확인했습니다. PowerShell 줄은 실행해 보지 못했습니다.)

```text
ERROR   API status error from OpenAI API: Error code: 500 - {'error': {'message': 'fake server error', 'code': 500}}
ERROR   Error in Agent run: fake server error
걸린 시간: 3.3 초
type: RunOutput | status: RunStatus.error | content: 'fake server error'
roles: ['system', 'user'] | messages[-1].content: 'hello budget'
```

(두 번째 줄 앞의 `OpenAI API`는 agno의 OpenRouter 클래스가 OpenAI 호환 클라이언트를 쓰기 때문입니다.) `arun`은 예외를 던지지 않고 `status`가 오류인 `RunOutput`을 돌려줍니다. 그런데 앱은 `.messages[-1].content`를 읽습니다. 이 목록의 마지막 메시지는 **에이전트가 받은 사용자 질문**(`user`)이라 "답"으로 질문이 들어갑니다. 키가 없을 때도 같습니다(`env -u OPENROUTER_API_KEY`로 돌리면 0.0초에 `content: 'OPENROUTER_API_KEY not set. …'`와 같은 마지막 메시지). 서비스 전체에서 이것이 어떻게 이어지는지 세 경우로 돌렸습니다. 모두 같은 요청 본문입니다.

| 경우 | 설정 | 걸린 시간 | 끝난 상태 | `trip_plan_status.error` |
|---|---|---|---|---|
| 변환 에이전트가 JSON이 아닌 글을 돌려줌 | `echo badjson > mode.txt` | 약 4초(`startedAt`~`completedAt` 3.78초) | `failed`, 단계 `Adding finishing touches` | `Failed to parse response into TravelPlanTeamResponse: Invalid JSON response: Expecting value: line 1 column 1 (char 0)` |
| 모델 서버가 모든 요청에 500 | `echo http500 > mode.txt` | 약 90초(500 응답 63건, `FAKE_DELAY` 없이) | `failed`, 같은 단계 | 같은 문구 |
| `OPENROUTER_API_KEY` 없음 | 키를 빼고 서버를 띄움 | 약 65초(`Model authentication error` 21줄) | `failed`, 같은 단계 | 같은 문구 |

(모델 요청마다 `FAKE_DELAY`를 주면 63건에 곱해져 그만큼 늘어납니다(0.3초면 약 19초). 둘째·셋째 줄의 걸린 시간은 요청을 보낸 뒤 상태가 `failed`가 될 때까지 폴링한 값이고, 셋째 줄의 서비스 로그 `Total time taken`은 62.21초였습니다. 500 응답 63건은 목적지·항공·호텔·식당이 각 12건, 일정 9건, 예산·변환이 각 3건으로 에이전트의 `retries`(3·3·3·3·2·0·0)에 1을 더한 실행 횟수에, 한 번의 실행이 모델 서버에 요청을 세 번(처음과 재시도 둘) 보내는 것을 곱한 값과 맞습니다. 예산 에이전트 단독 실험의 3건이 근거입니다.) 세 경우 모두 오류 문구는 **JSON 오류**입니다. 앞 에이전트들의 실패는 예외가 아니라 질문이 답으로 흘러가서, 모델이 죽었다는 사실은 로그의 `ERROR` 줄에만 남고 DB와 화면에는 "JSON 변환 실패"로만 보입니다. 같은 상황에서 변환 에이전트만 성공하는 경우(예: 한 에이전트에만 일시적 429가 난 경우)에는 그 에이전트의 "답"이 프롬프트 본문이 되어 계획 안으로 들어갈 것입니다. 이 경우는 만들어 보지 않았습니다. 실패한 쪽에서는 `500` 실행의 변환 입력이 `## Destination Attractions:` 아래에 목적지 에이전트가 받은 프롬프트 전체를 담은 것을 가짜 서버 로그에서 직접 봤습니다.

실패한 요청의 뒷정리도 봅니다. 위 세 경우에서 상태·작업 행은 `failed`·`error`가 되고 DB에 남지만, 에이전트가 이미 얻은 결과(앞 에이전트들의 글)는 저장되지 않아 재시도하면 처음부터 모두 다시 돕니다. 그리고 `generate_plan_with_tracking`이 오류를 기록한 뒤 `raise`를 하므로 백그라운드 작업의 예외를 아무도 받지 않아 서버 로그에 `Task exception was never retrieved`가 찍힙니다(직접 확인, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/router/plan.py:58-65`).

**agno 통계.** 에이전트마다 `telemetry=False`가 없고(`Team`에만 있음, `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/agents/team.py:320`) 이 `Team`은 돌지 않으므로 통계는 에이전트 쪽만 문제입니다. agno의 익명 통계는 Day 047 Step 5가 3.0.10 기준으로 다뤘습니다(`AGNO_TELEMETRY=false`가 에이전트 쪽 전송을 끔). 이 앱의 agno 3.1.2에서 한 요청이 보내려는 것을 보려고 `run_backend.py`의 `TELEMETRY_SPY`로 전송 함수를 가로채 파일에 기록하게 하고(네트워크로 나가지 않음), `AGNO_TELEMETRY`를 끈 채 한 번, 켜 둔 채 한 번 돌렸습니다.

```bash
AGNO_TELEMETRY=false TELEMETRY_SPY=spy-off.jsonl uv run --no-project python run_backend.py 53418 53417   # 한 요청 뒤 spy-off.jsonl이 없다
unset AGNO_TELEMETRY; TELEMETRY_SPY=spy-on.jsonl uv run --no-project python run_backend.py 53418 53417    # 한 요청 뒤 일곱 줄
```

```powershell
$env:AGNO_TELEMETRY = "false"; $env:TELEMETRY_SPY = "spy-off.jsonl"
uv run --no-project python run_backend.py 53418 53417
Remove-Item Env:AGNO_TELEMETRY; $env:TELEMETRY_SPY = "spy-on.jsonl"
uv run --no-project python run_backend.py 53418 53417
```

(두 줄 사이에 서버를 끄고 요청을 한 번씩 보냅니다.)

(PowerShell 줄은 실행해 보지 못했습니다.) 끈 쪽은 파일이 만들어지지 않았고(0건), 켠 쪽은 한 요청에 일곱 건(에이전트 여섯과 변환 에이전트)이었습니다. 한 건의 내용은 이렇습니다(직접 확인).

```json
{"session_id": "…", "run_id": "…", "data": {"agent_id": "destination-explorer", "db_type": null, "model_provider": "OpenRouter", "model_name": "OpenRouter", "model_id": "google/gemini-2.0-flash-001", "has_tools": true, "has_memory": false, "has_knowledge": false, "has_team": false, …}, "sdk_version": "3.1.2", "type": "agent"}
```

프롬프트나 응답 본문은 없고 에이전트 이름·모델 ID·기능 여부·SDK 버전입니다. 변환 에이전트는 호출마다 무작위 이름(`bold-tesla-88e2f64d` 같은)으로 만들어져 통계에서도 매번 다른 에이전트로 보입니다. 이 문서의 확인에는 모두 통계를 껐습니다.

**끝내기.** 띄운 서버를 모두 끄고 포트가 비었는지 봅니다. 앱 폴더에 둔 확인용 파일(`shim.py`, `fake_services.py`, `run_backend.py`, `prep_db.py`, `check_*.py`, `watch_db.py`, `summarize_log.py`, `probe_*.py`, `request.json`, `fake.db`, `*.jsonl`, `mode.txt`)을 지웁니다. `uv sync`가 고쳐 쓴 `uv.lock`은 `git checkout -- uv.lock`으로 되돌립니다. 포트가 비었는지는 `netstat -ano | grep :53418`로 봅니다.

## 요청 한 건이 흐르는 과정

폼 제출에서 결과 화면까지를 스물한 장으로, 실패와 재시도를 다섯 장으로 나눠 따라갑니다. 메시지는 모두 정확히 한 그림에, 코드의 순서대로 있습니다. 장이 많은 까닭은 sequence 그림이 메시지 하나에 높이가 고정으로 붙어, 메시지가 여덟아홉 개를 넘으면 세로 1,000px를 넘기 때문입니다(7개인 5단계가 879px, 한 그림에 6~10개를 넣었을 때 1,040~1,116px를 직접 쟀습니다). 클라이언트의 메시지는 소스로 읽은 것이고, 백엔드·에이전트·도구·DB의 메시지는 가짜 서버로 돌려 본 것입니다. 첫 장은 폼 제출에서 DB 저장까지입니다.

![1단계: 폼 제출과 저장](diagrams/sequence.svg)

사용자가 폼을 제출하면 `plan/page.tsx`가 `/api/plan/submit`로 폼 값을 POST하고, 라우트가 `trip_plan` 행을 만듭니다(`userId`는 `null`). 둘째 장은 백엔드 호출입니다.

![2단계: 백엔드 호출](diagrams/extra-trigger.svg)

라우트가 `/api/plan/trigger`로 요청을 보내면 백엔드가 작업 행(`queued`)을 만들고 그 id를 돌려받습니다. 셋째 장은 응답과 백그라운드 작업 시작입니다.

![3단계: 응답과 작업 시작](diagrams/extra-accept.svg)

백엔드가 `asyncio.create_task`로 작업을 띄운 뒤 곧바로 200을 돌려주고, 라우트가 이를 페이지에 넘기면 1.5초 뒤 화면이 `/plan/{id}`로 넘어갑니다. 이 순간부터 에이전트는 응답과 무관하게 돕니다. 넷째 장은 작업의 첫 두 호출입니다.

![4단계: 작업 시작](diagrams/extra-start.svg)

작업이 `in_progress`로 바꾸고 계획 서비스를 부릅니다(응답이 나간 뒤에 돕니다). 다섯째 장은 서비스의 준비입니다.

![5단계: 상태 행 만들기](diagrams/extra-record.svg)

상태 행을 읽고(없음), `pending`으로 만들고, `processing`으로 바꾸고, 폼을 마크다운으로 바꾸고, 단계 이름을 두 번 바꿉니다(마지막이 목적지 조사). 여섯째 장은 목적지 에이전트의 첫 모델 요청입니다.

![6단계: 목적지 에이전트 시작](diagrams/extra-destination.svg)

서비스가 에이전트를 부르고, 에이전트가 도구 네 개를 알려 주며 모델에 묻고, 모델이 `search_exa`를 지목합니다(가짜 서버가 시킨 값). 일곱째 장은 Exa 검색입니다.

![7단계: Exa 검색과 목적지 글](diagrams/extra-search.svg)

에이전트가 Exa에 `numResults: 10`으로 검색합니다. 모델이 정한 건수는 3이었는데 `ExaTools(num_results=10)`이 덮어썼습니다(가짜 서버 로그로 직접 확인). 결과를 모델에 돌려주고 글을 받아 서비스에 넘기며, 서비스가 단계 이름을 항공편으로 바꿉니다. 여덟째 장은 항공편 에이전트의 시작입니다.

![8단계: 항공편 에이전트](diagrams/extra-flight.svg)

항공편 에이전트가 `get_flights`를 지목받습니다. 아홉째 장은 도구 안입니다.

![9단계: 구글 항공편 조회](diagrams/extra-fetch.svg)

도구가 구글 항공편 주소를 가져오고, 200이 아니거나 200이어도 항공편을 읽지 못하면(조건 분기, 소스로 읽은 것이고 이 문서는 돌리지 않았습니다) `try.playwright.tech`에 코드를 보냅니다. 이 조회가 이 문서에서는 인자를 기록하는 대역이었습니다. 열째 장은 항공편 글입니다.

![10단계: 항공편 글과 호텔로](diagrams/extra-fallback.svg)

도구 결과(또는 예외일 때의 빈 목록)가 모델에 돌아가 글이 되고, 서비스가 단계를 호텔로 바꿉니다. 열한째 장은 호텔 에이전트의 URL 만들기입니다.

![11단계: 호텔 URL](diagrams/extra-hotel.svg)

모델이 URL 도구를 먼저 지목하고, 에이전트가 주소 문자열을 만들어 돌려주고, 모델이 그 주소로 `scrape_website`를 지목합니다. 열두째 장은 스크랩입니다.

![12단계: 스크랩과 호텔 글](diagrams/extra-scrape.svg)

Firecrawl가 마크다운을 돌려주고 모델이 호텔 글을 쓰며, 서비스가 단계를 식당으로 바꿉니다. 열셋째 장은 식당 에이전트입니다.

![13단계: 식당 에이전트](diagrams/extra-dining.svg)

식당 에이전트가 `search_exa`를 지목받습니다. 열넷째 장은 식당의 Exa 검색입니다.

![14단계: 식당 검색](diagrams/extra-dining-search.svg)

`ExaTools()`는 건수를 정하지 않아 모델이 정한 3건(`numResults: 3`)으로 나갑니다. 열다섯째 장은 일정 에이전트입니다.

![15단계: 일정 에이전트](diagrams/extra-itinerary.svg)

식당 글이 서비스에 돌아오고, 서비스가 단계를 일정으로 바꾸고, 앞 네 글을 프롬프트에 붙여 일정 에이전트를 부릅니다. 일정 에이전트는 도구 일곱을 알려 주지만 가짜 서버는 도구를 시키지 않아 모델이 바로 글을 돌려줍니다. 열여섯째 장은 예산입니다.

![16단계: 예산 에이전트](diagrams/extra-budget.svg)

일정 글이 서비스로 돌아오고, 서비스가 단계를 예산으로 바꾸고 앞 다섯 글을 붙여 예산 에이전트를 부릅니다(도구 없음). 예산 글이 돌아오면 단계가 `Adding finishing touches`로 바뀝니다. 열일곱째 장은 변환입니다.

![17단계: JSON 변환](diagrams/extra-convert.svg)

예산 글은 `budget_response`에만 담기고, 서비스는 앞 다섯 글만 변환 에이전트에 넘깁니다. 변환 에이전트가 스키마와 글을 모델에 보내 JSON을 받고, 파싱이 통과한 JSON 문자열을 서비스에 돌려줍니다. 열여덟째 장은 저장입니다.

![18단계: 결과 저장](diagrams/extra-save.svg)

서비스가 같은 계획의 옛 결과를 지우고, 새 결과를 넣고, 상태를 `completed`로 바꿉니다. 열아홉째 장은 작업 마무리입니다.

![19단계: 작업 마무리](diagrams/extra-return.svg)

서비스가 `final_response`를 백그라운드 작업에 돌려주고, 작업이 작업 행을 `success`로 바꿉니다. 이제 클라이언트가 읽을 차례입니다. 이 폴링은 위 모든 장과 **동시에** 5초마다 돕니다. 진행 중에 읽으면 이렇습니다.

![20단계: 진행 중 조회](diagrams/extra-poll.svg)

라우트가 DB에서 계획과 상태를 읽어 돌려주면(결과는 아직 없음) 화면이 `processing`을 진행 중으로 바꾸고 현재 단계 이름을 보여 줍니다. 완료된 뒤의 마지막 조회입니다.

![21단계: 완료 화면](diagrams/extra-screen.svg)

결과가 있으면 화면이 JSON을 두 번 파싱해(바깥 문자열, 안쪽 `itinerary`) 일정 화면을 그리고 폴링을 멈춥니다. 실패 쪽의 두 장입니다. 변환이 실패하는 경우입니다.

![실패 1: 변환 오류](diagrams/extra-failure.svg)

변환 에이전트가 JSON이 아닌 글을 받고 `ValueError`를 올립니다. 이어지는 장입니다.

![실패 2: 상태 기록과 작업 오류](diagrams/extra-failure-end.svg)

서비스가 상태를 `failed`로 쓰고 예외를 다시 던지고, 백그라운드 작업이 작업 행을 `error`로 쓴 뒤 다시 던져 아무도 받지 않는 예외가 로그에 남습니다. 사용자가 실패 화면의 재시도를 누르면 이렇게 됩니다.

![재시도 1: 저장된 폼 값 읽기와 상태 행 되돌리기](diagrams/extra-retry.svg)

라우트가 DB에서 계획과 상태를 읽어(저장된 폼 값이 여기서 옵니다) 상태 행을 `processing`·`Restarting trip plan generation...`으로 바꿉니다. 이어서 백엔드를 다시 부릅니다.

![재시도 2: 백엔드 재호출](diagrams/extra-retry-trigger.svg)

저장된 폼 값으로 `/api/plan/trigger`를 다시 부르면 작업 행이 새로 생기고 id가 돌아옵니다. 응답과 화면 쪽은 이렇습니다.

![재시도 3: 응답과 폴링 재개](diagrams/extra-retry-end.svg)

백엔드가 작업을 띄우고 200을 돌려주면 재시도 라우트가 `{success, message, response}`로 감싸 페이지에 넘기고, 페이지는 `fetchTripDetails()`로 한 번 읽은 뒤 `setPolling(true)`로 5초 폴링을 다시 켭니다. 이 `GET /api/plans/{id}`가 DB를 읽고 응답을 돌려받는 메시지는 위 20단계(`extra-poll`)의 그림과 같아 이 그림에는 다시 그리지 않았습니다. 작업이 시작된 뒤는 위 4단계부터와 같습니다.

## 실행 체크리스트

- [ ] `uv sync` 뒤 `uv lock --check`가 낡은 잠금을 알려 주는 것과, `google-genai`·`firecrawl-py`를 올려도 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:1`이 막히는 까닭을 읽었다
- [ ] `shim.py`를 앞에 import하면 가짜 키로 `api.app`이 import되는 것을 봤고, `uv run`을 그냥 쓰면 올린 패키지가 되돌려지는 것을 알았다
- [ ] `check_agents.py`로 에이전트 여섯의 모델·재시도·도구와 `Team`이 호출되지 않는 것을 확인했다
- [ ] Google 폐기 표에서 `gemini-2.0-flash-001`의 종료일 2026-06-01을 읽었고, OpenRouter 목록에 그 ID가 없는 것을 봤다
- [ ] `check_tools.py`로 Kayak URL(인코딩 없음)과 항공편 예외 삼킴(`[]`), 스크랩 대역을 봤다
- [ ] `run_backend.py`로 루프백에만 서버를 띄웠고 `DATABASE_URL`이 비거나 닿지 않으면 서버가 못 뜨는 것을 봤다
- [ ] `POST /api/plan/trigger`가 0.013초에 200을 돌려주고 에이전트는 그 뒤에 도는 것을 봤다
- [ ] 가짜 서버로 끝까지 돌려 모델 요청 12건·Exa 2건·Firecrawl 1건과 상태 단계 아홉을 봤다
- [ ] 변환 입력에 예산 글이 없고 저장된 `itinerary`가 JSON 문자열인 것을 `check_flow.py`로 봤다
- [ ] 4초 걸리는 도구 호출 동안 건강 확인이 계속 응답하는 것을 봤다
- [ ] 변환 실패 뒤 같은 `trip_plan_id`를 다시 돌리면 상태 행의 `error`가 남은 채 `completed`가 되는 것을 봤다
- [ ] 모델 500·키 없음에서 `arun`이 예외 없이 질문을 "답"으로 돌려주고 최종 오류가 JSON 오류로 나오는 것을 봤다
- [ ] `AGNO_TELEMETRY=false`에서 통계 0건, 끄지 않으면 한 요청에 일곱 건인 것을 봤다
- [ ] 띄운 서버를 모두 끄고 53417·53418 포트가 비었으며, 앱 폴더에 둔 확인용 파일을 지우고 `uv.lock`을 되돌렸다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `uv lock --check`가 `needs to be updated, but --locked was provided` | `uv.lock`이 `agno` 1.5.6에 묶였고 `pyproject.toml`은 `agno>=2.3.24`(직접 확인). uv 버전에 따라 문구가 `--locked`가 아니라 `--check`로 나옵니다 | `uv sync`가 잠금을 고쳐 씁니다. 끝나면 `git checkout -- uv.lock`으로 되돌릴 수 있습니다 |
| `TypeError: Agent.__init__() got an unexpected keyword argument 'add_datetime_to_context'` | `uv sync --frozen`이 `agno` 1.5.6을 설치했다. 이 이름은 agno 2.x 이후의 것(직접 확인) | `--frozen`을 쓰지 않는다 |
| ``ImportError: `google-genai` not installed or not at the latest version`` | agno 3.1.2의 Gemini 클래스가 `FileSearch` 등을 요구하는데 잠금의 `google-genai` 1.18.0에는 없다. `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/config/llm.py:1`이 쓰지도 않는 `Gemini`를 import한다(직접 확인) | `uv pip install -U google-genai`(직접 확인: 2.29.0에서 import됨) |
| ``ImportError: `firecrawl-py` not installed`` (`agno/tools/firecrawl.py`) | agno는 `firecrawl.types`를 요구하는데 2.7.1에는 없다(직접 확인) | `uv pip install -U "firecrawl-py>=3"` |
| `ImportError: cannot import name 'ScrapeOptions' from 'firecrawl'` (`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:1`) | `firecrawl-py` 3.x 이상은 옛 이름이 `V1ScrapeOptions`·`V1FirecrawlApp`이다. 어느 버전도 agno와 앱을 함께 만족하지 않는다(직접 확인) | 별칭 `shim.py`를 앞에 import하거나 복사본의 `scrape.py:1`을 고친다 |
| `ValueError: No API key provided` 또는 `API key must be provided as an argument or in EXA_API_KEY` | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/scrape.py:7`과 `ExaTools`가 import 때 키를 요구한다(직접 확인) | 두 키를 셸이나 `.env`에 둔다 |
| `uv run python …` 뒤 갑자기 `ImportError`가 다시 난다 | `uv run`이 환경을 잠금에 맞춰 되돌려 올린 패키지를 지웠다(직접 확인: 25개) | `uv run --no-project`를 쓴다 |
| `sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL` 뒤 `Application startup failed` | `DATABASE_URL`이 비어 있다(기본값 `""`). 시작 때 DB 풀을 만들지 못하면 서버가 뜨지 않는다(직접 확인) | 값을 넣는다 |
| `ConnectionRefusedError` 뒤 `Application startup failed` | DB가 그 주소에서 듣고 있지 않다(직접 확인) | DB를 띄운다 |
| 서버는 떴는데 `OPENROUTER_API_KEY not set`이 로그에 반복되고 계획이 1분 남짓 뒤 `failed` | 키가 없으면 `arun`이 예외 없이 오류 상태로 끝나고, 재시도(에이전트마다 최대 3번)를 거쳐 마지막 변환에서 JSON 오류로 보인다(직접 확인) | 키를 넣는다. 오류 원인은 DB 문구가 아니라 로그의 `ERROR` 줄에 있다 |
| 계획이 `failed`인데 `error`가 `Invalid JSON response`뿐 | 모델 실패가 앞 에이전트에서 이미 났는데 질문이 답으로 흘러 마지막에야 JSON 오류로 보인다(직접 확인) | 서버 로그의 `API status error`·`Model authentication error` 줄을 먼저 본다 |
| 모델 요청이 404 또는 실패 | `google/gemini-2.0-flash-001`은 Google 폐기 문서에 종료일 2026-06-01로 있고 OpenRouter 목록에 없다. 실제 오류 본문은 확인하지 못함 | `config/llm.py` 8·11행의 ID를 현재 모델(예: `google/gemini-3.6-flash`)로 바꾼다 |
| 항공편 결과가 비었는데 로그에 `Error getting flights from Google Flights: …` 한 줄뿐 | 조회 실패를 `except Exception`이 삼키고 `[]`을 돌려준다(`advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/tools/google_flight.py:50-52`, 직접 확인: 대역 예외로) | 로그를 본다 |
| `Task exception was never retrieved`가 서버 로그에 | 실패 뒤 `generate_plan_with_tracking`이 다시 `raise`해 받는 곳이 없다(직접 확인) | 상태는 이미 `failed`로 기록된다. 로그 소음이다 |
| 재시도해 `completed`가 됐는데 상태 행에 옛 `error` 문구가 남음 | 상태 갱신이 `error`를 `None`이 아닐 때만 쓴다(직접 확인) | 클라이언트는 이 열을 읽지 않는다 |
| `docker build`가 `app/`·`routers/`·`api.py`·`server.py`를 찾지 못함 | `Dockerfile`이 없는 경로를 복사한다(직접 확인: `없음`). 이 문서는 빌드를 실행하지 않았다 | 폴더 이름을 맞추고 `tools/`·`repository/`를 복사 목록에 더해야 합니다 |
| `client/`의 제출이 500 `Failed to save trip plan to database`, 화면에 `Failed to submit trip plan`인데 `trip_plan` 행은 생김. 서버 로그에 `Failed to parse URL from undefined/api/plan/trigger` | `BACKEND_API_URL`이 없으면 주소가 `undefined/api/plan/trigger`(상대 주소)가 되고, Node의 `fetch`는 요청을 보내지 않고 `TypeError`를 던져 `!backendResponse.ok` 분기가 아니라 바깥 `catch`로 간다. 행은 그 앞에서 이미 저장됐다. `.env.example`에도 없다(Node 24에서 `fetch("undefined/api/plan/trigger")`로 직접 확인, Next.js 서버는 실행하지 않음) | `.env.local`에 백엔드 주소를 넣는다 |
| 출력에 한글이 깨지거나 `UnicodeEncodeError` | 한국어 Windows의 기본 인코딩(`cp949`) | `PYTHONIOENCODING=utf-8` |

## 더 해보기

- 모델 ID를 현재 것으로 바꿔 보세요. 복사본의 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/config/llm.py:8`과 `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/backend/config/llm.py:11`의 `google/gemini-2.0-flash-001`을 `google/gemini-3.6-flash`로 바꾸고 `OPENROUTER_API_KEY`에 실제 키를 넣어 한 번 돌려 문서의 비용 어림($0.1 이하)이 맞는지 OpenRouter 사용량 화면과 견주세요. 가짜 서버로는 12건이 모두 새 ID로 나가는 것까지 봤습니다(직접 확인). 실제 키로는 하지 못했습니다.
- 예산 글이 결과에 들어가게 해 보세요. 복사본의 `backend/services/plan_service.py`에서 예산 응답을 `last_response_content`에 이어 붙인 뒤 `convert_to_model`을 부르면 변환 입력에 `## Budget` 같은 절이 생깁니다. 이 문서는 고쳐 보지 않았습니다. 고친 뒤 `check_flow.py`의 `budget` 줄이 `True`가 되는지 보면 됩니다.
- 실패가 오류로 보이게 해 보세요. 복사본의 `generate_travel_plan`에서 각 `arun` 결과의 `status`를 검사해 오류 상태면 `RuntimeError(content)`를 올리면 Step 7의 세 경우가 JSON 오류 대신 실제 원인(`fake server error`)으로 끝나는지 `probe_fail.py`와 `badjson` 실행으로 견줄 수 있습니다. 이 문서는 고쳐 보지 않았습니다.

## 다음 날 예고

[Day 125 · 🔍 AI SEO Audit Team](../day125-ai-seo-audit-team/README.md) — 오늘은 agno 에이전트 일곱을 서비스 함수가 차례로 불렀다면 내일은 Google ADK의 `SequentialAgent`가 순서를 맡습니다. 웹 페이지 URL 하나를 받아 페이지 감사, 검색 경쟁 분석, 개선안 작성을 맡는 `LlmAgent` 셋을 이어 돌리고, Gemini 2.5 Flash와 Gemini 내장 `google_search`, MCP로 붙는 Firecrawl 도구를 씁니다(원본 앱 소스 기준). 파이썬 파일 하나(`agent.py`)로 이루어진 앱입니다.
