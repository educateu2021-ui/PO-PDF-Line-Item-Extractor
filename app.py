import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
from PIL import Image

st.set_page_config(page_title="Stellantis PO AI Extractor", layout="wide")
st.title("👁️ Stellantis PO Bulk AI Extractor")

def parse_po_text(text, filename):
    """
    Robust parsing logic for Stellantis POs.
    """
    extracted_data = []
    # Pattern designed to handle OCR artifacts and varying headers
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
            "Unit Price / Per / Currency": match.group("price").strip() + " USD",
            "Effective Value": match.group("eff_val") + " USD",
            "Net Amount": match.group("net_amt") + " USD"
        })
    return extracted_data

tab1, tab2 = st.tabs(["📄 PDF Bulk Upload", "🖼️ Image Bulk Upload"])

# --- TAB 1: PDF BULK ---
with tab1:
    pdf_files = st.file_uploader("Upload Stellantis PO PDFs", type="pdf", accept_multiple_files=True, key="pdf_bulk")
    if pdf_files:
        all_pdf_items = []
        for pdf_file in pdf_files:
            with st.spinner(f"Processing PDF: {pdf_file.name}"):
                images = pdf2image.convert_from_bytes(pdf_file.read(), dpi=300)
                pdf_text = ""
                for img in images:
                    pdf_text += pytesseract.image_to_string(img)
                all_pdf_items.extend(parse_po_text(pdf_text, pdf_file.name))
        
        if all_pdf_items:
            df_pdf = pd.DataFrame(all_pdf_items)
            st.success(f"Extracted {len(df_pdf)} total items from {len(pdf_files)} PDFs.")
            st.dataframe(df_pdf, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_pdf.to_excel(writer, index=False)
            st.download_button("📥 Download Combined PDF Data", output.getvalue(), "Bulk_PDF_Extract.xlsx")

# --- TAB 2: IMAGE BULK ---
with tab2:
    img_files = st.file_uploader("Upload PO Images (JPG/PNG)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="img_bulk")
    if img_files:
        all_img_items = []
        for img_file in img_files:
            with st.spinner(f"Processing Image: {img_file.name}"):
                input_image = Image.open(img_file)
                img_text = pytesseract.image_to_string(input_image)
                all_img_items.extend(parse_po_text(img_text, img_file.name))
        
        if all_img_items:
            df_img = pd.DataFrame(all_img_items)
            st.success(f"Extracted {len(df_img)} total items from {len(img_files)} images.")
            st.dataframe(df_img, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_img.to_excel(writer, index=False)
            st.download_button("📥 Download Combined Image Data", output.getvalue(), "Bulk_Image_Extract.xlsx")
        else:
            st.error("No line items detected in uploaded images.")
