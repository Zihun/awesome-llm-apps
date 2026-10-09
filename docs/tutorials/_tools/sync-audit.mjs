#!/usr/bin/env node
// upstream 동기화 뒤에 튜토리얼이 손볼 곳을 찾는다. 절차는 루트 UPSTREAM_SYNC.md.
//
// 두 가지를 본다.
//   1. 계획 — 상위 README가 링크하는 로컬 앱과 days.json이 서로 맞는가. 빠진 앱, 디스크에서 사라진 경로.
//   2. 작성된 일차 — 기준 커밋 이후 바뀐 파일이 그 일차의 원본 앱 안에 있거나, 그 일차가 인용한 경로인가.
//
// 기준 커밋은 동기화 직전의 main이다. 병합 커밋 바로 위에서 돌리면 기본값 HEAD^1이 그것이다.
//
//   npm run sync-audit                # 기준 = HEAD^1
//   npm run sync-audit -- 2ccfeef     # 기준을 직접 준다
//
// 찾은 것이 있으면 exit 1. 찾은 것이 곧 고칠 것은 아니다 — 원장에 판단을 남기고 넘어가도 된다.
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { join, posix, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { loadDays, folderName, REPO_ROOT, TUTORIALS_DIR } from "./lib/days.mjs";
import { isDayDone } from "./roadmap.mjs";

/** 상위 README가 링크하는 로컬 앱 폴더. 외부 링크, 파일 링크, docs/ 아래(배너 등)는 뺀다. */
export function readmeAppLinks(readme) {
  const out = new Set();
  for (const m of readme.matchAll(/\]\(([^)\s#]+)\)/g)) {
    const p = m[1].replace(/^\.\//, "").replace(/\/$/, "");
    if (/^[a-z]+:/i.test(p) || p.startsWith("docs/") || /\.[a-z0-9]+$/i.test(p)) continue;
    out.add(p);
  }
  return [...out];
}

/** README 링크와 days.json의 차이. 링크가 일차 경로의 상위 폴더면(크래시 코스) 계획에 있는 것으로 본다. */
export function planGaps(days, links, exists) {
  const paths = days.map((d) => d.path);
  return {
    notInPlan: links.filter((l) => !paths.some((p) => p === l || p.startsWith(l + "/"))),
    missingOnDisk: paths.filter((p) => !exists(p)),
  };
}

/** 일차 README가 리포 경로로 인용한 것들. 백틱 안의 `경로/파일:줄`과, 리포 안을 가리키는 상대 링크. 다른 일차 문서는 뺀다. */
export function citedPaths(md, dayDirFromRoot) {
  const out = new Set();
  const add = (p) => {
    if (!p.startsWith("..") && !p.startsWith("docs/tutorials/")) out.add(p);
  };
  for (const m of md.matchAll(/`([A-Za-z0-9_.-]+(?:\/[A-Za-z0-9_.-]+)+)(?::\d+(?:-\d+)?)?`/g)) add(m[1]);
  for (const m of md.matchAll(/\]\(((?:\.\.\/)+[^)\s#]+)\)/g)) {
    add(posix.normalize(posix.join(dayDirFromRoot, m[1])).replace(/\/$/, ""));
  }
  return [...out];
}

const touches = (path, changed) => changed.filter((c) => c === path || c.startsWith(path + "/"));

/** 작성된 일차마다, 원본 앱 안에서 바뀐 파일과 인용한 경로 중 바뀐 것. 둘 다 없으면 빠진다.
 *  앱 폴더 여럿을 품은 분류 폴더(예: `advanced_ai_agents/multi_agent_apps`)를 인용한 것은 세지 않는다 —
 *  그 아래 다른 앱의 변경이 모두 그 날에 걸리는 오탐이 된다(2026-10-10, Day 084). */
export function affectedDays(written, changed, appPaths = []) {
  const isCategory = (p) => appPaths.some((a) => a.startsWith(p + "/"));
  const out = [];
  for (const { day, md, dayDirFromRoot } of written) {
    const inApp = touches(day.path, changed);
    const cited = citedPaths(md, dayDirFromRoot)
      .filter((p) => p !== day.path && !p.startsWith(day.path + "/") && !isCategory(p))
      .flatMap((p) => touches(p, changed));
    if (inApp.length || cited.length) out.push({ day, inApp, cited: [...new Set(cited)] });
  }
  return out;
}

const git = (...args) => execFileSync("git", args, { cwd: REPO_ROOT, encoding: "utf8" }).trim();

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const base = process.argv[2] ?? "HEAD^1";
  const range = `${git("rev-parse", "--short", base)}..${git("rev-parse", "--short", "HEAD")}`;
  const changed = git("diff", "--name-only", base, "HEAD").split("\n").filter(Boolean);
  const days = loadDays();
  let findings = 0;

  console.log(`기준 ${range} · 바뀐 파일 ${changed.length}개\n`);

  const links = readmeAppLinks(readFileSync(join(REPO_ROOT, "README.md"), "utf8"));
  const { notInPlan, missingOnDisk } = planGaps(days, links, (p) => existsSync(join(REPO_ROOT, p)));
  console.log(`[계획] README 로컬 앱 링크 ${links.length}개 · days.json ${days.length}일`);
  for (const p of notInPlan) console.log(`  README에 있고 계획에 없음: ${p}`);
  for (const p of missingOnDisk) console.log(`  계획에 있고 디스크에 없음: ${p}`);
  findings += notInPlan.length + missingOnDisk.length;

  const written = days
    .filter((d) => isDayDone(d, TUTORIALS_DIR))
    .map((day) => {
      const dir = join(TUTORIALS_DIR, folderName(day));
      return { day, md: readFileSync(join(dir, "README.md"), "utf8"), dayDirFromRoot: relative(REPO_ROOT, dir).replaceAll("\\", "/") };
    });
  const hits = affectedDays(written, changed, days.map((d) => d.path));
  console.log(`\n[작성된 일차] ${written.length}일 중 영향 ${hits.length}일`);
  for (const { day, inApp, cited } of hits) {
    console.log(`  ${folderName(day)}`);
    for (const f of inApp) console.log(`    원본 앱에서 바뀜: ${f}`);
    for (const f of cited) console.log(`    인용한 경로가 바뀜: ${f}`);
  }
  findings += hits.length;

  console.log(findings ? `\nsync-audit: ${findings}건 확인 필요` : "\nsync-audit: 통과");
  process.exitCode = findings ? 1 : 0;
}
