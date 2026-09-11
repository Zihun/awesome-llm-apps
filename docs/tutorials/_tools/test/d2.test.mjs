import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { inlineImports, sourceHash, readSvgHash, embedHash, renderSource } from "../lib/d2.mjs";

function fixture() {
  const root = mkdtempSync(join(tmpdir(), "tut-d2-"));
  mkdirSync(join(root, "_tools"));
  mkdirSync(join(root, "day001-x", "diagrams"), { recursive: true });
  writeFileSync(join(root, "_tools", "theme.d2"), "direction: right\nclasses: {\n  ours: { style.fill: \"#DBEAFE\" }\n  ours-new: { style.fill: \"#DBEAFE\"; style.stroke: \"#F97316\"; style.stroke-width: 4 }\n}\n");
  writeFileSync(join(root, "day001-x", "diagrams", "overview.d2"), "...@../../_tools/theme\na: 앱 { class: ours }\nb: 외부\na -> b: 요청\n");
  writeFileSync(join(root, "day001-x", "diagrams", "step1.d2"), "...@overview\na.class: ours-new\n");
  return root;
}

test("inlineImports replaces import lines recursively", () => {
  const root = fixture();
  const out = inlineImports(join(root, "day001-x", "diagrams", "step1.d2"));
  assert.ok(out.includes("classes: {"), "theme content inlined");
  assert.ok(out.includes("a: 앱 { class: ours }"), "overview content inlined");
  assert.ok(out.includes("a.class: ours-new"), "own content kept");
  assert.ok(!out.includes("...@"), "no import lines remain");
});

test("inlineImports throws on cycles", () => {
  const root = mkdtempSync(join(tmpdir(), "tut-cycle-"));
  writeFileSync(join(root, "a.d2"), "...@b\n");
  writeFileSync(join(root, "b.d2"), "...@a\n");
  assert.throws(() => inlineImports(join(root, "a.d2")), /import cycle/);
});

test("sourceHash is stable and hex", () => {
  assert.equal(sourceHash("x"), sourceHash("x"));
  assert.match(sourceHash("x"), /^[0-9a-f]{64}$/);
  assert.notEqual(sourceHash("x"), sourceHash("y"));
});

test("embedHash/readSvgHash round-trip", () => {
  const svg = "<svg><g/></svg>";
  const h = sourceHash("src");
  const out = embedHash(svg, h);
  assert.ok(out.endsWith("</svg>"));
  assert.equal(readSvgHash(out), h);
  assert.equal(readSvgHash(svg), null);
});

test("renderSource applies a single-class override and renders a sequence diagram", async () => {
  const root = fixture();
  const svg = await renderSource(inlineImports(join(root, "day001-x", "diagrams", "step1.d2")));
  assert.ok(svg.includes("<svg"), "svg produced");
  assert.ok(!svg.startsWith("<?xml"), "noXMLTag honoured");
  assert.ok(svg.toLowerCase().includes("f97316"), "step override (ours-new) reached the svg");
  const seq = await renderSource("shape: sequence_diagram\nu: 사용자\ns: 서버\nu -> s: 질문\ns -> u: 답변\n");
  assert.ok(seq.includes("<svg"));
});
