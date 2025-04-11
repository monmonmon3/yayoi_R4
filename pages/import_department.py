import streamlit as st
import sqlite3
import pandas as pd
import chardet
import io

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

# 入力用Excelテンプレート作成
def create_excel_template():
    # DataFrameの作成
    data = {
        "財務R4部門コード": ["", "", ""],  # 例: 初期空のデータ
        "財務R4部門名": ["", "", ""],
        "弥生会計部門名": ["", "", ""]
    }
    df = pd.DataFrame(data)
    
    # Excelファイルとして保存
    output = io.BytesIO()
    df.to_excel(output, index=False, engine="openpyxl")
    output.seek(0)
    return output

# StreamlitのUI
st.title("部門マスターのインポート")

# Excelテンプレートの作成
excel_file = create_excel_template()

# ダウンロードボタンの追加
st.download_button(
    label="部門インポート用テンプレートをダウンロード",
    data=excel_file,
    file_name="department_import_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# === データベース接続関数 ===
DB_NAME = "department.db"

def get_db_connection():
    return sqlite3.connect(DB_NAME)

def create_table():
    """ 部門マスターのテーブル作成 (初回のみ) """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS department_master (
            財務R4部門コード TEXT PRIMARY KEY, 
            財務R4部門名 TEXT NOT NULL, 
            弥生会計部門名 TEXT
        )
    ''')
    conn.commit()
    conn.close()

# 初回起動時にテーブル作成
create_table()

# === ファイルアップロードとデータベースへの保存 ===
uploaded_file = st.file_uploader("Excelをアップロード", type=["csv", "xlsx"])

if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    df = None  

    try:
        if file_extension == "csv":
            uploaded_file.seek(0)  # ストリームをリセット
            raw_data = uploaded_file.read()
            detected = chardet.detect(raw_data)
            encoding = detected["encoding"] or "utf-8"  # エンコーディングの設定

            uploaded_file.seek(0)  # 再び先頭に戻す
            df = pd.read_csv(io.BytesIO(raw_data), encoding=encoding, errors="replace")
        
        elif file_extension == "xlsx":
            df = pd.read_excel(uploaded_file, engine="openpyxl")

        if df is not None:
            df.columns = df.columns.str.strip()

            # 必要な列名にリネーム
            df = df.rename(columns={
                "財務R4部門コード": "財務R4部門コード",
                "財務R4部門名": "財務R4部門名",
                "弥生会計部門名": "弥生会計部門名",
            })

            # 「弥生会計部門名」がない場合は "？" を代入
            df["弥生会計部門名"] = df["弥生会計部門名"].fillna("？")

            st.write("アップロードされたデータ")
            st.dataframe(df)

            if st.button("データベースに保存"):
                conn = get_db_connection()
                cursor = conn.cursor()

                # df を1行ずつ辞書として取得し、確実に処理
                for row in df.to_dict(orient="records"):
                    cursor.execute('''
                        INSERT OR REPLACE INTO department_master 
                        (財務R4部門コード, 財務R4部門名, 弥生会計部門名)
                        VALUES (?, ?, ?)
                    ''', (row["財務R4部門コード"], row["財務R4部門名"], row["弥生会計部門名"]))

                conn.commit()
                conn.close()
                st.success("データベースに保存しました！")

            # データベースの内容を表示
            conn = get_db_connection()
            df_db = pd.read_sql_query("SELECT * FROM department_master", conn)
            conn.close()
            st.write("データベースの内容")
            st.dataframe(df_db)
        else:
            st.error("ファイルの読み込みに失敗しました。エンコーディングを確認してください。")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
