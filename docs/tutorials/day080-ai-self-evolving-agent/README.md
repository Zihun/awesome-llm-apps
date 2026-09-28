# Day 080 · 🧬 AI Self-Evolving Agent

> 볼륨 7 🚀 Advanced AI Agents · 난이도 ★★☆ · 예상 소요 90분(evoagentx 설치가 세 단계에 걸쳐 실패하는 과정을 직접 재현하고, 그때마다 원인을 패키지 소스로 확인하는 시간이 읽는 시간보다 깁니다) · API 비용 알 수 없음(워크플로우 생성이 만드는 에이전트 수와 각 호출의 토큰 수가 실행마다 달라 사전에 특정 금액을 계산할 수 없습니다 — 코드 경로상 OpenAI gpt-4o-mini 호출이 최소 2회, Anthropic Claude 3.7 Sonnet 호출이 1회는 보장됩니다) · 원본 앱: `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent`

## 오늘 만들 것

오늘 앱(`ai_Self-Evolving_agent.py`, 86줄, 소스로 확인)은 에이전트의 역할이나 프롬프트를 코드로 직접 짜지 않고, EvoAgentX(오늘 기준 PyPI 0.1.4, 직접 확인)라는 프레임워크에 자연어 목표 하나만 던져 워크플로우 자체를 자동으로 설계하게 합니다. 코드는 목표("브라우저에서 플레이할 수 있는 테트리스 게임의 HTML 코드를 생성하라")를 `WorkFlowGenerator`에 넘겨 멀티에이전트 워크플로우 그래프를 만들고(24~25행), `AgentManager`가 그 그래프의 노드마다 실제 에이전트 인스턴스를 등록하며(34~35행), `WorkFlow`가 그 에이전트들을 실행해 코드를 생성합니다(37~38행) — 에이전트가 무엇을 하는지는 실행 시점에 OpenAI `gpt-4o-mini`가 즉석에서 정하므로 코드 어디에도 지시문이 없습니다. 생성된 코드는 그대로 쓰이지 않고, 두 번째 모델(LiteLLM을 통한 Anthropic `claude-3-7-sonnet-20250219`)이 `CodeVerification` 액션으로 검증·수정합니다(41~51행). 이 문서를 쓰며 직접 확인한 것들이 있습니다. 원본 README는 `pip install -r requirements.txt` 뒤에 `pip install git+https://github.com/ANative-Lab/EvoAgentX.git`을 안내하는데, 이 URL 자체는 지금도 유효합니다 — GitHub이 `github.com/EvoAgentX/EvoAgentX`를 이 주소로 301 리다이렉트하는 것으로 직접 확인했습니다(조직 이름이 바뀐 것으로 보입니다). 다만 evoagentx는 이제 PyPI에 배포돼 있어(0.1.4) 소스 빌드 없이 `pip install evoagentx`만으로 설치할 수 있습니다. 그런데 그것만으로는 부족합니다 — 이 스크립트가 쓰는 `evoagentx.workflow`를 import하면 `evoagentx.agents.agent` → `evoagentx.memory.long_term_memory` → `evoagentx.rag`로 이어지는 내부 import 사슬이 그대로 실행되어, 패키지 자신이 선언한 `tools`·`rag`·`multimodal` extra의 의존성(`docker`, `html2text`, `llama_index`, `voyageai` 등)이 하나씩 `ModuleNotFoundError`로 걸립니다(직접 확인, Step 1) — 결국 `pip install "evoagentx[all]"`까지 가야 이 스크립트의 import 8개가 전부 통과합니다. 게다가 evoagentx가 고정하는 `faiss-cpu==1.8.0.post1`은 Python 3.13용 바이너리 휠이 없어(직접 확인) 이 설치 전체가 Python 3.12 이하에서만 됩니다. 이 설치를 다 통과하면, `OPENAI_API_KEY`·`ANTHROPIC_API_KEY` 없이도 `OpenAILLMConfig`·`OpenAILLM`·`WorkFlowGenerator` 객체는 그대로 만들어집니다(직접 확인) — 실패는 실제로 모델을 호출하는 순간에만 일어납니다. 마지막으로 소스로 확인한 구조상의 사실 하나: 이 예시 목표는 검증된 코드가 코드 블록 1개(HTML 하나)로 떨어지므로 56~61행에서 그대로 저장하고 함수가 끝나며, 63행 이후의 `CodeExtraction`(여러 파일로 쪼개 저장하는 경로)은 이 예시에서는 한 번도 실행되지 않습니다. 완성하면 `examples/output/tetris_game/index.html`이 만들어지고 브라우저에서 열립니다. 아래는 완성된 아키텍처입니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| OpenAI API 키 | 워크플로우 생성(`WorkFlowGenerator`)과 실행(`WorkFlow`) 양쪽에서 `gpt-4o-mini` 호출 | https://platform.openai.com/ 가입 후 발급, `OPENAI_API_KEY` 환경변수(이 문서는 키 없이 설치와 객체 생성까지만 직접 확인합니다) |
| Anthropic API 키 | 생성된 코드를 검증·수정하는 Claude 3.7 Sonnet 호출(LiteLLM 경유) | https://console.anthropic.com/ 가입 후 발급, `ANTHROPIC_API_KEY` 환경변수 |
| evoagentx (PyPI) | 워크플로우 자동 생성·실행·코드 검증·추출을 제공하는 프레임워크(오늘 기준 0.1.4) | `uv pip install "evoagentx[all]"` — 기본 설치(extra 없음)만으로는 이 스크립트의 import가 끝까지 통과하지 않습니다(Step 1에서 직접 확인) |
| Python 3.12 이하 | evoagentx가 고정하는 `faiss-cpu==1.8.0.post1`에 Python 3.13용 바이너리 휠이 없음(직접 확인) | `uv venv --python 3.12` |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 참고 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| .env / 환경변수 | `OPENAI_API_KEY`·`ANTHROPIC_API_KEY` 로드 | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:10-12` |
| 워크플로우 생성 (WorkFlowGenerator) | 목표 텍스트를 분해해 에이전트 워크플로우 그래프를 자동 생성 | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:3-4`, `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:24-25` |
| 에이전트 준비 (AgentManager) | 그래프 노드마다 실제 에이전트 인스턴스를 등록 | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:5`, `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:34-35` |
| 워크플로우 실행 (WorkFlow) | 등록된 에이전트를 실행해 코드를 생성 | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:4`, `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:37-38` |
| 코드 검증 (CodeVerification) | Claude로 생성된 코드를 검증·수정 | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:7`, `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:41-51` |
| 코드 추출 (CodeExtraction) | 코드 문자열이 여러 파일이면 분리해 저장(이 예시에서는 미실행) | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:6`, `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:63-70` |
| OpenAI gpt-4o-mini (외부) | 워크플로우 생성·실행 양쪽의 실제 추론 담당 | 코드 없음 (외부 서비스) |
| Anthropic Claude 3.7 Sonnet (외부, LiteLLM 경유) | 코드 검증·수정 담당 | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:41` |
| 결과 코드 파일 | 코드 블록 1개면 `index.html`로 직접 저장 | `advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:54-61` |

## 단계별 진행

### Step 1. 환경 변수와 OpenAI LLM 설정 — evoagentx가 무엇을 당기고, 무엇을 빠뜨리는지 확인

**목적.** 격리된 가상환경에 evoagentx를 설치하고, 이 스크립트가 쓰는 8개 import가 실제로 어디까지 통과하는지, 그리고 API 키 없이 LLM 설정 객체까지는 만들어지는지 확인합니다.

**할 일.**

```bash
uv venv --python 3.12
uv pip install "evoagentx[all]" python-dotenv
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install "evoagentx[all]" python-dotenv`. Windows PowerShell은 활성화만 `.venv\Scripts\Activate.ps1`로 바꿉니다.) 이 저장소는 루트에 `pyproject.toml`이 있어 `uv run`이 방금 만든 환경 대신 루트 `.venv`를 쓰므로, 이후 `uv run` 명령에는 모두 `--no-project`를 붙입니다.

`advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:1-19`

```python
import os 
from dotenv import load_dotenv 
from evoagentx.models import OpenAILLMConfig, OpenAILLM, LiteLLMConfig, LiteLLM
from evoagentx.workflow import WorkFlowGenerator, WorkFlowGraph, WorkFlow
from evoagentx.agents import AgentManager
from evoagentx.actions.code_extraction import CodeExtraction
from evoagentx.actions.code_verification import CodeVerification 
from evoagentx.core.module_utils import extract_code_blocks

load_dotenv() # Loads environment variables from .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") 

def main():

    # LLM configuration
    openai_config = OpenAILLMConfig(model="gpt-4o-mini", openai_key=OPENAI_API_KEY, stream=True, output_response=True, max_tokens=16000)
    # Initialize the language model
    llm = OpenAILLM(config=openai_config)
```

원본 앱의 `requirements.txt` 52줄은 이 스크립트가 실제로 필요로 하는 것과 거의 무관합니다 — `pytest`·`ruff`·`textgrad`·`fastapi`·`celery`·`redis`·`sqlalchemy` 등 EvoAgentX 저장소 자체의 개발용 의존성처럼 보이는 항목들이 섞여 있고, 정작 `evoagentx` 패키지 자신은 이 목록에 없습니다(직접 확인). 게다가 35행의 `faiss-cpu==1.8.0.post1` 고정 버전에는 Python 3.13용(`cp313`) 바이너리 휠이 없어, 오늘 기준 최신인 Python 3.13 환경에서 `uv pip install -r requirements.txt`는 evoagentx를 만나기도 전에 이 한 줄에서 실패합니다(직접 확인). 11~12행은 두 키를 모두 `None`이 될 수 있는 채로 읽습니다 — 아래 검증에서 보듯, 이 시점에는 아무 예외도 나지 않습니다.

![Step 1까지의 구성](diagrams/step1.svg)

**확인.** 먼저 Python 3.13 환경에서 원본 `requirements.txt`를 그대로 설치해 실패 지점을 확인했습니다.

```bash
uv pip install --python <3.13 스크래치 venv>/Scripts/python.exe -r requirements.txt
```

직접 확인한 출력(발췌):

```
× No solution found when resolving dependencies:
  ╰─▶ Because faiss-cpu==1.8.0.post1 has no wheels with a matching Python
      ABI tag (e.g., `cp313`) and you require faiss-cpu==1.8.0.post1, we can
      conclude that your requirements are unsatisfiable.
```

Python 3.12 환경에 `evoagentx`(extra 없이)만 설치한 뒤 이 스크립트의 import를 그대로 실행하면:

```bash
uv run --no-project python -c "from evoagentx.models import OpenAILLMConfig"
```

```
ModuleNotFoundError: No module named 'docker'
```

`docker`를 설치해도 다음은 `html2text`, `evoagentx[tools]`까지 설치하면 그다음은 `llama_index`, `evoagentx[tools,rag]`까지 설치하면 마지막으로 `voyageai` 순으로 걸립니다(직접 확인) — 각각 evoagentx의 `tools`·`rag`·`multimodal` extra가 선언한 패키지입니다. `uv pip install "evoagentx[all]"`까지 마치면 8개 import가 전부 통과합니다.

```bash
uv run --no-project python -m py_compile ai_Self-Evolving_agent.py && echo compiled
uv run --no-project python -c "
from evoagentx.models import OpenAILLMConfig, OpenAILLM, LiteLLMConfig, LiteLLM
from evoagentx.workflow import WorkFlowGenerator, WorkFlowGraph, WorkFlow
from evoagentx.agents import AgentManager
from evoagentx.actions.code_extraction import CodeExtraction
from evoagentx.actions.code_verification import CodeVerification
from evoagentx.core.module_utils import extract_code_blocks
print('all app imports OK')
"
```

직접 확인한 출력(2026-09-28 기준, Python 3.12.10 + evoagentx 0.1.4):

```
compiled
all app imports OK
```

API 키 없이 `OpenAILLMConfig`·`OpenAILLM`을 만들어도 예외가 나지 않는다는 것도 확인했습니다(아무도 듣지 않는 로컬 프록시로 외부 네트워크를 막은 채):

```bash
HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 ALL_PROXY=http://127.0.0.1:9 \
NO_PROXY=localhost,127.0.0.1 \
  uv run --no-project python -c "
import os
from evoagentx.models import OpenAILLMConfig, OpenAILLM
config = OpenAILLMConfig(model='gpt-4o-mini', openai_key=os.getenv('OPENAI_API_KEY'), stream=True, output_response=True, max_tokens=16000)
llm = OpenAILLM(config=config)
print('config OK, key value:', repr(config.openai_key))
"
```

직접 확인한 출력(발췌, 키를 설정하지 않은 상태):

```
config OK, key value: None
```

이 호출 과정에서 litellm(evoagentx가 내부적으로 씀)이 모델 요금표를 `raw.githubusercontent.com`에서 받아오려 3회 재시도하는 것도 함께 관찰했습니다 — 프록시가 연결을 거부해 매번 안전하게 실패하고 내장된 로컬 백업으로 대체됩니다(외부로 새어 나가지 않음, 직접 확인).

### Step 2. 목표 정의와 워크플로우 자동 생성

**목적.** 자연어 목표 하나가 `WorkFlowGenerator`를 거쳐 어떻게 멀티에이전트 워크플로우 그래프가 되는지 확인합니다.

**할 일.**

`advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:21-28`

```python
    goal = "Generate html code for the Tetris game that can be played in the browser."
    target_directory = "examples/output/tetris_game"
    
    wf_generator = WorkFlowGenerator(llm=llm)
    workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=goal)

    # [optional] display workflow
    workflow_graph.display()
```

evoagentx 0.1.4 소스(`evoagentx/workflow/workflow_generator.py`)로 확인하면, `generate_workflow()`는 목표 문자열이 10자 미만이면 즉시 `ValueError`를 냅니다(21행의 목표는 이 조건을 가볍게 넘습니다). 통과하면 내부적으로 `TaskPlanner`가 목표를 하위 작업으로 쪼개고, `AgentGenerator`가 작업마다 에이전트를 배정하거나 새로 만들어 `WorkFlowGraph`를 완성합니다 — 이 두 컴포넌트 모두 21행에서 만든 `llm`(OpenAI `gpt-4o-mini`)을 그대로 씁니다. 즉 "어떤 에이전트가 몇 개 필요한지" 자체가 모델의 출력이므로, 같은 목표라도 실행마다 그래프 구조가 달라질 수 있습니다. `target_directory`(22행)는 상대 경로이므로 스크립트를 실행하는 위치가 결과물의 실제 저장 위치를 정합니다.

![Step 2까지의 구성](diagrams/step2.svg)

**확인.**

```bash
grep -n "class WorkFlowGenerator" -A 5 <evoagentx 설치 경로>/workflow/workflow_generator.py
```

직접 확인한 출력(발췌, docstring):

```
Automated workflow generation system based on high-level goals.

The WorkFlowGenerator is responsible for creating complete workflow graphs
from high-level goals or task descriptions. It breaks down the goal into
subtasks, creates the necessary dependency connections between tasks,
```

### Step 3. 에이전트 준비와 워크플로우 실행

**목적.** 그래프의 노드가 실제 에이전트 객체로 바뀌는 지점과, 그 에이전트들이 실행되어 코드를 만드는 지점을 확인합니다.

**할 일.**

`advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:34-38`

```python
    agent_manager = AgentManager()
    agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)

    workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
    output = workflow.execute()
```

evoagentx 소스(`evoagentx/agents/agent_manager.py`)로 확인하면, 35행은 `workflow_graph.nodes`를 순회하며 노드마다 딸린 에이전트 스펙을 `add_agent()`로 등록합니다 — 스펙이 dict이면 그때 `llm_config`(OpenAI 설정)로 `CustomizeAgent`를 만듭니다. 38행의 `workflow.execute()`는 내부적으로 `async_execute()`를 동기 래핑한 것으로(소스로 확인), 그래프의 각 작업을 순서대로 실행하며 필요한 에이전트를 호출합니다 — 이 호출들이 실제로 OpenAI에 요청을 보내는 지점입니다.

![Step 3까지의 구성](diagrams/step3.svg)

**확인.**

```bash
uv run --no-project python -c "
from evoagentx.agents import AgentManager
am = AgentManager()
print(hasattr(am, 'add_agents_from_workflow'))
"
```

직접 확인한 출력:

```
True
```

### Step 4. Claude로 코드 검증

**목적.** 생성된 코드가 왜 다른 모델을 한 번 더 거치는지, 그리고 검증 결과가 어떤 형식으로 오는지 확인합니다.

**할 일.**

`advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:40-51`

```python
    # verfiy the code
    verification_llm_config = LiteLLMConfig(model="anthropic/claude-3-7-sonnet-20250219", anthropic_key=ANTHROPIC_API_KEY, stream=True, output_response=True, max_tokens=20000)
    verification_llm = LiteLLM(config=verification_llm_config)
    
    code_verifier = CodeVerification()
    output = code_verifier.execute(
        llm = verification_llm, 
        inputs={
            "requirements": goal, 
            "code": output
        }
    ).verified_code
```

41행은 생성 모델과 다른 제공자(Anthropic)를 LiteLLM으로 감쌉니다 — 코드 생성과 코드 검증을 서로 다른 모델에 맡기는 것이 이 앱 이름의 "검증" 절반입니다. evoagentx 소스(`evoagentx/actions/code_verification.py`)로 확인하면, `execute()`는 `code`·`requirements`를 고정 프롬프트에 채워 `llm.generate()`를 한 번 호출하고, 응답을 `analysis_summary`·`issues_identified`·`verified_code` 등의 필드로 파싱을 시도합니다 — 구조화된 파싱이 실패하면 응답에서 코드 블록만 다시 추출하는 방식으로 대체합니다. 49행에서 보듯 검증 대상은 원래 목표(`goal`) 문자열 그대로이고, 45행의 반환값이 51행에서 원래 `output` 변수를 덮어씁니다.

![Step 4까지의 구성](diagrams/step4.svg)

**확인.**

```bash
grep -n "def execute" -A 10 <evoagentx 설치 경로>/actions/code_verification.py
```

직접 확인한 출력(발췌):

```
    def execute(self, llm: Optional[BaseLLM] = None, inputs: Optional[dict] = None, sys_msg: Optional[str]=None, return_prompt: bool = False, **kwargs) -> CodeVerificationOutput:
        ...
        prompt = self.prompt.format(**prompt_params_values)
        response = llm.generate(prompt = prompt, system_message=sys_msg)
```

### Step 5. 단일 코드 블록이면 그대로 저장

**목적.** 검증된 코드가 파일로 저장되는 첫 번째 경로(코드 블록이 1개일 때)를 확인합니다.

**할 일.**

`advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:53-61`

```python
    # extract the code 
    os.makedirs(target_directory, exist_ok=True)
    code_blocks = extract_code_blocks(output)
    if len(code_blocks) == 1:
        file_path = os.path.join(target_directory, "index.html")
        with open(file_path, "w") as f:
            f.write(code_blocks[0])
        print(f"You can open this HTML file in a browser to play the Tetris game: {file_path}")
        return
```

55행의 `extract_code_blocks()`(evoagentx 유틸리티)는 마크다운 코드 펜스로 감싸인 블록을 찾아 리스트로 돌려줍니다. "테트리스 게임"이라는 목표는 검증된 코드가 HTML 하나로 떨어질 가능성이 높고, 그 경우 이 조건이 참이 되어 파일명을 **항상 `index.html`로 고정**한 채 저장하고 `return`으로 함수를 끝냅니다 — 원래 코드가 CSS나 JS를 분리해서 냈더라도 이 분기에서는 하나로 합쳐진 블록이어야만 여기로 옵니다. 57행의 파일명 고정 때문에, 다른 언어(예: Python)로 된 단일 블록이어도 확장자는 항상 `.html`이 됩니다 — 소스로 확인한, 코드 자체의 한계입니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.**

```bash
grep -n "extract_code_blocks" <evoagentx 설치 경로>/core/module_utils.py | head -3
```

직접 확인한 출력(발췌, 함수가 실제로 존재함):

```
def extract_code_blocks(text: str, return_type: bool = False):
```

### Step 6. 여러 파일이면 CodeExtraction으로 분리 저장

**목적.** 코드 블록이 여러 개일 때만 실행되는, 이 앱의 두 번째 저장 경로를 확인합니다. 이 예시(테트리스 HTML)에서는 이 경로가 실행되지 않습니다(Step 5).

**할 일.**

`advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py:63-83`

```python
    code_extractor = CodeExtraction()
    results = code_extractor.execute(
        llm=llm, 
        inputs={
            "code_string": output, 
            "target_directory": target_directory,
        }
    )

    print(f"Extracted {len(results.extracted_files)} files:")
    for filename, path in results.extracted_files.items():
        print(f"  - {filename}: {path}")
    
    if results.main_file:
        print(f"\nMain file: {results.main_file}")
        file_type = os.path.splitext(results.main_file)[1].lower()
        if file_type == '.html':
            print(f"You can open this HTML file in a browser to play the Tetris game")
        else:
            print(f"This is the main entry point for your application")
```

63행은 21행에서 만든 `llm`(OpenAI `gpt-4o-mini`)을 다시 씁니다 — Claude가 아니라 처음 모델로 되돌아갑니다. evoagentx 소스(`evoagentx/actions/code_extraction.py`)로 확인하면, `execute()`는 `llm.generate()`로 코드 문자열을 언어별 블록으로 분류한 뒤 각 블록을 실제로 `target_directory`에 파일로 씁니다(`open(file_path, 'w')`) — CodeExtraction 자신이 파일 저장까지 담당합니다. `identify_main_file()`은 `index.html`·`main.py`·`app.py` 같은 우선순위 목록과 확장자 휴리스틱으로 진입점을 추정합니다.

![Step 6까지의 구성](diagrams/step6.svg)

**확인.**

```bash
grep -n "os.makedirs\|open(file_path" <evoagentx 설치 경로>/actions/code_extraction.py
```

직접 확인한 출력(발췌, 파일 저장이 CodeExtraction 내부에서 일어남을 보여줌):

```
        os.makedirs(target_directory, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
```

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

스크립트를 실행하면 `WorkFlowGenerator`가 목표를 OpenAI에 보내 워크플로우 그래프(JSON)를 받습니다. 스크립트는 이 그래프로 `WorkFlow`를 실행하고, `WorkFlow`는 다시 OpenAI에 요청해 실제 코드(HTML)를 생성합니다. 여기까지가 `output` 변수 하나에 담깁니다. 스크립트는 이 `output`을 그대로 `CodeVerification`에 넘기고, `CodeVerification`은 Anthropic Claude에 코드와 원래 요구사항을 함께 보내 `verified_code`를 돌려받습니다 — 이 값이 다시 `output`을 덮어씁니다. 마지막으로 스크립트는 코드 블록 개수를 세어, 이 예시처럼 1개면 `index.html`로 직접 저장합니다(자기 자신에게 보내는 마지막 화살표로 표시). 여러 개였다면 이 자리에 `CodeExtraction`이 세 번째로 OpenAI를 호출해 파일별로 나눠 저장했을 것입니다 — Step 6에서 다룬 경로로, 이 요청 한 건에서는 실행되지 않습니다.

## 실행 체크리스트

- [ ] Python 3.12 이하 가상환경에서 `pip install "evoagentx[all]"`까지 마치면 이 스크립트의 import 8개가 전부 통과한다는 것을 확인했다
- [ ] `evoagentx`를 extra 없이 설치하면 이 스크립트의 import가 `docker`→`html2text`→`llama_index`→`voyageai` 순으로 `ModuleNotFoundError`를 낸다는 것을 직접 재현했다
- [ ] `requirements.txt`의 `faiss-cpu==1.8.0.post1`에 Python 3.13용 바이너리 휠이 없어 그 환경에서는 설치 자체가 실패한다는 것을 직접 확인했다
- [ ] `OPENAI_API_KEY`·`ANTHROPIC_API_KEY` 없이도 `OpenAILLMConfig`·`OpenAILLM`·`WorkFlowGenerator` 객체 생성까지는 예외 없이 된다는 것을 직접 확인했다
- [ ] litellm이 모델 요금표를 GitHub에서 받으려 시도하고, 네트워크를 막으면 연결 거부로 안전하게 실패한다는 것을 직접 확인했다
- [ ] "테트리스 게임" 목표에서는 코드가 블록 1개로 떨어져 `CodeExtraction` 경로(63~83행)가 실행되지 않는다는 것을 소스로 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| Python 3.13에서 `uv pip install -r requirements.txt`가 evoagentx를 설치하기도 전에 실패 | `requirements.txt` 35행의 `faiss-cpu==1.8.0.post1`에 `cp313` 바이너리 휠이 없음(직접 확인) | 리포 코드는 고치지 않음 — Python 3.12 이하 가상환경 사용 |
| `evoagentx` 설치 후 이 스크립트의 import 문장들이 `ModuleNotFoundError: No module named 'docker'`(고치면 `html2text`, `llama_index`, `voyageai` 순으로 계속) | evoagentx 0.1.4의 base 패키지 import 사슬이 `tools`·`rag`·`multimodal` extra의 의존성까지 끌어들이는데, extra를 지정하지 않으면 그 패키지들이 없음(직접 확인) | `pip install "evoagentx[all]"`로 설치(리포 코드는 고치지 않음) |
| 원본 README의 `pip install git+https://github.com/ANative-Lab/EvoAgentX.git`가 매번 소스 빌드를 함 | evoagentx가 이제 PyPI(0.1.4)에 배포돼 있어 git 설치가 더 이상 필요하지 않음(직접 확인) — URL 자체는 유효함(GitHub 301 리다이렉트로 확인) | `pip install evoagentx` 계열로 대체 가능(리포 코드는 고치지 않음, 설치 안내일 뿐) |
| "테트리스 게임" 목표로 실행해도 콘솔에 `Extracted N files` 메시지가 절대 뜨지 않음 | 검증된 코드가 코드 블록 1개(HTML)로 떨어져 56~61행에서 함수가 `return`함 — `CodeExtraction`(63행 이후)에 도달하지 못함(소스로 확인) | 버그 아님 — 여러 파일을 요구하는 목표로 바꾸면 이 경로를 볼 수 있음(더 해보기 참고) |

## 더 해보기

- `ai_Self-Evolving_agent.py:21`의 목표를 "여러 개의 파일로 구성된 정적 웹사이트를 만들어라"처럼 바꿔, `CodeExtraction` 경로(`ai_Self-Evolving_agent.py:63-83`)가 실제로 실행되고 `results.extracted_files`에 여러 항목이 담기는지 확인해보기
- `ai_Self-Evolving_agent.py:28`의 `workflow_graph.display()` 출력을 같은 목표로 여러 번 실행해 비교하며, `WorkFlowGenerator`가 매번 같은 개수·구조의 에이전트를 만드는지 확인해보기
- `ai_Self-Evolving_agent.py:41`의 `verification_llm_config` 모델을 다른 Anthropic 스냅샷이나 OpenAI 모델로 바꿔(코드 수정 필요), 검증·수정 결과가 모델마다 어떻게 달라지는지 비교해보기

## 다음 날 예고

[Day 081 · 🗞️ AI Journalist Agent](../day081-ai-journalist-agent/README.md) — OpenAI GPT-4o와 SerpAPI로 리서치·작성·편집 3단계를 거쳐 기사를 만드는 단일 에이전트 앱을 다룹니다.
