"""
漏斗分析模块.

分析订单从创建到送达的转化漏斗,
配送绩效, 支付方式分别, 购买时间模式.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import numpy as np
from data_loader import load_raw_data, clean_orders, create_master_orders

def analyze_order_funnel(master_df):
    """分析订单状态漏斗: 创建->批准->发货->送达."""
    status_counts = master_df["order_status"].value_counts()
    total = len(master_df)

    funnel = pd.DataFrame({
        "stage": ["created", "approved", "shipped", "delivered"],
        "count": [
            total,
            master_df["order_approved_at"].notna().sum(),
            master_df["order_delivered_carrier_date"].notna().sum(),
            master_df["order_delivered_customer_date"].notna().sum(),
        ],
    })
    funnel["conversion_rate"] = (funnel["count"] / total * 100).round(2)
    

    print("\n=== 订单状态漏斗 ===")
    print(funnel.to_string(index=False))
    return funnel


def analyze_delivery_performance(orders_df):
    """分析配送绩效: 准时率, 延迟天数, 平均配送时间."""
    delivered = orders_df.dropna(subset=["order_delivered_customer_date"]).copy()

    delivered["delivery_days"] = (
        delivered["order_delivered_customer_date"] - delivered["order_purchase_timestamp"]
    ).dt.days

    delivered["delay_days"] = (
        delivered["order_delivered_customer_date"] - delivered["order_estimated_delivery_date"]
    ).dt.days

    total_delivered = len(delivered)
    on_time = (delivered["delay_days"] <= 0).sum()
    delayed = (delivered["delay_days"] > 0).sum()

    print("\n=== 配送绩效 ===")
    print(f"已送达: {total_delivered}")
    print(f"准时送达: {on_time} ({on_time/total_delivered*100:.2f}%)")
    print(f"延迟送达: {delayed} ({delayed/total_delivered*100:.2f}%)")
    print(f"平均配送时间: {delivered['delivery_days'].mean():.1f} 天")
    print(f"平均延迟天数: {delivered['delay_days'].mean():.1f} 天")

    return delivered[["order_id", "delivery_days", "delay_days"]]

def analyze_payment_patterns(payments_df):
    """分析支付方式分布和订单金额."""
    payment_stats = payments_df.groupby("payment_type").agg(
        count=("payment_value", "count"),
        total_amount=("payment_value", "sum"),
        avg_amount=("payment_value", "mean"),
    ).reset_index()

    total_payments = payment_stats["total_amount"].sum()
    payment_stats["share"] = (payment_stats["total_amount"] / total_payments * 100).round(2)

    payment_stats = payment_stats.sort_values("total_amount", ascending=False)

    print("\n=== 支付方式分析 ===")
    print(payment_stats.to_string(index=False))

    return payment_stats


def analyze_purchase_patterns(orders_df):
    """分析购买时间模式: 小时分布, 星期分布, 月度趋势."""
    hourly = orders_df.groupby("purchase_hour").size().reset_index(name="orders")
    daily = orders_df.groupby("purchase_dow").size().reset_index(name="orders")
    monthly = orders_df.groupby("purchase_month").size().reset_index(name="orders")

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily = daily.set_index("purchase_dow").reindex(day_order).reset_index()

    print("\n=== 购买时间模式 ===")
    print("\n按小时分布:")
    print(hourly.to_string(index=False))
    print("\n按星期分布:")
    print(daily.to_string(index=False))
    print("\n按月分布:")
    print(monthly.to_string(index=False))

    return {"hourly": hourly, "daily": daily, "monthly": monthly}


if __name__ == "__main__":
    data = load_raw_data()
    master_df = create_master_orders(data)

    funnel = analyze_order_funnel(master_df)
    delivery = analyze_delivery_performance(master_df)
    payments = analyze_payment_patterns(data["order_payments"])
    patterns = analyze_purchase_patterns(master_df)