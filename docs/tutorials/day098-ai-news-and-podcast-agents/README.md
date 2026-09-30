# Day 098 · 🎧 AI Social Media News and Podcast Agent

> 볼륨 7 🚀 Advanced AI Agents · 난이도 ★★★ · 예상 소요 100분(그림이 스물일곱 장이고 명령이 스물두 개인 데다 2.3GB 설치가 있어 읽고 돌려 보는 시간이 깁니다) · API 비용 대략 이 문서의 실습은 무료(키·Redis·Chromium·네트워크 없이 가짜 입력으로 진행). 앱을 키로 실제 돌리면 기사 분석(gpt-4o)·임베딩·검색과 대본(gpt-4o-mini)·배너(gpt-4o + DALL·E 3)·음성이 모두 과금되고, 팟캐스트 한 편은 TTS 엔진에 따라 로컬 Kokoro 무료부터 ElevenLabs의 수 달러까지 벌어지며 기사 분석은 기사 하나에 최대 수 센트로 어림합니다(공개 요금표를 오늘 확인하지 못한 대략치, 키가 없어 실제 과금도 확인하지 못함) · 원본 앱: `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents`

## 오늘 만들 것

이 앱은 폴더 이름이 `ai_news_and_podcast_agents`이고 스스로는 "Beifong"이라 부릅니다. 내가 고른 RSS 뉴스 소스를 계속 모아 기사로 쌓고, AI가 요약·분류·임베딩까지 해 둔 그 기사와 웹 검색을 재료로 두 진행자(ALEX·MORGAN)의 팟캐스트 대본·배너·음성을 만들어 웹 UI에서 재생합니다. 백엔드는 FastAPI(`beifong/`)이고 UI는 미리 빌드된 React(`web/build`)를 백엔드가 그대로 서빙하며, 저장은 SQLite 파일과 FAISS 색인입니다. 팟캐스트를 만드는 길은 둘입니다 — 스케줄러가 처리기 스크립트를 서브프로세스로 돌리는 **예약 경로**, 그리고 Celery와 Redis 위에서 agno 에이전트가 사람의 확인을 받아 가며 진행하는 **Studio 채팅 경로**. 이 문서는 예약 경로 하나, **뉴스 소스 → 기사 → 임베딩 색인 → 대본 → 오디오 → 재생**만 따라가고, Studio는 프로세스와 저장소를 그림 하나로 정리했으며 소셜 스크래퍼·Slack은 파일 단위로 표에만 적었습니다(소스로 확인). 이 길을 고른 까닭은 단계 사이의 경계가 SQLite 표·FAISS·파일이라서, RSS·기사 사이트·OpenAI·Chromium·TTS 같은 바깥 호출 자리만 가짜로 바꿔 끼우면 키 없이도 각 단계를 실제 코드로 돌려 볼 수 있기 때문입니다. 그렇게 돌려 보니 소스만 읽어서는 보이지 않던 것이 여럿 드러났습니다. `&` 하나가 든 피드가 통째로 버려지고, RSS 날짜는 SQLite가 읽지 못해 날짜 필터에서 빠지며, "유사도 85%" 필터가 코사인 0.75짜리도 통과시키고, 설정 화면의 세 필드가 생성기에 전달되지 않으며, Windows에서는 배치가 만든 팟캐스트의 오디오 주소가 재생 파일이 아닌 화면을 가리킵니다(모두 직접 확인, 각 Step). 이 문서는 API 키를 쓰지 않았고 외부로 요청을 보내지 않았습니다. 아래는 완성된 아키텍처, 예약 경로입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| uv, Python 3.11 또는 3.12 | 가상환경과 패키지 252개 설치. Python 3.13 이상은 휠이 없는 패키지가 있어 설치가 막힘(문제 해결) | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| 디스크 약 3GB | 가상환경이 2.3GB — requirements에 torch·spacy·kokoro까지 들어 있음(직접 확인) | 별도 설치 없음 |
| OpenAI API 키 (실제로 돌릴 때만) | 기사 분석·임베딩·검색·대본·배너·openai TTS 엔진 모두 `OPENAI_API_KEY` | https://platform.openai.com/ 가입 후 발급 |
| ElevenLabs API 키 (선택) | UI 설정 화면의 기본 TTS 엔진. 환경변수 이름이 철자 그대로 `ELEVENSLAB_API_KEY`(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/tts_engine_selector.py:48`) | https://elevenlabs.io/ |
| Redis (Studio 채팅에만) | Celery 브로커와 세션 락. 예약 경로에는 필요 없음 | 로컬 설치 또는 Docker — 이 문서는 설치하지 않음 |
| Chromium (실제 스크랩에만) | Playwright가 기사 페이지를 여는 브라우저 | `python -m playwright install` — 이 문서는 실행하지 않음 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| FastAPI 백엔드 | 시작 시 폴더·SQLite 초기화, 라우터 7개(엔드포인트 65개), 오디오 Range 스트리밍, `web/build` 서빙 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/main.py:22-36`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/main.py:50-56`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/main.py:59-98` |
| 저장소 초기화 | SQLite 파일별 표 정의(`sources`·`feed_entries`·`crawled_articles`·`podcasts`·`tasks` 등)와 경로 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/db_init.py:347-365`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/db/config.py:7-18` |
| 소스·기사·팟캐스트·작업 API | 라우터 → 서비스 → SQLite로 이어지는 CRUD | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/source_service.py:158-181`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/article_service.py:11-102`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/podcast_service.py:97-179`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/task_service.py:75-118` |
| 스케줄러 | `tasks` 표에서 지금 돌 작업을 찾아 `command`를 서브프로세스로 실행 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/scheduler.py:96-103`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/scheduler.py:132-149` |
| 처리기 1~5 | 피드 → 항목 → 기사 → AI 분석 → 임베딩 → FAISS 색인 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/feed_processor.py:15-75`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/url_processor.py:7-45`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/ai_analysis_processor.py:28-118`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/embedding_processor.py:128-165`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/faiss_indexing_processor.py:165-229` |
| 팟캐스트 생성기(처리기 6) | 검색 → 스크랩 → 대본 → 배너 → 오디오 → 저장을 함수 하나가 순서대로 부름 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/podcast_generator_processor.py:36-190` |
| 파이프라인 에이전트 4개 | 검색·스크랩·대본·배너, 각각 agno `Agent`(배너만 gpt-4o, 나머지 gpt-4o-mini) | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/search_agent.py:63-90`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/scrape_agent.py:127-136`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/script_agent.py:90-120`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/image_generate_agent.py:58-81` |
| 검색 도구 7개 | Google News·DuckDuckGo·Wikipedia·Jikan(애니)·`embedding_search`·소셜 DB 둘 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/search_agent.py:72-80`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/embedding_search.py:94-163` |
| 브라우저 크롤러 | Playwright Chromium으로 페이지를 열고 newspaper4k로 본문을 뽑음 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/browser_crawler.py:19-58`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/browser_crawler.py:119-137` |
| TTS 선택기와 엔진 3개 | `elevenlabs`·`kokoro`(로컬)·`openai` 중 하나로 WAV를 조립 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/tts_engine_selector.py:14-84`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/text_to_audio_openai.py:119-210` |
| Studio 채팅 경로 | `agent_chat` Celery 작업 → 오케스트레이터 agno 에이전트가 도구 10개(검색·스크랩·UI 상태·대본·배너·오디오·제목·종료)를 호출 → 세션 상태를 SQLite에 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/async_podcast_agent_service.py:63-98`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/celery_tasks.py:29-64`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/db/agent_config_v2.py:119-145`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/agents/search_agent.py:65-105` |
| Celery·Redis | 작업 큐, 세션 락(10분) | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/celery_app.py:20-70`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/celery_worker.py:1-12` |
| 소셜 미디어 수집 | X·Facebook 피드를 창을 띄우는 Playwright(`headless=False`)로 긁어 감성 분석해 `social_media.db`에 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/social/browser.py:75-89`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/social/x_scraper.py:8-91`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/x_scraper_processor.py:8-24` |
| Slack 연동 | 같은 API의 클라이언트(스레드 하나가 세션 하나), `slack_bolt` 필요 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/integrations/slack/chat.py:15-24`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/integrations/slack/chat.py:1220-1223` |
| 웹 UI | React 19 페이지 13개 — Home·Sources·Articles·Podcasts·Studio·Voyager(작업·설정)·Social. 소스(`web/src`)와 미리 빌드한 `web/build`가 모두 저장소에 있고 백엔드는 `web/build`를 서빙 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/web/src/App.js:1-142`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/web/src/services/api.js:1-18` |
| 그 밖 | 데모 데이터 내려받기·압축, API를 부르는 스크립트형 테스트, 인트로 음악 | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/bootstrap_demo.py:54-64`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/pack_demo.py:8-21`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tests/agent_agno_test.py:1-12`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/static/musics/intro_audio.mp3` |

## 단계별 진행

### Step 1. 환경과 백엔드 기동 — 패키지 252개, 0.0.0.0, 포트 7000

**목적.** 앱의 `requirements.txt`를 그대로 설치하고 백엔드를 띄워, UI와 API가 한 프로세스에서 서빙되는 것과 시작할 때 무슨 일이 생기는지 확인합니다.

**할 일.**

```bash
cd advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong
uv venv --python 3.11
uv pip install -r requirements.txt
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Windows PowerShell은 활성화만 `.venv\Scripts\Activate.ps1`로 바꿉니다.)

`requirements.txt`는 236줄짜리 `pip freeze` 결과라 252개 패키지가 깔리고 가상환경이 2.3GB가 됩니다. 제 환경에서는 uv 캐시가 있는 상태로 40초가 걸리지 않았습니다(직접 확인). Python은 3.11이나 3.12를 씁니다 — 3.13과 3.14 가상환경에서 휠만 허용해(`--no-build`) 해석해 보면 3.13은 `blis==1.2.1`, 3.14는 `aiohttp==3.11.18`에서 막혔습니다(직접 확인). 이 저장소는 루트에 `pyproject.toml`이 있어 이후 `uv run`에는 모두 `--no-project`를 붙입니다. 진입점 `main.py`는 시작할 때(lifespan) 폴더 넷을 만들고 SQLite 표를 초기화하며, 마지막에 `../web/build`가 있는지만 봅니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/main.py:22-36`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up application...")
    os.makedirs("databases", exist_ok=True)
    os.makedirs("browsers", exist_ok=True)
    os.makedirs("podcasts/audio", exist_ok=True)
    os.makedirs("podcasts/images", exist_ok=True)
    os.makedirs("podcasts/recordings", exist_ok=True)
    await init_databases()
    if not os.path.exists(CLIENT_BUILD_PATH):
        print(f"WARNING: React client build path not found: {CLIENT_BUILD_PATH}")
    print("Application startup complete!")
    yield
    print("Shutting down application...")
    print("Shutdown complete")
```

앱 README는 `python main.py`를 안내하지만 그 진입점은 이렇습니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/main.py:185-187`

```python
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False, timeout_keep_alive=120, timeout_graceful_shutdown=120)
```

`0.0.0.0`이라 같은 네트워크의 누구나 접속할 수 있고 인증 코드는 없습니다(앱 README도 인증 계층이 아직 없다고 적음). 게다가 `main.py`에는 인자를 읽는 코드가 없어 README의 `python main.py --host 0.0.0.0 --port 7000`은 인자를 무시하고 포트는 환경변수 `PORT`(기본 7000)로만 바뀝니다(직접 확인, 아래). 그래서 같은 `main:app`을 `127.0.0.1`에만 열어 띄웁니다. 터미널 하나를 더 열어 이 명령을 계속 실행해 두고, 이후 명령은 첫 터미널에서 이어 갑니다.

```bash
uv run --no-project uvicorn main:app --host 127.0.0.1 --port 7000
```

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 컴파일이 조용히 끝나고 설치된 패키지 수와 버전이 나옵니다.

```bash
uv run --no-project python -m compileall -q main.py agents db models processors routers services tools utils integrations scheduler.py celery_worker.py
uv run --no-project python -c "import importlib.metadata as m; print(len(list(m.distributions())), m.version('agno'), m.version('fastapi'), m.version('faiss-cpu'))"
```

```text
252 1.4.2 0.115.12 1.9.0.post1
```

`import main`은 라우터·서비스·도구를 전부 끌어오므로 playwright·browser-use·faiss까지 import돼야 성공합니다. 이때 앱 폴더에 `databases/agent_sessions.db`와 `podcasts/`가 이미 생깁니다(서비스 객체가 만듭니다). 이어서 `main.py`에 인자 처리 코드가 없는지 봅니다.

```bash
uv run --no-project python -c "import main; print(type(main.app).__name__, len([r for r in main.app.routes if r.path.startswith('/api/')]))"
uv run --no-project python -c "src = open('main.py', encoding='utf-8').read(); print('argv' in src, 'argparse' in src)"
```

```text
INFO     [newspaper.network] Using requests library for http requests (alternative cloudscraper library is recommended for bypassing Cloudflare protection)
FastAPI 65
False False
```

서버가 떠 있는 상태에서 API 목록·UI 화면·UI 번들을 확인합니다. 브라우저로 `http://localhost:7000`을 열면 React UI가 뜹니다(스크래치 서버를 헤드리스 브라우저로 열어 홈 화면 "Hub"의 메뉴까지 그려지는 것을 직접 확인).

```bash
uv run --no-project python -c "import urllib.request as u; print(u.urlopen('http://127.0.0.1:7000/api/podcasts/').read().decode())"
uv run --no-project python -c "import urllib.request as u; r = u.urlopen('http://127.0.0.1:7000/'); print(r.status, r.headers['content-type']); print(r.read().decode()[:60])"
uv run --no-project python -c "import glob; t = open(glob.glob('../web/build/static/js/main.*.js')[0], encoding='utf-8').read(); print(t.count('localhost:7000'), 'cdn.jsdelivr.net' in open('../web/build/index.html', encoding='utf-8').read())"
```

```text
{"items":[],"total":0,"page":1,"per_page":10,"total_pages":0,"has_next":false,"has_prev":false}
200 text/html; charset=utf-8
<!doctype html><html lang="en"><head><meta charset="utf-8"/>
1 True
```

번들 안에 `localhost:7000`이 한 번 박혀 있어(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/web/src/services/api.js:3`) UI는 API를 항상 그 주소에서 찾으므로, 포트를 바꾸면 화면은 뜨지만 데이터가 오지 않습니다. `index.html`은 Tailwind를 `cdn.jsdelivr.net`에서 받아 옵니다 — 완전 로컬 앱이 아닙니다.

### Step 2. 저장소와 뉴스 소스 등록 — 단계 사이의 경계는 SQLite 표

**목적.** 파이프라인의 단계 경계가 어떤 표인지 보고, 첫 단계인 소스 등록 API를 호출해 봅니다.

**할 일.** 기동한 백엔드는 `db/config.py`의 경로에 SQLite 파일을 만들고, 표 정의는 `services/db_init.py`가 담고 있습니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/db/config.py:7-18`

```python
DEFAULT_DB_PATHS = {
    "sources_db": "databases/sources.db",
    "tracking_db": "databases/feed_tracking.db",
    "podcasts_db": "databases/podcasts.db",
    "tasks_db": "databases/tasks.db",
    "agent_session_db": "databases/agent_sessions.db",
    "faiss_index_db": "databases/faiss/article_index.faiss",
    "faiss_mapping_file": "databases/faiss/article_id_map.npy",
    "internal_sessions_db": "databases/internal_sessions.db",
    "social_media_db": "databases/social_media.db",
    "slack_sessions_db": "databases/slack_sessions.db",
}
```

`feed_tracking.db` 하나에 `feed_entries`(RSS 항목) → `crawled_articles`(본문과 AI 분석 결과) → `article_embeddings`(벡터)가 차례로 쌓이고, 처리기마다 "앞 표에서 읽어 뒤 표에 쓴다"가 이 파이프라인의 전부입니다.

![Step 2까지의 구성](diagrams/step2.svg)

**확인.**

```bash
uv run --no-project python -c "
import glob, os, sqlite3
for p in sorted(glob.glob('databases/*.db')):
    rows = sqlite3.connect(p).execute('select name from sqlite_master where type=? and name not like ? order by name', ('table', 'sqlite_%')).fetchall()
    print(os.path.basename(p), [r[0] for r in rows])
"
```

```text
agent_sessions.db []
feed_tracking.db ['article_categories', 'article_embeddings', 'crawled_articles', 'feed_entries', 'feed_tracking']
internal_sessions.db ['session_state']
podcasts.db ['podcasts']
social_media.db ['posts']
sources.db ['categories', 'source_categories', 'source_feeds', 'sources']
tasks.db ['podcast_configs', 'task_executions', 'tasks']
```

`agent_sessions.db`가 비어 있는 것은 정상입니다 — agno의 `SqliteStorage`는 파일만 만들고 표는 첫 사용 때 만듭니다(소스로 확인, agno 1.4.2 `agno/storage/sqlite.py`). 소스 등록은 `POST /api/sources/`입니다. 저장 함수는 소스·카테고리·피드를 하나씩 따로 넣습니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/source_service.py:158-181`

```python
    async def create_source(self, source_data: SourceCreate) -> Dict[str, Any]:
        """Create a new source."""
        try:
            source_query = """
            INSERT INTO sources (name, url, description, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            source_params = (source_data.name, source_data.url, source_data.description, source_data.is_active, datetime.now().isoformat())
            source_id = await sources_db.execute_query(source_query, source_params)
            if source_data.categories:
                for category_name in source_data.categories:
                    await self.add_source_category(source_id, category_name)
            elif hasattr(source_data, "category") and source_data.category:
                await self.add_source_category(source_id, source_data.category)
            if source_data.feeds:
                for feed in source_data.feeds:
                    await self.add_feed_to_source(source_id, feed)
            return await self.get_source(source_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "name" in str(e):
                raise HTTPException(status_code=409, detail="Source with this name already exists")
            raise HTTPException(status_code=500, detail=f"Error creating source: {str(e)}")
```

트랜잭션이 없어서, 같은 피드 URL로 두 번 등록하면 409가 돌아오는데도 피드 없는 소스 행이 하나 남습니다.

```bash
uv run --no-project python -c "
import json, urllib.request as u
def call(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = u.Request('http://127.0.0.1:7000' + path, data=data, method=method, headers={'Content-Type': 'application/json'})
    try:
        r = u.urlopen(req)
    except u.HTTPError as e:
        r = e
    return r.getcode(), json.load(r)
body = {'name': 'Local Tech Blog', 'url': 'https://example.com', 'categories': ['technology'], 'feeds': [{'feed_url': 'https://example.com/feed.xml', 'feed_type': 'main'}]}
code, j = call('POST', '/api/sources/', body)
print(code, j['id'], j['name'], j['categories'], [f['feed_url'] for f in j['feeds']])
code, j = call('POST', '/api/sources/', body)
print(code, j['detail'])
print(call('GET', '/api/sources/')[1]['total'])
"
```

```text
201 1 Local Tech Blog ['technology'] ['https://example.com/feed.xml']
409 A feed with this URL already exists for Local Tech Blog. Please edit the existing feed (ID: 1) instead.
2
```

### Step 3. 피드에서 항목으로 (처리기 1) — RSS가 아닌 것으로 판정되는 흔한 경우

**목적.** `feed_processor`의 부품 `get_feed_data`와 `store_feed_entries`를 가짜 RSS로 돌려, 항목이 `feed_entries`로 들어가는 모양과 검증 규칙의 함정을 확인합니다.

**할 일.** 처리기는 활성 피드마다 etag와 수정 시각을 넘겨 `feedparser.parse`를 부르고, 판정과 저장을 이렇게 합니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/rss_feed_parser.py:46-62`

```python
def is_rss_feed(feed_data: Any) -> bool:
    return feed_data.bozo and hasattr(feed_data, "bozo_exception")


def get_feed_data(
    feed_url: str, etag: Optional[str] = None, modified: Optional[Any] = None
) -> Dict[str, Any]:
    feed_data = feedparser.parse(feed_url, etag=etag, modified=modified)
    if is_rss_feed(feed_data):
        return {
            "is_rss_feed": False,
            "parsed_entries": None,
            "modified": None,
            "status": None,
            "current_hash": None,
            "etag": None,
        }
```

`is_rss_feed`라는 이름과 달리 실제로는 feedparser의 `bozo`(문서가 표준에서 벗어났다는 표시)만 봅니다. 처리기는 이 판정이 거짓이면 피드를 버립니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/feed_processor.py:42-56`

```python
            try:
                feed_data = get_feed_data(feed_url, etag=etag, modified=modified)
                if not feed_data["is_rss_feed"]:
                    print(f"Feed {feed_url} is not a valid RSS feed")
                    stats["failed_feeds"] += 1
                    continue
                if feed_data["status"] == 304:
                    print(f"Feed {feed_url} not modified since last check")
                    stats["unchanged_feeds"] += 1
                    continue
                current_hash = feed_data["current_hash"]
                if last_hash and current_hash == last_hash:
                    print(f"Feed {feed_url} content unchanged based on hash")
                    stats["unchanged_feeds"] += 1
                    continue
```

처리기의 반복문 자체(`fetch_and_process_feeds`)는 이 문서에서 돌리지 않았습니다. 실제 피드를 받는 함수이기 때문에, 같은 함수가 호출하는 부품만 XML 문자열로 돌렸습니다. `feedparser.parse`는 URL 대신 XML 문자열도 받습니다.

![Step 3까지의 구성](diagrams/step3.svg)

**확인.**

```bash
uv run --no-project python -c "
import feedparser
from utils.rss_feed_parser import get_feed_data
from db.config import get_tracking_db_path
from db.feeds import store_feed_entries
xml = '''<?xml version='1.0' encoding='UTF-8'?>
<rss version='2.0'><channel><title>Local Tech Blog</title><link>https://example.com</link><description>d</description>
<item><title>Faiss adds HNSW</title><link>https://example.com/a1</link><guid>a1</guid><pubDate>Tue, 29 Sep 2026 10:00:00 GMT</pubDate><description>HNSW index arrives.</description></item>
<item><title>Whisper for podcasts</title><link>https://example.com/a2</link><guid>a2</guid><pubDate>Tue, 29 Sep 2026 09:00:00 GMT</pubDate><description>Speech tools.</description></item>
</channel></rss>'''
d = get_feed_data(xml)
print(d['is_rss_feed'], d['status'], len(d['parsed_entries']), d['current_hash'])
print(d['parsed_entries'][0])
db = get_tracking_db_path()
print(store_feed_entries(db, 1, 1, d['parsed_entries']), store_feed_entries(db, 1, 1, d['parsed_entries']))
amp = xml.replace('Faiss adds HNSW', 'R&D news')
fp = feedparser.parse(amp)
print(fp.bozo, len(fp.entries))
bad = get_feed_data(amp)
print(bad['is_rss_feed'], bad['parsed_entries'])
"
```

```text
True 200 2 1ff4c790ddfe440ba5174654fb5e7220
{'title': 'Faiss adds HNSW', 'link': 'https://example.com/a1', 'summary': 'HNSW index arrives.', 'content': 'HNSW index arrives.', 'published_date': 'Tue, 29 Sep 2026 10:00:00 GMT', 'entry_id': 'a1'}
2 0
1 2
False None
```

항목 둘이 들어가고 같은 항목을 다시 넣으면 0건입니다(`link`가 `UNIQUE`). 마지막 두 줄이 함정입니다 — 제목에 `&` 하나가 든 피드를 feedparser는 항목까지 복구해 돌려주는데(`bozo`는 1), 이 앱은 피드 전체를 "RSS가 아님"으로 버립니다.

### Step 4. 항목에서 기사로, 그리고 AI 분석 (처리기 2·3) — API에 기사가 뜨는 조건

**목적.** 기사 수집이 원문 HTML의 `<body>`를 통째로 저장하는 것, AI 분석이 그것을 요약·분류로 바꿔 `processed=1`로 표시하는 것, 그 뒤에야 API가 기사를 보여 주는 것을 확인합니다.

**할 일.** 기사 수집(`url_processor`)은 아직 안 받은 항목마다 페이지를 받아 본문 태그와 메타를 저장합니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/crawl_url.py:64-70`

```python
def get_web_data(url: str) -> WebData:
    HEADERS["User-Agent"] = random.choice(USER_AGENTS)
    response = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    metadata = extract_meta_tags(soup)
    body = str(soup.find("body"))
    return {"raw_html": body, "metadata": metadata}
```

AI 분석(`ai_analysis_processor`)은 `raw_content`에서 스크립트·내비게이션을 걷어 낸 텍스트를 gpt-4o에 JSON으로 보내 `categories`·`summary`·`content`를 받습니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/ai_analysis_processor.py:15-25`

```python
def extract_clean_text(raw_html, max_tokens=8000):
    soup = BeautifulSoup(raw_html, "html.parser")
    for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
        element.decompose()
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)
    approx_tokens = len(text) / 4
    if approx_tokens > max_tokens:
        text = text[: max_tokens * 4]
    return text
```

두 처리기는 사이트와 OpenAI를 부르므로 돌리지 않았습니다. 대신 그 사이의 저장 함수를 가짜 페이지와 가짜 분석 결과로 돌렸습니다.

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 먼저 두 항목을 기사로 저장합니다.

```bash
uv run --no-project python -c "
from bs4 import BeautifulSoup
from utils.crawl_url import extract_meta_tags
from db.config import get_tracking_db_path
from db.feeds import get_uncrawled_entries, get_feed_stats
from db.articles import store_crawled_article, update_entry_status, get_article_stats
pages = {
    'https://example.com/a1': '''<html><head><title>Faiss adds HNSW</title><meta name='description' content='HNSW index arrives.'></head>
<body><nav>menu</nav><h1>Faiss adds HNSW</h1><p>Vector search got faster.</p><script>var x = 1;</script></body></html>''',
    'https://example.com/a2': '''<html><head><title>Whisper for podcasts</title></head>
<body><h1>Whisper for podcasts</h1><p>Speech tools help podcasters.</p></body></html>''',
}
db = get_tracking_db_path()
entries = get_uncrawled_entries(db, limit=20)
print([(e['id'], e['link']) for e in entries])
for e in entries:
    soup = BeautifulSoup(pages[e['link']], 'html.parser')
    ok = store_crawled_article(db, e, str(soup.find('body')), extract_meta_tags(soup))
    update_entry_status(db, e['id'], 'success' if ok else 'failed')
print(get_feed_stats(db))
print(get_article_stats(db))
"
```

```text
[(1, 'https://example.com/a1'), (2, 'https://example.com/a2')]
{'total_entries': 2, 'pending_entries': 0, 'processing_entries': 0, 'success_entries': 2, 'failed_entries': 0}
{'total_articles': 2, 'processed_articles': 0, 'pending_articles': 2, 'processing_articles': 0, 'success_articles': 0, 'error_articles': 0, 'failed_articles': 0}
```

기사는 둘이지만 아직 `processed`가 0이라 API에는 안 보입니다. 이제 분석 결과를 넣고 API를 부릅니다.

```bash
uv run --no-project python -c "
import json, sqlite3, urllib.request as u
from processors.ai_analysis_processor import extract_clean_text
from db.config import get_tracking_db_path
from db.articles import get_unprocessed_articles, update_article_status
def get(path):
    return json.load(u.urlopen('http://127.0.0.1:7000' + path))
db = get_tracking_db_path()
print('before AI:', get('/api/articles/')['total'])
for a in get_unprocessed_articles(db, limit=5):
    text = extract_clean_text(a['raw_content'])
    print(a['id'], repr(text))
    update_article_status(db, a['id'], {'categories': ['AI', 'Search'], 'summary': 'Summary of ' + a['title'], 'content': text}, True, None)
j = get('/api/articles/')
print('after AI:', j['total'], [(i['title'], i['categories']) for i in j['items']])
print('date_from filter:', get('/api/articles/?date_from=2026-09-01')['total'])
print(sqlite3.connect(':memory:').execute('select datetime(?), datetime(?)', ('Tue, 29 Sep 2026 10:00:00 GMT', '2026-09-29T10:00:00')).fetchone())
"
```

```text
before AI: 0
1 'Faiss adds HNSW\nVector search got faster.'
2 'Whisper for podcasts\nSpeech tools help podcasters.'
after AI: 2 [('Whisper for podcasts', ['ai', 'search']), ('Faiss adds HNSW', ['ai', 'search'])]
date_from filter: 0
(None, '2026-09-29 10:00:00')
```

분석 전에는 0건, 분석 뒤에는 2건입니다. 다만 RSS의 발행 시각은 `Tue, 29 Sep 2026 10:00:00 GMT`처럼 원문 문자열 그대로 저장되고, API의 날짜 필터와 정렬은 SQLite의 `datetime()`을 쓰는데 이 형식을 읽지 못해 `NULL`이 됩니다(마지막 줄). 그래서 `date_from=2026-09-01`이 두 기사를 모두 걸러 내고, 정렬은 `id` 역순으로 떨어집니다.

### Step 5. 임베딩과 FAISS 검색 (처리기 4·5) — "유사도 85%"의 실제 값

**목적.** 벡터가 BLOB으로 저장되고 FAISS 색인이 만들어지는 과정과, 검색 도구가 유사도를 계산하는 방식을 확인합니다.

**할 일.** 검색 에이전트의 도구 `embedding_search`는 질문을 임베딩하고 FAISS에서 가까운 기사 20개를 찾은 뒤, 아래 함수로 거리를 유사도로 바꿔 0.85 이상만 남깁니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/embedding_search.py:15-23`

```python
def l2_distance_to_cosine_similarity(distance: float) -> float:
    """Convert FAISS L2 distance to cosine similarity for unit-normalized embeddings.

    OpenAI text-embedding-3 vectors are length-1, so:
        ||a - b||^2 = 2 - 2 * cos(a, b)
        cos(a, b) = 1 - ||a - b||^2 / 2
    """
    similarity = 1.0 - (float(distance) ** 2) / 2.0
    return float(max(0.0, min(1.0, similarity)))
```

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/embedding_search.py:124-133`

```python
            return f"Semantic search unavailable: {error}. Continuing with other search methods."
        distances, indices = faiss_index.search(query_vector, top_k)
        results_with_metrics = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(id_map):
                distance = float(distances[0][i])
                similarity = l2_distance_to_cosine_similarity(distance)
                if similarity >= similarity_threshold:
                    article_id = id_map[idx]
                    results_with_metrics.append((idx, distance, similarity, article_id))
```

주석의 유도는 맞지만 FAISS의 L2 색인은 이미 **제곱** 거리를 돌려주므로(`D = 2 − 2cos`), 함수가 그것을 다시 제곱합니다. 임베딩 호출은 돌리지 않고 단위 벡터를 손으로 만들어 확인합니다.

```bash
uv run --no-project python -c "
import numpy as np, faiss
from tools.embedding_search import l2_distance_to_cosine_similarity as app_sim
rng = np.random.default_rng(0)
a = rng.standard_normal(1536).astype('float32'); a /= np.linalg.norm(a)
r = rng.standard_normal(1536).astype('float32'); r -= (r @ a) * a; r /= np.linalg.norm(r)
for cos in (0.9, 0.75, 0.5):
    b = (cos * a + (1 - cos ** 2) ** 0.5 * r).astype('float32')
    index = faiss.IndexHNSWFlat(1536, 32)
    index.add(b[None, :])
    D, I = index.search(a[None, :], 1)
    d = float(D[0][0])
    print('true cosine', cos, '| faiss D', round(d, 3), '| app similarity', round(app_sim(d), 3), '| passes 0.85:', app_sim(d) >= 0.85)
"
```

```text
true cosine 0.9 | faiss D 0.2 | app similarity 0.98 | passes 0.85: True
true cosine 0.75 | faiss D 0.5 | app similarity 0.875 | passes 0.85: True
true cosine 0.5 | faiss D 1.0 | app similarity 0.5 | passes 0.85: False
```

코사인 0.75가 0.875로 부풀어 필터를 통과합니다. 통과선 0.85를 거꾸로 풀면 실제 코사인 약 0.73입니다. 스케줄러가 부르는 색인 처리기의 기본 색인 종류는 `hnsw`이고(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/faiss_indexing_processor.py:306-311`), 아래는 저장된 벡터를 색인에 넣은 뒤 진짜 `embedding_search`를 질의 임베딩 자리만 가짜로 바꿔 부른 결과입니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.**

```bash
uv run --no-project python -c "
import json
import numpy as np
from db.config import get_tracking_db_path, get_faiss_db_path
from processors.embedding_processor import get_articles_without_embeddings, store_embedding
from processors.faiss_indexing_processor import process_embeddings_for_indexing
import tools.embedding_search as es
db = get_tracking_db_path()
rng = np.random.default_rng(0)
v1 = rng.standard_normal(1536); v1 /= np.linalg.norm(v1)
r = rng.standard_normal(1536); r -= (r @ v1) * v1; r /= np.linalg.norm(r)
v2 = 0.75 * v1 + (1 - 0.75 ** 2) ** 0.5 * r
for a, v in zip(get_articles_without_embeddings(db), (v1, v2)):
    store_embedding(db, a['id'], v.tolist(), 'text-embedding-3-small')
index_path, map_path = get_faiss_db_path()
print(process_embeddings_for_indexing(tracking_db_path=db, index_path=index_path, mapping_path=map_path, index_type='hnsw'))
es.generate_query_embedding = lambda text, model=es.EMBEDDING_MODEL: (v1.tolist(), None)
hits = json.loads(es.embedding_search(None, 'vector search').split('results: ', 1)[1])
print([(h['title'], round(h['similarity'], 3), h['is_scrapping_required']) for h in hits])
"
```

```text
Detected embedding dimension: 1536
Creating new FAISS index with dimension 1536, type: hnsw
Added 2 embeddings to FAISS index
FAISS index saved to databases/faiss/article_index.faiss
ID mapping saved to databases/faiss/article_id_map.npy
Marked 2 embeddings as indexed in the database
{'processed': 2, 'added': 2, 'errors': 0, 'total_vectors': 2, 'index_type': 'hnsw', 'status': 'success'}
Embedding Search Input: vector search
[('Faiss adds HNSW (Relevance: 100%)', 1.0, False), ('Whisper for podcasts (Relevance: 87%)', 0.875, False)]
```

기사 둘이 색인에 들어가고, 질의에 코사인 0.75인 둘째 기사가 "Relevance: 87%"로 함께 돌아옵니다.

### Step 6. 팟캐스트 생성기 (처리기 6) — 검색·스크랩·대본을 함수 하나가 부른다

**목적.** 생성기가 에이전트 넷과 TTS를 어떤 순서로 부르고 어디서 멈추는지, 설정 화면의 필드가 실제로 쓰이는지, 키가 없으면 어디서 실패하는지 확인합니다.

**할 일.** 검색 에이전트는 agno `Agent`(gpt-4o-mini, JSON 모드)에 도구 일곱 개를 주고, 어떤 도구를 부를지는 모델이 고릅니다. 실패하면 예외를 삼키고 빈 목록을 돌려줍니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/search_agent.py:63-90`

```python
def search_agent_run(query: str) -> str:
    try:
        session_id = str(uuid.uuid4())
        search_agent = Agent(
            model=OpenAIChat(id="gpt-4o-mini"),
            instructions=SEARCH_AGENT_INSTRUCTIONS,
            description=SEARCH_AGENT_DESCRIPTION,
            use_json_mode=True,
            response_model=SearchResults,
            tools=[
                google_news_discovery_run,
                DuckDuckGoTools(),
                wikipedia_search,
                jikan_search,
                embedding_search,
                social_media_search,
                social_media_trending_search,
            ],
            session_id=session_id,
        )
        response = search_agent.run(query, session_id=session_id)
        response_dict = response.to_dict()
        return response_dict["content"]["items"]
    except Exception as _:
        import traceback

        traceback.print_exc()
        return []
```

생성기는 이 결과를 받아 스크랩하고, 본문이 100자를 넘는 것만 대본 재료로 남깁니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/podcast_generator_processor.py:56-100`

```python
    try:
        search_results = search_agent_run(prompt)
        if not search_results:
            print(f"WARNING: No search results found for prompt: {prompt}")
            return {"error": "No search results found"}
        print(f"Found {len(search_results)} search results")
        if debug:
            print("Search results:", json.dumps(search_results[:2], indent=2))
    except Exception as e:
        print(f"ERROR: Search agent failed: {e}")
        return {"error": f"Search agent failed: {str(e)}"}
    try:
        scraped_results = scrape_agent_run(prompt, search_results)
        if not scraped_results:
            print("WARNING: No content could be scraped")
            return {"error": "No content could be scraped"}
        confirmed_results = []
        for result in scraped_results:
            if result.get("full_text") and len(result["full_text"].strip()) > 100:
                result["confirmed"] = True
                confirmed_results.append(result)
        if not confirmed_results:
            print("WARNING: No high-quality content available after scraping")
            return {"error": "No high-quality content available"}
        print(f"Successfully scraped {len(confirmed_results)} high-quality articles")
        if debug:
            print("Sample scraped content:", confirmed_results[0].get("full_text", "")[:200])
    except Exception as e:
        print(f"ERROR: Scrape agent failed: {e}")
        return {"error": f"Scrape agent failed: {str(e)}"}
    try:
        language_name = get_language_name(language_code)
        podcast_data = script_agent_run(query=prompt, search_results=confirmed_results, language_name=language_name)
        if not podcast_data or not isinstance(podcast_data, dict):
            print("ERROR: Failed to generate podcast script")
            return {"error": "Failed to generate podcast script"}
        if not podcast_data.get("sections"):
            print("ERROR: Generated podcast script is missing required sections")
            return {"error": "Invalid podcast script structure"}
        print(f"Generated script with {len(podcast_data['sections'])} sections")
        if debug:
            print("Script title:", podcast_data.get("title", "No title"))
    except Exception as e:
        print(f"ERROR: Script agent failed: {e}")
        return {"error": f"Script agent failed: {str(e)}"}
```

스크랩 에이전트가 쓰는 크롤러는 `scrape_urls`를 부를 때마다 곧바로 Chromium을 띄웁니다. 스크랩이 필요한 URL이 하나도 없어도 호출은 무조건 일어나므로(소스로 확인), 브라우저가 없으면 이 단계는 항상 실패합니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/scrape_agent.py:62-66`

```python
            unique_urls.append(url)
        url_to_search_results[url].append(search_result)
    browser_crawler = create_browser_crawler()
    scraped_results = browser_crawler.scrape_urls(unique_urls)
    url_to_scraped = {result["original_url"]: result for result in scraped_results}
```

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/browser_crawler.py:19-24`

```python
    def scrape_urls(self, urls: List[str]) -> List[Dict]:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
```

우리 DB에서 찾은 기사는 스크랩이 필요 없다고 표시돼 있어 본문 대신 `description`, 곧 Step 4의 AI 요약이 대본 재료가 됩니다(소스로 확인, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/pipeline/scrape_agent.py:70-85`). 이 스크랩 단계는 실제 브라우저를 열 수 있어 돌리지 않았습니다.

`agents/`에 같은 이름의 에이전트 네 개가 세션용으로 한 벌 더 있어 헷갈리기 쉽습니다. 예약 경로는 세션과 무관한 `tools/pipeline/`을 쓰고, `agents/`는 Studio의 도구입니다. 검색 에이전트는 Studio 쪽에 도구 둘(`search_articles`·`run_browser_search`)과 지시문 두 줄이 더 있습니다(소스로 확인). 이 앱의 agno는 1.4.2인데, 에이전트 실행이 끝날 때마다 `api.agno.com`으로 실행 통계를 보내고 `AGNO_TELEMETRY=false`로 끕니다(소스로 확인, `agno/agent/agent.py`·`agno/cli/settings.py`). Day 047 Step 5의 「agno의 익명 사용 통계」 단락은 agno 3.0.10을 다룬 것이지만 같은 환경변수를 씁니다. 검색·대본·배너가 각각 새 `Agent`를 만들어 부르므로 팟캐스트 한 편에 최소 세 번 나갑니다.

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** 설정 화면의 필드부터 봅니다. 생성기 소스에서 그 이름이 나오는 줄을 모두 찍습니다.

```bash
uv run --no-project python -c "
import re
for i, line in enumerate(open('processors/podcast_generator_processor.py', encoding='utf-8'), 1):
    if re.search('podcast_script_prompt|time_range_hours|limit_articles|image_prompt', line):
        print(i, line.strip())
"
```

```text
44 podcast_script_prompt: Optional[str] = None,
45 image_prompt: Optional[str] = None,
104 image_query = image_prompt if image_prompt else prompt
213 time_range_hours = config.get("time_range_hours", 24)
214 limit_articles = config.get("limit_articles", 20)
217 podcast_script_prompt = config.get("podcast_script_prompt")
218 image_prompt = config.get("image_prompt")
221 print(f"Time range: {time_range_hours} hours")
222 print(f"Limit: {limit_articles} articles")
233 podcast_script_prompt=podcast_script_prompt,
234 image_prompt=image_prompt,
```

`image_prompt`만 배너 질의로 쓰이고(104행), `time_range_hours`와 `limit_articles`는 읽어서 출력만 하고(221·222행), `podcast_script_prompt`는 함수에 전달되지만 본문 어디에서도 쓰이지 않습니다. 화면의 세 필드는 저장될 뿐 생성에는 영향이 없습니다. 이제 키가 없을 때, 그리고 외부 호출을 모두 가짜로 바꿨을 때 생성기 본체가 어떻게 흐르는지 봅니다.

```bash
uv run --no-project python -c "
import logging
logging.disable(logging.CRITICAL)
from agno.agent import Agent
from agno.models.openai import OpenAIChat
model = OpenAIChat(id='gpt-4o-mini')
agent = Agent(model=model, instructions=['x'])
print('agent built:', type(agent).__name__, agent.model.id)
try:
    model.get_client()
except Exception as e:
    print(type(e).__name__)
"
```

```text
agent built: Agent gpt-4o-mini
OpenAIError
```

`OpenAIChat`은 키 없이도 만들어지고, 클라이언트를 만드는 첫 순간에야 `OpenAIError`가 납니다. 예약 경로에서는 그 예외를 검색 에이전트가 삼키므로 생성기가 보는 것은 "No search results found"뿐입니다(소스로 확인, 실행하지는 않음). 아래는 검색·스크랩·대본·배너·TTS 다섯 호출을 가짜로 바꾸고 나머지 오케스트레이션은 원본 그대로 두 번 부른 결과입니다. 첫 호출은 본문이 짧아 멈추고, 둘째 호출은 끝까지 가서 `podcasts` 표에 한 행을 넣습니다.

```bash
uv run --no-project python -c "
import processors.podcast_generator_processor as g
g.search_agent_run = lambda prompt: [{'url': 'https://example.com/a1', 'title': 'Faiss adds HNSW', 'description': 'Faiss gained an HNSW index for vector search.', 'source_name': 'general', 'tool_used': 'embedding_search', 'published_date': '', 'is_scrapping_required': False}]
g.script_agent_run = lambda query, search_results, language_name: {'title': 'Daily AI Brief', 'sections': [{'type': 'intro', 'title': None, 'dialog': [{'speaker': 'ALEX', 'text': 'Welcome.'}, {'speaker': 'MORGAN', 'text': 'Thanks.'}]}], 'sources': [r['url'] for r in search_results]}
g.image_generation_agent_run = lambda query, script: {}
g.generate_podcast_audio = lambda script, output_path, tts_engine, language_code: 'podcasts/audio/fake.wav'
g.scrape_agent_run = lambda prompt, items: [dict(i, full_text='too short') for i in items]
print(g.generate_podcast_from_prompt_v2(prompt='AI news', openai_api_key='unused', tts_engine='openai'))
g.scrape_agent_run = lambda prompt, items: [dict(i, full_text=i['description'] * 4) for i in items]
print(g.generate_podcast_from_prompt_v2(prompt='AI news', openai_api_key='unused', tts_engine='openai')['processing_stats'])
"
```

```text
Starting enhanced podcast generation for prompt: AI news
Found 1 search results
WARNING: No high-quality content available after scraping
{'error': 'No high-quality content available'}
Starting enhanced podcast generation for prompt: AI news
Found 1 search results
Successfully scraped 1 high-quality articles
Generated script with 1 sections
WARNING: No images were generated
Generated podcast audio: podcasts/audio/fake.wav
Stored podcast data with ID: 1
{'search_results': 1, 'scraped_results': 1, 'confirmed_results': 1, 'images_generated': 0, 'audio_generated': True}
```

### Step 7. 대본에서 오디오로 — 화자 번호, 엔진 선택, 조립

**목적.** 대본 JSON이 화자 번호가 붙은 목록으로 바뀌고, TTS 선택기가 엔진을 고르고, 조각을 이어 붙여 WAV 하나를 만드는 과정을 확인합니다.

**할 일.** 대본의 `ALEX`·`MORGAN`은 1·2번 화자로 바뀝니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/processors/podcast_generator_processor.py:24-33`

```python
def convert_script_to_audio_format(podcast_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    speaker_map = {"ALEX": 1, "MORGAN": 2}
    dict_entries = []
    for section in podcast_data.get("sections", []):
        for dialog in section.get("dialog", []):
            speaker = dialog.get("speaker", "ALEX")
            text = dialog.get("text", "")
            if text and speaker in speaker_map:
                dict_entries.append({"text": text, "speaker": speaker_map[speaker]})
    return {"entries": dict_entries}
```

선택기는 이름으로 등록된 엔진 함수를 찾아 호출합니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/tts_engine_selector.py:14-31`

```python
def generate_podcast_audio(
    script: Any, output_path: str, tts_engine: str = "kokoro", language_code: str = "en", silence_duration: float = 0.7, voice_map=None
) -> Optional[str]:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    engine_name = tts_engine.lower()
    if engine_name not in _TTS_ENGINES:
        print(f"Unsupported TTS engine: {tts_engine}")
        return None
    try:
        return _TTS_ENGINES[engine_name](
            script=script, output_path=output_path, language_code=language_code, silence_duration=silence_duration, voice_map=voice_map
        )
    except Exception as e:
        import traceback

        print(f"Error generating audio with {tts_engine}: {e}")
        traceback.print_exc()
        return None
```

엔진 기본값이 곳곳에서 다릅니다 — 선택기 함수는 `kokoro`, 설정 API 스키마는 `kokoro`(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/models/podcast_config_schemas.py:12`), 표의 기본값과 UI 기본값은 `elevenlabs`(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/db_init.py:253`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/web/src/components/PodcastConfigForm.js:12`), Studio는 `openai` 고정(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/agents/audio_generate_agent.py:329`)입니다. 엔진 셋 모두 최종 경로를 `os.path.abspath`로 돌려줍니다(예: `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/text_to_audio_openai.py:140`). Day 003 Step 6이 ElevenLabs로 텍스트를 음성으로 바꾸는 호출을 이미 다뤘으니 여기서는 조립만 봅니다. TTS 호출 자리에는 사인파를 돌려주는 가짜 함수를 끼웠고 나머지 조립 코드는 원본 그대로입니다.

![Step 7까지의 구성](diagrams/step7.svg)

**확인.**

```bash
uv run --no-project python -c "
import contextlib, io
import numpy as np, soundfile as sf
import utils.text_to_audio_openai as t
from processors.podcast_generator_processor import convert_script_to_audio_format
script = {'title': 'Demo', 'sections': [
    {'type': 'intro', 'dialog': [{'speaker': 'ALEX', 'text': 'Welcome.'}, {'speaker': 'MORGAN', 'text': 'Thanks.'}]},
    {'type': 'outro', 'dialog': [{'speaker': 'ALEX', 'text': 'Bye.'}]}]}
entries = convert_script_to_audio_format(script)['entries']
print(entries)
def fake_tts(client, text, speaker_id, voice_map=None, model=None):
    n = 24000 * (1 if speaker_id == 1 else 2)
    tone = np.sin(2 * np.pi * (220 if speaker_id == 1 else 330) * np.arange(n) / 24000)
    return (0.5 * tone).astype('float32'), 24000
t.text_to_speech_openai = fake_tts
with contextlib.redirect_stdout(io.StringIO()):
    out = t.create_podcast(entries, 'podcasts/audio/demo.wav', api_key='dummy')
data, rate = sf.read(out)
print(rate, len(data), round(len(data) / rate, 2), round(float(abs(data).max()), 2))
"
```

```text
[{'text': 'Welcome.', 'speaker': 1}, {'text': 'Thanks.', 'speaker': 2}, {'text': 'Bye.', 'speaker': 1}]
24000 129600 5.4 0.95
```

세 대사(1초·2초·1초)가 0.7초 무음으로 이어져 5.4초가 되고, 진폭은 0.95로 정규화됩니다. 예약 경로의 조립에는 배경음악이 없습니다.

```bash
uv run --no-project python -c "
import soundfile as sf
from utils import tts_engine_selector as s
print(sorted(s._TTS_ENGINES))
print(s.generate_podcast_audio([], 'podcasts/audio/x.wav', tts_engine='piper'))
i = sf.info('static/musics/intro_audio.mp3')
print(i.samplerate, i.channels, round(i.duration, 1))
"
```

```text
['elevenlabs', 'kokoro', 'openai']
Unsupported TTS engine: piper
None
48000 2 6.1
```

엔진은 `elevenlabs`·`kokoro`·`openai` 셋이고, 모르는 이름은 조용히 `None`이 됩니다. 인트로·아웃트로 음악(같은 파일 하나, 48kHz 스테레오 6.1초)은 Studio의 오디오 에이전트만 앞뒤에 붙입니다(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/agents/audio_generate_agent.py:237-261`).

### Step 8. 저장·재생·스케줄러 — 절대 경로가 남긴 문제

**목적.** 생성기가 `podcasts` 표에 무엇을 저장하는지, 그것이 API와 UI를 거쳐 어떻게 재생되는지, 스케줄러가 처리기를 어떻게 띄우는지 확인합니다.

**할 일.** 저장 함수는 세션 상태 형태의 딕셔너리를 받아 `podcasts`에 한 행을 넣습니다. 생성기는 `audio_url` 자리에 TTS가 돌려준 경로를 그대로 넣으므로 예약 경로의 `audio_path`는 절대 경로입니다(Studio는 파일 이름만 넣습니다). API는 그것을 이렇게 주소로 바꿉니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/services/podcast_service.py:175-179`

```python
    async def get_podcast_audio_url(self, podcast: Dict[str, Any]) -> Optional[str]:
        """Get the URL for the podcast audio file if available."""
        if podcast.get("audio_generated") and podcast.get("audio_path"):
            return f"/audio/{podcast.get('audio_path')}"
        return None
```

UI는 그 주소에서 마지막 `/` 뒤만 잘라 스트리밍 주소를 만듭니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/web/src/pages/PodcastDetail.js:355-361`

```javascript
   const hasScript = content && content.sections && content.sections.length > 0;
   let streamingAudioUrl = '';
   if (hasAudio) {
      const originalAudioUrl = audio_url;
      const filename = originalAudioUrl.split('/').pop();
      streamingAudioUrl = `${apiService.API_BASE_URL}/stream-audio/${filename}`;
   }
```

macOS·Linux의 절대 경로는 `/`로 이어져 파일 이름만 남지만, Windows의 `C:\...` 경로는 자르지 못하고 통째로 남습니다. 브라우저는 URL 경로의 `\`를 `/`로 바꿔 보내므로 서버에는 `/stream-audio/C:/Users/...`가 도착합니다. 아래는 예약 경로가 저장한 것과 같은 절대 경로 행을 넣고 이 주소들을 서버에 물어본 결과입니다.

![Step 8까지의 구성](diagrams/step8.svg)

**확인.**

```bash
uv run --no-project python -c "
import json, os, urllib.request as u
from tools.session_state_manager import _save_podcast_to_database_sync
B = 'http://127.0.0.1:7000'
audio = os.path.abspath('podcasts/audio/demo.wav')
state = {'generated_script': {'title': 'Demo', 'sections': [], 'sources': ['https://example.com/a1']}, 'audio_url': audio, 'tts_engine': 'openai'}
ok, message, pid = _save_podcast_to_database_sync(state)
print(ok, pid)
j = json.load(u.urlopen(B + '/api/podcasts/by-identifier/' + str(pid)))
print(os.path.isabs(j['podcast']['audio_path']), j['audio_url'].startswith('/audio/'))
name = os.path.basename(audio)
r = u.urlopen(u.Request(B + '/stream-audio/' + name, headers={'Range': 'bytes=0-99'}))
print(r.status, r.headers['content-range'], r.headers['content-length'], r.headers['content-type'])
r = u.urlopen(B + '/stream-audio/C:/Users/me/' + name)
print(r.status, r.headers['content-type'])
"
node -e "console.log(new URL('http://localhost:7000/stream-audio/C:' + String.fromCharCode(92) + 'Users' + String.fromCharCode(92) + 'me' + String.fromCharCode(92) + 'demo.wav').pathname)"
```

```text
True 2
True True
206 bytes 0-99/259244 100 audio/wav
200 text/html; charset=utf-8
/stream-audio/C:/Users/me/demo.wav
```

셋째 줄은 파일 이름으로 Range 요청을 보냈을 때의 응답(206)이고, 넷째 줄은 브라우저가 Windows 경로를 바꿔 보내는 모양(`/stream-audio/C:/Users/...`, 다섯째 줄이 Node의 `URL`이 실제로 만든 경로)으로 물었을 때의 응답입니다. 서버는 이 주소를 `/{full_path:path}` 안전망으로 받아 오디오 대신 UI의 HTML을 200으로 돌려줍니다. Windows에서 예약 경로가 만든 팟캐스트가 재생되지 않을 이유입니다(브라우저 재생은 열어 보지 못했습니다). 반대로 서버는 `os.path.join("podcasts/audio", filename)`에 URL의 값을 그대로 넣어(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/main.py:61`), Windows에서는 절대 경로를 요청하면 다른 폴더의 파일도 읽힙니다. 그래서 `0.0.0.0`으로 열면 안 됩니다.

```bash
uv run --no-project python -c "
import os, tempfile, urllib.parse, urllib.request as u
f = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
f.write(b'outside-podcasts-audio')
f.close()
r = u.urlopen('http://127.0.0.1:7000/stream-audio/' + urllib.parse.quote(f.name, safe=''))
print(r.status, r.headers['content-type'], r.read())
os.unlink(f.name)
"
```

```text
200 audio/wav b'outside-podcasts-audio'
```

방금 만든 임시 파일이 오디오 폴더 밖에서 읽혔습니다(Windows에서 확인, macOS·Linux는 확인하지 못함). 마지막으로 스케줄러입니다. UI(Voyager)는 작업을 `tasks` 표에 넣을 뿐이고, 스케줄러가 표에서 지금 돌 작업을 찾아 `command`를 그대로 서브프로세스로 실행합니다.

`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/scheduler.py:96-103`

```python
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
```

스케줄러는 시작하자마자 한 번 점검하고 이후 1분마다 점검하며(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/scheduler.py:185`, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/scheduler.py:192`), `last_run`이 비어 있는 새 작업은 바로 대상이 됩니다. 이 문서는 스케줄러를 켜지 않았습니다. 대신 API로 작업을 만들고 "지금 돌 작업" 목록에 뜨는 것만 봤습니다.

```bash
uv run --no-project python -c "
import json, scheduler, urllib.request as u
def call(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = u.Request('http://127.0.0.1:7000' + path, data=data, method=method, headers={'Content-Type': 'application/json'})
    r = u.urlopen(req)
    return r.getcode(), json.load(r)
code, t = call('POST', '/api/tasks/', {'name': 'Feeds', 'task_type': 'feed_processor', 'frequency': 1, 'frequency_unit': 'hours'})
print(code, t['task_type'], t['command'], t['last_run'])
print([(x['id'], x['command']) for x in call('GET', '/api/tasks/pending')[1]])
print(scheduler.MAX_WORKERS, scheduler.DEFAULT_TASK_TIMEOUT)
"
```

```text
201 feed_processor python -m processors.feed_processor None
[(1, 'python -m processors.feed_processor')]
5 3600
```

Studio 경로는 처리기 대신 Celery 워커가 `agent_chat`을 실행하고, 그 프로세스와 저장소는 아래 그림에 정리했습니다. Redis 없이 Studio에 메시지를 보내 보는 명령은 문제 해결에 있습니다.

![Studio 채팅 경로의 프로세스와 저장소](diagrams/extra-studio.svg)

## 요청 한 건이 흐르는 과정

여기서 요청 한 건은 스케줄러가 팟캐스트 한 편을 만드는 한 주기입니다. 처리기마다 도는 시각이 달라 구간별로 나눠 그렸고(그림 17장), 메시지는 어느 그림에도 한 번씩, 시간 순서대로 있습니다. 화살표는 처리기가 표에서 입력을 읽는 것, 바깥에 요청하는 것, 산출물을 쓰는 것, 그리고 다음 실행을 가르는 표시(etag·해시·`processed`·색인 표시)까지 그렸습니다. 실행 전 준비 호출(개수 세기·중복 확인·추적 행 만들기·표 만들기·브라우저 탭 만들기·복구 초기화·`processing` 표시·색인 차원 확인)은 그리지 않았고, 배너 이미지 분기와 검색 도구 여섯 개, 그리고 에이전트 실행마다 agno가 보내는 실행 통계(Step 6)는 이 경로에서 뺐습니다. 먼저 작업이 만들어지는 과정입니다. UI가 작업 종류와 주기를 보내면 API가 표에 한 행을 넣습니다.

![작업 만들기](diagrams/extra-task.svg)

스케줄러는 표에서 지금 돌 작업을 찾아 처리기를 서브프로세스로 띄웁니다. 처리기 여섯이 모두 이렇게 뜹니다.

![작업 실행](diagrams/extra-schedule.svg)

첫째로 피드 처리기가 소스 표에서 피드를 읽어 항목을 씁니다. 사이트에는 etag와 수정 시각을 함께 보냅니다.

![피드 처리기](diagrams/extra-feed.svg)

기사 수집이 항목의 링크를 열어 본문을 저장합니다.

![기사 수집](diagrams/extra-crawl.svg)

AI 분석이 gpt-4o로 요약·분류를 만들어 기사를 완성합니다.

![AI 분석](diagrams/extra-analyze.svg)

임베딩이 완성된 기사에서 벡터를 만듭니다.

![임베딩](diagrams/extra-embed.svg)

색인이 새 벡터를 FAISS에 붙입니다.

![색인](diagrams/extra-index.svg)

여기까지가 기사를 만드는 쪽이고, 이제 팟캐스트를 만드는 쪽입니다. 생성기는 뜨자마자 설정을 읽습니다.

![설정 읽기](diagrams/extra-config.svg)

검색이 이 경로의 핵심이라 그림 셋으로 나눴습니다. 검색 에이전트가 gpt-4o-mini에게 일곱 도구를 주고, 모델이 `embedding_search`를 고른 경우를 따라갑니다. 어느 도구를 부를지는 실행마다 달라질 수 있습니다. 먼저 질문을 벡터로 바꿔 FAISS에서 가까운 기사를 찾습니다. 색인과 id 맵은 호출마다 디스크에서 새로 읽습니다(소스로 확인).

![요청 시퀀스](diagrams/sequence.svg)

그다음 찾은 기사 id로 기사 표와 소스 표를 조회합니다.

![기사 조회](diagrams/extra-lookup.svg)

도구 결과가 모델에게 돌아가 JSON으로 다듬어지고 생성기가 받습니다.

![검색 결과](diagrams/extra-result.svg)

검색 결과 가운데 스크랩이 필요한 URL을 브라우저로 엽니다. 우리 기사만 있어도 Chromium은 뜹니다(소스로 확인).

![스크랩](diagrams/extra-scrape.svg)

대본 에이전트가 확인된 소스로 두 진행자의 대본을 씁니다.

![대본](diagrams/extra-script.svg)

TTS 선택기가 엔진을 골라 대사를 음성으로 받아 옵니다. 그림은 UI 기본값인 ElevenLabs 엔진을 그렸습니다.

![TTS 호출](diagrams/extra-audio.svg)

엔진이 조각을 이어 붙여 WAV 하나로 쓰고, 생성기가 그 경로와 대본을 표에 저장합니다.

![WAV 쓰기와 저장](diagrams/extra-save.svg)

마지막으로 사용자가 UI에서 재생하는 과정입니다. 먼저 상세 화면이 팟캐스트 한 편의 데이터를 받습니다.

![재생 화면의 데이터](diagrams/extra-play.svg)

이어서 화면의 오디오 태그가 스트리밍 주소를 부릅니다.

![오디오 스트리밍](diagrams/extra-stream.svg)

## 실행 체크리스트

- [ ] `uv venv --python 3.11`과 `uv pip install -r requirements.txt`로 252개 패키지를 설치하고 `import main`까지 확인했다
- [ ] 백엔드를 `127.0.0.1`로만 띄우고 `/api/podcasts/`가 빈 목록을 돌려주는 것을 확인했다
- [ ] 여섯 SQLite 파일과 표를 확인하고, 소스 등록이 중복 피드에서 409와 고아 행을 남기는 것을 확인했다
- [ ] `&`가 든 RSS가 `is_rss_feed: False`로 버려지는 것을 확인했다
- [ ] AI 분석 결과가 있어야 `/api/articles/`에 기사가 나오고 RSS 날짜는 날짜 필터에서 빠지는 것을 확인했다
- [ ] 코사인 0.75가 앱 유사도 0.875로 필터를 통과하는 것을 확인했다
- [ ] 설정의 `time_range_hours`·`limit_articles`·`podcast_script_prompt`가 생성에 쓰이지 않는 것을 확인했다
- [ ] 가짜 외부 호출로 생성기가 `podcasts` 표에 한 행을 넣는 것과 오디오 조립 결과(5.4초)를 확인했다
- [ ] 예약 경로가 저장하는 `audio_path`가 절대 경로이고 브라우저 형태의 주소는 HTML을 돌려주는 것을 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `uv pip install -r requirements.txt`가 Python 3.13이나 3.14에서 실패 | 고정된 버전 중 휠이 없는 것이 있음(휠만 허용해 해석하면 3.13은 `blis==1.2.1`, 3.14는 `aiohttp==3.11.18`에서 막힘, 직접 확인) | 리포 코드는 고치지 않음 — `uv venv --python 3.11`(또는 3.12)로 새로 만든다 |
| 설치 때 `spacy==3.8.5` yanked 경고 | 고정한 버전이 PyPI에서 철회됨(직접 확인) | 경고일 뿐 설치는 끝까지 됨 |
| `python main.py --host ... --port ...`가 인자를 무시하고 `0.0.0.0:7000`으로 뜸 | `main.py`가 인자를 읽지 않고 호스트를 `0.0.0.0`으로 고정함(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/main.py:185-187`) | 로컬 실습에는 `uvicorn main:app --host 127.0.0.1`로 띄운다 |
| 포트를 바꿨더니 UI는 뜨는데 목록이 비어 있음 | UI 번들에 API 주소 `http://localhost:7000`이 박혀 있음(직접 확인) | 포트를 7000으로 두거나 `web/src/services/api.js`를 고쳐 다시 빌드 — 이 문서는 빌드하지 않음 |
| Redis 없이 Studio에서 메시지를 보내면 1분 넘게 매달렸다 500 | Celery의 Redis 결과 백엔드가 재연결을 20번 시도한 뒤 포기하고(직접 확인, 아래 명령) `chat`이 오류 응답을 만듦 | Redis를 띄우거나 예약 경로만 쓴다 |
| `python -m integrations.slack.chat`이 ImportError | `slack_bolt`가 `requirements.txt`에 없음(직접 확인, 아래 명령) | `pip install slack_bolt` 후 `SLACK_BOT_TOKEN`·`SLACK_APP_TOKEN` 설정 |
| 소스를 만들려다 409를 받았는데 목록에는 소스가 하나 더 있음 | `create_source`가 소스를 먼저 넣고 피드 추가에서 실패해도 되돌리지 않음(Step 2) | 목록에서 피드 없는 소스를 삭제 |
| `ELEVENSLAB_API_KEY`를 넣었는데 ElevenLabs 엔진이 키가 없다고 함 | 환경변수 이름이 철자 그대로 `ELEVENSLAB`이어야 함(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/tts_engine_selector.py:48`) | `ELEVENLABS_API_KEY`가 아니라 `ELEVENSLAB_API_KEY`로 설정 |
| 스크랩 단계에서 매번 실패, 생성기가 `No content could be scraped` | 스크랩 URL이 없어도 Chromium을 띄우므로 Playwright 브라우저가 없으면 실패(소스로 확인, 돌려 보지는 않음) | `python -m playwright install`(이 문서는 실행하지 않음) |
| 스케줄러를 켜자마자 작업이 실행돼 API 비용이 나감 | `last_run`이 빈 새 작업은 첫 점검에서 바로 대상이 됨(`advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/scheduler.py:192`) | 키를 넣기 전에는 스케줄러를 켜지 않는다 |
| `bootstrap_demo.py`가 "not empty. aborting" | `databases/`와 `podcasts/`가 비어 있어야 데모 zip을 풀음(소스로 확인, `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/bootstrap_demo.py:12-19`) | 백엔드를 처음 띄우기 전에 실행 — 이 문서는 GitHub에서 내려받는 이 스크립트를 실행하지 않음 |

Redis 없이 Studio 채팅을 보내 보는 명령은 아래와 같습니다. 약 1분 걸립니다.

```bash
uv run --no-project python -c "
import contextlib, io, logging, time
logging.disable(logging.CRITICAL)
from fastapi.testclient import TestClient
import main
c = TestClient(main.app)
print(c.post('/api/podcast-agent/session', json={}).status_code, len(c.get('/api/podcast-agent/languages').json()['languages']))
t = time.time()
with contextlib.redirect_stdout(io.StringIO()):
    r = c.post('/api/podcast-agent/chat', json={'session_id': 's1', 'message': 'hello'})
print(r.status_code, r.json()['stage'], r.json()['is_processing'], round(time.time() - t) > 30)
"
```

```text
200 100
500 error False True
```

Slack 연동 모듈을 import만 해 보는 명령은 아래와 같습니다.

```bash
uv run --no-project python -c "
try:
    import integrations.slack.chat
except Exception as e:
    print(type(e).__name__, e)
"
```

```text
ModuleNotFoundError No module named 'slack_bolt'
```

## 더 해보기

- 사본에서 `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/tools/embedding_search.py:22`의 식을 `1.0 - float(distance) / 2.0`으로 바꾸고 Step 5의 두 명령을 다시 돌려, 코사인 0.75짜리가 걸러지는지 확인해 보기
- `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/beifong/utils/rss_feed_parser.py:47`의 판정을 "`bozo`이고 항목이 하나도 없을 때만 거부"로 바꾸는 사본을 만들어, `&`가 든 피드에서 항목이 몇 개 살아나는지 Step 3 명령으로 확인해 보기
- Redis를 띄우고(`REDIS_HOST`·`REDIS_PORT` 확인) 별도 터미널에서 `python -m celery_worker`를 켠 뒤 Studio 채팅에서 메시지를 한 번 보내, 세션 상태가 `internal_sessions.db`에 쌓이는 모습을 표로 확인해 보기(OpenAI 키 필요)

## 다음 날 예고

[Day 099 · 🛡️ AI Agent Governance - Policy-Based Sandboxing](../day099-ai-agent-governance/README.md) — 에이전트가 도구를 실행하기 전에 정책으로 허용·거부·승인 대기를 가르고 감사 로그를 남기는 거버넌스 계층(앱 README 기준)을 봅니다.
