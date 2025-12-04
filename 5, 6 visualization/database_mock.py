import json
from langchain.tools import tool

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


