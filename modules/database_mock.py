import json
from langchain.tools import tool
import random

def _get_price_stats(product_name: str):
    """Lấy thống kê về giá của sản phẩm trên các sàn TMĐT.
    Trả về giá thấp nhất, trung bình, cao nhất và phân bố giá."""
    # Trong thực tế, đoạn này sẽ query SQL hoặc ElasticSearch
    return {
      "summary": {
        "lowest_price": 9500000,
        "average_price": 9850000, 
        "highest_price": 10500000, 
        "listing_count": 45
      },
      "current_price_by_platform": {
        "labels": ["Shopee", "Lazada", "Tiki", "Tiktokshop"],
        "data": [9850000, 9950000, 9700000, 9900000]
      },
      "price_distribution": {
        "labels": ["9.5M-9.7M", "9.7M-9.9M", "9.9M-10.1M", ">10.1M"],
        "data": [15, 20, 8, 2]
      },
      "top_cheapest_listings": [
        { "listing_name": "Sản phẩm A... Hàng Mới", "price": 9500000, "platform": "Tiki", "url": "http://..." },
        { "listing_name": "Sản phẩm A (Rẻ vô địch)", "price": 9550000, "platform": "Shopee", "url": "http://..." },
        { "listing_name": "Sản phẩm A 128GB", "price": 9600000, "platform": "Lazada", "url": "http://..." }
      ]
    }

def _get_sales_stats(product_name: str):
    """Lấy thống kê doanh số bán hàng, thị phần theo sàn và top shop bán chạy."""
    return {
      "summary": {
        "total_sold_all_time": 15000, 
        "best_selling_platform": "Shopee", 
        "total_revenue_estimate": 147750000000,
      },
      "sales_share_by_platform": {
        "labels": ["Shopee", "Lazada", "Tiki", "Tiktokshop"],
        "data": [8000, 4000, 1500, 1500]
      },
      "top_selling_shops_all_time": [
        { "shop_name": "Shop A (Shopee)", "total_sold": 3500 },
        { "shop_name": "Shop B (Lazada)", "total_sold": 2000 },
        { "shop_name": "Tiki Trading", "total_sold": 1500 }
      ],
      "sales_vs_price_correlation": [
        { "price": 9500000, "total_sold": 500, "listing_name": "Listing Rẻ Nhất" },
        { "price": 9700000, "total_sold": 1200, "listing_name": "Listing Khá Rẻ" },
        { "price": 9900000, "total_sold": 3500, "listing_name": "Shop A (Bán chạy)" },
        { "price": 10500000, "total_sold": 800, "listing_name": "Listing Mall Giá Cao" }
      ]
    }

def _get_review_stats(product_name: str):
    """Phân tích đánh giá khách hàng, sentiment (cảm xúc) và từ khóa nổi bật."""
    return {
      "summary": {
        "total_reviews": 5400, 
        "average_rating": 4.82, 
        "positive_sentiment_percent": 92
      },
      "rating_distribution": {
        "labels": ["5 Sao", "4 Sao", "3 Sao", "2 Sao", "1 Sao"],
        "data": [4900, 350, 100, 30, 20]
      },
      "sentiment_analysis": {
        "labels": ["Tích cực", "Tiêu cực", "Trung tính"],
        "data": [4968, 324, 108]
      },
      "positive_keywords": [
        { "word": "giao hàng nhanh", "count": 1500 },
        { "word": "chính hãng", "count": 1200 },
        { "word": "chất lượng", "count": 900 }
      ],
      "negative_keywords": [
        { "word": "hộp móp", "count": 50 },
        { "word": "pin yếu", "count": 35 },
        { "word": "chờ lâu", "count": 20 }
      ]
    }

def _generate_top_brands(keyword: str):
    """Mock data cho fe_top_brands"""
    # Giả lập các thương hiệu phổ biến
    brands = ["Apple", "Samsung", "Xiaomi", "Anker", "Baseus", "Logitech"]
    platforms = ["Shopee", "Lazada", "Tiki"]
    records = []
    
    # Tạo top 10 brand ngẫu nhiên
    for rank in range(1, 11):
        brand = brands[rank % len(brands)]
        platform = platforms[rank % len(platforms)]
        # Value giảm dần theo rank
        value = (11 - rank) * 1000000000 + random.randint(100, 500) * 1000000
        
        records.append({
            "rank": rank,
            "brand": brand,
            "platform": platform,
            "value": float(value) # Revenue estimate
        })
    return {"data": records, "meta": {"notes": "Mock data top brands"}}

def _generate_seller_diversity(keyword: str):
    """Mock data cho fe_seller_diversity_index"""
    sellers = [
        {"name": "CellphoneS Official", "plat": "Shopee", "div": 1.8, "count": 150},
        {"name": "Viettel Store", "plat": "Lazada", "div": 1.5, "count": 120},
        {"name": "Shop Phụ Kiện Giá Rẻ", "plat": "Shopee", "div": 0.4, "count": 500},
        {"name": "Tiki Trading", "plat": "Tiki", "div": 2.1, "count": 1000},
        {"name": "Apple Flagship Store", "plat": "Lazada", "div": 0.2, "count": 50}, # Chỉ bán Apple -> Diversity thấp
    ]
    
    records = []
    for s in sellers:
        records.append({
            "seller_name": s["name"],
            "platform": s["plat"],
            "product_count": s["count"],
            "unique_categories": int(s["div"] * 5) + 1,
            "diversity_index": s["div"]
        })
    return {"data": records, "meta": {"notes": "Mock seller diversity"}}

def _generate_price_range(keyword: str):
    """Mock data cho fe_price_range_by_category"""
    # Cấu trúc Box Plot: Min -> Q1 -> Median -> Q3 -> Max
    categories = [
        {"cat": "Điện thoại", "plat": "Shopee", "base": 5000000},
        {"cat": "Điện thoại", "plat": "Lazada", "base": 5200000},
        {"cat": "Phụ kiện", "plat": "Shopee", "base": 100000},
        {"cat": "Phụ kiện", "plat": "Tiki", "base": 150000},
    ]
    
    records = []
    for c in categories:
        base = c["base"]
        records.append({
            "platform": c["plat"],
            "categories": c["cat"],
            "min_price": float(base * 0.5),
            "q_low": float(base * 0.8),    # Q1
            "median_price": float(base),   # Median
            "q_high": float(base * 1.5),   # Q3
            "max_price": float(base * 3.0),
            "count": random.randint(100, 1000)
        })
    return {"data": records, "meta": {"notes": "Mock price range"}}

def _generate_roi_table(keyword: str):
    """Mock data cho fe_roi_table_for_A"""
    # ROI ở đây tính bằng Sold / Price (Hiệu suất bán trên giá)
    groups = ["Shopee", "Lazada", "Tiki", "Tiktokshop"]
    data = []
    
    for g in groups:
        # Giả sử Shopee có hiệu suất tốt nhất
        base_roi = 0.005 if g == "Shopee" else 0.002
        data.append({
            "group": g,
            "roi_mean": base_roi + random.uniform(0.0001, 0.0005),
            "roi_median": base_roi,
            "count": random.randint(500, 5000)
        })
    return {"data": data, "meta": {"notes": "Mock ROI table"}}


def _get_brand_share_stats(metric: str = "sku", normalize: bool = True):
    """Giả lập Brand Share Chart - thị phần thương hiệu theo sàn."""
    data = [
        {"platform": "Shopee", "brand": "Apple", "value": 1250, "share_pct": 28.5},
        {"platform": "Shopee", "brand": "Samsung", "value": 1100, "share_pct": 25.1},
        {"platform": "Shopee", "brand": "Xiaomi", "value": 980, "share_pct": 22.4},
        {"platform": "Shopee", "brand": "OPPO", "value": 650, "share_pct": 14.8},
        {"platform": "Shopee", "brand": "Vivo", "value": 400, "share_pct": 9.1},
        {"platform": "Lazada", "brand": "Apple", "value": 980, "share_pct": 30.2},
        {"platform": "Lazada", "brand": "Samsung", "value": 850, "share_pct": 26.2},
        {"platform": "Lazada", "brand": "Xiaomi", "value": 720, "share_pct": 22.2},
        {"platform": "Lazada", "brand": "OPPO", "value": 420, "share_pct": 12.9},
        {"platform": "Lazada", "brand": "Vivo", "value": 275, "share_pct": 8.5},
        {"platform": "Tiki", "brand": "Apple", "value": 1400, "share_pct": 35.5},
        {"platform": "Tiki", "brand": "Samsung", "value": 950, "share_pct": 24.1},
        {"platform": "Tiki", "brand": "Xiaomi", "value": 780, "share_pct": 19.8},
        {"platform": "Tiki", "brand": "OPPO", "value": 520, "share_pct": 13.2},
        {"platform": "Tiki", "brand": "Vivo", "value": 290, "share_pct": 7.4},
        {"platform": "Tiktokshop", "brand": "Xiaomi", "value": 1200, "share_pct": 32.4},
        {"platform": "Tiktokshop", "brand": "OPPO", "value": 980, "share_pct": 26.5},
        {"platform": "Tiktokshop", "brand": "Vivo", "value": 750, "share_pct": 20.3},
        {"platform": "Tiktokshop", "brand": "Samsung", "value": 520, "share_pct": 14.1},
        {"platform": "Tiktokshop", "brand": "Apple", "value": 250, "share_pct": 6.8},
    ]
    return {
        "data": data,
        "meta": {
            "filters": {"metric": metric, "normalize": normalize},
            "notes": "Mocked brand share data for demo"
        }
    }


def _get_top_sellers_stats(by: str = "sold"):
  """Giả lập Top Sellers theo tổng đã bán hoặc số sản phẩm."""
  records = [
    {"rank": 1, "seller_name": "Shop A", "platform": "Shopee", "value": 5200},
    {"rank": 2, "seller_name": "Shop B", "platform": "Lazada", "value": 4800},
    {"rank": 3, "seller_name": "Shop C", "platform": "Tiki", "value": 4300},
    {"rank": 4, "seller_name": "Shop D", "platform": "Shopee", "value": 3900},
    {"rank": 5, "seller_name": "Shop E", "platform": "Tiktokshop", "value": 3600},
    {"rank": 6, "seller_name": "Shop F", "platform": "Lazada", "value": 3300},
    {"rank": 7, "seller_name": "Shop G", "platform": "Shopee", "value": 3000},
    {"rank": 8, "seller_name": "Shop H", "platform": "Tiki", "value": 2700},
    {"rank": 9, "seller_name": "Shop I", "platform": "Shopee", "value": 2400},
    {"rank": 10, "seller_name": "Shop J", "platform": "Lazada", "value": 2100},
  ]
  return {
    "data": records,
    "meta": {
      "filters": {"by": by},
      "notes": "Mocked top sellers for demo"
    }
  }

# Giả lập database

@tool
def get_brand_share_stats(metric: str = "sku", normalize: bool = True):
    """Thị phần thương hiệu theo sàn, metric có thể là 'sku' (số sản phẩm) hoặc 'revenue_est' (doanh thu ước tính)."""
    return json.dumps(_get_brand_share_stats(metric, normalize))

@tool
def get_top_sellers_stats(by: str = "sold"):
  """Top người bán theo tổng đã bán (sold) hoặc số sản phẩm (product_count)."""
  return json.dumps(_get_top_sellers_stats(by))

# Giả lập database
@tool
def get_price_stats(product_name: str):
    """Lấy thống kê về giá của sản phẩm trên các sàn TMĐT.
    Trả về giá thấp nhất, trung bình, cao nhất và phân bố giá."""
    # Trong thực tế, đoạn này sẽ query SQL hoặc ElasticSearch
    return json.dumps(_get_price_stats(product_name))

@tool
def get_sales_stats(product_name: str):
    """Lấy thống kê doanh số bán hàng, thị phần theo sàn và top shop bán chạy."""
    return json.dumps(_get_sales_stats(product_name))

@tool
def get_review_stats(product_name: str):
    """Phân tích đánh giá khách hàng, sentiment (cảm xúc) và từ khóa nổi bật."""
    return json.dumps(_get_review_stats(product_name))

@tool
def get_product_analysis(product_name: str):
    """
    Phân tích toàn diện sản phẩm (Tổng hợp cả Giá, Doanh số và Đánh giá).
    Dùng hàm này khi người dùng hỏi chung chung: 'Phân tích iPhone 15', 'Đánh giá chi tiết sản phẩm X'.
    """
    # 1. Lấy dữ liệu Giá (Giả lập gọi logic của hàm Price)
    price_data = _get_price_stats(product_name)

    # 2. Lấy dữ liệu Doanh số
    sales_data = _get_sales_stats(product_name)

    # 3. Lấy dữ liệu Review
    review_data = _get_review_stats(product_name)

    # 4. Đóng gói tất cả vào 1 JSON tổng
    return json.dumps({
        "type": "combined_analysis", # Đánh dấu loại dữ liệu
        "product_name": product_name,
        "price_stats": price_data,
        "sales_stats": sales_data,
        "review_stats": review_data
    })

@tool
def get_top_brands_analysis(keyword: str):
    """Phân tích Top thương hiệu (Market Share) theo doanh thu hoặc số lượng bán."""
    return json.dumps(_generate_top_brands(keyword))

@tool
def get_seller_diversity_analysis(keyword: str):
    """Phân tích chỉ số đa dạng danh mục (Diversity Index) của các người bán."""
    return json.dumps(_generate_seller_diversity(keyword))

@tool
def get_price_range_analysis(keyword: str):
    """Phân tích dải giá (Price Range), phân khúc giá theo danh mục và sàn."""
    return json.dumps(_generate_price_range(keyword))

@tool
def get_roi_analysis(keyword: str):
    """Phân tích chỉ số ROI (Tỷ lệ Bán/Giá) để đánh giá hiệu quả đầu tư."""
    return json.dumps(_generate_roi_table(keyword))

@tool
def get_advanced_market_analysis(keyword: str):
    """
    Phân tích thị trường nâng cao (Advanced Market Analysis).
    Sử dụng hàm này khi người dùng muốn đánh giá sâu về: Thương hiệu, Đối thủ (Seller), Cấu trúc giá, và Hiệu quả đầu tư (ROI).
    """
    return json.dumps({
        "type": "advanced_analysis",
        "keyword": keyword,
        "top_brands": _generate_top_brands(keyword)["data"],
        "seller_diversity": _generate_seller_diversity(keyword)["data"],
        "price_range": _generate_price_range(keyword)["data"],
        "roi_stats": _generate_roi_table(keyword)["data"]
    })