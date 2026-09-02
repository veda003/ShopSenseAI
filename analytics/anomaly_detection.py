import os
import mysql.connector
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )


def load_sales_data():

    connection = get_connection()

    query = """
        SELECT
            sale_id,
            sale_datetime,
            total_amount,
            payment_method
        FROM sales
        ORDER BY sale_datetime
    """

    df = pd.read_sql(query, connection)

    connection.close()

    return df


def detect_transaction_anomalies():

    df = load_sales_data()

    # Calculate statistics
    mean = df["total_amount"].mean()
    std = df["total_amount"].std()

    # Z-score
    df["z_score"] = (
        (df["total_amount"] - mean) / std
    )

    # Transactions with absolute z-score > 3
    anomalies = df[
        df["z_score"].abs() > 3
    ].copy()

    anomalies = anomalies.sort_values(
        "z_score",
        ascending=False
    )

    return anomalies


if __name__ == "__main__":

    print("=" * 60)
    print("       SHOP SENSE AI - ANOMALY DETECTION")
    print("=" * 60)

    anomalies = detect_transaction_anomalies()

    print("\nNumber of anomalies detected:")
    print(len(anomalies))

    print("\nTop anomalies:")

    if len(anomalies) > 0:

        print(
            anomalies[
                [
                    "sale_id",
                    "sale_datetime",
                    "total_amount",
                    "z_score"
                ]
            ].head(10).to_string(index=False)
        )

    else:

        print("No major anomalies detected.")