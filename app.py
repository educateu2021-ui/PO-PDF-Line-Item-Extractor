import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
from PIL import Image

st.set_page_config(page_title="Stellantis PO Bulk Extractor", layout="wide")
st.title("📑 Stellantis PO Multi-Page Extractor")

def parse_po_text(text, filename):
    extracted_data = []
    # This pattern captures Item, Material, Quantity, UOM, and all Price fields
    pattern = r"[\]\s]*(?P<item>\d+)?\s+(?P<material>.*?)\s+(?P<qty>[\d,.]+)\s+(?P<uom>LO|EA|DAY|PC|AU)\s+(?P<price>[\d,./\s]+)\s+(?P<eff_val>[\d,.]+)\s+USD\s+(?P<net_amt>[\d,.]+)\s+USD"
    
    # Clean OCR noise like vertical bars or underscores found in Stellantis headers
    clean_text = text.replace('|', ' ').replace('_', ' ')
    
    # Use finditer to ensure we get EVERY match on EVERY page
    matches = re.finditer(pattern, clean_text)
    
    for match in matches:
        extracted_data.append({
            "Source File": filename,
            "Item": match.group("item") if match.group("item") else "N/A",
            "Material": match.group("material").strip(),
            "Quantity": match.group("qty"),
            "UOM": match.group("uom"),
            "Unit Price": match.group("price").strip() + " USD",
            "Effective Value": match.group("eff_val") + " USD",
            "Net Amount": match.group("net_amt") + " USD"
        })
    return extracted_data

# Tabs to organize the features
tab1, tab2 = st.tabs(["📄 PDF Scan (Multi-Page)", "🖼️ Image Scan"])

with tab1:
    pdf_files = st.file_uploader("Upload Stellantis PDFs", type="pdf", accept_multiple_files=True)
    if pdf_files:
        all_items = []
        for pdf in pdf_files:
            with st.spinner(f"Processing all pages of {pdf.name}..."):
                # Convert ALL pages to images (300 DPI for accuracy)
                images = pdf2image.convert_from_bytes(pdf.read(), dpi=300)
                
                # Scan every single page found in the PDF
                for i, img in enumerate(images):
                    page_text = pytesseract.image_to_string(img)
                    # Extract items from this specific page and add to master list
                    page_items = parse_po_text(page_text, f"{pdf.name} (Pg {i+1})")
                    all_items.extend(page_items)
        
        if all_items:
            df = pd.DataFrame(all_items)
            st.success(f"Extracted {len(df)} items from total PDF pages.")
            st.dataframe(df, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), "PDF_Full_Extract.xlsx")

with tab2:
    img_files = st.file_uploader("Upload PO Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if img_files:
        all_img_items = []
        for img_file in img_files:
            input_image = Image.open(img_file)
            img_text = pytesseract.image_to_string(input_image)
            all_img_items.extend(parse_po_text(img_text, img_file.name))
        
        if all_img_items:
            df_img = pd.DataFrame(all_img_items)
            st.dataframe(df_img, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_img.to_excel(writer, index=False)
            st.download_button("📥 Download Image Data", output.getvalue(), "Image_Extract.xlsx")
