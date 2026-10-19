import os
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="BEZA Electronic Permitting & Licensing Portal",
    page_icon="🏢",
    layout="wide",
)

# Custom Styling
st.markdown(
    """
    <style>
        .main-header {font-size: 24px; font-weight: bold; color: #1E3A8A; text-align: center;}
        .sub-header {font-size: 13px; color: #4B5563; text-align: center; margin-bottom: 20px;}
        .card {background-color: #F8FAFC; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 20px;}
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">BANGSAMORO ECONOMIC ZONE AUTHORITY</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">E-SERVICES & REGULATORY PERMIT PORTAL (RA 11032 ARTA Compliant)</div>',
    unsafe_allow_html=True,
)

# Map form names to actual filenames in your root directory
filename_map = {
    "BEZA.EESSU.F.001 BUILDING PERMIT": "BEZA.EESSU.F.001 BUILDING PERMIT.pdf",
    "BEZA.EESSU.F.002 MECHANICAL PERMIT": "BEZA.EESSU.F.002 MECHANICAL PERMIT.pdf",
    "BEZA.EESSU.F.003 ELECTRICAL PERMIT": "BEZA.EESSU.F.003 ELECTRICAL PERMIT.pdf",
    "BEZA.EESSU.F.004 ELECTRONICS PERMIT": "BEZA.EESSU.F.004 ELECTRONICS PERMIT.pdf",
    "BEZA.EESSU.F.005 FENCING PERMIT": "BEZA.EESSU.F.005 FENCING PERMIT.pdf",
    "BEZA.EESSU.F.006 SANITARY AND PLUMBING PERMIT": "BEZA.EESSU.F.006 SANITARY AND PLUMBING PERMIT.pdf",
    "BEZA.EESSU.F.007 Mechanical Data Sheet": "BEZA.EESSU.F.007 Mechanical Data Sheet.pdf",
    "BEZA.EESSU.F.008 Electrical Data Sheet": "BEZA.EESSU.F.008 Electrical Data Sheet.pdf",
    "BEZA.EESSU.F.009 Electronics Data Sheet": "BEZA.EESSU.F.009 Electronics Data Sheet.pdf",
    "BEZA DEMOLITION PERMIT": "BEZA DEMOLITION PERMIT FORM.pdf",
    "BEZA SIGN & SIGN STRUCTURE PERMIT": "BEZA SIGN AND SIGN STRUCTURE PERMIT FORM MERGED.pdf",
    "Excavation & Ground Preparation Permit": "Application-Form-Excavation-Ground-Preparation-and-Soil-Investigation.pdf",
}

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
  st.markdown("### 📋 Select Permit / Form")
  selected_form = st.selectbox("Choose Official Form", list(filename_map.keys()))

  st.markdown("---")
  st.markdown("### 📥 Step 1: Download Form")
  st.write("Download the clean blank PDF to fill out manually:")

  target_file = filename_map.get(selected_form)
  if target_file and os.path.exists(target_file):
    with open(target_file, "rb") as pdf_file:
      st.download_button(
          label="📄 Download Blank PDF",
          data=pdf_file,
          file_name=target_file,
          mime="application/pdf",
          type="primary",
      )
  else:
    st.warning("Selected PDF file not found in repository root.")


# --- MAIN PORTAL: UPLOAD REQUIREMENTS ---
st.markdown(f"### Online Submission Portal: **{selected_form}**")
st.markdown(
    '<div class="card"><b>Instructions (ARTA Compliance):</b><br>1. Download the official blank form from the sidebar.<br>2. Fill out the form and prepare all required technical plans and supporting documents.<br>3. Upload your completed documents below for official BEZA review.</div>',
    unsafe_allow_html=True,
)

with st.form("requirements_upload_form"):
  st.markdown("#### Applicant & Project Details")
  col1, col2 = st.columns(2)
  app_no = col1.text_input("Application Reference No. (if assigned)")
  owner_name = col2.text_input("Name of Owner / Applicant *")

  col3, col4 = st.columns(2)
  tin = col3.text_input("Taxpayer Identification No. (TIN) *")
  contact_no = col4.text_input("Contact Number *")

  location = st.text_input("Location of Construction / Installation *")

  st.markdown("---")
  st.markdown("#### Upload Completed Requirements")
  uploaded_application_form = st.file_uploader(
      "1. Upload Filled & Signed Official Application Form (PDF)", type=["pdf"]
  )
  uploaded_plans = st.file_uploader(
      "2. Upload Architectural / Engineering Plans & Specifications (PDF)",
      type=["pdf"],
  )
  uploaded_supporting = st.file_uploader(
      "3. Upload Supporting Documents / Clearances (PDF / ZIP)",
      type=["pdf", "zip"],
  )

  submitted = st.form_submit_button(
      "🚀 Submit Complete Application Package", type="primary"
  )

if submitted:
  if not owner_name or not tin or not location or not uploaded_application_form:
    st.error(
        "⚠️ Please complete all required fields (*) and upload your filled"
        " application form before submitting."
    )
  else:
    st.success(
        "🎉 Your application package has been successfully submitted to BEZA!"
        " You will receive an acknowledgment status update once initial"
        " evaluation begins."
    )
    st.balloons()
