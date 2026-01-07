import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
from PIL import Image

st.set_page_config(page_title="Stellantis PO AI Extractor", layout="wide")
st.title("👁️ Stellantis PO AI Detail Extractor")

def parse_po_text(text):
    extracted_data = []
    # UPDATED REGEX:
    # 1. [\]\s]*(\d+)? -> Handles potential OCR noise like ']' before the item number
    # 2. (?P<material>.*?) -> Captures the Material description/code
    # 3. (?P<qty>[\d,.]+) -> Quantity (e.g., 1.000)
    # 4. (?P<uom>LO|EA|DAY|PC|AU) -> UOM [cite: 7, 49, 74, 124]
    # 5. (?P<price>[\d,./\s]+) -> Unit Price [cite: 7, 49, 124]
    # 6. (?P<eff_val>[\d,.]+) -> Effective Value [cite: 7, 49, 74]
    # 7. (?P<net_amt>[\d,.]+) -> Net Amount [cite: 7, 49, 124]
    
    pattern = r"[\]\s]*(?P<item>\d+)?\s+(?P<material>.*?)\s+(?P<qty>[\d,.]+)\s+(?P<uom>LO|EA|DAY|PC|AU)\s+(?P<price>[\d,./\s]+)\s+(?P<eff_val>[\d,.]+)\s+USD\s+(?P<net_amt>[\d,.]+)\s+USD"
    
    # Cleaning noise characters from OCR output
    clean_text = text.replace('|', ' ').replace('_', ' ')
    
    matches = re.finditer(pattern, clean_text)
    for match in matches:
        extracted_data.append({
            "Item": match.group("item") if match.group("item") else "1",
            "Material": match.group("material").strip(),
            "Quantity": match.group("qty"),
            "UOM": match.group("uom"),
            "Unit Price / Per / Currency": match.group("price").strip() + " USD",
            "Effective Value": match.group("eff_val") + " USD",
            "Net Amount": match.group("net_amt") + " USD"
        })
    return extracted_data

tab1, tab2 = st.tabs(["📄 PDF to Image Scan", "🖼️ Direct Image Scan"])

with tab1:
    pdf_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf", key="pdf")
    if pdf_file:
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
            st.download_button("📥 Download Excel", output.getvalue(), "PO_Extract.xlsx")
        else:
            st.error("No items found. Check Raw Output.")
            with st.expander("Show Raw OCR Text"):
                st.text(full_text)

with tab2:
    img_file = st.file_uploader("Upload PO Image", type=["jpg", "png", "jpeg"], key="img")
    if img_file:
        input_image = Image.open(img_file)
        st.image(input_image, width=500)
        img_text = pytesseract.image_to_string(input_image)
        items = parse_po_text(img_text)
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", output.getvalue(), "Image_Extract.xlsx")
        else:
            st.error("No line items detected.")
            with st.expander("Show Raw OCR Text"):
                st.text(img_text)
