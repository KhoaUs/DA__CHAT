# import json
# import pandas as pd
# from src.backend.describe_market import search_products_hybrid

# BENCHMARK_IN = r"benchmark\benchmark_search.json"
# BENCHMARK_OUT = r"benchmark\benchmark_search_with_pred.json"
# DATA_PATH = "Data/data_fixed.csv"


# def load_data():
#     df = pd.read_csv(DATA_PATH)
#     catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
#     brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())
#     return df, catalog_categories, brand_list


# def run_hybrid_search(df, catalog_categories, brand_list, item):
#     import math

#     query = item["query"]
#     filters = item.get("filters", {})

#     # Extract filters
#     platforms = filters.get("platforms")
#     min_reviews = filters.get("min_reviews", 0)

#     # Build hint for search
#     hint = {}
#     if platforms:
#         hint["platforms"] = platforms
#     if filters.get("brand"):
#         hint["brand"] = filters["brand"]
#     if filters.get("category"):
#         hint["category"] = filters["category"]
#     if min_reviews:
#         hint["min_reviews"] = min_reviews

#     res = search_products_hybrid(
#         df=df,
#         A=query,
#         catalog_categories=catalog_categories,
#         brand_list=brand_list,
#         hint=hint if hint else None,
#         min_reviews=min_reviews,
#         max_rows=30,
#         enforce_phrase=True
#     )

#     # FIX SKU PROPERLY
#     pred_skus = []
#     for r in res["data"]:
#         sku = r.get("sku", "")

#         # Convert NaN or float to string safely
#         if sku is None or (isinstance(sku, float) and math.isnan(sku)):
#             pred_skus.append("")
#         else:
#             pred_skus.append(str(sku))

#     return pred_skus



# def main():
#     df, catalog_categories, brand_list = load_data()

#     with open(BENCHMARK_IN, "r", encoding="utf-8") as f:
#         benchmark = json.load(f)

#     updated = []

#     for item in benchmark:
#         pred_result = run_hybrid_search(df, catalog_categories, brand_list, item)
#         item["pred_result"] = pred_result
#         updated.append(item)
#         print(f"[DONE] {item['id']} → {len(pred_result)} results")

#     with open(BENCHMARK_OUT, "w", encoding="utf-8") as f:
#         json.dump(updated, f, ensure_ascii=False, indent=2)

#     print("\n== FINISHED ==")
#     print(f"Saved to: {BENCHMARK_OUT}")


# if __name__ == "__main__":
#     main()
import json
import pandas as pd
import math
from src.backend.describe_market import search_products_hybrid

BENCHMARK_IN = r"benchmark\benchmark_search.json"
BENCHMARK_OUT = r"benchmark\benchmark_search_with_pred.json"
DATA_PATH = "Data/data_fixed.csv"


def load_data():
    df = pd.read_csv(DATA_PATH)
    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())
    return df, catalog_categories, brand_list


# --------------------------
#  FIX: SKU NORMALIZATION
# --------------------------
def safe_sku_to_str(x):
    """Convert SKU safely to a clean string."""
    if x is None:
        return ""

    s = str(x).strip()

    # Remove .0 from floats
    if s.endswith(".0"):
        s = s[:-2]

    # Convert scientific notation
    # Example: "1.73e+18" → "1730000000000000000"
    if "e" in s.lower():
        try:
            s = str(int(float(s)))
        except:
            pass

    return s


def run_hybrid_search(df, catalog_categories, brand_list, item):
    query = item["query"]
    filters = item.get("filters", {})

    platforms = filters.get("platforms")
    min_reviews = filters.get("min_reviews", 0)

    hint = {}
    if platforms:
        hint["platforms"] = platforms
    if filters.get("brand"):
        hint["brand"] = filters["brand"]
    if filters.get("category"):
        hint["category"] = filters["category"]
    if min_reviews:
        hint["min_reviews"] = min_reviews

    res = search_products_hybrid(
        df=df,
        A=query,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint if hint else None,
        min_reviews=min_reviews,
        max_rows=30,
        enforce_phrase=True
    )

    # FIX SKU properly
    pred_skus = []
    for r in res["data"]:
        sku = r.get("sku", None)
        pred_skus.append(safe_sku_to_str(sku))

    return pred_skus


def main():
    df, catalog_categories, brand_list = load_data()

    with open(BENCHMARK_IN, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    updated = []

    for item in benchmark:
        pred_result = run_hybrid_search(df, catalog_categories, brand_list, item)
        item["pred_result"] = pred_result
        updated.append(item)
        print(f"[DONE] {item['id']} → {len(pred_result)} results")

    with open(BENCHMARK_OUT, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

    print("\n== FINISHED ==")
    print(f"Saved to: {BENCHMARK_OUT}")


if __name__ == "__main__":
    main()
