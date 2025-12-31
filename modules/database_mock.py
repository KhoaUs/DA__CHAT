import json
from langchain.tools import tool
from typing import List, Optional

# --- HELPER KHÔNG CẦN THIẾT NHƯNG GIỮ ĐỂ TRÁNH LỖI IMPORT ---
VALID_CATS_STR = "'Headphones', 'Mobile Phones', 'Accessories'"

# --- DỮ LIỆU MOCK (KỊCH BẢN TAI NGHE) ---
# Chúng ta chuẩn bị sẵn các biến data ở đây để dùng chung

MOCK_PRICE_DATA = [
    {"platform": "Shopee", "count": 150, "min_price": 50000, "max_price": 5000000, "mean_price": 450000, "median_price": 320000, "q10": 100000, "q90": 1200000, "std_price": 200000},
    {"platform": "Lazada", "count": 120, "min_price": 60000, "max_price": 5500000, "mean_price": 480000, "median_price": 350000, "q10": 110000, "q90": 1300000, "std_price": 210000},
    {"platform": "Tiki", "count": 80, "min_price": 250000, "max_price": 8000000, "mean_price": 1200000, "median_price": 890000, "q10": 400000, "q90": 3500000, "std_price": 500000},
    {"platform": "TikTok Shop", "count": 200, "min_price": 20000, "max_price": 1500000, "mean_price": 180000, "median_price": 120000, "q10": 50000, "q90": 450000, "std_price": 80000}
]

MOCK_SALES_ITEMS = [
    {"product_name": "Tai nghe Hoco W35 Air", "price": 155000, "sold": 15000, "platform": "TikTok Shop", "seller_name": "Hoco Mall", "revenue": 2325000000},
    {"product_name": "Tai nghe Bluetooth Sony WH-1000XM5", "price": 6490000, "sold": 120, "platform": "Tiki", "seller_name": "Sony Center", "revenue": 778800000},
    {"product_name": "Apple AirPods Pro 2", "price": 5990000, "sold": 2500, "platform": "Shopee", "seller_name": "Apple Flagship", "revenue": 14975000000},
    {"product_name": "Tai nghe Mèo Cute", "price": 89000, "sold": 5000, "platform": "Shopee", "seller_name": "Xưởng Sỉ", "revenue": 445000000},
    {"product_name": "Baseus Bowie E16", "price": 259000, "sold": 5600, "platform": "Lazada", "seller_name": "Baseus Mall", "revenue": 1450400000},
    {"product_name": "Marshall Emberton II", "price": 3990000, "sold": 450, "platform": "Tiki", "seller_name": "Marshall Store", "revenue": 1795500000},
    {"product_name": "Tai nghe Gaming Zidli", "price": 350000, "sold": 300, "platform": "Shopee", "seller_name": "Gear Shop", "revenue": 105000000},
]

MOCK_REVIEW_DATA = [
    {"bucket_left": 5.0, "bucket_right": 5.0, "count": 1500, "brand": "Sony"},
    {"bucket_left": 4.0, "bucket_right": 5.0, "count": 2000, "brand": "Apple"},
    {"bucket_left": 3.0, "bucket_right": 4.0, "count": 500, "brand": "Hoco"},
    {"bucket_left": 1.0, "bucket_right": 2.0, "count": 800, "brand": "No Brand"}, # Tai nghe mèo bị chê
    {"bucket_left": 4.0, "bucket_right": 5.0, "count": 1200, "brand": "Baseus"}
]

MOCK_TOP_BRANDS = [
    {"brand": "Apple", "value": 15000000000, "platform": "Shopee", "rank": 1},
    {"brand": "Sony", "value": 8000000000, "platform": "Tiki", "rank": 2},
    {"brand": "Hoco", "value": 5000000000, "platform": "TikTok Shop", "rank": 3},
    {"brand": "Baseus", "value": 3000000000, "platform": "Lazada", "rank": 4},
    {"brand": "Marshall", "value": 2500000000, "platform": "Tiki", "rank": 5},
    {"brand": "Samsung", "value": 2000000000, "platform": "Shopee", "rank": 6},
    {"brand": "JBL", "value": 1500000000, "platform": "Lazada", "rank": 7},
    {"brand": "SoundPEATS", "value": 1000000000, "platform": "Shopee", "rank": 8},
    {"brand": "Anker", "value": 800000000, "platform": "Shopee", "rank": 9},
    {"brand": "Remax", "value": 500000000, "platform": "TikTok Shop", "rank": 10},
]

# --- CÁC TOOL GIẢ LẬP (MOCK) ---

@tool
def get_price_stats(product_name: str, platforms: Optional[List[str]] = None, category: Optional[str] = None, min_reviews: int = 0, by_platform: bool = True):
    """Phân tích thống kê giá và phân khúc giá."""
    # Trả về dữ liệu cứng luôn, không cần tính toán
    return json.dumps(MOCK_PRICE_DATA)

@tool
def get_sales_stats(product_name: str, platforms: Optional[List[str]] = None, category: Optional[str] = None, min_reviews: int = 0, top_k: int = 10):
    """Phân tích doanh số bán hàng và Top Seller."""
    
    top_sellers = [
        {"seller_name": "Apple Flagship", "platform": "Shopee", "value": 2500, "rank": 1},
        {"seller_name": "Hoco Mall", "platform": "TikTok Shop", "value": 15000, "rank": 2}, # Số lượng nhiều nhưng giá rẻ
        {"seller_name": "Sony Official", "platform": "Lazada", "value": 450, "rank": 3},
        {"seller_name": "Baseus Mall", "platform": "Lazada", "value": 5600, "rank": 4},
        {"seller_name": "Tiki Trading", "platform": "Tiki", "value": 1200, "rank": 5}
    ]
    
    return json.dumps({
        "data": {
            "raw_items": MOCK_SALES_ITEMS,
            "top_sellers": top_sellers
        }
    })

@tool
def get_review_stats(product_name: str, platforms: Optional[List[str]] = None, category: Optional[str] = None, min_reviews: int = 0, group_by_brand: bool = True):
    """Phân tích phân bố đánh giá (Rating)."""
    return json.dumps(MOCK_REVIEW_DATA)

@tool
def get_top_brands_analysis(product_name: str, platforms: Optional[List[str]] = None, category: Optional[str] = None, min_reviews: int = 0, top_k: int = 10, rank_by: str = "revenue_est", share_metric: str = "revenue_est"):
    """Phân tích Top Thương hiệu."""
    
    # Giả lập dữ liệu Brand Share (cho biểu đồ tròn/sunburst)
    brand_share = MOCK_TOP_BRANDS + [
        {"brand": "No Brand", "value": 500000000, "platform": "Shopee", "rank": 11},
        {"brand": "Khác", "value": 200000000, "platform": "Lazada", "rank": 12}
    ]
    
    return json.dumps({
        "type": "brand_analysis",
        "rank_by": rank_by,
        "share_metric": share_metric,
        "top_brands": MOCK_TOP_BRANDS,
        "brand_share": brand_share
    })

@tool
def get_advanced_market_analysis(product_name: str, platforms: Optional[List[str]] = None, category: Optional[str] = None, min_reviews: int = 0, group_roi_by: str = "platform", min_products_div: int = 5):
    """Phân tích thị trường chuyên sâu (Advanced)."""
    
    # 1. Seller Diversity (Mock cho biểu đồ Quadrant)
    seller_div = [
        {"seller_name": "Tiki Trading", "product_count": 500, "diversity_index": 4.5, "unique_categories": 20, "platform": "Tiki"}, # Đại siêu thị
        {"seller_name": "Sony Official", "product_count": 50, "diversity_index": 1.2, "unique_categories": 2, "platform": "Shopee"}, # Ông trùm ngách
        {"seller_name": "Hoco Mall", "product_count": 200, "diversity_index": 2.5, "unique_categories": 10, "platform": "TikTok Shop"},
        {"seller_name": "Shop Phụ Kiện Nhỏ", "product_count": 10, "diversity_index": 1.5, "unique_categories": 3, "platform": "Shopee"} # Tạp hóa nhỏ
    ]
    
    # 2. ROI Stats (Mock cho biểu đồ hiệu suất)
    roi_stats = [
        {"group": "Hoco", "roi_mean": 0.000025, "count": 50}, # ROI cao (Giá rẻ bán nhiều) -> Viral
        {"group": "No Brand", "roi_mean": 0.000015, "count": 100},
        {"group": "Baseus", "roi_mean": 0.000010, "count": 80},
        {"group": "Sony", "roi_mean": 0.000001, "count": 20}, # ROI thấp (Giá cao bán ít) -> Kén khách
        {"group": "Apple", "roi_mean": 0.000002, "count": 30}
    ]
    
    return json.dumps({
        "type": "advanced_analysis",
        "keyword": product_name,
        "top_brands": MOCK_TOP_BRANDS, # Dùng lại data mock ở trên
        "seller_diversity": seller_div,
        "price_range": MOCK_PRICE_DATA, # Dùng lại data giá
        "roi_stats": roi_stats
    })

@tool
def get_product_analysis(product_name: str, platforms: Optional[List[str]] = None, category: Optional[str] = None, min_reviews: int = 0):
    """Phân tích tổng hợp toàn diện."""
    
    # Gom tất cả data mock lại trả về 1 cục
    sales_stats_data = {
        "raw_items": MOCK_SALES_ITEMS,
        "top_sellers": [
            {"seller_name": "Apple Flagship", "platform": "Shopee", "value": 2500, "rank": 1},
            {"seller_name": "Hoco Mall", "platform": "TikTok Shop", "value": 15000, "rank": 2}
        ]
    }
    
    return json.dumps({
        "type": "combined_analysis",
        "product_name": product_name,
        "price_stats": MOCK_PRICE_DATA,
        "sales_stats": sales_stats_data,
        "review_stats": MOCK_REVIEW_DATA
    })

@tool
def get_category_trends(product_name: str, platforms: Optional[List[str]] = None, level: str = "categories", top_k: int = 10, min_reviews: int = 0):
    """Phân tích xu hướng danh mục sản phẩm."""
    
    # Mock data cho Treemap & Pareto
    mock_trends = [
        {"product_count": "True Wireless Headphones", "count": 450}, # Hot nhất
        {"product_count": "Over-ear Headphones", "count": 200},
        {"product_count": "Gaming Headsets", "count": 150},
        {"product_count": "Wired Earphones", "count": 80},
        {"product_count": "Bluetooth Speakers", "count": 50},
        {"product_count": "Headphone Accessories", "count": 30}
    ]
    
    return json.dumps({
        "type": "category_trends",
        "level": level,
        "data": mock_trends
    })