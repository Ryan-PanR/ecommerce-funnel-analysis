"""
可视化图表模块.

将漏斗分析、同期群分析的结果可视化为图表.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Polygon
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False

from data_loader import load_raw_data, clean_order_items, create_master_orders
from funnel_analysis import analyze_order_funnel, analyze_delivery_performance, analyze_payment_patterns, analyze_purchase_patterns
from cohort_analysis import analyze_cohort, calculate_retention, analyze_repurchase, analyze_customer_value
from category_analysis import analyze_category_sales


def plot_funnel(funnel_df, save_path=None):
    """绘制订单漏斗横向柱状图."""
    fig, ax = plt.subplots(figsize=(10, 5))

    stages = funnel_df['stage']
    counts = funnel_df['count']
    rates = funnel_df['conversion_rate']

    colors = ['#440154', '#3b528b', '#21918c', '#5ec962']
    bars = ax.barh(stages, counts, color=colors)

    for bar, count, rate in zip(bars, counts, rates):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                f'{count:,} ({rate}%)', va='center', fontsize=12)

    ax.set_xlabel('订单数', fontsize=12)
    ax.set_title('订单状态漏斗分析', fontsize=16)
    ax.invert_yaxis()
    ax.set_xlim(0, max(counts) * 1.18)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_delivery_performance(delivery_df, save_path=None):
    """绘制配送准时率饼图."""
    total = len(delivery_df)
    on_time = (delivery_df["delay_days"] <= 0).sum()
    delayed = (delivery_df["delay_days"] > 0).sum()

    fig, ax = plt.subplots(figsize=(11, 7))
    labels = ['准时送达', '延迟送达']
    sizes = [on_time, delayed]
    colors = ['#21918c', '#f46d43']
    explode = (0, 0.05)

    pie_labels = [l if s / total * 100 >= 10 else '' for l, s in zip(labels, sizes)]

    wedges, texts = ax.pie(sizes, explode=explode, labels=pie_labels, colors=colors,
                            startangle=90, labeldistance=1.1,
                            textprops={'fontsize': 12, 'fontweight': 'bold'})

    for i, w in enumerate(wedges):
        p = sizes[i] / total * 100
        ang = (w.theta2 + w.theta1) / 2
        x = np.cos(np.radians(ang))
        y = np.sin(np.radians(ang))
        if p >= 10:
            ax.text(0.6 * x, 0.6 * y, f'{p:.2f}%\n({sizes[i]:,}单)',
                    ha='center', va='center', color='white', fontsize=12, fontweight='bold')
        else:
            ax.annotate(f'{labels[i]}: {p:.2f}% ({sizes[i]:,}单)',
                        xy=(x, y), xytext=(1.15, y + 0.05),
                        arrowprops=dict(arrowstyle='-', color='gray', lw=1,
                                        connectionstyle="angle,angleA=45,angleB=0,rad=0"),
                        ha='left', va='center', fontsize=12, fontweight='bold')

    ax.set_title('配送准时率分析', fontsize=16, fontweight='bold')
    ax.set_xlim(-1.3, 1.8)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_payment_distribution(payment_stats, save_path=None):
    """绘制支付方式分布饼图."""
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = ['#440154', '#3b528b', '#21918c', '#f46d43', '#a5a5a5']
    labels = payment_stats['payment_type'].tolist()
    sizes = payment_stats['share'].tolist()
    total = sum(sizes)

    wedges, texts = ax.pie(sizes, labels=['']*len(labels), colors=colors,
                            startangle=140, labeldistance=1.05)

    label_x = -1.6
    y_positions = [1.8, 1.5, 1.2, 0.9, 0.6]
    for i, w in enumerate(wedges):
        p = sizes[i] / total * 100
        ang = (w.theta2 + w.theta1) / 2
        x = np.cos(np.radians(ang))
        y = np.sin(np.radians(ang))
        if x > 0:
            x_edge = np.cos(np.radians(ang)) * 0.3
        else:
            x_edge = x
        mid_y = y_positions[i]
        mid_x = (x_edge + label_x) / 2
        ax.plot([x_edge, mid_x, label_x], [y, mid_y, mid_y], color='gray', lw=0.8)
        ax.text(label_x - 0.05, mid_y, f'{labels[i]}: {p:.2f}%',
                ha='right', va='center', fontsize=12, fontweight='bold')

    ax.set_title('支付方式分布', fontsize=16, fontweight='bold')
    ax.set_xlim(-2.8, 1.5)
    ax.set_ylim(-1.2, 2.2)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_purchase_patterns(patterns, save_path=None):
    """绘制购买时间模式(小时折线+星期柱状+月度折线)."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].plot(patterns["hourly"]["purchase_hour"], patterns["hourly"]["orders"],
                 marker='o', color='#3b528b', linewidth=2, markersize=4)
    axes[0].fill_between(patterns["hourly"]["purchase_hour"], patterns["hourly"]["orders"], alpha=0.2, color='#3b528b')
    axes[0].set_title('按小时分布', fontsize=13)
    axes[0].set_xlabel('小时')
    axes[0].set_ylabel('订单数')
    axes[0].set_xticks(range(0, 24, 2))

    axes[1].bar(patterns["daily"]["purchase_dow"], patterns["daily"]["orders"], color='#21918c')
    axes[1].set_title('按星期分布', fontsize=13)
    axes[1].set_xlabel('星期')
    axes[1].tick_params(axis='x', rotation=45)

    axes[2].plot(range(len(patterns["monthly"])), patterns["monthly"]["orders"],
                 marker='s', color='#440154', linewidth=2, markersize=4)
    axes[2].fill_between(range(len(patterns["monthly"])), patterns["monthly"]["orders"], alpha=0.2, color='#440154')
    axes[2].set_title('按月分布', fontsize=13)
    axes[2].set_xlabel('月份')
    axes[2].set_xticks(range(len(patterns["monthly"])))
    axes[2].set_xticklabels([str(m) for m in patterns["monthly"]["purchase_month"]], rotation=90, fontsize=8)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_retention(retention, save_path=None):
    """绘制各月平均留存率折线图(不含首月)."""
    avg_retention = retention.mean().drop(0)
    x_labels = avg_retention.index.astype(int)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(range(len(avg_retention)), avg_retention.values,
            marker='o', color='#21918c', linewidth=2, markersize=5)
    ax.fill_between(range(len(avg_retention)), avg_retention.values, alpha=0.2, color='#21918c')
    ax.set_title('各月平均留存率（不含首月）', fontsize=14, fontweight='bold')
    ax.set_xlabel('距首次购买月数', fontsize=12)
    ax.set_ylabel('平均留存率 (%)', fontsize=12)
    ax.set_xticks(range(len(avg_retention)))
    ax.set_xticklabels([f'{int(i)}月' for i in x_labels])
    for i, v in enumerate(avg_retention.values):
        ax.text(i, v + 0.05, f'{v:.2f}%', ha='center', fontsize=8)
    ax.set_ylim(0, avg_retention.max() * 1.3)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_repurchase(repurchase, save_path=None):
    """绘制客户复购率饼图."""
    total = repurchase["total_customers"]
    single = total - repurchase["repeat_customers"]
    repeat = repurchase["repeat_customers"]

    fig, ax = plt.subplots(figsize=(9, 7))
    labels = [f'仅购买1次\n({single:,}人)', f'购买2次以上\n({repeat:,}人)']
    sizes = [single, repeat]
    colors = ['#440154', '#21918c']
    explode = (0, 0.08)

    pie_labels = [l if s / total * 100 >= 10 else '' for l, s in zip(labels, sizes)]

    wedges, texts = ax.pie(sizes, explode=explode, labels=pie_labels, colors=colors,
                            startangle=90, labeldistance=1.1,
                            textprops={'fontsize': 12, 'fontweight': 'bold'})

    for i, w in enumerate(wedges):
        p = sizes[i] / total * 100
        ang = (w.theta2 + w.theta1) / 2
        x = np.cos(np.radians(ang))
        y = np.sin(np.radians(ang))
        if p >= 10:
            ax.text(0.6 * x, 0.6 * y, f'{p:.2f}%',
                    ha='center', va='center', color='white', fontsize=12, fontweight='bold')
        else:
            ax.annotate(f'{labels[i]}: {p:.2f}%',
                        xy=(x, y), xytext=(1.1, y + 0.05),
                        arrowprops=dict(arrowstyle='-', color='gray', lw=1,
                                        connectionstyle="angle,angleA=45,angleB=0,rad=0"),
                        ha='left', va='center', fontsize=12, fontweight='bold')

    ax.set_title('客户复购率分析', fontsize=16, fontweight='bold')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_customer_value(rfm, save_path=None):
    """绘制RFM客户价值分群柱状图(Top 10)."""
    segment_counts = rfm["segment"].value_counts().reset_index()
    segment_counts.columns = ['RFM组合', '客户数']
    top10 = segment_counts.head(10)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top10['RFM组合'], top10['客户数'], color='#3b528b')
    ax.set_xlabel('客户数')
    ax.set_title('RFM 客户价值分群 (Top 10)', fontsize=14)
    for i, v in enumerate(top10['客户数']):
        ax.text(v + 200, i, f'{v:,}', va='center', fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, top10['客户数'].max() * 1.2)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


def plot_rfm_3d(rfm, save_path=None):
    """绘制RFM 3D柱状图（pyecharts）."""
    from pyecharts import options as opts
    from pyecharts.charts import Bar3D
    from pyecharts.globals import ThemeType

    rfm_copy = rfm.copy()
    rfm_copy["R_level"] = pd.cut(rfm_copy["recency"], bins=[-1, 114, 339, 1000], labels=["高", "中", "低"])
    rfm_copy["F_level"] = pd.cut(rfm_copy["frequency"], bins=[0, 1, 20], labels=["低", "高"])
    rfm_copy["M_level"] = pd.cut(rfm_copy["monetary"], bins=[-1, 62, 172, 100000], labels=["低", "中", "高"])

    grouped = rfm_copy.groupby(["R_level", "F_level", "M_level"], observed=False).size().reset_index(name="count")

    r_order = ["高", "中", "低"]
    f_order = ["低", "高"]
    m_order = ["低", "中", "高"]
    m_map = {name: i for i, name in enumerate(m_order)}

    rf_labels = [f"R{r}-F{f}" for r in r_order for f in f_order]
    rf_map = {}
    for ri, r in enumerate(r_order):
        for fi, f in enumerate(f_order):
            rf_map[(r, f)] = ri * len(f_order) + fi

    data = []
    for r in r_order:
        for f in f_order:
            for m in m_order:
                x = rf_map[(r, f)]
                y = m_map[m]
                match = grouped[(grouped["R_level"] == r) & (grouped["F_level"] == f) & (grouped["M_level"] == m)]
                z = int(match["count"].values[0]) if len(match) > 0 else 0
                data.append([x, y, z])

    max_count = grouped["count"].max()
    if max_count == 0:
        max_count = 1

    bar3d = (
        Bar3D(init_opts=opts.InitOpts(
            width="1200px",
            height="800px",
            theme=ThemeType.LIGHT,
            bg_color="#ffffff",
        ))
        .add(
            series_name="客户数量",
            data=data,
            xaxis3d_opts=opts.Axis3DOpts(
                rf_labels, name="Recency × Frequency", min_=0, max_=5,
                axislabel_opts=opts.LabelOpts(font_size=11),
            ),
            yaxis3d_opts=opts.Axis3DOpts(
                [f"M{m}" for m in m_order], name="Monetary", min_=0, max_=2,
                axislabel_opts=opts.LabelOpts(font_size=12),
            ),
            zaxis3d_opts=opts.Axis3DOpts(
                name="客户数量", min_=0, max_=int(max_count * 1.15),
                axislabel_opts=opts.LabelOpts(font_size=10),
            ),
            grid3d_opts=opts.Grid3DOpts(
                width=100, depth=100, height=100,
                is_rotate=False, rotate_speed=10,
                view_control_alpha=20, view_control_beta=50,
            ),
            itemstyle_opts=opts.ItemStyleOpts(opacity=0.9),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(
                title="RFM 客户价值 3D 分析",
                subtitle="X=Recency×Frequency(6组合), Y=Monetary(3档), 柱高=客户数量",
                pos_left="center", pos_top="2%",
                title_textstyle_opts=opts.TextStyleOpts(font_size=20, color="#222", font_weight="bold"),
                subtitle_textstyle_opts=opts.TextStyleOpts(font_size=13, color="#666"),
            ),
            visualmap_opts=opts.VisualMapOpts(
                max_=int(max_count),
                range_color=["#313695", "#74add1", "#abd9e9", "#fee090", "#f46d43", "#a50026"],
                pos_right="3%", pos_top="10%",
            ),
            tooltip_opts=opts.TooltipOpts(trigger="item"),
        )
    )

    import webbrowser
    import os
    html_path = os.path.abspath("rfm_3d.html")
    bar3d.render(html_path)
    webbrowser.open(f"file:///{html_path}")
    print("3D图已生成: rfm_3d.html")


def plot_category_sales(category_stats, save_path=None):
    """绘制商品类目销售额柱状图(横向)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(category_stats['category_en'], category_stats['revenue'], color='#21918c')
    ax.set_xlabel('收入 (R$)', fontsize=12)
    ax.set_title('Top 10 类目销售额', fontsize=14)
    ax.tick_params(axis='y', labelsize=11)
    ax.tick_params(axis='x', labelsize=10)
    for i, (v, share) in enumerate(zip(category_stats['revenue'], category_stats['revenue_share'])):
        ax.text(v + 5000, i, f'{v:,.0f} ({share}%)', va='center', fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, category_stats['revenue'].max() * 1.25)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    import os
    img_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(img_dir, exist_ok=True)

    data = load_raw_data()
    master = create_master_orders(data)

    funnel = analyze_order_funnel(master)
    plot_funnel(funnel, save_path=os.path.join(img_dir, "funnel.png"))

    delivery = analyze_delivery_performance(master)
    plot_delivery_performance(delivery, save_path=os.path.join(img_dir, "delivery_performance.png"))

    payment_stats = analyze_payment_patterns(data["order_payments"])
    plot_payment_distribution(payment_stats, save_path=os.path.join(img_dir, "payment_distribution.png"))

    patterns = analyze_purchase_patterns(master)
    plot_purchase_patterns(patterns, save_path=os.path.join(img_dir, "purchase_patterns.png"))

    first_purchase = analyze_cohort(master)
    retention = calculate_retention(master, first_purchase)
    plot_retention(retention, save_path=os.path.join(img_dir, "retention.png"))

    repurchase = analyze_repurchase(master)
    plot_repurchase(repurchase, save_path=os.path.join(img_dir, "repurchase.png"))

    rfm = analyze_customer_value(master)
    plot_customer_value(rfm, save_path=os.path.join(img_dir, "rfm_segments.png"))

    items = clean_order_items(data["order_items"], data["products"], data["category_translation"])
    category_stats = analyze_category_sales(items)
    plot_category_sales(category_stats, save_path=os.path.join(img_dir, "category_sales.png"))

    plot_rfm_3d(rfm)
