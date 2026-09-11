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

test("a code ref one line past the end of a newline-terminated file is reported", () => {
  const { repo, dayDir } = fixture({ readme: GOOD_README("`app/main.py:1-3`\n") });
  const problems = checkDay(dayDir, { repoRoot: repo });
  assert.ok(problems.some((p) => p.includes("app/main.py:1-3") && p.includes("파일은 2줄")), problems.join("\n"));
});
