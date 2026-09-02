import mysql.connector
import random
from datetime import datetime, timedelta

# ==========================================
# MYSQL CONNECTION
# ==========================================

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Krishnavijisai003@",
    database="shopsense_ai_v2"
)

cursor = connection.cursor()

print("✅ Connected to MySQL")


# ==========================================
# SETTINGS
# ==========================================

TOTAL_SALES = 10000

# Generate approximately the last 180 days
START_DATE = datetime.now() - timedelta(days=180)


# ==========================================
# PRODUCTS
# ==========================================

products = [
    {"id": 1, "name": "Tea", "price": 15},
    {"id": 2, "name": "Coffee", "price": 20},
    {"id": 3, "name": "Vada", "price": 15},
    {"id": 4, "name": "Bajji", "price": 15},
    {"id": 5, "name": "Samosa", "price": 15},
    {"id": 6, "name": "Bun", "price": 20},
    {"id": 7, "name": "Biscuits", "price": 10},
    {"id": 8, "name": "Fresh Juice", "price": 40}
]


# ==========================================
# GENERATE REALISTIC DATE + TIME
# ==========================================

def generate_datetime():

    # Random date
    random_days = random.randint(0, 180)

    date = START_DATE + timedelta(days=random_days)

    weekday = date.weekday()

    # --------------------------------------
    # TIME PERIOD WEIGHTS
    # --------------------------------------

    periods = [
        (6, 9, 25),    # Morning
        (9, 12, 10),   # Late morning
        (12, 15, 8),   # Afternoon
        (15, 17, 12),  # Evening preparation
        (17, 20, 35),  # Evening peak
        (20, 22, 10)   # Night
    ]

    # Weekend gets more evening traffic
    if weekday >= 5:
        periods = [
            (6, 9, 28),
            (9, 12, 12),
            (12, 15, 10),
            (15, 17, 12),
            (17, 20, 28),
            (20, 22, 10)
        ]

    selected_period = random.choices(
        periods,
        weights=[p[2] for p in periods],
        k=1
    )[0]

    start_hour = selected_period[0]
    end_hour = selected_period[1]

    hour = random.randint(start_hour, end_hour - 1)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return date.replace(
        hour=hour,
        minute=minute,
        second=second,
        microsecond=0
    )


# ==========================================
# SELECT PRODUCTS
# ==========================================

def generate_items(sale_datetime):

    hour = sale_datetime.hour

    # --------------------------------------
    # PRODUCT WEIGHTS BY TIME
    # --------------------------------------

    if 6 <= hour < 10:

        # Morning
        weights = [
            35, 25, 12, 5,
            5, 10, 6, 2
        ]

    elif 10 <= hour < 15:

        # Afternoon
        weights = [
            20, 20, 10, 5,
            8, 10, 7, 20
        ]

    elif 15 <= hour < 20:

        # Evening
        weights = [
            30, 15, 15, 15,
            12, 5, 3, 5
        ]

    else:

        # Night
        weights = [
            25, 15, 15, 12,
            15, 8, 5, 5
        ]

    number_of_items = random.choices(
        [1, 2, 3, 4],
        weights=[55, 30, 12, 3]
    )[0]

    selected_products = random.choices(
        products,
        weights=weights,
        k=number_of_items
    )

    return selected_products


# ==========================================
# PAYMENT METHOD
# ==========================================

def generate_payment_method():

    return random.choices(
        ["Cash", "UPI", "Card"],
        weights=[25, 60, 15],
        k=1
    )[0]


# ==========================================
# GENERATE SALES
# ==========================================

for sale_number in range(TOTAL_SALES):

    sale_datetime = generate_datetime()

    payment_method = generate_payment_method()

    selected_products = generate_items(
        sale_datetime
    )

    total_amount = 0

    sale_items = []

    for product in selected_products:

        quantity = random.randint(1, 3)

        # Occasional large order
        if random.random() < 0.01:
            quantity = random.randint(5, 10)

        unit_price = product["price"]

        item_total = quantity * unit_price

        total_amount += item_total

        sale_items.append({
            "product_id": product["id"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total": item_total
        })


    # ======================================
    # INTENTIONAL ANOMALIES
    # ======================================

    # 0.5% chance of unusually large transaction
    if random.random() < 0.005:

        total_amount *= random.randint(4, 8)

    # 0.5% chance of unusually low transaction
    elif random.random() < 0.005:

        total_amount = random.choice(
            [5, 10, 15]
        )


    # ======================================
    # INSERT SALE
    # ======================================

    sale_query = """
        INSERT INTO sales
        (shop_id, sale_datetime, payment_method, total_amount)
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        sale_query,
        (
            1,
            sale_datetime,
            payment_method,
            total_amount
        )
    )

    sale_id = cursor.lastrowid


    # ======================================
    # INSERT SALE ITEMS
    # ======================================

    item_query = """
        INSERT INTO sale_items
        (sale_id, product_id, quantity, unit_price, discount, total)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    for item in sale_items:

        cursor.execute(
            item_query,
            (
                sale_id,
                item["product_id"],
                item["quantity"],
                item["unit_price"],
                0,
                item["total"]
            )
        )


    # ======================================
    # COMMIT EVERY 500 SALES
    # ======================================

    if (sale_number + 1) % 500 == 0:

        connection.commit()

        print(
            f"✅ Generated {sale_number + 1} V2 transactions"
        )


# ==========================================
# FINAL COMMIT
# ==========================================

connection.commit()

print()
print("🎉 V2 DATA GENERATION COMPLETED!")
print(f"Generated: {TOTAL_SALES} transactions")

cursor.close()
connection.close()

print("🔌 MySQL connection closed")