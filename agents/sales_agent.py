import os
import sys
import re

from dotenv import load_dotenv
from google import genai


# ============================================================
# PROJECT PATH
# ============================================================

AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(AGENTS_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if AGENTS_DIR not in sys.path:
    sys.path.insert(0, AGENTS_DIR)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")


# ============================================================
# SQL TOOLS
# ============================================================

from sql_tools import (
    get_total_revenue,
    get_total_transactions,

    get_today_sales,
    get_yesterday_sales,
    get_this_week_sales,
    get_this_month_sales,
    get_last_month_sales,

    get_best_product_this_week,
    compare_this_month_last_month,

    get_top_products,
    get_revenue_by_hour,
    get_payment_analysis,

    get_sales_anomalies,
    get_sales_forecast,
    get_business_insights,

    # Inventory
    get_low_stock_products,
    get_out_of_stock_products,
    get_inventory_summary,

    # Profit
    get_profit_summary,
    get_profit_by_product,
    get_least_profitable_products,
    get_daily_profit,
    get_monthly_profit,
    get_profit_by_date_range,

    # Sale entry
    record_new_sale,
)


# ============================================================
# SYSTEM INSTRUCTION
# ============================================================

SYSTEM_INSTRUCTION = """
You are ShopSense AI, an intelligent sales analyst for a
local tea and bakery shop.

You analyze REAL sales data from the ShopSense MySQL database.

RULES:
1. Never invent sales numbers.
2. Use real database results.
3. Currency is Indian Rupees (₹).
4. Clearly distinguish actual sales from forecast predictions.
5. Forecasts are estimates based on historical sales patterns.
6. For business advice, use the available analytics results.
7. Never invent products, quantities, prices or payment methods.
8. A sale requires product name, quantity and payment method.
9. Payment methods are Cash, UPI and Card.
10. Keep answers concise and easy to understand.
"""


# ============================================================
# SAFE GEMINI TOOLS
#
# IMPORTANT:
# Do NOT put functions with optional/default parameters here.
# The Google GenAI automatic function-calling schema can fail
# on signatures such as get_profit_by_product(limit=10).
#
# Questions that need parameterized functions are handled
# directly in ask_ai().
# ============================================================

TOOLS = [
    get_total_revenue,
    get_total_transactions,

    get_today_sales,
    get_yesterday_sales,
    get_this_week_sales,
    get_this_month_sales,
    get_last_month_sales,

    get_best_product_this_week,
    compare_this_month_last_month,

    get_top_products,
    get_revenue_by_hour,
    get_payment_analysis,

    get_sales_anomalies,
    get_sales_forecast,
    get_business_insights,

    get_low_stock_products,
    get_out_of_stock_products,
    get_inventory_summary,

    get_profit_summary,
]


# ============================================================
# GEMINI CLIENT
# ============================================================

def create_client():
    return genai.Client(api_key=api_key)


def create_chat():
    """
    Create a fresh Gemini client and chat.
    Returns: client, chat
    """

    client = create_client()

    chat = client.chats.create(
        model="gemini-3.5-flash-lite",
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "tools": TOOLS,
        },
    )

    return client, chat


# ============================================================
# HELPERS
# ============================================================

def money(value):
    return f"₹{float(value or 0):,.2f}"


def safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def normalize_payment(value):
    value = str(value or "").strip().lower()

    mapping = {
        "cash": "Cash",
        "upi": "UPI",
        "card": "Card",
    }

    return mapping.get(value)


# ============================================================
# SALE MESSAGE PARSER
# ============================================================

def parse_sale_request(message):
    """
    Parse natural-language sale requests.

    Supported examples:
        Record 1 Coffee paid by Card.
        Add 3 Samosa paid by Cash.
        Record 2 Tea paid by UPI.
        Create a sale of 5 Coffee paid by Card.
        Enter 1 Tea using UPI.
    """

    text = str(message or "").strip()

    if not text:
        return None

    lower = text.lower()

    sale_words = (
        "record",
        "add",
        "create",
        "enter",
        "save",
        "sell",
    )

    if not any(word in lower for word in sale_words):
        return None

    # Payment method
    payment_match = re.search(
        r"\b(?:paid\s+by|using|with|payment\s+(?:method|by)?)\s*"
        r"(cash|upi|card)\b",
        lower,
        re.IGNORECASE,
    )

    if not payment_match:
        # Also support "... Card" at the end.
        payment_match = re.search(
            r"\b(cash|upi|card)\s*[\.\!]*$",
            lower,
            re.IGNORECASE,
        )

    payment = (
        normalize_payment(payment_match.group(1))
        if payment_match
        else None
    )

    # Quantity
    quantity_match = re.search(
        r"\b(?:record|add|create|enter|save|sell)"
        r"(?:\s+a)?"
        r"(?:\s+sale)?"
        r"(?:\s+of)?"
        r"\s+(\d+)\b",
        lower,
        re.IGNORECASE,
    )

    if not quantity_match:
        quantity_match = re.search(
            r"\b(\d+)\s+"
            r"(?:[a-zA-Z][a-zA-Z ]*?)"
            r"\s+(?:paid\s+by|using|with)\b",
            lower,
            re.IGNORECASE,
        )

    quantity = (
        safe_int(quantity_match.group(1))
        if quantity_match
        else None
    )

    # Product name
    product = None

    if quantity_match:
        start = quantity_match.end()

        if payment_match:
            end = payment_match.start()
        else:
            end = len(text)

        product_text = text[start:end]

        product_text = re.sub(
            r"^\s*(?:of|for)\s+",
            "",
            product_text,
            flags=re.IGNORECASE,
        )

        product_text = re.sub(
            r"\s*(?:paid\s+by|using|with)\s*$",
            "",
            product_text,
            flags=re.IGNORECASE,
        )

        product_text = product_text.strip(" .,!:-")

        if product_text:
            product = product_text

    # Alternate form:
    # "Record Coffee 1 paid by Card"
    if not product:
        alternate = re.search(
            r"(?:record|add|create|enter|save|sell)"
            r"\s+(?:a\s+)?(?:sale\s+of\s+)?"
            r"([a-zA-Z][a-zA-Z ]*?)"
            r"\s+(\d+)\s+"
            r"(?:paid\s+by|using|with)\s+"
            r"(cash|upi|card)",
            text,
            re.IGNORECASE,
        )

        if alternate:
            product = alternate.group(1).strip()
            quantity = safe_int(alternate.group(2))
            payment = normalize_payment(alternate.group(3))

    # If the sentence clearly looks like a sale request,
    # return a partial result so ask_ai can request missing data.
    if any(word in lower for word in sale_words):
        return {
            "product_name": product,
            "quantity": quantity,
            "payment_method": payment,
        }

    return None


def handle_sale_request(message):
    parsed = parse_sale_request(message)

    if parsed is None:
        return None

    product = parsed.get("product_name")
    quantity = parsed.get("quantity")
    payment = parsed.get("payment_method")

    missing = []

    if not product:
        missing.append("product name")

    if quantity is None:
        missing.append("quantity")

    if not payment:
        missing.append("payment method")

    if missing:
        if len(missing) == 1:
            return (
                "I can record the sale, but I need the "
                f"**{missing[0]}** first."
            )

        return (
            "I can record the sale, but I need these details: "
            + ", ".join(missing)
            + "."
        )

    try:
        result = record_new_sale(
            product_name=product,
            quantity=quantity,
            payment_method=payment,
        )

        if not isinstance(result, dict):
            return "The sale could not be recorded."

        if result.get("success"):
            sale_id = result.get("sale_id", "N/A")
            total = safe_float(result.get("total_amount", 0))
            actual_payment = result.get(
                "payment_method",
                payment,
            )

            items = result.get("items", [])

            lines = [
                "✅ **Sale recorded successfully!**",
                "",
                f"**Sale ID:** {sale_id}",
                f"**Payment:** {actual_payment}",
                f"**Total:** {money(total)}",
            ]

            if items:
                item = items[0]
                lines.append(
                    f"**Product:** {item.get('product_name', product)}"
                )
                lines.append(
                    f"**Quantity:** {safe_int(item.get('quantity', quantity))}"
                )

            return "\n".join(lines)

        return (
            "❌ **Sale could not be recorded.**\n\n"
            + str(
                result.get(
                    "message",
                    "Unknown database error.",
                )
            )
        )

    except Exception as e:
        return f"❌ Error recording sale: {e}"


# ============================================================
# DIRECT SALES ANALYTICS
# ============================================================

def direct_sales_answer(lower):
    # --------------------------------------------------------
    # TOP PRODUCTS
    # --------------------------------------------------------

    if (
        "top 5 products" in lower
        or "top five products" in lower
    ):
        rows = get_top_products()

        if not rows:
            return "No product sales data is available."

        lines = ["🏆 **Top 5 Products by Revenue**", ""]

        for index, item in enumerate(rows[:5], start=1):
            lines.append(
                f"{index}. **{item.get('product_name', 'Unknown')}** — "
                f"{money(item.get('revenue', 0))}"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # TOP PRODUCTS GENERAL
    # --------------------------------------------------------

    if (
        "top products" in lower
        or "best selling products" in lower
    ):
        rows = get_top_products()

        if not rows:
            return "No product sales data is available."

        lines = ["🏆 **Top Products by Revenue**", ""]

        for index, item in enumerate(rows[:10], start=1):
            lines.append(
                f"{index}. **{item.get('product_name', 'Unknown')}** — "
                f"{money(item.get('revenue', 0))}"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # PRODUCT WITH MOST REVENUE
    # --------------------------------------------------------

    if (
        "most revenue" in lower
        or "highest revenue product" in lower
        or "product generates the most revenue" in lower
        or "highest revenue-generating product" in lower
    ):
        rows = get_top_products()

        if not rows:
            return "No product sales data is available."

        item = rows[0]

        return (
            f"🏆 **{item.get('product_name', 'Unknown')}** "
            f"generates the most revenue with "
            f"**{money(item.get('revenue', 0))}**."
        )

    # --------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------

    if (
        "payment method generates the most revenue" in lower
        or "payment method has the most revenue" in lower
        or "highest payment revenue" in lower
        or "best payment method" in lower
    ):
        rows = get_payment_analysis()

        if not rows:
            return "No payment analysis data is available."

        best = rows[0]

        lines = [
            "💳 **Payment Method Analysis**",
            "",
            f"**{str(best.get('payment_method', 'Unknown')).upper()}** "
            f"generates the most revenue: "
            f"**{money(best.get('revenue', 0))}**.",
            "",
        ]

        for index, row in enumerate(rows, start=1):
            lines.append(
                f"{index}. {str(row.get('payment_method', 'Unknown')).upper()} — "
                f"{money(row.get('revenue', 0))} "
                f"({safe_int(row.get('transactions', 0)):,} transactions)"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # BUSIEST HOUR
    # --------------------------------------------------------

    if (
        "busiest sales hour" in lower
        or "busiest hour" in lower
        or "peak sales hour" in lower
        or "strongest sales hour" in lower
    ):
        rows = get_revenue_by_hour()

        if not rows:
            return "No hourly sales data is available."

        best = max(
            rows,
            key=lambda x: safe_float(x.get("revenue", 0)),
        )

        hour = safe_int(best.get("sale_hour", 0))

        return (
            f"⏰ Your busiest sales hour is **{hour:02d}:00** "
            f"with revenue of **{money(best.get('revenue', 0))}** "
            f"across **{safe_int(best.get('transactions', 0)):,} transactions**."
        )

    # --------------------------------------------------------
    # TOTAL REVENUE
    # --------------------------------------------------------

    if (
        "total revenue" in lower
        or "overall revenue" in lower
        or lower == "revenue"
        or lower == "sales revenue"
    ):
        revenue = get_total_revenue()

        return (
            f"💰 **Total Revenue:** **{money(revenue)}**"
        )

    # --------------------------------------------------------
    # TRANSACTIONS
    # --------------------------------------------------------

    if (
        "how many transactions" in lower
        or "total transactions" in lower
        or "number of transactions" in lower
    ):
        transactions = get_total_transactions()

        return (
            f"🧾 **Total Transactions:** "
            f"**{safe_int(transactions):,}**"
        )

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    if (
        "sales today" in lower
        or "today's sales" in lower
        or "today sales" in lower
        or lower == "today"
    ):
        data = get_today_sales()

        return (
            "📅 **Today's Sales**\n\n"
            f"Revenue: **{money(data.get('revenue', 0))}**\n"
            f"Transactions: **{safe_int(data.get('transactions', 0)):,}**"
        )

    # --------------------------------------------------------
    # YESTERDAY
    # --------------------------------------------------------

    if (
        "sales yesterday" in lower
        or "yesterday's sales" in lower
        or "yesterday sales" in lower
        or lower == "yesterday"
    ):
        data = get_yesterday_sales()

        return (
            "📅 **Yesterday's Sales**\n\n"
            f"Revenue: **{money(data.get('revenue', 0))}**\n"
            f"Transactions: **{safe_int(data.get('transactions', 0)):,}**"
        )

    # --------------------------------------------------------
    # THIS WEEK
    # --------------------------------------------------------

    if (
        "sales this week" in lower
        or "this week's sales" in lower
        or "this week sales" in lower
        or "how are my sales this week" in lower
    ):
        data = get_this_week_sales()

        return (
            "📆 **This Week's Sales**\n\n"
            f"Revenue: **{money(data.get('revenue', 0))}**\n"
            f"Transactions: **{safe_int(data.get('transactions', 0)):,}**"
        )

    # --------------------------------------------------------
    # THIS MONTH
    # --------------------------------------------------------

    if (
        "sales this month" in lower
        or "this month's sales" in lower
        or "this month sales" in lower
        or "how are my sales this month" in lower
    ):
        data = get_this_month_sales()

        return (
            "📅 **This Month's Sales**\n\n"
            f"Revenue: **{money(data.get('revenue', 0))}**\n"
            f"Transactions: **{safe_int(data.get('transactions', 0)):,}**"
        )

    # --------------------------------------------------------
    # LAST MONTH
    # --------------------------------------------------------

    if (
        "sales last month" in lower
        or "last month's sales" in lower
        or "last month sales" in lower
    ):
        data = get_last_month_sales()

        return (
            "📅 **Last Month's Sales**\n\n"
            f"Revenue: **{money(data.get('revenue', 0))}**\n"
            f"Transactions: **{safe_int(data.get('transactions', 0)):,}**"
        )

    # --------------------------------------------------------
    # BEST PRODUCT THIS WEEK
    # --------------------------------------------------------

    if (
        "best product this week" in lower
        or "best product for this week" in lower
    ):
        data = get_best_product_this_week()

        if not data:
            return "No product sales were found for this week."

        return (
            "🏆 **Best Product This Week**\n\n"
            f"**{data.get('product_name', 'Unknown')}**\n\n"
            f"Quantity Sold: **{safe_int(data.get('quantity_sold', 0)):,}**\n"
            f"Revenue: **{money(data.get('revenue', 0))}**"
        )

    # --------------------------------------------------------
    # MONTH COMPARISON
    # --------------------------------------------------------

    if (
        "compare this month with last month" in lower
        or "compare this month and last month" in lower
        or "compare this month to last month" in lower
    ):
        data = compare_this_month_last_month()

        current = data.get("this_month", {})
        previous = data.get("last_month", {})
        change = data.get("percentage_change")

        change_text = (
            "N/A"
            if change is None
            else f"{safe_float(change):+.2f}%"
        )

        return (
            "📊 **This Month vs Last Month**\n\n"
            f"This Month: **{money(current.get('revenue', 0))}**\n"
            f"Last Month: **{money(previous.get('revenue', 0))}**\n"
            f"Revenue Change: **{change_text}**"
        )

    # --------------------------------------------------------
    # LOW STOCK
    # --------------------------------------------------------

    if (
        "low in stock" in lower
        or "low stock" in lower
        or "need restocking" in lower
        or "low-stock products" in lower
    ):
        rows = get_low_stock_products()

        if not rows:
            return "📦 **No products are currently low in stock.**"

        lines = ["⚠️ **Low-Stock Products**", ""]

        for index, item in enumerate(rows, start=1):
            lines.append(
                f"{index}. **{item.get('product_name', 'Unknown')}** — "
                f"Stock: {safe_int(item.get('stock_quantity', 0))}, "
                f"Reorder Level: {safe_int(item.get('reorder_level', 0))}"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # OUT OF STOCK
    # --------------------------------------------------------

    if (
        "out of stock" in lower
        or "out-of-stock" in lower
    ):
        rows = get_out_of_stock_products()

        if not rows:
            return "✅ **No products are currently out of stock.**"

        lines = ["❌ **Out-of-Stock Products**", ""]

        for index, item in enumerate(rows, start=1):
            lines.append(
                f"{index}. **{item.get('product_name', 'Unknown')}**"
            )

        return "\n".join(lines)

    # --------------------------------------------------------
    # INVENTORY SUMMARY
    # --------------------------------------------------------

    if (
        "inventory summary" in lower
        or "inventory status" in lower
        or "stock summary" in lower
    ):
        data = get_inventory_summary()

        return (
            "📦 **Inventory Summary**\n\n"
            f"Products: **{safe_int(data.get('total_products', 0))}**\n"
            f"Units: **{safe_int(float(data.get('total_units', 0))):,}**\n"
            f"Low Stock: **{safe_int(float(data.get('low_stock', 0)))}**\n"
            f"Out of Stock: **{safe_int(float(data.get('out_of_stock', 0)))}**"
        )

    # --------------------------------------------------------
    # FORECAST
    # --------------------------------------------------------

    if (
        "forecast" in lower
        or "predict my sales" in lower
        or "predicted sales" in lower
        or "next 7 days" in lower
    ):
        return forecast_answer()

    # --------------------------------------------------------
    # DECREASING FORECAST / RECOMMENDATION
    # --------------------------------------------------------

    if (
        "decreasing forecast" in lower
        or "forecast is decreasing" in lower
        or "what should i do about the forecast" in lower
        or "what should i do about decreasing" in lower
        or "forecast recommendation" in lower
    ):
        return forecast_recommendation()

    # --------------------------------------------------------
    # BUSINESS INSIGHTS
    # --------------------------------------------------------

    if (
        "business insights" in lower
        or "overall business" in lower
        or "overall insights" in lower
        or "business performance" in lower
    ):
        return business_insights_answer()

    # --------------------------------------------------------
    # ANOMALIES
    # --------------------------------------------------------

    if (
        "unusual sales" in lower
        or "sales anomalies" in lower
        or "anomalies" in lower
    ):
        data = get_sales_anomalies()

        count = safe_int(
            data.get("anomaly_count", 0)
            if isinstance(data, dict)
            else 0
        )

        if count:
            return (
                f"🚨 **Sales Anomalies**\n\n"
                f"{count} unusual sales transactions were detected. "
                f"These should be reviewed."
            )

        return "✅ **No significant sales anomalies were detected.**"

    # --------------------------------------------------------
    # PROFIT
    # --------------------------------------------------------

    if (
        "profit" in lower
        or "profitability" in lower
        or "profit margin" in lower
        or "total cost" in lower
    ):
        return profit_answer(lower)

    return None


# ============================================================
# FORECAST
# ============================================================

def forecast_answer():
    data = get_sales_forecast()

    if not isinstance(data, dict):
        return "Forecast data is unavailable."

    if data.get("status") != "success":
        return str(
            data.get(
                "message",
                "Forecast could not be generated.",
            )
        )

    rows = data.get("forecast", [])

    if not rows:
        return "No forecast values were returned."

    total = sum(
        safe_float(row.get("predicted_revenue", 0))
        for row in rows
    )

    average = total / len(rows)

    first = safe_float(rows[0].get("predicted_revenue", 0))
    last = safe_float(rows[-1].get("predicted_revenue", 0))

    if last > first:
        trend = "📈 Increasing"
    elif last < first:
        trend = "📉 Decreasing"
    else:
        trend = "➡️ Stable"

    lines = [
        "🔮 **7-Day Sales Forecast**",
        "",
        f"Expected Revenue: **{money(total)}**",
        f"Average Daily Revenue: **{money(average)}**",
        f"Trend: **{trend}**",
        "",
    ]

    for row in rows:
        lines.append(
            f"• **{row.get('date', '')}:** "
            f"{money(row.get('predicted_revenue', 0))}"
        )

    lines.extend([
        "",
        "⚠️ Forecast values are estimates based on historical "
        "sales patterns and are not guaranteed.",
    ])

    return "\n".join(lines)


def forecast_recommendation():
    data = get_sales_forecast()

    if (
        not isinstance(data, dict)
        or data.get("status") != "success"
    ):
        return "The forecast is currently unavailable."

    rows = data.get("forecast", [])

    if not rows:
        return "No forecast values are available."

    first = safe_float(rows[0].get("predicted_revenue", 0))
    last = safe_float(rows[-1].get("predicted_revenue", 0))

    total = sum(
        safe_float(row.get("predicted_revenue", 0))
        for row in rows
    )

    change = (
        ((last - first) / first) * 100
        if first
        else 0
    )

    top_products = get_top_products()
    hours = get_revenue_by_hour()

    best_product = (
        top_products[0]
        if top_products
        else {}
    )

    peak_hour = (
        max(
            hours,
            key=lambda x: safe_float(x.get("revenue", 0)),
        )
        if hours
        else {}
    )

    product_name = best_product.get(
        "product_name",
        "your best-selling products",
    )

    peak = safe_int(
        peak_hour.get("sale_hour", 0)
    )

    return (
        "📉 **Forecast Recommendation**\n\n"
        f"The forecast decreases from **{money(first)}** "
        f"to **{money(last)}** per day "
        f"({change:+.2f}%).\n\n"
        f"Expected revenue for the next 7 days is approximately "
        f"**{money(total)}**.\n\n"
        "### 💡 Recommended Actions\n\n"
        f"1. 🏆 Promote **{product_name}**, your current leading product.\n"
        "2. 💰 Consider promotions, bundles or pricing reviews "
        "for weaker-performing products.\n"
        "3. 📦 Maintain enough stock of high-demand products.\n"
        f"4. ⏰ Focus promotions around your strongest sales hour, "
        f"approximately **{peak:02d}:00**.\n"
        "5. 📊 Compare actual daily revenue with the forecast and "
        "adjust your strategy if the decline continues.\n\n"
        "⚠️ The forecast is an estimate, not a guarantee."
    )


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

def business_insights_answer():
    data = get_business_insights()

    if not isinstance(data, dict):
        return "Business insights are currently unavailable."

    lines = ["💡 **Overall Business Insights**", ""]

    profit = data.get("profit_summary", {})
    inventory = data.get("inventory_summary", {})

    if profit:
        lines.extend([
            "### 💰 Financial Overview",
            f"Revenue: **{money(profit.get('total_revenue', 0))}**",
            f"Cost: **{money(profit.get('total_cost', 0))}**",
            f"Profit: **{money(profit.get('total_profit', 0))}**",
            f"Profit Margin: **{safe_float(profit.get('profit_margin', 0)):.2f}%**",
            "",
        ])

    if inventory:
        lines.extend([
            "### 📦 Inventory",
            f"Products: **{safe_int(float(inventory.get('total_products', 0)))}**",
            f"Units: **{safe_int(float(inventory.get('total_units', 0))):,}**",
            f"Low Stock: **{safe_int(float(inventory.get('low_stock', 0)))}**",
            f"Out of Stock: **{safe_int(float(inventory.get('out_of_stock', 0)))}**",
            "",
        ])

    insights = data.get("insights", [])

    if insights:
        lines.append("### 🧠 Key Insights")

        for item in insights[:10]:
            if isinstance(item, dict):
                category = item.get("category", "Insight")
                message = item.get("insight", "")
                lines.append(
                    f"• **{category}:** {message}"
                )

        lines.append("")

    recommendations = data.get("recommendations", [])

    if recommendations:
        lines.append("### 💡 Recommended Actions")

        for item in recommendations[:10]:
            if isinstance(item, dict):
                category = item.get(
                    "category",
                    "Recommendation",
                )
                message = item.get(
                    "recommendation",
                    "",
                )
                lines.append(
                    f"• **{category}:** {message}"
                )

    return "\n".join(lines)


# ============================================================
# PROFIT
# ============================================================

def profit_answer(lower):
    if (
        "most profitable" in lower
        or "highest profit" in lower
        or "best profit" in lower
    ):
        rows = get_profit_by_product(10)

        if not rows:
            return "No product profitability data is available."

        item = rows[0]

        return (
            "🏆 **Most Profitable Product**\n\n"
            f"**{item.get('product_name', 'Unknown')}**\n\n"
            f"Revenue: {money(item.get('revenue', 0))}\n"
            f"Cost: {money(item.get('cost', 0))}\n"
            f"Profit: {money(item.get('profit', 0))}\n"
            f"Profit Margin: {safe_float(item.get('profit_margin', 0)):.2f}%"
        )

    if (
        "least profitable" in lower
        or "lowest profit" in lower
        or "worst profit" in lower
    ):
        rows = get_least_profitable_products(10)

        if not rows:
            return "No product profitability data is available."

        item = rows[0]

        return (
            "📉 **Least Profitable Product**\n\n"
            f"**{item.get('product_name', 'Unknown')}**\n\n"
            f"Revenue: {money(item.get('revenue', 0))}\n"
            f"Cost: {money(item.get('cost', 0))}\n"
            f"Profit: {money(item.get('profit', 0))}\n"
            f"Profit Margin: {safe_float(item.get('profit_margin', 0)):.2f}%"
        )

    if (
        "profit by product" in lower
        or "profitable products" in lower
        or "product profitability" in lower
    ):
        rows = get_profit_by_product(10)

        if not rows:
            return "No product profitability data is available."

        lines = ["💎 **Product Profitability**", ""]

        for index, item in enumerate(rows, start=1):
            lines.append(
                f"{index}. **{item.get('product_name', 'Unknown')}** — "
                f"Profit {money(item.get('profit', 0))} "
                f"({safe_float(item.get('profit_margin', 0)):.2f}%)"
            )

        return "\n".join(lines)

    if (
        "monthly profit" in lower
        or "profit this month" in lower
    ):
        rows = get_monthly_profit(12)

        if not rows:
            return "No monthly profit data is available."

        current = rows[-1]

        return (
            f"📆 **Monthly Profit — {current.get('month', '')}**\n\n"
            f"Revenue: {money(current.get('revenue', 0))}\n"
            f"Cost: {money(current.get('cost', 0))}\n"
            f"Profit: {money(current.get('profit', 0))}\n"
            f"Profit Margin: {safe_float(current.get('profit_margin', 0)):.2f}%"
        )

    if "daily profit" in lower:
        rows = get_daily_profit(30)

        if not rows:
            return "No daily profit data is available."

        current = rows[-1]

        return (
            f"📅 **Latest Daily Profit — {current.get('sale_date', '')}**\n\n"
            f"Revenue: {money(current.get('revenue', 0))}\n"
            f"Cost: {money(current.get('cost', 0))}\n"
            f"Profit: {money(current.get('profit', 0))}"
        )

    summary = get_profit_summary()

    return (
        "📈 **Profit Summary**\n\n"
        f"Revenue: **{money(summary.get('total_revenue', 0))}**\n"
        f"Cost: **{money(summary.get('total_cost', 0))}**\n"
        f"Profit: **{money(summary.get('total_profit', 0))}**\n"
        f"Profit Margin: **{safe_float(summary.get('profit_margin', 0)):.2f}%**"
    )


# ============================================================
# MAIN AI ROUTER
# ============================================================

def ask_ai(chat, user_message):
    """
    Main ShopSense AI router.

    Common business questions are answered directly from MySQL.
    Gemini is used only when no direct route matches.
    """

    if chat is None:
        raise ValueError("AI chat session is not available.")

    message = str(user_message or "").strip()

    if not message:
        return "Please enter a question."

    lower = message.lower().strip()

    # --------------------------------------------------------
    # SALE ENTRY FIRST
    # --------------------------------------------------------

    sale_result = handle_sale_request(message)

    if sale_result is not None:
        return sale_result

    # --------------------------------------------------------
    # DIRECT ANALYTICS
    # --------------------------------------------------------

    try:
        answer = direct_sales_answer(lower)

        if answer is not None:
            return answer

    except Exception as e:
        print(f"Direct analytics error: {e}")
        # Fall through to Gemini for non-critical requests.

    # --------------------------------------------------------
    # GEMINI FALLBACK
    # --------------------------------------------------------

    response = chat.send_message(message)

    if getattr(response, "text", None):
        return response.text

    return "I couldn't generate an answer for that question."


# ============================================================
# TERMINAL TEST MODE
# ============================================================

if __name__ == "__main__":

    client = None
    chat = None

    try:
        client, chat = create_chat()

        print("=" * 60)
        print("       🏪 SHOP SENSE AI - SALES AGENT")
        print("=" * 60)
        print("Type 'exit' to stop.\n")

        while True:

            user_input = input("You: ").strip()

            if user_input.lower() == "exit":
                break

            if not user_input:
                continue

            try:
                answer = ask_ai(chat, user_input)

                print("\n🤖 ShopSense AI:")
                print(answer)
                print()

            except Exception as e:
                print("\n❌ Error:")
                print(e)
                print()

    finally:

        if client is not None:
            try:
                client.close()
            except Exception:
                pass
