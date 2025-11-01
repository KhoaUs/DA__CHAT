import streamlit as st
from src.chatbot_app.nlp import get_intent_and_entities

# Đây là khâu "RÁP LẠI" - Nhóm 2 gọi code của Nhóm 1
# Ban đầu nó sẽ gọi code "Giả" 
from src.analysis_core.api import so_sanh_gia, goi_y_san_pham

# --- Cấu hình giao diện ---# st.title(":rainbow[Chatbot Phân tích TMĐT]")
# st.caption(f"Đồ án môn học - Phân tích dữ liệu thông minh")

st.set_page_config(
    page_title="Data analysis",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

"""
# :rainbow[:material/query_stats: Data analysis chatbot]

Công cụ phân tích dữ liệu thương mại điện tử

"""

""  # Add some space.

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "image" in message:
            st.image(message["image"])


# --- Luồng xử lý chính ---
if user_query := st.chat_input("Bạn cần tôi phân tích gì?"):

    # 1. Hiển thị tin nhắn của người dùng
    st.chat_message("user").write(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 2. Gọi "Bộ não NLP" (Code của Nhóm 2)
    intent, entities = get_intent_and_entities(user_query)

    response_text = ""
    response_image = None

    # 3. Gọi API (Code của Nhóm 1)
    try:
        if intent == "so_sanh_gia":
            result = so_sanh_gia(entities.get("ten_san_pham"))
           
            # Format kết quả trả về từ API
            response_text = f"Kết quả so sánh giá cho '{entities.get('ten_san_pham')}':\n"
            for item in result.get("data", []):
                response_text += f"- {item['platform']}: {item['price']:,} VND\n"

            # Lấy biểu đồ (theo yêu cầu đề tài)
            response_image = result.get("chart_path")

        elif intent == "goi_y_san_pham":
            result = goi_y_san_pham(entities.get("danh_muc"), entities.get("gia_max"))

            response_text = "Đây là các gợi ý cho bạn:\n"
            for item in result.get("data", []):
                response_text += f"- {item['name']} (Giá: {item['price']:,} VND)\n"

        else: # (intent == "fallback")
            response_text = "Xin lỗi, tôi chưa hiểu yêu cầu của bạn. Tôi chỉ có thể (1) so sánh giá hoặc (2) gợi ý sản phẩm."


    except Exception as e:
        response_text = f"Đã xảy ra lỗi: {e}"

    # 4. Hiển thị kết quả của Bot
    with st.chat_message("assistant"):
        st.write(response_text)
        if response_image:
            st.image(response_image)
   
    # Lưu tin nhắn của bot
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "image": response_image
    })