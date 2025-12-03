# search_es.py
import pandas as pd
from elasticsearch import Elasticsearch
from describe_market import resolve_product 

es = Elasticsearch(
    "http://localhost:9200",
    verify_certs=False, 
    ssl_show_warn=False
)
index_name = "products_index"

df = pd.read_csv(r"data\data_fixed.csv")
catalog_categories = sorted(df["super_category"].dropna().unique().tolist())
brand_list = sorted(df["brand"].dropna().unique().tolist())

query_text = "iPhone SE"

resolution = resolve_product(
    A=query_text,
    catalog_categories=catalog_categories,
    brand_list=brand_list,
    df=df,
    hint={"platforms": ["Lazada"]},
)

print("=== RESOLUTION ===")
print(resolution)

platforms = resolution["data"]["platforms"]

must_clauses = []
filter_clauses = []

# Dùng match_phrase để bắt đúng cụm "iPhone SE"
must_clauses.append({
    "match_phrase": {
        "product_name": query_text
    }
})

# Chỉ filter theo platform
if platforms:
    filter_clauses.append({"terms": {"platform": platforms}})

base_query = {
    "query": {
        "bool": {
            "must": must_clauses,
            "filter": filter_clauses
        }
    }
}

all_hits = []
page_size = 100
from_ = 0

while True:
    es_query = dict(base_query)
    es_query["from"] = from_
    es_query["size"] = page_size

    res = es.search(index=index_name, body=es_query)
    hits = res["hits"]["hits"]

    if not hits:
        break

    all_hits.extend(hits)

    if len(hits) < page_size:
        break

    from_ += page_size

# Lọc thêm ở Python để chắc chắn product_name chứa "iphone se"
filtered_hits = []
q_norm = query_text.lower()
for h in all_hits:
    name = str(h["_source"].get("product_name", ""))
    if q_norm in name.lower():
        filtered_hits.append(h)

print(f"\n=== ELASTICSEARCH RESULTS (total={len(filtered_hits)} rows) ===")

for rank, hit in enumerate(filtered_hits, start=1):
    row = hit["_source"]
    print(
        f"[{rank:03d}] "
        f"{row.get('platform', '')} | "
        f"{row.get('super_category', '')} | "
        f"{row.get('product_name', '')} | "
        f"brand={row.get('brand', '')} | "
        f"price={row.get('price', '')} | "
        f"sold={row.get('sold', '')} | "
        f"score={hit.get('_score', '')}"
    )
