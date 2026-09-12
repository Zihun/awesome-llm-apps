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
uv run python <엔트리 파일>
```

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

진도: 10 / 133일 완료

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
| ⬜ | Day 011 | ❤️‍🩹 AI Breakup Recovery Agent | [starter_ai_agents/ai_breakup_recovery_agent](../../starter_ai_agents/ai_breakup_recovery_agent/) |
| ⬜ | Day 012 | 🛫 AI Travel Agent (Local & Cloud) | [starter_ai_agents/ai_travel_agent](../../starter_ai_agents/ai_travel_agent/) |
| ⬜ | Day 013 | 🔍 OpenAI Research Agent | [starter_ai_agents/openai_research_agent](../../starter_ai_agents/openai_research_agent/) |

### 볼륨 2. 🧑‍🏫 Crash Courses (Day 14–34, 21일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 014 | Google ADK Crash Course · 1_starter_agent | [ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/1_starter_agent/) |
| ⬜ | Day 015 | Google ADK Crash Course · 2_model_agnostic_agent | [ai_agent_framework_crash_course/google_adk_crash_course/2_model_agnostic_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/2_model_agnostic_agent/) |
| ⬜ | Day 016 | Google ADK Crash Course · 3_structured_output_agent | [ai_agent_framework_crash_course/google_adk_crash_course/3_structured_output_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/3_structured_output_agent/) |
| ⬜ | Day 017 | Google ADK Crash Course · 4_tool_using_agent | [ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/4_tool_using_agent/) |
| ⬜ | Day 018 | Google ADK Crash Course · 5_memory_agent | [ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/5_memory_agent/) |
| ⬜ | Day 019 | Google ADK Crash Course · 6_callbacks | [ai_agent_framework_crash_course/google_adk_crash_course/6_callbacks](../../ai_agent_framework_crash_course/google_adk_crash_course/6_callbacks/) |
| ⬜ | Day 020 | Google ADK Crash Course · 7_plugins | [ai_agent_framework_crash_course/google_adk_crash_course/7_plugins](../../ai_agent_framework_crash_course/google_adk_crash_course/7_plugins/) |
| ⬜ | Day 021 | Google ADK Crash Course · 8_simple_multi_agent | [ai_agent_framework_crash_course/google_adk_crash_course/8_simple_multi_agent](../../ai_agent_framework_crash_course/google_adk_crash_course/8_simple_multi_agent/) |
| ⬜ | Day 022 | Google ADK Crash Course · 9_multi_agent_patterns | [ai_agent_framework_crash_course/google_adk_crash_course/9_multi_agent_patterns](../../ai_agent_framework_crash_course/google_adk_crash_course/9_multi_agent_patterns/) |
| ⬜ | Day 023 | Google ADK Crash Course · adk_yaml_examples | [ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples](../../ai_agent_framework_crash_course/google_adk_crash_course/adk_yaml_examples/) |
| ⬜ | Day 024 | OpenAI Agents SDK Crash Course · 1_starter_agent | [ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent](../../ai_agent_framework_crash_course/openai_sdk_crash_course/1_starter_agent/) |
| ⬜ | Day 025 | OpenAI Agents SDK Crash Course · 2_structured_output_agent | [ai_agent_framework_crash_course/openai_sdk_crash_course/2_structured_output_agent](../../ai_agent_framework_crash_course/openai_sdk_crash_course/2_structured_output_agent/) |
| ⬜ | Day 026 | OpenAI Agents SDK Crash Course · 3_tool_using_agent | [ai_agent_framework_crash_course/openai_sdk_crash_course/3_tool_using_agent](../../ai_agent_framework_crash_course/openai_sdk_crash_course/3_tool_using_agent/) |
| ⬜ | Day 027 | OpenAI Agents SDK Crash Course · 4_running_agents | [ai_agent_framework_crash_course/openai_sdk_crash_course/4_running_agents](../../ai_agent_framework_crash_course/openai_sdk_crash_course/4_running_agents/) |
| ⬜ | Day 028 | OpenAI Agents SDK Crash Course · 5_context_management | [ai_agent_framework_crash_course/openai_sdk_crash_course/5_context_management](../../ai_agent_framework_crash_course/openai_sdk_crash_course/5_context_management/) |
| ⬜ | Day 029 | OpenAI Agents SDK Crash Course · 6_guardrails_validation | [ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation](../../ai_agent_framework_crash_course/openai_sdk_crash_course/6_guardrails_validation/) |
| ⬜ | Day 030 | OpenAI Agents SDK Crash Course · 7_sessions | [ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions](../../ai_agent_framework_crash_course/openai_sdk_crash_course/7_sessions/) |
| ⬜ | Day 031 | OpenAI Agents SDK Crash Course · 8_handoffs_delegation | [ai_agent_framework_crash_course/openai_sdk_crash_course/8_handoffs_delegation](../../ai_agent_framework_crash_course/openai_sdk_crash_course/8_handoffs_delegation/) |
| ⬜ | Day 032 | OpenAI Agents SDK Crash Course · 9_multi_agent_orchestration | [ai_agent_framework_crash_course/openai_sdk_crash_course/9_multi_agent_orchestration](../../ai_agent_framework_crash_course/openai_sdk_crash_course/9_multi_agent_orchestration/) |
| ⬜ | Day 033 | OpenAI Agents SDK Crash Course · 10_tracing_observability | [ai_agent_framework_crash_course/openai_sdk_crash_course/10_tracing_observability](../../ai_agent_framework_crash_course/openai_sdk_crash_course/10_tracing_observability/) |
| ⬜ | Day 034 | OpenAI Agents SDK Crash Course · 11_voice | [ai_agent_framework_crash_course/openai_sdk_crash_course/11_voice](../../ai_agent_framework_crash_course/openai_sdk_crash_course/11_voice/) |

### 볼륨 3. 💬 Chat with X (Day 35–40, 6일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 035 | 📝 Chat with Substack | [advanced_llm_apps/chat_with_X_tutorials/chat_with_substack](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_substack/) |
| ⬜ | Day 036 | 📚 Chat with Research Papers (ArXiv) (GPT & Llama3) | [advanced_llm_apps/chat_with_X_tutorials/chat_with_research_papers](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_research_papers/) |
| ⬜ | Day 037 | 💬 Chat with GitHub (GPT & Llama3) | [advanced_llm_apps/chat_with_X_tutorials/chat_with_github](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_github/) |
| ⬜ | Day 038 | 📄 Chat with PDF (GPT & Llama3) | [advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_pdf/) |
| ⬜ | Day 039 | 📽️ Chat with YouTube Videos | [advanced_llm_apps/chat_with_X_tutorials/chat_with_youtube_videos](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_youtube_videos/) |
| ⬜ | Day 040 | 📨 Chat with Gmail | [advanced_llm_apps/chat_with_X_tutorials/chat_with_gmail](../../advanced_llm_apps/chat_with_X_tutorials/chat_with_gmail/) |

### 볼륨 4. 📀 RAG (Day 41–61, 21일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 041 | 🦙 Local RAG Agent | [rag_tutorials/local_rag_agent](../../rag_tutorials/local_rag_agent/) |
| ⬜ | Day 042 | 🔄 Llama 3.1 Local RAG | [rag_tutorials/llama3.1_local_rag](../../rag_tutorials/llama3.1_local_rag/) |
| ⬜ | Day 043 | 🔍 Autonomous RAG | [rag_tutorials/autonomous_rag](../../rag_tutorials/autonomous_rag/) |
| ⬜ | Day 044 | 🔥 Agentic RAG with Embedding Gemma | [rag_tutorials/agentic_rag_embedding_gemma](../../rag_tutorials/agentic_rag_embedding_gemma/) |
| ⬜ | Day 045 | 🧩 RAG-as-a-Service | [rag_tutorials/rag-as-a-service](../../rag_tutorials/rag-as-a-service/) |
| ⬜ | Day 046 | ⛓️ Basic RAG Chain | [rag_tutorials/rag_chain](../../rag_tutorials/rag_chain/) |
| ⬜ | Day 047 | 👀 Hybrid Search RAG (Cloud) | [rag_tutorials/hybrid_search_rag](../../rag_tutorials/hybrid_search_rag/) |
| ⬜ | Day 048 | 🧐 Agentic RAG with Reasoning | [rag_tutorials/agentic_rag_with_reasoning](../../rag_tutorials/agentic_rag_with_reasoning/) |
| ⬜ | Day 049 | 🖥️ Local Hybrid Search RAG | [rag_tutorials/local_hybrid_search_rag](../../rag_tutorials/local_hybrid_search_rag/) |
| ⬜ | Day 050 | 🩺 RAG Failure Diagnostics Clinic | [rag_tutorials/rag_failure_diagnostics_clinic](../../rag_tutorials/rag_failure_diagnostics_clinic/) |
| ⬜ | Day 051 | ✨ RAG Agent with Cohere | [rag_tutorials/rag_agent_cohere](../../rag_tutorials/rag_agent_cohere/) |
| ⬜ | Day 052 | 🔄 Contextual AI RAG Agent | [rag_tutorials/contextualai_rag_agent](../../rag_tutorials/contextualai_rag_agent/) |
| ⬜ | Day 053 | 📰 AI Blog Search (RAG) | [rag_tutorials/ai_blog_search](../../rag_tutorials/ai_blog_search/) |
| ⬜ | Day 054 | 📠 RAG with Database Routing | [rag_tutorials/rag_database_routing](../../rag_tutorials/rag_database_routing/) |
| ⬜ | Day 055 | 🔄 Corrective RAG (CRAG) | [rag_tutorials/corrective_rag](../../rag_tutorials/corrective_rag/) |
| ⬜ | Day 056 | 🤔 Gemini Agentic RAG | [rag_tutorials/gemini_agentic_rag](../../rag_tutorials/gemini_agentic_rag/) |
| ⬜ | Day 057 | 🕸️ Knowledge Graph RAG with Citations | [rag_tutorials/knowledge_graph_rag_citations](../../rag_tutorials/knowledge_graph_rag_citations/) |
| ⬜ | Day 058 | 🐋 Deepseek Local RAG Agent | [rag_tutorials/deepseek_local_rag_agent](../../rag_tutorials/deepseek_local_rag_agent/) |
| ⬜ | Day 059 | 🖼️ Vision RAG | [rag_tutorials/vision_rag](../../rag_tutorials/vision_rag/) |
| ⬜ | Day 060 | 📎 Typed Agentic RAG with Pydantic AI | [rag_tutorials/agentic_typed_rag_pydanticai](../../rag_tutorials/agentic_typed_rag_pydanticai/) |
| ⬜ | Day 061 | 🧬 Multimodal Agentic RAG | [rag_tutorials/multimodal_agentic_rag](../../rag_tutorials/multimodal_agentic_rag/) |

### 볼륨 5. 💾 LLM Apps with Memory (Day 62–67, 6일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 062 | 💬 Llama3 Stateful Chat | [advanced_llm_apps/llm_apps_with_memory_tutorials/llama3_stateful_chat](../../advanced_llm_apps/llm_apps_with_memory_tutorials/llama3_stateful_chat/) |
| ⬜ | Day 063 | 💾 AI ArXiv Agent with Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/ai_arxiv_agent_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/ai_arxiv_agent_memory/) |
| ⬜ | Day 064 | 📝 LLM App with Personalized Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory/) |
| ⬜ | Day 065 | 🧠 Multi-LLM Application with Shared Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/multi_llm_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/multi_llm_memory/) |
| ⬜ | Day 066 | 🛩️ AI Travel Agent with Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/ai_travel_agent_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/ai_travel_agent_memory/) |
| ⬜ | Day 067 | 🗄️ Local ChatGPT Clone with Memory | [advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory](../../advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/) |

### 볼륨 6. 🚀 Advanced AI Agents (Day 68–88, 21일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 068 | 📈 AI Investment Agent | [advanced_ai_agents/single_agent_apps/ai_investment_agent](../../advanced_ai_agents/single_agent_apps/ai_investment_agent/) |
| ⬜ | Day 069 | 🎬 AI Movie Production Agent | [advanced_ai_agents/single_agent_apps/ai_movie_production_agent](../../advanced_ai_agents/single_agent_apps/ai_movie_production_agent/) |
| ⬜ | Day 070 | 🧬 AI Self-Evolving Agent | [advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent](../../advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/) |
| ⬜ | Day 071 | 🗞️ AI Journalist Agent | [advanced_ai_agents/single_agent_apps/ai_journalist_agent](../../advanced_ai_agents/single_agent_apps/ai_journalist_agent/) |
| ⬜ | Day 072 | 🔬 AI Research Planner & Executor (Google Interactions API) | [advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api](../../advanced_ai_agents/single_agent_apps/research_agent_gemini_interaction_api/) |
| ⬜ | Day 073 | 🔍 AI Deep Research Agent | [advanced_ai_agents/single_agent_apps/ai_deep_research_agent](../../advanced_ai_agents/single_agent_apps/ai_deep_research_agent/) |
| ⬜ | Day 074 | 📑 AI Meeting Agent | [advanced_ai_agents/single_agent_apps/ai_meeting_agent](../../advanced_ai_agents/single_agent_apps/ai_meeting_agent/) |
| ⬜ | Day 075 | 🧠 AI Mental Wellbeing Agent | [advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent](../../advanced_ai_agents/multi_agent_apps/ai_mental_wellbeing_agent/) |
| ⬜ | Day 076 | 🏋️‍♂️ AI Health & Fitness Agent | [advanced_ai_agents/single_agent_apps/ai_health_fitness_agent](../../advanced_ai_agents/single_agent_apps/ai_health_fitness_agent/) |
| ⬜ | Day 077 | 🏗️ AI System Architect Agent | [advanced_ai_agents/single_agent_apps/ai_system_architect_r1](../../advanced_ai_agents/single_agent_apps/ai_system_architect_r1/) |
| ⬜ | Day 078 | 🤝 AI Consultant Agent | [advanced_ai_agents/single_agent_apps/ai_consultant_agent](../../advanced_ai_agents/single_agent_apps/ai_consultant_agent/) |
| ⬜ | Day 079 | 🚀 AI Product Launch Intelligence Agent | [advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent](../../advanced_ai_agents/multi_agent_apps/product_launch_intelligence_agent/) |
| ⬜ | Day 080 | 🛡️ Trust-Gated Multi-Agent Research Team | [advanced_ai_agents/multi_agent_apps/trust_gated_agent_team](../../advanced_ai_agents/multi_agent_apps/trust_gated_agent_team/) |
| ⬜ | Day 081 | 👨🏻‍💼 AI Sales Intelligence Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_sales_intelligence_agent_team/) |
| ⬜ | Day 082 | 📊 AI VC Due Diligence Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team/) |
| ⬜ | Day 083 | 🔍 AI Fraud Investigation Agent | [advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent](../../advanced_ai_agents/single_agent_apps/ai_fraud_investigation_agent/) |
| ⬜ | Day 084 | 💰 AI Financial Coach Agent | [advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent](../../advanced_ai_agents/multi_agent_apps/ai_financial_coach_agent/) |
| ⬜ | Day 085 | 🏚️ 🍌 AI Home Renovation Agent with Nano Banana Pro | [advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent](../../advanced_ai_agents/multi_agent_apps/ai_home_renovation_agent/) |
| ⬜ | Day 086 | 🧠 DevPulse AI - Multi-Agent Signal Intelligence | [advanced_ai_agents/multi_agent_apps/devpulse_ai](../../advanced_ai_agents/multi_agent_apps/devpulse_ai/) |
| ⬜ | Day 087 | 📡 Earnings Call Analyst Agent | [advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent](../../advanced_ai_agents/single_agent_apps/earnings_call_analyst_agent/) |
| ⬜ | Day 088 | 🎧 AI Social Media News and Podcast Agent | [advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents](../../advanced_ai_agents/multi_agent_apps/ai_news_and_podcast_agents/) |

### 볼륨 7. 🤝 Multi-agent Teams (Day 89–101, 13일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 089 | 💲 AI Finance Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_finance_agent_team/) |
| ⬜ | Day 090 | 👨‍🏫 AI Teaching Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/) |
| ⬜ | Day 091 | ✨ Multimodal Design Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_design_agent_team/) |
| ⬜ | Day 092 | 💻 Multimodal Coding Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_coding_agent_team/) |
| ⬜ | Day 093 | 🎨 AI Game Design Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_game_design_agent_team/) |
| ⬜ | Day 094 | 🧲 AI Competitor Intelligence Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_competitor_intelligence_agent_team/) |
| ⬜ | Day 095 | 👨‍💼 AI Services Agency (CrewAI) | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_services_agency/) |
| ⬜ | Day 096 | 🧭 AG2 Adaptive Research Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ag2_adaptive_research_team/) |
| ⬜ | Day 097 | 💼 AI Recruitment Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_recruitment_agent_team/) |
| ⬜ | Day 098 | 👨‍⚖️ AI Legal Agent Team (Cloud & Local) | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team/) |
| ⬜ | Day 099 | 🎨 🍌 Multimodal UI/UX Feedback Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/multimodal_uiux_feedback_agent_team/) |
| ⬜ | Day 100 | 🏠 AI Real Estate Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_real_estate_agent_team/) |
| ⬜ | Day 101 | 🌏 AI Travel Planner Agent Team | [advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team](../../advanced_ai_agents/multi_agent_apps/agent_teams/ai_travel_planner_agent_team/) |

### 볼륨 8. ♾️ MCP AI Agents (Day 102–107, 6일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 102 | 📑 Notion MCP Agent | [mcp_ai_agents/notion_mcp_agent](../../mcp_ai_agents/notion_mcp_agent/) |
| ⬜ | Day 103 | 🐙 GitHub MCP Agent | [mcp_ai_agents/github_mcp_agent](../../mcp_ai_agents/github_mcp_agent/) |
| ⬜ | Day 104 | ♾️ Browser MCP Agent | [mcp_ai_agents/browser_mcp_agent](../../mcp_ai_agents/browser_mcp_agent/) |
| ⬜ | Day 105 | 🔌 OpenAI Remote MCP Tool Bridge | [mcp_ai_agents/openai_remote_mcp_bridge](../../mcp_ai_agents/openai_remote_mcp_bridge/) |
| ⬜ | Day 106 | 🌍 AI Travel Planner MCP Agent | [mcp_ai_agents/ai_travel_planner_mcp_agent_team](../../mcp_ai_agents/ai_travel_planner_mcp_agent_team/) |
| ⬜ | Day 107 | 🔀 Multi-MCP Agent Router | [mcp_ai_agents/multi_mcp_agent_router](../../mcp_ai_agents/multi_mcp_agent_router/) |

### 볼륨 9. 🎮 Autonomous Game-Playing (Day 108–110, 3일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 108 | ♜ AI Chess Agent | [advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent](../../advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent/) |
| ⬜ | Day 109 | 🎮 AI 3D Pygame Agent | [advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1](../../advanced_ai_agents/autonomous_game_playing_agent_apps/ai_3dpygame_r1/) |
| ⬜ | Day 110 | 🎲 AI Tic-Tac-Toe Agent | [advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent](../../advanced_ai_agents/autonomous_game_playing_agent_apps/ai_tic_tac_toe_agent/) |

### 볼륨 10. 🗣️ Voice AI Agents (Day 111–114, 4일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 111 | 📞 Customer Support Voice Agent | [voice_ai_agents/customer_support_voice_agent](../../voice_ai_agents/customer_support_voice_agent/) |
| ⬜ | Day 112 | 🔊 Voice RAG Agent (OpenAI SDK) | [voice_ai_agents/voice_rag_openaisdk](../../voice_ai_agents/voice_rag_openaisdk/) |
| ⬜ | Day 113 | 🗣️ AI Audio Tour Agent | [voice_ai_agents/ai_audio_tour_agent](../../voice_ai_agents/ai_audio_tour_agent/) |
| ⬜ | Day 114 | 🛡️ Insurance Claim Live Agent Team | [voice_ai_agents/insurance_claim_live_agent_team](../../voice_ai_agents/insurance_claim_live_agent_team/) |

### 볼륨 11. 🖼️ Generative UI (Day 115–121, 7일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 115 | 🔍 AI Deep Research Agent | [generative_ui_agents/ai-deep-research-agent](../../generative_ui_agents/ai-deep-research-agent/) |
| ⬜ | Day 116 | 🪙 AI Financial Coach Agent | [generative_ui_agents/ai-financial-coach-agent](../../generative_ui_agents/ai-financial-coach-agent/) |
| ⬜ | Day 117 | 🗂️ Generative UI Starter Project | [generative_ui_agents/generative-ui-starter-project](../../generative_ui_agents/generative-ui-starter-project/) |
| ⬜ | Day 118 | 📊 AI Dashboard Canvas Agent | [generative_ui_agents/ai-dashboard-canvas-agent](../../generative_ui_agents/ai-dashboard-canvas-agent/) |
| ⬜ | Day 119 | ✈️ MCP Apps Generative UI Showcase | [generative_ui_agents/mcp-apps-generative-ui-showcase](../../generative_ui_agents/mcp-apps-generative-ui-showcase/) |
| ⬜ | Day 120 | 🛠️ AI MCP App Builder | [generative_ui_agents/ai-mcp-app-builder](../../generative_ui_agents/ai-mcp-app-builder/) |
| ⬜ | Day 121 | 🎛️ AI Shadcn Component Generator | [generative_ui_agents/ai-shadcn-component-generator](../../generative_ui_agents/ai-shadcn-component-generator/) |

### 볼륨 12. 🛰️ Always-on Agents (Day 122–123, 2일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 122 | 📰 Always-on Hacker News Briefing Agent | [always_on_agents/always_on_hn_briefing_agent](../../always_on_agents/always_on_hn_briefing_agent/) |
| ⬜ | Day 123 | 📡 Release Radar Agent | [always_on_agents/release_radar_agent](../../always_on_agents/release_radar_agent/) |

### 볼륨 13. 🎯 LLM Optimization (Day 124–125, 2일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 124 | 🧠 Headroom Context Optimization | [advanced_llm_apps/llm_optimization_tools/headroom_context_optimization](../../advanced_llm_apps/llm_optimization_tools/headroom_context_optimization/) |
| ⬜ | Day 125 | 🎯 Toonify Token Optimization | [advanced_llm_apps/llm_optimization_tools/toonify_token_optimization](../../advanced_llm_apps/llm_optimization_tools/toonify_token_optimization/) |

### 볼륨 14. 🔧 LLM Fine-tuning (Day 126–127, 2일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 126 | 🦙 Llama 3.2 Fine-tuning | [advanced_llm_apps/llm_finetuning_tutorials/llama3.2_finetuning](../../advanced_llm_apps/llm_finetuning_tutorials/llama3.2_finetuning/) |
| ⬜ | Day 127 | 🦥 Gemma 3 Fine-tuning | [advanced_llm_apps/llm_finetuning_tutorials/gemma3_finetuning](../../advanced_llm_apps/llm_finetuning_tutorials/gemma3_finetuning/) |

### 볼륨 15. 🧩 Agent Skills (Day 128–133, 6일)

| 완료 | 일차 | 앱 | 원본 앱 |
|---|---|---|---|
| ⬜ | Day 128 | 🧠 Advisor Orchestrator Worker | [agent_skills/advisor-orchestrator-worker](../../agent_skills/advisor-orchestrator-worker/) |
| ⬜ | Day 129 | 🏺 Commit Archaeologist | [agent_skills/commit-archaeologist](../../agent_skills/commit-archaeologist/) |
| ⬜ | Day 130 | 🩺 Dependency Doctor | [agent_skills/dependency-doctor](../../agent_skills/dependency-doctor/) |
| ⬜ | Day 131 | 🔭 Scope Creep Detector | [agent_skills/scope-creep-detector](../../agent_skills/scope-creep-detector/) |
| ⬜ | Day 132 | ⚰️ Project Graveyard | [agent_skills/project-graveyard](../../agent_skills/project-graveyard/) |
| ⬜ | Day 133 | ♾️ Self-Improving Agent Skills | [agent_skills/self-improving-agent-skills](../../agent_skills/self-improving-agent-skills/) |

