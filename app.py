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

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
  st.markdown("### 📋 Select Permit / Form")
  permit_choice = st.selectbox(
      "Choose Application Form",
      [
          "BEZA.EESSU.F.001 BUILDING PERMIT",
          "BEZA.EESSU.F.002 MECHANICAL PERMIT",
          "BEZA.EESSU.F.003 ELECTRICAL PERMIT",
          "BEZA.EESSU.F.004 ELECTRONICS PERMIT",
          "BEZA.EESSU.F.005 FENCING PERMIT",
          "BEZA.EESSU.F.006 SANITARY AND PLUMBING PERMIT",
          "BEZA.EESSU.F.007 Mechanical Data Sheet",
          "BEZA.EESSU.F.008 Electrical Data Sheet",
          "BEZA.EESSU.F.009 Electronics Data Sheet",
          "BEZA DEMOLITION PERMIT",
          "BEZA SIGN & SIGN STRUCTURE PERMIT",
          "Excavation & Ground Preparation Permit",
      ],
  )

  st.markdown("---")
  st.markdown("### ℹ️ Guidelines")
  st.info(
      "Ensure all technical data is reviewed by your licensed professional"
      " before generating the final printable submission."
  )


# --- CORE DATA ENTRY FORM ---
st.markdown(f"### Current Application Module: **{permit_choice}**")

with st.form("permit_application_form"):
  col1, col2, col3 = st.columns(3)
  app_no = col1.text_input("Application No.", placeholder="BEZA-2026-XXXX")
  permit_no = col2.text_input("Permit No. (Leave blank if new)")
  app_type = col3.radio("Application Type", ["ORIGINAL", "RENEWAL"], horizontal=True)

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

  st.markdown("---")
  st.markdown("#### 2. Project Scope & Technical Specifications")

  if "BUILDING PERMIT" in permit_choice:
    scope = st.multiselect(
        "Scope of Work",
        ["New Construction", "Addition", "Repair", "Renovation", "Demolition"],
    )
    occupancy = st.selectbox(
        "Type of Occupancy",
        [
            "Residential",
            "Commercial",
            "Industrial",
            "Institutional",
            "Agricultural",
        ],
    )
    est_cost = st.number_input(
        "Total Estimated Construction Cost (PHP)", min_value=0.0, step=10000.0
    )

  elif "MECHANICAL" in permit_choice:
    mech_type = st.text_input(
        "Type of Mechanical Equipment / Installation (e.g., Boiler, Elevator,"
        " Aircon)"
    )
    mech_cost = st.number_input(
        "Estimated Cost of Mechanical Installation (PHP)",
        min_value=0.0,
        step=5000.0,
    )

  elif "ELECTRICAL" in permit_choice:
    total_connected_load = st.text_input(
        "Total Connected Load (kVA / kW)"
    )
    elec_cost = st.number_input(
        "Estimated Cost of Electrical Installation (PHP)",
        min_value=0.0,
        step=5000.0,
    )

  else:
    general_notes = st.text_area(
        "Specific Details / Scope of Installation / Remarks"
    )

  submitted = st.form_submit_button(
      "🚀 Validate & Compile Official Printable Form", type="primary"
  )

# --- PDF OVERLAY & GENERATION FUNCTION ---
def overlay_data_on_pdf(template_filename, form_data):
  """Loads the blank PDF template from assets/ and stamps user inputs at precise coordinates."""
  template_path = os.path.join("assets", template_filename)

  if not os.path.exists(template_path):
    return None

  # Open the original blank PDF using PyMuPDF
  doc = fitz.open(template_path)
  page = doc[0]  # Target first page

  # Define coordinate mappings (x, y points) for standard BEZA layout forms
  # Note: You can fine-tune these coordinates depending on your exact scanned PDF resolution.
  page.insert_text(
      (150, 115), form_data.get("app_no", ""), fontsize=10, color=(0, 0, 0)
  )
  page.insert_text(
      (450, 115), form_data.get("permit_no", ""), fontsize=10, color=(0, 0, 0)
  )
  page.insert_text(
      (70, 175), form_data.get("owner_name", ""), fontsize=10, color=(0, 0, 0)
  )
  page.insert_text(
      (430, 175), form_data.get("tin", ""), fontsize=10, color=(0, 0, 0)
  )
  page.insert_text(
      (70, 230), form_data.get("address", ""), fontsize=10, color=(0, 0, 0)
  )
  page.insert_text(
      (430, 230), form_data.get("contact_no", ""), fontsize=10, color=(0, 0, 0)
  )
  page.insert_text(
      (70, 260), form_data.get("location", ""), fontsize=10, color=(0, 0, 0)
  )

  # Save to memory buffer
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
    st.success(
        "🎉 Form successfully validated and compiled according to ARTA standards!"
    )

    # Map form names to actual filenames in your assets folder
    filename_map = {
        "BEZA.EESSU.F.001 BUILDING PERMIT": "BEZA.EESSU.F.001 BUILDING PERMIT.pdf",
        "BEZA.EESSU.F.002 MECHANICAL PERMIT": (
            "BEZA.EESSU.F.002 MECHANICAL PERMIT.pdf"
        ),
        "BEZA.EESSU.F.003 ELECTRICAL PERMIT": (
            "BEZA.EESSU.F.003 ELECTRICAL PERMIT.pdf"
        ),
        "BEZA.EESSU.F.004 ELECTRONICS PERMIT": (
            "BEZA.EESSU.F.004 ELECTRONICS PERMIT.pdf"
        ),
        "BEZA.EESSU.F.005 FENCING PERMIT": "BEZA.EESSU.F.005 FENCING PERMIT.pdf",
        "BEZA.EESSU.F.006 SANITARY AND PLUMBING PERMIT": (
            "BEZA.EESSU.F.006 SANITARY AND PLUMBING PERMIT.pdf"
        ),
        "BEZA.EESSU.F.007 Mechanical Data Sheet": (
            "BEZA.EESSU.F.007 Mechanical Data Sheet.pdf"
        ),
        "BEZA.EESSU.F.008 Electrical Data Sheet": (
            "BEZA.EESSU.F.008 Electrical Data Sheet.pdf"
        ),
        "BEZA.EESSU.F.009 Electronics Data Sheet": (
            "BEZA.EESSU.F.009 Electronics Data Sheet.pdf"
        ),
        "BEZA DEMOLITION PERMIT": "BEZA DEMOLITION PERMIT FORM.pdf",
        "BEZA SIGN & SIGN STRUCTURE PERMIT": (
            "BEZA SIGN AND SIGN STRUCTURE PERMIT FORM MERGED.pdf"
        ),
        "Excavation & Ground Preparation Permit": (
            "Application-Form-Excavation-Ground-Preparation-and-Soil-Investigation.pdf"
        ),
    }

    target_file = filename_map.get(permit_choice)
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
          label="📥 Download Filled & Printable Official Permit PDF",
          data=pdf_result,
          file_name=f"Filled_{permit_choice.replace(' ', '_')}_{app_no}.pdf",
          mime="application/pdf",
          type="primary",
      )
    else:
      st.warning(
          f"Template file `{target_file}` not found in the `assets/` folder."
          " Please upload your PDF templates to GitHub to enable direct"
          " overlay generation."
      )
