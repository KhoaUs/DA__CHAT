import pandas as pd
import numpy as np
import os
from modules.analytics_core import set_product_embeddings

# Biến toàn cục để lưu cache
_CACHED_DF = None

def get_data_engine():
    """
    Hàm này load dữ liệu, xử lý preprocessing và nạp embedding.
    Nó chỉ chạy 1 lần, các lần sau sẽ trả về biến đã cache.
    """
    global _CACHED_DF
    
    if _CACHED_DF is not None:
        return _CACHED_DF

    # Đường dẫn file (Lấy đường dẫn tuyệt đối để tránh lỗi path)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_CSV = os.path.join(BASE_DIR, "data", "data_fixed.csv")
    EMB_NPY = os.path.join(BASE_DIR, "data", "product_name_embeddings.npy")

    print(f"⏳ Đang nạp dữ liệu từ: {DATA_CSV}")
    
    try:
        # 1. Load CSV & Numpy
        df = pd.read_csv(DATA_CSV)
        emb = np.load(EMB_NPY)

        # 2. Preprocessing (Logic từ file test của bạn)
        # Loại bỏ dòng tiêu đề lặp lại nếu có
        mask_valid = df["product_name"] != "product_name"
        df = df[mask_valid].reset_index(drop=True)
        emb = emb[mask_valid.values]

        # Chuyển đổi kiểu dữ liệu số
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
        df["sold"] = pd.to_numeric(df["sold"], errors="coerce").fillna(0)
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce") # Rating có thể để NaN
        df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").fillna(0).astype(int)

        # Điền chuỗi rỗng cho các cột khác
        cols_other = df.columns.difference(["price", "sold", "rating", "review_count"])
        df[cols_other] = df[cols_other].fillna("")

        # 3. Nạp Embeddings vào Core
        print(f"✅ Đã nạp {len(df)} dòng dữ liệu. Kích thước Emb: {emb.shape}")
        set_product_embeddings(emb)

        # Lưu vào cache
        _CACHED_DF = df
        return _CACHED_DF

    except Exception as e:
        print(f"❌ LỖI LOAD DATA: {e}")
        # Trả về DF rỗng để app không bị crash
        return pd.DataFrame()

# import pandas as pd
# import streamlit as st

# # Sử dụng decorator cache của Streamlit để không phải load lại file mỗi lần reload web
# @st.cache_resource
# def get_data_engine():
#     """
#     Load dữ liệu từ file CSV và chuẩn hóa tên cột.
#     Đảm bảo các cột quan trọng (price, sold, rating) luôn tồn tại.
#     """
#     try:
#         # 1. Đọc file CSV 
#         df = pd.read_csv("data/data_fixed.csv")
        
#         # 2. Map tên cột (Chuẩn hóa về tên tiếng Anh thống nhất)
#         # Sửa các key bên trái cho khớp với tên cột trong file CSV của bạn
#         column_mapping = {
#             "name": "product_name",
#             "title": "product_name",
            
#             "price": "price",
#             "price_min": "price", # Nếu có nhiều loại giá
            
#             "sold": "sold",
#             "historical_sold": "sold",
#             "sales": "sold",
            
#             "rating": "rating",
#             "rating_star": "rating", # <--- FIX LỖI TẠI ĐÂY
#             "stars": "rating",
#             "item_rating": "rating",
            
#             "platform": "platform",
#             "brand": "brand",
#             "seller_name": "seller_name",
#             "shop_name": "seller_name",
            
#             "review_count": "review_count",
#             "total_review": "review_count",
            
#             "sku": "sku",
#             "itemid": "sku",
            
#             "url": "url",
#             "link": "url",
            
#             "super_category": "super_category",
#             "category": "categories" # Sub-category
#         }
        
#         # Đổi tên cột
#         df = df.rename(columns=column_mapping)
        
#         # 3. Xử lý dữ liệu (Làm sạch)
#         # Đảm bảo các cột số là dạng số
#         for col in ['price', 'sold', 'rating', 'review_count']:
#             if col in df.columns:
#                 df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
#             else:
#                 # Nếu thiếu cột quan trọng, tạo cột giả định = 0 để tránh lỗi code
#                 df[col] = 0 
                
#         # Đảm bảo cột rating nằm trong khoảng 0-5
#         if 'rating' in df.columns:
#             df['rating'] = df['rating'].clip(0, 5)

#         # Xử lý text
#         text_cols = ['product_name', 'brand', 'platform', 'super_category', 'categories']
#         for col in text_cols:
#             if col in df.columns:
#                 df[col] = df[col].astype(str).fillna("Unknown")
#             else:
#                 df[col] = "Unknown"

#         return df

#     except Exception as e:
#         st.error(f"❌ Lỗi khi load dữ liệu: {e}")
#         return pd.DataFrame() # Trả về bảng rỗng để app không bị crash