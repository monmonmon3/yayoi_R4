import os
import tempfile
import sqlite3
from pathlib import Path
import streamlit as st

# ページ設定
st.set_page_config(layout="wide")

with st.sidebar:
    st.markdown('<div class="section red">データベース接続</div>', unsafe_allow_html=True)
    st.page_link("menu.py", label="&nbsp;&nbsp;データベース接続")

    st.markdown('<div class="section blue">処理項目</div>', unsafe_allow_html=True)
    st.page_link("pages/henkan.py", label="&nbsp;&nbsp;仕訳変換")

    st.markdown('<div class="section green">設定変更</div>', unsafe_allow_html=True)
    st.page_link("pages/setting_kamoku.py", label="&nbsp;&nbsp;勘定科目設定")
    st.page_link("pages/setting_hojo.py", label="&nbsp;&nbsp;補助科目設定")
    st.page_link("pages/setting_syouhizei.py", label="&nbsp;&nbsp;消費税設定")

    st.markdown('<div class="section orange">データベースへのインポート</div>', unsafe_allow_html=True)
    st.page_link("pages/import_kamoku.py", label="&nbsp;&nbsp;勘定科目マスタインポート")
    st.page_link("pages/import_hojo.py", label="&nbsp;&nbsp;補助科目マスタインポート")
    st.page_link("pages/import_syouhizei.py", label="&nbsp;&nbsp;消費税マスタインポート")

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
    .red {
        color: #d62728;
        border-color: #d62728;
        background-color: #fdecea;
    }
    </style>
""", unsafe_allow_html=True)

def initialize_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kamoku_master (
            管理番号 TEXT PRIMARY KEY,     
            財務R4科目コード TEXT NOT NULL,
            財務R4科目名 TEXT NOT NULL,
            弥生会計科目名 TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hojo_master (
            管理番号 TEXT PRIMARY KEY, 
            財務R4科目コード TEXT NOT NULL,
            財務R4科目名 TEXT NOT NULL, 
            財務R4補助科目コード TEXT NOT NULL,
            財務R4補助科目名 TEXT, 
            弥生会計補助科目名 TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS syouhizei_master (
            管理番号 TEXT PRIMARY KEY,  
            財務R4税コード TEXT NOT NULL,
            財務R4税率 TEXT,
            財務R4インボイス TEXT,
            財務R4簡易課税 TEXT,
            弥生会計税区分 TEXT
        )
    """)

    conn.commit()

def handle_file_upload_and_create_db_ui():
    st.header("🔌 データベース接続")

    uploaded_file = st.file_uploader("SQLiteファイルをアップロードして接続", type=["db"])
    if uploaded_file is not None:
        temp_dir = tempfile.gettempdir()
        temp_db_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_db_path, "wb") as f:
            f.write(uploaded_file.read())
        
        try:
            conn = sqlite3.connect(temp_db_path, check_same_thread=False)
            initialize_tables(conn)
            st.session_state.conn = conn
            st.session_state.db_path = temp_db_path
            st.success("DBに接続しました（アップロード）")
        except Exception as e:
            st.error(f"DB接続に失敗しました: {e}")

    st.divider()

st.title("📥 データベースを新規作成")

# 一時ファイルでDB作成
with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmpfile:
    db_path = tmpfile.name

conn = sqlite3.connect(db_path)
initialize_tables(conn)

# DBを保存してダウンロードリンクを表示
with open(db_path, "rb") as f:
    db_data = f.read()

st.download_button(
    label="📁 新規データベースをダウンロード",
    data=db_data,
    file_name="my_database.db",
    mime="application/octet-stream"
)


handle_file_upload_and_create_db_ui()
