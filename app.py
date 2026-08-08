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
    page_title="Ultimate Career Engine",
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

# ========== ADVANCED CSS UI/UX ==================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: #e2e8f0; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div, .stMultiSelect>div>div>div { background: rgba(255, 255, 255, 0.03) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; color: white !important; border-radius: 8px !important; }
    .job-card { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid rgba(255,255,255,0.1); }
    .job-type-badge { background: #38bdf8; color: black; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-left: 10px; }
    .sidebar-header { color: #38bdf8; font-weight: bold; font-size: 1.1rem; margin-top: 20px; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px; }
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

# ========== SIDEBAR: COMPREHENSIVE FILTERS ========
with st.sidebar:
    st.markdown("## ⚙️ Auth & APIs")
    with st.expander("🔑 API Keys", expanded=True):
        TAVILY_API_KEY = st.text_input("Tavily API Key", type="password")
        GOOGLE_API_KEY = st.text_input("Gemini API Key", type="password")

    st.markdown("<div class='sidebar-header'>🌍 Global Location Filter</div>", unsafe_allow_html=True)
    region = st.selectbox("Select Region", list(GLOBAL_LOCATIONS.keys()), index=1)
    
    selected_location = "Remote"
    if region == "Remote / Global":
        selected_location = st.selectbox("Remote Type", GLOBAL_LOCATIONS[region])
    else:
        country = st.selectbox("Select Country", list(GLOBAL_LOCATIONS[region].keys()), index=0)
        city = st.selectbox("Select City/State", GLOBAL_LOCATIONS[region][country], index=0)
        selected_location = f"{city}, {country}"

    st.markdown("<div class='sidebar-header'>💼 Industry & Role Filter</div>", unsafe_allow_html=True)
    
    # MULTIPLE INDUSTRIES SELECTION
    selected_industries = st.multiselect(
        "Select Industry(s)", 
        list(JOB_TAXONOMY.keys()), 
        default=["Tech & Engineering"]
    )
    
    # Aggregating roles based on all selected industries
    available_roles = []
    for ind in selected_industries:
        available_roles.extend(JOB_TAXONOMY[ind])
    
    # MULTIPLE ROLES SELECTION
    selected_roles = st.multiselect(
        "Select Specific Role(s)", 
        available_roles, 
        default=["Software Developer"] if "Software Developer" in available_roles else []
    )

    st.markdown("<div class='sidebar-header'>🕒 Employment Type</div>", unsafe_allow_html=True)
    emp_type = st.multiselect(
        "Contract Type", 
        ["Full-time", "Part-time", "Internship", "Freelance", "Gig/Contract"], 
        default=["Full-time", "Internship"]
    )

def check_apis():
    return bool(TAVILY_API_KEY and GOOGLE_API_KEY)

def get_llm():
    return ChatGoogleGenerativeAI(model='gemini-3.5-flash-lite', google_api_key=GOOGLE_API_KEY, temperature=0.3)

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
    except:
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
    except:
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

# ========== MAIN UI TABS ========================
st.markdown("<h1 style='text-align: center;'>💼 Ultimate Career Engine</h1>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📝 1. Resume Builder", "🎯 2. Global Job Board", "📊 3. ATS Scorer", "✉️ 4. Cold Emails"])

# --- TAB 1: RESUME BUILDER ---
with tab1:
    st.markdown("### Build Your Base Resume")
    colA, colB = st.columns(2)
    with colA:
        # Join selected roles into a single string for target role context
        roles_str = ", ".join(selected_roles) if selected_roles else "Professional"
        
        target_role = st.text_input("Target Roles", value=roles_str)
        raw_exp = st.text_area("Raw Experience & Details", height=200, value="BCA student, skilled in Python, PHP, web design. Strong foundation in discrete math. Building robust tech solutions.")
        
        if st.button("Generate Base Resume", use_container_width=True):
            if check_apis():
                with st.spinner("Structuring your data..."):
                    llm = get_llm()
                    st.session_state.base_resume = generate_base_resume(llm, raw_exp, target_role)
                    st.success("Resume saved to memory!")
            else:
                st.error("Missing API Keys.")
    with colB:
        if st.session_state.base_resume:
            st.markdown("### Current Base Resume (JSON)")
            st.json(st.session_state.base_resume)
        else:
            st.info("Generate a base resume first to unlock Job Tailoring and Cold Emails.")

# --- TAB 2: GLOBAL JOB BOARD & AUTO-APPLY ---
with tab2:
    st.markdown("### 🔍 Live Web Job Scraper")
    display_roles = ", ".join(selected_roles) if selected_roles else "Any Role"
    st.write(f"**Current Search Scope:** `{display_roles}` in `{selected_location}`")
    
    if st.button("Search Web (Tavily)", use_container_width=True):
        if not selected_roles:
            st.warning("Please select at least one role from the sidebar to search.")
        elif check_apis():
            with st.spinner(f"Scraping the web for {display_roles} roles in {selected_location}..."):
                client = TavilyClient(api_key=TAVILY_API_KEY)
                
                jobs = []
                # Fetch across the selected employment types
                for e_type in emp_type:
                    query = f"Latest {e_type} jobs for {display_roles} hiring in {selected_location} 2026 apply online"
                    res = client.search(query, search_depth="advanced", max_results=5)
                    
                    for r in res.get("results", []):
                        jobs.append({
                            "title": r.get("title", "Unknown Role"), 
                            "url": r.get("url", "#"), 
                            "desc": r.get("content", ""), 
                            "type": e_type, 
                            "company": r.get("title", "Company").split("-")[0].strip()
                        })
                st.session_state.jobs_data = jobs
                st.success(f"Found {len(jobs)} total live postings!")
        else:
            st.error("Missing API Keys.")

    # Segmented Job Slides based on fetched types
    tabs_list = st.tabs(["Full-time", "Part-time", "Internship", "Freelance", "Gig/Contract"])
    tab_mapping = dict(zip(["Full-time", "Part-time", "Internship", "Freelance", "Gig/Contract"], tabs_list))
    
    def render_job_list(filter_type, current_tab):
        with current_tab:
            filtered = [j for j in st.session_state.jobs_data if j["type"] == filter_type]
            if not filtered:
                st.info(f"No {filter_type} roles fetched yet. Run a search above.")
                return

            selected_jobs = []
            for idx, job in enumerate(filtered):
                st.markdown(f"""
                <div class='job-card'>
                    <h4>{job['title']} <span class='job-type-badge'>{job['type']}</span></h4>
                    <p style='font-size: 14px; color: #cbd5e1;'>{job['desc'][:200]}...</p>
                    <a href="{job['url']}" target="_blank" style="color: #38bdf8;">View Original Posting</a>
                </div>
                """, unsafe_allow_html=True)
                if st.checkbox(f"Select for Auto-Apply (ID: {idx})", key=f"sel_{filter_type}_{idx}"):
                    selected_jobs.append(job)
            
            if selected_jobs:
                st.warning("⚠️ **Disclaimer:** 'Apply to All' will generate tailored resumes and prepare data for review.")
                if st.button(f"🚀 Tailor & Apply to {len(selected_jobs)} Jobs", key=f"apply_{filter_type}"):
                    if not st.session_state.base_resume:
                        st.error("You need to generate a Base Resume in Tab 1 first!")
                    else:
                        llm = get_llm()
                        for sj in selected_jobs:
                            with st.spinner(f"Tailoring resume for {sj['title']}..."):
                                tailored = tailor_resume(llm, st.session_state.base_resume, sj['desc'])
                                st.session_state.tailored_resumes[sj['title']] = tailored
                                st.success(f"✅ Prepared & simulated submission for: {sj['title']}")
                        st.info("Check 'Cold Email' tab to follow up with HR!")

    for e_type, t_obj in tab_mapping.items():
        render_job_list(e_type, t_obj)

# --- TAB 3: ATS SCORER ---
with tab3:
    st.markdown("### 🤖 Resume ATS Scorer")
    st.write("Score your AI-generated resume from Tab 1, or upload your own PDF.")
    
    mode = st.radio("Select Resume Source", ["Use AI Base Resume (from Tab 1)", "Upload custom PDF"])
    target_jd = st.text_area("Paste Target Job Description (Optional)", height=150)
    
    resume_text_to_score = ""
    
    if mode == "Upload custom PDF":
        pdf_file = st.file_uploader("Upload PDF Resume", type=["pdf"])
        if pdf_file:
            resume_text_to_score = extract_pdf_text(pdf_file)
    else:
        if st.session_state.base_resume:
            resume_text_to_score = json.dumps(st.session_state.base_resume)
        else:
            st.warning("No Base Resume found. Go to Tab 1 to generate one.")

    if st.button("Score Resume", use_container_width=True):
        if not resume_text_to_score:
            st.error("Please provide a resume to score.")
        elif not check_apis():
            st.error("Missing API Keys.")
        else:
            with st.spinner("Analyzing against ATS algorithms..."):
                llm = get_llm()
                jd = target_jd if target_jd else "General Industry Standards"
                score_report = score_ats(llm, resume_text_to_score, jd)
                st.markdown("### 📊 ATS Report")
                st.markdown(score_report)

# --- TAB 4: COLD EMAILS ---
with tab4:
    st.markdown("### ✉️ Cold Email Generator")
    st.write("Generate personalized outreach emails for jobs you found in Tab 2.")
    
    if not st.session_state.base_resume:
        st.warning("Please generate a Base Resume in Tab 1 first.")
    elif not st.session_state.jobs_data:
        st.warning("Please search for jobs in Tab 2 first.")
    else:
        job_titles = [j['title'] for j in st.session_state.jobs_data]
        selected_job_title = st.selectbox("Select a Job to email about", job_titles)
        selected_job = next(j for j in st.session_state.jobs_data if j['title'] == selected_job_title)
        
        if st.button("Draft Cold Email", use_container_width=True):
            if check_apis():
                with st.spinner("Drafting email..."):
                    llm = get_llm()
                    draft = generate_cold_email(llm, st.session_state.base_resume, selected_job['title'], selected_job['company'])
                    st.session_state.current_draft = draft
            else:
                st.error("Missing API keys.")
                
        if "current_draft" in st.session_state:
            email_text = st.text_area("Review & Edit Email", value=st.session_state.current_draft, height=250)
            if st.button("📤 Send Email (Simulated)", use_container_width=True):
                st.success(f"Email officially 'sent' to HR regarding {selected_job['title']}! (Timestamp: {pd.Timestamp.now()})")
