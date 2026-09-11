# 133일 튜토리얼 시리즈 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/tutorials/` 아래에 D2 다이어그램 렌더·검사 도구, 133일 로드맵, 그리고 Day 1(xAI Finance Agent) 완성본을 만들어 시리즈 제작 파이프라인을 가동한다. 이후 볼륨 제작은 같은 절차를 반복한다.

**Architecture:** `docs/tutorials/_tools/`의 Node 스크립트(ESM)가 `.d2` → `.svg` 렌더(`render.mjs`), 문서 정합성 검사(`check.mjs`), 일차 폴더 생성(`scaffold.mjs`), 로드맵 생성(`roadmap.mjs`)을 맡는다. 일차 데이터는 `_tools/days.json` 하나가 원천이다. 각 일차는 `dayNNN-slug/README.md` + `diagrams/*.d2|svg`로 구성되며, `stepK.d2`는 `...@overview` import로 배치를 공유하고 클래스만 덧씌운다.

**Tech Stack:** Node.js 24 (ESM, `node:test`), `@terrastruct/d2` npm(D2 0.7 계열 WASM 렌더러, ELK 레이아웃), Markdown, uv 0.7 (앱 검증용).

**Spec:** `docs/superpowers/specs/2026-09-11-tutorial-series-design.md`

## Global Constraints

- 문서 본문은 한국어, 코드·명령·파일명·식별자·에러 메시지는 원문 그대로.
- 앱 코드를 수정하거나 새로 쓰지 않는다. 리포의 실제 파일을 발췌하고 `경로:시작-끝` 형식으로 위치를 적는다.
- 하루 문서의 H2 제목 9개는 스펙 4절 문자열 그대로: `오늘 만들 것`, `사전 준비`, `아키텍처 한눈에 보기`, `단계별 진행`, `요청 한 건이 흐르는 과정`, `실행 체크리스트`, `문제 해결`, `더 해보기`, `다음 날 예고`.
- 다이어그램 클래스는 기본 5개(`person`, `ours`, `ext`, `store`, `file`)와 각각의 `-new`, `-todo` 변형(예: `ours-new`, `ext-todo`)까지 15개만. `stepK.d2`의 덧씌우기는 `x.class: ours-new`처럼 **단일 클래스**로 한다. 배열 덧씌우기 `x.class: [a; b]`는 선언 뒤에 오면 이 렌더러가 무시한다(2026-09-11 프로브로 확인). 한 그림 노드 12개 이하. `sketch` 금지. 레이아웃 ELK.
- D2 렌더러의 ELK 워커는 Node 이벤트 루프를 붙잡아 프로세스가 스스로 끝나지 않는다. 렌더하는 스크립트는 마지막에 `process.exit(code)`를 호출하고, 테스트는 `node --test --test-force-exit`로 돈다.
- 렌더 옵션: `layout: "elk"`, `sketch: false`, `pad: 20`, `noXMLTag: true`.
- SVG는 커밋한다. `node_modules/`는 커밋하지 않는다(이미 `.gitignore`에 있음). `_tools/package-lock.json`은 커밋한다.
- 일차 번호와 폴더명은 `_tools/days.json`(= 스펙 부록 A)에서 가져오고 한 번 커밋되면 바꾸지 않는다.
- API 키가 필요한 앱은 실행하지 않는다. 키 없이 가능한 확인(의존성 설치, `python -m py_compile`, import 확인)만 한다.
- 커밋은 `main`에 직접. 푸시는 사용자가 요청할 때만. 커밋 메시지 끝에 세션의 attribution 줄을 붙인다.
- 모든 명령은 리포 루트 `D:\ws-llm\awesome-llm-apps`에서 실행하는 것으로 적는다(도구 명령은 `docs/tutorials/_tools`에서).

---

## File Structure

| 파일 | 책임 |
|---|---|
| `docs/tutorials/_tools/package.json` | 의존성(`@terrastruct/d2`)과 npm 스크립트(`render`, `check`, `test`, `scaffold`, `roadmap`) |
| `docs/tutorials/_tools/theme.d2` | 공통 클래스 7개와 `direction: right` |
| `docs/tutorials/_tools/lib/d2.mjs` | `inlineImports`, `sourceHash`, `readSvgHash`, `embedHash`, `renderSource` (render와 check가 공유) |
| `docs/tutorials/_tools/lib/days.mjs` | 경로 상수, `loadDays`, `folderName`, `pad3` |
| `docs/tutorials/_tools/lib/check.mjs` | `checkDay`, `checkRoadmap` (문제 목록 반환, 부작용 없음) |
| `docs/tutorials/_tools/render.mjs` | CLI: `.d2` 목록 → 해시 비교 → 렌더 |
| `docs/tutorials/_tools/check.mjs` | CLI: 모든 일차 + 로드맵 검사, 실패 시 exit 1 |
| `docs/tutorials/_tools/scaffold.mjs` | CLI: `dayNNN-slug/` 폴더, README 골격, `diagrams/` 생성 |
| `docs/tutorials/_tools/roadmap.mjs` | CLI: 템플릿 + days.json + 진도 → `docs/tutorials/README.md` |
| `docs/tutorials/_tools/roadmap.template.md` | 로드맵 고정 본문. `<!-- DAYS -->` 자리에 표 삽입 |
| `docs/tutorials/_tools/days.json` | 133일 일정 데이터 |
| `docs/tutorials/_tools/test/*.test.mjs` | `node --test` 테스트 |
| `docs/tutorials/README.md` | 생성물(로드맵) |
| `docs/tutorials/day001-xai-finance-agent/README.md`, `diagrams/*` | Day 1 |

---

### Task 1: 도구 패키지, 테마, D2 라이브러리

**Files:**
- Create: `docs/tutorials/_tools/package.json`
- Create: `docs/tutorials/_tools/theme.d2`
- Create: `docs/tutorials/_tools/lib/d2.mjs`
- Test: `docs/tutorials/_tools/test/d2.test.mjs`

**Interfaces:**
- Produces: `inlineImports(filePath: string): string` — `...@경로` 줄을 재귀 치환한 소스. 순환이면 throw.
- Produces: `sourceHash(src: string): string` — SHA-256 hex.
- Produces: `readSvgHash(svgText: string): string | null`, `embedHash(svg: string, hash: string): string`.
- Produces: `renderSource(src: string): Promise<string>` — SVG 문자열.

- [ ] **Step 1: 패키지 파일과 테마 작성**

`docs/tutorials/_tools/package.json`:

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
  "devDependencies": {
    "@terrastruct/d2": "^0.1.33"
  }
}
```

`docs/tutorials/_tools/theme.d2`:

```d2
direction: right
classes: {
  person: { shape: person; style.fill: "#FEF3C7"; style.stroke: "#B45309" }
  person-new: { shape: person; style.fill: "#FEF3C7"; style.stroke: "#F97316"; style.stroke-width: 4 }
  person-todo: { shape: person; style.fill: "#FEF3C7"; style.stroke: "#B45309"; style.opacity: 0.35; style.stroke-dash: 3 }
  ours: { style.fill: "#DBEAFE"; style.stroke: "#1D4ED8"; style.font-color: "#1E3A8A" }
  ours-new: { style.fill: "#DBEAFE"; style.stroke: "#F97316"; style.stroke-width: 4; style.font-color: "#1E3A8A" }
  ours-todo: { style.fill: "#DBEAFE"; style.stroke: "#1D4ED8"; style.font-color: "#1E3A8A"; style.opacity: 0.35; style.stroke-dash: 3 }
  ext: { shape: cloud; style.fill: "#F3F4F6"; style.stroke: "#6B7280" }
  ext-new: { shape: cloud; style.fill: "#F3F4F6"; style.stroke: "#F97316"; style.stroke-width: 4 }
  ext-todo: { shape: cloud; style.fill: "#F3F4F6"; style.stroke: "#6B7280"; style.opacity: 0.35; style.stroke-dash: 3 }
  store: { shape: cylinder; style.fill: "#DCFCE7"; style.stroke: "#15803D" }
  store-new: { shape: cylinder; style.fill: "#DCFCE7"; style.stroke: "#F97316"; style.stroke-width: 4 }
  store-todo: { shape: cylinder; style.fill: "#DCFCE7"; style.stroke: "#15803D"; style.opacity: 0.35; style.stroke-dash: 3 }
  file: { shape: page; style.fill: "#FFFFFF"; style.stroke: "#6B7280" }
  file-new: { shape: page; style.fill: "#FFFFFF"; style.stroke: "#F97316"; style.stroke-width: 4 }
  file-todo: { shape: page; style.fill: "#FFFFFF"; style.stroke: "#6B7280"; style.opacity: 0.35; style.stroke-dash: 3 }
}
```

Run: `cd docs/tutorials/_tools && npm install`
Expected: `node_modules/@terrastruct/d2` 생성, `package-lock.json` 생성. (설치가 수 분 걸릴 수 있음.)

- [ ] **Step 2: 실패하는 테스트 작성**

`docs/tutorials/_tools/test/d2.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { inlineImports, sourceHash, readSvgHash, embedHash, renderSource } from "../lib/d2.mjs";

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "tut-d2-"));
  mkdirSync(join(root, "_tools"));
  mkdirSync(join(root, "day001-x", "diagrams"), { recursive: true });
  writeFileSync(join(root, "_tools", "theme.d2"), "direction: right\nclasses: {\n  ours: { style.fill: \"#DBEAFE\" }\n  ours-new: { style.fill: \"#DBEAFE\"; style.stroke: \"#F97316\"; style.stroke-width: 4 }\n}\n");
  writeFileSync(join(root, "day001-x", "diagrams", "overview.d2"), "...@../../_tools/theme\na: 앱 { class: ours }\nb: 외부\na -> b: 요청\n");
  writeFileSync(join(root, "day001-x", "diagrams", "step1.d2"), "...@overview\na.class: ours-new\n");
  return root;
}

test("inlineImports replaces import lines recursively", () => {
  const root = fixture();
  const out = inlineImports(join(root, "day001-x", "diagrams", "step1.d2"));
  assert.ok(out.includes("classes: {"), "theme content inlined");
  assert.ok(out.includes("a: 앱 { class: ours }"), "overview content inlined");
  assert.ok(out.includes("a.class: ours-new"), "own content kept");
  assert.ok(!out.includes("...@"), "no import lines remain");
});

test("inlineImports throws on cycles", () => {
  const root = mkdtempSync(join(tmpdir(), "tut-cycle-"));
  writeFileSync(join(root, "a.d2"), "...@b\n");
  writeFileSync(join(root, "b.d2"), "...@a\n");
  assert.throws(() => inlineImports(join(root, "a.d2")), /import cycle/);
});

test("sourceHash is stable and hex", () => {
  assert.equal(sourceHash("x"), sourceHash("x"));
  assert.match(sourceHash("x"), /^[0-9a-f]{64}$/);
  assert.notEqual(sourceHash("x"), sourceHash("y"));
});

test("embedHash/readSvgHash round-trip", () => {
  const svg = "<svg><g/></svg>";
  const h = sourceHash("src");
  const out = embedHash(svg, h);
  assert.ok(out.endsWith("</svg>"));
  assert.equal(readSvgHash(out), h);
  assert.equal(readSvgHash(svg), null);
});

test("renderSource applies a single-class override and renders a sequence diagram", async () => {
  const root = fixture();
  const svg = await renderSource(inlineImports(join(root, "day001-x", "diagrams", "step1.d2")));
  assert.ok(svg.includes("<svg"), "svg produced");
  assert.ok(!svg.startsWith("<?xml"), "noXMLTag honoured");
  assert.ok(svg.toLowerCase().includes("f97316"), "step override (ours-new) reached the svg");
  const seq = await renderSource("shape: sequence_diagram\nu: 사용자\ns: 서버\nu -> s: 질문\ns -> u: 답변\n");
  assert.ok(seq.includes("<svg"));
});
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: FAIL — `Cannot find module '../lib/d2.mjs'`

- [ ] **Step 4: 라이브러리 구현**

`docs/tutorials/_tools/lib/d2.mjs`:

```js
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { D2 } from "@terrastruct/d2";

const IMPORT_RE = /^\.\.\.@(\S+)\s*$/;
const HASH_RE = /<!-- d2-source-sha256: ([0-9a-f]{64}) -->/;

export const RENDER_OPTIONS = { layout: "elk", sketch: false, pad: 20, noXMLTag: true };

/** `...@path` 줄을 해당 파일 내용으로 재귀 치환한다. 경로는 import하는 파일 기준 상대 경로, `.d2`는 생략 가능. */
export function inlineImports(filePath, seen = new Set()) {
  const abs = resolve(filePath);
  if (seen.has(abs)) throw new Error(`import cycle: ${abs}`);
  const next = new Set(seen).add(abs);
  return readFileSync(abs, "utf8")
    .split(/\r?\n/)
    .map((line) => {
      const m = line.match(IMPORT_RE);
      if (!m) return line;
      const target = resolve(dirname(abs), m[1].endsWith(".d2") ? m[1] : `${m[1]}.d2`);
      return inlineImports(target, next);
    })
    .join("\n");
}

export function sourceHash(src) {
  return createHash("sha256").update(src, "utf8").digest("hex");
}

export function readSvgHash(svgText) {
  const m = svgText.match(HASH_RE);
  return m ? m[1] : null;
}

export function embedHash(svg, hash) {
  const i = svg.lastIndexOf("</svg>");
  if (i < 0) throw new Error("renderer output has no </svg>");
  return `${svg.slice(0, i)}<!-- d2-source-sha256: ${hash} -->${svg.slice(i)}`;
}

let d2;
export async function renderSource(src) {
  d2 ??= new D2();
  const compiled = await d2.compile(src, RENDER_OPTIONS);
  return d2.render(compiled.diagram, compiled.renderOptions);
}
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: `# pass 5`, `# fail 0`, 그리고 프로세스가 스스로 끝난다(`--test-force-exit` 덕분. 이 플래그 없이 돌리면 D2의 ELK 워커 때문에 러너가 끝나지 않는다).

- [ ] **Step 6: 커밋**

```bash
git add docs/tutorials/_tools/package.json docs/tutorials/_tools/package-lock.json docs/tutorials/_tools/theme.d2 docs/tutorials/_tools/lib/d2.mjs docs/tutorials/_tools/test/d2.test.mjs
git commit -m "docs(tutorials): add D2 tooling package, theme and render library"
```

---

### Task 2: days.json, days 라이브러리, scaffold.mjs

**Files:**
- Create: `docs/tutorials/_tools/days.json`
- Create: `docs/tutorials/_tools/lib/days.mjs`
- Create: `docs/tutorials/_tools/scaffold.mjs`
- Test: `docs/tutorials/_tools/test/days.test.mjs`

**Interfaces:**
- Produces: `days.json` 항목 `{ day: number, vol: number, volLabel: string, title: string, path: string, slug: string }` 133개, `day` 오름차순.
- Produces (`lib/days.mjs`): `TOOLS_DIR`, `TUTORIALS_DIR`, `REPO_ROOT`, `loadDays(file?): Day[]`, `pad3(n): string`, `folderName(day): string` (`day001-xai-finance-agent`), `PLACEHOLDER = "(작성 필요)"` (골격의 미작성 표시. `scaffold.mjs`가 쓰고 `roadmap.mjs`(Task 4)와 `check.mjs`(Task 5)가 이 문자열을 찾는다).
- Produces (`scaffold.mjs`): `readmeSkeleton(day, nextDay | undefined): string`, `scaffoldDay(dayNumber, { days?, root? }): string` (만든 폴더 경로). CLI `node scaffold.mjs 001`.

- [ ] **Step 1: 스펙 부록 A에서 days.json 생성**

Run (리포 루트에서):

```bash
node -e '
const fs = require("fs");
const spec = fs.readFileSync("docs/superpowers/specs/2026-09-11-tutorial-series-design.md", "utf8");
const days = []; let vol = 0, volLabel = "";
for (const line of spec.split(/\r?\n/)) {
  const h = line.match(/^### 볼륨 (\d+)\. (.+?) \(Day /); if (h) { vol = +h[1]; volLabel = h[2]; continue; }
  const r = line.match(/^\| (\d{3}) \| (.+?) \| `([^`]+)` \| `day\d{3}-([^`]+)` \| (\d+) \|$/);
  if (r) days.push({ day: +r[1], vol, volLabel, title: r[2], path: r[3], slug: r[4] });
}
if (days.length !== 133) throw new Error("expected 133 rows, got " + days.length);
fs.writeFileSync("docs/tutorials/_tools/days.json", JSON.stringify(days, null, 2) + "\n");
console.log("days.json:", days.length);
'
```

Expected: `days.json: 133`

- [ ] **Step 2: 실패하는 테스트 작성**

`docs/tutorials/_tools/test/days.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadDays, folderName, pad3, REPO_ROOT } from "../lib/days.mjs";
import { readmeSkeleton, scaffoldDay } from "../scaffold.mjs";

test("days.json has 133 consecutive days with unique folders and existing app paths", () => {
  const days = loadDays();
  assert.equal(days.length, 133);
  days.forEach((d, i) => assert.equal(d.day, i + 1));
  assert.equal(new Set(days.map(folderName)).size, 133);
  for (const d of days) assert.ok(existsSync(join(REPO_ROOT, d.path)), `missing app dir: ${d.path}`);
  assert.equal(folderName(days[0]), "day001-xai-finance-agent");
  assert.equal(pad3(7), "007");
});

test("readmeSkeleton contains the nine H2 headings in order and links the next day", () => {
  const days = loadDays();
  const text = readmeSkeleton(days[0], days[1]);
  const heads = ["## 오늘 만들 것", "## 사전 준비", "## 아키텍처 한눈에 보기", "## 단계별 진행", "## 요청 한 건이 흐르는 과정", "## 실행 체크리스트", "## 문제 해결", "## 더 해보기", "## 다음 날 예고"];
  let pos = -1;
  for (const h of heads) { const i = text.indexOf(h); assert.ok(i > pos, `heading order: ${h}`); pos = i; }
  assert.ok(text.includes(`(../${folderName(days[1])}/README.md)`));
  assert.ok(text.includes("(작성 필요)"));
  assert.ok(readmeSkeleton(days[132], undefined).includes("시리즈의 마지막"));
});

test("scaffoldDay creates folder, diagrams dir and README once", () => {
  const root = mkdtempSync(join(tmpdir(), "tut-scaffold-"));
  const dir = scaffoldDay(1, { root });
  assert.equal(dir, join(root, "day001-xai-finance-agent"));
  assert.ok(existsSync(join(dir, "diagrams")));
  const readme = readFileSync(join(dir, "README.md"), "utf8");
  assert.ok(readme.startsWith("# Day 001 · "));
  assert.throws(() => scaffoldDay(1, { root }), /already exists/);
});
```

- [ ] **Step 3: 실패 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: FAIL — `Cannot find module '../lib/days.mjs'`

- [ ] **Step 4: 구현**

`docs/tutorials/_tools/lib/days.mjs`:

```js
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const TOOLS_DIR = fileURLToPath(new URL("..", import.meta.url));
export const TUTORIALS_DIR = resolve(TOOLS_DIR, "..");
export const REPO_ROOT = resolve(TUTORIALS_DIR, "..", "..");

export function loadDays(file = resolve(TOOLS_DIR, "days.json")) {
  return JSON.parse(readFileSync(file, "utf8"));
}

export const pad3 = (n) => String(n).padStart(3, "0");

export const PLACEHOLDER = "(작성 필요)";

export function folderName(day) {
  return `day${pad3(day.day)}-${day.slug}`;
}
```

`docs/tutorials/_tools/scaffold.mjs`:

```js
#!/usr/bin/env node
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { loadDays, folderName, pad3, PLACEHOLDER, TUTORIALS_DIR } from "./lib/days.mjs";

export function readmeSkeleton(day, nextDay) {
  const next = nextDay
    ? `[Day ${pad3(nextDay.day)} · ${nextDay.title}](../${folderName(nextDay)}/README.md) — ${PLACEHOLDER}`
    : "여기가 시리즈의 마지막 날입니다.";
  return `# Day ${pad3(day.day)} · ${day.title}

> 볼륨 ${day.vol} ${day.volLabel} · 난이도 ★☆☆ · 예상 소요 60분 · API 비용 대략 ${PLACEHOLDER} · 원본 앱: \`${day.path}\`

## 오늘 만들 것

${PLACEHOLDER}

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| ${PLACEHOLDER} | | |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| ${PLACEHOLDER} | | |

## 단계별 진행

### Step 1. ${PLACEHOLDER}

**목적.** ${PLACEHOLDER}

**할 일.** ${PLACEHOLDER}

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** ${PLACEHOLDER}

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

${PLACEHOLDER}

## 실행 체크리스트

- [ ] ${PLACEHOLDER}

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| ${PLACEHOLDER} | | |

## 더 해보기

- ${PLACEHOLDER}

## 다음 날 예고

${next}
`;
}

export function scaffoldDay(dayNumber, { days = loadDays(), root = TUTORIALS_DIR } = {}) {
  const day = days.find((d) => d.day === dayNumber);
  if (!day) throw new Error(`no such day: ${dayNumber}`);
  const dir = join(root, folderName(day));
  if (existsSync(dir)) throw new Error(`already exists: ${dir}`);
  mkdirSync(join(dir, "diagrams"), { recursive: true });
  writeFileSync(join(dir, "README.md"), readmeSkeleton(day, days.find((d) => d.day === dayNumber + 1)));
  return dir;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const n = Number.parseInt(process.argv[2], 10);
  if (!n) { console.error("usage: node scaffold.mjs <day number>"); process.exit(2); }
  console.log(scaffoldDay(n));
}
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: `# fail 0`.

- [ ] **Step 6: 커밋**

```bash
git add docs/tutorials/_tools/days.json docs/tutorials/_tools/lib/days.mjs docs/tutorials/_tools/scaffold.mjs docs/tutorials/_tools/test/days.test.mjs
git commit -m "docs(tutorials): add days.json schedule data and scaffold.mjs"
```

---

### Task 3: render.mjs CLI

**Files:**
- Create: `docs/tutorials/_tools/render.mjs`
- Test: `docs/tutorials/_tools/test/render.test.mjs`

**Interfaces:**
- Consumes: Task 1의 `inlineImports`, `sourceHash`, `readSvgHash`, `embedHash`, `renderSource`; Task 2의 `TUTORIALS_DIR`.
- Produces: `listD2Files(root: string, onlyDay?: string): string[]`, `renderFile(d2Path: string, { force?: boolean }): Promise<"rendered" | "skipped">`.
- CLI: `node render.mjs [dayNNN] [--force]`.

- [ ] **Step 1: 실패하는 테스트 작성**

`docs/tutorials/_tools/test/render.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, relative } from "node:path";
import { listD2Files, renderFile } from "../render.mjs";
import { readSvgHash } from "../lib/d2.mjs";

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "tut-render-"));
  mkdirSync(join(root, "_tools"));
  mkdirSync(join(root, "day001-x", "diagrams"), { recursive: true });
  mkdirSync(join(root, "day002-y", "diagrams"), { recursive: true });
  mkdirSync(join(root, "not-a-day", "diagrams"), { recursive: true });
  writeFileSync(join(root, "_tools", "theme.d2"), "direction: right\nclasses: { ours: { style.fill: \"#DBEAFE\" } }\n");
  writeFileSync(join(root, "day001-x", "diagrams", "overview.d2"), "...@../../_tools/theme\na: 앱 { class: ours }\nb: 외부\na -> b\n");
  writeFileSync(join(root, "day002-y", "diagrams", "overview.d2"), "x -> y\n");
  writeFileSync(join(root, "not-a-day", "diagrams", "z.d2"), "x -> y\n");
  return root;
}

test("listD2Files finds only dayNNN-* diagrams, optionally one day", () => {
  const root = fixture();
  assert.deepEqual(listD2Files(root).map((p) => relative(root, p)).sort(), [
    join("day001-x", "diagrams", "overview.d2"),
    join("day002-y", "diagrams", "overview.d2"),
  ]);
  assert.equal(listD2Files(root, "day002").length, 1);
});

test("renderFile writes svg with hash, then skips, then re-renders when theme changes", async () => {
  const root = fixture();
  const d2 = join(root, "day001-x", "diagrams", "overview.d2");
  const svg = join(root, "day001-x", "diagrams", "overview.svg");
  assert.equal(await renderFile(d2), "rendered");
  assert.ok(existsSync(svg));
  const first = readSvgHash(readFileSync(svg, "utf8"));
  assert.match(first, /^[0-9a-f]{64}$/);
  assert.equal(await renderFile(d2), "skipped");
  writeFileSync(join(root, "_tools", "theme.d2"), "direction: down\nclasses: { ours: { style.fill: \"#FFFFFF\" } }\n");
  assert.equal(await renderFile(d2), "rendered");
  assert.notEqual(readSvgHash(readFileSync(svg, "utf8")), first);
  assert.equal(await renderFile(d2, { force: true }), "rendered");
});
```

- [ ] **Step 2: 실패 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: FAIL — `Cannot find module '../render.mjs'`

- [ ] **Step 3: 구현**

`docs/tutorials/_tools/render.mjs`:

```js
#!/usr/bin/env node
import { readdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { inlineImports, sourceHash, readSvgHash, embedHash, renderSource } from "./lib/d2.mjs";
import { TUTORIALS_DIR } from "./lib/days.mjs";

export function listD2Files(root, onlyDay) {
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory() || !/^day\d{3}-/.test(entry.name)) continue;
    if (onlyDay && !entry.name.startsWith(onlyDay)) continue;
    const dir = join(root, entry.name, "diagrams");
    if (!existsSync(dir)) continue;
    for (const f of readdirSync(dir)) if (f.endsWith(".d2")) files.push(join(dir, f));
  }
  return files.sort();
}

export async function renderFile(d2Path, { force = false } = {}) {
  const src = inlineImports(d2Path);
  const hash = sourceHash(src);
  const svgPath = d2Path.replace(/\.d2$/, ".svg");
  if (!force && existsSync(svgPath) && readSvgHash(readFileSync(svgPath, "utf8")) === hash) return "skipped";
  const svg = await renderSource(src);
  writeFileSync(svgPath, embedHash(svg, hash));
  return "rendered";
}

async function main(argv) {
  const force = argv.includes("--force");
  const onlyDay = argv.find((a) => /^day\d{3}/.test(a));
  const counts = { rendered: 0, skipped: 0, failed: 0 };
  for (const file of listD2Files(TUTORIALS_DIR, onlyDay)) {
    try {
      const result = await renderFile(file, { force });
      counts[result]++;
      console.log(`${result.padEnd(8)} ${file}`);
    } catch (err) {
      counts.failed++;
      console.error(`FAILED   ${file}\n  ${err.message}`);
    }
  }
  console.log(`rendered ${counts.rendered}, skipped ${counts.skipped}, failed ${counts.failed}`);
  process.exit(counts.failed ? 1 : 0); // D2의 ELK 워커가 이벤트 루프를 붙잡으므로 명시적으로 끝낸다
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main(process.argv.slice(2));
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: `# fail 0`.

- [ ] **Step 5: 커밋**

```bash
git add docs/tutorials/_tools/render.mjs docs/tutorials/_tools/test/render.test.mjs
git commit -m "docs(tutorials): add render.mjs (hash-based d2 -> svg rendering)"
```

---

### Task 4: 로드맵 템플릿과 roadmap.mjs

**Files:**
- Create: `docs/tutorials/_tools/roadmap.template.md`
- Create: `docs/tutorials/_tools/roadmap.mjs`
- Create (생성물): `docs/tutorials/README.md`
- Test: `docs/tutorials/_tools/test/roadmap.test.mjs`

**Interfaces:**
- Consumes: `loadDays`, `folderName`, `pad3`, `PLACEHOLDER`, `TUTORIALS_DIR`, `TOOLS_DIR` (Task 2의 `lib/days.mjs`).
- Produces: `isDayDone(day, root): boolean` (README가 있고 `(작성 필요)`가 없음), `renderRoadmap(days, root, template): string`, CLI `node roadmap.mjs` → `docs/tutorials/README.md` 덮어쓰기.
- 표 규칙: 폴더가 있는 일차만 `[Day NNN](폴더/README.md)` 링크, 없으면 `Day NNN` 텍스트. 완료 열은 `✅`/`⬜`. 원본 앱은 `[경로](../../경로/)` 링크.

- [ ] **Step 1: 템플릿 작성**

`docs/tutorials/_tools/roadmap.template.md`:

```markdown
# awesome-llm-apps 133일 튜토리얼

이 리포에 있는 앱을 하루에 하나씩, 처음부터 끝까지 따라 만드는 시리즈입니다. 하루 분량은 60~90분이고, 매 일차는 완성 아키텍처와 각 단계의 시스템 구성을 D2 다이어그램으로 보여 줍니다. 순서는 학습 난이도 순이며 볼륨 안에서는 작은 앱부터 갑니다.

## 이렇게 진행하세요

1. 아래 표에서 오늘 일차를 열고 "오늘 만들 것"과 완성 아키텍처 그림을 먼저 봅니다.
2. "사전 준비"의 키와 도구를 마련합니다. 공통 준비는 바로 아래 절을 한 번만 하면 됩니다.
3. "단계별 진행"을 순서대로 따라가며 각 Step의 **확인** 명령을 꼭 실행합니다. 그림에서 주황 테두리가 이번 Step에 새로 붙는 부분이고, 흐린 부분은 아직 만들지 않은 부분입니다.
4. "실행 체크리스트"를 모두 채우면 그날은 끝입니다. "더 해보기"는 선택입니다.

## 공통 사전 준비 (한 번만)

| 항목 | 내용 |
|---|---|
| Python | 3.11 이상 3.13 이하 (`pyproject.toml`의 `requires-python`) |
| uv | 설치: macOS/Linux `curl -LsSf https://astral.sh/uv/install.sh \| sh`, Windows `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`, 또는 `pip install uv` |
| 리포 | `git clone https://github.com/Zihun/awesome-llm-apps.git && cd awesome-llm-apps` |
| API 키 | 일차마다 필요한 키가 다릅니다. 키는 셸 환경변수나 앱 폴더의 `.env`에 두고, 절대 커밋하지 않습니다 |

각 일차는 **앱 폴더 안에 독립 가상환경**을 만드는 방식을 기본으로 씁니다.

```bash
cd <원본 앱 폴더>
uv venv
uv pip install -r requirements.txt
uv run python <엔트리 파일>
```

리포 루트의 공용 환경(`uv sync --all-extras`)을 쓰는 방법은 [UV_MIGRATION_GUIDE.md](../../UV_MIGRATION_GUIDE.md)에 있습니다. 앱마다 의존성 버전이 달라 충돌할 수 있으므로, 튜토리얼의 확인 명령은 모두 독립 가상환경 기준으로 검증했습니다.

## 다이어그램 읽는 법

| 표현 | 뜻 |
|---|---|
| 사람 모양 | 사용자 |
| 파란 사각형 | 이 리포의 코드 (앱, 에이전트, 도구 함수) |
| 회색 구름 | 외부 API, LLM 제공자 |
| 초록 원통 | DB, 벡터 저장소, 캐시 |
| 문서 모양 | 파일, 설정 |
| 주황 굵은 테두리 | 이번 Step에서 새로 추가된 부분 |
| 흐리고 점선 | 아직 만들지 않은 부분 |

다이어그램 소스는 각 일차의 `diagrams/*.d2`에 있고, 렌더와 검사는 `docs/tutorials/_tools`에서 `npm install && npm run render && npm run check`로 합니다.

## 다루지 않는 항목

README에 실려 있지만 코드가 외부 리포에 있는 두 항목은 링크만 남깁니다: [Openwork](https://github.com/accomplish-ai/coworker), [OpenSource Voice Dictation Agent](https://github.com/akshayaggarwal/wispr-flow-clone).

## 133일 일정

<!-- DAYS -->
```

- [ ] **Step 2: 실패하는 테스트 작성**

`docs/tutorials/_tools/test/roadmap.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadDays, folderName } from "../lib/days.mjs";
import { isDayDone, renderRoadmap } from "../roadmap.mjs";

test("renderRoadmap lists 133 rows, links only existing days, marks done days", () => {
  const days = loadDays();
  const root = mkdtempSync(join(tmpdir(), "tut-roadmap-"));
  mkdirSync(join(root, folderName(days[0])), { recursive: true });
  writeFileSync(join(root, folderName(days[0]), "README.md"), "# Day 001\n완성");
  mkdirSync(join(root, folderName(days[1])), { recursive: true });
  writeFileSync(join(root, folderName(days[1]), "README.md"), "# Day 002\n(작성 필요)");
  const out = renderRoadmap(days, root, "HEAD\n<!-- DAYS -->\n");
  const rows = out.split("\n").filter((l) => /^\| (✅|⬜) \|/.test(l));
  assert.equal(rows.length, 133);
  assert.ok(rows[0].startsWith(`| ✅ | [Day 001](${folderName(days[0])}/README.md)`));
  assert.ok(rows[1].startsWith(`| ⬜ | [Day 002](${folderName(days[1])}/README.md)`));
  assert.ok(rows[2].startsWith("| ⬜ | Day 003 |"));
  assert.ok(out.includes("진도: 1 / 133"));
  assert.ok(out.includes("### 볼륨 1."));
  assert.ok(out.startsWith("HEAD\n"));
  assert.equal(isDayDone(days[0], root), true);
  assert.equal(isDayDone(days[1], root), false);
  assert.equal(isDayDone(days[2], root), false);
});
```

- [ ] **Step 3: 실패 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: FAIL — `Cannot find module '../roadmap.mjs'`

- [ ] **Step 4: 구현**

`docs/tutorials/_tools/roadmap.mjs`:

```js
#!/usr/bin/env node
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { loadDays, folderName, pad3, PLACEHOLDER, TUTORIALS_DIR, TOOLS_DIR } from "./lib/days.mjs";

export function isDayDone(day, root) {
  const readme = join(root, folderName(day), "README.md");
  return existsSync(readme) && !readFileSync(readme, "utf8").includes(PLACEHOLDER);
}

export function renderRoadmap(days, root, template) {
  const done = days.filter((d) => isDayDone(d, root)).length;
  let out = `진도: ${done} / ${days.length}일 완료\n`;
  let vol = 0;
  for (const d of days) {
    if (d.vol !== vol) {
      vol = d.vol;
      const inVol = days.filter((x) => x.vol === vol);
      out += `\n### 볼륨 ${vol}. ${d.volLabel} (Day ${inVol[0].day}–${inVol[inVol.length - 1].day}, ${inVol.length}일)\n\n`;
      out += "| 완료 | 일차 | 앱 | 원본 앱 |\n|---|---|---|---|\n";
    }
    const folder = folderName(d);
    const exists = existsSync(join(root, folder, "README.md"));
    const dayCell = exists ? `[Day ${pad3(d.day)}](${folder}/README.md)` : `Day ${pad3(d.day)}`;
    out += `| ${isDayDone(d, root) ? "✅" : "⬜"} | ${dayCell} | ${d.title} | [${d.path}](../../${d.path}/) |\n`;
  }
  return template.replace("<!-- DAYS -->", out);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const template = readFileSync(join(TOOLS_DIR, "roadmap.template.md"), "utf8");
  const target = join(TUTORIALS_DIR, "README.md");
  writeFileSync(target, renderRoadmap(loadDays(), TUTORIALS_DIR, template));
  console.log(`wrote ${target}`);
}
```

- [ ] **Step 5: 테스트 통과 확인 후 로드맵 생성**

Run: `cd docs/tutorials/_tools && npm test && npm run roadmap`
Expected: `# fail 0`, `wrote …/docs/tutorials/README.md`. `docs/tutorials/README.md`를 열어 133행, 15개 볼륨 제목, `진도: 0 / 133일 완료`를 확인한다.

- [ ] **Step 6: 커밋**

```bash
git add docs/tutorials/_tools/roadmap.template.md docs/tutorials/_tools/roadmap.mjs docs/tutorials/_tools/test/roadmap.test.mjs docs/tutorials/README.md
git commit -m "docs(tutorials): add roadmap generator and 133-day roadmap"
```

---

### Task 5: check.mjs

**Files:**
- Create: `docs/tutorials/_tools/lib/check.mjs`
- Create: `docs/tutorials/_tools/check.mjs`
- Test: `docs/tutorials/_tools/test/check.test.mjs`

**Interfaces:**
- Consumes: `inlineImports`, `sourceHash`, `readSvgHash` (Task 1); `loadDays`, `folderName`, `PLACEHOLDER`, `REPO_ROOT`, `TUTORIALS_DIR` (Task 2).
- Produces: `REQUIRED_H2: string[]`, `checkDay(dayDir, { repoRoot, allowNoNextDay }): string[]` (문제 메시지 배열, 비어 있으면 통과), `checkRoadmap(readmePath, days, root): string[]`. CLI `node check.mjs [dayNNN]`.
- 검사 항목: (1) H2 9개 순서, (2) 상대 링크·이미지 존재, (3) `.d2`↔`.svg` 짝과 해시 일치, (4) `` `경로:시작-끝` `` 참조 유효, (5) mermaid 펜스 없음, (6) 로드맵 133행과 링크 대상 존재, (7) `(작성 필요)` 없음.

- [ ] **Step 1: 실패하는 테스트 작성**

`docs/tutorials/_tools/test/check.test.mjs`:

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { checkDay, checkRoadmap, REQUIRED_H2 } from "../lib/check.mjs";
import { inlineImports, sourceHash, embedHash } from "../lib/d2.mjs";
import { loadDays, folderName } from "../lib/days.mjs";

const GOOD_README = (extra = "") => `# Day 001 · 테스트

> 볼륨 1 · 난이도 ★☆☆

${REQUIRED_H2.map((h) => `${h}\n\n본문 \`app/main.py:1-2\`\n`).join("\n")}
![그림](diagrams/overview.svg)
${extra}
`;

function fixture({ readme = GOOD_README(), svgHash } = {}) {
  const repo = mkdtempSync(join(tmpdir(), "tut-check-"));
  mkdirSync(join(repo, "app"));
  writeFileSync(join(repo, "app", "main.py"), "print(1)\nprint(2)\n");
  const tutorials = join(repo, "docs", "tutorials");
  mkdirSync(join(tutorials, "_tools"), { recursive: true });
  writeFileSync(join(tutorials, "_tools", "theme.d2"), "direction: right\n");
  const dayDir = join(tutorials, "day001-x");
  mkdirSync(join(dayDir, "diagrams"), { recursive: true });
  writeFileSync(join(dayDir, "README.md"), readme);
  const d2 = join(dayDir, "diagrams", "overview.d2");
  writeFileSync(d2, "...@../../_tools/theme\na -> b\n");
  const hash = svgHash ?? sourceHash(inlineImports(d2));
  writeFileSync(join(dayDir, "diagrams", "overview.svg"), embedHash("<svg></svg>", hash));
  return { repo, tutorials, dayDir };
}

test("a well-formed day passes", () => {
  const { repo, dayDir } = fixture();
  assert.deepEqual(checkDay(dayDir, { repoRoot: repo }), []);
});

test("missing or misordered headings are reported", () => {
  const { repo, dayDir } = fixture({ readme: GOOD_README().replace("## 문제 해결", "## 트러블슈팅") });
  const problems = checkDay(dayDir, { repoRoot: repo });
  assert.ok(problems.some((p) => p.includes("문제 해결")), problems.join("\n"));
});

test("last day may omit 다음 날 예고", () => {
  const { repo, dayDir } = fixture({ readme: GOOD_README().replace(/## 다음 날 예고[\s\S]*?(?=\n!\[)/, "") });
  assert.ok(checkDay(dayDir, { repoRoot: repo }).some((p) => p.includes("다음 날 예고")));
  assert.deepEqual(checkDay(dayDir, { repoRoot: repo, allowNoNextDay: true }), []);
});

test("broken image link, stale svg, bad code ref, mermaid and placeholder are reported", () => {
  const { repo, dayDir } = fixture({
    readme: GOOD_README("![없음](diagrams/missing.svg)\n`app/main.py:1-99`\n```mermaid\nA-->B\n```\n(작성 필요)\n"),
    svgHash: "0".repeat(64),
  });
  const problems = checkDay(dayDir, { repoRoot: repo });
  for (const needle of ["missing.svg", "stale", "app/main.py:1-99", "mermaid", "(작성 필요)"]) {
    assert.ok(problems.some((p) => p.includes(needle)), `expected a problem mentioning ${needle}:\n${problems.join("\n")}`);
  }
});

test("checkRoadmap requires 133 rows and existing link targets", () => {
  const days = loadDays();
  const root = mkdtempSync(join(tmpdir(), "tut-roadmap-check-"));
  mkdirSync(join(root, folderName(days[0])), { recursive: true });
  writeFileSync(join(root, folderName(days[0]), "README.md"), "# ok");
  const rows = days.map((d, i) => `| ⬜ | ${i < 2 ? `[Day ${String(d.day).padStart(3, "0")}](${folderName(d)}/README.md)` : `Day ${String(d.day).padStart(3, "0")}`} | t | p |`).join("\n");
  writeFileSync(join(root, "README.md"), `# r\n${rows}\n`);
  const problems = checkRoadmap(join(root, "README.md"), days, root);
  assert.equal(problems.length, 1, problems.join("\n"));
  assert.ok(problems[0].includes(folderName(days[1])));
  writeFileSync(join(root, "README.md"), `# r\n${rows.split("\n").slice(0, 10).join("\n")}\n`);
  assert.ok(checkRoadmap(join(root, "README.md"), days, root).some((p) => p.includes("133")));
});
```

- [ ] **Step 2: 실패 확인**

Run: `cd docs/tutorials/_tools && npm test`
Expected: FAIL — `Cannot find module '../lib/check.mjs'`

- [ ] **Step 3: 구현**

`docs/tutorials/_tools/lib/check.mjs`:

```js
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { inlineImports, sourceHash, readSvgHash } from "./d2.mjs";
import { folderName, PLACEHOLDER } from "./days.mjs";

export const REQUIRED_H2 = [
  "## 오늘 만들 것",
  "## 사전 준비",
  "## 아키텍처 한눈에 보기",
  "## 단계별 진행",
  "## 요청 한 건이 흐르는 과정",
  "## 실행 체크리스트",
  "## 문제 해결",
  "## 더 해보기",
  "## 다음 날 예고",
];

const LINK_RE = /!?\[[^\]]*\]\(([^)\s]+)\)/g;
const CODE_REF_RE = /`([A-Za-z0-9_.\-]+(?:\/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?`/g;

function stripFences(md) {
  return md.replace(/```[\s\S]*?```/g, (block) => (block.startsWith("```mermaid") ? block : ""));
}

export function checkDay(dayDir, { repoRoot, allowNoNextDay = false } = {}) {
  const problems = [];
  const readmePath = join(dayDir, "README.md");
  if (!existsSync(readmePath)) return [`${readmePath}: README.md 없음`];
  const md = readFileSync(readmePath, "utf8");
  const rel = (p) => `${dayDir}: ${p}`;

  // (1) headings in order
  const h2s = md.split(/\r?\n/).filter((l) => l.startsWith("## ")).map((l) => l.trim());
  const required = allowNoNextDay ? REQUIRED_H2.slice(0, -1) : REQUIRED_H2;
  let cursor = 0;
  for (const h of required) {
    const i = h2s.indexOf(h, cursor);
    if (i < 0) problems.push(rel(`H2 제목이 없거나 순서가 틀림: ${h}`));
    else cursor = i + 1;
  }

  // (2) relative links and images exist
  for (const m of md.matchAll(LINK_RE)) {
    const target = m[1];
    if (/^(https?:|mailto:|#)/.test(target)) continue;
    const file = resolve(dayDir, target.split("#")[0]);
    if (!existsSync(file)) problems.push(rel(`링크 대상 없음: ${target}`));
  }

  // (3) d2/svg pairs and hash
  const diagrams = join(dayDir, "diagrams");
  if (existsSync(diagrams)) {
    for (const f of readdirSync(diagrams).filter((f) => f.endsWith(".d2"))) {
      const svg = join(diagrams, f.replace(/\.d2$/, ".svg"));
      if (!existsSync(svg)) { problems.push(rel(`svg 없음: diagrams/${f}`)); continue; }
      const expected = sourceHash(inlineImports(join(diagrams, f)));
      if (readSvgHash(readFileSync(svg, "utf8")) !== expected) problems.push(rel(`stale svg (다시 렌더 필요): diagrams/${f}`));
    }
  }

  // (4) code refs
  const prose = stripFences(md);
  for (const m of prose.matchAll(CODE_REF_RE)) {
    const [, path, start, end] = m;
    const file = resolve(repoRoot, path);
    if (!existsSync(file)) { problems.push(rel(`코드 위치의 파일 없음: ${path}:${start}${end ? `-${end}` : ""}`)); continue; }
    const text = readFileSync(file, "utf8");
    const lines = text === "" ? 0 : text.split(/\r?\n/).length - (text.endsWith("\n") ? 1 : 0);
    const last = Number(end ?? start);
    if (Number(start) < 1 || last > lines || Number(start) > last) problems.push(rel(`코드 위치의 줄 범위가 파일 밖: ${path}:${start}${end ? `-${end}` : ""} (파일은 ${lines}줄)`));
  }

  // (5) no mermaid
  if (/```mermaid/.test(md)) problems.push(rel("mermaid 코드 펜스 사용"));

  // (7) no placeholder
  if (md.includes(PLACEHOLDER)) problems.push(rel(`미작성 표시 남음: ${PLACEHOLDER}`));

  return problems;
}

export function checkRoadmap(readmePath, days, root) {
  const problems = [];
  const md = readFileSync(readmePath, "utf8");
  const rows = md.split(/\r?\n/).filter((l) => /^\| (✅|⬜) \|/.test(l));
  if (rows.length !== days.length) problems.push(`${readmePath}: 일차 행이 ${rows.length}개 (기대 ${days.length})`);
  for (const m of md.matchAll(/\[Day \d{3}\]\(([^)]+)\)/g)) {
    if (!existsSync(resolve(dirname(readmePath), m[1]))) problems.push(`${readmePath}: 링크 대상 없음: ${m[1]}`);
  }
  return problems;
}

export function listDayDirs(root) {
  return readdirSync(root, { withFileTypes: true })
    .filter((e) => e.isDirectory() && /^day\d{3}-/.test(e.name))
    .map((e) => join(root, e.name))
    .sort();
}

export function isLastDay(dayDir, days) {
  return dayDir.endsWith(folderName(days[days.length - 1]));
}
```

`docs/tutorials/_tools/check.mjs`:

```js
#!/usr/bin/env node
import { join } from "node:path";
import { checkDay, checkRoadmap, listDayDirs, isLastDay } from "./lib/check.mjs";
import { loadDays, REPO_ROOT, TUTORIALS_DIR } from "./lib/days.mjs";

const onlyDay = process.argv.slice(2).find((a) => /^day\d{3}/.test(a));
const days = loadDays();
const problems = [];
for (const dir of listDayDirs(TUTORIALS_DIR)) {
  if (onlyDay && !dir.includes(onlyDay)) continue;
  problems.push(...checkDay(dir, { repoRoot: REPO_ROOT, allowNoNextDay: isLastDay(dir, days) }));
}
if (!onlyDay) problems.push(...checkRoadmap(join(TUTORIALS_DIR, "README.md"), days, TUTORIALS_DIR));
for (const p of problems) console.error(p);
console.log(problems.length ? `check: ${problems.length}개 문제` : "check: 통과");
process.exitCode = problems.length ? 1 : 0;
```

- [ ] **Step 4: 테스트 통과 확인, 현재 트리 검사**

Run: `cd docs/tutorials/_tools && npm test && npm run check`
Expected: `# fail 0`. `npm run check`는 일차 폴더가 아직 없으므로 로드맵만 검사해 `check: 통과`.

- [ ] **Step 5: 커밋**

```bash
git add docs/tutorials/_tools/lib/check.mjs docs/tutorials/_tools/check.mjs docs/tutorials/_tools/test/check.test.mjs
git commit -m "docs(tutorials): add check.mjs (headings, links, svg hash, code refs, roadmap)"
```

---

### Task 6: Day 1 — xAI Finance Agent

**Files:**
- Create: `docs/tutorials/day001-xai-finance-agent/README.md`
- Create: `docs/tutorials/day001-xai-finance-agent/diagrams/{overview,step1,step2,step3,step4,step5,step6,sequence}.d2` 와 각 `.svg`
- Modify (생성): `docs/tutorials/README.md`
- Modify (검토 후 필요 시): `docs/superpowers/specs/2026-09-11-tutorial-series-design.md`
- 원본 앱(읽기만): `starter_ai_agents/xai_finance_agent/xai_finance_agent.py` (23줄), `README.md`, `requirements.txt`

**Interfaces:**
- Consumes: `npm run scaffold -- 1`, `npm run render -- day001`, `npm run check`, `npm run roadmap`.
- Produces: 이후 모든 일차의 기준이 되는 완성본. 여기서 정한 문체·깊이가 Task 7, 8의 기준이다.

**원본 앱 사실 (계획 작성 시점, 실행 시 재확인):**

| 항목 | 값 | 근거 |
|---|---|---|
| 엔트리 | `xai_finance_agent.py` | 파일 1개 |
| 모델 | `xAI(id="grok-4-1-fast")` | 11행 |
| 도구 | `DuckDuckGoTools()`, `YFinanceTools()` | 12행 |
| 지시문 | 표로 수치 표시, 텍스트는 불릿과 짧은 문단 | 13행 |
| 옵션 | `debug_mode=True`, `markdown=True` | 14~15행 |
| 서비스 | `AgentOS(agents=[agent])`, `agent_os.get_app()`, `agent_os.serve(app="xai_finance_agent:app", reload=True)` | 19~23행 |
| 의존성 | `agno>=2.2.10`, `duckduckgo-search`, `yfinance` | `requirements.txt` |
| 키 | `XAI_API_KEY` (https://console.x.ai/) | 앱 README |
| UI | AgentOS 컨트롤 플레인(https://os.agno.com)에서 로컬 AgentOS에 연결 | 앱 README 6번 |

- [ ] **Step 1: 폴더 골격 생성**

Run: `cd docs/tutorials/_tools && npm run scaffold -- 1`
Expected: `…/docs/tutorials/day001-xai-finance-agent` 출력, `README.md`와 `diagrams/` 생성.

- [ ] **Step 2: 키 없이 되는 확인을 실제로 실행해 사실을 채운다**

임시 가상환경에서 의존성을 설치하고 import·속성을 확인한다. 결과(버전, 실패한 import, 에러 문구)를 메모해 README의 "확인"과 "문제 해결"에 쓴다.

```bash
uv venv "$TEMP/day001-venv" --python 3.12
uv pip install --python "$TEMP/day001-venv" -r starter_ai_agents/xai_finance_agent/requirements.txt
"$TEMP/day001-venv/Scripts/python.exe" -m py_compile starter_ai_agents/xai_finance_agent/xai_finance_agent.py && echo "py_compile OK"
"$TEMP/day001-venv/Scripts/python.exe" -c "import agno, importlib.metadata as m; print('agno', m.version('agno'))"
"$TEMP/day001-venv/Scripts/python.exe" -c "from agno.models.xai import xAI; m = xAI(id='grok-4-1-fast'); print(m.id, m.provider)"
"$TEMP/day001-venv/Scripts/python.exe" -c "from agno.tools.yfinance import YFinanceTools; from agno.tools.duckduckgo import DuckDuckGoTools; print(sorted(YFinanceTools().functions)); print(sorted(DuckDuckGoTools().functions))"
"$TEMP/day001-venv/Scripts/python.exe" -c "from agno.os import AgentOS; print(AgentOS)"
```

Expected: 각 줄이 출력을 내거나, 실패하면 정확한 예외 문구를 얻는다. 특히 확인할 것 세 가지.
1. `duckduckgo-search` 패키지가 최신 agno에서 `ddgs`로 바뀌었는지(ImportError가 나면 `uv pip install ddgs`로 해결되는지 확인하고 "문제 해결"에 적는다).
2. `XAI_API_KEY`가 없을 때 `xAI(...)` 생성이 예외를 내는지, 아니면 실행 시점에 내는지.
3. AgentOS가 기본으로 여는 포트(코드에 없으면 agno 문서 기본값 7777)와 문서 URL(`/docs`). 서버를 키 없이 띄워 볼 수 있으면 `python xai_finance_agent.py`를 앱 폴더에서 10초간 실행해 로그의 URL을 그대로 옮긴다(키가 없어 기동이 실패하면 그 사실을 적는다).

확인이 끝나면 `$TEMP/day001-venv`를 삭제한다.

- [ ] **Step 3: 다이어그램 소스 작성**

`diagrams/overview.d2` (노드 10개):

```d2
...@../../_tools/theme
user: 사용자 { class: person }
key: XAI_API_KEY (환경변수) { class: file }
app: xai_finance_agent.py {
  os: AgentOS 서버 (FastAPI, :7777) { class: ours }
  agent: 금융 에이전트 (Agent) { class: ours }
  ddg: 웹 검색 도구 (DuckDuckGoTools) { class: ours }
  yf: 주가 도구 (YFinanceTools) { class: ours }
}
plane: AgentOS 컨트롤 플레인 (os.agno.com) { class: ext }
grok: xAI Grok (grok-4-1-fast) { class: ext }
ddgapi: DuckDuckGo { class: ext }
yahoo: Yahoo Finance { class: ext }

user -> plane: 브라우저에서 질문
plane -> app.os: HTTP 요청
app.os -> app.agent: run(message)
key -> app.agent: 인증
app.agent -> grok: 메시지 + 도구 스키마
app.agent -> app.ddg -> ddgapi: 검색어
app.agent -> app.yf -> yahoo: 티커 (예: AAPL)
```

`diagrams/step1.d2` — 환경 구성(가상환경, 의존성, 키):

```d2
...@overview
key.class: file-new
app.os.class: ours-todo
app.agent.class: ours-todo
app.ddg.class: ours-todo
app.yf.class: ours-todo
plane.class: ext-todo
grok.class: ext-todo
ddgapi.class: ext-todo
yahoo.class: ext-todo
```

`diagrams/step2.d2` — 모델 연결(`Agent` + `xAI`):

```d2
...@overview
app.agent.class: ours-new
grok.class: ext-new
app.os.class: ours-todo
app.ddg.class: ours-todo
app.yf.class: ours-todo
plane.class: ext-todo
ddgapi.class: ext-todo
yahoo.class: ext-todo
```

`diagrams/step3.d2` — 도구 연결:

```d2
...@overview
app.ddg.class: ours-new
app.yf.class: ours-new
ddgapi.class: ext-new
yahoo.class: ext-new
app.os.class: ours-todo
plane.class: ext-todo
```

`diagrams/step4.d2` — 지시문과 출력 형식(에이전트 강조):

```d2
...@overview
app.agent.class: ours-new
app.os.class: ours-todo
plane.class: ext-todo
```

`diagrams/step5.d2` — AgentOS로 서비스:

```d2
...@overview
app.os.class: ours-new
plane.class: ext-new
```

`diagrams/step6.d2` — 첫 질문 실행(완성 상태, 사용자 경로 강조):

```d2
...@overview
user.class: person-new
```

`diagrams/sequence.d2`:

```d2
...@../../_tools/theme
shape: sequence_diagram
user: 사용자 { class: person }
plane: 컨트롤 플레인 { class: ext }
os: AgentOS 서버 { class: ours }
agent: 금융 에이전트 { class: ours }
grok: Grok { class: ext }
yf: YFinanceTools { class: ours }

user -> plane: "AAPL 최근 주가와 뉴스 요약해줘"
plane -> os: POST /agents/{id}/runs
os -> agent: run(message)
agent -> grok: 메시지 + 도구 스키마 + 지시문
grok -> agent: tool_call get_current_stock_price("AAPL")
agent -> yf: get_current_stock_price("AAPL")
yf -> agent: 가격 데이터
agent -> grok: 도구 결과
grok -> agent: 최종 답변 (markdown 표)
agent -> os: 응답
os -> plane -> user: 화면에 표시
```

Step 2에서 확인한 실제 함수 이름(`YFinanceTools().functions`)으로 시퀀스의 `get_current_stock_price`를 바로잡는다.

- [ ] **Step 4: 렌더**

Run: `cd docs/tutorials/_tools && npm run render -- day001`
Expected: `rendered 8, skipped 0, failed 0`. 실패하면 오류의 줄 번호로 `.d2`를 고친다(라벨의 괄호·콜론은 D2에서 그대로 허용되지만, 라벨에 `:`나 `{`가 들어가면 따옴표로 감싼다).

- [ ] **Step 5: README 작성**

`docs/tutorials/day001-xai-finance-agent/README.md`를 골격 위에 다음 내용으로 채운다. `(작성 필요)`가 하나도 남지 않아야 한다.

- 헤더 인용문: `볼륨 1 🌱 Starter AI Agents · 난이도 ★☆☆ · 예상 소요 60분 · API 비용 대략 질문 10개에 수십 원 이하 (xAI 콘솔 요금표 기준, 대략치) · 원본 앱: \`starter_ai_agents/xai_finance_agent\``
- **오늘 만들 것**: 23줄짜리 파일 하나로 "LLM + 도구 + 서버" 세 요소를 갖춘 에이전트를 만든다는 점, 이 리포 앱 대부분이 쓰는 agno의 `Agent` 패턴을 여기서 처음 익힌다는 점, 완성 그림.
- **사전 준비** 표: xAI API 키(https://console.x.ai/, 용도: Grok 호출), uv(공통 준비 링크 `../README.md#공통-사전-준비-한-번만`), 인터넷(Yahoo Finance·DuckDuckGo 접속).
- **아키텍처 한눈에 보기** 표: 사용자/컨트롤 플레인(외부 UI, 코드 없음), AgentOS 서버 `starter_ai_agents/xai_finance_agent/xai_finance_agent.py:19-23`, 에이전트 `…:9-16`, 모델 `…:3` 및 `…:11`, 도구 `…:4-5` 및 `…:12`, 외부 API 3개. (이 계획의 `…`는 줄임 표기다. README에는 매번 `starter_ai_agents/xai_finance_agent/xai_finance_agent.py:9-16`처럼 전체 경로를 쓴다. `check.mjs`가 전체 경로만 인식한다.)
- **단계별 진행** 6개 Step. 각 Step은 목적·할 일·그림·확인 순서.
  - Step 1 환경 만들기: `cd starter_ai_agents/xai_finance_agent`, `uv venv`, `uv pip install -r requirements.txt`, 키 설정(`export XAI_API_KEY=...` / PowerShell `$env:XAI_API_KEY="..."`). 확인: `uv run python -c "import agno; print('ok')"` → `ok`. Task 6 Step 2에서 ddgs 문제가 확인됐으면 여기서 미리 안내.
  - Step 2 모델 연결: `xai_finance_agent.py:2-3`, `:9-11` 발췌. `Agent`가 무엇이고 `model`이 무엇인지 두 문장. 확인: `uv run python -c "from agno.models.xai import xAI; m = xAI(id='grok-4-1-fast'); print(m.id, m.provider)"` → Step 2에서 얻은 실제 출력.
  - Step 3 도구 연결: `:4-5`, `:12` 발췌. 도구가 "함수 스키마로 LLM에 전달되고 LLM이 호출을 요청하면 에이전트가 실행한다"는 설명. 확인: `uv run python -c "from agno.tools.yfinance import YFinanceTools; print(sorted(YFinanceTools().functions))"` → 실제 출력.
  - Step 4 지시문과 출력 형식: `:13-16` 발췌. `instructions`, `markdown`, `debug_mode`의 뜻. 확인: `uv run python -c "import xai_finance_agent as m; print(m.agent.name, len(m.agent.tools))"` → `xAI Finance Agent 2` (모듈 import 시 서버는 뜨지 않음: `if __name__ == "__main__"` 가드, `:22-23`).
  - Step 5 AgentOS로 서비스: `:6`, `:19-23` 발췌. `get_app()`이 FastAPI 앱을 돌려주고 `serve`가 uvicorn으로 띄운다는 것, `reload=True`는 앱 폴더에서 실행해야 하는 이유. 확인: `uv run python xai_finance_agent.py` 후 로그에 나온 URL(기본 `http://localhost:7777`)과 `http://localhost:7777/docs` 접속. Step 2에서 확인한 실제 로그 문구를 옮긴다.
  - Step 6 첫 질문: https://os.agno.com 접속 → 로컬 AgentOS 연결(`http://localhost:7777`) → 질문 예시 "AAPL 최근 주가와 관련 뉴스를 표로 정리해줘". `debug_mode=True`라 터미널에 도구 호출 로그가 찍히는 것을 보라는 안내. 확인: 터미널 로그에 `YFinanceTools` 또는 `DuckDuckGoTools` 호출이 보이고 화면에 표가 나온다.
- **요청 한 건이 흐르는 과정**: 시퀀스 그림 + 도구 호출 루프(LLM이 tool_call을 돌려주면 에이전트가 실행하고 결과를 다시 LLM에 보내는 반복)가 핵심이라는 해설 한 문단.
- **실행 체크리스트**: 키 설정, 설치, 서버 기동, 컨트롤 플레인 연결, 질문 응답 확인, 로그에서 도구 호출 확인.
- **문제 해결** 표: `XAI_API_KEY` 미설정 시 증상(Step 2에서 확인한 실제 예외), `duckduckgo-search`/`ddgs` import 오류(확인된 경우), 7777 포트 충돌(`serve(port=...)`는 코드 수정이므로 다른 프로세스 종료 안내), 컨트롤 플레인이 localhost에 연결하지 못할 때(브라우저의 혼합 콘텐츠 차단, 서버가 떠 있는지 `curl http://localhost:7777/docs`), 앱 README가 "OpenAI API Key"라고 잘못 적은 것(실제로는 xAI 키).
- **더 해보기**: 지시문을 바꿔 한국어 답변 강제, `YFinanceTools`에 다른 종목 비교 질문, `debug_mode=False`로 바꿔 로그 차이 보기.
- **다음 날 예고**: `[Day 002 · 🕸️ Web Scraping AI Agent](../day002-web-scraping-ai-agent/README.md)` — 웹 페이지를 LLM으로 구조화해 긁어오는 에이전트.

- [ ] **Step 6: 검사와 로드맵 갱신**

Run: `cd docs/tutorials/_tools && npm run check && npm run roadmap && npm run check`
Expected: 두 번 모두 `check: 통과`. 로드맵에 `진도: 1 / 133일 완료`, Day 001 행이 ✅와 링크.

- [ ] **Step 7: 그림 육안 확인**

`docs/tutorials/day001-xai-finance-agent/diagrams/overview.svg`, `step3.svg`, `sequence.svg`를 브라우저로 연다(`start` 명령 또는 Chrome 도구). 확인: 한글 라벨이 깨지지 않음, 라벨이 도형 밖으로 넘치지 않음, `todo` 노드가 흐리고 `new` 노드가 주황 테두리, 시퀀스의 메시지 순서가 위에서 아래로 맞음. 문제가 있으면 `.d2`를 고치고 Step 4부터 반복.

- [ ] **Step 8: 커밋**

```bash
git add docs/tutorials/day001-xai-finance-agent docs/tutorials/README.md
git commit -m "docs(tutorials): scaffold 133-day series and Day 1"
```

- [ ] **Step 9: 사용자 검토 요청 (중단점)**

Day 1의 톤, 깊이, 그림 스타일에 대한 사용자 피드백을 받는다. 조정 사항은 `roadmap.template.md`(공통 안내), `theme.d2`(스타일), `scaffold.mjs`의 골격(구조), 스펙 4·5절(규칙)에 반영하고 커밋한 뒤 Task 7로 간다. 피드백 없이 다음 작업을 시작하지 않는다.

---

### Task 7: 볼륨 1 — Day 2~13 (Starter AI Agents)

**Files:**
- Create: `docs/tutorials/day002-…` ~ `docs/tutorials/day013-…` (아래 표), 각 `README.md` + `diagrams/*.d2|svg`
- Modify (생성): `docs/tutorials/README.md`

**Interfaces:**
- Consumes: Task 1~6의 도구와 Day 1의 문체·깊이.
- Produces: 볼륨 1 완성. 커밋 메시지 `docs(tutorials): Volume 1 Starter AI Agents, Day 2-13`.

**일차 표 (days.json과 동일):**

| Day | 폴더 | 원본 앱 |
|---|---|---|
| 002 | `day002-web-scraping-ai-agent` | `starter_ai_agents/web_scraping_ai_agent` |
| 003 | `day003-ai-blog-to-podcast-agent` | `starter_ai_agents/ai_blog_to_podcast_agent` |
| 004 | `day004-ai-music-generator-agent` | `starter_ai_agents/ai_music_generator_agent` |
| 005 | `day005-mixture-of-agents` | `starter_ai_agents/mixture_of_agents` |
| 006 | `day006-ai-data-analysis-agent` | `starter_ai_agents/ai_data_analysis_agent` |
| 007 | `day007-ai-meme-generator-agent-browseruse` | `starter_ai_agents/ai_meme_generator_agent_browseruse` |
| 008 | `day008-ai-medical-imaging-agent` | `starter_ai_agents/ai_medical_imaging_agent` |
| 009 | `day009-multimodal-ai-agent` | `starter_ai_agents/multimodal_ai_agent` |
| 010 | `day010-ai-x402-paying-agent` | `starter_ai_agents/ai_x402_paying_agent` |
| 011 | `day011-ai-breakup-recovery-agent` | `starter_ai_agents/ai_breakup_recovery_agent` |
| 012 | `day012-ai-travel-agent` | `starter_ai_agents/ai_travel_agent` |
| 013 | `day013-openai-research-agent` | `starter_ai_agents/openai_research_agent` |

**하루 제작 절차 (Day 2~13 각각에 대해 그대로 수행):**

- [ ] **Step 1: 골격 생성** — `cd docs/tutorials/_tools && npm run scaffold -- <일차 번호>`.
- [ ] **Step 2: 원본 앱 읽기** — 앱 폴더의 모든 파일(`README*`, `requirements.txt`, `*.py`, `.env.example`)을 읽고 다음을 표로 정리한다: 엔트리 파일, 실행 명령(Streamlit이면 `uv run streamlit run <파일>`), 모델/제공자, 도구·외부 서비스, 필요한 키(UI 입력인지 환경변수인지), 저장소(DB/벡터), 포트. 앱 README가 틀린 부분(잘못된 키 이름, 없는 파일 등)을 메모한다.
- [ ] **Step 3: 키 없이 되는 확인 실행** — Task 6 Step 2와 같은 방법으로 임시 가상환경에 `requirements.txt`를 설치하고, 엔트리 파일 `py_compile`, 주요 import, 도구 클래스의 `functions` 목록을 확인한다. 실패한 것은 정확한 예외 문구와 함께 "문제 해결"에 넣는다. 확인 후 임시 환경을 삭제한다.
- [ ] **Step 4: 스텝 설계** — 앱 구조를 따라 5~8개 Step을 정한다(환경 → 모델·에이전트 → 도구 → 프롬프트 → UI → 실행이 기본이고, 앱이 여러 에이전트를 쓰면 에이전트마다 Step 하나). 각 Step에 발췌할 줄 범위와 확인 명령을 먼저 적는다.
- [ ] **Step 5: 다이어그램 작성** — `overview.d2`(노드 12개 이하, 첫 줄 `...@../../_tools/theme`, 정해진 클래스 15개만), `step1..N.d2`(`...@overview` + `x.class: ours-new`/`x.class: ext-todo`처럼 단일 클래스 덧씌우기), `sequence.d2`(`shape: sequence_diagram`). 상태 기계·데이터 모델·배포가 핵심인 앱은 `extra-<이름>.d2` 추가.
- [ ] **Step 6: README 작성** — 스펙 4절 템플릿과 Day 1의 문체로 채운다. 모든 코드 발췌에 `경로:시작-끝`. `(작성 필요)`가 남지 않게 한다. "다음 날 예고"는 days.json의 다음 일차 제목과 폴더로.
- [ ] **Step 7: 렌더와 검사** — `npm run render -- day<NNN>` → `rendered N, failed 0`; `npm run check` → `check: 통과`.
- [ ] **Step 8: 로드맵 갱신** — `npm run roadmap && npm run check`.
- [ ] **Step 9: 육안 확인** — 그날의 `overview.svg`와 `sequence.svg`를 브라우저로 열어 라벨·배치를 본다.

**볼륨 마무리:**

- [ ] **Step 10: 볼륨 육안 표본 검사** — 볼륨의 SVG 중 3장 이상을 브라우저로 열어 확인했음을 기록.
- [ ] **Step 11: 커밋** — `git add docs/tutorials && git commit -m "docs(tutorials): Volume 1 Starter AI Agents, Day 2-13"`. 하루 서너 개마다 중간 커밋을 해도 된다(메시지 `docs(tutorials): Day 2-5`).

---

### Task 8: 볼륨 2~15 — Day 14~133

**Files:**
- Create: `docs/tutorials/day014-…` ~ `docs/tutorials/day133-…` (폴더명은 `_tools/days.json`), 각 `README.md` + `diagrams/*`
- Modify (생성): `docs/tutorials/README.md`

**Interfaces:**
- Consumes: Task 1~7.
- Produces: 시리즈 완성. 볼륨마다 커밋 `docs(tutorials): Volume {n} {볼륨명}, Day {a}-{b}`.

**볼륨 순서와 범위 (`days.json`의 `vol` 값):**

| 볼륨 | 이름 | Day |
|---|---|---|
| 2 | 🧑‍🏫 Crash Courses | 14–34 |
| 3 | 💬 Chat with X | 35–40 |
| 4 | 📀 RAG | 41–61 |
| 5 | 💾 LLM Apps with Memory | 62–67 |
| 6 | 🚀 Advanced AI Agents | 68–88 |
| 7 | 🤝 Multi-agent Teams | 89–101 |
| 8 | ♾️ MCP AI Agents | 102–107 |
| 9 | 🎮 Autonomous Game-Playing | 108–110 |
| 10 | 🗣️ Voice AI Agents | 111–114 |
| 11 | 🖼️ Generative UI | 115–121 |
| 12 | 🛰️ Always-on Agents | 122–123 |
| 13 | 🎯 LLM Optimization | 124–125 |
| 14 | 🔧 LLM Fine-tuning | 126–127 |
| 15 | 🧩 Agent Skills | 128–133 |

**하루 제작 절차 (Day 14~133 각각에 대해 그대로 수행):**

- [ ] **Step 1: 골격 생성** — `cd docs/tutorials/_tools && npm run scaffold -- <일차 번호>`.
- [ ] **Step 2: 원본 앱 읽기** — 앱 폴더의 모든 파일을 읽고 엔트리 파일, 실행 명령, 모델/제공자, 도구·외부 서비스, 키(UI 입력/환경변수), 저장소, 포트를 표로 정리한다. 앱 README의 오류를 메모한다. 파일이 많은 앱(수천 줄 이상)은 요청 경로 하나에 관여하는 핵심 파일만 고르고 나머지는 컴포넌트 표에 역할만 적는다.
- [ ] **Step 3: 키 없이 되는 확인 실행** — 임시 가상환경에 `requirements.txt`(또는 `pyproject.toml`)를 설치하고 엔트리 `py_compile`, 주요 import, 도구 `functions` 목록을 확인한다. Node 앱(볼륨 11)은 `npm install`과 `npm run build`(또는 `npx tsc --noEmit`)까지 확인한다. 실패는 정확한 문구와 함께 "문제 해결"에 넣고 임시 환경을 지운다.
- [ ] **Step 4: 스텝 설계** — 5~8개 Step, Step마다 줄 범위와 확인 명령을 먼저 적는다. 볼륨별 규칙: 크래시 코스는 레슨 README의 흐름을 따르되 템플릿으로 재구성; Generative UI는 Node 20+ 설치 Step과 백엔드/프론트엔드 Step 분리; Always-on은 `extra-deploy.d2` 추가; Fine-tuning은 GPU/Colab 필요를 사전 준비에 명시; Agent Skills는 설치(`npx skills add …`)·호출·스킬 흐름을 Step으로.
- [ ] **Step 5: 다이어그램 작성** — `overview.d2`(노드 12개 이하, `...@../../_tools/theme`, 정해진 클래스 15개만), `step1..N.d2`(`...@overview` + `x.class: 기본-new`/`기본-todo` 단일 클래스 덧씌우기), `sequence.d2`, 필요 시 `extra-<이름>.d2`.
- [ ] **Step 6: README 작성** — 스펙 4절 템플릿과 Day 1의 문체로. 코드 발췌마다 `경로:시작-끝`. `(작성 필요)` 금지. Day 133은 "다음 날 예고" 대신 시리즈 마무리 문단.
- [ ] **Step 7: 렌더와 검사** — `npm run render -- day<NNN>` → `failed 0`; `npm run check` → `check: 통과`.
- [ ] **Step 8: 로드맵 갱신** — `npm run roadmap && npm run check`.
- [ ] **Step 9: 육안 확인** — 그날의 `overview.svg`와 `sequence.svg`를 브라우저로 연다.

**볼륨 마무리 (볼륨마다):**

- [ ] **Step 10: 볼륨 육안 표본 검사** — SVG 3장 이상을 브라우저로 열어 확인.
- [ ] **Step 11: 커밋** — `git add docs/tutorials && git commit -m "docs(tutorials): Volume {n} {볼륨명}, Day {a}-{b}"`. 21일짜리 볼륨(2, 4, 6)은 7일 단위 중간 커밋을 허용.
- [ ] **Step 12: upstream 동기화 후 재검사** — 볼륨 사이에 upstream을 병합했다면 `npm run check`로 어긋난 코드 위치를 잡아 고친다.

---

## 실행 메모

- 세션이 바뀌면 먼저 `docs/tutorials/README.md`의 진도와 이 계획의 체크박스를 읽고, `cd docs/tutorials/_tools && npm install && npm test && npm run check`가 통과하는지 확인한 뒤 이어간다.
- D2 렌더러 초기화와 그림 한 장 렌더는 각각 1~2초다. 다만 ELK 워커가 살아 있어 프로세스가 스스로 끝나지 않으므로, 렌더하는 스크립트는 `process.exit`로 끝내고 테스트는 `--test-force-exit`로 돌린다. 파이프(`| tail`)로 출력을 받으면 끝날 때까지 아무것도 보이지 않으니 파일로 받거나 그대로 출력한다.
- Windows에서 `git add` 시 "LF will be replaced by CRLF" 경고는 무시한다(저장소는 LF).
