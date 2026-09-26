# Day 064 · 🐋 Deepseek Local RAG Agent

> 볼륨 5 📀 RAG · 난이도 ★★☆ · 예상 소요 90분(가짜 로컬 Ollama 서버를 여러 스텝에 걸쳐 띄우고 `AppTest`로 직접 왕복시켜 보는 손 작업이 읽는 시간보다 깁니다) · API 비용 대략 확인 불가(Qdrant Cloud·Exa AI 모두 가입이 필요한 관리형 서비스라 요금표를 확인하지 못했습니다 — 로컬 모델 추론 자체는 무료입니다) · 원본 앱: `rag_tutorials/deepseek_local_rag_agent`

## 오늘 만들 것

이 앱은 DeepSeek R1 추론 모델을 Ollama로 로컬 실행하면서 Qdrant Cloud 벡터 저장소와 Exa AI 웹 검색까지 얹은 526줄(마지막 줄에 개행이 없어 `wc -l`은 525로 세지만 편집기·GitHub에서는 526번째 줄까지 보입니다, 직접 확인) 단일 파일 Streamlit 앱입니다. 이름과 달리 "로컬"인 것은 모델 추론뿐입니다 — RAG 모드는 기본으로 켜져 있고, 그 벡터 저장소는 로컬 Qdrant가 아니라 `QdrantClient(url=..., api_key=...)`로 접속하는 Qdrant **Cloud**입니다(소스로 확인). `requirements.txt` 8줄을 그대로 설치하면 6번째 줄의 `import bs4`부터 `ModuleNotFoundError`로 막힙니다 — `beautifulsoup4`가 8개 의존성 어디에도 없기 때문입니다(직접 확인, Step 1). 반대로 Day 047이 겪었던 `ImportError: openai not installed`는 이 앱에서는 일어나지 않습니다 — `exa-py`가 자체적으로 `openai>=1.48`을 요구해 함께 설치되기 때문입니다(직접 확인). 임베딩은 `agno`의 `OllamaEmbedder`를 LangChain의 `Embeddings` 인터페이스로 감싼 `OllamaEmbedderr`(오타가 아니라 실제 클래스 이름입니다) 클래스가 맡고, 기본값을 `snowflake-arctic-embed`/1024차원으로 명시적으로 고정합니다. 채팅 모델은 사이드바에서 `deepseek-r1:1.5b`·`:7b` 중 고르지만, 웹 검색 실패 시 쓰는 보조 에이전트는 `llama3.2`로 하드코딩돼 있어 고를 수 없습니다.

API 키도, 큰 로컬 모델 다운로드도 없이 확인하기 위해 이 문서는 실제 Ollama 데몬 대신 이 PC의 다른 포트에 가짜 로컬 서버를 띄워 채팅(`/api/chat`)·임베딩(`/api/embed`) 왕복을 실제로 재현합니다(Step 2·5). 그 과정에서 흥미로운 사실 하나를 직접 확인했습니다 — 이 앱이 자랑하는 "Thinking process visualization" 기능은 지금 새로 설치되는 agno(3.0.11)에서는 절대 작동하지 않습니다. agno의 `Ollama` 모델이 `<think>` 태그를 응답 파싱 단계에서 이미 떼어 `reasoning_content`로 옮겨 버려서, 이 앱이 497~507행에서 다시 찾는 정규식이 항상 빈손을 짚기 때문입니다(Step 6에서 직접 재현). 완성하면 브라우저에는 문서 업로드 사이드바와 채팅창이 뜨지만, 이 문서는 키가 없어 실제 Qdrant Cloud·Exa 호출은 하지 않고 로컬 스텁으로 배선만 확인합니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| Ollama | `deepseek-r1:1.5b`·`deepseek-r1:7b`(채팅, 택1) · `snowflake-arctic-embed`(임베딩) · `llama3.2`(웹 검색용 채팅) 네 모델을 서빙하는 로컬 데몬 | https://ollama.com 설치 후 `ollama pull deepseek-r1:1.5b`(또는 `:7b`)·`ollama pull snowflake-arctic-embed`·`ollama pull llama3.2` — 이 문서는 받지 않습니다(이 PC에는 대신 `deepseek-r1:8b`·`llama3.2`가 이미 있었고, `ollama list`로 확인만 했습니다) |
| Qdrant Cloud | RAG 모드의 벡터 저장소(로컬 Qdrant 서버가 아닙니다) | https://cloud.qdrant.io 가입 → 클러스터 생성 → API Key·URL 발급 후 사이드바에 입력(이 문서는 키가 없어 실행하지 않습니다) |
| Exa AI (선택) | 사이드바의 "Enable Web Search Fallback"을 켰을 때만 필요 | https://exa.ai 가입 후 API Key 발급 |
| beautifulsoup4 | `requirements.txt`에 없지만 6행의 `import bs4`에 필요합니다(Step 1) | `uv pip install beautifulsoup4` 별도 설치 |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 절 참고 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| Streamlit UI | 사이드바 설정(모델·RAG 토글·키)과 채팅 루프 오케스트레이션 | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:71-143` |
| 문서 처리 | PDF·웹페이지를 1000자 청크(겹침 200자)로 분할, 소스 메타데이터 부착 | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:167-221` |
| RAG 에이전트 | 검색된 문맥(또는 웹 검색 결과)을 프롬프트에 담아 채팅 모델에 전달 | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:279-301` |
| 웹 검색 에이전트 | Exa 도구를 쥔 별도 agno `Agent`, RAG 실패 시 폴백 | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:259-276` |
| 채팅 모델 (deepseek-r1, Ollama, 로컬) | 최종 답변 생성, 사이드바에서 1.5b/7b 중 선택 | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:283` |
| 임베딩 모델 (snowflake-arctic-embed, Ollama, 로컬) | 청크·질문 텍스트를 1024차원 벡터로 변환 | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:19-33` |
| 웹검색 모델 (llama3.2, Ollama, 로컬) | 웹 검색 에이전트 전용 채팅 모델(선택 불가, 하드코딩) | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:263` |
| Qdrant Cloud | 청크 벡터+원문을 저장하는 클라우드 벡터 저장소, 컬렉션 `test-deepseek-r1` | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:146-163` |
| Exa AI 검색 | 관련 문서가 없을 때(또는 강제 토글 시) 웹 검색 수행 | `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:264-268` |

## 단계별 진행

### Step 1. 환경 만들기 — requirements.txt에 없는 bs4, 그리고 openai를 비껴간 이유

**목적.** 격리된 가상환경에 8줄짜리 `requirements.txt`를 설치하고, 오늘 실제로 풀리는 버전에서 10개 import가 정말 되는지 확인합니다.

**할 일.**

```bash
cd rag_tutorials/deepseek_local_rag_agent
uv venv
uv pip install -r requirements.txt
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.) 이 저장소 루트에는 `pyproject.toml`이 있어 이후 `uv run` 명령에는 모두 `--no-project`를 붙입니다.

`rag_tutorials/deepseek_local_rag_agent/requirements.txt:1-8`

```text
agno>=2.2.10
pypdf
exa-py
qdrant-client==1.12.1
langchain-qdrant==0.2.0
langchain-community==0.3.13
streamlit==1.41.1
ollama
```

이 문서를 쓰며 설치했을 때는 **agno 3.0.11**, **exa-py 2.22.2**, **qdrant-client 1.12.1**(고정), **langchain-qdrant 0.2.0**(고정), **langchain-community 0.3.13**(고정), **streamlit 1.41.1**(고정), **ollama(파이썬 클라이언트) 0.6.2**, **pypdf 6.19.0**이 받아졌습니다(직접 확인, 2026-09-26 기준). 눈에 띄는 것은 **openai 3.19.2가 요청하지 않았는데도 자동으로 설치**됐다는 점입니다 — Day 047이 같은 `agno>=2.2.10` 하한에서 `ImportError: openai not installed`를 겪었던 것과 달리, 이 앱은 `exa-py`를 함께 쓰기 때문에 그 문제를 피해 갑니다.

```bash
uv run --no-project python -c "
import importlib.metadata as m
print('exa-py requires:')
for r in sorted(m.requires('exa-py') or []):
    print(' ', r)
"
```

직접 확인한 출력:

```
exa-py requires:
  httpcore (>=1.0.9)
  httpx (>=0.28.1)
  openai (>=1.48)
  pydantic (>=2.10.6)
  python-dotenv (>=1.0.1)
  requests (>=2.32.3)
  typing-extensions (>=4.12.2)
```

`py_compile`은 바로 통과합니다.

```bash
uv run --no-project python -m py_compile deepseek_rag_agent.py && echo compiled
```

```
compiled
```

하지만 파일을 실제로 import하면(예: `streamlit run`이 내부적으로 하는 것과 같은 동작) 6번째 줄에서 막힙니다.

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:1-16`

```python
import os
import tempfile
from datetime import datetime
from typing import List
import streamlit as st
import bs4
from agno.agent import Agent
from agno.models.ollama import Ollama
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.embeddings import Embeddings
from agno.tools.exa import ExaTools
from agno.knowledge.embedder.ollama import OllamaEmbedder
```

```bash
uv run --no-project python -c "import bs4"
```

직접 확인한 출력:

```
ModuleNotFoundError: No module named 'bs4'
```

`beautifulsoup4`는 8개 의존성 중 어느 것도 전이 설치하지 않습니다 — `langchain-community`의 `WebBaseLoader`가 내부적으로 쓰지만, 그 의존성 자체는 선택 사항(extra)으로 분리돼 있어 기본 설치에 딸려오지 않습니다. (참고로 1행의 `import os`는 파일 전체에서 실제로 한 번도 쓰이지 않는 죽은 import입니다 — 직접 확인.)

```bash
uv pip install beautifulsoup4
```

```bash
uv run --no-project python -c "
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.exa import ExaTools
from agno.knowledge.embedder.ollama import OllamaEmbedder
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_core.embeddings import Embeddings
print('ALL IMPORTS OK')
"
```

**그림.**

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 위 설치까지 마치면 10개 import가 모두 성공합니다(직접 확인).

```
ALL IMPORTS OK
```

### Step 2. 두 얼굴의 Ollama — 채팅 모델 선택과 임베딩 클래스

**목적.** 사이드바가 만드는 `model_version` 값과, 임베딩을 LangChain 인터페이스로 감싸는 `OllamaEmbedderr` 클래스를 확인하고, 실제 모델을 내려받지 않고도 두 경로가 살아 있는지 가짜 로컬 서버로 검증합니다.

**할 일.**

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:19-33`

```python
class OllamaEmbedderr(Embeddings):
    def __init__(self, model_name="snowflake-arctic-embed"):
        """
        Initialize the OllamaEmbedderr with a specific model.

        Args:
            model_name (str): The name of the model to use for embedding.
        """
        self.embedder = OllamaEmbedder(id=model_name, dimensions=1024)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self.embedder.get_embedding(text)
```

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:74-86`

```python
st.sidebar.header("📦 Model Selection")
model_help = """
- 1.5b: Lighter model, suitable for most laptops
- 7b: More capable but requires better GPU/RAM

Choose based on your hardware capabilities.
"""
st.session_state.model_version = st.sidebar.radio(
    "Select Model Version",
    options=["deepseek-r1:1.5b", "deepseek-r1:7b"],
    help=model_help
)
st.sidebar.info("Run ollama pull deepseek-r1:7b or deepseek-r1:1.5b respectively")
```

`OllamaEmbedderr`는 사이드바 어디에도 노출되지 않습니다 — 임베딩 모델은 `snowflake-arctic-embed`/1024차원으로 코드에 고정돼 있고, 바뀔 수 있는 것은 채팅 모델(`model_version`)뿐입니다. 이 둘이 실제로 어디로 요청을 보내는지 보려고, Ollama 데몬 대신 이 PC의 11499 포트에 두 엔드포인트(`/api/chat`, `/api/embed`)만 흉내 내는 가짜 서버를 띄웁니다.

```bash
cat > fake_ollama.py <<'PY'
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class FakeOllama(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("content-length", 0))
        json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/chat":
            reply = {"message": {"role": "assistant", "content": "FAKE_OLLAMA_REPLY: 2+2=4"}, "done": True}
        else:
            reply = {"embeddings": [[0.001] * 1024]}
        data = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *a):
        pass

ThreadingHTTPServer(("127.0.0.1", 11499), FakeOllama).serve_forever()
PY
uv run --no-project python fake_ollama.py &
```

`agno`가 감싸는 `ollama` 파이썬 클라이언트는 `host=`를 안 주면 `OLLAMA_HOST` 환경변수를 봅니다(소스로 확인, `ollama` 0.6.2의 `_client.py`). 이 변수 하나로 앱 코드를 고치지 않고도 가짜 서버로 돌립니다.

```bash
OLLAMA_HOST=http://127.0.0.1:11499 uv run --no-project python -c "
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.knowledge.embedder.ollama import OllamaEmbedder
agent = Agent(name='DeepSeek RAG Agent', model=Ollama(id='deepseek-r1:1.5b'))
resp = agent.run('What is 2+2?')
print('chat content:', resp.content)
vec = OllamaEmbedder(id='snowflake-arctic-embed', dimensions=1024).get_embedding('hello')
print('embedding length:', len(vec))
"
```

PowerShell: `$env:OLLAMA_HOST="http://127.0.0.1:11499"; uv run --no-project python -c "..."`

**그림.**

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** 직접 확인한 출력(실제 모델도, 실제 Ollama 데몬도 쓰지 않습니다):

```
chat content: FAKE_OLLAMA_REPLY: 2+2=4
embedding length: 1024
```

### Step 3. Qdrant Cloud 벡터 저장소 — 그리고 한 번도 불려 가지 않는 함수

**목적.** `init_qdrant`·`create_vector_store`가 정말 클라우드 REST 엔드포인트를 쓰는지, 키가 없을 때 어떻게 조용히 실패하는지, 그리고 `check_document_relevance`가 죽은 코드라는 것을 확인합니다.

**할 일.**

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:146-163`

```python
def init_qdrant() -> QdrantClient | None:
    """Initialize Qdrant client with configured settings.

    Returns:
        QdrantClient: The initialized Qdrant client if successful.
        None: If the initialization fails.
    """
    if not all([st.session_state.qdrant_api_key, st.session_state.qdrant_url]):
        return None
    try:
        return QdrantClient(
            url=st.session_state.qdrant_url,
            api_key=st.session_state.qdrant_api_key,
            timeout=60
        )
    except Exception as e:
        st.error(f"🔴 Qdrant connection failed: {str(e)}")
        return None
```

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:36-37`

```python
# Constants
COLLECTION_NAME = "test-deepseek-r1"
```

`create_vector_store`(225-257행)는 컬렉션이 이미 있으면 나는 예외를 **문자열 매칭**으로 구분합니다 — `if "already exists" not in str(e).lower(): raise e`. Qdrant 서버가 실제로 그 문구를 쓰는 한에서만 통하는 다소 위태로운 패턴입니다(소스로 확인). 이 문서는 Qdrant Cloud 키가 없어 이 함수까지 실행하지 않지만, `init_qdrant()`가 키 없이 예외 없이 `None`을 돌려준다는 것은 Step 7의 전체 부팅 확인에서 다시 나옵니다.

한편 306~316행의 `check_document_relevance`는 정의만 되고 실제 호출부가 없습니다 — 실제 유사도 검색은 393~405행(Step 5)에서 같은 로직을 다시 인라인으로 씁니다.

```bash
grep -n "check_document_relevance" deepseek_rag_agent.py
```

직접 확인한 출력(정의 한 줄뿐, 호출은 없음):

```
306:def check_document_relevance(query: str, vector_store, threshold: float = 0.7) -> tuple[bool, List]:
```

**그림.**

![Step 3까지의 구성](diagrams/step3.svg)

**확인.** 키 없이 전체 화면을 `AppTest`로 띄우면 `init_qdrant()`가 조용히 `None`을 반환해 예외가 나지 않습니다(Step 7에서 전체 목록을 확인합니다).

```python
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('deepseek_rag_agent.py')
at.run(timeout=30)
print('exception:', list(at.exception))
```

```
exception: []
```

### Step 4. 문서 업로드와 청크화 — 그리고 지워지지 않는 임시 파일

**목적.** PDF·URL이 1000자/겹침 200자 청크가 되는 과정과, `WebBaseLoader`의 클래스 필터가 실제로 무엇을 제한하는지 확인합니다.

**할 일.**

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:167-190`

```python
def process_pdf(file) -> List:
    """Process PDF file and add source metadata."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            loader = PyPDFLoader(tmp_file.name)
            documents = loader.load()
            
            # Add source metadata
            for doc in documents:
                doc.metadata.update({
                    "source_type": "pdf",
                    "file_name": file.name,
                    "timestamp": datetime.now().isoformat()
                })
                
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            return text_splitter.split_documents(documents)
    except Exception as e:
        st.error(f"📄 PDF processing error: {str(e)}")
        return []
```

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:196-203`

```python
        loader = WebBaseLoader(
            web_paths=(url,),
            bs_kwargs=dict(
                parse_only=bs4.SoupStrainer(
                    class_=("post-content", "post-title", "post-header", "content", "main")
                )
            )
        )
```

`class_=(...)`는 이 다섯 CSS 클래스를 가진 태그만 남기고 나머지는 버립니다 — 블로그 플랫폼(Substack 등)에는 맞지만, 이 클래스명이 없는 일반 사이트에서는 본문이 통째로 걸러져 빈 문서가 될 수 있습니다(소스로 확인). `process_pdf`는 업로드된 PDF를 `tempfile.NamedTemporaryFile(delete=False, ...)`로 디스크에 쓰는데, `delete=False`이면 `with` 블록이 끝나도 파일이 지워지지 않고, 이 함수 어디에도 이후 `os.remove`가 없습니다(직접 확인) — 업로드할 때마다 임시 파일이 하나씩 쌓입니다.

```bash
uv run --no-project python -c "
import tempfile, os
with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
    tmp_file.write(b'%PDF-1.4 fake content')
    path = tmp_file.name
print('exists right after the with-block exits:', os.path.exists(path))
os.remove(path)
"
```

**그림.**

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** 직접 확인한 출력(같은 `delete=False` 패턴을 재현):

```
exists right after the with-block exits: True
```

### Step 5. 질의 처리 — 유사도 검색과 웹 검색 폴백의 순서

**목적.** 질문이 Qdrant 검색 → (조건부) Exa 웹 검색 → 채팅 모델 순으로 흐르는 정확한 조건을 확인하고, 가짜 로컬 서버로 전체 왕복을 재현합니다.

**할 일.**

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:393-405`

```python
            if not st.session_state.force_web_search and st.session_state.vector_store:
                # Try document search first
                retriever = st.session_state.vector_store.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "k": 5, 
                        "score_threshold": st.session_state.similarity_threshold
                    }
                )
                docs = retriever.invoke(rewritten_query)
                if docs:
                    context = "\n\n".join([d.page_content for d in docs])
                    st.info(f"📊 Found {len(docs)} relevant documents (similarity > {st.session_state.similarity_threshold})")
```

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:409-424`

```python
            # Step 3: Use web search if:
            # 1. Web search is forced ON via toggle, or
            # 2. No relevant documents found AND web search is enabled in settings
            if (st.session_state.force_web_search or not context) and st.session_state.use_web_search and st.session_state.exa_api_key:
                with st.spinner("🔍 Searching the web..."):
                    try:
                        web_search_agent = get_web_search_agent()
                        web_results = web_search_agent.run(rewritten_query).content
                        if web_results:
                            context = f"Web Search Results:\n{web_results}"
                            if st.session_state.force_web_search:
                                st.info("ℹ️ Using web search as requested via toggle.")
                            else:
                                st.info("ℹ️ Using web search as fallback since no relevant documents were found.")
                    except Exception as e:
                        st.error(f"❌ Web search error: {str(e)}")
```

웹 검색은 `force_web_search` 토글이 켜져 있거나 문맥이 비어 있을 때, **그리고** `use_web_search`가 켜져 있고 `exa_api_key`가 있을 때만 실행됩니다 — 셋 중 하나라도 빠지면 조용히 건너뜁니다. `vector_store`가 아예 없으면(이 문서처럼 Qdrant 키가 없으면) 검색 자체를 시도하지 않고 바로 이 조건으로 넘어갑니다. `OLLAMA_HOST`를 Step 2의 가짜 서버로 돌린 채 `AppTest`로 전체 채팅 한 턴을 재현합니다.

```python
import os
os.environ["OLLAMA_HOST"] = "http://127.0.0.1:11499"
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('deepseek_rag_agent.py')
at.run(timeout=30)
at.chat_input[0].set_value("What is 2+2?").run(timeout=30)
print('exception:', list(at.exception))
print('info banners:', [i.value for i in at.info])
for m in at.chat_message:
    print(' -', m.name, [w.value for w in m.markdown])
```

**그림.**

![Step 5까지의 구성](diagrams/step5.svg)

**확인.** 직접 확인한 출력(`vector_store`가 없어 "관련 정보 없음" 안내 후 채팅 모델로 바로 감):

```
exception: []
info banners: ['ℹ️ No relevant information found in documents or web search.', 'Run ollama pull deepseek-r1:7b or deepseek-r1:1.5b respectively']
 - user ['What is 2+2?']
 - assistant ['FAKE_OLLAMA_REPLY: 2+2=4']
```

### Step 6. "생각 과정 시각화"가 사라진 이유 — agno가 먼저 태그를 떼어 간다

**목적.** 이 앱이 직접 하는 `<think>` 정규식 분리가 지금 agno에서 왜 한 번도 매치되지 않는지, 그 텍스트가 실제로 어디로 가는지 확인합니다.

**할 일.**

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:497-507`

```python
                # Extract thinking process and final response
                import re
                think_pattern = r'<think>(.*?)</think>'
                think_match = re.search(think_pattern, response_content, re.DOTALL)
                
                if think_match:
                    thinking_process = think_match.group(1).strip()
                    final_response = re.sub(think_pattern, '', response_content, flags=re.DOTALL).strip()
                else:
                    thinking_process = None
                    final_response = response_content
```

agno 3.0.11의 `Ollama` 모델(`_parse_provider_response` 메서드, 소스로 확인)은 응답에 `<think>`가 있으면 **모델 호출 직후** `extract_thinking_content()`로 그 블록을 떼어 `response.reasoning_content`에 옮기고, `response.content`에는 `</think>` 뒤에 남은 텍스트만 남깁니다. 즉 이 앱의 코드가 497행에 도달했을 때는 `response_content`에 `<think>` 자체가 이미 없어서, `think_match`는 항상 `None`이고 "🤔 See thinking process" 확장 패널은 **한 번도 나타나지 않습니다** — RAG 모드에서도, 단순 모드에서도 마찬가지입니다. 텍스트가 사라지는 것은 아니고 `reasoning_content`에 남아 있지만, 이 앱은 그 필드를 어디서도 읽지 않습니다.

```bash
OLLAMA_HOST=http://127.0.0.1:11499 uv run --no-project python -c "
from agno.agent import Agent
from agno.models.ollama import Ollama
agent = Agent(name='t', model=Ollama(id='deepseek-r1:1.5b'))
resp = agent.run('What is 2+2?')
print('content:', repr(resp.content))
print('reasoning_content:', repr(getattr(resp, 'reasoning_content', 'NO ATTR')))
"
```

(이 명령을 실행하려면 Step 2의 `fake_ollama.py`를 응답에 `<think>2+2 is basic addition, sum is 4</think>The answer is 4.`를 담도록 잠깐 바꿔야 합니다 — 아래 확인 출력은 그렇게 바꾼 채로 직접 실행한 결과입니다.)

**그림.**

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** 직접 확인한 출력:

```
content: 'The answer is 4.'
reasoning_content: '2+2 is basic addition, sum is 4'
```

### Step 7. 실행 확인 — 키 없이 어디까지 뜨는가

**목적.** `streamlit run` 전체를 키 없이 `AppTest`로 실행해 정말 예외 없이 뜨는지, 그리고 idle 화면의 안내문이 실제로 RAG 모드 상태와 무관하다는 것을 확인합니다.

**할 일.**

`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:90`, `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:371-376`, `rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:525-526`

```python
st.session_state.rag_enabled = st.sidebar.toggle("Enable RAG Mode", value=st.session_state.rag_enabled)
```

```python
if prompt:
    # Add user message to history
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
```

```python
else:
    st.warning("You can directly talk to r1 locally! Toggle the RAG mode to upload documents!")
```

마지막 `else`는 `rag_enabled`가 아니라 **`if prompt:`**(371행)에 걸려 있습니다 — 즉 질문을 아직 입력하지 않은 첫 화면에서는 RAG 모드가 켜져 있든(기본값) 꺼져 있든 항상 이 문구가 뜹니다. "RAG 모드를 켜서 업로드하라"는 문구인데, 정작 RAG 모드는 이미 켜져 있고 업로드 UI도 사이드바에 이미 떠 있는 상태에서도 나타납니다.

```bash
PYTHONIOENCODING=utf-8 uv run --no-project python -c "
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('deepseek_rag_agent.py')
at.run(timeout=30)
print('exception:', list(at.exception))
print('sidebar toggle:', [(t.label, t.value) for t in at.sidebar.toggle])
print('warnings:', [w.value for w in at.warning])
print('chat_input placeholder:', [c.placeholder for c in at.chat_input])
"
```

**그림.**

![Step 7까지의 구성](diagrams/step7.svg)

**확인.** 직접 확인한 출력:

```
exception: []
sidebar toggle: [('Enable RAG Mode', True)]
warnings: ['You can directly talk to r1 locally! Toggle the RAG mode to upload documents!']
chat_input placeholder: ['Ask about your documents...']
```

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

사용자가 채팅창에 질문을 입력하면, Streamlit UI는 먼저 임베딩 모델에 질문 임베딩을 요청해 1024차원 벡터를 받고, 그 벡터로 Qdrant Cloud에 유사도 검색(`threshold=0.7`)을 보내 관련 청크 목록을 돌려받습니다. 이 결과를 문맥으로 묶은 프롬프트를 RAG 에이전트에 넘기면, 에이전트는 채팅 모델(`deepseek-r1`)에 완성을 요청하고 받은 답변 텍스트를 그대로 UI에 돌려주며, UI는 답변과 (있다면) 출처를 화면에 표시합니다. 이 그림은 Qdrant가 관련 문서를 찾은 경우를 그린 것입니다 — 문서가 없으면 Step 5에서 본 대로 Exa 웹 검색으로 갈라지거나, 그마저 없으면 문맥 없이 곧바로 채팅 모델로 갑니다.

## 실행 체크리스트

- [ ] `uv venv && uv pip install -r requirements.txt`만으로는 6행의 `import bs4`에서 실패하고, `beautifulsoup4`를 따로 설치해야 한다는 것을 확인했다
- [ ] `exa-py`가 `openai`를 함께 설치해 Day 047의 `ImportError`를 이 앱은 겪지 않는다는 것을 `importlib.metadata`로 확인했다
- [ ] `init_qdrant()`가 키 없이도 예외 없이 `None`을 반환하고, `AppTest`로 전체 화면이 뜬다는 것을 확인했다
- [ ] `check_document_relevance`가 정의만 되고 실제 호출부는 없다는 것을 grep으로 확인했다
- [ ] 가짜 로컬 Ollama 서버로 채팅(`/api/chat`)과 임베딩(`/api/embed`) 왕복이 실제로 되는 것을 확인했다(모델 다운로드 없이)
- [ ] agno가 `<think>` 태그를 자동으로 떼어 `reasoning_content`에 저장하며, 이 앱의 정규식 분리는 더 이상 매치되지 않는다는 것을 확인했다
- [ ] idle 화면의 경고문이 RAG 모드 토글 상태와 무관하게 항상 뜬다는 것을 `AppTest`로 확인했다
- [ ] `process_pdf`가 만드는 임시 PDF 파일이 `delete=False`로 인해 정리되지 않는다는 것을 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `streamlit run deepseek_rag_agent.py` 실행 즉시 `ModuleNotFoundError: No module named 'bs4'` | `requirements.txt`에 `beautifulsoup4`가 빠져 있고, 8개 의존성 중 어느 것도 이를 전이 설치하지 않음(직접 확인) | `uv pip install beautifulsoup4` 별도 설치 |
| RAG 모드를 켠 채 질문해도 항상 "관련 문서가 없다"는 안내만 나옴 | Qdrant API Key·URL을 넣지 않으면 `init_qdrant()`가 조용히 `None`을 반환해 벡터 저장소 자체가 만들어지지 않음(146-154행) | 사이드바에 실제 Qdrant Cloud API Key와 URL을 입력 |
| RAG 모드를 켰는데도 채팅창 위 안내문이 "RAG 모드를 켜서 업로드하라"고 말함 | 525-526행의 `else`가 `rag_enabled`가 아니라 `if prompt:`에 걸려 있어, 질문을 아직 입력하지 않은 첫 화면에서 RAG 모드 상태와 무관하게 항상 뜸(직접 확인) | 리포 코드는 고치지 않는 것이 이 시리즈의 방침 — 문구를 무시하고 사이드바 토글 상태로 판단 |
| "🤔 See thinking process" 확장 패널이 한 번도 나타나지 않음 | 설치되는 agno(3.0.11)가 `<think>` 태그를 응답 파싱 단계에서 이미 떼어 `reasoning_content`로 옮기므로, 이 앱이 497행 근처에서 다시 찾는 `<think>` 태그가 `response.content`에 남아 있지 않음(직접 확인) | 코드는 고치지 않음 — `response.reasoning_content`를 직접 출력해보기(더 해보기 참고) |
| PDF를 여러 번 업로드하면 임시 파일이 계속 쌓임 | `process_pdf`의 `tempfile.NamedTemporaryFile(delete=False, ...)`가 만든 파일을 이후 어디서도 지우지 않음(직접 확인) | 리포 코드는 고치지 않음 — 필요하면 OS 임시 폴더를 주기적으로 비우기 |

## 더 해보기

- `get_rag_agent()`가 돌려주는 `response.reasoning_content`(Step 6 참고)를 화면에 다시 붙여, agno가 떼어낸 DeepSeek의 실제 추론 과정을 확인해보기
- `check_document_relevance()`(`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:306-316`)를 인라인 검색(`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:393-405`) 대신 실제로 호출하도록 바꿔, 동작이 지금과 같은지 확인해보기
- `similarity_threshold` 슬라이더(`rag_tutorials/deepseek_local_rag_agent/deepseek_rag_agent.py:110-117`)를 0.0까지 낮췄을 때 실제 Qdrant Cloud 클러스터로 항상 문서가 "발견"되는지 확인해보기

## 다음 날 예고

[Day 065 · 🖼️ Vision RAG](../day065-vision-rag/README.md) — Cohere Embed-4로 이미지·PDF 페이지를 직접 임베딩하고 Google Gemini 2.5 Flash로 답하는, OCR 없는 멀티모달 RAG를 다룹니다.
