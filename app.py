import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re

# Set Page Config
st.set_page_config(page_title="Stellantis PO Multi-Table Extractor", layout="wide")
st.title("📊 Complete PO Detail Extractor")

uploaded_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf")

def extract_all_items(text):
    """
    Captures all details: Item, Material, Quantity, UOM, Unit Price, Effective Value, Net Amount.
    Supports varying UOMs (EA, LO, DAY, PC, etc.) and alphanumeric materials.
    """
    items = []
    
    # This regex is built to match the headers you specified:
    # 1. (\d+) -> Item
    # 2. (.*?) -> Material (captures codes and text)
    # 3. ([\d,.]+) -> Quantity
    # 4. (\w{2,4}) -> UOM (Matches EA, DAY, LO, etc.)
    # 5. ([\d,./]+) -> Unit Price / Per
    # 6. ([\d,.]+\s*USD) -> Effective Value
    # 7. ([\d,.]+\s*USD) -> Net Amount
    
    pattern = r"(\d+)\s+(.*?)\s+([\d,.]+)\s+([A-Z]{2,4})\s+([\d,./]+)\s+([\d,.]+\s+USD)\s+([\d,.]+\s+USD)"
    
    # Pre-process text to bring multi-line materials into a single line for the regex
    # Stellantis POs often put the Material description on a new line; this joins them.
    text_clean = re.sub(r'\n(?!\d+\s)', ' ', text)
    
    matches = re.finditer(pattern, text_clean)
    
    for match in matches:
        items.append({
            "Item": match.group(1),
            "Material": match.group(2).strip(),
            "Quantity": match.group(3),
            "UOM": match.group(4),
            "Unit Price / Per / Currency": match.group(5),
            "Effective Value": match.group(6),
            "Net Amount": match.group(7)
        })
    return items

if uploaded_file:
    with st.spinner("🔍 Scanning all pages for table data..."):
        # Convert PDF to Image (High DPI for better OCR accuracy)
        images = pdf2image.convert_from_bytes(uploaded_file.read(), dpi=300)
        
        full_document_text = ""
        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img)
            full_document_text += f"\n{page_text}"
            
        # Run the extraction logic
        all_extracted_items = extract_all_items(full_document_text)
        
    if all_extracted_items:
        st.success(f"✅ Found {len(all_extracted_items)} items across all tables.")
        df = pd.DataFrame(all_extracted_items)
        
        # Display the data
        st.subheader("Extracted Details")
        st.dataframe(df, use_container_width=True)
        
        # Export to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PO_Details')
            
        st.download_button(
            label="📥 Download All Details as Excel",
            data=output.getvalue(),
            file_name=f"Full_Extraction_{uploaded_file.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Could not find line items. Check 'Raw OCR' to see if the table headers were read correctly.")
        with st.expander("Show Raw OCR Text"):
            st.text(full_document_text)
