import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join, resolve, dirname } from "node:path";
import { inlineImports, sourceHash, readSvgHash } from "./d2.mjs";
import { folderName, PLACEHOLDER } from "./days.mjs";

export const SVG_MAX_WIDTH = 1400;

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
      const width = Number(svgText.match(/<svg[^>]*\swidth="(\d+)"/)?.[1] ?? 0);
      if (width > SVG_MAX_WIDTH) problems.push(rel(`다이어그램이 본문 폭에서 읽히지 않음: diagrams/${f.replace(/\.d2$/, ".svg")} (${width}px, 상한 ${SVG_MAX_WIDTH}px) — direction: down으로 바꾸거나 노드를 컨테이너로 묶으세요`));
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
