import streamlit as st
import pandas as pd
import sqlite3

# StreamlitのUI設定
st.set_page_config(layout="wide")  # レイアウトをデフォルトに設定

with st.sidebar:
    st.page_link("menu.py", label="データベース接続")

    # 処理項目（青系）
    st.markdown('<div class="section blue">処理項目</div>', unsafe_allow_html=True)
    st.page_link("pages/henkan.py", label="仕訳変換")

    # 設定変更（緑系）
    st.markdown('<div class="section green">設定変更</div>', unsafe_allow_html=True)
    st.page_link("pages/setting_kamoku.py", label="科目設定")
    st.page_link("pages/setting_hojo.py", label="補助設定")
    st.page_link("pages/setting_syouhizei.py", label="消費税設定")

    # 初期設定（オレンジ系）
    st.markdown('<div class="section orange">初期設定</div>', unsafe_allow_html=True)
    st.page_link("pages/import_kamoku.py", label="勘定科目マスタインポート")
    st.page_link("pages/import_hojo.py", label="補助科目マスタインポート")
    st.page_link("pages/import_syouhizei.py", label="消費税マスタインポート")

st.markdown("""
    <style>
    .section {
        font-size: 16px;
        font-weight: bold;
        padding: 8px 12px;
        margin: 15px 0 8px 0;
        border-radius: 8px;
        border: 2px solid;
    }
    .blue {
        color: #1f77b4;
        border-color: #1f77b4;
        background-color: #e6f0fa;
    }
    .green {
        color: #2ca02c;
        border-color: #2ca02c;
        background-color: #e9f7ea;
    }
    .orange {
        color: #ff7f0e;
        border-color: #ff7f0e;
        background-color: #fff4e6;
    }
    </style>
""", unsafe_allow_html=True)

# データベース接続用の関数を定義
def get_db_connection(db_name):
    return sqlite3.connect(db_name, check_same_thread=False)

st.title("部門設定")

# 部門データベース接続 (例: 部門のテーブルを取得)
conn = get_db_connection("department.db")  # 部門設定用のDBを仮定
query = "SELECT 部門コード, 部門名 FROM department_master"
df_dept = pd.read_sql_query(query, conn)

# データが存在する場合に表示
if df_dept.empty:
    st.warning("部門データが読み込まれていません")
else:
    st.dataframe(df_dept)

# 編集処理
cursor = conn.cursor()
for index, row in df_dept.iterrows():
    with st.expander(f"{row['部門コード']} - {row['部門名']}"):
        dept_name = st.text_input(
            f"部門名 (コード: {row['部門コード']})",
            value=row["部門名"] if row["部門名"] else "",
            key=f"dept_{index}"
        )
        if dept_name.strip() and dept_name.strip() != (row["部門名"] or "").strip():
            cursor.execute('''UPDATE department_master SET 部門名 = ? WHERE 部門コード = ?''',
                        (dept_name, row["部門コード"]))
            conn.commit()
            st.success(f"部門データを更新しました！（コード: {row['部門コード']}）")

        # 削除処理
        if st.button(f"削除（コード: {row['部門コード']}）", key=f"delete_dept_{index}"):
            cursor.execute('''DELETE FROM department_master WHERE 部門コード = ?''', (row["部門コード"],))
            conn.commit()
            st.success(f"部門データを削除しました！（コード: {row['部門コード']}）")
            st.experimental_rerun()  # ページを再読み込みしてデータを更新

# 新規追加機能
st.subheader("新規部門の追加")
new_dept_code = st.text_input("新しい部門コード")
new_dept_name = st.text_input("新しい部門名")

if st.button("新規追加"):
    if new_dept_code and new_dept_name:
        cursor.execute('''INSERT INTO department_master (部門コード, 部門名) VALUES (?, ?)''',
                    (new_dept_code, new_dept_name))
        conn.commit()
        st.success(f"新しい部門が追加されました！（コード: {new_dept_code}）")
        st.experimental_rerun()  # ページを再読み込みしてデータを更新
    else:
        st.error("部門コードと部門名を入力してください")

# データベース接続を閉じる
conn.close()
