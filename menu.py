if st.button("📁 デスクトップに新規作成"):
    try:
        desktop_path = get_desktop_path()  # 正確なデスクトップ取得
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
