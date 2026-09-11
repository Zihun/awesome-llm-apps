#!/usr/bin/env node
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { loadDays, folderName, pad3, PLACEHOLDER, TUTORIALS_DIR } from "./lib/days.mjs";

export function readmeSkeleton(day, nextDay) {
  const next = nextDay
    ? `[Day ${pad3(nextDay.day)} · ${nextDay.title}](../${folderName(nextDay)}/README.md) — ${PLACEHOLDER}`
    : "여기가 시리즈의 마지막 날입니다.";
  return `# Day ${pad3(day.day)} · ${day.title}

> 볼륨 ${day.vol} ${day.volLabel} · 난이도 ★☆☆ · 예상 소요 60분 · API 비용 대략 ${PLACEHOLDER} · 원본 앱: \`${day.path}\`

## 오늘 만들 것

${PLACEHOLDER}

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| ${PLACEHOLDER} | | |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| ${PLACEHOLDER} | | |

## 단계별 진행

### Step 1. ${PLACEHOLDER}

**목적.** ${PLACEHOLDER}

**할 일.** ${PLACEHOLDER}

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** ${PLACEHOLDER}

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

${PLACEHOLDER}

## 실행 체크리스트

- [ ] ${PLACEHOLDER}

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| ${PLACEHOLDER} | | |

## 더 해보기

- ${PLACEHOLDER}

## 다음 날 예고

${next}
`;
}

export function scaffoldDay(dayNumber, { days = loadDays(), root = TUTORIALS_DIR } = {}) {
  const day = days.find((d) => d.day === dayNumber);
  if (!day) throw new Error(`no such day: ${dayNumber}`);
  const dir = join(root, folderName(day));
  if (existsSync(dir)) throw new Error(`already exists: ${dir}`);
  mkdirSync(join(dir, "diagrams"), { recursive: true });
  writeFileSync(join(dir, "README.md"), readmeSkeleton(day, days.find((d) => d.day === dayNumber + 1)));
  return dir;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const n = Number.parseInt(process.argv[2], 10);
  if (!n) { console.error("usage: node scaffold.mjs <day number>"); process.exit(2); }
  console.log(scaffoldDay(n));
}
