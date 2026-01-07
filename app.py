import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(
    page_title="STLA / FCA PO Table Extractor",
    layout="wide"
)

st.title("📄 STLA / FCA PO Table Extractor")
st.caption("Upload PO PDF → Extract PO table → Download Excel")

uploaded_file = st.file_uploader(
    "Upload Purchase Order PDF",
    type=["pdf"]
)

# ---------------------------
# Core extractor
# ---------------------------
def extract_po_table(pdf_file):
    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = [l.strip() for l in text.split("\n") if l.strip()]

            for i, line in enumerate(lines):

                # -----------------------------
                # Quantity + UOM + Unit Price
                # Example: 120.000 EA 525.48/1/ USD
                # -----------------------------
                qty_match = re.search(
                    r"(\d+(?:\.\d+)?)\s+(EA|DAY|LO|UN)\s+([\d,]+\.\d+/1/\s+USD)",
                    line
                )

                if not qty_match:
                    continue

                quantity = float(qty_match.group(1))
                uom = qty_match.group(2)
                unit_price = qty_match.group(3)

                # -----------------------------
                # Effective Value + Net Amount
                # Usually next line
                # -----------------------------
                eff_value = net_amount = None
                if i + 1 < len(lines):
                    val_match = re.search(
                        r"([\d,]+\.\d+)\s+USD\s+([\d,]+\.\d+)\s+USD",
                        lines[i + 1]
                    )
                    if val_match:
                        eff_value = val_match.group(1) + " USD"
                        net_amount = val_match.group(2) + " USD"

                # -----------------------------
                # Walk backwards to find Item & Material
                # -----------------------------
                item = material = None
                for j in range(i - 1, max(i - 8, -1), -1):
                    back = lines[j]

                    # Item + numeric material
                    im = re.match(r"^(\d+)\s+(\d{6,})", back)
                    if im:
                        item = im.group(1)
                        material = im.group(2)
                        break

                    # Item only
                    im2 = re.match(r"^(\d+)\s+", back)
                    if im2 and item is None:
                        item = im2.group(1)

                rows.append({
                    "Item": item,
                    "Material": material,
                    "Quantity": quantity,
                    "UOM": uom,
                    "Unit Price / Per / Currency": unit_price,
                    "Effective Value": eff_value,
                    "Net Amount": net_amount
                })

    return pd.DataFrame(rows)


# ---------------------------
# UI logic
# ---------------------------
if uploaded_file:
    with st.spinner("Extracting PO table..."):
        df = extract_po_table(uploaded_file)

    if df.empty:
        st.error("No PO table rows detected in this PDF.")
    else:
        st.subheader("📦 Extracted PO Table")
        st.dataframe(df, use_container_width=True)

        # Excel download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="PO Table")

        st.download_button(
            label="⬇️ Download Excel",
            data=output.getvalue(),
            file_name="stla_po_table.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")
st.caption("Built specifically for STLA / FCA Purchase Order tables")
