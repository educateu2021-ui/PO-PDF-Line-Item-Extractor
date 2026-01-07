import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
import zipfile
from PIL import Image

# Set Page Config
st.set_page_config(page_title="Stellantis PO AI Tool", layout="wide")
st.title("📑 Stellantis PO AI Master Tool")

def parse_po_text(text, filename):
    """
    Unified extraction logic for all Stellantis PO formats.
    Handles noisy OCR artifacts like ']' or '|'.
    """
    extracted_data = []
    # This pattern captures Item, Material, Quantity, UOM, and all Pricing fields
    pattern = r"[\]\s|]*(?P<item>\d+)?\s+(?P<material>.*?)\s+(?P<qty>[\d,.]+)\s+(?P<uom>LO|EA|DAY|PC|AU|UN)\s+(?P<price>[\d,./\s]+)\s+(?P<eff_val>[\d,.]+)\s+USD\s+(?P<net_amt>[\d,.]+)\s+USD"
    
    # Pre-processing to clean Stellantis table artifacts
    clean_text = text.replace('|', ' ').replace('_', ' ')
    
    # Process text page-by-page to ensure multi-page support
    matches = re.finditer(pattern, clean_text)
    for match in matches:
        extracted_data.append({
            "Source": filename,
            "Item": match.group("item") if match.group("item") else "N/A",
            "Material": match.group("material").strip(),
            "Quantity": match.group("qty"),
            "UOM": match.group("uom"),
            "Unit Price": match.group("price").strip() + " USD",
            "Effective Value": match.group("eff_val") + " USD",
            "Net Amount": match.group("net_amt") + " USD"
        })
    return extracted_data

# Tabs setup
tab1, tab2, tab3 = st.tabs(["📄 PDF Scan (Multi-Page)", "🖼️ Bulk Image Scan", "📷 PDF to Image Converter"])

# --- TAB 1: PDF SCAN ---
with tab1:
    pdf_files = st.file_uploader("Upload Stellantis PDFs", type="pdf", accept_multiple_files=True, key="pdf_main")
    if pdf_files:
        all_pdf_items = []
        for pdf in pdf_files:
            with st.spinner(f"Converting and Scanning {pdf.name}..."):
                # Convert all pages (solves the 2/4 page issue)
                images = pdf2image.convert_from_bytes(pdf.read(), dpi=300)
                for i, img in enumerate(images):
                    page_text = pytesseract.image_to_string(img)
                    all_pdf_items.extend(parse_po_text(page_text, f"{pdf.name} (Pg {i+1})"))
        
        if all_pdf_items:
            df_pdf = pd.DataFrame(all_pdf_items)
            st.dataframe(df_pdf, use_container_width=True)
            
            # Excel export with XlsxWriter
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_pdf.to_excel(writer, index=False)
                st.download_button("📥 Download PDF Extraction", output.getvalue(), "PO_Full_Extract.xlsx")
            except ModuleNotFoundError:
                st.error("Error: 'xlsxwriter' not found. Ensure it is in your requirements.txt")

# --- TAB 2: IMAGE SCAN ---
with tab2:
    img_files = st.file_uploader("Upload PO Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="img_main")
    if img_files:
        all_img_items = []
        for img in img_files:
            input_img = Image.open(img)
            img_text = pytesseract.image_to_string(input_img)
            all_img_items.extend(parse_po_text(img_text, img.name))
        
        if all_img_items:
            df_img = pd.DataFrame(all_img_items)
            st.dataframe(df_img, use_container_width=True)

# --- TAB 3: CONVERTER ---
with tab3:
    st.header("PDF to Image Converter")
    convert_pdf = st.file_uploader("Upload PDF to save as Images", type="pdf", key="pdf_conv")
    if convert_pdf:
        images = pdf2image.convert_from_bytes(convert_pdf.read(), dpi=300)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, img in enumerate(images):
                st.image(img, caption=f"Page {i+1}", use_container_width=True)
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                zip_file.writestr(f"page_{i+1}.png", img_byte_arr.getvalue())
        
        st.download_button("📥 Download All Pages as ZIP", zip_buffer.getvalue(), f"{convert_pdf.name}_images.zip")
