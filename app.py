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

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split("\n")

            for i, line in enumerate(lines):
                line = line.strip()

                # ------------------------------------
                # 1️⃣ Quantity + UOM + Unit Price
                # ------------------------------------
                qty_match = re.search(
                    r"(\d+(?:\.\d+)?)\s+(EA|DAY|LO|UN)\s+([\d,]+\.\d+/1/\s+USD)",
                    line
                )
                if not qty_match:
                    continue

                quantity = float(qty_match.group(1))
                uom = qty_match.group(2)
                unit_price = qty_match.group(3)

                # ------------------------------------
                # 2️⃣ Effective Value + Net Amount (next line)
                # ------------------------------------
                eff_val = net_amt = None
                if i + 1 < len(lines):
                    val_match = re.search(
                        r"([\d,]+\.\d+)\s+USD\s+([\d,]+\.\d+)\s+USD",
                        lines[i + 1]
                    )
                    if val_match:
                        eff_val = float(val_match.group(1).replace(",", ""))
                        net_amt = float(val_match.group(2).replace(",", ""))

                # ------------------------------------
                # 3️⃣ Walk backwards to find Item & Material
                # ------------------------------------
                item = material = None
                for j in range(i - 1, max(i - 6, -1), -1):
                    back_line = lines[j].strip()

                    # Item + numeric material
                    im = re.match(r"^(\d+)\s+(\d{6,})", back_line)
                    if im:
                        item = im.group(1)
                        material = im.group(2)
                        break

                    # Item only (no material)
                    im2 = re.match(r"^(\d+)\s+", back_line)
                    if im2 and item is None:
                        item = im2.group(1)

                rows.append({
                    "Item": item,
                    "Material": material,
                    "Quantity": quantity,
                    "UOM": uom,
                    "Unit Price / Per / Currency": unit_price,
                    "Effective Value": eff_val,
                    "Net Amount": net_amt,
                })

    return pd.DataFrame(rows)


if uploaded_file:
    with st.spinner("Extracting PO table rows..."):
        df = extract_po_table(uploaded_file)

    if df.empty:
        st.error("No PO table rows detected. PDF format may be unsupported.")
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
