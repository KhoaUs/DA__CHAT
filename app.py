import streamlit as st
from streamlit_mic_recorder import mic_recorder
from modules.agent_engine import init_agent
from modules.visualization import DashboardRenderer
import os
from dotenv import load_dotenv
import speech_recognition as sr
import io
import json
import datetime
from langchain_core.messages import HumanMessage, ToolMessage

# --- 1. CẤU HÌNH TRANG & CSS ---
st.set_page_config(page_title="E-Commerce AI Analyst", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")

# Tắt log rác của Google
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

load_dotenv() 

# CSS Tùy chỉnh giao diện
st.markdown("""
<style>
    /* Ẩn menu mặc định */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {background-color: transparent;}
    
    /* Bong bóng chat */
    .stChatMessage {padding: 1rem; border-radius: 15px; margin-bottom: 10px; border: 1px solid #f0f2f6;}
    .stChatMessage .st-emotion-cache-1p1m4ay {background-color: #ffffff; border: 1px solid #eee;}
    
    /* Tiêu đề */
    .main-title {font-size: 2.5rem; font-weight: 700; color: #FF4B4B; text-align: center; margin-bottom: 0.5rem;}
    .sub-title {text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 2rem;}
    
    /* Nút mic */
    .stButton button {height: 50px; border-radius: 50%; width: 50px;}
    
    /* Expander Dashboard */
    .streamlit-expanderHeader {font-weight: 600; color: #31333F; background-color: #f0f2f6; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# --- 2. HÀM HỖ TRỢ ---
def parse_ai_response(content):
    """Làm sạch câu trả lời từ AI"""
    if isinstance(content, str): return content
    elif isinstance(content, list):
        text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
        return " ".join(text_parts)
    return str(content)

def transcribe_audio(audio_bytes):
    """Chuyển đổi giọng nói thành văn bản"""
    r = sr.Recognizer()
    try:
        audio_data = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_data) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="vi-VN")
            return text
    except Exception:
        return None

def log_to_file(user_input, tool_logs, ai_response):
    """Ghi log hoạt động vào file JSONL"""
    log_entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_input": user_input,
        "tools_called": tool_logs,
        "ai_response": ai_response
    }
    with open("agent_activity.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("Control Center")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Chưa tìm thấy GOOGLE_API_KEY")
        st.stop()
    
    st.markdown("### 🤖 Cấu hình AI")
    # Cập nhật danh sách model chuẩn
    model_options = {
        "Gemini 2.5 Flash (Khuyên dùng)": "gemini-2.5-flash",
        "Gemini 2.5 Pro (Thông minh nhất)": "gemini-2.5-pro",
        "Gemini 2.5 Flash Lite (Siêu tốc)": "gemini-2.5-flash-lite",
    }
    selected_model_label = st.selectbox("Chọn Model:", options=list(model_options.keys()), index=0)
    selected_model_name = model_options[selected_model_label]
    
    st.markdown("---")
    
    # Nút tải log
    st.markdown("### 📝 Nhật ký")
    if os.path.exists("agent_activity.jsonl"):
        with open("agent_activity.jsonl", "r", encoding="utf-8") as f:
            st.download_button("📥 Tải File Log (.jsonl)", f, "agent_activity.jsonl", "application/json")

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-title">🛍️ E-Commerce Smart Analyst</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Trợ lý phân tích thị trường & đối thủ cạnh tranh bằng AI</div>', unsafe_allow_html=True)

# Khởi tạo Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Hôm nay chúng ta sẽ phân tích sản phẩm nào?"}]
if "last_tool_output" not in st.session_state:
    st.session_state.last_tool_output = None
if "prev_audio_bytes" not in st.session_state:
    st.session_state.prev_audio_bytes = None

# Container chứa lịch sử chat
chat_container = st.container()

# Container nhập liệu (Nằm dưới cùng)
input_container = st.container()

with input_container:
    col1, col2 = st.columns([1, 15])
    with col1: # Nút Mic
        audio = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", key='recorder', format="wav")
    with col2: # Ô nhập liệu
        text_input = st.chat_input("Ví dụ: Phân tích thị trường tai nghe bluetooth...")

# --- 5. XỬ LÝ INPUT ---
final_user_input = None
if audio and audio['bytes'] != st.session_state.prev_audio_bytes:
    st.session_state.prev_audio_bytes = audio['bytes']
    with st.spinner("🎧 Đang nghe..."):
        text = transcribe_audio(audio['bytes'])
        if text: final_user_input = text
        else: st.toast("Không nghe rõ giọng nói.")
elif text_input:
    final_user_input = text_input

# --- 6. CORE LOGIC (AI AGENT) ---
if final_user_input:
    # 6.1. Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": final_user_input})
    st.session_state.last_tool_output = None # Reset Dashboard cũ
    
    try:
        # Khởi tạo Agent
        agent = init_agent(api_key, model_name=selected_model_name)
        
        with st.spinner(f"AI đang phân tích dữ liệu..."):
            # Gọi Agent thực thi
            response_state = agent.invoke({"messages": [HumanMessage(content=final_user_input)]})
            returned_messages = response_state['messages']
            
            # 6.2. Trích xuất Log (AI đã gọi tool gì?)
            tool_logs = []
            for msg in returned_messages:
                if hasattr(msg, 'tool_calls') and len(msg.tool_calls) > 0:
                    for tool_call in msg.tool_calls:
                        tool_logs.append({
                            "name": tool_call['name'],
                            "args": tool_call['args']
                        })
            
            # 6.3. Lấy câu trả lời text
            raw_content = returned_messages[-1].content
            ai_response = parse_ai_response(raw_content)
            
            # 6.4. Ghi log hệ thống
            log_to_file(final_user_input, tool_logs, ai_response)
            
            # 6.5. Hiển thị Log Tool ra màn hình (Debug UI)
            if tool_logs:
                with st.chat_message("ai"):
                    with st.expander("🛠️ [DEBUG] AI Execution Log", expanded=False):
                        st.json(tool_logs)

            # 6.6. Bắt dữ liệu Dashboard (Lấy output của tool cuối cùng)
            for msg in reversed(returned_messages):
                if isinstance(msg, ToolMessage):
                    st.session_state.last_tool_output = {
                        "tool": msg.name, 
                        "data": msg.content
                    }
                    break 
        
        # 6.7. Lưu câu trả lời AI
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

    except Exception as e:
        st.error(f"Lỗi hệ thống: {e}")

# --- 7. RENDER CHAT HISTORY ---
with chat_container:
    for msg in st.session_state.messages:
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

# --- 8. RENDER DASHBOARD (CHÌA KHÓA CỦA ỨNG DỤNG) ---
if st.session_state.last_tool_output:
    st.markdown("---")
    
    tool_type = st.session_state.last_tool_output['tool']
    data_content = st.session_state.last_tool_output['data']
    
    # Container Dashboard xịn sò
    with st.expander("📊 DASHBOARD PHÂN TÍCH CHI TIẾT", expanded=True):
        try:
            # === Mapping Tool -> Visualization Function ===
            
            # 1. Các Dashboard cơ bản
            if tool_type == "get_price_stats":
                DashboardRenderer.render_price_dashboard(data_content)
                
            elif tool_type == "get_sales_stats":
                DashboardRenderer.render_sales_dashboard(data_content)
                
            elif tool_type == "get_review_stats":
                DashboardRenderer.render_review_dashboard(data_content)
            
            # 2. Dashboard Tổng hợp & Nâng cao
            elif tool_type == "get_product_analysis":
                DashboardRenderer.render_combined_dashboard(data_content)
            
            elif tool_type == "get_advanced_market_analysis":
                DashboardRenderer.render_advanced_dashboard(data_content)
            
            # 3. Dashboard Top Brand (Đã sửa lỗi logic cũ)
            elif tool_type == "get_top_brands_analysis":
                # Truyền trực tiếp data_content (chuỗi JSON), 
                # DashboardRenderer sẽ tự parse để lấy đủ rank_by, share_metric
                DashboardRenderer.render_top_brands(data_content)
                
            # 4. Dashboard Category Trends (Mới thêm)
            elif tool_type == "get_category_trends":
                DashboardRenderer.render_category_trends(data_content)
                
        except Exception as e:
            st.error(f"⚠️ Không thể vẽ biểu đồ: {e}")
            with st.expander("Xem dữ liệu thô (Raw Data)"):
                st.write(data_content)