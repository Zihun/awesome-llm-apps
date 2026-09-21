#!/usr/bin/env python3
"""다이어그램에 임베드할 한글 서브셋 폰트를 만든다.

D2는 기본으로 Source Sans Pro를 임베드하는데 여기에는 한글 글리프가 없다. 그래서
한글 라벨은 (1) 글자 폭을 라틴 기준으로 잘못 재서 박스 크기가 어긋나고, (2) 보는
사람의 시스템 폰트에 기대게 되어 한글 폰트가 없는 환경에서는 두부(□)로 보인다.
여기서 만든 폰트를 D2에 넘기면 두 문제가 함께 사라진다.

D2는 실제로 쓰인 글자만 골라 SVG에 임베드하므로, 입력 폰트에 글자가 많아도 출력이
그만큼 커지지는 않는다. 다만 10MB짜리 가변 폰트를 그대로 넘기면 wasm 경계에서
"Invalid string length"로 실패하기 때문에, 정적 인스턴스로 굽고 실제 쓰는 글자만
남겨 입력 자체를 작게 만든다.

쓰는 글자만 남기므로 새 일차가 새 한글 음절을 쓰면 커버리지가 모자라게 된다.
`npm run check`가 그 경우를 잡아 이 스크립트를 다시 돌리라고 알려 준다.

    python fonts/build.py          # docs/tutorials/_tools 에서
"""
import sys
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

HERE = Path(__file__).resolve().parent
TUTORIALS = HERE.parent.parent
VF = HERE / "NotoSansKR-VF.ttf"
VF_URL = "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf"

# D2가 채우는 네 자리. Noto Sans KR에는 이탤릭이 없어 regular를 그대로 쓴다 —
# 한글이 이탤릭 자리에 오더라도 두부가 되는 것보다 낫다.
WEIGHTS = {"regular": 400, "semibold": 600, "bold": 700}

ASCII = "".join(chr(c) for c in range(0x20, 0x7F))


def used_characters() -> set[str]:
    """모든 .d2 소스에 실제로 등장하는 문자. 주석과 문법 기호까지 포함해 넉넉하게 잡는다."""
    chars = set(ASCII)
    for path in sorted(TUTORIALS.glob("day*/diagrams/*.d2")) + sorted(HERE.glob("*.d2")):
        chars |= set(path.read_text(encoding="utf-8"))
    return chars


def ensure_source() -> None:
    if VF.exists():
        return
    print(f"내려받는 중: {VF_URL}")
    urllib.request.urlretrieve(VF_URL, VF)
    print(f"  {VF.name}: {VF.stat().st_size:,} bytes")


def build(chars: set[str]) -> None:
    text = "".join(sorted(chars))
    for name, weight in WEIGHTS.items():
        font = TTFont(VF)
        instancer.instantiateVariableFont(font, {"wght": weight}, inplace=True)
        subsetter = subset.Subsetter(options=subset.Options(layout_features=["*"], notdef_outline=True))
        subsetter.populate(text=text)
        subsetter.subset(font)
        out = HERE / f"NotoSansKR-{name}.ttf"
        font.save(out)
        print(f"  NotoSansKR-{name}.ttf: {out.stat().st_size:,} bytes")


def main() -> int:
    ensure_source()
    chars = used_characters()
    hangul = sorted(c for c in chars if "가" <= c <= "힣")
    print(f".d2 소스가 쓰는 문자 {len(chars)}자 (그중 한글 {len(hangul)}자)")
    build(chars)
    print("완료. 폰트가 바뀌었으므로 `npm run render -- --force`로 전체를 다시 렌더하세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
