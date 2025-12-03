import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch(
    "http://localhost:9200",
    verify_certs=False, 
    ssl_show_warn=False
)

df = pd.read_csv(r"data\data_fixed.csv")
emb = np.load(r"data\product_name_embeddings.npy")

# Loại bỏ dòng header bị lẫn vào data (nếu có)
mask_valid = df["product_name"] != "product_name"
df = df[mask_valid].reset_index(drop=True)
emb = emb[mask_valid.values]

# Ép kiểu numeric cho price, sold
df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
df["sold"] = pd.to_numeric(df["sold"], errors="coerce").fillna(0)

# Các cột còn lại thay NaN bằng chuỗi rỗng
cols_other = df.columns.difference(["price", "sold"])
df[cols_other] = df[cols_other].fillna("")

if len(df) != emb.shape[0]:
    raise ValueError("Số lượng dòng trong CSV và Embeddings không khớp!")

index_name = "products_index"
vector_dim = emb.shape[1]

if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)

mapping = {
    "mappings": {
        "properties": {
            "product_name": {"type": "text"},
            "super_category": {"type": "keyword"},
            "categories": {"type": "text"},
            "brand": {"type": "keyword"},
            "platform": {"type": "keyword"},
            "price": {"type": "float"},
            "sold": {"type": "float"},
            "name_vector": {
                "type": "dense_vector",
                "dims": vector_dim,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
}

es.indices.create(index=index_name, body=mapping)
print(f"Đã tạo index '{index_name}' với vector {vector_dim} chiều.")

print("Đang đẩy dữ liệu lên Elasticsearch...")
actions = []

for i, row in df.iterrows():
    doc = {
        "_index": index_name,
        "_source": {
            "product_name": row["product_name"],
            "super_category": row["super_category"],
            "categories": row.get("categories", ""),
            "brand": row["brand"],
            "platform": row["platform"],
            "price": float(row["price"]),
            "sold": float(row["sold"]),
            "name_vector": emb[i].tolist()
        }
    }
    actions.append(doc)

    if len(actions) >= 500:
        helpers.bulk(es, actions)
        actions = []

if actions:
    helpers.bulk(es, actions)

print("Đã import dữ liệu thành công!!!!!!")
