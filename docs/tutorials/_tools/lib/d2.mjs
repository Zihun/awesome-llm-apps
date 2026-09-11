import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { D2 } from "@terrastruct/d2";

const IMPORT_RE = /^\.\.\.@(\S+)\s*$/;
const HASH_RE = /<!-- d2-source-sha256: ([0-9a-f]{64}) -->/;

export const RENDER_OPTIONS = { layout: "elk", sketch: false, pad: 20, noXMLTag: true };

/** `...@path` 줄을 해당 파일 내용으로 재귀 치환한다. 경로는 import하는 파일 기준 상대 경로, `.d2`는 생략 가능. */
export function inlineImports(filePath, seen = new Set()) {
  const abs = resolve(filePath);
  if (seen.has(abs)) throw new Error(`import cycle: ${abs}`);
  const next = new Set(seen).add(abs);
  return readFileSync(abs, "utf8")
    .split(/\r?\n/)
    .map((line) => {
      const m = line.match(IMPORT_RE);
      if (!m) return line;
      const target = resolve(dirname(abs), m[1].endsWith(".d2") ? m[1] : `${m[1]}.d2`);
      return inlineImports(target, next);
    })
    .join("\n");
}

export function sourceHash(src) {
  return createHash("sha256").update(src, "utf8").digest("hex");
}

export function readSvgHash(svgText) {
  const m = svgText.match(HASH_RE);
  return m ? m[1] : null;
}

export function embedHash(svg, hash) {
  const i = svg.lastIndexOf("</svg>");
  if (i < 0) throw new Error("renderer output has no </svg>");
  return `${svg.slice(0, i)}<!-- d2-source-sha256: ${hash} -->${svg.slice(i)}`;
}

let d2;
export async function renderSource(src) {
  d2 ??= new D2();
  const compiled = await d2.compile(src, RENDER_OPTIONS);
  return d2.render(compiled.diagram, compiled.renderOptions);
}
