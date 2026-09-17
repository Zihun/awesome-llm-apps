import os

import streamlit as st
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.openai import OpenAIChat
from agno.models.xai import xAI
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools

st.set_page_config(
    page_title="Multi-Model Finance Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Multi-Model Finance Agent")
st.caption("xAI, OpenAI, Gemini, Anthropic 모델을 선택해 같은 금융 에이전트를 실행합니다.")

with st.sidebar:
    st.header("🔐 API Keys")
    st.write("각 키는 로컬 세션에만 저장됩니다.")
    st.caption("Google Gemini는 Google AI Studio에서 발급한 키를 사용해야 하며, 최신 모델 ID를 사용해야 합니다.")

    xai_api_key = st.text_input("xAI API Key", type="password", key="xai_finance_key")
    openai_api_key = st.text_input("OpenAI API Key", type="password", key="openai_finance_key")
    google_api_key = st.text_input("Google API Key", type="password", key="google_finance_key")
    anthropic_api_key = st.text_input("Anthropic API Key", type="password", key="anthropic_finance_key")

    st.markdown("---")
    model_choice = st.selectbox(
        "Select LLM",
        ["xAI Grok", "OpenAI GPT", "Gemini", "Anthropic Claude"],
        index=1,
    )


def build_model(model_name: str):
    if model_name == "xAI Grok":
        if not xai_api_key:
            st.warning("xAI API 키를 입력하세요.")
            return None
        os.environ["XAI_API_KEY"] = xai_api_key
        return xAI(id="grok-4-1-fast", api_key=xai_api_key)

    if model_name == "OpenAI GPT":
        if not openai_api_key:
            st.warning("OpenAI API 키를 입력하세요.")
            return None
        os.environ["OPENAI_API_KEY"] = openai_api_key
        return OpenAIChat(id="gpt-4o", api_key=openai_api_key)

    if model_name == "Gemini":
        if not google_api_key:
            st.warning("Google API 키를 입력하세요.")
            return None
        os.environ["GOOGLE_API_KEY"] = google_api_key
        os.environ["GEMINI_API_KEY"] = google_api_key
        return Gemini(id="gemini-3.6-flash", api_key=google_api_key)

    if model_name == "Anthropic Claude":
        if not anthropic_api_key:
            st.warning("Anthropic API 키를 입력하세요.")
            return None
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key
        return Claude(id="claude-3-5-sonnet-20241022", api_key=anthropic_api_key)

    return None


@st.cache_resource

def initialize_agent(model_name: str):
    model = build_model(model_name)
    if model is None:
        return None

    return Agent(
        name=f"{model_name} Finance Agent",
        model=model,
        tools=[DuckDuckGoTools(), YFinanceTools()],
        instructions=[
            "Always use tables to display financial and numerical data.",
            "For text, use bullet points and short paragraphs.",
            "When giving stock information, explain assumptions clearly and cite the source when possible.",
        ],
        markdown=True,
    )


user_question = st.text_area(
    "질문을 입력하세요",
    value="AAPL 최근 주가, 주요 뉴스, 그리고 투자 관점 요약해줘.",
    height=120,
)

if st.button("실행"):
    agent = initialize_agent(model_choice)
    if agent is None:
        st.warning("선택한 모델에 맞는 API 키를 입력해주세요.")
    elif user_question.strip():
        with st.spinner(f"{model_choice} 모델로 분석 중..."):
            try:
                result = agent.run(user_question)
                st.subheader("결과")
                st.markdown(result.content)
            except Exception as e:
                st.error(f"실행 중 오류가 발생했습니다: {e}")
else:
    st.info("사이드바에서 API 키와 모델을 선택한 뒤 실행 버튼을 누르세요.")
