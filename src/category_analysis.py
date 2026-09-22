"""
商品类目分析模块.

基于订单商品明细表(items)分析各商品类目的销售表现.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from data_loader import load_raw_data, clean_order_items

def analyze_category_sales(items_df, top_n=10):
    """分析各商品类目的销售额和订单量(基于商品明细, 一个订单多件商品只算一次订单)."""
    category_stats = items_df.groupby("category_en").agg(
        order_count=("order_id", "nunique"),
        revenue=("price", "sum"),
    ).reset_index()

    category_stats["revenue_share"] = (category_stats["revenue"] / category_stats["revenue"].sum() * 100).round(2)
    category_stats = category_stats.sort_values("revenue", ascending=False).head(top_n)

    print(f"\n=== Top {top_n} 商品类目 ===")
    print(category_stats.to_string(index=False))

    return category_stats


if __name__ == "__main__":
    data = load_raw_data()
    items = clean_order_items(data["order_items"], data["products"], data["category_translation"])
    category_stats = analyze_category_sales(items)