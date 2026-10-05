# 업스트림 동기화 절차

이 리포(`Zihun/awesome-llm-apps`)는 `Shubhamsaboo/awesome-llm-apps`의 포크입니다. 포크의 `main`에는 upstream에 없는 커밋이 쌓여 있습니다. 한국어 튜토리얼 시리즈(`docs/tutorials/`), uv 설정, `crewai_version/`, 일부 앱 수정이 그것입니다. 그래서 포크는 upstream과 똑같아질 수 없고, 동기화는 항상 **merge**로 합니다. rebase나 reset은 이미 origin에 올라간 포크 이력을 다시 쓰므로 쓰지 않습니다.

```
upstream/main ──merge──▶ 로컬 main ──push──▶ origin/main ──pull──▶ 다른 PC의 클론
(Shubhamsaboo)                                (Zihun, 포크)
```

| 리모트 | 주소 | 용도 |
|---|---|---|
| `origin` | `https://github.com/Zihun/awesome-llm-apps.git` | 포크. push 대상 |
| `upstream` | `https://github.com/Shubhamsaboo/awesome-llm-apps.git` | 원본. fetch만 한다 |

아래 명령은 PowerShell과 Git Bash 어느 쪽에서도 같습니다. 리포 루트에서 실행합니다.

## 0. 처음 한 번: upstream 리모트 등록

클론마다 한 번씩 합니다. `origin`은 클론할 때 생기지만 `upstream`은 직접 더해야 합니다.

```
git remote add upstream https://github.com/Shubhamsaboo/awesome-llm-apps.git
git remote -v
```

upstream에 실수로 push하는 일을 막으려면 push 주소를 막아 둡니다. 선택 사항입니다.

```
git remote set-url --push upstream no_push
```

## 방법 A. 로컬에서 merge한 뒤 push (권장)

들어올 변경을 미리 보고, 튜토리얼 점검까지 마친 다음에 포크에 올릴 수 있어서 권장합니다. 2026-10-05 동기화가 이 방법이었습니다.

**1. 로컬 main을 origin과 맞추고 기준 커밋을 적어 둡니다.**

```
git switch main
git status
git pull --ff-only origin main
git rev-parse --short HEAD
```

`git status`는 깨끗해야 합니다. 마지막 줄에 나온 커밋이 **동기화 직전의 main**입니다. 뒤에 나오는 점검(`sync-audit`)의 기준으로 씁니다.

**2. upstream을 가져와 들어올 것을 봅니다.**

```
git fetch upstream
git log --oneline main..upstream/main
git diff --stat main...upstream/main
git merge-tree --write-tree --name-only main upstream/main
```

- `main..upstream/main`(점 두 개)은 들어올 커밋 목록입니다.
- `main...upstream/main`(점 세 개)은 갈라진 지점부터 upstream이 바꾼 파일입니다.
- `git merge-tree`는 작업 트리를 건드리지 않고 병합을 미리 해 봅니다. 트리 해시 한 줄만 나오면 충돌이 없습니다. `CONFLICT` 줄이 나오면 그 파일들이 충돌합니다. 이때는 아래 "포크 고유 영역"을 먼저 보세요.

**3. merge합니다.**

```
git merge --no-ff upstream/main -m "Merge upstream/main (Shubhamsaboo/awesome-llm-apps) into fork main"
```

충돌이 나면 파일을 고친 뒤 `git add <파일>`, `git commit` 순서로 마칩니다. 중간에 그만두려면 `git merge --abort`를 실행합니다. 그러면 merge 직전 상태로 돌아갑니다.

**4. 튜토리얼을 점검합니다.** 아래 "동기화 후 점검" 절을 따릅니다. 문서를 고쳤다면 커밋합니다.

**5. 포크에 올립니다.**

```
git push origin main
```

## 방법 B. GitHub 웹 "Sync fork" 후 로컬에서 pull

2026-09-21 동기화가 이 방법이었습니다(`2eae68a` "Merge branch 'Shubhamsaboo:main' into main"). 웹에서 바로 끝나는 대신, 병합하기 전에 점검할 수 없습니다.

1. `https://github.com/Zihun/awesome-llm-apps`에서 **Sync fork → Update branch**를 누릅니다. 포크가 앞서 있으면 GitHub가 병합 커밋을 만듭니다. 충돌이 있으면 웹에서는 할 수 없으니 방법 A로 합니다.
   - ⚠ **"Discard N commits"는 누르지 않습니다.** 포크에만 있는 커밋(튜토리얼 전체)이 origin에서 사라집니다.
2. 기준 커밋을 적어 두고 로컬로 받습니다.

   ```
   git switch main
   git rev-parse --short HEAD
   git pull --ff-only origin main
   ```

   `--ff-only`가 실패하면 로컬에 아직 push하지 않은 커밋이 있다는 뜻입니다. 이때는 `git pull --no-rebase origin main`으로 받습니다. 병합 커밋이 하나 더 생기는데, `02b7970`이 그 예입니다. `git pull --rebase`는 쓰지 않습니다. upstream 병합 커밋을 풀어 헤쳐 이력이 엉킵니다.
3. "동기화 후 점검"을 하고, 고친 것이 있으면 커밋한 뒤 `git push origin main`을 실행합니다.

`gh repo sync`는 대상이 로컬이냐 원격이냐에 따라 동작이 다릅니다. 특히 `--force`는 포크 브랜치를 upstream으로 덮어씁니다(hard reset). 이 리포에서는 위 두 방법만 씁니다.

## 다른 PC나 클론에서 받기

포크에 올라간 결과는 평소처럼 pull로 받습니다.

```
git switch main
git pull --ff-only origin main
```

그 클론에서도 직접 동기화하려면 0단계(upstream 등록)를 먼저 합니다.

## 포크 고유 영역: 충돌이 나면 지켜야 할 것

포크가 바꾼 파일 전체는 언제든 아래 명령으로 다시 볼 수 있습니다. 목록이 바뀌었을 수 있으니 충돌이 나면 이 명령부터 실행합니다.

```
git diff --name-only upstream/main...main
```

2026-10-05 기준 목록입니다.

| 경로 | 무엇 | 충돌 시 원칙 |
|---|---|---|
| `README.md` | 포크가 더한 "📦 Getting Started with uv" 절 | upstream은 상단 배너, 스폰서, 앱 목록을 자주 고칩니다. upstream 변경을 받되 uv 절은 남깁니다 |
| `.gitignore` | `!docs/tutorials/_tools/lib/` 예외 | 이 줄을 남깁니다. 빠지면 튜토리얼 도구의 `lib/`가 커밋에서 빠집니다 |
| `pyproject.toml`, `uv.lock`, `UV_MIGRATION_GUIDE.md` | 포크의 uv 설정 | upstream에 없는 파일이라 보통 충돌하지 않습니다 |
| `docs/tutorials/`, `docs/superpowers/`, `.superpowers/`, `crewai_version/` | 튜토리얼 시리즈, 설계·원장, CrewAI 변환판 | upstream에 없는 경로입니다 |
| `starter_ai_agents/web_scraping_ai_agent/` | OpenAI·Gemini 확장, Windows Playwright 수정 | 포크 수정의 이유를 먼저 확인합니다(`git log upstream/main..main -- <경로>`). upstream 변경과 합칩니다 |
| `starter_ai_agents/xai_finance_agent/xai_finance_agent_multi_model.py`, `starter_ai_agents/ai_breakup_recovery_agent/`, `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1/`, `rag_tutorials/agentic_rag_embedding_gemma/`, `advanced_llm_apps/thinkpath_chatbot_app/package-lock.json`, `README.pdf` | 포크가 고치거나 더한 앱 파일 | 위와 같습니다. 튜토리얼이 이 파일들을 인용하므로, 합친 뒤에는 반드시 아래 점검을 합니다 |

## 동기화 후 점검 (튜토리얼)

튜토리얼은 앱 코드를 `경로:줄`로 인용하고, 일정(`days.json`)은 상위 README의 앱 목록을 따릅니다. 그래서 동기화가 끝나면 아래 세 가지를 확인합니다. 명령은 `docs/tutorials/_tools`에서 실행합니다.

```
cd docs/tutorials/_tools
npm run sync-audit -- <동기화 직전 main 커밋>
npm run check
npm test
```

**`npm run sync-audit`** 는 기준 커밋 이후 바뀐 파일로 두 가지를 봅니다. 방법 A로 merge한 직후라 HEAD가 병합 커밋이면 인자를 생략해도 됩니다(기본값 `HEAD^1`). 통과하면 exit 0, 찾은 것이 있으면 exit 1로 끝납니다.

| 출력 | 뜻 | 할 일 |
|---|---|---|
| `README에 있고 계획에 없음` | upstream이 README에 앱을 새로 실었는데 `days.json`에 없습니다 | 아래 규칙대로 `days.json`에 끼웁니다 |
| `계획에 있고 디스크에 없음` | upstream이 앱을 옮기거나 지웠습니다 | 새 경로를 찾아 `days.json`을 고칩니다. 이미 쓴 일차라면 문서도 고칩니다 |
| `원본 앱에서 바뀜` / `인용한 경로가 바뀜` | 이미 쓴 일차가 다루는 코드가 바뀌었습니다 | 그 일차의 줄 번호 인용, 코드 발췌, 명령, 기대 출력을 다시 확인합니다 |

**`npm run check`** 는 이미 쓴 일차에서 0건이어야 합니다. 아직 쓰지 않은 골격 일차의 "링크 대상 없음"(SVG 없음)과 "미작성 표시 남음"은 정상입니다.

**`days.json`에 앱을 끼우는 규칙**(설계 문서 `docs/superpowers/specs/2026-09-11-tutorial-series-design.md` §2·§3)은 다음과 같습니다.

- 폴더가 이미 있는 일차의 번호와 폴더명은 바꾸지 않습니다(링크 안정성). 폴더가 아직 없는 구간에서만 끼우고 그 뒤를 다시 번호 매깁니다.
- 볼륨 안에서는 코드 규모(`.py/.ts/.tsx/.js/.jsx` 줄 수 합계) 오름차순입니다.
- 들어갈 볼륨이 폴더가 있는 구간이면 그 볼륨 끝에 붙이거나 새 볼륨을 만듭니다. 2026-09-21 확장이 그 예입니다.
- 바꾼 뒤에는 `npm run roadmap`으로 로드맵을 다시 만들고, `npm test`를 돌립니다. 설계 문서의 합계 문구와 부록 A도 고칩니다.
- 무엇을 왜 바꿨는지 원장 `.superpowers/sdd/2026-09-11-tutorial-series/progress.md`의 "▶ 재개 지점"에 남깁니다.

## 주의

- **루트 `.venv`에 `uv sync`를 하지 않습니다.** 이 venv에는 lock에 없는 패키지(`scrapegraphai`, `playwright`, `langchain-google-genai` 등)가 일부러 들어 있습니다. lock에 맞추면 Day 002 앱이 깨집니다. 동기화로 앱의 `requirements.txt`가 바뀌어도 루트 venv는 그대로 두고, 확인은 별도 venv에서 합니다.
- upstream에는 push하지 않습니다. 포크에 올리는 것은 `origin`뿐입니다.

## 동기화 기록

| 날짜 | 방법 | 병합 커밋 | 들어온 것 | 튜토리얼 영향 |
|---|---|---|---|---|
| 2026-09-10 | 로컬 merge | `edcdc65` | 설계 문서의 기준점 | 시리즈 시작 전 |
| 2026-09-21 | 웹 Sync fork + pull | `2eae68a`, `02b7970` | Needle, LLM Panel Agent Team(신규), Insurance Claim Live Agent Team 개편 | 작성된 Day 1–20 영향 없음. 계획 133 → 164일 |
| 2026-10-05 | 로컬 merge | `82201be` | Ripple(신규), agent_skills registry·lint·CI, Self-Improving Agent Skills 모델 선택, Insurance Claim 라이브 아바타, TinyFish 스폰서 배너 | 작성된 Day 1–99 영향 없음. 계획 164 → 167일(Thinking Out Loud, First Reader, Ripple) |
