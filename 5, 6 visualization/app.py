import streamlit as st
from streamlit_mic_recorder import mic_recorder
from modules.visualization import DashboardRenderer
from modules.database_mock import get_price_stats, get_sales_stats, get_review_stats, get_product_analysis, get_brand_sales_stats, get_top_sellers_stats, get_brand_share_stats
import os
from dotenv import load_dotenv
import speech_recognition as sr
import io
import json
from langchain_core.messages import HumanMessage, ToolMessage

# --- RENDER DASHBOARD (NẾU CÓ) ---
if final_user_input:
    st.markdown("---")
    
    tool_type = st.session_state.last_tool_output['tool']
    data_content = st.session_state.last_tool_output['data']

    
    # Container cho Dashboard đẹp hơn
    with st.expander("📊 KẾT QUẢ PHÂN TÍCH CHI TIẾT", expanded=True):
        try:
            elif tool_type == "get_top_sellers_stats":
                DashboardRenderer.render_top_sellers_dashboard(get_top_sellers_stats(''))
            elif tool_type == "get_brand_share_stats":
                DashboardRenderer.render_brand_share_dashboard(get_brand_share_stats(''))
        except Exception as e:
            st.warning("Dữ liệu không đủ để vẽ biểu đồ.")
            st.error(f"Lỗi: {e}")