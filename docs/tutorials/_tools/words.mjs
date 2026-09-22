#!/usr/bin/env node
// 본문 낱말 수와 "낱말/분"을 한 가지 방법으로 센다.
//
// 규격 §4는 잘 맞는 날이 분당 17~22낱말이라고 말하는데, 세는 방법을 정해 두지 않아
// 하루하루가 제각기 셌다. 같은 문서를 두고 1,997과 3,057이 함께 보고된 적도 있다.
// 기준이 되려면 방법이 하나여야 한다 — 그래서 여기서 못 박는다.
//
// 세지 않는 것: 코드 펜스, 인라인 코드, 제목, 표, 인용, 이미지, 체크리스트.
// 남는 것이 독자가 실제로 읽는 산문이고, 그것만 센다.
//
//   npm run words              # 작성된 모든 일차
//   npm run words -- day026    # 한 일차만
import { readFileSync, existsSync } from "node:fs";
import { join, resolve, basename } from "node:path";
import { fileURLToPath } from "node:url";
import { listDayDirs } from "./lib/check.mjs";
import { TUTORIALS_DIR } from "./lib/days.mjs";

export function proseWords(md) {
  const withoutFences = md.replace(/```[\s\S]*?```/g, "");
  const kept = withoutFences
    .split(/\r?\n/)
    .filter((line) => {
      const t = line.trimStart();
      if (t.startsWith("#") || t.startsWith("|") || t.startsWith(">") || t.startsWith("![")) return false;
      return !/^[-*]\s*\[/.test(t); // 체크리스트 항목
    })
    .join("\n");
  const text = kept.replace(/`[^`]*`/g, " ");
  const words = text.split(/\s+/).filter(Boolean);
  return words.length;
}

export function statedMinutes(md) {
  const m = md.match(/예상 소요\s*(\d+)\s*분/);
  return m ? Number(m[1]) : null;
}

/** 규격 §4가 말하는 밴드. 벗어나면 분량이나 시간 하나가 현실과 어긋난 것이다. */
export const BAND = { low: 17, high: 22 };

export function measure(dayDir) {
  const readme = join(dayDir, "README.md");
  if (!existsSync(readme)) return null;
  const md = readFileSync(readme, "utf8");
  const minutes = statedMinutes(md);
  if (minutes === null) return null;
  const words = proseWords(md);
  return { day: basename(dayDir).slice(0, 6), words, minutes, rate: words / minutes };
}

function main(argv) {
  const only = argv.find((a) => /^day\d{3}/.test(a));
  const rows = listDayDirs(TUTORIALS_DIR)
    .filter((d) => !only || basename(d).startsWith(only))
    .map(measure)
    .filter((r) => r && r.words > 200); // 아직 스캐폴드만 된 날은 건너뛴다
  if (!rows.length) return console.log("측정할 일차가 없습니다.");
  console.log("일차      낱말     분   낱말/분");
  for (const r of rows) {
    const off = r.rate < BAND.low || r.rate > BAND.high ? `  ← 밴드(${BAND.low}~${BAND.high}) 밖` : "";
    console.log(`${r.day}  ${String(r.words).padStart(6)} ${String(r.minutes).padStart(5)}  ${r.rate.toFixed(1).padStart(7)}${off}`);
  }
  const rates = rows.map((r) => r.rate).sort((a, b) => a - b);
  console.log(`\n${rows.length}일차 · 중앙값 ${rates[rates.length >> 1].toFixed(1)}낱말/분`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main(process.argv.slice(2));
