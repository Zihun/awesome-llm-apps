import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after } from "node:test";

// 시험이 만든 임시 폴더는 시험 파일이 끝날 때 지운다. 지우지 않던 동안
// 사용자의 TEMP에 tut-* 폴더가 700개 넘게 쌓였다(2026-10-19 확인).
const made = [];
after(() => {
  for (const dir of made) rmSync(dir, { recursive: true, force: true });
});

/** os.tmpdir() 아래에 `prefix`로 시작하는 새 폴더를 만들고, 이 시험 파일이 끝나면 지운다. */
export function tempDir(prefix) {
  const dir = mkdtempSync(join(tmpdir(), prefix));
  made.push(dir);
  return dir;
}
