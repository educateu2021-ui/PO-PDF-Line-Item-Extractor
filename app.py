import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
from PIL import Image

st.set_page_config(page_title="Stellantis PO AI Extractor", layout="wide")
st.title("👁️ Stellantis PO AI Detail Extractor")

# Define the Extraction Logic
def parse_po_text(text):
    """
    Robust parsing logic for Stellantis POs.
    Handles optional item numbers and varying UOMs.
    """
    extracted_data = []
    # Pattern looks for: Optional Item, Material (starts 999), Qty, UOM, Price, Value, Net Amount
    pattern = r"(?P<item>\d+)?\s+(?P<material>999\d+)\s+(?P<qty>[\d,.]+)\s+(?P<uom>EA|LO|DAY|PC|AU)\s+(?P<price>[\d,./]+)\s+(?P<eff_val>[\d,.]+)\s+USD\s+(?P<net_amt>[\d,.]+)\s+USD"
    
    clean_text = text.replace('|', ' ').replace('_', ' ')
    matches = re.finditer(pattern, clean_text)
    
    for match in matches:
        extracted_data.append({
            "Item": match.group("item") if match.group("item") else "1",
            "Material": match.group("material"),
            "Quantity": match.group("qty"),
            "UOM": match.group("uom"),
            "Unit Price": match.group("price") + " USD",
            "Effective Value": match.group("eff_val") + " USD",
            "Net Amount": match.group("net_amt") + " USD"
        })
    return extracted_data

# Create Tabs for PDF and Image
tab1, tab2 = st.tabs(["📄 PDF Upload", "🖼️ Image Upload"])

# --- TAB 1: PDF PROCESSING ---
with tab1:
    pdf_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf", key="pdf_up")
    if pdf_file:
        with st.spinner("Converting PDF pages to images..."):
            # Convert PDF to high-quality images (300 DPI)
            images = pdf2image.convert_from_bytes(pdf_file.read(), dpi=300)
            full_text = ""
            for img in images:
                full_text += pytesseract.image_to_string(img)
            
            items = parse_po_text(full_text)
            if items:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Download Excel", output.getvalue(), f"PDF_Extract_{pdf_file.name}.xlsx")
            else:
                st.error("No data found in PDF. Check raw text below.")
                with st.expander("Show Raw OCR Text"):
                    st.text(full_text)

# --- TAB 2: IMAGE PROCESSING ---
with tab2:
    img_file = st.file_uploader("Upload PO Image (JPG/PNG)", type=["jpg", "jpeg", "png"], key="img_up")
    if img_file:
        # Open the uploaded image
        input_image = Image.open(img_file)
        st.image(input_image, caption="Uploaded PO Image", width=400)
        
        with st.spinner("Extracting text from image..."):
            img_text = pytesseract.image_to_string(input_image)
            items = parse_po_text(img_text)
            
            if items:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False)
                st.download_button("📥 Download Excel", output.getvalue(), f"Image_Extract_{img_file.name}.xlsx")
            else:
                st.error("No line items detected in this image.")
                with st.expander("Show Raw OCR Text"):
                    st.text(img_text)
