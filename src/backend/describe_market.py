import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer


_COLUMN_MAP = {
    "name": "product_name",
    "platform": "platform",
    "category": "super_category",
    "categories": "categories",
    "brand": "brand",
    "price": "price",
    "sold": "sold",
    "rating": "rating",
    "review_count": "review_count",
    "seller_name": "seller_name",
    "sku": "sku",
    "url": "url",
}

_DEFAULT_PLATFORMS = ["Lazada", "Shopee", "Tiki", "TikTokShop", "Sendo"]

# Số lượng row tối đa dùng để RESOLVE (category/brand) – cố định để tránh nhảy lung tung giữa các fe_*
_RESOLVE_MAX_ROWS = 200

_EMB_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
_PRODUCT_EMB: Optional[np.ndarray] = None


@dataclass
class ProductResolution:
    detected_category: Optional[str]
    brand_guess: Optional[str]
    query_tokens: List[str]
    platforms: List[str]
    confidence: float
    notes: str
    product_query: str

    def to_output(self) -> Dict[str, Any]:
        return {
            "data": {
                "detected_category": self.detected_category,
                "brand_guess": self.brand_guess,
                "query_tokens": self.query_tokens,
                "platforms": self.platforms,
            },
            "meta": {
                "product_query": self.product_query,
                "confidence": self.confidence,
                "notes": self.notes,
                "filters": {
                    "platforms": self.platforms,
                    "time_window": None,
                    "brand": self.brand_guess,
                    "sku": None,
                },
                "ts_generated": _now_iso(),
            },
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def _tokenize(s: str) -> List[str]:
    return [t for t in _normalize_text(s).split() if t]


def _build_meta(
    product_query: str,
    detected_category: Optional[str],
    confidence: Optional[float],
    filters: Dict[str, Any],
    notes: str = "",
) -> Dict[str, Any]:
    return {
        "product_query": product_query,
        "detected_category": detected_category,
        "confidence": float(confidence) if confidence is not None else None,
        "filters": filters,
        "notes": notes,
        "ts_generated": _now_iso(),
    }


def _apply_platform_filter(df: pd.DataFrame, platforms: Optional[List[str]]) -> pd.DataFrame:
    col = _COLUMN_MAP["platform"]
    if platforms:
        return df[df[col].isin(platforms)]
    return df


def _apply_min_reviews(df: pd.DataFrame, min_reviews: int) -> pd.DataFrame:
    col = _COLUMN_MAP["review_count"]
    if col in df.columns and min_reviews > 0:
        reviews = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df[reviews >= min_reviews]
    return df


def _safe_column(df: pd.DataFrame, logical_name: str) -> str:
    return _COLUMN_MAP[logical_name]


def set_product_embeddings(emb: np.ndarray) -> None:
    global _PRODUCT_EMB
    _PRODUCT_EMB = emb


def hybrid_search(
    df: pd.DataFrame,
    query: str,
    detected_category: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    brand: Optional[str] = None,
    min_reviews: int = 0,
    max_rows: Optional[int] = None,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> pd.DataFrame:
    name_col = _safe_column(df, "name")
    cat_col = _safe_column(df, "category")
    cat_hier_col = _safe_column(df, "categories")
    brand_col = _safe_column(df, "brand")

    data = df

    if detected_category:
        cat_lower = detected_category.lower()
        cond_cat = data[cat_col].astype(str).str.lower().eq(cat_lower)
        if cat_hier_col in data.columns:
            cond_cat_hier = data[cat_hier_col].astype(str).str.lower().str.contains(cat_lower)
            cond = cond_cat | cond_cat_hier
        else:
            cond = cond_cat
        data = data[cond]

    data = _apply_platform_filter(data, platforms)
    data = _apply_min_reviews(data, min_reviews)

    if brand:
        brand_norm = brand.lower()
        data = data[data[brand_col].astype(str).str.lower().str.contains(brand_norm)]

    if data.empty:
        return data

    if query:
        q_tokens = set(_tokenize(query))
        q_norm = _normalize_text(query)

        def score_row(txt: str) -> float:
            tokens = set(_tokenize(txt))
            if not tokens:
                return 0.0
            overlap = len(q_tokens & tokens)
            union = len(q_tokens | tokens)
            jaccard = overlap / union if union > 0 else 0.0
            bonus = 0.0
            txt_norm = _normalize_text(txt)
            if q_norm and q_norm in txt_norm:
                bonus = 0.3
            return jaccard + bonus

        lexical_scores = data[name_col].astype(str).apply(score_row)
    else:
        lexical_scores = pd.Series(0.0, index=data.index)

    vector_scores = pd.Series(0.0, index=data.index)
    if query and _PRODUCT_EMB is not None:
        q_vec = _EMB_MODEL.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]
        idx = data.index.to_numpy()
        vec_scores_full = _PRODUCT_EMB @ q_vec
        vector_scores = pd.Series(vec_scores_full[idx], index=data.index)

    if query:
        final_scores = alpha * lexical_scores + beta * vector_scores
    else:
        final_scores = vector_scores

    data = data.assign(_hybrid_score=final_scores)
    data = data[data["_hybrid_score"] > 0].sort_values("_hybrid_score", ascending=False)

    if max_rows is not None:
        data = data.head(max_rows)

    return data.drop(columns=["_hybrid_score"])


_CATEGORY_KEYWORDS = {
    "Cameras & Drones": [
        "Security Cameras & Systems",
        "Cameras & Drones",
        "Video & Action Camcorder",
        "Cameras",
        "Compact Cameras",
        "Film Cameras",
        "Instant Cameras",
        "Camera Lenses",
        "Mirrorless Lenses",
        "IP Cameras",
        "Analog Surveillance Cameras",
        "Camera Recorders",
        "Surveillance Systems",
        "Camera Drones",
        "Action Cameras",
        "Car Motorcycle Dash Cameras",
        "Dslrs",
        "Mirrorless Cameras",
        "Camera Accessories",
        "Drones Accessories",
        "Point Shoot Cameras",
        "Action Cameras Accessories",
        "Security Cameras Systems",
        "Video Camcorders",
        "Camera Care",
    ],
    "Wearables": [
        "Smartwatches",
        "Smart Glasses",
        "Fitness Trackers",
        "Smart Watches",
        "Wearable Accessories",
    ],
    "Laptops & PCs": [
        "Laptops",
        "Desktops Computers",
        "Traditional Laptops",
        "2-in-1 Laptops",
        "Gaming Laptops",
        "MacBooks",
        "Branded Desktop Computers",
        "All-in-One Computers",
        "Gaming PCs",
        "Mini PCs",
        "Custom Desktop Computers",
        "Server Towers",
        "Laptop Stands Trays",
        "Laptop Chargers Adapters",
        "Laptop Covers Cases",
        "Laptop Batteries",
        "Pc Cases",
        "Ram",
        "Motherboards",
        "Ups Stabilizers",
        "Fans Heatsinks",
        "Power Supply Units",
        "Processors",
        "Print Servers",
        "Desktop Computers",
        "All In One Desktops",
    ],
    "Phones & Accessories": [
        "Mobiles",
        "Phones",
        "Smartphones",
        "Feature Phones",
        "Landline Phones",
        "Phone Holders Mounts",
        "Power Banks",
        "Phone Straps Charms",
        "Mobile Lenses Flashes",
        "Mobile Phone Parts",
        "Phone Batteries",
        "Sim Cards Accessories",
        "Usb Mobile Lights",
        "Usb Mobile Fans",
        "Usb Vacuums",
        "Pocket Wi Fi",
        "Mobile Phones",
    ],
    "Printers & Scanners": [
        "Printers",
        "Label Receipt Printers",
        "Laser Printers",
        "Printer Accessories",
        "Inkjet Printers",
        "Photocopiers",
        "Photo Printers",
        "Dot Matrix Printers",
        "Document Scanners",
        "Receipt Printing Paper",
        "Printing Labels",
        "Printing Paper",
        "Barcode Scanners",
        "Fax Machines",
        "Label Printers",
        "Printers Scanners",
    ],
    "Tablets & E-Readers": [
        "Tablets",
        "E-Readers",
        "Tablet Covers Cases",
        "Tablet Chargers Adapters",
        "Tablet Stands Bases",
        "Tablet Parts",
        "Tablet Keyboards",
        "Tablet Screen Protectors",
        "Tablet Bags Sleeves",
        "Writing Tablets",
        "Electronic Learning Devices",
        "Ereader Device",
        "Digital Smart Pens",
        "Reading Pens Devices",
        "Electronic Notebooks",
    ],
    "Gaming & VR": [
        "Console Gaming",
        "Game Consoles",
        "Console Accessories",
        "Game Discs",
        "Other Game Consoles",
        "Nintendo Consoles",
        "Xbox Consoles",
        "Game Controllers",
        "Game Control Devices",
        "VR Accessories",
        "Virtual Reality Devices",
        "Vr Devices",
        "Home Games Consoles",
        "Handheld Games Consoles",
        "Video Games",
    ],
    "Monitors": [
        "Monitors",
        "Standard Monitors",
        "Portable Monitors",
        "Gaming Monitors",
        "Graphic Monitors",
    ],
    "Audio Devices": [
        "Audio",
        "Headphones",
        "Speakers",
        "Wired In-Ear Headphones",
        "Wired On-Ear Headphones",
        "Wired Over-Ear Headphones",
        "Wired Headphones",
        "Bluetooth In-Ear Headphones",
        "True Wireless Earbuds",
        "Bluetooth Over-Ear Headphones",
        "Bluetooth On-Ear Headphones",
        "Bluetooth Headsets",
        "Computer Speakers",
        "Portable Speakers",
        "Bluetooth Speakers",
        "Bluetooth Computer Speakers",
        "Portable Trolley Speakers",
        "Hi-Fi Speakers",
        "Mobile Microphones",
        "Bluetooth Karaoke Microphones",
        "Computer Microphones",
        "Music Players",
        "Voice Recorders",
        "Streaming Devices",
        "Radio Cassette Players",
        "Receivers Amplifiers Mixers",
        "Stage Karaoke Microphones",
        "Audio DAC Converters",
        "Headphones Earphones Accessories",
        "Mp3 Mp4 Players",
        "Home Cinema Systems",
        "Cd Dvd Players",
        "Walkie Talkies",
        "Av Receivers",
        "Microphones",
        "Audio Video Accessories",
        "Amplifiers Mixers",
        "Refurbished Audio Video",
        "Conference Video Audio Devices",
    ],
    "Storage": [
        "Memory Cards",
        "Compact Discs",
        "Ssd",
        "Micro Sd Cards",
        "Hard Drives",
        "Hard Disk Enclosures Docking Stations",
        "Network Attached Storage Nas",
        "Sound Cards",
        "Optical Drives",
        "Graphics Cards",
    ],
    "Accessories": [
        "TV Accessories",
        "Accessories",
        "Projector Accessories",
        "Cases Screen Protectors Stickers",
        "Cables Chargers Adapters",
        "Selfie Accessories",
        "Gps Finders Accessories",
        "Universal Battery Chargers",
        "Styluses",
        "Education Device Parts Accessories",
        "Flash Drives Otg Cables",
        "Keyboards Mice",
        "Mouse Pads",
        "Usb Hubs Card Readers",
        "Webcams",
        "Keyboard Trackpad Covers",
        "Cooling Pads",
        "Cables Accessories",
        "Network Cables Connectors",
        "Wireless Adapters Network Cards",
        "Powerline Adapters",
    ],
    "Smart Home": [
        "Control Devices",
        "Smart Home Controls",
        "Smart Motion Sensors",
        "Temperature Control Systems",
        "Automatic Curtain Control Systems",
    ],
    "Office Equipment": [
        "Projectors",
        "Paper Shredders",
        "Time Attendance Machines",
        "Money Counters",
        "Casting Devices",
        "E Dictionaries",
    ],
    "Networking": [
        "Repeaters",
        "Modems Wireless Routers",
        "Kvm Switches",
        "Network Switches Poe",
    ],
}

_BRAND_KEYWORDS: Dict[str, str] = {
    "iphone": "Apple",
    "ipad": "Apple",
    "macbook": "Apple",
    "airpods": "Apple",
    "imac": "Apple",
    "samsung": "Samsung",
    "galaxy": "Samsung",
    "xiaomi": "Xiaomi",
    "oppo": "OPPO",
    "vivo": "Vivo",
    "realme": "Realme",
    "huawei": "Huawei",
}


def resolve_product(
    A: str,
    catalog_categories: List[str],
    brand_list: List[str],
    df: pd.DataFrame,
    hint: Optional[Dict[str, Any]] = None,
    max_rows: int = 200,
) -> Dict[str, Any]:

    query = A or ""
    tokens = _tokenize(query)

    hint = dict(hint or {})
    platforms = hint.get("platforms") or _DEFAULT_PLATFORMS
    min_reviews = int(hint.get("min_reviews", 0))

    # ❗ Không tự đoán brand hoặc category
    hint_brand = hint.get("brand")
    hint_category = hint.get("category")

    # ❗ CHỈ DÙNG HINT
    detected_category = hint_category if hint_category in catalog_categories else None
    brand_guess = hint_brand if hint_brand in brand_list else None

    # ❗ Tính confidence rất nhỏ vì ta không đoán
    confidence = 0.1
    notes_parts = []

    # Hybrid search chỉ để xem có hit hay không (không dùng để đoán brand/category)
    hits = hybrid_search(
        df=df,
        query=A,
        detected_category=None,
        platforms=platforms,
        brand=None,
        min_reviews=min_reviews,
        max_rows=max_rows,
    )

    if not hits.empty:
        notes_parts.append("hybrid_search_hits")
        confidence += 0.1

    # Không đoán category từ hits
    # Không đoán brand từ hits
    # Không dò keyword

    if hint_category:
        notes_parts.append(f"category_from_hint={hint_category}")

    if hint_brand:
        notes_parts.append(f"brand_from_hint={hint_brand}")

    if not notes_parts:
        notes_parts.append("no_hits")

    notes = "resolve_product; " + "; ".join(notes_parts)

    result = ProductResolution(
        detected_category=detected_category,
        brand_guess=brand_guess,
        query_tokens=tokens,
        platforms=platforms,
        confidence=confidence,
        notes=notes,
        product_query=A,
    )
    return result.to_output()



def _search_df_core(
    df: pd.DataFrame,
    A: str,
    catalog_categories: List[str],
    brand_list: List[str],
    hint: Optional[Dict[str, Any]] = None,
    min_reviews: int = 0,
    max_rows: int = 500,
    enforce_phrase: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    hint = dict(hint or {})
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    # ❗ Quan trọng: luôn dùng _RESOLVE_MAX_ROWS để resolve category/brand
    resolution = resolve_product(
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        df=df,
        hint=hint,
        max_rows=_RESOLVE_MAX_ROWS,
    )

    # ❗ Dùng đúng HINT, không dùng predicted brand/category
    detected_category = hint.get("category")
    brand_guess = hint.get("brand")

    platforms = resolution["data"]["platforms"] or _DEFAULT_PLATFORMS

    if "platforms" in hint and hint["platforms"]:
        platforms = hint["platforms"]
    if "category" in hint and hint["category"]:
        detected_category = hint["category"]
    if "brand" in hint and hint["brand"]:
        brand_guess = hint["brand"]

    df_hits = hybrid_search(
        df=df,
        query=A,
        detected_category=detected_category,
        platforms=platforms,
        brand=brand_guess,
        min_reviews=hint.get("min_reviews", min_reviews),
        max_rows=max_rows * 3,
        alpha=0.5,
        beta=0.5,
    )

    name_col = _safe_column(df_hits, "name")

    if enforce_phrase and A:
        q_norm = _normalize_text(A)

        def has_phrase(txt: str) -> bool:
            return q_norm in _normalize_text(str(txt))

        df_hits = df_hits[df_hits[name_col].apply(has_phrase)]

    if max_rows is not None and not df_hits.empty:
        df_hits = df_hits.head(max_rows)

    filters_meta = {
        "platforms": platforms,
        "time_window": None,
        "brand": brand_guess,
        "sku": None,
        "min_reviews": hint.get("min_reviews", min_reviews),
    }

    confidence = resolution["meta"]["confidence"]
    notes = resolution["meta"]["notes"] + f"; hybrid_search + phrase_filter={bool(enforce_phrase)}"

    meta = _build_meta(
        product_query=A,
        detected_category=detected_category,
        confidence=confidence,
        filters=filters_meta,
        notes=notes,
    )
    meta["brand_guess"] = brand_guess

    return df_hits, meta


def search_products_hybrid(
    df: pd.DataFrame,
    A: str,
    catalog_categories: List[str],
    brand_list: List[str],
    hint: Optional[Dict[str, Any]] = None,
    min_reviews: int = 0,
    max_rows: int = 50,
    enforce_phrase: bool = True,
) -> Dict[str, Any]:
    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=max_rows,
        enforce_phrase=enforce_phrase,
    )

    records: List[Dict[str, Any]] = []
    for _, row in df_hits.iterrows():
        records.append(
            {
                "sku": row.get("sku"),
                "product_name": row.get("product_name"),
                "platform": row.get("platform"),
                "super_category": row.get("super_category"),
                "categories": row.get("categories"),
                "brand": row.get("brand"),
                "price": float(row.get("price", 0) or 0),
                "sold": float(row.get("sold", 0) or 0),
                "rating": float(row.get("rating", 0) or 0),
                "review_count": int(row.get("review_count", 0) or 0),
                "seller_name": row.get("seller_name"),
                "url": row.get("url"),
            }
        )

    return {
        "data": records,
        "meta": meta,
    }


def fe_describe_price(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    min_reviews: int = 0,
    by_platform: bool = True,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=500,
        enforce_phrase=True,
    )

    price_col = _safe_column(df_hits, "price")
    platform_col = _safe_column(df_hits, "platform")

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    def agg(group: pd.DataFrame) -> Dict[str, Any]:
        prices = pd.to_numeric(group[price_col], errors="coerce").dropna()
        if prices.empty:
            return {
                "min_price": 0.0,
                "q10": 0.0,
                "median_price": 0.0,
                "mean_price": 0.0,
                "q90": 0.0,
                "max_price": 0.0,
                "std_price": 0.0,
                "count": 0,
            }
        return {
            "min_price": float(prices.min()),
            "q10": float(np.quantile(prices, 0.1)),
            "median_price": float(np.median(prices)),
            "mean_price": float(prices.mean()),
            "q90": float(np.quantile(prices, 0.9)),
            "max_price": float(prices.max()),
            "std_price": float(prices.std(ddof=1)) if len(prices) > 1 else 0.0,
            "count": int(len(prices)),
        }

    if by_platform:
        rows = []
        for platform, g in df_hits.groupby(platform_col):
            s = agg(g)
            s["platform"] = platform
            rows.append(s)
        data = rows
    else:
        s = agg(df_hits)
        data = [s]

    meta["notes"] += "; fe_describe_price over search subset"
    return {"data": data, "meta": meta}


def fe_rating_distribution(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    bins: int = 20,
    group_by_brand: bool = True,
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    rating_col = _safe_column(df_hits, "rating")
    brand_col = _safe_column(df_hits, "brand")

    df_hits = df_hits.dropna(subset=[rating_col])
    ratings = pd.to_numeric(df_hits[rating_col], errors="coerce").dropna()
    if ratings.empty:
        meta["notes"] += "; no rating data"
        meta["bin_edges"] = []
        return {"data": [], "meta": meta}

    bin_edges = np.linspace(ratings.min(), ratings.max(), bins + 1)

    records: List[Dict[str, Any]] = []

    if group_by_brand:
        for brand, g in df_hits.groupby(brand_col):
            r = pd.to_numeric(g[rating_col], errors="coerce").dropna().values
            if len(r) == 0:
                continue
            counts, edges = np.histogram(r, bins=bin_edges)
            for i in range(len(edges) - 1):
                if counts[i] == 0:
                    continue
                records.append(
                    {
                        "bucket_left": float(edges[i]),
                        "bucket_right": float(edges[i + 1]),
                        "count": int(counts[i]),
                        "brand": brand,
                    }
                )
    else:
        counts, edges = np.histogram(ratings.values, bins=bin_edges)
        for i in range(len(edges) - 1):
            if counts[i] == 0:
                continue
            records.append(
                {
                    "bucket_left": float(edges[i]),
                    "bucket_right": float(edges[i + 1]),
                    "count": int(counts[i]),
                    "brand": None,
                }
            )

    meta["notes"] += "; fe_rating_distribution over search subset"
    meta["bin_edges"] = [float(x) for x in bin_edges]
    return {"data": records, "meta": meta}


def fe_sold_distribution(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    bins: Any = (0, 10, 50, 100, 500, 1000, 5000, 10000),
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    sold_col = _safe_column(df_hits, "sold")
    platform_col = _safe_column(df_hits, "platform")

    df_hits = df_hits.dropna(subset=[sold_col])
    if df_hits.empty:
        meta["notes"] += "; no sold data"
        meta["bin_edges"] = []
        return {"data": [], "meta": meta}

    sold_values = pd.to_numeric(df_hits[sold_col], errors="coerce").dropna()
    if isinstance(bins, int):
        bin_edges = np.linspace(sold_values.min(), sold_values.max(), bins + 1)
    else:
        bin_edges = np.array(list(bins), dtype=float)

    records: List[Dict[str, Any]] = []
    for platform, g in df_hits.groupby(platform_col):
        s = pd.to_numeric(g[sold_col], errors="coerce").dropna().values
        total_count = len(s)
        if total_count == 0:
            continue
        counts, edges = np.histogram(s, bins=bin_edges)
        for i in range(len(edges) - 1):
            if counts[i] == 0:
                continue
            pct = counts[i] / total_count
            records.append(
                {
                    "platform": platform,
                    "bin_left": float(edges[i]),
                    "bin_right": float(edges[i + 1]),
                    "count": int(counts[i]),
                    "pct": float(pct),
                }
            )

    meta["notes"] += "; fe_sold_distribution over search subset"
    meta["bin_edges"] = [float(x) for x in bin_edges]
    return {"data": records, "meta": meta}


def fe_category_count_plot(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    sublevel_field: str = "categories",
    top_k: Optional[int] = None,
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    if sublevel_field not in _COLUMN_MAP:
        raise ValueError(f"sublevel_field '{sublevel_field}' not in column map")

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    sub_col = _safe_column(df_hits, sublevel_field)

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    counts = (
        df_hits[sub_col]
        .astype(str)
        .value_counts()
        .reset_index()
        .rename(columns={"index": sub_col, sub_col: "product_count"})
    )

    if top_k is not None:
        counts = counts.head(top_k)

    data = counts.to_dict("records")
    meta["notes"] += "; fe_category_count_plot over search subset"
    return {"data": data, "meta": meta}


def fe_brand_share_chart(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    metric: str = "sku",
    normalize: bool = True,
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    price_col = _safe_column(df_hits, "price")
    sold_col = _safe_column(df_hits, "sold")
    brand_col = _safe_column(df_hits, "brand")
    platform_col = _safe_column(df_hits, "platform")

    df_hits = df_hits.copy()
    if metric == "revenue_est":
        price = pd.to_numeric(df_hits[price_col], errors="coerce").fillna(0)
        sold = pd.to_numeric(df_hits[sold_col], errors="coerce").fillna(0)
        df_hits["metric_value"] = price * sold
    else:
        df_hits["metric_value"] = 1.0

    grouped = (
        df_hits.groupby([platform_col, brand_col], dropna=False)["metric_value"]
        .sum()
        .reset_index()
    )

    data: List[Dict[str, Any]] = []
    for platform, g in grouped.groupby(platform_col):
        total = g["metric_value"].sum()
        for _, row in g.iterrows():
            value = float(row["metric_value"])
            if normalize and total > 0:
                share_pct = value / total * 100.0
            else:
                share_pct = None
            data.append(
                {
                    "platform": platform,
                    "brand": row[brand_col],
                    "value": value,
                    "share_pct": float(share_pct) if share_pct is not None else None,
                }
            )

    meta["notes"] += f"; fe_brand_share_chart metric={metric} over search subset"
    return {"data": data, "meta": meta}


def fe_top_sellers(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    by: str = "product_count",
    top_k: int = 20,
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    seller_col = _safe_column(df_hits, "seller_name")
    platform_col = _safe_column(df_hits, "platform")
    sold_col = _safe_column(df_hits, "sold")

    if by == "sold":
        grouped = (
            df_hits.groupby([platform_col, seller_col], dropna=False)[sold_col]
            .apply(lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum())
            .reset_index(name="value")
        )
    else:
        grouped = (
            df_hits.groupby([platform_col, seller_col], dropna=False)[seller_col]
            .count()
            .reset_index(name="value")
        )

    records: List[Dict[str, Any]] = []
    for platform, g in grouped.groupby(platform_col):
        g_sorted = g.sort_values("value", ascending=False).head(top_k)
        for rank, (_, row) in enumerate(g_sorted.iterrows(), start=1):
            records.append(
                {
                    "rank": rank,
                    "seller_name": row[seller_col],
                    "platform": platform,
                    "value": float(row["value"]),
                }
            )

    meta["notes"] += f"; fe_top_sellers by={by} over search subset"
    return {"data": records, "meta": meta}


def fe_top_brands(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    by: str = "revenue_est",
    top_k: int = 20,
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    brand_col = _safe_column(df_hits, "brand")
    platform_col = _safe_column(df_hits, "platform")
    price_col = _safe_column(df_hits, "price")
    sold_col = _safe_column(df_hits, "sold")

    df_hits = df_hits.copy()
    if by == "sold":
        df_hits["metric_value"] = pd.to_numeric(df_hits[sold_col], errors="coerce").fillna(0)
    else:
        price = pd.to_numeric(df_hits[price_col], errors="coerce").fillna(0)
        sold = pd.to_numeric(df_hits[sold_col], errors="coerce").fillna(0)
        df_hits["metric_value"] = price * sold

    grouped = (
        df_hits.groupby([platform_col, brand_col], dropna=False)["metric_value"]
        .sum()
        .reset_index()
        .rename(columns={"metric_value": "value"})
    )

    records: List[Dict[str, Any]] = []
    for platform, g in grouped.groupby(platform_col):
        g_sorted = g.sort_values("value", ascending=False).head(top_k)
        for rank, (_, row) in enumerate(g_sorted.iterrows(), start=1):
            records.append(
                {
                    "rank": rank,
                    "brand": row[brand_col],
                    "platform": platform,
                    "value": float(row["value"]),
                }
            )

    meta["notes"] += f"; fe_top_brands by={by} over search subset"
    return {"data": records, "meta": meta}


def fe_seller_diversity_index(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    min_products: int = 5,
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    seller_col = _safe_column(df_hits, "seller_name")
    platform_col = _safe_column(df_hits, "platform")
    cat_col = _safe_column(df_hits, "category")

    records: List[Dict[str, Any]] = []
    for (platform, seller), g in df_hits.groupby([platform_col, seller_col], dropna=False):
        product_count = len(g)
        if product_count < min_products:
            continue
        cat_counts = g[cat_col].astype(str).value_counts()
        unique_categories = len(cat_counts)

        total = cat_counts.sum()
        p = cat_counts.values / total
        diversity_index = float(-(p * np.log(p + 1e-12)).sum())

        records.append(
            {
                "seller_name": seller,
                "platform": platform,
                "product_count": int(product_count),
                "unique_categories": int(unique_categories),
                "diversity_index": diversity_index,
            }
        )

    meta["notes"] += "; fe_seller_diversity_index over search subset"
    return {"data": records, "meta": meta}


def fe_price_range_by_category(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    brand: Optional[str] = None,
    quantiles: Tuple[float, float] = (0.1, 0.9),
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if brand:
        hint["brand"] = brand
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    price_col = _safe_column(df_hits, "price")
    platform_col = _safe_column(df_hits, "platform")
    cat_col = _safe_column(df_hits, "categories")

    q_low, q_high = quantiles

    records: List[Dict[str, Any]] = []
    for (platform, cat), g in df_hits.groupby([platform_col, cat_col]):
        prices = pd.to_numeric(g[price_col], errors="coerce").dropna()
        if prices.empty:
            continue
        records.append(
            {
                "platform": platform,
                "categories": cat,
                "min_price": float(prices.min()),
                "q_low": float(np.quantile(prices, q_low)),
                "median_price": float(np.median(prices)),
                "q_high": float(np.quantile(prices, q_high)),
                "max_price": float(prices.max()),
                "count": int(len(prices)),
            }
        )

    meta["notes"] += "; fe_price_range_by_category over search subset"
    return {"data": records, "meta": meta}


def fe_roi_table_for_A(
    df: pd.DataFrame,
    A: str,
    platforms: Optional[List[str]] = None,
    group_by: str = "platform",
    min_reviews: int = 0,
    hint: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    hint = dict(hint or {})
    if platforms:
        hint["platforms"] = platforms
    if "min_reviews" not in hint:
        hint["min_reviews"] = min_reviews

    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())

    df_hits, meta = _search_df_core(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint,
        min_reviews=min_reviews,
        max_rows=2000,
        enforce_phrase=True,
    )

    if df_hits.empty:
        meta["notes"] += "; no data"
        return {"data": [], "meta": meta}

    price_col = _safe_column(df_hits, "price")
    sold_col = _safe_column(df_hits, "sold")
    platform_col = _safe_column(df_hits, "platform")
    seller_col = _safe_column(df_hits, "seller_name")
    brand_col = _safe_column(df_hits, "brand")

    if group_by == "seller":
        group_col = seller_col
    elif group_by == "brand":
        group_col = brand_col
    else:
        group_col = platform_col

    df_hits = df_hits.copy()
    price = pd.to_numeric(df_hits[price_col], errors="coerce").replace(0, np.nan)
    sold = pd.to_numeric(df_hits[sold_col], errors="coerce")
    df_hits["roi"] = sold / price
    df_hits = df_hits.replace([np.inf, -np.inf], np.nan).dropna(subset=["roi"])

    grouped = df_hits.groupby(group_col, dropna=False)["roi"]
    stats = grouped.agg(["mean", "median", "count"]).reset_index()

    data: List[Dict[str, Any]] = []
    for _, row in stats.iterrows():
        data.append(
            {
                "group": row[group_col],
                "roi_mean": float(row["mean"]),
                "roi_median": float(row["median"]),
                "count": int(row["count"]),
            }
        )

    meta["notes"] += f"; fe_roi_table_for_A group_by={group_by} over search subset"
    return {"data": data, "meta": meta}
