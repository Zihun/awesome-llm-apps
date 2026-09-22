import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { inlineImports, sourceHash, readSvgHash } from "./d2.mjs";
import { edgeCrossings, stretchedIcons, ICON_MAX_HEIGHT } from "./edges.mjs";
import { folderName, PLACEHOLDER } from "./days.mjs";

// 폭 상한. 본문이 그림을 축소하면 12px 글자가 그만큼 작아지고 한글이 먼저 뭉개진다.
// 시퀀스 그림은 배우가 가로로 늘어서므로 따로 잡는다.
export const SVG_MAX_WIDTH = 1200;
export const SEQUENCE_MAX_WIDTH = 1400;

// 세로 상한. GitHub 본문에서 한 장이 화면을 통째로 먹지 않는 선이다. 시퀀스 그림은
// 메시지 하나가 행 하나라 본래 길쭉하므로 따로 잡는다.
export const SVG_MAX_HEIGHT = 700;
export const SEQUENCE_MAX_HEIGHT = 1500;

/** 임베드 폰트에 담긴 글자 목록. fonts/build.py가 쓴다. */
let fontCoverage;
export function coveredCharacters() {
  if (fontCoverage) return fontCoverage;
  const path = resolve(dirname(fileURLToPath(import.meta.url)), "..", "fonts", "coverage.txt");
  fontCoverage = existsSync(path) ? new Set(readFileSync(path, "utf8")) : null;
  return fontCoverage;
}

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
const EXCERPT_RE = /^`([A-Za-z0-9_.\-]+(?:\/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]+):(\d+)-(\d+)`[ \t]*\r?\n\r?\n```[A-Za-z0-9]*\r?\n([\s\S]*?)\r?\n```/gm;

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
      const svgText = readFileSync(svg, "utf8");
      if (readSvgHash(svgText) !== expected) problems.push(rel(`stale svg (다시 렌더 필요): diagrams/${f}`));
      const covered = coveredCharacters();
      if (covered) {
        const missing = [...new Set(readFileSync(join(diagrams, f), "utf8"))]
          .filter((c) => c.charCodeAt(0) > 0x7f && !covered.has(c));
        if (missing.length) problems.push(rel(`임베드 폰트에 없는 글자 ${JSON.stringify(missing.join(""))}: diagrams/${f} — \`python fonts/build.py\` 후 \`npm run render -- --force\``));
      }
      const width = Number(svgText.match(/<svg[^>]*\swidth="(\d+)"/)?.[1] ?? 0);
      const widthCap = f.startsWith("sequence") ? SEQUENCE_MAX_WIDTH : SVG_MAX_WIDTH;
      if (width > widthCap) problems.push(rel(`다이어그램이 본문 폭에서 읽히지 않음: diagrams/${f.replace(/\.d2$/, ".svg")} (${width}px, 상한 ${widthCap}px) — grid-columns를 줄여 줄을 나누세요. 라벨이 긴 상자를 가로로 여러 개 세우면 폭이 금세 넘칩니다`));
      // (17) 연결선이 남의 도형을 가로지르면 그림이 읽히지 않는다. 그리드는 엣지를 보지 않고
      //      자리를 정하고 그 위에 직선을 긋기 때문에, 멀리 떨어진 칸을 이으면 사이를 관통한다.
      //      고치는 법은 엣지를 컨테이너 수준으로 올리는 것이다(§5).
      const crossings = edgeCrossings(svgText);
      if (crossings) problems.push(rel(`연결선이 다른 도형을 가로지릅니다: diagrams/${f.replace(/\.d2$/, ".svg")} (${crossings}곳) — 자식 하나하나를 가리키는 대신 묶음끼리 잇도록 엣지를 컨테이너 수준으로 올리세요`));
      // (18) 종횡비를 지키는 아이콘이 그리드 칸을 혼자 쓰면 통째로 늘어난다.
      for (const icon of stretchedIcons(svgText)) {
        problems.push(rel(`아이콘이 칸에 맞춰 늘어났습니다: diagrams/${f.replace(/\.d2$/, ".svg")}의 ${icon.kind} ${icon.width}x${icon.height} (높이 상한 ${ICON_MAX_HEIGHT}px) — 그리드 칸을 혼자 쓰지 말고 형제와 함께 컨테이너에 넣으세요`));
      }
      const height = Number(svgText.match(/<svg[^>]*\sheight="(\d+)"/)?.[1] ?? 0);
      const heightCap = f.startsWith("sequence") ? SEQUENCE_MAX_HEIGHT : SVG_MAX_HEIGHT;
      if (height > heightCap) problems.push(rel(`다이어그램이 세로로 너무 깁니다: diagrams/${f.replace(/\.d2$/, ".svg")} (${height}px, 상한 ${heightCap}px) — 관련된 것끼리 컨테이너로 묶고 루트에 grid-rows/grid-columns를 주세요. 안쪽 컨테이너의 direction은 엣지가 있으면 무시됩니다`));
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

  // (9) 인용한 줄 범위와 바로 뒤 코드 블록의 내용이 일치하는지
  const norm = (s) => s.split(/\r?\n/).map((l) => l.replace(/[ \t]+$/, "")).join("\n").replace(/\n+$/, "");
  for (const m of md.matchAll(EXCERPT_RE)) {
    const [, path, start, end, quoted] = m;
    const file = resolve(repoRoot, path);
    if (!existsSync(file)) continue; // (4)가 이미 보고함
    const src = readFileSync(file, "utf8").split(/\r?\n/).slice(Number(start) - 1, Number(end));
    if (norm(src.join("\n")) !== norm(quoted)) {
      problems.push(rel(`코드 발췌가 인용한 줄 범위와 다름: ${path}:${start}-${end} — 발췌한 그대로의 범위를 적으세요`));
    }
  }

  // (10) 코드 스팬 백틱 짝 맞추기 (표 안에서 특히 자주 깨진다)
  let inFence = false;
  md.split(/\r?\n/).forEach((line, i) => {
    if (line.startsWith("```")) { inFence = !inFence; return; }
    if (inFence) return;
    const ticks = line.split("`").length - 1;
    if (ticks % 2) problems.push(rel(`백틱 짝이 맞지 않아 코드 스팬이 깨짐: README.md:${i + 1}`));
  });

  // (11) 경로 없는 줄 번호만 남은 인용. 펜스 밖에서, 같은 줄이 소스 파일을 언급할 때만
  //      본다 — 파이썬 슬라이스(`:10`)나 시각 표기(`:30`)를 인용으로 오인하지 않기 위해서다.
  const FILE_REF = /[A-Za-z0-9_.\-]+\.(?:py|ts|tsx|js|mjs|jsx|json|toml|md|txt|yml|yaml)\b/;
  for (const line of stripFences(md).split(/\r?\n/)) {
    if (!FILE_REF.test(line)) continue;
    for (const m of line.matchAll(/`:(\d+(?:-\d+)?)`/g)) {
      problems.push(rel(`인용에 파일 경로가 빠졌습니다: \`:${m[1]}\` — \`경로/파일.py:${m[1]}\` 형식으로 쓰세요`));
    }
  }

  // (12) 더 해보기의 줄 번호 인용은 백틱 안에 경로까지 들어가야 한다. 서술문 속
  //      "29행의 …"는 정상이므로 이 절에서만 본다.
  const howToLines = md.split(/\r?\n/);
  const moreStart = howToLines.findIndex((l) => l.startsWith("## 더 해보기"));
  if (moreStart >= 0) {
    let moreEnd = howToLines.findIndex((l, i) => i > moreStart && l.startsWith("## "));
    if (moreEnd < 0) moreEnd = howToLines.length;
    for (let i = moreStart + 1; i < moreEnd; i++) {
      const bare = howToLines[i].replace(/`[^`]*`/g, "");
      const hit = bare.match(/\d+(?:[-·]\d+)*행/);
      if (hit) problems.push(rel(`더 해보기의 줄 번호 인용에 백틱과 경로가 없음: README.md:${i + 1} (${hit[0]})`));
    }
  }

  // (13) 저장소 밖(.venv, site-packages)을 가리키는 인용은 독자 환경에서 깨진다.
  for (const m of stripFences(md).matchAll(/`((?:\.venv\/|[^`\s]*site-packages\/)[^`\s]*?):(\d+(?:-\d+)?)`/g)) {
    problems.push(rel(`저장소 밖을 가리키는 인용: \`${m[1]}:${m[2]}\` — 서드파티 내부는 "소스로 확인"으로 적고 패키지와 버전을 밝히세요`));
  }

  // (14) 이 저장소는 루트에 pyproject.toml이 있어 uv가 루트를 프로젝트로 본다. --no-project
  //      없이 uv run을 쓰면 독자가 만든 앱 폴더 환경이 아니라 루트 환경이 쓰인다. 독자가 실제로
  //      실행하는 명령만 본다 — 셸 펜스(bash/sh/powershell) 안쪽. 태그 없는 펜스는 실패를 보여
  //      주는 시연일 수 있으므로 건드리지 않는다.
  let shellFence = null;
  md.split(/\r?\n/).forEach((line, i) => {
    const open = line.match(/^```(\w*)/);
    if (open) {
      shellFence = shellFence === null ? (open[1] || "") : null;
      return;
    }
    if (!["bash", "sh", "powershell"].includes(shellFence)) return;
    if (/(?:^|\s)uv run\s/.test(line) && !line.includes("--no-project")) {
      problems.push(rel(`uv run에 --no-project가 없어 루트 환경이 쓰입니다: README.md:${i + 1}`));
    }
  });

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
