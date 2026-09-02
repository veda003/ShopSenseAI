from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os


# ============================================================
# FONT SETUP
# ============================================================

# Get the folder where invoice.py is located
UTILS_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# DejaVu Sans font
FONT_PATH = os.path.join(
    UTILS_DIR,
    "DejaVuSans.ttf"
)


# ============================================================
# CHECK FONT
# ============================================================

if not os.path.exists(FONT_PATH):

    raise FileNotFoundError(
        "DejaVuSans.ttf was not found.\n"
        f"Expected location:\n{FONT_PATH}"
    )


# ============================================================
# REGISTER FONT
# ============================================================

pdfmetrics.registerFont(
    TTFont(
        "DejaVuSans",
        FONT_PATH
    )
)


# Use the same font for normal and bold text
NORMAL_FONT = "DejaVuSans"
BOLD_FONT = "DejaVuSans"


# ============================================================
# GENERATE INVOICE
# ============================================================

def generate_invoice(
    sale_id,
    payment_method,
    items,
    total_amount,
    output_path
):
    """
    Generate a professional PDF invoice
    for a completed ShopSense AI sale.
    """

    # ========================================================
    # CREATE OUTPUT DIRECTORY
    # ========================================================

    output_directory = os.path.dirname(
        output_path
    )

    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True
        )


    # ========================================================
    # PDF DOCUMENT
    # ========================================================

    document = SimpleDocTemplate(

        output_path,

        pagesize=A4,

        rightMargin=20 * mm,
        leftMargin=20 * mm,

        topMargin=20 * mm,
        bottomMargin=20 * mm
    )


    # ========================================================
    # STYLES
    # ========================================================

    styles = getSampleStyleSheet()


    title_style = ParagraphStyle(

        "InvoiceTitle",

        parent=styles["Title"],

        fontName=BOLD_FONT,

        fontSize=22,

        leading=26,

        alignment=1,

        spaceAfter=6
    )


    subtitle_style = ParagraphStyle(

        "InvoiceSubtitle",

        parent=styles["Heading2"],

        fontName=NORMAL_FONT,

        fontSize=14,

        leading=18,

        alignment=1,

        spaceAfter=15
    )


    heading_style = ParagraphStyle(

        "InvoiceHeading",

        parent=styles["Heading2"],

        fontName=BOLD_FONT,

        fontSize=14,

        leading=18,

        spaceAfter=8
    )


    normal_style = ParagraphStyle(

        "InvoiceNormal",

        parent=styles["Normal"],

        fontName=NORMAL_FONT,

        fontSize=10,

        leading=14
    )


    small_style = ParagraphStyle(

        "InvoiceSmall",

        parent=styles["Normal"],

        fontName=NORMAL_FONT,

        fontSize=9,

        leading=12
    )


    # ========================================================
    # PDF ELEMENTS
    # ========================================================

    elements = []


    # ========================================================
    # HEADER
    # ========================================================

    elements.append(

        Paragraph(
            "ShopSense AI",
            title_style
        )

    )


    elements.append(

        Paragraph(
            "SALES RECEIPT",
            subtitle_style
        )

    )


    elements.append(
        Spacer(1, 5)
    )


    # ========================================================
    # SALE INFORMATION
    # ========================================================

    sale_information = [

        [
            Paragraph(
                "Sale ID",
                normal_style
            ),

            Paragraph(
                str(sale_id),
                normal_style
            )
        ],

        [
            Paragraph(
                "Payment Method",
                normal_style
            ),

            Paragraph(
                str(payment_method).upper(),
                normal_style
            )
        ]

    ]


    sale_table = Table(

        sale_information,

        colWidths=[
            55 * mm,
            95 * mm
        ]

    )


    sale_table.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                NORMAL_FONT
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])

    )


    elements.append(
        sale_table
    )


    elements.append(
        Spacer(1, 20)
    )


    # ========================================================
    # SALE DETAILS
    # ========================================================

    elements.append(

        Paragraph(
            "Sale Details",
            heading_style
        )

    )


    elements.append(
        Spacer(1, 5)
    )


    # ========================================================
    # TABLE HEADER
    # ========================================================

    item_data = [

        [

            Paragraph(
                "Product",
                normal_style
            ),

            Paragraph(
                "Quantity",
                normal_style
            ),

            Paragraph(
                "Unit Price",
                normal_style
            ),

            Paragraph(
                "Total",
                normal_style
            )

        ]

    ]


    # ========================================================
    # ADD ITEMS
    # ========================================================

    for item in items:

        product_name = str(

            item.get(
                "product_name",
                ""
            )

        )


        quantity = int(

            item.get(
                "quantity",
                0
            )

        )


        unit_price = float(

            item.get(
                "unit_price",
                0
            )

        )


        item_total = float(

            item.get(
                "total",
                0
            )

        )


        item_data.append(

            [

                Paragraph(
                    product_name,
                    normal_style
                ),

                Paragraph(
                    str(quantity),
                    normal_style
                ),

                Paragraph(
                    f"₹{unit_price:,.2f}",
                    normal_style
                ),

                Paragraph(
                    f"₹{item_total:,.2f}",
                    normal_style
                )

            ]

        )


    # ========================================================
    # ITEMS TABLE
    # ========================================================

    item_table = Table(

        item_data,

        colWidths=[
            65 * mm,
            25 * mm,
            35 * mm,
            35 * mm
        ],

        repeatRows=1
    )


    item_table.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                NORMAL_FONT
            ),

            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER"
            ),

            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "RIGHT"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])

    )


    elements.append(
        item_table
    )


    elements.append(
        Spacer(1, 20)
    )


    # ========================================================
    # TOTAL
    # ========================================================

    total_table = Table(

        [

            [

                Paragraph(
                    "TOTAL",
                    heading_style
                ),

                Paragraph(
                    f"₹{float(total_amount):,.2f}",
                    heading_style
                )

            ]

        ],

        colWidths=[
            100 * mm,
            60 * mm
        ]

    )


    total_table.setStyle(

        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.8,
                colors.black
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                BOLD_FONT
            ),

            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "RIGHT"
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                10
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                10
            )

        ])

    )


    elements.append(
        total_table
    )


    elements.append(
        Spacer(1, 30)
    )


    # ========================================================
    # FOOTER
    # ========================================================

    elements.append(

        Paragraph(
            "Thank you for your purchase!",
            normal_style
        )

    )


    elements.append(
        Spacer(1, 5)
    )


    elements.append(

        Paragraph(
            "ShopSense AI | Sales Management & Business Intelligence",
            small_style
        )

    )


    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        elements
    )


    return output_path