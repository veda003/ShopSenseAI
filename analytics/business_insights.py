import pandas as pd


def _money(value):
    """Format a numeric value as Indian currency."""
    try:
        return f"₹{float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def generate_business_summary(
    total_revenue,
    total_transactions,
    top_products,
    revenue_by_hour,
    payment_analysis,
    anomalies,
    forecast,
    profit_summary=None,
    profit_by_product=None,
    inventory_summary=None
):
    """
    Combine sales, profitability, inventory and forecast analytics
    into a structured business intelligence summary.

    The last three parameters are optional so existing callers remain
    compatible with the original function.
    """

    insights = []
    recommendations = []

    total_revenue = float(total_revenue or 0)
    total_transactions = int(total_transactions or 0)

    # ==========================================
    # AVERAGE TRANSACTION VALUE
    # ==========================================

    if total_transactions > 0:
        average_transaction = (
            total_revenue / total_transactions
        )

        insights.append({
            "category": "Revenue",
            "insight": (
                f"Average transaction value is "
                f"{_money(average_transaction)}."
            )
        })

    # ==========================================
    # TOTAL REVENUE
    # ==========================================

    insights.append({
        "category": "Revenue",
        "insight": (
            f"Total revenue is {_money(total_revenue)} "
            f"across {total_transactions:,} transactions."
        )
    })

    # ==========================================
    # TOP PRODUCT
    # ==========================================

    if top_products:
        top_product = top_products[0]

        product_name = top_product.get(
            "product_name",
            "Unknown"
        )

        revenue = float(
            top_product.get("revenue", 0) or 0
        )

        insights.append({
            "category": "Product",
            "insight": (
                f"{product_name} is the highest "
                f"revenue-generating product with "
                f"{_money(revenue)} revenue."
            )
        })

        recommendations.append({
            "category": "Product",
            "recommendation": (
                f"Maintain sufficient stock of {product_name} "
                "because it is currently the leading "
                "revenue-generating product."
            )
        })

    # ==========================================
    # PROFIT & LOSS
    # ==========================================

    if isinstance(profit_summary, dict):
        total_cost = float(
            profit_summary.get("total_cost", 0) or 0
        )

        total_profit = float(
            profit_summary.get("total_profit", 0) or 0
        )

        profit_margin = float(
            profit_summary.get("profit_margin", 0) or 0
        )

        insights.append({
            "category": "Profit",
            "insight": (
                f"Total cost is {_money(total_cost)}, "
                f"total profit is {_money(total_profit)}, "
                f"with a profit margin of "
                f"{profit_margin:.2f}%."
            )
        })

        if profit_margin < 20:
            recommendation = (
                "Profit margin is relatively low. Review product "
                "costs, pricing and discounts to improve profitability."
            )
        elif profit_margin < 40:
            recommendation = (
                "Profitability is moderate. Focus on high-margin "
                "products and control product costs."
            )
        else:
            recommendation = (
                "Profit margin is strong. Continue prioritizing "
                "profitable products while maintaining sales volume."
            )

        recommendations.append({
            "category": "Profit",
            "recommendation": recommendation
        })

    # ==========================================
    # MOST / LEAST PROFITABLE PRODUCTS
    # ==========================================

    if profit_by_product:
        valid_products = [
            item for item in profit_by_product
            if isinstance(item, dict)
        ]

        if valid_products:
            most_profitable = max(
                valid_products,
                key=lambda x: float(
                    x.get("profit", 0) or 0
                )
            )

            least_profitable = min(
                valid_products,
                key=lambda x: float(
                    x.get("profit", 0) or 0
                )
            )

            most_name = most_profitable.get(
                "product_name", "Unknown"
            )
            most_profit = float(
                most_profitable.get("profit", 0) or 0
            )
            most_margin = float(
                most_profitable.get("profit_margin", 0) or 0
            )

            least_name = least_profitable.get(
                "product_name", "Unknown"
            )
            least_profit = float(
                least_profitable.get("profit", 0) or 0
            )
            least_margin = float(
                least_profitable.get("profit_margin", 0) or 0
            )

            insights.append({
                "category": "Profitability",
                "insight": (
                    f"{most_name} is the most profitable product "
                    f"with {_money(most_profit)} profit and a "
                    f"{most_margin:.2f}% margin."
                )
            })

            insights.append({
                "category": "Profitability",
                "insight": (
                    f"{least_name} is the least profitable product "
                    f"with {_money(least_profit)} profit and a "
                    f"{least_margin:.2f}% margin."
                )
            })

            if most_name != least_name:
                recommendations.append({
                    "category": "Profitability",
                    "recommendation": (
                        f"Prioritize {most_name} for profitability "
                        f"and review the pricing or cost structure "
                        f"of {least_name}."
                    )
                })

    # ==========================================
    # PEAK SALES HOUR
    # ==========================================

    if revenue_by_hour:
        peak_hour = max(
            revenue_by_hour,
            key=lambda x: float(
                x.get("revenue", 0) or 0
            )
        )

        hour = peak_hour.get(
            "sale_hour", "Unknown"
        )

        revenue = float(
            peak_hour.get("revenue", 0) or 0
        )

        insights.append({
            "category": "Peak Hour",
            "insight": (
                f"The strongest sales hour is {hour}:00 "
                f"with revenue of {_money(revenue)}."
            )
        })

        recommendations.append({
            "category": "Sales Timing",
            "recommendation": (
                f"Ensure adequate staff and product availability "
                f"around the {hour}:00 peak sales period."
            )
        })

    # ==========================================
    # PAYMENT METHOD
    # ==========================================

    if payment_analysis:
        payment = max(
            payment_analysis,
            key=lambda x: float(
                x.get("revenue", 0) or 0
            )
        )

        method = payment.get(
            "payment_method", "Unknown"
        )

        revenue = float(
            payment.get("revenue", 0) or 0
        )

        insights.append({
            "category": "Payment",
            "insight": (
                f"{method} generates the highest payment "
                f"revenue at {_money(revenue)}."
            )
        })

    # ==========================================
    # INVENTORY
    # ==========================================

    if isinstance(inventory_summary, dict):
        low_stock = float(
            inventory_summary.get("low_stock", 0) or 0
        )

        out_of_stock = float(
            inventory_summary.get("out_of_stock", 0) or 0
        )

        total_products = float(
            inventory_summary.get("total_products", 0) or 0
        )

        insights.append({
            "category": "Inventory",
            "insight": (
                f"Inventory contains {int(total_products):,} products, "
                f"with {int(low_stock):,} low-stock products and "
                f"{int(out_of_stock):,} out-of-stock products."
            )
        })

        if out_of_stock > 0:
            recommendation = (
                f"{int(out_of_stock)} product(s) are out of stock. "
                "Restock them as soon as possible."
            )
        elif low_stock > 0:
            recommendation = (
                f"{int(low_stock)} product(s) are at low stock. "
                "Review and restock them before they run out."
            )
        else:
            recommendation = (
                "No low-stock or out-of-stock products are currently reported."
            )

        recommendations.append({
            "category": "Inventory",
            "recommendation": recommendation
        })

    # ==========================================
    # ANOMALIES
    # ==========================================

    if isinstance(anomalies, dict):
        anomaly_count = anomalies.get(
            "anomaly_count", 0
        )

        if anomaly_count > 0:
            insights.append({
                "category": "Anomaly",
                "insight": (
                    f"{anomaly_count} unusual sales transactions "
                    "were detected. These should be reviewed."
                )
            })

            recommendations.append({
                "category": "Anomaly",
                "recommendation": (
                    "Review the detected unusual transactions "
                    "to identify possible sales or data issues."
                )
            })
        else:
            insights.append({
                "category": "Anomaly",
                "insight": (
                    "No significant sales anomalies were detected."
                )
            })

    # ==========================================
    # FORECAST
    # ==========================================

    if isinstance(forecast, dict):
        if forecast.get("status") == "success":
            forecast_data = forecast.get(
                "forecast", []
            )

            if forecast_data:
                total_forecast = sum(
                    float(
                        item.get(
                            "predicted_revenue", 0
                        ) or 0
                    )
                    for item in forecast_data
                )

                average_forecast = (
                    total_forecast / len(forecast_data)
                )

                insights.append({
                    "category": "Forecast",
                    "insight": (
                        f"Expected revenue for the next "
                        f"{len(forecast_data)} days is approximately "
                        f"{_money(total_forecast)}, averaging "
                        f"{_money(average_forecast)} per day."
                    )
                })

                if len(forecast_data) >= 2:
                    first_prediction = float(
                        forecast_data[0].get(
                            "predicted_revenue", 0
                        ) or 0
                    )

                    last_prediction = float(
                        forecast_data[-1].get(
                            "predicted_revenue", 0
                        ) or 0
                    )

                    if last_prediction > first_prediction:
                        trend = "increasing"
                        recommendation = (
                            "The forecast shows an increasing sales trend. "
                            "Prepare enough inventory to support expected demand."
                        )
                    elif last_prediction < first_prediction:
                        trend = "decreasing"
                        recommendation = (
                            "The forecast shows a decreasing sales trend. "
                            "Consider promotions or reviewing underperforming products."
                        )
                    else:
                        trend = "stable"
                        recommendation = (
                            "The forecast is relatively stable. Maintain "
                            "current inventory and sales strategies."
                        )

                    insights.append({
                        "category": "Forecast Trend",
                        "insight": (
                            f"The forecast trend is {trend}, from "
                            f"{_money(first_prediction)} to "
                            f"{_money(last_prediction)} per day."
                        )
                    })

                    recommendations.append({
                        "category": "Forecast",
                        "recommendation": recommendation
                    })

    # ==========================================
    # FINAL RESULT
    # ==========================================

    return {
        "total_revenue": round(
            total_revenue,
            2
        ),
        "total_transactions": total_transactions,
        "insights": insights,
        "recommendations": recommendations
    }
