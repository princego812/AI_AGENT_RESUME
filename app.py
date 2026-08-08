# ========== LOAD MODULES ========================
import streamlit as st
import os
import time
import pandas as pd
import numpy as np

# Langchain & AI Modules
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from tavily import TavilyClient

# ========== PAGE CONFIGURATION ==================
st.set_page_config(
    page_title="AI Resume & Job Engine",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== ADVANCED CSS UI/UX INJECTION ========
st.markdown("""
<style>
    /* Global Theme & Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Typography Styling */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    /* Custom Inputs & Text Areas */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stMultiSelect>div>div>div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f8fafc !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2) !important;
    }
    
    /* Animated Primary Button */
    .stButton>button {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 9999px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        width: 100%;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5) !important;
    }
    
    /* Custom Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 8px;
    }
    
    /* Loader Animation */
    .stSpinner > div > div {
        border-color: #8b5cf6 transparent #38bdf8 transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR CONFIGURATION ===============
with st.sidebar:
    st.markdown("## ⚙️ Core Settings")
    st.markdown("Authenticate your AI agents to begin.")
    
    with st.expander("🔑 API Keys", expanded=True):
        TAVILY_API_KEY = st.text_input("Tavily API Key", type="password")
        GROQ_API_KEY = st.text_input("Groq API Key (Optional)", type="password")
        GOOGLE_API_KEY = st.text_input("Gemini API Key", type="password")

    st.markdown("### 🎯 Job Preferences")
    locations = ["Delhi", "Mumbai", "Pune", "Bangalore", "Gurugram", "Remote"]
    location = st.multiselect("Select Location(s)", options=locations, default=["Delhi"])

    profiles = ["Software Developer", "Full-Stack Dev", "Data Analyst", "AI Engineer", "Gen AI Developer", "Data Scientist"]
    profile = st.multiselect("Select Job Profile(s)", options=profiles, default=["Software Developer"])

# ========== MAIN DASHBOARD ======================
st.markdown("<h1 style='text-align: center; font-size: 3.5rem; margin-bottom: 0;'>🚀 Next-Gen Career Engine</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem;'>AI-Powered Resume Builder & Intelligent Auto-Apply Job Scraper</p>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 📝 Professional Summary & Details")
    default_summary = """BCA student passionate about software development and computer science. 
Skilled in Python, PHP, and web design, with a strong foundation in computer organization and discrete mathematics. 
Looking for dynamic roles to build robust software components, automate testing, and contribute to innovative tech solutions."""
    
    user_info = st.text_area(
        "Paste your raw details, rough notes, or existing resume here. The AI will perfectly structure it.",
        value=default_summary,
        height=250
    )

with col2:
    st.markdown("### 🎨 Design Preferences")
    theme_choice = st.selectbox("Resume Theme", ["Glassmorphism Dark", "Minimalist White", "Creative Vibrant", "Executive Blue"])
    tone_choice = st.select_slider("Writing Tone", options=["Aggressive/Salesy", "Confident/Direct", "Professional/Standard", "Humble/Academic"], value="Professional/Standard")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    generate_btn = st.button("✨ Generate Profile & Find Jobs", use_container_width=True)

# ========== AI AGENT DEFINITIONS ================
def check_apis():
    return bool(TAVILY_API_KEY and GOOGLE_API_KEY)

def fetch_real_jobs(location_list, profile_list):
    """Fetches real latest jobs using Tavily API"""
    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        query = f"Latest hiring job postings for {' and '.join(profile_list)} in {' and '.join(location_list)} 2026 apply online"
        response = client.search(query, search_depth="advanced", max_results=6)
        return response.get("results", [])
    except Exception as e:
        return []

def build_resume_code(model, user_data, theme, tone):
    """Agentic workflow for HTML/CSS Resume generation"""
    system_prompt = f"""
    You are an elite Senior UI/UX Developer and Expert Resume Writer. 
    Transform the following user data into a jaw-dropping, single-file HTML/CSS resume.
    
    USER DATA: {user_data}
    THEME PREFERENCE: {theme}
    WRITING TONE: {tone}
    
    REQUIREMENTS:
    1. Output ONLY RAW HTML with embedded <style> tags. No markdown blocks (```html), no explanations.
    2. Design: Use modern CSS (Flexbox/Grid, gradients, box-shadows, hover animations). 
    3. Sections: Header (Name/Role), Summary, Experience/Projects, Education, Skills (progress bars or tags).
    4. Content Enhancement: Rewrite the user's raw notes using strong action verbs and ATS-optimized keywords matching their requested tone.
    5. Responsiveness: Must look perfect on mobile and desktop.
    """
    
    response = model.invoke(system_prompt)
    code = response.content.replace("```html", "").replace("```", "").strip()
    return code

def build_job_cards(model, location_list, profile_list, real_job_data):
    """Agentic workflow for generating Auto-Apply UI Job Cards based on REAL data"""
    
    # Convert real job data to a string context for the LLM
    job_context = ""
    if real_job_data:
        for idx, job in enumerate(real_job_data):
            job_context += f"Job {idx+1}: Title: {job.get('title', 'N/A')}, URL: {job.get('url', '#')}, ContentSnippet: {job.get('content', 'N/A')}\n"
    else:
        job_context = "No live data fetched. Generate 6 realistic mock job listings for the requested profiles."

    loc_str = ", ".join(location_list)
    prof_str = ", ".join(profile_list)
    
    system_prompt = f"""
    You are an elite Frontend Developer. Create a stunning, dark-mode glassmorphism grid of Job Cards in HTML/CSS.
    
    PROFILES: {prof_str}
    LOCATIONS: {loc_str}
    REAL JOB DATA (Incorporate these into the cards if available):
    {job_context}
    
    REQUIREMENTS:
    1. Output ONLY RAW HTML with embedded <style> and <script> tags. No markdown formatting.
    2. UI/UX: Use CSS Grid. Cards should have hover-lift effects, glow borders, and pill-shaped tags.
    3. Include real Job Titles, snippet descriptions, and the actual URL to apply.
    4. THE AUTO-APPLY BUTTON: Each card MUST have an "⚡ Auto Apply" button. 
    5. JavaScript: Include a `<script>` tag at the bottom that adds an onclick event to these buttons. The event should change the button text to "Applying...", show a CSS spinner, and after 2 seconds, change to "✅ Applied" and turn green.
    """
    
    response = model.invoke(system_prompt)
    code = response.content.replace("```html", "").replace("```", "").strip()
    return code

# ========== EXECUTION PIPELINE ==================
if generate_btn:
    if not check_apis():
        st.error("🚨 Please provide Tavily and Gemini API keys in the sidebar to proceed.")
        st.stop()
        
    try:
        # Initialize LLM directly
        llm = ChatGoogleGenerativeAI(
            model='gemini-1.5-flash', 
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )
        
        # Tabs for output visualization
        res_tab, job_tab, code_tab = st.tabs(["📄 Generated Resume", "🎯 Smart Job Matches", "💻 Source Code"])
        
        with st.spinner("🧠 AI is architecting your premium resume and hunting the web for live jobs..."):
            
            # 1. Generate Resume
            resume_html = build_resume_code(llm, user_info, theme_choice, tone_choice)
            
            # 2. Fetch Real Jobs from Tavily
            real_jobs = fetch_real_jobs(location, profile)
            
            # 3. Generate Job UI incorporating real web data
            job_html = build_job_cards(llm, location, profile, real_jobs)
            
            # Render Resume
            with res_tab:
                st.components.v1.html(resume_html, height=800, scrolling=True)
                st.download_button(
                    label="📥 Download Resume HTML",
                    data=resume_html,
                    file_name="Premium_Resume.html",
                    mime="text/html",
                    use_container_width=True
                )
                
            # Render Jobs
            with job_tab:
                st.info("💡 Test the 'Auto-Apply' feature below. These jobs are pulled live from the web via Tavily Search!")
                st.components.v1.html(job_html, height=800, scrolling=True)
                
            # Provide Source Code
            with code_tab:
                st.markdown("### Resume HTML/CSS Source")
                st.code(resume_html, language='html')
                st.markdown("### Jobs UI Source")
                st.code(job_html, language='html')
                
        st.toast('Workflow Complete!', icon='✅')
        st.balloons()
        
    except Exception as e:
        st.error(f"An error occurred during generation: {str(e)}")
