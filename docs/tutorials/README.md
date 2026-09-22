# awesome-llm-apps 164일 튜토리얼

이 리포에 있는 앱을 하루에 하나씩, 처음부터 끝까지 따라 만드는 시리즈입니다. 하루 분량은 60~90분이고, 매 일차는 완성 아키텍처와 각 단계의 시스템 구성을 D2 다이어그램으로 보여 줍니다. 순서는 학습 난이도 순이며 볼륨 안에서는 작은 앱부터 갑니다.

## 이렇게 진행하세요

1. 아래 표에서 오늘 일차를 열고 "오늘 만들 것"과 완성 아키텍처 그림을 먼저 봅니다.
2. "사전 준비"의 키와 도구를 마련합니다. 공통 준비는 바로 아래 절을 한 번만 하면 됩니다.
3. "단계별 진행"을 순서대로 따라가며 각 Step의 **확인** 명령을 꼭 실행합니다. 그림에서 주황 테두리가 이번 Step에 새로 붙는 부분이고, 흐린 부분은 아직 만들지 않았거나 이번 Step에서는 실행되지 않는 부분입니다.
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

**그리고 `uv venv`를 건너뛰지 마세요.** `--no-project`는 "이 폴더를 프로젝트로 취급하지 말라"는 뜻일 뿐, 쓸 가상환경을 찾는 일은 그대로 합니다. 앱 폴더에 `.venv`가 없으면 uv는 상위 폴더로 올라가며 찾고 결국 저장소 루트의 환경을 집습니다 — 오류 없이 조용히 그렇게 됩니다. 그러면 방금 설치한 패키지가 아니라 엉뚱한 것이 import되고, 실제로 OpenAI Agents SDK 볼륨(Day 24~34)에서는 루트 환경에 이름이 같은 다른 패키지(TensorFlow Agents)가 들어 있어 원인과 한참 떨어진 오류가 납니다. 각 일차의 Step 1을 건너뛰고 뒤쪽 명령부터 실행하면 이 함정에 빠집니다.

리포 루트의 공용 환경(`uv sync --all-extras`)을 쓰는 방법은 [UV_MIGRATION_GUIDE.md](../../UV_MIGRATION_GUIDE.md)에 있습니다. 앱마다 의존성 버전이 달라 충돌할 수 있으므로, 튜토리얼의 확인 명령은 모두 독립 가상환경 기준으로 검증했습니다.

## 다이어그램 읽는 법

색이 아니라 **모양**이 종류를 말합니다. 강조색은 주황 하나뿐이고, 그 하나는 "이번 Step"에만 씁니다.

| 표현 | 뜻 |
|---|---|
| 사람 모양 | 사용자 |
| 사각형 | 이 리포의 코드 (앱, 에이전트, 도구 함수) |
| 구름 | 외부 API, LLM 제공자 |
| 원통 | DB, 벡터 저장소, 캐시 |
| 문서 모양 | 파일, 설정 |
| 주황 테두리 | 이번 Step에서 새로 추가된 부분 |
| 흐리고 점선 | 아직 만들지 않았거나, 이번 Step의 실행에서는 거치지 않는 부분 |

다이어그램 소스는 각 일차의 `diagrams/*.d2`에 있고, 렌더와 검사는 `docs/tutorials/_tools`에서 `npm install && npm run render && npm run check`로 합니다. 한글 글리프는 SVG 안에 직접 넣기 때문에 보는 사람 컴퓨터에 한국어 폰트가 없어도 같은 모양으로 보입니다 — 폰트는 `_tools/fonts/build.py`가 Noto Sans KR(OFL)에서 필요한 글자만 추려 만듭니다.

## 다루지 않는 항목

README에 실려 있지만 코드가 외부 리포에 있는 두 항목은 링크만 남깁니다: [Openwork](https://github.com/accomplish-ai/coworker), [OpenSource Voice Dictation Agent](https://github.com/akshayaggarwal/wispr-flow-clone).

## 164일 일정

진도: 30 / 164일 완료

### 볼륨 1. 🌱 Starter AI Agents (Day 1–13, 13일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ✅ | [Day 001](day001-xai-finance-agent/README.md) | 📊 xAI Finance Agent | [starter_ai_agents/xai_finance_agent](../../starter_ai_agents/xai_finance_agent/) |
| ✅ | [Day 002](day002-web-scraping-ai-agent/README.md) | 🕸️ Web Scraping AI Agent | [starter_ai_agents/web_scraping_ai_agent](../../starter_ai_agents/web_scraping_ai_agent/) |
| ✅ | [Day 003](day003-ai-blog-to-podcast-agent/README.md) | 🎙️ AI Blog to Podcast Agent | [starter_ai_agents/ai_blog_to_podcast_agent](../../starter_ai_agents/ai_blog_to_podcast_agent/) |
| ✅ | [Day 004](day004-ai-music-generator-agent/README.md) | 🎵 AI Music Generator Agent | [starter_ai_agents/ai_music_generator_agent](../../starter_ai_agents/ai_music_generator_agent/) |
| ✅ | [Day 005](day005-mixture-of-agents/README.md) | 🔄 Mixture of Agents | [starter_ai_agents/mixture_of_agents](../../starter_ai_agents/mixture_of_agents/) |
| ✅ | [Day 006](day006-ai-data-analysis-agent/README.md) | 📊 AI Data Analysis Agent | [starter_ai_agents/ai_data_analysis_agent](../../starter_ai_agents/ai_data_analysis_agent/) |
| ✅ | [Day 007](day007-ai-meme-generator-agent-browseruse/README.md) | 😂 AI Meme Generator Agent (Browser) | [starter_ai_agents/ai_meme_generator_agent_browseruse](../../starter_ai_agents/ai_meme_generator_agent_browseruse/) |
| ✅ | [Day 008](day008-ai-medical-imaging-agent/README.md) | 🩻 AI Medical Imaging Agent | [starter_ai_agents/ai_medical_imaging_agent](../../starter_ai_agents/ai_medical_imaging_agent/) |
| ✅ | [Day 009](day009-multimodal-ai-agent/README.md) | ✨ Gemini Multimodal Agent | [starter_ai_agents/multimodal_ai_agent](../../starter_ai_agents/multimodal_ai_agent/) |
| ✅ | [Day 010](day010-ai-x402-paying-agent/README.md) | 💸 AI x402 Paying Agent | [starter_ai_agents/ai_x402_paying_agent](../../starter_ai_agents/ai_x402_paying_agent/) |
| ✅ | [Day 011](day011-ai-breakup-recovery-agent/README.md) | ❤️‍🩹 AI Breakup Recovery Agent | [starter_ai_agents/ai_breakup_recovery_agent](../../starter_ai_agents/ai_breakup_recovery_agent/) |
| ✅ | [Day 012](day012-ai-travel-agent/README.md) | 🛫 AI Travel Agent (Local & Cloud) | [starter_ai_agents/ai_travel_agent](../../starter_ai_agents/ai_travel_agent/) |
| ✅ | [Day 013](day013-openai-research-agent/README.md) | 🔍 OpenAI Research Agent | [starter_ai_agents/openai_research_agent](../../starter_ai_agents/openai_research_agent/) |

### 볼륨 2. 🧑‍🏫 Crash Courses (Day 14–34, 21일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ✅ | [Day 014](day014-adk-1-starter-agent/README.md) | Google ADK Crash Course · 1_starter_agent | [ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent/) |
| ✅ | [Day 015](day015-adk-2-model-agnostic-agent/README.md) | Google ADK Crash Course · 2_model_agnostic_agent | [ai_agent_framework_crash_course/google_adk_crash_course/2_model_agnostic_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/2_model_agnostic_agent/) |
| ✅ | [Day 016](day016-adk-3-structured-output-agent/README.md) | Google ADK Crash Course · 3_structured_output_agent | [ai_agent_framework_crash_course/google_adk_crash_course/3_structured_output_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/3_structured_output_agent/) |
| ✅ | [Day 017](day017-adk-4-tool-using-agent/README.md) | Google ADK Crash Course · 4_tool_using_agent | [ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent/) |
| ✅ | [Day 018](day018-adk-5-memory-agent/README.md) | Google ADK Crash Course · 5_memory_agent | [ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent/) |
| ✅ | [Day 019](day019-adk-6-callbacks/README.md) | Google ADK Crash Course · 6_callbacks | [ai_agent_framework_crash_course/google_adk_crash_course/6_callbacks](../../ai_agent_framework_crash_course/google_adk_crash_course/6_callbacks/) |
| ✅ | [Day 020](day020-adk-7-plugins/README.md) | Google ADK Crash Course · 7_plugins | [ai_agent_framework_crash_course/google_adk_crash_course/7_plugins](../../ai_agent_framework_crash_course/google_adk_crash_course/7_plugins/) |
| ✅ | [Day 021](day021-adk-8-simple-multi-agent/README.md) | Google ADK Crash Course · 8_simple_multi_agent | [ai_agent_framework_crash_course/google_adk_crash_course/8_simple_multi_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/8_simple_multi_agent/) |
| ✅ | [Day 022](day022-adk-9-multi-agent-patterns/README.md) | Google ADK Crash Course · 9_multi_agent_patterns | [ai_agent_framework_crash_course/google_adk_crash_course/9_multi_agent_patterns](../../ai_agent_framework_crash_course/google_adk_crash_course/9_multi_agent_patterns/) |
| ✅ | [Day 023](day023-adk-10-adk-yaml-examples/README.md) | Google ADK Crash Course · adk_yaml_examples | [ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples](../../ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples/) |
| ✅ | [Day 024](day024-openai-sdk-1-starter-agent/README.md) | OpenAI Agents SDK Crash Course · 1_starter_agent | [ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent](../../ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent/) |
| ✅ | [Day 025](day025-openai-sdk-2-structured-output-agent/README.md) | OpenAI Agents SDK Crash Course · 2_structured_output_agent | [ai_agent_framework_crash_course/openai_sdk_crash_course/2_structured_output_agent](../../ai_agent_framework_crash_course/openai_sdk_crash_course/2_structured_output_agent/) |
| ✅ | [Day 026](day026-openai-sdk-3-tool-using-agent/README.md) | OpenAI Agents SDK Crash Course · 3_tool_using_agent | [ai_agent_framework_crash_course/openai_sdk_crash_course/3_tool_using_agent](../../ai_agent_framework_crash_course/openai_sdk_crash_course/3_tool_using_agent/) |
| ✅ | [Day 027](day027-openai-sdk-4-running-agents/README.md) | OpenAI Agents SDK Crash Course · 4_running_agents | [ai_agent_framework_crash_course/openai_sdk_crash_course/4_running_agents](../../ai_agent_framework_crash_course/openai_sdk_crash_course/4_running_agents/) |
| ✅ | [Day 028](day028-openai-sdk-5-context-management/README.md) | OpenAI Agents SDK Crash Course · 5_context_management | [ai_agent_framework_crash_course/openai_sdk_crash_course/5_context_management](../../ai_agent_framework_crash_course/openai_sdk_crash_course/5_context_management/) |
| ✅ | [Day 029](day029-openai-sdk-6-guardrails-validation/README.md) | OpenAI Agents SDK Crash Course · 6_guardrails_validation | [ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation](../../ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/) |
| ✅ | [Day 030](day030-openai-sdk-7-sessions/README.md) | OpenAI Agents SDK Crash Course · 7_sessions | [ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions](../../ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions/) |
| ⬜ | [Day 031](day031-openai-sdk-8-handoffs-delegation/README.md) | OpenAI Agents SDK Crash Course · 8_handoffs_delegation | [ai_agent_framework_crash_course/openai_sdk_crash_course/8_handoffs_delegation](../../ai_agent_framework_crash_course/openai_sdk_crash_course/8_handoffs_delegation/) |
| ⬜ | [Day 032](day032-openai-sdk-9-multi-agent-orchestration/README.md) | OpenAI Agents SDK Crash Course · 9_multi_agent_orchestration | [ai_agent_framework_crash_course/openai_sdk_crash_course/9_multi_agent_orchestration](../../ai_agent_framework_crash_course/openai_sdk_crash_course/9_multi_agent_orchestration/) |
| ⬜ | [Day 033](day033-openai-sdk-10-tracing-observability/README.md) | OpenAI Agents SDK Crash Course · 10_tracing_observability | [ai_agent_framework_crash_course/openai_sdk_crash_course/10_tracing_observability](../../ai_agent_framework_crash_course/openai_sdk_crash_course/10_tracing_observability/) |
| ⬜ | [Day 034](day034-openai-sdk-11-voice/README.md) | OpenAI Agents SDK Crash Course · 11_voice | [ai_agent_framework_crash_course/openai_sdk_crash_course/11_voice](../../ai_agent_framework_crash_course/openai_sdk_crash_course/11_voice/) |

### 볼륨 3. 🌱 Starter AI Agents (추가분) (Day 35–38, 4일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | [Day 035](day035-ai-data-visualisation-agent/README.md) | 📊 AI Data Visualization Agent | [starter_ai_agents/ai_data_visualisation_agent](../../starter_ai_agents/ai_data_visualisation_agent/) |
| ⬜ | [Day 036](day036-ai-life-insurance-advisor-agent/README.md) | 🛡️ Life Insurance Coverage Advisor Agent | [starter_ai_agents/ai_life_insurance_advisor_agent](../../starter_ai_agents/ai_life_insurance_advisor_agent/) |
| ⬜ | [Day 037](day037-ai-reasoning-agent/README.md) | AI Reasoning Agent | [starter_ai_agents/ai_reasoning_agent](../../starter_ai_agents/ai_reasoning_agent/) |
| ⬜ | [Day 038](day038-ai-startup-trend-analysis-agent/README.md) | 📈 AI Startup Trend Analysis Agent | [starter_ai_agents/ai_startup_trend_analysis_agent](../../starter_ai_agents/ai_startup_trend_analysis_agent/) |

### 볼륨 4. 💬 Chat with X (Day 39–46, 8일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | [Day 039](day039-chat-with-substack/README.md) | 📝 Chat with Substack | [advanced_llm_apps/chat_with_X_tutorials/chat_with_substack](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_substack/) |
| ⬜ | [Day 040](day040-chat-with-research-papers/README.md) | 📚 Chat with Research Papers (ArXiv) (GPT & Llama3) | [advanced_llm_apps/chat_with_X_tutorials/chat_with_research_papers](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_research_papers/) |
| ⬜ | [Day 041](day041-chat-with-github/README.md) | 💬 Chat with GitHub (GPT & Llama3) | [advanced_llm_apps/chat_with_X_tutorials/chat_with_github](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_github/) |
| ⬜ | [Day 042](day042-chat-with-pdf/README.md) | 📄 Chat with PDF (GPT & Llama3) | [advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf/) |
| ⬜ | [Day 043](day043-chat-with-youtube-videos/README.md) | 📽️ Chat with YouTube Videos | [advanced_llm_apps/chat_with_X_tutorials/chat_with_youtube_videos](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_youtube_videos/) |
| ⬜ | [Day 044](day044-chat-with-gmail/README.md) | 📨 Chat with Gmail | [advanced_llm_apps/chat_with_X_tutorials/chat_with_gmail](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_gmail/) |
| ⬜ | [Day 045](day045-streaming-ai-chatbot/README.md) | Streaming AI Chatbot | [advanced_llm_apps/chat_with_X_tutorials/streaming_ai_chatbot](../../advanced_llm_apps/chat_with_X_tutorials/streaming_ai_chatbot/) |
| ⬜ | [Day 046](day046-chat-with-tarots/README.md) | ✨ The Magician IA Reader: AI-Powered NLP & Tarot Insights ✨ | [advanced_llm_apps/chat-with-tarots](../../advanced_llm_apps/chat-with-tarots/) |

### 볼륨 5. 📀 RAG (Day 47–70, 24일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | [Day 047](day047-local-rag-agent/README.md) | 🦙 Local RAG Agent | [rag_tutorials/local_rag_agent](../../rag_tutorials/local_rag_agent/) |
| ⬜ | [Day 048](day048-llama3.1-local-rag/README.md) | 🔄 Llama 3.1 Local RAG | [rag_tutorials/llama3.1_local_rag](../../rag_tutorials/llama3.1_local_rag/) |
| ⬜ | [Day 049](day049-autonomous-rag/README.md) | 🔍 Autonomous RAG | [rag_tutorials/autonomous_rag](../../rag_tutorials/autonomous_rag/) |
| ⬜ | [Day 050](day050-agentic-rag-embedding-gemma/README.md) | 🔥 Agentic RAG with Embedding Gemma | [rag_tutorials/agentic_rag_embedding_gemma](../../rag_tutorials/agentic_rag_embedding_gemma/) |
| ⬜ | [Day 051](day051-rag-as-a-service/README.md) | 🧩 RAG-as-a-Service | [rag_tutorials/rag-as-a-service](../../rag_tutorials/rag-as-a-service/) |
| ⬜ | [Day 052](day052-rag-chain/README.md) | ⛓️ Basic RAG Chain | [rag_tutorials/rag_chain](../../rag_tutorials/rag_chain/) |
| ⬜ | [Day 053](day053-hybrid-search-rag/README.md) | 👀 Hybrid Search RAG (Cloud) | [rag_tutorials/hybrid_search_rag](../../rag_tutorials/hybrid_search_rag/) |
| ⬜ | [Day 054](day054-agentic-rag-with-reasoning/README.md) | 🧐 Agentic RAG with Reasoning | [rag_tutorials/agentic_rag_with_reasoning](../../rag_tutorials/agentic_rag_with_reasoning/) |
| ⬜ | [Day 055](day055-local-hybrid-search-rag/README.md) | 🖥️ Local Hybrid Search RAG | [rag_tutorials/local_hybrid_search_rag](../../rag_tutorials/local_hybrid_search_rag/) |
| ⬜ | [Day 056](day056-rag-failure-diagnostics-clinic/README.md) | 🩺 RAG Failure Diagnostics Clinic | [rag_tutorials/rag_failure_diagnostics_clinic](../../rag_tutorials/rag_failure_diagnostics_clinic/) |
| ⬜ | [Day 057](day057-rag-agent-cohere/README.md) | ✨ RAG Agent with Cohere | [rag_tutorials/rag_agent_cohere](../../rag_tutorials/rag_agent_cohere/) |
| ⬜ | [Day 058](day058-contextualai-rag-agent/README.md) | 🔄 Contextual AI RAG Agent | [rag_tutorials/contextualai_rag_agent](../../rag_tutorials/contextualai_rag_agent/) |
| ⬜ | [Day 059](day059-ai-blog-search/README.md) | 📰 AI Blog Search (RAG) | [rag_tutorials/ai_blog_search](../../rag_tutorials/ai_blog_search/) |
| ⬜ | [Day 060](day060-rag-database-routing/README.md) | 📠 RAG with Database Routing | [rag_tutorials/rag_database_routing](../../rag_tutorials/rag_database_routing/) |
| ⬜ | [Day 061](day061-corrective-rag/README.md) | 🔄 Corrective RAG (CRAG) | [rag_tutorials/corrective_rag](../../rag_tutorials/corrective_rag/) |
| ⬜ | [Day 062](day062-gemini-agentic-rag/README.md) | 🤔 Gemini Agentic RAG | [rag_tutorials/gemini_agentic_rag](../../rag_tutorials/gemini_agentic_rag/) |
| ⬜ | [Day 063](day063-knowledge-graph-rag-citations/README.md) | 🕸️ Knowledge Graph RAG with Citations | [rag_tutorials/knowledge_graph_rag_citations](../../rag_tutorials/knowledge_graph_rag_citations/) |
| ⬜ | [Day 064](day064-deepseek-local-rag-agent/README.md) | 🐋 Deepseek Local RAG Agent | [rag_tutorials/deepseek_local_rag_agent](../../rag_tutorials/deepseek_local_rag_agent/) |
| ⬜ | [Day 065](day065-vision-rag/README.md) | 🖼️ Vision RAG | [rag_tutorials/vision_rag](../../rag_tutorials/vision_rag/) |
| ⬜ | [Day 066](day066-agentic-typed-rag-pydanticai/README.md) | 📎 Typed Agentic RAG with Pydantic AI | [rag_tutorials/agentic_typed_rag_pydanticai](../../rag_tutorials/agentic_typed_rag_pydanticai/) |
| ⬜ | [Day 067](day067-multimodal-agentic-rag/README.md) | 🧬 Multimodal Agentic RAG | [rag_tutorials/multimodal_agentic_rag](../../rag_tutorials/multimodal_agentic_rag/) |
| ⬜ | [Day 068](day068-agentic-rag-gpt5/README.md) | 🧠 Agentic RAG with GPT-5 | [rag_tutorials/agentic_rag_gpt5](../../rag_tutorials/agentic_rag_gpt5/) |
| ⬜ | [Day 069](day069-agentic-rag-math-agent/README.md) | 🧠 Math Tutor Agent – Agentic RAG with Feedback Loop | [rag_tutorials/agentic_rag_math_agent](../../rag_tutorials/agentic_rag_math_agent/) |
| ⬜ | [Day 070](day070-qwen-local-rag/README.md) | 🐋 Qwen 3 Local RAG Reasoning Agent | [rag_tutorials/qwen_local_rag](../../rag_tutorials/qwen_local_rag/) |

### 볼륨 6. 💾 LLM Apps with Memory (Day 71–77, 7일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 071 | 💬 Llama3 Stateful Chat | [advanced_llm_apps/llm_apps_with_memory_tutorials/llama3_stateful_chat](../../advanced_llm_apps/llm_apps_with_memory_tutorials/llama3_stateful_chat/) |
| ⬜ | Day 072 | 💾 AI ArXiv Agent with Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/ai_arxiv_agent_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/ai_arxiv_agent_memory/) |
| ⬜ | Day 073 | 📝 LLM App with Personalized Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory/) |
| ⬜ | Day 074 | 🧠 Multi-LLM Application with Shared Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/multi_llm_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/multi_llm_memory/) |
| ⬜ | Day 075 | 🛩️ AI Travel Agent with Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/ai_travel_agent_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/ai_travel_agent_memory/) |
| ⬜ | Day 076 | 🗄️ Local ChatGPT Clone with Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/) |
| ⬜ | Day 077 | 🎯 AI Career Coach with Memory (ADK Multi-Agent) | [advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/adk_career_coach_agent_memory/) |

### 볼륨 7. 🚀 Advanced AI Agents (Day 78–111, 34일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 078 | 📈 AI Investment Agent | [advanced_ai_agents/single_agent_apps/ai_investment_agent](../../advanced_ai_agents/single_agent_apps/ai_investment_agent/) |
| ⬜ | Day 079 | 🎬 AI Movie Production Agent | [advanced_ai_agents/single_agent_apps/ai_movie_production_agent](../../advanced_ai_agents/single_agent_apps/ai_movie_production_agent/) |
| ⬜ | Day 080 | 🧬 AI Self-Evolving Agent | [advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent](../../advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/) |
| ⬜ | Day 081 | 🗞️ AI Journalist Agent | [advanced_ai_agents/single_agent_apps/ai_journalist_agent](../../advanced_ai_agents/single_agent_apps/ai_journalist_agent/) |
| ⬜ | Day 082 | 🔬 AI Research Planner & Executor (Google Interactions API) | [advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api](../../advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api/) |
| ⬜ | Day 083 | 🔍 AI Deep Research Agent | [advanced_ai_agents/single_agent_apps/ai_deep_research_agent](../../advanced_ai_agents/single_agent_apps/ai_deep_research_agent/) |
| ⬜ | Day 084 | 📑 AI Meeting Agent | [advanced_ai_agents/single_agent_apps/ai_meeting_agent](../../advanced_ai_agents/single_agent_apps/ai_meeting_agent/) |
| ⬜ | Day 085 | 🧠 AI Mental Wellbeing Agent | [advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent](../../advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent/) |
| ⬜ | Day 086 | 🏋️‍♂️ AI Health & Fitness Agent | [advanced_ai_agents/single_agent_apps/ai_health_fitness_agent](../../advanced_ai_agents/single_agent_apps/ai_health_fitness_agent/) |
| ⬜ | Day 087 | 🏗️ AI System Architect Agent | [advanced_ai_agents/single_agent_apps/ai_system_architect_r1](../../advanced_ai_agents/single_agent_apps/ai_system_architect_r1/) |
| ⬜ | Day 088 | 🤝 AI Consultant Agent | [advanced_ai_agents/single_agent_apps/ai_consultant_agent](../../advanced_ai_agents/single_agent_apps/ai_consultant_agent/) |
| ⬜ | Day 089 | 🚀 AI Product Launch Intelligence Agent | [advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent](../../advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent/) |
| ⬜ | Day 090 | 🛡️ Trust-Gated Multi-Agent Research Team | [advanced_ai_agents/multi_agent_apps/trust_gated_agent_team](../../advanced_ai_agents/multi_agent_apps/trust_gated_agent_team/) |
| ⬜ | Day 091 | 👨🏻‍💼 AI Sales Intelligence Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team/) |
| ⬜ | Day 092 | 📊 AI VC Due Diligence Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team/) |
| ⬜ | Day 093 | 🔍 AI Fraud Investigation Agent | [advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent](../../advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent/) |
| ⬜ | Day 094 | 💰 AI Financial Coach Agent | [advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent](../../advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent/) |
| ⬜ | Day 095 | 🏚️ 🍌 AI Home Renovation Agent with Nano Banana Pro | [advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent](../../advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent/) |
| ⬜ | Day 096 | 🧠 DevPulse AI - Multi-Agent Signal Intelligence | [advanced_ai_agents/multi_agent_apps/devpulse_ai](../../advanced_ai_agents/multi_agent_apps/devpulse_ai/) |
| ⬜ | Day 097 | 📡 Earnings Call Analyst Agent | [advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent](../../advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/) |
| ⬜ | Day 098 | 🎧 AI Social Media News and Podcast Agent | [advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents](../../advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/) |
| ⬜ | Day 099 | 🛡️ AI Agent Governance - Policy-Based Sandboxing | [advanced_ai_agents/single_agent_apps/ai_agent_governance](../../advanced_ai_agents/single_agent_apps/ai_agent_governance/) |
| ⬜ | Day 100 | 🛒 AI Customer Support Agent with Memory | [advanced_ai_agents/single_agent_apps/ai_customer_support_agent](../../advanced_ai_agents/single_agent_apps/ai_customer_support_agent/) |
| ⬜ | Day 101 | 🚀 AI Email GTM Reachout Agent | [advanced_ai_agents/single_agent_apps/ai_email_gtm_reachout_agent](../../advanced_ai_agents/single_agent_apps/ai_email_gtm_reachout_agent/) |
| ⬜ | Day 102 | 💰 AI Personal Finance Planner | [advanced_ai_agents/single_agent_apps/ai_personal_finance_agent](../../advanced_ai_agents/single_agent_apps/ai_personal_finance_agent/) |
| ⬜ | Day 103 | 🍽️ AI Recipe & Meal Planning Agent | [advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent](../../advanced_ai_agents/single_agent_apps/ai_recipe_meal_planning_agent/) |
| ⬜ | Day 104 | 🔥 AI Startup Insight with Firecrawl FIRE-1 Agent | [advanced_ai_agents/single_agent_apps/ai_startup_insight_fire1_agent](../../advanced_ai_agents/single_agent_apps/ai_startup_insight_fire1_agent/) |
| ⬜ | Day 105 | 🌍 AQI Analysis Agent | [advanced_ai_agents/multi_agent_apps/ai_aqi_analysis_agent](../../advanced_ai_agents/multi_agent_apps/ai_aqi_analysis_agent/) |
| ⬜ | Day 106 | ⚡ Codebase Migration & Refactor Planner (LangGraph) | [advanced_ai_agents/multi_agent_apps/ai_codebase_migration_agent](../../advanced_ai_agents/multi_agent_apps/ai_codebase_migration_agent/) |
| ⬜ | Day 107 | 🔍 AI Domain Deep Research Agent | [advanced_ai_agents/multi_agent_apps/ai_domain_deep_research_agent](../../advanced_ai_agents/multi_agent_apps/ai_domain_deep_research_agent/) |
| ⬜ | Day 108 | Requirements | [advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent](../../advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent/) |
| ⬜ | Day 109 | AI Speech Trainer Agent | [advanced_ai_agents/multi_agent_apps/ai_speech_trainer_agent](../../advanced_ai_agents/multi_agent_apps/ai_speech_trainer_agent/) |
| ⬜ | Day 110 | 📰 Multi-Agent AI Researcher | [advanced_ai_agents/multi_agent_apps/multi_agent_researcher](../../advanced_ai_agents/multi_agent_apps/multi_agent_researcher/) |
| ⬜ | Day 111 | 🤝 Multi-Agent Trust Layer - Secure Agent-to-Agent Communication | [advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer](../../advanced_ai_agents/multi_agent_apps/multi_agent_trust_layer/) |

### 볼륨 8. 🤝 Multi-agent Teams (Day 112–126, 15일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 112 | 💲 AI Finance Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team/) |
| ⬜ | Day 113 | 👨‍🏫 AI Teaching Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/) |
| ⬜ | Day 114 | ✨ Multimodal Design Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team/) |
| ⬜ | Day 115 | 💻 Multimodal Coding Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team/) |
| ⬜ | Day 116 | 🎨 AI Game Design Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team/) |
| ⬜ | Day 117 | 🧲 AI Competitor Intelligence Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team/) |
| ⬜ | Day 118 | 👨‍💼 AI Services Agency (CrewAI) | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency/) |
| ⬜ | Day 119 | 🧭 AG2 Adaptive Research Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team/) |
| ⬜ | Day 120 | 💼 AI Recruitment Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team/) |
| ⬜ | Day 121 | 👨‍⚖️ AI Legal Agent Team (Cloud & Local) | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team/) |
| ⬜ | Day 122 | 🎨 🍌 Multimodal UI/UX Feedback Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team/) |
| ⬜ | Day 123 | 🏠 AI Real Estate Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team/) |
| ⬜ | Day 124 | 🌏 AI Travel Planner Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/) |
| ⬜ | Day 125 | 🔍 AI SEO Audit Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_seo_audit_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_seo_audit_team/) |
| ⬜ | Day 126 | ⚖️ LLM Panel Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/llm_panel_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/llm_panel_agent_team/) |

### 볼륨 9. ♾️ MCP AI Agents (Day 127–133, 7일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 127 | 📑 Notion MCP Agent | [mcp_ai_agents/notion_mcp_agent](../../mcp_ai_agents/notion_mcp_agent/) |
| ⬜ | Day 128 | 🐙 GitHub MCP Agent | [mcp_ai_agents/github_mcp_agent](../../mcp_ai_agents/github_mcp_agent/) |
| ⬜ | Day 129 | ♾️ Browser MCP Agent | [mcp_ai_agents/browser_mcp_agent](../../mcp_ai_agents/browser_mcp_agent/) |
| ⬜ | Day 130 | 🔌 OpenAI Remote MCP Tool Bridge | [mcp_ai_agents/openai_remote_mcp_bridge](../../mcp_ai_agents/openai_remote_mcp_bridge/) |
| ⬜ | Day 131 | 🌍 AI Travel Planner MCP Agent | [mcp_ai_agents/ai_travel_planner_mcp_agent_team](../../mcp_ai_agents/ai_travel_planner_mcp_agent_team/) |
| ⬜ | Day 132 | 🔀 Multi-MCP Agent Router | [mcp_ai_agents/multi_mcp_agent_router](../../mcp_ai_agents/multi_mcp_agent_router/) |
| ⬜ | Day 133 | 🚀 Multi-MCP Intelligent Assistant | [mcp_ai_agents/multi_mcp_agent](../../mcp_ai_agents/multi_mcp_agent/) |

### 볼륨 10. 🎮 Autonomous Game-Playing (Day 134–136, 3일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 134 | ♜ AI Chess Agent | [advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent](../../advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent/) |
| ⬜ | Day 135 | 🎮 AI 3D Pygame Agent | [advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1](../../advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1/) |
| ⬜ | Day 136 | 🎲 AI Tic-Tac-Toe Agent | [advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent](../../advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent/) |

### 볼륨 11. 🗣️ Voice AI Agents (Day 137–140, 4일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 137 | 📞 Customer Support Voice Agent | [voice_ai_agents/customer_support_voice_agent](../../voice_ai_agents/customer_support_voice_agent/) |
| ⬜ | Day 138 | 🔊 Voice RAG Agent (OpenAI SDK) | [voice_ai_agents/voice_rag_openaisdk](../../voice_ai_agents/voice_rag_openaisdk/) |
| ⬜ | Day 139 | 🗣️ AI Audio Tour Agent | [voice_ai_agents/ai_audio_tour_agent](../../voice_ai_agents/ai_audio_tour_agent/) |
| ⬜ | Day 140 | 🛡️ Insurance Claim Live Agent Team | [voice_ai_agents/insurance_claim_live_agent_team](../../voice_ai_agents/insurance_claim_live_agent_team/) |

### 볼륨 12. 🖼️ Generative UI (Day 141–147, 7일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 141 | 🔍 AI Deep Research Agent | [generative_ui_agents/ai-deep-research-agent](../../generative_ui_agents/ai-deep-research-agent/) |
| ⬜ | Day 142 | 🪙 AI Financial Coach Agent | [generative_ui_agents/ai-financial-coach-agent](../../generative_ui_agents/ai-financial-coach-agent/) |
| ⬜ | Day 143 | 🗂️ Generative UI Starter Project | [generative_ui_agents/generative-ui-starter-project](../../generative_ui_agents/generative-ui-starter-project/) |
| ⬜ | Day 144 | 📊 AI Dashboard Canvas Agent | [generative_ui_agents/ai-dashboard-canvas-agent](../../generative_ui_agents/ai-dashboard-canvas-agent/) |
| ⬜ | Day 145 | ✈️ MCP Apps Generative UI Showcase | [generative_ui_agents/mcp-apps-generative-ui-showcase](../../generative_ui_agents/mcp-apps-generative-ui-showcase/) |
| ⬜ | Day 146 | 🛠️ AI MCP App Builder | [generative_ui_agents/ai-mcp-app-builder](../../generative_ui_agents/ai-mcp-app-builder/) |
| ⬜ | Day 147 | 🎛️ AI Shadcn Component Generator | [generative_ui_agents/ai-shadcn-component-generator](../../generative_ui_agents/ai-shadcn-component-generator/) |

### 볼륨 13. 🛰️ Always-on Agents (Day 148–149, 2일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 148 | 📰 Always-on Hacker News Briefing Agent | [always_on_agents/always_on_hn_briefing_agent](../../always_on_agents/always_on_hn_briefing_agent/) |
| ⬜ | Day 149 | 📡 Release Radar Agent | [always_on_agents/release_radar_agent](../../always_on_agents/release_radar_agent/) |

### 볼륨 14. 🎯 LLM Optimization (Day 150–151, 2일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 150 | 🧠 Headroom Context Optimization | [advanced_llm_apps/llm_optimization_tools/headroom_context_optimization](../../advanced_llm_apps/llm_optimization_tools/headroom_context_optimization/) |
| ⬜ | Day 151 | 🎯 Toonify Token Optimization | [advanced_llm_apps/llm_optimization_tools/toonify_token_optimization](../../advanced_llm_apps/llm_optimization_tools/toonify_token_optimization/) |

### 볼륨 15. 🔧 LLM Fine-tuning (Day 152–153, 2일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 152 | 🦙 Llama 3.2 Fine-tuning | [advanced_llm_apps/llm_finetuning_tutorials/llama3.2_finetuning](../../advanced_llm_apps/llm_finetuning_tutorials/llama3.2_finetuning/) |
| ⬜ | Day 153 | 🦥 Gemma 3 Fine-tuning | [advanced_llm_apps/llm_finetuning_tutorials/gemma3_finetuning](../../advanced_llm_apps/llm_finetuning_tutorials/gemma3_finetuning/) |

### 볼륨 16. 🧩 Agent Skills (Day 154–159, 6일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 154 | 🧠 Advisor Orchestrator Worker | [agent_skills/advisor-orchestrator-worker](../../agent_skills/advisor-orchestrator-worker/) |
| ⬜ | Day 155 | 🏺 Commit Archaeologist | [agent_skills/commit-archaeologist](../../agent_skills/commit-archaeologist/) |
| ⬜ | Day 156 | 🩺 Dependency Doctor | [agent_skills/dependency-doctor](../../agent_skills/dependency-doctor/) |
| ⬜ | Day 157 | 🔭 Scope Creep Detector | [agent_skills/scope-creep-detector](../../agent_skills/scope-creep-detector/) |
| ⬜ | Day 158 | ⚰️ Project Graveyard | [agent_skills/project-graveyard](../../agent_skills/project-graveyard/) |
| ⬜ | Day 159 | ♾️ Self-Improving Agent Skills | [agent_skills/self-improving-agent-skills](../../agent_skills/self-improving-agent-skills/) |

### 볼륨 17. 🔎 AI 브라우저 도구 (Day 160–160, 1일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 160 | 🪡 Needle - A New Way to Find | [advanced_llm_apps/needle](../../advanced_llm_apps/needle/) |

### 볼륨 18. 🧪 기타 LLM 앱 (Day 161–164, 4일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 161 | 🔄 GPT-OSS Advanced Critique & Improvement Loop | [advanced_llm_apps/gpt_oss_critique_improvement_loop](../../advanced_llm_apps/gpt_oss_critique_improvement_loop/) |
| ⬜ | Day 162 | 📄 Resume & Job Matcher | [advanced_llm_apps/resume_job_matcher](../../advanced_llm_apps/resume_job_matcher/) |
| ⬜ | Day 163 | ThinkPath Chatbot  🧠 | [advanced_llm_apps/thinkpath_chatbot_app](../../advanced_llm_apps/thinkpath_chatbot_app/) |
| ⬜ | Day 164 | Cursor Ai Experiments | [advanced_llm_apps/cursor_ai_experiments](../../advanced_llm_apps/cursor_ai_experiments/) |

