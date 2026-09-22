import { test } from "node:test";
import assert from "node:assert/strict";
import { pathPoints, edgeCrossings, stretchedIcons } from "../lib/edges.mjs";

// D2는 도형을 그릴 때 `H 336`처럼 좌표를 하나만 받는 명령을 섞어 쓴다. 숫자를 무작정
// 쌍으로 묶으면 좌표가 한 칸씩 밀려 경계상자가 터무니없이 커진다 — 실제로 921px짜리
// 그림 안에서 1280px 구름이 나왔고, 그 때문에 첫 측정이 70%라는 거짓 수치를 냈다.
test("pathPoints honours single-argument commands", () => {
  const pts = pathPoints("M 10 10 H 50 V 40 Z");
  assert.equal(Math.max(...pts.map((p) => p[0])), 50);
  assert.equal(Math.max(...pts.map((p) => p[1])), 40);
});

test("pathPoints follows relative commands", () => {
  const pts = pathPoints("M 10 10 l 20 0 v 15");
  assert.equal(Math.max(...pts.map((p) => p[0])), 30);
  assert.equal(Math.max(...pts.map((p) => p[1])), 25);
});

function svgOf(shapes, connection) {
  const nodes = shapes
    .map((s) => '<g class="YQ== ' + s.cls + '"><g class="shape" >' + s.tag + "</g></g>")
    .join("");
  const edge = connection ? '<path d="' + connection + '" class="connection" />' : "";
  return nodes + edge;
}

const box = (x, y) => '<rect x="' + x + '" y="' + y + '" width="60" height="40" />';

test("an edge crossing a shape that is not its endpoint is reported", () => {
  const shapes = [
    { cls: "ours", tag: box(0, 0) },
    { cls: "ours", tag: box(100, 0) }, // 가운데를 막고 선 상자
    { cls: "ours", tag: box(200, 0) },
  ];
  // 왼쪽 끝에서 오른쪽 끝으로 곧장 그으면 가운데 상자를 관통한다
  assert.ok(edgeCrossings(svgOf(shapes, "M 60 20 L 200 20")) > 0);
  // 위로 돌아가면 아무것도 건드리지 않는다
  assert.equal(edgeCrossings(svgOf(shapes, "M 60 20 L 60 -30 L 200 -30 L 200 20")), 0);
});

test("an edge touching only its own endpoints is not a crossing", () => {
  const shapes = [{ cls: "ours", tag: box(0, 0) }, { cls: "ours", tag: box(100, 0) }];
  assert.equal(edgeCrossings(svgOf(shapes, "M 60 20 L 100 20")), 0);
});

// 그리드가 칸 크기를 줄맞춤하면 종횡비를 지키는 아이콘이 칸을 채우려고 통째로 늘어난다.
// 늘어남은 높이에만 나타나고, 라벨이 길어 옆으로 넓어지는 것은 정상이다.
test("an icon stretched by its grid cell is reported, but a wide one is not", () => {
  const tall = [{ cls: "person", tag: '<path d="M 0 0 H 300 V 260 H 0 Z" />' }];
  const wide = [{ cls: "ext", tag: '<path d="M 0 0 H 360 V 79 H 0 Z" />' }];
  assert.equal(stretchedIcons(svgOf(tall)).length, 1);
  assert.equal(stretchedIcons(svgOf(wide)).length, 0);
});

// Day 045는 사람 아이콘이 643x64로 그림 폭을 가로질러 납작해졌는데, 높이만 재던
// 첫 규칙은 이것을 통과시켰다. 사람은 대체로 정사각형이므로 폭도 함께 본다.
test("a person smeared across the diagram is reported", () => {
  const flat = [{ cls: "person", tag: '<path d="M 0 0 H 640 V 64 H 0 Z" />' }];
  assert.equal(stretchedIcons(svgOf(flat)).length, 1);
});

test("a wide cloud is still allowed", () => {
  const cloud = [{ cls: "ext", tag: '<path d="M 0 0 H 430 V 79 H 0 Z" />' }];
  assert.equal(stretchedIcons(svgOf(cloud)).length, 0);
});

test("rectangles are never counted as stretched icons", () => {
  const rect = [{ cls: "ours", tag: '<rect x="0" y="0" width="400" height="300" />' }];
  assert.equal(stretchedIcons(svgOf(rect)).length, 0);
});
