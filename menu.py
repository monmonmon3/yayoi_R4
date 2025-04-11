import streamlit as st
import os
import sqlite3
from pathlib import Path
import tempfile

# ページ設定
st.set_page_config(layout="wide")

def main():
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
    st.header("🆕 新規データベース作成")

    db_name = st.text_input("作成するDBファイル名（例: my_database.db）", value="my_database.db")
    if st.button("📁 デスクトップに新規作成"):
        try:
            desktop_path = os.path.join(Path.home(), "Desktop")
            os.makedirs(desktop_path, exist_ok=True)
            db_path = os.path.join(desktop_path, db_name)

            if os.path.exists(db_path):
                st.warning("同名のDBファイルがすでに存在します。上書きします。")

            conn = sqlite3.connect(db_path, check_same_thread=False)
            initialize_tables(conn)
            st.session_state.conn = conn
            st.session_state.db_path = db_path
            st.success(f"デスクトップに新しいDBを作成しました: {db_path}")
        except Exception as e:
            st.error(f"DB作成に失敗しました: {e}")

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

if __name__ == "__main__":
    main()
