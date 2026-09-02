import os
from decimal import Decimal, InvalidOperation

import mysql.connector
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# MYSQL CONNECTION
# ============================================================

def get_connection():

    import streamlit as st

    try:
        host = st.secrets.get(
            "MYSQL_HOST",
            os.getenv("MYSQL_HOST")
        )

        port = st.secrets.get(
            "MYSQL_PORT",
            os.getenv("MYSQL_PORT", 3306)
        )

        user = st.secrets.get(
            "MYSQL_USER",
            os.getenv("MYSQL_USER")
        )

        password = st.secrets.get(
            "MYSQL_PASSWORD",
            os.getenv("MYSQL_PASSWORD")
        )

        database = st.secrets.get(
            "MYSQL_DATABASE",
            os.getenv("MYSQL_DATABASE")
        )

    except Exception:
        host = os.getenv("MYSQL_HOST")
        port = os.getenv("MYSQL_PORT", 3306)
        user = os.getenv("MYSQL_USER")
        password = os.getenv("MYSQL_PASSWORD")
        database = os.getenv("MYSQL_DATABASE")

    return mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        ssl_disabled=False
    )

# ============================================================
# GET PRODUCT
# ============================================================

def get_product(product_name):

    if not product_name:

        return None

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query = """
            SELECT
                product_id,
                product_name,
                selling_price,
                stock_quantity,
                reorder_level
            FROM products
            WHERE LOWER(product_name) = LOWER(%s)
            LIMIT 1
        """

        cursor.execute(
            query,
            (str(product_name).strip(),)
        )

        product = cursor.fetchone()

        if product:

            product["selling_price"] = float(
                product["selling_price"]
            )

            product["stock_quantity"] = int(
                product["stock_quantity"]
            )

            product["reorder_level"] = int(
                product["reorder_level"]
            )

        return product

    finally:

        cursor.close()
        connection.close()


# ============================================================
# NORMALIZE PAYMENT METHOD
# ============================================================

def normalize_payment_method(payment_method):

    if not payment_method:

        raise ValueError(
            "Payment method is required."
        )

    payment = (
        str(payment_method)
        .strip()
        .upper()
    )

    allowed_methods = {
        "CASH",
        "UPI",
        "CARD"
    }

    if payment not in allowed_methods:

        raise ValueError(
            "Invalid payment method. "
            "Please use CASH, UPI or CARD."
        )

    return payment


# ============================================================
# NORMALIZE ITEMS
# ============================================================

def normalize_items(items):

    if not items:

        raise ValueError(
            "At least one product is required."
        )

    combined_items = {}

    for item in items:

        if not isinstance(item, dict):

            raise ValueError(
                "Each sale item must be a dictionary."
            )

        product_name = item.get(
            "product_name"
        )

        if not product_name:

            raise ValueError(
                "Product name is required."
            )

        product_name = (
            str(product_name)
            .strip()
        )

        if not product_name:

            raise ValueError(
                "Product name cannot be empty."
            )

        try:

            quantity = int(
                item.get("quantity")
            )

        except (
            ValueError,
            TypeError
        ):

            raise ValueError(
                f"Invalid quantity for "
                f"{product_name}."
            )

        if quantity <= 0:

            raise ValueError(
                f"Quantity for "
                f"{product_name} "
                "must be greater than zero."
            )

        # ----------------------------------------------------
        # COMBINE DUPLICATE PRODUCTS
        # ----------------------------------------------------

        product_key = product_name.lower()

        if product_key in combined_items:

            combined_items[
                product_key
            ]["quantity"] += quantity

        else:

            combined_items[
                product_key
            ] = {
                "product_name":
                    product_name,

                "quantity":
                    quantity
            }

    return list(
        combined_items.values()
    )


# ============================================================
# ADD COMPLETE SALE
# ============================================================

def add_sale(
    items,
    payment_method,
    shop_id=None
):

    """
    Create a complete multi-product sale.

    Example:

        items = [
            {
                "product_name": "Tea",
                "quantity": 2
            },
            {
                "product_name": "Samosa",
                "quantity": 3
            }
        ]

    The function:

    1. Validates payment method
    2. Validates products
    3. Combines duplicate products
    4. Locks product rows
    5. Checks stock
    6. Calculates totals
    7. Creates one sale
    8. Creates multiple sale_items
    9. Updates inventory
    10. Commits everything together

    If any step fails, the entire transaction
    is rolled back.
    """

    connection = None
    cursor = None

    try:

        # ====================================================
        # VALIDATE PAYMENT
        # ====================================================

        payment_method = normalize_payment_method(
            payment_method
        )

        # ====================================================
        # NORMALIZE ITEMS
        # ====================================================

        normalized_items = normalize_items(
            items
        )

        # ====================================================
        # DATABASE CONNECTION
        # ====================================================

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # ====================================================
        # SALE ITEMS
        # ====================================================

        sale_items = []

        grand_total = Decimal(
            "0.00"
        )

        # ====================================================
        # PROCESS PRODUCTS
        # ====================================================

        for item in normalized_items:

            product_name = item[
                "product_name"
            ]

            quantity = int(
                item["quantity"]
            )

            # =================================================
            # GET PRODUCT + LOCK ROW
            # =================================================

            cursor.execute(
                """
                SELECT
                    product_id,
                    product_name,
                    selling_price,
                    stock_quantity,
                    reorder_level
                FROM products
                WHERE LOWER(product_name)
                    = LOWER(%s)
                LIMIT 1
                FOR UPDATE
                """,
                (product_name,)
            )

            product = cursor.fetchone()

            # =================================================
            # PRODUCT NOT FOUND
            # =================================================

            if not product:

                raise ValueError(
                    f"Product not found: "
                    f"{product_name}"
                )

            # =================================================
            # STOCK
            # =================================================

            current_stock = int(
                product["stock_quantity"]
            )

            reorder_level = int(
                product["reorder_level"]
            )

            # =================================================
            # OUT OF STOCK
            # =================================================

            if current_stock <= 0:

                raise ValueError(
                    f"{product['product_name']} "
                    "is out of stock."
                )

            # =================================================
            # INSUFFICIENT STOCK
            # =================================================

            if quantity > current_stock:

                raise ValueError(
                    f"Insufficient stock for "
                    f"{product['product_name']}. "
                    f"Available stock: "
                    f"{current_stock}, "
                    f"Requested: "
                    f"{quantity}."
                )

            # =================================================
            # PRICE
            # =================================================

            try:

                unit_price = Decimal(
                    str(
                        product[
                            "selling_price"
                        ]
                    )
                )

            except (
                InvalidOperation,
                TypeError
            ):

                raise ValueError(
                    f"Invalid selling price "
                    f"for {product['product_name']}."
                )

            if unit_price < 0:

                raise ValueError(
                    f"Invalid selling price "
                    f"for {product['product_name']}."
                )

            # =================================================
            # DISCOUNT
            # =================================================

            discount = Decimal(
                "0.00"
            )

            # =================================================
            # TOTAL
            # =================================================

            total = (
                unit_price * quantity
            ) - discount

            if total < 0:

                raise ValueError(
                    f"Invalid total for "
                    f"{product['product_name']}."
                )

            grand_total += total

            # =================================================
            # NEW STOCK
            # =================================================

            new_stock = (
                current_stock -
                quantity
            )

            # =================================================
            # STOCK STATUS
            # =================================================

            if new_stock <= 0:

                stock_status = (
                    "OUT OF STOCK"
                )

            elif new_stock <= reorder_level:

                stock_status = (
                    "LOW STOCK"
                )

            else:

                stock_status = (
                    "IN STOCK"
                )

            # =================================================
            # SAVE ITEM
            # =================================================

            sale_items.append(
                {
                    "product_id":
                        product["product_id"],

                    "product_name":
                        product["product_name"],

                    "quantity":
                        quantity,

                    "unit_price":
                        unit_price,

                    "discount":
                        discount,

                    "total":
                        total,

                    "old_stock":
                        current_stock,

                    "new_stock":
                        new_stock,

                    "reorder_level":
                        reorder_level,

                    "stock_status":
                        stock_status
                }
            )

        # ====================================================
        # CREATE SALE
        # ====================================================

        if shop_id is not None:

            cursor.execute(
                """
                INSERT INTO sales
                (
                    shop_id,
                    sale_datetime,
                    payment_method,
                    total_amount
                )
                VALUES
                (
                    %s,
                    NOW(),
                    %s,
                    %s
                )
                """,
                (
                    shop_id,
                    payment_method,
                    grand_total
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO sales
                (
                    sale_datetime,
                    payment_method,
                    total_amount
                )
                VALUES
                (
                    NOW(),
                    %s,
                    %s
                )
                """,
                (
                    payment_method,
                    grand_total
                )
            )

        sale_id = cursor.lastrowid

        # ====================================================
        # INSERT SALE ITEMS
        # ====================================================

        for item in sale_items:

            cursor.execute(
                """
                INSERT INTO sale_items
                (
                    sale_id,
                    product_id,
                    quantity,
                    unit_price,
                    discount,
                    total
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    sale_id,

                    item["product_id"],

                    item["quantity"],

                    item["unit_price"],

                    item["discount"],

                    item["total"]
                )
            )

        # ====================================================
        # UPDATE INVENTORY
        # ====================================================

        for item in sale_items:

            cursor.execute(
                """
                UPDATE products
                SET stock_quantity =
                    stock_quantity - %s
                WHERE product_id = %s
                  AND stock_quantity >= %s
                """,
                (
                    item["quantity"],

                    item["product_id"],

                    item["quantity"]
                )
            )

            # ------------------------------------------------
            # VERIFY UPDATE
            # ------------------------------------------------

            if cursor.rowcount != 1:

                raise ValueError(
                    f"Inventory update failed "
                    f"for {item['product_name']}."
                )

        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()

        # ====================================================
        # RETURN RESULT
        # ====================================================

        return {
            "success": True,

            "sale_id":
                sale_id,

            "payment_method":
                payment_method,

            "total_amount":
                float(grand_total),

            "items": [

                {
                    "product_id":
                        item["product_id"],

                    "product_name":
                        item["product_name"],

                    "quantity":
                        item["quantity"],

                    "unit_price":
                        float(
                            item["unit_price"]
                        ),

                    "discount":
                        float(
                            item["discount"]
                        ),

                    "total":
                        float(
                            item["total"]
                        ),

                    "previous_stock":
                        item["old_stock"],

                    "remaining_stock":
                        item["new_stock"],

                    "reorder_level":
                        item["reorder_level"],

                    "stock_status":
                        item["stock_status"]
                }

                for item in sale_items
            ],

            "message":
                "Sale successfully recorded "
                "and inventory updated."
        }

    except Exception as e:

        # ====================================================
        # ROLLBACK
        # ====================================================

        if connection:

            connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        # ====================================================
        # CLOSE DATABASE
        # ====================================================

        if cursor:

            cursor.close()

        if connection:

            connection.close()


# ============================================================
# INTERACTIVE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "       SHOP SENSE - SALES + INVENTORY"
    )

    print(
        "=" * 60
    )

    items = []

    # ========================================================
    # PRODUCT INPUT
    # ========================================================

    while True:

        product_name = input(
            "\nEnter product name "
            "(or type 'done'): "
        )

        if (
            product_name
            .strip()
            .lower()
            == "done"
        ):

            break

        product_name = (
            product_name.strip()
        )

        if not product_name:

            print(
                "❌ Product name cannot be empty."
            )

            continue

        try:

            quantity = int(
                input(
                    "Enter quantity: "
                )
            )

        except ValueError:

            print(
                "❌ Please enter a valid quantity."
            )

            continue

        if quantity <= 0:

            print(
                "❌ Quantity must be greater than zero."
            )

            continue

        # ====================================================
        # FIND PRODUCT
        # ====================================================

        product = get_product(
            product_name
        )

        if not product:

            print(
                f"❌ Product not found: "
                f"{product_name}"
            )

            continue

        # ====================================================
        # SHOW PRODUCT
        # ====================================================

        print(
            f"\nProduct: "
            f"{product['product_name']}"
        )

        print(
            f"Price: ₹"
            f"{product['selling_price']:.2f}"
        )

        print(
            f"Available stock: "
            f"{product['stock_quantity']}"
        )

        # ====================================================
        # STOCK CHECK
        # ====================================================

        if product["stock_quantity"] <= 0:

            print(
                "❌ Product is out of stock."
            )

            continue

        if quantity > product["stock_quantity"]:

            print(
                "\n❌ Insufficient stock."
            )

            print(
                f"Available: "
                f"{product['stock_quantity']}"
            )

            print(
                f"Requested: "
                f"{quantity}"
            )

            continue

        # ====================================================
        # CHECK DUPLICATE IN CART
        # ====================================================

        duplicate = False

        for existing_item in items:

            if (
                existing_item[
                    "product_name"
                ].lower()
                ==
                product[
                    "product_name"
                ].lower()
            ):

                existing_item[
                    "quantity"
                ] += quantity

                duplicate = True

                print(
                    "✅ Product quantity "
                    "updated in cart."
                )

                break

        if not duplicate:

            items.append(
                {
                    "product_name":
                        product[
                            "product_name"
                        ],

                    "quantity":
                        quantity
                }
            )

            print(
                "✅ Product added."
            )

    # ========================================================
    # NO ITEMS
    # ========================================================

    if not items:

        print(
            "\n❌ No products selected."
        )

        raise SystemExit

    # ========================================================
    # SHOW CART
    # ========================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "              CURRENT BILL"
    )

    print(
        "=" * 60
    )

    estimated_total = Decimal(
        "0.00"
    )

    for item in items:

        product = get_product(
            item["product_name"]
        )

        if product:

            price = Decimal(
                str(
                    product[
                        "selling_price"
                    ]
                )
            )

            total = (
                price *
                item["quantity"]
            )

            estimated_total += total

            print(
                f"{item['product_name']} × "
                f"{item['quantity']} = "
                f"₹{total:.2f}"
            )

    print(
        "-" * 60
    )

    print(
        f"Estimated Total: "
        f"₹{estimated_total:.2f}"
    )

    # ========================================================
    # PAYMENT
    # ========================================================

    payment_method = input(
        "\nPayment method "
        "(Cash/UPI/Card): "
    )

    try:

        payment_method = (
            normalize_payment_method(
                payment_method
            )
        )

    except ValueError as e:

        print(
            f"\n❌ {e}"
        )

        raise SystemExit

    # ========================================================
    # CREATE SALE
    # ========================================================

    result = add_sale(
        items=items,
        payment_method=payment_method
    )

    # ========================================================
    # RESULT
    # ========================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "              SALE RESULT"
    )

    print(
        "=" * 60
    )

    if result["success"]:

        print(
            f"\nSale ID: "
            f"{result['sale_id']}"
        )

        print(
            f"Payment: "
            f"{result['payment_method']}"
        )

        print(
            "\nItems:"
        )

        for item in result["items"]:

            print(
                f"\n{item['product_name']} × "
                f"{item['quantity']} "
                f"= ₹{item['total']:.2f}"
            )

            print(
                f"   Unit Price: "
                f"₹{item['unit_price']:.2f}"
            )

            print(
                f"   Previous Stock: "
                f"{item['previous_stock']}"
            )

            print(
                f"   Remaining Stock: "
                f"{item['remaining_stock']}"
            )

            print(
                f"   Status: "
                f"{item['stock_status']}"
            )

        print(
            "\n" + "-" * 60
        )

        print(
            f"TOTAL: "
            f"₹{result['total_amount']:.2f}"
        )

        print(
            "\n✅ Sale successfully recorded!"
        )

        print(
            "✅ Inventory successfully updated!"
        )

    else:

        print(
            "\n❌ Sale failed:"
        )

        print(
            result["message"]
        )

    print(
        "=" * 60
    )