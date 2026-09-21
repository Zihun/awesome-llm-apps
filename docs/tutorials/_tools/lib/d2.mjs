import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { D2 } from "@terrastruct/d2";

const IMPORT_RE = /^\.\.\.@(\S+)\s*$/;
const HASH_RE = /<!-- d2-source-sha256: ([0-9a-f]{64}) -->/;

const FONT_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..", "fonts");

/** D2의 기본 폰트(Source Sans Pro)에는 한글이 없다. 그대로 두면 글자 폭을 라틴 기준으로
 *  재어 박스가 어긋나고, 보는 사람에게 한글 폰트가 없으면 두부(□)로 보인다.
 *  fonts/build.py가 만든 서브셋을 넘겨 두 문제를 함께 없앤다.
 *  D2는 JSON 경계를 넘길 때 []byte를 base64 문자열로 받으므로 Uint8Array가 아니라 문자열로 준다. */
function loadFonts() {
  const read = (name) => readFileSync(resolve(FONT_DIR, name)).toString("base64");
  const regular = read("NotoSansKR-regular.ttf");
  return {
    fontRegular: regular,
    fontSemibold: read("NotoSansKR-semibold.ttf"),
    fontBold: read("NotoSansKR-bold.ttf"),
    fontItalic: regular, // Noto Sans KR에는 이탤릭이 없다. 두부보다 정체가 낫다.
  };
}

let fonts;
export function fontOptions() {
  return (fonts ??= loadFonts());
}

/** 서체를 바꿀 때 손으로 올린다. 이 값이 바뀌면 전체가 다시 렌더된다. */
export const FONT_VERSION = "notosans-kr-1";

/** 폰트가 바뀌면 이미 렌더된 SVG도 낡은 것이 된다. 해시에 섞어 재렌더를 강제한다.
 *  TTF 바이트가 아니라 글자 집합을 지문으로 쓴다 — fontTools는 같은 입력을 두 번 구워도
 *  바이트가 달라지므로, 바이트를 섞으면 폰트를 다시 굽기만 해도 멀쩡한 SVG가 전부 stale이 된다. */
export function fontFingerprint() {
  const coverage = resolve(FONT_DIR, "coverage.txt");
  const chars = existsSync(coverage) ? readFileSync(coverage, "utf8") : "";
  return createHash("sha256").update(`${FONT_VERSION}\n${chars}`, "utf8").digest("hex").slice(0, 16);
}

export const RENDER_OPTIONS = { layout: "elk", sketch: false, pad: 8, noXMLTag: true };

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
  return createHash("sha256").update(`${fontFingerprint()}\n${src}`, "utf8").digest("hex");
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
  const compiled = await d2.compile(src, { ...RENDER_OPTIONS, ...fontOptions() });
  return d2.render(compiled.diagram, compiled.renderOptions);
}
