# ========== LOAD MODULES ========================
import streamlit as st
import os
import json
import pandas as pd
import PyPDF2
from datetime import datetime

# Langchain & AI Modules
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient

# ========== PAGE CONFIGURATION ==================
st.set_page_config(
    page_title="Career Engine",
    page_icon="💼",
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

# ========== BESPOKE CSS INJECTION ===============
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
  
  :root {
    --paper:#F7F5F0; --paper-raised:#FCFBF8; --ink:#1A1918; --ink-soft:#5B5854;
    --forest:#2D4A3E; --forest-dim:#3D5F51; --gold:#C9A648; --sage:#DDE5DE;
    --sage-line:#C7D2C8; --clay:#B8543E; --clay-soft:#F3E4E0;
    --rail:#E7E3DA; --shadow: 0 1px 2px rgba(26,25,24,0.04), 0 4px 16px rgba(26,25,24,0.06);
  }
  
  /* STREAMLIT OVERRIDES */
  .stApp { background: var(--paper); color: var(--ink); font-family: 'Inter', sans-serif; }
  [data-testid="stSidebar"] { background: var(--paper-raised); border-right: 1px solid var(--rail); }
  h1, h2, h3, [data-testid="stHeader"] { font-family: 'Fraunces', serif !important; color: var(--ink) !important; margin: 0; }
  
  /* Hide default Streamlit headers */
  header {visibility: hidden;}
  
  /* Inputs & Selectboxes */
  .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div, .stMultiSelect>div>div>div { 
      background: var(--paper) !important; 
      border: 1px solid var(--rail) !important; 
      color: var(--ink) !important; 
      border-radius: 6px !important; 
      font-family: 'JetBrains Mono', monospace !important; 
      font-size: 0.85rem !important;
  }
  .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border-color: var(--forest) !important; box-shadow: 0 0 0 1px var(--forest) !important;}
  label { font-size: 0.72rem !important; font-weight: 600 !important; color: var(--ink-soft) !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; font-family: 'Inter', sans-serif !important;}
  
  /* Primary Button overrides */
  .stButton>button {
      background: var(--forest) !important; color: #F7F5F0 !important; border: none !important; 
      border-radius: 7px !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; 
      font-size: 0.86rem !important; padding: 13px 18px !important; transition: transform .12s ease, box-shadow .12s ease !important;
  }
  .stButton>button:hover { background: var(--forest-dim) !important; box-shadow: 0 4px 12px rgba(45,74,62,0.25) !important; }
  .stButton>button:active { transform: translateY(1px) !important; }
  
  /* CUSTOM HTML CLASSES */
  .brand { display: flex; align-items: baseline; gap: 8px; margin-bottom: 5px; }
  .brand-mark { width: 10px; height: 10px; background: var(--forest); border-radius: 2px; }
  .brand h1 { font-size: 1.25rem; font-weight: 600; letter-spacing: -0.01em; }
  .brand-tag { font-size: 0.75rem; color: var(--ink-soft); margin-left: 18px; letter-spacing: 0.02em; margin-bottom: 25px; }
  
  .stepper{position:relative;padding-left:28px; margin-bottom: 30px;}
  .stepper::before{content:'';position:absolute;left:9px;top:6px;bottom:6px;width:2px;background:var(--rail);}
  .stepper-fill{position:absolute;left:9px;top:6px;width:2px;background:var(--gold);transition:height .4s ease;}
  .step{position:relative;padding:12px 0 12px 4px;cursor:default;}
  .step::before{content:'';position:absolute;left:-28px;top:16px;width:20px;height:20px;border-radius:50%;background:var(--paper-raised);border:2px solid var(--rail);z-index:2;}
  .step.done::before{border-color:var(--gold);background:var(--gold);}
  .step.active::before{border-color:var(--forest);background:var(--forest);box-shadow:0 0 0 4px rgba(45,74,62,0.12);}
  .step-num{font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:var(--ink-soft);letter-spacing:0.06em;}
  .step-label{font-size:0.92rem;font-weight:600;margin-top:2px; color: var(--ink);}
  .step-sub{font-size:0.76rem;color:var(--ink-soft);margin-top:2px;line-height:1.35;}
  .step.active .step-label{color:var(--forest);}

  .page-head{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px;border-bottom:1px solid var(--rail);padding-bottom:20px;}
  .eyebrow{font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:var(--forest);letter-spacing:0.08em;text-transform:uppercase;margin-bottom:6px;}
  .page-head h2{font-size:2rem;font-weight:600;letter-spacing:-0.01em;}
  .page-desc{color:var(--ink-soft);font-size:0.92rem;margin-top:6px;max-width:52ch;}

  .search-scope{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px; margin-top: 20px;}
  .scope-pill{background:var(--sage);border:1px solid var(--sage-line);border-radius:20px;padding:6px 14px;font-size:0.8rem;color:var(--forest);font-weight:500;}

  .job-card{background:var(--paper-raised);border:1px solid var(--rail);border-radius:10px;padding:18px 20px;margin-bottom:12px;display:flex;gap:16px;transition:border-color .15s ease, box-shadow .15s ease;}
  .job-card:hover{border-color:var(--sage-line);box-shadow:var(--shadow);}
  .job-body{flex:1;}
  .job-top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
  .job-title{font-weight:600;font-size:0.98rem; color: var(--ink);}
  .job-company{color:var(--ink-soft);font-size:0.82rem;margin-top:2px;}
  .job-badge{font-family:'JetBrains Mono',monospace;font-size:0.68rem;background:var(--sage);color:var(--forest);padding:3px 8px;border-radius:5px;white-space:nowrap;text-transform:uppercase;letter-spacing:0.03em;}
  .job-desc{font-size:0.82rem;color:var(--ink-soft);line-height:1.5;margin-top:8px;}
  .job-link{font-size:0.78rem;color:var(--forest);font-weight:600;margin-top:10px;display:inline-block;text-decoration:none;border-bottom:1px solid var(--sage-line);}

  .apply-bar{background:var(--ink);color:var(--paper);border-radius:10px;padding:14px 20px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 8px 24px rgba(0,0,0,0.18);margin-top:16px;}
  .apply-bar-text{font-size:0.85rem;}
  .apply-bar-text b{color:var(--gold);}
</style>
""", unsafe_allow_html=True)

# ========== MASSIVE DATA DICTIONARIES ===========
GLOBAL_LOCATIONS = {
    "Asia": {"India": ["Delhi", "Mumbai", "Bangalore", "Pune", "Gurugram"], "Singapore": ["Singapore City"]},
    "North America": {"United States": ["New York", "San Francisco", "Remote"], "Canada": ["Toronto", "Vancouver"]},
    "Europe": {"United Kingdom": ["London"], "Germany": ["Berlin"]}
}
JOB_TAXONOMY = {
    "Tech & Engineering": ["Software Developer", "Python Developer", "Full-Stack Developer", "AI/ML Engineer"],
    "Business & Finance": ["Financial Analyst", "Business Operations Manager"],
    "Creative, Arts & Media": ["UI/UX Designer", "Graphic Designer"]
}

# ========== SIDEBAR: CUSTOM LAYOUT ========
with st.sidebar:
    st.markdown("""
    <div class="brand"><span class="brand-mark"></span><h1>Career Engine</h1></div>
    <div class="brand-tag">Your application, in one line</div>
    
    <nav class="stepper">
      <div class="stepper-fill" style="height:25%"></div>
      <div class="step done">
        <div class="step-num">01</div><div class="step-label">Build resume</div><div class="step-sub">Structure your raw data</div>
      </div>
      <div class="step active">
        <div class="step-num">02 — IN PROGRESS</div><div class="step-label">Find roles</div><div class="step-sub">Filter and scrape the open web</div>
      </div>
      <div class="step">
        <div class="step-num">03</div><div class="step-label">Score against ATS</div><div class="step-sub">Formatting and keyword checks</div>
      </div>
      <div class="step">
        <div class="step-num">04</div><div class="step-label">Send outreach</div><div class="step-sub">Draft AI cold emails</div>
      </div>
    </nav>
    """, unsafe_allow_html=True)

    with st.expander("🔑 Setup API Keys", expanded=True):
        TAVILY_API_KEY = st.text_input("Tavily API Key", type="password")
        GOOGLE_API_KEY = st.text_input("Gemini API Key", type="password")

    region = st.selectbox("Region", list(GLOBAL_LOCATIONS.keys()), index=0)
    country = st.selectbox("Country", list(GLOBAL_LOCATIONS[region].keys()), index=0)
    city = st.selectbox("City/State", GLOBAL_LOCATIONS[region][country], index=0)
    selected_location = f"{city}, {country}"

    selected_industries = st.multiselect("Industry", list(JOB_TAXONOMY.keys()), default=["Tech & Engineering"])
    available_roles = []
    for ind in selected_industries: available_roles.extend(JOB_TAXONOMY[ind])
    selected_roles = st.multiselect("Specific Role(s)", available_roles, default=["Software Developer"] if "Software Developer" in available_roles else [])
    
    emp_type = st.multiselect("Contract Type", ["Full-time", "Part-time", "Internship", "Freelance"], default=["Full-time", "Internship"])

def check_apis(): return bool(TAVILY_API_KEY and GOOGLE_API_KEY)
def get_llm(): return ChatGoogleGenerativeAI(model='gemini-3.5-flash-lite', google_api_key=GOOGLE_API_KEY, temperature=0.3)

# ========== AI LOGIC ============================
def extract_text(resp):
    c = resp.content
    return "".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in c]) if isinstance(c, list) else str(c)

def generate_base_resume(llm, raw_text, role):
    p = f"Convert this raw user data into structured JSON resume for a {role}. DO NOT fabricate skills. Output ONLY JSON: 'Name', 'Summary', 'Skills', 'Experience', 'Education'. Data: {raw_text}"
    t = extract_text(llm.invoke(p)).replace("```json", "").replace("```", "").strip()
    try: return json.loads(t)
    except: return {"Summary": t}

def tailor_resume(llm, base_json, jd_text):
    p = f"Tailor this base resume JSON to match this JD. Highlight keywords, reorder bullets. DO NOT fabricate. Output valid JSON.\nBase: {json.dumps(base_json)}\nJD: {jd_text}"
    t = extract_text(llm.invoke(p)).replace("```json", "").replace("```", "").strip()
    try: return json.loads(t)
    except: return base_json

def score_ats(llm, resume, jd):
    return extract_text(llm.invoke(f"Act as strict ATS. Score 0-100. Find missing keywords and formatting issues.\nResume:{resume}\nJD:{jd}"))

def get_cold_email(llm, base, role, company):
    return extract_text(llm.invoke(f"Write a concise professional cold email applying for {role} at {company} using highlights from this resume: {json.dumps(base)}. Under 150 words."))

# ========== MAIN LAYOUT =========================
tab1, tab2, tab3, tab4 = st.tabs(["01 Resume", "02 Job Search", "03 ATS Score", "04 Cold Mail"])
display_roles = ", ".join(selected_roles) if selected_roles else "Any Role"

# --- TAB 1 ---
with tab1:
    st.markdown("""
    <div class="page-head">
      <div>
        <div class="eyebrow">Step 01 · Build Resume</div>
        <h2>Structure your raw data</h2>
        <div class="page-desc">Generate a baseline structured JSON resume that serves as the foundation for tailoring.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    colA, colB = st.columns(2)
    with colA:
        target_role = st.text_input("Target Focus", value=display_roles)
        raw_exp = st.text_area("Raw Experience & Notes", height=250, value="BCA student, Python, PHP, web design. Strong math foundation.")
        if st.button("Generate Base Profile", use_container_width=True):
            if check_apis():
                with st.spinner("Compiling JSON profile..."):
                    st.session_state.base_resume = generate_base_resume(get_llm(), raw_exp, target_role)
            else: st.error("Add API Keys in Sidebar")
    with colB:
        if st.session_state.base_resume: st.json(st.session_state.base_resume)
        else: st.info("Your structured profile will appear here.")

# --- TAB 2 ---
with tab2:
    st.markdown("""
    <div class="page-head">
      <div>
        <div class="eyebrow">Step 02 · Find roles</div>
        <h2>Live roles matching your filters</h2>
        <div class="page-desc">Pulled from the open web just now. Select the ones worth applying to.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render Custom Scope Pills
    pills_html = f"<div class='search-scope'>"
    for r in selected_roles: pills_html += f"<span class='scope-pill'>{r}</span>"
    pills_html += f"<span class='scope-pill'>{selected_location}</span>"
    pills_html += f"</div>"
    st.markdown(pills_html, unsafe_allow_html=True)
    
    col_btn, _ = st.columns([1,3])
    if col_btn.button("↻ Scrape Web Now"):
        if check_apis() and selected_roles:
            with st.spinner(f"Hunting for {display_roles}..."):
                client = TavilyClient(api_key=TAVILY_API_KEY)
                jobs = []
                for e_type in emp_type:
                    query = f"Latest {e_type} jobs for {display_roles} hiring in {selected_location} apply online"
                    res = client.search(query, search_depth="advanced", max_results=4)
                    for r in res.get("results", []):
                        jobs.append({"title": r.get("title", "Role"), "url": r.get("url", "#"), "desc": r.get("content", ""), "type": e_type, "company": r.get("title", "Company").split("-")[0].strip()})
                st.session_state.jobs_data = jobs
        else: st.warning("Ensure API keys and Roles are selected.")

    t_ft, t_pt, t_int, t_free = st.tabs(["Full-time", "Part-time", "Internships", "Freelance"])
    mapping = {"Full-time": t_ft, "Part-time": t_pt, "Internship": t_int, "Freelance": t_free}
    
    for e_type, tab_obj in mapping.items():
        with tab_obj:
            filtered = [j for j in st.session_state.jobs_data if j["type"] == e_type]
            if not filtered:
                st.write(f"No {e_type} roles fetched yet.")
                continue
            
            selected_for_apply = []
            for idx, job in enumerate(filtered):
                st.markdown(f"""
                <div class="job-card">
                  <div class="job-body">
                    <div class="job-top">
                      <div><div class="job-title">{job['title']}</div><div class="job-company">{job['company']}</div></div>
                      <span class="job-badge">{job['type']}</span>
                    </div>
                    <div class="job-desc">{job['desc'][:180]}...</div>
                    <a class="job-link" href="{job['url']}" target="_blank">View original posting ↗</a>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if st.checkbox(f"Add to application queue", key=f"q_{e_type}_{idx}"): selected_for_apply.append(job)

            if selected_for_apply:
                st.markdown(f"""
                <div class="apply-bar">
                  <div class="apply-bar-text">{len(selected_for_apply)} roles selected · Resumes will be tailored <b>before</b> sending</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Tailor Resumes & Prepare Submission", key=f"btn_{e_type}"):
                    if not st.session_state.base_resume: st.error("Generate Base Resume first (Step 01)")
                    else:
                        for j in selected_for_apply:
                            st.session_state.tailored_resumes[j['title']] = tailor_resume(get_llm(), st.session_state.base_resume, j['desc'])
                            st.success(f"Tailored resume saved in memory for: {j['company']}")

# --- TAB 3 ---
with tab3:
    st.markdown("""
    <div class="page-head">
      <div><div class="eyebrow">Step 03 · Score against ATS</div><h2>Ensure you pass the bots</h2></div>
    </div>
    """, unsafe_allow_html=True)
    
    source = st.radio("Resume Source:", ["AI Base Profile", "Upload PDF"])
    jd_input = st.text_area("Target Job Description (Optional)", height=100)
    
    res_text = ""
    if source == "Upload PDF":
        pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf: res_text = PyPDF2.PdfReader(pdf).pages[0].extract_text()
    else:
        res_text = json.dumps(st.session_state.base_resume) if st.session_state.base_resume else ""
        
    if st.button("Run ATS Check"):
        if not res_text: st.warning("Provide a resume first.")
        elif check_apis():
            with st.spinner("Scoring..."):
                st.markdown(score_ats(get_llm(), res_text, jd_input or "General Industry Standards"))

# --- TAB 4 ---
with tab4:
    st.markdown("""
    <div class="page-head">
      <div><div class="eyebrow">Step 04 · Send outreach</div><h2>Bypass the application pile</h2></div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.jobs_data and st.session_state.base_resume:
        titles = [j['title'] for j in st.session_state.jobs_data]
        sel = st.selectbox("Select target role", titles)
        j = next(j for j in st.session_state.jobs_data if j['title'] == sel)
        
        if st.button("Draft Cold Email"):
            if check_apis():
                with st.spinner("Drafting..."):
                    st.session_state.draft = get_cold_email(get_llm(), st.session_state.base_resume, j['title'], j['company'])
        
        if "draft" in st.session_state:
            email = st.text_area("Review Email", value=st.session_state.draft, height=200)
            if st.button("Send via Email (Simulated)"):
                st.success(f"Email sent to recruiter at {j['company']}!")
    else:
        st.info("Complete Step 01 and Step 02 to unlock tailored cold emails.")
