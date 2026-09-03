import os
import sys
from datetime import date, timedelta
from io import BytesIO

import streamlit as st
import pandas as pd


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# IMPORT SQL TOOLS
# ============================================================

from agents.sql_tools import (
    # Basic Sales
    get_total_revenue,
    get_total_transactions,

    # Date Sales
    get_today_sales,
    get_yesterday_sales,
    get_this_week_sales,
    get_this_month_sales,
    get_last_month_sales,

    # Product / Sales Analysis
    get_best_product_this_week,
    compare_this_month_last_month,
    get_top_products,
    get_revenue_by_hour,
    get_payment_analysis,

    # Advanced Analytics
    get_sales_anomalies,
    get_sales_forecast,
    get_business_insights,

    # Date Range
    get_sales_by_date_range,
    get_date_range_summary,
    get_top_products_by_date_range,
    get_payment_analysis_by_date_range,
    get_revenue_by_hour_date_range,
    compare_date_range_with_previous,

    # Sales History
    get_sales_history,
    get_sale_details,

    # Inventory
    get_inventory,
    get_low_stock_products,
    get_out_of_stock_products,
    get_inventory_summary,
    get_product_stock,
    restock_product,
    update_reorder_level,

    # Profit & Loss
    get_profit_summary,
    get_profit_by_product,
    get_least_profitable_products,
    get_daily_profit,
    get_monthly_profit,
    get_profit_by_date_range,

    # Sales Entry
    record_new_sale,
)

from agents.sales_entry import add_sale
from agents.sales_agent import create_chat, ask_ai
from agents.auth import authenticate_user

from utils.invoice import generate_invoice

from agents.permissions import (
    is_admin,
    can_create_sale,
    can_view_inventory,
    can_use_ai,
)



# ============================================================
# PERFORMANCE / DATA CACHING
# ============================================================

# Read-only analytics are cached briefly because the deployed app
# connects to Aiven MySQL over the internet. Write operations such
# as New Sale and Restock are NOT cached.

@st.cache_data(ttl=300, show_spinner=False)
def cached_total_revenue():
    return get_total_revenue()


@st.cache_data(ttl=300, show_spinner=False)
def cached_total_transactions():
    return get_total_transactions()


@st.cache_data(ttl=300, show_spinner=False)
def cached_top_products():
    return get_top_products()


@st.cache_data(ttl=300, show_spinner=False)
def cached_revenue_by_hour():
    return get_revenue_by_hour()


@st.cache_data(ttl=300, show_spinner=False)
def cached_payment_analysis():
    return get_payment_analysis()


@st.cache_data(ttl=300, show_spinner=False)
def cached_profit_summary():
    return get_profit_summary()


@st.cache_data(ttl=300, show_spinner=False)
def cached_profit_by_product(limit=10):
    return get_profit_by_product(limit)


@st.cache_data(ttl=300, show_spinner=False)
def cached_monthly_profit(months=12):
    return get_monthly_profit(months)


@st.cache_data(ttl=300, show_spinner=False)
def cached_inventory_summary():
    return get_inventory_summary()


@st.cache_data(ttl=600, show_spinner=False)
def cached_sales_forecast():
    return get_sales_forecast()


@st.cache_data(ttl=600, show_spinner=False)
def cached_business_insights():
    return get_business_insights()


@st.cache_data(ttl=300, show_spinner=False)
def cached_date_range_summary(start_date, end_date):
    return get_date_range_summary(start_date, end_date)


# ============================================================
# CACHE CLEARING
# ============================================================

def clear_read_cache():
    """Clear cached read-only analytics after a database write."""
    try:
        cached_total_revenue.clear()
        cached_total_transactions.clear()
        cached_top_products.clear()
        cached_revenue_by_hour.clear()
        cached_payment_analysis.clear()
        cached_profit_summary.clear()
        cached_profit_by_product.clear()
        cached_monthly_profit.clear()
        cached_inventory_summary.clear()
        cached_sales_forecast.clear()
        cached_business_insights.clear()
        cached_date_range_summary.clear()
    except Exception:
        # Cache helpers may not all exist during the first import.
        pass


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ShopSense AI",
    page_icon="🏪",
    layout="wide",
)
# ============================================================
# PROFESSIONAL SHOP SENSE AI THEME
# ============================================================

st.markdown("""
<style>

    /* ========================================================
       SHOPSENSE AI - PROFESSIONAL VISUAL THEME
       Reference palette:
       Charcoal / Cream / White / Muted Gold
       ======================================================== */

    :root {
        --ss-charcoal: #181818;
        --ss-charcoal-2: #222222;
        --ss-charcoal-3: #2c2c2c;

        --ss-cream: #f4f0e7;
        --ss-white: #ffffff;

        --ss-gold: #d8b36e;
        --ss-gold-light: #efd7a7;

        --ss-dark: #171717;
        --ss-text: #202020;
        --ss-muted: #55514a;

        --ss-border: #ded9d0;
    }


    /* ========================================================
       APPLICATION BACKGROUND
       ======================================================== */

    .stApp {
        background: #f6f5f2 !important;
        color: var(--ss-text) !important;
        font-family:
            "Segoe UI",
            "Inter",
            Arial,
            sans-serif !important;
    }

    .main {
        background: #f6f5f2 !important;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2.75rem !important;
        padding-right: 2.75rem !important;
        max-width: 1500px !important;
    }


    /* ========================================================
       GLOBAL TEXT - DARK / BOLD
       ======================================================== */

    h1 {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.8px !important;
    }

    h2 {
        color: #151515 !important;
        -webkit-text-fill-color: #151515 !important;
        font-size: 1.55rem !important;
        font-weight: 850 !important;
        letter-spacing: -0.35px !important;
    }

    h3 {
        color: #202020 !important;
        -webkit-text-fill-color: #202020 !important;
        font-size: 1.2rem !important;
        font-weight: 850 !important;
    }

    .main p,
    .main label,
    .main label p,
    .main .stMarkdown {
        color: #48443f !important;
        -webkit-text-fill-color: #48443f !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    hr {
        border: none !important;
        border-top: 1px solid #ded9d0 !important;
        margin: 1.4rem 0 !important;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background:
            linear-gradient(
                180deg,
                #151515 0%,
                #222222 100%
            ) !important;
        border-right: 1px solid #303030 !important;
    }

    section[data-testid="stSidebar"] * {
        color: #f3f0e9 !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 900 !important;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: #c9c4bb !important;
        -webkit-text-fill-color: #c9c4bb !important;
        font-weight: 600 !important;
    }

    section[data-testid="stSidebar"] hr {
        border-top-color: #3a3a3a !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 5px !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 9px 11px !important;
        border-radius: 9px !important;
        font-weight: 750 !important;
        transition: 0.18s ease !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: #2b2b2b !important;
    }


    /* ========================================================
       BUTTONS - WHITE SURFACE MATCH
       ======================================================== */

    .stButton > button,
    .stDownloadButton > button {
        min-height: 42px !important;
        border-radius: 10px !important;
        border: 1px solid #d4d0c8 !important;
        background: #ffffff !important;
        color: #161616 !important;
        -webkit-text-fill-color: #161616 !important;
        font-weight: 850 !important;
        box-shadow: 0 2px 8px rgba(23,23,23,0.05) !important;
        transition: 0.18s ease !important;
    }

    .stButton > button *,
    .stButton > button p,
    .stButton > button span,
    .stDownloadButton > button *,
    .stDownloadButton > button p,
    .stDownloadButton > button span {
        color: #161616 !important;
        -webkit-text-fill-color: #161616 !important;
        font-weight: 850 !important;
        opacity: 1 !important;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: #fbfaf7 !important;
        border-color: #bdb7aa !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 7px 18px rgba(23,23,23,0.10) !important;
    }

    /* Primary = reference muted gold */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {
        background:
            linear-gradient(
                135deg,
                #efd39b 0%,
                #d5a85c 100%
            ) !important;
        border: 1px solid #d2a55a !important;
        color: #171717 !important;
        -webkit-text-fill-color: #171717 !important;
        font-weight: 900 !important;
    }

    .stButton > button[kind="primary"] *,
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span,
    .stButton > button[data-testid="baseButton-primary"] *,
    .stButton > button[data-testid="baseButton-primary"] p,
    .stButton > button[data-testid="baseButton-primary"] span {
        color: #171717 !important;
        -webkit-text-fill-color: #171717 !important;
        font-weight: 900 !important;
    }

    /* Sidebar buttons remain dark */
    section[data-testid="stSidebar"] .stButton > button {
        background: #2a2a2a !important;
        border-color: #414141 !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    section[data-testid="stSidebar"] .stButton > button *,
    section[data-testid="stSidebar"] .stButton > button p,
    section[data-testid="stSidebar"] .stButton > button span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 850 !important;
    }


    /* ========================================================
       INPUTS
       ======================================================== */

    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #202020 !important;
        -webkit-text-fill-color: #202020 !important;
        border: 1px solid #d7d2c9 !important;
        border-radius: 9px !important;
        font-weight: 650 !important;
    }

    .stTextInput input::placeholder,
    .stNumberInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #88837b !important;
        -webkit-text-fill-color: #88837b !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }

    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stDateInput input:focus,
    .stTextArea textarea:focus {
        border-color: #d1a457 !important;
        box-shadow:
            0 0 0 2px rgba(209,164,87,0.13) !important;
    }

    .stTextInput label,
    .stTextInput label p,
    .stNumberInput label,
    .stNumberInput label p,
    .stDateInput label,
    .stDateInput label p,
    .stSelectbox label,
    .stSelectbox label p,
    .stTextArea label,
    .stTextArea label p {
        color: #2b2926 !important;
        -webkit-text-fill-color: #2b2926 !important;
        font-weight: 800 !important;
        opacity: 1 !important;
    }

    div[data-baseweb="select"] *,
    div[data-baseweb="select"] input {
        color: #202020 !important;
        -webkit-text-fill-color: #202020 !important;
        font-weight: 650 !important;
    }


    /* ========================================================
       METRIC CARDS
       ======================================================== */

    div[data-testid="stMetric"] {
        background:
            linear-gradient(
                145deg,
                #ffffff 0%,
                #fbfaf7 100%
            ) !important;
        border: 1px solid #dfdbd3 !important;
        border-radius: 13px !important;
        padding: 18px 19px !important;
        box-shadow:
            0 4px 14px rgba(23,23,23,0.065) !important;
    }

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p {
        color: #55514a !important;
        -webkit-text-fill-color: #55514a !important;
        font-weight: 850 !important;
        opacity: 1 !important;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div,
    div[data-testid="stMetricValue"] p {
        color: #101010 !important;
        -webkit-text-fill-color: #101010 !important;
        font-weight: 950 !important;
        opacity: 1 !important;
        letter-spacing: -0.7px !important;
    }


    /* ========================================================
       TABLES
       ======================================================== */

    div[data-testid="stDataFrame"] {
        background: #ffffff !important;
        border: 1px solid #ded9d1 !important;
        border-radius: 11px !important;
        overflow: hidden !important;
        box-shadow:
            0 3px 12px rgba(23,23,23,0.045) !important;
    }


    /* ========================================================
       EXPANDERS
       ======================================================== */

    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #ded9d1 !important;
        border-radius: 11px !important;
    }

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary p {
        color: #222222 !important;
        -webkit-text-fill-color: #222222 !important;
        font-weight: 800 !important;
    }


    /* ========================================================
       ALERTS
       ======================================================== */

    div[data-testid="stAlert"] {
        border-radius: 10px !important;
    }


    /* ========================================================
       CHAT
       ======================================================== */

    div[data-testid="stChatMessage"] {
        background: #ffffff !important;
        border: 1px solid #e3dfd8 !important;
        border-radius: 13px !important;
        margin-bottom: 10px !important;
    }

    div[data-testid="stChatMessage"] p {
        color: #252525 !important;
        -webkit-text-fill-color: #252525 !important;
        font-weight: 600 !important;
    }


    /* ========================================================
       RADIO / CHECKBOX
       ======================================================== */

    div[data-testid="stRadio"] label,
    div[data-testid="stCheckbox"] label {
        color: #2d2b28 !important;
        -webkit-text-fill-color: #2d2b28 !important;
        font-weight: 700 !important;
    }


    /* ========================================================
       LOGIN PAGE - REFERENCE THEME ONLY
       No external image is used.
       ======================================================== */

    body:has(.ss-login-marker) .stApp {
        min-height: 100vh !important;
        background:
            radial-gradient(
                circle at 7% 8%,
                rgba(255,255,255,0.07),
                transparent 22%
            ),
            radial-gradient(
                circle at 93% 90%,
                rgba(216,179,110,0.065),
                transparent 24%
            ),
            #181818 !important;
    }

    body:has(.ss-login-marker) .main {
        background: transparent !important;
        min-height: 100vh !important;
    }

    body:has(.ss-login-marker) .block-container {
        min-height: 100vh !important;
        max-width: 100% !important;
        padding: 0 28px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* First global application title is hidden while logged out.
       The login title remains visible. */
    body:has(.ss-login-marker) h1:first-of-type {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 900 !important;
    }

    /* Force the existing application subtitle on the login
       screen to white because the login background is dark. */
    body:has(.ss-login-marker) [data-testid="stCaptionContainer"],
    body:has(.ss-login-marker) [data-testid="stCaptionContainer"] p,
    body:has(.ss-login-marker) .stCaption,
    body:has(.ss-login-marker) .stCaption p {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    /* Fallback for Streamlit versions where the caption is
       rendered as a normal paragraph near the first title. */
    body:has(.ss-login-marker) .main > div > div > div > p {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }


    body:has(.ss-login-marker) .main h1,
    body:has(.ss-login-marker) .main h1 span {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 900 !important;
    }

    body:has(.ss-login-marker) .main [data-testid="stCaptionContainer"] p,
    body:has(.ss-login-marker) .main .stCaption {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Login page content */
    body:has(.ss-login-marker) h3 {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-weight: 900 !important;
        text-align: center !important;
    }

    body:has(.ss-login-marker) .stTextInput label,
    body:has(.ss-login-marker) .stTextInput label p {
        color: #f2eee6 !important;
        -webkit-text-fill-color: #f2eee6 !important;
        font-weight: 850 !important;
    }

    body:has(.ss-login-marker) .stTextInput input {
        background: #ffffff !important;
        color: #202020 !important;
        -webkit-text-fill-color: #202020 !important;
        border: 1px solid #d8d2c7 !important;
        border-radius: 9px !important;
        font-weight: 650 !important;
    }

    body:has(.ss-login-marker) .stTextInput input::placeholder {
        color: #77726a !important;
        -webkit-text-fill-color: #77726a !important;
        opacity: 1 !important;
    }

    body:has(.ss-login-marker) .stButton > button[kind="primary"],
    body:has(.ss-login-marker) .stButton > button[data-testid="baseButton-primary"] {
        background:
            linear-gradient(
                135deg,
                #ecd09a 0%,
                #d5a85d 100%
            ) !important;
        color: #151515 !important;
        -webkit-text-fill-color: #151515 !important;
        border: none !important;
        font-weight: 900 !important;
        border-radius: 24px !important;
        box-shadow:
            0 8px 20px rgba(0,0,0,0.23) !important;
    }

    body:has(.ss-login-marker) .stButton > button[kind="primary"] *,
    body:has(.ss-login-marker) .stButton > button[kind="primary"] p,
    body:has(.ss-login-marker) .stButton > button[kind="primary"] span {
        color: #151515 !important;
        -webkit-text-fill-color: #151515 !important;
        font-weight: 900 !important;
    }

    body:has(.ss-login-marker) .stAlert {
        font-weight: 700 !important;
    }


    /* ========================================================
       SCROLLBAR
       ======================================================== */

    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #ece9e3;
    }

    ::-webkit-scrollbar-thumb {
        background: #bdb6aa;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #938b7e;
    }

</style>
""", unsafe_allow_html=True)

# ============================================================
# TITLE
# ============================================================

st.title("🏪 ShopSense AI")

st.caption(
    "AI-powered Sales Management & Business Intelligence"
)

st.divider()


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "sale_cart" not in st.session_state:
    st.session_state.sale_cart = []


# ============================================================
# GEMINI CHAT
# ============================================================

def get_ai_chat():

    # Keep both client and chat alive.
    #
    # This prevents errors such as:
    # "The AI connection was refreshed"
    # "Cannot send a request, as the client has been closed."

    if (
        "gemini_client" not in st.session_state
        or "gemini_chat" not in st.session_state
    ):

        client, chat = create_chat()

        st.session_state.gemini_client = client
        st.session_state.gemini_chat = chat

    return (
        st.session_state.gemini_client,
        st.session_state.gemini_chat,
    )


def reset_ai_chat():

    try:

        if "gemini_client" in st.session_state:

            client = st.session_state.gemini_client

            try:
                client.close()
            except Exception:
                pass

    except Exception:
        pass

    if "gemini_client" in st.session_state:
        del st.session_state.gemini_client

    if "gemini_chat" in st.session_state:
        del st.session_state.gemini_chat


# ============================================================
# EXCEL SALES REPORT GENERATOR
# ============================================================

def create_sales_excel_report(
    report_df,
    report_products,
    report_start,
    report_end,
    report_revenue,
    report_transactions,
    report_average
):
    """
    Create a downloadable Excel sales report.

    Excel contains:
        1. Summary
        2. Daily Sales
        3. Top Products
    """

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        # ====================================================
        # SUMMARY
        # ====================================================

        summary_df = pd.DataFrame([
            {
                "Report Start": str(report_start),
                "Report End": str(report_end),
                "Total Revenue": float(report_revenue),
                "Total Transactions": int(report_transactions),
                "Average Transaction": float(report_average),
            }
        ])

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        # ====================================================
        # DAILY SALES
        # ====================================================

        daily_df = report_df.copy()

        daily_df.to_excel(
            writer,
            sheet_name="Daily Sales",
            index=False
        )

        # ====================================================
        # TOP PRODUCTS
        # ====================================================

        if report_products:

            products_df = pd.DataFrame([
                {
                    "Product": item.get(
                        "product_name",
                        ""
                    ),
                    "Quantity Sold": int(
                        item.get(
                            "quantity_sold",
                            0
                        ) or 0
                    ),
                    "Revenue": float(
                        item.get(
                            "revenue",
                            0
                        ) or 0
                    )
                }

                for item in report_products
            ])

        else:

            products_df = pd.DataFrame(
                columns=[
                    "Product",
                    "Quantity Sold",
                    "Revenue"
                ]
            )

        products_df.to_excel(
            writer,
            sheet_name="Top Products",
            index=False
        )

        # ====================================================
        # FORMAT EXCEL SHEETS
        # ====================================================

        try:

            from openpyxl.styles import Font, Alignment
            from openpyxl.utils import get_column_letter

            for worksheet in writer.book.worksheets:

                # Header
                for cell in worksheet[1]:

                    cell.font = Font(
                        bold=True
                    )

                    cell.alignment = Alignment(
                        horizontal="center"
                    )

                # Auto width
                for column_cells in worksheet.columns:

                    max_length = 0

                    column_letter = (
                        get_column_letter(
                            column_cells[0].column
                        )
                    )

                    for cell in column_cells:

                        try:

                            cell_length = len(
                                str(cell.value)
                            )

                            if cell_length > max_length:
                                max_length = cell_length

                        except Exception:
                            pass

                    worksheet.column_dimensions[
                        column_letter
                    ].width = min(
                        max_length + 2,
                        40
                    )

        except Exception:
            pass

    output.seek(0)

    return output.getvalue()


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    # Closed marker used only to activate login-specific CSS.
    st.markdown(
        '<span class="ss-login-marker" style="display:none;"></span>',
        unsafe_allow_html=True
    )

    st.title("🏪 ShopSense AI")

    st.caption(
        "Sales Management & Business Intelligence"
    )

    st.divider()

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        st.subheader(
            "🔐 Login"
        )

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        if st.button(
            "🔐 Login",
            type="primary",
            use_container_width=True
        ):

            if not username or not password:

                st.warning(
                    "Please enter username and password."
                )

            else:

                try:

                    result = authenticate_user(
                        username,
                        password
                    )

                    if result.get("success"):

                        st.session_state.logged_in = True

                        st.session_state.user_id = (
                            result.get("user_id")
                        )

                        st.session_state.username = (
                            result.get("username")
                        )

                        st.session_state.role = (
                            result.get("role")
                        )

                        st.success(
                            "Login successful!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            result.get(
                                "message",
                                "Invalid login details."
                            )
                        )

                except Exception as e:

                    st.error(
                        f"Login error: {e}"
                    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🏪 ShopSense AI")

st.sidebar.success(
    f"👤 {st.session_state.username}"
)

st.sidebar.caption(
    f"Role: {st.session_state.role}"
)


# ============================================================
# LOGOUT
# ============================================================

if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):

    st.session_state.logged_in = False

    st.session_state.user_id = None

    st.session_state.username = None

    st.session_state.role = None

    st.session_state.messages = []

    st.session_state.sale_cart = []

    reset_ai_chat()

    st.rerun()


st.sidebar.divider()


# ============================================================
# NAVIGATION BY ROLE
# ============================================================

if str(
    st.session_state.role
).strip().upper() == "ADMIN":

    pages = [
        "📊 Dashboard",
        "📈 Sales Performance",
        "📅 Monthly Performance",
        "📆 Date Range Sales",
        "📦 Inventory Management",
        "🧾 Sales History",
        "🤖 AI Sales Assistant",
        "🛒 New Sale",
        "📈 Sales Forecast",
        "💡 Business Insights",
        "📋 Sales Report",
        "💰 Profit & Loss",
    ]

else:

    pages = [
        "📦 Inventory Management",
        "🧾 Sales History",
        "🤖 AI Sales Assistant",
        "🛒 New Sale",
    ]


page = st.sidebar.radio(
    "Navigate",
    pages
)


# ============================================================
# REFRESH
# ============================================================

st.sidebar.divider()

if st.sidebar.button(
    "🔄 Refresh Data",
    use_container_width=True
):

    clear_read_cache()
    st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

if page == "📊 Dashboard":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()

    st.header(
        "📊 Sales Dashboard"
    )

    st.caption(
        "Complete overview of sales, profitability, "
        "inventory and business performance."
    )

    try:

        total_revenue = float(
            cached_total_revenue() or 0
        )

        total_transactions = int(
            cached_total_transactions() or 0
        )

        top_products = cached_top_products()

        revenue_by_hour = (
            cached_revenue_by_hour()
        )

        payment_analysis = (
            cached_payment_analysis()
        )

        profit_summary = (
            cached_profit_summary()
        )

        product_profit = (
            cached_profit_by_product(10)
        )

        monthly_profit = (
            cached_monthly_profit(12)
        )

        inventory_summary = (
            cached_inventory_summary()
        )

        forecast_result = (
            cached_sales_forecast()
        )

    except Exception as e:

        st.error(
            f"Database error: {e}"
        )

        st.stop()


    revenue = float(
        profit_summary.get(
            "total_revenue",
            total_revenue
        ) or 0
    )

    cost = float(
        profit_summary.get(
            "total_cost",
            0
        ) or 0
    )

    profit = float(
        profit_summary.get(
            "total_profit",
            0
        ) or 0
    )

    margin = float(
        profit_summary.get(
            "profit_margin",
            0
        ) or 0
    )


    # ========================================================
    # FINANCIAL KPI
    # ========================================================

    st.subheader(
        "💰 Financial Overview"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "💰 Total Revenue",
            f"₹{revenue:,.2f}"
        )

    with col2:

        st.metric(
            "💸 Total Cost",
            f"₹{cost:,.2f}"
        )

    with col3:

        st.metric(
            "📈 Total Profit",
            f"₹{profit:,.2f}"
        )

    with col4:

        st.metric(
            "📊 Profit Margin",
            f"{margin:.2f}%"
        )


    st.divider()


    # ========================================================
    # BUSINESS KPIs
    # ========================================================

    st.subheader(
        "📊 Business Overview"
    )

    total_units = int(
        float(
            inventory_summary.get(
                "total_units",
                0
            ) or 0
        )
    )

    low_stock = int(
        float(
            inventory_summary.get(
                "low_stock",
                0
            ) or 0
        )
    )

    out_of_stock = int(
        float(
            inventory_summary.get(
                "out_of_stock",
                0
            ) or 0
        )
    )

    inventory_value = float(
        inventory_summary.get(
            "inventory_sales_value",
            0
        ) or 0
    )

    average_transaction = (
        revenue / total_transactions
        if total_transactions > 0
        else 0
    )


    col1, col2, col3, col4, col5 = (
        st.columns(5)
    )

    with col1:

        st.metric(
            "🧾 Transactions",
            f"{total_transactions:,}"
        )

    with col2:

        st.metric(
            "💵 Avg. Transaction",
            f"₹{average_transaction:,.2f}"
        )

    with col3:

        st.metric(
            "📦 Stock Units",
            f"{total_units:,}"
        )

    with col4:

        st.metric(
            "⚠️ Low Stock",
            f"{low_stock:,}"
        )

    with col5:

        st.metric(
            "❌ Out of Stock",
            f"{out_of_stock:,}"
        )

    st.caption(
        f"Current inventory sales value: "
        f"₹{inventory_value:,.2f}"
    )


    st.divider()


    # ========================================================
    # FINANCIAL CHART
    # ========================================================

    st.subheader(
        "💰 Revenue vs Cost vs Profit"
    )

    financial_df = pd.DataFrame(
        {
            "Metric": [
                "Revenue",
                "Cost",
                "Profit"
            ],
            "Amount": [
                revenue,
                cost,
                profit
            ]
        }
    ).set_index("Metric")

    st.bar_chart(
        financial_df
    )


    st.divider()


    # ========================================================
    # MONTHLY PROFIT
    # ========================================================

    st.subheader(
        "📆 Monthly Profit Trend"
    )

    if monthly_profit:

        monthly_df = pd.DataFrame(
            monthly_profit
        )

        if (
            "month" in monthly_df.columns
            and
            "profit" in monthly_df.columns
        ):

            monthly_df["profit"] = (
                pd.to_numeric(
                    monthly_df["profit"],
                    errors="coerce"
                )
                .fillna(0)
            )

            monthly_chart = (
                monthly_df[
                    [
                        "month",
                        "profit"
                    ]
                ]
                .set_index("month")
            )

            st.line_chart(
                monthly_chart
            )

        else:

            st.info(
                "Monthly profit data is incomplete."
            )

    else:

        st.info(
            "No monthly profit data available."
        )


    st.divider()


    # ========================================================
    # TOP PRODUCTS
    # ========================================================

    st.subheader(
        "🏆 Top Products by Revenue"
    )

    if top_products:

        product_chart = pd.DataFrame(
            [
                {
                    "Product":
                        item.get(
                            "product_name",
                            "Unknown"
                        ),

                    "Revenue":
                        float(
                            item.get(
                                "revenue",
                                0
                            ) or 0
                        )
                }

                for item in top_products
            ]
        ).set_index("Product")

        st.bar_chart(
            product_chart
        )


        product_display = [
            {
                "Product":
                    item.get(
                        "product_name",
                        ""
                    ),

                "Quantity Sold":
                    int(
                        item.get(
                            "quantity_sold",
                            0
                        ) or 0
                    ),

                "Revenue":
                    (
                        f"₹{float(item.get('revenue', 0) or 0):,.2f}"
                    )
            }

            for item in top_products
        ]

        st.dataframe(
            product_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No product sales available."
        )


    st.divider()


    # ========================================================
    # PRODUCT PROFITABILITY
    # ========================================================

    st.subheader(
        "💎 Product Profitability"
    )

    if product_profit:

        profitability_df = pd.DataFrame(
            [
                {
                    "Product":
                        item.get(
                            "product_name",
                            "Unknown"
                        ),

                    "Profit":
                        float(
                            item.get(
                                "profit",
                                0
                            ) or 0
                        )
                }

                for item in product_profit
            ]
        ).set_index("Product")

        st.bar_chart(
            profitability_df
        )


        profit_display = [
            {
                "Product":
                    item.get(
                        "product_name",
                        ""
                    ),

                "Revenue":
                    (
                        f"₹{float(item.get('revenue', 0) or 0):,.2f}"
                    ),

                "Cost":
                    (
                        f"₹{float(item.get('cost', 0) or 0):,.2f}"
                    ),

                "Profit":
                    (
                        f"₹{float(item.get('profit', 0) or 0):,.2f}"
                    ),

                "Profit Margin":
                    (
                        f"{float(item.get('profit_margin', 0) or 0):.2f}%"
                    )
            }

            for item in product_profit
        ]

        st.dataframe(
            profit_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No product profitability data available."
        )


    st.divider()


    # ========================================================
    # INVENTORY HEALTH
    # ========================================================

    st.subheader(
        "📦 Inventory Health"
    )

    if out_of_stock > 0:

        st.error(
            f"❌ {out_of_stock} product(s) "
            "are out of stock."
        )

    elif low_stock > 0:

        st.warning(
            f"⚠️ {low_stock} product(s) "
            "are at or below reorder level."
        )

    else:

        st.success(
            "✅ Inventory is currently above "
            "reorder levels."
        )


    st.divider()


    # ========================================================
    # SALES FORECAST
    # ========================================================

    st.subheader(
        "🔮 7-Day Sales Forecast"
    )

    if (
        isinstance(
            forecast_result,
            dict
        )
        and
        forecast_result.get(
            "status"
        ) == "success"
    ):

        forecast_data = (
            forecast_result.get(
                "forecast",
                []
            )
        )

        if forecast_data:

            forecast_df = pd.DataFrame(
                [
                    {
                        "Date":
                            item.get(
                                "date",
                                ""
                            ),

                        "Predicted Revenue":
                            float(
                                item.get(
                                    "predicted_revenue",
                                    0
                                ) or 0
                            )
                    }

                    for item in forecast_data
                ]
            )

            forecast_total = (
                forecast_df[
                    "Predicted Revenue"
                ].sum()
            )

            forecast_average = (
                forecast_df[
                    "Predicted Revenue"
                ].mean()
            )

            first_prediction = float(
                forecast_df[
                    "Predicted Revenue"
                ].iloc[0]
            )

            last_prediction = float(
                forecast_df[
                    "Predicted Revenue"
                ].iloc[-1]
            )

            if last_prediction > first_prediction:

                trend = "📈 Increasing"

            elif last_prediction < first_prediction:

                trend = "📉 Decreasing"

            else:

                trend = "➡️ Stable"


            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:

                st.metric(
                    "Expected 7-Day Revenue",
                    f"₹{forecast_total:,.2f}"
                )

            with col2:

                st.metric(
                    "Average Daily Revenue",
                    f"₹{forecast_average:,.2f}"
                )

            with col3:

                st.metric(
                    "Forecast Trend",
                    trend
                )


            forecast_chart = (
                forecast_df
                .set_index("Date")
            )

            st.line_chart(
                forecast_chart[
                    "Predicted Revenue"
                ],
                use_container_width=True
            )

        else:

            st.info(
                "No forecast values returned."
            )

    else:

        message = (
            forecast_result.get(
                "message",
                "Forecast unavailable."
            )

            if isinstance(
                forecast_result,
                dict
            )

            else
            "Forecast unavailable."
        )

        st.info(message)


    st.divider()


    # ========================================================
    # REVENUE BY HOUR
    # ========================================================

    st.subheader(
        "⏰ Revenue by Hour"
    )

    if revenue_by_hour:

        hour_df = pd.DataFrame(
            [
                {
                    "Hour":
                        f"{int(row.get('sale_hour', 0)):02d}:00",

                    "Revenue":
                        float(
                            row.get(
                                "revenue",
                                0
                            ) or 0
                        )
                }

                for row in revenue_by_hour
            ]
        ).set_index("Hour")

        st.line_chart(
            hour_df
        )

    else:

        st.info(
            "No hourly sales data available."
        )


    st.divider()


    # ========================================================
    # PAYMENT ANALYSIS
    # ========================================================

    st.subheader(
        "💳 Payment Method Analysis"
    )

    if payment_analysis:

        payment_df = pd.DataFrame(
            [
                {
                    "Payment Method":
                        row.get(
                            "payment_method",
                            "Unknown"
                        ),

                    "Transactions":
                        int(
                            row.get(
                                "transactions",
                                0
                            ) or 0
                        ),

                    "Revenue":
                        float(
                            row.get(
                                "revenue",
                                0
                            ) or 0
                        )
                }

                for row in payment_analysis
            ]
        )

        st.bar_chart(
            payment_df
            .set_index(
                "Payment Method"
            )["Revenue"]
        )

        payment_display = (
            payment_df.copy()
        )

        payment_display["Revenue"] = (
            payment_display["Revenue"]
            .apply(
                lambda x:
                f"₹{x:,.2f}"
            )
        )

        st.dataframe(
            payment_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No payment data available."
        )


# ============================================================
# SALES PERFORMANCE
# ============================================================

elif page == "📈 Sales Performance":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.header(
        "📈 Sales Performance"
    )

    st.write(
        "Compare your shop's recent sales performance."
    )

    st.divider()


    try:

        today_sales = (
            get_today_sales()
        )

        yesterday_sales = (
            get_yesterday_sales()
        )

        this_week = (
            get_this_week_sales()
        )

        this_month = (
            get_this_month_sales()
        )

        best_product = (
            get_best_product_this_week()
        )

    except Exception as e:

        st.error(
            f"Database error: {e}"
        )

        st.stop()


    # ========================================================
    # TODAY
    # ========================================================

    st.subheader("📅 Today")

    today_revenue = float(
        today_sales.get(
            "revenue",
            0
        ) or 0
    )

    today_transactions = int(
        today_sales.get(
            "transactions",
            0
        ) or 0
    )

    today_average = (
        today_revenue / today_transactions
        if today_transactions > 0
        else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Revenue",
            f"₹{today_revenue:,.2f}"
        )

    with col2:

        st.metric(
            "Transactions",
            f"{today_transactions:,}"
        )

    with col3:

        st.metric(
            "Average Transaction",
            f"₹{today_average:,.2f}"
        )


    # ========================================================
    # YESTERDAY
    # ========================================================

    st.subheader("📅 Yesterday")

    yesterday_revenue = float(
        yesterday_sales.get(
            "revenue",
            0
        ) or 0
    )

    yesterday_transactions = int(
        yesterday_sales.get(
            "transactions",
            0
        ) or 0
    )

    yesterday_average = (
        yesterday_revenue /
        yesterday_transactions

        if yesterday_transactions > 0

        else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Revenue",
            f"₹{yesterday_revenue:,.2f}"
        )

    with col2:

        st.metric(
            "Transactions",
            f"{yesterday_transactions:,}"
        )

    with col3:

        st.metric(
            "Average Transaction",
            f"₹{yesterday_average:,.2f}"
        )


    st.divider()


    # ========================================================
    # THIS WEEK
    # ========================================================

    st.subheader("📆 This Week")

    week_revenue = float(
        this_week.get(
            "revenue",
            0
        ) or 0
    )

    week_transactions = int(
        this_week.get(
            "transactions",
            0
        ) or 0
    )

    week_average = (
        week_revenue /
        week_transactions

        if week_transactions > 0

        else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Revenue",
            f"₹{week_revenue:,.2f}"
        )

    with col2:

        st.metric(
            "Transactions",
            f"{week_transactions:,}"
        )

    with col3:

        st.metric(
            "Average Transaction",
            f"₹{week_average:,.2f}"
        )


    # ========================================================
    # THIS MONTH
    # ========================================================

    st.subheader("📅 This Month")

    month_revenue = float(
        this_month.get(
            "revenue",
            0
        ) or 0
    )

    month_transactions = int(
        this_month.get(
            "transactions",
            0
        ) or 0
    )

    month_average = (
        month_revenue /
        month_transactions

        if month_transactions > 0

        else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Revenue",
            f"₹{month_revenue:,.2f}"
        )

    with col2:

        st.metric(
            "Transactions",
            f"{month_transactions:,}"
        )

    with col3:

        st.metric(
            "Average Transaction",
            f"₹{month_average:,.2f}"
        )


    st.divider()


    # ========================================================
    # BEST PRODUCT
    # ========================================================

    st.subheader(
        "🏆 Best Product This Week"
    )

    if (
        best_product
        and best_product.get(
            "product_name"
        )
    ):

        col1, col2, col3 = (
            st.columns(3)
        )

        with col1:

            st.metric(
                "Product",
                best_product.get(
                    "product_name",
                    "N/A"
                )
            )

        with col2:

            st.metric(
                "Quantity Sold",
                f"{int(best_product.get('quantity_sold', 0)):,.0f}"
            )

        with col3:

            st.metric(
                "Revenue",
                f"₹{float(best_product.get('revenue', 0) or 0):,.2f}"
            )

    else:

        st.info(
            "No product sales found for this week."
        )


# ============================================================
# MONTHLY PERFORMANCE
# ============================================================

elif page == "📅 Monthly Performance":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.header(
        "📅 Monthly Performance"
    )

    st.write(
        "Compare this month's actual sales "
        "with last month's actual sales."
    )

    st.divider()


    try:

        comparison = (
            compare_this_month_last_month()
        )

    except Exception as e:

        st.error(
            f"Database error: {e}"
        )

        st.stop()


    this_month = comparison.get(
        "this_month",
        {}
    )

    last_month = comparison.get(
        "last_month",
        {}
    )

    percentage_change = comparison.get(
        "percentage_change"
    )


    current_revenue = float(
        this_month.get(
            "revenue",
            0
        ) or 0
    )

    previous_revenue = float(
        last_month.get(
            "revenue",
            0
        ) or 0
    )

    current_transactions = int(
        this_month.get(
            "transactions",
            0
        ) or 0
    )

    previous_transactions = int(
        last_month.get(
            "transactions",
            0
        ) or 0
    )


    st.subheader(
        "💰 Revenue Comparison"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "This Month",
            f"₹{current_revenue:,.2f}"
        )

    with col2:

        st.metric(
            "Last Month",
            f"₹{previous_revenue:,.2f}"
        )

    with col3:

        if percentage_change is None:

            st.metric(
                "Revenue Change",
                "N/A"
            )

        else:

            st.metric(
                "Revenue Change",
                f"{float(percentage_change):+.2f}%"
            )


    st.divider()


    st.subheader(
        "🧾 Transaction Comparison"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "This Month",
            f"{current_transactions:,}"
        )

    with col2:

        st.metric(
            "Last Month",
            f"{previous_transactions:,}"
        )


    if previous_transactions > 0:

        transaction_change = (
            (
                current_transactions -
                previous_transactions
            )
            /
            previous_transactions
        ) * 100

    else:

        transaction_change = None


    with col3:

        if transaction_change is None:

            st.metric(
                "Transaction Change",
                "N/A"
            )

        else:

            st.metric(
                "Transaction Change",
                f"{transaction_change:+.2f}%"
            )


    st.divider()


    st.subheader(
        "📊 Monthly Revenue Comparison"
    )

    monthly_chart = pd.DataFrame(
        {
            "Month": [
                "Last Month",
                "This Month"
            ],

            "Revenue": [
                previous_revenue,
                current_revenue
            ]
        }
    ).set_index("Month")

    st.bar_chart(
        monthly_chart
    )


    if percentage_change is not None:

        if percentage_change > 0:

            st.success(
                f"📈 Revenue increased by "
                f"{float(percentage_change):.2f}% "
                "compared with last month."
            )

        elif percentage_change < 0:

            st.warning(
                f"📉 Revenue decreased by "
                f"{abs(float(percentage_change)):.2f}% "
                "compared with last month."
            )

        else:

            st.info(
                "Revenue is unchanged compared with last month."
            )


# ============================================================
# DATE RANGE SALES
# ============================================================

elif page == "📆 Date Range Sales":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.header(
        "📆 Date Range Sales"
    )

    st.write(
        "Analyze actual sales for a selected date range."
    )

    st.divider()


    range_option = st.radio(
        "Select Date Range",
        [
            "Last 7 Days",
            "Last 30 Days",
            "Last 3 Months",
            "Custom Date Range"
        ],
        horizontal=True
    )


    today_date = date.today()


    if range_option == "Last 7 Days":

        start_date = (
            today_date -
            timedelta(days=6)
        )

        end_date = today_date

    elif range_option == "Last 30 Days":

        start_date = (
            today_date -
            timedelta(days=29)
        )

        end_date = today_date

    elif range_option == "Last 3 Months":

        start_date = (
            today_date -
            timedelta(days=89)
        )

        end_date = today_date

    else:

        col1, col2 = st.columns(2)

        with col1:

            start_date = st.date_input(
                "Start Date",
                value=(
                    today_date -
                    timedelta(days=6)
                )
            )

        with col2:

            end_date = st.date_input(
                "End Date",
                value=today_date
            )


    if start_date > end_date:

        st.error(
            "Start date cannot be after end date."
        )

        st.stop()


    st.info(
        f"Showing actual sales from "
        f"**{start_date}** to **{end_date}**"
    )


    try:

        summary = get_date_range_summary(
            start_date,
            end_date
        )

        comparison = (
            compare_date_range_with_previous(
                start_date,
                end_date
            )
        )

        daily_sales = (
            get_sales_by_date_range(
                start_date,
                end_date
            )
        )

        range_products = (
            get_top_products_by_date_range(
                start_date,
                end_date
            )
        )

        range_payments = (
            get_payment_analysis_by_date_range(
                start_date,
                end_date
            )
        )

        range_hours = (
            get_revenue_by_hour_date_range(
                start_date,
                end_date
            )
        )

    except Exception as e:

        st.error(
            f"Date range database error: {e}"
        )

        st.stop()


    # ========================================================
    # SUMMARY
    # ========================================================

    st.subheader(
        "📊 Selected Period Summary"
    )

    range_revenue = float(
        summary.get(
            "revenue",
            0
        ) or 0
    )

    range_transactions = int(
        summary.get(
            "transactions",
            0
        ) or 0
    )

    range_average = (
        range_revenue /
        range_transactions

        if range_transactions > 0

        else 0
    )


    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "💰 Total Revenue",
            f"₹{range_revenue:,.2f}"
        )

    with col2:

        st.metric(
            "🧾 Transactions",
            f"{range_transactions:,}"
        )

    with col3:

        st.metric(
            "💵 Average Transaction",
            f"₹{range_average:,.2f}"
        )


    st.divider()


    # ========================================================
    # PERIOD COMPARISON
    # ========================================================

    st.subheader(
        "📊 Previous Period Comparison"
    )

    current_period = comparison.get(
        "current_period",
        {}
    )

    previous_period = comparison.get(
        "previous_period",
        {}
    )

    revenue_change = comparison.get(
        "revenue_change"
    )

    transaction_change = comparison.get(
        "transaction_change"
    )


    col1, col2 = st.columns(2)

    with col1:

        if revenue_change is None:

            st.metric(
                "Revenue Change",
                "N/A"
            )

        else:

            st.metric(
                "Revenue Change",
                f"{float(revenue_change):+.2f}%"
            )

    with col2:

        if transaction_change is None:

            st.metric(
                "Transaction Change",
                "N/A"
            )

        else:

            st.metric(
                "Transaction Change",
                f"{float(transaction_change):+.2f}%"
            )


    if revenue_change is not None:

        if revenue_change > 0:

            st.success(
                f"📈 Revenue increased by "
                f"{float(revenue_change):.2f}% "
                "compared with the previous period."
            )

        elif revenue_change < 0:

            st.warning(
                f"📉 Revenue decreased by "
                f"{abs(float(revenue_change)):.2f}% "
                "compared with the previous period."
            )

        else:

            st.info(
                "Revenue is unchanged compared with the previous period."
            )


    st.divider()


    # ========================================================
    # DAILY SALES
    # ========================================================

    st.subheader(
        "📈 Daily Revenue"
    )

    if daily_sales:

        daily_df = pd.DataFrame(
            daily_sales
        )

        daily_df["sale_date"] = (
            pd.to_datetime(
                daily_df["sale_date"]
            )
        )

        daily_df["revenue"] = (
            pd.to_numeric(
                daily_df["revenue"],
                errors="coerce"
            )
            .fillna(0)
        )

        daily_chart = (
            daily_df[
                [
                    "sale_date",
                    "revenue"
                ]
            ]
            .set_index("sale_date")
        )

        st.line_chart(
            daily_chart
        )

    else:

        st.info(
            "No sales found for the selected date range."
        )


    # ========================================================
    # DAILY TRANSACTIONS
    # ========================================================

    st.subheader(
        "🧾 Daily Transactions"
    )

    if daily_sales:

        transaction_df = pd.DataFrame(
            daily_sales
        )

        transaction_df["sale_date"] = (
            pd.to_datetime(
                transaction_df["sale_date"]
            )
        )

        transaction_df["transactions"] = (
            pd.to_numeric(
                transaction_df["transactions"],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
        )

        transaction_chart = (
            transaction_df[
                [
                    "sale_date",
                    "transactions"
                ]
            ]
            .set_index("sale_date")
        )

        st.bar_chart(
            transaction_chart
        )


    # ========================================================
    # TOP PRODUCTS
    # ========================================================

    st.subheader(
        "🏆 Top Products in Selected Period"
    )

    if range_products:

        product_data = [
            {
                "Product":
                    item.get(
                        "product_name",
                        ""
                    ),

                "Quantity Sold":
                    int(
                        item.get(
                            "quantity_sold",
                            0
                        ) or 0
                    ),

                "Revenue":
                    (
                        f"₹{float(item.get('revenue', 0) or 0):,.2f}"
                    )
            }

            for item in range_products
        ]

        st.dataframe(
            product_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No product sales found."
        )


    # ========================================================
    # PAYMENT
    # ========================================================

    st.subheader(
        "💳 Payment Methods"
    )

    if range_payments:

        payment_data = [
            {
                "Payment Method":
                    row.get(
                        "payment_method",
                        ""
                    ),

                "Transactions":
                    int(
                        row.get(
                            "transactions",
                            0
                        ) or 0
                    ),

                "Revenue":
                    float(
                        row.get(
                            "revenue",
                            0
                        ) or 0
                    )
            }

            for row in range_payments
        ]

        payment_df = pd.DataFrame(
            payment_data
        )

        st.bar_chart(
            payment_df
            .set_index(
                "Payment Method"
            )["Revenue"]
        )

        payment_display = (
            payment_df.copy()
        )

        payment_display["Revenue"] = (
            payment_display["Revenue"]
            .apply(
                lambda x:
                f"₹{x:,.2f}"
            )
        )

        st.dataframe(
            payment_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No payment data found."
        )


    # ========================================================
    # REVENUE BY HOUR
    # ========================================================

    st.subheader(
        "⏰ Revenue by Hour"
    )

    if range_hours:

        hour_df = pd.DataFrame(
            range_hours
        )

        hour_df["Hour"] = (
            hour_df["sale_hour"]
            .apply(
                lambda x:
                f"{int(x):02d}:00"
            )
        )

        hour_df["Revenue"] = (
            pd.to_numeric(
                hour_df["revenue"],
                errors="coerce"
            )
            .fillna(0)
        )

        hour_chart = (
            hour_df[
                [
                    "Hour",
                    "Revenue"
                ]
            ]
            .set_index("Hour")
        )

        st.line_chart(
            hour_chart
        )

    else:

        st.info(
            "No hourly sales data found."
        )


    # ========================================================
    # DAILY DETAILS
    # ========================================================

    if daily_sales:

        st.subheader(
            "📋 Daily Sales Details"
        )

        detailed_data = [
            {
                "Date":
                    row.get(
                        "sale_date",
                        ""
                    ),

                "Transactions":
                    int(
                        row.get(
                            "transactions",
                            0
                        ) or 0
                    ),

                "Revenue":
                    (
                        f"₹{float(row.get('revenue', 0) or 0):,.2f}"
                    )
            }

            for row in daily_sales
        ]

        st.dataframe(
            detailed_data,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# SALES HISTORY
# ============================================================

elif page == "🧾 Sales History":

    st.header(
        "🧾 Sales History"
    )

    st.write(
        "View completed sales, search transactions "
        "and download invoices."
    )

    st.divider()


    try:

        sales_history = (
            get_sales_history(100)
        )

    except Exception as e:

        st.error(
            f"Sales history database error: {e}"
        )

        st.stop()


    # ========================================================
    # FILTERS
    # ========================================================

    col1, col2 = st.columns(2)

    with col1:

        search_sale_id = st.text_input(
            "🔎 Search Sale ID",
            placeholder="Example: 10027"
        )

    with col2:

        payment_options = ["All"]

        payment_options.extend(
            sorted(
                {
                    str(
                        sale.get(
                            "payment_method",
                            ""
                        )
                    ).upper()

                    for sale in sales_history

                    if sale.get(
                        "payment_method"
                    )
                }
            )
        )

        selected_payment = st.selectbox(
            "💳 Payment Method",
            payment_options,
            key="sales_history_payment"
        )


    filtered_sales = sales_history


    # ========================================================
    # SEARCH SALE ID
    # ========================================================

    if search_sale_id.strip():

        try:

            sale_id_value = int(
                search_sale_id.strip()
            )

            filtered_sales = [
                sale

                for sale in filtered_sales

                if int(
                    sale.get(
                        "sale_id",
                        0
                    )
                ) == sale_id_value
            ]

        except ValueError:

            st.warning(
                "Please enter a valid numeric Sale ID."
            )

            filtered_sales = []


    # ========================================================
    # PAYMENT FILTER
    # ========================================================

    if selected_payment != "All":

        filtered_sales = [
            sale

            for sale in filtered_sales

            if str(
                sale.get(
                    "payment_method",
                    ""
                )
            ).upper()
            ==
            selected_payment
        ]


    # ========================================================
    # SUMMARY
    # ========================================================

    history_revenue = sum(
        float(
            sale.get(
                "total_amount",
                0
            ) or 0
        )

        for sale in filtered_sales
    )

    history_transactions = len(
        filtered_sales
    )

    average_sale = (
        history_revenue /
        history_transactions

        if history_transactions > 0

        else 0
    )


    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🧾 Transactions",
            f"{history_transactions:,}"
        )

    with col2:

        st.metric(
            "💰 Revenue",
            f"₹{history_revenue:,.2f}"
        )

    with col3:

        st.metric(
            "💵 Average Sale",
            f"₹{average_sale:,.2f}"
        )


    st.divider()


    # ========================================================
    # RECENT SALES
    # ========================================================

    st.subheader(
        "📋 Recent Sales"
    )

    if filtered_sales:

        history_display = [
            {
                "Sale ID":
                    sale.get(
                        "sale_id",
                        ""
                    ),

                "Date & Time":
                    str(
                        sale.get(
                            "sale_datetime",
                            ""
                        )
                    ).replace(
                        "T",
                        " "
                    ),

                "Payment Method":
                    str(
                        sale.get(
                            "payment_method",
                            ""
                        )
                    ).upper(),

                "Total":
                    (
                        f"₹{float(sale.get('total_amount', 0) or 0):,.2f}"
                    )
            }

            for sale in filtered_sales
        ]

        st.dataframe(
            history_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No sales found for the selected filters."
        )


    st.divider()


    # ========================================================
    # SALE DETAILS
    # ========================================================

    st.subheader(
        "🔍 View Sale Details"
    )

    if filtered_sales:

        sale_ids = [
            int(
                sale.get(
                    "sale_id"
                )
            )

            for sale in filtered_sales
        ]

        selected_sale_id = st.selectbox(
            "Select Sale ID",
            sale_ids,
            key="selected_history_sale"
        )

        if st.button(
            "🔍 View Details",
            type="primary"
        ):

            try:

                selected_sale = (
                    get_sale_details(
                        selected_sale_id
                    )
                )

            except Exception as e:

                st.error(
                    f"Unable to load sale details: {e}"
                )

                selected_sale = None


            if selected_sale:

                payment_method = str(
                    selected_sale.get(
                        "payment_method",
                        ""
                    )
                ).upper()

                total_amount = float(
                    selected_sale.get(
                        "total_amount",
                        0
                    ) or 0
                )

                sale_datetime = str(
                    selected_sale.get(
                        "sale_datetime",
                        ""
                    )
                ).replace(
                    "T",
                    " "
                )


                col1, col2, col3 = (
                    st.columns(3)
                )

                with col1:

                    st.metric(
                        "🧾 Sale ID",
                        str(
                            selected_sale_id
                        )
                    )

                with col2:

                    st.metric(
                        "💳 Payment",
                        payment_method
                    )

                with col3:

                    st.metric(
                        "💰 Total",
                        f"₹{total_amount:,.2f}"
                    )


                st.caption(
                    f"Sale Date & Time: "
                    f"{sale_datetime}"
                )


                items = selected_sale.get(
                    "items",
                    []
                )


                if items:

                    details_display = [
                        {
                            "Product":
                                item.get(
                                    "product_name",
                                    ""
                                ),

                            "Quantity":
                                int(
                                    item.get(
                                        "quantity",
                                        0
                                    ) or 0
                                ),

                            "Unit Price":
                                (
                                    f"₹{float(item.get('unit_price', 0) or 0):,.2f}"
                                ),

                            "Discount":
                                (
                                    f"₹{float(item.get('discount', 0) or 0):,.2f}"
                                ),

                            "Total":
                                (
                                    f"₹{float(item.get('total', 0) or 0):,.2f}"
                                )
                        }

                        for item in items
                    ]

                    st.dataframe(
                        details_display,
                        use_container_width=True,
                        hide_index=True
                    )

                else:

                    st.info(
                        "No item details found for this sale."
                    )


                # =================================================
                # INVOICE
                # =================================================

                st.divider()

                st.subheader(
                    "🧾 Invoice"
                )

                try:

                    invoice_directory = os.path.join(
                        PROJECT_ROOT,
                        "invoices"
                    )

                    os.makedirs(
                        invoice_directory,
                        exist_ok=True
                    )

                    invoice_filename = (
                        f"invoice_{selected_sale_id}.pdf"
                    )

                    invoice_path = os.path.join(
                        invoice_directory,
                        invoice_filename
                    )

                    generated_invoice = (
                        generate_invoice(
                            sale_id=selected_sale_id,
                            payment_method=payment_method,
                            items=items,
                            total_amount=total_amount,
                            output_path=invoice_path
                        )
                    )

                    with open(
                        generated_invoice,
                        "rb"
                    ) as invoice_file:

                        invoice_data = (
                            invoice_file.read()
                        )

                    st.success(
                        "✅ Invoice ready."
                    )

                    st.download_button(
                        label="⬇️ Download Invoice PDF",

                        data=invoice_data,

                        file_name=invoice_filename,

                        mime="application/pdf",

                        use_container_width=True,

                        key=(
                            f"download_invoice_"
                            f"{selected_sale_id}"
                        )
                    )

                except Exception as invoice_error:

                    st.error(
                        f"❌ Invoice generation failed: "
                        f"{invoice_error}"
                    )

    else:

        st.info(
            "Select a valid sale to view details."
        )


# ============================================================
# INVENTORY MANAGEMENT
# ============================================================

elif page == "📦 Inventory Management":

    if not can_view_inventory(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 You do not have permission "
            "to view inventory."
        )

        st.stop()


    st.header(
        "📦 Inventory Management"
    )

    st.write(
        "Monitor product stock, low-stock alerts "
        "and restocking."
    )

    st.divider()


    try:

        inventory_summary = (
            get_inventory_summary()
        )

        inventory = (
            get_inventory()
        )

        low_stock = (
            get_low_stock_products()
        )

        out_of_stock = (
            get_out_of_stock_products()
        )

    except Exception as e:

        st.error(
            f"Inventory database error: {e}"
        )

        st.stop()


    total_products = int(
        inventory_summary.get(
            "total_products",
            0
        ) or 0
    )

    total_units = int(
        inventory_summary.get(
            "total_units",
            0
        ) or 0
    )

    low_stock_count = int(
        inventory_summary.get(
            "low_stock",
            0
        ) or 0
    )

    out_of_stock_count = int(
        inventory_summary.get(
            "out_of_stock",
            0
        ) or 0
    )

    inventory_value = float(
        inventory_summary.get(
            "inventory_sales_value",
            0
        ) or 0
    )


    # ========================================================
    # KPI
    # ========================================================

    col1, col2, col3, col4, col5 = (
        st.columns(5)
    )

    with col1:

        st.metric(
            "📦 Products",
            f"{total_products:,}"
        )

    with col2:

        st.metric(
            "🔢 Total Units",
            f"{total_units:,}"
        )

    with col3:

        st.metric(
            "⚠️ Low Stock",
            f"{low_stock_count:,}"
        )

    with col4:

        st.metric(
            "❌ Out of Stock",
            f"{out_of_stock_count:,}"
        )

    with col5:

        st.metric(
            "💰 Stock Value",
            f"₹{inventory_value:,.2f}"
        )


    st.divider()


    # ========================================================
    # OUT OF STOCK
    # ========================================================

    if out_of_stock:

        st.error(
            f"❌ {len(out_of_stock)} product(s) "
            "are out of stock."
        )

        st.dataframe(
            [
                {
                    "Product":
                        item.get(
                            "product_name",
                            ""
                        ),

                    "Current Stock":
                        int(
                            item.get(
                                "stock_quantity",
                                0
                            ) or 0
                        ),

                    "Reorder Level":
                        int(
                            item.get(
                                "reorder_level",
                                0
                            ) or 0
                        )
                }

                for item in out_of_stock
            ],

            use_container_width=True,

            hide_index=True
        )


    # ========================================================
    # LOW STOCK
    # ========================================================

    if low_stock:

        st.warning(
            f"⚠️ {len(low_stock)} product(s) "
            "need restocking."
        )

        st.dataframe(
            [
                {
                    "Product":
                        item.get(
                            "product_name",
                            ""
                        ),

                    "Current Stock":
                        int(
                            item.get(
                                "stock_quantity",
                                0
                            ) or 0
                        ),

                    "Reorder Level":
                        int(
                            item.get(
                                "reorder_level",
                                0
                            ) or 0
                        )
                }

                for item in low_stock
            ],

            use_container_width=True,

            hide_index=True
        )


    st.divider()


    # ========================================================
    # CURRENT INVENTORY
    # ========================================================

    st.subheader(
        "📋 Current Inventory"
    )

    if inventory:

        inventory_display = []

        for item in inventory:

            stock = int(
                item.get(
                    "stock_quantity",
                    0
                ) or 0
            )

            reorder = int(
                item.get(
                    "reorder_level",
                    0
                ) or 0
            )

            if stock <= 0:

                status = "❌ OUT OF STOCK"

            elif stock <= reorder:

                status = "⚠️ LOW STOCK"

            else:

                status = "✅ IN STOCK"


            inventory_display.append(
                {
                    "Product":
                        item.get(
                            "product_name",
                            ""
                        ),

                    "Category":
                        item.get(
                            "category",
                            ""
                        ),

                    "Selling Price":
                        (
                            f"₹{float(item.get('selling_price', 0) or 0):,.2f}"
                        ),

                    "Current Stock":
                        stock,

                    "Reorder Level":
                        reorder,

                    "Status":
                        status
                }
            )


        st.dataframe(
            inventory_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No products found in inventory."
        )


    st.divider()


    # ========================================================
    # RESTOCK
    # ========================================================

    st.subheader(
        "🔄 Restock Product"
    )

    inventory_names = [
        item.get(
            "product_name",
            ""
        )

        for item in inventory

        if item.get(
            "product_name"
        )
    ]


    if inventory_names:

        col1, col2 = st.columns(2)

        with col1:

            selected_product = st.selectbox(
                "Select Product",
                inventory_names,
                key="restock_product"
            )

        with col2:

            restock_quantity = st.number_input(
                "Restock Quantity",
                min_value=1,
                value=10,
                step=1,
                key="restock_quantity"
            )


        if st.button(
            "🔄 Add Stock",
            type="primary"
        ):

            try:

                result = restock_product(
                    selected_product,
                    int(restock_quantity)
                )

                if result.get("success"):

                    st.success(
                        f"✅ {selected_product} "
                        "restocked successfully. "
                        f"New stock: "
                        f"{result.get('current_stock', 0)}"
                    )

                    st.rerun()

                else:

                    st.error(
                        result.get(
                            "message",
                            "Restock failed."
                        )
                    )

            except Exception as e:

                st.error(
                    f"Restock error: {e}"
                )

    else:

        st.info(
            "No products available for restocking."
        )


    st.divider()


    # ========================================================
    # REORDER LEVEL
    # ========================================================

    st.subheader(
        "⚙️ Update Reorder Level"
    )

    if inventory_names:

        col1, col2 = st.columns(2)

        with col1:

            reorder_product = st.selectbox(
                "Select Product",
                inventory_names,
                key="reorder_product"
            )


        try:

            current_product = (
                get_product_stock(
                    reorder_product
                )
            )

        except Exception:

            current_product = None


        current_reorder = int(
            current_product.get(
                "reorder_level",
                0
            )
        ) if current_product else 0


        with col2:

            new_reorder_level = (
                st.number_input(
                    "Reorder Level",
                    min_value=0,
                    value=current_reorder,
                    step=1,
                    key="new_reorder_level"
                )
            )


        if st.button(
            "⚙️ Update Reorder Level"
        ):

            try:

                result = update_reorder_level(
                    reorder_product,
                    int(new_reorder_level)
                )

                if result.get("success"):

                    st.success(
                        f"✅ Reorder level updated "
                        f"for {reorder_product}."
                    )

                    st.rerun()

                else:

                    st.error(
                        result.get(
                            "message",
                            "Update failed."
                        )
                    )

            except Exception as e:

                st.error(
                    f"Reorder level update error: {e}"
                )

    else:

        st.info(
            "No products available."
        )


# ============================================================
# AI SALES ASSISTANT
# ============================================================

elif page == "🤖 AI Sales Assistant":

    if not can_use_ai(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 You do not have permission "
            "to use the AI assistant."
        )

        st.stop()


    st.header(
        "🤖 ShopSense AI Assistant"
    )

    st.write(
        "Ask questions about your real shop sales data."
    )


    # ========================================================
    # EXAMPLE QUESTIONS
    # ========================================================

    with st.expander(
        "💬 Example Questions",
        expanded=True
    ):

        st.markdown(
            """
### 💰 Sales

- What is my total revenue?
- How many transactions do I have?
- What are my top 5 products?
- Which product generates the most revenue?
- Which payment method generates the most revenue?
- What is my busiest sales hour?

### 📅 Performance

- What are my sales today?
- What were my sales yesterday?
- How are my sales this week?
- How are my sales this month?
- Compare this month with last month.
- What is the best product this week?

### 📈 Analytics

- Are there any unusual sales?
- Forecast my sales for the next 7 days.
- Give me overall business insights.

### 🛒 Sales Entry

- Record a sale of 2 Tea paid by UPI.
- Add 3 Samosa paid by Cash.
- Record 1 Coffee paid by Card.
"""
        )


    # ========================================================
    # RESET AI
    # ========================================================

    if st.button(
        "🔄 Reset AI Connection"
    ):

        reset_ai_chat()

        st.success(
            "AI connection reset successfully."
        )

        st.rerun()


    # ========================================================
    # CLEAR CHAT
    # ========================================================

    if st.button(
        "🗑️ Clear Chat"
    ):

        st.session_state.messages = []

        reset_ai_chat()

        st.rerun()


    # ========================================================
    # CHAT HISTORY
    # ========================================================

    for message in st.session_state.messages:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )


    # ========================================================
    # CHAT INPUT
    # ========================================================

    user_input = st.chat_input(
        "Ask ShopSense AI about your sales..."
    )


    if user_input:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )


        with st.chat_message("user"):

            st.markdown(
                user_input
            )


        with st.chat_message("assistant"):

            with st.spinner(
                "🤖 Analyzing your sales..."
            ):

                try:

                    client, chat = (
                        get_ai_chat()
                    )

                    answer = ask_ai(
                        chat,
                        user_input
                    )

                    st.markdown(
                        answer
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": answer
                        }
                    )


                except Exception as e:

                    error_text = str(e)


                    if (
                        "client has been closed"
                        in error_text.lower()
                        or
                        "cannot send a request"
                        in error_text.lower()
                        or
                        "client is closed"
                        in error_text.lower()
                    ):

                        reset_ai_chat()

                        error_message = (
                            "The AI connection was refreshed. "
                            "Please send your question again."
                        )


                    elif "503" in error_text:

                        error_message = (
                            "Gemini is temporarily busy. "
                            "Please try again in a moment."
                        )


                    elif "429" in error_text:

                        error_message = (
                            "The Gemini API usage limit has "
                            "been reached. Please try again later."
                        )


                    else:

                        error_message = (
                            "Sorry, I couldn't process "
                            "your question."
                        )


                    st.error(
                        error_message
                    )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_message
                        }
                    )


# ============================================================
# NEW SALE
# ============================================================

elif page == "🛒 New Sale":

    if not can_create_sale(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 You do not have permission "
            "to create sales."
        )

        st.stop()


    st.header(
        "🛒 New Sale"
    )

    st.write(
        "Create a bill with multiple products."
    )

    st.divider()


    # ========================================================
    # ADD PRODUCT
    # ========================================================

    st.subheader(
        "➕ Add Product"
    )

    col1, col2, col3 = st.columns(
        [2, 1, 1]
    )

    with col1:

        # Load all products from inventory
        try:
            available_products = get_inventory()
        except Exception as e:
            available_products = []
            st.error(f"Unable to load products: {e}")

        product_options = [
            item.get("product_name")
            for item in available_products
            if item.get("product_name")
        ]

        if product_options:

            product_name = st.selectbox(
                "Product Name",
                product_options,
                key="sale_product_name"
            )

        else:

            product_name = None

            st.warning(
                "⚠️ No products available in inventory."
            )

    with col2:

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            value=1,
            step=1,
            key="sale_quantity"
        )

    with col3:

        st.write("")

        if st.button(
            "➕ Add Product",
            use_container_width=True
        ):

            name = product_name.strip()


            if not name:

                st.warning(
                    "⚠️ Please enter a product name."
                )

            else:

                try:

                    product = (
                        get_product_stock(
                            name
                        )
                    )


                    if not product:

                        st.error(
                            f"❌ Product not found: {name}"
                        )

                    else:

                        stock = int(
                            product.get(
                                "stock_quantity",
                                0
                            ) or 0
                        )

                        canonical_name = (
                            product.get(
                                "product_name",
                                name
                            )
                        )


                        existing_qty = 0

                        for cart_item in (
                            st.session_state.sale_cart
                        ):

                            if (
                                cart_item[
                                    "product_name"
                                ].lower()
                                ==
                                canonical_name.lower()
                            ):

                                existing_qty = int(
                                    cart_item[
                                        "quantity"
                                    ]
                                )

                                break


                        requested_qty = (
                            existing_qty +
                            int(quantity)
                        )


                        if stock <= 0:

                            st.error(
                                f"❌ {canonical_name} "
                                "is out of stock."
                            )

                        elif requested_qty > stock:

                            st.error(
                                f"❌ Insufficient stock "
                                f"for {canonical_name}. "
                                f"Available stock: {stock}. "
                                f"Already in cart: "
                                f"{existing_qty}."
                            )

                        else:

                            found = False

                            for cart_item in (
                                st.session_state.sale_cart
                            ):

                                if (
                                    cart_item[
                                        "product_name"
                                    ].lower()
                                    ==
                                    canonical_name.lower()
                                ):

                                    cart_item[
                                        "quantity"
                                    ] += int(quantity)

                                    found = True

                                    break


                            if not found:

                                st.session_state.sale_cart.append(
                                    {
                                        "product_name":
                                            canonical_name,

                                        "quantity":
                                            int(quantity)
                                    }
                                )


                            st.success(
                                f"✅ {canonical_name} "
                                "added to bill."
                            )

                            st.rerun()


                except Exception as e:

                    st.error(
                        f"❌ Product error: {e}"
                    )


    # ========================================================
    # CURRENT BILL
    # ========================================================

    st.divider()

    st.subheader(
        "🧾 Current Bill"
    )

    cart = (
        st.session_state.sale_cart
    )


    if not cart:

        st.info(
            "No products added yet."
        )

    else:

        bill_items = []

        grand_total = 0.0


        for cart_item in cart:

            try:

                product = (
                    get_product_stock(
                        cart_item[
                            "product_name"
                        ]
                    )
                )

            except Exception:

                product = None


            unit_price = (
                float(
                    product.get(
                        "selling_price",
                        0
                    ) or 0
                )

                if product

                else 0.0
            )

            qty = int(
                cart_item[
                    "quantity"
                ]
            )

            item_total = (
                unit_price * qty
            )

            grand_total += item_total


            bill_items.append(
                {
                    "Product":
                        cart_item[
                            "product_name"
                        ],

                    "Quantity":
                        qty,

                    "Unit Price":
                        (
                            f"₹{unit_price:,.2f}"
                        ),

                    "Total":
                        (
                            f"₹{item_total:,.2f}"
                        )
                }
            )


        st.dataframe(
            bill_items,
            use_container_width=True,
            hide_index=True
        )


        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "🛍️ Products",
                len(cart)
            )

        with col2:

            st.metric(
                "💰 Grand Total",
                f"₹{grand_total:,.2f}"
            )


        st.divider()


        # ====================================================
        # REMOVE PRODUCT
        # ====================================================

        st.subheader(
            "🗑️ Remove Product"
        )

        remove_product = st.selectbox(
            "Select product to remove",
            [
                item[
                    "product_name"
                ]

                for item in cart
            ],
            key="remove_sale_product"
        )


        if st.button(
            "🗑️ Remove Selected Product",
            use_container_width=True
        ):

            st.session_state.sale_cart = [
                item

                for item in (
                    st.session_state.sale_cart
                )

                if item[
                    "product_name"
                ]
                !=
                remove_product
            ]

            st.rerun()


        st.divider()


        # ====================================================
        # PAYMENT
        # ====================================================

        st.subheader(
            "💳 Payment Method"
        )

        payment_method = st.selectbox(
            "Payment Method",
            [
                "Cash",
                "UPI",
                "Card"
            ],
            key="new_sale_payment"
        )


        st.divider()


        # ====================================================
        # COMPLETE SALE
        # ====================================================

        if st.button(
            "✅ Complete Sale",
            type="primary",
            use_container_width=True
        ):

            try:

                sale_items = [
                    {
                        "product_name":
                            item[
                                "product_name"
                            ],

                        "quantity":
                            int(
                                item[
                                    "quantity"
                                ]
                            )
                    }

                    for item in cart
                ]


                result = add_sale(
                    items=sale_items,
                    payment_method=payment_method
                )


                if result.get(
                    "success"
                ):

                    sale_id = result.get(
                        "sale_id"
                    )

                    payment = result.get(
                        "payment_method",
                        payment_method
                    )

                    total_amount = float(
                        result.get(
                            "total_amount",
                            0
                        ) or 0
                    )

                    items = result.get(
                        "items",
                        []
                    )


                    st.success(
                        "🎉 Sale successfully recorded!"
                    )


                    col1, col2, col3 = (
                        st.columns(3)
                    )

                    with col1:

                        st.metric(
                            "🧾 Sale ID",
                            str(sale_id)
                        )

                    with col2:

                        st.metric(
                            "💳 Payment",
                            str(payment).upper()
                        )

                    with col3:

                        st.metric(
                            "💰 Total",
                            f"₹{total_amount:,.2f}"
                        )


                    st.divider()

                    st.subheader(
                        "🛍️ Sale Details"
                    )


                    display_items = []


                    for item in items:

                        row = {
                            "Product":
                                item.get(
                                    "product_name",
                                    ""
                                ),

                            "Quantity":
                                int(
                                    item.get(
                                        "quantity",
                                        0
                                    ) or 0
                                ),

                            "Unit Price":
                                (
                                    f"₹{float(item.get('unit_price', 0) or 0):,.2f}"
                                ),

                            "Total":
                                (
                                    f"₹{float(item.get('total', 0) or 0):,.2f}"
                                )
                        }


                        if (
                            "remaining_stock"
                            in item
                        ):

                            row[
                                "Remaining Stock"
                            ] = int(
                                item.get(
                                    "remaining_stock",
                                    0
                                ) or 0
                            )


                        if (
                            "stock_status"
                            in item
                        ):

                            row[
                                "Stock Status"
                            ] = item.get(
                                "stock_status",
                                ""
                            )


                        display_items.append(
                            row
                        )


                    if display_items:

                        st.dataframe(
                            display_items,
                            use_container_width=True,
                            hide_index=True
                        )


                    # =================================================
                    # PDF INVOICE
                    # =================================================

                    st.divider()

                    st.subheader(
                        "🧾 Invoice"
                    )


                    try:

                        invoice_directory = os.path.join(
                            PROJECT_ROOT,
                            "invoices"
                        )

                        os.makedirs(
                            invoice_directory,
                            exist_ok=True
                        )


                        invoice_filename = (
                            f"invoice_{sale_id}.pdf"
                        )

                        invoice_path = os.path.join(
                            invoice_directory,
                            invoice_filename
                        )


                        generated_invoice = (
                            generate_invoice(
                                sale_id=sale_id,
                                payment_method=payment,
                                items=items,
                                total_amount=total_amount,
                                output_path=invoice_path
                            )
                        )


                        with open(
                            generated_invoice,
                            "rb"
                        ) as invoice_file:

                            invoice_data = (
                                invoice_file.read()
                            )


                        st.success(
                            "✅ Invoice generated successfully!"
                        )


                        st.download_button(
                            label="⬇️ Download Invoice PDF",

                            data=invoice_data,

                            file_name=invoice_filename,

                            mime="application/pdf",

                            use_container_width=True,

                            key=(
                                f"download_new_invoice_"
                                f"{sale_id}"
                            )
                        )


                    except Exception as invoice_error:

                        st.error(
                            f"❌ Invoice generation failed: "
                            f"{invoice_error}"
                        )


                    st.info(
                        "📦 Inventory stock was automatically "
                        "updated for all products."
                    )


                    # Clear cached analytics because the database changed.
                    clear_read_cache()

                    # Clear cart only after successful sale
                    st.session_state.sale_cart = []


                else:

                    st.error(
                        "❌ Sale could not be recorded."
                    )

                    st.warning(
                        result.get(
                            "message",
                            "Unknown error."
                        )
                    )


            except Exception as e:

                st.error(
                    f"❌ Error recording sale: {e}"
                )


        # ====================================================
        # CLEAR BILL
        # ====================================================

        if st.button(
            "🧹 Clear Entire Bill",
            use_container_width=True
        ):

            st.session_state.sale_cart = []

            st.rerun()


# ============================================================
# SALES FORECAST
# ============================================================

elif page == "📈 Sales Forecast":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.header(
        "📈 7-Day Sales Forecast"
    )

    st.write(
        "Estimated future revenue based on "
        "historical sales patterns."
    )

    st.warning(
        "⚠️ Forecast values are predictions, "
        "not actual sales and are not guaranteed."
    )

    st.divider()


    try:

        forecast_result = (
            cached_sales_forecast()
        )


        if (
            isinstance(
                forecast_result,
                dict
            )
            and
            forecast_result.get(
                "status"
            ) == "success"
        ):

            forecast = (
                forecast_result.get(
                    "forecast",
                    []
                )
            )

            historical_days = int(
                forecast_result.get(
                    "historical_days",
                    0
                ) or 0
            )

            forecast_days = int(
                forecast_result.get(
                    "forecast_days",
                    len(forecast)
                ) or len(forecast)
            )


            if forecast:

                predictions = [
                    float(
                        item.get(
                            "predicted_revenue",
                            0
                        ) or 0
                    )

                    for item in forecast
                ]


                total_forecast = sum(
                    predictions
                )

                average_forecast = (
                    total_forecast /
                    len(predictions)
                )


                first_prediction = (
                    predictions[0]
                )

                last_prediction = (
                    predictions[-1]
                )


                trend_difference = (
                    last_prediction -
                    first_prediction
                )


                if abs(
                    first_prediction
                ) > 0:

                    trend_percentage = (
                        trend_difference /
                        first_prediction
                    ) * 100

                else:

                    trend_percentage = 0


                st.subheader(
                    "📊 Forecast Summary"
                )


                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:

                    st.metric(
                        "📅 Forecast Period",
                        f"{forecast_days} Days"
                    )

                with col2:

                    st.metric(
                        "💰 Expected Revenue",
                        f"₹{total_forecast:,.2f}"
                    )

                with col3:

                    st.metric(
                        "💵 Average Daily Revenue",
                        f"₹{average_forecast:,.2f}"
                    )

                with col4:

                    st.metric(
                        "📚 Historical Data",
                        f"{historical_days} Days"
                    )


                st.divider()


                st.subheader(
                    "📈 Forecast Trend"
                )


                if trend_difference > 0.01:

                    st.success(
                        f"📈 Expected revenue is increasing. "
                        f"The forecast rises by "
                        f"₹{trend_difference:,.2f} "
                        f"({trend_percentage:+.2f}%) "
                        "from the first to the last forecast day."
                    )

                elif trend_difference < -0.01:

                    st.warning(
                        f"📉 Expected revenue is decreasing. "
                        f"The forecast changes by "
                        f"₹{trend_difference:,.2f} "
                        f"({trend_percentage:+.2f}%) "
                        "from the first to the last forecast day."
                    )

                else:

                    st.info(
                        "➡️ Expected revenue is approximately "
                        "stable throughout the forecast period."
                    )


                st.divider()


                st.subheader(
                    "📊 Expected Daily Revenue"
                )


                forecast_df = pd.DataFrame(
                    [
                        {
                            "Date":
                                item.get(
                                    "date",
                                    ""
                                ),

                            "Predicted Revenue":
                                float(
                                    item.get(
                                        "predicted_revenue",
                                        0
                                    ) or 0
                                )
                        }

                        for item in forecast
                    ]
                )


                forecast_df["Date"] = (
                    pd.to_datetime(
                        forecast_df["Date"]
                    )
                )


                forecast_df = (
                    forecast_df
                    .set_index("Date")
                )


                st.line_chart(
                    forecast_df[
                        "Predicted Revenue"
                    ],
                    use_container_width=True
                )


                st.divider()


                st.subheader(
                    "📅 Daily Predictions"
                )


                cols = st.columns(
                    min(
                        len(forecast),
                        4
                    )
                )


                for index, item in enumerate(
                    forecast
                ):

                    predicted = float(
                        item.get(
                            "predicted_revenue",
                            0
                        ) or 0
                    )


                    with cols[
                        index % len(cols)
                    ]:

                        st.metric(
                            str(
                                item.get(
                                    "date",
                                    ""
                                )
                            ),

                            f"₹{predicted:,.2f}"
                        )


                st.divider()


                st.subheader(
                    "📋 Detailed Forecast"
                )


                forecast_display = [
                    {
                        "Date":
                            item.get(
                                "date",
                                ""
                            ),

                        "Predicted Revenue":
                            (
                                f"₹{float(item.get('predicted_revenue', 0) or 0):,.2f}"
                            )
                    }

                    for item in forecast
                ]


                st.dataframe(
                    forecast_display,
                    use_container_width=True,
                    hide_index=True
                )


                st.divider()


                st.subheader(
                    "💡 Forecast Interpretation"
                )


                st.write(
                    f"Based on {historical_days} "
                    "historical sales days, the model "
                    f"expects approximately "
                    f"**₹{total_forecast:,.2f}** "
                    f"in revenue over the next "
                    f"{forecast_days} days."
                )


                if trend_difference < 0:

                    st.write(
                        "The model indicates a mild "
                        "downward trend. Consider monitoring "
                        "daily sales, inventory availability "
                        "and product demand."
                    )

                elif trend_difference > 0:

                    st.write(
                        "The model indicates a positive trend. "
                        "Make sure popular products have "
                        "sufficient stock."
                    )

                else:

                    st.write(
                        "The model indicates a relatively "
                        "stable revenue trend."
                    )


            else:

                st.info(
                    "No forecast values were returned."
                )


        else:

            message = (
                forecast_result.get(
                    "message",
                    "Forecast could not be generated."
                )

                if isinstance(
                    forecast_result,
                    dict
                )

                else
                "Forecast could not be generated."
            )

            st.warning(
                f"⚠️ {message}"
            )


    except Exception as e:

        st.error(
            f"Forecast error: {e}"
        )


# ============================================================
# BUSINESS INSIGHTS
# ============================================================

elif page == "💡 Business Insights":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.header(
        "💡 AI Business Insights"
    )

    st.write(
        "Actionable business insights based on "
        "your real sales, profit, inventory and "
        "forecast data."
    )

    st.divider()


    try:

        # ====================================================
        # LOAD CACHED ANALYTICS
        # ====================================================
        # Business Insights previously calculated these metrics,
        # then calculated them again inside get_business_insights(),
        # and then generated another enhanced summary. That caused
        # many repeated cloud database / AI calls.

        total_revenue = cached_total_revenue()
        total_transactions = cached_total_transactions()
        profit_summary = cached_profit_summary()
        profit_by_product = cached_profit_by_product(10)
        inventory_summary = cached_inventory_summary()
        forecast = cached_sales_forecast()

        insights = cached_business_insights()

        if isinstance(insights, dict):
            insight_list = insights.get("insights", [])
            recommendation_list = insights.get("recommendations", [])
        elif isinstance(insights, list):
            insight_list = insights
            recommendation_list = []
        else:
            insight_list = []
            recommendation_list = []

        # ====================================================
        # FINANCIAL OVERVIEW
        # ====================================================

        revenue = float(
            profit_summary.get(
                "total_revenue",
                total_revenue
            ) or 0
        )

        cost = float(
            profit_summary.get(
                "total_cost",
                0
            ) or 0
        )

        profit = float(
            profit_summary.get(
                "total_profit",
                0
            ) or 0
        )

        margin = float(
            profit_summary.get(
                "profit_margin",
                0
            ) or 0
        )


        st.subheader(
            "💰 Financial Overview"
        )


        col1, col2, col3, col4 = (
            st.columns(4)
        )


        with col1:

            st.metric(
                "💰 Total Revenue",
                f"₹{revenue:,.2f}"
            )

        with col2:

            st.metric(
                "💸 Total Cost",
                f"₹{cost:,.2f}"
            )

        with col3:

            st.metric(
                "📈 Total Profit",
                f"₹{profit:,.2f}"
            )

        with col4:

            st.metric(
                "📊 Profit Margin",
                f"{margin:.2f}%"
            )


        st.divider()


        # ====================================================
        # BUSINESS KPIs
        # ====================================================

        st.subheader(
            "📊 Business Overview"
        )


        average_transaction = (
            revenue /
            int(total_transactions)

            if int(total_transactions) > 0

            else 0
        )


        col1, col2, col3 = (
            st.columns(3)
        )


        with col1:

            st.metric(
                "🧾 Transactions",
                f"{int(total_transactions):,}"
            )

        with col2:

            st.metric(
                "💵 Average Transaction",
                f"₹{average_transaction:,.2f}"
            )

        with col3:

            st.metric(
                "📦 Products",
                f"{int(inventory_summary.get('total_products', 0) or 0):,}"
            )


        st.divider()


        # ====================================================
        # PROFITABLE PRODUCTS
        # ====================================================

        if profit_by_product:

            st.subheader(
                "🏆 Product Profitability"
            )


            profit_rows = [
                {
                    "Product":
                        item.get(
                            "product_name",
                            "Unknown"
                        ),

                    "Quantity Sold":
                        int(
                            item.get(
                                "quantity_sold",
                                0
                            ) or 0
                        ),

                    "Revenue":
                        (
                            f"₹{float(item.get('revenue', 0) or 0):,.2f}"
                        ),

                    "Cost":
                        (
                            f"₹{float(item.get('cost', 0) or 0):,.2f}"
                        ),

                    "Profit":
                        (
                            f"₹{float(item.get('profit', 0) or 0):,.2f}"
                        ),

                    "Margin":
                        (
                            f"{float(item.get('profit_margin', 0) or 0):.2f}%"
                        )
                }

                for item in profit_by_product
            ]


            st.dataframe(
                profit_rows,
                use_container_width=True,
                hide_index=True
            )


        st.divider()


        # ====================================================
        # INVENTORY STATUS
        # ====================================================

        st.subheader(
            "📦 Inventory Status"
        )


        inventory_total = int(
            inventory_summary.get(
                "total_products",
                0
            ) or 0
        )

        inventory_units = float(
            inventory_summary.get(
                "total_units",
                0
            ) or 0
        )

        low_stock_count = int(
            inventory_summary.get(
                "low_stock",
                0
            ) or 0
        )

        out_of_stock_count = int(
            inventory_summary.get(
                "out_of_stock",
                0
            ) or 0
        )

        inventory_cost_value = float(
            inventory_summary.get(
                "inventory_cost_value",
                0
            ) or 0
        )


        col1, col2, col3, col4, col5 = (
            st.columns(5)
        )


        with col1:

            st.metric(
                "Products",
                f"{inventory_total:,}"
            )

        with col2:

            st.metric(
                "Units",
                f"{inventory_units:,.0f}"
            )

        with col3:

            st.metric(
                "⚠️ Low Stock",
                f"{low_stock_count:,}"
            )

        with col4:

            st.metric(
                "❌ Out of Stock",
                f"{out_of_stock_count:,}"
            )

        with col5:

            st.metric(
                "Inventory Cost",
                f"₹{inventory_cost_value:,.2f}"
            )


        st.divider()


        # ====================================================
        # FORECAST
        # ====================================================

        if (
            isinstance(
                forecast,
                dict
            )
            and
            forecast.get(
                "status"
            ) == "success"
        ):

            forecast_data = (
                forecast.get(
                    "forecast",
                    []
                )
            )


            if forecast_data:

                forecast_total = sum(
                    float(
                        item.get(
                            "predicted_revenue",
                            0
                        ) or 0
                    )

                    for item in forecast_data
                )


                forecast_average = (
                    forecast_total /
                    len(forecast_data)
                )


                first_value = float(
                    forecast_data[0].get(
                        "predicted_revenue",
                        0
                    ) or 0
                )

                last_value = float(
                    forecast_data[-1].get(
                        "predicted_revenue",
                        0
                    ) or 0
                )


                if last_value > first_value:

                    forecast_trend = (
                        "📈 Increasing"
                    )

                elif last_value < first_value:

                    forecast_trend = (
                        "📉 Decreasing"
                    )

                else:

                    forecast_trend = (
                        "➡️ Stable"
                    )


                st.subheader(
                    "🔮 Sales Forecast"
                )


                col1, col2, col3 = (
                    st.columns(3)
                )


                with col1:

                    st.metric(
                        "Expected Revenue",
                        f"₹{forecast_total:,.2f}"
                    )

                with col2:

                    st.metric(
                        "Average / Day",
                        f"₹{forecast_average:,.2f}"
                    )

                with col3:

                    st.metric(
                        "Trend",
                        forecast_trend
                    )


                forecast_chart = pd.DataFrame(
                    [
                        {
                            "Date":
                                item.get(
                                    "date",
                                    ""
                                ),

                            "Predicted Revenue":
                                float(
                                    item.get(
                                        "predicted_revenue",
                                        0
                                    ) or 0
                                )
                        }

                        for item in forecast_data
                    ]
                )


                forecast_chart["Date"] = (
                    pd.to_datetime(
                        forecast_chart["Date"]
                    )
                )


                forecast_chart = (
                    forecast_chart
                    .set_index("Date")
                )


                st.line_chart(
                    forecast_chart[
                        "Predicted Revenue"
                    ],
                    use_container_width=True
                )


        st.divider()


        # ====================================================
        # INSIGHTS
        # ====================================================

        st.subheader(
            "🧠 Key Business Insights"
        )


        icons = {
            "Revenue": "💰",
            "Product": "🏆",
            "Profit": "💵",
            "Profitability": "📊",
            "Peak Hour": "⏰",
            "Payment": "💳",
            "Anomaly": "🚨",
            "Forecast": "🔮",
            "Forecast Trend": "📈",
            "Inventory": "📦",
        }


        if insight_list:

            for insight in insight_list:

                if not isinstance(
                    insight,
                    dict
                ):

                    st.info(
                        str(insight)
                    )

                    continue


                category = insight.get(
                    "category",
                    "Insight"
                )

                message = insight.get(
                    "insight",
                    ""
                )

                icon = icons.get(
                    category,
                    "💡"
                )


                with st.container(
                    border=True
                ):

                    st.subheader(
                        f"{icon} {category}"
                    )

                    st.write(
                        message
                    )

        else:

            st.info(
                "No business insights available."
            )


        st.divider()


        # ====================================================
        # RECOMMENDATIONS
        # ====================================================

        st.subheader(
            "💡 Recommended Actions"
        )


        if recommendation_list:

            for recommendation in (
                recommendation_list
            ):

                if not isinstance(
                    recommendation,
                    dict
                ):

                    st.info(
                        str(recommendation)
                    )

                    continue


                category = (
                    recommendation.get(
                        "category",
                        "Recommendation"
                    )
                )

                message = (
                    recommendation.get(
                        "recommendation",
                        ""
                    )
                )


                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"**💡 {category}**"
                    )

                    st.write(
                        message
                    )

        else:

            st.info(
                "No additional recommendations available."
            )


    except Exception as e:

        st.error(
            f"Business insight error: {e}"
        )


# ============================================================
# SALES REPORT
# ============================================================

elif page == "📋 Sales Report":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.header(
        "📋 Sales Report"
    )

    st.write(
        "Generate a report from actual sales data."
    )

    st.divider()


    # ========================================================
    # REPORT PERIOD
    # ========================================================

    report_option = st.radio(
        "Report Period",
        [
            "Last 7 Days",
            "Last 30 Days",
            "Last 3 Months",
            "Custom Date Range"
        ],
        horizontal=True
    )


    today_date = date.today()


    if report_option == "Last 7 Days":

        report_start = (
            today_date -
            timedelta(days=6)
        )

        report_end = today_date


    elif report_option == "Last 30 Days":

        report_start = (
            today_date -
            timedelta(days=29)
        )

        report_end = today_date


    elif report_option == "Last 3 Months":

        report_start = (
            today_date -
            timedelta(days=89)
        )

        report_end = today_date


    else:

        col1, col2 = st.columns(2)

        with col1:

            report_start = st.date_input(
                "Start Date",
                value=(
                    today_date -
                    timedelta(days=6)
                ),
                key="report_start"
            )

        with col2:

            report_end = st.date_input(
                "End Date",
                value=today_date,
                key="report_end"
            )


    # ========================================================
    # VALIDATION
    # ========================================================

    if report_start > report_end:

        st.error(
            "Start date cannot be after end date."
        )

        st.stop()


    st.info(
        f"Report period: "
        f"**{report_start}** to **{report_end}**"
    )


    # ========================================================
    # LOAD REPORT DATA
    # ========================================================

    try:

        report_summary = (
            get_date_range_summary(
                report_start,
                report_end
            )
        )

        report_sales = (
            get_sales_by_date_range(
                report_start,
                report_end
            )
        )

        report_products = (
            get_top_products_by_date_range(
                report_start,
                report_end
            )
        )


    except Exception as e:

        st.error(
            f"Report error: {e}"
        )

        st.stop()


    # ========================================================
    # REPORT SUMMARY
    # ========================================================

    report_revenue = float(
        report_summary.get(
            "revenue",
            0
        ) or 0
    )

    report_transactions = int(
        report_summary.get(
            "transactions",
            0
        ) or 0
    )

    report_average = (
        report_revenue /
        report_transactions

        if report_transactions > 0

        else 0
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    with col1:

        st.metric(
            "💰 Revenue",
            f"₹{report_revenue:,.2f}"
        )


    with col2:

        st.metric(
            "🧾 Transactions",
            f"{report_transactions:,}"
        )


    with col3:

        st.metric(
            "💵 Average Transaction",
            f"₹{report_average:,.2f}"
        )


    st.divider()


    # ========================================================
    # REPORT DATA
    # ========================================================

    if report_sales:

        report_df = pd.DataFrame(
            report_sales
        )


        # ----------------------------------------------------
        # NORMALIZE DATA
        # ----------------------------------------------------

        report_df["sale_date"] = (
            pd.to_datetime(
                report_df["sale_date"]
            )
            .dt.strftime(
                "%Y-%m-%d"
            )
        )


        report_df["revenue"] = (
            pd.to_numeric(
                report_df["revenue"],
                errors="coerce"
            )
            .fillna(0)
        )


        report_df["transactions"] = (
            pd.to_numeric(
                report_df["transactions"],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
        )


        # ----------------------------------------------------
        # DISPLAY TABLE
        # ----------------------------------------------------

        report_display = (
            report_df.rename(
                columns={
                    "sale_date":
                        "Date",

                    "transactions":
                        "Transactions",

                    "revenue":
                        "Revenue"
                }
            )
        )


        report_display["Revenue"] = (
            report_display["Revenue"]
            .apply(
                lambda x:
                f"₹{x:,.2f}"
            )
        )


        st.subheader(
            "📊 Daily Sales Report"
        )


        st.dataframe(
            report_display,
            use_container_width=True,
            hide_index=True
        )


        st.divider()


        # ====================================================
        # DOWNLOAD SECTION
        # ====================================================

        st.subheader(
            "⬇️ Download Report"
        )


        col1, col2 = st.columns(2)


        # ====================================================
        # CSV
        # ====================================================

        csv_df = report_df.copy()


        csv_df = csv_df.rename(
            columns={
                "sale_date":
                    "Date",

                "transactions":
                    "Transactions",

                "revenue":
                    "Revenue"
            }
        )


        csv_data = (
            csv_df
            .to_csv(
                index=False
            )
            .encode(
                "utf-8"
            )
        )


        with col1:

            st.download_button(
                label="⬇️ Download Sales Report CSV",

                data=csv_data,

                file_name=(
                    f"shopsense_sales_report_"
                    f"{report_start}_"
                    f"{report_end}.csv"
                ),

                mime="text/csv",

                use_container_width=True,

                key=(
                    f"download_csv_"
                    f"{report_start}_"
                    f"{report_end}"
                )
            )


        # ====================================================
        # EXCEL
        # ====================================================

        try:

            excel_data = (
                create_sales_excel_report(
                    report_df=csv_df,
                    report_products=report_products,
                    report_start=report_start,
                    report_end=report_end,
                    report_revenue=report_revenue,
                    report_transactions=report_transactions,
                    report_average=report_average
                )
            )


            with col2:

                st.download_button(
                    label="📊 Download Sales Report Excel",

                    data=excel_data,

                    file_name=(
                        f"shopsense_sales_report_"
                        f"{report_start}_"
                        f"{report_end}.xlsx"
                    ),

                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),

                    use_container_width=True,

                    key=(
                        f"download_excel_"
                        f"{report_start}_"
                        f"{report_end}"
                    )
                )


        except Exception as e:

            with col2:

                st.error(
                    f"Excel report generation failed: {e}"
                )


    else:

        st.info(
            "No sales found for the selected report period."
        )


    # ========================================================
    # TOP PRODUCTS
    # ========================================================

    st.subheader(
        "🏆 Top Products"
    )


    if report_products:

        product_report = []

        for item in report_products:

            product_report.append(
                {
                    "Product":
                        item.get(
                            "product_name",
                            ""
                        ),

                    "Quantity Sold":
                        int(
                            item.get(
                                "quantity_sold",
                                0
                            ) or 0
                        ),

                    "Revenue":
                        (
                            f"₹{float(item.get('revenue', 0) or 0):,.2f}"
                        )
                }
            )


        st.dataframe(
            product_report,
            use_container_width=True,
            hide_index=True
        )


    else:

        st.info(
            "No product sales found."
        )


# ============================================================
# PROFIT & LOSS
# ============================================================

elif page == "💰 Profit & Loss":

    if not is_admin(
        st.session_state.get("role")
    ):

        st.error(
            "🚫 Admin access required."
        )

        st.stop()


    st.header(
        "💰 Profit & Loss"
    )

    st.write(
        "Analyze revenue, product cost, gross profit "
        "and profit margin from your actual sales data."
    )

    st.divider()


    try:

        profit_summary = (
            get_profit_summary()
        )

        product_profit = (
            get_profit_by_product(10)
        )

        least_profitable = (
            get_least_profitable_products(10)
        )

        daily_profit = (
            get_daily_profit(30)
        )

        monthly_profit = (
            get_monthly_profit(12)
        )

    except Exception as e:

        st.error(
            f"Profit & Loss database error: {e}"
        )

        st.stop()


    # ========================================================
    # KPI
    # ========================================================

    revenue = float(
        profit_summary.get(
            "total_revenue",
            0
        ) or 0
    )

    cost = float(
        profit_summary.get(
            "total_cost",
            0
        ) or 0
    )

    profit = float(
        profit_summary.get(
            "total_profit",
            0
        ) or 0
    )

    margin = float(
        profit_summary.get(
            "profit_margin",
            0
        ) or 0
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    with col1:

        st.metric(
            "💰 Total Revenue",
            f"₹{revenue:,.2f}"
        )

    with col2:

        st.metric(
            "💸 Total Cost",
            f"₹{cost:,.2f}"
        )

    with col3:

        st.metric(
            "📈 Gross Profit",
            f"₹{profit:,.2f}"
        )

    with col4:

        st.metric(
            "📊 Profit Margin",
            f"{margin:.2f}%"
        )


    st.divider()


    # ========================================================
    # PROFIT BY PRODUCT
    # ========================================================

    st.subheader(
        "🏆 Profit by Product"
    )


    if product_profit:

        product_rows = []

        for item in product_profit:

            product_rows.append(
                {
                    "Product":
                        item.get(
                            "product_name",
                            ""
                        ),

                    "Quantity Sold":
                        int(
                            item.get(
                                "quantity_sold",
                                0
                            ) or 0
                        ),

                    "Revenue":
                        float(
                            item.get(
                                "revenue",
                                0
                            ) or 0
                        ),

                    "Cost":
                        float(
                            item.get(
                                "cost",
                                0
                            ) or 0
                        ),

                    "Profit":
                        float(
                            item.get(
                                "profit",
                                0
                            ) or 0
                        ),

                    "Profit Margin":
                        float(
                            item.get(
                                "profit_margin",
                                0
                            ) or 0
                        )
                }
            )


        product_df = pd.DataFrame(
            product_rows
        )


        chart_df = (
            product_df[
                [
                    "Product",
                    "Profit"
                ]
            ]
            .set_index(
                "Product"
            )
        )


        st.bar_chart(
            chart_df
        )


        display_df = (
            product_df.copy()
        )


        display_df["Revenue"] = (
            display_df["Revenue"]
            .apply(
                lambda x:
                f"₹{x:,.2f}"
            )
        )


        display_df["Cost"] = (
            display_df["Cost"]
            .apply(
                lambda x:
                f"₹{x:,.2f}"
            )
        )


        display_df["Profit"] = (
            display_df["Profit"]
            .apply(
                lambda x:
                f"₹{x:,.2f}"
            )
        )


        display_df["Profit Margin"] = (
            display_df["Profit Margin"]
            .apply(
                lambda x:
                f"{x:.2f}%"
            )
        )


        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No product profit data available."
        )


    st.divider()


    # ========================================================
    # MOST PROFITABLE
    # ========================================================

    st.subheader(
        "🥇 Most Profitable Products"
    )


    if product_profit:

        top_display = []


        for item in product_profit[:5]:

            top_display.append(
                {
                    "Product":
                        item.get(
                            "product_name",
                            ""
                        ),

                    "Profit":
                        (
                            f"₹{float(item.get('profit', 0) or 0):,.2f}"
                        ),

                    "Margin":
                        (
                            f"{float(item.get('profit_margin', 0) or 0):.2f}%"
                        )
                }
            )


        st.dataframe(
            top_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No profitable products available."
        )


    # ========================================================
    # LEAST PROFITABLE
    # ========================================================

    st.subheader(
        "📉 Least Profitable Products"
    )


    if least_profitable:

        least_display = []


        for item in least_profitable[:5]:

            least_display.append(
                {
                    "Product":
                        item.get(
                            "product_name",
                            ""
                        ),

                    "Profit":
                        (
                            f"₹{float(item.get('profit', 0) or 0):,.2f}"
                        ),

                    "Margin":
                        (
                            f"{float(item.get('profit_margin', 0) or 0):.2f}%"
                        )
                }
            )


        st.dataframe(
            least_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No product profitability data available."
        )


    st.divider()


    # ========================================================
    # DAILY PROFIT
    # ========================================================

    st.subheader(
        "📅 Daily Profit — Last 30 Days"
    )


    if daily_profit:

        daily_df = pd.DataFrame(
            daily_profit
        )


        daily_df["sale_date"] = (
            pd.to_datetime(
                daily_df["sale_date"]
            )
        )


        daily_df["profit"] = (
            pd.to_numeric(
                daily_df["profit"],
                errors="coerce"
            )
            .fillna(0)
        )


        daily_chart = (
            daily_df[
                [
                    "sale_date",
                    "profit"
                ]
            ]
            .set_index(
                "sale_date"
            )
        )


        st.line_chart(
            daily_chart
        )


        daily_display = (
            daily_df.copy()
        )


        for column in [
            "revenue",
            "cost",
            "profit"
        ]:

            if column in daily_display.columns:

                daily_display[column] = (
                    pd.to_numeric(
                        daily_display[column],
                        errors="coerce"
                    )
                    .fillna(0)
                    .apply(
                        lambda x:
                        f"₹{x:,.2f}"
                    )
                )


        daily_display = (
            daily_display.rename(
                columns={
                    "sale_date":
                        "Date",

                    "revenue":
                        "Revenue",

                    "cost":
                        "Cost",

                    "profit":
                        "Profit"
                }
            )
        )


        st.dataframe(
            daily_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No daily profit data available."
        )


    st.divider()


    # ========================================================
    # MONTHLY PROFIT
    # ========================================================

    st.subheader(
        "📆 Monthly Profit"
    )


    if monthly_profit:

        monthly_df = pd.DataFrame(
            monthly_profit
        )


        monthly_df["profit"] = (
            pd.to_numeric(
                monthly_df["profit"],
                errors="coerce"
            )
            .fillna(0)
        )


        monthly_chart = (
            monthly_df[
                [
                    "month",
                    "profit"
                ]
            ]
            .set_index(
                "month"
            )
        )


        st.bar_chart(
            monthly_chart
        )


        monthly_display = (
            monthly_df.copy()
        )


        for column in [
            "revenue",
            "cost",
            "profit"
        ]:

            if column in monthly_display.columns:

                monthly_display[column] = (
                    pd.to_numeric(
                        monthly_display[column],
                        errors="coerce"
                    )
                    .fillna(0)
                    .apply(
                        lambda x:
                        f"₹{x:,.2f}"
                    )
                )


        if "profit_margin" in (
            monthly_display.columns
        ):

            monthly_display[
                "profit_margin"
            ] = (
                pd.to_numeric(
                    monthly_display[
                        "profit_margin"
                    ],
                    errors="coerce"
                )
                .fillna(0)
                .apply(
                    lambda x:
                    f"{x:.2f}%"
                )
            )


        monthly_display = (
            monthly_display.rename(
                columns={
                    "month":
                        "Month",

                    "revenue":
                        "Revenue",

                    "cost":
                        "Cost",

                    "profit":
                        "Profit",

                    "profit_margin":
                        "Profit Margin"
                }
            )
        )


        st.dataframe(
            monthly_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No monthly profit data available."
        )


    st.divider()


    # ========================================================
    # DATE RANGE PROFIT
    # ========================================================

    st.subheader(
        "📆 Profit by Date Range"
    )


    today_date = date.today()


    col1, col2 = st.columns(2)


    with col1:

        profit_start = st.date_input(
            "Start Date",
            value=(
                today_date -
                timedelta(days=6)
            ),
            key="profit_start_date"
        )


    with col2:

        profit_end = st.date_input(
            "End Date",
            value=today_date,
            key="profit_end_date"
        )


    if profit_start > profit_end:

        st.error(
            "Start date cannot be after end date."
        )

    else:

        if st.button(
            "🔍 Analyze Date Range Profit",
            type="primary"
        ):

            try:

                range_profit = (
                    get_profit_by_date_range(
                        profit_start,
                        profit_end
                    )
                )


                range_revenue = float(
                    range_profit.get(
                        "revenue",
                        0
                    ) or 0
                )

                range_cost = float(
                    range_profit.get(
                        "cost",
                        0
                    ) or 0
                )

                range_total_profit = float(
                    range_profit.get(
                        "profit",
                        0
                    ) or 0
                )

                range_margin = float(
                    range_profit.get(
                        "profit_margin",
                        0
                    ) or 0
                )

                range_transactions = int(
                    range_profit.get(
                        "transactions",
                        0
                    ) or 0
                )


                col1, col2, col3, col4, col5 = (
                    st.columns(5)
                )


                with col1:

                    st.metric(
                        "Revenue",
                        f"₹{range_revenue:,.2f}"
                    )

                with col2:

                    st.metric(
                        "Cost",
                        f"₹{range_cost:,.2f}"
                    )

                with col3:

                    st.metric(
                        "Profit",
                        f"₹{range_total_profit:,.2f}"
                    )

                with col4:

                    st.metric(
                        "Margin",
                        f"{range_margin:.2f}%"
                    )

                with col5:

                    st.metric(
                        "Transactions",
                        f"{range_transactions:,}"
                    )


            except Exception as e:

                st.error(
                    f"Date range profit error: {e}"
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "ShopSense AI | "
    "MySQL + Python + Analytics + Gemini AI"
)