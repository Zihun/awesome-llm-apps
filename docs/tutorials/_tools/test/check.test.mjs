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

test("an svg wider than the column cap is reported", () => {
  const { repo, dayDir } = fixture();
  const d2 = join(dayDir, "diagrams", "overview.d2");
  const hash = sourceHash(inlineImports(d2));
  writeFileSync(join(dayDir, "diagrams", "overview.svg"), embedHash('<svg width="3030" height="349"></svg>', hash));
  const problems = checkDay(dayDir, { repoRoot: repo });
  assert.ok(problems.some((p) => p.includes("3030px") && p.includes("1400px")), problems.join("\n"));
  writeFileSync(join(dayDir, "diagrams", "overview.svg"), embedHash('<svg width="1400" height="900"></svg>', hash));
  assert.deepEqual(checkDay(dayDir, { repoRoot: repo }), []);
});

test("an unbalanced code span is reported outside a fence, but not inside one", () => {
  const { repo, dayDir } = fixture({
    readme: GOOD_README("정상: `x` `y`\n깨진: ``a` 하나\n```text\n펜스 안 홀수 백틱: `\n```\n"),
  });
  const problems = checkDay(dayDir, { repoRoot: repo });
  const backtickProblems = problems.filter((p) => p.includes("백틱 짝"));
  assert.equal(backtickProblems.length, 1, problems.join("\n"));
  assert.ok(backtickProblems[0].includes("README.md:"), backtickProblems[0]);
});

test("a bare :N-M citation missing its file path is reported, a full path:N-M is not", () => {
  // Case 1: A line with file name and orphaned citation IS reported
  const case1 = fixture({ readme: GOOD_README("파일 언급과 고아 인용: app/main.py `:12-15`\n") });
  const problems1 = checkDay(case1.dayDir, { repoRoot: case1.repo });
  assert.ok(
    problems1.some((p) => p.includes("인용에 파일 경로가 빠졌습니다") && p.includes(":12-15")),
    `Case 1 (file + orphan) should report: ${problems1.join("\n")}`
  );

  // Case 2: Same orphaned citation inside a fenced code block is NOT reported
  const case2 = fixture({ readme: GOOD_README("```\napp/main.py `:12-15`\n```\n") });
  const problems2 = checkDay(case2.dayDir, { repoRoot: case2.repo });
  assert.ok(
    !problems2.some((p) => p.includes("인용에 파일 경로가 빠졌습니다") && p.includes(":12-15")),
    `Case 2 (fence) should not report: ${problems2.join("\n")}`
  );

  // Case 3: Python slice `:10` without file name is NOT reported
  const case3 = fixture({ readme: GOOD_README("슬라이스 `:10`을 사용합니다\n") });
  const problems3 = checkDay(case3.dayDir, { repoRoot: case3.repo });
  assert.ok(
    !problems3.some((p) => p.includes("인용에 파일 경로가 빠졌습니다")),
    `Case 3 (slice, no file) should not report: ${problems3.join("\n")}`
  );

  // Case 4: Full citation `app/main.py:1-2` is NOT reported as orphaned
  const case4 = fixture({ readme: GOOD_README("정상 인용: `app/main.py:1-2`\n") });
  const problems4 = checkDay(case4.dayDir, { repoRoot: case4.repo });
  assert.deepEqual(problems4, [], `Case 4 (full path) should pass`);
});

test("a code excerpt that does not match its cited range is reported", () => {
  const good = GOOD_README("`app/main.py:1-2`\n\n```python\nprint(1)\nprint(2)\n```\n");
  const f1 = fixture({ readme: good });
  assert.deepEqual(checkDay(f1.dayDir, { repoRoot: f1.repo }), [], "an exact excerpt passes");
  const bad = GOOD_README("`app/main.py:1-2`\n\n```python\nprint(2)\n```\n");
  const f2 = fixture({ readme: bad });
  assert.ok(checkDay(f2.dayDir, { repoRoot: f2.repo }).some((p) => p.includes("코드 발췌가 인용한 줄 범위와 다름")), "a trimmed excerpt is reported");
});

test("더 해보기 section bare line citations are detected", () => {
  // Case 1: A 더 해보기 bullet with bare (16-81행) IS reported
  const case1 = fixture({
    readme: GOOD_README().replace("## 더 해보기", "## 더 해보기\n\n- `initialize_agents`(16-81행)에 수정을 붙이기"),
  });
  const problems1 = checkDay(case1.dayDir, { repoRoot: case1.repo });
  assert.ok(
    problems1.some((p) => p.includes("더 해보기의 줄 번호 인용에 백틱과 경로가 없음") && p.includes("16-81행")),
    `Case 1 (bare in 더 해보기) should report: ${problems1.join("\n")}`
  );

  // Case 2: The same bullet with full backticked citation is NOT reported
  const case2 = fixture({
    readme: GOOD_README().replace("## 더 해보기", "## 더 해보기\n\n- `initialize_agents`(`app/main.py:16-81`)에 수정을 붙이기"),
  });
  const problems2 = checkDay(case2.dayDir, { repoRoot: case2.repo });
  assert.ok(
    !problems2.some((p) => p.includes("더 해보기의 줄 번호 인용에 백틱과 경로가 없음")),
    `Case 2 (full citation) should not report: ${problems2.join("\n")}`
  );

  // Case 3: A bare line number in ordinary prose (outside 더 해보기) is NOT reported
  const case3 = fixture({
    readme: GOOD_README("29행의 코드를 보면 주목할 점이 있습니다.\n\n## 더 해보기\n\n- 수정하기"),
  });
  const problems3 = checkDay(case3.dayDir, { repoRoot: case3.repo });
  assert.ok(
    !problems3.some((p) => p.includes("더 해보기의 줄 번호 인용에 백틱과 경로가 없음")),
    `Case 3 (bare in prose, not in 더 해보기) should not report: ${problems3.join("\n")}`
  );
});

test("citations pointing outside the repo (.venv, site-packages) are reported; an ordinary repo citation is not", () => {
  // Case 1: A `.venv/...` citation IS reported
  const case1 = fixture({
    readme: GOOD_README("설치된 패키지 코드(`.venv/Lib/site-packages/streamlit/web/bootstrap.py:87-90`)를 인용\n"),
  });
  const problems1 = checkDay(case1.dayDir, { repoRoot: case1.repo });
  assert.ok(
    problems1.some((p) => p.includes("저장소 밖을 가리키는 인용") && p.includes(".venv/Lib/site-packages/streamlit/web/bootstrap.py:87-90")),
    `Case 1 (.venv citation) should report: ${problems1.join("\n")}`
  );

  // Case 2: A `site-packages/...` citation without a leading .venv/ IS reported
  const case2 = fixture({
    readme: GOOD_README("다른 site-packages 경로(`lib/site-packages/pkg/mod.py:12-15`)를 인용\n"),
  });
  const problems2 = checkDay(case2.dayDir, { repoRoot: case2.repo });
  assert.ok(
    problems2.some((p) => p.includes("저장소 밖을 가리키는 인용") && p.includes("lib/site-packages/pkg/mod.py:12-15")),
    `Case 2 (site-packages citation) should report: ${problems2.join("\n")}`
  );

  // Case 3: An ordinary repo citation is NOT reported
  const case3 = fixture({ readme: GOOD_README("정상 인용: `app/main.py:1-2`\n") });
  const problems3 = checkDay(case3.dayDir, { repoRoot: case3.repo });
  assert.ok(
    !problems3.some((p) => p.includes("저장소 밖을 가리키는 인용")),
    `Case 3 (ordinary repo citation) should not report: ${problems3.join("\n")}`
  );
});

test("a bare uv run line is reported; the same line with --no-project is not; a mid-sentence mention is not", () => {
  // Case 1: A bare `uv run ...` command line inside bash fence IS reported
  const case1 = fixture({ readme: GOOD_README("```bash\nuv run python -c \"print(1)\"\n```\n") });
  const problems1 = checkDay(case1.dayDir, { repoRoot: case1.repo });
  assert.ok(
    problems1.some((p) => p.includes("uv run에 --no-project가 없어 루트 환경이 쓰입니다")),
    `Case 1 (bare uv run in bash fence) should report: ${problems1.join("\n")}`
  );

  // Case 2: The same line with --no-project inside bash fence is NOT reported
  const case2 = fixture({ readme: GOOD_README("```bash\nuv run --no-project python -c \"print(1)\"\n```\n") });
  const problems2 = checkDay(case2.dayDir, { repoRoot: case2.repo });
  assert.ok(
    !problems2.some((p) => p.includes("uv run에 --no-project가 없어 루트 환경이 쓰입니다")),
    `Case 2 (--no-project present in bash fence) should not report: ${problems2.join("\n")}`
  );

  // Case 3: A bare `uv run ...` inside an untagged fence is NOT reported (failure demo case)
  const case3 = fixture({ readme: GOOD_README("```\nuv run python -c \"print(1)\"\n```\n") });
  const problems3 = checkDay(case3.dayDir, { repoRoot: case3.repo });
  assert.ok(
    !problems3.some((p) => p.includes("uv run에 --no-project가 없어 루트 환경이 쓰입니다")),
    `Case 3 (bare uv run in untagged fence) should not report: ${problems3.join("\n")}`
  );

  // Case 4: Prose that merely mentions `uv run` mid-sentence, outside any fence, is NOT reported
  const case4 = fixture({ readme: GOOD_README("이 저장소에서는 uv run이 루트 환경을 씁니다.\n") });
  const problems4 = checkDay(case4.dayDir, { repoRoot: case4.repo });
  assert.ok(
    !problems4.some((p) => p.includes("uv run에 --no-project가 없어 루트 환경이 쓰입니다")),
    `Case 4 (mid-sentence mention outside fence) should not report: ${problems4.join("\n")}`
  );

  // Case 5: An env-var-prefixed `uv run ...` command (no --no-project) inside bash fence IS reported
  const case5 = fixture({ readme: GOOD_README("```bash\nOPENAI_API_KEY=sk-not-a-real-key uv run python -c \"print(1)\"\n```\n") });
  const problems5 = checkDay(case5.dayDir, { repoRoot: case5.repo });
  assert.ok(
    problems5.some((p) => p.includes("uv run에 --no-project가 없어 루트 환경이 쓰입니다")),
    `Case 5 (env-var-prefixed uv run in bash fence) should report: ${problems5.join("\n")}`
  );
});
