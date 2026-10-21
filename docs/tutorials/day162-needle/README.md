# Day 162 · 🪡 Needle - A New Way to Find

> 볼륨 17 🔎 AI 브라우저 도구 · 난이도 ★★☆ · 예상 소요 140분(붙여 넣을 블록 열네 개를 돌리고, 서버 셋과 확장 소스 600줄가량을 읽으며 출력을 소스와 맞대 보는 데 시간이 듭니다. 본문은 2,800낱말이지만 읽는 시간보다 손으로 돌리는 시간이 큽니다) · API 비용 대략 0원(가짜 게이트웨이만 썼습니다. 진짜 Vercel AI Gateway로 쓰면 크레딧이 들지만 Jev의 단가는 이 문서가 읽은 Vercel 문서에 없고 모델 목록 페이지에 있다고만 되어 있습니다) · 원본 앱: `advanced_llm_apps/needle`

## 오늘 만들 것

웹 페이지(또는 붙여 넣은 글)에서 "키워드가 같은 글"이 아니라 "뜻이 맞는 문장"을 찾아 강조해 주는 앱을 따라 봅니다. 크롬 확장이 쪽의 문단을 모아 로컬 Node 서버로 보내고, 서버가 문단마다 점수와 가장 알맞은 문장을 Vercel AI Gateway의 `typesafe-ai/jev` 모델에게서 받아 돌려주고, 확장이 그 문장 범위에 형광펜을 칠합니다. 같은 서버를 React 웹 앱(`src/`)도 씁니다. 오늘의 공부거리는 모델이 글을 **만들지 않고 고르기만 한다**는 점과 그 선택을 **원문의 글자 위치**로 되돌리는 길, 그리고 로컬 서버가 어디까지 믿을 만한가입니다.

볼륨 17은 브라우저 확장 + 로컬 Node 백엔드 + LLM API라는 꼴을 두 날 봅니다. 볼륨 16(Day 154~161)은 에이전트에게 주는 스킬 일곱 개와 파이썬 앱 하나였고, [Day 161](../day161-self-improving-agent-skills/README.md)은 화면만 Node(Next.js)였습니다. 오늘은 앱 전체가 Node이고 파이썬이 하나도 없습니다. 새로운 것은 둘입니다. 서버가 부르는 모델이 채팅 모델이 아니라 **결정 모델**(질문에 불리언 확률이나 선택지를 답하는 모델)이라는 것, 그리고 호출하는 쪽이 사람이 여는 페이지가 아니라 **브라우저 안에서 남의 페이지를 읽는 확장**이라는 것입니다.

이 문서는 진짜 AI Gateway를 부르지 않았고 크롬도 띄우지 않았고 `npm install`도 하지 않았습니다. 서버(`server/dev.mjs`)와 시험 세 개는 **실제로 돌렸습니다**. 가짜 게이트웨이는 내가 만든 대본(동의어 표와 낱말 일치로 점수를 짓는 40줄)이라서, 아래의 "0.90"이나 "일치 5개"는 Jev가 낸 값이 아니라 **앱이 그 값을 어떻게 다루는지**를 보이는 값입니다. 확장(`extension/`)과 React 화면(`src/*.jsx`)은 소스로만 읽었습니다.

1. 한 번의 검색은 게이트웨이 요청 **한 건**입니다. 문단마다 불리언 질문 하나, 문장이 둘 이상이면 선택 질문 하나가 더 붙습니다. 내장 문서 `stay`는 문단 13개로 질문 26개입니다(Step 1, 4).
2. 요청은 커집니다. 레시피 문서에서 앱 본문 1,601바이트가 게이트웨이 요청 10,988바이트가 됐습니다. 늘어난 몫의 대부분은 질문마다 되풀이되는 영어 지시문(5,511바이트)과 기준(1,656바이트)이고, 문단·문장이 두 번 실리는 몫은 1KB 남짓입니다(Step 6).
3. 서버는 `127.0.0.1`에서만 듣고, 토큰이 없으면 **누구든** 검색할 수 있습니다. Origin·CORS 검사는 없습니다. 다른 사이트를 흉내 낸 Node 요청(`Origin`을 단 `text/plain` POST)이 preflight 없이 200으로 처리됐습니다. 크롬의 Local Network Access 허락 창이 이 길을 막을 수 있지만 그것에 기대지는 않습니다(Step 5). `NEEDLE_ACCESS_TOKEN`을 두면 틀린 요청이 401이 되고, 이 토큰은 로컬에서도 두는 편이 낫습니다(Step 5).
4. 요청 본문은 512,000바이트(→ 413), 문단은 160개·문단당 2,200자·전체 60,000자, 질문은 400자까지입니다(Step 5).
5. 게이트웨이의 401·402·403은 모두 HTTP 502로, 429만 429로 바뀌어 나옵니다(Step 6).
6. 문장 나누기는 `Intl.Segmenter("en")`입니다. 한국어 문장은 맞게 나뉘지만 `Dr.`·`sec.` 같은 영어 약어에서 문장이 끊깁니다(Step 3).
7. 앱 README는 확장 단축키를 Ctrl+F(macOS는 Cmd+F)라고 쓰지만 `manifest.json`이 정한 기본 단축키는 Ctrl+Shift+F입니다(Step 7).

![완성 아키텍처](diagrams/overview.svg)

위 그림의 "호출하는 쪽"과 "백엔드"는 묶음이라 안쪽 화살표는 따로 그렸습니다. [`extra-extension`](diagrams/extra-extension.svg)은 확장 안의 흐름, [`extra-web`](diagrams/extra-web.svg)은 웹 앱의 흐름, [`extra-backend`](diagrams/extra-backend.svg)는 서버 안의 흐름입니다.

![확장 안의 구조](diagrams/extra-extension.svg)

![웹 앱의 구조](diagrams/extra-web.svg)

![백엔드 안의 구조](diagrams/extra-backend.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Node.js 22.12 이상 | 서버와 시험. `package.json`의 `engines`가 `>=22.12.0`이다. 이 문서는 24.12.0으로 돌렸다 | [Node.js 내려받기](https://nodejs.org/) |
| bash와 curl | 이 문서의 명령. Windows는 Git Bash | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| git, 이 저장소의 클론 | 원본 폴더를 읽고 복사한다. 아래 명령은 모두 저장소 루트에서 시작한다 | `git clone https://github.com/Shubhamsaboo/awesome-llm-apps` |
| npm | **이 문서는 쓰지 않았다.** `npm ci`·`npm run dev`는 설치 스크립트를 돌리는 단계라 실행하지 않았다(Step 7) | 진짜로 쓸 때만 |
| Vercel AI Gateway 키 | 진짜로 쓸 때만. **이 문서는 쓰지 않았다**(키는 `fake-…`만) | [Vercel 대시보드](https://vercel.com/dashboard/ai-gateway) |
| 크롬 | 확장을 올려 볼 때만. **이 문서는 띄우지 않았다** | 없음 |

이 폴더에는 파이썬이 없어서 uv와 파이썬 버전 준비가 필요 없습니다. 터미널은 하나를 씁니다. 서버 둘과 가짜 게이트웨이는 같은 터미널의 백그라운드로 띄우고 Step 7에서 끕니다.

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 쪽 글 모으기·강조 | 보이는 문단을 모으고, 검색 메시지를 보내고, 받은 문장 범위를 칠한다 | `advanced_llm_apps/needle/extension/content.js:1-217` |
| 서비스 워커 | 확장 아이콘을 누르면 스크립트를 넣고, 서버로 POST를 대신 보낸다 | `advanced_llm_apps/needle/extension/background.js:1-50` |
| 문장 범위 변환 | 서버가 준 글자 위치를 DOM `Range`로 바꾼다 | `advanced_llm_apps/needle/extension/text-range.js:1-39` |
| 설정 쪽 | 서버 주소·토큰을 저장하고 그 서버에 대한 접근 권한을 요청한다 | `advanced_llm_apps/needle/extension/options.js:1-36` |
| 로컬 서버 | `127.0.0.1`에서 듣고 토큰·크기를 검사한 뒤 검색 함수로 넘긴다 | `advanced_llm_apps/needle/server/dev.mjs:1-84` |
| 검색 함수 | 메서드·토큰·크기를 다시 보고 `search()`를 부른다(Vercel에서는 이것만 돈다) | `advanced_llm_apps/needle/api/search.js:1-27` |
| 검증·질문·점수 | 본문 검증, 게이트웨이 요청 만들기, 응답 해석, 0.58 거르기 | `advanced_llm_apps/needle/server/search.mjs:1-170` |
| 문장 나누기 | 원문 글자 위치를 지키며 문장 범위를 계산한다 | `advanced_llm_apps/needle/server/sentences.mjs:1-11` |
| 접근 검사 | `NEEDLE_ACCESS_TOKEN`과 Vercel 닫힘 | `advanced_llm_apps/needle/server/http.mjs:1-13` |
| 웹 앱 | 문서 고르기·붙여 넣기, 650ms 쉬면 검색, 결과 25개 캐시 | `advanced_llm_apps/needle/src/App.jsx:1-477` |
| 내장 문서 | 예시 문서 셋과 문단 블록 만들기 | `advanced_llm_apps/needle/src/documents.js:1-163` |
| 시험 | 검색·문장·접근 검사·확장 묶기 | `advanced_llm_apps/needle/tests/search.test.mjs:1-169` |
| 이 문서의 가짜 게이트웨이·가드 | 대본 서버, 루프백 가드, 서버 기동기 | 코드 없음 (Step 2에서 직접 만듦) |

## 단계별 진행

### Step 1. 폴더를 읽고 앱 사본을 만든다

**목적.** 원본에는 아무것도 쓰지 않고, 서버가 쓰는 파일만 실습 폴더로 복사해 그 사본에서 돌립니다. 앱은 지금 폴더의 `.env`를 읽으므로(`advanced_llm_apps/needle/server/env.mjs:1-7`) 원본이나 진짜 홈의 `.env`가 읽힐 길을 막는 것이 이 단계의 일입니다.

**할 일.** 저장소 루트에서 시작합니다. `LAB`은 저장소 밖의 새 폴더로 자기 절대 경로로 바꿉니다. 아래 블록은 폴더를 만들기 **전에** 자리 표시 값 그대로인지, 절대 경로인지, 에이전트 설정 폴더(`.claude`·`.agents` 등)나 `CLAUDE_CONFIG_DIR` 아래인지를 보고, 하나라도 걸리면 아무것도 만들지 않습니다. 이 문서는 bash 전용입니다(PowerShell 판은 싣지 않았습니다). 환경 파일은 HOME·TEMP를 `LAB` 아래로 돌리고, 프록시 변수와 키 변수를 지우고, `NO_PROXY`를 루프백으로 둡니다. 복사는 `server`·`api`·`src`·`tests`·`extension`과 `package.json`·`vercel.json`만 하고(`node_modules`나 원본 `.env`는 가져오지 않습니다), 사본의 `.env`에는 가짜 키 한 줄만 씁니다.

```bash
cd awesome-llm-apps
export REPO="$PWD"
export LAB=/path/to/d162-lab          # 저장소 밖의 새 폴더(자기 절대 경로로 바꾼다)
_ok=1; _n() { { cygpath -m "$1" 2>/dev/null || printf '%s' "$1"; } | tr 'A-Z' 'a-z' | tr '\134' '/'; }
[ -d "$REPO/advanced_llm_apps/needle/server" ] || { echo "저장소 루트(awesome-llm-apps)에서 시작하세요"; _ok=0; }
case "$LAB" in ""|/path/to/*) echo "LAB을 자기 경로로 바꾸세요"; _ok=0 ;; esac
case "$LAB" in /*|[A-Za-z]:*) ;; *) echo "LAB은 절대 경로여야 합니다: $LAB"; _ok=0 ;; esac
case "$(_n "$LAB")/" in
  */.claude/*|*/.agents/*|*/.codex/*|*/.cursor/*|*/.copilot/*|*/.openclaw/*|*/.hermes/*)
    echo "LAB이 에이전트 설정 폴더 아래입니다: $LAB"; _ok=0 ;; esac
if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
  _c=$(_n "$CLAUDE_CONFIG_DIR")
  case "$(_n "$LAB")/" in "${_c%/}"/*) echo "LAB이 CLAUDE_CONFIG_DIR 아래입니다"; _ok=0 ;; esac
fi
if [ "$_ok" = 1 ]; then
  mkdir -p "$LAB/home" "$LAB/tmp" "$LAB/logs" "$LAB/work/lab" "$LAB/work/needle"
  cat > "$LAB/env.sh" <<'EOF'
# Day 162 작업 셸의 환경. 이 문서의 모든 명령은 이 파일을 불러온 셸에서 돌린다.
: "${REPO:?REPO를 먼저 정하세요}" "${LAB:?LAB을 먼저 정하세요}"
_n() { { cygpath -m "$1" 2>/dev/null || printf '%s' "$1"; } | tr 'A-Z' 'a-z' | tr '\134' '/'; }
_lab=$(cd "$LAB" 2>/dev/null && pwd -P) || { echo "LAB 폴더가 없습니다: $LAB"; return 1; }
_low="$(_n "$_lab")/"
case "$_low" in
  */.claude/*|*/.agents/*|*/.codex/*|*/.cursor/*|*/.copilot/*|*/.openclaw/*|*/.hermes/*)
    echo "LAB이 에이전트 설정 폴더 아래입니다: $_lab"; return 1 ;;
esac
if [ -n "${CLAUDE_CONFIG_DIR:-}" ] && _cfg=$(cd "$CLAUDE_CONFIG_DIR" 2>/dev/null && pwd -P); then
  _cfg="$(_n "$_cfg")/"
  case "$_low" in "$_cfg"*) echo "LAB이 CLAUDE_CONFIG_DIR 아래입니다"; return 1 ;; esac
fi
case "${NODE_OPTIONS:-}" in *proxy*|*PROXY*) echo "NODE_OPTIONS에 proxy가 있습니다. 지우고 다시 하세요"; return 1 ;; esac
export HOME="$LAB/home" USERPROFILE="$LAB/home" CLAUDE_CONFIG_DIR="$LAB/home/.claude"
export TEMP="$LAB/tmp" TMP="$LAB/tmp" TMPDIR="$LAB/tmp"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy NODE_USE_ENV_PROXY
unset AI_GATEWAY_API_KEY AI_GATEWAY_KEY_FILE NEEDLE_ACCESS_TOKEN VERCEL PORT
export NO_PROXY=127.0.0.1,localhost,::1 no_proxy=127.0.0.1,localhost,::1
export NEEDLE_DIR="$LAB/work/needle" LABDIR="$LAB/work/lab"
export FAKE_PORT=51911 APP_PORT=51913 APP2_PORT=51915
export FAKE_LOG="$LAB/logs/fake.jsonl" LAST_REQ="$LAB/logs/last-request.json"
EOF
  source "$LAB/env.sh" && {
    for d in server api src tests extension; do mkdir -p "$NEEDLE_DIR/$d" && cp -r "$REPO/advanced_llm_apps/needle/$d/." "$NEEDLE_DIR/$d/"; done
    cp "$REPO/advanced_llm_apps/needle/package.json" "$REPO/advanced_llm_apps/needle/vercel.json" "$NEEDLE_DIR/"
    printf 'AI_GATEWAY_API_KEY=fake-from-dotenv\n' > "$NEEDLE_DIR/.env"
    ls "$NEEDLE_DIR"
  }
fi
```

기대 출력은 마지막 `ls`입니다.

```text
api
extension
package.json
server
src
tests
vercel.json
```

`LAB`을 자리 표시 값 그대로 두고 붙여 넣으면 `LAB을 자기 경로로 바꾸세요` 한 줄만 나오고 폴더가 만들어지지 않습니다(직접 확인했습니다). 새 터미널에서는 `export REPO=… LAB=…`를 다시 정한 뒤 `source "$LAB/env.sh"`로 시작합니다. 아래 블록은 모두 첫 줄이 그 일을 합니다.

내장 문서는 웹 앱이 처음 보여 주는 예시이고 `advanced_llm_apps/needle/src/documents.js:1-163`에 있습니다. 세 편이며 문단 단위로 쓰여 있습니다. 문서마다 `suggestions`(검색어 예시)가 있고 `getBlocks`(`advanced_llm_apps/needle/src/documents.js:154-163`)가 문단에 `b0`, `b1`… 번호를 붙입니다. 서버가 요구하는 id 꼴(`/^b\d+$/`, `advanced_llm_apps/needle/server/search.mjs:38`)과 같습니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
cat > "${LABDIR:?}/docs-count.mjs" <<'EOF'
// 사용: node docs-count.mjs  → 웹 앱에 내장된 문서와 문단·질문 수를 센다
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
const at = (p) => import(pathToFileURL(resolve(process.env.NEEDLE_DIR, p)).href);
const { documents, getBlocks } = await at("src/documents.js");
const { sentenceSpans } = await at("server/sentences.mjs");
for (const d of documents) {
  const b = getBlocks(d);
  const multi = b.filter((x) => sentenceSpans(x.text).length > 1).length;
  console.log(`${d.id.padEnd(7)} 문단 ${String(b.length).padStart(2)}  글자 ${b.reduce((n, x) => n + x.text.length, 0)}  게이트웨이 질문 ${b.length + multi}  예시: ${d.suggestions[0]}`);
}
EOF
node "${LABDIR:?}/docs-count.mjs"
```

```text
stay    문단 13  글자 2128  게이트웨이 질문 26  예시: hidden fees
recipe  문단  8  글자 1387  게이트웨이 질문 15  예시: what can replace the eggs?
thread  문단 11  글자 1545  게이트웨이 질문 20  예시: what price did we agree on?
```

문서 `stay`는 호텔 예약 안내(숨은 요금, 반려견, 취소)이고 `recipe`는 팬케이크, `thread`는 팀 채팅 기록입니다. 

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** `ls "$NEEDLE_DIR"`에 `.env`가 보이고 `cat "$NEEDLE_DIR/.env"`가 `AI_GATEWAY_API_KEY=fake-from-dotenv` 한 줄이면 됩니다.

### Step 2. 가짜 게이트웨이와 가드를 만든다

**목적.** 앱이 부르는 곳은 `https://ai-gateway.vercel.sh/v1/evaluate` 하나입니다(`advanced_llm_apps/needle/server/search.mjs:125`). 이 문서는 그 주소를 루프백의 가짜 서버로 돌리고, 가드가 빠지면 앱이 아예 돌지 않게 만듭니다.

**할 일.** Vercel 문서는 이 API의 요청을 `model`·`state`·`questions`로 설명하고, 질문 종류를 `boolean`(확률)·`choice`(선택지)·`score`로 둡니다. 응답에는 `answers`와 `usage`가 있습니다. 이 페이지는 `evaluation`이라는 옛 이름으로 들어가면 `Decision` 페이지로 이어졌고, "결정 모델은 예전에 평가 모델이라 불렀다"고 밝히고, `experimental_evaluate`와 `gateway.evaluationModel()`은 폐기 예정 별칭으로 남는다고 적습니다. `/v1/evaluate`는 HTTP API 절에 그대로 적혀 있습니다(읽은 날 2026-10-21). Jev는 TypeSafe AI가 "빠르고 타입이 있는 결정"을 위해 만든 모델로 소개되고, 글을 생성하지 않고 선택·점수·확률을 돌려줍니다. 가짜 서버는 이 모양만 흉내 냅니다. 파일은 넷입니다.

- `fake-gateway.mjs`: `127.0.0.1`에서만 듣고 `POST /v1/evaluate`만 받습니다. 질문 낱말 일치로 확률을 지어내고, 선택 질문은 낱말이 가장 많이 든 문장을 고릅니다. 질문에 `__401__`·`__429__`·`__incomplete__`가 들어 있으면 그 오류를 냅니다(Step 6). 받은 요청은 `last-request.json`과 기록 파일에 남깁니다.
- `guard.mjs`: 앱 프로세스 안에서 `fetch`와 `net`·`tls` 연결을 가로챕니다. 위 주소는 가짜 서버로 바꾸고 루프백 밖으로 가는 이 세 길은 막습니다(`dns`를 직접 부르는 코드는 막지 않지만 이 앱은 그런 코드를 쓰지 않고, 연결을 만들기 전에 호스트부터 보므로 앱의 `fetch`는 이름 조회까지 가지 못합니다). 불러지자마자 예약 주소 `192.0.2.1`로 `fetch`·`net.connect`·`tls.connect`를 시도해 **셋 다 막히는지 먼저 단언**하고, 아니면 프로세스를 끝냅니다.
- `serve.mjs`: 가드를 불러오고, 불러졌는지 단언하고, 사본이 `LAB` 안인지 보고, 그 폴더로 옮겨 `server/dev.mjs`를 부릅니다. 가드를 부르는 줄을 빼면 단언이 앱을 멈춥니다(아래에서 그 줄을 빼 보입니다). 단언 줄만 빼면 가드는 그대로 걸려 있어 안전은 변하지 않습니다.
- `mkbody.mjs`: 내장 문서와 질문으로 앱이 보내는 것과 같은 본문을 만듭니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
cat > "${LABDIR:?}/fake-gateway.mjs" <<'EOF'
// 가짜 AI Gateway. POST /v1/evaluate 만 받고 127.0.0.1 에서만 듣는다. 모델이 아니라 대본이다.
import http from "node:http";
import { appendFileSync, writeFileSync } from "node:fs";
const port = Number(process.env.FAKE_PORT);
const STOP = new Set(["what", "the", "can", "and", "for", "are", "how", "does", "did", "who", "is", "my", "if", "to", "of", "in", "i"]);
const SYN = { // 의미 일치를 흉내 내는 작은 동의어표
  fees: ["fee", "fees", "charge", "charges", "deposit", "$"], hidden: ["hidden", "added", "additional", "extra"],
  dog: ["dog", "dogs", "pet", "pets", "lead"], plans: ["plan", "plans", "cancel", "cancelled", "cancellation", "move"],
  change: ["change", "changes", "refund", "cancel", "cancelled", "move"], price: ["price", "$", "tier", "month"],
};
const terms = (q) => q.toLowerCase().replace(/[^a-z$ ]/g, " ").split(/\s+/).filter((w) => w.length > 1 && !STOP.has(w));
const words = (text) => text.toLowerCase().match(/[a-z]+|\$/g) || [];
const hits = (q, text) => terms(q).filter((t) => (SYN[t] || [t]).some((s) => words(text).includes(s))).length;
const server = http.createServer((req, res) => {
  let raw = "";
  req.on("data", (c) => (raw += c));
  req.on("end", () => {
    const send = (code, obj) => { res.statusCode = code; res.setHeader("Content-Type", "application/json"); res.end(JSON.stringify(obj)); };
    if (req.method !== "POST" || req.url !== "/v1/evaluate") return send(404, { error: "not found" });
    const body = JSON.parse(raw), q = body.state.search;
    appendFileSync(process.env.FAKE_LOG, JSON.stringify({ auth: /^Bearer fake-/.test(req.headers.authorization || "") ? req.headers.authorization : "(fake- 로 시작하지 않아 가렸습니다)", model: body.model, passages: body.state.passages.length, questions: Object.keys(body.questions).length }) + "\n");
    writeFileSync(process.env.LAST_REQ, JSON.stringify(body, null, 2));
    if (q.includes("__401__")) return send(401, {});
    if (q.includes("__429__")) return send(429, {});
    if (q.includes("__incomplete__")) return send(200, { answers: {} });
    const n = Math.max(1, terms(q).length), answers = {};
    for (const [key, spec] of Object.entries(body.questions)) {
      if (spec.type === "boolean") {
        const p = body.state.passages.find((x) => x.id === key);
        const h = hits(q, p.text);
        answers[key] = { type: "boolean", probability: h ? Math.min(0.97, 0.3 + (0.6 * h) / n) : 0.04 };
      } else {
        const scored = Object.entries(spec.criteria).map(([k, text]) => [k, hits(q, text)]);
        const best = scored.reduce((a, b) => (b[1] > a[1] ? b : a));
        answers[key] = { type: "choice", choice: best[0] };
      }
    }
    send(200, { model: body.model, answers, usage: { inputTokens: Math.ceil(raw.length / 4), outputTokens: 20 } });
  });
});
server.listen(port, "127.0.0.1", () => console.log(`가짜 게이트웨이: http://127.0.0.1:${port}`));
EOF
cat > "${LABDIR:?}/guard.mjs" <<'EOF'
// 앱 프로세스 안의 가드. ai-gateway.vercel.sh/v1/evaluate 를 가짜 서버로 돌리고, fetch·net·tls 연결은 루프백 밖이면 막는다(dns를 직접 부르는 코드는 막지 않는다).
import net from "node:net";
import tls from "node:tls";
const FAKE = `http://127.0.0.1:${Number(process.env.FAKE_PORT)}/v1/evaluate`;
const GATEWAY = "https://ai-gateway.vercel.sh/v1/evaluate";
const LOOP = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);
const refuse = (what) => Object.assign(new Error(`needle-lab guard: ${what}`), { code: "ELABGUARD" });
const realFetch = globalThis.fetch;
globalThis.fetch = (input, init) => {
  const url = new URL(typeof input === "string" || input instanceof URL ? input : input.url);
  if (url.href === GATEWAY) return realFetch(FAKE, init);
  if (!LOOP.has(url.hostname)) return Promise.reject(refuse(url.hostname));
  return realFetch(input, init);
};
const hostOf = (args) => {
  const o = args[0];
  if (typeof o === "object" && o !== null) return o.path ? "localhost" : o.host || "localhost";
  return typeof args[1] === "string" ? args[1] : "localhost";
};
for (const [owner, name] of [[net.Socket.prototype, "connect"], [net, "connect"], [net, "createConnection"], [tls, "connect"]]) {
  const real = owner[name];
  owner[name] = function (...args) {
    if (!LOOP.has(hostOf(args))) throw refuse(hostOf(args));
    return real.apply(this, args);
  };
}
// 가드가 정말 걸렸는지 예약 주소(192.0.2.1)로 fetch·net·tls 세 길을 먼저 확인한다. 걸리지 않았으면 여기서 멈춘다.
let blocked = 0;
try { await fetch("http://192.0.2.1/"); } catch (e) { if (e.code === "ELABGUARD") blocked++; }
try { net.connect(80, "192.0.2.1"); } catch (e) { if (e.code === "ELABGUARD") blocked++; }
try { tls.connect(443, "192.0.2.1"); } catch (e) { if (e.code === "ELABGUARD") blocked++; }
if (blocked !== 3) { console.error("가드가 걸리지 않았습니다. 멈춥니다."); process.exit(1); }
globalThis[Symbol.for("needle.lab.guard")] = true;
console.log("가드 확인: 예약 주소 세 길 모두 막힘");
EOF
cat > "${LABDIR:?}/serve.mjs" <<'EOF'
// 앱 서버를 가드 아래서 띄운다. 가드를 부르는 줄이나 아래 단언을 빼면 앱은 돌지 않는다.
import "./guard.mjs";
import { resolve, sep } from "node:path";
import { pathToFileURL } from "node:url";
if (!globalThis[Symbol.for("needle.lab.guard")]) { console.error("가드 없음. 멈춥니다."); process.exit(1); }
const dir = resolve(process.env.NEEDLE_DIR), lab = resolve(process.env.LAB);
if (!dir.toLowerCase().startsWith(lab.toLowerCase() + sep)) { console.error("앱 사본이 LAB 밖입니다. 멈춥니다."); process.exit(1); }
process.chdir(dir); // 앱은 지금 폴더의 .env 를 읽는다(server/env.mjs)
await import(pathToFileURL(resolve(dir, "server/dev.mjs")).href);
EOF
cat > "${LABDIR:?}/mkbody.mjs" <<'EOF'
// 사용: node mkbody.mjs <문서 id> "<질문>"  → 앱이 보내는 것과 같은 모양의 JSON 본문을 찍는다
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
const { documents, getBlocks } = await import(pathToFileURL(resolve(process.env.NEEDLE_DIR, "src/documents.js")).href);
const doc = documents.find((d) => d.id === process.argv[2]);
if (!doc) { console.error("문서 id:", documents.map((d) => d.id).join(", ")); process.exit(1); }
console.log(JSON.stringify({ query: process.argv[3], blocks: getBlocks(doc).map(({ id, text }) => ({ id, text })) }));
EOF
ls "$LABDIR"
```

```text
docs-count.mjs
fake-gateway.mjs
guard.mjs
mkbody.mjs
serve.mjs
```

Node 24에는 환경 변수의 프록시를 `fetch`에 쓰는 설정이 있습니다. 공식 문서(CLI 문서의 `--use-env-proxy`와 `NODE_USE_ENV_PROXY=1`은 v24.0.0, `--use-env-proxy`는 v24.5.0에 추가, `NO_PROXY`는 시작 때 읽음)와 `http` 문서(`http.setGlobalProxyFromEnv`는 `fetch()`와 `http.request()` 둘 다에 켠다)를 읽었고, 후자의 예제는 `NO_PROXY=localhost,127.0.0.1`을 직접 적습니다. 루프백이 자동으로 빠진다는 말은 없습니다. 독자의 셸에 프록시가 있고 Node가 그것을 쓰도록 켜져 있으면 **루프백 요청도 독자의 프록시로 갈 수 있습니다.** 직접 확인해 보입니다. 프록시 주소는 아무도 듣지 않는 루프백 포트(9)입니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
cat > "${LABDIR:?}/proxytest.mjs" <<'EOF'
// Node가 환경 변수의 프록시를 fetch에 쓰는지, 루프백 요청이 거기로 새는지 본다. 프록시 주소는 아무도 안 듣는 루프백 포트다.
import http from "node:http";
const s = http.createServer((q, r) => r.end("직접 도착")).listen(0, "127.0.0.1", async () => {
  try {
    const r = await fetch(`http://127.0.0.1:${s.address().port}/`);
    console.log("응답:", await r.text());
  } catch (e) { console.log("실패:", e.cause?.code || e.message); }
  s.close();
});
EOF
echo "--- 프록시 변수 없음(이 문서의 기본)"
node "${LABDIR:?}/proxytest.mjs"
echo "--- NODE_USE_ENV_PROXY=1 + HTTP_PROXY, NO_PROXY 없음"
NODE_USE_ENV_PROXY=1 HTTP_PROXY=http://127.0.0.1:9 NO_PROXY= no_proxy= node "${LABDIR:?}/proxytest.mjs"
echo "--- 같은 것 + NO_PROXY=127.0.0.1"
NODE_USE_ENV_PROXY=1 HTTP_PROXY=http://127.0.0.1:9 NO_PROXY=127.0.0.1 no_proxy=127.0.0.1 node "${LABDIR:?}/proxytest.mjs"
```

```text
--- 프록시 변수 없음(이 문서의 기본)
응답: 직접 도착
--- NODE_USE_ENV_PROXY=1 + HTTP_PROXY, NO_PROXY 없음
실패: ECONNREFUSED
--- 같은 것 + NO_PROXY=127.0.0.1
응답: 직접 도착
```

그래서 환경 파일은 프록시 변수를 지우고 `NO_PROXY`를 루프백으로 둡니다. 줄 하나를 빼도 바깥에 닿지 않는지는 다음 한 가지로 봅니다. `serve.mjs`에서 가드를 부르는 줄을 뺀 사본을 돌리면 앱이 서버를 띄우기 전에 멈춥니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
grep -v '^import "./guard.mjs";' "${LABDIR:?}/serve.mjs" > "${LABDIR:?}/serve-noguard.mjs"
PORT=$APP_PORT node "${LABDIR:?}/serve-noguard.mjs" --production; echo "종료 코드 $?"
```

```text
가드 없음. 멈춥니다.
종료 코드 1
```

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** 위 두 출력이 나오면 됩니다.

### Step 3. 시험과 문장 나누기를 돌린다

**목적.** 서버가 하는 일의 대부분(검증, 질문 만들기, 응답 해석, 문장 위치, 접근 검사, 확장의 범위 변환)은 외부 호출 없이 도는 시험이 이미 지킵니다. 그 시험을 먼저 돌립니다.

**할 일.** `npm test`는 `node --test tests/*.test.mjs`(`advanced_llm_apps/needle/package.json:11`)라서 `npm`을 쓰지 않고 같은 일을 `node`로 합니다. 시험은 넷이고 그 가운데 `package.test.mjs`만 `fflate`가 필요합니다. 먼저 나머지 셋을 돌립니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
cd "${NEEDLE_DIR:?}" || return
node --test tests/search.test.mjs tests/sentences.test.mjs tests/http.test.mjs
```

```text
✔ local backend permits tokenless use, but Vercel fails closed (0.4671ms)
✔ API rejects wrong methods before attempting inference (0.1559ms)
✔ validates passage boundaries and duplicate IDs (1.0949ms)
✔ binds each relevance question to a specific passage (0.2663ms)
✔ rejects incomplete, out-of-range and nonnumeric scores (0.2593ms)
✔ uses evaluation endpoint, keeps key server-side, returns ranked matching source IDs (0.8587ms)
✔ missing keys and upstream failures never fabricate matches (0.43ms)
✔ splits long pasted documents into valid bounded passages (0.257ms)
✔ splitting preserves punctuation, URLs and numbers in original passages (0.1264ms)
✔ asks Jev to select a sentence, and maps it to exact source offsets (0.1968ms)
✔ sentence spans preserve whitespace offsets, decimal numbers and Unicode (0.5133ms)
✔ sentence range crosses inline markup and accounts for trimmed leading whitespace (1.2385ms)
✔ range handles a sentence at a text node boundary and rejects changed page text (0.6928ms)
ℹ tests 13
ℹ pass 13
ℹ fail 0
```

(출력의 요약 줄 일부와 시험 열세 개 이름은 그대로 옮겼습니다.) 시험이 지키는 것은 `search.test.mjs`(검증 경계와 중복 id, 질문이 문단에 묶이는지, 범위 밖 점수 거부, 키가 응답에 안 새는지, 오류 때 가짜 일치를 안 만드는지, 긴 글 쪼개기, 문장 선택이 원문 위치로 돌아오는지), `sentences.test.mjs`(공백·소수·이모지가 든 글의 위치, 인라인 태그를 가로지르는 문장의 DOM 범위), `http.test.mjs`(토큰이 없을 때와 Vercel에서 닫힘, 틀린 메서드)입니다. 문장 범위 시험은 확장의 `text-range.js`를 `node:vm`으로 불러서 가짜 DOM에 돌립니다. 확장의 이 부분만은 브라우저 없이 Node 시험이 실제로 돌립니다.

네 번째 시험은 설치가 필요합니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
cd "${NEEDLE_DIR:?}" || return
node --test tests/package.test.mjs 2>&1 | grep -m3 -E "Cannot find|ERR_MODULE|fflate|^# (pass|fail)"
```

```text
  throw new ERR_MODULE_NOT_FOUND(packageName, fileURLToPath(base), null);
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'fflate' imported from <LAB>/work/needle/tests/package.test.mjs
  code: 'ERR_MODULE_NOT_FOUND'
```

(출력의 경로는 `<LAB>`으로 줄였습니다.) `fflate`는 `devDependencies`이고(`advanced_llm_apps/needle/package.json:21-26`) 확장 묶기 스크립트(`advanced_llm_apps/needle/scripts/package-extension.mjs:4`)도 씁니다. 이 문서는 설치하지 않았으므로 확장 묶기와 `package.test.mjs`는 **소스로만** 읽었습니다. 묶기는 허용 목록(매니페스트·스크립트·옵션 쪽·아이콘)에 든 파일만 zip에 넣으므로 `.env`와 서버 코드가 들어갈 길이 없습니다(`advanced_llm_apps/needle/scripts/package-extension.mjs:10-22`).

서버가 문장을 나누는 방식은 시험에 한 줄씩만 있어서 직접 봅니다. `sentences.mjs`는 `Intl.Segmenter("en", { granularity: "sentence" })`로 나눈 조각에서 앞뒤 공백을 뺀 시작·끝 위치를 돌려줍니다(`advanced_llm_apps/needle/server/sentences.mjs:1-11`).

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
cat > "${LABDIR:?}/spans.mjs" <<'EOF'
// 사용: node spans.mjs  → 서버가 문장을 어떻게 나누는지 본다(server/sentences.mjs 그대로)
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
const { sentenceSpans } = await import(pathToFileURL(resolve(process.env.NEEDLE_DIR, "server/sentences.mjs")).href);
for (const t of ["취소는 7일 전까지 무료입니다. 이후에는 첫날 요금이 환불되지 않습니다. 문의는 3.5일 안에 주세요.", "Dr. Kim said no. Fees apply (see sec. 3.2). Done!"])
  console.log(JSON.stringify(sentenceSpans(t).map((s) => [s.start, s.end, s.text])));
EOF
node "${LABDIR:?}/spans.mjs"
```

```text
[[0,17,"취소는 7일 전까지 무료입니다."],[18,40,"이후에는 첫날 요금이 환불되지 않습니다."],[41,57,"문의는 3.5일 안에 주세요."]]
[[0,3,"Dr."],[4,16,"Kim said no."],[17,37,"Fees apply (see sec."],[38,43,"3.2)."],[44,49,"Done!"]]
```

한국어는 문장 끝 마침표에서 맞게 나뉘고 `3.5일`의 소수점도 지킵니다. 영어 약어는 ICU의 문장 규칙이 약어 목록을 갖지 않아서 `Dr.`와 `sec.` 뒤에서 끊깁니다. 이 앱에서 끊긴 문장은 "강조할 문장 후보"가 쪼개지는 것이라, 문장 하나를 고르는 선택 질문의 보기에 `Dr.`만 있는 보기가 들어갑니다.

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 첫 시험 출력이 `pass 13`, `fail 0`이고 두 번째가 `fflate`를 못 찾는다는 오류면 됩니다.

### Step 4. 서버를 띄우고 검색을 한 번 부른다

**목적.** 가짜 게이트웨이와 앱 서버를 가드 아래서 띄우고, 확장과 웹 앱이 보내는 것과 같은 요청을 `curl`로 보냅니다.

**할 일.** `server/dev.mjs`는 `--production`이 없으면 `vite`를 불러 화면까지 서빙하고(`advanced_llm_apps/needle/server/dev.mjs:8-13`), 설치 없이는 그 줄에서 멈춥니다. 그래서 `serve.mjs`에 `--production`을 줍니다. 이 모드는 `dist/`의 정적 파일을 서빙하는데(`advanced_llm_apps/needle/server/dev.mjs:44-69`) 빌드를 하지 않았으므로 화면은 나오지 않고 `/api/*`만 돕니다(소스로 확인). 서버는 `server.listen(port, "127.0.0.1")`로 듣습니다(`advanced_llm_apps/needle/server/dev.mjs:75-77`). 포트는 `PORT`(기본 4199)입니다. 키는 `.env`(`fake-from-dotenv`)에서 옵니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
: > "${FAKE_LOG:?}"
up() { for _ in $(seq 1 50); do curl -s --noproxy '*' -o /dev/null "$1" && return 0; sleep 0.2; done; echo "서버가 안 떴습니다: $1"; return 1; }
node "${LABDIR:?}/fake-gateway.mjs" > "${LAB:?}/logs/fake.out" 2>&1 &
echo $! > "${LAB:?}/logs/fake.pid"
PORT=$APP_PORT node "${LABDIR:?}/serve.mjs" --production > "${LAB:?}/logs/app-a.out" 2>&1 &
echo $! > "${LAB:?}/logs/app-a.pid"
up "http://127.0.0.1:$FAKE_PORT/" ; up "http://127.0.0.1:$APP_PORT/api/health"
cat "${LAB:?}/logs/app-a.out"
echo "--- health"
curl -s --noproxy '*' "http://127.0.0.1:$APP_PORT/api/health"; echo
echo "--- GET /api/search"
curl -s --noproxy '*' -w ' [%{http_code}]\n' "http://127.0.0.1:$APP_PORT/api/search"
```

```text
가드 확인: 예약 주소 세 길 모두 막힘
Needle running at http://127.0.0.1:51913
--- health
{"configured":true,"model":"typesafe-ai/jev"}
--- GET /api/search
{"error":"Use POST."} [405]
```

`/api/health`의 `configured: true`는 키가 있다는 뜻일 뿐 키가 맞는지는 모릅니다(`advanced_llm_apps/needle/api/health.js:1-5`). `GET /api/search`는 405와 `Use POST.`입니다. 이제 `stay` 문서와 질문 두 개로 검색합니다. `show.mjs`는 응답에서 점수 순위와 강조 문장 위치만 간추립니다. 응답의 `scores`는 문단 전부의 점수이고 `matches`는 그 가운데 `0.58` 이상(`advanced_llm_apps/needle/server/search.mjs:4, 165`)입니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
cat > "${LABDIR:?}/show.mjs" <<'EOF'
// 사용: <응답 JSON> | node show.mjs  → 점수 순위와 강조 문장만 간추려 찍는다
let raw = "";
for await (const c of process.stdin) raw += c;
const r = JSON.parse(raw);
if (r.error) { console.log("오류:", r.error); process.exit(0); }
console.log(`threshold=${r.threshold} 점수 ${r.scores.length}개, 일치 ${r.matches.length}개, usage=${JSON.stringify(r.usage)}`);
for (const s of r.scores.slice(0, 5))
  console.log(`${s.id} p=${s.probability.toFixed(2)} ${s.probability >= r.threshold ? "일치" : "탈락"} [${s.focus.start}-${s.focus.end}] ${s.focus.text.slice(0, 60)}`);
EOF
for q in "hidden fees" "can I bring my dog?"; do
  echo "=== stay / $q"
  node "${LABDIR:?}/mkbody.mjs" stay "$q" > "${LAB:?}/logs/body.json"
  curl -s --noproxy '*' -H 'Content-Type: application/json' --data-binary @"${LAB:?}/logs/body.json" "http://127.0.0.1:$APP_PORT/api/search" | node "${LABDIR:?}/show.mjs"
done
echo "=== 가짜 서버가 받은 마지막 요청(질문 키)"
node -e 'const b=JSON.parse(require("fs").readFileSync(process.env.LAST_REQ,"utf8"));console.log(Object.keys(b),b.model,JSON.stringify(b.state.search),b.state.passages.length+"개");const k=Object.keys(b.questions);console.log(k.length+"개:",k.slice(0,3).join(","),"...");console.log(b.questions.b2.type,Object.keys(b.questions.b2.criteria).join("/"));console.log(b.questions.focus_b2.type,JSON.stringify(b.questions.focus_b2.criteria))'
echo "=== 가짜 서버 기록"
cat "${FAKE_LOG:?}"
```

```text
=== stay / hidden fees
threshold=0.58 점수 13개, 일치 5개, usage={"inputTokens":4628,"outputTokens":20}
b3 p=0.90 일치 [47-111] A property service charge of $35 per night is added at check
b7 p=0.90 일치 [0-98] You may move your stay once, at no extra charge, when reques
b4 p=0.60 일치 [0-62] A refundable security deposit of $150 is collected on arriva
b6 p=0.60 일치 [0-116] A $25 administration charge is deducted from every cancellat
b9 p=0.60 일치 [0-73] A cleaning supplement of $45 per stay applies to reservation
=== stay / can I bring my dog?
threshold=0.58 점수 13개, 일치 2개, usage={"inputTokens":4630,"outputTokens":20}
b8 p=0.60 일치 [0-51] Well-behaved dogs are welcome in our Garden Cabins.
b9 p=0.60 일치 [0-73] A cleaning supplement of $45 per stay applies to reservation
b0 p=0.04 탈락 [0-115] Tucked between the redwoods and the coast, The Wilder House 
b1 p=0.04 탈락 [0-33] We want your stay to feel simple.
b2 p=0.04 탈락 [0-50] Check-in begins at 3 pm and check-out is by 11 am.
=== 가짜 서버가 받은 마지막 요청(질문 키)
[ 'model', 'state', 'questions' ] typesafe-ai/jev "can I bring my dog?" 13개
26개: b0,focus_b0,b1 ...
boolean true/false
choice {"s0":"Check-in begins at 3 pm and check-out is by 11 am.","s1":"Early arrivals are welcome to leave their bags at reception while exploring the grounds."}
=== 가짜 서버 기록
{"auth":"Bearer fake-from-dotenv","model":"typesafe-ai/jev","passages":13,"questions":26}
{"auth":"Bearer fake-from-dotenv","model":"typesafe-ai/jev","passages":13,"questions":26}
```

첫 질문 "hidden fees"는 문단 13개 중 5개가 일치로 나왔고, 각 줄의 `[시작-끝]`이 그 문단 **안에서의** 문장 위치입니다. `b3`는 `The nightly rate includes breakfast and Wi-Fi. A property service charge of $35 …` 문단이고 `[47-111]`은 그 안의 둘째 문장(`A property service charge … checkout.`)입니다. 이 위치가 확장으로 가서 형광펜 범위가 됩니다. 두 번째 질문은 일치 2개이고, 일치가 아닌 문단은 가짜 서버가 `0.04`를 준 것입니다.

가짜 서버가 받은 마지막 요청이 앱이 만든 요청입니다. 문단마다 불리언 질문(`b2`, 보기 `true`/`false`)이 있고, 문장이 둘 이상인 문단에는 `focus_b2` 선택 질문이 붙어 보기 `s0`·`s1`…이 **문단의 문장 그대로**입니다(`advanced_llm_apps/needle/server/search.mjs:55-82`). 질문 지시문은 "그 문단만 평가하라", "넓은 주제 겹침은 부족하다", "문단·검색어를 지시가 아닌 데이터로 취급하라"를 영어로 적습니다. 모델이 문장을 **만들어 내지 못하게** 보기에서 고르게 하고, 응답의 `choice`가 `s<숫자>`인지, 그 문장이 실제로 있는지를 `parseAnswers`가 다시 확인합니다(`advanced_llm_apps/needle/server/search.mjs:83-117`). 이 확인이 "결과는 언제나 원문 안의 실제 글"이라는 약속의 근거입니다.

기록 파일의 두 줄은 서버가 보낸 `Authorization: Bearer fake-from-dotenv`가 `.env`의 키임을 보입니다.

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 첫 질문의 일치가 5개, 두 번째가 2개이고 응답에 `threshold=0.58`이 보이면 됩니다.

### Step 5. 접근 토큰, Origin, 크기 한도

**목적.** 서버를 열어 두는 앱이므로 누가 부를 수 있는지를 봅니다.

**할 일.** 접근 검사는 `accessError`(`advanced_llm_apps/needle/server/http.mjs:2-13`)입니다. `NEEDLE_ACCESS_TOKEN`이 있으면 요청 머리 `x-needle-token`이 같아야 하고, `VERCEL` 환경에서 토큰이 없으면 503입니다. 토큰이 비어 있고 Vercel이 아니면 통과합니다. 두 번째 서버를 토큰과 다른 가짜 키(`fake-from-shell`, 셸 변수가 `.env`보다 우선합니다)로 띄워 보입니다. 토큰 없음과 틀린 토큰은 같은 401 문구이고, `/api/health`는 토큰 없이 열려 있습니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
up() { for _ in $(seq 1 50); do curl -s --noproxy '*' -o /dev/null "$1" && return 0; sleep 0.2; done; echo "서버가 안 떴습니다: $1"; return 1; }
PORT=$APP2_PORT NEEDLE_ACCESS_TOKEN=lab-token AI_GATEWAY_API_KEY=fake-from-shell node "${LABDIR:?}/serve.mjs" --production > "${LAB:?}/logs/app-b.out" 2>&1 &
echo $! > "${LAB:?}/logs/app-b.pid"
up "http://127.0.0.1:$APP2_PORT/api/health"
node "${LABDIR:?}/mkbody.mjs" stay "hidden fees" > "${LAB:?}/logs/body.json"
B="http://127.0.0.1:$APP2_PORT/api/search"
echo "--- 토큰 서버(B): 없음 / 틀림 / 맞음"
curl -s --noproxy '*' -w ' [%{http_code}]\n' -H 'Content-Type: application/json' --data-binary @"${LAB:?}/logs/body.json" "$B"
curl -s --noproxy '*' -w ' [%{http_code}]\n' -H 'x-needle-token: wrong' -H 'Content-Type: application/json' --data-binary @"${LAB:?}/logs/body.json" "$B"
curl -s --noproxy '*' -o /dev/null -w '[%{http_code}]\n' -H 'x-needle-token: lab-token' -H 'Content-Type: application/json' --data-binary @"${LAB:?}/logs/body.json" "$B"
echo "--- health는 토큰 없이도 열린다(B)"
curl -s --noproxy '*' -w ' [%{http_code}]\n' "http://127.0.0.1:$APP2_PORT/api/health"
echo "--- 가짜 서버가 받은 Authorization(A는 .env, B는 셸)"
grep -o '"auth":"[^"]*"' "${FAKE_LOG:?}" | sort | uniq -c
```

```text
--- 토큰 서버(B): 없음 / 틀림 / 맞음
{"error":"Set the Needle access token in settings."} [401]
{"error":"Set the Needle access token in settings."} [401]
[200]
--- health는 토큰 없이도 열린다(B)
{"configured":true,"model":"typesafe-ai/jev"} [200]
--- 가짜 서버가 받은 Authorization(A는 .env, B는 셸)
      2 "auth":"Bearer fake-from-dotenv"
      1 "auth":"Bearer fake-from-shell"
```

Origin과 CORS는 소스에 없습니다(`advanced_llm_apps/needle/server/dev.mjs`에 `Origin`·`Access-Control`·`Host`를 보는 줄이 없음, 소스로 확인). 다른 사이트의 Origin을 단 요청 둘을 보내 봅니다. `curl`로 쓰려면 `Origin: http://…` 머리를 줘야 하는데 이 작업 상자의 `curl`이 루프백이 아닌 주소가 든 인자를 거부해서(`safe.sh`가 막았습니다), 같은 일을 Node의 `http.request`로 하는 `probe.mjs`를 썼습니다. 서버는 `127.0.0.1`에서 듣고 있습니다(`netstat`). 한도 세 가지도 이어서 봅니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
A="http://127.0.0.1:$APP_PORT/api/search"
cat > "${LABDIR:?}/probe.mjs" <<'EOF'
// 사용: node probe.mjs <포트>  → 다른 사이트의 Origin을 단 요청 둘을 보내고 응답 머리를 간추려 찍는다
import http from "node:http";
import { readFileSync } from "node:fs";
if (!process.env.LAB) throw new Error("LAB 없음");
const body = readFileSync(process.env.LAB + "/logs/body.json");
const send = (label, method, headers, payload) => new Promise((done) => {
  const req = http.request({ host: "127.0.0.1", port: Number(process.argv[2]), path: "/api/search", method, headers: { Origin: "http://evil.example", ...headers } }, (res) => {
    res.resume();
    res.on("end", () => {
      const h = Object.entries(res.headers).filter(([k]) => /^(access-control|allow|cache-control)/.test(k)).map(([k, v]) => `${k}: ${v}`);
      console.log(`${label} -> ${res.statusCode}`, h.length ? h.join(" | ") : "(CORS 머리 없음)");
      done();
    });
  });
  req.end(payload);
});
await send("OPTIONS preflight", "OPTIONS", { "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type" });
await send("POST text/plain  ", "POST", { "Content-Type": "text/plain" }, body);
EOF
node "${LABDIR:?}/probe.mjs" "$APP_PORT"
echo "--- 서버가 듣는 주소"
{ netstat -ano 2>/dev/null || netstat -ltn; } | grep -E ":($APP_PORT|$APP2_PORT|$FAKE_PORT) .*LISTEN"
echo "--- 한도 셋"
cat > "${LABDIR:?}/mklimits.mjs" <<'EOF'
import { writeFileSync } from "node:fs";
if (!process.env.LAB) throw new Error("LAB 없음");
const dir = process.env.LAB + "/logs/";
const blk = (i, n) => ({ id: `b${i}`, text: "x".repeat(n) });
writeFileSync(dir + "big.json", JSON.stringify({ query: "fees", blocks: Array.from({ length: 300 }, (_, i) => blk(i, 2000)) }));
writeFileSync(dir + "many.json", JSON.stringify({ query: "fees", blocks: Array.from({ length: 161 }, (_, i) => blk(i, 20)) }));
writeFileSync(dir + "long-query.json", JSON.stringify({ query: "q".repeat(401), blocks: [blk(0, 20)] }));
EOF
node "${LABDIR:?}/mklimits.mjs"
for f in big many long-query; do
  printf '%s (%s바이트): ' "$f" "$(wc -c < "${LAB:?}/logs/$f.json" | tr -d ' ')"
  curl -s --noproxy '*' -w ' [%{http_code}]\n' -H 'Content-Type: application/json' --data-binary @"${LAB:?}/logs/$f.json" "$A"
done
```

```text
OPTIONS preflight -> 405 cache-control: no-store | allow: POST
POST text/plain   -> 200 cache-control: no-store
--- 서버가 듣는 주소
  TCP    127.0.0.1:51911        0.0.0.0:0              LISTENING       49492
  TCP    127.0.0.1:51913        0.0.0.0:0              LISTENING       36536
  TCP    127.0.0.1:51915        0.0.0.0:0              LISTENING       51132
--- 한도 셋
big (607117바이트): {"error":"Document is too large."} [413]
many (7001바이트): {"error":"Search between 1 and 160 passages at a time."} [400]
long-query (466바이트): {"error":"Keep your search under 400 characters."} [400]
```

읽는 법은 이렇습니다.

- 응답에 CORS 머리가 하나도 없고 preflight(`OPTIONS`)는 405입니다. 그런데 `Content-Type: text/plain`으로 보낸 POST는 **200으로 처리됐습니다.** 서버가 본문을 `JSON.parse`할 때 `Content-Type`을 보지 않기 때문입니다(`advanced_llm_apps/needle/api/search.js:12-18`).
- MDN의 CORS 문서에 따르면 `text/plain`·`application/x-www-form-urlencoded`·`multipart/form-data`만 preflight 없는 "단순 요청"이 될 수 있고, `application/json`이나 `x-needle-token` 같은 사용자 머리는 preflight를 부릅니다. 그리고 응답에 `Access-Control-Allow-Origin`이 없으면 그 페이지의 스크립트는 응답을 **읽지 못합니다.** 그러니 내가 연 어떤 웹 페이지가 브라우저에서 `127.0.0.1:4199`로 `text/plain` POST를 쏘면(실제 브라우저로는 시험하지 않았고, 위 규칙과 Node 요청으로 짐작한 것입니다), 결과는 못 읽어도 서버는 검색을 하고 **내 게이트웨이 키로 요금이 나갑니다.** 다만 크롬 142부터는 Local Network Access 허락 창이 공용 사이트에서 루프백으로 가는 요청에 사용자 허락을 요구합니다(Chrome 개발자 블로그, 이 문서는 확인하지 못했습니다). 그 창은 브라우저 쪽 방어이고 서버는 여전히 열려 있으므로 토큰 권고는 그대로입니다.
- 토큰을 두면 이 길이 막힙니다. 토큰이 있으면 서버는 `x-needle-token` 없는 요청을 401로 거절하고, 그 머리를 붙이려는 다른 사이트의 요청은 preflight를 먼저 보내야 하는데 `OPTIONS`가 405라 거기서 멈춥니다. 앱 README는 "로컬에서는 토큰을 비워 두라"고 하지만, 키가 든 서버라면 로컬에서도 `NEEDLE_ACCESS_TOKEN`을 두고 확장 설정에 같은 값을 넣는 편이 안전합니다.
- 한도: 본문이 512,000바이트를 넘으면 413(`advanced_llm_apps/needle/server/dev.mjs:32-39`, 서버는 읽는 도중 끊습니다), 문단 161개나 질문 401자는 400입니다(`advanced_llm_apps/needle/server/search.mjs:21-54`). 위 세 줄이 각각 607,117·7,001·466바이트 본문의 결과입니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 토큰 서버의 세 응답이 401·401·200, 단순 요청이 200, 한도 셋이 413·400·400이면 됩니다.

### Step 6. 게이트웨이가 실패할 때

**목적.** 앱은 "가짜 일치를 만들지 않는다"고 약속합니다. 게이트웨이의 실패가 어떻게 전해지는지 봅니다.

**할 일.** 가짜 게이트웨이에 특별한 질문 세 개를 보냅니다(`__401__`·`__429__`·`__incomplete__`가 질문에 있으면 그 오류를 흉내 냅니다). 이어서 레시피 문서 한 건의 요청 크기를 잽니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
A="http://127.0.0.1:$APP_PORT/api/search"
for q in __401__ __429__ __incomplete__; do
  node "${LABDIR:?}/mkbody.mjs" recipe "$q" > "${LAB:?}/logs/body.json"
  printf '%s -> ' "$q"
  curl -s --noproxy '*' -w ' [%{http_code}]\n' -H 'Content-Type: application/json' --data-binary @"${LAB:?}/logs/body.json" "$A"
done
echo "--- 레시피 문서 한 건: 앱이 보낸 본문과 게이트웨이로 간 요청의 크기(바이트)"
printf '앱 본문 %s\n' "$(wc -c < "${LAB:?}/logs/body.json" | tr -d ' ')"
cat > "${LABDIR:?}/sizes.mjs" <<'EOF'
// 사용: node sizes.mjs  → 가짜 서버가 받은 마지막 요청이 무엇으로 이루어졌는지 바이트로 나눈다
import { readFileSync } from "node:fs";
if (!process.env.LAST_REQ) throw new Error("LAST_REQ 없음");
const b = JSON.parse(readFileSync(process.env.LAST_REQ, "utf8"));
const n = (x) => JSON.stringify(x).length;
const qs = Object.values(b.questions);
const sum = (f) => qs.reduce((t, q) => t + f(q), 0);
const bool = qs.filter((q) => q.type === "boolean"), choice = qs.filter((q) => q.type === "choice");
console.log(`요청 ${n(b)} = state ${n(b.state)} + questions ${n(b.questions)} (질문 ${qs.length}개: boolean ${bool.length}, choice ${choice.length})`);
console.log(`질문 지시문 ${sum((q) => n(q.instructions))} · boolean 기준 ${bool.reduce((t, q) => t + n(q.criteria), 0)} · choice 보기(문장 사본) ${choice.reduce((t, q) => t + n(q.criteria), 0)} · 문단 본문 ${n(b.state.passages.map((p) => p.text))}`);
EOF
node "${LABDIR:?}/sizes.mjs"
```

```text
__401__ -> {"error":"The server’s AI Gateway key was rejected."} [502]
__429__ -> {"error":"Too many searches. Give it a moment and try again."} [429]
__incomplete__ -> {"error":"Jev returned an incomplete evaluation. Please try again."} [502]
--- 레시피 문서 한 건: 앱이 보낸 본문과 게이트웨이로 간 요청의 크기(바이트)
앱 본문 1601
요청 10988 = state 1603 + questions 9336 (질문 15개: boolean 8, choice 7)
질문 지시문 5511 · boolean 기준 1656 · choice 보기(문장 사본) 1353 · 문단 본문 1412
```

`search()`는 게이트웨이의 401을 "서버의 키가 거절됐다"로, 402·403·429도 각자의 문구로 바꾸지만, HTTP 상태는 429만 그대로고 나머지는 모두 502입니다(`advanced_llm_apps/needle/server/search.mjs:142-154`). 그래서 확장 쪽에서 "502"만 보면 키 문제인지 일시 장애인지 알 수 없고 문구를 읽어야 합니다. 게이트웨이에 닿지 못하면(네트워크 오류) `Could not reach AI Gateway`, 45초가 넘으면 `Jev took too long`입니다(`advanced_llm_apps/needle/server/search.mjs:132-141`). 확장은 55초를 기다립니다(`advanced_llm_apps/needle/extension/background.js:32`). Vercel 설정의 함수 제한은 60초(`advanced_llm_apps/needle/vercel.json:5`)라 이 세 숫자가 45 < 55 < 60으로 겹치지 않게 놓였습니다. `answers`가 비어 있으면 `incomplete evaluation`으로 502이고, 불완전한 응답 한 조각이라도 있으면 전체가 실패합니다(검색 결과를 일부만 돌려주지 않습니다).

크기는 `makePayload`가 만드는 질문에서 생깁니다. 레시피 문서는 앱 본문 1,601바이트가 게이트웨이 요청 10,988바이트(질문 15개, 약 6.9배)가 됐고, 그 가운데 질문 쪽이 9,336바이트입니다. 위 `sizes.mjs`가 나눈 것을 보면 **질문마다 똑같이 붙는 영어 지시문**이 5,511바이트, 불리언 질문의 기준(`true`/`false` 설명)이 1,656바이트로 가장 큽니다(`advanced_llm_apps/needle/server/search.mjs:60-65, 71`). 문장이 둘 이상인 문단의 선택 질문에 문장이 다시 실리는 몫은 1,353바이트이고, 문단 본문 자체는 1,412바이트입니다. 질문 수는 문단 수 + 문장이 둘 이상인 문단 수라서 문서가 길어질수록 이 고정 문구가 그 수만큼 되풀이됩니다. 진짜 요금은 입력 토큰으로 계산되므로 이 배수가 중요합니다. 이 문서는 진짜 단가를 모르고, 가짜 서버의 `usage`(길이를 4로 나눈 값)는 지어낸 값입니다.

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** 세 질문이 502·429·502로 나오고 마지막 두 줄에 크기가 찍히면 됩니다.

### Step 7. 확장과 웹 앱은 소스로 읽고, 서버를 끈다

**목적.** 실행하지 않은 두 부분이 위에서 확인한 서버와 어떻게 맞물리는지를 소스로 따라갑니다. 이 단계의 내용은 모두 **소스로 확인**한 것이고 브라우저에서는 돌려 보지 않았습니다.

**할 일.** 확장의 흐름은 이렇습니다.

1. 아이콘을 누르면 `background.js`가 `text-range.js`와 `content.js`를 그 탭에 넣고, 넣지 못하면(크롬 시스템 쪽 등) 설정 쪽을 엽니다(`advanced_llm_apps/needle/extension/background.js:5-14`). 이미 떠 있으면 `content.js`가 패널을 닫습니다(`advanced_llm_apps/needle/extension/content.js:2-6`). 패널은 shadow root(`mode: "open"`)에 그려져 페이지 CSS와 섞이지 않습니다(`advanced_llm_apps/needle/extension/content.js:10`).
2. 글자를 입력하고 0.7초 쉬면 검색합니다(`advanced_llm_apps/needle/extension/content.js:201-208`). `collect()`는 `p,li,pre,blockquote,h1~h4,td,figcaption`를 모읍니다. `nav,header,footer,script,style`과 편집 가능한 영역 안, 보이지 않는 요소는 빼고, 안에 다른 후보를 품은 요소는 건너뛰어 가장 안쪽 문단만 남깁니다. 12자 미만은 버리고 2,200자를 넘는 문단은 건너뛰며 "일부 생략"이라 알립니다. 160개·60,000자에서 멈춥니다(`advanced_llm_apps/needle/extension/content.js:26-60`). 서버 한도와 같은 숫자라서 서버가 `invalid passage`로 거절할 일이 드뭅니다.
3. 검색은 `chrome.runtime.sendMessage`로 서비스 워커에 맡기고(`advanced_llm_apps/needle/extension/content.js:144-150`), 워커가 저장소에서 서버 주소·토큰을 읽어 `` fetch(`${server}/api/search`) ``를 보냅니다(`advanced_llm_apps/needle/extension/background.js:15-33`). 페이지가 아니라 워커가 보내고, `manifest.json`의 `host_permissions`에 `127.0.0.1`·`localhost`가 선언돼 있습니다(`advanced_llm_apps/needle/extension/manifest.json:6-8`). 서버가 CORS 머리를 하나도 주지 않는데도 확장이 서버를 부를 수 있는 것은 이 권한 덕이라고 알려져 있지만, 이 문서는 브라우저에서 확인하지 못했습니다.
4. 응답의 `matches`마다 문단 전체를 옅은 초록(`needle-matches`), 서버가 고른 문장을 진한 초록(`needle-sentences`), 지금 고른 것을 가장 진한 초록(`needle-active`)으로 칠합니다. CSS Custom Highlight API(`CSS.highlights`, `Highlight`)를 쓰므로 DOM을 바꾸지 않습니다. 이 API가 없으면 칠하지 않고 스크롤만 합니다(`advanced_llm_apps/needle/extension/content.js:70-118`). `manifest.json`의 `minimum_chrome_version`은 105입니다(`advanced_llm_apps/needle/extension/manifest.json:35`).
5. 서버가 준 글자 위치를 `NeedleTextRange`가 DOM `Range`로 바꿉니다. 문단의 `textContent`가 보낸 글과 달라졌으면(그 사이 페이지가 바뀌었으면) `null`을 돌려주고 그 문장은 칠하지 않습니다. 앞의 공백 길이를 더하고, 텍스트 노드를 차례로 걸으며 시작·끝 노드를 찾습니다. 그래서 문장이 `<b>`나 `<a>`로 쪼개진 텍스트 노드를 가로질러도 됩니다(`advanced_llm_apps/needle/extension/text-range.js:1-39`, Step 3의 시험이 이 부분을 돌렸습니다).
6. 설정 쪽은 주소가 `http`나 `https`인지, 원격이면 `https`인지 보고(`advanced_llm_apps/needle/extension/options.js:12-23`), 그 서버에 대한 권한을 `chrome.permissions.request`로 요청합니다. 요청하는 출처는 `프로토콜//호스트/*` 꼴이라 포트는 들어가지 않습니다(`advanced_llm_apps/needle/extension/options.js:24-26`). 토큰은 `chrome.storage.local`에 평문으로 저장됩니다(`advanced_llm_apps/needle/extension/options.js:28-31`). 앱 README도 이를 밝힙니다.
7. 단축키는 `manifest.json`의 `_execute_action`이 `Ctrl+Shift+F`(macOS `Command+Shift+F`)로 정합니다(`advanced_llm_apps/needle/extension/manifest.json:20-28`). 패널이 열려 있을 때 `content.js`가 가로채는 `Ctrl/Cmd+F`는 입력칸으로 초점을 옮길 뿐입니다(`advanced_llm_apps/needle/extension/content.js:178-189`). 앱 README는 "아이콘을 누르거나 Cmd+F / Ctrl+F"라고 써서 이 둘과 어긋납니다.

웹 앱(`src/`)은 같은 서버를 같은 본문 모양으로 부릅니다. 문서를 고르면 `getBlocks`가, 붙여 넣은 글은 `splitDocument`가 문단 블록을 만듭니다. `splitDocument`는 빈 줄로 나누고 1,800자를 넘는 덩어리는 공백에서 자릅니다(`advanced_llm_apps/needle/src/search.js:1-18`, 160개를 넘으면 거절 `advanced_llm_apps/needle/src/App.jsx:219-223`). 검색은 650ms 쉬면 시작하고, 같은 문서·질문·토큰이면 서버에 다시 묻지 않고 결과 25개까지 기억합니다(`advanced_llm_apps/needle/src/App.jsx:87-95, 113-127`). 토큰은 `sessionStorage`에 둡니다(`advanced_llm_apps/needle/src/App.jsx:47-49`). 시작할 때 `/api/health`를 불러 키가 있는지 알립니다(`advanced_llm_apps/needle/src/App.jsx:61-64`).

진짜로 쓰려면(**이 문서는 실행하지 않았습니다**) 앱 README대로 `advanced_llm_apps/needle`에서 `npm ci`로 설치하고 `.env`에 AI Gateway 키를 넣은 뒤 `npm run dev`를 돌립니다. `npm run dev`는 먼저 `predev`로 확장을 zip으로 묶습니다(`advanced_llm_apps/needle/package.json:7-8`). `npm ci`를 돌리지 않은 까닭은 설치 스크립트가 임의 코드를 돌리기 때문입니다. `package-lock.json`(lockfileVersion 3, 패키지 118개)에서 `hasInstallScript`가 참인 것은 `esbuild` 0.25.12와 macOS 전용 선택 의존성 `fsevents` 2.3.3 둘입니다. 스크립트가 무엇을 하는지는 lock 파일에 적혀 있지 않아 확인하지 못했습니다. lock이 가리키는 판은 `vite` 6.4.3, `react` 19.3.0, `fflate` 0.8.3입니다. 확장은 크롬의 `chrome://extensions`에서 개발자 모드로 `extension/` 폴더를 **압축해제된 확장**으로 올립니다. 이 문서는 크롬을 띄우지 않았습니다.

서버를 끕니다. 이 블록은 내가 띄운 세 프로세스의 PID 파일만 읽고, 살아 있는지 확인한 뒤에만 `kill`을 보냅니다.

```bash
source "${LAB:?LAB을 먼저 정하세요}/env.sh" || return
for n in app-a app-b fake; do
  pid=$(cat "${LAB:?}/logs/$n.pid" 2>/dev/null) || continue
  if kill -0 "$pid" 2>/dev/null; then kill "$pid" && echo "$n($pid) 끔"; else echo "$n($pid) 이미 없음"; fi
done
sleep 1
for p in "$FAKE_PORT" "$APP_PORT" "$APP2_PORT"; do
  if curl -s --noproxy '*' -o /dev/null "http://127.0.0.1:$p/"; then echo "$p 아직 응답함"; else echo "$p 꺼짐"; fi
done
```

```text
app-a(2231) 끔
app-b(2320) 끔
fake(2230) 끔
51911 꺼짐
51913 꺼짐
51915 꺼짐
```

![Step 7까지의 구성](diagrams/step7.svg)

**확인.** 마지막 세 줄이 모두 `꺼짐`이면 됩니다. (포트가 닫혔는지는 `curl`로 봅니다. `netstat` 출력은 운영체제마다 다릅니다.)

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

아래 다섯 그림이 이 그림의 화살표 사이에서 일어나는 일을 나눠 그렸습니다. 같은 메시지는 한 그림에만 있습니다.

![설정 읽기·쓰기](diagrams/extra-sequence-settings.svg)

![서버 문 앞의 접근 검사](diagrams/extra-sequence-token.svg)

![서버 안의 호출](diagrams/extra-sequence-call.svg)

![검증·질문·점수](diagrams/extra-sequence-search.svg)

![강조 칠하기](diagrams/extra-sequence-paint.svg)

페이지에서 질문을 입력하고 0.7초 쉬면 `content.js`가 보이는 문단을 모읍니다(`collect`, 최대 160개). 그것을 `NEEDLE_SEARCH`로 워커에 맡기면 워커는 저장소에서 서버 주소·토큰을 읽고(설정 그림, 그 값은 `options.js`가 저장한 것) `POST /api/search`를 보냅니다. 서버 안에서는 `dev.mjs`가 `http.mjs`의 `accessError`로 요청 머리를 보고 본문을 512,000바이트까지 읽은 뒤 `api/search.js`의 핸들러를 부르고, 핸들러가 `accessError`를 한 번 더 부른 다음 `search()`를 부릅니다(접근 검사 그림과 호출 그림). `search()`는 본문을 검증하고(`validate`) 질문을 만들며(`makePayload`, 이때 `sentences.mjs`가 문장 범위를 줍니다) 게이트웨이에 `Bearer` 키로 `POST /v1/evaluate`를 보내고, `answers`를 `parseAnswers`가 해석해 `0.58` 이상만 `matches`로 가립니다(검증·질문·점수 그림). 결과는 `api/search.js`를 거쳐 `dev.mjs`가 `200` JSON으로 워커에 돌려주고, 워커가 `sendResponse`로 `content.js`에 넘깁니다(첫 그림 끝). `content.js`는 `text-range.js`로 글자 위치를 DOM 범위로 바꿔 형광펜을 칠하고 "n of m connections"를 띄웁니다(강조 그림). 아이콘을 누를 때 워커가 스크립트를 넣는 일은 [`extra-extension`](diagrams/extra-extension.svg)에 있습니다.

## 실행 체크리스트

- [ ] `LAB`이 저장소 밖의 새 절대 경로이고, 점검이 통과해 `env.sh`가 만들어졌다
- [ ] 사본에 `server`·`api`·`src`·`tests`·`extension`이 있고 `.env`에는 가짜 키 한 줄뿐이다
- [ ] `guard.mjs`가 "예약 주소 세 길 모두 막힘"을 찍는다
- [ ] 시험 13개가 통과하고 `package.test.mjs`는 `fflate`가 없어 실패한다(설치하지 않았으므로 정상)
- [ ] `/api/health`가 `configured: true`, `GET /api/search`가 405다
- [ ] 같은 질문의 일치가 5개(hidden fees)와 2개(can I bring my dog?)다
- [ ] 토큰 서버가 없음·틀림 401, 맞음 200이고, 단순 요청(`text/plain`)이 200으로 처리된다
- [ ] 413·400·400이 나오고, `__401__`·`__429__`·`__incomplete__`가 502·429·502다
- [ ] 마지막 세 포트가 모두 `꺼짐`이다
- [ ] 원본 폴더 `advanced_llm_apps/needle`에 `git status`로 본 변경이 없다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| 점검이 `LAB을 자기 경로로 바꾸세요`로 멈춘다 | `LAB`이 자리 표시 값 그대로다 | 저장소 밖의 새 절대 경로로 바꾼다 |
| `npm test`가 `fflate`를 못 찾는다 | `package.test.mjs`가 `fflate`(devDependency)를 쓴다 | 시험 셋만 `node --test`로 돌린다. 진짜 설치(`npm ci`)는 이 문서가 하지 않았다 |
| 설치 없이 `node server/dev.mjs`가 멈춘다 | `--production`이 없으면 `vite`를 불러 화면을 서빙한다(소스로 확인, `advanced_llm_apps/needle/server/dev.mjs:8-13`) | `--production`을 주고 `/api/*`만 쓴다 |
| `가드가 걸리지 않았습니다. 멈춥니다.` | `guard.mjs`의 두 시도 중 하나라도 막히지 않았다 | `guard.mjs`를 고치지 말고 파일 내용이 위와 같은지 본다 |
| `curl`이 프록시를 거쳐 실패한다 | 셸의 프록시 변수가 루프백에도 쓰인다 | `curl --noproxy '*'`를 쓴다. Node는 `NODE_USE_ENV_PROXY=1`일 때 `NO_PROXY`에 루프백을 적어야 한다(Step 2) |
| 확장 단축키 Ctrl+F가 아무 일도 안 한다 | 기본 단축키는 Ctrl+Shift+F다(`advanced_llm_apps/needle/extension/manifest.json:20-28`) | 아이콘을 누르거나 `chrome://extensions/shortcuts`에서 바꾼다(앱 README도 같은 곳을 안내한다) |
| 401 `Set the Needle access token in settings.` | 서버에 `NEEDLE_ACCESS_TOKEN`이 있는데 요청에 `x-needle-token`이 없거나 다르다 | 확장 설정(또는 웹 앱의 "How it works")에 같은 값을 넣는다 |
| 503 `Set NEEDLE_ACCESS_TOKEN on the server…` | `VERCEL` 환경인데 토큰이 없다 | 서버 환경 변수에 토큰을 둔다 |
| 502 `The server’s AI Gateway key was rejected.` | 게이트웨이가 401을 줬다. 402(크레딧·계정 확인)·403(Jev 접근 없음)도 같은 502로 오고 문구만 다르다 | 문구를 읽고 키·크레딧을 본다. 429만 상태가 429다 |
| `.env`를 고쳤는데 그대로다 | `.env`는 서버가 시작할 때 한 번만 읽고(`advanced_llm_apps/needle/server/env.mjs:1-7`), 이미 있는 환경 변수가 `.env`보다 우선한다(Step 5) | 서버를 다시 띄운다 |
| `AI_GATEWAY_KEY_FILE`을 줬는데 키가 없다고 한다 | 그 경로의 파일을 읽다 실패하면 오류를 삼키고 빈 키가 된다(`advanced_llm_apps/needle/server/search.mjs:11-20`) | 절대 경로와 읽기 권한을 확인한다. 가리키는 것은 키 한 줄이 든 파일이다 |
| 413 `Document is too large.` | 본문이 512,000바이트를 넘었다 | 문단을 줄인다 |
| 강조가 안 보이고 스크롤만 된다 | 브라우저에 CSS Custom Highlight API가 없거나(`advanced_llm_apps/needle/extension/content.js:93`), 그 사이 문단 글이 바뀌었다(`advanced_llm_apps/needle/extension/content.js:78`) | 크롬을 105 이상으로 올리거나 다시 검색한다 |
| 긴 문단이 검색에서 빠진다 | 2,200자를 넘는 문단은 건너뛴다(`advanced_llm_apps/needle/extension/content.js:48-51`) | 화면의 "일부 생략" 표시를 본다 |
| `address already in use` | 포트가 쓰인다 | `env.sh`의 `FAKE_PORT`·`APP_PORT`·`APP2_PORT`를 49152~65535의 다른 값으로 바꾼다 |

## 더 해보기

- 스크래치 사본의 `server/dev.mjs`에서 `/api/search`를 처리하기 전에 `Origin` 머리가 있고 허용 목록(없음, 크롬 확장 `chrome-extension://…`, `http://127.0.0.1:4199`)에 없으면 403으로 거절하게 고치고, `probe.mjs`의 `text/plain` POST가 200에서 403으로 바뀌는지 보세요. 확장의 워커가 보내는 요청에 어떤 `Origin`이 붙는지는 이 문서가 확인하지 못했습니다.
- `advanced_llm_apps/needle/server/search.mjs:67-75`처럼 문장을 보기로 다시 싣는 줄을 빼고 문장 번호만 고르게 해도 줄어드는 것은 Step 6에서 잰 1,353바이트쯤입니다. 더 큰 몫은 질문마다 되풀이되는 지시문(5,511바이트)이니, 지시문을 짧게 고치거나 문단 id만 다르게 하나로 합친 질문 구조를 스크래치 사본에 만들고 `sizes.mjs`로 요청 크기를 다시 재 보세요. 모델이 같은 정확도를 내는지는 가짜 서버로는 알 수 없으니 진짜 키를 가진 뒤에 같은 질문 열 개로 견줘 보세요.
- `sentences.mjs`에 `Dr.`·`sec.` 같은 영어 약어 목록을 두어 그 뒤에서는 끊지 않게 고치고 `spans.mjs`로 `Dr. Kim said no.`가 한 문장으로 나오는지 보세요. 한국어 약어(`제3조 제1항` 같은 법령 인용)는 이 문서가 시험하지 않았습니다.

## 다음 날 예고

[Day 163 · 🌀 Ripple - Change One Thing, Find What Else Needs to Change](../day163-ripple/README.md) — 볼륨 17의 마지막 날이고 이번에도 확장 + 로컬 Node 서버 + 외부 모델 API의 꼴입니다. `advanced_llm_apps/ripple`에는 Google Docs 안에서 도는 확장(`extension/content.js` 680줄, `ui.js` 361줄, `bootstrap.js` 336줄)과 서버(`server.mjs`), TypeSafe의 결정 API를 부르는 `jev.mjs`, Gemini를 부르는 `suggestions.mjs`, 시험 여덟 개가 있습니다. Needle은 모델 하나(Jev)가 고르기만 했다면 Ripple은 Jev가 "어느 문장이 어긋나는가"를 찾고 Gemini가 고친 문장 초안을 쓰며, 문서는 사용자가 누를 때만 바뀐다고 앱 README가 적습니다(소스로 어떻게 지키는지는 Day 163에서 읽습니다).
