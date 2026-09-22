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

/** 노드의 경계상자 목록. 컨테이너(다른 노드를 품는 것)는 빼고 잎만 돌려준다. */
export function leafBoxes(svg) {
  const boxes = [];
  const re = /<g class="[A-Za-z0-9+/=]+ [\w-]+">\s*<g class="shape"\s*>\s*(<(?:rect|ellipse|path|polygon)[^>]*>)/g;
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
    if (h > maxHeight || tooWide) out.push({ kind, width: w, height: h });
  }
  return out;
}
