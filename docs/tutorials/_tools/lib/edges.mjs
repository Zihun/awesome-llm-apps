// 연결선이 남의 도형을 가로지르는지 본다.
//
// 왜 필요한가: `grid-rows`/`grid-columns`는 엣지를 보지 않고 자리를 정하고, D2는 그
// 위에 **꺾임 없는 직선**을 긋는다. 그래서 그리드 안에서 멀리 떨어진 두 칸을 잇는 순간
// 그 사이에 있는 상자를 그대로 관통한다. ELK 배치는 돌아가게 경로를 잡지만 같은 내용이
// 두 배 이상 길어진다(2026-09-23 측정: Day 005 overview가 943x662 → 1083x1479).
//
// 실제로 통하는 해법은 세 번째다 — **엣지를 컨테이너 수준으로 올린다**. 자식 하나하나를
// 가리키는 대신 묶음끼리 잇는다. 같은 그림이 1137x440이 되면서 교차가 6건에서 0건으로
// 사라졌다. 개요도는 어차피 구조를 그리는 자리이므로 이 편이 내용에도 맞는다.
//
// 판정: 어떤 선분의 내부 점이 "이 엣지의 출발/도착이 아닌 잎 도형" 안에 들어가면 교차다.
// 컨테이너는 장애물이 아니다 — 자식을 품는 것이 컨테이너의 일이다.

const NUM = "[-+]?[0-9]*\\.?[0-9]+";

/** SVG의 도형 요소 하나에서 경계상자를 뽑는다. 베지에 제어점은 곡선을 감싸므로 안전한 과대추정이다. */
function boxOf(tag) {
  const num = (name) => {
    const m = tag.match(new RegExp(`\\s${name}="(${NUM})"`));
    return m ? Number(m[1]) : null;
  };
  if (tag.startsWith("<rect")) {
    const [x, y, w, h] = ["x", "y", "width", "height"].map(num);
    if ([x, y, w, h].some((v) => v === null)) return null;
    return { x1: x, y1: y, x2: x + w, y2: y + h };
  }
  if (tag.startsWith("<ellipse")) {
    const [cx, cy, rx, ry] = ["cx", "cy", "rx", "ry"].map(num);
    if ([cx, cy, rx, ry].some((v) => v === null)) return null;
    return { x1: cx - rx, y1: cy - ry, x2: cx + rx, y2: cy + ry };
  }
  const coords = tag.match(/\s(?:d|points)="([^"]+)"/);
  if (!coords) return null;
  const pts = tag.startsWith("<polygon") ? pairsOf(coords[1]) : pathPoints(coords[1]);
  if (pts.length < 2) return null;
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  return { x1: Math.min(...xs), y1: Math.min(...ys), x2: Math.max(...xs), y2: Math.max(...ys) };
}

function pairsOf(text) {
  const n = text.match(new RegExp(NUM, "g"))?.map(Number) ?? [];
  const out = [];
  for (let i = 0; i + 1 < n.length; i += 2) out.push([n[i], n[i + 1]]);
  return out;
}

/** path의 `d`를 명령별 인자 개수를 지켜 읽는다.
 *  `H 336`처럼 좌표를 하나만 받는 명령이 있어, 숫자를 무작정 쌍으로 묶으면 좌표가 밀려
 *  경계상자가 터무니없이 커진다 — 실제로 921px 그림 안에서 1280px짜리 구름이 나왔다.
 *  베지에 제어점은 곡선을 감싸므로 그대로 써도 안전한 과대추정이다. */
export function pathPoints(d) {
  const tokens = d.match(new RegExp(`[A-Za-z]|${NUM}`, "g")) ?? [];
  const arity = { M: 2, L: 2, T: 2, H: 1, V: 1, C: 6, S: 4, Q: 4, A: 7, Z: 0 };
  const pts = [];
  let cur = [0, 0];
  let cmd = "M";
  let i = 0;
  while (i < tokens.length) {
    if (/[A-Za-z]/.test(tokens[i])) { cmd = tokens[i]; i++; }
    const up = cmd.toUpperCase();
    const rel = cmd !== up;
    const n = arity[up];
    if (n === undefined) { i++; continue; }
    if (n === 0) continue;
    const args = tokens.slice(i, i + n).map(Number);
    if (args.length < n || args.some(Number.isNaN)) break;
    i += n;
    if (up === "H") cur = [rel ? cur[0] + args[0] : args[0], cur[1]];
    else if (up === "V") cur = [cur[0], rel ? cur[1] + args[0] : args[0]];
    else if (up === "A") cur = rel ? [cur[0] + args[5], cur[1] + args[6]] : [args[5], args[6]];
    else {
      for (let k = 0; k + 1 < n; k += 2) {
        const p = rel ? [cur[0] + args[k], cur[1] + args[k + 1]] : [args[k], args[k + 1]];
        pts.push(p);
      }
      cur = pts[pts.length - 1] ?? cur;
    }
    pts.push(cur);
  }
  return pts;
}

/** 노드의 경계상자 목록. 컨테이너(다른 노드를 품는 것)는 빼고 잎만 돌려준다.
 *  클래스는 있을 수도 없을 수도 있다(D2는 클래스 없는 노드를 <g class="BASE64ID">로만
 *  쓴다 — 2026-09-23 검사 20~23 작업 중 P1 검증 SVG에서 확인: class 없는 잎을 컨테이너로
 *  오인해 라벨-도형 겹침을 놓쳤다). 실제 일차는 잎마다 항상 클래스를 붙이므로(person·ours·
 *  ext·store·file) 이 완화가 실전 결과를 바꾸지 않는다 — 컨테이너는 자식을 갖고, 자식을
 *  가지면 아래 contains 필터가 어차피 걸러낸다. */
export function leafBoxes(svg) {
  const boxes = [];
  const re = /<g class="[A-Za-z0-9+/=]+(?: [\w-]+)?">\s*<g class="shape"\s*>\s*(<(?:rect|ellipse|path|polygon)[^>]*>)/g;
  for (const m of svg.matchAll(re)) {
    const b = boxOf(m[1]);
    if (b) boxes.push(b);
  }
  const contains = (a, b) => a !== b && a.x1 <= b.x1 && a.y1 <= b.y1 && a.x2 >= b.x2 && a.y2 >= b.y2;
  return boxes.filter((b) => !boxes.some((o) => contains(b, o)));
}

/** 연결선 하나를 점의 나열로 바꾼다. */
function polyline(d) {
  const pts = [];
  for (const m of d.matchAll(new RegExp(`([ML])\\s*(${NUM})[ ,]+(${NUM})`, "g"))) {
    pts.push([Number(m[2]), Number(m[3])]);
  }
  return pts;
}

export function connectionPaths(svg) {
  return [...svg.matchAll(/<path d="([^"]+)"[^>]*class="connection/g)].map((m) => m[1]);
}

const PAD = 3; // 테두리를 스치는 것은 교차로 치지 않는다
const near = (p, b) => b.x1 - 4 < p[0] && p[0] < b.x2 + 4 && b.y1 - 4 < p[1] && p[1] < b.y2 + 4;
const inside = (x, y, b) => b.x1 + PAD < x && x < b.x2 - PAD && b.y1 + PAD < y && y < b.y2 - PAD;

/** 남의 도형을 가로지르는 선분 수. */
export function edgeCrossings(svg) {
  const leaves = leafBoxes(svg);
  if (!leaves.length) return 0;
  let crossings = 0;
  for (const d of connectionPaths(svg)) {
    const pts = polyline(d);
    if (pts.length < 2) continue;
    const ends = [pts[0], pts[pts.length - 1]];
    const own = leaves.filter((b) => ends.some((p) => near(p, b)));
    for (let i = 0; i < pts.length - 1; i++) {
      const [x1, y1] = pts[i];
      const [x2, y2] = pts[i + 1];
      let hit = false;
      for (let s = 4; s <= 36 && !hit; s++) {
        const t = s / 40;
        const x = x1 + (x2 - x1) * t;
        const y = y1 + (y2 - y1) * t;
        hit = leaves.some((b) => !own.includes(b) && inside(x, y, b));
      }
      if (hit) crossings++;
    }
  }
  return crossings;
}

/** 아이콘 도형의 자연 크기 상한.
 *
 *  그리드는 칸 크기를 줄맞춤하고, 종횡비를 지키는 도형은 칸을 채우려고 늘어난다. 늘어남은
 *  두 방향으로 나타난다 — Day 031의 사람은 761x761로 **정사각형인 채 거대해졌고**, Day 045의
 *  사람은 643x64로 **그림 폭을 가로질러 납작해졌다**. 둘 다 같은 원인이고 둘 다 막아야 한다.
 *
 *  다만 도형마다 자연스러운 모양이 다르다. 사람은 대체로 정사각형이다(정상값 64x63). 구름·
 *  원통·문서는 라벨을 담느라 옆으로 넓어지는 것이 정상이어서(예: 358x79) 폭을 재면 멀쩡한
 *  것까지 걸린다. 그래서 **사람만 폭과 높이를 함께 보고, 나머지는 높이만 본다.**
 *  (2026-09-23: 처음에는 높이만 봤다가 Day 045의 643x64를 놓쳤다.) */
export const ICON_MAX_HEIGHT = 200;
export const PERSON_MAX_WIDTH = 200;

const ICON_RE =
  /<g class="[A-Za-z0-9+/=]+ ((?:person|ext|store|file)[\w-]*)">\s*<g class="shape"\s*>\s*(<(?:path|polygon)[^>]*>)/g;

export function stretchedIcons(svg, maxHeight = ICON_MAX_HEIGHT) {
  const out = [];
  for (const m of svg.matchAll(ICON_RE)) {
    const b = boxOf(m[2]);
    if (!b) continue;
    const kind = m[1].split("-")[0];
    const w = Math.round(b.x2 - b.x1);
    const h = Math.round(b.y2 - b.y1);
    const tooWide = kind === "person" && w > PERSON_MAX_WIDTH;
    const tooTall = h > maxHeight;
    if (tooTall || tooWide) out.push({ kind, width: w, height: h, tooWide, tooTall });
  }
  return out;
}

// 화살표 규칙(검사 20~23) — 2026-09-23 사용자 지시: 화살표가 서로 겹치거나 글자에
// 걸치면 안 되고, 곧게 그어서 그렇게 안 되면 꺾어야 한다. grid로 자리를 정한 층은 D2가
// 칸 중심끼리 직선만 긋고 경로를 잡지 않으므로(§5), 네 검사 모두 걸리면 처방은 대개
// "그 층을 ELK에 맡겨라"다. 실측(overview 57장): 화살표 382개 중 꺾인 것 3개, 비스듬한
// 선 241개, 53장이 아래 네 검사 중 하나 이상에 걸린다. 같은 57장 중 5장을 ELK로만
// 배치하자 넷 다 0이 됐다(레이아웃만 바꾸고 좌표는 손대지 않은 값 — 검증 근거).

const decodeEntities = (s) =>
  s.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#34;/g, '"').replace(/&#39;/g, "'");

/** 글자 하나의 대략적인 폭(px, 12px 글자 기준). 묶음 제목은 잎과 달리 <mask> 상자가
 *  없으므로(마스크는 연결선 라벨만 가린다) 글자 수로 폭을 추정하는 수밖에 없다. */
function charWidth(ch) {
  if (/[ㄱ-힣一-鿿]/.test(ch)) return 12; // 한글·CJK
  if (ch === " ") return 3.2;
  if (/[()·,.:|/_-]/.test(ch)) return 4;
  if (/[A-Z]/.test(ch)) return 7.8;
  return 6.6; // 그 밖의 라틴·숫자
}
const textWidth = (text) => [...text].reduce((sum, ch) => sum + charWidth(ch), 0);

/** 연결선 하나를 점의 나열(0.5px 이내로 붙은 점은 합친다)과 자기 라벨로 바꾼다.
 *  라벨이 있으면 path 바로 뒤 <text x=… y=…>가 자기 것이다(그 사이에 다른 원소가 오지
 *  않는다 — 실제 D2 마크업 확인). */
function connectionsOf(svg) {
  const re = /<path d="([^"]+)"[^>]*class="connection[^"]*"[^>]*\/>\s*(?:<text x="([^"]+)" y="([^"]+)"[^>]*>([^<]*)<\/text>)?/g;
  const out = [];
  for (const m of svg.matchAll(re)) {
    const raw = pathPoints(m[1]);
    const pts = raw.filter((p, i) => i === 0 || Math.hypot(p[0] - raw[i - 1][0], p[1] - raw[i - 1][1]) > 0.5);
    const label = m[2] !== undefined ? { x: Number(m[2]), y: Number(m[3]), text: decodeEntities(m[4]) } : null;
    out.push({ pts, label });
  }
  return out;
}

const segmentsOf = (pts) => pts.slice(1).map((p, i) => [pts[i], p]);

/** <mask> 안 fill="black" 사각형 = 연결선 라벨 상자. D2 여백이 섞여 있어(실측: 글자 폭
 *  63px "질문 텍스트"의 상자가 82px) 좌우 6px·상하 3px씩 안쪽으로 줄인다. */
function labelBoxesOf(svg) {
  const out = [];
  for (const block of svg.matchAll(/<mask[^>]*>[\s\S]*?<\/mask>/g)) {
    for (const m of block[0].matchAll(/<rect x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)" fill="black"/g)) {
      const [x, y, w, h] = [m[1], m[2], m[3], m[4]].map(Number);
      out.push({ x1: x + 6, y1: y + 3, x2: x + w - 6, y2: y + h - 3 });
    }
  }
  return out;
}

/** 잎이 아닌 도형(자식을 품는 컨테이너)의 제목 상자. 구조는 잎과 똑같다(도형 뒤에 바로
 *  제목 <text>가 온다) — 그래서 leafBoxes에 없는 것만 컨테이너로 남긴다. */
function containerTitleBoxes(svg) {
  const leaves = leafBoxes(svg);
  const isLeaf = (b) =>
    leaves.some((o) => Math.abs(o.x1 - b.x1) < 0.5 && Math.abs(o.y1 - b.y1) < 0.5 && Math.abs(o.x2 - b.x2) < 0.5 && Math.abs(o.y2 - b.y2) < 0.5);
  const re =
    /<g class="[A-Za-z0-9+/=]+(?: [\w-]+)?">\s*<g class="shape"\s*>\s*(<(?:rect|ellipse|path|polygon)[^>]*>)\s*<\/g>\s*<text x="([^"]+)" y="([^"]+)"[^>]*>([^<]*)<\/text>/g;
  const out = [];
  for (const m of svg.matchAll(re)) {
    const box = boxOf(m[1]);
    if (!box || isLeaf(box)) continue;
    const cx = Number(m[2]);
    const baseline = Number(m[3]);
    const w = textWidth(decodeEntities(m[4]));
    out.push({ x1: cx - w / 2, x2: cx + w / 2, y1: baseline - 12, y2: baseline + 4 });
  }
  return out;
}

/** 라벨이 속한 상자를 찾는다: 그 <text>의 (x, y-4)를 담는 상자. 줄인 상자 그대로 대면
 *  반올림에 걸려 자기 라벨을 "남의 것"으로 오판할 수 있어 살짝 넉넉하게(좌우 7px·
 *  상하 4px) 잡는다 — 이 여유는 소유권 판정에만 쓰고, 다른 라벨과의 충돌 판정에는
 *  줄인 상자를 그대로 쓴다. */
function ownLabelBox(label, labelBoxes) {
  if (!label) return null;
  const px = label.x;
  const py = label.y - 4;
  return labelBoxes.find((b) => b.x1 - 7 < px && px < b.x2 + 7 && b.y1 - 4 < py && py < b.y2 + 4) ?? null;
}

/** 점이 상자 경계에서 pad px 안쪽에 있는지. 테두리를 스치는 것은 침범으로 치지 않는다. */
const insideBy = (x, y, b, pad) => b.x1 + pad < x && x < b.x2 - pad && b.y1 + pad < y && y < b.y2 - pad;

/** 두 상자가 겹치는지(면적이 0보다 큰지만 본다 — 스치는 것은 겹침이 아니다). */
const boxesOverlap = (a, b) => Math.min(a.x2, b.x2) > Math.max(a.x1, b.x1) && Math.min(a.y2, b.y2) > Math.max(a.y1, b.y1);

/** 두 선분이 같은 직선 위에서 겹치는 길이. seg1의 직선을 기준으로 seg2의 양 끝점이
 *  2px 이내에 있어야("같은 선") 겹침을 잰다 — 그냥 교차하는 선(예: 수직으로 만나는 것)은
 *  한쪽 끝이 반드시 멀리 떨어지므로 걸리지 않는다. */
function collinearOverlap([a, b], [c, d]) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len = Math.hypot(dx, dy);
  if (len < 1) return 0;
  const dist = (p) => Math.abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / len;
  if (dist(c) > 2 || dist(d) > 2) return 0;
  const t = (p) => ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len;
  const lo = Math.max(0, Math.min(t(c), t(d)));
  const hi = Math.min(len, Math.max(t(c), t(d)));
  return Math.max(0, hi - lo);
}

/** 20. 서로 다른 두 연결선이 같은 직선 위에서 8px 넘게 겹치는 곳. */
export function edgeOverlaps(svg) {
  const edges = connectionsOf(svg);
  const out = [];
  for (let i = 0; i < edges.length; i++) {
    const segsA = segmentsOf(edges[i].pts);
    for (let j = i + 1; j < edges.length; j++) {
      const segsB = segmentsOf(edges[j].pts);
      let overlap = 0;
      for (const s of segsA) for (const t of segsB) overlap = Math.max(overlap, collinearOverlap(s, t));
      if (overlap > 8) out.push({ a: i, b: j, overlap: Math.round(overlap) });
    }
  }
  return out;
}

/** 21. 선분이 남의 라벨이나 묶음 제목 위를 지나는 곳(경계에서 2px 안쪽). sequence의
 *  수명선도 연결선 path라서 저절로 걸린다 — 라벨이 없으니 모든 라벨이 "남의 것"이다. */
export function edgesThroughText(svg) {
  const edges = connectionsOf(svg);
  const labels = labelBoxesOf(svg);
  const titles = containerTitleBoxes(svg);
  const out = [];
  for (const e of edges) {
    const mine = ownLabelBox(e.label, labels);
    const others = labels.filter((b) => b !== mine).concat(titles);
    if (!others.length) continue;
    const hit = segmentsOf(e.pts).some(([p, q]) =>
      others.some((b) => {
        for (let s = 1; s < 40; s++) {
          const t = s / 40;
          if (insideBy(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, b, 2)) return true;
        }
        return false;
      })
    );
    if (hit) out.push({ label: e.label?.text ?? null });
  }
  return out;
}

/** 22. 줄인 라벨 상자가 잎 도형과 겹치거나(화살표가 라벨보다 짧아 라벨이 넘친 것),
 *  줄인 라벨 상자 둘이 서로 겹치는 곳. */
export function labelCollisions(svg) {
  const labels = labelBoxesOf(svg);
  const leaves = leafBoxes(svg);
  const out = [];
  for (const label of labels) {
    if (leaves.some((leaf) => boxesOverlap(label, leaf))) out.push({ type: "shape" });
  }
  for (let i = 0; i < labels.length; i++) {
    for (let j = i + 1; j < labels.length; j++) {
      if (boxesOverlap(labels[i], labels[j])) out.push({ type: "label" });
    }
  }
  return out;
}

/** 23. 길이 12px 넘는 선분 중 가로·세로 변화가 둘 다 1.5px를 넘는 것(비스듬한 선).
 *  호출하는 쪽(check.mjs)이 sequence 그림에는 이 검사를 적용하지 않는다. */
export function diagonalEdges(svg) {
  const out = [];
  for (const e of connectionsOf(svg)) {
    for (const [p, q] of segmentsOf(e.pts)) {
      const dx = Math.abs(q[0] - p[0]);
      const dy = Math.abs(q[1] - p[1]);
      if (dx > 1.5 && dy > 1.5 && Math.hypot(q[0] - p[0], q[1] - p[1]) > 12) {
        out.push({ dx: Math.round(dx), dy: Math.round(dy) });
      }
    }
  }
  return out;
}
