import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="STLA PO Line Item Extractor", layout="wide")
st.title("📄 STLA / FCA PO Line Item Extractor")
st.caption("Upload PO PDF → Extract required line items → Download Excel")

uploaded_file = st.file_uploader("Upload PO PDF", type=["pdf"])

def classify_category(description):
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

                # Start of item
                item_match = re.match(r"^(\d+)\s+(\d{9})", line)
                if item_match:
                    if current:
                        items.append(current)
                    current = {
                        "Item": item_match.group(1),
                        "Material": item_match.group(2)
                    }

                # Description
                if "DEV" in line or "LAPTOP" in line:
                    current["Description"] = line.strip()

                # Delivery date
                if "Delivery date:" in line:
                    current["Delivery Date"] = line.split("Delivery date:")[-1].strip()

                # Qty / UOM / Price / Amount
                value_match = re.search(
                    r"(\d+[.,]?\d*)\s+(EA|DAY|LO|UN)\s+([\d,]+\.\d+)/1/\s+USD\s+([\d,]+\.\d+)\s+USD",
                    line
                )
                if value_match:
                    current["Quantity"] = float(value_match.group(1).replace(",", ""))
                    current["UOM"] = value_match.group(2)
                    current["Unit Price (USD)"] = float(value_match.group(3).replace(",", ""))
                    current["Net Amount (USD)"] = float(value_match.group(4).replace(",", ""))

    if current:
        items.append(current)

    df = pd.DataFrame(items)
    df["Category"] = df["Description"].apply(classify_category)
    return df


if uploaded_file:
    with st.spinner("Extracting line items..."):
        df = extract_items(uploaded_file)

    if df.empty:
        st.error("No line items found.")
    else:
        st.subheader("📦 Extracted Line Items")
        st.dataframe(df, use_container_width=True)

        col1, col2 = st.columns(2)
        col1.metric("Total Amount", f"${df['Net Amount (USD)'].sum():,.2f}")
        col2.metric("Line Items", len(df))

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="PO Line Items")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="stla_po_line_items.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
