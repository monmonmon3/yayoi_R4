import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
import io
from datetime import datetime
import os

st.set_page_config(layout="wide")

# 画像読み込み
image1 = Image.open("image1.png")
image2 = Image.open("image2.png")
image3 = Image.open("image3.png")

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

with st.expander("⚽️ 弥生会計からの仕訳データのエクスポート方法"):
    st.write("「仕訳日記帳」を開きます。")
    st.image(image1, caption='サンプル画像')
    st.write("期間を選択して「エクスポート」")
    st.image(image2, caption='サンプル画像')
    st.write("「弥生会計インポート形式」「カンマ(CSV)形式」で出力")
    st.image(image3, caption='サンプル画像')

with st.expander("⚾️ 財務R4への仕訳データのインポート方法"):
    st.write("えい")

with st.expander("☠️ 注意点"):
    st.write("弥生会計側が外税でも、財務R4には内税でインポートします。")

st.title("仕訳変換")
# 接続中のデータベースのパスを表示
st.info(f"現在接続中のデータベース: {st.session_state.db_path}")
uploaded_file = st.file_uploader("弥生会計から出力したCSVファイルをアップロード", type=["csv", "xlsx"])

@st.cache_data
def load_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        try:
            df = pd.read_csv(uploaded_file, header=None, encoding="cp932")
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, header=None, encoding="utf-8", errors="replace")
    elif uploaded_file.name.endswith('.xlsx'):
        df = pd.read_excel(uploaded_file, header=None)
    else:
        st.error("対応ファイル形式は .csv です。")
        return None

    df.columns = [
        "識別フラグ", "伝票No.", "決算", "取引日付", "借方勘定科目", "借方補助科目", "借方部門", "借方税区分",
        "借方金額", "借方税金額", "貸方勘定科目", "貸方補助科目", "貸方部門", "貸方税区分", "貸方金額", "貸方税金額",
        "摘要", "番号", "期日", "タイプ", "生成元", "仕訳メモ", "付箋1", "付箋2", "調整"
    ]

    def wareki_to_date_simple(date_str):
        if isinstance(date_str, str) and date_str.startswith("R."):
            try:
                date_str = date_str.replace("R.", "")
                year, month, day = map(int, date_str.split("/"))
                seireki_year = 2018 + year
                return f"{seireki_year}/{month:02d}/{day:02d}"
            except:
                return date_str
        return date_str

    df.rename(columns={
        "取引日付": "日付",
        "借方税金額": "借方税額",
        "貸方税金額": "貸方税額"
    }, inplace=True)

    if "日付" in df.columns:
        df["日付"] = df["日付"].apply(wareki_to_date_simple)
        df["日付"] = pd.to_datetime(df["日付"], errors="coerce").dt.date

    return df

if uploaded_file and uploaded_file.size > 0:
    if "conn" not in st.session_state:
        st.error("データベースが未接続です。menu.pyで接続してください。")
    else:
        conn = st.session_state.conn
        df = load_file(uploaded_file)
        df["日付"] = pd.to_datetime(df["日付"], errors="coerce").dt.date

        # 借方勘定科目が欠損している行に"諸口"を入力し、借方金額を貸方金額で補完
        mask_kari_empty = df["借方勘定科目"].isna()
        df.loc[mask_kari_empty, "借方勘定科目"] = "諸口"
        df.loc[mask_kari_empty, "借方金額"] = df.loc[mask_kari_empty, "貸方金額"]

        # 貸方勘定科目が欠損している行にも同様に"諸口"と補完処理
        mask_kashi_empty = df["貸方勘定科目"].isna()
        df.loc[mask_kashi_empty, "貸方勘定科目"] = "諸口"
        df.loc[mask_kashi_empty, "貸方金額"] = df.loc[mask_kashi_empty, "借方金額"]

        # 借方補助科目または貸方補助科目が「賃貸収入」の場合、補助科目を空欄にし勘定科目を賃貸収入に変更
        df.loc[df["借方補助科目"] == "賃貸収入", "借方勘定科目"] = "賃貸収入"
        df.loc[df["借方補助科目"] == "賃貸収入", "借方補助科目"] = ""
        
        df.loc[df["貸方補助科目"] == "賃貸収入", "貸方勘定科目"] = "賃貸収入"
        df.loc[df["貸方補助科目"] == "賃貸収入", "貸方補助科目"] = ""

        st.write("弥生会計形式 仕訳データプレビュー")
        st.dataframe(df)
    
        def get_accounting_data():
            query = "SELECT 財務R4科目コード, 財務R4科目名, 弥生会計科目名 FROM kamoku_master"
            return pd.read_sql(query, conn)

        accounting_data = get_accounting_data()

        df_book = pd.DataFrame(columns=[
            "月種別", "種類", "形式", "作成方法", "付箋", "伝票日付", "伝票番号", "伝票摘要", "枝番",
            "借方部門", "借方部門名", "借方科目", "借方科目名", "借方補助", "借方補助科目名", "借方金額",
            "借方消費税コード", "借方消費税業種", "借方消費税税率", "借方資金区分", "借方任意項目１",
            "借方任意項目２", "借方インボイス情報", "貸方部門", "貸方部門名", "貸方科目", "貸方科目名",
            "貸方補助", "貸方補助科目名", "貸方金額", "貸方消費税コード", "貸方消費税業種",
            "貸方消費税税率", "貸方資金区分", "貸方任意項目１", "貸方任意項目２", "貸方インボイス情報",
            "摘要", "期日", "証番号", "入力マシン", "入力ユーザ", "入力アプリ", "入力会社", "入力日付"
        ])

        df_book["伝票日付"] = df["日付"]
        df_book["摘要"] = df["摘要"]
        df_book["伝票番号"] = df["伝票No."]

        for i, row in df.iterrows():
            for col in ["借方", "貸方"]:
                yayoi_account = row[f"{col}勘定科目"]
                matched_row = accounting_data[accounting_data["弥生会計科目名"] == yayoi_account]
                if not matched_row.empty:
                    df_book.at[i, f"{col}科目"] = matched_row["財務R4科目コード"].values[0]
                    df_book.at[i, f"{col}科目名"] = matched_row["財務R4科目名"].values[0]
            df_book.at[i, "借方金額"] = row["借方金額"]
            df_book.at[i, "貸方金額"] = row["貸方金額"]

        def get_tax_data():
            query = """
            SELECT 財務R4税コード, 財務R4税率, 財務R4インボイス, 財務R4簡易課税, 弥生会計税区分
            FROM syouhizei_master
            """
            return pd.read_sql(query, conn)

        tax_data = get_tax_data()

        for i, row in df.iterrows():
            for col in ["借方", "貸方"]:
                yayoi_tax = row[f"{col}税区分"]
                matched_row = tax_data[tax_data["弥生会計税区分"] == yayoi_tax]
                if not matched_row.empty:
                    df_book.at[i, f"{col}消費税コード"] = matched_row["財務R4税コード"].values[0]
                    df_book.at[i, f"{col}消費税税率"] = matched_row["財務R4税率"].values[0]
                    df_book.at[i, f"{col}インボイス情報"] = matched_row["財務R4インボイス"].values[0]   
                    df_book.at[i, f"{col}消費税業種"] = matched_row["財務R4簡易課税"].values[0]  


        def update_df_book(df, df_book):
            query_hojo = """
            SELECT 管理番号, 財務R4科目コード, 財務R4科目名, 財務R4補助科目コード, 
                   財務R4補助科目名, 弥生会計補助科目名 
            FROM hojo_master
            """
            df_hojo_db = pd.read_sql_query(query_hojo, conn)

            for index, row in df_book.iterrows():
                # 借方の処理
                debit_account = row['借方科目名']
                debit_sub_account = df.loc[index, '貸方補助科目']
                match_debit = df_hojo_db[(df_hojo_db['財務R4科目名'] == debit_account) & 
                                        (df_hojo_db['弥生会計補助科目名'] == debit_sub_account)]
                
                if not match_debit.empty:
                    df_book.loc[index, '借方補助'] = match_debit['財務R4補助科目コード'].values[0]
                    df_book.loc[index, '借方補助科目名'] = match_debit['財務R4補助科目名'].values[0]
                elif debit_account == '商品売上高':
                    df_book.loc[index, '借方補助'] = '19'   
                    df_book.loc[index, '借方補助科目名'] = 'その他'  
                elif debit_account in ['材料仕入高', 'C消耗品費', 'C外注加工費']:
                    df_book.loc[index, '借方補助'] = '99'   
                    df_book.loc[index, '借方補助科目名'] = 'その他'  
                else:
                    df_book.loc[index, '借方補助'] = '0'  # マッチしない場合は "0"
                    df_book.loc[index, '借方補助科目名'] = ''  # マッチしない場合は 空欄
                
                # 貸方の処理
                credit_account = row['貸方科目名']
                credit_sub_account = df.loc[index, '借方補助科目']
                match_credit = df_hojo_db[(df_hojo_db['財務R4科目名'] == credit_account) & 
                                        (df_hojo_db['弥生会計補助科目名'] == credit_sub_account)]
                
                if not match_credit.empty:
                    df_book.loc[index, '貸方補助'] = match_credit['財務R4補助科目コード'].values[0]
                    df_book.loc[index, '貸方補助科目名'] = match_credit['財務R4補助科目名'].values[0]
                elif credit_account == '商品売上高':
                    df_book.loc[index, '貸方補助'] = '19'  
                    df_book.loc[index, '貸方補助科目名'] = 'その他' 
                elif credit_account in ['材料仕入高', 'C消耗品費', 'C外注加工費']:
                    df_book.loc[index, '借方補助'] = '99'   
                    df_book.loc[index, '借方補助科目名'] = 'その他'  
                else:
                    df_book.loc[index, '貸方補助'] = '0'  # マッチしない場合は "0"
                    df_book.loc[index, '貸方補助科目名'] = ''  # マッチしない場合は 空欄
                    
            for index, row in df_book.iterrows():

                # 借方科目の確認
                debit_account = row['借方科目']
                # 貸方科目の確認
                credit_account = row['貸方科目']
                
                # 借方補助が空白の場合
                if pd.isna(row['借方補助']) or row['借方補助'] == "":
                    if debit_account == 810:
                        df_book.loc[index, '借方補助'] = 19  # 810の場合
                    elif debit_account in [401, 435, 448]:
                        df_book.loc[index, '借方補助'] = 99  # 401, 435, 448の場合

                # 貸方補助が空白の場合
                if pd.isna(row['貸方補助']) or row['貸方補助'] == "":
                    if credit_account == 810:
                        df_book.loc[index, '貸方補助'] = 19  # 810の場合
                    elif credit_account in [401, 435, 448]:
                        df_book.loc[index, '貸方補助'] = 99  # 401, 435, 448の場合

            return df_book

        df_book = update_df_book(df, df_book)
        st.write("R4形式 仕訳データプレビュー")
        st.dataframe(df_book)


    # SQLiteファイル名を取得
    db_path = st.session_state.conn.execute("PRAGMA database_list").fetchone()[2]
    db_name = os.path.splitext(os.path.basename(db_path))[0]

    # 今日の日付を "YYYYMMDD" 形式で取得
    today = datetime.today().strftime("%Y%m%d")

    # ファイル名を「DB名_作成日:YYYYMMDD.csv」の形式に
    file_name = f"{db_name}_作成日:{today}.csv"

    # CSVをバイナリ形式でエクスポート（Excel文字化け回避のためutf-8-sig）
    csv_bytes = io.BytesIO()
    df_book.to_csv(csv_bytes, index=False, encoding="utf-8-sig")
    csv_bytes.seek(0)

    # ダウンロードボタン
    st.download_button(
        label="CSVをダウンロード",
        data=csv_bytes,
        file_name=file_name,
        mime="application/octet-stream"
    )