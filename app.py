import os
import base64
import csv
import re
import pandas as pd
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from PyPDF2 import PdfMerger

# --------------------------------------------------------
# 1. PAGE CONFIGURATION & THEME (Dynamic Light/Dark Adaptive)
# --------------------------------------------------------
st.set_page_config(page_title="CNHS Form 137 Archive System", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* --- DYNAMIC THEME ENGINE COUPLING --- */
    :root {
        --primary-blue: #1877F2;
        --accent-blue: #1877F2;
        --hover-blue: #166FE5;
        
        /* Map layouts directly to Streamlit's UI State Engine */
        --main-bg: var(--secondary-background-color);
        --card-bg: var(--background-color);
        --sidebar-bg: var(--secondary-background-color);
        --text-main: var(--text-color);
        
        /* Light Theme Default Variables */
        --text-muted: #65676B;
        --metric-border: rgba(0, 0, 0, 0.08);
        --badge-bg: rgba(0, 0, 0, 0.05);
        --danger-bg: #FFEBEB;
        --danger-border: #FFCCD2;
        --card-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        --logo-filter: grayscale(100%);
        --logo-opacity: 0.07;
        
        /* Smart Alpha-Blended Status Badges & Metrics (Light Mode Mode) */
        --box-tot-bg: rgba(24, 119, 242, 0.12);   --box-tot-txt: #1877F2; --box-tot-brd: rgba(24, 119, 242, 0.25);
        --box-pen-bg: rgba(228, 30, 63, 0.12);    --box-pen-txt: #E41E3F; --box-pen-brd: rgba(228, 30, 63, 0.25);
        --box-pro-bg: rgba(240, 167, 10, 0.12);   --box-pro-txt: #D97706; --box-pro-brd: rgba(240, 167, 10, 0.25);
        --box-rel-bg: rgba(49, 162, 76, 0.12);    --box-rel-txt: #31A24C; --box-rel-brd: rgba(49, 162, 76, 0.25);
    }

    /* Automated Dark-State Adjustments via System Values */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-muted: #9CA3AF;
            --metric-border: rgba(255, 255, 255, 0.12);
            --badge-bg: rgba(255, 255, 255, 0.08);
            --danger-bg: #451212;
            --danger-border: #7F1D1D;
            --card-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
            --logo-filter: invert(1) grayscale(100%);
            --logo-opacity: 0.04;
            
            /* High-Contrast Badges & Metrics (Dark Mode Environment) */
            --box-tot-bg: rgba(96, 165, 250, 0.18);  --box-tot-txt: #60A5FA; --box-tot-brd: rgba(96, 165, 250, 0.35);
            --box-pen-bg: rgba(244, 63, 94, 0.18);   --box-pen-txt: #F43F5E; --box-pen-brd: rgba(244, 63, 94, 0.35);
            --box-pro-bg: rgba(251, 191, 36, 0.18);  --box-pro-txt: #FBBF24; --box-pro-brd: rgba(251, 191, 36, 0.35);
            --box-rel-bg: rgba(52, 211, 153, 0.18);  --box-rel-txt: #34D399; --box-rel-brd: rgba(52, 211, 153, 0.35);
        }
    }

    /* Force backgrounds and global overrides */
    [data-testid="stAppViewContainer"], .stApp {
        background-color: var(--main-bg) !important;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* --- SIDEBAR PANEL --- */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
    }
    
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] div {
        color: var(--text-main) !important;
    }
    
    /* --- NAVIGATION ITEMS --- */
    [data-testid="stSidebar"] div[role="radiogroup"] > label {
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 5px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: var(--badge-bg) !important;
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: rgba(24, 119, 242, 0.15) !important;
        box-shadow: var(--card-shadow) !important;
        border-left: 4px solid var(--accent-blue);
    }
    
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) span {
        color: var(--accent-blue) !important;
        font-weight: 600;
    }
    
    /* Watermark Background Graphic Setup */
    .backdrop {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 450px;
        opacity: var(--logo-opacity);
        filter: var(--logo-filter);
        z-index: 0;
        pointer-events: none;
    }
    
    .record-card, .metric-box, .view-frame, [data-testid="stVerticalBlock"] {
        position: relative;
        z-index: 1;
    }
    
    /* --- COMPONENT CARDS --- */
    .record-card {
        background-color: var(--card-bg);
        border-left: 4px solid var(--accent-blue);
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 15px;
        box-shadow: var(--card-shadow);
        border-top: 1px solid var(--metric-border);
        border-right: 1px solid var(--metric-border);
        border-bottom: 1px solid var(--metric-border);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .record-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    
    /* --- STATUS BADGES --- */
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
    .stat-none { background-color: var(--badge-bg); color: var(--text-main); border: 1px solid var(--metric-border); }
    .stat-pending { background-color: var(--box-pen-bg); color: var(--box-pen-txt); border: 1px solid var(--box-pen-brd); }
    .stat-processing { background-color: var(--box-pro-bg); color: var(--box-pro-txt); border: 1px solid var(--box-pro-brd); }
    .stat-released { background-color: var(--box-rel-bg); color: var(--box-rel-txt); border: 1px solid var(--box-rel-brd); }
    
    .tag-badge {
        background-color: var(--box-tot-bg);
        color: var(--box-tot-txt);
        border: 1px solid var(--box-tot-brd);
        padding: 4px 10px;
        font-weight: 600;
        font-size: 11px;
        border-radius: 4px;
        display: inline-block;
        margin-right: 5px;
        margin-top: 5px;
    }
    
    .no-tags-label {
        color: var(--text-muted);
        font-size: 12px;
        font-style: italic;
        display: inline-block;
    }
    
    /* --- ANALYTICAL METRICS COUNTERS --- */
    .metric-box {
        padding: 20px 25px;
        border-radius: 8px;
        text-align: center;
        box-shadow: var(--card-shadow);
        transition: transform 0.2s ease;
    }
    .metric-box.total { background-color: var(--box-tot-bg); border: 1px solid var(--box-tot-brd); }
    .metric-box.total .metric-val, .metric-box.total .metric-lbl { color: var(--box-tot-txt); }
    
    .metric-box.pending { background-color: var(--box-pen-bg); border: 1px solid var(--box-pen-brd); }
    .metric-box.pending .metric-val, .metric-box.pending .metric-lbl { color: var(--box-pen-txt); }
    
    .metric-box.processing { background-color: var(--box-pro-bg); border: 1px solid var(--box-pro-brd); }
    .metric-box.processing .metric-val, .metric-box.processing .metric-lbl { color: var(--box-pro-txt); }
    
    .metric-box.released { background-color: var(--box-rel-bg); border: 1px solid var(--box-rel-brd); }
    .metric-box.released .metric-val, .metric-box.released .metric-lbl { color: var(--box-rel-txt); }

    .metric-box:hover {
        transform: translateY(-2px);
    }
    .metric-val {
        font-size: 28px;
        font-weight: 800;
    }
    .metric-lbl {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 5px;
        font-weight: 600;
    }

    /* --- SYSTEM BUTTONS --- */
    .stButton>button {
        background-color: var(--accent-blue) !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.15s ease !important;
    }
    .stButton>button:hover {
        background-color: var(--hover-blue) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .btn-danger>button {
        background-color: #DC2626 !important;
    }
    .btn-danger>button:hover {
        background-color: #991B1B !important;
    }
    
    .view-frame {
        border: 2px solid var(--accent-blue);
        border-radius: 8px;
        background-color: var(--card-bg);
        padding: 10px;
        margin-top: 15px;
    }
    
    .theme-text { color: var(--text-main) !important; }
    .theme-text-muted { color: var(--text-muted) !important; }
    hr { border: 0.5px solid var(--metric-border) !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

if os.path.exists("SCHOOL_LOGO.PNG"):
    with open("SCHOOL_LOGO.PNG", "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    # Render the backdrop image with an ID for our script to target
    st.markdown(f'<img id="dynamic-backdrop" src="data:image/png;base64,{img_data}" class="backdrop">', unsafe_allow_html=True)
    
    # Inject an invisible JavaScript watcher to sync logo with Streamlit's internal theme toggle
    components.html(
        """
        <script>
        // Access the main Streamlit document from the component iframe
        const doc = window.parent.document;
        
        const syncTheme = () => {
            const backdrop = doc.getElementById('dynamic-backdrop');
            if (!backdrop) return;
            
            // Streamlit dynamically updates the background-color and color of the main app
            const textColor = window.getComputedStyle(doc.body).color;
            const rgb = textColor.match(/\\d+/g);
            
            if (rgb) {
                // Calculate brightness of text to determine if we are in Dark Mode or Light Mode
                const luma = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
                if (luma > 128) {
                    // Light Text = Dark Mode App Active
                    backdrop.style.filter = 'invert(1) grayscale(100%)';
                    backdrop.style.opacity = '0.04';
                } else {
                    // Dark Text = Light Mode App Active
                    backdrop.style.filter = 'grayscale(100%)';
                    backdrop.style.opacity = '0.07';
                }
            }
        };
        
        // Run immediately on load
        syncTheme();
        
        // Watch for any class/style changes Streamlit makes to the DOM when toggling themes
        const observer = new MutationObserver(syncTheme);
        observer.observe(doc.body, { attributes: true, childList: true, subtree: true });
        </script>
        """,
        height=0, width=0
    )

# --------------------------------------------------------
# 2. FILE DIRECTORY SETTINGS
# --------------------------------------------------------
LOGIN_TOKEN_FILE = ".login_token"
LOG_FILE = "audit_log.csv"
TAGS_FILE = "document_tags_metadata.csv"
LOCAL_REQUESTS_FILE = "student_remote_requests.csv"

ARCHIVE_DIR = r"C:\Users\SSD\Desktop\Form137_manager\scanned_records"
COMPILED_OUT_DIR = r"C:\Users\user\Desktop\Form137_Manager\compiled_outputs"

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
    st.markdown("<h1 style='text-align: center; font-weight: 800; letter-spacing: -0.025em;' class='theme-text'>CALAUAG NATIONAL HIGH SCHOOL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: var(--accent-blue); font-weight: 600; margin-bottom: 30px;'>Internal Records Management System</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1.3, 1, 1.3])
    with col2:
        st.markdown("<div style='background: var(--card-bg); padding: 40px 30px; border-radius: 12px; box-shadow: var(--card-shadow); border: 1px solid var(--metric-border); position: relative; z-index: 10;'>", unsafe_allow_html=True)
        
        if os.path.exists("SCHOOL_LOGO.PNG"):
            col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
            with col_img2:
                st.image("SCHOOL_LOGO.PNG", use_container_width=True)
        
        st.markdown("<h3 style='text-align: center; font-size: 20px; font-weight: 600; margin-bottom: 20px;' class='theme-text'>Administrator Login</h3>", unsafe_allow_html=True)
            
        username = st.text_input("Username", placeholder="Enter administrator username")
        password = st.text_input("Password", type="password", placeholder="Enter secure password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log In", use_container_width=True):
            if username == "admin" and password == "CNHS2026":
                st.session_state.logged_in = True
                with open(LOGIN_TOKEN_FILE, "w") as f:
                    f.write("authenticated")
                log_action("admin", "LOGIN", "Successful connection established.")
                st.rerun()
            else:
                st.error("Incorrect username or password. Please try again.")
        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------------
# 4. MAIN APPLICATION INTERFACE
# --------------------------------------------------------
def main_app():
    col_logo, col_title = st.columns([1, 15])
    with col_logo:
        if os.path.exists("SCHOOL_LOGO.PNG"):
            st.image("SCHOOL_LOGO.PNG", width=100)
    with col_title:
        st.markdown("<h2 style='margin: 0; padding-top: 5px; font-weight: 800;' class='theme-text'>CNHS Form 137 Archive</h2>", unsafe_allow_html=True)
        st.markdown("<p style='margin: 0; color: var(--accent-blue); font-size: 14px; font-weight: 600;'>Form 137 Internal Record Management Hub</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    # --- NAVIGATION SIDEBAR ---
    st.sidebar.markdown("""
        <div style='background-color: var(--card-bg); padding: 15px; border-radius: 8px; border: 1px solid var(--metric-border); margin-bottom: 20px; text-align: center;'>
            <h3 style='margin: 0; font-size: 16px;' class='theme-text'>Welcome, Administrator</h3>
            <p style='margin: 0; font-size: 12px; color: #31A24C; font-weight: 600;'>● System Status: Online</p>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("<p style='font-weight:700; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom:5px;' class='theme-text-muted'>MAIN MENU</p>", unsafe_allow_html=True)
    
    nav_options = [
        "FORM 137 ONLINE REQUEST", 
        "SEARCH AND TAG",
        "RELEASED & TAGGED RECORDS",
        "MERGE PAGES", 
        "SYSTEM LOGS AND SETTINGS"
    ]
    app_mode = st.sidebar.radio("Navigation Menu", nav_options, label_visibility="collapsed")
    
    st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='font-weight:700; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom:5px;' class='theme-text-muted'>ACCOUNT</p>", unsafe_allow_html=True)
    
    st.sidebar.markdown('<div class="btn-danger">', unsafe_allow_html=True)
    if st.sidebar.button("Log Out", use_container_width=True):
        log_action("admin", "LOGOUT", "Session disconnected.")
        st.session_state.logged_in = False
        if os.path.exists(LOGIN_TOKEN_FILE):
            os.remove(LOGIN_TOKEN_FILE)
        st.rerun()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

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

    # --- SYNCHRONIZED COUNTER METRICS ---
    req_c_p, req_c_w, req_c_r = 0, 0, 0
    
    if os.path.exists(LOCAL_REQUESTS_FILE):
        try:
            with open(LOCAL_REQUESTS_FILE, mode="r", encoding="utf-8") as fl:
                for row in csv.DictReader(fl):
                    s = row.get("Status", "")
                    if s == "Pending Request": req_c_p += 1
                    elif s == "Processing": req_c_w += 1
                    elif s == "Released": req_c_r += 1
        except Exception:
            pass

    if os.path.exists(TAGS_FILE):
        try:
            with open(TAGS_FILE, mode="r", encoding="utf-8") as fm:
                for row in csv.DictReader(fm):
                    if row.get("status") == "Released":
                        req_c_r += 1 
        except Exception:
            pass

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(f"<div class='metric-box total'><div class='metric-val'>{len(all_files)}</div><div class='metric-lbl'>Total Scanned Records</div></div>", unsafe_allow_html=True)
    with col_m2:
        st.markdown(f"<div class='metric-box pending'><div class='metric-val'>{req_c_p}</div><div class='metric-lbl'>Pending Requests</div></div>", unsafe_allow_html=True)
    with col_m3:
        st.markdown(f"<div class='metric-box processing'><div class='metric-val'>{req_c_w}</div><div class='metric-lbl'>In Processing</div></div>", unsafe_allow_html=True)
    with col_m4:
        st.markdown(f"<div class='metric-box released'><div class='metric-val'>{req_c_r}</div><div class='metric-lbl'>Released This Term</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    # --- MODE 0: FORM 137 ONLINE REQUEST ---
    if app_mode == "FORM 137 ONLINE REQUEST":
        st.markdown("<h3 style='margin:0; font-weight:700;' class='theme-text'>Student Online Request Inbox</h3>", unsafe_allow_html=True)
        st.markdown("<p class='theme-text-muted'>Sync, review, and manage form requests submitted online by students.</p>", unsafe_allow_html=True)
        
        GOOGLE_CSV_LINK = st.text_input(
            "Google Form Database Link (CSV):", 
            value="https://docs.google.com/spreadsheets/d/e/2PACX-1vQu5ODrv21SrJ7O-IuP4-CM2xQVP-Od2rHxtp8zBT53mM5t6BLo-Nr4iC3KksPCP8NygskFrxjQcGvq/pub?gid=16629536&single=true&output=csv"
        )
        
        col_btn1, col_btn2 = st.columns([3, 7])
    
        with col_btn1:
            if st.button("Sync Cloud Requests", use_container_width=True):
                try:
                    df_cloud = pd.read_csv(GOOGLE_CSV_LINK)
                    if df_cloud.empty:
                        st.warning("The form database is currently empty.")
                    else:
                        expected_cols = ["Timestamp", "Student_Name", "Contact_Number", "Adviser", "School_Year", "Purpose"]
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
                            writer.writerow(["Request_ID", "Timestamp", "Student_Name", "Contact_Number", "Adviser", "School_Year", "Purpose", "Status"])
                            
                            for idx, r_row in df_cloud.iterrows():
                                s_name = str(r_row.get("Student_Name", "UNKNOWN")).upper().strip()
                                t_stamp = str(r_row.get("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                                lookup_key = t_stamp + "_" + s_name
                                
                                current_status = local_lookup.get(lookup_key, "Pending Request")
                                req_id = f"REQ-{idx+1001}"
                                
                                writer.writerow([
                                    req_id, t_stamp, s_name, 
                                    r_row.get("Contact_Number", "N/A"), 
                                    r_row.get("Adviser", "N/A"), 
                                    r_row.get("School_Year", "N/A"), 
                                    r_row.get("Purpose", "General Request"), 
                                    current_status
                                ])
                       
                        st.success("Sync completed successfully! Local database updated.")
                        log_action("admin", "CLOUD_SYNC", "Fetched data from online form.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Could not connect to online data source: {e}")
                        
        st.markdown("<hr>", unsafe_allow_html=True)
        
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
                                <span style='font-size:18px; font-weight:700;' class='theme-text'>{req['Student_Name']}</span>
                                <div style='margin-top:8px;'>
                                    <span class='status-badge {st_css}'>{req['Status']}</span>
                                    <span style='font-size:13px;' class='theme-text-muted'>
                                        <b>Contact:</b> {req.get('Contact_Number', 'N/A')} | <b>Adviser:</b> {req.get('Adviser', 'N/A')} | 
                                        <b>Year:</b> {req.get('School_Year', 'N/A')} | 
                                        <b>Purpose:</b> {req.get('Purpose', 'General Request')}
                                    </span>
                                </div>
                            </div>
                            <span style='font-size:12px; font-weight:600;' class='theme-text-muted'>ID: {req['Request_ID']} | Filed: {req['Timestamp']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_act1, c_act2, c_act3, c_act4 = st.columns([1.5, 1.5, 1.5, 4.5])
                    real_idx = len(requests) - 1 - idx
                    
                    with c_act1:
                        if st.button("Process", key=f"p_{req['Request_ID']}_{idx}", use_container_width=True):
                            requests[real_idx]["Status"] = "Processing"
                            with open(LOCAL_REQUESTS_FILE, mode="w", newline="", encoding="utf-8") as fw:
                                writer = csv.writer(fw)
                                writer.writerow(["Request_ID", "Timestamp", "Student_Name", "Contact_Number", "Adviser", "School_Year", "Purpose", "Status"])
                                for r in requests: writer.writerow(list(r.values()))
                            st.rerun()
                    with c_act2:
                        if st.button("Release", key=f"r_{req['Request_ID']}_{idx}", use_container_width=True):
                            requests[real_idx]["Status"] = "Released"
                            with open(LOCAL_REQUESTS_FILE, mode="w", newline="", encoding="utf-8") as fw:
                                writer = csv.writer(fw)
                                writer.writerow(["Request_ID", "Timestamp", "Student_Name", "Contact_Number", "Adviser", "School_Year", "Purpose", "Status"])
                                for r in requests: writer.writerow(list(r.values()))
                            st.rerun()
                    with c_act3:
                        st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                        if st.button("Remove", key=f"del_{req['Request_ID']}_{idx}", use_container_width=True):
                            requests.pop(real_idx)
                            with open(LOCAL_REQUESTS_FILE, mode="w", newline="", encoding="utf-8") as fw:
                                writer = csv.writer(fw)
                                writer.writerow(["Request_ID", "Timestamp", "Student_Name", "Contact_Number", "Adviser", "School_Year", "Purpose", "Status"])
                                for r in requests: writer.writerow(list(r.values()))
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)

    # --- MODE 1: SEARCH AND TAG ---
    elif app_mode == "SEARCH AND TAG":
        st.markdown("<h3 style='margin:0; font-weight:700;' class='theme-text'>Records Archive Search Engine</h3>", unsafe_allow_html=True)
        st.markdown("<p class='theme-text-muted'>Locate student records, preview documents, and update verification tags instantly.</p>", unsafe_allow_html=True)
        
        console_source = st.selectbox(
            "Choose Document Storage Source:",
            ["Local System Server Directory Workspace", "Google Drive Live Integration URL Network"]
        )
        
        gdrive_search_url = ""
        if "Google Drive" in console_source:
            gdrive_search_url = st.text_input(
                "Paste Exact Google Drive File Link:", 
                placeholder="https://drive.google.com/file/d/your-file-id/view"
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
            st.markdown("<div style='background-color:var(--card-bg); border: 1px dashed var(--metric-border); border-radius:8px; padding:40px; text-align:center; margin-top:20px;' class='theme-text-muted'>Enter a search keyword above to locate student documents.</div>", unsafe_allow_html=True)
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

            st.markdown(f"<p class='theme-text-muted' style='font-weight:600; margin-top:15px;'>Matching Results Found: <span style='color:var(--accent-blue);'>{len(filtered)}</span></p>", unsafe_allow_html=True)
            
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
                        tags_html += f"<span class='tag-badge'>{tag}</span>"
                else:
                    tags_html = "<span class='no-tags-label'>No purpose tags added</span>"

                st.markdown(f"""
                <div class='record-card'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;'>
                        <div>
                            <div style='font-size:20px; font-weight:700; margin-bottom:8px;' class='theme-text'>{doc['filename']}</div>
                            <div style='display:flex; align-items:center; flex-wrap:wrap; gap:5px;'>
                                <span class='status-badge {status_css}'>{current_status}</span>
                                {tags_html}
                            </div>
                        </div>
                        <span style='background:var(--badge-bg); padding:6px 14px; font-weight:600; font-size:12px; border-radius:50px; border:1px solid var(--metric-border);' class='theme-text'>
                            Location: {doc['year']} | {doc['grade']} | {doc['adviser']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col_c1, col_c2 = st.columns([1, 1])
                with col_c1:
                    status_options = ["No Active Request", "Pending Request", "Processing", "Released"]
                    try: 
                        idx = status_options.index(current_status)
                    except ValueError: 
                        idx = 0
                        
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

                c1, c2, c3 = st.columns([2.5, 2.5, 4.7])
                
                binary_data = b""
                gdrive_fetch_error = False
                drive_id = ""
                
                if "Google Drive" in console_source and gdrive_search_url.strip():
                    match = re.search(r'(?:/d/|id=)([\w-]+)', gdrive_search_url)
                    drive_id = match.group(1) if match else ""
                    
                    if drive_id:
                        try:
                            import requests
                            direct_dl_url = f"https://drive.google.com/uc?export=download&id={drive_id}"
                            res = requests.get(direct_dl_url)
                            if res.status_code == 200 and 'text/html' not in res.headers.get('Content-Type', ''):
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

                with c1: 
                    view_clicked = st.button("Preview File", key=f"btn_view_{path_key}", use_container_width=True, disabled=(not binary_data and not drive_id))
                
                with c2: 
                    if binary_data:
                        st.download_button(label="Direct Download", data=binary_data, file_name=doc['filename'], mime="application/octet-stream", key=f"btn_dl_{path_key}", use_container_width=True)
                    elif drive_id:
                        st.link_button("Open in Drive", url=f"https://drive.google.com/file/d/{drive_id}/view", use_container_width=True)
                    else:
                        st.button("Direct Download", key=f"btn_dl_{path_key}_disabled", use_container_width=True, disabled=True)
                
                if (view_clicked or st.session_state.get(f"keep_view_{path_key}", False)):
                    if drive_id and gdrive_fetch_error:
                        st.info("File is too large for direct preview. Click 'Open in Drive' to view.")
                    elif binary_data:
                        st.session_state[f"keep_view_{path_key}"] = True
                        st.markdown("<div class='view-frame'>", unsafe_allow_html=True)
                        ext = doc['filename'].lower().split('.')[-1]
                        if ext == 'pdf':
                            base64_pdf = base64.b64encode(binary_data).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="650" type="application/pdf"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.image(binary_data, use_container_width=True)
                        
                        if st.button("Close File Preview", key=f"close_{path_key}"):
                            st.session_state[f"keep_view_{path_key}"] = False
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<hr>", unsafe_allow_html=True)

    # --- MODE 2: MERGE PAGES ---
    elif app_mode == "MERGE PAGES":
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            from PyPDF2 import PdfReader, PdfWriter

        st.markdown("<h3 style='margin:0; font-weight:700;' class='theme-text'>Multi-Page Compilation Console</h3>", unsafe_allow_html=True)
        st.markdown("<p class='theme-text-muted'>Merge multiple disconnected scan pages into a single, comprehensive student document safely.</p>", unsafe_allow_html=True)
        
        file_options = {f"{f['year']} / {f['grade']} / {f['adviser']} ➔ {f['filename']}": f for f in all_files}
        selected_to_merge = st.multiselect("Select the pages you want to compile (order matters):", list(file_options.keys()))
        
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
        
        if st.button("Compile Selected Pages Now", use_container_width=True):
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
                    
                    st.session_state['compiled_pdf_path'] = output_path
                    st.session_state['compiled_pdf_filename'] = output_filename
                    st.session_state['show_preview'] = True
                    
                except Exception as e:
                    st.error(f"Error compiling files: {e}")

        if 'compiled_pdf_path' in st.session_state and os.path.exists(st.session_state['compiled_pdf_path']):
            current_path = st.session_state['compiled_pdf_path']
            current_filename = st.session_state['compiled_pdf_filename']
            
            if 'show_preview' not in st.session_state:
                st.session_state['show_preview'] = True
                
            try:
                reader = PdfReader(current_path)
                total_pages = len(reader.pages)
                
                st.markdown("---")
                st.markdown("<h3 class='theme-text'>🛠️ Page Management & Actions</h3>", unsafe_allow_html=True)
                
                pages_to_delete = st.multiselect(
                    f"Select pages to remove from this compiled document (Total pages: {total_pages}):",
                    options=list(range(1, total_pages + 1)),
                    format_func=lambda x: f"Page {x}"
                )
                
                if pages_to_delete:
                    if len(pages_to_delete) >= total_pages:
                        st.error("Operation Denied: You cannot delete all pages from the document.")
                    elif st.button("Confirm and Remove Selected Pages", type="primary", use_container_width=True):
                        writer = PdfWriter()
                        indices_to_delete = [p - 1 for p in pages_to_delete]
                        
                        for idx in range(total_pages):
                            if idx not in indices_to_delete:
                                writer.add_page(reader.pages[idx])
                        
                        with open(current_path, "wb") as f_out:
                            writer.write(f_out)
                        
                        log_action("admin", "EDIT_DOCUMENTS", f"Removed pages {pages_to_delete} from {current_filename}")
                        st.success("Selected pages removed successfully from the file!")
                        st.rerun()
                
                with open(current_path, "rb") as f:
                    st.download_button(
                        label="Download Final PDF",
                        data=f,
                        file_name=current_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                hdr_col1, hdr_col2 = st.columns([0.9, 0.1])
                with hdr_col1:
                    st.markdown("<h4 style='margin:0; padding-top:4px;' class='theme-text'>📄 Live PDF Document Preview</h4>", unsafe_allow_html=True)
                with hdr_col2:
                    icon = "➖" if st.session_state['show_preview'] else "🔍"
                    if st.button(icon, help="Toggle Preview Window Display", key="toggle_preview_btn"):
                        st.session_state['show_preview'] = not st.session_state['show_preview']
                        st.rerun()
                
                if st.session_state['show_preview']:
                    with open(current_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.info("Preview hidden. Click the icon above to expand.")
                    
            except Exception as e:
                st.error(f"Error managing pages: {e}")

    # --- MODE 3: RELEASED & TAGGED RECORDS ---
    elif app_mode == "RELEASED & TAGGED RECORDS":
        import shutil
        
        SAFE_FOLDER = "my_saved_tags"
        os.makedirs(SAFE_FOLDER, exist_ok=True)
        safe_backup_path = os.path.join(SAFE_FOLDER, "permanent_tags_backup.csv")
        
        st.markdown("<h2 style='margin:0; font-weight:700; color:var(--accent-blue);'>📋 List of Released & Tagged Files</h2>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:14px;' class='theme-text-muted'>View your tagged documents and protect your data before changing or updating your application code.</p>", unsafe_allow_html=True)
        st.markdown("---")

        if os.path.exists(TAGS_FILE):
            df = pd.read_csv(TAGS_FILE)
            filtered_df = df[(df['status'] == 'Released') | (df['tags'].notna() & (df['tags'] != ''))].copy()
            
            total_released = len(filtered_df[filtered_df['status'] == 'Released'])
            total_tagged = len(filtered_df[filtered_df['tags'].notna() & (filtered_df['tags'] != '')])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Number of Released Files", total_released)
            with col2:
                st.metric("Number of Tagged Files", total_tagged)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not filtered_df.empty:
                filtered_df['File Name'] = filtered_df['full_path'].apply(lambda x: os.path.basename(x))
                display_cols = ['File Name', 'tags', 'status']
                if 'purpose' in filtered_df.columns:
                    display_cols.append('purpose')
                
                st.markdown("<h4 class='theme-text'>🔍 Current Records</h4>", unsafe_allow_html=True)
                st.dataframe(
                    filtered_df[display_cols].rename(columns={'tags': 'Tags Given', 'status': 'Current Status', 'purpose': 'Reason for Release'}),
                    use_container_width=True
                )
            else:
                st.info("💡 No files have been released or tagged yet.")
        else:
            st.warning("⚠️ Cannot find the main data file.")

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin:0; font-weight:700;' class='theme-text'>🛡️ Code Update Protection Tools</h3>", unsafe_allow_html=True)
        box1, box2 = st.columns(2)

        with box1:
            with st.container(border=True):
                st.markdown("<h3 class='theme-text'>🔒 Step 1: Save My Tags</h3>", unsafe_allow_html=True)
                st.markdown("<p class='theme-text-muted'>Click this button <b>BEFORE</b> you update your code. It makes a safe copy of all your tags so they won't get deleted.</p>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Click Here to Save My Tags", key="save_tags_btn", use_container_width=True):
                    if os.path.exists(TAGS_FILE):
                        shutil.copy2(TAGS_FILE, safe_backup_path)
                        st.toast("Tags saved safely!", icon="🔒")
                        st.success("🎉 **Success!** Your tags are now locked up safely in the backup folder.")
                    else:
                        st.error("Nothing to save yet. You haven't added any tags.")

        with box2:
            with st.container(border=True):
                st.markdown("<h3 class='theme-text'>🔓 Step 2: Bring Back My Tags</h3>", unsafe_allow_html=True)
                st.markdown("<p class='theme-text-muted'>Click this button <b>AFTER</b> you update your code. It loads all your saved tags back into the fresh system.</p>", unsafe_allow_html=True)
                
                if os.path.exists(safe_backup_path):
                    st.markdown("<span style='color:#31A24C; font-weight:600; font-size:12px;'>🟢 Ready: Saved copy is found.</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#F0A70A; font-weight:600; font-size:12px;'>⚪ Empty: You haven't saved any copy yet.</span>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Click Here to Load My Tags", key="load_tags_btn", type="primary", use_container_width=True):
                    if os.path.exists(safe_backup_path):
                        try:
                            shutil.copy2(safe_backup_path, TAGS_FILE)
                            log_action("admin", "DATABASE_RESTORE", "Restored tags from backup folder.")
                            st.toast("Tags loaded!", icon="🔄")
                            st.success("🤝 **Success!** All your saved tags and reasons have been successfully brought back.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not load data: {e}")
                    else:
                        st.error("Failed: No saved tags found. Did you click Step 1 first?")

    # --- MODE 4: SYSTEM LOGS AND SETTINGS ---
    elif app_mode == "SYSTEM LOGS AND SETTINGS":
        st.markdown("<h3 style='margin:0; font-weight:700;' class='theme-text'>System Settings, Logs & Report Export Desk</h3>", unsafe_allow_html=True)
        st.markdown("<p class='theme-text-muted'>Manage system configurations, clear cache, export database metrics, and review security audit logs.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        c_set1, c_set2 = st.columns(2)
        
        with c_set1:
            st.markdown("""
            <div style='background-color:var(--card-bg); padding:20px; border-radius:8px; border:1px solid var(--metric-border); height: 180px;'>
                <h4 style='margin-top:0;' class='theme-text'>Export Sheet Data Reports</h4>
                <p class='theme-text-muted' style='font-size:13px;'>Download all metadata tags, document statuses, and file locations as a standardized CSV file.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Generate CSV Spreadsheet Report", use_container_width=True):
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
                        st.download_button("Click Here to Download Compiled File", data=f_dl.read(), file_name=report_file, mime="text/csv", use_container_width=True)

        with c_set2:
            st.markdown("""
            <div style='background-color:var(--danger-bg); padding:20px; border-radius:8px; border:1px solid var(--danger-border); height: 180px;'>
                <h4 style='margin-top:0; color:#DC2626;'>Clear Session Search Cache</h4>
                <p style='color:var(--text-muted); font-size:13px;'>Wipe the search history footprints from your current administrative session.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.search_history:
                st.markdown('<div class="btn-danger">', unsafe_allow_html=True)
                if st.button("Clear Session Cache Now", use_container_width=True):
                    st.session_state.search_history = []
                    st.success("Session footprints successfully cleared.")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.button("Session Cache Empty", disabled=True, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)
        
        c_log1, c_log2 = st.columns([3, 1])
        with c_log1:
            st.markdown("<h4 class='theme-text'>Security & Operations Audit Trail Logs</h4>", unsafe_allow_html=True)
        with c_log2:
            if os.path.exists(LOG_FILE) and st.button("Clear All Logs", type="primary"):
                with open(LOG_FILE, "w") as f:
                    f.write("Timestamp,User,Action,Details\n")
                st.rerun()
        
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode="r", encoding="utf-8") as f_log:
                log_data = f_log.readlines()
            
            st.markdown("<div style='max-height: 400px; overflow-y: auto; background-color: var(--card-bg); padding: 15px; border-radius: 8px; border: 1px solid var(--metric-border);'>", unsafe_allow_html=True)
            for row in reversed(log_data[1:]):
                r_parts = row.strip().split(",")
                if len(r_parts) >= 4:
                    st.markdown(f"<span style='color:var(--text-muted); font-family:monospace; font-size:12px;'>[{r_parts[0]}]</span> <span style='color:var(--accent-blue); font-weight:600; font-size:13px;'>{r_parts[1]}</span> <span style='color:#10B981; font-size:13px;'>[{r_parts[2]}]</span> <span class='theme-text' style='font-size:13px;'>{','.join(r_parts[3:])}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.download_button("Download Full Audit Log (.csv)", data="".join(log_data), file_name="Audit_Trail_Log.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("No system activity logged yet.")

def render_footer():
    deped_logo_html = ""
    logo_path = "DEPED_QUEZON_LOGO.PNG"
    
    # Check if the logo file exists to encode it
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
            
        # Removed absolute positioning, set a clean height, and added a bottom margin
        deped_logo_html = f'<img src="data:image/png;base64,{logo_data}" style="height: 55px; object-fit: contain; margin-bottom: 8px;" alt="DepEd Quezon Logo">'

    st.markdown(f"""
        <style>
            .footer {{
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                text-align: center;
                padding: 10px 10px 12px 10px;
                font-size: 12px;
                color: var(--text-muted);
                background-color: var(--main-bg); 
                border-top: 1px solid var(--metric-border);
                z-index: 1000;
                display: flex;
                flex-direction: column; /* This stacks the logo and text vertically */
                align-items: center;    /* Centers them horizontally */
                justify-content: center;
            }}
        </style>
        <div class="footer">
            {deped_logo_html}
            <p style="margin: 0; z-index: 1001; position: relative;">CNHS Form 137 Archive System © 2026 | Calauag National High School | Records Management Office</p>
        </div>
    """, unsafe_allow_html=True)

render_footer()

if not st.session_state.logged_in:
    login_page()
else:
    main_app()