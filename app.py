"""
Bangsamoro Economic Zone Authority (BEZA) - Electronic Permitting & E-Services Portal
Office of the Building Official | RA 11032 ARTA Compliant
"""

from datetime import datetime
import hashlib
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import pandas as pd
import requests
import streamlit as st

# ==========================================
# 1. CONSTANTS & CLOUDFLARE R2 CONFIGURATION
# ==========================================
CSV_FILE: str = "submissions.csv"
LOGO_FILENAME: str = "BEZA-LOGO-Copy-300x300.png"
BUCKET_NAME: str = "beza-permits-bucket"

# Cloudflare R2 S3-Compatible Credentials (safely loaded from Streamlit TOML secrets)
R2_ENDPOINT_URL: str = st.secrets.get(
    "R2_ENDPOINT_URL",
    "https://2859e7a87dd0372ba85ff9d2df8e22c8.r2.cloudflarestorage.com",
)
R2_ACCESS_KEY_ID: str = st.secrets.get(
    "R2_ACCESS_KEY_ID", "ce61aadbcb4f8c3be0a35c14b1b69ece"
)
R2_SECRET_ACCESS_KEY: str = st.secrets.get(
    "R2_SECRET_ACCESS_KEY",
    "0c8b60d8bf0a4def6ed9d063fdfec0680c9b51235b042558c7634c08395177bb",
)

# httpSMS Gateway Configuration
HTTPSMS_API_KEY: str = st.secrets.get(
    "HTTPSMS_API_KEY",
    "pk_RM08tumlmQrM-x1ESRcuM6iIZB3sn8luzH4ZP47DNl8gCNkGOtA7mmZkI--6miSb",
)
HTTPSMS_SENDER_PHONE: str = st.secrets.get(
    "HTTPSMS_SENDER_PHONE", "+639293367787"
)

AGENCY_STAGES: List[str] = [
    "BEZA - Office of the Building Official (Intake & Pre-Check)",
    "MENRE - Ministry of Environment, Natural Resources & Energy",
    "MOLE - Ministry of Labor and Employment",
    "BFP - Bureau of Fire Protection (Fire Safety Evaluation)",
    "BEZA OBO - Final Review & Permit Issuance",
    "Approved & Ready for Release",
]

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
    "Form_Key",
    "Plans_File",
    "Plans_Key",
    "Computations_File",
    "Computations_Key",
    "Clearances_File",
    "Clearances_Key",
    "Status",
    "Current_Agency_Stage",
]

FILENAME_MAP: Dict[str, str] = {
    "BUILDING PERMIT": "BEZA.EESSU.F.001 BUILDING PERMIT.pdf",
    "BEZA.EESSU.F.002 MECHANICAL PERMIT": (
        "BEZA.EESSU.F.002 MECHANICAL PERMIT.pdf"
    ),
    "ELECTRICAL PERMIT": "BEZA.EESSU.F.003 ELECTRICAL PERMIT.pdf",
    "ELECTRONICS PERMIT": "BEZA.EESSU.F.004 ELECTRONICS PERMIT.pdf",
    "FENCING PERMIT": "BEZA.EESSU.F.005 FENCING PERMIT.pdf",
    "SANITARY AND PLUMBING PERMIT": (
        "BEZA.EESSU.F.006 SANITARY AND PLUMBING PERMIT.pdf"
    ),
    "Mechanical Data Sheet": "BEZA.EESSU.F.007 Mechanical Data Sheet.pdf",
    "Electrical Data Sheet": "BEZA.EESSU.F.008 Electrical Data Sheet.pdf",
    "Electronics Data Sheet": "BEZA.EESSU.F.009 Electronics Data Sheet.pdf",
    "BEZA DEMOLITION PERMIT": "BEZA DEMOLITION PERMIT FORM.pdf",
    "BEZA SIGN & SIGN STRUCTURE PERMIT": (
        "BEZA SIGN AND SIGN STRUCTURE PERMIT FORM MERGED.pdf"
    ),
    "Excavation & Ground Preparation Permit": (
        "Application-Form-Excavation-Ground-Preparation-and-Soil-Investigation.pdf"
    ),
    "Building Permit Checklist": "building permit.pdf",
    "Anti Graft": "anti_graft_1.doc",
}

# Page Setup
st.set_page_config(
    page_title="BEZA Electronic Permitting Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# 2. WRAPPIXEL EXECUTIVE HIGH-CONTRAST CSS
# ==========================================
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

        /* Global Font & High Contrast */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #0F172A !important;
        }

        /* Top Page Alignment & Chrome Clean-Up */
        .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 3rem !important;
            max-width: 1280px;
        }
        
        header[data-testid="stHeader"] {
            display: none !important;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stDecoration"] {display: none;}

        /* WrapPixel Executive Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, #0A2540 0%, #006A35 100%);
            padding: 24px 32px;
            border-radius: 12px;
            box-shadow: 0 8px 24px -4px rgba(0, 106, 53, 0.25);
            color: #FFFFFF !important;
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 24px;
            border-bottom: 4px solid #FFC72C;
        }
        .hero-title {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin: 0;
            color: #FFFFFF !important;
        }
        .hero-subtitle {
            font-size: 13px;
            color: #E2E8F0 !important;
            margin-top: 4px;
            font-weight: 500;
        }
        .arta-badge {
            background: rgba(255, 255, 255, 0.18);
            padding: 4px 10px;
            border-radius: 16px;
            font-size: 11px;
            font-weight: 700;
            border: 1px solid rgba(255, 255, 255, 0.3);
            display: inline-block;
            margin-top: 8px;
            color: #FFC72C !important;
        }

        /* Module & Section Card Styling */
        .module-header {
            background: #F8FAFC;
            border-left: 6px solid #006A35;
            border-top: 1px solid #E2E8F0;
            border-right: 1px solid #E2E8F0;
            border-bottom: 1px solid #E2E8F0;
            padding: 14px 20px;
            border-radius: 0 8px 8px 0;
            font-size: 18px;
            font-weight: 700;
            color: #0F172A !important;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }

        .info-card {
            background-color: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-radius: 8px;
            padding: 16px 20px;
            color: #14532D !important;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 24px;
        }

        label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stFileUploader label, p, span {
            color: #0F172A !important;
            font-weight: 600 !important;
        }

        div[data-testid="stForm"] {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 28px;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.03);
        }

        .section-header {
            font-size: 14px;
            font-weight: 800;
            color: #0A2540 !important;
            margin-top: 15px;
            margin-bottom: 18px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            border-bottom: 2px solid #F1F5F9;
            padding-bottom: 8px;
        }

        section[data-testid="stSidebar"] {
            background-color: #F8FAFC;
            border-right: 1px solid #E2E8F0;
        }
        
        div.stButton > button[kind="primary"], .stFormSubmitButton > button {
            background: linear-gradient(135deg, #006A35 0%, #004D26 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 12px 24px !important;
            box-shadow: 0 4px 12px rgba(0, 106, 53, 0.25) !important;
            width: 100%;
        }

        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-top: 4px solid #006A35;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            text-align: center;
        }
        .metric-val {
            font-size: 28px;
            font-weight: 800;
            color: #0A2540 !important;
        }
        .metric-lbl {
            font-size: 12px;
            color: #64748B !important;
            font-weight: 700;
            text-transform: uppercase;
            margin-top: 4px;
        }

        .badge {
            padding: 5px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            display: inline-block;
        }
        .badge-eval { background: #FEF3C7; color: #92400E !important; border: 1px solid #FCD34D; }
        .badge-approved { background: #D1FAE5; color: #065F46 !important; border: 1px solid #6EE7B7; }
        .badge-pending { background: #FEE2E2; color: #991B1B !important; border: 1px solid #FCA5A5; }
    </style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 3. UTILITIES & HTTPSMS GATEWAY
# ==========================================
def get_r2_client():
  return boto3.client(
      "s3",
      endpoint_url=R2_ENDPOINT_URL,
      aws_access_key_id=R2_ACCESS_KEY_ID,
      aws_secret_access_key=R2_SECRET_ACCESS_KEY,
      region_name="auto",
      config=Config(signature_version="s3v4"),
  )


def upload_file_to_r2(file_obj, object_key: str) -> bool:
  try:
    s3 = get_r2_client()
    s3.upload_fileobj(file_obj, BUCKET_NAME, object_key)
    return True
  except ClientError as e:
    st.error(f"❌ Cloud Storage Upload Error: {e}")
    return False


def get_r2_download_link(object_key: str, expiration: int = 3600) -> Optional[str]:
  try:
    s3 = get_r2_client()
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": object_key},
        ExpiresIn=expiration,
    )
    return url
  except ClientError as e:
    st.error(f"❌ Failed to generate secure download link: {e}")
    return None


def send_sms_notification(to_phone: str, message: str) -> bool:
  if not HTTPSMS_API_KEY or not HTTPSMS_SENDER_PHONE:
    return False

  url = "https://api.httpsms.com/v1/messages/send"
  headers = {
      "x-api-key": HTTPSMS_API_KEY,
      "Accept": "application/json",
      "Content-Type": "application/json",
  }
  payload = {"content": message, "from": HTTPSMS_SENDER_PHONE, "to": to_phone}

  try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    return response.status_code in [200, 201]
  except Exception as e:
    st.warning(f"⚠️ SMS Gateway Warning: {e}")
    return False


def sanitize_filename(filename: str) -> str:
  if not filename:
    return "unnamed_attachment.pdf"
  base_name = os.path.basename(filename)
  cleaned = re.sub(r"[^a-zA-Z0-9._-]", "_", base_name)
  return cleaned if cleaned else "unnamed_attachment.pdf"


def hash_string(input_str: str) -> str:
  return hashlib.sha256(input_str.encode("utf-8")).hexdigest()


def verify_admin_pin(entered_pin: str) -> bool:
  default_hash = hash_string("BEZA2026")
  stored_hash = st.secrets.get("ADMIN_PIN_HASH", default_hash)
  return hash_string(entered_pin) == stored_hash


def load_submissions(csv_path: str) -> pd.DataFrame:
  if not os.path.exists(csv_path):
    return pd.DataFrame(columns=REQUIRED_COLUMNS)

  try:
    df = pd.read_csv(csv_path)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
      for col in missing_cols:
        if col == "Status":
          df[col] = "Under Evaluation"
        elif col == "Current_Agency_Stage":
          df[col] = AGENCY_STAGES[0]
        else:
          df[col] = None
    return df
  except Exception as e:
    st.error(f"⚠️ Warning: Submissions data store issue. ({e})")
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def save_submissions(df: pd.DataFrame, csv_path: str) -> bool:
  try:
    df.to_csv(csv_path, index=False)
    return True
  except Exception as e:
    st.error(f"❌ Critical I/O Error: Failed to persist database. ({e})")
    return False


if "admin_authenticated" not in st.session_state:
  st.session_state.admin_authenticated = False

if "accepted_guidelines" not in st.session_state:
  st.session_state.accepted_guidelines = False


# ==========================================
# 4. UI COMPONENTS & RENDER FUNCTIONS
# ==========================================
def render_header() -> None:
  logo_html = ""
  if os.path.exists(LOGO_FILENAME):
    with open(LOGO_FILENAME, "rb") as img_file:
      import base64

      encoded = base64.b64encode(img_file.read()).decode("utf-8")
    logo_html = f'<img src="data:image/png;base64,{encoded}" style="height: 65px; width: auto; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));">'
  else:
    logo_html = '<div style="font-size: 40px;">🏛️</div>'

  st.markdown(
      f"""
      <div class="hero-banner">
          <div>{logo_html}</div>
          <div>
              <div class="hero-title">BANGSAMORO ECONOMIC ZONE AUTHORITY</div>
              <div class="hero-subtitle">Office of the Building Official — One-Stop Shop Cloud Permitting Portal</div>
              <div class="arta-badge">⚡ RA 11032 ARTA Compliant • Cloudflare R2 & httpSMS Active</div>
          </div>
      </div>
      """,
      unsafe_allow_html=True,
  )


def render_sidebar() -> str:
  with st.sidebar:
    if os.path.exists(LOGO_FILENAME):
      st.image(LOGO_FILENAME, width=120)

    st.markdown("### 📋 Regulatory Modules")
    selected_form = st.selectbox(
        "Select Application / Permit Form", list(FILENAME_MAP.keys())
    )

    st.markdown("---")
    st.markdown("### 🔍 Track Application Location")
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
          current_stage = row.get("Current_Agency_Stage", AGENCY_STAGES[0])
          timestamp_filled = row.get("Timestamp", "N/A")

          badge_class = "badge-eval"
          if status == "Approved":
            badge_class = "badge-approved"
          elif status == "Pending Requirements":
            badge_class = "badge-pending"

          st.markdown(
              f"""
              <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:14px; border-radius:8px; margin-top:8px; box-shadow:0 2px 6px rgba(0,0,0,0.02);">
                  <div style="font-size:11px; color:#64748B; font-weight:700;">Submitted At:</div>
                  <div style="font-size:12px; font-weight:700; color:#0F172A; margin-bottom:6px;">{timestamp_filled}</div>
                  <div style="font-size:11px; color:#64748B; font-weight:700;">Overall Status:</div>
                  <div style="margin-top:2px; margin-bottom:6px;"><span class="badge {badge_class}">{status}</span></div>
                  <div style="font-size:11px; color:#64748B; font-weight:700;">📍 Current Agency Location:</div>
                  <div style="font-size:12px; font-weight:700; color:#0A2540; margin-top:2px;">{current_stage}</div>
                  <hr style="margin:8px 0; border:none; border-top:1px solid #F1F5F9;">
                  <div style="font-size:12px; color:#0F172A;"><b>Owner:</b> {row['Owner_Name']}</div>
                  <div style="font-size:12px; color:#0F172A;"><b>Module:</b> {row['Module']}</div>
              </div>
              """,
              unsafe_allow_html=True,
          )
        else:
          st.error("❌ Reference number not found.")
      else:
        st.info("No records in system yet.")

    st.markdown("---")
    st.markdown("### 📥 Document Center")
    st.caption("Download official blank templates for offline encoding:")

    target_file = FILENAME_MAP.get(selected_form)
    if target_file and os.path.exists(target_file):
      with open(target_file, "rb") as pdf_file:
        st.download_button(
            label="📄 Download Official PDF Form",
            data=pdf_file,
            file_name=target_file,
            mime="application/pdf",
        )
    else:
      st.warning("Template file not found in repository.")

    st.markdown("---")
    st.markdown("### 🔒 BEZA One-Stop Shop Admin")

    if st.session_state.admin_authenticated:
      st.success("Admin Session Active")
      if st.button("🔒 Logout from Admin"):
        st.session_state.admin_authenticated = False
        st.rerun()
    else:
      admin_toggle = st.checkbox("Access Review Panel")
      if admin_toggle:
        admin_pin = st.text_input("Enter Access PIN", type="password")
        if admin_pin:
          if verify_admin_pin(admin_pin):
            st.session_state.admin_authenticated = True
            st.success("Access Granted.")
            st.rerun()
          else:
            st.error("Invalid security PIN.")

    st.markdown("---")
    st.caption("BEZA Cloud Portal • Powered by Cloudflare R2 & httpSMS")

  return selected_form


def render_admin_dashboard() -> None:
  st.markdown(
      '<div class="module-header">🛡️ BEZA One-Stop Shop Cloud Review'
      " Dashboard</div>",
      unsafe_allow_html=True,
  )

  df_submissions = load_submissions(CSV_FILE)

  if df_submissions.empty:
    st.info("No application submissions recorded in the database yet.")
    return

  col_m1, col_m2, col_m3 = st.columns(3)
  with col_m1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-val">{len(df_submissions)}</div>
            <div class="metric-lbl">Total Submissions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
  with col_m2:
    total_est_cost = (
        df_submissions["Estimated_Cost"].sum()
        if "Estimated_Cost" in df_submissions
        else 0.0
    )
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-val">₱{total_est_cost:,.2f}</div>
            <div class="metric-lbl">Total Portfolio Value</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-val" style="color: #D97706;">{pending_count}</div>
            <div class="metric-lbl">Active Processing Files</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)
  st.markdown("### 📊 Submissions Master Registry (Interactive)")
  st.caption(
      "💡 **Direct Editing & Row Deletion Enabled:** Click cell values to edit"
      " directly, or select row checkboxes and press **Delete** on your"
      " keyboard to remove records."
  )

  edited_df = st.data_editor(
      df_submissions,
      num_rows="dynamic",
      use_container_width=True,
      key="master_registry_editor",
  )

  if not edited_df.equals(df_submissions):
    if save_submissions(edited_df, CSV_FILE):
      st.success("✅ Master Registry updated and saved successfully!")
      st.rerun()

  st.markdown("---")
  st.markdown("### 🔀 Inter-Agency Routing & SMS Notification Inspector")

  if not edited_df.empty:
    row_indices = list(range(len(edited_df)))
    selected_idx = st.selectbox(
        "Select Row Index to Inspect & Route",
        row_indices,
        format_func=lambda x: f"Row {x} - {edited_df.loc[x, 'Owner_Name']} [{edited_df.loc[x, 'App_Ref_No']}]",
    )

    current_row = edited_df.loc[selected_idx]

    # --- Sub-navigation / Action Tabs ---
    tab_inspect, tab_print = st.tabs(
        ["📝 Routing & Attachments", "🖨️ Printable Receiving Slip"]
    )

    with tab_inspect:
      col_info1, col_info2 = st.columns(2)
      with col_info1:
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:18px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,0.02);">
                <div style="font-size:13px; color:#0F172A; margin-bottom:6px;"><b>Active Timestamp:</b> <code>{current_row['Timestamp']}</code></div>
                <div style="font-size:13px; color:#0F172A; margin-bottom:6px;"><b>Applicant Name:</b> {current_row['Owner_Name']}</div>
                <div style="font-size:13px; color:#0F172A; margin-bottom:6px;"><b>Tracking Ref:</b> <code>{current_row['App_Ref_No']}</code></div>
                <div style="font-size:13px; color:#0F172A; margin-bottom:6px;"><b>Contact No:</b> {current_row['Contact_No']}</div>
                <div style="font-size:13px; color:#0F172A;"><b>Module Category:</b> {current_row['Module']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
      with col_info2:
        current_stage = current_row.get("Current_Agency_Stage", AGENCY_STAGES[0])
        new_stage = st.selectbox(
            "Update Current Agency / Processing Stage",
            AGENCY_STAGES,
            index=(
                AGENCY_STAGES.index(current_stage)
                if current_stage in AGENCY_STAGES
                else 0
            ),
            key=f"agency_stage_{selected_idx}",
        )

        current_status = current_row.get("Status", "Under Evaluation")
        new_status = st.selectbox(
            "Update Overall Status",
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

        send_sms_flag = st.checkbox(
            "📱 Send SMS update to applicant via httpSMS", value=True
        )

        if new_stage != current_stage or new_status != current_status:
          edited_df.loc[selected_idx, "Current_Agency_Stage"] = new_stage
          edited_df.loc[selected_idx, "Status"] = new_status
          save_submissions(edited_df, CSV_FILE)

          if send_sms_flag and current_row["Contact_No"]:
            sms_msg = (
                f"BEZA Notice: Your permit application ({current_row['App_Ref_No']}) status is now '{new_status}'. "
                f"Current Stage: {new_stage}."
            )
            success_sms = send_sms_notification(
                str(current_row["Contact_No"]), sms_msg
            )
            if success_sms:
              st.success(
                  f"✅ Updated route and dispatched httpSMS alert to"
                  f" {current_row['Contact_No']}!"
              )
            else:
              st.warning(
                  "⚠️ Database updated, but httpSMS gateway failed to dispatch"
                  " SMS (check API key & gateway phone balance/load)."
              )
          else:
            st.success(
                f"✅ Updated agency route to **{new_stage}** successfully!"
            )
          st.rerun()

      st.markdown("<br>", unsafe_allow_html=True)
      
      # --- Full 4-Column Admin Download Suite ---
      col_f1, col_f2, col_f3, col_f4 = st.columns(4)

      with col_f1:
        form_key = current_row.get("Form_Key", "")
        if pd.notna(form_key) and form_key:
          form_url = get_r2_download_link(str(form_key))
          if form_url:
            btn_html = f'<a href="{form_url}" target="_blank"><button style="background:#006A35; color:white; border:none; padding:12px 10px; border-radius:8px; font-weight:700; cursor:pointer; width:100%; font-size:12px;">Download Application Form</button></a>'
            st.markdown(btn_html, unsafe_allow_html=True)
        else:
          st.info("No Form attached")

      with col_f2:
        plans_key = current_row.get("Plans_Key", "")
        if pd.notna(plans_key) and plans_key:
          plans_url = get_r2_download_link(str(plans_key))
          if plans_url:
            btn_html = f'<a href="{plans_url}" target="_blank"><button style="background:#0A2540; color:white; border:none; padding:12px 10px; border-radius:8px; font-weight:700; cursor:pointer; width:100%; font-size:12px;">Download Engineering Plans</button></a>'
            st.markdown(btn_html, unsafe_allow_html=True)
        else:
          st.info("No Plans attached")

      with col_f3:
        comp_key = current_row.get("Computations_Key", "")
        if pd.notna(comp_key) and str(comp_key).strip():
          comp_url = get_r2_download_link(str(comp_key))
          if comp_url:
            btn_html = f'<a href="{comp_url}" target="_blank"><button style="background:#D97706; color:white; border:none; padding:12px 10px; border-radius:8px; font-weight:700; cursor:pointer; width:100%; font-size:12px;">Download Computations</button></a>'
            st.markdown(btn_html, unsafe_allow_html=True)
        else:
          st.info("No Computations")

      with col_f4:
        clear_key = current_row.get("Clearances_Key", "")
        if pd.notna(clear_key) and str(clear_key).strip():
          clear_url = get_r2_download_link(str(clear_key))
          if clear_url:
            btn_html = f'<a href="{clear_url}" target="_blank"><button style="background:#4F46E5; color:white; border:none; padding:12px 10px; border-radius:8px; font-weight:700; cursor:pointer; width:100%; font-size:12px;">Download Clearances / ZIP</button></a>'
            st.markdown(btn_html, unsafe_allow_html=True)
        else:
          st.info("No Clearances")

    with tab_print:
      st.markdown("### 🖨️ Official Receiving Record & Claim Slip Preview")
      st.caption("This printable document represents the official file receipt by the BEZA Records Officer for the selected applicant.")

      slip_html = f"""
      <!DOCTYPE html>
      <html>
      <head>
      <style>
          @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
          body {{
              font-family: 'Plus Jakarta Sans', sans-serif;
              background-color: #ffffff;
              color: #0F172A;
              margin: 0;
              padding: 10px;
          }}
          .printable-slip-card {{
              background: #FFFFFF;
              border: 2px dashed #006A35;
              padding: 24px;
              border-radius: 10px;
              max-width: 600px;
              margin: 0 auto;
              box-shadow: 0 4px 12px rgba(0,0,0,0.05);
          }}
      </style>
      </head>
      <body>
      <div class="printable-slip-card">
          <div style="text-align: center; font-weight: 800; font-size: 14px; letter-spacing: 0.5px; color: #0F172A;">BANGSAMORO ECONOMIC ZONE AUTHORITY</div>
          <div style="text-align: center; font-size: 11px; font-weight: 700; color: #006A35; margin-bottom: 12px;">OFFICE OF THE BUILDING OFFICIAL — RECORDS & INTAKE SECTION</div>
          <div style="text-align: center; font-weight: 700; font-size: 13px; text-decoration: underline; margin-bottom: 15px; color: #0F172A;">OFFICIAL APPLICATION RECEIVING & CLAIM SLIP</div>
          
          <table style="width: 100%; font-size: 12px; margin-bottom: 15px; border-collapse: collapse;">
              <tr>
                  <td style="padding: 4px 0; color: #64748B; width: 35%;"><b>Tracking No:</b></td>
                  <td style="padding: 4px 0; font-weight: 700; color: #0A2540;">{current_row['App_Ref_No']}</td>
              </tr>
              <tr>
                  <td style="padding: 4px 0; color: #64748B;"><b>Applicant / Owner:</b></td>
                  <td style="padding: 4px 0; font-weight: 700; color: #0F172A;">{current_row['Owner_Name']}</td>
              </tr>
              <tr>
                  <td style="padding: 4px 0; color: #64748B;"><b>Module / Permit:</b></td>
                  <td style="padding: 4px 0; font-weight: 600; color: #0F172A;">{current_row['Module']}</td>
              </tr>
              <tr>
                  <td style="padding: 4px 0; color: #64748B;"><b>Location:</b></td>
                  <td style="padding: 4px 0; font-weight: 600; color: #0F172A;">{current_row['Location']}</td>
              </tr>
              <tr>
                  <td style="padding: 4px 0; color: #64748B;"><b>Floor Area / Cost:</b></td>
                  <td style="padding: 4px 0; font-weight: 600; color: #0F172A;">{current_row['Floor_Area_Sqm']} sq.m. | ₱{current_row['Estimated_Cost']:,.2f}</td>
              </tr>
              <tr>
                  <td style="padding: 4px 0; color: #64748B;"><b>Date Filed:</b></td>
                  <td style="padding: 4px 0; font-weight: 600; color: #0F172A;">{current_row['Timestamp']}</td>
              </tr>
          </table>
          
          <hr style="border: none; border-top: 1px dashed #CBD5E1; margin: 12px 0;">
          
          <div style="font-size: 11px; margin-bottom: 20px; color: #0F172A;">
              <b>Received By (Records Officer):</b><br>
              <span style="font-size: 12px; font-weight: 700; color: #006A35;">BEZA OBO Records & Intake Desk</span>
          </div>
          
          <div style="font-size: 10px; color: #64748B; font-style: italic; line-height: 1.4;">
              <b>Note:</b> Please present this original claim slip to claim evaluation status updates, assessment findings, and approved permits. Xerox or digital snapshots are subject to verification.
          </div>
      </div>
      </body>
      </html>
      """
      
      # FIX: Rendered cleanly using st.components.v1.html to prevent raw text tags
      st.components.v1.html(slip_html, height=400, scrolling=False)
      st.markdown("<br>", unsafe_allow_html=True)
      
      col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
      with col_p2:
        if st.button("🖨️ Print Receiving Claim Slip", type="primary"):
          st.components.v1.html(
              """
              <script>
                  window.parent.print();
              </script>
              """,
              height=0,
          )

  st.markdown("---")
  csv_bytes = edited_df.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Export Complete Audit Log (CSV)",
      data=csv_bytes,
      file_name="BEZA_Audit_Logs.csv",
      mime="text/csv",
  )


def render_public_submission_form(module_name: str) -> None:
  st.markdown(
      f'<div class="module-header">Active Module: <b>{module_name}</b></div>',
      unsafe_allow_html=True,
  )

  st.markdown(
      """
      <div class="info-card">
          <b>📌 One-Stop Shop Cloud Workflow Instructions:</b><br>
          1. Download the official blank PDF template from the sidebar document center.<br>
          2. Complete the form and compile your required engineering plans and technical drawings.<br>
          3. Transmit your complete digital package below. Files are uploaded securely to <b>Cloudflare R2 cloud storage</b> and applicants receive automated <b>httpSMS notifications</b>.
      </div>
      """,
      unsafe_allow_html=True,
  )

  with st.form("technical_submission_form"):
    st.markdown(
        '<div class="section-header">📌 1. Project Identification & Applicant'
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

    col_c, col_d1, col_d2 = st.columns([2, 1, 2])
    enterprise_name = col_c.text_input(
        "Registered Enterprise Name (if applicable)"
    )

    country_code = col_d1.selectbox(
        "Country Code *",
        [
            "🇵🇭 Philippines (+63)",
            "🇺🇸 USA / Canada (+1)",
            "🇸🇬 Singapore (+65)",
            "🇦🇪 UAE (+971)",
            "🇸🇦 Saudi Arabia (+966)",
            "🇯🇵 Japan (+81)",
            "🇲🇾 Malaysia (+60)",
        ],
        index=0,
    )
    prefix = country_code.split("(")[-1].replace(")", "").strip()

    raw_mobile = col_d2.text_input(
        "Mobile No. (e.g., 9171234567) *",
        placeholder="9171234567",
    )
    clean_number = raw_mobile.lstrip("0").strip()
    contact_no = f"{prefix}{clean_number}" if clean_number else ""

    location = st.text_input(
        "Exact Location of Construction / Installation (Zone, Municipality) *"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">📐 2. Engineering Metrics & Cost Estimates'
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
        "Primary Structural Materials", ["Concrete", "Steel", "Wooden", "Mixed"]
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header">📂 3. Technical Document Attachments (PDF /'
        " CAD .dwg Packages / ZIP)</div>",
        unsafe_allow_html=True,
    )

    up_col1, up_col2 = st.columns(2)
    with up_col1:
      uploaded_application_form = st.file_uploader(
          "Upload Accomplished & Signed Official Form (PDF) *", type=["pdf"]
      )
      uploaded_plans = st.file_uploader(
          "Upload Signed & Sealed Engineering Plans / CAD Drawings *",
          type=["pdf", "dwg"],
      )

    with up_col2:
      uploaded_computations = st.file_uploader(
          "Upload Structural / Technical Computations (PDF)", type=["pdf"]
      )
      uploaded_clearances = st.file_uploader(
          "Upload Environmental / Zone Clearances (PDF/ZIP)",
          type=["pdf", "zip"],
      )

    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.form_submit_button(
        "🔒 Securely Transmit Application Package & Dispatch SMS Notice"
    )

  if submitted:
    if (
        not owner_name
        or not tin
        or not location
        or not raw_mobile
        or floor_area <= 0
        or estimated_cost <= 0
        or not uploaded_application_form
        or not uploaded_plans
    ):
      st.error(
          "⚠️ Incomplete Submission: Please fill out all required fields (*)"
          " and attach required files."
      )
    else:
      active_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      auto_ref_no = f"BEZA-{datetime.now().strftime('%Y%m%d%H%M%S')}"

      safe_form_name = sanitize_filename(uploaded_application_form.name)
      form_key = f"uploads/{auto_ref_no}_form_{safe_form_name}"
      form_uploaded = upload_file_to_r2(uploaded_application_form, form_key)

      safe_plans_name = sanitize_filename(uploaded_plans.name)
      plans_key = f"uploads/{auto_ref_no}_plans_{safe_plans_name}"
      plans_uploaded = upload_file_to_r2(uploaded_plans, plans_key)

      comp_file_name = ""
      comp_key = ""
      if uploaded_computations:
        safe_comp_name = sanitize_filename(uploaded_computations.name)
        comp_key = f"uploads/{auto_ref_no}_comp_{safe_comp_name}"
        upload_file_to_r2(uploaded_computations, comp_key)
        comp_file_name = uploaded_computations.name

      clear_file_name = ""
      clear_key = ""
      if uploaded_clearances:
        safe_clear_name = sanitize_filename(uploaded_clearances.name)
        clear_key = f"uploads/{auto_ref_no}_clear_{safe_clear_name}"
        upload_file_to_r2(uploaded_clearances, clear_key)
        clear_file_name = uploaded_clearances.name

      if form_uploaded and plans_uploaded:
        sub_data = {
            "Timestamp": [active_timestamp],
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
            "Form_Key": [form_key],
            "Plans_File": [uploaded_plans.name],
            "Plans_Key": [plans_key],
            "Computations_File": [comp_file_name],
            "Computations_Key": [comp_key],
            "Clearances_File": [clear_file_name],
            "Clearances_Key": [clear_key],
            "Status": ["Under Evaluation"],
            "Current_Agency_Stage": [AGENCY_STAGES[0]],
        }

        df_new = pd.DataFrame(sub_data)
        df_existing = load_submissions(CSV_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)

        if save_submissions(df_combined, CSV_FILE):
          sms_welcome = (
              f"BEZA OBO: Application received! Ref: {auto_ref_no}. "
              f"Status: Under Evaluation. Track online via your ref number."
          )
          sms_sent = send_sms_notification(contact_no, sms_welcome)

          st.success(
              f"✅ **Cloud Transmission & SMS Notice Successful!**\n\n"
              f"⏱️ **Timestamp:** `{active_timestamp}`\n"
              f"📌 **Tracking Ref:** `{auto_ref_no}`\n"
              f"📱 **httpSMS Notification:** "
              f"{'Dispatched successfully to ' + contact_no if sms_sent else 'Gateway not configured or gateway phone lacks load.'}"
          )
          st.balloons()
      else:
        st.error("❌ Failed to upload required files to Cloudflare R2 bucket.")


# ==========================================
# 5. EXECUTION & ROUTING CONTROLLER
# ==========================================
render_header()
selected_form = render_sidebar()

if not st.session_state.admin_authenticated and not st.session_state.accepted_guidelines:
  st.markdown(
      '<div class="module-header">🏛️ BEZA Electronic Permitting Portal — Terms &'
      " Guidelines</div>",
      unsafe_allow_html=True,
  )

  st.markdown(
      """
      <div class="info-card" style="background-color: #F8FAFC; border: 1px solid #CBD5E1; color: #0F172A !important;">
          <b>⚠️ IMPORTANT NOTICE TO ALL APPLICANTS:</b><br>
          Before proceeding with your electronic submission under the National Building Code (NBC), please read and understand the official compliance guidelines below. Click <b>"Continue to Portal"</b> at the bottom to unlock the submission forms.
      </div>
      """,
      unsafe_allow_html=True,
  )

  st.markdown("### GUIDELINES IN THE SUBMISSION OF APPLICATIONS FOR PERMITS UNDER THE NATIONAL BUILDING CODE (NBC):")
  
  guidelines_content = """
**A. PRE-CONSTRUCTION STAGE**
* **Company Registration:** All applications for permits under the National Building Code (NBC) – building, sanitary/plumbing, fencing, electronics, electrical, and mechanical must be in the BEZA company's complete registered company name (as indicated in the BEZA Registration Certificate).
* **Signatures & Authorization:** All applications must be signed by the company owner or authorized representative (in case of a representative, a secretary certificate or authorization letter from the owner is required). Printed name and position of signatory must be indicated in the plans.
* **Professional Seals:** All applications must be signed and sealed by the required professional with valid PRC license and updated PTR. Clear copy of PRC and PTR must be submitted. Dry seal in all plans and documents must be clear and recognizable.
* **Project Title Uniformity:** If the proposed project has several components - civil, sanitary/plumbing, fencing, electrical and mechanical, the same project title will be used in all the plans and documents to be submitted.
* **Simultaneous Submissions:** All plans and documents of the project components must be submitted at the same time – partial submissions will not be accepted.
* **Plan Dimensions:** Required plans are 2 standard size (20"x30") and 1 A3 size.
* **Scaling Rules:** Plans must be drawn in scale as required under the NBC or the biggest possible scale in a 20x30 sheet. If fitting the entire layout in a 20x30 sheet will still result to a smaller scale - sectional details must be provided in scale 1:100. Scale used must be indicated.
* **Gridlines:** All drawings must have gridlines and dimensions.
* **Site Development:** Site development plans must be drawn in scale 1:100 or biggest possible scale in a 20x30 sheet.
* **Project Location Plans:** Project location plans (in case of interior works and installation) must be the floor plan of the entire floor where the project will be implemented.
* **Header Information:** As indicated in the checklist of requirements, all pages of the structural/electrical computation, detailed material and cost estimate, and technical specification must have the BEZA company's name, complete project title (as in the plans) and location.
* **Technical Specifications:** Technical Specification must contain not only the list of materials to be used but must enumerate/state Codes/Publications/Standards to be used as reference in the project, method of execution, testing etc.
* **Leased Facilities:** In case of company leasing from BEZA facilities – the location will be the lessor's bldg. and unit no. and BEZA zone or IT Site (e.g., Unit 1 ABCEDEF Building, Alphabet St. Laguna Technopark). For IT enterprises, e.g., Unit 2301 23rd floor XYZ Bldg. Makati, must be indicated in the plans and all documents.
* **IT Enterprise Furniture Layout:** For IT Enterprises applying for building permit, floor plans with furniture layout must indicate width of aisles/walkways and distance back to back of chairs with notation that distances indicated in plans are when seats are occupied.
* **Erasures & Corrections:** In case of erasures, notations, changes, or any paper pasted on the plans - all must be properly countersigned and noted by the signing professional of the page or sheet.
* **Complete Packages:** Only complete and complying documents will be accepted. – No plan or document will be accepted for safekeeping.

---

**B. POST-CONSTRUCTION STAGE**
* **Permits to Operate:** After completion of work and prior to use/occupancy and operation, BEZA Registered Enterprise must secure Occupancy Permit and Electrical and Mechanical Permit to Operate. Must submit requirements as per checklist.
* **As-Built Plans:** All plans must be labeled AS-BUILT as of date (month & year) and the Project Title must be the same as in the proposed plan (used in the pre-construction permit applications).
* **Signatures:** The plans and Certificates of Completion must be signed and sealed by the same designer engineer who signed the application form and proposed plans.
* **Dual Authorization:** The plans must be signed and sealed by both the Designer and Project-in-Charge.
* **No Partial Submissions:** Only complete and complying documents will be accepted. – No partial submission will be allowed.

---

**PROOF OF ACCEPTANCE OF APPLICATION IS A CLAIM SLIP** with application reference no. Only the original copy of the claim slip can be used to claim assessments, permits, and certificates. (Xerox and fax copies will not be honored)
  """

  with st.container(height=380):
    st.markdown(guidelines_content)

  st.markdown("<br>", unsafe_allow_html=True)

  with st.form("guidelines_agreement_form"):
    agreed = st.checkbox(
        "I have read, understood, and agree to comply with all BEZA pre-construction"
        " and post-construction guidelines stated above. *"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    proceed_btn = st.form_submit_button(
        "🚀 I Have Read and Agree — Continue to Portal"
    )

  if proceed_btn:
    if agreed:
      st.session_state.accepted_guidelines = True
      st.success("Guidelines accepted! Loading portal...")
      st.rerun()
    else:
      st.error(
          "⚠️ You must check the agreement box to confirm you have read the"
          " guidelines before proceeding to the application portal."
      )

  st.stop()

if st.session_state.admin_authenticated:
  render_admin_dashboard()
else:
  render_public_submission_form(selected_form)
