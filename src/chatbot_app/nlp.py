def get_intent_and_entities(user_query: str) -> (str, dict):
    """
    Bộ não NLP (Giả lập bằng từ khóa)
    Nhận câu hỏi của người dùng và trả về (ý định, thực thể)
    """
    query = user_query.lower()
    
    if "so sánh" in query or "giá" in query:
        intent = "so_sanh_gia"
        # Logic trích xuất thực thể (ví dụ đơn giản)
        entities = {"ten_san_pham": "iPhone 15"} # Tạm hardcode
        if "laptop" in query:
            entities = {"ten_san_pham": "Laptop XYZ"}
        return intent, entities

    if "gợi ý" in query or "tìm" in query:
        intent = "goi_y_san_pham"
        entities = {"danh_muc": "laptop", "gia_max": 20000000}
        return intent, entities
    
    # Ý định bắt buộc phải có
    return "fallback", {}