import pandas as pd
import numpy as np
from pprint import pprint
import re

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


DATA_CSV = r"data\data_fixed.csv"
EMB_NPY = r"data\product_name_embeddings.npy"


def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def load_data():
    df = pd.read_csv(DATA_CSV)
    emb = np.load(EMB_NPY)

    mask_valid = df["product_name"] != "product_name"
    df = df[mask_valid].reset_index(drop=True)
    emb = emb[mask_valid.values]

    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["sold"] = pd.to_numeric(df["sold"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce").fillna(0).astype(int)

    cols_other = df.columns.difference(["price", "sold", "rating", "review_count"])
    df[cols_other] = df[cols_other].fillna("")

    return df, emb


def show_sample_products(records, k=5):
    for i, r in enumerate(records[:k], start=1):
        print(
            f"[{i:02d}] {r.get('platform','')} | "
            f"{r.get('brand','')} | "
            f"{r.get('product_name','')} | "
            f"price={r.get('price')} | sold={r.get('sold')} | rating={r.get('rating')}"
        )


def main():
    print_section("LOAD DATA & EMBEDDINGS")
    df, emb = load_data()
    print(f"Rows: {len(df)}, Emb dim: {emb.shape[1]}")
    print(f"Distinct super_category: {df['super_category'].nunique()}, brand: {df['brand'].nunique()}")
    set_product_embeddings(emb)

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    query = "iPhone SE"
    hint = {"platforms": ["Lazada"]}

    print_section("RESOLVE_PRODUCT")
    res = resolve_product(
        A=query,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        df=df,
        hint=hint,
        max_rows=200,
    )
    pprint(res)

    print_section("SEARCH_PRODUCTS_HYBRID – CHECK PHRASE MATCH")
    search_result = search_products_hybrid(
        df=df,
        A=query,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=0,
        max_rows=50,
        enforce_phrase=True,
    )
    data = search_result["data"]
    meta = search_result["meta"]

    print(f"Total products returned: {len(data)}")
    print("Meta:")
    pprint(meta)
    print("\nSample results:")
    show_sample_products(data, k=10)

    q_norm = " ".join(query.lower().split())
    bad = []
    for r in data:
        name = str(r.get("product_name", "")).lower()
        name_norm = " ".join(re.split(r"[^a-z0-9]+", name))
        if q_norm not in name_norm:
            bad.append((name, name_norm))
    if bad:
        print("\n[WARNING] Có product không chứa đúng cụm query sau normalize:")
        for name, name_norm in bad[:5]:
            print("  raw:", name)
            print("  norm:", name_norm)
    else:
        print("\nAll returned products contain phrase:", q_norm)

    print_section("fe_describe_price")
    out_price = fe_describe_price(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        min_reviews=0,
        by_platform=True,
        hint=None,
    )
    pprint(out_price["meta"])
    print("Data:")
    pprint(out_price["data"])

    print_section("fe_rating_distribution")
    out_rating = fe_rating_distribution(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        bins=10,
        group_by_brand=True,
        min_reviews=0,
        hint=None,
    )
    pprint(out_rating["meta"])
    print(f"Number of buckets: {len(out_rating['data'])}")
    print("Sample buckets:")
    pprint(out_rating["data"][:10])

    print_section("fe_sold_distribution")
    out_sold = fe_sold_distribution(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        bins=(0, 10, 50, 100, 500, 1000, 5000, 10000),
        min_reviews=0,
        hint=None,
    )
    pprint(out_sold["meta"])
    print(f"Number of buckets: {len(out_sold['data'])}")
    print("Sample buckets:")
    pprint(out_sold["data"][:10])

    print_section("fe_category_count_plot")
    out_cat = fe_category_count_plot(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        sublevel_field="categories",
        top_k=10,
        min_reviews=0,
        hint=None,
    )
    pprint(out_cat["meta"])
    print("Top categories:")
    pprint(out_cat["data"])

    print_section("fe_brand_share_chart")
    out_share = fe_brand_share_chart(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        metric="revenue_est",
        normalize=True,
        min_reviews=0,
        hint=None,
    )
    pprint(out_share["meta"])
    print(f"Records: {len(out_share['data'])}")
    print("Sample:")
    pprint(out_share["data"][:10])

    print_section("fe_top_sellers")
    out_sellers = fe_top_sellers(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        by="sold",
        top_k=10,
        min_reviews=0,
        hint=None,
    )
    pprint(out_sellers["meta"])
    print("Top sellers:")
    pprint(out_sellers["data"])

    print_section("fe_top_brands")
    out_brands = fe_top_brands(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        by="revenue_est",
        top_k=10,
        min_reviews=0,
        hint=None,
    )
    pprint(out_brands["meta"])
    print("Top brands:")
    pprint(out_brands["data"])

    print_section("fe_seller_diversity_index")
    out_div = fe_seller_diversity_index(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        min_products=3,
        min_reviews=0,
        hint=None,
    )
    pprint(out_div["meta"])
    print(f"Records: {len(out_div['data'])}")
    print("Sample:")
    pprint(out_div["data"][:10])

    print_section("fe_price_range_by_category")
    out_price_range = fe_price_range_by_category(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        brand=None,
        quantiles=(0.1, 0.9),
        min_reviews=0,
        hint=None,
    )
    pprint(out_price_range["meta"])
    print("Sample:")
    pprint(out_price_range["data"][:10])

    print_section("fe_roi_table_for_A")
    out_roi = fe_roi_table_for_A(
        df=df,
        A=query,
        platforms=["Lazada", "Shopee"],
        group_by="platform",
        min_reviews=0,
        hint=None,
    )
    pprint(out_roi["meta"])
    print("ROI table:")
    pprint(out_roi["data"])


if __name__ == "__main__":
    main()
