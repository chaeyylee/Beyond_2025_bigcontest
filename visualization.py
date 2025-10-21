import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import uuid
from column_descriptions import COLUMN_DESCRIPTIONS

def display_store_insights(store_row):
    graphs = []

    # 1. 연령·성별 고객 비중
    age_gender_cols = [
        "m12_mal_1020_rat", "m12_mal_30_rat", "m12_mal_40_rat",
        "m12_mal_50_rat", "m12_mal_60_rat",
        "m12_fme_1020_rat", "m12_fme_30_rat", "m12_fme_40_rat",
        "m12_fme_50_rat", "m12_fme_60_rat"
    ]
    data = {col: store_row.get(col) for col in age_gender_cols if store_row.get(col) not in [None, -999999.9]}
    if data:
        translated_data = {
            COLUMN_DESCRIPTIONS.get(col.lower(), (col, ""))[0].replace(" 고객 비중", ""): val
            for col, val in data.items()
        }

        df = pd.DataFrame(list(translated_data.items()), columns=["고객군", "비중"])
        df["성별"] = df["고객군"].apply(lambda x: "남성" if "남성" in x else "여성")

        color_map = {"남성": "lightskyblue", "여성": "lightpink"}

        fig = px.bar(
            df, x="고객군", y="비중", color="성별",
            color_discrete_map=color_map
        )
        graphs.append(("🧍 연령·성별 고객 비중", fig))

    # 2. 재방문 vs 신규 고객
    reu = store_row.get("mct_ue_cln_reu_rat")
    new = store_row.get("mct_ue_cln_new_rat")
    if reu is not None and new is not None:
        if all(v != -999999.9 for v in [reu, new]):
            fig = px.pie(
                names=["재방문 고객", "신규 고객"],
                values=[reu, new]
            )
            graphs.append(("🔁 재방문 vs 신규 고객", fig))

    # 3. 고객 유형 (거주/직장/유동)
    cust_type_cols = {
        "거주 고객": "rc_m1_shc_rsd_ue_cln_rat",
        "직장 고객": "rc_m1_shc_wp_ue_cln_rat",
        "유동 고객": "rc_m1_shc_flp_ue_cln_rat"
    }
    values = {k: store_row.get(v) for k, v in cust_type_cols.items() if store_row.get(v) not in [None, -999999.9]}
    if values:
        fig = px.pie(
            names=list(values.keys()),
            values=list(values.values()),
            color=list(values.keys()),
            color_discrete_map={
                "거주 고객": "#FFD700",
                "직장 고객": "#5DADE2",
                "유동 고객": "#F1948A"
            }
        )
        graphs.append(("👥️ 주요 고객군 구성", fig))

    # 4. 배달 비중 (게이지)
    dlv = store_row.get("dlv_saa_rat")
    if dlv is not None and dlv != -999999.9:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=dlv,
            title={'text': "배달 매출 비율 (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {
                    'color': '#1C2E59',
                    'thickness': 1.0
                }
            }
        ))
        graphs.append(("🚚 배달 매출 비율", fig))

    # 5. 업종 평균 대비 성과 (비율)
    avg_cols = {
        "매출금액 비율": "m1_sme_ry_saa_rat",
        "매출건수 비율": "m1_sme_ry_cnt_rat"
    }
    avg_data = {k: store_row.get(v) for k, v in avg_cols.items() if store_row.get(v) not in [None, -999999.9]}
    if avg_data:
        df = pd.DataFrame(list(avg_data.items()), columns=["지표", "값"])
        fig = px.bar(
            df, x="지표", y="값",
            color="지표",
            color_discrete_map={
                "매출금액 비율": "#2ECC71",
                "매출건수 비율": "#2E8B57"
            }
        )
        fig.add_shape(
            type="line",
            y0=100, y1=100, x0=-0.5, x1=1.5,
            line=dict(dash='dash', color='red')
        )
        fig.update_layout(yaxis_title="(업종 평균 = 100%)", showlegend=False, bargap=0.5)
        graphs.append(("📈 업종 평균 대비 성과", fig))

    # 6. 순위 지표
    rank_cols = {
        "업종 내 순위 비율": "m12_sme_ry_saa_pce_rt",
        "상권 내 순위 비율": "m12_sme_bzn_saa_pce_rt"
    }
    rank_data = {k: store_row.get(v) for k, v in rank_cols.items() if store_row.get(v) not in [None, -999999.9]}
    if rank_data:
        df = pd.DataFrame(list(rank_data.items()), columns=["구분", "순위"])
        fig = px.bar(
            df, x="순위", y="구분", orientation="h",
            color="구분",
            color_discrete_map={
                "업종 내 순위 비율": "#5B2C6F",
                "상권 내 순위 비율": "#BB8FCE"
            }
        )
        fig.update_layout(showlegend=False, bargap=0.5)
        graphs.append(("📉 업종/상권 내 순위 (낮을수록 상위)", fig))

    # ✅ 병렬 출력 (각 그래프는 한 번만 렌더링)
    cols_per_row = 3 if len(graphs) >= 3 else 2
    for i in range(0, len(graphs), cols_per_row):
        row_graphs = graphs[i:i + cols_per_row]
        columns = st.columns(len(row_graphs))
        for col, (title, fig) in zip(columns, row_graphs):
            with col:
                st.markdown(f"**{title}**")
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{title}_{uuid.uuid4()}")
