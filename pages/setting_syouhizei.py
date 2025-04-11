import streamlit as st
import pandas as pd
import sqlite3
import uuid
import os
from datetime import datetime

# ページ設定
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
    </style>
""", unsafe_allow_html=True)

# タイトルと参考リンク
st.title("消費税設定")

with st.expander("弥生会計の消費税情報"):
    st.markdown("[弥生会計サポートページ](https://support.yayoi-kk.co.jp/faq_Subcontents.html?page_id=18111)")

with st.expander("財務R4の消費税情報"):
    st.markdown("[財務R4サポートページ](https://faq.r4support.epson.jp/app/answers/detail/a_id/5144)")

# DB接続（menu.pyと共通化）
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
query_tax = "SELECT 管理番号, 財務R4税コード, 財務R4税率, 財務R4インボイス, 財務R4簡易課税, 弥生会計税区分 FROM syouhizei_master"
df_tax_db = pd.read_sql_query(query_tax, conn)

# タブ構成
tab1, tab2 = st.tabs(["📋 一覧・編集・削除", "➕ 新規追加"])

with tab1:
    if df_tax_db.empty:
        st.warning("データが読み込まれていません")
    else:
        df_edit = df_tax_db.copy()
        df_edit["削除"] = False

        edited_df = st.data_editor(
            df_edit,
            num_rows="dynamic",
            use_container_width=True,
            key="tax_data_editor",
        )

        rows_to_delete = edited_df[edited_df["削除"] == True]
        if not rows_to_delete.empty:
            if st.button("選択した行を削除"):
                for code in rows_to_delete["管理番号"]:
                    cursor.execute("DELETE FROM syouhizei_master WHERE 管理番号 = ?", (code,))
                conn.commit()
                st.success("削除しました。ページを再読み込みしてください。")

        if st.button("変更を保存"):
            for _, row in edited_df.iterrows():
                cursor.execute("""
                    UPDATE syouhizei_master SET 
                        財務R4税コード = ?, 
                        財務R4税率 = ?, 
                        財務R4インボイス = ?, 
                        財務R4簡易課税 = ?, 
                        弥生会計税区分 = ?
                    WHERE 管理番号 = ?
                """, (
                    row["財務R4税コード"], row["財務R4税率"], row["財務R4インボイス"],
                    row["財務R4簡易課税"], row["弥生会計税区分"], row["管理番号"]
                ))
            conn.commit()
            st.success("変更を保存しました。ページを再読み込みしてください。")

with tab2:
    st.subheader("新規税区分の追加")

    new_id = st.text_input("管理番号（未入力の場合は自動生成）")
    new_tax_code = st.text_input("新しい財務R4税コード")
    new_tax_rate = st.text_input("新しい財務R4税率（空欄可）")
    new_invoice = st.text_input("新しい財務R4インボイス（空欄可）")
    new_simplified_tax = st.text_input("新しい財務R4簡易課税（空欄可）")
    new_yayoi_tax = st.text_input("新しい弥生会計税区分")

    if st.button("追加"):
        if new_tax_code.strip():
            new_id = new_id.strip() if new_id.strip() else str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO syouhizei_master 
                (管理番号, 財務R4税コード, 財務R4税率, 財務R4インボイス, 財務R4簡易課税, 弥生会計税区分)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                new_id, new_tax_code,
                None if new_tax_rate.strip() == "" else new_tax_rate,
                None if new_invoice.strip() == "" else new_invoice,
                None if new_simplified_tax.strip() == "" else new_simplified_tax,
                new_yayoi_tax
            ))
            conn.commit()
            st.success(f"追加完了（管理番号: {new_id}）")
        else:
            st.error("税コードは必須です")

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
