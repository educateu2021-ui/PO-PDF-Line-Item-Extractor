import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

# -------------------------
# Page Config
# -------------------------
st.set_page_config(
    page_title="STLA / FCA PO Line Item Extractor",
    layout="wide"
)

st.title("📄 STLA / FCA PO Line Item Extractor")
st.caption("Upload PO PDF → Extract required line items → Download Excel")

uploaded_file = st.file_uploader(
    "Upload Purchase Order PDF",
    type=["pdf"]
)

# -------------------------
# Helpers
# -------------------------
def classify_category(description: str) -> str:
    if not isinstance(description, str):
        return "Unknown"

    desc = description.upper()

    if "LAPTOP" in desc or "HARDWARE" in desc or "HW" in desc:
        return "Hardware"
    if "TRAVEL" in desc:
        return "Travel"
    return "Labour"


def extract_items(pdf_file):
    items = []
    current = {}

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                line = line.strip()

                # -------------------------
                # Item start (Item + Material)
                # Example: "1 999760227 DEV016_USA_EXP"
                # -------------------------
                item_match = re.match(r"^(\d+)\s+(\d{9})", line)
                if item_match:
                    if current:
                        items.append(current)
                    current = {
                        "Item": item_match.group(1),
                        "Material": item_match.group(2),
                        "Description": "",
                        "Quantity": None,
                        "UOM": None,
                        "Unit Price (USD)": None,
                        "Net Amount (USD)": None,
                        "Delivery Date": None,
                    }
                    continue

                # -------------------------
                # Description lines
                # -------------------------
                if current and (
                    "DEV" in line
                    or "LAPTOP" in line
                    or "HARDWARE" in line
                    or "SERVICE" in line
                ):
                    if current["Description"]:
                        current["Description"] += " " + line
                    else:
                        current["Description"] = line

                # -------------------------
                # Delivery Date
                # -------------------------
                if "Delivery date:" in line and current:
                    current["Delivery Date"] = line.split("Delivery date:")[-1].strip()

                # -------------------------
                # Quantity / UOM / Unit Price / Net Amount
                # Handles FCA / STLA formats
                # -------------------------
                value_match = re.search(
                    r"(\d+(?:\.\d+)?)\s+(EA|DAY|LO|UN)\s+([\d,]+\.\d+)/1/\s+USD\s+([\d,]+\.\d+)\s+USD",
                    line
                )

                if value_match and current:
                    current["Quantity"] = float(value_match.group(1).replace(",", ""))
                    current["UOM"] = value_match.group(2)
                    current["Unit Price (USD)"] = float(value_match.group(3).replace(",", ""))
                    current["Net Amount (USD)"] = float(value_match.group(4).replace(",", ""))

    if current:
        items.append(current)

    df = pd.DataFrame(items)

    # -------------------------
    # Force required columns (CRITICAL FIX)
    # -------------------------
    required_cols = [
        "Item",
        "Material",
        "Description",
        "Quantity",
        "UOM",
        "Unit Price (USD)",
        "Net Amount (USD)",
        "Delivery Date",
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = None

    df["Category"] = df["Description"].apply(classify_category)

    return df


# -------------------------
# Main App Logic
# -------------------------
if uploaded_file:
    with st.spinner("Extracting line items..."):
        df = extract_items(uploaded_file)

    if df.empty:
        st.error("No line items could be extracted from this PDF.")
    else:
        st.subheader("📦 Extracted Line Items")

        st.dataframe(df, use_container_width=True)

        # -------------------------
        # KPIs (SAFE — no KeyError)
        # -------------------------
        col1, col2 = st.columns(2)

        total_amount = (
            df["Net Amount (USD)"].sum()
            if df["Net Amount (USD)"].notna().any()
            else 0.0
        )

        col1.metric("Total Net Amount", f"${total_amount:,.2f}")
        col2.metric("Line Items", len(df))

        # -------------------------
        # Excel Export
        # -------------------------
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="PO Line Items")

        st.download_button(
            label="⬇️ Download Excel",
            data=output.getvalue(),
            file_name="stla_po_line_items.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

st.markdown("---")
st.caption("Robust extractor for STLA / FCA Purchase Orders • No highlighting required")
