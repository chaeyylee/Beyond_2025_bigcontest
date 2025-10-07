import re
import pandas as pd
from data_loader import load_store_data
from strategy_rules import get_strategies
from gemini_client import generate_gemini_caption

def analyze_store(store_name):
    store, df = load_store_data(store_name)
    df.columns = df.columns.str.lower()
    store = store.rename(str.lower)

    # 경쟁 매장 필터링
    competitors = df[
        (df["hpsn_mct_zcd_nm"] == store["hpsn_mct_zcd_nm"]) &
        (df["hpsn_mct_bzn_cd_nm"] == store["hpsn_mct_bzn_cd_nm"]) &
        (df["ta_ym"] == store["ta_ym"]) &
        (df["mct_nm"] != store_name)
    ]

    # 주요 지표
    metrics = {
        "배달비율": (store["dlv_saa_rat"], competitors["dlv_saa_rat"].mean()),
        "재방문율": (store["mct_ue_cln_reu_rat"], competitors["mct_ue_cln_reu_rat"].mean()),
        "신규고객비율": (store["mct_ue_cln_new_rat"], competitors["mct_ue_cln_new_rat"].mean()),
    }

    # Percentile
    percentiles = {}
    for label, col in {
        "배달비율": "dlv_saa_rat",
        "재방문율": "mct_ue_cln_reu_rat",
        "신규고객": "mct_ue_cln_new_rat"
    }.items():
        try:
            comp_values = competitors[competitors[col] != -999999.9][col]
            value = store[col]
            if value == -999999.9 or comp_values.empty:
                percentiles[label] = None
            else:
                percentiles[label] = (comp_values < value).mean() * 100
        except Exception:
            percentiles[label] = None

    # 주고객층
    male_cols = {k: v for k, v in store.items() if k.startswith("m12_mal") and v != -999999.9}
    female_cols = {k: v for k, v in store.items() if k.startswith("m12_fme") and v != -999999.9}
    top_male = max(male_cols.items(), key=lambda x: x[1])[0] if male_cols else None
    top_female = max(female_cols.items(), key=lambda x: x[1])[0] if female_cols else None
    if top_female and female_cols[top_female] >= male_cols.get(top_male, 0):
        store["주고객층"] = top_female.split("_")[-2] + "대 여성"
    elif top_male:
        store["주고객층"] = top_male.split("_")[-2] + "대 남성"
    else:
        store["주고객층"] = "기타"

    # 유입 필요 고객층
    target_cols = [col for col in df.columns if (col.startswith("m12_mal_") or col.startswith("m12_fme_")) and df[col].dtype != object]
    lowest_gap = None
    target_group = None
    for col in target_cols:
        store_val = store.get(col, -999999.9)
        mean_val = competitors[col][competitors[col] != -999999.9].mean()
        diff = mean_val - store_val
        if store_val != -999999.9 and (lowest_gap is None or diff > lowest_gap):
            lowest_gap = diff
            target_group = col
    if target_group:
        gender = "여성" if "fme" in target_group else "남성"
        age = target_group.split("_")[-2]
        store["유입필요고객"] = f"{age}대 {gender}"
    else:
        store["유입필요고객"] = "없음"

    # 상권유형
    types = {
        "거주": store.get("rc_m1_shc_rsd_ue_cln_rat", 0),
        "직장": store.get("rc_m1_shc_wp_ue_cln_rat", 0),
        "유동": store.get("rc_m1_shc_flp_ue_cln_rat", 0)
    }
    store["상권유형"] = max(types, key=types.get)

    # 전략 도출
    strategies = get_strategies(store, percentiles)

    # ✅ 단일 프롬프트 구성
    strategy_bullets = "\n".join([f"{i+1}. {s}" for i, s in enumerate(strategies)])
    prompt = f"""
당신은 전문 마케팅 컨설턴트입니다.
다음 매장 분석 결과와 전략들을 참고하여, 각 전략에 대한 마케팅 실행 아이디어를 간결하게 작성해주세요.

🏪 매장명: {store_name}
업종: {store['hpsn_mct_zcd_nm']}
상권: {store['hpsn_mct_bzn_cd_nm']}
기준년월: {store['ta_ym']}

📊 주요 지표
- 배달비율: {store['dlv_saa_rat']:.2f}% (경쟁 평균: {metrics['배달비율'][1]:.2f}%)
- 재방문율: {store['mct_ue_cln_reu_rat']:.2f}% (경쟁 평균: {metrics['재방문율'][1]:.2f}%)
- 신규고객비율: {store['mct_ue_cln_new_rat']:.2f}% (경쟁 평균: {metrics['신규고객비율'][1]:.2f}%)

🎯 주고객층: {store['주고객층']}
🎯 유입 필요 고객층: {store['유입필요고객']}
🏙️ 상권 유형: {store['상권유형']}

📋 전략 목록:
{strategy_bullets}

각 전략에 대해:
- 제목
- 타깃 고객
- 주요 채널
- 구체적 실행 방법

을 간결하고 이모지와 함께 작성해주세요.
"""

    # Gemini API 1회 호출
    full_response = generate_gemini_caption(prompt)

    # ✅ 문단 분리
    parts = re.split(r"\n?전략\s*\d+[:：]", full_response)
    parts = [p.strip() for p in parts if p.strip()]
    gemini_strategies = parts[:3]  # 최대 3개만

    return {
        "store": store.to_dict(),
        "metrics": metrics,
        "percentiles": percentiles,
        "strategies": strategies,
        "gemini_strategies": gemini_strategies
    }
