#!/usr/bin/env node
import { readdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { inlineImports, sourceHash, readSvgHash, embedHash, renderSource } from "./lib/d2.mjs";
import { TUTORIALS_DIR } from "./lib/days.mjs";

export function listD2Files(root, onlyDay) {
  const files = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory() || !/^day\d{3}-/.test(entry.name)) continue;
    if (onlyDay && !entry.name.startsWith(onlyDay)) continue;
    const dir = join(root, entry.name, "diagrams");
    if (!existsSync(dir)) continue;
    for (const f of readdirSync(dir)) if (f.endsWith(".d2")) files.push(join(dir, f));
  }
  return files.sort();
}

export async function renderFile(d2Path, { force = false } = {}) {
  const src = inlineImports(d2Path);
  const hash = sourceHash(src);
  const svgPath = d2Path.replace(/\.d2$/, ".svg");
  if (!force && existsSync(svgPath) && readSvgHash(readFileSync(svgPath, "utf8")) === hash) return "skipped";
  const svg = await renderSource(src);
  writeFileSync(svgPath, embedHash(svg, hash));
  return "rendered";
}

async function main(argv) {
  const force = argv.includes("--force");
  const onlyDay = argv.find((a) => /^day\d{3}/.test(a));
  const counts = { rendered: 0, skipped: 0, failed: 0 };
  for (const file of listD2Files(TUTORIALS_DIR, onlyDay)) {
    try {
      const result = await renderFile(file, { force });
      counts[result]++;
      console.log(`${result.padEnd(8)} ${file}`);
    } catch (err) {
      counts.failed++;
      console.error(`FAILED   ${file}\n  ${err.message}`);
    }
  }
  console.log(`rendered ${counts.rendered}, skipped ${counts.skipped}, failed ${counts.failed}`);
  process.exit(counts.failed ? 1 : 0); // D2의 ELK 워커가 이벤트 루프를 붙잡으므로 명시적으로 끝낸다
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main(process.argv.slice(2));
