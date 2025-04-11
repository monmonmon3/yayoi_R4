import streamlit as st
import sqlite3
import pandas as pd
import chardet
import io
import os
from datetime import datetime

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

# 参考リンク
with st.expander("弥生会計の消費税情報"):
    st.markdown("[弥生会計サポートページ](https://support.yayoi-kk.co.jp/faq_Subcontents.html?page_id=18111&msockid=1e855cf3643b6d9a21ec51ec65476c70)")

with st.expander("財務R4の消費税情報"):
    st.markdown("[財務R4サポートページ](https://faq.r4support.epson.jp/app/answers/detail/a_id/5144)")

# タイトル
st.title("消費税マスターのインポート")

# Excelテンプレート作成
def create_excel_template():
    data = {
        "管理番号": ["", "", ""],
        "財務R4税コード": ["", "", ""],
        "財務R4税率": ["", "", ""],
        "財務R4インボイス": ["", "", ""],
        "財務R4簡易課税": ["", "", ""],
        "弥生会計税区分": ["", "", ""]
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output

# ExcelテンプレートDL（上に移動）
excel_file = create_excel_template()
st.download_button(
    label="📥 消費税マスターのインポート用テンプレートをダウンロード",
    data=excel_file,
    file_name="syouhizei_import_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# DB接続
def get_db_connection():
    if "conn" not in st.session_state:
        if "db_path" not in st.session_state or not st.session_state.db_path:
            st.error("「データベース接続」でデータベースに接続してください。")
            st.stop()
        st.session_state.conn = sqlite3.connect(st.session_state.db_path, check_same_thread=False)
    return st.session_state.conn

conn = get_db_connection()

# 接続DB表示（テンプレートの下に）
st.info(f"現在接続中のデータベース: {st.session_state.get('db_path')}")

# テーブル作成
def create_table():
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS syouhizei_master (
            管理番号 TEXT PRIMARY KEY,
            財務R4税コード TEXT NOT NULL,
            財務R4税率 TEXT,
            財務R4インボイス TEXT,
            財務R4簡易課税 TEXT,
            弥生会計税区分 TEXT
        )
    ''')
    conn.commit()

create_table()

# 既存データ表示
try:
    with st.expander("📂 現在のデータベース内容を表示（syouhizei_master）", expanded=False):
        df_existing = pd.read_sql_query("SELECT * FROM syouhizei_master", conn)
        st.dataframe(df_existing)
        st.caption(f"現在の件数: {len(df_existing)} 件")
except Exception as e:
    st.warning("既存データの表示に失敗しました。")
    st.exception(e)

# アップロードと保存
uploaded_file = st.file_uploader("📤 エクセルのアップロード", type=["csv", "xlsx"])
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
            # 列名のトリミングと標準化
            df.columns = df.columns.str.strip()
            df = df.rename(columns={
                "管理番号": "管理番号",
                "財務R4税コード": "財務R4税コード",
                "財務R4税率": "財務R4税率",
                "財務R4インボイス": "財務R4インボイス",
                "財務R4簡易課税": "財務R4簡易課税",
                "弥生会計税区分": "弥生会計税区分"
            })

            # 文字列として読み込み
            df["管理番号"] = df["管理番号"].astype(str)
            df["財務R4税コード"] = df["財務R4税コード"].astype(str)

            # 税率がNaNの場合は空欄にする
            df["財務R4税率"] = df["財務R4税率"].fillna("").astype(str)

            # 小数点を取り除き、整数化 → 文字列化。ただし空欄はそのまま空欄に
            def clean_integer_string(val):
                if pd.isna(val) or val == "":
                    return ""
                try:
                    return str(int(float(val)))
                except:
                    return ""

            df["財務R4インボイス"] = df["財務R4インボイス"].apply(clean_integer_string)
            df["財務R4簡易課税"] = df["財務R4簡易課税"].apply(clean_integer_string)

            # 弥生会計税区分の処理
            df["弥生会計税区分"] = df["弥生会計税区分"].fillna("？").astype(str)

            # 表示
            st.write("📄 アップロードされたデータ")
            st.dataframe(df)

            # 保存ボタン
            if st.button("💾 データベースに保存"):
                try:
                    cursor = conn.cursor()
                    for _, row in df.iterrows():
                        cursor.execute('''
                            INSERT OR REPLACE INTO syouhizei_master
                            (管理番号, 財務R4税コード, 財務R4税率, 財務R4インボイス, 財務R4簡易課税, 弥生会計税区分)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            row["管理番号"], row["財務R4税コード"], row["財務R4税率"],
                            row["財務R4インボイス"], row["財務R4簡易課税"], row["弥生会計税区分"]
                        ))
                    conn.commit()
                    st.success("データベースに保存しました！")
                    st.session_state["refresh_syouhizei"] = True
                except Exception as db_error:
                    st.error(f"保存時にエラーが発生しました: {db_error}")

    except Exception as e:
        st.error(f"ファイルの処理中にエラーが発生しました: {e}")
        st.exception(e)

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
