import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const TOOLS_DIR = fileURLToPath(new URL("..", import.meta.url));
export const TUTORIALS_DIR = resolve(TOOLS_DIR, "..");
export const REPO_ROOT = resolve(TUTORIALS_DIR, "..", "..");

export function loadDays(file = resolve(TOOLS_DIR, "days.json")) {
  return JSON.parse(readFileSync(file, "utf8"));
}

export const pad3 = (n) => String(n).padStart(3, "0");

export const PLACEHOLDER = "(작성 필요)";

export function folderName(day) {
  return `day${pad3(day.day)}-${day.slug}`;
}
