import streamlit as st
import PyPDF2
import pdfplumber
import re
from io import BytesIO
import zipfile

st.set_page_config(page_title="ITS Certificate Splitter", layout="wide")
st.title("📄 ITS Certificate Splitter & Renamer")
st.markdown("""
Upload a PDF containing multiple ITS certificates.  
The app will split each certificate into a separate PDF and rename it in the format:

**<CertificateNo>_CERTIFICATE OF ATTENDANCE_<ParticipantName>**
""")

# ----------------- File Upload -----------------
uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file is not None:
    # Read PDF
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    total_pages = len(pdf_reader.pages)
    st.write(f"Total pages in PDF: {total_pages}")

    # Prepare ZIP in memory
    zip_buffer = BytesIO()
    processed_count = 0

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for i in range(total_pages):
            # Extract text from the page
            with pdfplumber.open(uploaded_file) as pdf:
                page_text = pdf.pages[i].extract_text() or ""

            # ----------------- Extract certificate number -----------------
            cert_num_match = re.search(r"Certificate No[:\s]*([\d]+)", page_text, re.IGNORECASE)
            cert_num = cert_num_match.group(1) if cert_num_match else None

            # ----------------- Extract participant name -----------------
            name = None
            for line in page_text.split("\n"):
                line_clean = line.strip()
                if line_clean.isupper() and len(line_clean.split()) >= 2:
                    name = line_clean
                    break

            if not cert_num or not name:
                st.warning(f"Skipped page {i+1}: Certificate number or name not found")
                continue

            # ----------------- Create new PDF in memory -----------------
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[i])
            pdf_bytes = BytesIO()
            pdf_writer.write(pdf_bytes)

            # ----------------- Add to ZIP -----------------
            output_filename = f"{cert_num}_CERTIFICATE OF ATTENDANCE_{name}.pdf"
            zip_file.writestr(output_filename, pdf_bytes.getvalue())
            processed_count += 1
            st.write(f"✅ Processed page {i+1}: {output_filename}")

    if processed_count > 0:
        st.success(f"All done! {processed_count} certificates processed.")
        # ----------------- Download button -----------------
        st.download_button(
            label="📥 Download All Certificates as ZIP",
            data=zip_buffer.getvalue(),
            file_name="certificates.zip",
            mime="application/zip"
        )
    else:
        st.error("No certificates processed. Please check your PDF and certificate layout.")
