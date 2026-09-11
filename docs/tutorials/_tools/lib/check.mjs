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
    const lines = readFileSync(file, "utf8").split(/\r?\n/).length;
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
