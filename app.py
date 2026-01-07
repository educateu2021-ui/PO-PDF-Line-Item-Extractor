import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re

# Set Page Config
st.set_page_config(page_title="Stellantis PO Detail Extractor", layout="wide")
st.title("📊 Complete PO Detail Extractor")
st.markdown("This app converts PDF pages to images first to ensure the most accurate data extraction from complex PO tables.")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf")

def parse_po_text(text):
    """
    Logic remains unchanged but enhanced to handle OCR noise:
    Captures: Item, Material, Quantity, UOM, Unit Price, Effective Value, Net Amount.
    """
    extracted_data = []
    
    # Regex Pattern designed for Stellantis table headers[cite: 7, 49, 74, 124, 140]:
    # 1. (\d+) -> Item Number
    # 2. (.*?) -> Material (Part numbers or text)
    # 3. ([\d,.]+) -> Quantity
    # 4. ([A-Z/|_\s]{2,5}) -> UOM (EA, LO, DAY, etc.)
    # 5. ([\d,./\s]+) -> Unit Price / Per / Currency
    # 6. ([\d,.]+\s*USD) -> Effective Value
    # 7. ([\d,.]+\s*USD) -> Net Amount
    pattern = r"(\d+)\s+(.*?)\s+([\d,.]+)\s+([A-Z/|_\s]{2,5})\s+([\d,./\s]+)\s+([\d,.]+\s*USD)\s+([\d,.]+\s*USD)"
    
    # Pre-process text to remove common OCR "noise" characters like | or _ that break rows
    clean_text = text.replace('|', ' ').replace('_', ' ')
    # Join multi-line descriptions into a single line for regex matching
    clean_text = re.sub(r'\n(?!\d+\s)', ' ', clean_text)
    
    matches = re.finditer(pattern, clean_text)
    for match in matches:
        extracted_data.append({
            "Item": match.group(1),
            "Material": match.group(2).strip(),
            "Quantity": match.group(3),
            "UOM": match.group(4).strip(),
            "Unit Price / Per / Currency": match.group(5).strip(),
            "Effective Value": match.group(6).strip(),
            "Net Amount": match.group(7).strip()
        })
    return extracted_data

if uploaded_file:
    with st.spinner("🔄 STEP 1: Converting PDF to Image..."):
        # Convert PDF to high-quality images (300 DPI)
        images = pdf2image.convert_from_bytes(uploaded_file.read(), dpi=300)
        
    with st.spinner("🔄 STEP 2: Scanning Image for Text (OCR)..."):
        full_document_text = ""
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img)
            full_document_text += f"\n--- Page {i+1} ---\n{page_text}"
            
    # Process the extracted text
    items = parse_po_text(full_document_text)
        
    if items:
        st.success(f"✅ Extracted {len(items)} items across all pages!")
        df = pd.DataFrame(items)
        
        # Display Table
        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True)
        
        # Excel Export Logic using xlsxwriter
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PO_Items')
            
        st.download_button(
            label="📥 Download Excel File",
            data=output.getvalue(),
            file_name=f"Extracted_{uploaded_file.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Could not find line items. The OCR might have misread the headers.")
        with st.expander("Show Raw OCR Text"):
            st.text(full_document_text)
