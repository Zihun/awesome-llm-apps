# Day 055 · 🖥️ Local Hybrid Search RAG

> 볼륨 5 📀 RAG · 난이도 ★★★ ⚠ · 예상 소요 100분(설치 자체가 두 개의 컴파일 벽에 부딪히고, 그중 하나는 20분을 기다려도 끝나지 않아 손으로 확인하는 데 시간이 많이 듭니다) · API 비용 무료(LLM·임베더·리랭커 모두 로컬 실행 — 다만 GGUF 모델 2개와 spaCy 언어 모델을 최초 1회 내려받아야 하며 크기는 Step 1~2에서 다룸) · 원본 앱: `rag_tutorials/local_hybrid_search_rag`

## 오늘 만들 것

Day 047이 정리한 파이프라인 — 문서 → 청크 → 임베딩 → 저장 → 질의 → 검색 → 답변 — 에서 오늘 앱이 다르게 채우는 자리는 "검색"과 "저장"입니다. `raglite`라는 라이브러리 위에 257줄짜리 Streamlit 앱을 올린 이 앱은, 질문 하나마다 키워드 검색(BM25류)과 벡터 검색을 각각 따로 돌려 Reciprocal Rank Fusion(RRF)으로 한 순위 목록으로 합치고, 그 상위 결과를 FlashRank라는 별도의 로컬 크로스인코더로 다시 정렬합니다 — 이것이 제목의 "Hybrid"입니다. 그리고 "Local"은 이 앱에서 겉치레가 아닙니다: 답변을 쓰는 LLM도, 문서를 벡터로 바꾸는 임베더도 `llama-cpp-python`이 돌리는 GGUF 파일이고, 재순위화 모델도 API가 아니라 ONNX 런타임으로 이 컴퓨터에서 돕니다. 그 대가는 설치 단계에서부터 드러납니다 — `llama-cpp-python`은 오늘 기준 어떤 플랫폼에도 미리 빌드된 wheel을 내놓지 않아 소스 빌드가 강제되고, 이 컴퓨터에는 실제로 Visual Studio(MSVC)와 CMake가 있는데도(직접 확인) 그 빌드가 20분 넘게 끝나지 않았습니다. 여기에 더해 이 Python(3.13)에서는 `spacy`·`thinc`·`blis`도 미리 빌드된 wheel이 없어 별도로 컴파일해야 하는데, `blis` 0.7.11은 Cython 오류로 아예 실패합니다(직접 확인) — 컴파일러가 없어서가 아니라 오래된 패키지가 오늘의 Cython과 맞지 않아서입니다. 데이터베이스도 앱 자체 README는 PostgreSQL(Neon)을 권하지만, 실제 코드와 `raglite` 소스를 보면 `sqlite:///`로 시작하는 URL도 그대로 받아들입니다 — 서버 없이 로컬 파일 하나로 시작할 길이 코드상 열려 있다는 뜻입니다. 마지막으로, 검색 결과가 없을 때 쓰는 폴백 함수 `handle_fallback`은 오늘 설치되는 `raglite`의 `rag()` 시그니처에 없는 인자를 넘겨 항상 `TypeError`로 죽고, 그 예외를 자기 자신의 `except`가 조용히 삼킵니다. 완성하면(그리고 위 벽들을 넘기면) PDF를 올리고 질문하면 하이브리드 검색과 재순위화를 거친 근거로 로컬 LLM이 스트리밍으로 답하는 화면을 로컬에서 띄우게 됩니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |
| C/C++ 컴파일러 + CMake | `llama-cpp-python` 소스 빌드에 필수. Python 3.13에서는 `spacy`·`thinc`·`blis`도 wheel이 없어 추가로 필요 | Windows는 Visual Studio Build Tools의 "C++를 사용한 데스크톱 개발" 워크로드 + CMake. 이 문서를 쓴 컴퓨터에는 이미 둘 다 있었다(Step 1에서 직접 확인) — 그런데도 빌드가 끝까지 가지 않았다는 것이 오늘의 핵심 발견 |
| spaCy 언어 모델 `xx_sent_ud_sm` | `raglite`의 문장 분리기가 문서를 청크로 나누기 전에 사용(4.1MB, 이 문서는 받음) | `pip install https://github.com/explosion/spacy-models/releases/download/xx_sent_ud_sm-3.7.0/xx_sent_ud_sm-3.7.0-py3-none-any.whl` — 이 wheel 하나만 받아도 `spacy`가 딸려 오고, Python 3.13에서는 Step 1과 같은 컴파일 벽에 부딪힌다(직접 확인) |
| 로컬 GGUF 모델 파일 2개(LLM·임베더) | 답변 생성과 문서/질의 임베딩 | 사이드바에 `<HF 저장소>/<파일명>@<n>` 형식 경로를 입력하면 최초 사용 시 Hugging Face에서 자동 다운로드(수백 MB~수 GB, 발행 크기는 Step 2에서 확인, 이 문서는 받지 않음) |
| 데이터베이스(선택) | 청크·임베딩·전문색인 저장 | 앱 자체 README는 PostgreSQL(Neon 무료 티어)을 안내하지만, 코드는 `sqlite:///로컬파일.db`도 그대로 받아들이는 것으로 보인다(Step 2, 소스로 확인) — 이 문서는 어느 쪽도 실행하지 않음 |
| 인터넷 연결 | PyPI/Hugging Face 설치·다운로드 | 별도 설치 없음 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 사용자 | 사이드바에 모델 경로·DB URL 입력, PDF 업로드, 질문 입력 | 코드 없음 (브라우저) |
| Streamlit UI (local_main.py) | 설정 화면, 문서 업로드, 채팅 루프 조립 | `rag_tutorials/local_hybrid_search_rag/local_main.py:124-257` |
| RAGLiteConfig | DB URL·LLM·임베더·리랭커·청크 크기를 한데 묶은 설정 객체 | `rag_tutorials/local_hybrid_search_rag/local_main.py:41-48` |
| 문서 삽입 (insert_document) | PDF→마크다운→문장 분리→임베딩→의미 기반 청킹→DB 저장 | `rag_tutorials/local_hybrid_search_rag/local_main.py:67` |
| 하이브리드 검색 (hybrid_search) | 키워드 검색과 벡터 검색을 각각 수행해 RRF로 융합 | `rag_tutorials/local_hybrid_search_rag/local_main.py:87` |
| 재순위화 (rerank_chunks · FlashRank) | 융합된 후보를 로컬 크로스인코더로 재정렬 | `rag_tutorials/local_hybrid_search_rag/local_main.py:91` |
| 답변 생성 (rag) | 컨텍스트를 시스템 프롬프트에 넣어 로컬 LLM으로 스트리밍 생성 | `rag_tutorials/local_hybrid_search_rag/local_main.py:229-236` |
| 로컬 LLM·임베더 (llama-cpp-python) | GGUF 모델을 이 컴퓨터에서 직접 실행 | 코드 없음(라이브러리 내부, `RAGLiteConfig`가 문자열로 지정) |
| 데이터베이스 (SQLite 기본값 / PostgreSQL) | 청크·벡터·전문색인 저장, 하이브리드 검색의 두 절반이 모두 여기서 실행됨 | 코드 없음(raglite 내부, `db_url`로 지정) |

## 단계별 진행

### Step 1. 환경 만들기 — 컴파일러는 있어도 wheel이 없다

**목적.** `requirements.txt` 15줄을 설치할 때 정확히 어디서 막히는지 확인합니다. `llama-cpp-python`이 왜 막히는지, 그리고 그것이 "컴파일러가 없어서"가 맞는지부터 검증합니다.

**할 일.**

```bash
cd rag_tutorials/local_hybrid_search_rag
uv venv
uv pip install -r requirements.txt
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Windows PowerShell은 활성화만 `.venv\Scripts\Activate.ps1`로 바꿉니다.)

이 저장소는 루트에 `pyproject.toml`이 있어 `uv run`이 방금 만든 환경 대신 루트의 `.venv`를 쓰므로, 이후 `uv run` 명령에는 모두 `--no-project`를 붙입니다. `uv venv`는 이 환경의 기본값인 Python 3.13.3을 그대로 골랐습니다(직접 확인) — 이 컴퓨터의 시스템 Python은 `python --version` 기준 3.13.12, `py` 런처 기준 3.14.3으로 셋 다 다릅니다(직접 확인).

`rag_tutorials/local_hybrid_search_rag/requirements.txt:1-15`

```text
raglite==0.2.1
llama-cpp-python>=0.2.56
sentence-transformers>=2.5.1
pydantic==2.10.1
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
pypdf>=3.0.0
python-dotenv>=1.0.0
rerankers==0.6.0
spacy>=3.7.0
streamlit>=1.31.0
flashrank==0.2.9
numpy>=1.24.0
pandas>=2.0.0
tqdm>=4.66.0
```

먼저 정확한 버전 고정 네 개(`raglite==0.2.1`, `pydantic==2.10.1`, `rerankers==0.6.0`, `flashrank==0.2.9`)가 오늘도 함께 풀리는지만 따로 확인했습니다 — 실제 다운로드 없이 해석만 하는 `--dry-run`으로, 무거운 전이 의존성까지 포함해 얼마나 큰 그래프가 나오는지 보기 위해서입니다.

```bash
uv venv --python 3.13
uv pip install --dry-run "raglite==0.2.1" "pydantic==2.10.1" "rerankers==0.6.0" "flashrank==0.2.9"
```

직접 확인한 출력(발췌 — 전체 116줄 중 이 문서와 관련된 줄만):

```
Resolved 116 packages in 57.8s
 + flashrank==0.2.9
 + llama-cpp-python==0.3.35
 + pydantic==2.10.1
 + raglite==0.2.1
 + rerankers==0.6.0
 + spacy==3.7.5
 + sqlalchemy==2.0.54
```

네 핀은 오늘도(2026-09-23) 함께 풀립니다. 그런데 이 목록에 이 앱의 `requirements.txt`에는 없는 `llama-cpp-python==0.3.35`가 끼어 있습니다 — `raglite==0.2.1` 자신이 `llama_cpp`를 가져오기 때문입니다(다음 문단). 즉 `llama-cpp-python`을 요구하는 것은 이 앱의 `requirements.txt`뿐 아니라 `raglite` 자신이기도 합니다.

PyPI가 이 패키지에 실제로 무엇을 올려 두는지부터 봅니다.

```bash
python -c "
import json, urllib.request
d = json.load(urllib.request.urlopen('https://pypi.org/pypi/llama-cpp-python/json'))
for v in ['0.3.35', '0.2.90', '0.2.56']:
    files = d['releases'][v]
    print(v, [(f['filename'], f['packagetype']) for f in files])
"
```

직접 확인한 출력:

```
0.3.35 [('llama_cpp_python-0.3.35.tar.gz', 'sdist')]
0.2.90 [('llama_cpp_python-0.2.90.tar.gz', 'sdist')]
0.2.56 [('llama_cpp_python-0.2.56.tar.gz', 'sdist')]
```

이 앱이 요구하는 하한(0.2.56)부터 오늘 풀리는 최신판(0.3.35)까지, 어느 버전도 **어떤 플랫폼의 wheel도 올리지 않았습니다** — 소스 배포(sdist)뿐입니다. 즉 이것은 "이 컴퓨터·이 Python이라서" 겪는 문제가 아니라 이 패키지가 오늘 모두에게 강제하는 소스 빌드입니다. 실제로 설치를 시도하면 무슨 일이 벌어지는지 직접 확인합니다.

```bash
uv pip install llama-cpp-python
```

직접 확인한 출력(전부):

```
Resolved 6 packages in 923ms
   Building llama-cpp-python==0.3.35
```

이 상태로 CMake(`C:\Program Files\CMake\bin\cmake.exe`)가 곧바로 뜨는 것을 프로세스 목록에서 확인했고, 그 후 20분 넘게 기다렸지만 다음 줄이 출력되지 않았습니다. 그사이 프로세스 목록에는 `cl.exe`와 `link.exe`(`...Visual Studio\18\Community\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64\`)가 실제로 나타났다 사라졌습니다 — 즉 이 컴퓨터에는 CMake도 MSVC 컴파일러/링커도 실제로 있고 빌드가 그것들을 실제로 불렀습니다. "컴파일러가 없다"는 이 컴퓨터에서는 사실이 아니었습니다. 그런데도 20분 안에 끝나지 않아 결국 프로세스를 강제 종료했고, 그 뒤 확인한 결과는 아무것도 설치되지 않았다는 것이었습니다.

```bash
python -c "import llama_cpp"
```

```
ModuleNotFoundError: No module named 'llama_cpp'
```

같은 Python(3.13)에서 `spacy`·`thinc`·`blis`(모두 `raglite`가 문장 분리에 쓰는 `spacy`의 하위 의존성)도 wheel이 없다는 것을 PyPI 메타데이터로 확인했습니다 — 세 패키지 모두 cp310~cp312 wheel은 있지만 cp313은 없습니다.

```bash
python -c "
import json, urllib.request
for pkg, ver in [('spacy','3.7.5'), ('thinc','8.2.4'), ('blis','0.7.11')]:
    d = json.load(urllib.request.urlopen(f'https://pypi.org/pypi/{pkg}/{ver}/json'))
    tags = sorted({f['filename'] for f in d['urls'] if 'win_amd64' in f['filename']})
    print(pkg, ver, '->', [t.split('-')[-2] for t in tags])
"
```

직접 확인한 출력:

```
spacy 3.7.5 -> ['cp310', 'cp311', 'cp312', 'cp37m', 'cp38', 'cp39']
thinc 8.2.4 -> ['cp310', 'cp311', 'cp312', 'cp37m', 'cp38', 'cp39']
blis 0.7.11 -> ['cp310', 'cp311', 'cp312', 'cp37m', 'cp38', 'cp39']
```

실제로 `blis`를 소스 빌드하면 컴파일러 유무와 무관한 다른 이유로 실패합니다 — Cython 3.x가 이 오래된 `.pyx` 문법을 거부합니다(직접 확인, 아래는 실제로 이 wheel 하나만 설치를 시도했을 때의 출력 마지막 부분입니다).

```bash
uv venv --python 3.13
uv pip install "https://github.com/explosion/spacy-models/releases/download/xx_sent_ud_sm-3.7.0/xx_sent_ud_sm-3.7.0-py3-none-any.whl"
```

직접 확인한 출력(발췌, 5분 3초 만에 실패):

```
Error compiling Cython file:
blis\py.pyx:128:27: Accessing Python attribute not allowed without gil
Cython.Compiler.Errors.CompileError: blis\py.pyx
help: `blis` (v0.7.11) was included because `xx-sent-ud-sm` (v3.7.0) depends
      on `spacy` (v3.7.5) which depends on `thinc` (v8.2.5) which depends
      on `blis`
```

즉 이 Python 버전에서는 spaCy 언어 모델 wheel 하나만 따로 받으려 해도 같은 벽에 부딪힙니다. Python을 3.10~3.12로 낮추면 이 벽은 피할 수 있지만(spacy/thinc/blis에 wheel이 있으므로), `llama-cpp-python`은 어느 Python에도 wheel이 없으므로 그 벽은 그대로 남습니다 — 두 문제는 원인이 다르고 해결책도 다릅니다.

**그림.**

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 위에서 실행한 각 명령의 실제 출력이 이 단계의 확인입니다. 요약하면: PyPI 메타데이터로 wheel 부재를 확인했고, 실제 설치 시도로 CMake·MSVC가 호출되지만 20분 안에 끝나지 않는다는 것을 확인했고, `import llama_cpp`로 아무것도 설치되지 않았다는 것을 확인했습니다.

```bash
uv run --no-project python -c "import raglite" 2>&1 | tail -3
```

기대 출력(이 컴퓨터에서 직접 확인 — `llama_cpp`가 없으므로 `raglite`의 최상단 import에서부터 실패합니다):

```
ModuleNotFoundError: No module named 'llama_cpp'
```

### Step 2. RAGLiteConfig — 로컬 모델 세 자리와 데이터베이스 한 자리

**목적.** `initialize_config`가 만드는 `RAGLiteConfig`의 다섯 필드가 각각 무엇을 가리키는지, GGUF 모델이 실제로 얼마나 큰지, 그리고 데이터베이스가 정말 PostgreSQL만 받는지 확인합니다.

**할 일.**

`rag_tutorials/local_hybrid_search_rag/local_main.py:41-48`

```python
        return RAGLiteConfig(
            db_url=settings["DBUrl"],
            llm=f"llama-cpp-python/{settings['LLMPath']}",
            embedder=f"llama-cpp-python/{settings['EmbedderPath']}",
            embedder_normalize=True,
            chunk_max_size=512,
            reranker=Reranker("ms-marco-MiniLM-L-12-v2", model_type="flashrank")
        )
```

`llm=`과 `embedder=`는 raglite가 문서화하는 `"llama-cpp-python/<HF 저장소>/<파일명>@<n>"` 형식 문자열입니다 — `n`은 LLM이면 컨텍스트 길이, 임베더면 차원입니다. 앱 자체 README의 "Quick Start"가 권하는 값은 `bartowski/Llama-3.2-3B-Instruct-GGUF/Llama-3.2-3B-Instruct-Q4_K_M.gguf@4096`(LLM)과 `lm-kit/bge-m3-gguf/bge-m3-Q4_K_M.gguf@1024`(임베더)인데, 이는 raglite 0.2.1 자신의 기본값(GPU 오프로드가 없거나 CPU 4코어 미만일 때)과 정확히 같습니다(소스로 확인, `_config.py`) — 이 앱은 raglite의 기본 선택을 그대로 명시한 것입니다. 각 파일의 발행 크기는 Hugging Face에 직접 확인했습니다(파일을 받지 않고 HTTP HEAD로만).

```bash
curl -sIL "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf" | grep -i content-length
curl -sIL "https://huggingface.co/lm-kit/bge-m3-gguf/resolve/main/bge-m3-Q4_K_M.gguf" | grep -i content-length
```

직접 확인한 출력:

```
content-length: 2019377696
content-length: 437778592
```

즉 LLM 약 1.9GiB, 임베더 약 417MiB — 둘을 더하면 2.3GiB 남짓을 최초 1회 내려받아야 합니다(이 문서는 받지 않았습니다). raglite가 GPU 오프로드 가능 환경에서 고르는 기본 LLM(`Meta-Llama-3.1-8B-Instruct-GGUF`, Q4_K_M)은 같은 방식으로 확인하면 약 4.6GiB로 더 큽니다.

데이터베이스는 앱 자체 README의 "Database Setup" 절이 PostgreSQL(Neon)만 안내하고, 사이드바 입력창의 placeholder도 `postgresql://user:pass@host:port/db`이지만, 코드 어디에도 이 문자열의 스킴을 검사하는 부분은 없습니다.

`rag_tutorials/local_hybrid_search_rag/local_main.py:155-168`

```python
        if st.button("Save Configuration"):
            try:
                if not all([llm_path, embedder_path, db_url]):
                    st.error("All fields are required!")
                    return
                
                settings = {
                    "LLMPath": llm_path,
                    "EmbedderPath": embedder_path,
                    "DBUrl": db_url
                }
                
                st.session_state.my_config = initialize_config(settings)
                st.success("Configuration saved successfully!")
```

검사하는 것은 "세 칸이 비어 있지 않은가"뿐입니다. raglite 0.2.1 소스를 보면 `RAGLiteConfig.db_url`의 기본값 자체가 `"sqlite:///raglite.sqlite"`이고(`_config.py`), 실제 연결을 여는 `_database.py`는 `make_url(db_url).get_backend_name()`으로 `"postgresql"`과 `"sqlite"` 두 값만 분기 처리하며 그 외에는 `"RAGLite only supports PostgreSQL and SQLite."`라는 오류를 던집니다 — 즉 SQLite도 정식으로 지원되는 경로입니다(소스로 확인). Day 049의 PostgreSQL이 코드에 주소가 그대로 박혀 있어 대안이 없었던 것과 달리, 이 앱은 라이브러리 차원에서 서버 없는 대안이 이미 있는데 앱의 UI와 앱 자체 README가 그쪽을 안내하지 않을 뿐입니다. 다만 이 자리를 실제로 `sqlite:///...`로 채워 끝까지 실행하는 것은 Step 1에서 확인한 `llama_cpp` 부재 때문에 이 문서에서는 재현하지 못했습니다.

**그림.**

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** raglite의 기본값이 정말 그런지는 소스를 내려받아 직접 읽어 확인했습니다(패키지를 설치하지 않고, GitHub의 해당 버전 태그에서).

```bash
curl -s "https://raw.githubusercontent.com/superlinear-ai/raglite/v0.2.1/src/raglite/_config.py" | grep -A1 "db_url:"
```

직접 확인한 출력:

```
    db_url: str | URL = "sqlite:///raglite.sqlite"
```

### Step 3. 문서 적재 — 임베딩이 청크보다 먼저 온다

**목적.** `process_document`가 부르는 `insert_document`가 내부적으로 몇 단계를 거치는지, 그리고 Day 047의 "고정 크기로 자르고 그다음에 임베딩"과 순서가 다르다는 것을 확인합니다.

**할 일.**

`rag_tutorials/local_hybrid_search_rag/local_main.py:64-68`

```python
    try:
        if not st.session_state.get('my_config'):
            raise ValueError("Configuration not initialized")
        insert_document(Path(file_path), config=st.session_state.my_config)
        return True
```

raglite 0.2.1의 `insert_document`(소스로 확인, `_insert.py`)는 `tqdm`으로 5단계를 진행합니다 — DB 초기화, 마크다운 변환, **문장 분리**(spaCy `xx_sent_ud_sm`, Step 1의 그 모델), **문장 임베딩**(`llm-cpp-python` 임베더), 그리고 **청크 분할**입니다. 순서가 중요합니다: 문장을 먼저 통째로 임베딩한 다음, 그 임베딩들의 유사도를 보고 의미가 이어지는 문장끼리 묶어 청크를 만듭니다(`embedder_sentence_window_size`, `chunk_max_size=512`로 이 앱이 raglite 기본값 1440에서 낮춘 값). Day 047의 agno 리더는 반대로 5000자 고정 크기로 먼저 자른 뒤 그 조각을 임베딩했습니다 — 오늘 앱은 의미가 끊기는 자리에서 청크를 나누려는 편입니다. 이 단계도 임베더(`llama_cpp`)가 있어야 하므로 Step 1의 벽 때문에 이 문서에서 실제로 실행하지는 못했습니다.

**그림.**

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 앱이 저장하려는 파일이 실제로 존재하고 pypdf로 열리는지까지는 임베더 없이 확인할 수 있습니다(리포에 포함된 예시 PDF는 없으므로, 아무 PDF나 받아 pypdf 설치만으로 페이지 수를 셉니다).

```bash
uv run --no-project python -c "
from pypdf import PdfReader
import inspect
print('pypdf version import ok:', inspect.getfile(PdfReader))
"
```

기대 출력(경로는 환경마다 다름):

```
pypdf version import ok: ...\site-packages\pypdf\_reader.py
```

### Step 4. 하이브리드 검색 — 키워드와 벡터를 RRF로 합치기

**목적.** `perform_search`의 `hybrid_search` 호출이 실제로 무엇을 두 번 하고 어떻게 하나로 합치는지, 정확한 공식까지 확인합니다.

**할 일.**

`rag_tutorials/local_hybrid_search_rag/local_main.py:86-94`

```python
    try:
        chunk_ids, scores = hybrid_search(query, num_results=10, config=st.session_state.my_config)
        if not chunk_ids:
            return []
        chunks = retrieve_chunks(chunk_ids, config=st.session_state.my_config)
        return rerank_chunks(query, chunks, config=st.session_state.my_config)
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return []
```

raglite 0.2.1의 `hybrid_search`(소스로 확인, `_search.py`)는 정확히 이렇게 동작합니다. 먼저 같은 질의로 `vector_search`와 `keyword_search`를 각각 독립적으로 실행해 후보를 최대 100개씩(`num_rerank` 기본값) 뽑습니다. `keyword_search`는 백엔드에 따라 다른 엔진을 씁니다 — PostgreSQL이면 `to_tsvector`/`to_tsquery`와 `ts_rank`(Postgres 자체의 전문검색), SQLite면 FTS5의 `bm25()` 함수(부호가 반대라 앱 쪽에서 다시 뒤집습니다)입니다. `vector_search`는 질의를 같은 임베더로 벡터화해 코사인 유사도로 가장 가까운 청크를 찾습니다. 두 순위 목록은 `reciprocal_rank_fusion`으로 합쳐집니다 — 각 목록에서 어떤 청크의 순위가 `i`번째(0부터 시작)면 `1 / (k + i)`를 더하고, 그 목록에 아예 없으면 `i` 대신 그 목록의 길이(즉 "가장 뒤"로 취급)를 씁니다. 상수 `k`는 60으로 고정되어 있습니다. 두 목록 모두에서 상위권인 청크일수록 점수가 높게 쌓이고, 이 합산 점수 내림차순으로 정렬한 뒤 `num_results=10`(이 앱이 넘긴 값, 기본값은 3)만 남깁니다. 즉 "하이브리드"는 문자 그대로 키워드 검색과 벡터 검색이 같은 문서 집합 위에서 각자 돈 다음 순위로만 합쳐지는 것이지, 점수나 임베딩을 섞는 것이 아닙니다.

**그림.**

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** RRF 공식 자체는 라이브러리를 설치하지 않고 소스로 직접 옮겨 재현할 수 있습니다 — 숫자 계산은 파이썬 언어 자체의 동작이라 별도 의존성이 필요 없습니다.

```bash
uv run --no-project python -c "
from collections import defaultdict
def rrf(rankings, k=60):
    ids = {c for r in rankings for c in r}
    score = defaultdict(float)
    for r in rankings:
        idx = {c: i for i, c in enumerate(r)}
        for c in ids:
            score[c] += 1 / (k + idx.get(c, len(idx)))
    return sorted(score.items(), key=lambda x: x[1], reverse=True)
vec = ['A', 'B', 'C']
kw  = ['C', 'A', 'D']
for cid, s in rrf([vec, kw]):
    print(cid, round(s, 5))
"
```

기대 출력(직접 확인 — A와 C가 두 목록 모두에 들어 있어 D·B보다 높습니다):

```
A 0.03252
C 0.03226
D 0.01587
B 0.01575
```

### Step 5. 재순위화 — FlashRank ONNX 크로스인코더

**목적.** `rerank_chunks`가 실제로 어떤 모델을 어디서 내려받아 어떻게 돌리는지 실제로 내려받고 실행해 확인합니다.

**할 일.**

`initialize_config`의 `reranker=Reranker("ms-marco-MiniLM-L-12-v2", model_type="flashrank")`(`rag_tutorials/local_hybrid_search_rag/local_main.py:47`)는 `rerankers` 패키지가 `flashrank.Ranker`를 감싼 것입니다. raglite의 `rerank_chunks`(소스로 확인, `_search.py`)는 `config.reranker`가 튜플이 아니라 이렇게 단일 객체면 언어 감지 없이 그대로 씁니다 — raglite 자신의 기본값은 언어별로 다른 모델을 쓰는 튜플(영어는 이 모델, 그 외 언어는 `ms-marco-MultiBERT-L-12`)인데, 이 앱은 언어와 무관하게 항상 이 영어 모델 하나만 씁니다. `rerankers`·`flashrank` 자체는 `llama-cpp-python`이나 `torch`를 요구하지 않습니다 — 실제로 이 둘만 따로 설치하면 30개 패키지가 91초 만에 받아지고, 무거운 것은 `onnxruntime`(ONNX 실행기)뿐입니다(직접 확인).

```bash
uv venv --python 3.13
uv pip install "rerankers==0.6.0" "flashrank==0.2.9"
```

이 모델을 실제로 생성해 내려받고, 실제 문장 3개를 재정렬해 봤습니다.

```bash
uv run --no-project python -c "
from rerankers import Reranker
r = Reranker('ms-marco-MiniLM-L-12-v2', model_type='flashrank', verbose=0)
docs = ['The cat sat on the mat.', 'Paris is the capital of France, known for the Eiffel Tower.', 'RAGLite supports hybrid search combining keyword and vector retrieval.']
result = r.rank(query='What is the capital of France?', docs=docs)
top = result.top_k(1)[0]
print('top:', top.document.text[:50], '| score:', round(top.score, 4))
"
```

직접 확인한 출력:

```
top: Paris is the capital of France, known for the Ei | score: 0.9998
```

모델은 Hugging Face의 `prithivida/flashrank` 저장소에서 zip으로 내려받습니다(`https://huggingface.co/prithivida/flashrank/resolve/main/ms-marco-MiniLM-L-12-v2.zip`) — 압축 파일은 22,696,961바이트(≈21.6MiB), 풀었을 때 실제로 추론에 쓰는 ONNX 파일(`flashrank-MiniLM-L-12-v2_Q.onnx`)은 34,004,051바이트(≈32.4MiB)로, flashrank 자신의 README가 이 모델을 "~34MB"라고 표기한 것과 정확히 일치합니다(둘 다 직접 확인). 재순위화 자체는 CPU에서 문장 3개에 0.13초가 걸렸습니다 — 실행마다 달라질 수 있는 값입니다.

이 생성자는 **매번 즉시** 다운로드를 시도합니다(지연 로딩이 아닙니다) — 이 문서를 쓰며 처음 시도했을 때는 파이썬 `requests`가 huggingface.co와의 TLS 핸드셰이크에서 `SSLEOFError`로 실패했지만, 같은 URL을 `curl`로 받으면 문제없이 끝까지 받아졌습니다(둘 다 직접 확인) — 모델이나 URL의 문제가 아니라 이 환경의 `requests`/OpenSSL 스택과 관련된 것으로 보입니다.

**그림.**

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 위 두 명령(설치, 실제 rank 호출)의 출력이 이 단계의 확인입니다. 네트워크 상태에 따라 다운로드 자체가 실패할 수 있습니다(위 SSL 오류 참고) — 실패하면 재시도하거나 같은 URL을 `curl`로 받아 봅니다.

### Step 6. 답변 생성과 실패하는 폴백

**목적.** 검색 결과가 있을 때와 없을 때 각각 어떤 함수가 LLM을 부르는지, 그리고 없을 때 쓰는 `handle_fallback`이 왜 raglite 0.2.1에서 항상 실패하는지 정확히 확인합니다.

**할 일.**

`rag_tutorials/local_hybrid_search_rag/local_main.py:101-109`

```python
        response_stream = rag(
            prompt=query,
            system_prompt=system_prompt,
            search=None,
            messages=[],
            max_tokens=1024,
            temperature=0.7,
            config=st.session_state.my_config
        )
```

`rag_tutorials/local_hybrid_search_rag/local_main.py:229-236`

```python
                        response_stream = rag(
                            prompt=user_input,
                            system_prompt=RAG_SYSTEM_PROMPT,
                            search=hybrid_search,
                            messages=formatted_messages,
                            max_contexts=5,
                            config=st.session_state.my_config
                        )
```

두 호출 모두 raglite의 `rag()`를 부르지만 넘기는 인자가 다릅니다. raglite 0.2.1의 `rag()` 시그니처는(소스로 확인, `_rag.py`) `prompt, *, max_contexts=5, context_neighbors=(-1,1), search=hybrid_search, messages=None, system_prompt=..., config=None`이고 `**kwargs`가 없습니다 — `max_tokens`도 `temperature`도 이 함수가 아는 이름이 아닙니다. 즉 `handle_fallback`의 호출(101-109행)은 존재하지 않는 두 키워드 인자 때문에 **항상** `TypeError`가 나고, 그 예외는 `handle_fallback` 자신의 `except Exception as e:`(122행)가 그대로 삼켜 "I apologize, but I encountered an error while processing your request."만 화면에 남깁니다 — 검색 결과가 없을 때 나오는 이 문구는 raglite나 LLM의 실패가 아니라 이 두 인자 이름 때문입니다. 반대로 본문 채팅 경로(229-236행)는 `search`·`messages`·`max_contexts`만 넘기므로 이 함수의 실제 시그니처와 맞습니다 — 검색 결과가 있을 때만 정상적으로 LLM을 호출한다는 뜻입니다. `search=None`도 별개의 문제입니다: `_contexts()`(소스로 확인)는 `callable(search)`가 거짓이면 `search` 값 자체를 청크 목록으로 취급해 그대로 슬라이스하므로, `None`을 넘기면 `max_tokens` 문제와 별개로 `'NoneType' object is not subscriptable` 오류가 날 자리이기도 합니다 — 다만 앞선 인자 문제 때문에 이 코드는 실제로 이 줄까지 가지도 못합니다.

**그림.**

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** raglite 자체를 이 컴퓨터에서 import할 수 없으므로(Step 1), 실제 실행 대신 두 호출이 쓰는 인자 이름을 라이브러리의 실제 시그니처와 나란히 비교합니다 — 어느 이름이 맞고 틀린지는 소스에 그대로 있어 실행 없이도 확정할 수 있습니다.

```bash
curl -s "https://raw.githubusercontent.com/superlinear-ai/raglite/v0.2.1/src/raglite/_rag.py" | grep -A8 "^def rag("
```

직접 확인한 출력:

```
def rag(  # noqa: PLR0913
    prompt: str,
    *,
    max_contexts: int = 5,
    context_neighbors: tuple[int, ...] | None = (-1, 1),
    search: SearchMethod | list[str] | list[Chunk] = hybrid_search,
    messages: list[dict[str, str]] | None = None,
    system_prompt: str = RAG_SYSTEM_PROMPT,
```

`max_tokens`와 `temperature`가 이 목록에 없다는 것이 `handle_fallback`이 항상 실패하는 이유입니다.

### Step 7. Streamlit 조립과 실행 — 어디까지 가는가

**목적.** `main()`이 설정 화면부터 채팅 루프까지 어떻게 잇는지 보고, `python local_main.py`를 그대로 실행하면 정확히 어느 줄에서 멈추는지 확인합니다. 질문 하나에 `hybrid_search`가 실제로 몇 번 실행되는지도 여기서 확인합니다.

**할 일.**

`rag_tutorials/local_hybrid_search_rag/local_main.py:124-129`

```python
def main():
    st.set_page_config(page_title="Local LLM-Powered Hybrid Search-RAG Assistant", layout="wide")
    
    for state_var in ['chat_history', 'documents_loaded', 'my_config']:
        if state_var not in st.session_state:
            st.session_state[state_var] = [] if state_var == 'chat_history' else False if state_var == 'documents_loaded' else None
```

`rag_tutorials/local_hybrid_search_rag/local_main.py:212-222`

```python
                try:
                    reranked_chunks = perform_search(query=user_input)
                    if not reranked_chunks or len(reranked_chunks) == 0:
                        logger.info("No relevant documents found. Falling back to local LLM.")
                        with st.spinner("Using general knowledge to answer..."):
                            full_response = handle_fallback(user_input)
                            if full_response.startswith("I apologize"):
                                st.warning("No relevant documents found and fallback failed.")
                            else:
                                st.info("Answering from general knowledge.")
                    else:
```

이 앱의 파일 맨 위 import(`rag_tutorials/local_hybrid_search_rag/local_main.py:4`)가 `from raglite import ...`이므로, Step 1의 `llama_cpp` 부재 때문에 `streamlit run local_main.py`는 사이드바나 제목이 뜨기도 전에 스크립트 실행 자체가 맨 처음 줄에서 실패합니다 — Streamlit은 이런 경우에도 정적 셸(HTTP 200)은 응답하지만, 그 안에는 이 예외가 표시됩니다. 그리고 213행의 `perform_search` 호출을 보면, 이 함수가 돌려주는 `reranked_chunks`는 "있는지 없는지"만 검사될 뿐(214행) 정상 경로(else 블록, Step 6에서 본 229-236행)에서 그대로 재사용되지 않습니다 — `rag(..., search=hybrid_search, ...)`가 `_contexts()` 내부에서 **다시** `hybrid_search`를 호출합니다(이번엔 `num_results=max_contexts+extra_contexts`인 20개 후보로, `perform_search`의 10개와 다른 크기입니다). 즉 검색 결과가 있는 매 질문마다 `hybrid_search`(키워드+벡터+RRF 전부)가 서로 다른 후보 수로 **두 번** 실행됩니다 — 한 번은 폴백 여부를 결정하기 위해, 한 번은 실제 답변 컨텍스트를 만들기 위해서입니다.

**그림.**

![Step 7까지의 구성](diagrams/step7.svg)

**확인.** 파일이 어느 import에서 멈추는지 직접 확인합니다.

```bash
uv run --no-project python -m py_compile local_main.py && echo compiled
uv run --no-project python -c "import local_main"
```

직접 확인한 출력:

```
compiled
```

```
  File "local_main.py", line 4, in <module>
    from raglite import RAGLiteConfig, insert_document, hybrid_search, retrieve_chunks, rerank_chunks, rag
  ...
ModuleNotFoundError: No module named 'llama_cpp'
```

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

사용자가 질문을 보내면 Streamlit UI는 먼저 `perform_search`로 하이브리드 검색을 한 번 돌립니다 — 데이터베이스에 키워드 검색과 벡터 검색을 각각 요청하고, 두 순위 목록을 RRF(k=60)로 합친 상위 10개를 재순위화 모델(FlashRank)에 보내 다시 정렬합니다. 이 결과는 "검색된 것이 있는가"를 판단하는 데만 쓰이고, 실제 답변을 만드는 단계에서는 버려집니다 — UI는 `rag()`를 호출하고, `rag()`는 내부적으로 하이브리드 검색과 재순위화를 후보 수를 바꿔(20개) **다시** 실행한 뒤, 그렇게 얻은 컨텍스트를 시스템 프롬프트에 넣어 로컬 LLM에 스트리밍 생성을 요청합니다. 토큰이 도착할 때마다 화면에 이어붙여 표시되고, 완성된 답이 대화 기록에 저장됩니다. 이 그림은 검색 결과가 있는 경우의 경로만 그린 것입니다 — 결과가 없으면 대신 `handle_fallback`이 불리는데, 이 함수가 넘기는 `max_tokens`·`temperature` 인자를 raglite 0.2.1의 `rag()`가 모르기 때문에 그 호출은 항상 `TypeError`로 끝나고 함수 자신의 `except`가 이를 삼켜 사과 메시지만 돌려줍니다(Step 6). 이 전체 시퀀스는 Step 1에서 확인한 `llama_cpp` 부재 때문에 처음부터 끝까지 한 번에 재현하지는 못했고, RRF 융합(Step 4)과 재순위화(Step 5)는 각각 라이브러리 소스를 그대로 옮겨 실행하거나 실제 모델을 내려받아 개별적으로 확인한 것을 이어붙인 것입니다.

## 실행 체크리스트

- [ ] `llama-cpp-python`이 오늘 기준 0.2.56~0.3.35 어느 버전도 어떤 플랫폼에도 사전 빌드 wheel을 올리지 않는다는 것을 PyPI 메타데이터로 확인했다
- [ ] 이 컴퓨터에 CMake와 MSVC(Visual Studio)가 실제로 있고 빌드 도중 `cl.exe`·`link.exe`가 호출되는데도, 소스 빌드가 20분 안에 끝나지 않는다는 것을 직접 확인했다
- [ ] Python 3.13에서는 `spacy`·`thinc`·`blis`도 wheel이 없어 컴파일이 필요하고, `blis` 0.7.11이 Cython 3.x와 맞지 않아 실패한다는 것을 확인했다 — spaCy 언어 모델 wheel 하나만 받으려 해도 같은 벽에 부딪힌다
- [ ] 네 개의 정확한 버전 고정(raglite/pydantic/rerankers/flashrank)이 오늘도 116개 패키지로 함께 풀리고, 그 안에 `llama-cpp-python`이 raglite 자신의 전이 의존성으로 포함된다는 것을 확인했다
- [ ] raglite의 `db_url` 기본값이 `sqlite:///raglite.sqlite`이고 PostgreSQL·SQLite 둘 다 정식 경로라는 것을 소스로 확인했다 — 이 앱의 UI는 검사하지 않지만 앱 자체 README는 PostgreSQL만 안내한다
- [ ] `hybrid_search`가 키워드 검색과 벡터 검색을 각각 최대 100개까지 뽑아 Reciprocal Rank Fusion(`1/(60+순위)`의 합)으로 융합한다는 것을 소스로 확인하고 같은 공식을 직접 실행해 재현했다
- [ ] 재순위화 모델(FlashRank ms-marco-MiniLM-L-12-v2)을 실제로 내려받아(zip 22.7MB, ONNX 34.0MB) 실제 문장 3개를 재정렬해 봤다
- [ ] `handle_fallback`의 `rag()` 호출이 오늘 버전에 없는 키워드 인자(`max_tokens`, `temperature`) 때문에 항상 `TypeError`로 실패하고 자기 자신의 `except`가 이를 삼킨다는 것을 시그니처 대조로 확인했다
- [ ] 검색 결과가 있는 질문마다 `hybrid_search`가 서로 다른 후보 수로 두 번(폴백 판단용 10개, 실제 컨텍스트용 20개) 실행된다는 것을 코드로 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `uv pip install llama-cpp-python`이 "Building llama-cpp-python==0.3.35"에서 몇 분 넘게 멈춰 있음 | 모든 버전이 sdist뿐이라 소스 빌드가 강제되고, ggml/llama.cpp 전체 컴파일에 시간이 오래 걸림(직접 확인, 컴파일러 유무와 무관) | 컴파일러가 있어도 수십 분을 기다려야 할 수 있음 — 시간을 넉넉히 잡거나 별도로 미리 빌드된 배포판을 찾아본다 |
| Python 3.13에서 `spacy`/`thinc`/`blis` 설치 시 `Cython.Compiler.Errors.CompileError: blis\py.pyx` | `blis` 0.7.11의 `.pyx`가 Cython 3.x의 `nogil` 제약과 맞지 않고, 세 패키지 모두 cp313 wheel이 없음(직접 확인) | `uv venv --python 3.12`처럼 3.10~3.12로 내리면 이 벽은 피함(단 `llama-cpp-python` 벽은 별개로 남음) |
| `handle_fallback`을 거치면 항상 "I apologize, but I encountered an error while processing your request."만 나옴 | `rag(..., max_tokens=1024, temperature=0.7, ...)`가 raglite 0.2.1의 `rag()`에 없는 키워드 인자를 넘겨 `TypeError`가 나고, 같은 함수의 `except`가 이를 삼킴(소스 대조로 확인) | 리포 코드는 고치지 않는 것이 이 시리즈의 방침 — 고친다면 `max_tokens`/`temperature`를 빼거나 `search=hybrid_search`로 바꿔야 함 |
| "Database URL"에 PostgreSQL이 아닌 문자열을 넣으면 동작이 불확실해 보임 | raglite는 `postgresql`·`sqlite` 두 스킴만 인식함(소스로 확인) | `sqlite:///로컬파일명.db` 형식이면 서버 없이 동작할 것으로 보임(소스로 확인 — `llama_cpp` 부재로 이 문서에서 끝까지 실행하지는 못함) |
| `flashrank.Ranker` 생성 시 `requests.exceptions.SSLError: ... SSLEOFError`로 모델 다운로드 실패 | 이 환경의 파이썬 `requests`/OpenSSL 스택이 huggingface.co와의 TLS 핸드셰이크를 간헐적으로 실패시킴(직접 확인) — 모델·URL 자체의 문제는 아님 | 같은 URL을 `curl`로 받으면 문제없이 완료됨(직접 확인) — 재시도하거나 `curl`로 받아 캐시 디렉터리에 직접 넣어두는 우회가 가능 |

## 더 해보기

- `sys.modules['llama_cpp']`에 `llama_supports_gpu_offload`·`Llama`·`LLAMA_POOLING_TYPE_NONE`만 갖춘 가짜 모듈을 미리 넣어 `from raglite import RAGLiteConfig`(`rag_tutorials/local_hybrid_search_rag/local_main.py:4`)를 우회하고, `RAGLiteConfig(db_url="sqlite:///test.db", ...)`가 정말 서버 없이 로컬 파일을 만드는지 실험해보기
- `initialize_config`(`rag_tutorials/local_hybrid_search_rag/local_main.py:41-48`)의 `reranker=` 자리를 raglite 기본값처럼 언어별 튜플(`(("en", ...), ("other", ...))`)로 바꿔, 영어가 아닌 문서에서 재순위화 결과가 달라지는지 비교해보기
- `perform_search`(`rag_tutorials/local_hybrid_search_rag/local_main.py:86-94`)가 돌려주는 `reranked_chunks`를 버리지 않고 `rag()`의 `search=`에 직접 넘기도록 고쳐, 질문당 `hybrid_search`가 한 번만 실행되도록 만들어보기

## 다음 날 예고

[Day 056 · 🩺 RAG Failure Diagnostics Clinic](../day056-rag-failure-diagnostics-clinic/README.md) — 검색과 재순위화가 개별적으로 어떻게 어긋날 수 있는지를 오늘 하나씩 봤다면, 내일은 RAG 파이프라인의 실패 유형을 진단하는 방법 자체를 다룹니다.
