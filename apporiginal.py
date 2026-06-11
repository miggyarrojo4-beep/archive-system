import os
import base64
import csv
import re
import pandas as pd
from datetime import datetime
import streamlit as st
from PIL import Image
from PyPDF2 import PdfMerger

# --------------------------------------------------------
# 1. PAGE CONFIGURATION & THEME (Premium Institutional Blue/Brown/White)
# --------------------------------------------------------
st.set_page_config(page_title="CNHS Form 137 Archive System", layout="wide")

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    :root {
        --primary-blue: #0F172A;
        --accent-blue: #1E40AF;
        --warm-brown: #854D0E;
        --bg-white: #FAFAFA;
        --card-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
    }
    
    .backdrop {
        position: fixed;
        top: 55%;
        left: 55%;
        transform: translate(-50%, -50%);
        width: 45%;
        opacity: 0.03;
        z-index: -1000;
        pointer-events: none;
    }
    
    .record-card {
        background-color: #FFFFFF;
        border-left: 6px solid var(--accent-blue);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 15px;
        box-shadow: var(--card-shadow);
    }
    
    /* High-End Target Tracking Status Badges */
    .status-badge {
        padding: 5px 12px;
        font-weight: 700;
        font-size: 12px;
        border-radius: 50px;
        text-transform: uppercase;
        display: inline-block;
        margin-right: 8px;
        letter-spacing: 0.03em;
    }
    .stat-none { background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
    .stat-pending { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
    .stat-processing { background-color: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .stat-released { background-color: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
    
    .tag-badge {
        background-color: #E0F2FE;
        color: #0369A1;
        border: 1px solid #7DD3FC;
        padding: 4px 10px;
        font-weight: 600;
        font-size: 11px;
        border-radius: 4px;
        display: inline-block;
        margin-right: 5px;
        margin-top: 5px;
    }
    
    .no-tags-label {
        color: #94A3B8;
        font-size: 12px;
        font-style: italic;
        display: inline-block;
    }
    
    .metric-box {
        background: #FFFFFF;
        padding: 15px 25px;
        border-radius: 8px;
        text-align: center;
        box-shadow: var(--card-shadow);
        border: 1px solid #E2E8F0;
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: var(--accent-blue);
    }
    .metric-lbl {
        font-size: 12px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 5px;
    }

    .stButton>button {
        background-color: var(--accent-blue) !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    .stButton>button:hover {
        background-color: var(--warm-brown) !important;
    }
    
    .view-frame {
        border: 2px solid #1E40AF;
        border-radius: 8px;
        background-color: #FFFFFF;
        padding: 10px;
        margin-top: 15px;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if os.path.exists("SCHOOL_LOGO.PNG"):
    with open("SCHOOL_LOGO.PNG", "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    st.markdown(f'<img src="data:image/png;base64,{img_data}" class="backdrop">', unsafe_allow_html=True)

# --------------------------------------------------------
# 2. FILE DIRECTORY SETTINGS
# --------------------------------------------------------
LOGIN_TOKEN_FILE = ".login_token"
LOG_FILE = "audit_log.csv"
TAGS_FILE = "document_tags_metadata.csv"
LOCAL_REQUESTS_FILE = "student_remote_requests.csv"

ARCHIVE_DIR = r"C:\Users\SSD\Desktop\Form137_manager\scanned_records"
COMPILED_OUT_DIR = r"C:\Users\SSD\Desktop\Form137_manager\compiled_outputs"

for path_dir in [ARCHIVE_DIR, COMPILED_OUT_DIR]:
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)

def log_action(username, action, details):
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "User", "Action", "Details"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, action, details])

def load_metadata():
    tags = {}
    statuses = {}
    if os.path.exists(TAGS_FILE):
        with open(TAGS_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                path = row["full_path"]
                tags[path] = [t.strip() for t in row["tags"].split(",") if t.strip()]
                statuses[path] = row.get("status", "No Active Request")
    return tags, statuses

def save_metadata():
    with open(TAGS_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["full_path", "tags", "status"])
        for path in set(list(st.session_state.tags.keys()) + list(st.session_state.statuses.keys())):
            t_list = ", ".join(st.session_state.tags.get(path, []))
            stat = st.session_state.statuses.get(path, "No Active Request")
            writer.writerow([path, t_list, stat])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = os.path.exists(LOGIN_TOKEN_FILE)
if "search_history" not in st.session_state:
    st.session_state.search_history = []

tags_load, stats_load = load_metadata()
if "tags" not in st.session_state:
    st.session_state.tags = tags_load
if "statuses" not in st.session_state:
    st.session_state.statuses = stats_load

# --------------------------------------------------------
# 3. SECURE ACCESS MANAGEMENT (LOGIN WALL)
# --------------------------------------------------------
def login_page():
    st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-weight: 700; letter-spacing: -0.025em;'>CALAUAG NATIONAL HIGH SCHOOL</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.3, 1, 1.3])
    with col2:
        st.markdown("<div style='background: white; padding: 30px; border-radius: 12px; box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); border: 1px solid #E2E8F0;'>", unsafe_allow_html=True)
        if os.path.exists("SCHOOL_LOGO.PNG"):
            st.image("SCHOOL_LOGO.PNG", use_container_width=True)
            
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        
        if st.button("Log In", use_container_width=True):
            if username == "admin" and password == "CNHS2026":
                st.session_state.logged_in = True
                with open(LOGIN_TOKEN_FILE, "w") as f:
                    f.write("authenticated")
                log_action("admin", "LOGIN", "Successful connection established.")
                st.rerun()
            else:
                st.error("Incorrect username or password.")
        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------
# 4. MAIN APPLICATION
# --------------------------------------------------------
def main_app():
    col_logo, col_title = st.columns([1, 12])
    with col_logo:
        if os.path.exists("SCHOOL_LOGO.PNG"):
            st.image("SCHOOL_LOGO.PNG", width=65)
    with col_title:
        st.markdown("<h2 style='margin: 0; font-weight: 700; color:#0F172A;'>Calauag National High School Admin Dashboard</h2>", unsafe_allow_html=True)
        st.markdown("<p style='margin: 0; color: #64748B; font-size: 14px;'>Internal Record Management Hub</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    st.sidebar.markdown("<p style='font-weight:700; color:#0F172A; margin-bottom:5px;'>SYSTEM NAVIGATION</p>", unsafe_allow_html=True)
    
    app_mode = st.sidebar.radio("Navigation Menu", ["Cloud Student Inbox", "Search & Tag Console", "Bulk Upload & Sort", "Merge Operations Desk", "System Records Logs"], label_visibility="collapsed")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        log_action("admin", "LOGOUT", "Session disconnected.")
        st.session_state.logged_in = False
        if os.path.exists(LOGIN_TOKEN_FILE):
            os.remove(LOGIN_TOKEN_FILE)
        st.rerun()

    def get_all_files(root_dir):
        file_list = []
        if not os.path.exists(root_dir):
            return file_list
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    rel_path = os.path.relpath(root, root_dir)
                    parts = rel_path.split(os.sep)
                    
                    year = parts[0] if len(parts) > 0 and parts[0] != '.' else "Legacy / Old Curriculum"
                    grade = parts[1] if len(parts) > 1 else "Legacy / Unspecified Grade"
                    adviser = parts[2] if len(parts) > 2 else "Legacy / Unspecified Adviser"
                    
                    if year.lower() in ["", ".", "unknown"]:
                        year = "Legacy / Old Curriculum"
                    
                    file_list.append({
                        "filename": file,
                        "full_path": os.path.join(root, file),
                        "folder_dir": root,
                        "year": year,
                        "grade": grade,
                        "adviser": adviser
                    })
        return file_list

    all_files = get_all_files(ARCHIVE_DIR)

    # Counters Header Row
    vals = list(st.session_state.statuses.values())
    c_p = vals.count("Pending Request")
    c_w = vals.count("Processing")
    c_r = vals.count("Released")
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(f"<div class='metric-box'><div class='metric-val'>{len(all_files)}</div><div class='metric-lbl'>Total Scanned Records</div></div>", unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"<div class='metric-box'><div class='metric-val' style='color:#DC2626;'>{c_p}</div><div class='metric-lbl'>Pending Requests</div></div>", unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"<div class='metric-box'><div class='metric-val' style='color:#D97706;'>{c_w}</div><div class='metric-lbl'>In Processing</div></div>", unsafe_allow_html=True)
    with col_m4:
        st.markdown(f"<div class='metric-box'><div class='metric-val' style='color:#16A34A;'>{c_r}</div><div class='metric-lbl'>Released This Term</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # --- MODE 0: CLOUD STUDENT INBOX FUNCTION ---
    if app_mode == "Cloud Student Inbox":
        st.markdown("<h3 style='margin:0; font-weight:700;'>📥 Student Online Request Inbox</h3>", unsafe_allow_html=True)
        st.write("Sync and review form requests submitted online by students.")
        
        GOOGLE_CSV_LINK = st.text_input(
            "Google Form Database Link (CSV):", 
            value="https://docs.google.com/spreadsheets/d/e/2PACX-1vQu5ODrv21SrJ7O-IuP4-CM2xQVP-Od2rHxtp8zBT53mM5t6BLo-Nr4iC3KksPCP8NygskFrxjQcGvq/pub?gid=16629536&single=true&output=csv"
        )
        
        col_btn1, col_btn2 = st.columns([3, 7])
        with col_btn1:
            if st.button("🔄 Sync Cloud Requests", use_container_width=True):
                try:
                    df_cloud = pd.read_csv(GOOGLE_CSV_LINK)
                    
                    if df_cloud.empty:
                        st.warning("The form database is currently empty.")
                    else:
                        expected_cols = ["Timestamp", "Student_Name", "Contact_Number", "Batch_Year", "Purpose"]
                        cleaned_columns = expected_cols + list(df_cloud.columns[len(expected_cols):])
                        df_cloud.columns = cleaned_columns[:len(df_cloud.columns)]
                        
                        local_lookup = {}
                        if os.path.exists(LOCAL_REQUESTS_FILE):
                            with open(LOCAL_REQUESTS_FILE, mode="r", encoding="utf-8") as fl:
                                rdr = csv.DictReader(fl)
                                for row in rdr:
                                    local_lookup[row["Timestamp"] + "_" + row["Student_Name"]] = row["Status"]
                        
                        with open(LOCAL_REQUESTS_FILE, mode="w", newline="", encoding="utf-8") as fw:
                            writer = csv.writer(fw)
                            writer.writerow(["Request_ID", "Timestamp", "Student_Name", "Contact_Number", "Batch_Year", "Purpose", "Status"])
                            
                            for idx, r_row in df_cloud.iterrows():
                                s_name = str(r_row.get("Student_Name", "UNKNOWN")).upper().strip()
                                t_stamp = str(r_row.get("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                lookup_key = t_stamp + "_" + s_name
                                
                                current_status = local_lookup.get(lookup_key, "Pending Request")
                                req_id = f"REQ-{idx+1001}"
                                
                                writer.writerow([
                                    req_id, 
                                    t_stamp, 
                                    s_name, 
                                    r_row.get("Contact_Number", "N/A"), 
                                    r_row.get("Batch_Year", "N/A"), 
                                    r_row.get("Purpose", "General Request"), 
                                    current_status
                                ])
                        
                        st.success("🎉 Sync completed successfully! Local database updated.")
                        log_action("admin", "CLOUD_SYNC", "Fetched data from online form.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Could not connect to online data source: {e}")
                        
        st.markdown("<hr style='border:0.5px solid #E2E8F0; margin: 15px 0;'>", unsafe_allow_html=True)
        
        if not os.path.exists(LOCAL_REQUESTS_FILE):
            st.info("No records cached. Click 'Sync Cloud Requests' above to fetch items.")
        else:
            requests = []
            try:
                with open(LOCAL_REQUESTS_FILE, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    requests = list(reader)
            except Exception:
                requests = []
                
            if not requests: 
                st.info("No current requests found.")
            else:
                for idx, req in enumerate(reversed(requests)):
                    if not req.get("Student_Name") or not req.get("Request_ID"):
                        continue
                        
                    st_css = "stat-pending" if req["Status"] == "Pending Request" else ("stat-processing" if req["Status"] == "Processing" else "stat-released")
                    st.markdown(f"""
                    <div class='record-card'>
                        <div style='display:flex; justify-content:space-between;'>
                            <div>
                                <span style='font-size:18px; font-weight:700; color:#0F172A;'>🎓 {req['Student_Name']}</span>
                                <div style='margin-top:6px;'>
                                    <span class='status-badge {st_css}'>{req['Status']}</span>
                                    <span style='font-size:13px; color:#475569;'>📞 Contact: <b>{req['Contact_Number']}</b> | 📅 Year: <b>{req['Batch_Year']}</b> | 🎯 Purpose: <b>{req['Purpose']}</b></span>
                                </div>
                            </div>
                            <span style='font-size:12px; color:#94A3B8; font-weight:600;'>ID: {req['Request_ID']} | Filed: {req['Timestamp']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_act1, c_act2, c_act3, c_act4 = st.columns([1.5, 1.5, 2, 5])
                    with c_act1:
                        if st.button("⚙️ Move to Processing", key=f"p_{req['Request_ID']}_{idx}"):
                            requests[len(requests)-1-idx]["Status"] = "Processing"
                            with open(LOCAL_REQUESTS_FILE, mode="w", newline="", encoding="utf-8") as fw:
                                writer = csv.writer(fw)
                                writer.writerow(["Request_ID", "Timestamp", "Student_Name", "Contact_Number", "Batch_Year", "Purpose", "Status"])
                                for r in requests: writer.writerow(list(r.values()))
                            st.rerun()
                    with c_act2:
                        if st.button("✅ Mark as Released", key=f"r_{req['Request_ID']}_{idx}"):
                            requests[len(requests)-1-idx]["Status"] = "Released"
                            with open(LOCAL_REQUESTS_FILE, mode="w", newline="", encoding="utf-8") as fw:
                                writer = csv.writer(fw)
                                writer.writerow(["Request_ID", "Timestamp", "Student_Name", "Contact_Number", "Batch_Year", "Purpose", "Status"])
                                for r in requests: writer.writerow(list(r.values()))
                            st.rerun()
                    with c_act3:
                        st.markdown(f"`Search Key: {req['Student_Name']}`")
                    st.markdown("<br>", unsafe_allow_html=True)

    # --- MODE 1: SEARCH & TAG CONSOLE (WITH SYSTEM FILE SOURCE DROPDOWN SELECTION) ---
    elif app_mode == "Search & Tag Console":
        st.markdown("<h3 style='margin:0; font-weight:600;'>🔍 Records Archive Search Engine</h3>", unsafe_allow_html=True)
        
        console_source = st.selectbox(
            "Choose Document Storage Source:",
            ["📁 Local System Server Directory Workspace", "☁️ Google Drive Live Integration URL Network"]
        )
        
        gdrive_search_url = ""
        if "Google Drive" in console_source:
            gdrive_search_url = st.text_input(
                "Paste Google Drive Folder or Document Link:", 
                placeholder="https://drive.google.com/drive/folders/your-id-here",
                help="Make sure your Google Drive folder's sharing configuration is set to 'Anyone with the link can view'."
            )

        search_query = st.text_input("Search student name or filename...", placeholder="Type student name here (e.g. DELA CRUZ, JUAN)")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            years = sorted(list(set(f["year"] for f in all_files)))
            selected_year = st.selectbox("Filter by Batch Year", ["All Records"] + years)
        with col_f2:
            grades = sorted(list(set(f["grade"] for f in all_files)))
            selected_grade = st.selectbox("Filter by Grade Level", ["All Levels"] + grades)
        with col_f3:
            advisers = sorted(list(set(f["adviser"] for f in all_files)))
            selected_adviser = st.selectbox("Filter by Classroom Adviser", ["All Advisers"] + advisers)

        if not search_query.strip():
            st.markdown("<div style='background-color:#F8FAFC; border: 1px dashed #CBD5E1; border-radius:8px; padding:40px; text-align:center; color:#64748B; margin-top:20px;'>💡 Enter a search keyword above to locate student documents.</div>", unsafe_allow_html=True)
        else:
            filtered = [f for f in all_files if search_query.lower() in f["filename"].lower()]
            if search_query not in st.session_state.search_history:
                st.session_state.search_history.append(search_query)
                log_action("admin", "SEARCH", f"Searched: '{search_query}' using source: {console_source}")
                    
            if selected_year != "All Records":
                filtered = [f for f in filtered if f["year"] == selected_year]
            if selected_grade != "All Levels":
                filtered = [f for f in filtered if f["grade"] == selected_grade]
            if selected_adviser != "All Advisers":
                filtered = [f for f in filtered if f["adviser"] == selected_adviser]

            st.markdown(f"<p style='color:#475569; font-weight:600; margin-top:15px;'>Matching Results Found: {len(filtered)}</p>", unsafe_allow_html=True)
            
            for doc in filtered:
                path_key = doc['full_path']
                current_status = st.session_state.statuses.get(path_key, "No Active Request")
                current_tags = st.session_state.tags.get(path_key, [])
                
                if current_status == "Pending Request": status_css = "stat-pending"
                elif current_status == "Processing": status_css = "stat-processing"
                elif current_status == "Released": status_css = "stat-released"
                else: status_css = "stat-none"
                
                tags_html = ""
                if current_tags:
                    for tag in current_tags:
                        tags_html += f"<span class='tag-badge'>🏷️ {tag}</span>"
                else:
                    tags_html = "<span class='no-tags-label'>No purpose tags added</span>"

                st.markdown(f"""
                <div class='record-card'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>
                        <div>
                            <div style='font-size:22px; font-weight:700; color:#0F172A; margin-bottom:8px;'>📄 {doc['filename']}</div>
                            <div style='display:flex; align-items:center; flex-wrap:wrap; gap:5px;'>
                                <span class='status-badge {status_css}'>📋 {current_status}</span>
                                {tags_html}
                            </div>
                        </div>
                        <span style='background:#F1F5F9; color:#334155; padding:6px 14px; font-weight:600; font-size:12px; border-radius:50px; border:1px solid #E2E8F0;'>
                            📍 {doc['year']} | {doc['grade']} | {doc['adviser']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_c1, col_c2 = st.columns([1, 1])
                with col_c1:
                    status_options = ["No Active Request", "Pending Request", "Processing", "Released"]
                    try: idx = status_options.index(current_status)
                    except ValueError: idx = 0
                        
                    chosen_status = st.selectbox(f"Update Document Status:", status_options, index=idx, key=f"stat_sel_{path_key}")
                    if chosen_status != current_status:
                        st.session_state.statuses[path_key] = chosen_status
                        save_metadata()
                        log_action("admin", "STATUS_CHANGE", f"Updated [{doc['filename']}] status to: {chosen_status}")
                        st.rerun()
                
                with col_c2:
                    new_tags = st.text_input(f"Purpose Tags (Comma Separated):", value=", ".join(current_tags), key=f"tags_inp_{path_key}", placeholder="e.g. COLLEGE, TRANSFER, EMPLOYMENT")
                    if new_tags:
                        processed_tags = [t.strip() for t in new_tags.split(",") if t.strip()]
                        if processed_tags != current_tags:
                            st.session_state.tags[path_key] = processed_tags
                            save_metadata()
                            st.rerun()

                c1, c2, c3 = st.columns([2.5, 2.8, 4.7])
                
                binary_data = b""
                gdrive_fetch_error = False
                
                if "Google Drive" in console_source and gdrive_search_url.strip():
                    f_match = re.search(r'folders/([a-zA-Z0-9-_]+)', gdrive_search_url)
                    doc_id_match = re.search(r'file/d/([a-zA-Z0-9-_]+)', gdrive_search_url)
                    target_id = f_match.group(1) if f_match else (doc_id_match.group(1) if doc_id_match else "")
                    
                    if target_id:
                        try:
                            import requests
                            direct_dl_url = f"https://drive.google.com/uc?export=download&id={target_id}"
                            res = requests.get(direct_dl_url)
                            if res.status_code == 200:
                                binary_data = res.content
                            else:
                                gdrive_fetch_error = True
                        except Exception:
                            gdrive_fetch_error = True
                    else:
                        gdrive_fetch_error = True
                else:
                    if os.path.exists(path_key):
                        with open(path_key, "rb") as file_bytes:
                            binary_data = file_bytes.read()

                if gdrive_fetch_error:
                    st.error("⚠️ Drive Asset Error: Could not download the document payload from Google Drive.")
                
                with c1: view_clicked = st.button("👁️ Preview File", key=f"btn_view_{path_key}", use_container_width=True)
                with c2: st.download_button(label="📥 Download File", data=binary_data, file_name=doc['filename'], mime="application/octet-stream", key=f"btn_dl_{path_key}", use_container_width=True, disabled=gdrive_fetch_error)
                
                if (view_clicked or st.session_state.get(f"keep_view_{path_key}", False)) and not gdrive_fetch_error:
                    st.session_state[f"keep_view_{path_key}"] = True
                    st.markdown("<div class='view-frame'>", unsafe_allow_html=True)
                    ext = doc['filename'].lower().split('.')[-1]
                    if ext == 'pdf':
                        base64_pdf = base64.b64encode(binary_data).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="650" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.image(binary_data if "Google Drive" in console_source else path_key, use_container_width=True)
                    
                    if st.button("❌ Close File Preview", key=f"close_{path_key}"):
                        st.session_state[f"keep_view_{path_key}"] = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<hr style='border:0.5px solid #E2E8F0; margin:15px 0;'>", unsafe_allow_html=True)

    # --- MODE 2: BULK UPLOAD SYSTEM PANEL ---
    elif app_mode == "Bulk Upload & Sort":
        st.markdown("<h3 style='margin:0; font-weight:600;'>📂 Document Ingestion Desk & Automated Organizer</h3>", unsafe_allow_html=True)
        st.write("Upload new batches of Form 137 files. The system will automatically file them into organized directories.")
        
        col_up1, col_up2, col_up3 = st.columns(3)
        with col_up1: up_year = st.text_input("Target Batch Year (e.g. 1996-1997)", value="Legacy")
        with col_up2: up_grade = st.text_input("Grade Level / Classification", value="Unspecified Grade")
        with col_up3: up_adviser = st.text_input("Classroom Faculty Adviser Name", value="Unspecified Adviser")
            
        uploaded_files = st.file_uploader("Drag and drop files here to start upload processing", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)
        
        if st.button("📥 Upload & Save Records"):
            if not uploaded_files:
                st.error("No files selected. Please add documents before saving.")
            else:
                y_folder = up_year.strip() if up_year.strip() else "Legacy"
                g_folder = up_grade.strip() if up_grade.strip() else "Unspecified Grade"
                a_folder = up_adviser.strip() if up_adviser.strip() else "Unspecified Adviser"
                
                target_dest_directory = os.path.join(ARCHIVE_DIR, y_folder.upper(), g_folder.upper(), a_folder.upper())
                if not os.path.exists(target_dest_directory):
                    os.makedirs(target_dest_directory)
                    
                success_count = 0
                for file_payload in uploaded_files:
                    write_target_path = os.path.join(target_dest_directory, file_payload.name)
                    with open(write_target_path, "wb") as f_writer:
                        f_writer.write(file_payload.getbuffer())
                    success_count += 1
                    
                st.success(f"Processing complete! Successfully filed {success_count} documents into: `{target_dest_directory}`.")

    # --- MODE 3: COMPILATION DESK DESKTOP CONSOLE ---
    elif app_mode == "Merge Operations Desk":
        st.markdown("<h3 style='margin:0; font-weight:600;'>🔀 Multi-Page Compilation Console</h3>", unsafe_allow_html=True)
        st.write("Merge multiple disconnected scan pages into a single, comprehensive student document.")
        
        file_options = {f"{f['year']} / {f['grade']} / {f['adviser']} ➔ {f['filename']}": f for f in all_files}
        selected_to_merge = st.multiselect("Select the pages you want to compile:", list(file_options.keys()))
        
        default_absorbed_name = "Compiled_Student_Document.pdf"
        if selected_to_merge:
            first_selected_key = selected_to_merge[0]
            first_file_meta = file_options[first_selected_key]
            raw_filename = first_file_meta['filename']
            
            clean_name = re.sub(r'\.[a-zA-Z0-9]+$', '', raw_filename)
            clean_name = re.sub(r'[\s_\-]*\(\d+\)[\s_\-]*', '', clean_name)
            clean_name = re.sub(r'[\s_\-]*copy[\s_\-]*', '', clean_name, flags=re.IGNORECASE)
            
            default_absorbed_name = f"{clean_name.strip()}.pdf"

        output_filename = st.text_input("Name for the Merged PDF File:", value=default_absorbed_name)
        
        if st.button("🔀 Compile Selected Pages"):
            if len(selected_to_merge) < 2:
                st.error("Please choose at least 2 files to generate a combined document.")
            else:
                try:
                    merger = PdfMerger()
                    temp_files_to_clean = []
                    
                    for key in selected_to_merge:
                        doc = file_options[key]
                        filepath = doc['full_path']
                        
                        if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                            image = Image.open(filepath)
                            pdf_path = filepath.rsplit('.', 1)[0] + "_temp_conv.pdf"
                            image.convert('RGB').save(pdf_path, "PDF")
                            merger.append(pdf_path)
                            temp_files_to_clean.append(pdf_path)
                        elif filepath.lower().endswith('.pdf'):
                            merger.append(filepath)
                    
                    if not output_filename.lower().endswith('.pdf'):
                        output_filename += ".pdf"
                    
                    output_path = os.path.join(COMPILED_OUT_DIR, output_filename)
                    
                    with open(output_path, "wb") as f_out:
                        merger.write(f_out)
                    merger.close()
                    
                    for temp_file in temp_files_to_clean:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                            
                    log_action("admin", "MERGE_DOCUMENTS", f"Merged pages into single file: {output_filename}")
                    st.success(f"Compilation finished! Combined document safely written to outputs folder: `{output_path}`.")
                except Exception as e:
                    st.error(f"Error compiling files: {e}")

    # --- MODE 4: SYSTEM DATA CONTROL DESK ---
    elif app_mode == "System Records Logs":
        st.markdown("<h3 style='margin:0; font-weight:600;'>📜 System Activity Logs & Report Export Desk</h3>", unsafe_allow_html=True)
        
        st.markdown("#### 📊 Export Sheet Data Reports")
        if st.button("Generate CSV Spreadsheet Report"):
            if not st.session_state.tags and not st.session_state.statuses:
                st.warning("No operational custom metadata records found to export.")
            else:
                report_file = "Form137_Active_Requests_Report.csv"
                with open(report_file, mode="w", newline="", encoding="utf-8") as f_rep:
                    writer = csv.writer(f_rep)
                    writer.writerow(["Document Path Location Link", "Assigned Verification Tags", "Active Request Workflow Pipeline Status"])
                    for p in set(list(st.session_state.tags.keys()) + list(st.session_state.statuses.keys())):
                        writer.writerow([p, ", ".join(st.session_state.tags.get(p, [])), st.session_state.statuses.get(p, "No Active Request")])
                
                with open(report_file, "rb") as f_dl:
                    st.download_button("📥 Click Here to Download Compiled CSV Sheet Report", data=f_dl.read(), file_name=report_file, mime="text/csv")
        
        st.markdown("<hr style='border:0.5px solid #E2E8F0; margin: 25px 0;'>", unsafe_allow_html=True)
        st.markdown("#### 🛡️ Operations Audit Trail Logs")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode="r", encoding="utf-8") as f_log:
                log_data = f_log.readlines()
            for row in reversed(log_data[1:]):
                r_parts = row.strip().split(",")
                if len(r_parts) >= 4:
                    st.markdown(f"⏱️ **`{r_parts[0]}`** | User: `{r_parts[1]}` | Action: `{r_parts[2]}` | Details: *{','.join(r_parts[3:])}*")
        
        if st.session_state.search_history:
            if st.button("🗑️ Clear Session Search History Cache"):
                st.session_state.search_history = []
                st.success("Session footprints successfully cleared.")
                st.rerun()

if not st.session_state.logged_in:
    login_page()
else:
    main_app()