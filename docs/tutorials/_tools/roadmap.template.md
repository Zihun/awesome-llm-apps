# awesome-llm-apps 133일 튜토리얼

이 리포에 있는 앱을 하루에 하나씩, 처음부터 끝까지 따라 만드는 시리즈입니다. 하루 분량은 60~90분이고, 매 일차는 완성 아키텍처와 각 단계의 시스템 구성을 D2 다이어그램으로 보여 줍니다. 순서는 학습 난이도 순이며 볼륨 안에서는 작은 앱부터 갑니다.

## 이렇게 진행하세요

1. 아래 표에서 오늘 일차를 열고 "오늘 만들 것"과 완성 아키텍처 그림을 먼저 봅니다.
2. "사전 준비"의 키와 도구를 마련합니다. 공통 준비는 바로 아래 절을 한 번만 하면 됩니다.
3. "단계별 진행"을 순서대로 따라가며 각 Step의 **확인** 명령을 꼭 실행합니다. 그림에서 주황 테두리가 이번 Step에 새로 붙는 부분이고, 흐린 부분은 아직 만들지 않은 부분입니다.
4. "실행 체크리스트"를 모두 채우면 그날은 끝입니다. "더 해보기"는 선택입니다.

## 공통 사전 준비 (한 번만)

| 항목 | 내용 |
|---|---|
| Python | 3.11 이상 3.13 이하 (`pyproject.toml`의 `requires-python`) |
| uv | 설치: macOS/Linux `curl -LsSf https://astral.sh/uv/install.sh \| sh`, Windows `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"`, 또는 `pip install uv` |
| 리포 | `git clone https://github.com/Zihun/awesome-llm-apps.git && cd awesome-llm-apps` |
| API 키 | 일차마다 필요한 키가 다릅니다. 키는 셸 환경변수나 앱 폴더의 `.env`에 두고, 절대 커밋하지 않습니다 |

각 일차는 **앱 폴더 안에 독립 가상환경**을 만드는 방식을 기본으로 씁니다.

```bash
cd <원본 앱 폴더>
uv venv
uv pip install -r requirements.txt
uv run --no-project python <엔트리 파일>
```

이 저장소는 루트에도 `pyproject.toml`과 `uv.lock`이 있어, `--no-project` 없이 `uv run`을 쓰면 방금 만든 앱 폴더의 환경이 아니라 루트 환경이 쓰입니다 — 각 일차의 확인 명령이 모두 이 플래그를 붙이는 이유입니다.

리포 루트의 공용 환경(`uv sync --all-extras`)을 쓰는 방법은 [UV_MIGRATION_GUIDE.md](../../UV_MIGRATION_GUIDE.md)에 있습니다. 앱마다 의존성 버전이 달라 충돌할 수 있으므로, 튜토리얼의 확인 명령은 모두 독립 가상환경 기준으로 검증했습니다.

## 다이어그램 읽는 법

| 표현 | 뜻 |
|---|---|
| 사람 모양 | 사용자 |
| 파란 사각형 | 이 리포의 코드 (앱, 에이전트, 도구 함수) |
| 회색 구름 | 외부 API, LLM 제공자 |
| 초록 원통 | DB, 벡터 저장소, 캐시 |
| 문서 모양 | 파일, 설정 |
| 주황 굵은 테두리 | 이번 Step에서 새로 추가된 부분 |
| 흐리고 점선 | 아직 만들지 않은 부분 |

다이어그램 소스는 각 일차의 `diagrams/*.d2`에 있고, 렌더와 검사는 `docs/tutorials/_tools`에서 `npm install && npm run render && npm run check`로 합니다.

## 다루지 않는 항목

README에 실려 있지만 코드가 외부 리포에 있는 두 항목은 링크만 남깁니다: [Openwork](https://github.com/accomplish-ai/coworker), [OpenSource Voice Dictation Agent](https://github.com/akshayaggarwal/wispr-flow-clone).

## 133일 일정

<!-- DAYS -->
