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
