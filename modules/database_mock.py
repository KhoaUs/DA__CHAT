import json
from langchain.tools import tool

# Giả lập database
@tool
def get_price_stats(product_name: str):
    """Lấy thống kê về giá của sản phẩm trên các sàn TMĐT.
    Trả về giá thấp nhất, trung bình, cao nhất và phân bố giá."""
    # Trong thực tế, đoạn này sẽ query SQL hoặc ElasticSearch
    return json.dumps({
      "summary": {
        "lowest_price": 9500000, "average_price": 9850000, "highest_price": 10500000, "listing_count": 45
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
        { "listing_name": "Sản phẩm A... Hàng Mới", "price": 9500000, "platform": "Tiki", "url": "http://tiki..." },
        { "listing_name": "Sản phẩm A (Rẻ vô địch)", "price": 9550000, "platform": "Shopee", "url": "http://shopee..." }
      ]
    })

@tool
def get_sales_stats(product_name: str):
    """Lấy thống kê doanh số bán hàng, thị phần theo sàn và top shop bán chạy."""
    return json.dumps({
      "summary": {
        "total_sold_all_time": 15000, "best_selling_platform": "Shopee", "total_revenue_estimate": 147750000000,
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
        { "price": 9500000, "total_sold": 500 }, { "price": 9700000, "total_sold": 1200 },
        { "price": 9900000, "total_sold": 3500 }, { "price": 10500000, "total_sold": 800 }
      ]
    })

@tool
def get_review_stats(product_name: str):
    """Phân tích đánh giá khách hàng, sentiment (cảm xúc) và từ khóa nổi bật."""
    return json.dumps({
      "summary": {
        "total_reviews": 5400, "average_rating": 4.82, "positive_sentiment_percent": 92
      },
      "rating_distribution": {
        "labels": ["5 Sao", "4 Sao", "3 Sao", "2 Sao", "1 Sao"],
        "data": [4900, 350, 100, 30, 20]
      },
      "sentiment_analysis": {
        "labels": ["Tích cực", "Tiêu cực", "Trung tính"],
        "data": [4968, 324, 108]
      }
    })

@tool
def get_product_analysis(product_name: str):
    """
    Phân tích toàn diện sản phẩm (Tổng hợp cả Giá, Doanh số và Đánh giá).
    Dùng hàm này khi người dùng hỏi chung chung: 'Phân tích iPhone 15', 'Đánh giá chi tiết sản phẩm X'.
    """
    # 1. Lấy dữ liệu Giá (Giả lập gọi logic của hàm Price)
    price_data = {
      "summary": { "lowest_price": 9500000, "average_price": 9850000, "highest_price": 10500000, "listing_count": 45 },
      "current_price_by_platform": { "labels": ["Shopee", "Lazada", "Tiki", "Tiktokshop"], "data": [9850000, 9950000, 9700000, 9900000] },
      "price_distribution": { "labels": ["9.5M-9.7M", "9.7M-9.9M", "9.9M-10.1M", ">10.1M"], "data": [15, 20, 8, 2] }
    }

    # 2. Lấy dữ liệu Doanh số
    sales_data = {
      "summary": { "total_sold_all_time": 15000, "best_selling_platform": "Shopee", "total_revenue_estimate": 147750000000 },
      "sales_share_by_platform": { "labels": ["Shopee", "Lazada", "Tiki", "Tiktokshop"], "data": [8000, 4000, 1500, 1500] },
      "top_selling_shops_all_time": [ { "shop_name": "Shop A (Shopee)", "total_sold": 3500 }, { "shop_name": "Shop B (Lazada)", "total_sold": 2000 }, { "shop_name": "Tiki Trading", "total_sold": 1500 } ]
    }

    # 3. Lấy dữ liệu Review
    review_data = {
      "summary": { "total_reviews": 5400, "average_rating": 4.82, "positive_sentiment_percent": 92 },
      "rating_distribution": { "labels": ["5 Sao", "4 Sao", "3 Sao", "2 Sao", "1 Sao"], "data": [4900, 350, 100, 30, 20] },
      "sentiment_analysis": { "labels": ["Tích cực", "Tiêu cực", "Trung tính"], "data": [4968, 324, 108] }
    }

    # 4. Đóng gói tất cả vào 1 JSON tổng
    return json.dumps({
        "type": "combined_analysis", # Đánh dấu loại dữ liệu
        "product_name": product_name,
        "price_stats": price_data,
        "sales_stats": sales_data,
        "review_stats": review_data
    })