import streamlit as st
import json
import os
import time
from datetime import datetime
import pandas as pd

# 設定頁面設定
st.set_page_config(
    page_title="羽球場地公告監控",
    page_icon="🏸",
    layout="wide",
)

# 匯入專案模組
import config
from main import run

# CSS 樣式
st.markdown("""
<style>
    .card {
        border-radius: 10px;
        padding: 20px;
        background-color: #f8f9fa;
        margin-bottom: 20px;
        border-left: 5px solid #00d4aa;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .dark .card {
        background-color: #2b3035;
    }
    .title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .tag {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 5px;
    }
    .tag.school { background-color: #e0f2fe; color: #0284c7; }
    .tag.keyword { background-color: #fef3c7; color: #d97706; }
    .tag.date { background-color: #f3f4f6; color: #4b5563; }
</style>
""", unsafe_allow_html=True)

st.title("🏸 羽球場地公告監控")
st.markdown("自動監控學校場地租用公告。")

# 左側邊欄
with st.sidebar:
    st.header("⚙️ 控制面板")
    st.write(f"目前監控中學校共 **{len(config.SCHOOLS)}** 所。")
    if st.button("🚀 立即手動掃描所有學校", use_container_width=True):
        with st.spinner("正在爬取最新公告...這可能需要幾十秒鐘"):
            start_time = time.time()
            result = run(dry_run=True, force=True)
            elapsed = time.time() - start_time
            # 將結果存入 session_state 以便顯示
            st.session_state["scan_result"] = result
            st.session_state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"掃描完成！耗時 {elapsed:.1f} 秒。")

    st.markdown("---")
    st.subheader("🏫 監控學校列表")
    for s in config.SCHOOLS:
        st.markdown(f"- {s['name']}")

# 主畫面
result_data = None
result_source = "尚未檢查"

# 決定要用哪份資料
if "scan_result" in st.session_state:
    result_data = st.session_state["scan_result"]
    result_source = f"即時掃描 ({st.session_state.get('last_updated', '')})"
else:
    # 嘗試讀取 GitHub Action 自動產生的 results.json
    results_path = os.path.join("docs", "results.json")
    if os.path.exists(results_path):
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                result_data = json.load(f)
            result_source = f"自動排程紀錄 ({result_data.get('timestamp', '未知時間')})"
        except Exception as e:
            st.warning(f"無法讀取快取結果：{e}")

if not result_data:
    st.info("👋 目前沒有資料，您可以等待系統每日自動執行，或是點擊左側面板「立即手動掃描所有學校」。")
else:
    # 顯示統計資料
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("監控學校數", len(config.SCHOOLS))
    with col2:
        st.metric("共爬取公告", result_data.get("total_fetched", 0))
    with col3:
        st.metric("30天內公告", result_data.get("after_date_filter", 0))
    with col4:
        st.metric("關鍵字命中", result_data.get("keyword_matched", 0))

    st.markdown(f"**資料來源：** `{result_source}`")
    st.markdown("---")
    
    announcements = result_data.get("all_matched", [])
    if not announcements:
        st.success("🎉 目前無任何符合『場地/租用/羽球』關鍵字的公告。")
    else:
        st.subheader(f"📋 近期符合條件公告 (共 {len(announcements)} 筆)")
        
        # 可讓使用者快速過濾
        search_term = st.text_input("🔍 搜尋公告標題...")
        
        for ann in announcements:
            title = ann.get("title", "")
            if search_term and search_term.lower() not in title.lower():
                continue
                
            school = ann.get("school", "")
            url = ann.get("url", "#")
            date_str = ann.get("date", "")
            matched_kws = ann.get("matched_keywords", [])
            
            # 使用 HTML / CSS 卡片來美化
            kw_tags = "".join([f'<span class="tag keyword">🔑 {kw}</span>' for kw in matched_kws])
            
            st.markdown(f"""
            <div class="card">
                <a href="{url}" target="_blank" style="font-size: 1.1rem; font-weight: bold; text-decoration: none;">{title}</a>
                <div style="margin-top: 10px;">
                    <span class="tag school">🏫 {school}</span>
                    <span class="tag date">📅 {date_str}</span>
                    {kw_tags}
                </div>
            </div>
            """, unsafe_allow_html=True)
