import streamlit as st
import os
import zipfile
import io

def rename_logic(filename, prefix_to_remove, suffix_to_add):
    # Split filename and extension
    base_name, extension = os.path.splitext(filename)
    
    # Remove the specific prefix if it exists
    if prefix_to_remove and base_name.startswith(prefix_to_remove):
        new_name = base_name.replace(prefix_to_remove, "", 1)
    else:
        new_name = base_name
        
    # Add the descriptive suffix
    new_name = f"{new_name}{suffix_to_add}{extension}"
    return new_name

st.set_page_config(page_title="Image Bulk Renamer", layout="centered")
st.title("🖼️ Image Bulk Renamer")
st.info("Remove brand prefixes and add standard viewpoints (e.g., exterior-right-front-three-quarter)")

# Sidebar Configuration
st.sidebar.header("Renaming Rules")
prefix = st.sidebar.text_input("Prefix to remove (e.g., 'Ampere-')", value="Ampere-")
suffix = st.sidebar.text_input("Suffix to add", value="-exterior-right-front-three-quarter")

tab1, tab2 = st.tabs(["Bulk Upload", "Single Upload"])

# --- TAB 1: BULK UPLOAD ---
with tab1:
    uploaded_files = st.file_uploader("Upload multiple images", accept_multiple_files=True)
    
    if uploaded_files:
        st.write(f"Total files: {len(uploaded_files)}")
        
        # Create a ZIP in memory for download
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for uploaded_file in uploaded_files:
                new_filename = rename_logic(uploaded_file.name, prefix, suffix)
                
                # Copy file content to zip with new name
                zip_file.writestr(new_filename, uploaded_file.getvalue())
                st.text(f"✅ {uploaded_file.name} ➡️ {new_filename}")

        st.download_button(
            label="Download Renamed Files (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="renamed_images.zip",
            mime="application/zip"
        )

# --- TAB 2: SINGLE UPLOAD ---
with tab2:
    single_file = st.file_uploader("Upload a single image", key="single")
    
    if single_file:
        new_name = rename_logic(single_file.name, prefix, suffix)
        st.success(f"New Name: {new_name}")
        
        st.download_button(
            label="Download Renamed Image",
            data=single_file.getvalue(),
            file_name=new_name,
            mime="image/png"
        )
