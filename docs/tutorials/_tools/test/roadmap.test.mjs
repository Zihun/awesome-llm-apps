import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { loadDays, folderName } from "../lib/days.mjs";
import { isDayDone, renderRoadmap } from "../roadmap.mjs";

test("renderRoadmap lists every day, links only existing days, marks done days", () => {
  const days = loadDays();
  const root = mkdtempSync(join(tmpdir(), "tut-roadmap-"));
  mkdirSync(join(root, folderName(days[0])), { recursive: true });
  writeFileSync(join(root, folderName(days[0]), "README.md"), "# Day 001\n완성");
  mkdirSync(join(root, folderName(days[1])), { recursive: true });
  writeFileSync(join(root, folderName(days[1]), "README.md"), "# Day 002\n(작성 필요)");
  const out = renderRoadmap(days, root, "HEAD\n<!-- DAYS -->\n");
  const rows = out.split("\n").filter((l) => /^\| (✅|⬜) \|/.test(l));
  assert.equal(rows.length, days.length);
  assert.ok(rows[0].startsWith(`| ✅ | [Day 001](${folderName(days[0])}/README.md)`));
  assert.ok(rows[1].startsWith(`| ⬜ | [Day 002](${folderName(days[1])}/README.md)`));
  assert.ok(rows[2].startsWith("| ⬜ | Day 003 |"));
  assert.ok(out.includes(`진도: 1 / ${days.length}`));
  assert.ok(out.includes("### 볼륨 1."));
  assert.ok(out.startsWith("HEAD\n"));
  assert.equal(isDayDone(days[0], root), true);
  assert.equal(isDayDone(days[1], root), false);
  assert.equal(isDayDone(days[2], root), false);
});
