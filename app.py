import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO

st.set_page_config(
    page_title="STLA / FCA PO Layout Extractor",
    layout="wide"
)

st.title("📄 STLA / FCA PO Layout-Aware Extractor")
st.caption("Extract PO table using PDF layout (X/Y coordinates)")

uploaded_file = st.file_uploader(
    "Upload Purchase Order PDF",
    type=["pdf"]
)

# -------------------------------------------------
# Column X-coordinate ranges (tuned for STLA POs)
# -------------------------------------------------
COLUMNS = {
    "Item": (40, 80),
    "Material": (90, 170),
    "Quantity": (240, 300),
    "UOM": (305, 345),
    "Unit Price / Per / Currency": (350, 430),
    "Effective Value": (460, 540),
    "Net Amount": (560, 650),
}

def extract_po_table_layout(pdf_file):
    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                use_text_flow=True,
                keep_blank_chars=True
            )

            # Group words by row using Y position
            lines = {}
            for w in words:
                y = round(w["top"], 1)
                lines.setdefault(y, []).append(w)

            for y, line_words in lines.items():
                row = {
                    "Item": None,
                    "Material": None,
                    "Quantity": None,
                    "UOM": None,
                    "Unit Price / Per / Currency": None,
                    "Effective Value": None,
                    "Net Amount": None,
                }

                for w in line_words:
                    x = w["x0"]
                    text = w["text"].strip()

                    for col, (x_min, x_max) in COLUMNS.items():
                        if x_min <= x <= x_max:
                            if row[col] is None:
                                row[col] = text
                            else:
                                row[col] += " " + text

                # Row validation:
                # Quantity + Net Amount must exist to be a real PO row
                if row["Quantity"] and row["Net Amount"]:
                    rows.append(row)

    return pd.DataFrame(rows)


# -------------------------------------------------
# UI Logic
# -------------------------------------------------
if uploaded_file:
    with st.spinner("Extracting PO table using layout analysis..."):
        df = extract_po_table_layout(uploaded_file)

    if df.empty:
        st.error("No PO table rows detected. PDF layout may be unsupported.")
    else:
        st.subheader("📦 Extracted PO Table")
        st.dataframe(df, use_container_width=True)

        # Excel download
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="PO Table")

        st.download_button(
            "⬇️ Download Excel",
            data=output.getvalue(),
            file_name="stla_po_table.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")
st.caption("Layout-aware extraction • Stable for STLA / FCA POs")
