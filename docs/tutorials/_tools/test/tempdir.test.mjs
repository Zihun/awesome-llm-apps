import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

test("tempDir removes its folders when the test file finishes", () => {
  const helper = new URL("../support/tempdir.mjs", import.meta.url).href;
  const box = mkdtempSync(join(tmpdir(), "tut-tmp-"));
  try {
    const script = join(box, "uses-temp.test.mjs");
    writeFileSync(
      script,
      `import { test } from "node:test";\nimport { tempDir } from ${JSON.stringify(helper)};\n` +
        `test("x", () => { console.log("MADE " + tempDir("tut-tmp-inner-")); });\n`,
    );
    // node --test가 자식 프로세스에 거는 NODE_TEST_CONTEXT를 빼야 자식이 제 출력을 그대로 낸다.
    const { NODE_TEST_CONTEXT, ...env } = process.env;
    const out = execFileSync(process.execPath, [script], { encoding: "utf8", env });
    const made = out.match(/MADE (.+)/)[1].trim();
    assert.equal(existsSync(made), false);
  } finally {
    rmSync(box, { recursive: true, force: true });
  }
});
