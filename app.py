import streamlit as st
import pandas as pd
import pdf2image
import pytesseract
import io
import re
import xlsxwriter

st.set_page_config(page_title="Stellantis PO Extractor PRO", layout="wide")

st.title("📑 Stellantis PO AI Extractor")
st.markdown("""
This app uses **OCR** to read PO images and **Regex** to structure the data. 
It supports multiple Unit of Measures (EA, LO) and alphanumeric Material codes.
""")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload Stellantis PO PDF", type="pdf")

def parse_po_text(text):
    """
    Advanced regex to capture Stellantis PO line items:
    - Item Number
    - Material (including part numbers or descriptions)
    - Quantity
    - UOM (EA, LO, PC, etc.)
    - Unit Price / Currency / Net Amount
    """
    extracted_data = []
    
    # Updated pattern to handle: Item, Material (greedy), Qty, UOM, and Price/USD
    # Example: 1 1999761892 120.000 EA 100.00/1/ 12,000.00 USD
    pattern = r"(\d+)\s+(.*?)\s+([\d,.]+)\s+(EA|LO|PC|AU|UN)\s+([\d,./\s]+USD)"
    
    lines = text.split('\n')
    for line in lines:
        match = re.search(pattern, line)
        if match:
            # Clean up Material: Remove trailing noise or dates
            material = match.group(2).strip()
            material = re.split(r'Delivery date:', material)[0].strip()
            
            # Extract the final Net Amount from the price string
            price_string = match.group(5).strip()
            net_amount = price_string.split()[-2] if "USD" in price_string else price_string

            extracted_data.append({
                "Item": match.group(1),
                "Material": material,
                "Quantity": match.group(3),
                "UOM": match.group(4),
                "Unit Price / Per / Currency": price_string,
                "Net Amount": net_amount
            })
    return extracted_data

if uploaded_file:
    with st.spinner("🔄 Converting PDF to Image & Running OCR..."):
        # Convert PDF to list of images
        images = pdf2image.convert_from_bytes(uploaded_file.read())
        
        full_text = ""
        for i, img in enumerate(images):
            # Process each page with OCR
            page_text = pytesseract.image_to_string(img)
            full_text += f"\n--- Page {i+1} ---\n" + page_text
        
        # Parse the extracted text
        items = parse_po_text(full_text)
        
    if items:
        st.success(f"✅ Extracted {len(items)} items!")
        df = pd.DataFrame(items)
        
        # Display Table
        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True)
        
        # Excel Export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PO_Items')
            # Formatting the excel columns
            workbook = writer.book
            worksheet = writer.sheets['PO_Items']
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        st.download_button(
            label="📥 Download Excel File",
            data=output.getvalue(),
            file_name=f"Extracted_PO_{uploaded_file.name}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("❌ No items found. Please check the 'Raw Text' below to see if the OCR read the document correctly.")
        with st.expander("View Raw OCR Text"):
            st.text(full_text)

st.sidebar.info("Tip: If items are missing, ensure the PDF is high quality and not blurry.")
