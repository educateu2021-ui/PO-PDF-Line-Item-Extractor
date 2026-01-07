import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="PO Line Item Extractor", layout="wide")

st.title("📄 FCA / Stellantis PO Line Item Extractor")
st.caption("Upload PO PDF → Extract line items → Download Excel")

uploaded_file = st.file_uploader(
    "Upload Purchase Order PDF",
    type=["pdf"]
)

def extract_line_items_fca(pdf_file):
    items = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            current_item = {}

            for line in lines:
                # Item number + description
                item_match = re.match(r"^(\d+)\s+(.*)", line)
                if item_match and "Delivery date" not in line:
                    if current_item:
                        items.append(current_item)
                        current_item = {}

                    current_item["Item"] = item_match.group(1)
                    current_item["Description"] = item_match.group(2)

                # Delivery date
                if "Delivery date:" in line:
                    date = line.split("Delivery date:")[-1].strip()
                    current_item["Delivery Date"] = date

                # Quantity / UOM / Price / Net Amount
                value_match = re.search(
                    r"(\d+\.\d+)\s+(LO|EA|DAY|UN)\s+([\d,]+\.\d+)/1/\s+USD\s+([\d,]+\.\d+)\s+USD",
                    line
                )

                if value_match:
                    current_item["Quantity"] = float(value_match.group(1))
                    current_item["UOM"] = value_match.group(2)
                    current_item["Unit Price (USD)"] = float(value_match.group(3).replace(",", ""))
                    current_item["Net Amount (USD)"] = float(value_match.group(4).replace(",", ""))

            if current_item:
                items.append(current_item)

    return pd.DataFrame(items)


if uploaded_file:
    st.success("PDF uploaded successfully")

    with st.spinner("Extracting line items..."):
        df = extract_line_items_fca(uploaded_file)

    if df.empty:
        st.error("No line items detected. PDF may be scanned or formatted differently.")
    else:
        st.subheader("📦 Extracted Line Items")
        st.dataframe(df, use_container_width=True)

        # Totals
        col1, col2 = st.columns(2)
        col1.metric("Total Net Amount", f"${df['Net Amount (USD)'].sum():,.2f}")
        col2.metric("Total Line Items", len(df))

        # Excel download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Line Items")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="po_line_items.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")
st.caption("Designed for FCA / Stellantis PO formats (text-based PDFs)")
