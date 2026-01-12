import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# 1. データ準備（分析済みの実データ）
# =========================================================
def load_data():
    # Excelファイルから企業スコアを読み込む
    df = pd.read_excel("score_all.xlsx")
    return df

# =========================================================
# 2. 計算アルゴリズム（片側ペナルティ方式）
# =========================================================
def calculate_penalty_ranking(df, user_inputs):
    df_result = df.copy()
    df_result['不満度スコア'] = 0.0

    for label, user_point in user_inputs.items():
        target_val = user_point / 5.0
        actual_val = df_result[label]
        gap = np.maximum(0, target_val - actual_val)
        df_result['不満度スコア'] += gap ** 2

    df_sorted = df_result.sort_values(
        '不満度スコア', ascending=True
    ).reset_index(drop=True)

    return df_sorted

# =========================================================
# 3. アプリ画面 (UI)
# =========================================================
st.set_page_config(
    page_title="価値観重視型 就活マッチング",
    layout="wide"
)

st.title("🎓 価値観重視型 就活レコメンド")
st.markdown("""
本アプリは、社員口コミをBERTで分析し定量化した指標を用いて、  
**あなたの価値観とのミスマッチが最小となる企業**を提示する研究用デモである。
""")

# ---------------------------------------------------------
# サイドバー：条件入力
# ---------------------------------------------------------
st.sidebar.header("💎 条件設定")

MAX_POINTS = 15
st.sidebar.info(f"持ち点は **合計 {MAX_POINTS} ポイント** である。")

labels = [
    '①年収・評価',
    '②成長・将来性',
    '③キャリアアップ',
    '④ワークライフバランス',
    '⑤福利厚生・環境',
    '⑥やりがい'
]

user_inputs = {}
current_total = 0

for label in labels:
    val = st.sidebar.slider(label, 0, 5, 2)
    user_inputs[label] = val
    current_total += val

remaining = MAX_POINTS - current_total

if remaining >= 0:
    st.sidebar.success(f"残り **{remaining}** ポイント")
    is_valid = True
else:
    st.sidebar.error(f"⚠️ **{abs(remaining)} ポイント超過**")
    is_valid = False

# ---------------------------------------------------------
# メイン表示
# ---------------------------------------------------------
if st.button("診断スタート", type="primary", disabled=not is_valid):
    df_companies = load_data()
    ranking = calculate_penalty_ranking(df_companies, user_inputs)

    best_company = ranking.iloc[0]

    st.success("分析完了。最もミスマッチが少ない企業は以下である。")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header(f"🏆 第1位：{best_company['企業名']}")
        st.caption(
            f"不満度スコア：{best_company['不満度スコア']:.4f} "
            "(0に近いほど理想)"
        )

        st.write("【評価ポイント】")
        good_points = []
        for label in labels:
            user_req = user_inputs[label] / 5.0
            actual = best_company[label]
            if user_inputs[label] >= 3 and actual >= user_req:
                good_points.append(f"・{label}（希望水準を満たす）")

        if good_points:
            for p in good_points:
                st.write(p)
        else:
            st.write("・全体としてバランス良く条件を満たしている")

    with col2:
        chart_data = pd.DataFrame({
            '評価軸': labels,
            'スコア': best_company[labels].values
        }).set_index('評価軸')
        st.bar_chart(chart_data)

    st.divider()

    st.subheader("📊 企業ランキング")
    display_cols = ['企業名', '不満度スコア'] + labels
    st.dataframe(
        ranking[display_cols]
        .style.background_gradient(
            subset=['不満度スコア'],
            cmap='RdYlGn_r'
        )
    )

elif not is_valid:
    st.warning(
        f"左のメニューで合計が {MAX_POINTS} 以下になるよう調整する必要がある。"
    )
else:
    st.info(
        "左のメニューで条件を設定し、「診断スタート」を押すことで分析が開始される。"
    )

