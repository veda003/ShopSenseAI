import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. CONNECT TO MYSQL
# ==========================================

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Krishnavijisai003@",
    database="shopsense_ai"
)

print("✅ Connected to MySQL")


# ==========================================
# 2. LOAD SALES DATA
# ==========================================

query = """
SELECT
    sale_id,
    shop_id,
    sale_datetime,
    payment_method,
    total_amount
FROM sales
"""

sales_df = pd.read_sql(query, connection)

print(f"✅ Loaded {len(sales_df)} sales records")


# ==========================================
# 3. BASIC INFORMATION
# ==========================================

print("\n========== DATA INFORMATION ==========")

print(sales_df.info())


# ==========================================
# 4. BASIC STATISTICS
# ==========================================

print("\n========== BASIC STATISTICS ==========")

print(sales_df["total_amount"].describe())


# ==========================================
# 5. TOTAL REVENUE
# ==========================================

total_revenue = sales_df["total_amount"].sum()

print("\n========== BUSINESS KPIs ==========")

print(f"Total Revenue: ₹{total_revenue:,.2f}")


# ==========================================
# 6. AVERAGE BILL
# ==========================================

average_bill = sales_df["total_amount"].mean()

print(f"Average Bill: ₹{average_bill:,.2f}")


# ==========================================
# 7. HIGHEST BILL
# ==========================================

highest_bill = sales_df["total_amount"].max()

print(f"Highest Bill: ₹{highest_bill:,.2f}")


# ==========================================
# 8. LOWEST BILL
# ==========================================

lowest_bill = sales_df["total_amount"].min()

print(f"Lowest Bill: ₹{lowest_bill:,.2f}")


# ==========================================
# 9. PAYMENT METHOD ANALYSIS
# ==========================================

payment_analysis = (
    sales_df
    .groupby("payment_method")
    .agg(
        transactions=("sale_id", "count"),
        revenue=("total_amount", "sum")
    )
    .sort_values("revenue", ascending=False)
)

print("\n========== PAYMENT ANALYSIS ==========")

print(payment_analysis)


# ==========================================
# 10. DAILY SALES
# ==========================================

sales_df["sale_datetime"] = pd.to_datetime(
    sales_df["sale_datetime"]
)

sales_df["sale_date"] = sales_df["sale_datetime"].dt.date

daily_sales = (
    sales_df
    .groupby("sale_date")
    .agg(
        transactions=("sale_id", "count"),
        revenue=("total_amount", "sum")
    )
    .reset_index()
)

print("\n========== DAILY SALES ==========")

print(daily_sales.head(10))


# ==========================================
# 11. BEST SALES DAY
# ==========================================

best_day = daily_sales.loc[
    daily_sales["revenue"].idxmax()
]

print("\n========== BEST SALES DAY ==========")

print(best_day)


# ==========================================
# 12. WORST SALES DAY
# ==========================================

worst_day = daily_sales.loc[
    daily_sales["revenue"].idxmin()
]

print("\n========== WORST SALES DAY ==========")

print(worst_day)


# ==========================================
# 13. HOURLY ANALYSIS
# ==========================================

sales_df["hour"] = sales_df[
    "sale_datetime"
].dt.hour

hourly_sales = (
    sales_df
    .groupby("hour")
    .agg(
        transactions=("sale_id", "count"),
        revenue=("total_amount", "sum")
    )
    .reset_index()
)

print("\n========== HOURLY SALES ==========")

print(hourly_sales)


# ==========================================
# 14. BEST HOUR
# ==========================================

best_hour = hourly_sales.loc[
    hourly_sales["revenue"].idxmax()
]

print("\n========== BUSIEST HOUR ==========")

print(best_hour)


# ==========================================
# 15. SAVE DAILY DATA
# ==========================================

daily_sales.to_csv(
    "analytics/daily_sales.csv",
    index=False
)

payment_analysis.to_csv(
    "analytics/payment_analysis.csv"
)

hourly_sales.to_csv(
    "analytics/hourly_sales.csv",
    index=False
)

print("\n✅ Analysis files saved")


# ==========================================
# 16. REVENUE TREND CHART
# ==========================================

plt.figure(figsize=(12, 6))

plt.plot(
    daily_sales["sale_date"],
    daily_sales["revenue"]
)

plt.title("Daily Revenue Trend")

plt.xlabel("Date")

plt.ylabel("Revenue")

plt.xticks(rotation=45)

plt.tight_layout()

plt.show()


# ==========================================
# CLOSE CONNECTION
# ==========================================

connection.close()

print("\n🔌 MySQL connection closed")
print("🎉 Analysis completed successfully!")