"""
同期群分析模块.

按客户首次购买月份分组,
追踪各同期群的留存率和复购行为, 以及RFM客户价值分析.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from data_loader import load_raw_data, create_master_orders


def analyze_cohort(orders_df):
    """找出每个客户的首次购买月份, 按月份分组."""
    first_purchase = orders_df.groupby("customer_unique_id")["purchase_month"].min().reset_index()
    first_purchase.columns = ["customer_unique_id", "cohort_month"]

    print("\n=== 同期群分组 ===")
    print(first_purchase["cohort_month"].value_counts().sort_index())

    return first_purchase


def calculate_retention(orders_df, first_purchase):
    """计算各同期群每月的留存率."""
    orders_df = orders_df.merge(first_purchase[["customer_unique_id", "cohort_month"]], on="customer_unique_id", how="left")

    orders_df["cohort_index"] = orders_df["purchase_month"].astype("int64") - orders_df["cohort_month"].astype("int64")

    retention = orders_df.groupby(["cohort_month", "cohort_index"])["customer_unique_id"].nunique().reset_index(name="users")
    retention = retention.pivot(index="cohort_month", columns="cohort_index", values="users")

    retention_rate = retention.div(retention[0], axis=0).round(4) * 100

    print("\n=== 留存率表 ===")
    print(retention_rate.to_string())

    return retention_rate


def analyze_repurchase(orders_df):
    """分析整体复购率."""
    customer_orders = orders_df.groupby("customer_unique_id")["order_id"].nunique()
    total_customers = len(customer_orders)
    repeat_customers = (customer_orders > 1).sum()
    repurchase_rate = repeat_customers / total_customers * 100

    print("\n=== 复购率分析 ===")
    print(f"总客户数: {total_customers}")
    print(f"复购客户数: {repeat_customers}")
    print(f"复购率: {repurchase_rate:.2f}%")

    return {"total_customers": total_customers, "repeat_customers": repeat_customers, "repurchase_rate": repurchase_rate}


def analyze_customer_value(master_df):
    """RFM客户价值分析: 基于购买时间、频率、金额进行客户分群."""
    last_date = master_df["order_purchase_timestamp"].max()

    rfm = master_df.groupby("customer_unique_id").agg(
        recency=("order_purchase_timestamp", lambda x: (last_date - x.max()).days),
        frequency=("order_id", "count"),
        monetary=("total_payment", "sum"),
    ).reset_index()

    rfm["R_level"] = pd.cut(rfm["recency"], bins=[-1, 114, 339, 1000], labels=["高", "中", "低"])
    rfm["F_level"] = pd.cut(rfm["frequency"], bins=[0, 1, 20], labels=["低", "高"])
    rfm["M_level"] = pd.cut(rfm["monetary"], bins=[-1, 62, 172, 100000], labels=["低", "中", "高"])

    rfm["segment"] = "R" + rfm["R_level"].astype(str) + "-F" + rfm["F_level"].astype(str) + "-M" + rfm["M_level"].astype(str)

    print("\n=== RFM 客户价值分群 ===")
    print(rfm[["recency", "frequency", "monetary"]].describe())
    segment_counts = rfm["segment"].value_counts().reset_index()
    segment_counts.columns = ["RFM组合", "客户数"]
    print(segment_counts)

    return rfm


if __name__ == "__main__":
    data = load_raw_data()
    master = create_master_orders(data)

    first_purchase = analyze_cohort(master)
    retention = calculate_retention(master, first_purchase)
    repurchase = analyze_repurchase(master)
    rfm = analyze_customer_value(master)
