def get_strategies(store, percentile):
    strategies = []

    # 🧭 1. 고객군 / 단골 & 신규 유입 관련 전략 분기
    
    # 1(1) 재방문율
    if metrics.get("재방문율") is not None and metrics["재방문율"] >= 60:
        strategies.append("💎 재방문율이 높습니다. 단골 리워드, 후기 이벤트, 생일 쿠폰 등 유지 전략이 적합합니다.")
    elif metrics.get("재방문율") is not None and metrics["재방문율"] < 60:
        strategies.append("📉 재방문율이 낮습니다. 충성 고객 유지를 위한 혜택 강화가 필요합니다.")

    # 1(2) 단골손님 (재방문 고객 비중)
    if metrics.get("재방문 고객 비중") is not None and metrics["재방문 고객 비중"] >= 60:
        strategies.append("🎁 단골 고객 비중이 높습니다. 단골 이벤트나 VIP 혜택을 강화해보세요.")
    elif metrics.get("재방문 고객 비중") is not None and metrics["재방문 고객 비중"] < 60:
        strategies.append("🧊 단골 고객 비중이 낮습니다. 충성도를 높이는 멤버십 제안이 좋습니다.")

    # 1(3) 신규 고객 비율
    if percentile.get("신규고객") is not None and percentile["신규고객"] <= 25:
        strategies.append("📣 신규 고객 유입이 업종 하위 25% 수준입니다. 첫방문 할인, SNS 광고를 강화하세요.")
    elif percentile.get("신규고객") is not None and percentile["신규고객"] >= 75: # 확인해보고 빼기 
        strategies.append("🚀 신규 고객 비율이 높습니다. 재방문 유도를 위한 후기 이벤트나 쿠폰이 효과적입니다.")


    # 1(4) 주 고객층 (연령/성별)

    # 각 성별·연령대 비중 중 최대값 찾기
    age_gender_cols = {
        "남성 20대 이하": data.get("M12_MAL_1020_RAT", 0),
        "남성 30대": data.get("M12_MAL_30_RAT", 0),
        "남성 40대": data.get("M12_MAL_40_RAT", 0),
        "남성 50대": data.get("M12_MAL_50_RAT", 0),
        "남성 60대 이상": data.get("M12_MAL_60_RAT", 0),
        "여성 20대 이하": data.get("M12_FME_1020_RAT", 0),
        "여성 30대": data.get("M12_FME_30_RAT", 0),
        "여성 40대": data.get("M12_FME_40_RAT", 0),
        "여성 50대": data.get("M12_FME_50_RAT", 0),
        "여성 60대 이상": data.get("M12_FME_60_RAT", 0)
}

    # 가장 높은 비중의 그룹 찾기
    main_group = max(age_gender_cols, key=age_gender_cols.get)
    strategies = []

    # 연령/성별별 맞춤 전략 분기
    if main_group == "남성 20대 이하":
        strategies.append("🧢 남성 10~20대 고객이 많습니다. 배달 앱 홍보, 가성비 세트, 간편 메뉴 중심으로 구성하세요.")
    elif main_group == "남성 30대":
        strategies.append("👔 남성 30대 고객이 주 고객층입니다. 직장인 점심세트, 커피 쿠폰, 빠른 식사류를 추천합니다.")
    elif main_group == "남성 40대":
        strategies.append("🥢 남성 40대 고객이 많습니다. 점심 도시락, 단골 포인트제, 퇴근 시간대 할인 이벤트를 운영하세요.")
    elif main_group == "남성 50대":
        strategies.append("🍛 남성 50대 고객층입니다. 든든한 한식 메뉴, 지역 신문 홍보, 단골 리워드 전략이 효과적입니다.")
    elif main_group == "남성 60대 이상":
        strategies.append("👨‍🦳 남성 60대 이상 고객이 많습니다. 전통 메뉴, 지역 커뮤니티 제휴, 점심 쿠폰을 활용하세요.")

    elif main_group == "여성 20대 이하":
        strategies.append("🎀 여성 10~20대 고객층입니다. SNS 포토존, 신메뉴 체험단, 감성 인테리어로 유입을 늘리세요.")
    elif main_group == "여성 30대":
        strategies.append("☕ 여성 30대 고객층입니다. 감성 마케팅, 후기 이벤트, 디저트 강화가 좋습니다.")
    elif main_group == "여성 40대":
        strategies.append("🌸 여성 40대 고객층입니다. 가족 단위 세트, 지역 커뮤니티 이벤트를 추천합니다.")
    elif main_group == "여성 50대":
        strategies.append("🫖 여성 50대 고객층입니다. 건강식 메뉴, 단체 예약 혜택, 평일 낮시간 할인 이벤트가 적합합니다.")
    elif main_group == "여성 60대 이상":
        strategies.append("👩‍🦳 여성 60대 이상 고객층입니다. 건강식·차류 중심 구성과 편안한 좌석 환경으로 방문을 유도하세요.")

    else:
        strategies.append("👥 주요 고객층이 명확하지 않습니다. 연령·성별 데이터를 보완해 세밀한 타겟 전략을 세워보세요.")

    # 결과 출력
    print(f"📊 주요 고객층: {main_group}")
    for s in strategies:
        print("-", s)

    # 1(5) 유입 약한 고객군 <- 신규 고객과 겹치는 듯
    
    # --------------------------------------------------------------------------------------------------------------------------------

    # 🏙️ 2. 상권 / 입지 / 점유율 관련 전략 분기

    # 2(1) 거주 / 직장 / 유동 고객 비율 기반 상권 분기

    res_ratio = data.get("RC_M1_SHC_RSD_UE_CLN_RAT", 0)  # 거주 이용 고객 비율
    work_ratio = data.get("RC_M1_SHC_WP_UE_CLN_RAT", 0)  # 직장 이용 고객 비율
    flow_ratio = data.get("RC_M1_SHC_FLP_UE_CLN_RAT", 0)  # 유동인구 이용 고객 비율

    # 어떤 유형이 가장 높은지 확인
    ratios = {
        "거주": res_ratio,
        "직장": work_ratio,
        "유동": flow_ratio
    }
    dominant_type = max(ratios, key=ratios.get)

    # 전략 리스트 초기화
    strategies = []

    # 절대 기준 조건
    if res_ratio > 50:
        strategies.append("🏘️ 거주 이용 고객 비율이 높습니다. 가족 세트, 주말 이벤트, 지역 맘카페 홍보를 활용하세요.")
    elif work_ratio > 50:
        strategies.append("💼 직장 이용 고객 비율이 높습니다. 점심 회전율 전략과 빠른 메뉴 구성이 중요합니다. 또한 해피아워, 점심 메뉴, 회식 세트 등 직장인 중심 전략이 좋습니다.")
    elif flow_ratio > 50:
        strategies.append("🚶 유동 고객 비율이 높습니다. 테이크아웃 중심 구성과 즉시 구매 유도 이벤트를 추천합니다.")
    else:
        strategies.append("📊 특정 고객 비율이 50%를 넘지 않습니다. 상권 특성이 혼합형으로, 다층 타깃 마케팅이 필요합니다.")

    # 결과 출력
    print("📍 주요 상권 유형:", dominant_type)
    for s in strategies:
        print("-", s)

    # 2(2) 상권 내 우리 매장 점유율 전략
    our_share = data.get("M12_SME_BZN_ME_MCT_RAT", 0)

    if our_share < 5:
        strategies.append("📣 상권 내 우리 매장 점유율이 5% 미만입니다. 로컬 홍보를 강화하고, 협업 이벤트 및 노출 확대가 필요합니다.")
    else:
        strategies.append("🏪 상권 내 점유율이 안정적입니다. 기존 고객 유지와 재방문 유도 전략을 병행하세요.")

    # --------------------------------------------------------------------------------------------------------------------------------

    # 🏙️ 3. 매출 / 판매 구조 / 비율 관련 전략 분기
    

    return strategies