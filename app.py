import streamlit as st
import requests
import os

st.set_page_config(page_title="Job Search AI Agent")

st.title("🚀 Job Search AI Agent")
st.subheader("Find your next career opportunity")

# You can enter the API key directly in the sidebar or via Streamlit Secrets
api_key = st.sidebar.text_input("Enter your RapidAPI Key", type="password")

job_title = st.text_input("Job Title", "Software Engineer")
location = st.text_input("Location", "Bangalore")

if st.button("Search Jobs"):
    if not api_key:
        st.warning("Please enter your RapidAPI Key in the sidebar.")
    else:
        st.write(f"Searching for {job_title} in {location}...")
        
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {"query": f"{job_title} in {location}", "page": "1", "num_pages": "1"}
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)
            data = response.json()

            if "data" in data and len(data["data"]) > 0:
                for job in data["data"]:
                    st.write(f"### {job.get('job_title', 'N/A')}")
                    st.write(f"**Company:** {job.get('employer_name', 'N/A')}")
                    st.write(f"**Location:** {job.get('job_city', 'N/A')}")
                    st.link_button("View Job", job.get('job_apply_link', '#'))
                    st.divider()
            else:
                st.info("No jobs found.")
        except Exception as e:
            st.error(f"Error: {e}")