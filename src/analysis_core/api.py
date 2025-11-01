# Đây là file của Nhóm 1, nhưng Nhóm 2 đang viết "giả"
import pandas as pd
import matplotlib.pyplot as plt

def so_sanh_gia(ten_san_pham: str) -> dict:
    """
    API Giả: So sánh giá sản phẩm.
    Nhóm 1 sẽ thay thế logic này bằng code thật.
    """
    print(f"[API Thật/Giả]: Đã gọi hàm so sánh giá cho '{ten_san_pham}'")
    
    # Dữ liệu giả
    data = {
        "platform": ["Tiki (Giả)", "Shopee (Giả)", "Lazada (Giả)"],
        "price": [10500000, 10200000, 10350000]
    }
    df = pd.DataFrame(data)
    
    # Tạo biểu đồ giả (theo yêu cầu đề tài)
    chart_path = "images/gia_san_pham.png"
    fig, ax = plt.subplots()
    df.plot(kind='bar', x='platform', y='price', ax=ax, title=f"So sánh giá {ten_san_pham}")
    plt.savefig(chart_path) # Lưu ảnh vào thư mục
    
    return {
        "status": "success",
        "data": df.to_dict('records'),
        "chart_path": chart_path
    }

def goi_y_san_pham(danh_muc: str, gia_max: int) -> dict:
    """
    API Giả: Gợi ý sản phẩm.
    """
    print(f"[API Thật/Giả]: Đã gọi hàm gợi ý '{danh_muc}' dưới {gia_max}")
    
    data = [
        {"name": "Laptop Giả 1", "price": 15000000},
        {"name": "Laptop Giả 2", "price": 18000000}
    ]
    
    return {
        "status": "success",
        "data": data
    }

