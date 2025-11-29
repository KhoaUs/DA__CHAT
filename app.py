import streamlit as st
from streamlit_mic_recorder import mic_recorder
from modules.agent_engine import init_agent
from modules.visualization import DashboardRenderer
import os
from dotenv import load_dotenv
import speech_recognition as sr
import io
import json
from langchain_core.messages import HumanMessage, ToolMessage

# --- CẤU HÌNH TRANG & CSS TÙY CHỈNH ---
st.set_page_config(page_title="E-Commerce AI Analyst", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")
load_dotenv() 

# CSS để làm đẹp giao diện
st.markdown("""
<style>
    /* 1. Ẩn menu mặc định (3 chấm) và footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 2. KHÔNG ẩn header hoàn toàn nữa để giữ nút Sidebar */
    /* header {visibility: hidden;}  <-- Dòng cũ gây lỗi, đã bỏ đi */
    
    /* Nếu muốn ẩn thanh màu đỏ/cam trang trí trên cùng (tùy chọn) */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    /* 3. Tùy chỉnh bong bóng chat */
    .stChatMessage {
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 10px;
        border: 1px solid #f0f2f6; /* Thêm viền nhẹ */
    }
    
    /* 4. Avatar Icon */
    .stChatMessage .st-emotion-cache-1p1m4ay {
        background-color: #ffffff;
        border: 1px solid #eee;
    }
    
    /* 5. Tiêu đề chính đẹp hơn */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* 6. Chỉnh lại khoảng cách input giọng nói cho cân đối */
    .stButton button {
        height: 50px; /* Cân chỉnh chiều cao nút mic */
        border-radius: 50%; /* Làm nút mic tròn vo cho đẹp */
    }
</style>
""", unsafe_allow_html=True)

# --- HÀM HỖ TRỢ ---
def parse_ai_response(content):
    if isinstance(content, str): return content
    elif isinstance(content, list):
        text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
        return " ".join(text_parts)
    return str(content)

def transcribe_audio(audio_bytes):
    r = sr.Recognizer()
    try:
        audio_data = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_data) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="vi-VN")
            return text
    except Exception:
        return None

# --- SIDEBAR CẤU HÌNH ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.title("Setting Center")
    
    # Lấy API Key từ môi trường
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Chưa tìm thấy GOOGLE_API_KEY trong file .env")
        st.stop()
    
    st.markdown("### 🤖 Chọn Model AI")
    
    # Dictionary map tên hiển thị -> tên kỹ thuật
    # Lưu ý: Hiện tại 1.5 là bản mới nhất public. Nếu bạn có 2.5, hãy sửa value ở đây.
    model_options = {
        "Gemini Flash (Standard)": "gemini-2.5-flash",      # Mặc định (Tương đương yêu cầu 2.5 flash của bạn)
        "Gemini Flash Lite": "gemini-2.5-flash-lite",           # Bản Lite/Micro
        "Gemini Pro (Advanced)": "gemini-pro-latest"      # Bản Pro mạnh nhất
    }
    
    selected_model_label = st.selectbox(
        "Model Version",
        options=list(model_options.keys()),
        index=0 # Mặc định chọn cái đầu tiên
    )
    
    selected_model_name = model_options[selected_model_label]
    
    st.markdown("---")
    st.caption(f"Đang chạy: **{selected_model_label}**")
    st.caption("Ver: Latest")

# --- GIAO DIỆN CHÍNH ---
st.markdown('<div class="main-title">🛍️ E-Commerce Smart Analyst</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Trợ lý phân tích thị trường & đối thủ cạnh tranh bằng AI</div>', unsafe_allow_html=True)

# Init Session State
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Tôi có thể giúp gì cho việc kinh doanh của bạn hôm nay?"}]
if "last_tool_output" not in st.session_state:
    st.session_state.last_tool_output = None
if "prev_audio_bytes" not in st.session_state:
    st.session_state.prev_audio_bytes = None

# Container chứa chat history (để input luôn ở dưới cùng)
chat_container = st.container()

# --- INPUT AREA (STICKY BOTTOM) ---
# Tạo container input cố định hoặc nằm dưới cùng
input_container = st.container()

with input_container:
    col1, col2 = st.columns([1, 15])
    
    # Voice Input
    with col1:
        audio = mic_recorder(start_prompt="🎙️", stop_prompt="⏹️", key='recorder', format="wav")
    
    # Text Input
    with col2:
        text_input = st.chat_input("Hỏi về giá, doanh số, hoặc đánh giá sản phẩm...")

# --- LOGIC XỬ LÝ INPUT ---
final_user_input = None

# Xử lý Audio
if audio and audio['bytes'] != st.session_state.prev_audio_bytes:
    st.session_state.prev_audio_bytes = audio['bytes']
    with st.spinner("🎧 Đang nghe..."):
        text_from_voice = transcribe_audio(audio['bytes'])
        if text_from_voice:
            final_user_input = text_from_voice
        else:
            st.toast("Không nghe rõ giọng nói.")
# Xử lý Text
elif text_input:
    final_user_input = text_input

# --- CORE ENGINE ---
if final_user_input:
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": final_user_input})
    st.session_state.last_tool_output = None # Reset Dashboard
    
    try:
        # Gọi Init Agent với model được chọn từ Sidebar
        agent = init_agent(api_key, model_name=selected_model_name)
        
        with st.spinner(f"AI ({selected_model_label}) đang phân tích..."):
            response_state = agent.invoke({"messages": [HumanMessage(content=final_user_input)]})
            returned_messages = response_state['messages']
            
            raw_content = returned_messages[-1].content
            ai_response = parse_ai_response(raw_content)
            
            # Detect Tool Usage
            for msg in reversed(returned_messages):
                if isinstance(msg, ToolMessage):
                    st.session_state.last_tool_output = {
                        "tool": msg.name, 
                        "data": msg.content
                    }
                    break 
        
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

    except Exception as e:
        st.error(f"Lỗi: {e}")

# --- RENDER CHAT HISTORY (Ở TRÊN CÙNG) ---
with chat_container:
    for msg in st.session_state.messages:
        # Render icon tùy chỉnh
        avatar = "🤖" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

# --- RENDER DASHBOARD (NẾU CÓ) ---
if st.session_state.last_tool_output:
    st.markdown("---")
    
    tool_type = st.session_state.last_tool_output['tool']
    data_content = st.session_state.last_tool_output['data']
    
    # Container cho Dashboard đẹp hơn
    with st.expander("📊 KẾT QUẢ PHÂN TÍCH CHI TIẾT", expanded=True):
        try:
            if tool_type == "get_price_stats":
                DashboardRenderer.render_price_dashboard(data_content)
            elif tool_type == "get_sales_stats":
                DashboardRenderer.render_sales_dashboard(data_content)
            elif tool_type == "get_review_stats":
                DashboardRenderer.render_review_dashboard(data_content)
            elif tool_type == "get_product_analysis":
                DashboardRenderer.render_combined_dashboard(data_content)
        except Exception as e:
            st.warning("Dữ liệu không đủ để vẽ biểu đồ.")