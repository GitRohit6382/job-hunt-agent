import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load API key
load_dotenv()
API_KEY = os.getenv("RAPIDAPI_KEY")

st.set_page_config(page_title="Career AI Assistant", layout="wide")

# Sidebar
st.sidebar.title("🛠️ Career Tools")
tool = st.sidebar.radio("Select a tool:", ["Job Search", "Company Insights"])

# API Input
if not API_KEY:
    API_KEY = st.sidebar.text_input("Enter RapidAPI Key", type="password")

st.title("🚀 Career AI Assistant")

if tool == "Job Search":
    st.subheader("Find Your Next Role")
    col1, col2 = st.columns(2)
    job_title = col1.text_input("Job Title", "Software Engineer")
    location = col2.text_input("Location", "Bangalore")
    
    if st.button("Search Jobs"):
        if not API_KEY:
            st.warning("Please enter your RapidAPI Key.")
        else:
            with st.spinner("Searching..."):
                url = "https://jsearch.p.rapidapi.com/search"
                querystring = {"query": f"{job_title} in {location}", "page": "1", "num_pages": "1"}
                headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"}
                
                try:
                    response = requests.get(url, headers=headers, params=querystring)
                    data = response.json()
                    if "data" in data and data["data"]:
                        for job in data["data"]:
                            with st.container(border=True):
                                st.write(f"### {job.get('job_title')}")
                                st.write(f"**Company:** {job.get('employer_name')}")
                                st.write(f"**Location:** {job.get('job_city')}")
                                st.link_button("Apply", job.get('job_apply_link', '#'))
                    else:
                        st.info("No jobs found for this criteria.")
                except Exception as e:
                    st.error(f"Error: {e}")

elif tool == "Company Insights":
    st.subheader("Research Companies")
    company = st.text_input("Enter Company Name")
    if st.button("Search Insights"):
        st.info("This feature is placeholder logic for your Week 5-6 milestone.")
        st.write(f"Displaying research data for {company}...")