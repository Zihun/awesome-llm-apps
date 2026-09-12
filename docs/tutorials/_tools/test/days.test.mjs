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
  assert.ok(text.includes(`Day 002 · ${days[1].title} — `), "unlinked by default");
  assert.ok(!text.includes(`(../${folderName(days[1])}/README.md)`), "no link when the next day does not exist");
  const linkedText = readmeSkeleton(days[0], days[1], true);
  assert.ok(linkedText.includes(`[Day 002 · ${days[1].title}](../${folderName(days[1])}/README.md)`), "linked when it exists");
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

test("scaffolding a day links the previous day's pointer", () => {
  const root = mkdtempSync(join(tmpdir(), "tut-link-"));
  const days = loadDays();
  scaffoldDay(1, { root });
  const day1Readme = join(root, folderName(days[0]), "README.md");
  assert.ok(!readFileSync(day1Readme, "utf8").includes(`(../${folderName(days[1])}/README.md)`), "day 1 starts unlinked");
  scaffoldDay(2, { root });
  assert.ok(readFileSync(day1Readme, "utf8").includes(`[Day 002 · ${days[1].title}](../${folderName(days[1])}/README.md)`), "day 1 now links day 2");
  assert.ok(!readFileSync(day1Readme, "utf8").includes("링크로 바뀝니다"), "the stale aside is removed when the link goes live");
  assert.ok(!readFileSync(join(root, folderName(days[1]), "README.md"), "utf8").includes(`(../${folderName(days[2])}/README.md)`), "day 2 itself stays unlinked");
});
