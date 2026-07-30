# ============================LOAD MODULES=========================
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
import langchain
from langchain.agents import create_agent
from tavily import TavilyClient
import streamlit as st
import os
import time
from PIL import Image
import pandas as pd
import numpy as np


# To show web-app: complete page layout
st.set_page_config(layout="wide")


# To Give title 
st.title("AI RESUME GENERATOR")


st.write(""" This app helps user to build customized professional 
resume with latest job apply links""")

st.image("bg.png")

st.sidebar.title("Fill Important Details")
st.sidebar.image("bg.png")

# step-3 API KEYS
GOOGLE_API_KEY =st.sidebar.text_input("Gemini-API",type = "password") 
GROQ_API_KEY = st.sidebar.text_input("Groq-API",type = "password") 
TAVILY_API_KEY= st.sidebar.text_input("Tavily-API",type = "password") 

all_API = [GROQ_API_KEY,GOOGLE_API_KEY,TAVILY_API_KEY]
if not all(all_API):
    st.error("Must give API keys")
    st.stop()
elif all(all_API):
    st.success("API KEYS LOADED SUCESSFULLY")
else:
    st.info("pass all API keys")


# slect model 
model = ChatGoogleGenerativeAI(
    model = "gemini-3.5-flash-lite",
    google_api_key = GOOGLE_API_KEY
    )

# response = model.invoke("Hello buddy!")
# response.content[-1]['text']

#===============FUNCTION==================
def search_latest_news_jobs(query):
    """This function helps to fetch latest
    news or jobs related article using tavily
    """

    client = TavilyClient(
        api_key = TAVILY_API_KEY
    )
    response = client.search(query)
    return response

#==================Agent Creation===========================
agent = create_agent(
    model = model,
    tools = [search_latest_news_jobs]
)
#agent


#=====================AGENT FUNCTION=======================
def main_agent(agent,query):
    """This is main agent or leader agent
    orchestrate sub agents"""


    #Giving prompt to create detailed prompt for code generation
    prompt = """You are AI assistant and below given is
    a prompt , your task is to give detailed prompt for
    this .
    You are a professional Resume generator
    where user will give thier personal info ,
    you have to create deatiled resume for students for profgessional one ,
    it must be with dynamic UI and UX and,
    with advanced CSS professional Desgining
    make sure to give output in HTML format only
    no markdowns allowed , and theme should be dark with having red and white and black in it
    """

    response = agent.invoke({'messages':[{'role':'user','content':prompt}]})

    deatiled_prompt = response['messages'][-1].content[-1]['text']

    # save prompt using file handling

    with open("prompt.txt","w") as f:
        f.write(deatiled_prompt)

    user_details = f""" Below Given is a user details
    generate Resume based on that, if not
    given keep: default Resume: Pyhton Developer
    user details: {query}"""

    final_prompt = prompt + deatiled_prompt + user_details



    # CODE GENERATION

    response = agent.invoke({'messages':[{'role':'user','content':final_prompt}]})
    code = response['messages'][-1].content[-1]['text']

    return code



# code = main_agent(agent, "ALAN TURING , GEN AI EXPERT")
# from IPython import display as DISPLAY
# DISPLAY.HTML(code)


# fetch latest Domain related jobs using tavily

def get_jobs(agent,
             Loaction = "Noida , Delhi",
             Profile = "Data Analysts, AI Engineer"):
    Location = "Noida,Delhi"
    Profile = "Data Analysts,AI Engineer"
    prompt = f"""Based on user given job profile ,
    fetch latest jobs or job apply article
    using naukri , linkedin , indeed , sprout, or all popular
    job apply platforms, show results with JOB PROFILE NAME, LOCAITON, SALARY
    , COMPANY NAME, SHOW JOBS only related to given {Location} and {Profile}.Output
    must be in Professional HTML Naukri theme cards with Dynamic Design ,
    show atleast TOP 10-20 results with direct apply link , and all jobs experience should be 0-1 year """

    response = agent.invoke({'messages':[{'role':'user','content':prompt}]})

    code = response['messages'][-1].content[-1]['text']

    return code

# code = get_jobs(agent)
# DISPLAY.HTML(code)
