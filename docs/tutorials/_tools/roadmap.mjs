#!/usr/bin/env node
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { loadDays, folderName, pad3, PLACEHOLDER, TUTORIALS_DIR, TOOLS_DIR } from "./lib/days.mjs";

export function isDayDone(day, root) {
  const readme = join(root, folderName(day), "README.md");
  return existsSync(readme) && !readFileSync(readme, "utf8").includes(PLACEHOLDER);
}

export function renderRoadmap(days, root, template) {
  const done = days.filter((d) => isDayDone(d, root)).length;
  let out = `진도: ${done} / ${days.length}일 완료\n`;
  let vol = 0;
  for (const d of days) {
    if (d.vol !== vol) {
      vol = d.vol;
      const inVol = days.filter((x) => x.vol === vol);
      out += `\n### 볼륨 ${vol}. ${d.volLabel} (Day ${inVol[0].day}–${inVol[inVol.length - 1].day}, ${inVol.length}일)\n\n`;
      out += "| 완료 | 일차 | 앱 | 원본 앱 |\n|---|---|---|---|\n";
    }
    const folder = folderName(d);
    const exists = existsSync(join(root, folder, "README.md"));
    const dayCell = exists ? `[Day ${pad3(d.day)}](${folder}/README.md)` : `Day ${pad3(d.day)}`;
    out += `| ${isDayDone(d, root) ? "✅" : "⬜"} | ${dayCell} | ${d.title} | [${d.path}](../../${d.path}/) |\n`;
  }
  return template.replace("<!-- DAYS -->", out);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const template = readFileSync(join(TOOLS_DIR, "roadmap.template.md"), "utf8");
  const target = join(TUTORIALS_DIR, "README.md");
  writeFileSync(target, renderRoadmap(loadDays(), TUTORIALS_DIR, template));
  console.log(`wrote ${target}`);
}
