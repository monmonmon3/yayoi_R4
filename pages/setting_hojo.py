import streamlit as st
import pandas as pd
import sqlite3
import uuid
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
    [data-baseweb="input"] input {
        background-color: white !important;
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

# タイトル
st.title("補助科目マスター設定")

# DB接続（menu.pyと同じ）
def get_db_connection():
    if "conn" not in st.session_state:
        if "db_path" not in st.session_state or not st.session_state.db_path:
            st.error("menu.pyでDBに接続してください")
            st.stop()
        st.session_state.conn = sqlite3.connect(st.session_state.db_path, check_same_thread=False)
    return st.session_state.conn

conn = get_db_connection()
cursor = conn.cursor()
st.info(f"接続中のDB: {st.session_state.get('db_path')}")

# データ取得
query = "SELECT 管理番号, 財務R4科目コード, 財務R4科目名, 財務R4補助科目コード, 財務R4補助科目名, 弥生会計補助科目名 FROM hojo_master"
df = pd.read_sql_query(query, conn)

# タブ表示
tab1, tab2 = st.tabs(["📋 一覧・編集・削除", "➕ 新規追加"])

with tab1:
    if df.empty:
        st.warning("データがありません")
    else:
        df_edit = df.copy()
        df_edit["削除"] = False

        edited_df = st.data_editor(
            df_edit,
            num_rows="dynamic",
            use_container_width=True,
            key="hojo_data_editor",
        )

        rows_to_delete = edited_df[edited_df["削除"] == True]
        if not rows_to_delete.empty:
            if st.button("選択した行を削除"):
                for code in rows_to_delete["管理番号"]:
                    cursor.execute("DELETE FROM hojo_master WHERE 管理番号 = ?", (code,))
                conn.commit()
                st.success("削除しました。ページを再読み込みしてください。")

        if st.button("変更を保存"):
            for _, row in edited_df.iterrows():
                cursor.execute("""
                    UPDATE hojo_master SET 
                        財務R4科目コード = ?, 
                        財務R4科目名 = ?, 
                        財務R4補助科目コード = ?, 
                        財務R4補助科目名 = ?, 
                        弥生会計補助科目名 = ?
                    WHERE 管理番号 = ?
                """, (
                    row["財務R4科目コード"], row["財務R4科目名"], row["財務R4補助科目コード"],
                    row["財務R4補助科目名"], row["弥生会計補助科目名"], row["管理番号"]
                ))
            conn.commit()
            st.success("変更を保存しました。ページを再読み込みしてください。")

with tab2:
    st.subheader("新規追加")
    new_id = st.text_input("管理番号（未入力なら自動生成）")
    new_main_code = st.text_input("財務R4科目コード")
    new_main_name = st.text_input("財務R4科目名")
    new_sub_code = st.text_input("財務R4補助科目コード")
    new_sub_name = st.text_input("財務R4補助科目名")
    new_yayoi_name = st.text_input("弥生会計補助科目名")

    if st.button("追加"):
        if new_main_code.strip() and new_sub_code.strip():
            new_id = new_id.strip() if new_id.strip() else str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO hojo_master 
                (管理番号, 財務R4科目コード, 財務R4科目名, 財務R4補助科目コード, 財務R4補助科目名, 弥生会計補助科目名)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                new_id, new_main_code, new_main_name, new_sub_code, new_sub_name, new_yayoi_name
            ))
            conn.commit()
            st.success(f"追加完了（管理番号: {new_id}）")
        else:
            st.error("財務R4科目コードと補助コードは必須です")

# --- データベースダウンロードボタン（接続中のDB名＋日付） ---
if "db_path" in st.session_state and os.path.isfile(st.session_state.db_path):
    db_path = st.session_state.db_path
    db_filename = os.path.basename(db_path)
    db_name, db_ext = os.path.splitext(db_filename)
    today = datetime.today().strftime("%Y%m%d")
    download_name = f"{db_name}_{today}{db_ext}"

    with open(db_path, "rb") as f:
        db_bytes = f.read()

    st.download_button(
        label="💾 データベースを保存（デスクトップへ）",
        data=db_bytes,
        file_name=download_name,
        mime="application/octet-stream"
    )
