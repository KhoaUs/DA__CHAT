import json
from langchain.tools import tool
from modules.data_loader import get_data_engine
from typing import List, Dict, Any, Optional, Tuple
from modules.analytics_core import (
    fe_describe_price, fe_sold_distribution, fe_rating_distribution,
    fe_top_brands, fe_seller_diversity_index, fe_price_range_by_category,
    fe_roi_table_for_A, fe_category_count_plot, fe_top_sellers, fe_brand_share_chart,
    search_products_hybrid
)

# --- HELPER: Tự động convert kết quả sang JSON ---
def to_json(result_dict):
    # Hàm này giúp xử lý các object NumPy (int64, float32) thành chuẩn Python để JSON không lỗi
    def convert(o):
        if isinstance(o, (int, float)): return o
        if hasattr(o, 'item'): return o.item() # Numpy scalar
        if hasattr(o, 'tolist'): return o.tolist() # Numpy array
        return str(o)
    return json.dumps(result_dict, default=convert, ensure_ascii=False)

# --- 2. HELPER: LẤY DANH MỤC HỢP LỆ ĐỂ DẠY AI ---
def get_valid_categories_string():
    """Lấy danh sách các Super Category từ dữ liệu để đưa vào Prompt cho AI"""
    try:
        df = get_data_engine()
        if df is not None and not df.empty:
            # Lấy các category duy nhất, loại bỏ None/NaN
            cats = sorted(df["super_category"].dropna().astype(str).unique().tolist())
            # Ghép thành chuỗi: "Điện thoại, Máy tính bảng, Phụ kiện..."
            return ", ".join([f"'{c}'" for c in cats])
    except Exception:
        pass
    return "Không xác định"

# Lưu danh sách này vào biến toàn cục để dùng trong docstring
VALID_CATS_STR = get_valid_categories_string()

# --- TOOL DEFINITIONS ---

@tool
def get_price_stats(product_name: str, platforms: Optional[List[str]] = None, category: Optional[str] = None, min_reviews: int = 0, by_platform: bool = True):
    """
    SỬ DỤNG KHI: Phân tích CÁC CHỈ SỐ VỀ GIÁ. Chỉ gọi tool này khi người dùng quan tâm đến: giá rẻ nhất, giá đắt nhất, giá trung bình, biến động giá, hoặc so sánh giá giữa các sàn.
    KHÔNG SỬ DỤNG KHI: người dùng hỏi "Tình hình kinh doanh", "Bán chạy không".
    Args:
        product_name: Tên sản phẩm hoặc từ khóa tìm kiếm (VD: "iPhone 15").
        platforms: Danh sách các sàn muốn lọc (VD: ["Shopee", "Lazada"]). Nếu tìm tất cả thì để None hoặc rỗng.
        category: Dự đoán danh mục chính (Super Category) của sản phẩm để tìm kiếm chính xác hơn.
                  Các danh mục hợp lệ trong hệ thống: {VALID_CATS_STR}.
                  Ví dụ: Nếu user hỏi "iPhone", hãy điền 'Phones & Accessories' (hoặc tên tương ứng trong list trên).
        min_reviews: (ưu tiên để min_reviews = 0 nếu người dùng không để cập)
        by_platform: Set True nếu người dùng muốn so sánh giá giữa các sàn. Set False nếu muốn xem giá trung bình gộp chung toàn thị trường.
    """
    df = get_data_engine()
    
    # Logic xử lý default cho platforms nếu AI truyền None
    target_platforms = platforms
    if not target_platforms:
        # Mặc định tìm trên 4 sàn lớn nếu không chỉ định cụ thể
        target_platforms = ["Shopee", "Lazada", "Tiki", "TikTok Shop"]

    # Đóng gói hint
    hint = {"category": category} if category else None

    # Gọi hàm core với đúng tham số
    result = fe_describe_price(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        min_reviews=min_reviews,
        by_platform=by_platform,
        hint=hint
    )
    
    return to_json(result)

@tool
def get_sales_stats(
    product_name: str, 
    platforms: Optional[List[str]] = None, 
    category: Optional[str] = None,
    min_reviews: int = 0, 
    top_k: int = 10
):
    """
    SỬ DỤNG KHI: Phân tích NGƯỜI BÁN (SELLER/SHOP) và SẢN PHẨM CỤ THỂ. Dùng để tìm Top Shop bán chạy, danh sách sản phẩm bán tốt nhất, hoặc xem phân bố lượng đã bán (Sold count).
    KHÔNG SỬ DỤNG KHI: người dùng hỏi về "Thị phần thương hiệu" (Ví dụ: Thị phần của Samsung -> Phải dùng get_top_brands_analysis).
    
    Args:
        product_name: Tên sản phẩm hoặc từ khóa tìm kiếm.
        platforms: Danh sách các sàn muốn lọc (VD: ["Shopee", "TikTok Shop"]). Nếu tìm tất cả thì để None.
        category: Danh mục chính của sản phẩm (Super Category). Chọn từ: {VALID_CATS_STR}.
        min_reviews: Số lượng đánh giá tối thiểu để lọc bỏ shop ảo/rác(ưu tiên để min_reviews = 0 nếu người dùng không để cập)
        top_k: Số lượng người bán hàng đầu muốn lấy (VD: 5 để lấy Top 5 Shop). Mặc định là 10.
    """
    df = get_data_engine()
    
    target_platforms = platforms if platforms else ["Shopee", "Lazada", "Tiki", "TikTok Shop"]

    # Đóng gói hint
    hint = {"category": category} if category else None
    # 1. Lấy Top Seller (Giữ nguyên)
    top_sellers = fe_top_sellers(
        df, A=product_name, platforms=target_platforms, 
        by="sold", top_k=top_k, min_reviews=min_reviews, hint=hint
    )
    
    # 2. [MỚI] Lấy danh sách 20 sản phẩm liên quan nhất để vẽ Scatter Plot
    # Dùng hàm search_products_hybrid để lấy raw data
    raw_products = search_products_hybrid(
        df, A=product_name, 
        platforms=target_platforms, 
        min_reviews=min_reviews,
        max_rows=20, # Lấy mẫu sản phẩm để vẽ biểu đồ 
        hint=hint
    )

    return to_json({
        "data": {
            # Thay vì trả về distribution (đã gom nhóm), ta trả về raw items
            "raw_items": raw_products.get("data"), 
            "top_sellers": top_sellers.get("data")
        }
    })


@tool
def get_review_stats(
    product_name: str, 
    platforms: Optional[List[str]] = None, 
    category: Optional[str] = None,
    min_reviews: int = 0, 
    group_by_brand: bool = True
):
    """
    SỬ DỤNG KHI: Phân tích CHẤT LƯỢNG và ĐÁNH GIÁ (Star Ratings). Dùng để xem phân bố sao (1-5 sao), tỉ lệ hài lòng của khách hàng.
    
    Args:
        product_name: Tên sản phẩm hoặc từ khóa tìm kiếm.
        platforms: Danh sách các sàn muốn lọc. Nếu tìm tất cả thì để None.
        category: Danh mục chính của sản phẩm (Super Category). Chọn từ: {VALID_CATS_STR}.
        min_reviews: Số lượng đánh giá tối thiểu để đảm bảo độ tin cậy (min_reviews: (ưu tiên để min_reviews = 0 nếu người dùng không để cập)
        group_by_brand: True nếu muốn chia tách phân bố sao theo từng Thương hiệu riêng biệt (VD: so sánh xem Apple hay Samsung được đánh giá cao hơn). False nếu muốn xem tổng quan phân bố sao của toàn bộ thị trường gộp chung.
    """
    df = get_data_engine()
    
    # Xử lý mặc định cho platforms
    target_platforms = platforms
    if not target_platforms:
        target_platforms = ["Shopee", "Lazada", "Tiki", "TikTok Shop"]

    # Đóng gói hint
    hint = {"category": category} if category else None

    result = fe_rating_distribution(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        group_by_brand=group_by_brand,
        min_reviews=min_reviews,
        hint=hint
    )
    
    return to_json(result)

@tool
def get_top_brands_analysis(
    product_name: str, 
    platforms: Optional[List[str]] = None, 
    category: Optional[str] = None,
    min_reviews: int = 0,
    top_k: int = 10,
    rank_by: str = "revenue_est",
    share_metric: str = "revenue_est"
):
    """
    SỬ DỤNG KHI: Phân tích THƯƠNG HIỆU (BRAND) và THỊ PHẦN (MARKET SHARE). Dùng để xếp hạng các hãng sản xuất, xem hãng nào chiếm doanh thu cao nhất (Revenue Share) hoặc phủ sóng rộng nhất (SKU Share).
    
    Args:
        product_name: Tên sản phẩm hoặc từ khóa tìm kiếm.
        platforms: Danh sách các sàn muốn lọc. Nếu tìm tất cả thì để None.
        min_reviews: Số lượng đánh giá tối thiểu (ưu tiên để min_reviews = 0 nếu người dùng không để cập)
        category: Danh mục chính (Super Category). Chọn từ: {VALID_CATS_STR}.
        top_k: Số lượng thương hiệu hàng đầu muốn lấy (VD: Top 10).
        rank_by: Tiêu chí để xếp hạng Top Brand. 
                 - "revenue_est": Xếp hạng theo Tổng Doanh Thu (Tiền). (Mặc định)
                 - "sold": Xếp hạng theo Tổng Số Lượng Bán (Cái). Dùng khi muốn tìm hãng bán chạy nhất về số lượng (phổ thông).
        share_metric: Tiêu chí để vẽ biểu đồ tròn Thị Phần (Brand Share).
                 - "revenue_est": Thị phần theo Doanh Thu (Ai kiếm được nhiều tiền nhất). (Mặc định)
                 - "sku": Thị phần theo Số lượng mã sản phẩm (Ai đăng nhiều bài bán nhất/Độ phủ listing).
    """
    df = get_data_engine()
    
    # Xử lý mặc định cho platforms
    target_platforms = platforms
    if not target_platforms:
        target_platforms = ["Shopee", "Lazada", "Tiki", "TikTok Shop"]
        
    # Đóng gói hint
    hint = {"category": category} if category else None

    # 1. Top Brands (List/Bar Chart)
    # rank_by mapping vào tham số 'by' của hàm core
    top_brands = fe_top_brands(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        by=rank_by, # <--- Tham số dynamic ("revenue_est" hoặc "sold")
        top_k=top_k,
        min_reviews=min_reviews, 
        hint=hint
    )
    
    # 2. Brand Share (Pie Chart)
    # share_metric mapping vào tham số 'metric' của hàm core
    brand_share = fe_brand_share_chart(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        metric=share_metric, # <--- Tham số dynamic ("revenue_est" hoặc "sku")
        min_reviews=min_reviews, 
        hint=hint
    )
    
    return to_json({
        "type": "brand_analysis",
        "rank_by": rank_by,       # Trả về để UI biết tiêu đề nên ghi là Doanh thu hay Số lượng
        "share_metric": share_metric,
        "top_brands": top_brands.get("data"),
        "brand_share": brand_share.get("data")
    })


@tool
def get_advanced_market_analysis(
    product_name: str, 
    platforms: Optional[List[str]] = None, 
    category: Optional[str] = None,
    min_reviews: int = 0,
    group_roi_by: str = "platform",
    min_products_div: int = 2
):
    """
    SỬ DỤNG KHI: Cần phân tích CHUYÊN SÂU 360 ĐỘ dành cho mục đích KINH DOANH/ĐẦU TƯ. Cung cấp các chỉ số phức tạp: ROI (Hiệu suất đầu tư), Seller Diversity (Độ cạnh tranh của người bán), Phân tích ngách thị trường.
    KHÔNG SỬ DỤNG KHI: Không dùng cho câu hỏi đơn giản như "Giá bao nhiêu".
    
    Args:
        product_name: Tên sản phẩm hoặc từ khóa tìm kiếm.
        platforms: Danh sách các sàn muốn lọc. Nếu tìm tất cả thì để None.
        category: Danh mục chính (Super Category). Chọn từ: {VALID_CATS_STR}.
        min_reviews: Số lượng đánh giá tối thiểu.((ưu tiên để min_reviews = 0 nếu người dùng không để cập))
        group_roi_by: Tiêu chí nhóm để tính ROI (Hiệu suất Sold/Price).
                      - "platform": So sánh hiệu quả giữa các sàn (VD: TikTok vs Shopee sàn nào bán tốt hơn?). (Mặc định)
                      - "brand": So sánh hiệu quả giữa các hãng.
                      - "seller": So sánh hiệu quả giữa các người bán.
        min_products_div: Số lượng sản phẩm tối thiểu của 1 shop để được đưa vào phân tích độ đa dạng (Diversity). Giúp lọc bỏ các shop nhỏ lẻ. Mặc định là 5.
    """
    df = get_data_engine()
    
    # Xử lý mặc định cho platforms
    target_platforms = platforms
    if not target_platforms:
        target_platforms = ["Shopee", "Lazada", "Tiki", "TikTok Shop"]

    # Đóng gói hint
    hint = {"category": category} if category else None

    # 1. Top Brands (Cần thiết cho Tab 1 của Dashboard Advanced)
    top_brands = fe_top_brands(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        by="revenue_est", 
        min_reviews=min_reviews,
        hint=hint
    )

    # 2. Seller Diversity (Độ đa dạng danh mục của Shop)
    seller_div = fe_seller_diversity_index(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        min_products=min_products_div, 
        min_reviews=min_reviews,
        hint=hint
    )

    # 3. Price Range (Phân khúc giá Boxplot)
    price_range = fe_price_range_by_category(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        min_reviews=min_reviews, 
        hint=hint
    )

    # 4. ROI Table (Hiệu suất đầu tư)
    roi_table = fe_roi_table_for_A(
        df, 
        A=product_name, 
        platforms=target_platforms, 
        group_by=group_roi_by, 
        min_reviews=min_reviews, 
        hint=hint
    )
    
    return to_json({
        "type": "advanced_analysis",
        "keyword": product_name,
        "top_brands": top_brands.get("data"),
        "seller_diversity": seller_div.get("data"),
        "price_range": price_range.get("data"),
        "roi_stats": roi_table.get("data")
    })

@tool
def get_product_analysis(
    product_name: str, 
    platforms: Optional[List[str]] = None, 
    category: Optional[str] = None,
    min_reviews: int = 0
):
    """
    SỬ DỤNG KHI: Công cụ BÁO CÁO TỔNG HỢP (All-in-One). Chỉ sử dụng khi người dùng yêu cầu "Review tổng thể", "Phân tích A-Z", hoặc câu hỏi chung chung không rõ ý định cụ thể. Nó sẽ gọi gộp cả Giá, Doanh số và Đánh giá.
    
    Args:
        product_name: Tên sản phẩm hoặc từ khóa tìm kiếm.
        platforms: Danh sách các sàn muốn lọc. Nếu tìm tất cả thì để None.
        category: Danh mục chính (Super Category). Chọn từ: {VALID_CATS_STR}.
        min_reviews: Số lượng đánh giá tối thiểu để lọc bỏ sản phẩm rác/ảo. (min_reviews: (ưu tiên để min_reviews = 0 nếu người dùng không để cập))
    """
    df = get_data_engine()
    
    # Xử lý mặc định cho platforms
    target_platforms = platforms if platforms else ["Shopee", "Lazada", "Tiki", "TikTok Shop"]
    # Đóng gói hint
    hint = {"category": category} if category else None

    # 1. PRICE (Mặc định bật by_platform=True để so sánh)
    price = fe_describe_price(
        df, A=product_name, platforms=target_platforms, 
        min_reviews=min_reviews, by_platform=True, hint=hint
    )
    
    # 2. SALES (Lấy Raw Items cho Scatter & Top 5 Sellers)
    # Chúng ta tự động set top_k=5 và max_rows=10 cho báo cáo tổng hợp để không bị quá tải
    raw_products = search_products_hybrid(
        df, A=product_name, platforms=target_platforms, 
        min_reviews=min_reviews, max_rows=10, hint=hint
    )
    top_sellers = fe_top_sellers(
        df, A=product_name, platforms=target_platforms, 
        by="sold", top_k=5, min_reviews=min_reviews, hint=hint
    )
    sales_stats_data = {
        "raw_items": raw_products.get("data"),
        "top_sellers": top_sellers.get("data")
    }
    
    # 3. REVIEW (Mặc định bật group_by_brand=True)
    rating = fe_rating_distribution(
        df, A=product_name, platforms=target_platforms, 
        min_reviews=min_reviews, group_by_brand=True, hint=hint
    )
    
    return to_json({
        "type": "combined_analysis",
        "product_name": product_name,
        "price_stats": price.get("data"),
        "sales_stats": sales_stats_data, 
        "review_stats": rating.get("data")
    })

@tool
def get_category_trends(
    product_name: str, 
    platforms: Optional[List[str]] = None, 
    level: str = "categories",
    top_k: int = 10,
    min_reviews: int = 0
):
    """
    SỬ DỤNG KHI: Dùng để xác định XU HƯỚNG DANH MỤC. Giúp trả lời câu hỏi: "Từ khóa này chủ yếu trả về loại sản phẩm gì?", "Người dùng đang tìm kiếm phụ kiện hay máy chính?".
    
    Args:
        product_name: Từ khóa tìm kiếm.
        platforms: Danh sách sàn.
        level: Cấp độ danh mục muốn phân tích.
               - "category": Danh mục lớn (Super Category). VD: "Điện thoại & Phụ kiện".
               - "categories": Danh mục chi tiết (Sub Category). VD: "Ốp lưng", "Cáp sạc". (Mặc định)
        top_k: Lấy Top bao nhiêu danh mục phổ biến nhất.
        min_reviews: Lọc bỏ sản phẩm ít đánh giá. min_reviews: (ưu tiên để min_reviews = 0 nếu người dùng không để cập)
    """
    df = get_data_engine()
    
    # Xử lý mặc định
    target_platforms = platforms if platforms else ["Shopee", "Lazada", "Tiki", "TikTok Shop"]

    result = fe_category_count_plot(
        df,
        A=product_name,
        platforms=target_platforms,
        sublevel_field=level, # Map tham số level vào sublevel_field
        top_k=top_k,
        min_reviews=min_reviews
    )
    
    return to_json({
        "type": "category_trends",
        "level": level,
        "data": result.get("data")
    })