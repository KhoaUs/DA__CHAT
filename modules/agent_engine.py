from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent
from langgraph.types import Command
from modules.database_mock import get_price_stats, get_sales_stats, get_review_stats, get_product_analysis

def init_agent(api_key, model_name="gemini-2.5-flash", version_name="001"):
    if model_name=="gemini-pro-latest":
        version_name="Gemini Pro Latest"

    # 1. Khởi tạo LLM với Gemini
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        version=version_name,
        google_api_key=api_key,
        temperature=0
    )
    
    # 2. Định nghĩa Tools
    tools = [get_price_stats, get_sales_stats, get_review_stats, get_product_analysis]
    
    # 3. Tạo System Prompt
    system_prompt = (
        "ROLE & CONTEXT:"
        "\nBạn là một Chuyên gia Tư vấn Chiến lược Thương mại Điện tử (E-Commerce Strategist) hàng đầu. "
        "Khách hàng của bạn là những nhà bán hàng hoặc nhà đầu tư đang cần ra quyết định kinh doanh. "
        "Họ không cần bạn đọc lại các con số, họ cần bạn cho họ biết 'Phải làm gì tiếp theo?' dựa trên các con số đó."
        
        "\n\nACCESS:"
        "\nBạn có quyền truy cập vào các công cụ (tools) để lấy dữ liệu thị trường thực tế (Giá, Doanh số, Review)."

        "\n\nGUIDELINES (QUAN TRỌNG):"
        "\n1. CHẾ ĐỘ CHAT:"
        "\n   - Xã giao/Kiến thức chung -> Trả lời ngắn gọn, thân thiện, KHÔNG dùng tool."
        "\n   - Hỏi về sản phẩm -> BẮT BUỘC dùng tool."

        "\n2. TƯ DUY PHÂN TÍCH (THE THINKING PROCESS):"
        "\n   Khi nhận được JSON dữ liệu, hãy thực hiện quy trình suy luận sau trong đầu:"
        "\n   - Bối cảnh hóa: Giá này thấp hay cao so với thị trường? (So sánh min/max/avg)."
        "\n   - Tìm quan hệ nhân quả: Giá rẻ có bán chạy không? Hay giá cao nhưng shop uy tín vẫn bán tốt? (Dựa vào sales_vs_price_correlation)."
        "\n   - Phân tích cảm xúc: Người ta khen vì rẻ hay vì chất lượng? Chê vì ship lâu hay hàng dở? (Dựa vào keywords)."

        "\n3. ĐỊNH DẠNG CÂU TRẢ LỜI (OUTPUT FORMAT):"
        "\n   Không được trả lời kiểu văn xuôi tràn lan. Hãy chia thành 3 phần rõ rệt:"
        "\n   - TÓM TẮT THỊ TRƯỜNG: 2-3 câu ngắn gọn về tình hình chung (VD: 'Thị trường iPhone 15 đang cạnh tranh gay gắt về giá, Tiki đang dẫn đầu về giá rẻ')."
        "\n   - INSIGHT CHUYÊN SÂU (Điểm nhấn): Chỉ ra 2-3 điểm bất thường hoặc thú vị. (VD: 'Dù giá cao hơn 200k, Shop A vẫn bán chạy nhất -> Khách hàng ưu tiên uy tín hơn giá rẻ')."
        "\n   - KHUYẾN NGHỊ HÀNH ĐỘNG: Đưa ra lời khuyên cụ thể cho người bán"

        "\n4. STYLE:"
        "\n   - Dùng giọng văn chuyên nghiệp, sắc sảo, đi thẳng vào vấn đề."
        "\n   - Tuyệt đối KHÔNG dùng các câu thừa như: 'Dựa trên dữ liệu tôi thấy...', 'Dưới đây là kết quả...', 'Số liệu cho thấy...' -> Hãy nói thẳng vào kết luận."
        "\n   - Sử dụng emoji hợp lý để làm nổi bật các ý chính."
    )
    
    # 4. Bind system prompt vào LLM
    # llm_with_system = llm.bind(system_prompt=system_prompt)
    
    # 5. Tạo Agent với LangGraph
    agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)
    
    return agent