from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
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
            "Bạn là một chuyên gia phân tích dữ liệu TMĐT. "
            "Bạn có quyền truy cập vào các công cụ (tools) để lấy dữ liệu giá, doanh số, đánh giá. "
            "\nQUY TẮC:"
            "\n1. Nếu người dùng hỏi các câu xã giao (chào hỏi, bạn là ai) hoặc kiến thức chung -> Hãy trả lời bình thường, KHÔNG dùng tool."
            "\n2. Nếu người dùng hỏi về sản phẩm cụ thể -> BẮT BUỘC dùng tool để lấy số liệu thực tế."
            "\n3. Sau khi tool trả về dữ liệu JSON -> Phân tích dữ liệu trả về và cung cấp những đánh giá kèm với Kết Luận Insight có giá trị bằng Tiếng Việt."
        )
    
    # 4. Bind system prompt vào LLM
    llm_with_system = llm.bind(system_prompt=system_prompt)
    
    # 5. Tạo Agent với LangGraph
    agent = create_react_agent(llm_with_system, tools)
    
    return agent