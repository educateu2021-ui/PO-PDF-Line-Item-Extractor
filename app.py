import streamlit as st
import pdfplumber
import pandas as pd
import re

st.set_page_config(page_title="PO PDF Line Item Extractor", layout="wide")

st.title("📄 PO PDF Line Item Extractor")
st.caption("Upload a Purchase Order PDF to extract line items automatically")

uploaded_file = st.file_uploader(
    "Upload PO PDF",
    type=["pdf"]
)

def extract_line_items(pdf):
    rows = []

    with pdfplumber.open(pdf) as pdf_file:
        for page in pdf_file.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                # Typical PO line item pattern (adjustable)
                match = re.search(
                    r"(\d+)\s+(.+?)\s+(\d+(?:\.\d+)?)\s+(EA|DAY|UN)\s+([\d,.]+)\s+USD\s+([\d,.]+)\s+USD",
                    line
                )

                if match:
                    rows.append({
                        "Item": match.group(1),
                        "Description": match.group(2),
                        "Quantity": float(match.group(3)),
                        "UOM": match.group(4),
                        "Unit Price (USD)": float(match.group(5).replace(",", "")),
                        "Net Amount (USD)": float(match.group(6).replace(",", ""))
                    })

    return pd.DataFrame(rows)


if uploaded_file:
    st.success("PDF uploaded successfully")

    with st.spinner("Extracting line items..."):
        df = extract_line_items(uploaded_file)

    if df.empty:
        st.warning("No structured line items detected. PDF may be image-based or formatted differently.")
    else:
        st.subheader("📦 Extracted Line Items")
        st.dataframe(df, use_container_width=True)

        # Totals
        col1, col2 = st.columns(2)
        col1.metric("Total Net Amount", f"${df['Net Amount (USD)'].sum():,.2f}")
        col2.metric("Total Quantity", f"{df['Quantity'].sum():,.0f}")

        # Download
        st.download_button(
            "⬇️ Download CSV",
            df.to_csv(index=False),
            "po_line_items.csv",
            "text/csv"
        )

st.markdown("---")
st.caption("Supports FCA / Stellantis / Segula PO formats (text-based PDFs)")
