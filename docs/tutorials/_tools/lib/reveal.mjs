import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

// 검사 19 — 단계 공개 불변식.
//
// 왜 필요한가: step<N>.d2는 `...@overview`로 배치를 그대로 가져와 클래스만 덧씌운다
// (§5). 덧씌우는 경로를 잘못 짚으면(overview에 없는 하위 경로에 대입하면) D2가 그 경로를
// 새 최상위 노드로 만들어 버리는데, 렌더된 그림만 보면 "그림이 커졌다"만 보이고 원인은
// 안 보인다(2026-09-22에 실제로 이렇게 그림이 커졌다). 노드 집합을 overview와 맞대 보면
// 이 실수를 바로 잡아낸다. 나머지 세 불변식은 "공개가 다시 흐려짐", "마지막 단계에
// 미완성 표시가 남는 것", "흐렸던 노드가 -new를 거치지 않고 곧장 평상으로 나타나는 것"을
// 막는다 — 마지막 것은 리뷰가 찾은 결함으로, 독자가 그 부품이 어느 단계에서 붙었는지 볼 수
// 없게 만든다(2026-09-23, 5일에서 5건: 012·013·019·020·023). 평상 -> -new 재강조는
// 반대로 막지 않는다 — 그쪽을 막는 불변식을 넣었더니 49일 중 31일이 걸렸는데, 결함이
// 아니라 흔한 관행이었다(2026-09-23 확인). 그래서 이번 조건은 "흐림 -> 평상 직행"
// 한쪽만 좁게 잡는다.
//
// 렌더된 SVG에서 읽는다 — 검사 3이 이미 SVG가 소스와 맞는지(안 낡았는지) 보장하므로
// 여기서는 다시 확인하지 않는다.

// 노드 그룹은 <g class="BASE64ID CLASS"> 또는 클래스가 없으면 <g class="BASE64ID">이고
// 바로 안에 <g class="shape">가 온다. 연결선 그룹은 이 모양이 아니다(안에 shape가 없다) —
// 그래서 이 정규식 자체가 연결선을 걸러낸다. id가 "("로 시작하면(예: "(a -> b)[0]") 그래도
// 한 번 더 건너뛴다.
const NODE_RE = /<g class="([A-Za-z0-9+/=]+)(?: ([\w-]+))?">\s*<g class="shape"/g;

/** 렌더된 SVG 하나에서 노드 id → class 맵을 뽑는다(연결선 그룹은 제외). */
function nodesOf(svgText) {
  const nodes = new Map();
  for (const m of svgText.matchAll(NODE_RE)) {
    const id = Buffer.from(m[1], "base64").toString("utf8");
    if (id.startsWith("(")) continue; // 연결선 그룹의 id는 "(a -> b)[0]" 꼴
    nodes.set(id, m[2] ?? "");
  }
  return nodes;
}

const isTodo = (cls) => cls.endsWith("-todo");
const isNew = (cls) => cls.endsWith("-new");

/** "step12.svg" -> "12". sortedStepFiles가 이미 이 모양만 골라 두므로 항상 잡힌다. */
const stepNumber = (file) => file.match(/^step(\d+)\.svg$/)[1];

/** diagrams/ 안의 step<N>.svg를 N 순서로 정렬해 돌려준다. sequence*, extra-*는 대상이 아니다. */
function sortedStepFiles(diagramsDir) {
  return readdirSync(diagramsDir)
    .map((f) => ({ f, n: Number(f.match(/^step(\d+)\.svg$/)?.[1]) }))
    .filter((x) => !Number.isNaN(x.n))
    .sort((a, b) => a.n - b.n)
    .map((x) => x.f);
}

/** 한 일차의 diagrams/를 단계 공개 불변식 넷으로 검사한다.
 *  1. 모든 stepN의 노드 id 집합이 overview의 집합과 같다.
 *  2. class가 "-todo"로 끝나는 노드 수가 step k → k+1에서 늘지 않는다.
 *  3. 마지막 step에 "-todo" 노드가 없다.
 *  4. step k에서 "-todo"였던 노드가 step k+1에서 "-todo"를 벗어나면 "-new"로 끝나야
 *     한다 — 처음 드러나는 단계는 주황으로. (평상 → "-new" 재강조는 관례이므로 허용.)
 *  step 파일이 없으면(아직 stepK.d2를 안 썼거나 overview뿐인 일차) 문제 없음. */
export function revealProblems(diagramsDir) {
  const problems = [];
  const overviewPath = join(diagramsDir, "overview.svg");
  if (!existsSync(overviewPath)) return problems;
  const overviewIds = new Set(nodesOf(readFileSync(overviewPath, "utf8")).keys());

  const stepFiles = sortedStepFiles(diagramsDir);
  if (!stepFiles.length) return problems;

  let prevFile = null;
  let prevTodoCount = null;
  let prevNodes = null;
  let lastFile = null;
  let lastNodes = null;

  for (const file of stepFiles) {
    const nodes = nodesOf(readFileSync(join(diagramsDir, file), "utf8"));
    const ids = new Set(nodes.keys());

    for (const id of ids) {
      if (!overviewIds.has(id)) {
        problems.push(`diagrams/${file}: overview에 없는 노드 "${id}" — step이 overview에 없는 경로를 덮어써 D2가 새 최상위 노드를 만들었습니다`);
      }
    }
    for (const id of overviewIds) {
      if (!ids.has(id)) {
        problems.push(`diagrams/${file}: overview에 있는 노드 "${id}"가 빠졌습니다`);
      }
    }

    const todoCount = [...nodes.values()].filter(isTodo).length;
    if (prevTodoCount !== null && todoCount > prevTodoCount) {
      problems.push(`diagrams/${file}: -todo 노드가 ${prevFile}보다 늘었습니다 (${prevTodoCount}개 → ${todoCount}개) — 한 번 공개된 것을 다시 흐리지 마세요`);
    }

    if (prevNodes) {
      for (const [id, cls] of nodes) {
        const prevCls = prevNodes.get(id);
        if (prevCls !== undefined && isTodo(prevCls) && !isTodo(cls) && !isNew(cls)) {
          problems.push(`diagrams/${file}: "${id}"가 step${stepNumber(prevFile)}에서 흐렸다가 주황(-new) 없이 바로 평상으로 나타납니다 — 처음 드러나는 단계에서는 -new로 표시하세요`);
        }
      }
    }

    prevFile = file;
    prevTodoCount = todoCount;
    prevNodes = nodes;
    lastFile = file;
    lastNodes = nodes;
  }

  const leftoverTodo = [...lastNodes.entries()].filter(([, cls]) => isTodo(cls)).map(([id]) => id);
  if (leftoverTodo.length) {
    problems.push(`diagrams/${lastFile}: 마지막 단계인데 -todo 노드가 남아 있습니다: ${leftoverTodo.join(", ")}`);
  }

  return problems;
}
