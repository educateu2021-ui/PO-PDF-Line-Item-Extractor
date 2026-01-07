import streamlit as st
import pandas as pd
import io

# App Title
st.set_page_config(page_title="PO Data Extractor", layout="wide")
st.title("📋 PO Item Extractor to Excel")
st.write("Upload your Purchase Order data to generate a downloadable Excel file.")

# 1. Data Input (Simulating the extraction from your specific PO)
# In a full app, you would integrate an OCR tool here to read the PDF.
data = [
    {
        "Item": 1,
        "Material": "72 Resources for EEHD Service",
        "Quantity": 1.000,
        "UOM": "LO",
        "Unit Price / Per / Currency": "986,878.04 / 1 / USD",
        "Effective Value": "986,878.04 USD",
        "Net Amount": "986,878.04 USD"
    },
    {
        "Item": 2,
        "Material": "Hardware cost",
        "Quantity": 1.000,
        "UOM": "LO",
        "Unit Price / Per / Currency": "43,205.40 / 1 / USD",
        "Effective Value": "43,205.40 USD",
        "Net Amount": "43,205.40 USD"
    }
]

# 2. Display the Table in the App
df = pd.DataFrame(data)
st.subheader("Extracted PO Line Items")
st.dataframe(df, use_container_width=True)

# 3. Excel Export Logic
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='PO_Items')
    return output.getvalue()

excel_data = to_excel(df)

# 4. Download Button
st.download_button(
    label="📥 Download as Excel",
    data=excel_data,
    file_name="PO_62128188_Items.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Metadata Sidebar
st.sidebar.header("Document Metadata")
st.sidebar.info(f"PO Number: 62128188\n\nBuyer: T5K\n\nVendor: SEGULA TECHNOLOGIES")
