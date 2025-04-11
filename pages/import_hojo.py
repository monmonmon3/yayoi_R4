import streamlit as st
import sqlite3
import pandas as pd
import chardet
import io
import os
from datetime import datetime

# StreamlitのUI設定
st.set_page_config(layout="wide")

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

# DB接続
def get_db_connection():
    if "conn" not in st.session_state:
        if "db_path" not in st.session_state or not st.session_state.db_path:
            st.error("menu.pyでデータベースに接続してください。")
            st.stop()
        st.session_state.conn = sqlite3.connect(st.session_state.db_path, check_same_thread=False)
    return st.session_state.conn

conn = get_db_connection()

# テンプレート作成
def create_excel_template():
    data = {
        "管理番号": ["", "", ""],
        "財務R4科目コード": ["", "", ""],
        "財務R4科目名": ["", "", ""],
        "財務R4補助科目コード": ["", "", ""],
        "財務R4補助科目名": ["", "", ""],
        "弥生会計補助科目名": ["", "", ""]
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output

# タイトル
st.title("補助科目マスターのインポート")

# ✅ テンプレートダウンロード（上に配置）
excel_file = create_excel_template()
st.download_button(
    label="📥 補助科目マスターのインポート用テンプレートをダウンロード",
    data=excel_file,
    file_name="hojo_import_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ✅ 接続中DBパス表示（テンプレートの下）
st.info(f"現在接続中のデータベース: {st.session_state.get('db_path')}")

# テーブル作成（なければ）
def create_table():
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hojo_master (
            管理番号 TEXT PRIMARY KEY,
            財務R4科目コード TEXT NOT NULL,
            財務R4科目名 TEXT NOT NULL,
            財務R4補助科目コード TEXT NOT NULL,
            財務R4補助科目名 TEXT,
            弥生会計補助科目名 TEXT
        )
    ''')
    conn.commit()

create_table()

# 既存データ表示
try:
    with st.expander("📂 現在のデータベース内容を表示（hojo_master）", expanded=False):
        df_existing = pd.read_sql_query("SELECT * FROM hojo_master", conn)
        st.dataframe(df_existing)
        st.caption(f"現在の件数: {len(df_existing)} 件")
except Exception as e:
    st.warning("既存データの表示に失敗しました。")
    st.exception(e)

# アップロード処理
uploaded_file = st.file_uploader("📤 補助科目マスターエクセルをアップロード", type=["csv", "xlsx"])
if uploaded_file:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    df = None

    try:
        if file_extension == "csv":
            raw_data = uploaded_file.read()
            encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
            df = pd.read_csv(io.BytesIO(raw_data), encoding=encoding, errors="replace")
        elif file_extension == "xlsx":
            df = pd.read_excel(uploaded_file, engine="openpyxl")

        if df is not None:
            df.columns = df.columns.str.strip()
            df = df.rename(columns={
                "管理番号": "管理番号",
                "財務R4科目コード": "財務R4科目コード",
                "財務R4科目名": "財務R4科目名",
                "財務R4補助科目コード": "財務R4補助科目コード",
                "財務R4補助科目名": "財務R4補助科目名",
                "弥生会計補助科目名": "弥生会計補助科目名"
            })
            df["弥生会計補助科目名"] = df["弥生会計補助科目名"].fillna("？")

            st.write("📄 アップロードされたデータ")
            st.dataframe(df)

            if st.button("💾 データベースに保存"):
                try:
                    cursor = conn.cursor()
                    for row in df.to_dict(orient="records"):
                        cursor.execute('''
                            INSERT OR REPLACE INTO hojo_master
                            (管理番号, 財務R4科目コード, 財務R4科目名, 財務R4補助科目コード, 財務R4補助科目名, 弥生会計補助科目名)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            row["管理番号"], row["財務R4科目コード"], row["財務R4科目名"],
                            row["財務R4補助科目コード"], row["財務R4補助科目名"], row["弥生会計補助科目名"]
                        ))
                    conn.commit()
                    st.success("データベースに保存しました！")
                    st.session_state["refresh_hojo"] = True
                except Exception as db_error:
                    st.error(f"データベース保存時にエラーが発生しました: {db_error}")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.exception(e)

# 保存後再表示
if st.session_state.get("refresh_hojo"):
    try:
        df_db = pd.read_sql_query("SELECT * FROM hojo_master", conn)
        st.write("📋 データベースの内容")
        st.dataframe(df_db)
        st.caption(f"件数: {len(df_db)} 件")
    except Exception as e:
        st.error("再表示中にエラーが発生しました")
        st.exception(e)
    del st.session_state["refresh_hojo"]

# ✅ DBファイルのダウンロードボタン（DB名 + 日付）
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
