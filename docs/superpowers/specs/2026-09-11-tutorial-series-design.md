# awesome-llm-apps 133일 튜토리얼 시리즈 설계

작성일: 2026-09-11 · 상태: 검토 대기 · 대상 리포: Zihun/awesome-llm-apps (upstream Shubhamsaboo/awesome-llm-apps 2026-09-10 동기화 기준, 병합 커밋 `edcdc65`)

## 1. 목적과 범위

**목적.** 이 리포에 있는 모든 앱을 하루에 하나씩, 처음부터 끝까지 따라 만들 수 있는 상세 튜토리얼 문서 시리즈를 만든다. 매 일차는 앱의 완성 아키텍처와 각 진행 단계의 시스템 구성을 D2 다이어그램으로 도식화해서, 독자가 "지금 무엇을 어디에 붙이고 있는지"를 그림으로 확인하며 따라오게 한다.

**범위.**

- README 목록 116개 항목 중 외부 리포 링크 2개(Openwork, OpenSource Voice Dictation Agent)는 코드가 이 리포에 없으므로 제외한다. 로드맵에 링크만 남긴다.
- AI Agent Framework Crash Course 2개는 레슨 단위로 풀어 21일(Google ADK 10, OpenAI Agents SDK 11)로 다룬다.
- 합계 **133일**. 전체 일정은 부록 A에 있다.

**대상 독자.** Python 기초와 터미널 사용이 가능하고, LLM 앱 개발은 처음인 개발자. Node.js가 필요한 볼륨(Generative UI)은 해당 일차에서 설치부터 안내한다.

**언어.** 본문은 한국어. 코드, 명령, 파일명, 식별자, 에러 메시지는 원문 그대로 둔다.

**비범위.**

- 앱 코드를 수정하거나 새로 쓰지 않는다. 리포의 실제 코드를 발췌해 설명한다. 알려진 결함(폐기된 API 등)은 고치지 않고 "문제 해결" 절에 적는다.
- 실행 결과 스크린샷은 넣지 않는다. 기대 출력은 텍스트로 적는다.
- 영어판은 만들지 않는다.

## 2. 확정된 결정

| 항목 | 결정 | 이유 |
|---|---|---|
| 문서 형식 | 리포 안 Markdown, `docs/tutorials/` | GitHub에서 바로 읽히고 fork에 영구 보관됨 |
| 다이어그램 | D2 (`@terrastruct/d2` npm 패키지로 로컬 렌더), `.d2` 소스와 렌더된 `.svg`를 함께 커밋 | Mermaid 대체. 텍스트 기반이라 수백 장을 일관되게 만들고 고칠 수 있음. SVG를 커밋해 두면 뷰어 쪽에 도구가 필요 없음 |
| 구조 | 하루 = 폴더 하나 (`dayNNN-slug/README.md` + `diagrams/`) | 파일이 작아 리뷰와 수정이 쉽고 하루 단위 진도가 명확함 |
| 순서 | 난이도 순 15볼륨. 볼륨 안에서는 코드 규모(줄 수) 오름차순. 예외: Chat with Gmail은 Google OAuth 설정 부담 때문에 볼륨 끝 | 작은 앱에서 패턴을 익히고 큰 앱으로 감 |
| 커밋 | 볼륨 단위로 `main`에 커밋. 푸시는 사용자가 요청할 때만 | 사용자 결정 |
| 첫 산출물 | 스캐폴딩 + Day 1 완성본을 먼저 만들어 검토받은 뒤 확장 | 톤, 깊이, 그림 스타일을 133일에 복제하기 전에 맞춤 |

## 3. 폴더 구조

```
docs/tutorials/
├── README.md                     # 133일 로드맵: 볼륨별 표(일차·앱·난이도·링크), 진도 체크박스, 공통 사전 준비
├── _tools/
│   ├── package.json              # @terrastruct/d2 devDependency, scripts: render / check / test / scaffold / roadmap
│   ├── render.mjs                # **/diagrams/*.d2 → 같은 이름 .svg
│   ├── check.mjs                 # 문서·다이어그램 정합성 검사
│   ├── theme.d2                  # 공통 색·도형 클래스
│   ├── days.json                 # 133일 일정 데이터(부록 A와 동일). 로드맵·스캐폴딩의 원천
│   ├── scaffold.mjs              # dayNNN-slug/ 폴더와 README 골격, diagrams/ 생성
│   ├── roadmap.mjs               # roadmap.template.md + days.json + 진도 → README.md 생성
│   ├── roadmap.template.md       # 로드맵의 고정 본문(소개, 공통 사전 준비). <!-- DAYS --> 자리에 표가 들어감
│   ├── lib/                      # 스크립트가 공유하는 모듈 (d2.mjs, days.mjs, check.mjs)
│   └── test/                     # node --test 로 도는 도구 테스트
├── day001-xai-finance-agent/
│   ├── README.md
│   └── diagrams/
│       ├── overview.d2  overview.svg
│       ├── step1.d2     step1.svg
│       ├── …
│       └── sequence.d2  sequence.svg
└── day002-… (총 133개 폴더)
```

- 폴더 이름은 `day` + 3자리 일차 + `-` + 슬러그. 슬러그는 원본 앱 폴더명을 소문자·하이픈으로 바꾼 것이며, Generative UI 볼륨은 `genui-` 접두사를 붙여 같은 이름의 Python 앱과 구분한다. 크래시 코스는 `adk-N-…`, `openai-sdk-N-…` 형식이다. 전체 목록은 부록 A에 고정되어 있고, 한 번 커밋된 일차 번호와 폴더명은 바꾸지 않는다(링크 안정성).
- `node_modules/`는 이미 `.gitignore`에 있다. `_tools/package-lock.json`은 커밋한다.

## 4. 하루 문서 템플릿

모든 일차의 `README.md`는 아래 골격을 그대로 따른다. H2 제목 문자열은 `check.mjs`가 검사하므로 바꾸지 않는다.

```markdown
# Day NNN · {앱 이름}

> 볼륨 {n} {볼륨명} · 난이도 ★★☆ · 예상 소요 {60~90}분 · API 비용 대략 {$0.1 이하 / 무료(로컬)} · 원본 앱: `{원본 경로}`

## 오늘 만들 것
한 문단으로 완성물과 배우는 개념. 이어서 완성 아키텍처 그림.
![완성 아키텍처](diagrams/overview.svg)

## 사전 준비
| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
공통 준비(uv, Python 버전)는 로드맵 README 링크로 대신하고, 이 앱에만 필요한 것만 적는다.

## 아키텍처 한눈에 보기
| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
코드 위치는 `path/file.py:시작-끝` 형식.

## 단계별 진행
### Step 1. {제목}
**목적.** 한두 문장.
**할 일.** 명령 또는 코드 발췌(파일 경로와 줄 범위 명시).
![Step 1까지의 구성](diagrams/step1.svg)
**확인.** 실행할 명령과 기대 출력.
### Step 2. … (5~8개)

## 요청 한 건이 흐르는 과정
![요청 시퀀스](diagrams/sequence.svg)
시퀀스 해설.

## 실행 체크리스트
- [ ] 항목

## 문제 해결
| 증상 | 원인 | 해결 |
|---|---|---|
리포 코드의 알려진 문제(폐기된 API, 모델명 변경 등) 포함.

## 더 해보기
심화 과제 2~3개.

## 다음 날 예고
다음 일차 링크와 한 줄 소개. (Day 133은 시리즈 마무리로 대체)
```

**스텝 설계 규칙.**

- 스텝은 앱의 실제 구조를 따른다. 보통 환경 구성 → 모델·에이전트 정의 → 도구 연결 → 프롬프트/지시문 → UI → 실행 순이며, 앱마다 5~8개.
- 모든 스텝은 목적, 할 일, 이 단계까지의 다이어그램, 확인의 4요소로 끝난다. 확인은 독자가 실제로 실행할 수 있는 것이어야 한다(파일 존재 확인, `uv run python -c "import …"`, 앱 기동 후 화면 요소 확인 등).
- 코드 발췌는 리포의 실제 파일에서 가져오고 경로와 줄 범위를 적는다. 발췌를 고쳐 쓰지 않는다.
- 명령은 uv 기준으로 쓰고 pip 대안을 한 줄 덧붙인다. 앱 폴더의 `requirements.txt`가 있으면 `uv pip install -r requirements.txt`, 없으면 로드맵 README의 공통 설치 안내로 보낸다.
- 난이도 기준: ★ 키 1개 이하·단일 파일·외부 서비스 없음, ★★ 도구나 외부 API 1~2개·다중 파일, ★★★ 멀티 에이전트·프론트엔드·인프라(DB, 큐, 배포) 포함.
- 예상 소요 시간과 비용은 대략치임을 문구로 밝힌다.
- 분량 기준: 본문 1,000~1,500단어(한국어) + 코드 발췌. 60~90분 안에 끝나도록 한다. 새로 가르치는 내용이 많은 날은 이 범위를 넘어도 되지만, 되풀이 때문에 넘는 것은 안 된다. 자주 나오는 되풀이 두 가지는 (1) 앞선 일차가 이미 가르친 사실을 다시 확인 블록으로 증명하는 것, (2) 앞 스텝에서 밝힌 사실을 뒤 스텝에서 길게 다시 설명하는 것이다. 둘 다 한 문장으로 줄이고 앞을 가리킨다.
- "직접 확인"은 그 일차 보고서에 명령과 출력이 그대로 남아 있는 것에만 붙인다. 소스를 읽어서 안 것은 "소스로 확인"이라고 적고 어느 파일인지 밝힌다. 실행해 보지 못한 것은 그렇다고 적는다.
- 파일의 줄 수를 본문에 적을 때는 독자가 편집기나 GitHub에서 보게 될 숫자를 적는다. 마지막 줄에 개행이 없는 파일은 `wc -l`이 한 줄 적게 세므로 그대로 옮기면 어긋난다.

**볼륨별 특이사항.**

- Crash Courses(볼륨 2): 레슨마다 하루. 레슨 README가 있으면 그 흐름을 따르되 이 템플릿으로 재구성한다.
- Generative UI(볼륨 11): Node.js 20+ 설치 스텝을 포함하고, 백엔드(Python)와 프론트엔드(Next.js) 스텝을 분리한다. 다이어그램에 두 프로세스와 그 사이 API 경계를 그린다.
- Always-on(볼륨 12): 스케줄러·웹훅·메일 발송 구성을 배포 다이어그램(`extra-deploy`)으로 추가한다.
- Fine-tuning(볼륨 14): GPU 또는 Colab 필요를 사전 준비에 명시한다.
- Agent Skills(볼륨 15): Python 앱이 아니라 코딩 에이전트용 스킬 파일이다. 설치(`npx skills add …`), 호출, 스킬이 하는 일의 흐름을 다이어그램으로 다룬다.
- 코드가 매우 큰 앱(예: Day 88, Day 101, 볼륨 11)은 핵심 파일만 다루고, 나머지는 컴포넌트 표에서 역할만 적는다.

## 5. 다이어그램 규격

**하루 세트.**

| 파일 | 내용 | 수 |
|---|---|---|
| `overview.d2` | 완성 아키텍처. 사용자, UI, 에이전트, 도구, LLM, 외부 API, 저장소를 컨테이너와 라벨 달린 화살표로 | 1 |
| `stepK.d2` | overview와 같은 배치. 이번 스텝에 추가된 요소는 `new` 클래스, 이전 것은 기본, 아직 안 만든 것은 `todo` 클래스로 흐리게. 스텝을 넘길수록 그림이 채워짐 | 스텝 수 |
| `sequence.d2` | 요청 하나가 사용자 → UI → 에이전트 → 도구/LLM → 응답으로 흐르는 시퀀스(`shape: sequence_diagram`) | 1 |
| `extra-{이름}.d2` | 필요할 때만: 상태 기계(CRAG, LangGraph), 인덱스 데이터 모델(RAG), 배포 구성(Always-on) | 0~2 |

**테마 `_tools/theme.d2`.** 모든 `.d2`는 첫 줄에서 테마를 가져온다. 기본 클래스 다섯 개와 각각의 `-new`, `-todo` 변형까지 15개로 고정한다.

| 클래스 | 용도 | 표현 |
|---|---|---|
| `person` | 사용자 | `shape: person` |
| `ours` | 이 리포의 코드(앱, 에이전트, 도구 함수) | 파란 채움 사각형 |
| `ext` | 외부 API, LLM 제공자 | 회색 `shape: cloud` |
| `store` | DB, 벡터 저장소, 캐시 | 초록 `shape: cylinder` |
| `file` | 파일, 문서, 설정 | `shape: page` |
| `<기본>-new` (예: `ours-new`) | 이번 스텝에서 추가된 요소 | 기본 모양·채움 그대로, 주황 굵은 테두리 |
| `<기본>-todo` (예: `ext-todo`) | 아직 만들지 않은 요소 | 기본 모양·채움 그대로, 점선, 낮은 불투명도 |

`stepK.d2`는 `...@overview`로 배치를 가져온 뒤 `app.agent.class: ours-new`처럼 **단일 클래스**로 덧씌운다. 배열 덧씌우기(`x.class: [ours; new]`)는 선언 뒤에 오면 사용 중인 렌더러가 무시하므로 쓰지 않는다(2026-09-11 확인).

- 레이아웃은 ELK, 방향은 `direction: right`가 기본이고 세로가 자연스러운 경우 `down`. 손그림(`sketch`)은 쓰지 않는다.
- 라벨은 "한국어 역할 (식별자)" 형식. 예: `여행 에이전트 (travel_agent.py)`, `검색 도구 (SerpApiTools)`.
- 화살표 라벨에는 오가는 데이터를 적는다. 예: `질문 텍스트`, `JSON 결과`.
- 색은 밝은 배경 기준으로 정하고, 색 외에 도형과 테두리 스타일로도 구분되게 한다.
- 한 그림의 노드는 12개 이하. 넘치면 컨테이너로 묶는다.
- 렌더된 `.svg`의 너비는 1400px 이하여야 한다. GitHub 본문 폭(약 880px)에서 축소돼도 라벨이 읽히는 한계선이다. 넘으면 `direction: down`으로 바꾸거나 노드를 컨테이너로 묶는다. `check.mjs`가 검사한다.

**렌더 결과.** `.svg`는 같은 폴더에 같은 이름으로 저장하고 커밋한다. README는 `![설명](diagrams/이름.svg)`로 참조한다.

## 6. 도구 파이프라인

`_tools/package.json`

```json
{
  "name": "awesome-llm-apps-tutorial-tools",
  "private": true,
  "type": "module",
  "scripts": {
    "render": "node render.mjs",
    "check": "node check.mjs",
    "scaffold": "node scaffold.mjs",
    "roadmap": "node roadmap.mjs",
    "test": "node --test --test-force-exit"
  },
  "devDependencies": { "@terrastruct/d2": "^0.1.33" }
}
```

**`render.mjs`.**

- 인자 없음: `docs/tutorials/day*/diagrams/*.d2` 전부. 인자 `day001` 등: 그 폴더만. `--force`: 변경 여부와 상관없이 전부 다시 렌더.
- 변경 감지는 mtime이 아니라 해시로 한다(git checkout은 mtime을 보존하지 않으므로). 렌더할 때 import를 펼친 최종 소스의 SHA-256을 `<!-- d2-source-sha256: … -->` 주석으로 SVG의 `</svg>` 바로 앞에 넣고, 다음 실행 때 같은 해시면 건너뛴다. 테마가 바뀌면 해시가 바뀌므로 모든 그림이 다시 렌더된다.
- import는 render.mjs가 텍스트로 펼친다. `...@경로` 한 줄을 그 파일(`.d2` 확장자 생략 가능, 경로는 그 파일 기준 상대 경로)의 내용으로 치환하며 재귀 import와 순환을 처리한다. 일차 폴더의 `.d2`는 첫 줄에 `...@../../_tools/theme`를 쓰고, `stepK.d2`는 `...@overview`로 배치를 그대로 가져온 뒤 클래스만 덧씌운다(`app.agent.class: ours-new`). 이 문법은 D2 CLI에서도 그대로 유효하다.
- D2의 ELK 레이아웃 워커가 Node 이벤트 루프를 붙잡아 프로세스가 스스로 끝나지 않으므로 `render.mjs`는 마지막에 `process.exit(code)`를 호출하고, 테스트는 `node --test --test-force-exit`로 돌린다.
- 컴파일 옵션: `layout: "elk"`, `sketch: false`, `pad: 20`, `noXMLTag: true`.
- 실패한 파일은 이름과 오류를 출력하고 마지막에 exit 1.

**`check.mjs`.** 다음을 검사하고 하나라도 실패하면 exit 1.

1. 모든 `day*/README.md`에 4절의 H2 제목 9개가 순서대로 있다(Day 133은 "다음 날 예고" 생략 허용).
2. README가 참조하는 상대 링크와 이미지 파일이 존재한다.
3. `diagrams/*.d2`마다 짝이 되는 `.svg`가 있고, `.svg` 안의 `d2-source-sha256` 주석이 현재 소스(import를 펼친 것)의 해시와 같다(다르면 "stale").
4. 본문의 코드 위치 표기 `` `경로:시작-끝` ``이 실제 파일을 가리키고 줄 범위가 파일 길이 안에 있다.
5. mermaid 코드 펜스가 없다.
6. 로드맵 README에 일차 행이 133개 있고, 링크가 걸린 일차는 모두 존재하는 폴더를 가리킨다. (로드맵은 폴더가 있는 일차에만 링크를 걸고, 아직 없는 일차는 링크 없이 나열한다.)
7. 골격의 미작성 표시 `(작성 필요)`가 본문에 남아 있지 않다. (`scaffold.mjs`가 만든 골격의 빈칸 표시. `roadmap.mjs`도 이 문자열이 없는 일차만 완료로 센다.)
8. 렌더된 `.svg`의 너비가 1400px 이하다.
9. 코드 발췌가 바로 앞에서 인용한 줄 범위와 정확히 일치한다.
10. 펜스 바깥의 각 줄은 백틱(`` ` ``) 개수가 짝수다(홀수면 코드 스팬이 안 닫혀 표가 깨진 것). 표 안에서 오류 문구를 인용할 때 특히 자주 깨진다(2026-09-12 Day 6 문제 해결 표에서 발견).
11. 코드 위치 인용에 파일 경로가 들어 있다(줄 번호만 남은 `:12-15` 형태는 오류). 펜스 밖에서 같은 줄이 소스 파일을 언급할 때만 검사한다(슬라이스·시각 표기 오탐 방지).

실행: `cd docs/tutorials/_tools && npm install && npm run render && npm run check`.

## 7. 제작 순서와 커밋 규칙

1. **스캐폴딩.** 로드맵 README, `_tools` 일체, Day 1 완성본을 만들고 렌더·검사를 통과시킨 뒤 커밋한다. 도구는 작업 단위마다 따로 커밋해도 된다. 마지막 커밋 메시지: `docs(tutorials): scaffold 133-day series and Day 1`.
2. **검토.** 사용자가 Day 1의 톤, 깊이, 그림 스타일을 보고 조정 사항을 준다. 조정을 템플릿과 테마에 반영한 뒤 확장한다.
3. **볼륨 제작.** 볼륨 1부터 순서대로. 볼륨마다 커밋 하나. 메시지: `docs(tutorials): Volume {n} {볼륨명}, Day {a}-{b}`. 큰 볼륨(21일)은 중간 커밋을 허용한다.
4. **진도 기록.** 로드맵 README의 체크박스를 완료된 일차만큼 채운다. 새 세션은 로드맵과 이 문서를 먼저 읽고 이어간다.
5. **푸시.** 사용자가 요청할 때만 `git push origin main`.

## 8. 검증 (완료 기준)

일차 하나를 "완료"라고 부르려면 아래가 모두 그 시점에 실제로 확인되어야 한다.

- `npm run render`가 exit 0으로 끝나고 `.d2`마다 `.svg`가 있다.
- `npm run check`가 exit 0.
- 문서의 모든 명령은 앱의 README, `requirements.txt`, 실제 엔트리 파일과 대조했다(파일명과 경로가 존재함을 확인).
- API 키가 필요한 앱은 실행하지 않는다. 키 없이 가능한 확인(의존성 설치, `python -m py_compile`, `--help`)만 실행하고 그 결과를 문서의 "확인" 항목에 반영한다.

볼륨 하나를 완료하려면 추가로:

- 그 볼륨의 SVG 중 최소 3장을 브라우저로 열어 배치, 라벨 겹침, 한글 렌더링을 눈으로 확인한다.
- 로드맵 README의 해당 볼륨 체크박스와 링크를 갱신한다.

## 9. 위험과 대응

| 위험 | 대응 |
|---|---|
| upstream 동기화로 앱 코드가 바뀌어 줄 번호 참조가 어긋남 | `check.mjs`가 줄 범위 초과를 잡는다. 동기화 후에는 `npm run check`를 돌리고 어긋난 참조를 고친다. 코드 발췌는 줄 번호보다 함수·변수 이름을 기준으로 설명해 어긋나도 찾을 수 있게 한다 |
| 일부 앱이 폐기된 라이브러리 API를 쓰거나 현재 실행되지 않음 | 고치지 않고 "문제 해결" 절에 증상과 우회법을 적는다. 문서 상단 난이도 옆에 ⚠ 표시 |
| 대형 앱(수천~수만 줄)은 하루 분량을 넘음 | 핵심 파일과 요청 경로 하나만 다루고 나머지는 컴포넌트 표에 역할만 적는다 |
| D2 JS 렌더러의 import 처리 불확실 | render.mjs가 import를 텍스트로 펼치므로 렌더러의 import 지원에 의존하지 않는다(6절) |
| 다이어그램 수가 많아(약 900장) 일관성이 무너짐 | 정해진 테마 클래스 15개만 사용, `check.mjs`가 파일 세트 누락을 잡음, 볼륨마다 육안 표본 검사 |
| D2 렌더러 프로세스가 끝나지 않아 자동화가 멈춤 | 렌더 스크립트는 `process.exit`, 테스트는 `--test-force-exit`, 출력은 파이프 대신 파일로 |
| API 비용 | 문서에 대략치를 적고 로컬 모델 대안이 있는 앱은 함께 안내 |

## 부록 A. 133일 전체 일정

일차 번호와 폴더명은 여기서 고정한다. 코드 규모는 정렬 근거로 쓴 `.py/.ts/.tsx/.js/.jsx` 줄 수 합계다.

### 볼륨 1. 🌱 Starter AI Agents (Day 1–13, 13일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 001 | 📊 xAI Finance Agent | `starter_ai_agents/xai_finance_agent` | `day001-xai-finance-agent` | 24 |
| 002 | 🕸️ Web Scraping AI Agent | `starter_ai_agents/web_scraping_ai_agent` | `day002-web-scraping-ai-agent` | 76 |
| 003 | 🎙️ AI Blog to Podcast Agent | `starter_ai_agents/ai_blog_to_podcast_agent` | `day003-ai-blog-to-podcast-agent` | 87 |
| 004 | 🎵 AI Music Generator Agent | `starter_ai_agents/ai_music_generator_agent` | `day004-ai-music-generator-agent` | 94 |
| 005 | 🔄 Mixture of Agents | `starter_ai_agents/mixture_of_agents` | `day005-mixture-of-agents` | 103 |
| 006 | 📊 AI Data Analysis Agent | `starter_ai_agents/ai_data_analysis_agent` | `day006-ai-data-analysis-agent` | 121 |
| 007 | 😂 AI Meme Generator Agent (Browser) | `starter_ai_agents/ai_meme_generator_agent_browseruse` | `day007-ai-meme-generator-agent-browseruse` | 139 |
| 008 | 🩻 AI Medical Imaging Agent | `starter_ai_agents/ai_medical_imaging_agent` | `day008-ai-medical-imaging-agent` | 158 |
| 009 | ✨ Gemini Multimodal Agent | `starter_ai_agents/multimodal_ai_agent` | `day009-multimodal-ai-agent` | 167 |
| 010 | 💸 AI x402 Paying Agent | `starter_ai_agents/ai_x402_paying_agent` | `day010-ai-x402-paying-agent` | 257 |
| 011 | ❤️‍🩹 AI Breakup Recovery Agent | `starter_ai_agents/ai_breakup_recovery_agent` | `day011-ai-breakup-recovery-agent` | 282 |
| 012 | 🛫 AI Travel Agent (Local & Cloud) | `starter_ai_agents/ai_travel_agent` | `day012-ai-travel-agent` | 312 |
| 013 | 🔍 OpenAI Research Agent | `starter_ai_agents/openai_research_agent` | `day013-openai-research-agent` | 331 |

### 볼륨 2. 🧑‍🏫 Crash Courses (Day 14–34, 21일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 014 | Google ADK Crash Course · 1_starter_agent | `ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent` | `day014-adk-1-starter-agent` | 27 |
| 015 | Google ADK Crash Course · 2_model_agnostic_agent | `ai_agent_framework_crash_course/google_adk_crash_course/2_model_agnostic_agent` | `day015-adk-2-model-agnostic-agent` | 78 |
| 016 | Google ADK Crash Course · 3_structured_output_agent | `ai_agent_framework_crash_course/google_adk_crash_course/3_structured_output_agent` | `day016-adk-3-structured-output-agent` | 78 |
| 017 | Google ADK Crash Course · 4_tool_using_agent | `ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent` | `day017-adk-4-tool-using-agent` | 1367 |
| 018 | Google ADK Crash Course · 5_memory_agent | `ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent` | `day018-adk-5-memory-agent` | 276 |
| 019 | Google ADK Crash Course · 6_callbacks | `ai_agent_framework_crash_course/google_adk_crash_course/6_callbacks` | `day019-adk-6-callbacks` | 890 |
| 020 | Google ADK Crash Course · 7_plugins | `ai_agent_framework_crash_course/google_adk_crash_course/7_plugins` | `day020-adk-7-plugins` | 171 |
| 021 | Google ADK Crash Course · 8_simple_multi_agent | `ai_agent_framework_crash_course/google_adk_crash_course/8_simple_multi_agent` | `day021-adk-8-simple-multi-agent` | 88 |
| 022 | Google ADK Crash Course · 9_multi_agent_patterns | `ai_agent_framework_crash_course/google_adk_crash_course/9_multi_agent_patterns` | `day022-adk-9-multi-agent-patterns` | 751 |
| 023 | Google ADK Crash Course · adk_yaml_examples | `ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples` | `day023-adk-10-adk-yaml-examples` | 2 |
| 024 | OpenAI Agents SDK Crash Course · 1_starter_agent | `ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent` | `day024-openai-sdk-1-starter-agent` | 218 |
| 025 | OpenAI Agents SDK Crash Course · 2_structured_output_agent | `ai_agent_framework_crash_course/openai_sdk_crash_course/2_structured_output_agent` | `day025-openai-sdk-2-structured-output-agent` | 603 |
| 026 | OpenAI Agents SDK Crash Course · 3_tool_using_agent | `ai_agent_framework_crash_course/openai_sdk_crash_course/3_tool_using_agent` | `day026-openai-sdk-3-tool-using-agent` | 414 |
| 027 | OpenAI Agents SDK Crash Course · 4_running_agents | `ai_agent_framework_crash_course/openai_sdk_crash_course/4_running_agents` | `day027-openai-sdk-4-running-agents` | 1031 |
| 028 | OpenAI Agents SDK Crash Course · 5_context_management | `ai_agent_framework_crash_course/openai_sdk_crash_course/5_context_management` | `day028-openai-sdk-5-context-management` | 84 |
| 029 | OpenAI Agents SDK Crash Course · 6_guardrails_validation | `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation` | `day029-openai-sdk-6-guardrails-validation` | 158 |
| 030 | OpenAI Agents SDK Crash Course · 7_sessions | `ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions` | `day030-openai-sdk-7-sessions` | 911 |
| 031 | OpenAI Agents SDK Crash Course · 8_handoffs_delegation | `ai_agent_framework_crash_course/openai_sdk_crash_course/8_handoffs_delegation` | `day031-openai-sdk-8-handoffs-delegation` | 308 |
| 032 | OpenAI Agents SDK Crash Course · 9_multi_agent_orchestration | `ai_agent_framework_crash_course/openai_sdk_crash_course/9_multi_agent_orchestration` | `day032-openai-sdk-9-multi-agent-orchestration` | 890 |
| 033 | OpenAI Agents SDK Crash Course · 10_tracing_observability | `ai_agent_framework_crash_course/openai_sdk_crash_course/10_tracing_observability` | `day033-openai-sdk-10-tracing-observability` | 648 |
| 034 | OpenAI Agents SDK Crash Course · 11_voice | `ai_agent_framework_crash_course/openai_sdk_crash_course/11_voice` | `day034-openai-sdk-11-voice` | 1065 |

### 볼륨 3. 💬 Chat with X (Day 35–40, 6일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 035 | 📝 Chat with Substack | `advanced_llm_apps/chat_with_X_tutorials/chat_with_substack` | `day035-chat-with-substack` | 42 |
| 036 | 📚 Chat with Research Papers (ArXiv) (GPT & Llama3) | `advanced_llm_apps/chat_with_X_tutorials/chat_with_research_papers` | `day036-chat-with-research-papers` | 54 |
| 037 | 💬 Chat with GitHub (GPT & Llama3) | `advanced_llm_apps/chat_with_X_tutorials/chat_with_github` | `day037-chat-with-github` | 108 |
| 038 | 📄 Chat with PDF (GPT & Llama3) | `advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf` | `day038-chat-with-pdf` | 148 |
| 039 | 📽️ Chat with YouTube Videos | `advanced_llm_apps/chat_with_X_tutorials/chat_with_youtube_videos` | `day039-chat-with-youtube-videos` | 354 |
| 040 | 📨 Chat with Gmail | `advanced_llm_apps/chat_with_X_tutorials/chat_with_gmail` | `day040-chat-with-gmail` | 40 |

### 볼륨 4. 📀 RAG (Day 41–61, 21일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 041 | 🦙 Local RAG Agent | `rag_tutorials/local_rag_agent` | `day041-local-rag-agent` | 43 |
| 042 | 🔄 Llama 3.1 Local RAG | `rag_tutorials/llama3.1_local_rag` | `day042-llama3.1-local-rag` | 81 |
| 043 | 🔍 Autonomous RAG | `rag_tutorials/autonomous_rag` | `day043-autonomous-rag` | 145 |
| 044 | 🔥 Agentic RAG with Embedding Gemma | `rag_tutorials/agentic_rag_embedding_gemma` | `day044-agentic-rag-embedding-gemma` | 152 |
| 045 | 🧩 RAG-as-a-Service | `rag_tutorials/rag-as-a-service` | `day045-rag-as-a-service` | 190 |
| 046 | ⛓️ Basic RAG Chain | `rag_tutorials/rag_chain` | `day046-rag-chain` | 200 |
| 047 | 👀 Hybrid Search RAG (Cloud) | `rag_tutorials/hybrid_search_rag` | `day047-hybrid-search-rag` | 215 |
| 048 | 🧐 Agentic RAG with Reasoning | `rag_tutorials/agentic_rag_with_reasoning` | `day048-agentic-rag-with-reasoning` | 251 |
| 049 | 🖥️ Local Hybrid Search RAG | `rag_tutorials/local_hybrid_search_rag` | `day049-local-hybrid-search-rag` | 258 |
| 050 | 🩺 RAG Failure Diagnostics Clinic | `rag_tutorials/rag_failure_diagnostics_clinic` | `day050-rag-failure-diagnostics-clinic` | 300 |
| 051 | ✨ RAG Agent with Cohere | `rag_tutorials/rag_agent_cohere` | `day051-rag-agent-cohere` | 320 |
| 052 | 🔄 Contextual AI RAG Agent | `rag_tutorials/contextualai_rag_agent` | `day052-contextualai-rag-agent` | 329 |
| 053 | 📰 AI Blog Search (RAG) | `rag_tutorials/ai_blog_search` | `day053-ai-blog-search` | 383 |
| 054 | 📠 RAG with Database Routing | `rag_tutorials/rag_database_routing` | `day054-rag-database-routing` | 388 |
| 055 | 🔄 Corrective RAG (CRAG) | `rag_tutorials/corrective_rag` | `day055-corrective-rag` | 469 |
| 056 | 🤔 Gemini Agentic RAG | `rag_tutorials/gemini_agentic_rag` | `day056-gemini-agentic-rag` | 473 |
| 057 | 🕸️ Knowledge Graph RAG with Citations | `rag_tutorials/knowledge_graph_rag_citations` | `day057-knowledge-graph-rag-citations` | 525 |
| 058 | 🐋 Deepseek Local RAG Agent | `rag_tutorials/deepseek_local_rag_agent` | `day058-deepseek-local-rag-agent` | 526 |
| 059 | 🖼️ Vision RAG | `rag_tutorials/vision_rag` | `day059-vision-rag` | 554 |
| 060 | 📎 Typed Agentic RAG with Pydantic AI | `rag_tutorials/agentic_typed_rag_pydanticai` | `day060-agentic-typed-rag-pydanticai` | 1229 |
| 061 | 🧬 Multimodal Agentic RAG | `rag_tutorials/multimodal_agentic_rag` | `day061-multimodal-agentic-rag` | 1618 |

### 볼륨 5. 💾 LLM Apps with Memory (Day 62–67, 6일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 062 | 💬 Llama3 Stateful Chat | `advanced_llm_apps/llm_apps_with_memory_tutorials/llama3_stateful_chat` | `day062-llama3-stateful-chat` | 38 |
| 063 | 💾 AI ArXiv Agent with Memory | `advanced_llm_apps/llm_apps_with_memory_tutorials/ai_arxiv_agent_memory` | `day063-ai-arxiv-agent-memory` | 65 |
| 064 | 📝 LLM App with Personalized Memory | `advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory` | `day064-llm-app-personalized-memory` | 75 |
| 065 | 🧠 Multi-LLM Application with Shared Memory | `advanced_llm_apps/llm_apps_with_memory_tutorials/multi_llm_memory` | `day065-multi-llm-memory` | 94 |
| 066 | 🛩️ AI Travel Agent with Memory | `advanced_llm_apps/llm_apps_with_memory_tutorials/ai_travel_agent_memory` | `day066-ai-travel-agent-memory` | 102 |
| 067 | 🗄️ Local ChatGPT Clone with Memory | `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory` | `day067-local-chatgpt-with-memory` | 137 |

### 볼륨 6. 🚀 Advanced AI Agents (Day 68–88, 21일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 068 | 📈 AI Investment Agent | `advanced_ai_agents/single_agent_apps/ai_investment_agent` | `day068-ai-investment-agent` | 28 |
| 069 | 🎬 AI Movie Production Agent | `advanced_ai_agents/single_agent_apps/ai_movie_production_agent` | `day069-ai-movie-production-agent` | 85 |
| 070 | 🧬 AI Self-Evolving Agent | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent` | `day070-ai-self-evolving-agent` | 87 |
| 071 | 🗞️ AI Journalist Agent | `advanced_ai_agents/single_agent_apps/ai_journalist_agent` | `day071-ai-journalist-agent` | 92 |
| 072 | 🔬 AI Research Planner & Executor (Google Interactions API) | `advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api` | `day072-research-agent-gemini-interaction-api` | 103 |
| 073 | 🔍 AI Deep Research Agent | `advanced_ai_agents/single_agent_apps/ai_deep_research_agent` | `day073-ai-deep-research-agent` | 185 |
| 074 | 📑 AI Meeting Agent | `advanced_ai_agents/single_agent_apps/ai_meeting_agent` | `day074-ai-meeting-agent` | 186 |
| 075 | 🧠 AI Mental Wellbeing Agent | `advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent` | `day075-ai-mental-wellbeing-agent` | 227 |
| 076 | 🏋️‍♂️ AI Health & Fitness Agent | `advanced_ai_agents/single_agent_apps/ai_health_fitness_agent` | `day076-ai-health-fitness-agent` | 245 |
| 077 | 🏗️ AI System Architect Agent | `advanced_ai_agents/single_agent_apps/ai_system_architect_r1` | `day077-ai-system-architect-r1` | 318 |
| 078 | 🤝 AI Consultant Agent | `advanced_ai_agents/single_agent_apps/ai_consultant_agent` | `day078-ai-consultant-agent` | 320 |
| 079 | 🚀 AI Product Launch Intelligence Agent | `advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent` | `day079-product-launch-intelligence-agent` | 484 |
| 080 | 🛡️ Trust-Gated Multi-Agent Research Team | `advanced_ai_agents/multi_agent_apps/trust_gated_agent_team` | `day080-trust-gated-agent-team` | 652 |
| 081 | 👨🏻‍💼 AI Sales Intelligence Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team` | `day081-ai-sales-intelligence-agent-team` | 659 |
| 082 | 📊 AI VC Due Diligence Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team` | `day082-ai-vc-due-diligence-agent-team` | 674 |
| 083 | 🔍 AI Fraud Investigation Agent | `advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent` | `day083-ai-fraud-investigation-agent` | 936 |
| 084 | 💰 AI Financial Coach Agent | `advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent` | `day084-ai-financial-coach-agent` | 968 |
| 085 | 🏚️ 🍌 AI Home Renovation Agent with Nano Banana Pro | `advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent` | `day085-ai-home-renovation-agent` | 1077 |
| 086 | 🧠 DevPulse AI - Multi-Agent Signal Intelligence | `advanced_ai_agents/multi_agent_apps/devpulse_ai` | `day086-devpulse-ai` | 1532 |
| 087 | 📡 Earnings Call Analyst Agent | `advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent` | `day087-earnings-call-analyst-agent` | 2286 |
| 088 | 🎧 AI Social Media News and Podcast Agent | `advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents` | `day088-ai-news-and-podcast-agents` | 32594 |

### 볼륨 7. 🤝 Multi-agent Teams (Day 89–101, 13일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 089 | 💲 AI Finance Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team` | `day089-ai-finance-agent-team` | 45 |
| 090 | 👨‍🏫 AI Teaching Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team` | `day090-ai-teaching-agent-team` | 208 |
| 091 | ✨ Multimodal Design Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team` | `day091-multimodal-design-agent-team` | 264 |
| 092 | 💻 Multimodal Coding Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team` | `day092-multimodal-coding-agent-team` | 283 |
| 093 | 🎨 AI Game Design Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team` | `day093-ai-game-design-agent-team` | 291 |
| 094 | 🧲 AI Competitor Intelligence Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team` | `day094-ai-competitor-intelligence-agent-team` | 343 |
| 095 | 👨‍💼 AI Services Agency (CrewAI) | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency` | `day095-ai-services-agency` | 370 |
| 096 | 🧭 AG2 Adaptive Research Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team` | `day096-ag2-adaptive-research-team` | 406 |
| 097 | 💼 AI Recruitment Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team` | `day097-ai-recruitment-agent-team` | 522 |
| 098 | 👨‍⚖️ AI Legal Agent Team (Cloud & Local) | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team` | `day098-ai-legal-agent-team` | 665 |
| 099 | 🎨 🍌 Multimodal UI/UX Feedback Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team` | `day099-multimodal-uiux-feedback-agent-team` | 837 |
| 100 | 🏠 AI Real Estate Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team` | `day100-ai-real-estate-agent-team` | 1665 |
| 101 | 🌏 AI Travel Planner Agent Team | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team` | `day101-ai-travel-planner-agent-team` | 8134 |

### 볼륨 8. ♾️ MCP AI Agents (Day 102–107, 6일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 102 | 📑 Notion MCP Agent | `mcp_ai_agents/notion_mcp_agent` | `day102-notion-mcp-agent` | 124 |
| 103 | 🐙 GitHub MCP Agent | `mcp_ai_agents/github_mcp_agent` | `day103-github-mcp-agent` | 151 |
| 104 | ♾️ Browser MCP Agent | `mcp_ai_agents/browser_mcp_agent` | `day104-browser-mcp-agent` | 181 |
| 105 | 🔌 OpenAI Remote MCP Tool Bridge | `mcp_ai_agents/openai_remote_mcp_bridge` | `day105-openai-remote-mcp-bridge` | 270 |
| 106 | 🌍 AI Travel Planner MCP Agent | `mcp_ai_agents/ai_travel_planner_mcp_agent_team` | `day106-ai-travel-planner-mcp-agent-team` | 321 |
| 107 | 🔀 Multi-MCP Agent Router | `mcp_ai_agents/multi_mcp_agent_router` | `day107-multi-mcp-agent-router` | 372 |

### 볼륨 9. 🎮 Autonomous Game-Playing (Day 108–110, 3일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 108 | ♜ AI Chess Agent | `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent` | `day108-ai-chess-agent` | 249 |
| 109 | 🎮 AI 3D Pygame Agent | `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1` | `day109-ai-3dpygame-r1` | 273 |
| 110 | 🎲 AI Tic-Tac-Toe Agent | `advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent` | `day110-ai-tic-tac-toe-agent` | 893 |

### 볼륨 10. 🗣️ Voice AI Agents (Day 111–114, 4일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 111 | 📞 Customer Support Voice Agent | `voice_ai_agents/customer_support_voice_agent` | `day111-customer-support-voice-agent` | 393 |
| 112 | 🔊 Voice RAG Agent (OpenAI SDK) | `voice_ai_agents/voice_rag_openaisdk` | `day112-voice-rag-openaisdk` | 401 |
| 113 | 🗣️ AI Audio Tour Agent | `voice_ai_agents/ai_audio_tour_agent` | `day113-ai-audio-tour-agent` | 697 |
| 114 | 🛡️ Insurance Claim Live Agent Team | `voice_ai_agents/insurance_claim_live_agent_team` | `day114-insurance-claim-live-agent-team` | 2663 |

### 볼륨 11. 🖼️ Generative UI (Day 115–121, 7일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 115 | 🔍 AI Deep Research Agent | `generative_ui_agents/ai-deep-research-agent` | `day115-genui-deep-research-agent` | 1617 |
| 116 | 🪙 AI Financial Coach Agent | `generative_ui_agents/ai-financial-coach-agent` | `day116-genui-financial-coach-agent` | 1857 |
| 117 | 🗂️ Generative UI Starter Project | `generative_ui_agents/generative-ui-starter-project` | `day117-genui-generative-ui-starter-project` | 2935 |
| 118 | 📊 AI Dashboard Canvas Agent | `generative_ui_agents/ai-dashboard-canvas-agent` | `day118-genui-dashboard-canvas-agent` | 3171 |
| 119 | ✈️ MCP Apps Generative UI Showcase | `generative_ui_agents/mcp-apps-generative-ui-showcase` | `day119-genui-mcp-apps-generative-ui-showcase` | 4364 |
| 120 | 🛠️ AI MCP App Builder | `generative_ui_agents/ai-mcp-app-builder` | `day120-genui-mcp-app-builder` | 7176 |
| 121 | 🎛️ AI Shadcn Component Generator | `generative_ui_agents/ai-shadcn-component-generator` | `day121-genui-shadcn-component-generator` | 7682 |

### 볼륨 12. 🛰️ Always-on Agents (Day 122–123, 2일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 122 | 📰 Always-on Hacker News Briefing Agent | `always_on_agents/always_on_hn_briefing_agent` | `day122-always-on-hn-briefing-agent` | 890 |
| 123 | 📡 Release Radar Agent | `always_on_agents/release_radar_agent` | `day123-release-radar-agent` | 1292 |

### 볼륨 13. 🎯 LLM Optimization (Day 124–125, 2일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 124 | 🧠 Headroom Context Optimization | `advanced_llm_apps/llm_optimization_tools/headroom_context_optimization` | `day124-headroom-context-optimization` | 204 |
| 125 | 🎯 Toonify Token Optimization | `advanced_llm_apps/llm_optimization_tools/toonify_token_optimization` | `day125-toonify-token-optimization` | 700 |

### 볼륨 14. 🔧 LLM Fine-tuning (Day 126–127, 2일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 126 | 🦙 Llama 3.2 Fine-tuning | `advanced_llm_apps/llm_finetuning_tutorials/llama3.2_finetuning` | `day126-llama3.2-finetuning` | 63 |
| 127 | 🦥 Gemma 3 Fine-tuning | `advanced_llm_apps/llm_finetuning_tutorials/gemma3_finetuning` | `day127-gemma3-finetuning` | 91 |

### 볼륨 15. 🧩 Agent Skills (Day 128–133, 6일)

| Day | 앱 | 원본 경로 | 폴더 | 코드 규모(줄) |
|---|---|---|---|---|
| 128 | 🧠 Advisor Orchestrator Worker | `agent_skills/advisor-orchestrator-worker` | `day128-advisor-orchestrator-worker` | 0 |
| 129 | 🏺 Commit Archaeologist | `agent_skills/commit-archaeologist` | `day129-commit-archaeologist` | 389 |
| 130 | 🩺 Dependency Doctor | `agent_skills/dependency-doctor` | `day130-dependency-doctor` | 486 |
| 131 | 🔭 Scope Creep Detector | `agent_skills/scope-creep-detector` | `day131-scope-creep-detector` | 529 |
| 132 | ⚰️ Project Graveyard | `agent_skills/project-graveyard` | `day132-project-graveyard` | 556 |
| 133 | ♾️ Self-Improving Agent Skills | `agent_skills/self-improving-agent-skills` | `day133-self-improving-agent-skills` | 2421 |
