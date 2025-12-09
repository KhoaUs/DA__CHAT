import pandas as pd
import numpy as np
import re
from pprint import pprint

from describe_market import (
    set_product_embeddings,
    resolve_product,
    search_products_hybrid,
    fe_describe_price,
    fe_rating_distribution,
    fe_sold_distribution,
    fe_category_count_plot,
    fe_brand_share_chart,
    fe_top_sellers,
    fe_top_brands,
    fe_seller_diversity_index,
    fe_price_range_by_category,
    fe_roi_table_for_A,
)

DATA_CSV = r"Data\data_fixed.csv"
EMB_NPY = r"Data\product_name_embeddings.npy"


# =====================================================
# UTILITIES
# =====================================================

def print_section(title: str):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def normalize_name(name: str) -> str:
    return " ".join(re.split(r"[^a-z0-9]+", name.lower()))


def phrase_check(records, query: str):
    q_norm = normalize_name(query)
    for r in records:
        norm_name = normalize_name(str(r.get("product_name", "")))
        if q_norm not in norm_name:
            print(f"✗ Phrase mismatch → {r.get('product_name')}")
            return
    print(f"✓ Phrase check passed → '{q_norm}'")


def preview(records, k=5):
    for i, r in enumerate(records[:k], start=1):
        print(
            f"[{i:02d}] {r.get('platform','')} | {r.get('brand','')} | "
            f"{r.get('product_name','')} | price={r.get('price')} | sold={r.get('sold')} | rating={r.get('rating')}"
        )


# =====================================================
# LOAD DATA
# =====================================================

def load_data():
    df = pd.read_csv(DATA_CSV)
    emb = np.load(EMB_NPY)

    df = df[df["product_name"] != "product_name"].reset_index(drop=True)
    emb = emb[df.index.values]

    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["sold"] = pd.to_numeric(df["sold"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").fillna(0).astype(int)

    df[df.columns] = df[df.columns].fillna("")

    return df, emb


# =====================================================
# RUN TESTS
# =====================================================

def run_full_fe_tests(df, catalog_categories, brand_list, query, HINT, case_name):

    print_section(f"CASE: {case_name} — resolve_product")
    res = resolve_product(
        A=query,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        df=df,
        hint=HINT,
    )
    pprint(res)

    print_section(f"CASE: {case_name} — search_products_hybrid")
    out = search_products_hybrid(
        df=df,
        A=query,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=HINT,
        max_rows=50,
        enforce_phrase=True,
    )
    pprint(out["meta"])
    preview(out["data"])
    phrase_check(out["data"], query)

    records = out["data"]

    # =============== FE TEST TABLE ===============
    FE_FUNCTIONS = [
        ("fe_describe_price", fe_describe_price, {"by_platform": True}),
        ("fe_rating_distribution", fe_rating_distribution, {"bins": 10}),
        ("fe_sold_distribution", fe_sold_distribution, {}),
        ("fe_category_count_plot", fe_category_count_plot, {"sublevel_field": "categories", "top_k": 10}),
        ("fe_brand_share_chart", fe_brand_share_chart, {"metric": "revenue_est"}),
        ("fe_top_sellers", fe_top_sellers, {"by": "sold", "top_k": 10}),
        ("fe_top_brands", fe_top_brands, {"by": "revenue_est", "top_k": 10}),
        ("fe_seller_diversity_index", fe_seller_diversity_index, {"min_products": 3}),
        ("fe_price_range_by_category", fe_price_range_by_category, {"quantiles": (0.1, 0.9)}),
        ("fe_roi_table_for_A", fe_roi_table_for_A, {"group_by": "platform"}),
    ]

    # Running all FE functions
    for title, func, kwargs in FE_FUNCTIONS:
        print_section(f"{case_name} — {title}")
        out = func(df=df, A=query, hint=HINT, **kwargs)
        pprint(out["meta"])
        print(f"Records: {len(out['data'])}")
        preview(out["data"])


# =====================================================
# MAIN
# =====================================================

def main():

    print_section("LOAD DATA")
    df, emb = load_data()
    set_product_embeddings(emb)

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique())
    brand_list = sorted(df["brand"].dropna().astype(str).unique())

    print(f"Rows: {len(df)}, Emb dim: {emb.shape[1]}")
    print(f"Categories: {len(catalog_categories)}, Brands: {len(brand_list)}")

    query = "iPhone 17"

    # =====================================================
    # CASE 1 — NO BRAND/CATEGORY
    # =====================================================
    HINT1 = {
        "platforms": ["Tiki", "TikTok Shop"]
    }

    run_full_fe_tests(
        df=df,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        query=query,
        HINT=HINT1,
        case_name="CASE 1 (NO BRAND/CATEGORY)"
    )

    # =====================================================
    # CASE 2 — WITH brand + category
    # =====================================================
    HINT2 = {
        "platforms": ["Tiki", "TikTok Shop"],
        "brand": "Apple",
        "category": "Phones & Accessories"
    }

    run_full_fe_tests(
        df=df,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        query=query,
        HINT=HINT2,
        case_name="CASE 2 (WITH BRAND/CATEGORY)"
    )

    print_section("DONE")


if __name__ == "__main__":
    main()
