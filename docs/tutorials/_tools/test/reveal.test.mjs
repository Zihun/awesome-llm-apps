import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { revealProblems } from "../lib/reveal.mjs";

// 노드 하나: <g class="BASE64ID CLASS"> (클래스가 없으면 공백 없이 BASE64ID만). shape가
// 바로 안에 와야 연결선 그룹(안에 shape가 없다)과 구분된다 — check.mjs의 reveal 규격 그대로.
function node(id, cls) {
  const b64 = Buffer.from(id).toString("base64");
  const clsPart = cls ? ` ${cls}` : "";
  return `<g class="${b64}${clsPart}"><g class="shape" ><rect x="0" y="0" width="10" height="10" /></g></g>`;
}

function svgOfNodes(entries) {
  return `<svg>${entries.map(([id, cls]) => node(id, cls)).join("")}</svg>`;
}

// diagrams/ 폴더 하나를 임시로 만든다. files: { "overview.svg": [[id, cls], ...], "step1.svg": [...] }
function diagramsDir(files) {
  const dir = mkdtempSync(join(tmpdir(), "tut-reveal-"));
  for (const [name, entries] of Object.entries(files)) {
    writeFileSync(join(dir, name), svgOfNodes(entries));
  }
  return dir;
}

test("identical node sets across every step pass with no problems", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ours"], ["b", "ext"]],
    "step1.svg": [["a", "ours-new"], ["b", "ext-todo"]],
    "step2.svg": [["a", "ours"], ["b", "ext-new"]],
  });
  assert.deepEqual(revealProblems(dir), []);
});

test("a node in a step that overview does not have is reported", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ours"], ["b", "ext"]],
    "step1.svg": [["a", "ours"], ["b", "ext"], ["c", "store-new"]],
  });
  const problems = revealProblems(dir);
  assert.ok(problems.some((p) => p.includes("step1.svg") && p.includes("c")), problems.join("\n"));
});

test("a node overview has that a step is missing is reported", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ours"], ["b", "ext"], ["c", "store"]],
    "step1.svg": [["a", "ours"], ["b", "ext"]],
  });
  const problems = revealProblems(dir);
  assert.ok(problems.some((p) => p.includes("step1.svg") && p.includes("c")), problems.join("\n"));
});

test("the count of -todo nodes increasing from one step to the next is reported", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ours"], ["b", "ext"]],
    "step1.svg": [["a", "ours-new"], ["b", "ext"]], // 0개
    "step2.svg": [["a", "ours-new"], ["b", "ext-todo"]], // 1개 — 늘었다
  });
  const problems = revealProblems(dir);
  assert.ok(problems.some((p) => p.includes("step2.svg")), problems.join("\n"));
});

test("a -todo node left in the last step is reported", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ours"], ["b", "ext"]],
    "step1.svg": [["a", "ours-new"], ["b", "ext-todo"]],
    "step2.svg": [["a", "ours"], ["b", "ext-todo"]], // 마지막인데 아직 todo
  });
  const problems = revealProblems(dir);
  assert.ok(problems.some((p) => p.includes("step2.svg") && p.includes("b")), problems.join("\n"));
});

// 넷째 불변식: step k에서 "-todo"였던 노드가 step k+1에서 "-todo"를 벗어나면 그 step에서
// "-new"로 끝나야 한다 — 흐림 -> 평상 직행은 독자가 그 부품이 언제 붙었는지 볼 수 없게
// 만드는 결함이고, 평상 -> "-new" 재강조는 관례이므로 이 불변식이 막지 않는다(§5).
test("a node that goes from -todo straight to normal (skipping -new) is reported", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ext"]],
    "step1.svg": [["a", "ext-todo"]],
    "step2.svg": [["a", "ext"]], // 흐림 -> 평상 직행: -new를 거치지 않았다
  });
  const problems = revealProblems(dir);
  assert.deepEqual(problems, [
    'diagrams/step2.svg: "a"가 step1에서 흐렸다가 주황(-new) 없이 바로 평상으로 나타납니다 — 처음 드러나는 단계에서는 -new로 표시하세요',
  ]);
});

test("a node that goes from -todo to -new (first reveal marked orange) is not reported", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ext"]],
    "step1.svg": [["a", "ext-todo"]],
    "step2.svg": [["a", "ext-new"]],
  });
  assert.deepEqual(revealProblems(dir), []);
});

test("a node that goes from -new to normal is not reported (already revealed; dropping emphasis is fine)", () => {
  const dir = diagramsDir({
    "overview.svg": [["a", "ext"]],
    "step1.svg": [["a", "ext-new"]],
    "step2.svg": [["a", "ext"]],
  });
  assert.deepEqual(revealProblems(dir), []);
});
