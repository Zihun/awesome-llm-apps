# Day 163 · 🌀 Ripple - Change One Thing, Find What Else Needs to Change

> 볼륨 17 🔎 AI 브라우저 도구 · 난이도 ★★★ · 예상 소요 120분(손으로 하는 일이 많습니다. 파일 다섯을 직접 만들고, 터미널 셋에서 서버 둘을 띄우고, 확장 소스 1,660줄 가운데 문서를 읽고 고치는 길을 따라 읽고, 소스와 출력을 맞대 보는 데 시간이 듭니다) · API 비용 대략 0원(이 문서는 TypeSafe도 Gemini도 한 번도 부르지 않았습니다. 진짜 키로 쓸 때의 호출 수는 Step 4와 Step 5에 셉니다) · 원본 앱: `advanced_llm_apps/ripple`

## 오늘 만들 것

Google Docs에서 한 문장을 고치면 "같이 고쳐야 할 다른 문장"을 찾아 밑줄을 긋고, 고친 문장 후보를 카드로 보여 주고, 독자가 누르면 문서에 직접 적용해 주는 Chrome 확장을 따라 봅니다. 확장(`extension/`, JavaScript 약 1,660줄)과 `127.0.0.1:4212`에서 도는 Node 백엔드(`server.mjs`·`jev.mjs`·`suggestions.mjs`·`config.mjs`, 약 470줄), 시험 여덟 파일(1,460줄)로 이루어지고, `package.json`에 의존성이 없습니다. 충돌 판정은 TypeSafe의 Jev가, 수정안은 Gemini가 맡습니다. 볼륨 17을 닫는 날입니다. 이 볼륨이 어떤 꼴(브라우저 확장 + 로컬 Node 백엔드 + LLM API)인지는 [Day 162](../day162-needle/README.md)가 맡고, 오늘은 그 꼴 안에서 Ripple만 봅니다.

이 문서는 브라우저도 확장도 띄우지 않았고, 진짜 API도 부르지 않았고, `npm`을 한 번도 돌리지 않았습니다. 확장의 동작은 **소스를 읽고**, 그 소스를 불러 쓰는 앱의 시험 53개를 돌려 확인했습니다. 백엔드는 진짜로 띄웠지만 TypeSafe와 Gemini 자리에는 **내가 쓴 가짜 서버**가 있습니다. 가짜 서버는 모델이 아니라 정규식 몇 줄입니다. 그래서 아래의 "Zoom 문장이 충돌로 나온다"는 출력은 요청과 응답의 **모양과 배선**을 보이는 것이지 Jev나 Gemini가 잘한다는 증거가 아닙니다. 알게 된 것은 여덟입니다.

1. 확장이 하는 일은 두 세계로 나뉩니다. 문서 글을 읽고 고치는 `bootstrap.js`는 페이지 안(MAIN 세계)에서 Docs의 내부 함수 `_docs_annotate_getAnnotatedText`를 부르고, 나머지는 격리된 `content.js`가 맡습니다. 둘은 `postMessage`로만 말합니다(Step 2). 이 내부 함수는 구글이 공개한 API가 아니라 확장 전용으로 노출해 둔 것이라고 앱 README가 밝힙니다.
2. 고친 곳을 찾는 일은 모델 없이 `core.js`가 합니다. 앞뒤가 같은 글자는 건너뛰고 달라진 구간이 걸친 문장을 "바꾼 문장"으로 잡아, 나머지 문장 전부를 후보로 보냅니다. 영어 문장 분리기(`Intl.Segmenter("en")`)를 씁니다(Step 2).
3. 백엔드는 문장마다 Jev에게 `choice` 질문 하나씩을 묻습니다. 12문장씩 묶어 최대 둘을 동시에 보내고, **묶음마다 후보 문장 전체를 다시 싣습니다**(Step 4).
4. Jev가 `likely_conflict`라고 해도 확률이 0.8 미만이면 `worth_reviewing`(0.45 이상) 또는 `unaffected`로 내려갑니다. 그리고 확장은 `likely_conflict`만 남깁니다. 가짜 응답으로 `worth_reviewing` 문장이 밑줄도 수정안도 받지 못하는 것을 확인했습니다(Step 4).
5. 수정안은 문장 하나에 `replace`·`delete`·`keep`·`needs_info` 넷 중 하나입니다. 시스템 지시문(3,757자)이 예시를 길게 들고 있고, 그 예시 가운데 다섯은 앱의 라이브 평가 스크립트 사례와 거의 같습니다(Step 5).
6. 서버는 `127.0.0.1`에만 듣고(`netstat`로 확인), Host·Origin·`X-Ripple-Client`·본문 50,000바이트를 검사합니다. 허용 Origin은 `manifest.json`의 `key`에서 계산한 확장 ID 하나이고, 그 ID는 `bootstrap.js`가 Docs에 내세우는 ID와 같습니다(Step 6).
7. 문서 글은 서버에 저장되지도 로그에 남지도 않습니다(`server.mjs`의 `console`은 시작 메시지 하나). 다만 TypeSafe와 Google에는 갑니다(Step 4·5).
8. `advanced_llm_apps/ripple/scripts/evaluate-suggestions.mjs`는 진짜 Gemini를 부르므로 **돌리지 않았습니다**(Step 5).

![완성 아키텍처](diagrams/overview.svg)

위 그림은 묶음 사이의 관계만 보입니다. 묶음 안 상자 사이의 관계는 [`extra-extension`](diagrams/extra-extension.svg)(확장)과 [`extra-backend`](diagrams/extra-backend.svg)(백엔드)에, 요청의 순서는 아래 "요청 한 건이 흐르는 과정"의 두 그림에, 문서에 적용하는 순서는 Step 2의 [`extra-apply`](diagrams/extra-apply.svg)에 그렸습니다.

![확장 안의 구조](diagrams/extra-extension.svg)

![백엔드 안의 구조](diagrams/extra-backend.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Node.js 22 이상 | 백엔드, 시험, 가짜 서버. `package.json`의 `engines`가 22 이상입니다. 이 문서는 24.12.0으로 확인했습니다 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 참고 |
| bash(Git Bash) | 아래 명령 전부. **이 문서는 bash 전용입니다**(PowerShell 판은 싣지 않았습니다) | Windows는 Git for Windows |
| git, 이 저장소의 클론 | 원본 폴더를 읽고 사본을 만듭니다 | `git clone https://github.com/Shubhamsaboo/awesome-llm-apps` |
| npm | **필요 없습니다.** 의존성도 설치 스크립트도 없습니다(`package.json`의 `scripts`는 `start`·`test`·`package` 셋뿐이고 `dependencies` 필드가 없습니다). 이 문서는 `npm`을 쓰지 않고 `node`를 바로 불렀습니다 | 없음 |
| Chrome 또는 Brave | 확장을 진짜로 쓸 때만. **이 문서는 쓰지 않았습니다** | 앱 README의 "Load unpacked" |
| TypeSafe API 키(Jev 접근 권한), Gemini API 키 | 진짜로 쓸 때만. **이 문서는 가짜 키 `fake-…`만 썼습니다** | [TypeSafe 콘솔](https://docs.typesafe.ai/introduction/quickstart), [Google AI Studio](https://aistudio.google.com/apikey) |
| `zip` 명령 | `npm run package`(확장 묶기)에만. 이 컴퓨터(Git Bash)에는 `zip`이 없어서 **돌리지 않았습니다**(소스 `package.mjs:10-12`) | 필요할 때만 |

터미널은 둘을 씁니다. 가짜 서버와 앱 서버를 한 터미널씩 띄우고(터미널 A·B), 명령은 터미널 C에서 칩니다. 세 터미널 모두 Step 1의 환경 파일을 불러옵니다.

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 문서 입출력 | 600ms마다 문서 글을 읽어 보내고, Apply 요청이 오면 선택·붙여넣기·확인을 한다 | `advanced_llm_apps/ripple/extension/bootstrap.js:1-336` |
| 조정 | 쉬는 시간 재기(1.9초), 바뀐 곳 찾기, 요청 보내기, 결과 보관, Apply 거래 | `advanced_llm_apps/ripple/extension/content.js:1-680` |
| 문장·차이 | 문장 나누기, 앞뒤 글 비교, 추적 중인 "바꾼 사실" 관리 | `advanced_llm_apps/ripple/extension/core.js:2-137` |
| 카드 화면 | 그림자 DOM 안의 마커·카드·상태 칩 | `advanced_llm_apps/ripple/extension/ui.js:1-361` |
| 중계 | 허용된 발신자의 `health`·`check`·`suggest`를 백엔드로 전달 | `advanced_llm_apps/ripple/extension/background.js:1-63` |
| 적용 검사 | 문서가 기대한 꼴로 바뀌었는지(공백 접힘 허용) | `advanced_llm_apps/ripple/extension/correction.js:1-37` |
| 문지기 | 호스트·Origin·헤더 검사, 동시 요청 제한, 본문 한도 | `advanced_llm_apps/ripple/server.mjs:31-84` |
| 충돌 판정 | 질문 묶음을 만들고 TypeSafe를 부르고 상태로 바꾼다 | `advanced_llm_apps/ripple/jev.mjs:7-160` |
| 수정안 | Gemini 요청과 응답 검사 | `advanced_llm_apps/ripple/suggestions.mjs:2-176` |
| 키 | `.env` 또는 환경변수에서 읽는다(요청마다) | `advanced_llm_apps/ripple/config.mjs:4-27` |
| 시험 | 여덟 파일 53개. 확장 파일을 가짜 브라우저 안에서 돌린다 | `advanced_llm_apps/ripple/tests/*.test.mjs` |
| 이 문서의 가드·가짜 서버·시험 클라이언트 | 루프백 가드, 가짜 TypeSafe·Gemini, 확장 흉내 | 코드 없음(Step 2~3에서 직접 만듦) |

## 단계별 진행

### Step 1. 앱을 사본으로 두고 시험 53개를 돌린다

**목적.** 원본에는 아무것도 쓰지 않고, 앱 사본에서 시험이 도는지 봅니다. 시험은 이 앱이 확장을 어떻게 시험하는지도 알려 줍니다.

**할 일.** 저장소 루트에서 시작합니다. `LAB`은 저장소 밖의 새 폴더로 자기 경로로 바꿉니다. 블록은 `LAB`이 비었거나 자리 표시 값 그대로이거나 절대 경로가 아니거나 `.claude`·`.agents` 같은 에이전트 설정 폴더(또는 `CLAUDE_CONFIG_DIR`) 아래이면 폴더를 하나도 만들지 않고 멈춥니다(대소문자는 가리지 않습니다). 환경 파일은 HOME·USERPROFILE·CLAUDE_CONFIG_DIR·TEMP를 이 폴더로 돌리고, 프록시 변수를 지우고 `NO_PROXY`를 루프백으로 둡니다. Node 24의 `NODE_USE_ENV_PROXY=1`(또는 `--use-env-proxy`)을 켜면 Node가 시작할 때 `HTTP_PROXY`·`HTTPS_PROXY`·`NO_PROXY`를 읽어 요청을 프록시로 보냅니다([Node 24 CLI 문서](https://nodejs.org/docs/latest-v24.x/api/cli.html)). 그 문서는 이 변수들이 `fetch`에 닿는지까지는 적지 않으므로 닿는다고 가정하고 막습니다. 독자 셸에 그 변수가 켜져 있어도 루프백 요청이 독자의 프록시로 가지 않게 하려는 것입니다. 이후 블록에서 파일을 만드는 줄은 모두 `"${LAB:?}/…"` 절대 경로로 씁니다. 환경 블록을 건너뛰고 대화식 터미널에 붙여 넣어도 지금 폴더에 파일이 생기지 않게 하려는 것입니다.

```bash
cd awesome-llm-apps
export REPO="$PWD"
export LAB=/path/to/d163-lab          # 저장소 밖의 새 폴더(자기 절대 경로로 바꾼다)
_ok=1; _n() { { cygpath -m "$1" 2>/dev/null || printf '%s' "$1"; } | tr 'A-Z\' 'a-z/'; }
case "$LAB" in ""|/path/to/*) echo "LAB을 자기 경로로 바꾸세요"; _ok=0 ;; esac
case "$LAB" in /*|[A-Za-z]:[/\]*) ;; *) echo "LAB은 절대 경로여야 합니다: $LAB"; _ok=0 ;; esac
case "$(_n "$LAB")/" in
  */.claude/*|*/.agents/*|*/.codex/*|*/.cursor/*|*/.copilot/*|*/.openclaw/*|*/.hermes/*)
    echo "LAB이 에이전트 설정 폴더 아래입니다: $LAB"; _ok=0 ;;
esac
if [ -n "${CLAUDE_CONFIG_DIR:-}" ]; then
  _c=$(_n "$CLAUDE_CONFIG_DIR")
  case "$(_n "$LAB")/" in "${_c%/}"/*) echo "LAB이 CLAUDE_CONFIG_DIR 아래입니다"; _ok=0 ;; esac
fi
[ "$_ok" = 1 ] && mkdir -p "$LAB/home" "$LAB/tmp" "$LAB/work" && cat > "$LAB/env.sh" <<'EOF'
# Day 163 작업 셸의 환경. 이 문서의 모든 명령은 이 파일을 불러온 셸에서 돌린다.
: "${REPO:?REPO를 먼저 정하세요}" "${LAB:?LAB을 먼저 정하세요}"
_n() { { cygpath -m "$1" 2>/dev/null || printf '%s' "$1"; } | tr 'A-Z\' 'a-z/'; }
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
export HOME="$LAB/home" USERPROFILE="$LAB/home" CLAUDE_CONFIG_DIR="$LAB/home/.claude"
export TEMP="$LAB/tmp" TMP="$LAB/tmp" TMPDIR="$LAB/tmp"
# 프록시를 쓰지 않는다. Node 24의 NODE_USE_ENV_PROXY가 켜져 있으면 루프백 요청도 프록시로 갈 수 있다.
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy NODE_USE_ENV_PROXY
export NO_PROXY=127.0.0.1,localhost,::1 no_proxy=127.0.0.1,localhost,::1
export LABW=$(cygpath -m "$_lab")               # node에 넘기는 Windows 꼴 경로
export APP="$LAB/work/ripple" APPW="$LABW/work/ripple"
export FAKE_PORT=51931                          # 앱 포트 4212는 소스에 박혀 있다
EOF
[ "$_ok" = 1 ] && source "$LAB/env.sh" && cd "$LAB/work"
```

앱 폴더를 사본으로 가져오고 시험을 돌립니다. 사본에는 `.env`가 없습니다. 앱의 `config.mjs`는 자기 옆의 `.env`를 읽으므로, 원본 폴더에서 돌리면 독자가 갖고 있을지 모르는 진짜 키 파일을 읽게 됩니다.

```bash
[ -e "${LAB:?}/work/ripple" ] || cp -r "${REPO:?}/advanced_llm_apps/ripple" "${LAB:?}/work/ripple"
ls -A "${LAB:?}/work/ripple"
cd "${LAB:?}/work/ripple" && node --test tests/*.test.mjs 2>&1 | grep -E '^ℹ (tests|pass|fail)'
```

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 마지막 명령의 출력이 다음과 같으면 됩니다.

```text
ℹ tests 53
ℹ pass 53
ℹ fail 0
```

53개는 파일별로 `apply` 10, `core` 12, `correction` 3, `review` 11, `server` 7, `suggestions` 5, `transport` 3, `ui` 2입니다(`grep -c "^test("`). 이름만 보면 서버를 시험하는 파일은 `server.test.mjs`가 아니라 `transport.test.mjs`입니다. `server.test.mjs`는 `jev.mjs`의 질문 만들기와 TypeSafe 호출을 시험합니다. 그리고 `review`·`apply`·`ui`·`transport`는 `content.js`·`bootstrap.js`·`ui.js`·`server.mjs`의 **소스를 읽어 `node:vm` 안에서 돌립니다**(`advanced_llm_apps/ripple/tests/review.test.mjs:97`, `apply.test.mjs:132`, `ui.test.mjs:36`, `transport.test.mjs:29`). 브라우저가 없어도 확장 코드가 도는 이유입니다. 가짜로 만든 것은 `chrome`·`window`·DOM이고, 그래서 이 시험이 통과해도 **진짜 Google Docs에서의 동작은 보증되지 않습니다.** 앱 README도 공유 전에 "일회용 문서에서 직접 확인"하라고 적습니다.

### Step 2. 확장이 문서를 읽고 고치는 길을 따라가고, 바뀐 곳 찾기를 돌려 본다

**목적.** 브라우저 없이 확장의 앞 절반을 이해합니다. 소스로 읽는 부분(문서 입출력)과, 소스 파일을 그대로 불러 돌려 볼 수 있는 부분(`core.js`)을 나눕니다.

**읽기(소스로 확인, 실행하지 않음).** `manifest.json`은 권한을 `storage` 하나로 두고, 호스트는 `https://docs.google.com/document/*`와 `http://127.0.0.1:4212/*` 둘만 엽니다(`manifest.json:7-11`). 내용 스크립트가 둘입니다. `correction.js`+`bootstrap.js`는 `document_start`에 **`world: "MAIN"`**으로, `correction.js`+`content.js`는 `document_idle`에 격리된 세계로 들어갑니다(`manifest.json:25-37`). 격리된 세계는 Docs 페이지의 자바스크립트 변수를 볼 수 없으므로, 문서 글을 읽으려면 페이지 안에서 도는 `bootstrap.js`가 필요합니다. 그 스크립트는 `window._docs_annotate_getAnnotatedText()`가 돌려 주는 객체에서 `getText()`로 글을, `setSelection()`으로 선택을 다룹니다(`bootstrap.js:35-43`, `177`). 앱 README는 이것을 "확장 쪽으로 열린 Docs 인터페이스"라 부르고 구글이 바꿀 수 있다고 적습니다. `bootstrap.js:2-3`은 주석("Ripple의 자기 신원을 쓴다. 다른 확장을 사칭하지 않는다")과 함께 `window._docs_annotate_canvas_by_ext`를 Ripple 자신의 ID로 채웁니다. 그 ID가 `server.mjs`가 `manifest.json`의 `key`에서 계산하는 ID와 같다는 것은 Step 3의 `/health` 출력에서 직접 봅니다.

읽기는 `setInterval(read, 600)`(`bootstrap.js:335`)로 600ms마다 하고, 글이 30,000자를 넘으면 보내지 않습니다(`bootstrap.js:44-49`). `content.js`는 글이 바뀌면 `schedule()`로 **1.9초**(`content.js:139`) 쉰 뒤에 `check()`를 부릅니다. 한국어 입력기가 글자를 조합하는 중에는(`compositionstart`~`compositionend`, `content.js:654-663`) 보내지 않습니다.

적용은 `content.js`의 `applySuggestion`이 `apply` 메시지를 보내고(`content.js:424-432`), `bootstrap.js:78-317`이 받아서 처리합니다. 순서는 아래 그림과 같습니다. 눈여겨볼 곳은 "Docs의 모델을 직접 고치지 않는다"는 것입니다. `bootstrap.js:230-257`의 주석 그대로, 입력 iframe은 "이벤트를 받는 곳"이라서 거기에 붙여넣기 이벤트(바꾸기)나 Backspace 키 이벤트(지우기)를 한 번 보내고, 80ms 간격으로 최대 20번 `getText()`를 다시 읽어 기대한 꼴인지(`rippleCorrection.matches`) 확인합니다. 기대와 다르면 "바뀌긴 했는데 기대와 다르다"고 알리고 다시 시도하지 않습니다. 선택 범위·글 전체·초점·탭이 하나라도 달라졌으면 시작도 하지 않습니다.

![Apply의 순서](diagrams/extra-apply.svg)

**할 일.** 확장 소스 가운데 `core.js`는 브라우저 상태가 없는 순수 함수라서(첫 줄 주석), 사본 파일을 그대로 불러 돌릴 수 있습니다. 시험 클라이언트 `client.mjs`를 만듭니다. 이 파일은 Step 4·5·6에서도 씁니다. 요청 머리글은 `background.js:27-30`과 같게 `Content-Type`·`X-Ripple-Client`를 붙이고, 브라우저가 붙여 줄 `Origin`도 같은 값으로 붙입니다.

```bash
cat > "${LAB:?}/client.mjs" <<'EOF'
// 확장 프로그램 흉내. core.js는 앱 사본 것을 그대로 불러오고, 요청은 background.js와 같은 머리글로 보낸다.
import http from "node:http";
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
const { reconcile, sentences, uniqueSpan, fingerprint } = await import(
  pathToFileURL(process.env.APPW + "/extension/core.js").href
);
const before = [
  "Attendance is online.",
  "Participants can attend from anywhere in the world.",
  "We will email the Zoom link one day before the workshop.",
  "Bring a laptop for the exercises.",
  "Last year's workshop was online.",
].join("\n");
const after = before.replace("Attendance is online.", "Attendance is in person only.");
const call = (method, path, headers = {}, body) =>
  new Promise((resolve, reject) => {
    const req = http.request({ host: "127.0.0.1", port: 4212, method, path, headers }, (res) => {
      let raw = "";
      res.on("data", (c) => (raw += c));
      res.on("end", () => resolve({ status: res.statusCode, headers: res.headers, body: raw ? JSON.parse(raw) : null }));
    });
    req.on("error", reject);
    req.end(body);
  });
const cmd = process.argv[2];
if (cmd === "plan" || cmd === "ask") {
  const source = reconcile(before, after, [], [])[0];
  const span = uniqueSpan(after, source.after);
  const candidates = sentences(after)
    .filter((s) => s.end <= span.start || s.start >= span.end)
    .map(({ id, text, section }) => ({ id, text, section }));
  const checkInput = { source: { before: source.before, after: source.after }, sentences: candidates };
  if (cmd === "plan") console.log(JSON.stringify({ source, sentences: candidates.length, checkInput }, null, 1));
  else {
    const id = (await call("GET", "/health")).body.extensionId;
    const h = { "Content-Type": "application/json", "X-Ripple-Client": id, Origin: "chrome-extension://" + id };
    const check = await call("POST", "/check", h, JSON.stringify(checkInput));
    console.log("/check", check.status, JSON.stringify(check.body.results));
    const flagged = check.body.results
      .filter((r) => r.status === "likely_conflict")
      .map((r) => candidates.find((s) => s.id === r.id));
    const passages = flagged.map((s) => {
      const at = after.indexOf(s.text);
      return {
        id: fingerprint(source.before + "\0" + source.after + "\0" + s.text),
        text: s.text,
        context: after.slice(Math.max(0, at - 300), at + s.text.length + 300),
      };
    });
    const sug = await call("POST", "/suggest", h, JSON.stringify({ source: checkInput.source, passages }));
    console.log("/suggest", sug.status, JSON.stringify(sug.body.suggestions, null, 1));
  }
} else if (cmd === "deny") {
  const id = (await call("GET", "/health")).body.extensionId;
  const ok = { "Content-Type": "application/json", "X-Ripple-Client": id, Origin: "chrome-extension://" + id };
  const tiny = JSON.stringify({ source: { before: "a", after: "b" }, sentences: [] });
  const show = (label, r) => console.log(label.padEnd(34), r.status, JSON.stringify(r.body?.error ?? r.body));
  show("GET /health, Origin 없음", await call("GET", "/health"));
  show("POST /check, X-Ripple-Client 없음", await call("POST", "/check", { "Content-Type": "application/json" }, tiny));
  show("POST /check, Origin이 다른 곳", await call("POST", "/check", { ...ok, Origin: "https://evil.example" }, tiny));
  show("POST /check, Host가 다른 이름", await call("POST", "/check", { ...ok, Host: "evil.example:4212" }, tiny));
  show("POST /check, 문장 0개", await call("POST", "/check", ok, tiny));
  show("POST /check, 본문 50,001바이트", await call("POST", "/check", ok, "x".repeat(50001)));
  const pre = await call("OPTIONS", "/check", { ...ok, "Access-Control-Request-Method": "POST" });
  console.log("OPTIONS /check".padEnd(34), pre.status, pre.headers["access-control-allow-origin"], pre.headers["access-control-allow-headers"]);
} else if (cmd === "log") {
  for (const line of readFileSync(process.env.LABW + "/fake.log", "utf8").trim().split("\n")) {
    const r = JSON.parse(line), b = r.body;
    if (r.url.includes("systemone"))
      console.log(r.url, "| auth:", r.auth, "| model:", b.model, "| 질문", Object.keys(b.questions).length, "| change:", JSON.stringify(b.state.change), "| document:", b.state.document.length);
    else
      console.log(r.url, "| key:", r.gkey, "| 지시문", b.systemInstruction.parts[0].text.length, "자 | cfg:", JSON.stringify(b.generationConfig).slice(0, 90) + "…");
  }
} else console.log("사용법: node client.mjs plan|ask|deny|log");
EOF
```

문서는 앱 README의 예시와 같은 다섯 문장입니다. 첫 문장 `Attendance is online.`을 `Attendance is in person only.`로 바꾼 것으로 하고, 확장이 백엔드로 보낼 요청을 만들어 봅니다.

```bash
cd "${LAB:?}/work" && node "${LABW:?}/client.mjs" plan
```

![Step 2까지의 구성](diagrams/step2.svg)

**확인.**

```text
{
 "source": {
  "id": "1vn7h2g",
  "before": "Attendance is online.",
  "after": "Attendance is in person only."
 },
 "sentences": 4,
 "checkInput": {
  "source": {
   "before": "Attendance is online.",
   "after": "Attendance is in person only."
  },
  "sentences": [
   {
    "id": "b0s1",
    "text": "Participants can attend from anywhere in the world.",
    "section": ""
   },
   {
    "id": "b0s2",
    "text": "We will email the Zoom link one day before the workshop.",
    "section": ""
   },
   {
    "id": "b0s3",
    "text": "Bring a laptop for the exercises.",
    "section": ""
   },
   {
    "id": "b0s4",
    "text": "Last year's workshop was online.",
    "section": ""
   }
  ]
 }
}
```

`source`가 `core.js`의 `reconcile`이 만든 "추적 중인 바뀐 사실"이고(`id`는 앞뒤 문장 글의 해시 `fingerprint`입니다), `checkInput`이 확장이 `/check`에 보낼 본문입니다. 바꾼 문장 자리(`b0s0`)는 후보에서 빠져서 문장이 네 개입니다. `id`의 `b0`은 문단 번호가 아니라 고정값이고(`core.js:13`) `section`은 항상 빈 문자열입니다. 이 앱은 문서 구조(제목 등)를 읽지 않습니다. 문장 분리는 `Intl.Segmenter("en", …)`로 영어 규칙을 쓰는데(`core.js:3`), 한국어 문서가 어떻게 나뉘는지는 이 문서에서 시험하지 않았습니다. `reconcile`은 추적하는 바뀐 사실을 **최대 넷**으로 제한하고(`core.js:125-128`), 사용자가 이미 표시된 문장을 고친 것은 새 사실이 아니라 "수선"으로 보고 무시합니다(`core.js:110-117`).

### Step 3. 가짜 TypeSafe·Gemini와 가드를 만들고 서버를 띄운다

**목적.** 앱이 진짜 주소를 부르는 곳은 둘뿐입니다. `jev.mjs:97`의 `https://api.typesafe.ai/v1/systemone`과 `suggestions.mjs:117-118`의 `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent`입니다. 둘 다 앱 코드가 주소를 박아 넣었고 바꿀 설정이 없습니다. 그래서 앱 코드를 고치지 않고 `fetch`를 가로채는 **독자용 가드**를 앱 앞에 둡니다.

**할 일.** 파일 셋을 만듭니다. `fake.mjs`는 두 경로를 받는 가짜 서버로, 받은 요청을 `fake.log`에 한 줄씩 남깁니다. `guard.mjs`는 `globalThis.fetch`를 바꿔서 그 두 주소를 가짜 서버로 돌리고, 루프백이 아닌 곳은 모두 거부하며, 예약 주소 `192.0.2.1`에 먼저 부르는 단언을 합니다. 막히지 않으면 그 자리에서 멈춥니다. `serve.mjs`는 가드를 불러온 뒤 가짜 키를 환경변수에 넣고 앱의 `server.mjs`를 불러옵니다. `serve.mjs`에서 가드를 불러오는 줄을 빼면 `armed`가 없다는 오류로 서버가 뜨지 않습니다(작성자가 줄을 빼 보았습니다: `ReferenceError: armed is not defined`, 포트 4212는 열리지 않았습니다).

이 가드는 `fetch`만 막습니다. 이 앱이 바깥으로 나가는 길은 `fetch` 둘뿐이지만(`jev.mjs`·`suggestions.mjs`, 소스로 확인), 다른 소켓 호출까지 막는 가드는 아닙니다.

```bash
cat > "${LAB:?}/fake.mjs" <<'EOF'
// 가짜 TypeSafe + 가짜 Gemini. 루프백 한 포트에서 두 경로를 받고, 받은 요청을 fake.log에 한 줄씩 남긴다.
import http from "node:http";
import { appendFileSync } from "node:fs";
const log = process.env.LABW + "/fake.log";
const jev = (text) =>
  /Zoom|anywhere/.test(text) ? ["likely_conflict", 0.95]
  : /laptop/.test(text) ? ["likely_conflict", 0.6]
  : ["unaffected", 0.01];
const gem = (text) =>
  /Zoom link/.test(text) ? ["delete", "", "참석 링크 안내는 더는 쓸모가 없다."]
  : /anywhere/.test(text) ? ["replace", "Participants attend in person.", "원격 참석 문장을 대면 참석으로 바꾼다."]
  : ["keep", "", "그대로 둬도 맞는다."];
http.createServer(async (req, res) => {
  let raw = "";
  for await (const c of req) raw += c;
  const body = raw ? JSON.parse(raw) : null;
  appendFileSync(log, JSON.stringify({
    url: req.url, auth: req.headers.authorization, gkey: req.headers["x-goog-api-key"],
    type: req.headers["content-type"], body }) + "\n");
  const send = (o, code = 200) => { res.writeHead(code, { "Content-Type": "application/json" }); res.end(JSON.stringify(o)); };
  if (req.url === "/typesafe/v1/systemone") {
    const answers = {};
    for (const s of body.state.document) {
      const [choice, p] = jev(s.text);
      answers[s.id] = { type: "choice", choice, confidence: p,
        probabilities: { likely_conflict: p, worth_reviewing: 0, unaffected: 1 - p } };
    }
    return send({ model: "jev-fake", answers, usage: { input_tokens: 0, output_tokens: 0 } });
  }
  if (req.url.startsWith("/gemini/v1beta/models/")) {
    const input = JSON.parse(body.contents[0].parts[0].text);
    const suggestions = input.passages.map((p) => {
      const [action, replacement, reason] = gem(p.text);
      return { id: p.id, action, replacement, reason };
    });
    return send({ candidates: [{ finishReason: "STOP", content: { parts: [{ text: JSON.stringify({ suggestions }) }] } }] });
  }
  send({ error: "no such fake route" }, 404);
}).listen(Number(process.env.FAKE_PORT), "127.0.0.1", () => console.log("fake on 127.0.0.1:" + process.env.FAKE_PORT));
EOF
cat > "${LAB:?}/guard.mjs" <<'EOF'
// 독자용 가드. 앱의 fetch에서 진짜 주소 둘을 가짜 서버로 돌리고, 루프백 밖은 모두 막는다.
const real = globalThis.fetch;
const FAKE = "http://127.0.0.1:" + (process.env.FAKE_PORT ?? (() => { throw new Error("FAKE_PORT가 없습니다"); })());
const GEM = "https://generativelanguage.googleapis.com/v1beta/models/";
globalThis.fetch = (input, init) => {
  const url = typeof input === "string" || input instanceof URL ? String(input) : input.url;
  let to = null;
  if (url === "https://api.typesafe.ai/v1/systemone") to = FAKE + "/typesafe/v1/systemone";
  else if (url.startsWith(GEM)) to = FAKE + "/gemini/v1beta/models/" + url.slice(GEM.length);
  else if (["127.0.0.1", "localhost"].includes(new URL(url).hostname)) to = url;
  if (!to) return Promise.reject(Object.assign(new Error("lab guard blocked " + url), { code: "EGUARD" }));
  return real(to, init);
};
// 예약 주소(192.0.2.1)로 먼저 단언한다. 막히지 않으면 여기서 멈춘다.
try { await fetch("http://192.0.2.1/"); throw new Error("가드가 192.0.2.1을 막지 않았습니다"); }
catch (e) { if (e.code !== "EGUARD") throw e; }
export const armed = true;
EOF
cat > "${LAB:?}/serve.mjs" <<'EOF'
// 앱 서버를 가드 아래서 띄운다. 이 줄들을 빼면 armed가 없어 서버가 뜨지 않는다.
import { pathToFileURL } from "node:url";
import { armed } from "./guard.mjs";
if (armed !== true) throw new Error("가드가 없습니다");
process.env.TYPESAFE_API_KEY = "fake-typesafe-key";
process.env.GEMINI_API_KEY = "fake-gemini-key";
delete process.env.GOOGLE_API_KEY;
await import(pathToFileURL(process.env.APPW + "/server.mjs").href);
EOF
ls "${LAB:?}"
```

터미널 A와 B에서 각각 서버를 띄웁니다. 앱 서버는 포트 4212가 소스에 박혀 있습니다(`server.mjs:104`). 이미 쓰는 프로그램이 있으면 이 단계가 실패합니다. 가짜 서버 포트는 `env.sh`의 `FAKE_PORT`입니다.

```bash
# 터미널 A
cd awesome-llm-apps && export REPO="$PWD" LAB=/path/to/d163-lab   # Step 1과 같은 경로
source "${LAB:?}/env.sh" && node "${LABW:?}/fake.mjs"
```

```bash
# 터미널 B
cd awesome-llm-apps && export REPO="$PWD" LAB=/path/to/d163-lab
source "${LAB:?}/env.sh" && node "${LABW:?}/serve.mjs"
```

터미널 C에서 서버가 어디에 듣는지, `/health`가 무엇을 돌려 주는지 봅니다. `curl`에는 `--noproxy '*'`를 붙입니다.

```bash
curl -s --noproxy '*' http://127.0.0.1:4212/health; echo
netstat -ano | grep LISTENING | grep -E ':(4212|51931) '
```

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 터미널 A는 `fake on 127.0.0.1:51931`, B는 `Ripple is running on http://127.0.0.1:4212. …`를 찍습니다. 터미널 C의 출력은 다음과 같습니다(`netstat`의 PID는 환경마다 다릅니다).

```text
{"ready":true,"model":"jev-latest","provider":"typesafe","suggestionsReady":true,"suggestionModel":"gemini-3.5-flash-lite","extensionId":"fmalimpikdmpeejecilonpfjklejiccd"}
  TCP    127.0.0.1:4212         0.0.0.0:0              LISTENING       45636
  TCP    127.0.0.1:51931        0.0.0.0:0              LISTENING       10832
```

`ready`는 키가 있는지(`getApiKey()`), `suggestionsReady`는 Gemini 키가 있는지입니다(`server.mjs:47-55`). 두 서버 모두 `127.0.0.1`에만 듣습니다(`server.mjs:104`, `netstat`의 `127.0.0.1:4212`). `extensionId`는 Step 2에서 `bootstrap.js:3`이 Docs에 내세우는 ID와 같은 `fmalimpikdmpeejecilonpfjklejiccd`입니다. 서버가 `manifest.json`의 공개 키를 SHA-256으로 해시해 앞 32자리를 `a`~`p` 글자로 바꾸는(`server.mjs:12-20`) 크롬 확장 ID 규칙을 따라 계산한 값입니다. 키는 `manifest.json`에 박혀 있어서 확장을 어디에 풀어도 ID가 같습니다.

### Step 4. 확장이 보낼 `/check` 요청과 TypeSafe가 받는 모양을 본다

**목적.** 한 번의 편집이 TypeSafe에 어떤 질문이 되는지, 응답이 어떻게 상태로 바뀌고 확장이 어느 것을 남기는지 봅니다.

**할 일.** 터미널 C에서 확장 흉내를 돌립니다. `client.mjs ask`는 `/health`로 확장 ID를 얻고, Step 2의 `checkInput`을 `/check`에 보내고, 가짜 응답에서 `likely_conflict`만 골라 `content.js:252-307`처럼 `/suggest`에 보냅니다(수정안은 Step 5에서 봅니다).

```bash
cd "${LAB:?}/work" && node "${LABW:?}/client.mjs" ask
```

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 첫 줄이 `/check`입니다.

```text
/check 200 [{"id":"b0s1","status":"likely_conflict"},{"id":"b0s2","status":"likely_conflict"},{"id":"b0s3","status":"worth_reviewing"},{"id":"b0s4","status":"unaffected"}]
```

가짜 Jev는 `Zoom`·`anywhere`가 든 문장에 확률 0.95의 `likely_conflict`를, `laptop`이 든 문장에 0.6의 `likely_conflict`를, 나머지에 `unaffected`를 줍니다. 그런데 `b0s3`(laptop)의 상태가 `worth_reviewing`입니다. 서버가 `likely_conflict`이면서 확률이 0.8 미만이면 낮추기 때문입니다. 0.45 이상이면 `worth_reviewing`, 미만이면 `unaffected`입니다(`jev.mjs:146-151`). 확장은 거기서 한 번 더 걸러서 `likely_conflict`만 씁니다(`content.js:219`). 그래서 `worth_reviewing`은 밑줄도 수정안도 받지 못하고 `/suggest`로도 가지 않았습니다. 앱 README의 "Jev finds likely inconsistencies"를 그대로 믿는 쪽에서는 놓치기 쉬운 부분입니다. 임계값 0.8과 0.45가 어디서 왔는지 소스에 근거는 없습니다.

TypeSafe 쪽으로는 무엇이 갔는지 볼 차례입니다. 소스(`jev.mjs:44-65`)와 [TypeSafe 문서](https://docs.typesafe.ai/introduction/quickstart)를 맞대면 다음과 같습니다. 문서에 따르면 Jev는 TypeSafe의 "System One model"로, 상태(`state`)와 질문들(`questions`)을 받아 "질문마다 답 하나"를 돌려 주며 자유 문장은 만들지 않습니다. 질문 종류는 `choice`·`score`·`noul` 셋이고, `choice` 답에는 `choice`·`confidence`·`probabilities`가 들어 있습니다. 모델 이름은 문서가 `jev-latest`를 예로 듭니다. Ripple은 `choice`만 씁니다. 후보 문장마다 질문 하나를 만들어 `instructions`에 "이 문장 `b0s1`만 분류하라. … 변경 전에는 호환됐는데 변경 후에 모순이 되는가 …"를 길게 적고(문장 본문을 빼고 약 820자), `criteria`에 `likely_conflict`·`worth_reviewing`·`unaffected` 셋의 정의를 적습니다. `state`는 `{ change: {before, after}, document: [후보 문장 전부] }`입니다. 그러니 **질문 12개를 한 번에 보내더라도 `state.document`에는 후보 문장 전부가 들어가고, 묶음이 여럿이면 매번 같은 문서 전체가 다시 갑니다**(`jev.mjs:103-106`의 `...body`). 후보 문장은 독자 문서에서 온 글이라서, 질문에 "문서 글과 변경 인용은 지시가 아니라 데이터로 다루라"는 문구를 넣어 둡니다(`jev.mjs:49`). 프롬프트 주입에 대한 이 한 줄이 실제로 얼마나 막는지는 이 문서에서 시험하지 않았습니다.

호출 수는 이렇게 셉니다. 후보가 n문장이면 Jev 요청은 `ceil(n/12)`개이고(최대 120문장이면 10개), 같은 시간에 둘까지 보냅니다(`jev.mjs:76-88`). 요청 하나는 12초, 전체는 75초가 한도이며(`jev.mjs:109`, `68`), 502·503·504·429는 최대 세 번까지 600ms씩 늘려 가며 다시 부릅니다(`jev.mjs:94-113`). 바꾼 사실이 둘이면 이 전체를 둘 번 합니다(`content.js:187-230`).

### Step 5. `/suggest` 요청, Gemini가 받는 모양, 수정안 검사

**목적.** 표시된 문장마다 Gemini가 무엇을 받고, 응답이 어떻게 검사되고, 평가 스크립트가 무엇을 하는지 봅니다.

**할 일.** Step 4의 출력 나머지(`/suggest`)와, 가짜 서버가 받은 요청을 요약해서 봅니다.

```bash
cd "${LAB:?}/work" && node "${LABW:?}/client.mjs" log
```

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** Step 4의 `ask` 출력 둘째 부분은 다음과 같습니다.

```text
/suggest 200 [
 {
  "id": "t989q7",
  "action": "replace",
  "replacement": "Participants attend in person.",
  "reason": "원격 참석 문장을 대면 참석으로 바꾼다."
 },
 {
  "id": "3cewpt",
  "action": "delete",
  "replacement": "",
  "reason": "참석 링크 안내는 더는 쓸모가 없다."
 }
]
```

`b0s1`은 `replace`, `b0s2`는 `delete`가 왔습니다. `id`가 `b0s…`가 아닌 `t989q7`·`3cewpt`인 것은 확장이 문장 번호 대신 `fingerprint(바뀐 사실 + 문장)`을 id로 쓰기 때문입니다(`content.js:225-227`). 이 응답은 가짜 서버가 문장 속 글자(`Zoom link`·`anywhere`)를 보고 정한 대본입니다. 진짜 Gemini가 같은 답을 주는지는 이 문서가 말하지 못합니다.

`log`의 출력입니다. 가짜 서버가 두 요청에서 본 인증 헤더·모델·질문 수가 한 줄에 보입니다.

```text
/typesafe/v1/systemone | auth: Bearer fake-typesafe-key | model: jev-latest | 질문 4 | change: {"before":"Attendance is online.","after":"Attendance is in person only."} | document: 4
/gemini/v1beta/models/gemini-3.5-flash-lite:generateContent | key: fake-gemini-key | 지시문 3757 자 | cfg: {"temperature":0.2,"maxOutputTokens":4096,"responseMimeType":"application/json","responseS…
```

TypeSafe에는 `Authorization: Bearer <키>`가, Gemini에는 `x-goog-api-key: <키>` 헤더가 갔고(`jev.mjs:98-102`, `suggestions.mjs:121`) 키는 URL에 들어가지 않습니다. Gemini 호출은 `generateContent` 엔드포인트에 시스템 지시문(`systemInstruction`), 사용자 내용(`{source, passages}` JSON 한 덩어리), `generationConfig`(`temperature` 0.2, `maxOutputTokens` 4096, `responseMimeType: application/json`, `responseSchema`)을 실어 보냅니다(`suggestions.mjs:121-155`). [Gemini 공식 문서](https://ai.google.dev/gemini-api/docs/models)는 `gemini-3.5-flash-lite`를 안정판으로 싣고 종료 예정 공지가 없습니다. 다만 같은 사이트의 구조화 출력 문서는 지금 새 `interactions` 엔드포인트의 `response_format`을 예로 보이고, `generateContent`가 폐기 예정인지는 이 문서가 확인하지 못했습니다(`generateContent` 문서에는 그런 표시가 없었습니다).

응답 검사는 꽤 엄격합니다(`suggestions.mjs:58-108`). `finishReason`이 `STOP`이어야 하고, `thought` 조각은 버리고, 배열 길이와 `id`가 요청과 맞아야 하며, `action`은 넷 중 하나, `replacement`는 한 줄(개행·제어문자 없음)이고 2,500자 이하, `replace`일 때만 비어 있지 않아야 하고, 원문과 같은 글이면 "실제 변경 없음"으로 거절합니다. 이 검사는 `tests/suggestions.test.mjs`가 시험합니다. 확장은 한 번에 최대 네 문장씩(`content.js:259`), 서버는 최대 열두 문장까지 받습니다(`suggestions.mjs:14-30`). 문장마다 앞뒤 300자의 문맥을 함께 보냅니다(`content.js:271-281`).

시스템 지시문은 3,757자로, 네 동작의 기준과 예시를 길게 적습니다(`suggestions.mjs:3-13`). 흥미로운 점은 그 안에 든 예시입니다. "Participants can attend from anywhere in the world"를 지우라고, "Please arrive at 12 Market Street by 9 AM"에는 `needs_info`를 고르라고, "We will email a Zoom link; bring a laptop for exercises"는 laptop 문장만 남기라고 말합니다. 평가 스크립트 `advanced_llm_apps/ripple/scripts/evaluate-suggestions.mjs`의 11개 사례 가운데 `global`·`address`·`mixed`·`zoom`·`invite`는 이 예시와 문장이 같거나 거의 같습니다. 그래서 그 스크립트의 통과 수는 "일반적인 품질"이 아니라 "예시를 따르는가"에 가깝게 읽어야 합니다(스크립트 마지막 줄도 "작은 라이브 평가이지 일반적 품질 보증이 아니다"라고 적습니다). 이 스크립트는 `suggestions.mjs`의 `suggest()`를 불러 **진짜 Gemini를 4번(그룹 수) 부릅니다**(`advanced_llm_apps/ripple/scripts/evaluate-suggestions.mjs:2, 105`). 그래서 이 문서는 돌리지 않았습니다.

### Step 6. 문지기: 호스트·Origin·헤더·크기 검사

**목적.** 로컬 서버가 브라우저의 다른 페이지나 다른 프로그램의 요청에 악용되지 않게 어떻게 막는지 봅니다. 이 서버는 키를 들고 있어서, 아무나 부를 수 있으면 남이 내 키로 모델을 부를 수 있습니다.

**할 일.** 같은 클라이언트가 정상 요청 하나(`GET /health`), 잘못된 요청 다섯, 사전 요청(preflight) 하나를 보냅니다.

```bash
cd "${LAB:?}/work" && node "${LABW:?}/client.mjs" deny
```

![Step 6까지의 구성](diagrams/step6.svg)

**확인.**

```text
GET /health, Origin 없음             200 {"ready":true,"model":"jev-latest","provider":"typesafe","suggestionsReady":true,"suggestionModel":"gemini-3.5-flash-lite","extensionId":"fmalimpikdmpeejecilonpfjklejiccd"}
POST /check, X-Ripple-Client 없음    403 "Use the Ripple extension."
POST /check, Origin이 다른 곳          403 "Only the Ripple extension can use this service."
POST /check, Host가 다른 이름           403 "Invalid host."
POST /check, 문장 0개                 400 "This prototype supports 1 to 120 sentences."
POST /check, 본문 50,001바이트          400 "Document exceeds the prototype limit."
OPTIONS /check                     204 chrome-extension://fmalimpikdmpeejecilonpfjklejiccd Content-Type, X-Ripple-Client
```

검사는 `server.mjs`에서 이 순서로 합니다(번호는 `server.mjs`의 줄입니다). (1) `Host`가 `127.0.0.1:4212` 또는 `localhost:4212`가 아니면 403(`31-32`). 이것은 다른 이름이 내 컴퓨터를 가리키게 해서 접근하는 DNS 재바인딩을 막는 흔한 방어입니다. (2) `Origin`이 있고 확장 Origin이 아니면 403(`33-36`). (3) 확장 Origin이면 `Access-Control-Allow-Origin`에 그 Origin만 되돌려 줍니다(`37-38`). `OPTIONS`는 204와 허용 메서드·헤더(`Content-Type`, `X-Ripple-Client`)를 줍니다. (4) `POST /check`·`/suggest`가 아니면 404(`56-57`), `X-Ripple-Client`가 ID와 다르거나 `Content-Type`이 정확히 `application/json`이 아니면 403(`58-62`). (5) 동시 요청은 `/check` 1개, `/suggest` 2개까지이고 넘으면 429와 `retryable: true`입니다(`64-68`). 확장 쪽 `background.js`는 429를 받으면 1.5초, 3초를 기다려 세 번까지 다시 부릅니다(`background.js:17-40`). (6) 본문이 50,000바이트를 넘으면 중단합니다(`76-84`). 이 모든 검사는 **키가 필요한 일에 앞서** 합니다. 출력에서 첫 줄 `GET /health`만 `Origin` 없이도 통과하는데, 이것은 설계입니다. 확장 ID와 키 보유 여부(`ready`)만 알려 주며 키 자체는 주지 않습니다.

주의할 점이 둘 있습니다. 하나는 이 검사들이 **인증이 아니라는 것**입니다. `X-Ripple-Client`의 값은 `/health`가 아무에게나 알려 주는 확장 ID이므로, 같은 컴퓨터의 다른 프로그램이 `Host`·`Origin`·헤더를 맞춰 보내면 통과합니다. 웹 페이지는 `Origin`과 `Host` 같은 헤더를 마음대로 정할 수 없으므로 막지만, 로컬 프로그램은 막지 못합니다. 앱 README에는 이 한계에 대한 말이 없습니다(소스로 확인). 다른 하나는 429 시험입니다. 이 문서는 `/check`를 동시에 두 번 보내는 실험을 하지 않았고, 그 동작은 `tests/transport.test.mjs`의 "HTTP busy response is retryable; disconnect cancels work before releasing slot"가 시험합니다(소스로 확인).

마지막으로 서버가 끝나면 터미널 A와 B에서 `Ctrl+C`를 누릅니다.

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

독자가 한 문장을 고치면 `bootstrap.js`가 600ms마다 읽는 문서 글이 달라지고, `content.js`가 1.9초 조용하길 기다린 뒤 `core.js`로 바뀐 곳과 후보 문장을 계산해 `background.js`에 `check`를 맡깁니다. 서버는 문지기 검사를 거쳐 문장마다 질문을 만들어 TypeSafe를 부르고, 응답을 상태로 바꿔 돌려 줍니다. 확장은 `likely_conflict`만 남기고 밑줄을 그립니다. 밑줄 위치는 Docs 캔버스의 `rect[aria-label]`에서 문장 글을 찾아 계산하고, 문서를 건드리지 않습니다(`content.js:537-618`). 이어서 수정안을 요청합니다.

![수정안 요청의 순서](diagrams/extra-suggest.svg)

수정안이 오면 카드가 문장과 제안을 나란히 보이고, 독자가 `Apply change`를 눌러야 `apply`가 `bootstrap.js`로 갑니다. 독자가 누르기 전에는 문서에 아무 것도 쓰이지 않습니다. 적용한 뒤에는 `corrections`에 최대 20개까지 앞뒤 글을 기억해서(`content.js:389`), Docs의 되돌리기·다시 하기가 오면 처음 바꾼 사실을 기준으로 다시 검사합니다.

## 실행 체크리스트

- [ ] `LAB`이 저장소 밖의 새 폴더이고 `env.sh`가 만들어졌다
- [ ] 사본에서 `node --test`가 53 pass, 0 fail
- [ ] `client.mjs plan`이 후보 문장 4개와 `source`를 찍었다
- [ ] 가드를 빼면 `serve.mjs`가 뜨지 않는다
- [ ] `curl /health`가 `ready: true`와 확장 ID를 돌려 주고, `netstat`에 `127.0.0.1:4212`만 보인다
- [ ] `ask`에서 `worth_reviewing` 문장이 수정안 요청에서 빠졌다
- [ ] `deny`의 잘못된 요청 다섯이 403·403·403·400·400이고 `OPTIONS`가 204이다
- [ ] 서버와 가짜 서버를 `Ctrl+C`로 끝냈다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `EADDRINUSE` 4212 | 포트가 소스에 박혀 있어서 다른 프로그램이나 이전 서버가 쓰는 중 | 그 프로그램을 끄거나 이전 서버를 `Ctrl+C`. 앱에는 포트 설정이 없다(`server.mjs:104`) |
| `serve.mjs`가 `armed is not defined` | 가드를 불러오는 줄이 빠졌다. 의도한 동작이다 | 줄을 되돌린다 |
| `/health`의 `ready`가 `false` | `TYPESAFE_API_KEY`가 환경변수에도 `.env`에도 없다 | 이 문서에서는 `serve.mjs`가 가짜 키를 넣는다. 진짜 앱에서는 `.env`에 쓴다 |
| `403 Invalid host.` | `Host`가 `127.0.0.1:4212`·`localhost:4212`가 아님. 예컨대 컴퓨터 이름이나 다른 포트로 부름 | 주소를 `http://127.0.0.1:4212`로 쓴다 |
| `403 Only the Ripple extension…` | `Origin`이 확장의 것이 아님(웹 페이지나 다른 확장이 부름) | 정상. 확장만 쓸 수 있다 |
| 진짜 앱에서 `Cannot connect to Ripple` | `npm start`가 꺼져 있다 | 서버를 띄운다(앱 README 문제 해결 표) |
| 밑줄이 안 생기고 "Doc access unavailable" | Docs가 `_docs_annotate_getAnnotatedText`를 열지 않았다. 구글이 내부 인터페이스를 바꿨을 수 있다 | 문서를 새로 고친다. 계속되면 이 Docs 버전은 지원하지 않는다(앱 README) |
| 가짜 키로 진짜 앱에 대고 시험했는데 401·403 | 가짜 키는 TypeSafe와 Google이 거절한다 | 이 문서는 진짜 서버를 부르지 않는다. 부를 거면 가드를 빼지 말고 진짜 키는 `.env`에 둔다 |
| 문서를 고쳤는데 아무 일도 없다 | Ripple을 켜기 **전**의 글을 알 수 없다(기준선이 켜는 순간의 글) | 켠 뒤에 고친다. 큰 개작 뒤에는 껐다 켠다(앱 README) |

## 더 해보기

- 한국어 문서가 `sentences()`로 어떻게 나뉘는지 `node`로 불러 시험해 보세요. `Intl.Segmenter("en")`가 `다.`로 끝나는 문장과 줄바꿈 없는 긴 문단을 어떻게 자르는지, 120문장·2,500자 한도에 걸리는 문서는 어떤 것인지 찾아 보세요.
- `fake.mjs`의 응답을 바꿔(`likely_conflict` 확률을 0.79와 0.8로) 임계값 0.8 경계에서 상태가 어떻게 달라지는지, 확장이 어느 쪽만 남기는지 `ask`로 확인해 보세요. 질문 열두 개를 넘기는 문서(13문장 이상)로 만들면 TypeSafe 요청이 둘로 나뉘고 `state.document`가 둘 다에 실리는지도 `log`로 셀 수 있습니다.
- `tests/review.test.mjs`의 `harness`를 읽고, 시험이 `chrome`·DOM 자리에 무엇을 넣는지 정리해 보세요. 그 가짜가 진짜 Google Docs와 다른 점(캔버스 렌더링, 입력 iframe, 협업 편집)이 무엇인지 앱 README의 한계 절과 맞대 보세요.

## 다음 날 예고

[Day 164 · 🔄 GPT-OSS Advanced Critique & Improvement Loop](../day164-gpt-oss-critique-improvement-loop/README.md) — 볼륨 18의 첫날입니다. 브라우저 확장과 Node를 떠나 Python Streamlit 앱(`streamlit_app.py` 227줄)으로 돌아옵니다. 질문마다 후보 답을 병렬로 셋 만들어 하나로 합친 뒤, 비평 단계가 결점을 짚고 수정 단계가 고치는 "비평 + 개선" 루프를 1~3번 돌립니다. 모델은 Groq로 부르는 `openai/gpt-oss-120b`입니다(앱 소스 `MODEL` 상수).
