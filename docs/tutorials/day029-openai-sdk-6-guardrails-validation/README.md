# Day 029 · OpenAI Agents SDK Crash Course · 6_guardrails_validation

> 볼륨 2 🧑‍🏫 Crash Courses · 난이도 ★★☆ · 예상 소요 110분(SDK 소스 다섯 파일과 오프라인 재현 실험 일곱 개를 모두 거쳐 확인하느라 다른 크래시 코스 날보다 깁니다) · API 비용 $0 (API 키를 발급하지 않았습니다 — 이 문서의 모든 "직접 확인"은 키 없이 실패하는 지점을 보거나, SDK가 제공하는 오프라인 테스트 더블로 실제 모델 호출 없이 가드레일을 재현합니다) · 원본 앱: `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation`

## 오늘 만들 것

Day 024가 세운 이 볼륨의 공통 축(`openai-agents` 패키지, `from agents import ...`, 단일 키 `OPENAI_API_KEY`)은 오늘도 그대로입니다 — 다시 설명하지 않습니다. 오늘의 `6_guardrails_validation`은 157줄짜리 `agent.py` 한 파일로, 이 볼륨에서 세 번째로 `requirements.txt`가 아예 없는 폴더입니다(Day 024가 이미 `3_tool_using_agent`·`5_context_management`·`6_guardrails_validation` 세 곳을 그렇게 지목해 두었습니다). Day 026이 `3_tool_using_agent`에서 한 것처럼, 이번에도 그 답을 그대로 베끼는 대신 이 파일 자신의 import 두 줄(`pydantic`, `agents`)만 직접 읽어 무엇을 설치해야 하는지 Step 1에서 다시 뽑아냅니다 — 도구 에이전트 레슨과 임포트 목록 자체가 다르기 때문입니다.

이 날의 주제는 **가드레일**입니다. Day 019는 ADK의 콜백이 참값을 반환하면 실행 자체를 가로챈다는 것과, 에이전트·모델 레벨은 그 반환이 뒤따르는 after 훅까지 함께 건너뛰게 만들지만 도구 레벨은 그렇지 않다는 비대칭을 확인했습니다. OpenAI SDK의 가드레일은 같은 계열의 아이디어를 다른 메커니즘으로 구현합니다 — ADK 콜백은 값을 "반환"해서 그 값이 조용히 최종 결과를 갈아치우지만, 가드레일은 `tripwire_triggered=True`를 반환해도 호출자에게 어떤 결과도 주지 않고 대신 `InputGuardrailTripwireTriggered`/`OutputGuardrailTripwireTriggered`라는 타입 있는 예외를 던져 호출자가 반드시 `try/except`로 받아야 합니다. 그리고 이 SDK에만 있는 축이 하나 더 있습니다 — 입력 가드레일은 보호 대상 에이전트의 첫 모델 호출과 **동시에** 돌 수도, 그 앞에서 돌 수도 있는 반면(`run_in_parallel`), 출력 가드레일에는 그런 선택지 자체가 없습니다. 이 문서는 정확히 이 질문에 답합니다: 가드레일은 실행의 어느 지점에서 무엇을 보고, 트립됐을 때 무엇을 실제로 멈출 수 있으며, 무엇은 이미 늦었는가.

API 키가 없으면 보호 대상 에이전트의 모델 호출뿐 아니라 가드레일 자신의 판정 에이전트 호출도 똑같이 막혀, "가드레일이 실제로 트립하는 모습"은 평범한 방법으로는 볼 수 없습니다(Step 7). 대신 이 문서는 openai-agents 0.22.3이 함께 배포하는 `agents.testing.ScriptedModel` — 실제 네트워크 호출 없이 모델 응답을 미리 정해 둘 수 있는 공식 테스트 더블 — 을 이용해 Step 4·5·6에서 가드레일이 실제로 트립하는 순간과, 그 승패가 갈리는 경합 상황까지 키 없이 직접 재현합니다. 이 레슨의 최상위 README(259줄)는 실제 코드를 인용하는 대신 대부분 `content_filter`·`spam_detector` 같은 이름의 일반적인 예시 코드로 개념을 설명합니다 — Day 019·022·023·024·026이 찾은 것과 같은 종류의 정면 오류는 이번엔 없었습니다. 다만 "가드레일 예외를 우아하게 처리하는 법을 배운다"는 README의 학습 목표는, 이 파일 안의 데모 함수 세 개가 실제로는 서로 다른 수준의 예외 처리를 하고 있다는 사실(Step 7)과 정확히 들어맞지는 않습니다. 완성 아키텍처는 다음과 같습니다.

![완성 아키텍처](diagrams/overview.svg)

## 사전 준비

| 서비스/도구 | 용도 | 발급·설치 |
|---|---|---|
| OpenAI API 키 (`OPENAI_API_KEY`) | 보호 대상 에이전트 하나와 그 안의 가드레일 판정 에이전트 둘, 합쳐서 한 번의 성공적인 요청마다 최소 3번의 모델 호출 인증(Step 2). 이 문서는 키를 발급하지 않고, 키가 없을 때 어디서 멈추는지(Step 7)와 SDK의 오프라인 테스트 더블로 가드레일이 실제로 트립하는 모습(Step 4~6)을 대신 확인합니다 | https://platform.openai.com/api-keys 에서 발급 (이 실습에서는 생략) |
| uv | 가상환경 생성과 패키지 설치 | [공통 사전 준비](../README.md#공통-사전-준비-한-번만) 참고 |
| 인터넷 연결 | PyPI에서 `openai-agents` 설치(OpenAI API 자체는 이 문서 어디에서도 실제로 호출하지 않습니다) | 별도 설치 없음 |

## 아키텍처 한눈에 보기

| 컴포넌트 | 역할 | 코드 위치 |
|---|---|---|
| 사용자 | 질문을 보내는 호출자 | 코드 없음 (외부 호출자) |
| 보호 대상 에이전트 (`root_agent`) | 입력·출력 가드레일이 걸린 고객지원 에이전트, 구조화된 `AgentResponse`로만 답함 | `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:97-117` |
| 입력 가드레일 (`math_homework_guardrail`) | 원본 입력을 받아 `input_guardrail_agent`를 자체 `Runner.run()`으로 호출해 수학 숙제 여부를 판정 | `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:63-77` |
| 입력 판정 에이전트 (`input_guardrail_agent`) | `MathHomeworkCheck` 구조화 출력을 내는, 완전히 독립된 작은 에이전트 | `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:29-45` |
| 출력 가드레일 (`content_safety_guardrail`) | 이미 생성된 `AgentResponse`를 받아 `output_guardrail_agent`를 자체 `Runner.run()`으로 호출해 안전성을 판정 | `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:80-94` |
| 출력 판정 에이전트 (`output_guardrail_agent`) | `ContentSafetyCheck` 구조화 출력을 내는, 완전히 독립된 작은 에이전트 | `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:47-60` |
| OpenAI API | 세 에이전트 모두의 실제 추론 수행 | 코드 없음 (외부 서비스) |

## 단계별 진행

### Step 1. 환경 만들기 — requirements.txt 없이, import에서 의존성을 뽑는다

**목적.** 이 폴더에 `requirements.txt`가 정말 없다는 것을 확인하고, `agent.py`가 실제로 무엇을 import하는지 읽어 설치할 패키지를 정합니다.

**할 일.** 이 파일의 import는 두 줄뿐입니다.

`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:1-12`

```python
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    output_guardrail,
)
```

서드파티 패키지는 `pydantic`과 `agents`(배포명 `openai-agents`) 둘뿐입니다 — `python-dotenv`는 어디에도 없고(`import os`도 없어 `OPENAI_API_KEY`를 명시적으로 검사하는 코드 자체가 이 파일엔 없습니다, Step 3), Day 026의 도구 레슨과 달리 `pydantic`을 별도로 설치할 필요도 없습니다 — Day 025가 이미 확인했듯 openai-agents 0.22.3은 `pydantic<3,>=2.12.2`를 전이 의존성으로 이미 선언하고 있습니다(같은 사실을 오늘 설치판에서 다시 확인: 아래 확인 블록). `env.example`(`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/env.example:1-1`)은 `OPENAI_API_KEY=your_openai_api_key_here` 한 줄뿐이지만, 이 파일을 읽어 들이는 `load_dotenv()` 호출이 코드 어디에도 없으므로 — Day 026이 형제 레슨에서 확인한 것과 같은 이유로 — `cp env.example .env`만으로는 아무 효과가 없습니다.

```bash
cd ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation
uv venv --python 3.12
uv pip install openai-agents
```

```powershell
cd ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation
uv venv --python 3.12
uv pip install openai-agents
```

(pip 대안: `python -m venv .venv && source .venv/bin/activate && pip install openai-agents`.) 이 저장소는 루트에 `pyproject.toml`이 있어 `uv run`이 방금 만든 환경 대신 루트의 `.venv`를 쓰므로, 이후 `uv run` 명령에는 모두 `--no-project`를 붙입니다 — 이 볼륨의 루트 `.venv`에는 이름이 같은 다른 패키지(TensorFlow Agents)가 있어 이 플래그를 빠뜨리면 엉뚱한 자리에서 실패한다는 것은 Day 024·026이 이미 정리했습니다.

![Step 1까지의 구성](diagrams/step1.svg)

**확인.**

```bash
uv run --no-project python -c "
import importlib.metadata as md
print('openai-agents', md.version('openai-agents'))
print('openai', md.version('openai'))
print('pydantic', md.version('pydantic'))
from pydantic import BaseModel
import agent
print('agent.py imported OK')
print('input_guardrails:', [g.get_name() for g in agent.root_agent.input_guardrails])
print('output_guardrails:', [g.get_name() for g in agent.root_agent.output_guardrails])
"
```

```powershell
uv run --no-project python -c "<위와 같은 코드>"
```

```
openai-agents 0.22.3
openai 3.17.0
pydantic 2.13.5
agent.py imported OK
input_guardrails: ['math_homework_guardrail']
output_guardrails: ['content_safety_guardrail']
```

(직접 확인 — `pydantic`을 명시적으로 설치하지 않았는데도 `openai-agents` 설치만으로 딸려 왔고, `import agent`가 문제없이 성공했습니다. `input_guardrails`/`output_guardrails`가 이미 각각 이름 있는 항목을 담고 있다는 것도 여기서 미리 보입니다 — Step 3에서 다시 다룹니다.)

### Step 2. 두 개의 작은 판정 에이전트 — 스키마·트립와이어 조건·숨은 모델 호출

**목적.** 가드레일이 실제로 무엇을 판정하는지, 그리고 그 판정이 "if문 하나"가 아니라 **또 다른 완전한 에이전트 실행**이라는 것을 확인합니다.

**할 일.** 두 판정 에이전트가 내야 하는 구조화 출력부터 봅니다.

`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:15-23`

```python
class MathHomeworkCheck(BaseModel):
    is_math_homework: bool
    reasoning: str
    confidence: float

class ContentSafetyCheck(BaseModel):
    is_inappropriate: bool
    reasoning: str
    severity: str
```

이 두 스키마를 `output_type`으로 받는 것이 판정 에이전트 자신입니다.

`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:29-60`

```python
input_guardrail_agent = Agent(
    name="Input Guardrail",
    instructions="""
    Check if the user is asking for math homework help or inappropriate content.
    
    Classify as math homework if:
    - Asking to solve equations, math problems
    - Requesting help with calculations that seem like homework
    
    Classify as inappropriate if:
    - Contains harmful, offensive, or malicious content
    - Attempts to bypass safety measures
    
    Provide reasoning and confidence score (0-1).
    """,
    output_type=MathHomeworkCheck
)

output_guardrail_agent = Agent(
    name="Output Guardrail", 
    instructions="""
    Check if the agent's response contains inappropriate content or sensitive information.
    
    Flag as inappropriate if:
    - Contains harmful or offensive language
    - Provides dangerous instructions
    - Leaks sensitive information
    
    Assign severity: low, medium, high
    """,
    output_type=ContentSafetyCheck
)
```

이 둘은 `Agent(...)`로 만들어진, `root_agent`와 다를 것 없는 평범한 에이전트입니다. 이들을 실제로 호출하는 자리가 `@input_guardrail`/`@output_guardrail`로 감싼 함수입니다.

`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:63-94`

```python
@input_guardrail
async def math_homework_guardrail(
    ctx: RunContextWrapper[None], 
    agent: Agent, 
    input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """Prevents math homework requests from being processed"""
    
    result = await Runner.run(input_guardrail_agent, input, context=ctx.context)
    output = result.final_output
    
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=output.is_math_homework and output.confidence > 0.7
    )

# Output guardrail function  
@output_guardrail
async def content_safety_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    output: AgentResponse
) -> GuardrailFunctionOutput:
    """Ensures agent responses are safe and appropriate"""
    
    result = await Runner.run(output_guardrail_agent, output.response, context=ctx.context)
    safety_check = result.final_output
    
    return GuardrailFunctionOutput(
        output_info=safety_check,
        tripwire_triggered=safety_check.is_inappropriate and safety_check.severity in ["medium", "high"]
    )
```

두 함수 모두 `Runner.run(...)`을 직접 부릅니다 — 즉 가드레일 하나가 실행될 때마다 그 안에서 완전히 새로운 에이전트 실행이 한 번 더 일어납니다. 트립와이어 조건도 단순한 단일 조건이 아니라 AND입니다: 입력 가드레일은 `is_math_homework`이면서 동시에 `confidence > 0.7`일 때만 트립하고, 출력 가드레일은 `is_inappropriate`이면서 동시에 `severity`가 `"medium"`이나 `"high"`일 때만 트립합니다 — 확신이 낮은 수학 숙제 판정이나 `"low"` 등급의 부적절 판정은 트립하지 않고 그냥 통과합니다. `@input_guardrail`/`@output_guardrail` 데코레이터는 이 함수들을 평범한 코루틴 함수가 아니라 `InputGuardrail`/`OutputGuardrail` 객체로 바꿔 둔다는 것(소스로 확인, openai-agents 0.22.3의 `agents/guardrail.py`)도 아래 확인에서 직접 봅니다 — 이 객체의 `run_in_parallel` 필드(기본값 `True`)가 Step 4의 주제입니다.

![Step 2까지의 구성](diagrams/step2.svg)

**확인.** 두 함수가 실제로 어떤 타입인지, 그리고 아무것도 트립하지 않는 정상 요청 한 건이 실제로 몇 번의 모델 호출을 만드는지를 SDK의 공식 오프라인 테스트 더블(`agents.testing.ScriptedModel`)로 함께 봅니다 — `input_guardrail_agent`·`output_guardrail_agent`·`root_agent`의 모델을 각각 미리 정해 둔 응답으로 바꿔 치환할 뿐, 리포의 파일은 고치지 않습니다.

```bash
uv run --no-project python -c "
import agent as m
from agents import Runner
from agents.testing import ScriptedModel, assistant_message
import json, asyncio

print('type(math_homework_guardrail):', type(m.math_homework_guardrail).__name__)
print('type(content_safety_guardrail):', type(m.content_safety_guardrail).__name__)
print('math_homework_guardrail.get_name():', m.math_homework_guardrail.get_name())
print('math_homework_guardrail.run_in_parallel:', m.math_homework_guardrail.run_in_parallel)

m.input_guardrail_agent = m.input_guardrail_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'is_math_homework': False, 'reasoning': 'not homework', 'confidence': 0.05}))]
]))
m.output_guardrail_agent = m.output_guardrail_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'is_inappropriate': False, 'reasoning': 'ordinary answer', 'severity': 'low'}))]
]))
protected = m.root_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'response': 'To reset your password, click Forgot password.'}))]
]))

async def main():
    result = await Runner.run(protected, 'How do I reset my password?')
    print('final_output:', result.final_output)
    total = len(m.input_guardrail_agent.model.calls) + len(protected.model.calls) + len(m.output_guardrail_agent.model.calls)
    print('total model calls for one fully-passing protected run:', total)

asyncio.run(main())
"
```

```powershell
uv run --no-project python -c "<위와 같은 코드>"
```

```
type(math_homework_guardrail): InputGuardrail
type(content_safety_guardrail): OutputGuardrail
math_homework_guardrail.get_name(): math_homework_guardrail
math_homework_guardrail.run_in_parallel: True
final_output: response='To reset your password, click Forgot password.'
total model calls for one fully-passing protected run: 3
```

(직접 확인 — `OPENAI_API_KEY is not set, skipping trace export`라는 트레이싱 안내 줄이 출력 맨 앞이나 맨 뒤 중 어디에 끼어드는지는 표준출력·표준에러 버퍼링 순서에 좌우돼 실행마다 달라질 수 있어 위 발췌에서는 뺐습니다. 핵심은 마지막 줄입니다 — 트립이 하나도 없는, 완전히 정상적인 요청 한 건이 실제로는 모델 호출 3번(입력 판정 1 + 보호 대상 1 + 출력 판정 1)이라는 것입니다. 가드레일은 공짜가 아닙니다.)

### Step 3. 보호 대상 에이전트 조립 — 가드레일은 그냥 리스트 필드

**목적.** `root_agent`가 두 가드레일을 어떻게 등록하는지 확인하고, 그것이 특수 문법이 아니라 `Agent`의 평범한 리스트 필드라는 것을 확인합니다. 이 파일 자체엔 아무 진입점이 없다는 것도 함께 봅니다.

**할 일.**

`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:97-117`

```python
root_agent = Agent(
    name="Protected Customer Support Agent",
    instructions="""
    You are a helpful customer support agent.
    
    You help customers with:
    - Product questions and information
    - Account issues and support
    - General inquiries and guidance
    
    You DO NOT help with:
    - Academic homework (especially math)
    - Inappropriate or harmful requests
    - Sensitive or confidential information
    
    Be helpful but maintain appropriate boundaries.
    """,
    input_guardrails=[math_homework_guardrail],
    output_guardrails=[content_safety_guardrail],
    output_type=AgentResponse
)
```

`input_guardrails=[...]`과 `output_guardrails=[...]`은 각각 `list[InputGuardrail]`/`list[OutputGuardrail]` 타입의 평범한 리스트 필드입니다(소스로 확인, `agents/agent.py`의 `Agent` 데이터클래스) — 리스트이므로 여러 개를 등록할 수 있고(더 해보기), 지금은 하나씩만 들어 있습니다. `output_type=AgentResponse`(`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:25-26`의 `class AgentResponse(BaseModel): response: str`)는 Day 025가 다룬 것과 같은 구조화 출력 메커니즘이고, `content_safety_guardrail`이 검사하는 대상도 자유 텍스트가 아니라 바로 이 `AgentResponse.response` 필드입니다. 이 파일에는 `import os`도, `if __name__ == "__main__":` 블록도 없습니다(직접 확인, 아래) — 세 개의 데모 함수(`guardrails_example`·`test_input_guardrail`·`test_valid_request`, Step 7)를 정의만 해 두고 아무것도 부르지 않습니다. Day 024의 `1_personal_assistant_agent/agent.py`와 같은 모양입니다.

![Step 3까지의 구성](diagrams/step3.svg)

**확인.**

```bash
grep -n "os\.getenv\|import os\|load_dotenv\|__main__" agent.py; echo "grep exit=$?"
```

```powershell
Select-String -Path agent.py -Pattern "os\.getenv|import os|load_dotenv|__main__"
```

```
grep exit=1
```

(직접 확인 — 네 패턴 중 어느 것도 없어 `grep`이 아무것도 찾지 못하고 종료 코드 1을 돌려줍니다. PowerShell의 `Select-String`도 아무 줄도 출력하지 않습니다.)

```bash
uv run --no-project python -c "
import subprocess, sys
r = subprocess.run([sys.executable, 'agent.py'], capture_output=True, text=True)
print('returncode:', r.returncode, '| stdout:', repr(r.stdout), '| stderr:', repr(r.stderr))
import agent as m
print()
print('root_agent.name:', m.root_agent.name)
print('root_agent.output_type:', m.root_agent.output_type)
print('root_agent.input_guardrails:', [g.get_name() for g in m.root_agent.input_guardrails])
print('root_agent.output_guardrails:', [g.get_name() for g in m.root_agent.output_guardrails])
print('type(root_agent.input_guardrails):', type(m.root_agent.input_guardrails).__name__)
"
```

```powershell
uv run --no-project python -c "<위와 같은 코드>"
```

```
returncode: 0 | stdout: '' | stderr: ''

root_agent.name: Protected Customer Support Agent
root_agent.output_type: <class 'agent.AgentResponse'>
root_agent.input_guardrails: ['math_homework_guardrail']
root_agent.output_guardrails: ['content_safety_guardrail']
type(root_agent.input_guardrails): list
```

(직접 확인 — `python agent.py`는 종료 코드 0으로 끝나지만 화면엔 아무것도 찍지 않습니다. `input_guardrails`의 실제 파이썬 타입은 그냥 `list`입니다.)

### Step 4. 입력 가드레일이 실행되는 자리 — "사전"이 아니라 기본은 "병렬"

**목적.** 입력 가드레일이 정말로 실행을 멈추는지, 그리고 그 트립이 언제 일어나는지를 소스와 오프라인 재현 양쪽으로 확인합니다.

**할 일.** `InputGuardrail` 데이터클래스의 독스트링과 필드는(소스로 확인, openai-agents 0.22.3의 `agents/guardrail.py`) 이렇게 밝히고 있습니다 — "Input guardrails are checks that run either in parallel with the agent or before it starts", 그리고 `run_in_parallel: bool = True`가 기본값입니다. `Agent` 자신의 필드 독스트링(소스로 확인, `agents/agent.py`)도 같은 이야기를 합니다: "A list of checks that run in parallel to the agent's execution, before generating a response. Runs only if the agent is the first agent in the chain." 즉 기본 설정에서 입력 가드레일은 보호 대상 에이전트의 **첫 모델 호출을 막아선 뒤 여는 문이 아니라, 그 호출과 동시에 출발하는 경쟁자**입니다. 실제 구현(소스로 확인, `agents/run.py`)은 `asyncio.create_task`로 두 코루틴 — 실제 모델 호출(`model_task`)과 가드레일 판정(`guardrail_task`) — 을 나란히 띄운 뒤 `asyncio.gather(guardrail_task, model_task)`로 기다립니다. 가드레일이 트립을 던지면 아직 끝나지 않은 `model_task`를 `cancel()`하려고 시도하지만, 이미 끝난 태스크는 취소할 것이 없습니다 — 이 승패는 Step 5에서 직접 재현합니다.

![Step 4까지의 구성](diagrams/step4.svg)

**확인.** Step 2와 같은 방식으로, 입력 가드레일이 수학 숙제로 확신 있게 판정하도록 스크립트를 짜고 실제로 트립하는지 봅니다. `root_agent`의 모델에는 "여기까지 오면 안 되는" 응답을 심어 둡니다.

```bash
uv run --no-project python -c "
import agent as m
from agents import Runner, InputGuardrailTripwireTriggered
from agents.testing import ScriptedModel, assistant_message
import json, asyncio

m.input_guardrail_agent = m.input_guardrail_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'is_math_homework': True, 'reasoning': 'Algebra request.', 'confidence': 0.95}))]
]))
protected = m.root_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'response': 'should never be reached'}))]
]))

async def main():
    try:
        result = await Runner.run(protected, 'Can you solve this equation: 2x + 5 = 15?')
        print('NO TRIP, result:', result.final_output)
    except InputGuardrailTripwireTriggered as e:
        print('str(e):', str(e))
        print('e.guardrail_result.guardrail.get_name():', e.guardrail_result.guardrail.get_name())
        info = e.guardrail_result.output.output_info
        print('output_info:', info)
    print('protected model calls consumed:', len(protected.model.calls))

asyncio.run(main())
"
```

```powershell
uv run --no-project python -c "<위와 같은 코드>"
```

```
str(e): Guardrail InputGuardrail triggered tripwire
e.guardrail_result.guardrail.get_name(): math_homework_guardrail
output_info: is_math_homework=True reasoning='Algebra request.' confidence=0.95
protected model calls consumed: 1
```

(직접 확인 — API 키 없이, 실제 OpenAI 호출 없이 재현했습니다. 두 가지가 눈에 띕니다. 첫째, `str(e)`는 "Guardrail **InputGuardrail** triggered tripwire"라고만 말합니다 — 실제로 트립한 함수 이름(`math_homework_guardrail`)이 아니라 감싸는 클래스 이름입니다(소스로 확인, `agents/exceptions.py`의 `InputGuardrailTripwireTriggered.__init__`이 `guardrail_result.guardrail.__class__.__name__`을 쓰기 때문). 실제 이름은 `e.guardrail_result.guardrail.get_name()`으로만 얻어집니다. 둘째, `protected model calls consumed: 1` — 이 실행에서는 보호 대상 모델이 이미 1번 불려 완전히 응답까지 마쳤습니다. 트립이 나긴 했지만 "모델이 아예 불리지 않았다"는 뜻은 아닙니다 — Step 5에서 이 승패를 직접 뒤집어 봅니다.)

### Step 5. 경합의 결과 — 이기면 취소되고, 지면 이미 다 끝나 있다

**목적.** Step 4에서 본 경합의 승패가 실제로 타이밍에 좌우된다는 것을, 느리게 걸리는 쪽을 바꿔 가며 양방향으로 직접 재현합니다.

**할 일.** Step 4의 확인은 판정과 보호 대상 모델 둘 다 즉시 응답하는 스크립트라 승부가 사실상 우연히 갈렸습니다. 이번엔 한쪽에 인위적인 지연을 주어 어느 쪽이 이기는지를 통제합니다 — (A) 판정은 즉시 끝나고 보호 대상 모델에 3초 지연을 주면, (B) 반대로 판정에 1초 지연을 주고 보호 대상 모델은 즉시 응답하게 합니다.

![Step 5까지의 구성](diagrams/step5.svg)

**확인.**

```bash
uv run --no-project python -c "
import agent as m
from agents import Runner, InputGuardrailTripwireTriggered
from agents.testing import ScriptedModel, ModelStep, assistant_message
import json, asyncio, time

TRIP = [assistant_message(json.dumps({'is_math_homework': True, 'reasoning': 'algebra', 'confidence': 0.95}))]

async def race(label, guardrail_script, protected_script):
    m.input_guardrail_agent = m.input_guardrail_agent.clone(model=ScriptedModel(guardrail_script))
    protected = m.root_agent.clone(model=ScriptedModel(protected_script))
    t0 = time.monotonic()
    try:
        await Runner.run(protected, 'Can you solve this equation: 2x + 5 = 15?')
    except InputGuardrailTripwireTriggered:
        elapsed = time.monotonic() - t0
        print(f'{label}: tripped after {elapsed:.2f}s')

async def main():
    state_a = {'ran_to_completion': False}
    async def slow_protected(call):
        try:
            await asyncio.sleep(3.0)
        except asyncio.CancelledError:
            raise
        state_a['ran_to_completion'] = True
        return [assistant_message(json.dumps({'response': 'too late'}))]
    await race('A) guardrail instant, protected 3s', [TRIP], [ModelStep.respond(slow_protected)])
    print('   protected model ran to completion:', state_a['ran_to_completion'])

    state_b = {'ran_to_completion': False}
    async def slow_guardrail(call):
        await asyncio.sleep(1.0)
        return TRIP
    async def fast_protected(call):
        state_b['ran_to_completion'] = True
        return [assistant_message(json.dumps({'response': 'real, fully generated answer'}))]
    await race('B) guardrail 1s, protected instant', [ModelStep.respond(slow_guardrail)], [ModelStep.respond(fast_protected)])
    print('   protected model ran to completion:', state_b['ran_to_completion'])

asyncio.run(main())
"
```

```powershell
uv run --no-project python -c "<위와 같은 코드>"
```

```
A) guardrail instant, protected 3s: tripped after 0.08s
   protected model ran to completion: False
B) guardrail 1s, protected instant: tripped after 1.02s
   protected model ran to completion: True
```

(직접 확인 — 초 단위 수치는 실행 환경의 스케줄링에 따라 조금씩 달라질 수 있지만, 두 줄의 `True`/`False` 대비는 이 SDK 버전에서 안정적으로 재현됩니다. (A)에서는 판정이 이겨 0.08초 만에 트립했고, 3초짜리 보호 대상 모델은 `asyncio.CancelledError`로 끊겨 끝까지 실행되지 못했습니다(`ran_to_completion: False`) — Step 4에서 예고한 `model_task.cancel()`이 실제로 작동한 순간입니다. (B)에서는 보호 대상 모델이 먼저 응답을 마쳤는데도(`ran_to_completion: True`) 최종 결과는 똑같이 트립입니다 — 다만 판정이 1초 걸린 만큼 전체 시간도 1.02초로 늘어났습니다. 이 실행에서 이미 완성된 응답은 호출자에게 전달되지 않고 버려집니다. 요약하면: 기본값 `run_in_parallel=True`는 "보호 대상 호출을 막는 문"이 아니라 "결과를 볼 자격이 있는지에 대한 경주"이고, 느린 쪽이 판정이면 보호 대상 호출은 이미 값을 다 만든 뒤에야 버려집니다.)

### Step 6. 출력 가드레일이 실행되는 자리 — 완성된 답을 사후 검사

**목적.** 출력 가드레일에는 `run_in_parallel` 같은 선택지 자체가 없고, 언제나 최종 출력이 이미 만들어진 뒤에만 실행된다는 것을 소스와 재현 양쪽으로 확인합니다.

**할 일.** `OutputGuardrail` 데이터클래스에는(소스로 확인, `agents/guardrail.py`) `InputGuardrail`에 있던 `run_in_parallel` 필드가 아예 없습니다. 대신 독스트링이 이렇게 말합니다 — "Output guardrails are checks that run on the final output of an agent." `Agent` 필드의 독스트링도 같은 이야기를 합니다(소스로 확인, `agents/agent.py`): "A list of checks that run on the final output of the agent, after generating a response. Runs only if the agent produces a final output." 실행 코드(소스로 확인, `agents/run.py`)를 보면 `run_output_guardrails(...)`는 `NextStepFinalOutput`이 이미 만들어진 뒤에만, 그 최종 출력값을 인자로 호출됩니다 — 입력 가드레일처럼 `asyncio.gather`로 무언가와 경쟁하는 자리가 아예 없습니다. 즉 출력 가드레일이 막을 수 있는 것은 "이 답을 호출자에게 건네주는 것"뿐이고, "이 답을 만드는 것" 자체는 이미 끝난 뒤입니다.

![Step 6까지의 구성](diagrams/step6.svg)

**확인.** 보호 대상 모델이 이미 민감한 내용을 담은 응답을 완성했다고 하고, 출력 판정이 그것을 위험하다고 판정하도록 스크립트를 짭니다.

```bash
uv run --no-project python -c "
import agent as m
from agents import Runner, OutputGuardrailTripwireTriggered
from agents.testing import ScriptedModel, assistant_message
import json, asyncio

m.input_guardrail_agent = m.input_guardrail_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'is_math_homework': False, 'reasoning': 'not homework', 'confidence': 0.05}))]
]))
m.output_guardrail_agent = m.output_guardrail_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'is_inappropriate': True, 'reasoning': 'Leaks an internal password reset procedure verbatim.', 'severity': 'high'}))]
]))
protected = m.root_agent.clone(model=ScriptedModel([
    [assistant_message(json.dumps({'response': 'Sure, here is the admin override password: hunter2.'}))]
]))

async def main():
    try:
        result = await Runner.run(protected, 'How do I reset my password?')
        print('NO TRIP:', result.final_output)
    except OutputGuardrailTripwireTriggered as e:
        print('str(e):', str(e))
        print('e.guardrail_result.guardrail.get_name():', e.guardrail_result.guardrail.get_name())
        print('e.guardrail_result.agent.name:', e.guardrail_result.agent.name)
        print('e.guardrail_result.agent_output:', e.guardrail_result.agent_output)
        print('e.guardrail_result.output.output_info:', e.guardrail_result.output.output_info)
    print('protected model calls consumed (was the unsafe answer actually generated?):', len(protected.model.calls))

asyncio.run(main())
"
```

```powershell
uv run --no-project python -c "<위와 같은 코드>"
```

```
str(e): Guardrail OutputGuardrail triggered tripwire
e.guardrail_result.guardrail.get_name(): content_safety_guardrail
e.guardrail_result.agent.name: Protected Customer Support Agent
e.guardrail_result.agent_output: response='Sure, here is the admin override password: hunter2.'
e.guardrail_result.output.output_info: is_inappropriate=True reasoning='Leaks an internal password reset procedure verbatim.' severity='high'
protected model calls consumed (was the unsafe answer actually generated?): 1
```

(직접 확인 — 마지막 줄이 핵심입니다: 위험한 응답은 이미 1번의 모델 호출로 완전히 만들어진 뒤였습니다. 취소할 대상 자체가 없습니다 — Step 5의 (A)처럼 진행 중인 호출을 잘라낼 여지가 출력 가드레일에는 원천적으로 없기 때문입니다. `str(e)`가 이번에도 "Guardrail **OutputGuardrail** triggered tripwire"로 실제 이름(`content_safety_guardrail`)을 말하지 않는 것도 입력 가드레일과 같은 패턴입니다. 반면 `e.guardrail_result`는 `agent`(누가 만들었는지)와 `agent_output`(실제로 만들어진 값)까지 담고 있어, 입력 가드레일의 `InputGuardrailResult`보다 필드가 하나 더 많습니다(소스로 확인, `agents/guardrail.py`의 두 결과 데이터클래스 비교).)

### Step 7. 키 없이 이 파일을 직접 불러보면 — 세 진입점, 세 가지 예외 처리 수준

**목적.** 실제 키 없이 `Runner.run`을 부르면 왜 가드레일의 판정 결과를 볼 수 없는지 확인하고, 이 파일 자신이 정의한 데모 함수 세 개가 그 실패를 서로 다르게 다룬다는 것을 직접 확인합니다.

**할 일.** 보호 대상 에이전트의 모델 호출과 가드레일 판정 에이전트의 모델 호출은 둘 다 결국 같은 `OpenAIProvider`를 거칩니다 — 키가 없으면 어느 쪽이 실행되든 Day 024·026이 이미 확인한 것과 같은 자리에서 `openai.OpenAIError: Missing credentials...`로 끊깁니다. 즉 진짜 키 없이는 `math_homework_guardrail`이 "무엇을 판정했는지" 자체를 볼 기회가 없습니다 — 판정 이전에 이미 끊기기 때문입니다(Step 4~6이 대신 오프라인 재현으로 답한 이유입니다). 이 파일의 세 데모 함수는 이 실패를 서로 다르게 대합니다.

`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:120-143`

```python
async def guardrails_example():
    """Demonstrates guardrails with various inputs"""
    
    test_cases = [
        "How do I reset my password?",  # Should pass
        "Can you solve this equation: 2x + 5 = 15?",  # Should trigger input guardrail
        "What are your product features?",  # Should pass
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_input} ---")
        
        try:
            result = await Runner.run(root_agent, test_input)
            print(f"✅ Success: {result.final_output.response}")
            
        except InputGuardrailTripwireTriggered as e:
            print(f"🚫 Input Guardrail Triggered: {e}")
            
        except OutputGuardrailTripwireTriggered as e:
            print(f"⚠️ Output Guardrail Triggered: {e}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
```

`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:145-157`

```python
# Standalone example functions
async def test_input_guardrail():
    """Test input guardrail specifically"""
    try:
        await Runner.run(root_agent, "Can you help me solve this calculus problem?")
        print("❌ Guardrail should have triggered")
    except InputGuardrailTripwireTriggered:
        print("✅ Input guardrail correctly triggered for math homework")

async def test_valid_request():
    """Test valid customer support request"""
    result = await Runner.run(root_agent, "I'm having trouble logging into my account. Can you help?")
    print(f"✅ Valid request processed: {result.final_output.response}")
```

세 함수 중 `guardrails_example()`만 맨 끝에 `except Exception as e:` 포괄 절을 갖고 있습니다. `test_input_guardrail()`은 `InputGuardrailTripwireTriggered`만, `test_valid_request()`는 아무 것도 잡지 않습니다. 어느 쪽이든 키가 없는 상태에서 `except Exception`이 실제로 실행되면, 그 안의 `print(f"❌ Error: {e}")`가 이모지를 그대로 찍으려다 한국어 Windows 콘솔(cp949)에서 `UnicodeEncodeError`를 낼 수 있다는 것은 Day 019가 이미 정리했으므로, 여기서는 `PYTHONIOENCODING=utf-8`로 그 너머를 바로 확인합니다.

![Step 7까지의 구성](diagrams/step7.svg)

**확인.**

```bash
PYTHONIOENCODING=utf-8 uv run --no-project python -c "
import agent as m
import asyncio

print('=== test_valid_request() (no try/except at all) ===')
try:
    asyncio.run(m.test_valid_request())
except Exception as e:
    print('RAISED:', type(e).__name__, type(e).__module__)

print()
print('=== test_input_guardrail() (only catches InputGuardrailTripwireTriggered) ===')
try:
    asyncio.run(m.test_input_guardrail())
except Exception as e:
    print('RAISED:', type(e).__name__, type(e).__module__)

print()
print('=== guardrails_example() (has a catch-all except Exception) ===')
asyncio.run(m.guardrails_example())
print('[returned normally -- exit code would be 0]')
"
```

```powershell
$env:PYTHONIOENCODING="utf-8"; uv run --no-project python -c "<위와 같은 코드>"
```

```
=== test_valid_request() (no try/except at all) ===
RAISED: OpenAIError openai

=== test_input_guardrail() (only catches InputGuardrailTripwireTriggered) ===
RAISED: OpenAIError openai

=== guardrails_example() (has a catch-all except Exception) ===

--- Test Case 1: How do I reset my password? ---
❌ Error: Missing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` environment variable.

--- Test Case 2: Can you solve this equation: 2x + 5 = 15? ---
❌ Error: Missing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` environment variable.

--- Test Case 3: What are your product features? ---
❌ Error: Missing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` environment variable.
[returned normally -- exit code would be 0]
```

(직접 확인 — `test_valid_request()`와 `test_input_guardrail()`은 둘 다 `openai.OpenAIError`를 잡지 못해 그대로 위로 튀어 오릅니다. `guardrails_example()`만 세 테스트 케이스 모두에서 그 예외를 붙잡아 "❌ Error: ..."로 출력하고 정상적으로 반환합니다 — 세 경우 모두 "✅ Success"도, "🚫 Input Guardrail Triggered"도 아닌 마지막 포괄 절에 걸린 것입니다. 즉 이 파일 안에서도 예외 처리 수준이 균일하지 않습니다 — README의 "가드레일 예외를 우아하게 처리하는 법을 배운다"는 목표는 세 함수 중 하나에만 해당합니다.)

## 요청 한 건이 흐르는 과정

![요청 시퀀스](diagrams/sequence.svg)

이 시퀀스는 아무것도 트립하지 않는 성공 경로를 순서대로 그립니다: 사용자의 질문이 보호 대상 에이전트에 들어가면 원본 입력이 입력 가드레일로, 그 가드레일은 다시 자신의 판정 에이전트를 통해 OpenAI를 호출해 `MathHomeworkCheck`를 받습니다. 트립하지 않으면 보호 대상 에이전트 자신도 OpenAI를 호출해 `AgentResponse`를 만들고, 그 값이 다시 출력 가드레일과 그 판정 에이전트를 거쳐 `ContentSafetyCheck`로 확인된 뒤에야 최종 응답이 사용자에게 돌아갑니다. 그림은 이해를 돕기 위해 순서대로 그렸지만, Step 4·5에서 직접 확인했듯 입력 가드레일의 판정 요청과 보호 대상의 실제 응답 생성 요청은 실제로는 **동시에** 나갑니다 — 어느 쪽이 먼저 끝나느냐에 따라 보호 대상 모델 호출이 중간에 잘리기도(Step 5의 (A)), 이미 완성된 채로 버려지기도(Step 5의 (B)) 합니다. 출력 가드레일 쪽은 이런 동시성이 없습니다 — 보호 대상의 응답이 완전히 만들어진 뒤에만 그림의 마지막 두 화살표가 시작됩니다(Step 6). 이 전체 시퀀스가 유효한 키로 처음부터 끝까지 이어지는 것은 직접 보지 못했습니다 — Step 2·4·5·6의 각 구간을 SDK의 오프라인 테스트 더블로 개별적으로 재현해 확인한 것입니다.

## 실행 체크리스트

- [ ] 이 폴더에 `requirements.txt`가 없다는 것과, 이 파일이 실제로 필요로 하는 서드파티 패키지는 `pydantic`·`agents` 둘뿐이라는 것을 import에서 직접 확인했다
- [ ] `pydantic`이 `openai-agents`의 전이 의존성이라 별도 설치가 필요 없다는 것을 `importlib.metadata`로 확인했다
- [ ] `math_homework_guardrail`/`content_safety_guardrail`이 `@input_guardrail`/`@output_guardrail`을 거쳐 각각 `InputGuardrail`/`OutputGuardrail` 객체가 된다는 것을 확인했다
- [ ] 두 가드레일의 트립와이어 조건이 단일 불리언이 아니라 두 조건의 AND라는 것을 소스로 확인했다
- [ ] 트립 없이 성공하는 요청 한 건이 실제로는 모델 호출 3번(입력 판정 + 보호 대상 + 출력 판정)이라는 것을 오프라인으로 직접 세었다
- [ ] `input_guardrails`/`output_guardrails`가 `Agent`의 평범한 리스트 필드이고, 이 파일엔 `import os`도 `__main__` 블록도 없어 `python agent.py`가 그대로는 아무것도 하지 않는다는 것을 확인했다
- [ ] 입력 가드레일의 기본값(`run_in_parallel=True`)이 보호 대상의 첫 모델 호출을 "막는 문"이 아니라 그것과 경쟁하는 동시 실행이라는 것을 소스로 확인했다
- [ ] 판정이 이기면 아직 끝나지 않은 보호 대상 모델 호출이 실제로 취소된다는 것을, 판정이 지면 이미 완성된 응답이 버려질 뿐 취소되지 않는다는 것을 양방향으로 직접 재현했다
- [ ] 출력 가드레일에는 `run_in_parallel` 같은 선택지가 없고, 언제나 최종 출력이 이미 만들어진 뒤에만 실행된다는 것을 소스와 재현으로 확인했다
- [ ] `InputGuardrailTripwireTriggered`/`OutputGuardrailTripwireTriggered`를 `print(f"...{e}")`로 찍으면 실제로 트립한 가드레일 이름이 아니라 감싸는 클래스 이름만 보인다는 것을 확인했다
- [ ] 키가 없으면 보호 대상과 가드레일 판정 에이전트 모두 같은 지점(`openai.OpenAIError: Missing credentials`)에서 끊긴다는 것을, 그리고 이 파일의 데모 함수 세 개가 그 실패를 서로 다른 수준으로 처리한다는 것을 직접 확인했다

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| `guardrails_example()`이 키 없이 실행되다가 API 오류 대신 `UnicodeEncodeError: 'cp949' codec can't encode character '❌'...`로 먼저 멈춤 | 마지막 `except Exception`절의 `print(f"❌ Error: {e}")`가 이모지를 그대로 찍는데, 한국어 Windows 콘솔의 기본 코드페이지 `cp949`는 이모지를 인코딩하지 못한다(Day 019와 같은 종류, 직접 확인) | `PYTHONIOENCODING=utf-8 uv run --no-project python -c "..."`처럼 환경변수를 지정하거나(PowerShell은 `$env:PYTHONIOENCODING="utf-8"`), 콘솔을 `chcp 65001`로 바꾼다 |
| 키 없이 `Runner.run(root_agent, ...)`을 불러도 `InputGuardrailTripwireTriggered`가 나지 않고 `openai.OpenAIError: Missing credentials...`만 남 | 가드레일 자신의 판정 에이전트(`input_guardrail_agent`)도 결국 `Runner.run()`으로 모델을 호출해야 하는데, 키가 없으면 보호 대상과 똑같은 지점에서 먼저 끊긴다(직접 확인) | 실제 트립 동작을 보려면 유효한 키를 쓰거나, 이 문서의 Step 4~6처럼 `agents.testing.ScriptedModel`로 판정·보호 대상 양쪽의 모델을 오프라인 응답으로 대체한다 |
| `except InputGuardrailTripwireTriggered as e: print(f"...{e}")`가 여러 개의 입력 가드레일 중 어느 것이 트립했는지 알려주지 않고 매번 "Guardrail InputGuardrail triggered tripwire"만 찍음 | 예외 메시지가 `guardrail_result.guardrail.__class__.__name__`(항상 래퍼 클래스 이름)을 쓰지, 함수 이름을 쓰지 않는다(소스로 확인, `agents/exceptions.py`) | `e.guardrail_result.guardrail.get_name()`으로 실제 가드레일 함수 이름을 꺼낸다 |
| 같은 파일 안에서 `test_valid_request()`/`test_input_guardrail()`을 부르면 키 없이 프로그램이 처리되지 않은 예외로 죽는데, `guardrails_example()`은 죽지 않음 | 이 두 함수엔 `guardrails_example()`에 있는 마지막 `except Exception` 포괄 절이 없다(직접 확인, Step 7) | 두 함수를 그대로 쓰려면 호출부를 직접 `try/except`로 감싸거나, 키 없이 패턴만 보고 싶다면 `guardrails_example()`을 대신 부른다 |

## 더 해보기

- `guardrails_example()`의 두 가드레일 전용 except 절(`ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:136-137`, `ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/agent.py:139-140`)을 사본에서 `e.guardrail_result.guardrail.get_name()`을 찍도록 고쳐, 지금의 일반 메시지 대신 실제로 어떤 가드레일이 트립했는지 나오는지 확인해보기
- `math_homework_guardrail`을 `@input_guardrail(run_in_parallel=False)`로 다시 선언한 사본을 만들어 Step 5의 (A) 실험을 다시 돌려보고, 이번에는 판정이 끝나기 전까지 보호 대상 모델 호출 자체가 아예 시작되지 않는지 확인해보기
- `root_agent.clone(input_guardrails=[math_homework_guardrail, math_homework_guardrail])`처럼 같은 가드레일을 두 번 등록해, `agents.testing.ScriptedModel`에 판정 에이전트용 스텝을 2개 채워 두고 `Runner.run()`을 실행해 정말 판정 호출이 두 번 나가는지 확인해보기

## 다음 날 예고

[Day 030 · OpenAI Agents SDK Crash Course · 7_sessions](../day030-openai-sdk-7-sessions/README.md) — `Session` 객체로 대화 기록을 여러 턴에 걸쳐 자동으로 유지하는 방법을 다룹니다. 매 턴 `.to_input_list()`를 직접 이어붙이는 대신 SQLite 기반 세션이 기록을 대신 관리합니다.
