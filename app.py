import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
import zipfile
from PIL import Image

st.set_page_config(page_title="Stellantis PO Tool", layout="wide")
st.title("📑 Stellantis PO AI Tool")

def parse_po_text(text, filename):
    extracted_data = []
    # Pattern to capture Item, Material, Quantity, UOM, and Price fields [cite: 7, 49, 74]
    pattern = r"[\]\s]*(?P<item>\d+)?\s+(?P<material>.*?)\s+(?P<qty>[\d,.]+)\s+(?P<uom>LO|EA|DAY|PC|AU)\s+(?P<price>[\d,./\s]+)\s+(?P<eff_val>[\d,.]+)\s+USD\s+(?P<net_amt>[\d,.]+)\s+USD"
    
    clean_text = text.replace('|', ' ').replace('_', ' ')
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

# Create three tabs
tab1, tab2, tab3 = st.tabs(["📄 PDF Scan", "🖼️ Image Scan", "📷 PDF to Image Converter"])

# --- TAB 1 & 2: SCANNING LOGIC ---
with tab1:
    pdf_files = st.file_uploader("Upload PDFs for Data Extraction", type="pdf", accept_multiple_files=True, key="scan_pdf")
    if pdf_files:
        all_items = []
        for pdf in pdf_files:
            images = pdf2image.convert_from_bytes(pdf.read(), dpi=300)
            for i, img in enumerate(images):
                page_text = pytesseract.image_to_string(img)
                all_items.extend(parse_po_text(page_text, f"{pdf.name} (Pg {i+1})"))
        if all_items:
            df = pd.DataFrame(all_items)
            st.dataframe(df, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), "PO_Data.xlsx")

with tab2:
    img_files = st.file_uploader("Upload Images for Data Extraction", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="scan_img")
    if img_files:
        all_img_items = []
        for img_file in img_files:
            input_image = Image.open(img_file)
            img_text = pytesseract.image_to_string(input_image)
            all_img_items.extend(parse_po_text(img_text, img_file.name))
        if all_img_items:
            df_img = pd.DataFrame(all_img_items)
            st.dataframe(df_img, use_container_width=True)

# --- TAB 3: PDF TO IMAGE CONVERTER ---
with tab3:
    st.header("Convert PDF Pages to Image Files")
    convert_pdf = st.file_uploader("Upload PDF to convert", type="pdf", key="convert_pdf")
    
    if convert_pdf:
        with st.spinner("Converting pages..."):
            images = pdf2image.convert_from_bytes(convert_pdf.read(), dpi=300)
            
            # Use a ZIP file to allow downloading all pages at once
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for i, img in enumerate(images):
                    # Show preview in app
                    st.image(img, caption=f"Page {i+1}", use_container_width=True)
                    
                    # Convert PIL image to bytes for the ZIP
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    zip_file.writestr(f"page_{i+1}.png", img_byte_arr.getvalue())
            
            st.download_button(
                label="📥 Download All Pages as ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"{convert_pdf.name}_images.zip",
                mime="application/zip"
            )
