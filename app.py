import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="STLA / FCA PO Table Extractor", layout="wide")
st.title("📄 STLA / FCA PO Table Extractor")
st.caption("Extract Item / Material / Quantity / Price / Amount directly from PO")

uploaded_file = st.file_uploader("Upload Purchase Order PDF", type=["pdf"])

def extract_po_table(pdf_file):
    rows = []
    current = {}

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                line = line.strip()

                # ---------------------------------
                # Item + Material
                # Example: "1 999760227"
                # ---------------------------------
                item_match = re.match(r"^(\d+)\s+(\d{9})$", line)
                if item_match:
                    if current:
                        rows.append(current)
                    current = {
                        "Item": item_match.group(1),
                        "Material": item_match.group(2),
                        "Quantity": None,
                        "UOM": None,
                        "Unit Price / Per / Currency": None,
                        "Effective Value": None,
                        "Net Amount": None,
                    }
                    continue

                # ---------------------------------
                # Quantity + UOM + Unit Price
                # Example: "120.000 EA 610.95/1/ USD"
                # ---------------------------------
                qty_match = re.search(
                    r"(\d+(?:\.\d+)?)\s+(EA|DAY|LO|UN)\s+([\d,]+\.\d+/1/\s+USD)",
                    line
                )
                if qty_match and current:
                    current["Quantity"] = float(qty_match.group(1))
                    current["UOM"] = qty_match.group(2)
                    current["Unit Price / Per / Currency"] = qty_match.group(3)

                # ---------------------------------
                # Effective Value + Net Amount
                # Example: "73,314.00 USD 73,314.00 USD"
                # ---------------------------------
                value_match = re.search(
                    r"([\d,]+\.\d+)\s+USD\s+([\d,]+\.\d+)\s+USD",
                    line
                )
                if value_match and current:
                    current["Effective Value"] = float(value_match.group(1).replace(",", ""))
                    current["Net Amount"] = float(value_match.group(2).replace(",", ""))

    if current:
        rows.append(current)

    return pd.DataFrame(rows)


if uploaded_file:
    with st.spinner("Extracting PO table..."):
        df = extract_po_table(uploaded_file)

    if df.empty:
        st.error("No PO table rows detected.")
    else:
        st.subheader("📦 Extracted PO Line Items")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="PO Table")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="po_table_extracted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
