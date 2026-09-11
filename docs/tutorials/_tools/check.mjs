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
