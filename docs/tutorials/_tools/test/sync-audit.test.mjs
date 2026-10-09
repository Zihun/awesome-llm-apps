import { test } from "node:test";
import assert from "node:assert/strict";
import { readmeAppLinks, planGaps, citedPaths, affectedDays } from "../sync-audit.mjs";

test("readmeAppLinks keeps local app folders and drops external, file and docs/ links", () => {
  const readme = [
    "* [A](starter_ai_agents/a/) - x",
    "* [B](https://github.com/x/y) <sub>↗ external</sub>",
    "<img src=\"docs/banner/x.png\"> [banner](docs/banner/)",
    "* [C](agent_skills/c) [again](agent_skills/c/)",
    "[guide](UV_MIGRATION_GUIDE.md)",
  ].join("\n");
  assert.deepEqual(readmeAppLinks(readme), ["starter_ai_agents/a", "agent_skills/c"]);
});

test("planGaps treats a README link to a parent folder as covered (crash courses)", () => {
  const days = [{ path: "course/1_lesson" }, { path: "starter/a" }, { path: "gone/b" }];
  const links = ["course", "starter/a", "new/c"];
  const gaps = planGaps(days, links, (p) => p !== "gone/b");
  assert.deepEqual(gaps, { notInPlan: ["new/c"], missingOnDisk: ["gone/b"] });
});

test("citedPaths reads repo paths in backticks and repo-relative links, not bare file names or other days", () => {
  const md = [
    "코드는 `starter/a/app.py:11`와 `starter/a/README.md`에 있다. 앱 `README.md`는 다르게 말한다.",
    "전날 설명은 `docs/tutorials/day001-x/README.md`에 있다.",
    "[원본](../../../starter/a/) · [전날](../day001-x/README.md) · [로드맵](../README.md)",
  ].join("\n");
  assert.deepEqual(citedPaths(md, "docs/tutorials/day002-a").sort(), [
    "starter/a",
    "starter/a/README.md",
    "starter/a/app.py",
  ]);
});

test("a cited category folder that holds other apps does not pull in their changes", () => {
  // Day 084는 `advanced_ai_agents/multi_agent_apps`를 분류로만 언급했는데, 그 아래 다른 앱의
  // 변경이 모두 Day 084에 걸렸다(2026-10-10). 앱을 품은 상위 폴더 인용은 세지 않는다.
  const written = [
    { day: { path: "cat/apps/a" }, md: "`cat/apps` 아래 · `cat/apps/b` 참고", dayDirFromRoot: "docs/tutorials/day001-a" },
  ];
  const changed = ["cat/apps/c/README.md", "cat/apps/b/app.py"];
  const appPaths = ["cat/apps/a", "cat/apps/b", "cat/apps/c"];
  assert.deepEqual(affectedDays(written, changed, appPaths), [
    { day: { path: "cat/apps/a" }, inApp: [], cited: ["cat/apps/b/app.py"] },
  ]);
});

test("affectedDays reports changes inside the day's app and in paths it cites elsewhere", () => {
  const written = [
    { day: { path: "starter/a" }, md: "`shared/util.py:3`", dayDirFromRoot: "docs/tutorials/day001-a" },
    { day: { path: "starter/b" }, md: "`starter/b/app.py:1`", dayDirFromRoot: "docs/tutorials/day002-b" },
  ];
  const changed = ["starter/a/app.py", "shared/util.py", "other/z.py"];
  assert.deepEqual(affectedDays(written, changed), [
    { day: { path: "starter/a" }, inApp: ["starter/a/app.py"], cited: ["shared/util.py"] },
  ]);
});
