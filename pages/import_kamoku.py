import streamlit as st
import sqlite3
import pandas as pd
import chardet
import io
import os
from datetime import datetime

# StreamlitのUI設定
st.set_page_config(layout="wide")

# サイドバー
with st.sidebar:
    st.page_link("menu.py", label="データベース接続")
    st.markdown('<div class="section blue">処理項目</div>', unsafe_allow_html=True)
    st.page_link("pages/henkan.py", label="仕訳変換")
    st.markdown('<div class="section green">設定変更</div>', unsafe_allow_html=True)
    st.page_link("pages/setting_kamoku.py", label="科目設定")
    st.page_link("pages/setting_hojo.py", label="補助設定")
    st.page_link("pages/setting_syouhizei.py", label="消費税設定")
    st.markdown('<div class="section orange">初期設定</div>', unsafe_allow_html=True)
    st.page_link("pages/import_kamoku.py", label="勘定科目マスタインポート")
    st.page_link("pages/import_hojo.py", label="補助科目マスタインポート")
    st.page_link("pages/import_syouhizei.py", label="消費税マスタインポート")

# CSS
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
[data-baseweb="input"] input {
    background-color: white !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# DB接続関数
def get_db_connection():
    if 'conn' not in st.session_state:
        if st.session_state.db_path:
            conn = sqlite3.connect(st.session_state.db_path, check_same_thread=False)
            st.session_state.conn = conn
        else:
            conn = None
    else:
        conn = st.session_state.conn
    return conn

# 共通のDB接続
conn = get_db_connection()

# タイトル
st.title("勘定科目マスターのインポート")

# --- Excelテンプレート作成＆ダウンロード ---
def create_excel_template():
    data = {
        "管理番号": ["", "", ""],
        "財務R4科目コード": ["", "", ""],
        "財務R4科目名": ["", "", ""],
        "弥生会計科目名": ["", "", ""],
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output

excel_file = create_excel_template()

st.download_button(
    label="📥 勘定科目マスターのインポート用テンプレートをダウンロード",
    data=excel_file,
    file_name="kamoku_import_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- 接続DBパスの表示 ---
if 'db_path' in st.session_state and st.session_state.db_path:
    st.info(f"現在接続中のデータベース: {st.session_state.db_path}")
else:
    st.error("データベースが接続されていません。menu.pyで接続してください。")
    st.stop()

# --- DBの内容を表示 ---
try:
    with st.expander("📂 現在のデータベース内容を表示（kamoku_master）", expanded=False):
        df_existing = pd.read_sql_query("SELECT * FROM kamoku_master", conn)
        st.dataframe(df_existing)
        st.caption(f"現在の件数: {len(df_existing)} 件")
except Exception as e:
    st.warning("既存データの表示に失敗しました。")
    st.exception(e)

# テーブル作成（初回用）
def create_table():
    cursor = conn.cursor()
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS kamoku_master (
            管理番号 TEXT PRIMARY KEY,     
            財務R4科目コード TEXT NOT NULL,
            財務R4科目名 TEXT NOT NULL,
            弥生会計科目名 TEXT
        )
    ''')
    conn.commit()

create_table()

# ファイルアップロード
uploaded_file = st.file_uploader("📤 勘定科目マスターエクセルをアップロード", type=["csv", "xlsx"])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    df = None

    try:
        if file_extension == "csv":
            raw_data = uploaded_file.read()
            detected = chardet.detect(raw_data)
            encoding = detected["encoding"] or "utf-8"
            df = pd.read_csv(io.BytesIO(raw_data), encoding=encoding, errors="replace")

        elif file_extension == "xlsx":
            df = pd.read_excel(uploaded_file, engine="openpyxl")

        if df is not None:
            df.columns = df.columns.str.strip()
            df = df.rename(columns={
                "管理番号": "管理番号",
                "財務R4科目コード": "財務R4科目コード",
                "財務R4科目名": "財務R4科目名",
                "弥生会計科目名": "弥生会計科目名"
            })
            df["弥生会計科目名"] = df["弥生会計科目名"].fillna("？")

            st.write("📄 アップロードされたデータ")
            st.dataframe(df)

        if st.button("💾 データベースに保存"):
            try:
                cursor = conn.cursor()
                for _, row in df.iterrows():
                    cursor.execute(''' 
                        INSERT OR REPLACE INTO kamoku_master (管理番号, 財務R4科目コード, 財務R4科目名, 弥生会計科目名) 
                        VALUES (?, ?, ?, ?)''', 
                        (row["管理番号"], row["財務R4科目コード"], row["財務R4科目名"], row["弥生会計科目名"]))
                conn.commit()
                st.success("データベースに保存しました！")
                st.session_state["refresh_kamoku"] = True
            except Exception as db_error:
                st.error(f"データベース保存時にエラーが発生しました: {db_error}")


        else:
            st.error("ファイルの読み込みに失敗しました。エンコーディングを確認してください。")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.exception(e)

# 保存後に再表示
if st.session_state.get("refresh_kamoku"):
    try:
        df_db = pd.read_sql_query("SELECT * FROM kamoku_master", conn)
        st.write("📋 データベースの内容")
        st.dataframe(df_db)

        st.write("\n--- 🛠 デバッグ情報 ---")
        st.write("DBパス:", st.session_state.get("db_path"))
        count = conn.execute("SELECT COUNT(*) FROM kamoku_master").fetchone()[0]
        st.write("kamoku_master 行数:", count)

    except Exception as debug_error:
        st.error(f"DB再表示時にエラーが発生しました: {debug_error}")
        st.exception(debug_error)

    del st.session_state["refresh_kamoku"]

# --- DBファイルのダウンロード（接続中のDB名＋日付） ---
if "db_path" in st.session_state and os.path.isfile(st.session_state.db_path):
    db_path = st.session_state.db_path
    db_filename = os.path.basename(db_path)
    db_name, db_ext = os.path.splitext(db_filename)
    today = datetime.today().strftime("%Y%m%d")
    download_name = f"{db_name}_{today}{db_ext}"

    with open(db_path, "rb") as f:
        db_bytes = f.read()

    st.download_button(
        label="💾 現在のデータベースを保存（デスクトップへ）",
        data=db_bytes,
        file_name=download_name,
        mime="application/octet-stream"
    )

    st.write('データベースの内容を変更した場合は、必ずデータベースを保存してください。')