import streamlit as st
import os
from PyPDF2 import PdfReader
import docx

# -------------------------------
# PAGE CONFIGURATION
# -------------------------------
st.set_page_config(page_title="AI Resume Parser", page_icon="💬", layout="wide")

# -------------------------------
# MAIN TITLE
# -------------------------------
st.title("💬 AI Resume Parser")
st.write("Upload a resume file (PDF or DOCX) below to extract and analyze its content.")

# -------------------------------
# FILE UPLOAD
# -------------------------------
uploaded_file = st.file_uploader("📎 Upload resumes", type=["pdf", "docx"])


# -------------------------------
# FUNCTION TO EXTRACT TEXT
# -------------------------------
def extract_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text.strip()


# -------------------------------
# DISPLAY PARSED DATA
# -------------------------------
if uploaded_file:
    st.subheader("📄 Extracted Resume Content")

    extracted_text = extract_text(uploaded_file)

    if extracted_text:
        st.success("✅ Resume successfully processed!")

        # Display in collapsible section
        with st.expander("View Full Extracted Text"):
            st.text_area("Extracted Text", extracted_text, height=300)

        # Simple list view (simulate AI summary)
        st.subheader("🧠 Key Information (Summary Example)")
        st.markdown("""
        - **Name:** Automatically detected from text (if available)  
        - **Email:** Extracted if found in document  
        - **Skills:** Parsed keywords like Python, Excel, etc.  
        - **Experience:** Summarized years or job positions  
        - **Education:** School, degree, and field detected  
        """)
    else:
        st.warning("⚠️ No text could be extracted from the uploaded file. Please try an
