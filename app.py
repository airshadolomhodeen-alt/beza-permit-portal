"""
Bangsamoro Economic Zone Authority (BEZA) - Electronic Permitting & E-Services Portal
Office of the Building Official | RA 11032 ARTA Compliant
Office of the Building Official-BEZA
"""

from datetime import datetime
import hashlib
import os
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st
from werkzeug.utils import secure_filename

# ==========================================
# 1. CONSTANTS & CONFIGURATION
# ==========================================
UPLOAD_DIR: str = "uploads"
CSV_FILE: str = "submissions.csv"
LOGO_FILENAME: str = "BEZA-LOGO-Copy-300x300.png"

REQUIRED_COLUMNS: List[str] = [
    "Timestamp",
    "Module",
    "App_Ref_No",
    "Category",
    "Owner_Name",
    "TIN",
    "Enterprise",
    "Contact_No",
    "Floor_Area_Sqm",
    "Estimated_Cost",
    "Storeys",
    "Materials",
    "Location",
    "Form_File",
    "Form_Path",
    "Plans_File",
    "Plans_Path",
    "Status",
]

FILENAME_MAP: Dict[str, str] = {
    "BUILDING PERMIT": "BEZA.EESSU.F.001 BUILDING PERMIT.pdf",
    "BEZA.EESSU.F.002 MECHANICAL PERMIT": "BEZA.EESSU.F.002 MECHANICAL PERMIT.pdf",
    "ELECTRICAL PERMIT": "BEZA.EESSU.F.003 ELECTRICAL PERMIT.pdf",
    "ELECTRONICS PERMIT": "BEZA.EESSU.F.004 ELECTRONICS PERMIT.pdf",
    "FENCING PERMIT": "BEZA.EESSU.F.005 FENCING PERMIT.pdf",
    "SANITARY AND PLUMBING PERMIT": "BEZA.EESSU.F.006 SANITARY AND PLUMBING PERMIT.pdf",
    "Mechanical Data Sheet": "BEZA.EESSU.F.007 Mechanical Data Sheet.pdf",
    "Electrical Data Sheet": "BEZA.EESSU.F.008 Electrical Data Sheet.pdf",
    "Electronics Data Sheet": "BEZA.EESSU.F.009 Electronics Data Sheet.pdf",
    "BEZA DEMOLITION PERMIT": "BEZA DEMOLITION PERMIT FORM.pdf",
    "BEZA SIGN & SIGN STRUCTURE PERMIT": "BEZA SIGN AND SIGN STRUCTURE PERMIT FORM MERGED.pdf",
    "Excavation & Ground Preparation Permit": "Application-Form-Excavation-Ground-Preparation-and-Soil-Investigation.pdf",
    "Building Permit Checklist": "building permit.pdf",
    "Anti Graft": "anti_graft_1.doc",
}

# Page Setup
st.set_page_config(
    page_title="BEZA Electronic Permitting & Licensing Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 2. ENTERPRISE CSS & DESIGN TOKENS
# ==========================================
st.markdown(
    """
    <style>
        .main-title { font-size: 22px; font-weight: 700; color: #0F172A; margin-bottom: 0px; letter-spacing: -0.5px; }
        .sub-title { font-size: 13px; font-weight: 600; color: #475569; margin-top: 2px; }
        .section-header { font-size: 15px; font-weight: 600; color: #1E3A8A; margin-top: 15px; margin-bottom: 10px; border-bottom: 2px solid #E2E8F0; padding-bottom: 4px; }
        .status-badge-eval { background-color: #FEF3C7; color: #92400E; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .status-badge-approved { background-color: #D1FAE5; color: #065F46; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .status-badge-pending { background-color: #E0E7FF; color: #3730A3; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .metric-card { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 3. HELPER FUNCTIONS & UTILITIES
# ==========================================
def ensure_upload_directory(directory: str) -> None:
  """Ensures that the designated secure file upload directory exists."""
  try:
    if not os.path.exists(directory):
      os.makedirs(directory, exist_ok=True)
  except Exception as e:
    st.error(f"Critical Error: Failed to create upload directory. Details: {e}")


def sanitize_filename(filename: str) -> str:
  """Sanitizes uploaded filenames to prevent directory traversal and path injection."""
  base_name = secure_filename(filename)
  return base_name if base_name else "unnamed_attachment.pdf"


def hash_string(input_str: str) -> str:
  """Returns the SHA-256 cryptographic hash of a given string."""
  return hashlib.sha256(input_str.encode("utf-8")).hexdigest()


def verify_admin_pin(entered_pin: str) -> bool:
  """Verifies the entered admin PIN against stored secrets hash with secure fallback."""
  # Default fallback hash for 'BEZA2026' if st.secrets is unconfigured
  default_hash = hash_string("BEZA2026")
  stored_hash = st.secrets.get("ADMIN_PIN_HASH", default_hash)
  return hash_string(entered_pin) == stored_hash


def load_submissions(csv_path: str) -> pd.DataFrame:
  """Loads submissions CSV with schema validation and self-healing fallback."""
  if not os.path.exists(csv_path):
    return pd.DataFrame(columns=REQUIRED_COLUMNS)

  try:
    df = pd.read_csv(csv_path)
    # Schema validation: Ensure all mandatory columns are present
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
      for col in missing_cols:
        if col == "Status":
          df[col] = "Under Evaluation"
        else:
          df[col] = None
    return df
  except Exception as e:
    st.error(
        f"⚠️ Warning: Submissions data store appears corrupt or locked. ({e})"
    )
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def save_submissions(df: pd.DataFrame, csv_path: str) -> bool:
  """Safely writes the dataframe to CSV with exception handling."""
  try:
    df.to_csv(csv_path, index=False)
    return True
  except Exception as e:
    st.error(f"❌ Critical I/O Error: Failed to persist database. ({e}))")
    return False


# ==========================================
# 4. INITIALIZATION & SETUP
# ==========================================
ensure_upload_directory(UPLOAD_DIR)

if "admin_authenticated" not in st.session_state:
  st.session_state.admin_authenticated = False


# ==========================================
# 5. HEADER RENDERER
# ==========================================
def render_header() -> None:
  """Renders the official government portal header with agency branding."""
  col_logo, col_text = st.columns([1, 8])
  with col_logo:
    if os.path.exists(LOGO_FILENAME):
      st.image(LOGO_FILENAME, width=75)
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


render_header()


# ==========================================
# 6. SIDEBAR NAVIGATION & GATEWAY
# ==========================================
def render_sidebar() -> str:
  """Renders the sidebar navigation, tracking tool, document center, and admin gateway."""
  with st.sidebar:
    if os.path.exists(LOGO_FILENAME):
      st.image(LOGO_FILENAME, width=110)

    st.markdown("### 📋 Regulatory Modules")
    selected_form = st.selectbox(
        "Select Application / Permit Form", list(FILENAME_MAP.keys())
    )

    st.markdown("---")
    st.markdown("### 🔍 Track Application Status")
    track_code = st.text_input(
        "Enter Tracking Ref. No.", placeholder="BEZA-2026..."
    )
    if st.button("Check Status"):
      df_check = load_submissions(CSV_FILE)
      if not df_check.empty and "App_Ref_No" in df_check.columns:
        match = df_check[df_check["App_Ref_No"] == track_code]
        if not match.empty:
          row = match.iloc[0]
          status = row.get("Status", "Under Evaluation")
          st.success(
              f"✅ Status: **{status}**\n\n"
              f"• **Owner:** {row['Owner_Name']}\n"
              f"• **Module:** {row['Module']}\n"
              f"• **Filing Date:** {row['Timestamp']}"
          )
        else:
          st.error("❌ Reference number not found in gateway records.")
      else:
        st.info("No records in system yet.")

    st.markdown("---")
    st.markdown("### 📥 Document Center")
    st.write("Download official blank templates for offline encoding:")

    target_file = FILENAME_MAP.get(selected_form)
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

    if st.session_state.admin_authenticated:
      st.success("Admin Session Active")
      if st.button("🔒 Logout from Admin"):
        st.session_state.admin_authenticated = False
        st.rerun()
    else:
      admin_toggle = st.checkbox("Access Official Review Panel")
      if admin_toggle:
        admin_pin = st.text_input("Enter Official Access PIN", type="password")
        if admin_pin:
          if verify_admin_pin(admin_pin):
            st.session_state.admin_authenticated = True
            st.success("Access Granted.")
            st.rerun()
          else:
            st.error("Invalid security PIN.")

    st.markdown("---")
    st.markdown("### ⚖️ ARTA Compliance")
    st.info(
        "Streamlined e-submission portal designed for efficient technical"
        " evaluation and transparent processing cycles."
    )

  return selected_form


selected_form = render_sidebar()


# ==========================================
# 7. PORTAL VIEW 2: ADMIN REVIEW DASHBOARD
# ==========================================
def render_admin_dashboard() -> None:
  """Renders the secure administrative review dashboard for managing applications."""
  st.markdown("### 🛡️ BEZA Official Evaluation & Review Dashboard")
  st.write(
      "Review incoming applicant submissions, inspect/download uploaded files,"
      " update evaluation status, edit records, or process audit logs."
  )

  df_submissions = load_submissions(CSV_FILE)

  if df_submissions.empty:
    st.info("No application submissions recorded in the database yet.")
    return

  # Metrics Overview
  col_m1, col_m2, col_m3 = st.columns(3)
  with col_m1:
    st.metric("Total Submissions", len(df_submissions))
  with col_m2:
    total_est_cost = (
        df_submissions["Estimated_Cost"].sum()
        if "Estimated_Cost" in df_submissions
        else 0.0
    )
    st.metric("Total Project Portfolio", f"₱{total_est_cost:,.2f}")
  with col_m3:
    pending_count = (
        len(
            df_submissions[
                df_submissions["Status"] == "Under Evaluation"
            ]
        )
        if "Status" in df_submissions
        else 0
    )
    st.metric("Pending Evaluations", pending_count)

  st.markdown("---")
  st.markdown("### 📊 Submissions Master Registry")
  st.dataframe(df_submissions, use_container_width=True)

  st.markdown("---")
  st.markdown("### 🔍 Inspect, Update Status & Download Files")

  row_indices = list(range(len(df_submissions)))
  selected_idx = st.selectbox(
      "Select Row Index to Inspect",
      row_indices,
      format_func=lambda x: f"Row {x} - {df_submissions.loc[x, 'Owner_Name']} ({df_submissions.loc[x, 'App_Ref_No']}) [{df_submissions.loc[x, 'Status']}]",
  )

  current_row = df_submissions.loc[selected_idx]

  col_info1, col_info2 = st.columns(2)
  with col_info1:
    st.write(f"**Applicant:** {current_row['Owner_Name']}")
    st.write(f"**Tracking Ref:** `{current_row['App_Ref_No']}`")
    st.write(f"**Contact Number:** {current_row['Contact_No']}")
    st.write(f"**Current Module:** {current_row['Module']}")
  with col_info2:
    current_status = current_row.get("Status", "Under Evaluation")
    new_status = st.selectbox(
        "Update Application Status",
        ["Under Evaluation", "Approved", "Pending Requirements"],
        index=(
            ["Under Evaluation", "Approved", "Pending Requirements"].index(
                current_status
            )
            if current_status
            in ["Under Evaluation", "Approved", "Pending Requirements"]
            else 0
        ),
        key=f"status_select_{selected_idx}",
    )
    if new_status != current_status:
      df_submissions.loc[selected_idx, "Status"] = new_status
      save_submissions(df_submissions, CSV_FILE)
      st.success(f"Status updated to **{new_status}** successfully!")
      st.rerun()

  # Document inspection download buttons
  col_f1, col_f2 = st.columns(2)
  with col_f1:
    form_path = current_row.get("Form_Path", "")
    if isinstance(form_path, str) and os.path.exists(form_path):
      with open(form_path, "rb") as f:
        st.download_button(
            label="📥 Download Submitted Application Form",
            data=f,
            file_name=os.path.basename(form_path),
            mime="application/pdf",
            key=f"dl_form_{selected_idx}",
        )
    else:
      st.info("Application form file not found on server storage.")

  with col_f2:
    plans_path = current_row.get("Plans_Path", "")
    if isinstance(plans_path, str) and os.path.exists(plans_path):
      with open(plans_path, "rb") as f:
        st.download_button(
            label="📥 Download Engineering Plans",
            data=f,
            file_name=os.path.basename(plans_path),
            mime="application/pdf",
            key=f"dl_plans_{selected_idx}",
        )
    else:
      st.info("Engineering plans file not found on server storage.")

  st.markdown("---")
  st.markdown("### ⚙️ Manage / Edit / Delete Submission Record")
  col_edit, col_del = st.columns(2)

  with col_edit:
    with st.form("edit_form"):
      edit_ref = st.text_input(
          "Application Reference No.", value=str(current_row["App_Ref_No"])
      )
      edit_owner = st.text_input(
          "Owner Name", value=str(current_row["Owner_Name"])
      )
      edit_contact = st.text_input(
          "Contact No.", value=str(current_row["Contact_No"])
      )
      edit_cost = st.number_input(
          "Estimated Cost (PHP)", value=float(current_row["Estimated_Cost"])
      )
      edit_area = st.number_input(
          "Floor Area (sq. m.)", value=float(current_row["Floor_Area_Sqm"])
      )
      save_changes = st.form_submit_button("💾 Save Record Changes")

    if save_changes:
      df_submissions.loc[selected_idx, "App_Ref_No"] = edit_ref
      df_submissions.loc[selected_idx, "Owner_Name"] = edit_owner
      df_submissions.loc[selected_idx, "Contact_No"] = edit_contact
      df_submissions.loc[selected_idx, "Estimated_Cost"] = edit_cost
      df_submissions.loc[selected_idx, "Floor_Area_Sqm"] = edit_area
      if save_submissions(df_submissions, CSV_FILE):
        st.success(
            f"✅ Row {selected_idx} successfully updated! Refreshing view..."
        )
        st.rerun()

  with col_del:
    st.warning(
        "⚠️ Deleting a record is permanent and removes it from the regulatory"
        " audit log."
    )
    if st.button(
        "🗑️ Delete This Record Permanently",
        type="primary",
        key="delete_btn",
    ):
      df_submissions = df_submissions.drop(selected_idx).reset_index(drop=True)
      if save_submissions(df_submissions, CSV_FILE):
        st.success(
            f"🗑️ Row {selected_idx} successfully deleted! Refreshing view..."
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


# ==========================================
# 8. PORTAL VIEW 1: PUBLIC SUBMISSION FORM
# ==========================================
def render_public_submission_form(module_name: str) -> None:
  """Renders the secure applicant submission form for public filers."""
  st.markdown(f"### Active Module: **{module_name}**")
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
    contact_no = col_d.text_input("Official Contact Number / Mobile No. *")

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
    # Validation checks
    if (
        not owner_name
        or not tin
        or not location
        or not contact_no
        or floor_area <= 0
        or estimated_cost <= 0
        or not uploaded_application_form
        or not uploaded_plans
    ):
      st.error(
          "⚠️ Incomplete Submission: Please ensure all mandatory fields (*),"
          " valid project metrics, and required PDF documents are attached."
      )
    else:
      # Generate secure tracking reference and sanitize file paths to prevent collisions
      auto_ref_no = f"BEZA-{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"

      safe_form_name = sanitize_filename(uploaded_application_form.name)
      form_filename = f"{auto_ref_no}_form_{safe_form_name}"
      form_path = os.path.join(UPLOAD_DIR, form_filename)
      with open(form_path, "wb") as f:
        f.write(uploaded_application_form.getbuffer())

      safe_plans_name = sanitize_filename(uploaded_plans.name)
      plans_filename = f"{auto_ref_no}_plans_{safe_plans_name}"
      plans_path = os.path.join(UPLOAD_DIR, plans_filename)
      with open(plans_path, "wb") as f:
        f.write(uploaded_plans.getbuffer())

      sub_data = {
          "Timestamp": [pd.Timestamp.now()],
          "Module": [module_name],
          "App_Ref_No": [auto_ref_no],
          "Category": [proj_category],
          "Owner_Name": [owner_name],
          "TIN": [tin],
          "Enterprise": [enterprise_name],
          "Contact_No": [contact_no],
          "Floor_Area_Sqm": [floor_area],
          "Estimated_Cost": [estimated_cost],
          "Storeys": [storeys],
          "Materials": [materials],
          "Location": [location],
          "Form_File": [uploaded_application_form.name],
          "Form_Path": [form_path],
          "Plans_File": [uploaded_plans.name],
          "Plans_Path": [plans_path],
          "Status": ["Under Evaluation"],
      }

      df_new = pd.DataFrame(sub_data)
      df_existing = load_submissions(CSV_FILE)
      df_combined = pd.concat([df_existing, df_new], ignore_index=True)

      if save_submissions(df_combined, CSV_FILE):
        st.success(
            f"✅ **Transmission Successful!** Your application package has been"
            f" successfully received by BEZA.\n\n"
            f"📌 **System-Generated Tracking Reference No.:** `{auto_ref_no}`\n"
            f"📱 **SMS / Contact Dispatch Notice:** Confirmation logged for contact"
            f" number `{contact_no}`.\n\n"
            f"🏗️ **Declared Area:** {floor_area:,.2f} sq. m. | 💰 **Estimated"
            f" Cost:** ₱{estimated_cost:,.2f}\n\n"
            "*(Please save your tracking reference number to check your status"
            " anytime via the sidebar lookup tool.)*"
        )
        st.balloons()


# ==========================================
# 9. MAIN ROUTING CONTROLLER
# ==========================================
if st.session_state.admin_authenticated:
  render_admin_dashboard()
else:
  render_public_submission_form(selected_form)
