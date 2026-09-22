"""
数据加载和清晰模块.

负责加载 9个CSV文件, 清洗缺失值,
转换时间格式, 合并成分析用的主表.
"""

import pandas as pd
from pathlib import Path
pd.set_option('display.max_columns', None)

RAW_DIR = Path(__file__).parent.parent/"data"/'raw'
PROCESSED_DIR = Path(__file__).parent.parent/'data'/'processed'

def load_raw_data():
    '''
    加载全部9个CSV文件, 返回一个字典.
    '''
    files  = {
        'customers' : 'olist_customers_dataset.csv',
        'geolocation' : 'olist_geolocation_dataset.csv',
        'order_items' : 'olist_order_items_dataset.csv',
        'order_payments' : 'olist_order_payments_dataset.csv',
        'order_reviews': 'olist_order_reviews_dataset.csv',
        'orders' : 'olist_orders_dataset.csv',
        'products' : 'olist_products_dataset.csv',
        'sellers' : 'olist_sellers_dataset.csv',
        'category_translation' :'product_category_name_translation.csv'


    }

    data = {}
    for key, filename in files.items(): # items()返回的是键值对
        filepath = RAW_DIR / filename  # 路径
        data[key] = pd.read_csv(filepath)  # 填入字典data内 key : df
        print(f"  {key:<22} {data[key].shape[0]:>7} rows * {data[key].shape[1]} cols") # 表名 以及几行几列

    return data

# if __name__ == "__main__":

    # data = load_raw_data()
    # print(f"\n共加载了 {len(data)} 个表")
    # print(data['orders'].columns.tolist())
    # print(data['orders'].head())

def clean_orders(orders_df, customers_df):
    """清洗订单表: 转时间格式, 处理缺失值, 加衍生列, 合并customer_unique_id."""
    timestamp_cols= [
        'order_purchase_timestamp', # 顾客下单时间
        'order_approved_at', # 订单审核通过时间
        "order_delivered_carrier_date", # 订单交付快递时间
        'order_delivered_customer_date', # 订单送达时间
        'order_estimated_delivery_date' # 订单预计到达时间
    ]

    for col in timestamp_cols:
        orders_df[col] = pd.to_datetime(orders_df[col],errors='coerce') # dataframe读进来的是str
        # errors = 'raise'(默认)报错停止运行 'ignore'忽略报留原样 'coerce'变成NaN


    before = len(orders_df)

    orders_df = orders_df[~orders_df['order_status'].isin(['canceled', 'unavailable'])].copy()
    after = len(orders_df)

    print(f"清洗后剩余: {len(orders_df)} 条订单, 清洗掉了{before - after}条订单")
    # orders['order_status'].value_counts()

    # 增加了四列分别是 天 eg:10 月: eg: 2017-09 小时: 13 周几: 4
    orders_df["purchase_date"] = orders_df["order_purchase_timestamp"].dt.date 
    orders_df["purchase_month"] = orders_df["order_purchase_timestamp"].dt.to_period("M")
    orders_df["purchase_hour"] = orders_df["order_purchase_timestamp"].dt.hour
    orders_df["purchase_dow"] = orders_df["order_purchase_timestamp"].dt.day_name()         

    orders_df = orders_df.merge(customers_df[['customer_id', 'customer_unique_id']], on='customer_id', how='left')
    return orders_df

# if __name__ == "__main__":
    # data = load_raw_data()
    # print("清洗前列名：")
    # print(data['orders'].columns.tolist())
    # cleaned = clean_orders(data['orders'])
    # print("\n清洗后列名：")
    # print(cleaned.columns.tolist())
    # print("\n新增的4列前5行：")
    # print(cleaned[['purchase_date', 'purchase_month', 'purchase_hour', 'purchase_dow']].head())


def clean_order_items(items_df, products_df, translation_df):
    """清洗订单商品表, 翻译商品类目为英文"""
    items_df = items_df.merge(products_df[['product_id', 'product_category_name']], on = 'product_id', how = 'left') # 按照左连接关联表 现实当中可能被下单的商品在商品表中找不到id
    items_df = items_df.merge(translation_df, on = 'product_category_name', how = 'left') # 再关联上他们的英文名字
    items_df['category_en'] = items_df['product_category_name_english'].fillna(items_df['product_category_name']) # 添加英文名字列

    items_df['category_en'] = items_df['category_en'].fillna('unknown') 
    items_df['shipping_limit_date'] = pd.to_datetime(items_df['shipping_limit_date'], errors='coerce')

    return items_df # 原来7列, 关联上两列又添加1列变成10列


def create_master_orders(data):
    """合并所有清洗后的表, 生成分析用的主表."""

    orders = clean_orders(data["orders"], data["customers"])
    items = clean_order_items(data["order_items"], data["products"], data["category_translation"]) # 调用两个函数清洗


    payment_agg = data['order_payments'].groupby('order_id')['payment_value'].sum().reset_index()
    payment_agg.columns = ['order_id', 'total_payment']
    master = orders.merge(payment_agg, on='order_id', how='left')

    master = master.merge(data["customers"][["customer_id", "customer_state"]], on = "customer_id", how = "left") # 

    return master


if __name__ == "__main__":
    print(f"----------- it works ----------")
    data = load_raw_data()
  
    # for table_idx, key in enumerate(data.keys(), start= 1):
        
        # print(f" --------第 {table_idx} 张表: {key} ---------")
        # df = data[key]

        # print(f" 行数: {df.shape[0]}, 列数： {df.shape[1]}")
        # print(f" 列名: {df.columns.tolist()}")
        # print(df.head())
    

    print(f" --------- 函数1检查完毕 -------")
    orders = data["orders"]            # 先拿到原始表
    print(f"orders 表中 有\t{orders.isna().sum()}条空数据")

    print(f"\n ---- 查看orders表中下单没成功的有(即数据为空): --------")
    print(orders["order_purchase_timestamp"].isna().sum())
    

    master = create_master_orders(data)
    print(f"\n主表行数: {len(master)}")
    print(f"主表列数: {master.shape[1]}")
    print(f"列名: {master.columns.tolist()}")
    print(master.head())

