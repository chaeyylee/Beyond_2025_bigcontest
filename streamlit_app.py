import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
from data_loader import load_store_data
from column_descriptions import COLUMN_DESCRIPTIONS
from visualization import display_store_insights
import pandas as pd

# .env에서 GOOGLE_API_KEY 로드
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Gemini 모델 초기화
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.5,
)

def clear_chat_history():
    st.session_state.chat_history = []
    st.rerun()

# 첫화면 멘트
INITIAL_INTRO = """
🗣️ **가게명**이나 지금 겪고 계신 **문제 상황**을 말씀해 주세요. 구체적인 전략을 드리기 위해 사건 제보가 필요합니다.  

예시:  
- "OO 매장인데, 단골이 줄었어요."
- "△△ 카페인데, 젊은 손님들이 잘 안 와요."
- "□□ 식당인데, 홍보가 잘 안 되는 것 같아요."

"""

# 페이지 설정
st.set_page_config(page_title="🕵️ 탐정 D의 마케팅 수사노트", layout="wide")

# 초기화
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

# 사이드바 구성
if st.session_state.sidebar_open:
    with st.sidebar:
        st.image("assets/shc_ci_basic_00.png", use_container_width=True)

        st.markdown("<p style='text-align: center; font-size: 18px; font-weight: bold;'>🕵️ 탐정 D 마케팅 수사본부</p>", unsafe_allow_html=True)
        st.markdown("""
        <p style='text-align: center; font-size: 16px;'>
          데이터와 추리가 만나는 곳<br><strong>Data × Detective</strong>
        </p>
        """, unsafe_allow_html=True)

        st.write("")

        button_html = """
        <style>
        div.stButton > button {
            width: 180px;
            margin: auto;
            display: block;
        }
        </style>
        """
        st.markdown(button_html, unsafe_allow_html=True)

        if st.button("🧹 Clear Case Log"):
            st.session_state.chat_history = [{
                "role": "assistant",
                "content": INITIAL_INTRO
            }]
            st.rerun()

st.title("🕵️ 탐정 D : 데이터 기반 마케팅 수사 AI")
st.markdown("""
이곳은 단골 실종 사건과 매출 하락 미스터리가 끊이지 않는 현장.  
저는 데이터를 단서 삼아 문제를 추적하는 마케팅 전문 탐정, **데이텍티브 Datetective**입니다. 사람들은 저를 **탐정 D**라고 부르죠.

📂 단골 손님의 실종, 📉 매출의 급락, 🧩 의문의 광고 성과 하락…  
무엇이든 **사건**이 있다면, 단서를 분석해 **전략이라는 이름의 해결책**을 찾아드립니다.

🕵️ **탐정 D, 수사 개시 준비 완료.**
""")

# 전체 매장 목록
_, df = load_store_data("")
all_store_names = df["mct_nm"].unique().tolist()

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.chat_history.append({"role": "assistant", "content": INITIAL_INTRO})

# ✅ 채팅 메시지 출력
def render_chat():
    case_index = 1  # 사건 번호를 추적할 인덱스

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):

            # 📎 사건 파일 번호는 assistant이면서 store_row가 있는 경우만 표시
            if msg["role"] == "assistant" and msg.get("store_row"):
                st.markdown(f"📎 **사건 파일 #{case_index:03}**")
                case_index += 1

            # 📊 시각화 단서가 포함된 경우
            if "[[VISUALIZATION_PLACEHOLDER]]" in msg["content"]:
                before_vis, after_vis = msg["content"].split("[[VISUALIZATION_PLACEHOLDER]]", 1)
                st.markdown(before_vis)

                if msg.get("store_row"):
                    df_row = pd.Series(msg["store_row"])
                    display_store_insights(df_row)

                st.markdown(after_vis)

            else:
                # 일반 텍스트 메시지 출력
                st.markdown(msg["content"])


# ✅ 반드시 초기화 후에 호출
render_chat()

# 프롬프트 생성 함수
def build_prompt(messages, store_row):
    base = """
    당신은 우리 주변 음식 가맹점에게 진짜 필요한 ‘맞춤 마케팅 전략’을 제공하는 **마케팅 전문 탐정**, **데이텍티브 Datetective**입니다. 
    사람들은 당신을 **탐정 D**라고 부릅니다.

    사용자의 문제 상황을 **사건**으로 보고, 고객 데이터를 **단서**로 활용해 원인을 분석한 뒤,
    그에 맞는 전략을 **수사 보고서**처럼 정리해 제시하세요.

    - 사용자가 겪고 있는 문제 = 사건  
    - 고객 데이터 = 단서  
    - 분석 결과 = 수사 보고서  
    - 전략 제시 = 범인(원인) 검거 + 해결 방안 제시  
    - 전략 효과 = 사건 이후 변화 예측 보고  

    ---

    ## 📝 출력 형식 예시 (아래 구성과 유사하게 작성해 주세요)

    ### 🚨 사건명
    - 사용자의 문제 상황을 핵심 키워드로 요약한 **사건 제목**을 한 줄로 작성해 주세요.
    - 가게명을 포함하여 분석을 위한 관찰 제목처럼 작성해 주세요.  
        - 예: ㅇㅇ매장 단골 손님 감소 추정 건, ㅁㅁ매장 신규 유입률 저하 의심 등
        
    ---

    ### 📋 사건 개요
    - 사용자가 입력한 문제 상황의 **배경과 맥락**을 명확하게 설명해 주세요.
    - 지나치게 감정적이기보단, **탐정이 현장을 기록하듯** 정리해 주세요.
    - 문제의 징후, 맥락, 관찰된 패턴 등을 중심으로 서술합니다.

    ---

    ### 🧩 단서 분석

    | 주요 지표 | 값 또는 상태 | 해석 |
    |-----------|--------------|------|
    | 예: 재방문 고객 비중 | 25% | 업종 평균보다 낮음. 고객 충성도 부족 |
    | 예: 배달 매출 비율 | 10% | 배달 채널 활용도 낮음 |

    - 가능한 경우 **store_row 데이터를 기반**으로, 없는 경우 **유사 업종 평균을 가정하여 작성**하세요.
    - 사용자의 발화와 가맹점 데이터를 바탕으로 탐지된 주요 지표/수치/패턴을 정리해 주세요.

    ---
    
    ### 📊 단서 시각화
    [[VISUALIZATION_PLACEHOLDER]]
    
    ---

    ### 🧭 원인 추론
    - 단서 분석 결과를 바탕으로 **실제 원인을 명확히 추론**해 주세요.
    - 마치 탐정처럼 “이 사건의 핵심 원인은 ○○입니다” 형식으로 작성해 주세요.

    ---

    ### 💡 해결 전략 제시

    #### 1. 전략 제목 (이모지 포함)  
    - 타깃 고객:  
    - 주요 채널:  
    - 실행 방안:  

    #### 2. ... (같은 형식으로 총 3개 전략 제시)

    ---

    ### 🪄 기대 효과

    - 제목에는 반드시 **이모지 하나**를 포함해야 합니다.
    - 앞서 나온 해결 전략을 적용할 경우 해당 매장이 얻을 수 있는 기대 효과를 적어주세요.   
    - **수치 기반 효과**(예: +12%, 100명 이상 유입 등)를 포함해 주세요.  
    - 전략 효과를 설명할 때는 신뢰할 수 있는 구체적인 근거(예: 정부 기관 통계, 공공 데이터, 연구 결과 등)를 반드시 포함해주세요.  
       (예: “2025 통계청 소비 트렌드 조사에 따르면 20대 여성의 외식 빈도는 전년 대비 12% 증가했습니다.”)  
    - 각 항목은 **번호, 이모지, 제목, 근거, 설명** 구조로 작성해 주세요.

    출력 예시:

    #### 1. 💡 신규 고객 유입 증가  
    - 근거: 2025 통계청 소비 트렌드 조사에 따르면 20대 여성의 외식 빈도는 전년 대비 12% 증가했습니다.  
    - 설명: SNS 이벤트 및 리뷰 인증 캠페인을 통해 신규 고객 유입률이 약 +15% 증가할 것으로 예상됩니다.  

    ---

    """

    # 📌 컬럼 설명 포함
    base += "\n\n📌 참고: 데이터 컬럼 설명\n"
    for col, (name, desc) in COLUMN_DESCRIPTIONS.items():
        base += f"- {col} ({name}): {desc}\n"

    # 📂 가맹점 데이터 유무에 따라
    if store_row is not None:
        base += "\n\n📂 가맹점 데이터 요약:\n"
        for col, val in store_row.items():
            base += f"- {col}: {val}\n"
    else:
        base += "\n\n📂 가맹점 데이터는 제공되지 않았습니다. 사용자 메시지만 참고해 주세요.\n"

    # 대화 메시지 반영
    for msg in messages:
        base += f"\n사용자: {msg['content']}"

    base += "\n탐정으로서 분석을 시작하세요."
    return base


# 세션 상태 초기화 (처음 1회만)
if "case_counter" not in st.session_state:
    st.session_state.case_counter = 1

user_input = st.chat_input("💬 사건을 제보해 주세요 (예: 다다** 단골이 줄었어요)")

if user_input:
    current_case_number = st.session_state.case_counter
    matched_store_name = None

    # 매장명 포함 여부 확인
    for name in all_store_names:
        if name in user_input:
            matched_store_name = name
            break

    # 가맹점 데이터 로드
    if matched_store_name:
        store_row, _ = load_store_data(matched_store_name)

        if store_row is None:
            st.warning(f"❗ '{matched_store_name}' 매장을 데이터에서 찾을 수 없습니다.")
            st.stop()

        # 매장 인식 시에만 사건 번호 증가
        st.session_state.case_counter += 1
    else:
        store_row = None

    st.chat_message("user").markdown(user_input)

    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("🔍 단서를 분석 중입니다..."):
        try:
            prompt = build_prompt(st.session_state.chat_history, store_row)
            response = llm.invoke([HumanMessage(content=prompt)])
            reply = response.content
        except Exception as e:
            reply = f"❌ 오류가 발생했습니다: {str(e)}"

    # 사건 파일 헤더는 render_chat()에서 표시하므로 여기서는 붙이지 않음
    if matched_store_name:
        pass

    st.session_state.chat_history.append({
        "role": "assistant",
        "content": reply,
        "store_row": store_row.to_dict() if store_row is not None else None
    })

    st.rerun()
