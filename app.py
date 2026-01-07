import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
from PIL import Image

# Function remains the same as it is proven to work in your image scan
def parse_po_text(text, filename):
    extracted_data = []
    # Pattern to handle the data in your POs (EEHD, CAE CFD, HV Validation)
    pattern = r"[\]\s]*(?P<item>\d+)?\s+(?P<material>.*?)\s+(?P<qty>[\d,.]+)\s+(?P<uom>LO|EA|DAY|PC|AU)\s+(?P<price>[\d,./\s]+)\s+(?P<eff_val>[\d,.]+)\s+USD\s+(?P<net_amt>[\d,.]+)\s+USD"
    
    clean_text = text.replace('|', ' ').replace('_', ' ')
    matches = re.finditer(pattern, clean_text)
    
    for match in matches:
        extracted_data.append({
            "Source File": filename,
            "Item": match.group("item") if match.group("item") else "1",
            "Material": match.group("material").strip(),
            "Quantity": match.group("qty"),
            "UOM": match.group("uom"),
            "Unit Price": match.group("price").strip() + " USD",
            "Effective Value": match.group("eff_val") + " USD",
            "Net Amount": match.group("net_amt") + " USD"
        })
    return extracted_data

st.title("📑 Stellantis PO Bulk Extractor")
tab1, tab2 = st.tabs(["📄 PDF Bulk Scan", "🖼️ Image Bulk Scan"])

with tab1:
    pdf_files = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    if pdf_files:
        all_items = []
        for pdf in pdf_files:
            try:
                # This line requires 'poppler-utils' in packages.txt
                images = pdf2image.convert_from_bytes(pdf.read(), dpi=300)
                pdf_text = ""
                for img in images:
                    pdf_text += pytesseract.image_to_string(img)
                all_items.extend(parse_po_text(pdf_text, pdf.name))
            except Exception as e:
                st.error(f"Error processing {pdf.name}: {e}")
        
        if all_items:
            df = pd.DataFrame(all_items)
            st.dataframe(df)
            # Excel download logic...
