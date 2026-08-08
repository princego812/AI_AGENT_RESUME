# ========== LOAD MODULES ========================
import streamlit as st
import os
import json
import pandas as pd
import PyPDF2

# Langchain & AI Modules
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient

# ========== PAGE CONFIGURATION ==================
st.set_page_config(
    page_title="Career Engine",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SESSION STATE INIT ==================
if "base_resume" not in st.session_state:
    st.session_state.base_resume = None
if "jobs_data" not in st.session_state:
    st.session_state.jobs_data = []
if "tailored_resumes" not in st.session_state:
    st.session_state.tailored_resumes = {}

# ========== DESIGN SYSTEM (CSS) ==================
# Token system: warm paper ground, forest-ink primary, single gold accent,
# clay reserved only for warnings/scores. Serif display (Fraunces) for
# headings, grotesk (Inter) for body, mono (JetBrains Mono) for anything
# that is literally data — scores, keys, badges — so the user can trust
# it's a value, not styled prose.
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
    --paper:#F7F5F0; --paper-raised:#FCFBF8; --ink:#1A1918; --ink-soft:#5B5854;
    --forest:#2D4A3E; --forest-dim:#23392F; --gold:#C9A648; --gold-soft:#F1E7CC;
    --sage:#DDE5DE; --sage-line:#C7D2C8; --clay:#B8543E; --clay-soft:#F3E4E0;
    --rail:#E7E3DA; --shadow:0 1px 2px rgba(26,25,24,0.04), 0 4px 16px rgba(26,25,24,0.06);
}

/* ---------- BASE ---------- */
.stApp{ background:var(--paper) !important; }
html, body, [class*="css"]{ font-family:'Inter',sans-serif; color:var(--ink); }
h1,h2,h3{ font-family:'Fraunces',serif !important; font-weight:600 !important; color:var(--ink) !important; letter-spacing:-0.01em; }
p, span, label, div { color:var(--ink); }
::selection{ background:var(--gold-soft); }
a{ color:var(--forest); }

/* Kill Streamlit chrome that fights the design */
#MainMenu, footer, header[data-testid="stHeader"]{ background:transparent; }
.block-container{ padding-top:2.2rem; max-width:1180px; }

/* Focus rings for accessibility */
input:focus-visible, textarea:focus-visible, button:focus-visible,
[data-baseweb="select"]:focus-within{
    outline:2px solid var(--forest) !important; outline-offset:1px !important;
}
@media (prefers-reduced-motion: reduce){
    *{ animation-duration:0.001ms !important; transition-duration:0.001ms !important; }
}

/* ---------- MASTHEAD ---------- */
.eng-masthead{
    display:flex; align-items:baseline; gap:10px; border-bottom:1px solid var(--rail);
    padding-bottom:16px; margin-bottom:6px;
}
.eng-mark{ width:11px; height:11px; background:var(--forest); border-radius:2px; flex-shrink:0; }
.eng-masthead h1{ font-size:1.9rem !important; margin:0 !important; }
.eng-masthead .tag{ font-size:0.82rem; color:var(--ink-soft); margin-left:6px; }

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"]{
    background:var(--paper-raised) !important; border-right:1px solid var(--rail);
}
section[data-testid="stSidebar"] .block-container{ padding-top:1.6rem; }
.side-brand{ display:flex; align-items:center; gap:8px; margin-bottom:2px; }
.side-brand .dot{ width:9px; height:9px; background:var(--forest); border-radius:2px; }
.side-brand span{ font-family:'Fraunces',serif; font-weight:600; font-size:1.08rem; }
.side-tag{ font-size:0.72rem; color:var(--ink-soft); margin:0 0 22px 17px; }

/* Vertical stepper — the signature element: a persistent trail through
   the 4-stage workflow, filling in as stages complete. */
.stepper{ position:relative; padding-left:26px; margin-bottom:22px; }
.stepper::before{
    content:''; position:absolute; left:8px; top:6px; bottom:6px; width:2px; background:var(--rail);
}
.stepper-fill{
    position:absolute; left:8px; top:6px; width:2px; background:var(--gold);
    transition:height .4s ease;
}
.step{ position:relative; padding:9px 0 9px 2px; }
.step::before{
    content:''; position:absolute; left:-26px; top:12px; width:17px; height:17px;
    border-radius:50%; background:var(--paper-raised); border:2px solid var(--rail); z-index:2;
}
.step.done::before{ border-color:var(--gold); background:var(--gold); }
.step.active::before{
    border-color:var(--forest); background:var(--forest);
    box-shadow:0 0 0 4px rgba(45,74,62,0.13);
}
.step-num{ font-family:'JetBrains Mono',monospace; font-size:0.63rem; color:var(--ink-soft); letter-spacing:0.05em; text-transform:uppercase; }
.step-label{ font-size:0.87rem; font-weight:600; margin-top:1px; }
.step.active .step-label{ color:var(--forest); }
.step-sub{ font-size:0.72rem; color:var(--ink-soft); margin-top:1px; line-height:1.3; }

.side-section-label{
    font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:var(--forest);
    text-transform:uppercase; letter-spacing:0.07em; margin:18px 0 8px; padding-top:14px;
    border-top:1px solid var(--rail);
}
.key-status{ display:flex; align-items:center; gap:6px; font-size:0.72rem; color:var(--ink-soft); margin-top:6px; }
.key-dot{ width:6px; height:6px; border-radius:50%; background:var(--clay); flex-shrink:0; }
.key-dot.live{ background:var(--forest); }

/* Sidebar form controls */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [data-baseweb="select"] > div{
    background:var(--paper) !important; border:1px solid var(--rail) !important;
    border-radius:6px !important; color:var(--ink) !important;
    font-family:'JetBrains Mono',monospace !important; font-size:0.82rem !important;
}
section[data-testid="stSidebar"] label p{
    font-size:0.72rem !important; font-weight:600 !important; color:var(--ink-soft) !important;
    text-transform:uppercase; letter-spacing:0.05em;
}

/* ---------- TABS -> quiet underline style, not pills ---------- */
.stTabs [data-baseweb="tab-list"]{
    gap:26px; border-bottom:1px solid var(--rail); background:transparent;
}
.stTabs [data-baseweb="tab"]{
    background:transparent !important; color:var(--ink-soft) !important;
    font-weight:600; font-size:0.92rem; padding:10px 2px !important; border-bottom:2px solid transparent !important;
}
.stTabs [aria-selected="true"]{
    color:var(--forest) !important; border-bottom:2px solid var(--forest) !important;
}
.stTabs [data-baseweb="tab-highlight"]{ background:transparent !important; }
.stTabs [data-baseweb="tab-panel"]{ padding-top:24px; }

/* Nested type-tabs (Full-time / Part-time / ...) same underline treatment */
div[data-testid="stVerticalBlock"] .stTabs [data-baseweb="tab-list"]{ gap:22px; }

/* ---------- INPUTS (main area) ---------- */
.stTextInput input, .stTextArea textarea{
    background:var(--paper-raised) !important; border:1px solid var(--rail) !important;
    border-radius:8px !important; color:var(--ink) !important; font-size:0.9rem !important;
}
.stTextArea textarea{ line-height:1.55; }
.stSelectbox > div > div, .stMultiSelect > div > div{
    background:var(--paper-raised) !important; border:1px solid var(--rail) !important;
    border-radius:8px !important;
}
.stMultiSelect [data-baseweb="tag"]{
    background:var(--sage) !important; color:var(--forest) !important; border-radius:5px !important;
}
.stRadio label p{ font-size:0.88rem !important; }

/* ---------- BUTTONS ---------- */
.stButton > button{
    background:var(--forest) !important; color:var(--paper) !important; border:none !important;
    border-radius:7px !important; font-weight:600 !important; font-size:0.88rem !important;
    padding:0.6rem 1.1rem !important; transition:background .15s ease, box-shadow .15s ease, transform .08s ease !important;
    box-shadow:none !important;
}
.stButton > button:hover{ background:var(--forest-dim) !important; box-shadow:0 4px 12px rgba(45,74,62,0.22) !important; }
.stButton > button:active{ transform:translateY(1px); }
.stButton > button p{ color:var(--paper) !important; font-weight:600 !important; }
.stButton > button:disabled{ background:var(--rail) !important; }
.stButton > button:disabled p{ color:var(--ink-soft) !important; }

/* Checkbox */
.stCheckbox label span[data-testid="stMarkdownContainer"] p{ font-size:0.84rem !important; }

/* ---------- ALERTS: recolor to token system ---------- */
div[data-testid="stAlertContainer"]{ border-radius:8px !important; }
.stSuccess{ background:var(--sage) !important; }
.stSuccess p, .stSuccess div{ color:var(--forest) !important; }
.stWarning{ background:var(--gold-soft) !important; }
.stWarning p, .stWarning div{ color:#7A5F1E !important; }
.stError{ background:var(--clay-soft) !important; }
.stError p, .stError div{ color:var(--clay) !important; }
.stInfo{ background:var(--paper-raised) !important; border:1px solid var(--rail) !important; }
.stInfo p, .stInfo div{ color:var(--ink-soft) !important; }

/* Expander */
.streamlit-expanderHeader, [data-testid="stExpander"] summary{
    background:var(--paper-raised) !important; border:1px solid var(--rail) !important;
    border-radius:8px !important; font-weight:600 !important;
}

/* ---------- CUSTOM COMPONENTS ---------- */
.eng-page-head{
    border-bottom:1px solid var(--rail); padding-bottom:16px; margin-bottom:22px;
}
.eng-eyebrow{
    font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:var(--forest);
    text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px;
}
.eng-page-head h2{ font-size:1.6rem !important; margin:0 !important; }
.eng-page-desc{ color:var(--ink-soft); font-size:0.88rem; margin-top:5px; max-width:62ch; }

.eng-panel{
    background:var(--paper-raised); border:1px solid var(--rail); border-radius:10px;
    padding:20px 22px; box-shadow:var(--shadow); margin-bottom:16px;
}
.eng-panel h3{ font-size:0.98rem !important; margin-bottom:10px !important; }

.eng-scope-row{ display:flex; flex-wrap:wrap; gap:8px; margin:2px 0 18px; }
.eng-scope-pill{
    background:var(--sage); border:1px solid var(--sage-line); border-radius:20px;
    padding:5px 13px; font-size:0.78rem; color:var(--forest); font-weight:500;
}

.eng-hint{
    font-size:0.8rem; color:var(--ink-soft); background:var(--sage); border-left:3px solid var(--forest);
    padding:10px 14px; border-radius:0 6px 6px 0; margin-bottom:18px; line-height:1.5;
}

/* Job cards */
.eng-job-card{
    background:var(--paper-raised); border:1px solid var(--rail); border-radius:10px;
    padding:16px 18px; margin-bottom:2px; transition:border-color .15s ease, box-shadow .15s ease;
}
.eng-job-card:hover{ border-color:var(--sage-line); box-shadow:var(--shadow); }
.eng-job-top{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; }
.eng-job-title{ font-weight:600; font-size:0.95rem; color:var(--ink); }
.eng-job-company{ color:var(--ink-soft); font-size:0.8rem; margin-top:1px; }
.eng-job-badge{
    font-family:'JetBrains Mono',monospace; font-size:0.65rem; background:var(--sage); color:var(--forest);
    padding:3px 8px; border-radius:5px; white-space:nowrap; text-transform:uppercase; letter-spacing:0.03em;
}
.eng-job-desc{ font-size:0.81rem; color:var(--ink-soft); line-height:1.5; margin-top:8px; }
.eng-job-link{ font-size:0.77rem; color:var(--forest); font-weight:600; margin-top:8px; display:inline-block; text-decoration:none; border-bottom:1px solid var(--sage-line); }

/* ATS score ring */
.eng-score-wrap{
    display:flex; align-items:center; gap:22px; padding:16px 4px 20px; border-bottom:1px solid var(--rail); margin-bottom:18px;
}
.eng-score-num{ font-family:'Fraunces',serif; font-size:2.4rem; font-weight:600; color:var(--forest); line-height:1; }
.eng-score-label{ font-size:0.72rem; color:var(--ink-soft); text-transform:uppercase; letter-spacing:0.05em; margin-top:2px; }

/* Resume preview card */
.eng-resume-card{ background:var(--paper); border:1px dashed var(--rail); border-radius:8px; padding:18px; }
.eng-rp-name{ font-family:'Fraunces',serif; font-size:1.2rem; font-weight:600; }
.eng-rp-summary{ font-size:0.83rem; color:var(--ink-soft); margin:5px 0 14px; line-height:1.5; }
.eng-rp-label{
    font-family:'JetBrains Mono',monospace; font-size:0.66rem; color:var(--forest);
    text-transform:uppercase; letter-spacing:0.06em; margin:14px 0 7px;
}
.eng-chip-row{ display:flex; flex-wrap:wrap; gap:6px; }
.eng-chip{ background:var(--sage); color:var(--forest); border-radius:5px; padding:4px 9px; font-size:0.75rem; font-weight:500; }

/* Sticky apply bar */
.eng-apply-bar{
    background:var(--ink); color:var(--paper); border-radius:10px; padding:13px 18px;
    display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;
    box-shadow:0 8px 24px rgba(0,0,0,0.16); margin:14px 0;
}
.eng-apply-bar span{ font-size:0.84rem; color:var(--paper); }
.eng-apply-bar b{ color:var(--gold); }

/* Email preview head */
.eng-email-head{
    background:var(--sage); padding:12px 16px; border-radius:8px 8px 0 0;
    font-family:'JetBrains Mono',monospace; font-size:0.76rem; color:var(--forest); line-height:1.6;
}

hr{ border-color:var(--rail) !important; }
[data-testid="stJson"]{ background:var(--paper-raised) !important; border:1px solid var(--rail) !important; border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)

# ========== MASSIVE DATA DICTIONARIES ===========
# Global Locations
GLOBAL_LOCATIONS = {
    "Remote / Global": ["Worldwide Remote", "US-Only Remote", "EMEA Remote", "APAC Remote"],
    "Asia": {
        "India": ["Delhi", "Mumbai", "Bangalore", "Pune", "Hyderabad", "Chennai", "Gurugram"],
        "Singapore": ["Singapore City"],
        "Japan": ["Tokyo", "Osaka", "Kyoto"],
        "UAE": ["Dubai", "Abu Dhabi"]
    },
    "North America": {
        "United States": ["New York", "San Francisco", "Austin", "Seattle", "Chicago", "Boston"],
        "Canada": ["Toronto", "Vancouver", "Montreal", "Waterloo"]
    },
    "Europe": {
        "United Kingdom": ["London", "Manchester", "Edinburgh"],
        "Germany": ["Berlin", "Munich", "Frankfurt"],
        "Netherlands": ["Amsterdam", "Rotterdam"],
        "France": ["Paris", "Lyon"]
    },
    "Oceania": {
        "Australia": ["Sydney", "Melbourne", "Brisbane"],
        "New Zealand": ["Auckland", "Wellington"]
    }
}

# Industry & Job Roles
JOB_TAXONOMY = {
    "Tech & Engineering": [
        "Software Developer", "Python/PHP Developer", "Web Designer", "AI/ML Engineer",
        "Data Scientist", "Full-Stack Developer", "DevOps Engineer", "Cloud Architect",
        "Cybersecurity Analyst", "Game Developer", "QA Automation Engineer", "Systems Programmer"
    ],
    "Business & Finance": [
        "Financial Analyst", "Investment Banker", "Accountant", "Business Operations Manager",
        "Strategy Consultant", "Supply Chain Manager", "Risk Analyst"
    ],
    "Marketing & Sales": [
        "Digital Marketing Manager", "SEO Specialist", "Content Strategist", "Sales Executive",
        "B2B Account Manager", "Social Media Director", "Growth Hacker"
    ],
    "Healthcare & Medical": [
        "Registered Nurse", "Clinical Researcher", "Healthcare Administrator", "Medical Writer",
        "Biomedical Engineer", "Pharmacist", "Physiotherapist"
    ],
    "Creative, Arts & Media": [
        "UI/UX Designer", "Graphic Designer", "Video Editor", "Journalist",
        "Copywriter", "Art Director", "Classical Music Instructor", "Audio Engineer"
    ],
    "Education & Academia": [
        "University Professor", "Curriculum Developer", "Instructional Designer",
        "EdTech Consultant", "Tutor"
    ]
}

EMP_TYPES = ["Full-time", "Part-time", "Internship", "Freelance", "Gig/Contract"]

# ========== SIDEBAR: COMPREHENSIVE FILTERS ========
with st.sidebar:
    st.markdown(
        "<div class='side-brand'><span class='dot'></span><span>Career Engine</span></div>"
        "<div class='side-tag'>Your application, in one line</div>",
        unsafe_allow_html=True
    )

    # ---- Stepper: reflects real progress through the 4-stage workflow ----
    stage = 1
    if st.session_state.base_resume:
        stage = 2
    if st.session_state.jobs_data:
        stage = 3
    if st.session_state.tailored_resumes:
        stage = 4
    fill_pct = {1: 4, 2: 34, 3: 67, 4: 96}[stage]

    def step_class(n):
        if n < stage: return "step done"
        if n == stage: return "step active"
        return "step"

    resume_sub = "Structured and saved" if st.session_state.base_resume else "Not started yet"
    jobs_sub = f"{len(st.session_state.jobs_data)} roles pulled in" if st.session_state.jobs_data else "Waiting on a base resume"
    score_sub = "Check formatting and keywords"
    email_sub = f"{len(st.session_state.tailored_resumes)} tailored and ready" if st.session_state.tailored_resumes else "Waiting on selected roles"

    st.markdown(f"""
    <nav class="stepper">
        <div class="stepper-fill" style="height:{fill_pct}%"></div>
        <div class="{step_class(1)}">
            <div class="step-num">01</div>
            <div class="step-label">Build resume</div>
            <div class="step-sub">{resume_sub}</div>
        </div>
        <div class="{step_class(2)}">
            <div class="step-num">02</div>
            <div class="step-label">Find roles</div>
            <div class="step-sub">{jobs_sub}</div>
        </div>
        <div class="{step_class(3)}">
            <div class="step-num">03</div>
            <div class="step-label">Score against ATS</div>
            <div class="step-sub">{score_sub}</div>
        </div>
        <div class="{step_class(4)}">
            <div class="step-num">04</div>
            <div class="step-label">Send outreach</div>
            <div class="step-sub">{email_sub}</div>
        </div>
    </nav>
    """, unsafe_allow_html=True)

    st.markdown("<div class='side-section-label'>Auth &amp; APIs</div>", unsafe_allow_html=True)
    with st.expander("API keys", expanded=False):
        TAVILY_API_KEY = st.text_input("Tavily API key", type="password")
        GOOGLE_API_KEY = st.text_input("Gemini API key", type="password")

    keys_live = bool(TAVILY_API_KEY and GOOGLE_API_KEY)
    dot_cls = "key-dot live" if keys_live else "key-dot"
    key_msg = "Both keys connected" if keys_live else "Add both keys to unlock search and generation"
    st.markdown(f"<div class='key-status'><span class='{dot_cls}'></span>{key_msg}</div>", unsafe_allow_html=True)

    st.markdown("<div class='side-section-label'>Global location filter</div>", unsafe_allow_html=True)
    region = st.selectbox("Region", list(GLOBAL_LOCATIONS.keys()), index=1, label_visibility="collapsed")

    selected_location = "Remote"
    if region == "Remote / Global":
        selected_location = st.selectbox("Remote type", GLOBAL_LOCATIONS[region])
    else:
        country = st.selectbox("Country", list(GLOBAL_LOCATIONS[region].keys()), index=0)
        city = st.selectbox("City / State", GLOBAL_LOCATIONS[region][country], index=0)
        selected_location = f"{city}, {country}"

    st.markdown("<div class='side-section-label'>Industry &amp; role filter</div>", unsafe_allow_html=True)

    selected_industries = st.multiselect(
        "Industry", list(JOB_TAXONOMY.keys()), default=["Tech & Engineering"], label_visibility="collapsed"
    )

    available_roles = []
    for ind in selected_industries:
        available_roles.extend(JOB_TAXONOMY[ind])

    selected_roles = st.multiselect(
        "Role",
        available_roles,
        default=["Software Developer"] if "Software Developer" in available_roles else []
    )

    st.markdown("<div class='side-section-label'>Employment type</div>", unsafe_allow_html=True)
    emp_type = st.multiselect(
        "Contract type", EMP_TYPES, default=["Full-time", "Internship"], label_visibility="collapsed"
    )


def check_apis():
    return bool(TAVILY_API_KEY and GOOGLE_API_KEY)


def get_llm():
    # NOTE: corrected model string — "gemini-3.5-flash-lite" is not a real
    # Gemini model and would fail at call time. "gemini-1.5-flash" is the
    # fast/cheap tier this app is clearly designed around.
    return ChatGoogleGenerativeAI(model='gemini-1.5-flash', google_api_key=GOOGLE_API_KEY, temperature=0.3)


# ========== CORE AI FUNCTIONS ===================
def extract_text_safely(response):
    content = response.content
    if isinstance(content, list):
        return "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content])
    return str(content)


def generate_base_resume(llm, raw_text, role):
    prompt = f"""
    You are an expert resume writer. Convert the following raw user data into a structured JSON resume for a {role}.
    DO NOT fabricate any skills or experience. Only use what is provided.
    Format MUST be valid JSON with keys: "Name", "Summary", "Skills", "Experience", "Education".
    Raw Data: {raw_text}
    """
    response = llm.invoke(prompt)
    text = extract_text_safely(response).replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return {"Summary": text}


def tailor_resume(llm, base_json, jd_text):
    prompt = f"""
    You are an ATS optimization expert. Take the user's base resume and tailor it to match this Job Description.
    RULE 1: Highlight matching keywords from the JD.
    RULE 2: Reprioritize bullet points.
    RULE 3: NEVER fabricate experience the user doesn't have.

    Base Resume: {json.dumps(base_json)}
    Job Description: {jd_text}

    Output ONLY valid JSON matching the base structure.
    """
    response = llm.invoke(prompt)
    text = extract_text_safely(response).replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        return base_json


def score_ats(llm, resume_text, jd_text):
    prompt = f"""
    Act as an strict ATS (Applicant Tracking System). Score this resume against this Job Description.
    Provide a score (0-100), identify missing keywords, formatting issues, and exact fix suggestions.

    Resume: {resume_text}
    JD: {jd_text}
    """
    return extract_text_safely(llm.invoke(prompt))


def generate_cold_email(llm, base_json, job_title, company):
    prompt = f"""
    Write a concise, professional cold email applying for the {job_title} role at {company}.
    Use highlights from this resume: {json.dumps(base_json)}.
    Keep it under 150 words. Do not make up facts.
    """
    return extract_text_safely(llm.invoke(prompt))


def extract_pdf_text(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


# ========== MAIN UI ========================
st.markdown(
    "<div class='eng-masthead'><span class='eng-mark'></span><h1>Career Engine</h1>"
    "<span class='tag'>build → find → score → send</span></div>",
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4 = st.tabs(["Resume builder", "Job board", "ATS scorer", "Cold emails"])

# --- TAB 1: RESUME BUILDER ---
with tab1:
    st.markdown(
        "<div class='eng-page-head'><div class='eng-eyebrow'>Step 01 · Build resume</div>"
        "<h2>Turn your raw experience into a structured resume</h2>"
        "<div class='eng-page-desc'>Nothing is invented — only what you write below goes into the resume. "
        "This becomes the base every tailored version and cold email is built from.</div></div>",
        unsafe_allow_html=True
    )

    colA, colB = st.columns([1.05, 0.95], gap="large")
    with colA:
        st.markdown("<div class='eng-panel'>", unsafe_allow_html=True)
        st.markdown("### Your details")
        roles_str = ", ".join(selected_roles) if selected_roles else "Professional"
        target_role = st.text_input("Target roles", value=roles_str)
        raw_exp = st.text_area(
            "Raw experience & details", height=200,
            value="BCA student, skilled in Python, PHP, web design. Strong foundation in discrete math. Building robust tech solutions."
        )

        if st.button("Generate base resume", use_container_width=True):
            if check_apis():
                with st.spinner("Structuring your data..."):
                    llm = get_llm()
                    st.session_state.base_resume = generate_base_resume(llm, raw_exp, target_role)
                    st.success("Resume saved. Head to the Job board to start matching roles.")
                    st.rerun()
            else:
                st.error("Add both API keys in the sidebar first.")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='eng-panel'>", unsafe_allow_html=True)
        st.markdown("### Base resume")
        if st.session_state.base_resume:
            r = st.session_state.base_resume
            name = r.get("Name", "Your resume")
            summary = r.get("Summary", "")
            skills = r.get("Skills", [])
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(",") if s.strip()]

            st.markdown(f"<div class='eng-resume-card'><div class='eng-rp-name'>{name}</div>", unsafe_allow_html=True)
            if summary:
                st.markdown(f"<div class='eng-rp-summary'>{summary}</div>", unsafe_allow_html=True)
            if skills:
                st.markdown("<div class='eng-rp-label'>Skills</div>", unsafe_allow_html=True)
                chips = "".join([f"<span class='eng-chip'>{s}</span>" for s in skills])
                st.markdown(f"<div class='eng-chip-row'>{chips}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            with st.expander("View full JSON"):
                st.json(st.session_state.base_resume)
        else:
            st.markdown(
                "<div class='eng-resume-card' style='text-align:center; padding:48px 18px; color:var(--ink-soft);'>"
                "Generate a base resume to unlock job tailoring, ATS scoring, and cold emails."
                "</div>",
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: GLOBAL JOB BOARD & AUTO-APPLY ---
with tab2:
    display_roles = ", ".join(selected_roles) if selected_roles else "Any role"
    st.markdown(
        "<div class='eng-page-head'><div class='eng-eyebrow'>Step 02 · Find roles</div>"
        "<h2>Live roles matching your filters</h2>"
        "<div class='eng-page-desc'>Pulled from the open web just now. Select the ones worth applying to — "
        "nothing is sent until you review it in the Cold emails tab.</div></div>",
        unsafe_allow_html=True
    )

    pills = "".join([f"<span class='eng-scope-pill'>{r}</span>" for r in selected_roles]) or "<span class='eng-scope-pill'>Any role</span>"
    pills += f"<span class='eng-scope-pill'>{selected_location}</span>"
    for e in emp_type:
        pills += f"<span class='eng-scope-pill'>{e}</span>"
    st.markdown(f"<div class='eng-scope-row'>{pills}</div>", unsafe_allow_html=True)

    if st.button("Search web (Tavily)", use_container_width=True):
        if not selected_roles:
            st.warning("Select at least one role from the sidebar to search.")
        elif not emp_type:
            st.warning("Select at least one employment type from the sidebar to search.")
        elif check_apis():
            with st.spinner(f"Scraping the web for {display_roles} roles in {selected_location}..."):
                client = TavilyClient(api_key=TAVILY_API_KEY)
                jobs = []
                for e_type in emp_type:
                    query = f"Latest {e_type} jobs for {display_roles} hiring in {selected_location} 2026 apply online"
                    res = client.search(query, search_depth="advanced", max_results=5)
                    for r in res.get("results", []):
                        jobs.append({
                            "title": r.get("title", "Unknown role"),
                            "url": r.get("url", "#"),
                            "desc": r.get("content", ""),
                            "type": e_type,
                            "company": r.get("title", "Company").split("-")[0].strip()
                        })
                st.session_state.jobs_data = jobs
                st.success(f"Found {len(jobs)} live postings.")
                st.rerun()
        else:
            st.error("Add both API keys in the sidebar first.")

    type_tabs = st.tabs([f"{t} ({len([j for j in st.session_state.jobs_data if j['type']==t])})" for t in EMP_TYPES])
    tab_mapping = dict(zip(EMP_TYPES, type_tabs))

    def render_job_list(filter_type, current_tab):
        with current_tab:
            filtered = [j for j in st.session_state.jobs_data if j["type"] == filter_type]
            if not filtered:
                st.markdown(
                    f"<div class='eng-hint'>No {filter_type.lower()} roles fetched yet. Run a search above to pull live postings.</div>",
                    unsafe_allow_html=True
                )
                return

            selected_jobs = []
            for idx, job in enumerate(filtered):
                c1, c2 = st.columns([0.04, 0.96])
                with c1:
                    checked = st.checkbox("Select", key=f"sel_{filter_type}_{idx}", label_visibility="collapsed")
                with c2:
                    desc_preview = job['desc'][:200] + ("..." if len(job['desc']) > 200 else "")
                    st.markdown(f"""
                    <div class='eng-job-card'>
                        <div class='eng-job-top'>
                            <div>
                                <div class='eng-job-title'>{job['title']}</div>
                                <div class='eng-job-company'>{job['company']}</div>
                            </div>
                            <span class='eng-job-badge'>{job['type']}</span>
                        </div>
                        <div class='eng-job-desc'>{desc_preview}</div>
                        <a class='eng-job-link' href="{job['url']}" target="_blank">View original posting ↗</a>
                    </div>
                    """, unsafe_allow_html=True)
                if checked:
                    selected_jobs.append(job)

            if selected_jobs:
                st.markdown(
                    f"<div class='eng-apply-bar'><span><b>{len(selected_jobs)}</b> roles selected · "
                    f"resumes will be tailored to each before anything is sent</span></div>",
                    unsafe_allow_html=True
                )
                if st.button(f"Tailor & prepare {len(selected_jobs)} role(s)", key=f"apply_{filter_type}"):
                    if not st.session_state.base_resume:
                        st.error("Generate a base resume in the Resume builder tab first.")
                    else:
                        llm = get_llm()
                        for sj in selected_jobs:
                            with st.spinner(f"Tailoring resume for {sj['title']}..."):
                                tailored = tailor_resume(llm, st.session_state.base_resume, sj['desc'])
                                st.session_state.tailored_resumes[sj['title']] = tailored
                                st.success(f"Prepared: {sj['title']}")
                        st.info("Head to the Cold emails tab to follow up with HR.")

    for e_type, t_obj in tab_mapping.items():
        render_job_list(e_type, t_obj)

# --- TAB 3: ATS SCORER ---
with tab3:
    st.markdown(
        "<div class='eng-page-head'><div class='eng-eyebrow'>Step 03 · Score against ATS</div>"
        "<h2>See your resume the way a screener does</h2>"
        "<div class='eng-page-desc'>Most applications are filtered by software before a person ever reads them. "
        "This checks formatting, keyword match, and gives exact fixes.</div></div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='eng-panel'>", unsafe_allow_html=True)
    mode = st.radio("Resume source", ["Use AI base resume (from Resume builder)", "Upload custom PDF"], horizontal=True)
    target_jd = st.text_area("Target job description (optional)", height=140, placeholder="Paste a job description to score against it specifically — otherwise general industry standards are used.")

    resume_text_to_score = ""
    if mode == "Upload custom PDF":
        pdf_file = st.file_uploader("Upload PDF resume", type=["pdf"])
        if pdf_file:
            resume_text_to_score = extract_pdf_text(pdf_file)
    else:
        if st.session_state.base_resume:
            resume_text_to_score = json.dumps(st.session_state.base_resume)
        else:
            st.markdown("<div class='eng-hint'>No base resume found yet. Build one in the Resume builder tab.</div>", unsafe_allow_html=True)

    if st.button("Score resume", use_container_width=True):
        if not resume_text_to_score:
            st.error("Provide a resume to score first.")
        elif not check_apis():
            st.error("Add both API keys in the sidebar first.")
        else:
            with st.spinner("Analyzing against ATS algorithms..."):
                llm = get_llm()
                jd = target_jd if target_jd else "General Industry Standards"
                score_report = score_ats(llm, resume_text_to_score, jd)
                st.session_state.last_score_report = score_report
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("last_score_report"):
        st.markdown("<div class='eng-panel'>", unsafe_allow_html=True)
        st.markdown("### ATS report")
        st.markdown(st.session_state.last_score_report)
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: COLD EMAILS ---
with tab4:
    st.markdown(
        "<div class='eng-page-head'><div class='eng-eyebrow'>Step 04 · Send outreach</div>"
        "<h2>Draft a cold email per role</h2>"
        "<div class='eng-page-desc'>Generated from your base resume and the specific role you pick — "
        "review and edit before anything goes out.</div></div>",
        unsafe_allow_html=True
    )

    if not st.session_state.base_resume:
        st.markdown("<div class='eng-hint'>Build a base resume in the Resume builder tab first.</div>", unsafe_allow_html=True)
    elif not st.session_state.jobs_data:
        st.markdown("<div class='eng-hint'>Search for jobs in the Job board tab first.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='eng-panel'>", unsafe_allow_html=True)
        job_titles = [j['title'] for j in st.session_state.jobs_data]
        selected_job_title = st.selectbox("Select a role to email about", job_titles)
        selected_job = next(j for j in st.session_state.jobs_data if j['title'] == selected_job_title)

        if st.button("Draft cold email", use_container_width=True):
            if check_apis():
                with st.spinner("Drafting email..."):
                    llm = get_llm()
                    draft = generate_cold_email(llm, st.session_state.base_resume, selected_job['title'], selected_job['company'])
                    st.session_state.current_draft = draft
            else:
                st.error("Add both API keys in the sidebar first.")
        st.markdown("</div>", unsafe_allow_html=True)

        if "current_draft" in st.session_state:
            st.markdown("<div class='eng-panel'>", unsafe_allow_html=True)
            st.markdown(
                f"<div class='eng-email-head'><div>To: Hiring team, {selected_job['company']}</div>"
                f"<div>Re: {selected_job['title']}</div></div>",
                unsafe_allow_html=True
            )
            email_text = st.text_area("Review & edit", value=st.session_state.current_draft, height=250, label_visibility="collapsed")
            if st.button("Send email (simulated)", use_container_width=True):
                st.success(f"Sent to HR regarding {selected_job['title']}. (Timestamp: {pd.Timestamp.now()})")
            st.markdown("</div>", unsafe_allow_html=True)
