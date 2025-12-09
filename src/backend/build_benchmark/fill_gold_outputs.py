import json
import copy
import pandas as pd

from src.backend import describe_market as dm

BENCHMARK_IN_PATH = r"benchmark\benchmark_v1.json"
BENCHMARK_OUT_PATH = r"benchmark\benchmark_v1_with_gold_outputs.json"
DATA_PATH = "data/data_fixed.csv"

def load_data(path):
    df = pd.read_csv(path)
    catalog_categories = sorted(df["super_category"].dropna().astype(str).unique().tolist())
    brand_list = sorted(df["brand"].dropna().astype(str).unique().tolist())
    return df, catalog_categories, brand_list

def call_search_products_hybrid(df, catalog_categories, brand_list, tool_args):
    A = tool_args.get("A", "")
    platforms = tool_args.get("platforms", None)
    min_reviews = tool_args.get("min_reviews", 0)
    max_rows = tool_args.get("max_rows", 50)
    enforce_phrase = tool_args.get("enforce_phrase", True)

    hint = {}
    if platforms:
        hint["platforms"] = platforms

    res = dm.search_products_hybrid(
        df=df,
        A=A,
        catalog_categories=catalog_categories,
        brand_list=brand_list,
        hint=hint if hint else None,
        min_reviews=min_reviews,
        max_rows=max_rows,
        enforce_phrase=enforce_phrase,
    )
    return res

def call_fe_function(df, tool_name, tool_args):
    func = getattr(dm, tool_name)
    kw = {"df": df, "A": tool_args.get("A", "")}

    for k, v in tool_args.items():
        if k == "A":
            continue
        if v is None:
            continue
        kw[k] = v

    return func(**kw)

def process_sample(sample, df, catalog_categories, brand_list):
    gold_calls = sample.get("gold_calls", [])
    new_gold_outputs = []

    for call_spec in gold_calls:
        intent_id = call_spec.get("intent_id")
        tool_name = call_spec.get("tool_name")
        tool_args = copy.deepcopy(call_spec.get("tool_arguments", {}))

        if tool_name == "search_products_hybrid":
            output = call_search_products_hybrid(df, catalog_categories, brand_list, tool_args)
        else:
            output = call_fe_function(df, tool_name, tool_args)

        new_gold_outputs.append(
            {
                "intent_id": intent_id,
                "tool_name": tool_name,
                "tool_arguments_used": tool_args,
                "output": output,
            }
        )

    sample["gold_tool_outputs"] = new_gold_outputs
    return sample

def main():
    df, catalog_categories, brand_list = load_data(DATA_PATH)

    with open(BENCHMARK_IN_PATH, "r", encoding="utf-8") as f:
        benchmark = json.load(f)

    updated = []
    for sample in benchmark:
        updated_sample = process_sample(sample, df, catalog_categories, brand_list)
        updated.append(updated_sample)

    with open(BENCHMARK_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(updated, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
