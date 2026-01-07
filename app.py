import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re

st.set_page_config(page_title="Stellantis PO Extractor PRO", layout="wide")
st.title("📑 Stellantis PO AI Extractor")

uploaded_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf")

def parse_po_text(text):
    extracted_data = []
    
    # This pattern is specifically updated to find:
    # 1. Item number (1 or 2)
    # 2. Material code (999760010 or 999762209)
    # 3. Quantity (120.000)
    # 4. UOM (EA or DAY)
    # 5. Prices and Net Amounts
    pattern = r"(\d+)\s+(\d{7,10})\s+([\d,.]+)\s+(EA|DAY|LO|PC)\s+([\d,./]+)\s+([\d,.]+\s+USD)\s+([\d,.]+\s+USD)"
    
    # We clean the text by removing extra newlines that break the rows
    clean_text = re.sub(r'\n(?!\d+\s)', ' ', text)
    
    matches = re.findall(pattern, clean_text)
    for m in matches:
        extracted_data.append({
            "Item": m[0],
            "Material": m[1],
            "Quantity": m[2],
            "UOM": m[3],
            "Unit Price": m[4],
            "Effective Value": m[5],
            "Net Amount": m[6]
        })
    return extracted_data

if uploaded_file:
    with st.spinner("🔄 Converting PDF to Image & Running OCR..."):
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        full_text = ""
        for img in images:
            full_text += pytesseract.image_to_string(img)
        
        items = parse_po_text(full_text)
        
    if items:
        st.success(f"✅ Extracted {len(items)} items!")
        df = pd.DataFrame(items)
        st.dataframe(df, use_container_width=True)
        
        # Download Logic
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Download Excel File", output.getvalue(), "PO_Data.xlsx")
    else:
        st.error("No items found. Try viewing the raw text to see how the OCR is reading it.")
        with st.expander("View Raw OCR Text"):
            st.text(full_text)
