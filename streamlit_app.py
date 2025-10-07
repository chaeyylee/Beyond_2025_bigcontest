import streamlit as st
from mcp_server import analyze_store
from data_loader import load_store_data
import plotly.graph_objects as go
from markdown import markdown as md_to_html  # pip install markdown

# 페이지 설정
st.set_page_config(page_title="AI 마케팅 전략 챗봇", layout="wide")

# 세션 상태 초기화
if "store_name" not in st.session_state:
    st.session_state.store_name = None
if "clicked_strategy" not in st.session_state:
    st.session_state.clicked_strategy = {}

# 헤더 영역
st.title("🤖 내 가게를 살리는 AI 비밀상담사")
st.markdown("""
매장 데이터를 기반으로 경쟁 매장과의 상대적인 위치를 분석하고,  
배달/재방문/신규 유입 전략을 자동 추천해드립니다.
""")

# 💬 사용자 말풍선 출력 함수
def user_message(content):
    with st.chat_message("user"):
        st.markdown(
            f"<div style='padding:0.5rem 1rem; background-color:#e8f0fe; border-radius:1rem;'>{content}</div>",
            unsafe_allow_html=True
        )

# 💬 챗봇 말풍선 출력 함수
def bot_message(content):
    with st.chat_message("assistant"):
        st.markdown(content, unsafe_allow_html=True)

# ✅ 전략 제목과 본문을 분리해주는 함수
def split_strategy_title_body(text: str, index: int) -> tuple[str, str]:
    """
    전략 텍스트에서 제목과 본문을 분리하여 반환합니다.
    - 제목: 첫 줄을 <h3>로 감싸고 '1. ' 등 전략 번호를 붙임
    - 본문: 마크다운 그대로 출력 가능하도록 나머지 줄
    """
    lines = text.strip().splitlines()
    title_line = lines[0] if lines else f"전략 {index+1}"
    full_title = f"{index+1}. {title_line}"
    title_html = f"<h3 style='margin-top:0; margin-bottom:0.5rem;'>{full_title}</h3>"
    body_md = "\n".join(lines[1:]) if len(lines) > 1 else ""
    return title_html, body_md

# ✅ 전략 말풍선 렌더링 함수 (제목+본문을 모두 박스 안에)
def render_chat_bubble_full(title_html: str, body_md: str, color: str = "blue"):
    """
    제목과 본문을 모두 말풍선 안에서 보여주는 버전.
    본문은 마크다운 → HTML 변환 후 함께 넣음.
    """
    border_color = {
        "blue": "#1c64f2",
        "green": "#22c55e",
        "red": "#ef4444",
        "gray": "#6b7280",
        "yellow": "#eab308"
    }.get(color, color)

    # 본문 마크다운 → HTML
    body_html = md_to_html(body_md)

    st.markdown(f"""
    <div style="background-color:#f0f4ff;
                border-left: 5px solid {border_color};
                border-radius: 0.5rem;
                padding: 1rem;
                margin-bottom: 1rem;">
        {title_html}
        {body_html}
    </div>
    """, unsafe_allow_html=True)

# 유저 입력
user_input = st.chat_input("매장명을 입력하세요")

# 매장명이 없는 초기 화면
if not st.session_state.store_name:
    _, df = load_store_data("")
    bot_message("안녕하세요! 💡 매장명을 입력하시면 마케팅 전략을 분석해드릴게요.")
    st.markdown("🔍 예시 매장명 (상위 5개)")
    st.write(df["mct_nm"].dropna().unique().tolist()[:5])

# 매장명 입력 후 분석
if user_input:
    user_message(user_input)
    st.session_state.store_name = user_input

    try:
        with st.spinner("전략 분석 중입니다..."):
            result = analyze_store(user_input)

        store = result["store"]
        strategies = result["strategies"]
        gemini_strategies = result["gemini_strategies"]
        percentile = result["percentiles"]

        # 📊 경쟁 매장 대비 퍼센타일 차트
        with st.chat_message("assistant"):
            st.markdown("📊 <strong>경쟁 매장 대비 주요 지표 백분위</strong>", unsafe_allow_html=True)
            labels = list(percentile.keys())
            values = [percentile[k] if percentile[k] is not None else 0 for k in labels]

            fig = go.Figure(go.Bar(
                x=labels,
                y=values,
                marker_color=['#636EFA', '#EF553B', '#00CC96'],
                text=[f"{v:.1f}%" for v in values],
                textposition='auto'
            ))
            fig.update_layout(
                yaxis=dict(title='백분위 (%)', range=[0, 100]),
                xaxis=dict(title='지표'),
                height=400,
                margin=dict(l=40, r=40, t=30, b=40)
            )
            st.plotly_chart(fig, use_container_width=True)

        # 🧠 전략 카드 + 말풍선 출력
        with st.chat_message("assistant"):
            st.markdown("🧠 <strong>AI 추천 마케팅 전략 카드</strong>", unsafe_allow_html=True)

            for i in range(len(strategies)):
                # 전략 요약 카드
                st.markdown(
                    f"""
                    <div style="background-color:#fffbe6; padding:1rem; border-radius:1rem; margin-bottom:0.5rem;">
                        <strong>전략 {i+1}:</strong> {strategies[i]}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # 전략 제목과 본문 분리
                title_html, body_md = split_strategy_title_body(gemini_strategies[i], i)

                # 제목+본문 모두 박스 안에 렌더링
                render_chat_bubble_full(title_html, body_md, color="blue")

                # 실행 버튼
                if st.button(f"🎯 이 전략을 실행한다면?", key=f"btn_{i}"):
                    st.session_state.clicked_strategy[i] = True

        # 버튼 클릭 후 실행 팁 출력
        for i in range(len(strategies)):
            if st.session_state.clicked_strategy.get(i):
                with st.chat_message("assistant"):
                    st.markdown(f"✅ 전략 {i+1} 실행 팁:")
                    st.markdown(f"👉 {strategies[i]}")

    except Exception as e:
        bot_message(f"❌ 오류 발생: {str(e)}")
