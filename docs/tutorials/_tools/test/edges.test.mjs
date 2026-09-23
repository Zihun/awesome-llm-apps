import { test } from "node:test";
import assert from "node:assert/strict";
import {
  pathPoints,
  edgeCrossings,
  stretchedIcons,
  edgeOverlaps,
  edgesThroughText,
  labelCollisions,
  diagonalEdges,
} from "../lib/edges.mjs";

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

// --- 검사 20~23: 화살표 규칙. 실제 D2 마크업(연결선 path + 바로 뒤 자기 <text> 라벨,
// <mask> 안 fill="black" 사각형이 라벨 상자, 잎이 아닌 도형의 shape+text가 묶음 제목)을
// 그대로 흉내 낸 합성 SVG로 검사한다.

/** 연결선 하나. 라벨이 있으면 path 바로 뒤에 자기 <text>를 둔다(실제 D2와 같은 자리). */
function edge(d, label) {
  const path = `<path d="${d}" class="connection" />`;
  return label ? `${path}<text x="${label.x}" y="${label.y}">${label.text}</text>` : path;
}

/** <mask> 하나. rects는 [x, y, width, height] 목록 — 연결선 라벨 상자(fill="black")들. */
function mask(rects) {
  const blacks = rects.map(([x, y, w, h]) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="black"></rect>`).join("");
  return `<mask id="m"><rect x="-9999" y="-9999" width="1" height="1" fill="white"></rect>${blacks}</mask>`;
}

/** 잎 도형 하나(클래스 필수 — leafBoxes가 요구하는 형태). */
function leaf(cls, tag) {
  return `<g class="YQ== ${cls}"><g class="shape" >${tag}</g></g>`;
}

/** 묶음(컨테이너) 하나: 클래스 없이 바깥 <g>를 열고 shape 뒤에 제목 <text>를, 그 뒤에
 *  자식 잎 하나를 둔다 — 실제 D2처럼 컨테이너는 항상 자식을 품는다. 자식이 없으면
 *  leafBoxes의 contains 필터가 걸러낼 것이 없어 컨테이너 자신이 잎으로 오인된다. */
function container(id, x, y, w, h, title) {
  const b64 = Buffer.from(id).toString("base64");
  const cx = x + w / 2;
  const titleY = y + 17;
  const child = leaf("ours", `<rect x="${x + 10}" y="${y + 20}" width="20" height="10" />`);
  return `<g class="${b64}"><g class="shape" ><rect x="${x}" y="${y}" width="${w}" height="${h}" /></g><text x="${cx}" y="${titleY}">${title}</text>${child}</g>`;
}

test("edgeOverlaps: two edges collinear on the same line are reported; a parallel gap or a perpendicular meeting is not", () => {
  assert.equal(edgeOverlaps(edge("M 0 0 L 100 0") + edge("M 50 0 L 150 0")).length, 1);
  assert.equal(edgeOverlaps(edge("M 0 0 L 100 0") + edge("M 0 20 L 100 20")).length, 0);
  assert.equal(edgeOverlaps(edge("M 0 0 L 100 0") + edge("M 50 -50 L 50 50")).length, 0);
});

test("edgesThroughText: a path through another edge's label is reported, through only its own label is not, through a group title is reported", () => {
  const labelBox = mask([[40, -9, 20, 18]]); // 자기 <text>의 (x=50, y-4=0)을 담는 상자

  const throughOthers = edge("M 0 0 L 100 0") + edge("M 500 500 L 501 500", { x: 50, y: 4, text: "B" }) + labelBox;
  assert.equal(edgesThroughText(throughOthers).length, 1);

  const throughOwn = edge("M 0 0 L 100 0", { x: 50, y: 4, text: "A" }) + labelBox;
  assert.equal(edgesThroughText(throughOwn).length, 0);

  const throughTitle = edge("M 0 10 L 200 10") + container("grp", 50, 0, 100, 30, "묶음");
  assert.equal(edgesThroughText(throughTitle).length, 1);
});

test("labelCollisions: a label overlapping a leaf shape is reported, a far label is not, two overlapping labels are reported", () => {
  const onShape = leaf("ours", '<rect x="0" y="0" width="60" height="40" />') + mask([[10, 10, 20, 20]]);
  assert.equal(labelCollisions(onShape).length, 1);

  const farAway = leaf("ours", '<rect x="0" y="0" width="60" height="40" />') + mask([[500, 500, 20, 20]]);
  assert.equal(labelCollisions(farAway).length, 0);

  const twoLabels = mask([[0, 0, 30, 20], [15, 5, 30, 20]]);
  assert.equal(labelCollisions(twoLabels).length, 1);
});

test("diagonalEdges: a diagonal segment is reported, an axis-aligned bend is not, a short diagonal jog is not", () => {
  assert.equal(diagonalEdges(edge("M 0 0 L 100 50")).length, 1);
  assert.equal(diagonalEdges(edge("M 0 0 L 100 0 L 100 50")).length, 0);
  assert.equal(diagonalEdges(edge("M 0 0 L 8 6")).length, 0); // 길이 10px, 상한 12px 밑
});
