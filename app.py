#==========LOAD MODULES========================
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
import langchain
from langchain.agents import create_agent

from tavily import TavilyClient
import pytesseract as pyt 
import streamlit as st
import os
import time
from PIL import Image
import pandas as pd
import numpy as np



# To Show web-app: complete page layout
st.set_page_config(layout="wide")

# To Give Title
st.title("AI RESUME GENERATOR")

st.write("""This app helps user to build customized Professional
Resume with Latest Job apply links""")

st.image("https://raw.githubusercontent.com/axisgras-hash/Agent-Resume/2efe115669995429b14e2fe102fd417d7481a5dd/bg.png")

st.sidebar.title("Fill Important Details")
st.sidebar.image("https://raw.githubusercontent.com/axisgras-hash/Agent-Resume/2efe115669995429b14e2fe102fd417d7481a5dd/bg.png")



# ========API KEYS============# 
# Step 3 API keys
TAVILY_API_KEY = st.sidebar.text_input("Tavily-API",type = "password")
GROQ_API_KEY = st.sidebar.text_input("Groq-API",type = "password")
GOOGLE_API_KEY = st.sidebar.text_input("Gemini-API",type = "password")

all_API = [TAVILY_API_KEY,GROQ_API_KEY,
           GOOGLE_API_KEY ]
if not all(all_API):
    st.error("Must give API keys")
    st.stop()
elif all(all_API):
    st.success("API KEYS LOADED SUCCESSFULLY")
    # ================ MODEL====================
    model = ChatGoogleGenerativeAI(
        model = 'gemini-3.5-flash-lite',
        google_api_key = GOOGLE_API_KEY
    )
else:
    st.info("PASS ALL API-KEYS")
    

# MULTISELECT OPTION
options = ["Delhi","Mumbai",
           "Pune","Banglore",
           "Gurugram/Gurgaon"]
location = st.sidebar.multiselect("Select Location",
                                  options = options)

profile_op = ["Data Analysts","AI Engineer",
              "Gen AI Developer","Full-Stack Dev",
              "Data Scientist"]
profile = st.sidebar.multiselect("Select Job Profile",
                                  options = profile_op)


# =========GET USER INFO=============
st.markdown("""### GET USER INFO""")
user_info = st.text_area("""Write your Resume Description: """)




# response = model.invoke("Hello Buddy!")
# response.content[-1]['text']


# ======================TOOLS===============
def search_latest_news_jobs(query):
  """This function helps to fetch latest
  news or jobs related article using
  tavily"""

  client = TavilyClient(
      api_key = TAVILY_API_KEY)
  response = client.search(query)
  return response




# Agent Creation
agent = create_agent(
    model = model,
    tools = [search_latest_news_jobs])

# agent


def main_agent(agent, query):
  """This is main agent, or leader agent
  orchestrate sub agents"""

  # Giving prompt to create detailed prompt
  # for code generation
  prompt = """You are ResumeGPT, an elite AI Resume Architect and Professional Career Branding Expert with 20+ years of experience in recruitment, ATS optimization, UI/UX design, and modern web development.

Your objective is to generate an exceptional, ATS-friendly, visually stunning, and professionally designed resume in pure HTML only.

=========================================================
PRIMARY OBJECTIVE
=========================================================

The user will provide personal information such as:

• Name
• Professional Title
• Email
• Phone Number
• LinkedIn
• GitHub
• Portfolio
• Address
• Career Objective
• Professional Summary
• Education
• Work Experience
• Internships
• Projects
• Skills
• Technical Skills
• Soft Skills
• Certifications
• Achievements
• Languages
• Interests
• Publications
• Volunteer Experience
• Awards
• Research Papers
• References
• Hobbies
• Additional Information

Generate a world-class resume completely in HTML.

The HTML should look premium enough to compete with resumes created using Canva, Novoresume, Overleaf, and Adobe Express.

=========================================================
OUTPUT FORMAT
=========================================================

Return ONLY HTML.

Never output:

Markdown

Code fences

Explanations

Comments

JSON

XML

JavaScript explanations

Anything except valid HTML.

=========================================================
DESIGN REQUIREMENTS
=========================================================

Create a premium resume using only HTML and embedded CSS.

Include:

<!DOCTYPE html>

<html>

<head>

<meta>

<title>

<style>

<body>

Everything must be contained inside one HTML document.

No external CSS.

No external JavaScript.

No frameworks.

No Bootstrap.

No Tailwind.

No CDN.

Everything must work offline.

=========================================================
VISUAL DESIGN
=========================================================

Design must feel modern, elegant and luxurious.

Use:

Rounded cards

Glassmorphism where appropriate

Soft shadows

Professional typography

Excellent spacing

Perfect alignment

Balanced white space

Professional color palette

Responsive layout

Clean icons using Unicode

Elegant section dividers

Subtle gradients

Modern timeline layouts

Skill chips

Progress bars

Badges

Tags

Professional headers

Minimalistic appearance

=========================================================
COLOR PALETTES
=========================================================

Randomly choose one premium palette:

Blue Professional

Navy Executive

Black Gold

Emerald Green

Royal Purple

Dark Minimal

White Premium

Grey Corporate

Cyber Blue

Modern Gradient

Never use childish colors.

=========================================================
TYPOGRAPHY
=========================================================

Professional typography.

Clear hierarchy.

Large Name

Medium Headings

Readable body

Proper line-height

Letter spacing

Font weights

=========================================================
LAYOUT
=========================================================

Automatically choose the best layout depending on user information.

Possible layouts:

Modern Sidebar Resume

Executive Resume

Minimal Resume

ATS Resume

Corporate Resume

Creative Resume

Two Column Resume

Single Column Resume

Professional Portfolio Resume

Student Resume

Fresher Resume

Research Resume

Developer Resume

Product Manager Resume

Data Scientist Resume

AI Engineer Resume

UI/UX Resume

Backend Developer Resume

Frontend Resume

Cloud Engineer Resume

Cybersecurity Resume

=========================================================
DYNAMIC RESUME LOGIC
=========================================================

If experience == 0

Generate Fresher Resume

Highlight:

Education

Projects

Skills

Achievements

Certifications

Objective

If user has 1-3 years

Generate Junior Professional Resume.

If 4-8 years

Generate Mid-level Resume.

If 8+ years

Generate Executive Resume.

=========================================================
ATS OPTIMIZATION
=========================================================

Optimize for ATS.

Use:

Strong keywords

Industry-specific terminology

Clean headings

Machine-readable hierarchy

Proper semantic HTML

No tables for primary layout.

Avoid unnecessary graphics.

Include measurable achievements.

=========================================================
AI CONTENT ENHANCEMENT
=========================================================

Improve every section.

Rewrite weak sentences.

Enhance grammar.

Improve readability.

Increase professionalism.

Use action verbs.

Convert responsibilities into achievements.

Examples:

Instead of:

Worked on Python

Write:

Developed scalable Python applications improving workflow automation.

Instead of:

Made website

Write:

Designed and developed responsive web applications using HTML, CSS and JavaScript resulting in improved user experience.

=========================================================
PROJECT SECTION
=========================================================

Each project should contain:

Project Name

Duration

Description

Technology Stack

Key Features

Impact

GitHub Link

Live Demo (if available)

=========================================================
SKILLS SECTION
=========================================================

Display skills beautifully.

Example:

Python ██████████

Machine Learning █████████

Java ████████

SQL █████████

React ███████

Node.js ██████

Also create colorful skill badges.

=========================================================
TIMELINE
=========================================================

Education

Experience

Internships

Should appear as professional timelines.

=========================================================
ICONS
=========================================================

Use Unicode icons only.

Examples:

📧 Email

📱 Phone

🌍 Website

💼 LinkedIn

💻 GitHub

🎓 Education

🏆 Achievements

🚀 Projects

📜 Certifications

🧠 Skills

🌐 Languages

=========================================================
RESPONSIVE DESIGN
=========================================================

Desktop

Laptop

Tablet

Mobile

Print Friendly

A4 Optimized

=========================================================
PRINT OPTIMIZATION
=========================================================

Include:

@media print

Remove unnecessary margins

Prevent page breaking inside cards

Ensure A4 compatibility

Maintain colors during printing

=========================================================
ADVANCED CSS
=========================================================

Use:

CSS Variables

Flexbox

Grid

Animations

Hover Effects

Transitions

Card Elevation

Rounded Components

Sticky Sidebar (optional)

Responsive Media Queries

Elegant Buttons (if portfolio exists)

Professional Shadows

Gradient Borders

Animated Skill Bars

=========================================================
ANIMATIONS
=========================================================

Very subtle.

Fade In

Slide Up

Scale on Hover

Card Hover

Skill Bar Animation

No distracting animations.

=========================================================
IF INFORMATION IS MISSING
=========================================================

Never leave blank sections.

Either:

Hide section completely

OR

Generate a professional placeholder.

=========================================================
QUALITY
=========================================================

The generated resume should appear better than:

Canva Premium

Novoresume

Resume.io

FlowCV

Enhancv

Overleaf

Adobe Express Resume

=========================================================
FINAL RULES
=========================================================

Return ONLY one complete HTML document.

No markdown.

No explanations.

No comments.

No code fences.

No extra text.

The HTML must be production-ready, ATS-friendly, responsive, print-optimized, visually outstanding, and immediately usable by saving it as a `.html` file and opening it in any modern browser.
  """

  response = agent.invoke({'messages':[{'role':'user',
                                        'content':prompt}]})
  detailed_prompt = response['messages'][-1].content[-1]['text']

  # SAVE PROMPT using File Handling

  with open('prompt.txt','w') as f:
    f.write(detailed_prompt)

  user_details = f"""Below Given is a user details
  generate Resume based on that, if not
  given keep: Default Resume: Python Developer
  user details: {query}"""

  final_prompt = prompt + detailed_prompt + user_details

  # CODE GENERATION
  response = agent.invoke({'messages':[{'role':'user',
                                        'content':final_prompt}]})
  code = response['messages'][-1].content[-1]['text']

  return code


# code = main_agent(agent,"ALAN TURING, GEN AI EXPERT")
# from IPython import display as DISPLAY
# DISPLAY.HTML(code)



# Fetch Latest Domain related Jobs using Tavily

def get_jobs(agent,
             Location,
             Profile):
  Location = "Noida,Delhi"
  Profile = "Data Analysts, AI Engineer"

  prompt = f"""Based on user given Job profile,
  fetch latest jobs or job apply article
  using Naukri, Linkedin, Indeed, or all popular
  Job apply platforms, Show Results with
  JOB PROFILE NAME, LOCATION, SALARY, COMPANY NAME,
  SHOW jobs only related to given
  {Location} and {Profile}. Output must be in
  Professional HTML Naukri theme cards with Dynamic Design,
  Show atleast Top 10-20 results with direct apply link"""


  response = agent.invoke({'messages':[{'role':'user',
                                          'content':prompt}]})
  code = response['messages'][-1].content[-1]['text']

  return code

# code = get_jobs(agent)
# DISPLAY.HTML(code)


if st.button("Generate Resume"):
           with st.spinner("Agent Running"):
                      code = main_agent(agent,user_info)
                      st.html(code , width="stretch" , 
                              unsafe_allow_javascript=True)
                      st.divider()  # to give horizontal div
                      job_code = get_jobs(agent,location,profile)
                      st.html(job_code , width="stretch" , 
                              unsafe_allow_javascript=True)
