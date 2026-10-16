# Day 145 · ✈️ MCP Apps Generative UI Showcase

> 볼륨 12 🖼️ Generative UI · 난이도 ★★★ ⚠ 앱 화면도 서버도 실행하지 않은 날입니다. 소스와 내려받은 패키지 압축 파일을 읽고, 읽은 내용을 `grep`과 작은 Node 스크립트로 확인합니다. 앱이 보내는 크기 알림 이름(`size-change`)이 읽은 호스트가 듣는 이름(`size-changed`)과 달라 보이는데, 화면으로 보지는 못했습니다(Step 5) · 예상 소요 125분(실행할 앱이 없어 손으로 돌려 보는 일은 적지만, 읽어야 하는 소스가 앱 파일 여섯 개에 패키지 셋의 소스맵까지 이어지고, 같은 요청이 브라우저·런타임·MCP 서버를 세 번씩 오가서 한 줄씩 따라가는 데 시간이 듭니다) · API 비용 대략 이 문서의 따라 하기는 $0(앱을 띄우지 않으니 모델은 한 번도 부르지 않습니다). 진짜 키로 앱을 돌린다면 질문 한 번에 모델 호출이 한 번이고 어림으로 $0.01~0.02입니다(⚠ 추정, 아래 Step 4) · 원본 앱: `generative_ui_agents/mcp-apps-generative-ui-showcase`

## 오늘 만들 것

채팅 사이드바에서 "JFK에서 LAX로 1월 20일에 두 명 예약해 줘"라고 하면 대화 안에 항공권 예약 마법사가 뜨는 앱입니다. 마법사는 항공편 검색, 항공편 선택, 좌석 선택, 승객 정보, 예약 확인의 다섯 단계이고, 호텔 예약·투자 시뮬레이터·칸반 보드까지 모두 네 가지 앱이 있습니다. 앱 README는 이것을 "sandboxed in-chat apps over a tool protocol"이라고 부릅니다. 지난 날들의 생성 UI는 화면 쪽 코드가 부품을 정하고 에이전트가 거기에 값을 채우는 모양이었다면, 오늘은 **도구를 가진 서버가 화면 조각(HTML 한 장)까지 함께 줍니다.** MCP 서버의 도구가 `_meta["ui/resourceUri"]`로 HTML 자원을 가리키고, CopilotKit이 그것을 채팅 안 iframe으로 띄우며, iframe 안의 앱은 `postMessage`로 도구를 직접 부릅니다. 이 약속이 MCP Apps Extension(SEP-1865)입니다.

이 문서는 앱을 실행하지 않았습니다. 앱은 파이썬 쪽이 없고 TypeScript만 있습니다. `npm install`·`pnpm install`·`npx`·`next`·`vite`는 한 번도 실행하지 않았고, 원본 README의 설치 명령은 아래 Step 1에 그대로 보여 드릴 뿐 이 문서는 그 명령을 실행하지 않았습니다. 대신 앱이 의존하는 세 패키지(`@ag-ui/mcp-apps-middleware` 0.0.3, `@copilotkit/react-core` 1.59.2, `@copilotkit/runtime` 1.59.2)를 npm 레지스트리에서 압축 파일로 `curl`로 받아 풀기만 하고, 패키지에 들어 있는 소스맵에서 원래 소스를 꺼내 읽었습니다. 브라우저로 화면을 연 적도 없습니다. 그래서 마법사가 실제로 어떻게 보이는지, 높이가 맞는지, 진짜 `gpt-5.5`가 네 도구 가운데 무엇을 고르는지는 보여 드리지 못합니다. 이 문서에서 "직접 확인"은 Step마다 있는 `grep`·`wc`·Node 스크립트의 출력을 말하고, 나머지는 "소스로 확인"입니다.

앞 날과 이어지는 곳은 이렇습니다. Next.js와 Node 쪽을 소스로만 읽는 방식은 [Day 124](../day124-ai-travel-planner-agent-team/README.md)가 다뤘습니다. CopilotKit 런타임의 `route.ts`와 AG-UI 이벤트는 [Day 143](../day143-genui-generative-ui-starter-project/README.md)이 파이썬 에이전트 쪽에서 다뤘고, 그 날 Step 8에는 런타임 설정 `mcpApps`가 MCP 앱을 켠다는 말이 나옵니다. 오늘은 같은 일을 설정 옵션이 아니라 `@ag-ui/mcp-apps-middleware`라는 미들웨어를 직접 끼워서 합니다. MCP를 HTTP로 붙이는 클라이언트는 [Day 130](../day130-openai-remote-mcp-bridge/README.md)이 파이썬(`streamable_http_client`)으로 다뤘고, 오늘은 같은 프로토콜을 TypeScript 서버와 TypeScript 클라이언트로 봅니다. 새로 나오는 것은 세 가지입니다. 도구가 화면 조각을 가리키는 약속(`ui/resourceUri`), 그 조각을 가두는 이중 iframe, 그리고 iframe이 모델을 거치지 않고 도구를 부르는 우회 경로입니다.

![완성 아키텍처](diagrams/overview.svg)

그림에서 사용자는 뺐습니다. 사용자와 주고받는 것은 시퀀스 그림이 맡습니다. 런타임에서 MCP 서버로 가는 화살표는 서버 묶음 전체로 갑니다. 묶음 안의 도구·데이터·메모리 관계는 Step 2·3이 글로 보여 줍니다. 앱 iframe은 브라우저 안에 있지만 믿는 범위가 달라 묶음 밖에 그렸습니다.

직접 읽어서 알게 된 것이 여덟입니다. 첫째, 모델에게 보이는 도구는 MCP 서버의 도구 열여섯 가운데 `ui/resourceUri`가 달린 네 개뿐입니다. 시스템 프롬프트가 이름을 대는 도우미 도구 열둘은 모델에게 주어지지 않고 iframe만 부릅니다(Step 4). 둘째, 모델은 질문 한 번에 한 번 불리고, 마법사 안의 클릭은 모델을 거치지 않고 런타임의 "프록시 요청" 길로 MCP 서버에 갑니다(Step 4·6). 셋째, 미들웨어는 MCP 연결을 요청마다 새로 맺고 닫습니다. 질문 하나에 두 번(앱을 띄우는 자원 읽기까지 세 번), 서버는 연결마다 HTML 네 장을 디스크에서 다시 읽습니다(Step 2·4). 넷째, 항공편·호텔·종목은 모두 지어낸 데이터이고 서버 메모리에만 있습니다(Step 3). 다섯째, iframe의 `sandbox` 속성은 `allow-scripts allow-same-origin`을 함께 켜 둡니다. 사양은 호스트와 샌드박스의 출처가 달라야 한다고 적는데, 이 구현은 `srcdoc`으로 만들어 출처가 같을 것으로 읽힙니다(Step 5). 여섯째, `postMessage`는 양쪽 모두 `"*"`로 보내고 `event.origin`을 보지 않으며, 보낸 창이 맞는지(`event.source`)만 봅니다(Step 5·6). 일곱째, 앱이 보내는 크기 알림 이름과 호스트가 듣는 이름이 한 글자 다릅니다(Step 5). 여덟째, MCP 서버는 모든 네트워크 인터페이스에 열리고 CORS가 `*`이며 인증이 없습니다(Step 7).

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Node.js 18 이상 | 이 문서의 읽기 스크립트(`unmap.mjs`·`count.mjs`)용(내장 모듈만 씁니다). **앱 자체는 설치도 실행도 하지 않았습니다.** 앱을 돌리려면 더 높은 버전이 필요합니다. 앱 README는 Node 버전을 적지 않습니다. `next@16.1.1`의 `engines`는 `>=20.9.0`, `vite@7.3.1`은 `^20.19.0 \|\| >=22.12.0`입니다(npm 레지스트리 메타데이터로 직접 확인). `mcp-server/.nixpacks`의 `NODE_VERSION=20.18.1`은 vite의 하한보다 낮습니다 | https://nodejs.org |
| `curl`·`tar`·`grep` | 패키지 압축 파일을 받아 풀고 소스를 검색 | Git Bash에 들어 있음 |
| OpenAI API 키 | **이 문서는 쓰지 않습니다.** 앱을 진짜로 돌릴 때만 필요합니다 | https://platform.openai.com/api-keys |

명령은 Git Bash 기준입니다. PowerShell 줄은 실행해 보지 못했습니다(이 문서를 쓴 하네스가 PowerShell 실행을 막습니다). 이 문서의 어떤 명령도 API 키를 읽거나 서버를 띄우지 않습니다. 셸에 진짜 키가 있어도 닿는 곳은 `registry.npmjs.org` 하나이고, 받은 압축 파일은 풀기만 합니다(설치 스크립트가 없습니다).

**이 앱의 모델이 아직 살아 있는지.** 키가 있으면 앱은 `openai/gpt-5.5`를 씁니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:18-29`). OpenAI 폐기 문서(https://developers.openai.com/api/docs/deprecations)와 모델 페이지(https://developers.openai.com/api/docs/models/gpt-5.5)를 2026-10-16에 원문으로 읽었습니다. 폐기 문서에 `gpt-5.5`와 그 스냅숏은 올라 있지 않고, 모델 페이지는 기본 스냅숏을 `gpt-5.5-2026-04-23`, Chat Completions와 Responses를 지원으로 적습니다. 가격은 입력 $5, 캐시 입력 $0.5, 출력 $30(100만 토큰당)입니다. OpenAI 키가 없을 때 고르는 `anthropic/claude-sonnet-4-6`은 Anthropic 폐기 문서(https://platform.claude.com/docs/en/about-claude/model-deprecations)에서 Active, 퇴역은 2027-02-17보다 빠르지 않다고 적혀 있고, `google/gemini-3.1-pro-preview`는 Google 폐기 문서(https://ai.google.dev/gemini-api/docs/deprecations)에 종료일이 없다고 올라 있습니다. 비용 어림(⚠ 추정)은 Step 4에 있습니다.

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 채팅 페이지 (`page.tsx`) | `CopilotKitProvider`와 사이드바. 예시 문구 단추가 메시지를 넣고 에이전트를 돌림 | `generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/page.tsx:160-188` |
| 런타임 (`route.ts`) | 모델 고르기, 시스템 프롬프트, `MCPAppsMiddleware`, `/api/copilotkit` 엔드포인트 | `generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:18-93` |
| MCP 서버 (`server.ts`) | 도구 열여섯, UI 자원 넷, `/mcp`(Streamable HTTP)와 `/health` | `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:98-1136` |
| 항공권 데이터 (`flights.ts`) | 공항 15·항공사 6, 검색·좌석·예약을 난수로 짓고 `Map`에 담음 | `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:176-667` |
| 앱 HTML (`flights-app.html` 외 셋) | 마법사 화면과 `postMessage` 통신 모듈. Vite 단일 파일로 묶여 `apps/dist/`에서 서빙됨 | `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:1096-1786` |
| 호스트 렌더러 (`MCPAppsActivityRenderer`) | 자원을 받아 이중 iframe에 넣고 JSON-RPC를 중개. 앱 저장소 밖(`@copilotkit/react-core` 1.59.2) | 소스로 확인(소스맵) |
| 미들웨어 (`MCPAppsMiddleware`) | UI 도구만 골라 모델에 주고, 모델이 부른 도구를 대신 실행하고, iframe의 요청을 MCP 서버로 전달. 앱 저장소 밖(`@ag-ui/mcp-apps-middleware` 0.0.3) | 소스로 확인(소스맵) |

폴더에서 눈여겨볼 점이 둘 있습니다. `public/sandbox.html`(101줄)은 이중 iframe의 프록시 페이지와 같은 구조의 파일인데, 앱 코드 어디에서도 가리키지 않고 `@copilotkit/react-core` 소스에도 `sandbox.html`이라는 이름이 없습니다(Step 5). 이름과 문구에는 템플릿 흔적이 남아 있습니다. `generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/layout.tsx:17`의 페이지 제목은 "AI Fitness Coach"이고, 앱 README 7행은 존재하지 않는 도구 `workout-generator`를 예로 들며, `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/vite.config.ts:5`의 기본 빌드 대상은 `fitness-app`입니다.

## 단계별 진행

### Step 1. 읽을 준비 — 실행하지 않는 명령과 받아서 풀 패키지

**목적.** 이 앱이 프로세스 둘(Next.js 3000, MCP 서버 3001)이라는 것을 확인하고, 앱 README의 설치 명령을 실행하지 않는 까닭을 밝히고, 읽을 세 패키지의 소스를 꺼냅니다.

**할 일.** 원본 앱 README가 알려 주는 실행 순서는 이렇습니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/README.md:45-55`).

```bash
```bash
# Terminal 1: Build and run MCP Server
cd mcp-server
npm run build
npm run dev
# Server runs at http://localhost:3001/mcp

# Terminal 2: Run Next.js Frontend (from mcp-apps directory)
npm run dev
# Frontend at http://localhost:3000
```
```

이 문서는 위 명령도, 그 앞의 `npm install`도 실행하지 않았습니다. 까닭은 셋입니다. 루트에는 `pnpm-lock.yaml`만 있고 `package-lock.json`이 없어서 `npm install`은 잠금 없이 새로 풉니다. 의존성이 많습니다. `pnpm-lock.yaml`의 `packages:` 절은 788개 항목(제가 센 값)이고 `mcp-server/package-lock.json`은 176개입니다. 그중 `esbuild`(0.27.2)는 `hasInstallScript`가 켜져 있어 설치 때 스크립트가 돕니다. 그리고 `npm run build`가 부르는 `build:app`(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/package.json:17`)은 `rm -rf dist && BUILD_APP=flights-app vite build`처럼 POSIX 셸 문법이라, npm이 Windows에서 스크립트를 기본으로 `cmd.exe`에 넘기므로(npm 문서의 `script-shell`) Git Bash로 npm을 불러도 안 맞을 것으로 읽힙니다. 실행하지 않아 확인하지는 못했습니다.

이제 읽을 패키지를 받습니다. `<저장소>`는 이 저장소를 받은 경로입니다. 저장소 밖 아무 폴더에서 시작합니다.

```bash
mkdir genui-read
cd genui-read
APP=<저장소>/generative_ui_agents/mcp-apps-generative-ui-showcase
mkdir pkg
for spec in "@ag-ui/mcp-apps-middleware/-/mcp-apps-middleware-0.0.3" "@copilotkit/react-core/-/react-core-1.59.2" "@copilotkit/runtime/-/runtime-1.59.2"; do
  name=$(basename "$spec")
  mkdir "pkg/$name"
  curl -sSfL -o "pkg/$name.tgz" "https://registry.npmjs.org/$spec.tgz"
  tar -xzf "pkg/$name.tgz" -C "pkg/$name"
done
ls pkg
```

```powershell
mkdir genui-read
cd genui-read
$APP = "<저장소>\generative_ui_agents\mcp-apps-generative-ui-showcase"
mkdir pkg
foreach ($spec in "@ag-ui/mcp-apps-middleware/-/mcp-apps-middleware-0.0.3", "@copilotkit/react-core/-/react-core-1.59.2", "@copilotkit/runtime/-/runtime-1.59.2") {
  $name = Split-Path $spec -Leaf
  mkdir "pkg\$name"
  curl.exe -sSfL -o "pkg\$name.tgz" "https://registry.npmjs.org/$spec.tgz"
  tar -xzf "pkg\$name.tgz" -C "pkg\$name"
}
ls pkg
```

(`npm pack`이나 `npm install`로도 받을 수 있지만 둘 다 npm을 실행하는 길이라 쓰지 않았습니다. 이 문서는 `curl`로만 받았습니다.) 이 패키지들은 번들되어 있어 소스가 `dist/*.mjs`에 한 줄로 뭉쳐 있습니다. 대신 `.map` 파일의 `sourcesContent`에 원래 TypeScript가 들어 있으니 그것을 꺼내는 스크립트를 저장합니다.

```bash
cat > unmap.mjs <<'EOF'
// 소스맵의 sourcesContent를 이어 붙여 출력한다. JSON을 읽기만 하고 아무것도 실행하지 않는다.
import { readFileSync } from "node:fs";

const map = JSON.parse(readFileSync(process.argv[2], "utf8"));
map.sources.forEach((src, i) => {
  console.log("=== " + src);
  console.log(map.sourcesContent[i]);
});
EOF
node unmap.mjs pkg/mcp-apps-middleware-0.0.3/package/dist/index.mjs.map > mw.txt
node unmap.mjs pkg/react-core-1.59.2/package/dist/copilotkit-B5RsC6la.mjs.map > rc.txt
node unmap.mjs pkg/runtime-1.59.2/package/dist/agent/index.mjs.map > agent.txt
sed -n '4021,4837p' rc.txt > host.txt
```

`host.txt`는 `rc.txt`에서 `MCPAppsActivityRenderer.tsx` 한 파일만 잘라 낸 것입니다. 이 줄 범위는 위 `.map` 파일에서만 맞습니다.

**확인.** 압축 파일이 풀렸고 소스가 나왔는지 봅니다.

```bash
ls pkg
wc -l mw.txt rc.txt agent.txt host.txt
grep -c "" "$APP/src/app/page.tsx" "$APP/mcp-server/server.ts" "$APP/mcp-server/src/flights.ts"
```

```text
mcp-apps-middleware-0.0.3
mcp-apps-middleware-0.0.3.tgz
react-core-1.59.2
react-core-1.59.2.tgz
runtime-1.59.2
runtime-1.59.2.tgz
   615 mw.txt
 19162 rc.txt
  1745 agent.txt
   817 host.txt
 22339 total
/…/page.tsx:343
/…/server.ts:1136
/…/flights.ts:667
```

(앞 줄 경로는 줄여 적었습니다. `ls`는 환경에 따라 순서가 다를 수 있습니다.)

![Step 1까지의 구성](diagrams/step1.svg)

### Step 2. MCP 서버 — 도구가 화면 조각을 가리키는 법

**목적.** 서버가 도구 열여섯과 HTML 자원 넷을 어떻게 등록하는지, 도구와 자원이 어떻게 이어지는지 읽습니다.

**할 일.** 서버는 `@modelcontextprotocol/sdk` 1.25.2의 `McpServer`로 도구를 등록합니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:98-105`). 자원 등록은 헬퍼 하나가 하고, 항공권 자원은 `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:133-143`입니다.

```ts
  const flightsResource = registerResource(
    {
      name: "flights-app-template",
      uri: "ui://flights/flights-app.html",
      title: "Airline Booking",
      description:
        "Interactive flight search and booking wizard with seat selection",
      mimeType: "text/html+mcp",
    },
    flightsAppHtml,
  );
```

`mimeType: "text/html+mcp"`가 이 자원이 MCP 앱의 HTML이라는 표시이고, 주소는 `ui://flights/flights-app.html`입니다. 도구 쪽은 `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:207-215`에서 `_meta`에 이 주소를 답니다.

```ts
        cabinClass: z
          .enum(["economy", "business", "first"])
          .optional()
          .describe("Cabin class (default: economy)"),
      },
      _meta: {
        [RESOURCE_URI_META_KEY]: flightsResource.uri,
      },
    },
```

이 연결을 단 도구는 넷입니다. 나머지 열둘에는 `_meta`가 없습니다.

| 앱 | UI 도구(`_meta` 있음) | 도우미 도구(`_meta` 없음) |
|---|---|---|
| 항공권 | `search-flights` | `select-flight`·`select-seats`·`book-flight` |
| 호텔 | `search-hotels` | `select-hotel`·`select-room`·`book-hotel` |
| 투자 시뮬레이터 | `create-portfolio` | `execute-trade`·`refresh-prices` |
| 칸반 | `create-board` | `move-card`·`add-card`·`update-card`·`delete-card` |

HTML은 소스 폴더의 `apps/flights-app.html`을 그대로 주지 않습니다. `loadHtml`은 `apps/dist/<이름>.html`을 읽고, 없으면 "Loading... The app UI needs to be built" 문구가 든 자리표시 HTML을 돌려줍니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:74-95`). `dist/`는 `build:app`이 Vite 단일 파일 플러그인으로 만듭니다. 그리고 `getServer`(98행)는 새 MCP 연결이 시작될 때마다 불려서 네 파일을 처음부터 다시 읽습니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:108-111`). 호출하는 곳은 `initialize` 요청을 받는 분기(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:1030-1051`)입니다.

**확인.** 도구 수와 `_meta`를 단 도구 수, 자원의 MIME 표시를 셉니다.

```bash
grep -c "server.registerTool(" $APP/mcp-server/server.ts
grep -c "\[RESOURCE_URI_META_KEY\]" $APP/mcp-server/server.ts
grep -c 'mimeType: "text/html+mcp"' $APP/mcp-server/server.ts
```

```text
16
4
4
```

![Step 2까지의 구성](diagrams/step2.svg)

### Step 3. 가짜 데이터 — 항공권은 요청마다 난수로 지어집니다

**목적.** 이 앱의 항공권·호텔·종목이 실제 데이터가 아니라는 것과 어디에 사는지를 확인합니다.

**할 일.** `flights.ts`의 머리 주석이 "mock airport/airline data"라고 밝힙니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:1-4`). 항공편은 검색할 때마다 지어집니다. 편수는 5~8개 무작위이고, 항공사는 여섯을 돌려 가며 고르고, 편명 번호·가격(±20%)·경유 횟수·남은 좌석도 `Math.random()`입니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:405-413`). 그래서 같은 질문을 두 번 하면 다른 항공편이 나옵니다. 좌석 배치는 항공편 아이디를 씨앗으로 하는 난수라 같은 편에서는 같습니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:489-537`). 검색과 예약은 모듈 안의 `Map` 둘에 쌓이고(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:176-177`), 예약이 끝나면 그 검색은 지워집니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:653`). 결제는 어디에도 없습니다. 서버 프로세스가 죽으면 모두 사라집니다.

서버는 포트폴리오와 칸반 보드도 "세션별로 저장한다"고 주석을 달지만(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:66-70`) 저장소는 `Map` 하나이고 키는 포트폴리오·보드 아이디입니다. MCP 세션과 무관합니다. 연결마다 세션이 새로 생겨도 데이터가 이어지는 까닭이 이것입니다(Step 4).

데이터의 수는 원본 README가 적은 숫자(공항 15·도시 10·호텔 30·종목 18)와 맞는지 셉니다. 아래 스크립트를 저장해 돌립니다.

```bash
cat > count.mjs <<'EOF'
// 가짜 데이터 파일에서 항목 수를 센다. 파일을 읽기만 하고 앱 코드는 실행하지 않는다.
import { readFileSync } from "node:fs";

const dir = process.argv[2];
const read = (name) => readFileSync(`${dir}/${name}`, "utf8");
const between = (text, from, to) => text.slice(text.indexOf(from), text.indexOf(to));
const count = (text, re) => (text.match(re) || []).length;

const flights = read("flights.ts");
console.log("공항", count(between(flights, "const AIRPORTS", "const AIRLINES"), /code: "/g));
console.log("항공사", count(between(flights, "const AIRLINES", "const AIRCRAFT_TYPES"), /code: "/g));

const hotels = read("hotels.ts");
console.log("도시", count(between(hotels, "const CITIES", "const ROOM_CONFIGS"), /name: "/g));
console.log("호텔", count(between(hotels, "const HOTELS", "export const hotelSearches"), /^ {6}name: "/gm));

const stocks = read("stocks.ts");
console.log("종목", count(between(stocks, "const STOCKS", "const portfolios"), /symbol: "/g));

console.log("flights.ts의 Math.random 호출", count(flights, /Math\.random\(\)/g));
EOF
node count.mjs $APP/mcp-server/src
```

**확인.**

```text
공항 15
항공사 6
도시 10
호텔 30
종목 18
flights.ts의 Math.random 호출 11
```

앱 README의 숫자와 같고, 항공편이 난수라는 것도 보입니다(열한 곳).

![Step 3까지의 구성](diagrams/step3.svg)

### Step 4. 런타임과 미들웨어 — 모델에게는 UI 도구 넷만 보입니다

**목적.** 모델을 고르는 곳, 모델이 보는 도구, 모델이 도구를 부른 뒤 일어나는 일을 읽습니다.

**할 일.** 모델은 환경변수의 키 순서로 정합니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:18-29`).

```ts
const determineModel = () => {
  if (process.env.OPENAI_API_KEY?.trim()) {
    return "openai/gpt-5.5";
  }
  if (process.env.ANTHROPIC_API_KEY?.trim()) {
    return "anthropic/claude-sonnet-4-6";
  }
  if (process.env.GOOGLE_API_KEY?.trim()) {
    return "google/gemini-3.1-pro-preview";
  }
  return "openai/gpt-5.5";
};
```

셸에 OpenAI 키가 없고 다른 제공자 키가 있으면 그쪽으로 갑니다. 셋 다 없으면 `openai/gpt-5.5`인 채로 요청 때 키가 없다고 실패할 것으로 읽힙니다(`@copilotkit/runtime`의 `resolveModel`이 `process.env.OPENAI_API_KEY!`를 그대로 넘깁니다, 소스로 확인). 같은 파일의 시스템 프롬프트는 네 앱을 설명하고 도우미 도구 이름도 댑니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:42`·`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:48`·`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:54`·`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:60`). 그런데 모델에게 실제로 주어지는 도구는 이 이름들이 아닙니다. 미들웨어가 끼는 곳은 이렇습니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:67-76`).

```ts
}).use(
  new MCPAppsMiddleware({
    mcpServers: [
      {
        type: "http",
        url: process.env.MCP_SERVER_URL || "http://localhost:3001/mcp",
      },
    ],
  }),
);
```

`MCPAppsMiddleware`(0.0.3)의 `run`은 요청이 올 때마다 MCP 서버에 붙어 `tools/list`를 받고, `_meta["ui/resourceUri"]`가 문자열인 도구만 남겨(`hasUIResource`) 모델에게 가는 도구 목록에 더합니다. 이 앱이 `page.tsx`에서 프런트엔드 도구를 따로 등록하지 않으므로(소스로 확인) 모델의 도구는 `search-flights`·`search-hotels`·`create-portfolio`·`create-board` 넷이 전부입니다. 도우미 열둘은 모델에게 보이지 않고, 시스템 프롬프트가 이름을 대고 있어도 모델이 부를 수 없습니다. 모델이 그 넷 가운데 하나를 부르면, 미들웨어는 모델의 스트림이 끝난 뒤에 그 도구 호출에 결과가 없는 것을 찾아 직접 MCP 서버에 `tools/call`을 하고, 두 이벤트를 만들어 냅니다. 글로 된 결과(`TOOL_CALL_RESULT`)와 `activityType: "mcp-apps"`인 `ACTIVITY_SNAPSHOT`입니다. 스냅숏의 내용은 도구 결과, `resourceUri`, 서버 해시, 모델이 준 인자(`toolInput`)입니다. HTML은 싣지 않고 주소만 싣습니다. 모델이 보는 길과 iframe이 부르는 길이 어디서 갈라지는지는 아래 그림입니다.

![모델과 iframe이 부르는 도구](diagrams/extra-tools.svg)

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 소스 맵에서 꺼낸 미들웨어 소스로 위 설명을 확인합니다.

```bash
grep -n 'hasUIResource\|new Client(\|client.connect\|case "\|MCP method not allowed' mw.txt
```

```text
107:function hasUIResource(tool: { _meta?: Record<string, unknown> }): boolean {
289:    const client = new Client(
303:      await client.connect(transport);
308:        case "tools/call":
312:        case "resources/read":
314:        case "notifications/message":
321:        case "ping":
325:            `MCP method not allowed for UI proxy: ${method}`
468:    const client = new Client(
482:      await client.connect(transport);
579:    const client = new Client(
594:      await client.connect(transport);
601:        .filter(hasUIResource)
```

읽을 곳은 세 가지입니다. `new Client(`가 세 군데(289·468·579행)이고 모두 바로 뒤에서 `client.connect`를 하고 `finally`에서 닫으므로 MCP 연결은 쓰일 때마다 새로 맺고 닫습니다. 목록 받기(579행 아래)와 도구 실행(468행 아래)이 질문 한 번에 연결을 둘 쓰고, 뒤에 나오는 자원 읽기(289행 아래, Step 5)가 하나 더입니다. 601행이 필터이고, 308~323행의 `case`들이 iframe이 프록시로 보낼 수 있는 메서드의 전부입니다(`tools/call`·`resources/read`·`notifications/message`·`ping`). 허용하는 **도구 이름**을 거르는 곳은 없습니다. iframe은 UI 도구가 아닌 도우미 열둘도, UI 도구도 이름만 알면 부를 수 있습니다.

모델 호출이 한 번이라는 것은 이렇게 읽습니다. `BuiltInAgent`의 `maxSteps`는 설정하지 않았고 그 설정의 주석이 기본을 1이라 적습니다(`agent.txt`, 소스로 확인). 같은 실행 안에서 도구 결과가 모델에게 돌아가 다시 답하게 하는 호출은 소스에 보이지 않고, 결과는 대화에만 남는 것으로 읽힙니다. 비용은 이렇게 어림합니다(⚠ 추정). 시스템 프롬프트는 261낱말·1,926자이고(`route.ts` 34~66행의 `wc`), 4자에 1토큰으로 어림하면 약 500토큰입니다. 도구 넷의 설명과 스키마, 대화 내용을 더해 한 번에 입력 1,500~2,500토큰 정도로 잡으면 입력이 $0.01 안팎이고 출력(도구 호출 한 줄)은 그 몇 분의 일입니다. 이 숫자는 대화가 길어질수록 커집니다. 마법사 안의 클릭에는 모델 비용이 붙지 않습니다. 단 마법사 마지막 화면의 [Add to Calendar] 단추는 예외입니다. 이 단추는 `ui/message`로 "Add this flight to my calendar"라는 사용자 메시지를 채팅에 넣고(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:1716-1721`) 에이전트를 다시 돌리는데, 모델의 도구 가운데 일정 도구는 없으므로 말로만 답할 것으로 읽힙니다.

### Step 5. 호스트 쪽 — 이중 iframe, 출처, 크기 알림

**목적.** 브라우저가 자원을 받아 어떻게 가두는지, 사양이 말하는 것과 이 구현이 하는 것이 어디서 갈리는지 읽습니다.

**할 일.** 스냅숏이 오면 `MCPAppsActivityRenderer`(react-core 1.59.2, 저장소 밖)가 두 가지를 합니다. 먼저 HTML을 가져옵니다. 에이전트를 한 번 더 `runAgent`로 부르되 `forwardedProps.__proxiedMCPRequest`에 `resources/read`와 주소를 실어 보내고, 미들웨어는 이 요청을 모델로 보내지 않고 MCP 서버에 `resources/read`로 전달해 HTML 한 장을 돌려줍니다.

![자원 읽기 시퀀스](diagrams/extra-resource.svg)

그다음 iframe을 둘 만듭니다. 바깥 iframe은 프록시 HTML을 `srcdoc`으로 가지고, 그 안에서 안쪽 iframe이 앱 HTML을 `srcdoc`으로 가집니다. 둘의 `sandbox` 값은 같습니다.

![이중 iframe 구조](diagrams/extra-sandbox.svg)

호스트의 소스는 이렇습니다. 저장소 밖 소스라 줄 범위는 `host.txt` 기준이고(450~453행, 496행, 289행), 세 곳을 `...`로 이어 붙였습니다.

```text
          iframe.setAttribute(
            "sandbox",
            "allow-scripts allow-same-origin allow-forms",
          );
...
            if (event.source !== iframe.contentWindow) return;
...
        iframeRef.current.contentWindow.postMessage(msg, "*");
```

세 줄이 말하는 것은 이렇습니다. 첫째, 사양(SEP-1865, https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx 를 2026-10-16에 읽음)은 웹 호스트의 샌드박스에 `allow-scripts`와 `allow-same-origin`을 요구하면서 "호스트와 샌드박스는 출처가 달라야 한다(MUST)"고 적습니다. 이 구현은 프록시를 별도 출처의 주소가 아니라 `srcdoc` 문자열로 만듭니다. 앱 폴더의 `public/sandbox.html`은 같은 일을 하는 파일이지만 이 버전의 호스트는 쓰지 않습니다(아래 확인). `srcdoc` 문서는 만든 쪽의 출처를 물려받는 것으로 알고 있으므로, 이 조합에서는 안쪽 앱이 부모 문서에 손댈 수 있고 MDN이 "`allow-scripts`와 `allow-same-origin`을 함께 쓰면 `sandbox` 속성을 스스로 지울 수 있어 속성이 없는 것과 같아진다"고 경고한 상황에 해당할 것으로 읽힙니다. 다만 이 문서는 브라우저를 열지 않았고 그 출처를 직접 보지 않았습니다. 둘째, 메시지 처리는 **보낸 창**(`event.source`)이 방금 만든 iframe인지만 보고 `event.origin`은 보지 않습니다. 셋째, 호스트가 iframe에 보낼 때 대상 출처가 `"*"`입니다. 사양 문서의 예시도 `'*'`를 쓰고 출처 검사를 정하지 않으니 사양을 벗어난 것은 아닙니다.

크기 알림이 하나 어긋납니다. 호스트가 듣는 이름은 `ui/notifications/size-changed`이고 그 알림이 와야 iframe 높이를 바꿉니다. 처음 높이는 100px입니다. 네 앱이 모두 `ui/notifications/size-change`로 보냅니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:1695-1703`). 공식 사양 문서에도 호스트에도 앞의 이름은 없습니다. 호스트가 이 이름을 따로 받지 않는 한 iframe은 100px에 머물 것으로 읽히지만, 이 문서는 화면을 열지 않았으므로 단정하지 않습니다(문제 해결 표).

앱이 열리면 앱이 먼저 `ui/initialize`를 보내고 호스트가 답한 뒤, 호스트가 `tool-input`과 `tool-result`를 앱에 보냅니다. 호스트가 받아 주는 앱의 요청은 `ui/initialize`·`ui/message`·`ui/open-link`·`tools/call` 넷이고, 그 밖의 메서드에는 "Method not found" 오류를 돌려줍니다.

![핸드셰이크 시퀀스](diagrams/extra-handshake.svg)

**확인.** 위 세 줄과 이름 불일치를 직접 찾아봅니다. (`host.txt`는 Step 1에서 만들었습니다.)

```bash
grep -n 'allow-scripts allow-same-origin allow-forms' host.txt
grep -n 'event.source !== iframe.contentWindow' host.txt
grep -c 'event.origin' host.txt
grep -n 'size-changed"' host.txt
grep -c 'size-change"' host.txt
grep -rn 'ui/notifications/size-change"' $APP/mcp-server/apps | cut -d: -f1,2 | sed 's#.*/##'
grep -c "sandbox.html" rc.txt
grep -rn "sandbox.html" $APP/src $APP/next.config.ts $APP/mcp-server/server.ts
```

```text
33:inner.setAttribute("sandbox","allow-scripts allow-same-origin allow-forms");
452:            "allow-scripts allow-same-origin allow-forms",
496:            if (event.source !== iframe.contentWindow) return;
0
676:                case "ui/notifications/size-changed": {
0
flights-app.html:1698
hotels-app.html:1685
kanban-app.html:1144
trading-app.html:1130
0
```

(마지막 `grep -rn`은 아무것도 출력하지 않습니다. 줄 번호는 `host.txt` 기준입니다.) 앱 쪽 이름은 네 파일 모두 `size-change"`이고 호스트는 `size-changed"`입니다.

![Step 5까지의 구성](diagrams/step5.svg)

### Step 6. 앱 안 — 마법사가 모델 없이 도구를 부르는 법

**목적.** iframe 안의 앱이 호스트와 어떻게 이야기하는지, 마법사 한 단계가 어떤 길을 지나는지 읽습니다.

**할 일.** 앱의 통신 모듈은 요청과 응답을 번호로 짝짓는 작은 JSON-RPC입니다. 받는 쪽은 `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:1107-1109`입니다.

```js
        window.addEventListener("message", (event) => {
          const msg = event.data;
          if (!msg || typeof msg !== "object") return;
```

메시지가 어디서 왔는지(`event.source`·`event.origin`)를 보지 않고, 객체이기만 하면 받습니다. 보내는 쪽은 `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:1131-1140`입니다.

```js
          sendRequest(method, params) {
            const id = requestId++;
            return new Promise((resolve, reject) => {
              pendingRequests.set(id, { resolve, reject });
              window.parent.postMessage(
                { jsonrpc: "2.0", id, method, params },
                "*",
              );
            });
          },
```

`window.parent.postMessage(…, "*")`입니다. 부모는 바깥 iframe(프록시)이고, 프록시는 `event.source`가 안쪽 iframe일 때만 위로 전달합니다. 마법사의 각 단계가 부르는 도구는 네 번입니다. 검색은 `search-flights`(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:1313-1322`)인데, 모델이 이미 한 검색이 `tool-result`로 먼저 와 있으면 그 결과로 곧바로 2단계를 그립니다. 이어서 항공편을 고르면 `select-flight`, 좌석을 확정하면 `select-seats`, 승객 정보를 넣으면 `book-flight`입니다. 세 번 모두 같은 길을 지납니다. 앱이 `tools/call`을 보내면 호스트가 `agent.runAgent`에 `__proxiedMCPRequest`를 실어 런타임으로 보내고, 미들웨어가 모델 없이 MCP 서버에 `tools/call`을 하고, 결과가 `RUN_FINISHED`의 `result`로 돌아와 호스트가 앱에 JSON-RPC 응답으로 넘깁니다. 호스트는 이런 요청을 큐에 넣어 하나씩 처리하고 에이전트가 실행 중이면 끝나기를 기다립니다.

![항공편 선택 시퀀스](diagrams/extra-flight.svg)

![좌석 확정 시퀀스](diagrams/extra-seats.svg)

![예약 시퀀스](diagrams/extra-book.svg)

서버 쪽에서는 `select-flight`가 검색을 찾아 `selectedFlightId`를 적고 좌석표를 만들고, `select-seats`는 그 항공편이 선택된 것인지와 좌석이 비었는지 보고 요금을 합치고, `book-flight`는 승객 수가 검색의 인원과도, 고른 좌석 수와도 같을 때만 예약을 만듭니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:467-483`·`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:542-586`·`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:591-660`). 칸반 앱은 카드 제목과 설명을 이스케이프 없이 `innerHTML`로 넣습니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/kanban-app.html:1216-1218`). 카드 내용은 모델이 지은 도구 인자에서 오므로, 이 앱을 가두는 것은 앱 코드의 정제가 아니라 Step 5의 iframe뿐입니다.

**확인.** 앱이 부르는 도구 이름과 통신 모듈의 검사를 찾아봅니다.

```bash
grep -h -A1 'sendRequest("tools/call"' $APP/mcp-server/apps/flights-app.html | grep -o 'name: "[a-z-]*"'
grep -c "event.origin\|event.source" $APP/mcp-server/apps/flights-app.html
grep -c 'postMessage' $APP/mcp-server/apps/flights-app.html
```

```text
name: "search-flights"
name: "select-flight"
name: "select-seats"
name: "book-flight"
0
2
```

![Step 6까지의 구성](diagrams/step6.svg)

### Step 7. 직접 돌린다면 — 먼저 알아 둘 것

**목적.** 이 문서가 실행하지 않은 부분을 독자가 실행할 때 무엇이 바깥에 닿는지 소스로 미리 적어 둡니다. 아래 명령은 이 문서가 실행해 보지 못한 것입니다.

**할 일.** 바깥에 닿는 것은 이렇습니다. 앱을 그대로 띄우면 MCP 서버는 `app.listen(PORT)`이라 호스트를 정하지 않아 모든 네트워크 인터페이스에 열립니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:1117`). CORS는 `origin: "*"`이고(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:1010-1015`) `/mcp`에는 인증이 없어서, 같은 네트워크의 누구나 열여섯 도구를 부를 수 있습니다. 데이터는 가짜지만 서버 메모리에 쌓입니다. `next dev`와 `next start`의 호스트 기본값은 `0.0.0.0`입니다(Next.js CLI 문서를 2026-10-16에 읽음). 런타임 엔드포인트도 CORS를 열어 두고(`createCopilotEndpoint`에 `cors`를 주지 않으면 모든 출처를 허용한다고 소스에 적혀 있음) 인증이 없으니, 키가 든 `/api/copilotkit`이 같은 네트워크에 열립니다. 텔레메트리는 둘입니다. CopilotKit 런타임은 `https://telemetry.copilotkit.ai/ingest`로 이벤트를 보내되 익명 이벤트를 5%만 보내고, `DO_NOT_TRACK=1`이나 `COPILOTKIT_TELEMETRY_DISABLED=true`로 끕니다. 런타임은 매 실행 요청에도 `oss.runtime.copilot_request_created` 이벤트를 만듭니다(둘 다 소스로 확인). Next.js의 익명 텔레메트리는 `NEXT_TELEMETRY_DISABLED=1`로 끕니다(Next 문서). 화면에서는 `showDevConsole="auto"`가 `localhost`·`127.0.0.1`에서만 인스펙터를 켭니다(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/page.tsx:162`). 브라우저는 앱 iframe이 열릴 때 Google Fonts에서 글꼴을 받고(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:7-10`), `layout.tsx`가 가져오는 `next/font/google`도 Google 글꼴을 쓰는 경로입니다(Next가 언제 무엇을 내려받는지는 확인하지 않았습니다).

그러므로 독자가 돌린다면 위 점을 막는 쪽으로 시작합니다. 새 폴더에 복사본을 만들고, 복사본에서만 MCP 서버의 줄 하나를 고쳐 루프백에만 엽니다.

```bash
cp -r $APP app-copy
cd app-copy/mcp-server
# server.ts의 app.listen(PORT, () => {  를  app.listen(PORT, "127.0.0.1", () => {  로 고친다
export DO_NOT_TRACK=1 COPILOTKIT_TELEMETRY_DISABLED=true NEXT_TELEMETRY_DISABLED=1
```

그다음 `npm ci` → `npm run build`(`build:app`이 POSIX 문법이므로 Git Bash가 아닌 Windows에서는 안 될 수 있습니다) → `npm run dev`로 서버를, 다른 터미널에서 `npm install`(또는 루트의 `pnpm-lock.yaml`에 맞게 `pnpm install`) 뒤 `npm run dev -- -H 127.0.0.1`(`--`는 npm이 `next`에 플래그를 넘기는 문법)로 화면을 띄웁니다. 터미널마다 위 `export`를 다시 합니다. `.env.local`에 `OPENAI_API_KEY`를 넣으면 질문마다 위에서 어림한 비용이 듭니다. 셸에 `MCP_SERVER_URL`이 있으면 미들웨어가 그 주소로 붙고(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:72`), `ANTHROPIC_API_KEY`나 `GOOGLE_API_KEY`가 있고 OpenAI 키가 없으면 그 제공자로 요청이 갑니다. 이 문서는 위 명령을 하나도 실행하지 않았고, 설치 단계의 `esbuild` 설치 스크립트도 실행하지 않았습니다.

**확인.** 이 문서가 읽은 것과 읽지 못한 것을 나눕니다.

- 직접 확인한 것: 위 `grep`·`wc`·`count.mjs` 출력, 레지스트리 메타데이터(`engines`), 잠금 파일의 항목 수.
- 소스로 확인한 것: 서버·런타임·앱 HTML·세 패키지의 동작. 모두 읽기였고 실행하지 않았습니다.
- 확인하지 못한 것: 화면에서 마법사가 어떻게 보이는지, iframe 높이, `srcdoc` iframe의 실제 출처, 진짜 모델이 도구를 고르는 모습, `npm`·`pnpm` 설치와 `vite build`의 성공 여부, 서버 세션 맵(`transports`)이 연결마다 비는지.

![Step 7까지의 구성](diagrams/step7.svg)

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

"예시 문구 클릭"에서 모델의 도구 호출 결과까지가 위 그림입니다. `page.tsx`의 단추가 메시지를 넣고 `copilotkit.runAgent`를 부르면(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/page.tsx:175-188`) 브라우저가 `/api/copilotkit`에 `POST`하고, 런타임의 미들웨어가 먼저 MCP 서버에서 도구를 받아 UI 도구만 모델에게 줍니다. 모델이 `search-flights`와 인자를 돌려주면 미들웨어가 그것을 MCP 서버에 실행하고, 결과와 `mcp-apps` 스냅숏이 브라우저에 갑니다. 이 한 번의 질문에 모델 호출은 한 번, MCP 연결은 둘입니다. 이어지는 자원 읽기가 연결 하나를 더 쓰고(Step 5), 앱이 열려 `tool-result`를 받으면 곧바로 검색 결과 화면(2단계)을 그립니다(Step 6). 그다음부터는 마법사의 클릭마다 같은 우회 길(Step 6의 세 그림)을 한 번씩 지나, 항공권 하나를 예약하기까지 MCP 연결이 모두 여섯 번 열립니다. 모델은 처음 한 번 말고는 관여하지 않습니다.

## 실행 체크리스트

- [ ] Step 1: 세 패키지를 받아 풀고 `mw.txt`·`rc.txt`·`agent.txt`·`host.txt`의 줄 수가 615·19162·1745·817인지 확인했다
- [ ] Step 2: `registerTool`이 16개이고 `_meta`를 단 도구가 4개인 것을 확인했다
- [ ] Step 3: `count.mjs`가 공항 15·항공사 6·도시 10·호텔 30·종목 18을 낸다
- [ ] Step 4: 미들웨어 소스에서 `hasUIResource` 필터와 `new Client(` 세 곳을 찾았다
- [ ] Step 5: `host.txt`에서 `sandbox` 값과 `size-changed`를, 앱에서 `size-change`를 찾아 이름이 다른 것을 확인했다
- [ ] Step 6: 앱이 부르는 도구 이름 넷과 `event.origin` 검사가 0건인 것을 확인했다
- [ ] Step 7: 원본을 그대로 띄우면 모든 인터페이스에 열린다는 것, 끄는 환경변수 셋을 이해했다
- [ ] 앱을 띄우지 않았고 `npm install`·`npx`를 실행하지 않았다(`ls $APP`에 `node_modules`가 없다)

## 문제 해결

표의 증상은 모두 이 문서가 소스에서 읽은 것이고, 화면에서 직접 본 것은 없습니다.

| 증상 | 원인 | 해결 |
|---|---|---|
| 앱 자리에 "flights-app Loading... The app UI needs to be built"가 뜬다 | `apps/dist/`가 없다. `loadHtml`이 자리표시 HTML을 돌려준다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:74-95`) | `mcp-server`에서 `npm run build`. Windows 비Bash 셸에서는 `build:app`이 안 될 수 있어 Git Bash에서 `npm`을 부르거나 Vite 빌드 네 번을 `BUILD_APP`을 환경에 걸고 따로 돌린다 |
| 마법사가 100px 높이로 잘려 보인다 | 앱은 `size-change`를, 호스트(react-core 1.59.2)는 `size-changed`를 듣는다(Step 5) ⚠ 소스로 읽은 추정 | 복사본의 `apps/*.html` 네 곳의 알림 이름을 `size-changed`로 고치고 다시 빌드. 고치기 전 높이와 비교해 본다 |
| `Invalid airport code: XXX` | 공항 코드는 15개뿐이다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:395-399`) | JFK·LAX·LHR·CDG·NRT·DXB·SIN·SFO·ORD·MIA·SEA·BOS·FRA·HKG·SYD 중에서 고른다 |
| 예약 직후 같은 검색으로 좌석을 또 고르면 "Search session not found" | 예약이 끝나면 검색을 지운다(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/src/flights.ts:653`). 서버를 다시 띄워도 `Map`이 비어 같은 오류가 난다 | 새로 검색한다 |
| [Add to Calendar]를 눌러도 일정이 안 생긴다 | 단추는 채팅에 문장만 넣고, 모델의 도구에 일정 도구가 없다(Step 4) | 일정 도구를 가진 MCP 서버를 `mcpServers`에 더하거나 단추를 지운다 |
| 키가 없는데 질문하면 실패한다 | OpenAI·Anthropic·Google 키가 모두 비어 있으면 `openai/gpt-5.5`가 키 없이 불린다(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:28`) | `.env.local`에 `OPENAI_API_KEY` |
| `vite`가 Node 버전 경고나 오류를 낸다(⚠ `engines`에서 읽은 것) | `vite@7.3.1`은 Node `^20.19.0 \|\| >=22.12.0`이 필요한데 `mcp-server/.nixpacks`는 20.18.1이다 | Node 20.19 이상으로 맞춘다 |
| 페이지 제목이 "AI Fitness Coach"로 보인다 | 템플릿 이름이 남았다(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/layout.tsx:17`) | 코드에 영향 없음. 필요하면 고친다 |

## 더 해보기

- **크기 알림 이름을 고쳐 본다.** 복사본에서 `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/apps/flights-app.html:1698`의 `size-change`를 `size-changed`로 바꾸고 다시 빌드해 iframe 높이가 달라지는지 본다(이 문서는 해 보지 못했습니다).
- **iframe이 부를 수 있는 도구에 허용 목록을 둔다.** 미들웨어는 도구 이름을 거르지 않습니다(Step 4). `generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:67-76`의 `MCPAppsMiddleware`를 상속해 `run`에서 `forwardedProps.__proxiedMCPRequest`의 `params.name`이 허용된 이름일 때만 부모를 부르게 해 보고, 허용되지 않은 `book-flight`가 어떻게 막히는지 적어 본다.
- **새 앱을 하나 더한다.** 항공권과 같은 모양으로 `search-trains` 도구와 `ui://trains/trains-app.html` 자원을 `generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:133-143`·`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/server.ts:188-215`처럼 등록하고, `build:app`(`generative_ui_agents/mcp-apps-generative-ui-showcase/mcp-server/package.json:17`)에 빌드 줄을 더한다. 시스템 프롬프트(`generative_ui_agents/mcp-apps-generative-ui-showcase/src/app/api/copilotkit/[[...slug]]/route.ts:34-66`)에 안 적어도 모델이 새 도구를 고르는지 본다.

## 다음 날 예고

[Day 146 · 🛠️ AI MCP App Builder](../day146-genui-mcp-app-builder/README.md) — 오늘은 서버가 미리 만든 HTML 네 장을 띄웠다면 내일은 **에이전트가 MCP 앱 자체를 지어 냅니다.** 원본 `generative_ui_agents/ai-mcp-app-builder`는 pnpm 모노레포이고, 락 파일과 이미지를 뺀 추적 파일 135개의 `wc -l` 합계가 21,782줄입니다. 그중 51개(13,388줄)는 `apps/mcp-use-server/.agent/`의 스킬 문서이고, 코드는 `.ts`·`.tsx`·`.js`·`.jsx`가 7,122줄입니다. 중심은 `apps/web/app/api/mastra-agent/route.ts`(920줄)의 Mastra 에이전트와 `apps/web/app/api/workspace/` 아래 파일 도구 여섯, 그리고 `apps/web/app/components/McpAppPreview.tsx`(204줄)의 미리보기입니다. 이 미리보기도 `sandbox="allow-scripts allow-same-origin"`인 iframe입니다(199행). 에이전트가 지은 MCP 서버는 E2B 클라우드 샌드박스(`E2B_API_KEY`)에서 돌아가며 이 문서의 규칙대로 소스로만 읽습니다. 모델은 `OPENAI_MODEL`이 없으면 `gpt-5.5`입니다(`generative_ui_agents/ai-mcp-app-builder/apps/web/app/api/mastra-agent/route.ts:783`).
