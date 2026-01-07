import streamlit as st
import pandas as pd
import pdfplumber
import io
import re

st.set_page_config(page_title="Stellantis PO Extractor", layout="wide")
st.title("📄 Multi-PDF PO Extractor")
st.write("Upload your Purchase Order PDFs (e.g., PO 62128188) to extract item details into Excel.")

# 1. File Uploader for multiple PDFs
uploaded_files = st.file_uploader("Choose PO PDF files", type="pdf", accept_multiple_files=True)

def extract_po_data(pdf_file):
    items_list = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Look for tables with the specific headers found in the PO
                if any("Material" in str(cell) for cell in table[0]):
                    for row in table[1:]:
                        if len(row) >= 7 and row[0]: # Ensure it's an item row
                            items_list.append({
                                "PO Number": pdf_file.name.split(' ')[0], # Extracts ID from filename
                                "Item": row[0],
                                "Material": row[1].replace('\n', ' '),
                                "Quantity": row[2],
                                "UOM": row[3],
                                "Unit Price": row[4].replace('\n', ''),
                                "Effective Value": row[5],
                                "Net Amount": row[6]
                            })
    return items_list

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            file_data = extract_po_data(uploaded_file)
            all_data.extend(file_data)
    
    if all_data:
        df = pd.DataFrame(all_data)
        st.success(f"Successfully extracted {len(df)} items from {len(uploaded_files)} files.")
        
        # Display Preview
        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True)

        # 2. Excel Export Logic
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Extracted_PO_Items')
        
        st.download_button(
            label="📥 Download Consolidated Excel",
            data=output.getvalue(),
            file_name="Consolidated_PO_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("No item data found. Please ensure the PDF format matches the Stellantis PO structure.")

# Update Requirements for Streamlit Cloud
# Add 'pdfplumber' to your requirements.txt file
