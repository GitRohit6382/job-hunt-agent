# Job Search AI Agent - Final Submission

## Project Overview
An AI-powered career assistant built for the Indian job market, designed to automate job discovery and provide streamlined application tracking.

## Architecture
- **Framework:** Streamlit (Frontend & Backend)
- **API Strategy:** JSearch API (RapidAPI) for real-time data.
- **Workflow:** User Input -> API Request -> Data Parsing -> UI Display.

## Features
- **Job Search:** Real-time filtering by role and location (e.g., Bangalore, Mumbai).
- **Company Insights:** Tool for basic research (Expanding in progress).
- **Security:** API keys are managed via Environment Variables and Streamlit Secrets.

## Setup Instructions
1. Clone the repo: `git clone <your-repo-url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with `RAPIDAPI_KEY=your_key`.
4. Run: `streamlit run app.py`

## User Journey
1. Open the application.
2. Navigate to "Job Search" in the sidebar.
3. Input the job title and preferred Indian city.
4. View real-time listings and click "Apply" to be redirected.