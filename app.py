# ========== LOAD MODULES ========================
import streamlit as st
import os
import json
import pandas as pd
import PyPDF2
from io import BytesIO
from docx import Document
from fpdf import FPDF

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

# ========== SIDEBAR: THEME & SETUP ==============
with st.sidebar:
    st.markdown("""
    <div class="brand" style="display:flex; align-items:baseline; gap:8px;">
        <span style="width:10px;height:10px;background:#38bdf8;border-radius:2px;"></span>
        <h1 style="margin:0;font-size:1.4rem;">Career Engine</h1>
    </div>
    <div style="font-size:0.75rem;color:gray;margin-bottom:20px;margin-left:18px;">Your application, in one line</div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎨 Theme Preference")
    theme_mode = st.radio("Appearance Mode", ["Light Mode ☀️", "Dark Mode 🌙"], index=0, horizontal=True)

is_dark = "Dark" in theme_mode

# ========== DYNAMIC BESPOKE CSS INJECTION =======
if is_dark:
    theme_css = """
    :root {
      --paper: #0f172a; --paper-raised: #1e293b; --ink: #f8fafc; --ink-soft: #94a3b8;
      --forest: #38bdf8; --forest-dim: #0284c7; --gold: #f59e0b; --sage: rgba(56, 189, 248, 0.15);
      --sage-line: rgba(56, 189, 248, 0.3); --clay: #ef4444; --rail: #334155; --shadow: 0 4px 16px rgba(0,0,0,0.4);
    }
    """
else:
    theme_css = """
    :root {
      --paper: #F7F5F0; --paper-raised: #FCFBF8; --ink: #1A1918; --ink-soft: #5B5854;
      --forest: #2D4A3E; --forest-dim: #1e332a; --gold: #C9A648; --sage: #DDE5DE;
      --sage-line: #C7D2C8; --clay: #B8543E; --rail: #E7E3DA; --shadow: 0 2px 8px rgba(26,25,24,0.06);
    }
    """

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
  {theme_css}
  
  /* STREAMLIT BASE OVERRIDES */
  .stApp {{ background: var(--paper) !important; color: var(--ink) !important; font-family: 'Inter', sans-serif; }}
  [data-testid="stSidebar"] {{ background: var(--paper-raised) !important; border-right: 1px solid var(--rail) !important; }}
  h1, h2, h3, [data-testid="stHeader"] {{ font-family: 'Fraunces', serif !important; color: var(--ink) !important; margin: 0; }}
  header {{visibility: hidden;}}
  
  /* Inputs & Buttons */
  input, textarea, .stSelectbox>div>div>div, .stMultiSelect>div>div>div {{ 
      background: var(--paper) !important; border: 1px solid var(--rail) !important; color: var(--ink) !important; 
      border-radius: 6px !important; font-family: 'Inter', sans-serif !important; font-size: 0.85rem !important;
  }}
  .stButton>button {{
      background: var(--forest) !important; color: #ffffff !important; border: none !important; border-radius: 6px !important; 
      font-weight: 600 !important; font-size: 0.86rem !important; transition: all 0.2s ease !important;
  }}
  .stButton>button:hover {{ background: var(--forest-dim) !important; transform: translateY(-1px); box-shadow: var(--shadow); }}
  
  /* Resume Preview Card */
  .resume-card {{ background: var(--paper-raised); border: 1px solid var(--rail); border-radius: 10px; padding: 28px; box-shadow: var(--shadow); }}
  .r-name {{ font-family: 'Fraunces', serif; font-size: 2rem; font-weight: 600; color: var(--ink); margin-bottom: 8px; }}
  .r-summary {{ font-size: 0.9rem; color: var(--ink-soft); line-height: 1.6; margin-bottom: 20px; }}
  .r-section {{ font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; text-transform: uppercase; color: var(--forest); border-bottom: 1px solid var(--sage-line); padding-bottom: 4px; margin: 20px 0 10px 0; letter-spacing: 0.05em; }}
  .r-chip {{ display: inline-block; background: var(--sage); color: var(--forest); border-radius: 4px; padding: 4px 10px; font-size: 0.78rem; font-weight: 600; margin: 3px; }}
  .r-body {{ font-size: 0.85rem; line-height: 1.6; color: var(--ink); white-space: pre-wrap; }}
  
  /* Job Cards */
  .job-card {{ background: var(--paper-raised); border: 1px solid var(--rail); border-radius: 10px; padding: 20px; box-shadow: var(--shadow); margin-bottom: 12px; border-left: 4px solid var(--forest); }}
  .j-title {{ font-weight: 600; font-size: 1.1rem; color: var(--ink); }}
  .j-company {{ font-size: 0.85rem; color: var(--ink-soft); }}
  .j-badge {{ background: var(--sage); color: var(--forest); padding: 3px 8px; border-radius: 4px; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace; font-weight: 600; text-transform: uppercase; }}
  .j-desc {{ font-size: 0.85rem; color: var(--ink-soft); margin-top: 10px; line-height: 1.5; }}
</style>
""", unsafe_allow_html=True)

# ========== DATA & SIDEBAR FILTERS ================
GLOBAL_LOCATIONS = {
    "Asia": {"India": ["Delhi", "Mumbai", "Bangalore", "Pune", "Gurugram"], "Singapore": ["Singapore City"]},
    "North America": {"United States": ["New York", "San Francisco", "Remote"], "Canada": ["Toronto", "Vancouver"]},
    "Europe": {"United Kingdom": ["London"], "Germany": ["Berlin"]}
}
JOB_TAXONOMY = {
    "Tech & Engineering": ["Software Developer", "Python Developer", "Full-Stack Developer", "AI/ML Engineer"],
    "Business & Finance": ["Financial Analyst", "Business Operations Manager"],
    "Creative & Arts": ["UI/UX Designer", "Graphic Designer"]
}

with st.sidebar:
    with st.expander("🔑 Setup API Keys", expanded=False):
        TAVILY_API_KEY = st.text_input("Tavily API Key", type="password")
        GOOGLE_API_KEY = st.text_input("Gemini API Key", type="password")

    st.markdown("### 🌍 Location")
    region = st.selectbox("Region", list(GLOBAL_LOCATIONS.keys()), index=0)
    country = st.selectbox("Country", list(GLOBAL_LOCATIONS[region].keys()), index=0)
    city = st.selectbox("City/State", GLOBAL_LOCATIONS[region][country], index=0)
    selected_location = f"{city}, {country}"

    st.markdown("### 💼 Job Preferences")
    selected_industries = st.multiselect("Industry", list(JOB_TAXONOMY.keys()), default=["Tech & Engineering"])
    available_roles = [r for ind in selected_industries for r in JOB_TAXONOMY[ind]]
    selected_roles = st.multiselect("Roles", available_roles, default=["Software Developer"] if available_roles else [])
    emp_type = st.multiselect("Contract Type", ["Full-time", "Part-time", "Internship", "Freelance"], default=["Full-time"])
    
    st.markdown("### 📊 Advanced Filters")
    exp_years = st.slider("Years of Experience", 0, 20, (0, 3))
    salary_range = st.slider("Salary Range ($)", 0, 300000, (40000, 120000), step=5000)

def check_apis(): return bool(TAVILY_API_KEY and GOOGLE_API_KEY)
def get_llm(): return ChatGoogleGenerativeAI(model='gemini-1.5-flash', google_api_key=GOOGLE_API_KEY, temperature=0.3)

# ========== EXPORT GENERATORS ===================
def create_docx(resume_data):
    doc = Document()
    doc.add_heading(resume_data.get("Name", "Applicant Resume"), 0)
    doc.add_paragraph(resume_data.get("Summary", ""))
    doc.add_heading("Skills", level=1)
    skills = resume_data.get("Skills", [])
    doc.add_paragraph(", ".join(skills) if isinstance(skills, list) else str(skills))
    doc.add_heading("Experience", level=1)
    doc.add_paragraph(resume_data.get("Experience", ""))
    doc.add_heading("Education", level=1)
    doc.add_paragraph(resume_data.get("Education", ""))
    b = BytesIO()
    doc.save(b)
    return b.getvalue()

def create_pdf(resume_data):
    pdf = FPDF()
    pdf.add_page()
    def clean_txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_txt(resume_data.get("Name", "Resume")), ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 7, clean_txt(resume_data.get("Summary", "")))
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Skills", ln=True)
    pdf.set_font("Arial", '', 11)
    skills = resume_data.get("Skills", [])
    pdf.multi_cell(0, 7, clean_txt(", ".join(skills) if isinstance(skills, list) else str(skills)))
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Experience", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 7, clean_txt(resume_data.get("Experience", "")))
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Education", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 7, clean_txt(resume_data.get("Education", "")))
    
    return pdf.output()

# ========== AI LOGIC ============================
def extract_text(resp):
    c = resp.content
    return "".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in c]) if isinstance(c, list) else str(c)

def generate_base_resume(llm, raw_text, role):
    p = f"Convert this raw user data into structured JSON resume for a {role}. DO NOT fabricate skills. Output strictly valid JSON with keys: 'Name', 'Summary', 'Skills' (array of strings), 'Experience', 'Education'. Data: {raw_text}"
    t = extract_text(llm.invoke(p)).replace("```json", "").replace("```", "").strip()
    try: return json.loads(t)
    except: return {"Name": "Professional", "Summary": t, "Skills": [], "Experience": "", "Education": ""}

def tailor_resume(llm, base_json, jd_text):
    p = f"Tailor this base resume JSON to match this JD. Output strictly valid JSON.\nBase: {json.dumps(base_json)}\nJD: {jd_text}"
    t = extract_text(llm.invoke(p)).replace("```json", "").replace("```", "").strip()
    try: return json.loads(t)
    except: return base_json

def score_ats(llm, resume, jd):
    return extract_text(llm.invoke(f"Act as strict ATS. Score 0-100. Find missing keywords and format issues.\nResume:{resume}\nJD:{jd}"))

# ========== MAIN LAYOUT =========================
tab1, tab2, tab3, tab4 = st.tabs(["01 Resume Builder", "02 Job Board", "03 ATS Score", "04 Cold Mail"])
display_roles = ", ".join(selected_roles) if selected_roles else "Any Role"

# --- TAB 1: RESUME BUILDER ---
with tab1:
    st.markdown("<h2>Build Your Base Profile</h2>", unsafe_allow_html=True)
    colA, colB = st.columns([1, 1.3], gap="large")
    
    with colA:
        target_role = st.text_input("Target Focus", value=display_roles)
        raw_exp = st.text_area("Raw Experience & Notes", height=250, value="BCA student, Python, PHP, web design. Strong math foundation.")
        if st.button("Generate Master Profile", use_container_width=True):
            if check_apis():
                with st.spinner("Compiling structured profile..."):
                    st.session_state.base_resume = generate_base_resume(get_llm(), raw_exp, target_role)
            else: st.error("Add API Keys in Sidebar")
            
    with colB:
        if st.session_state.base_resume:
            r = st.session_state.base_resume
            skills_arr = r.get("Skills", [])
            chips = "".join([f"<span class='r-chip'>{s}</span>" for s in skills_arr]) if isinstance(skills_arr, list) else f"<span class='r-chip'>{skills_arr}</span>"
            
            st.markdown(f"""
            <div class="resume-card">
                <div class="r-name">{r.get('Name', 'Your Name')}</div>
                <div class="r-summary">{r.get('Summary', '')}</div>
                <div class="r-section">Core Competencies</div>
                <div>{chips}</div>
                <div class="r-section">Experience</div>
                <div class="r-body">{r.get('Experience', '')}</div>
                <div class="r-section">Education</div>
                <div class="r-body">{r.get('Education', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            d1.download_button("📥 Download PDF", data=create_pdf(r), file_name="Resume.pdf", mime="application/pdf", use_container_width=True)
            d2.download_button("📥 Download Word", data=create_docx(r), file_name="Resume.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        else: 
            st.info("Your polished profile preview and download buttons will appear here.")

# --- TAB 2: JOB BOARD ---
with tab2:
    st.markdown("<h2>Live Web Job Scraper</h2>", unsafe_allow_html=True)
    
    if st.button("↻ Scrape Web Now", use_container_width=True):
        if check_apis() and selected_roles:
            with st.spinner(f"Hunting for {display_roles} (${salary_range[0]}+) ..."):
                client = TavilyClient(api_key=TAVILY_API_KEY)
                jobs = []
                for e_type in emp_type:
                    query = f"Latest {e_type} jobs for {display_roles} in {selected_location} {exp_years[0]} to {exp_years[1]} years experience salary ${salary_range[0]} to ${salary_range[1]} apply"
                    res = client.search(query, search_depth="advanced", max_results=5)
                    for r in res.get("results", []):
                        jobs.append({"title": r.get("title", "Role"), "url": r.get("url", "#"), "desc": r.get("content", ""), "type": e_type, "company": r.get("title", "Company").split("-")[0].strip()})
                st.session_state.jobs_data = jobs
                st.success(f"Found {len(jobs)} live postings.")
        else: st.warning("Ensure API keys and Roles are selected.")

    if st.session_state.jobs_data:
        st.markdown("<hr style='border-color:var(--rail);'>", unsafe_allow_html=True)
        selected_for_bulk = []
        
        for idx, job in enumerate(st.session_state.jobs_data):
            st.markdown(f"""
            <div class="job-card">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div><span class="j-title">{job['title']}</span> <span class="j-company">at {job['company']}</span></div>
                  <span class="j-badge">{job['type']}</span>
              </div>
              <div class="j-desc">{job['desc'][:200]}...</div>
              <a href="{job['url']}" target="_blank" style="font-size:0.8rem; margin-top:8px; display:inline-block;">View original posting ↗</a>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1.5, 2, 5])
            if c1.button("⚡ Apply Now", key=f"apply_single_{idx}"):
                if not st.session_state.base_resume: st.error("Build base resume first!")
                else:
                    with st.spinner("Tailoring and submitting..."):
                        st.session_state.tailored_resumes[job['title']] = tailor_resume(get_llm(), st.session_state.base_resume, job['desc'])
                        st.success(f"Successfully processed application for {job['title']}!")
            
            if c2.checkbox("Select for bulk apply", key=f"q_bulk_{idx}"):
                selected_for_bulk.append(job)
            st.markdown("<br>", unsafe_allow_html=True)

        if selected_for_bulk:
            st.markdown(f"**{len(selected_for_bulk)} roles selected for bulk submission.**")
            if st.button("🚀 Apply to All Selected", use_container_width=True):
                if not st.session_state.base_resume: st.error("Generate Base Resume first (Step 01)")
                else:
                    for j in selected_for_bulk:
                        with st.spinner(f"Processing {j['company']}..."):
                            st.session_state.tailored_resumes[j['title']] = tailor_resume(get_llm(), st.session_state.base_resume, j['desc'])
                    st.success("All selected applications processed successfully!")

# --- TAB 3: ATS SCORER ---
with tab3:
    st.markdown("<h2>Ensure you pass the bots</h2>", unsafe_allow_html=True)
    source = st.radio("Resume Source:", ["AI Base Profile", "Upload PDF"], horizontal=True)
    jd_input = st.text_area("Target Job Description (Optional)", height=120)
    
    res_text = ""
    if source == "Upload PDF":
        pdf = st.file_uploader("Upload PDF", type=["pdf"])
        if pdf: res_text = PyPDF2.PdfReader(pdf).pages[0].extract_text()
    else:
        res_text = json.dumps(st.session_state.base_resume) if st.session_state.base_resume else ""
        
    if st.button("Run ATS Check", use_container_width=True):
        if not res_text: st.warning("Provide a resume first.")
        elif check_apis():
            with st.spinner("Scoring..."):
                st.markdown(score_ats(get_llm(), res_text, jd_input or "General Industry Standards"))

# --- TAB 4: COLD EMAILS ---
with tab4:
    st.markdown("<h2>Bypass the application pile</h2>", unsafe_allow_html=True)
    if st.session_state.jobs_data and st.session_state.base_resume:
        titles = [j['title'] for j in st.session_state.jobs_data]
        sel = st.selectbox("Select target role", titles)
        j = next(j for j in st.session_state.jobs_data if j['title'] == sel)
        
        if st.button("Draft Cold Email", use_container_width=True):
            if check_apis():
                with st.spinner("Drafting..."):
                    prompt = f"Write a professional cold email applying for {j['title']} at {j['company']} using highlights from this resume: {json.dumps(st.session_state.base_resume)}. Under 150 words."
                    st.session_state.draft = extract_text(get_llm().invoke(prompt))
        
        if "draft" in st.session_state:
            email = st.text_area("Review Email", value=st.session_state.draft, height=200)
            if st.button("Send via Email (Simulated)", use_container_width=True):
                st.success(f"Email sent to recruiter at {j['company']}!")
    else:
        st.info("Complete Step 01 and Step 02 to unlock tailored cold emails.")
