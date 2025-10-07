import streamlit as st
from mcp_server import analyze_store
from data_loader import load_store_data
import plotly.graph_objects as go

st.set_page_config(page_title="AI 마케팅 전략 코치", layout="wide")

# 세션 상태 초기화
if "store_name" not in st.session_state:
    st.session_state.store_name = None
if "clicked_strategy" not in st.session_state:
    st.session_state.clicked_strategy = [False, False, False]

# 상단 제목 및 설명
st.title("🤖 내 가게를 살리는 AI 비밀상담사")
st.markdown("""
매장 데이터를 기반으로 경쟁 매장과의 상대적인 위치를 분석하고,  
배달/재방문/신규 유입 전략을 자동 추천해드립니다.
""")

# 사용자 메시지 출력
def user_message(content):
    with st.chat_message("user"):
        st.markdown(f"<div style='padding:0.5rem 1rem; background-color:#e8f0fe; border-radius:1rem;'>{content}</div>", unsafe_allow_html=True)

# 챗봇 메시지 출력
def bot_message(content):
    with st.chat_message("assistant"):
        st.markdown(content, unsafe_allow_html=True)

# 입력창
user_input = st.chat_input("매장명을 입력해주세요")

# 초기 예시 출력
if not st.session_state.store_name:
    _, df = load_store_data("")
    bot_message("안녕하세요! 💡 매장명을 입력하시면 마케팅 전략을 분석해드릴게요.")
    st.markdown("🔍 예시 매장명 (상위 5개)")
    st.write(df["mct_nm"].dropna().unique().tolist()[:5])

# 입력 분석
if user_input:
    user_message(user_input)
    st.session_state.store_name = user_input

    try:
        with st.spinner("🔍 전략 분석 중..."):
            result = analyze_store(user_input)

        store = result["store"]
        strategies = result["strategies"]
        gemini_strategies = result["gemini_strategies"]

        # 📊 퍼센타일 그래프
        with st.chat_message("assistant"):
            st.markdown("📊 <strong>경쟁 매장 대비 퍼센타일</strong>", unsafe_allow_html=True)
            percentile = result["percentiles"]
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

        # 🧠 전략 카드 출력
        with st.chat_message("assistant"):
            st.markdown("🧠 <strong>AI 추천 마케팅 전략 카드</strong>", unsafe_allow_html=True)
            for i, strat in enumerate(strategies):
                st.markdown(
                    f"""
                    <div style="background-color:#fffbe6; padding:1rem; border-radius:1rem; margin-bottom:0.5rem;">
                        <strong>전략 {i+1}:</strong> {strat}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # 💬 Gemini 전략 문구 + 동적 버튼 처리
        for i, g_caption in enumerate(gemini_strategies):
            with st.chat_message("assistant"):
                st.markdown(f"📌 <strong>전략 {i+1} 상세 설명</strong>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div style="background-color:#f0f4ff; padding: 1rem; border-left: 5px solid #1c64f2; border-radius: 0.5rem; margin-bottom: 0.5rem;">
                        {g_caption}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # 버튼은 항상 보이게 하고, 클릭하면 상태 저장만
                if st.button(f"🎯 이 전략을 실행에 옮긴다면?", key=f"btn_{i}"):
                    st.session_state.clicked_strategy[i] = True

            # 💬 버튼이 눌렸으면 별도 말풍선으로 실행 코멘트 출력
            if st.session_state.clicked_strategy[i]:
                bot_message(f"✅ 전략 {i+1} 실행 팁:\n\n👉 {strategies[i]}")

    except Exception as e:
        bot_message(f"❌ 오류 발생: {str(e)}")
