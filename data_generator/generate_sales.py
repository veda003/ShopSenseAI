import mysql.connector
import random
from datetime import datetime, timedelta

# ============================================
# DATABASE CONNECTION
# ============================================

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Krishnavijisai003@",
    database="shopsense_ai"
)

cursor = connection.cursor()

print("✅ Connected to MySQL")


# ============================================
# PRODUCT DATA
# ============================================

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


# ============================================
# GENERATE ONE RANDOM DATETIME
# ============================================

def generate_datetime():

    start_date = datetime.now() - timedelta(days=180)

    random_days = random.randint(0, 180)

    date = start_date + timedelta(days=random_days)

    # Business hours: 6 AM - 10 PM
    hour = random.randint(6, 21)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return date.replace(
        hour=hour,
        minute=minute,
        second=second,
        microsecond=0
    )


# ============================================
# DETERMINE NUMBER OF PRODUCTS IN A BILL
# ============================================

def generate_items():

    number_of_items = random.choices(
        [1, 2, 3, 4],
        weights=[50, 30, 15, 5]
    )[0]

    selected_products = random.sample(
        products,
        number_of_items
    )

    return selected_products


# ============================================
# GENERATE SALES
# ============================================

TOTAL_SALES = 10000

for sale_number in range(TOTAL_SALES):

    sale_datetime = generate_datetime()

    # Select payment method
    payment_method = random.choices(
        ["Cash", "UPI", "Card"],
        weights=[30, 55, 15]
    )[0]

    selected_products = generate_items()

    total_amount = 0

    sale_items = []

    for product in selected_products:

        quantity = random.randint(1, 4)

        unit_price = product["price"]

        item_total = quantity * unit_price

        total_amount += item_total

        sale_items.append({
            "product_id": product["id"],
            "quantity": quantity,
            "unit_price": unit_price,
            "total": item_total
        })

    # ========================================
    # INSERT SALE
    # ========================================

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

    # ========================================
    # INSERT SALE ITEMS
    # ========================================

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

    # Commit every 500 transactions
    if (sale_number + 1) % 500 == 0:

        connection.commit()

        print(
            f"✅ Generated {sale_number + 1} transactions"
        )


# ============================================
# FINAL COMMIT
# ============================================

connection.commit()

print()
print("🎉 SALES DATA GENERATION COMPLETED!")
print(f"Total transactions: {TOTAL_SALES}")


# ============================================
# CLOSE CONNECTION
# ============================================

cursor.close()
connection.close()

print("🔌 MySQL connection closed.")