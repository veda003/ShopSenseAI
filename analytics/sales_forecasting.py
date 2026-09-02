import os

import mysql.connector
import pandas as pd
import numpy as np

from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression


load_dotenv()


# ==========================================
# MYSQL CONNECTION
# ==========================================

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


# ==========================================
# LOAD DAILY SALES
# ==========================================

def get_daily_sales():

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            DATE(sale_datetime) AS sale_date,
            SUM(total_amount) AS revenue
        FROM sales
        GROUP BY DATE(sale_datetime)
        ORDER BY sale_date
    """

    try:

        cursor.execute(query)

        rows = cursor.fetchall()

        df = pd.DataFrame(
            rows,
            columns=["sale_date", "revenue"]
        )

        return df

    finally:

        cursor.close()
        connection.close()


# ==========================================
# FORECAST NEXT 7 DAYS
# ==========================================

def forecast_sales(days=7):

    try:
        days = int(days)
    except (ValueError, TypeError):
        days = 7

    if days <= 0:

        return {
            "status": "error",
            "message": "Forecast days must be greater than 0."
        }

    df = get_daily_sales()

    if df.empty:

        return {
            "status": "error",
            "message": "No sales data available."
        }

    # ======================================
    # CONVERT DATE
    # ======================================

    df["sale_date"] = pd.to_datetime(
        df["sale_date"]
    )

    # ======================================
    # CONVERT REVENUE
    # ======================================

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="coerce"
    )

    # ======================================
    # REMOVE INVALID VALUES
    # ======================================

    df = df.dropna(
        subset=[
            "sale_date",
            "revenue"
        ]
    ).copy()

    if df.empty:

        return {
            "status": "error",
            "message": "No valid sales data available."
        }

    # ======================================
    # NEED ENOUGH HISTORICAL DATA
    # ======================================

    if len(df) < 7:

        return {
            "status": "error",
            "message": (
                "At least 7 days of sales data "
                "are required."
            )
        }

    # ======================================
    # CREATE TIME INDEX
    # ======================================

    df["day_number"] = np.arange(
        len(df),
        dtype=float
    )

    X = df[
        ["day_number"]
    ]

    y = df[
        "revenue"
    ]

    # ======================================
    # TRAIN MODEL
    # ======================================

    model = LinearRegression()

    model.fit(
        X,
        y
    )

    # ======================================
    # FUTURE DAYS
    # ======================================

    last_day = float(
        df["day_number"].iloc[-1]
    )

    future_days = np.arange(
        last_day + 1,
        last_day + days + 1,
        dtype=float
    )

    future_dates = pd.date_range(
        start=(
            df["sale_date"].max()
            + pd.Timedelta(days=1)
        ),
        periods=days,
        freq="D"
    )

    # ======================================
    # PREDICT
    # ======================================

    # Use the same feature name as the training
    # DataFrame to avoid sklearn feature-name warnings.
    future_X = pd.DataFrame(
        {
            "day_number": future_days
        }
    )

    predictions = model.predict(
        future_X
    )

    # ======================================
    # DON'T ALLOW NEGATIVE REVENUE
    # ======================================

    predictions = np.maximum(
        predictions,
        0
    )

    # ======================================
    # BUILD FORECAST
    # ======================================

    forecast = []

    for date, prediction in zip(
        future_dates,
        predictions
    ):

        forecast.append(
            {
                "date": date.strftime(
                    "%Y-%m-%d"
                ),
                "predicted_revenue": round(
                    float(prediction),
                    2
                )
            }
        )

    return {
        "status": "success",
        "historical_days": len(df),
        "forecast_days": days,
        "forecast": forecast
    }


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    print(
        "\n" + "=" * 60
    )

    print(
        "       SHOP SENSE AI - SALES FORECAST"
    )

    print(
        "=" * 60
    )

    result = forecast_sales(7)

    print(
        "\nForecast Result:"
    )

    if result["status"] == "success":

        print(
            f"\nHistorical days: "
            f"{result['historical_days']}"
        )

        print(
            f"Forecast days: "
            f"{result['forecast_days']}"
        )

        print(
            "\nNext 7 Days:"
        )

        for row in result["forecast"]:

            print(
                f"{row['date']}  →  "
                f"₹{row['predicted_revenue']:,.2f}"
            )

    else:

        print(
            result["message"]
        )

    print(
        "\n" + "=" * 60
    )
