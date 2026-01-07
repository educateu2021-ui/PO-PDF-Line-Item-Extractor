import streamlit as st
import pandas as pd
import numpy as np
from pdf2image import convert_from_bytes
import pytesseract
import io
import re

st.set_page_config(page_title="Stellantis PO OCR Extractor", layout="wide")
st.title("👁️ PO OCR Image Extractor")
st.write("This version converts PDFs to images to 'read' hard-to-parse documents.")

uploaded_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf")

def perform_ocr_extraction(pdf_bytes):
    # Convert PDF pages to images
    images = convert_from_bytes(pdf_bytes)
    all_extracted_text = ""
    
    for i, image in enumerate(images):
        # Perform OCR on each page
        page_text = pytesseract.image_to_string(image)
        all_extracted_text += f"\n--- Page {i+1} ---\n" + page_text
    
    return all_extracted_text

def parse_text_to_table(text):
    # Regex designed for Item 1 and Item 2 in your document 
    # Looks for: [Item #] [Description] [Quantity] [UOM] [Price]
    pattern = r"(\d+)\s+([\w\s/]+)\s+([\d,.]+)\s+(LO)\s+([\d,.]+)"
    matches = re.findall(pattern, text)
    
    results = []
    for m in matches:
        results.append({
            "Item": m[0],
            "Material": m[1].strip(),
            "Quantity": m[2],
            "UOM": m[3],
            "Unit Price": m[4],
            "Net Amount": m[4]
        })
    return results

if uploaded_file:
    with st.spinner("Converting PDF to Image and running OCR..."):
        pdf_bytes = uploaded_file.read()
        raw_text = perform_ocr_extraction(pdf_bytes)
        items = parse_text_to_table(raw_text)
        
    if items:
        df = pd.DataFrame(items)
        st.success("Data Extracted Successfully!")
        st.dataframe(df, use_container_width=True)
        
        # Download Logic
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button("📥 Download Excel", output.getvalue(), "PO_OCR_Data.xlsx")
    else:
        st.error("Could not find line items in the image text.")
        with st.expander("Show Raw OCR Text"):
            st.text(raw_text)
