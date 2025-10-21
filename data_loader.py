import pandas as pd

def load_store_data(store_name: str = ""):
    df = pd.read_csv("data/real_final_set_f.csv", encoding="cp949")
    df.columns = df.columns.str.lower()
    st_col = "mct_nm"

    if not store_name:
        return None, df

    if st_col not in df.columns:
        raise ValueError(f"CSV에 '{st_col}' 컬럼이 없습니다.")

    store_row = df[df[st_col] == store_name]
    return store_row.iloc[0] if not store_row.empty else None, df
