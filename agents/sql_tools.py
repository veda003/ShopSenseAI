import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

import mysql.connector
from dotenv import load_dotenv


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# AGENTS DIRECTORY
# ============================================================

AGENTS_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(
    os.path.join(
        PROJECT_ROOT,
        ".env"
    )
)


# ============================================================
# ANALYTICS IMPORTS
# ============================================================

from analytics.anomaly_detection import (
    detect_transaction_anomalies
)

from analytics.sales_forecasting import (
    forecast_sales
)

from analytics.business_insights import (
    generate_business_summary
)

from agents.sales_entry import (
    add_sale
)


# ============================================================
# MYSQL CONNECTION
# ============================================================

def get_connection():
    """
    Create a MySQL connection.
    """

    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )


# ============================================================
# JSON SAFE CONVERSION
# ============================================================

def make_json_safe(data):
    """
    Convert Decimal, date and datetime values
    into JSON-safe Python values.
    """

    if isinstance(data, Decimal):
        return float(data)

    if isinstance(data, datetime):
        return data.isoformat()

    if hasattr(data, "isoformat"):

        try:
            return data.isoformat()
        except Exception:
            pass

    if isinstance(data, list):

        return [
            make_json_safe(item)
            for item in data
        ]

    if isinstance(data, tuple):

        return [
            make_json_safe(item)
            for item in data
        ]

    if isinstance(data, dict):

        return {
            key: make_json_safe(value)
            for key, value in data.items()
        }

    return data


# ============================================================
# DATE VALIDATION
# ============================================================

def validate_date(date_value):

    try:

        return datetime.strptime(
            str(date_value),
            "%Y-%m-%d"
        ).date()

    except ValueError:

        raise ValueError(
            "Date must be in YYYY-MM-DD format."
        )


# ============================================================
# TOTAL REVENUE
# ============================================================

def get_total_revenue():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                )
            FROM sales
            """
        )

        result = cursor.fetchone()[0]

        return float(result or 0)

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TOTAL TRANSACTIONS
# ============================================================

def get_total_transactions():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM sales
            """
        )

        result = cursor.fetchone()[0]

        return int(result or 0)

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TODAY SALES
# ============================================================

def get_today_sales():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue,

                COUNT(*) AS transactions

            FROM sales

            WHERE DATE(sale_datetime)
                = CURDATE()
            """
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# YESTERDAY SALES
# ============================================================

def get_yesterday_sales():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue,

                COUNT(*) AS transactions

            FROM sales

            WHERE DATE(sale_datetime)
                = CURDATE() - INTERVAL 1 DAY
            """
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# THIS WEEK SALES
# ============================================================

def get_this_week_sales():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue,

                COUNT(*) AS transactions

            FROM sales

            WHERE YEARWEEK(
                sale_datetime,
                1
            ) = YEARWEEK(
                CURDATE(),
                1
            )
            """
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# THIS MONTH SALES
# ============================================================

def get_this_month_sales():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue,

                COUNT(*) AS transactions

            FROM sales

            WHERE YEAR(sale_datetime)
                = YEAR(CURDATE())

            AND MONTH(sale_datetime)
                = MONTH(CURDATE())
            """
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# LAST MONTH SALES
# ============================================================

def get_last_month_sales():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue,

                COUNT(*) AS transactions

            FROM sales

            WHERE YEAR(sale_datetime)
                = YEAR(
                    CURDATE()
                    - INTERVAL 1 MONTH
                )

            AND MONTH(sale_datetime)
                = MONTH(
                    CURDATE()
                    - INTERVAL 1 MONTH
                )
            """
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# BEST PRODUCT THIS WEEK
# ============================================================

def get_best_product_this_week():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                p.product_name,

                SUM(si.quantity)
                    AS quantity_sold,

                COALESCE(
                    SUM(si.total),
                    0
                ) AS revenue

            FROM sale_items si

            INNER JOIN products p
                ON si.product_id =
                   p.product_id

            INNER JOIN sales s
                ON si.sale_id =
                   s.sale_id

            WHERE YEARWEEK(
                s.sale_datetime,
                1
            ) = YEARWEEK(
                CURDATE(),
                1
            )

            GROUP BY
                p.product_id,
                p.product_name

            ORDER BY
                revenue DESC

            LIMIT 1
            """
        )

        result = cursor.fetchone()

        if not result:

            return {
                "message":
                    "No sales found for this week."
            }

        return make_json_safe(result)

    finally:

        cursor.close()
        connection.close()


# ============================================================
# MONTHLY COMPARISON
# ============================================================

def compare_this_month_last_month():

    this_month = get_this_month_sales()
    last_month = get_last_month_sales()

    current_revenue = float(
        this_month.get(
            "revenue",
            0
        )
    )

    previous_revenue = float(
        last_month.get(
            "revenue",
            0
        )
    )

    current_transactions = int(
        this_month.get(
            "transactions",
            0
        )
    )

    previous_transactions = int(
        last_month.get(
            "transactions",
            0
        )
    )

    if previous_revenue == 0:

        percentage_change = None

    else:

        percentage_change = (
            (
                current_revenue -
                previous_revenue
            )
            / previous_revenue
        ) * 100

    return make_json_safe({

        "this_month":
            this_month,

        "last_month":
            last_month,

        "percentage_change":
            percentage_change,

        "current_transactions":
            current_transactions,

        "previous_transactions":
            previous_transactions
    })


# ============================================================
# DATE RANGE SUMMARY
# ============================================================

def get_date_range_summary(
    start_date,
    end_date
):

    start = validate_date(start_date)
    end = validate_date(end_date)

    if start > end:

        raise ValueError(
            "Start date cannot be after end date."
        )

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue,

                COUNT(*) AS transactions

            FROM sales

            WHERE DATE(sale_datetime)
                BETWEEN %s AND %s
            """,
            (
                start,
                end
            )
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# DAILY SALES BY DATE RANGE
# ============================================================

def get_sales_by_date_range(
    start_date,
    end_date
):

    start = validate_date(start_date)
    end = validate_date(end_date)

    if start > end:

        raise ValueError(
            "Start date cannot be after end date."
        )

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                DATE(sale_datetime)
                    AS sale_date,

                COUNT(*)
                    AS transactions,

                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue

            FROM sales

            WHERE DATE(sale_datetime)
                BETWEEN %s AND %s

            GROUP BY
                DATE(sale_datetime)

            ORDER BY
                sale_date
            """,
            (
                start,
                end
            )
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# PREVIOUS PERIOD COMPARISON
# ============================================================

def compare_date_range_with_previous(
    start_date,
    end_date
):

    start = validate_date(start_date)
    end = validate_date(end_date)

    if start > end:

        raise ValueError(
            "Start date cannot be after end date."
        )

    period_days = (
        end - start
    ).days + 1

    previous_end = (
        start -
        timedelta(days=1)
    )

    previous_start = (
        previous_end -
        timedelta(
            days=period_days - 1
        )
    )

    current = get_date_range_summary(
        start,
        end
    )

    previous = get_date_range_summary(
        previous_start,
        previous_end
    )

    current_revenue = float(
        current.get(
            "revenue",
            0
        )
    )

    previous_revenue = float(
        previous.get(
            "revenue",
            0
        )
    )

    current_transactions = int(
        current.get(
            "transactions",
            0
        )
    )

    previous_transactions = int(
        previous.get(
            "transactions",
            0
        )
    )

    if previous_revenue > 0:

        revenue_change = (
            (
                current_revenue -
                previous_revenue
            )
            / previous_revenue
        ) * 100

    else:

        revenue_change = None

    if previous_transactions > 0:

        transaction_change = (
            (
                current_transactions -
                previous_transactions
            )
            / previous_transactions
        ) * 100

    else:

        transaction_change = None

    return make_json_safe({

        "current_period": {

            "start_date":
                str(start),

            "end_date":
                str(end),

            "revenue":
                current_revenue,

            "transactions":
                current_transactions
        },

        "previous_period": {

            "start_date":
                str(previous_start),

            "end_date":
                str(previous_end),

            "revenue":
                previous_revenue,

            "transactions":
                previous_transactions
        },

        "revenue_change":
            revenue_change,

        "transaction_change":
            transaction_change
    })


# ============================================================
# TOP PRODUCTS BY DATE RANGE
# ============================================================

def get_top_products_by_date_range(
    start_date,
    end_date
):

    start = validate_date(start_date)
    end = validate_date(end_date)

    if start > end:

        raise ValueError(
            "Start date cannot be after end date."
        )

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                p.product_name,

                SUM(si.quantity)
                    AS quantity_sold,

                COALESCE(
                    SUM(si.total),
                    0
                ) AS revenue

            FROM sale_items si

            INNER JOIN products p
                ON si.product_id =
                   p.product_id

            INNER JOIN sales s
                ON si.sale_id =
                   s.sale_id

            WHERE DATE(s.sale_datetime)
                BETWEEN %s AND %s

            GROUP BY
                p.product_id,
                p.product_name

            ORDER BY
                revenue DESC

            LIMIT 10
            """,
            (
                start,
                end
            )
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# PAYMENT ANALYSIS BY DATE RANGE
# ============================================================

def get_payment_analysis_by_date_range(
    start_date,
    end_date
):

    start = validate_date(start_date)
    end = validate_date(end_date)

    if start > end:

        raise ValueError(
            "Start date cannot be after end date."
        )

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                payment_method,

                COUNT(*)
                    AS transactions,

                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue

            FROM sales

            WHERE DATE(sale_datetime)
                BETWEEN %s AND %s

            GROUP BY
                payment_method

            ORDER BY
                revenue DESC
            """,
            (
                start,
                end
            )
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# REVENUE BY HOUR - DATE RANGE
# ============================================================

def get_revenue_by_hour_date_range(
    start_date,
    end_date
):

    start = validate_date(start_date)
    end = validate_date(end_date)

    if start > end:

        raise ValueError(
            "Start date cannot be after end date."
        )

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                HOUR(sale_datetime)
                    AS sale_hour,

                COUNT(*)
                    AS transactions,

                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue

            FROM sales

            WHERE DATE(sale_datetime)
                BETWEEN %s AND %s

            GROUP BY
                HOUR(sale_datetime)

            ORDER BY
                sale_hour
            """,
            (
                start,
                end
            )
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TOP PRODUCTS - ALL TIME
# ============================================================

def get_top_products():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                p.product_name,

                SUM(si.quantity)
                    AS quantity_sold,

                COALESCE(
                    SUM(si.total),
                    0
                ) AS revenue

            FROM sale_items si

            INNER JOIN products p
                ON si.product_id =
                   p.product_id

            GROUP BY
                p.product_id,
                p.product_name

            ORDER BY
                revenue DESC

            LIMIT 10
            """
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# REVENUE BY HOUR - ALL TIME
# ============================================================

def get_revenue_by_hour():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                HOUR(sale_datetime)
                    AS sale_hour,

                COUNT(*)
                    AS transactions,

                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue

            FROM sales

            GROUP BY
                HOUR(sale_datetime)

            ORDER BY
                sale_hour
            """
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# PAYMENT ANALYSIS - ALL TIME
# ============================================================

def get_payment_analysis():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                payment_method,

                COUNT(*)
                    AS transactions,

                COALESCE(
                    SUM(total_amount),
                    0
                ) AS revenue

            FROM sales

            GROUP BY
                payment_method

            ORDER BY
                revenue DESC
            """
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()



# ============================================================
# TOTAL COST OF SOLD PRODUCTS
# ============================================================

def get_total_cost():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(
                SUM(
                    si.quantity * COALESCE(p.cost_price, 0)
                ),
                0
            )
            FROM sale_items si
            INNER JOIN products p
                ON si.product_id = p.product_id
            """
        )

        return float(cursor.fetchone()[0] or 0)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# TOTAL PROFIT
# ============================================================

def get_total_profit():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        si.total -
                        (
                            si.quantity *
                            COALESCE(p.cost_price, 0)
                        )
                    ),
                    0
                )
            FROM sale_items si

            INNER JOIN products p
                ON si.product_id = p.product_id
            """
        )

        result = cursor.fetchone()[0]

        return float(result or 0)

    finally:

        cursor.close()
        connection.close()


# ============================================================
# PROFIT MARGIN
# ============================================================

def get_profit_margin():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(si.total), 0),
                COALESCE(
                    SUM(
                        si.total -
                        (
                            si.quantity *
                            COALESCE(p.cost_price, 0)
                        )
                    ),
                    0
                )
            FROM sale_items si

            INNER JOIN products p
                ON si.product_id = p.product_id
            """
        )

        result = cursor.fetchone()

        revenue = float(result[0] or 0)
        profit = float(result[1] or 0)

        if revenue <= 0:
            return 0.0

        return float(
            (profit / revenue) * 100
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# PROFIT SUMMARY
# ============================================================

def get_profit_summary():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------------
        # TOTAL REVENUE
        # Use sales.total_amount so it matches get_total_revenue()
        # --------------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_amount),
                    0
                )
            FROM sales
            """
        )

        revenue_result = cursor.fetchone()

        revenue = float(
            revenue_result[0] or 0
        )

        # --------------------------------------------------------
        # TOTAL COST
        # Calculate product cost from sale items
        # --------------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(
                        si.quantity *
                        COALESCE(p.cost_price, 0)
                    ),
                    0
                )
            FROM sale_items si

            INNER JOIN products p
                ON si.product_id = p.product_id
            """
        )

        cost_result = cursor.fetchone()

        cost = float(
            cost_result[0] or 0
        )

        # --------------------------------------------------------
        # TOTAL PROFIT
        # --------------------------------------------------------

        profit = revenue - cost

        # --------------------------------------------------------
        # PROFIT MARGIN
        # --------------------------------------------------------

        margin = (
            (profit / revenue) * 100
            if revenue > 0
            else 0.0
        )

        return make_json_safe(
            {
                "total_revenue": revenue,
                "total_cost": cost,
                "total_profit": profit,
                "profit_margin": margin
            }
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# PROFIT BY PRODUCT
# ============================================================

def get_profit_by_product(limit=10):

    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 10

    if limit <= 0:
        limit = 10

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query = f"""
            SELECT
                p.product_id,
                p.product_name,
                SUM(si.quantity) AS quantity_sold,

                COALESCE(
                    SUM(si.total),
                    0
                ) AS revenue,

                COALESCE(
                    SUM(
                        si.quantity *
                        COALESCE(p.cost_price, 0)
                    ),
                    0
                ) AS cost,

                COALESCE(
                    SUM(
                        si.total -
                        (
                            si.quantity *
                            COALESCE(p.cost_price, 0)
                        )
                    ),
                    0
                ) AS profit

            FROM sale_items si

            INNER JOIN products p
                ON si.product_id = p.product_id

            GROUP BY
                p.product_id,
                p.product_name

            ORDER BY profit DESC

            LIMIT {limit}
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        for row in rows:

            revenue = float(
                row.get("revenue", 0) or 0
            )

            profit = float(
                row.get("profit", 0) or 0
            )

            row["profit_margin"] = (
                (profit / revenue) * 100
                if revenue > 0
                else 0.0
            )

        return make_json_safe(rows)

    finally:
        cursor.close()
        connection.close()


# ============================================================
# MOST PROFITABLE PRODUCTS
# ============================================================

def get_most_profitable_products(limit=10):

    return get_profit_by_product(limit)


# ============================================================
# LEAST PROFITABLE PRODUCTS
# ============================================================

def get_least_profitable_products(limit=10):

    rows = get_profit_by_product(1000)

    rows = sorted(
        rows,
        key=lambda row: float(
            row.get("profit", 0) or 0
        )
    )

    return rows[:max(1, int(limit))]


# ============================================================
# DAILY PROFIT
# ============================================================

def get_daily_profit(days=30):

    try:
        days = int(days)
    except (ValueError, TypeError):
        days = 30

    if days <= 0:
        days = 30

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query = f"""
            SELECT
                DATE(s.sale_datetime) AS sale_date,

                COALESCE(
                    SUM(si.total),
                    0
                ) AS revenue,

                COALESCE(
                    SUM(
                        si.quantity *
                        COALESCE(p.cost_price, 0)
                    ),
                    0
                ) AS cost,

                COALESCE(
                    SUM(
                        si.total -
                        (
                            si.quantity *
                            COALESCE(p.cost_price, 0)
                        )
                    ),
                    0
                ) AS profit

            FROM sales s

            INNER JOIN sale_items si
                ON s.sale_id = si.sale_id

            INNER JOIN products p
                ON si.product_id = p.product_id

            WHERE DATE(s.sale_datetime)
                >= CURDATE()
                   - INTERVAL {days - 1} DAY

            GROUP BY DATE(s.sale_datetime)

            ORDER BY sale_date
        """

        cursor.execute(query)

        return make_json_safe(
            cursor.fetchall()
        )

    finally:
        cursor.close()
        connection.close()


# ============================================================
# MONTHLY PROFIT
# ============================================================

def get_monthly_profit(months=12):

    try:
        months = int(months)
    except (ValueError, TypeError):
        months = 12

    if months <= 0:
        months = 12

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        query = f"""
            SELECT

                YEAR(s.sale_datetime) AS sale_year,

                MONTH(s.sale_datetime) AS sale_month,

                DATE_FORMAT(
                    MIN(s.sale_datetime),
                    '%Y-%m'
                ) AS month,

                COALESCE(
                    SUM(si.total),
                    0
                ) AS revenue,

                COALESCE(
                    SUM(
                        si.quantity *
                        COALESCE(
                            p.cost_price,
                            0
                        )
                    ),
                    0
                ) AS cost,

                COALESCE(
                    SUM(
                        si.total -
                        (
                            si.quantity *
                            COALESCE(
                                p.cost_price,
                                0
                            )
                        )
                    ),
                    0
                ) AS profit

            FROM sales s

            INNER JOIN sale_items si
                ON s.sale_id = si.sale_id

            INNER JOIN products p
                ON si.product_id = p.product_id

            WHERE s.sale_datetime >=
                DATE_FORMAT(
                    CURDATE()
                    - INTERVAL {months - 1} MONTH,
                    '%Y-%m-01'
                )

            GROUP BY
                YEAR(s.sale_datetime),
                MONTH(s.sale_datetime)

            ORDER BY
                YEAR(s.sale_datetime),
                MONTH(s.sale_datetime)
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        for row in rows:

            revenue = float(
                row.get("revenue", 0) or 0
            )

            profit = float(
                row.get("profit", 0) or 0
            )

            row["profit_margin"] = (
                (profit / revenue) * 100
                if revenue > 0
                else 0.0
            )

        return make_json_safe(rows)

    finally:

        cursor.close()
        connection.close()

# ============================================================
# PROFIT BY DATE RANGE
# ============================================================

def get_profit_by_date_range(start_date, end_date):

    start = validate_date(start_date)
    end = validate_date(end_date)

    if start > end:
        raise ValueError(
            "Start date cannot be after end date."
        )

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT

                COALESCE(
                    SUM(si.total),
                    0
                ) AS revenue,

                COALESCE(
                    SUM(
                        si.quantity *
                        COALESCE(p.cost_price, 0)
                    ),
                    0
                ) AS cost,

                COALESCE(
                    SUM(
                        si.total -
                        (
                            si.quantity *
                            COALESCE(p.cost_price, 0)
                        )
                    ),
                    0
                ) AS profit,

                COUNT(
                    DISTINCT s.sale_id
                ) AS transactions

            FROM sales s

            INNER JOIN sale_items si
                ON s.sale_id = si.sale_id

            INNER JOIN products p
                ON si.product_id = p.product_id

            WHERE DATE(s.sale_datetime)
                BETWEEN %s AND %s
            """,
            (start, end)
        )

        result = cursor.fetchone()

        revenue = float(
            result.get("revenue", 0) or 0
        )

        profit = float(
            result.get("profit", 0) or 0
        )

        result["profit_margin"] = (
            (profit / revenue) * 100
            if revenue > 0
            else 0.0
        )

        return make_json_safe(result)

    finally:
        cursor.close()
        connection.close()



# ============================================================
# SALES ANOMALIES
# ============================================================

def get_sales_anomalies():

    anomalies = (
        detect_transaction_anomalies()
    )

    if anomalies is None:

        return {
            "anomaly_count": 0,
            "message":
                "No anomaly data available."
        }

    if anomalies.empty:

        return {
            "anomaly_count": 0,
            "message":
                "No significant sales anomalies detected."
        }

    if "sale_datetime" in anomalies.columns:

        anomalies["sale_datetime"] = (
            anomalies["sale_datetime"]
            .astype(str)
        )

    columns = [
        "sale_id",
        "sale_datetime",
        "total_amount",
        "z_score"
    ]

    available_columns = [
        column
        for column in columns
        if column in anomalies.columns
    ]

    results = (
        anomalies[
            available_columns
        ]
        .head(10)
        .to_dict(
            orient="records"
        )
    )

    return make_json_safe({

        "anomaly_count":
            int(len(anomalies)),

        "top_anomalies":
            results
    })


# ============================================================
# SALES FORECAST
# ============================================================

def get_sales_forecast():

    result = forecast_sales(7)

    return make_json_safe(result)


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

def get_business_insights():
    """
    Build the complete ShopSense AI business-intelligence summary.

    Includes:
    - Revenue
    - Transactions
    - Top products
    - Peak sales hour
    - Payment analysis
    - Sales anomalies
    - Sales forecast
    - Profit & Loss
    - Product profitability
    - Inventory health
    """

    total_revenue = get_total_revenue()

    total_transactions = get_total_transactions()

    top_products = get_top_products()

    revenue_by_hour = get_revenue_by_hour()

    payment_analysis = get_payment_analysis()

    anomalies = get_sales_anomalies()

    forecast = get_sales_forecast()

    # --------------------------------------------------------
    # PROFIT & LOSS
    # --------------------------------------------------------

    profit_summary = get_profit_summary()

    profit_by_product = get_profit_by_product(10)

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    inventory_summary = get_inventory_summary()

    # --------------------------------------------------------
    # GENERATE ENHANCED BUSINESS SUMMARY
    # --------------------------------------------------------

    summary = generate_business_summary(

        total_revenue=total_revenue,

        total_transactions=total_transactions,

        top_products=top_products,

        revenue_by_hour=revenue_by_hour,

        payment_analysis=payment_analysis,

        anomalies=anomalies,

        forecast=forecast,

        profit_summary=profit_summary,

        profit_by_product=profit_by_product,

        inventory_summary=inventory_summary
    )

    # Add the raw business metrics too, so the AI Assistant
    # and Dashboard can access the detailed values directly.

    if isinstance(summary, dict):

        summary["profit_summary"] = profit_summary

        summary["profit_by_product"] = profit_by_product

        summary["inventory_summary"] = inventory_summary

        summary["forecast"] = forecast

        summary["total_revenue"] = total_revenue

        summary["total_transactions"] = total_transactions

    return make_json_safe(summary)


# ============================================================
# FIND PRODUCT FOR SALE
# ============================================================

def get_product_for_sale(
    product_name: str
):

    if not product_name:
        return None

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                product_id,
                product_name,
                category,
                cost_price,
                selling_price,

                COALESCE(
                    stock_quantity,
                    0
                ) AS stock_quantity,

                COALESCE(
                    reorder_level,
                    10
                ) AS reorder_level

            FROM products

            WHERE LOWER(product_name)
                = LOWER(%s)

            LIMIT 1
            """,
            (
                product_name.strip(),
            )
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# RECORD NEW SALE
# ============================================================

def record_new_sale(
    product_name: str,
    quantity: int,
    payment_method: str
):

    if not product_name:

        return {
            "success": False,
            "message":
                "Product name is required."
        }

    product_name = str(
        product_name
    ).strip()

    if not product_name:

        return {
            "success": False,
            "message":
                "Product name is required."
        }

    try:

        quantity = int(quantity)

    except (
        ValueError,
        TypeError
    ):

        return {
            "success": False,
            "message":
                "Quantity must be a valid number."
        }

    if quantity <= 0:

        return {
            "success": False,
            "message":
                "Quantity must be greater than zero."
        }

    if not payment_method:

        return {
            "success": False,
            "message":
                "Payment method is required."
        }

    payment = str(
        payment_method
    ).strip().lower()

    allowed_methods = {
        "cash": "CASH",
        "upi": "UPI",
        "card": "CARD"
    }

    if payment not in allowed_methods:

        return {
            "success": False,
            "message":
                "Invalid payment method. "
                "Please use Cash, UPI or Card."
        }

    # --------------------------------------------------------
    # FIND PRODUCT
    # --------------------------------------------------------

    product = get_product_for_sale(
        product_name
    )

    if not product:

        return {
            "success": False,
            "message":
                f"Product '{product_name}' "
                "was not found in the products table."
        }

    # --------------------------------------------------------
    # CHECK STOCK
    # --------------------------------------------------------

    current_stock = int(
        product.get(
            "stock_quantity",
            0
        )
    )

    if current_stock < quantity:

        return {
            "success": False,
            "message":
                f"Insufficient stock for "
                f"{product['product_name']}. "
                f"Available stock: "
                f"{current_stock}"
        }

    # --------------------------------------------------------
    # CREATE SALE ITEMS
    # --------------------------------------------------------

    items = [
        {
            "product_name":
                product["product_name"],

            "quantity":
                quantity
        }
    ]

    # --------------------------------------------------------
    # ADD SALE
    # --------------------------------------------------------

    try:

        result = add_sale(

            items=items,

            payment_method=
                allowed_methods[payment]
        )

        return make_json_safe(
            result
        )

    except Exception as e:

        return {
            "success": False,
            "message":
                f"Failed to record sale: {str(e)}"
        }


# ============================================================
# INVENTORY SCHEMA CHECK
# ============================================================

def ensure_inventory_columns():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns

            WHERE table_schema = DATABASE()

            AND table_name = 'products'

            AND column_name = 'stock_quantity'
            """
        )

        has_stock = (
            cursor.fetchone()[0] > 0
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.columns

            WHERE table_schema = DATABASE()

            AND table_name = 'products'

            AND column_name = 'reorder_level'
            """
        )

        has_reorder = (
            cursor.fetchone()[0] > 0
        )

        if not has_stock:

            cursor.execute(
                """
                ALTER TABLE products

                ADD COLUMN
                    stock_quantity INT
                    NOT NULL DEFAULT 0
                """
            )

        if not has_reorder:

            cursor.execute(
                """
                ALTER TABLE products

                ADD COLUMN
                    reorder_level INT
                    NOT NULL DEFAULT 10
                """
            )

        connection.commit()

        return {
            "success": True,
            "message":
                "Inventory columns are ready."
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET ALL INVENTORY
# ============================================================

def get_inventory():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                product_id,

                product_name,

                category,

                cost_price,

                selling_price,

                COALESCE(
                    stock_quantity,
                    0
                ) AS stock_quantity,

                COALESCE(
                    reorder_level,
                    10
                ) AS reorder_level,

                (
                    COALESCE(
                        stock_quantity,
                        0
                    )
                    *
                    COALESCE(
                        cost_price,
                        0
                    )
                ) AS inventory_cost_value,

                (
                    COALESCE(
                        stock_quantity,
                        0
                    )
                    *
                    COALESCE(
                        selling_price,
                        0
                    )
                ) AS inventory_sales_value,

                CASE

                    WHEN COALESCE(
                        stock_quantity,
                        0
                    ) <= 0

                    THEN 'OUT OF STOCK'

                    WHEN COALESCE(
                        stock_quantity,
                        0
                    ) <= COALESCE(
                        reorder_level,
                        10
                    )

                    THEN 'LOW STOCK'

                    ELSE 'IN STOCK'

                END AS stock_status

            FROM products

            ORDER BY
                product_name
            """
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# LOW STOCK PRODUCTS
# ============================================================

def get_low_stock_products():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                product_id,

                product_name,

                category,

                stock_quantity,

                reorder_level,

                selling_price,

                cost_price

            FROM products

            WHERE COALESCE(
                stock_quantity,
                0
            ) > 0

            AND COALESCE(
                stock_quantity,
                0
            ) <= COALESCE(
                reorder_level,
                10
            )

            ORDER BY
                stock_quantity ASC,

                product_name
            """
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# OUT OF STOCK PRODUCTS
# ============================================================

def get_out_of_stock_products():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                product_id,

                product_name,

                category,

                stock_quantity,

                reorder_level,

                selling_price,

                cost_price

            FROM products

            WHERE COALESCE(
                stock_quantity,
                0
            ) <= 0

            ORDER BY
                product_name
            """
        )

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# INVENTORY SUMMARY
# ============================================================

def get_inventory_summary():

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                COUNT(*)
                    AS total_products,

                COALESCE(
                    SUM(
                        COALESCE(
                            stock_quantity,
                            0
                        )
                    ),
                    0
                ) AS total_units,

                COALESCE(
                    SUM(
                        COALESCE(
                            stock_quantity,
                            0
                        )
                        *
                        COALESCE(
                            cost_price,
                            0
                        )
                    ),
                    0
                ) AS inventory_cost_value,

                COALESCE(
                    SUM(
                        COALESCE(
                            stock_quantity,
                            0
                        )
                        *
                        COALESCE(
                            selling_price,
                            0
                        )
                    ),
                    0
                ) AS inventory_sales_value,

                COALESCE(
                    SUM(
                        CASE

                            WHEN COALESCE(
                                stock_quantity,
                                0
                            ) <= 0

                            THEN 1

                            ELSE 0

                        END
                    ),
                    0
                ) AS out_of_stock,

                COALESCE(
                    SUM(
                        CASE

                            WHEN COALESCE(
                                stock_quantity,
                                0
                            ) > 0

                            AND COALESCE(
                                stock_quantity,
                                0
                            ) <= COALESCE(
                                reorder_level,
                                10
                            )

                            THEN 1

                            ELSE 0

                        END
                    ),
                    0
                ) AS low_stock

            FROM products
            """
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET SINGLE PRODUCT STOCK
# ============================================================

def get_product_stock(
    product_name: str
):

    if not product_name:
        return None

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                product_id,

                product_name,

                category,

                cost_price,

                selling_price,

                COALESCE(
                    stock_quantity,
                    0
                ) AS stock_quantity,

                COALESCE(
                    reorder_level,
                    10
                ) AS reorder_level,

                CASE

                    WHEN COALESCE(
                        stock_quantity,
                        0
                    ) <= 0

                    THEN 'OUT OF STOCK'

                    WHEN COALESCE(
                        stock_quantity,
                        0
                    ) <= COALESCE(
                        reorder_level,
                        10
                    )

                    THEN 'LOW STOCK'

                    ELSE 'IN STOCK'

                END AS stock_status

            FROM products

            WHERE LOWER(product_name)
                = LOWER(%s)

            LIMIT 1
            """,
            (
                product_name.strip(),
            )
        )

        return make_json_safe(
            cursor.fetchone()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# RESTOCK PRODUCT
# ============================================================

def restock_product(
    product_name: str,
    quantity: int
):

    if not product_name:

        return {
            "success": False,
            "message":
                "Product name is required."
        }

    try:

        quantity = int(quantity)

    except (
        ValueError,
        TypeError
    ):

        return {
            "success": False,
            "message":
                "Quantity must be a valid number."
        }

    if quantity <= 0:

        return {
            "success": False,
            "message":
                "Restock quantity must be greater than zero."
        }

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT

                product_id,

                product_name,

                COALESCE(
                    stock_quantity,
                    0
                ) AS stock_quantity

            FROM products

            WHERE LOWER(product_name)
                = LOWER(%s)

            LIMIT 1
            """,
            (
                product_name.strip(),
            )
        )

        product = cursor.fetchone()

        if not product:

            return {
                "success": False,
                "message":
                    f"Product '{product_name}' "
                    "was not found."
            }

        old_stock = int(
            product["stock_quantity"]
        )

        new_stock = (
            old_stock +
            quantity
        )

        cursor.execute(
            """
            UPDATE products

            SET stock_quantity = %s

            WHERE product_id = %s
            """,
            (
                new_stock,
                product["product_id"]
            )
        )

        connection.commit()

        return {
            "success": True,

            "product_id":
                product["product_id"],

            "product_name":
                product["product_name"],

            "previous_stock":
                old_stock,

            "added_quantity":
                quantity,

            "current_stock":
                new_stock,

            "message":
                "Stock successfully updated."
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message":
                f"Failed to update stock: {str(e)}"
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# UPDATE REORDER LEVEL
# ============================================================

def update_reorder_level(
    product_name: str,
    reorder_level: int
):

    if not product_name:

        return {
            "success": False,
            "message":
                "Product name is required."
        }

    try:

        reorder_level = int(
            reorder_level
        )

    except (
        ValueError,
        TypeError
    ):

        return {
            "success": False,
            "message":
                "Reorder level must be a valid number."
        }

    if reorder_level < 0:

        return {
            "success": False,
            "message":
                "Reorder level cannot be negative."
        }

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                product_id,
                product_name
            FROM products
            WHERE LOWER(product_name)
                = LOWER(%s)
            LIMIT 1
            """,
            (
                product_name.strip(),
            )
        )

        product = cursor.fetchone()

        if not product:

            return {
                "success": False,
                "message":
                    f"Product '{product_name}' "
                    "was not found."
            }

        cursor.execute(
            """
            UPDATE products

            SET reorder_level = %s

            WHERE product_id = %s
            """,
            (
                reorder_level,
                product["product_id"]
            )
        )

        connection.commit()

        return {
            "success": True,

            "product_id":
                product["product_id"],

            "product_name":
                product["product_name"],

            "reorder_level":
                reorder_level,

            "message":
                "Reorder level successfully updated."
        }

    except Exception as e:

        connection.rollback()

        return {
            "success": False,
            "message":
                f"Failed to update reorder level: {str(e)}"
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# SALES HISTORY
# ============================================================

def get_sales_history(
    limit=100
):

    try:
        limit = int(limit)
    except (
        ValueError,
        TypeError
    ):
        limit = 100

    if limit <= 0:
        limit = 100

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        # LIMIT cannot safely be used as a normal
        # parameter in every MySQL configuration,
        # so validate it and insert the integer.

        query = f"""
            SELECT

                sale_id,

                sale_datetime,

                total_amount,

                payment_method

            FROM sales

            ORDER BY
                sale_datetime DESC

            LIMIT {limit}
        """

        cursor.execute(query)

        return make_json_safe(
            cursor.fetchall()
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# GET SALE DETAILS
# ============================================================

def get_sale_details(
    sale_id
):

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    try:

        # ----------------------------------------------------
        # SALE INFORMATION
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT

                sale_id,

                sale_datetime,

                total_amount,

                payment_method

            FROM sales

            WHERE sale_id = %s

            LIMIT 1
            """,
            (
                sale_id,
            )
        )

        sale = cursor.fetchone()

        if not sale:
            return None

        # ----------------------------------------------------
        # SALE ITEMS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT

                p.product_name,

                si.quantity,

                si.unit_price,

                si.discount,

                si.total

            FROM sale_items si

            INNER JOIN products p
                ON si.product_id =
                   p.product_id

            WHERE si.sale_id = %s

            ORDER BY
                si.sale_item_id
            """,
            (
                sale_id,
            )
        )

        items = cursor.fetchall()

        sale["items"] = items

        return make_json_safe(
            sale
        )

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TEST INVENTORY FUNCTIONS
# ============================================================

def test_inventory_functions():

    print("\n" + "=" * 60)
    print("             INVENTORY TEST")
    print("=" * 60)

    print("\n1. INVENTORY")

    try:

        inventory = get_inventory()

        for item in inventory:
            print(item)

    except Exception as e:

        print(
            "Inventory error:",
            e
        )

    print("\n2. LOW STOCK")

    try:

        result = (
            get_low_stock_products()
        )

        if result:

            for item in result:
                print(item)

        else:

            print(
                "No low-stock products."
            )

    except Exception as e:

        print(
            "Low-stock error:",
            e
        )

    print("\n3. OUT OF STOCK")

    try:

        result = (
            get_out_of_stock_products()
        )

        if result:

            for item in result:
                print(item)

        else:

            print(
                "No out-of-stock products."
            )

    except Exception as e:

        print(
            "Out-of-stock error:",
            e
        )

    print("\n4. INVENTORY SUMMARY")

    try:

        print(
            get_inventory_summary()
        )

    except Exception as e:

        print(
            "Summary error:",
            e
        )


# ============================================================
# TEST ALL TOOLS
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("        SHOP SENSE AI DATABASE TEST")
    print("=" * 60)

    tests = [

        (
            "TOTAL REVENUE",
            get_total_revenue
        ),

        (
            "TOTAL TRANSACTIONS",
            get_total_transactions
        ),

        (
            "TODAY SALES",
            get_today_sales
        ),

        (
            "YESTERDAY SALES",
            get_yesterday_sales
        ),

        (
            "THIS WEEK SALES",
            get_this_week_sales
        ),

        (
            "THIS MONTH SALES",
            get_this_month_sales
        ),

        (
            "LAST MONTH SALES",
            get_last_month_sales
        ),

        (
            "BEST PRODUCT THIS WEEK",
            get_best_product_this_week
        ),

        (
            "MONTHLY COMPARISON",
            compare_this_month_last_month
        ),

        (
            "TOP PRODUCTS",
            get_top_products
        ),

        (
            "REVENUE BY HOUR",
            get_revenue_by_hour
        ),

        (
            "PAYMENT ANALYSIS",
            get_payment_analysis
        ),

        (
            "SALES ANOMALIES",
            get_sales_anomalies
        ),

        (
            "SALES FORECAST",
            get_sales_forecast
        ),

        (
            "BUSINESS INSIGHTS",
            get_business_insights
        )
    ]

    for number, (
        name,
        function
    ) in enumerate(
        tests,
        start=1
    ):

        print(
            f"\n{number}. {name}"
        )

        print("-" * 40)

        try:

            result = function()

            print(result)

        except Exception as e:

            print(
                f"ERROR: {e}"
            )

    # ========================================================
    # DATE RANGE TEST
    # ========================================================

    print(
        "\n16. DATE RANGE TEST"
    )

    print("-" * 40)

    try:

        today = datetime.now().date()

        start_date = (
            today -
            timedelta(days=6)
        )

        print(
            "Date range:",
            start_date,
            "to",
            today
        )

        print(
            "\nSummary:"
        )

        print(
            get_date_range_summary(
                start_date,
                today
            )
        )

        print(
            "\nDaily Sales:"
        )

        for row in get_sales_by_date_range(
            start_date,
            today
        ):

            print(row)

        print(
            "\nPrevious Period:"
        )

        print(
            compare_date_range_with_previous(
                start_date,
                today
            )
        )

        print(
            "\nTop Products:"
        )

        for row in get_top_products_by_date_range(
            start_date,
            today
        ):

            print(row)

        print(
            "\nPayment Analysis:"
        )

        for row in get_payment_analysis_by_date_range(
            start_date,
            today
        ):

            print(row)

        print(
            "\nRevenue By Hour:"
        )

        for row in get_revenue_by_hour_date_range(
            start_date,
            today
        ):

            print(row)

    except Exception as e:

        print(
            "Date range error:",
            e
        )

    # ========================================================
    # INVENTORY TEST
    # ========================================================

    print(
        "\n17. INVENTORY TEST"
    )

    print("-" * 40)

    try:

        test_inventory_functions()

    except Exception as e:

        print(
            "Inventory test error:",
            e
        )

    # ========================================================
    # SALES HISTORY TEST
    # ========================================================

    print(
        "\n18. SALES HISTORY"
    )

    print("-" * 40)

    try:

        print(
            get_sales_history(10)
        )

    except Exception as e:

        print(
            "Sales history error:",
            e
        )

    print("\n" + "=" * 60)
    print("              TEST COMPLETED")
    print("=" * 60)