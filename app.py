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


# --- PORTAL VIEW 2: SECURE BEZA OFFICIAL REVIEW & EDIT/DELETE DASHBOARD ---
if show_admin:
  st.markdown("### 🛡️ BEZA Official Evaluation & Review Dashboard")
  st.write(
      "Review incoming applicant submissions, edit records, delete invalid"
      " entries, and export compliance logs."
  )

  csv_file = "submissions.csv"
  if os.path.exists(csv_file):
    df_submissions = pd.read_csv(csv_file)
    st.markdown(
        f"**Total Received Applications:** {len(df_submissions)}"
    )
    st.dataframe(df_submissions, use_container_width=True)

    st.markdown("---")
    st.markdown("### ⚙️ Manage / Edit / Delete Submissions")

    if len(df_submissions) > 0:
      row_indices = list(range(len(df_submissions)))
      selected_idx = st.selectbox(
          "Select Row Index to Edit or Delete",
          row_indices,
          format_func=lambda x: f"Row {x} - {df_submissions.loc[x, 'Owner_Name']} ({df_submissions.loc[x, 'App_Ref_No']})",
      )

      col_edit, col_del = st.columns(2)

      with col_edit:
        st.markdown("#### Edit Selected Record")
        current_row = df_submissions.loc[selected_idx]

        with st.form("edit_form"):
          edit_ref = st.text_input(
              "Application Reference No.", value=str(current_row["App_Ref_No"])
          )
          edit_owner = st.text_input(
              "Owner Name", value=str(current_row["Owner_Name"])
          )
          edit_tin = st.text_input("TIN", value=str(current_row["TIN"]))
          edit_cost = st.number_input(
              "Estimated Cost (PHP)",
              value=float(current_row["Estimated_Cost"]),
          )
          edit_area = st.number_input(
              "Floor Area (sq. m.)", value=float(current_row["Floor_Area_Sqm"])
          )

          save_changes = st.form_submit_button("💾 Save Changes")

        if save_changes:
          df_submissions.loc[selected_idx, "App_Ref_No"] = edit_ref
          df_submissions.loc[selected_idx, "Owner_Name"] = edit_owner
          df_submissions.loc[selected_idx, "TIN"] = edit_tin
          df_submissions.loc[selected_idx, "Estimated_Cost"] = edit_cost
          df_submissions.loc[selected_idx, "Floor_Area_Sqm"] = edit_area
          df_submissions.to_csv(csv_file, index=False)
          st.success(
              f"✅ Row {selected_idx} successfully updated! Please refresh the"
              " page."
          )
          st.rerun()

      with col_del:
        st.markdown("#### Delete Selected Record")
        st.warning(
            "⚠️ Deleting a record is permanent and removes it from the audit"
            " log."
        )
        if st.button(
            "🗑️ Delete This Record", type="primary", key="delete_btn"
        ):
          df_submissions = df_submissions.drop(selected_idx).reset_index(
              drop=True
          )
          df_submissions.to_csv(csv_file, index=False)
          st.success(
              f"🗑️ Row {selected_idx} successfully deleted! Please refresh the"
              " page."
          )
          st.rerun()

    st.markdown("---")
    csv_bytes = df_submissions.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Submission Audit Log (CSV)",
        data=csv_bytes,
        file_name="BEZA_Audit_Logs.csv",
        mime="text/csv",
        type="primary",
    )
  else:
    st.info("No application submissions recorded yet.")

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
    proj_category = c1.selectbox(
        "Project Classification",
        [
            "Commercial",
            "Industrial",
            "Institutional",
            "Residential",
            "Infrastructure",
        ],
    )
    submission_stage = c2.radio(
        "Submission Type", ["Original Filing", "Resubmission / Compliance"]
    )
    storeys = c3.number_input("Number of Storeys", min_value=1, step=1)

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
        '<div class="section-header">2. Engineering Metrics & Cost Estimates'
        " (Box 3A Data)</div>",
        unsafe_allow_html=True,
    )

    m1, m2, m3 = st.columns(3)
    floor_area = m1.number_input(
        "Total Floor Area (sq. m.) *", min_value=0.0, step=1.0
    )
    estimated_cost = m2.number_input(
        "Total Estimated Project Cost (PHP) *", min_value=0.0, step=1000.0
    )
    materials = m3.selectbox(
        "Primary Materials", ["Concrete", "Steel", "Wooden", "Mixed"]
    )

    st.markdown("---")
    st.markdown(
        '<div class="section-header">3. Technical Document Attachments (PDF / CAD'
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
        or floor_area <= 0
        or estimated_cost <= 0
        or not uploaded_application_form
        or not uploaded_plans
    ):
      st.error(
          "⚠️ Incomplete Submission: Please ensure all mandatory fields (*)"
          " marked with an asterisk, valid project metrics (Area & Cost > 0), and"
          " required technical documents are attached."
      )
    else:
      auto_ref_no = f"BEZA-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"

      sub_data = {
          "Timestamp": [pd.Timestamp.now()],
          "Module": [selected_form],
          "App_Ref_No": [auto_ref_no],
          "Category": [proj_category],
          "Owner_Name": [owner_name],
          "TIN": [tin],
          "Enterprise": [enterprise_name],
          "Floor_Area_Sqm": [floor_area],
          "Estimated_Cost": [estimated_cost],
          "Storeys": [storeys],
          "Materials": [materials],
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
          f"✅ **Transmission Successful!** Your application package has been"
          f" logged into the BEZA gateway.\n\n"
          f"📌 **System-Generated Tracking Reference No.:** `{auto_ref_no}`\n"
          f"🏗️ **Declared Area:** {floor_area:,.2f} sq. m. | 💰 **Estimated"
          f" Cost:** ₱{estimated_cost:,.2f}\n\n"
          "*(Please save your tracking number for your records.)*"
      )
      st.balloons()
