import streamlit as st
import pandas as pd
import pdfplumber
import io

st.set_page_config(page_title="Stellantis PO Extractor", layout="wide")
st.title("📄 Stellantis PO Extractor")

uploaded_files = st.file_uploader("Upload Stellantis PO PDFs", type="pdf", accept_multiple_files=True)

def extract_stellantis_logic(pdf_file):
    extracted_items = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Force table extraction using visual lines
            table = page.extract_table({
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
            })
            
            if not table:
                # Fallback: Try extracting without strict lines (for borderless tables)
                table = page.extract_table()

            if table:
                for row in table:
                    # Filter for rows that look like Line Items (contain 'USD' or 'LO')
                    # This matches Item 1 and Item 2 in your document [cite: 7, 49]
                    if any("USD" in str(cell) for cell in row) and any("LO" in str(cell) for cell in row):
                        # Clean up the row data
                        clean_row = [str(c).replace('\n', ' ').strip() if c else "" for c in row]
                        
                        # Mapping based on your document's columns [cite: 7, 49]
                        extracted_items.append({
                            "Source File": pdf_file.name,
                            "Item": clean_row[0],
                            "Material": clean_row[1],
                            "Quantity": clean_row[2],
                            "UOM": clean_row[3],
                            "Unit Price / Currency": clean_row[4],
                            "Effective Value": clean_row[5],
                            "Net Amount": clean_row[6]
                        })
    return extracted_items

if uploaded_files:
    final_data = []
    for file in uploaded_files:
        data = extract_stellantis_logic(file)
        final_data.extend(data)
    
    if final_data:
        df = pd.DataFrame(final_data)
        st.success(f"Extracted {len(df)} items!")
        st.dataframe(df)

        # Download to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='PO_Data')
        
        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name="Stellantis_PO_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Still no data found. The PDF might be a scanned image. Would you like to try OCR mode?")
