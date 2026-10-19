import os
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="BEZA Electronic Permitting & Licensing Portal",
    page_icon="🏢",
    layout="wide",
)

# Custom Enterprise Styling for Technical Evaluators
st.markdown(
    """
    <style>
        .main-title {font-size: 22px; font-weight: 700; color: #0F172A; margin-bottom: 0px;}
        .sub-title {font-size: 13px; font-weight: 600; color: #475569; margin-top: 2px;}
        .section-header {font-size: 15px; font-weight: 600; color: #1E3A8A; margin-top: 10px; margin-bottom: 10px;}
    </style>
""",
    unsafe_allow_html=True,
)

# --- HEADER WITH OFFICIAL LOGO ---
logo_filename = "BEZA-LOGO-Copy-300x300.png"

col_logo, col_text = st.columns([1, 8])
with col_logo:
  if os.path.exists(logo_filename):
    st.image(logo_filename, width=75)
  else:
    st.write("🏢")

with col_text:
  st.markdown(
      '<div class="main-title">BANGSAMORO ECONOMIC ZONE AUTHORITY (BEZA)</div>',
      unsafe_allow_html=True,
  )
  st.markdown(
      '<div class="sub-title">Office of the Building Official — Electronic'
      " Permitting & E-Services Portal (RA 11032 ARTA Compliant)</div>",
      unsafe_allow_html=True,
  )

st.markdown("---")

# Map form names to actual filenames in your root directory
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

# --- SIDEBAR NAVIGATION & SECURE ADMIN GATEWAY ---
with st.sidebar:
  if os.path.exists(logo_filename):
    st.image(logo_filename, width=110)

  st.markdown("### 📋 Regulatory Modules")
  selected_form = st.selectbox(
      "Select Application / Permit Form", list(filename_map.keys())
  )

  st.markdown("---")
  st.markdown("### 📥 Document Center")
  st.write("Download official blank templates for offline encoding:")

  target_file = filename_map.get(selected_form)
  if target_file and os.path.exists(target_file):
    with open(target_file, "rb") as pdf_file:
      st.download_button(
          label="📄 Download Blank Official PDF",
          data=pdf_file,
          file_name=target_file,
          mime="application/pdf",
          type="primary",
      )
  else:
    st.warning("Template file not found in repository.")

  st.markdown("---")
  st.markdown("### 🔒 BEZA Official Gateway")
  admin_toggle = st.checkbox("Access Official Review Panel")

  show_admin = False
  if admin_toggle:
    # Secure PIN protection for evaluators (You can change "BEZA2026" to any PIN you prefer)
    admin_pin = st.text_input("Enter Official Access PIN", type="password")
    if admin_pin == "BEZA2026":
      show_admin = True
      st.success("Access Granted.")
    elif admin_pin != "":
      st.error("Invalid PIN.")

  st.markdown("---")
  st.markdown("### ⚖️ ARTA Compliance")
  st.info(
      "Streamlined e-submission portal designed for efficient technical"
      " evaluation and transparent processing cycles."
  )


# --- PORTAL VIEW 2: SECURE BEZA OFFICIAL REVIEW DASHBOARD ---
if show_admin:
  st.markdown("### 🛡️ BEZA Official Evaluation & Review Dashboard")
  st.write(
      "Review incoming applicant submissions, track metadata, and export"
      " compliance logs for technical auditing."
  )

  csv_file = "submissions.csv"
  if os.path.exists(csv_file):
    df_submissions = pd.read_csv(csv_file)
    st.markdown(
        f"**Total Received Applications:** {len(df_submissions)}"
    )
    st.dataframe(df_submissions, use_container_width=True)

    # Export button for officials
    csv_bytes = df_submissions.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Submission Audit Log (CSV)",
        data=csv_bytes,
        file_name="BEZA_Audit_Logs.csv",
        mime="text/csv",
        type="primary",
    )
  else:
    st.info(
        "No application submissions recorded yet. Once applicants transmit"
        " their packages, they will appear securely here."
    )

# --- PORTAL VIEW 1: PUBLIC APPLICANT SUBMISSION (DEFAULT) ---
else:
  st.markdown(f"### Active Module: **{selected_form}**")
  st.info(
      "**Workflow Instructions:** 1. Download the official blank form from the"
      " sidebar. 2. Accomplish the form and compile required engineering plans"
      " and specifications. 3. Submit your complete digital package below."
  )

  with st.form("technical_submission_form"):
    st.markdown(
        '<div class="section-header">1. Project Identification & Applicant'
        " Metadata</div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    app_ref_no = c1.text_input(
        "Application Reference No.", placeholder="BEZA-2026-XXXX"
    )
    proj_category = c2.selectbox(
        "Project Classification",
        [
            "Commercial",
            "Industrial",
            "Institutional",
            "Residential",
            "Infrastructure",
        ],
    )
    submission_stage = c3.radio(
        "Submission Type", ["Original Filing", "Resubmission / Compliance"]
    )

    col_a, col_b = st.columns([2, 1])
    owner_name = col_a.text_input(
        "Name of Owner / Applicant (Last Name, First Name, M.I.) *"
    )
    tin = col_b.text_input("Taxpayer Identification No. (TIN) *")

    col_c, col_d = st.columns(2)
    enterprise_name = col_c.text_input(
        "Registered Enterprise Name (if applicable)"
    )
    contact_no = col_d.text_input("Official Contact Number *")

    location = st.text_input(
        "Exact Location of Construction / Installation (Zone, Municipality) *"
    )

    st.markdown("---")
    st.markdown(
        '<div class="section-header">2. Technical Document Attachments (PDF / CAD'
        " Packages)</div>",
        unsafe_allow_html=True,
    )

    up_col1, up_col2 = st.columns(2)
    with up_col1:
      uploaded_application_form = st.file_uploader(
          "Upload Accomplished & Signed Official Form (PDF) *", type=["pdf"]
      )
      uploaded_plans = st.file_uploader(
          "Upload Signed & Sealed Engineering Plans (PDF) *", type=["pdf"]
      )

    with up_col2:
      uploaded_computations = st.file_uploader(
          "Upload Structural / Technical Computations (PDF)", type=["pdf"]
      )
      uploaded_clearances = st.file_uploader(
          "Upload Environmental / Zone Clearances & Supporting Docs (PDF/ZIP)",
          type=["pdf", "zip"],
      )

    st.markdown("---")
    submitted = st.form_submit_button(
        "🔒 Securely Transmit Application Package to BEZA", type="primary"
    )

  if submitted:
    if (
        not owner_name
        or not tin
        or not location
        or not uploaded_application_form
        or not uploaded_plans
    ):
      st.error(
          "⚠️ Incomplete Submission: Please ensure all mandatory fields (*)"
          " marked with an asterisk and required technical documents are"
          " attached."
      )
    else:
      # Save submission record to CSV for BEZA evaluators
      sub_data = {
          "Timestamp": [pd.Timestamp.now()],
          "Module": [selected_form],
          "App_Ref_No": [app_ref_no or "BEZA-2026-AUTO"],
          "Category": [proj_category],
          "Owner_Name": [owner_name],
          "TIN": [tin],
          "Enterprise": [enterprise_name],
          "Contact": [contact_no],
          "Location": [location],
          "Form_File": [uploaded_application_form.name],
          "Plans_File": [uploaded_plans.name],
      }
      df_new = pd.DataFrame(sub_data)
      csv_file = "submissions.csv"

      if os.path.exists(csv_file):
        df_existing = pd.read_csv(csv_file)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
      else:
        df_combined = df_new

      df_combined.to_csv(csv_file, index=False)

      st.success(
          "✅ **Transmission Successful:** Your technical documentation"
          " package has been logged into the BEZA regulatory gateway for"
          " initial review by the Office of the Building Official."
      )
      st.balloons()
