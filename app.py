import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re

st.set_page_config(page_title="Stellantis PO Detail Extractor", layout="wide")
st.title("📊 Complete PO Detail Extractor")

uploaded_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf")

def parse_po_text(text):
    extracted_data = []
    
    # IMPROVED REGEX:
    # 1. (?P<item>\d+)? -> Optional Item number
    # 2. (?P<material>999\d+) -> Material starting with 999
    # 3. (?P<qty>[\d,.]+) -> Quantity
    # 4. (?P<uom>EA|LO|DAY|PC|AU) -> UOM
    # 5. (?P<price>[\d,./]+) -> Price/Per
    # 6. (?P<eff_val>[\d,.]+) -> Effective Value
    # 7. (?P<net_amt>[\d,.]+) -> Net Amount
    
    pattern = r"(?P<item>\d+)?\s+(?P<material>999\d+)\s+(?P<qty>[\d,.]+)\s+(?P<uom>EA|LO|DAY|PC|AU)\s+(?P<price>[\d,./]+)\s+(?P<eff_val>[\d,.]+)\s+USD\s+(?P<net_amt>[\d,.]+)\s+USD"
    
    # Clean OCR noise and join lines
    clean_text = text.replace('|', ' ').replace('_', ' ')
    
    matches = re.finditer(pattern, clean_text)
    for match in matches:
        extracted_data.append({
            "Item": match.group("item") if match.group("item") else "1", # Default to 1 if missing
            "Material": match.group("material"),
            "Quantity": match.group("qty"),
            "UOM": match.group("uom"),
            "Unit Price / Per / Currency": match.group("price") + " USD",
            "Effective Value": match.group("eff_val") + " USD",
            "Net Amount": match.group("net_amt") + " USD"
        })
    return extracted_data

if uploaded_file:
    with st.spinner("🔄 Step 1: Converting to Image..."):
        images = pdf2image.convert_from_bytes(uploaded_file.read(), dpi=300)
        
    with st.spinner("🔄 Step 2: Scanning Text..."):
        full_text = ""
        for img in images:
            full_text += pytesseract.image_to_string(img)
            
    items = parse_po_text(full_text)
        
    if items:
        st.success(f"✅ Extracted {len(items)} items!")
        df = pd.DataFrame(items)
        st.dataframe(df, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 Download Excel File", output.getvalue(), "PO_Extraction.xlsx")
    else:
        st.error("Still no data found. The Regex pattern is not matching the text.")
        with st.expander("Review Raw Text vs Pattern"):
            st.write("Pattern looking for: Item(opt) + 999... + Qty + UOM + Price + USD")
            st.text(full_text)
