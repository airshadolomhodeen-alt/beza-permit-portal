import io
import os
import streamlit as st
import fitz  # PyMuPDF for precise PDF form overlay

# Page Configuration
st.set_page_config(
    page_title="BEZA Electronic Permitting & Licensing Portal",
    page_icon="🏢",
    layout="wide",
)

# Custom Styling for ARTA-Compliant Professional Interface
st.markdown(
    """
    <style>
        .main-header {font-size: 26px; font-weight: bold; color: #1E3A8A; text-align: center;}
        .sub-header {font-size: 14px; color: #4B5563; text-align: center; margin-bottom: 25px;}
        .card {background-color: #F8FAFC; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; margin-bottom: 20px;}
    </style>
""",
    unsafe_allow_html=True,
)

# Header
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
  permit_choice = st.selectbox("Choose Application Form", list(filename_map.keys()))

  st.markdown("---")
  st.markdown("### 📥 Download Blank Official Form")
  st.write("Need the raw printable PDF? Download it directly below:")

  target_file = filename_map.get(permit_choice)
  if target_file and os.path.exists(target_file):
    with open(target_file, "rb") as pdf_file:
      st.download_button(
          label=f"📄 Download Blank PDF",
          data=pdf_file,
          file_name=target_file,
          mime="application/pdf",
      )
  else:
    st.warning("Blank PDF file not found in repository root.")

  st.markdown("---")
  st.markdown("### ℹ️ ARTA Compliance")
  st.info(
      "Applicants can either fill out the digital portal for automated filing"
      " or download blank forms for manual completion."
  )


# --- CORE DATA ENTRY FORM ---
st.markdown(f"### Digital Filing Module: **{permit_choice}**")

with st.form("permit_application_form"):
  col1, col2, col3 = st.columns(3)
  app_no = col1.text_input("Application No.", placeholder="BEZA-2026-XXXX")
  permit_no = col2.text_input("Permit No. (Leave blank if new)")
  app_type = st.radio("Application Type", ["ORIGINAL", "RENEWAL"], horizontal=True)

  st.markdown("---")
  st.markdown("#### 1. Applicant & Enterprise Information")
  col_a, col_b = st.columns([2, 1])
  owner_name = col_a.text_input(
      "NAME OF OWNER / APPLICANT (Last Name, First Name, M.I.) *"
  )
  tin = col_b.text_input("TAXPAYER IDENTIFICATION NO. (TIN) *")

  col_c, col_d = st.columns(2)
  enterprise = col_c.text_input("For Construction Owned by an Enterprise")
  ownership_form = col_d.text_input("Form of Ownership (Sole Prop / Corp / Partnership)")

  address = st.text_input("Complete Address *")
  contact_no = st.text_input("Telephone / Mobile No. *")
  location = st.text_input(
      "Location of Construction / Installation (Zone, Block, Lot, Municipality)"
      " *"
  )

  submitted = st.form_submit_button(
      "🚀 Generate Filled Digital Application", type="primary"
  )

# --- PDF OVERLAY FUNCTION ---
def overlay_data_on_pdf(template_filename, form_data):
  template_path = template_filename
  if not os.path.exists(template_path):
    return None

  doc = fitz.open(template_path)
  page = doc[0]

  # Adjusted coordinates for BEZA EESSUF.001 form layout
  # (You can fine-tune these x, y numbers if needed based on your exact PDF dimensions)
  page.insert_text(
      (120, 105), form_data.get("app_no", ""), fontsize=9, color=(0, 0, 0)
  )
  page.insert_text(
      (430, 105), form_data.get("permit_no", ""), fontsize=9, color=(0, 0, 0)
  )
  page.insert_text(
      (75, 175), form_data.get("owner_name", ""), fontsize=9, color=(0, 0, 0)
  )
  page.insert_text(
      (420, 175), form_data.get("tin", ""), fontsize=9, color=(0, 0, 0)
  )
  page.insert_text(
      (75, 215), form_data.get("address", ""), fontsize=9, color=(0, 0, 0)
  )
  page.insert_text(
      (420, 215), form_data.get(
          "contact_no", ""
      ), fontsize=9, color=(0, 0, 0)
  )
  page.insert_text(
      (75, 245), form_data.get("location", ""), fontsize=9, color=(0, 0, 0)
  )

  output_buffer = io.BytesIO()
  doc.save(output_buffer)
  doc.close()
  output_buffer.seek(0)
  return output_buffer


# --- OUTPUT HANDLING ---
if submitted:
  if not owner_name or not tin or not location:
    st.error(
        "⚠️ Please fill out all required fields marked with (*) before"
        " proceeding."
    )
  else:
    st.success("🎉 Form compiled successfully!")

    form_payload = {
        "app_no": app_no,
        "permit_no": permit_no,
        "owner_name": owner_name,
        "tin": tin,
        "address": address,
        "contact_no": contact_no,
        "location": location,
    }

    pdf_result = overlay_data_on_pdf(target_file, form_payload)

    if pdf_result:
      st.download_button(
          label="📥 Download Your Filled Application Form",
          data=pdf_result,
          file_name=f"Filled_{permit_choice.replace(' ', '_')}_{app_no}.pdf",
          mime="application/pdf",
          type="primary",
      )
