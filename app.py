import streamlit as st
import pandas as pd
import numpy as np

# =========================================================
# 1. データ読み込み
# =========================================================
@st.cache_data
def load_data():
    # GitHubリポジトリ直下に score_all.xlsx を置いている前提
    df = pd.read_excel("score_all.xlsx")

    # 列名が想定通りかチェック（安全対策）
    expected_cols = [
        "企業名",
        "①年収・評価",
        "②成長・将来性",
        "③キャリアアップ",
        "④ワークライフバランス",
        "⑤福利厚生・環境",
        "⑥やりがい",
    ]
    df = df[expected_cols]

    return df


# =========================================================
# 2. ペナルティ計算（片側ペナルティ方式）
# =========================================================
def calculate_penalty_ranking(df, user_inputs):
    df_result = df.copy()
    df_result["不満度スコア"] = 0.0

    for label, user_point in user_inputs.items():
        target_val = user_point / 5.0
        actual_val = df_result[label]
        gap = np.maximum(0, target_val - actual_val)
        df_result["不満度スコア"] += gap ** 2

    df_sorted = (
        df_result
        .sort_values("不満度スコア", ascending=True)
        .reset_index(drop=True)
    )

    return df_sorted


# =========================================================
# 3. 画面設定
# =========================================================
st.set_page_config(
    page_title="価値観重視型 就活マッチング",
    layout="wide"
)

st.title("🎓 価値観重視型 就活レコメンド")
st.markdown("""
あなたの**譲れない条件**にポイントを配分してください。  
条件を満たしていない企業ほど「不満度スコア」が高くなります。
""")


# =========================================================
# 4. サイドバー（条件入力）
# =========================================================
st.sidebar.header("💎 条件設定")

MAX_POINTS = 15
st.sidebar.info(f"持ち点は **合計 {MAX_POINTS} ポイント**")

labels = [
    "①年収・評価",
    "②成長・将来性",
    "③キャリアアップ",
    "④ワークライフバランス",
    "⑤福利厚生・環境",
    "⑥やりがい",
]

user_inputs = {}
current_total = 0

for label in labels:
    val = st.sidebar.slider(label, 0, 5, 2)
    user_inputs[label] = val
    current_total += val

remaining = MAX_POINTS - current_total

if remaining >= 0:
    st.sidebar.success(f"あと **{remaining}** ポイント")
    is_valid = True
else:
    st.sidebar.error(f"⚠️ **{abs(remaining)} ポイント超過**")
    is_valid = False


# =========================================================
# 5. 診断結果表示
# =========================================================
if st.button("診断スタート", type="primary", disabled=not is_valid):

    df_companies = load_data()
    ranking = calculate_penalty_ranking(df_companies, user_inputs)

    # ---- 1位表示 ----
    best = ranking.iloc[0]

    st.success("分析完了：あなたに最もミスマッチが少ない企業")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.header(f"🏆 第1位：{best['企業名']}")
        st.caption(f"不満度スコア：{best['不満度スコア']:.4f}")

        st.write("【おすすめ理由】")
        reasons = []
        for label in labels:
            if user_inputs[label] >= 3 and best[label] >= user_inputs[label] / 5.0:
                reasons.append(f"・{label}が希望水準以上")

        if reasons:
            for r in reasons:
                st.write(r)
        else:
            st.write("・全体的にバランスが取れている")

    with col2:
        chart_df = pd.DataFrame({
            "評価軸": labels,
            "スコア": best[labels].values
        }).set_index("評価軸")
        st.bar_chart(chart_df)

    st.divider()

    # ---- ランキング表 ----
    st.subheader("📊 企業ランキング")

    display_cols = ["企業名", "不満度スコア"] + labels

    # ★ここが重要：index完全削除
    ranking_display = ranking[display_cols].reset_index(drop=True)

    # 順位列を追加（1始まり）
    ranking_display.insert(0, "順位", ranking_display.index + 1)

    st.dataframe(ranking_display, use_container_width=True)

else:
    st.info("👈 左のメニューで条件を設定してください")
