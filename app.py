import streamlit as st
import requests
import os
import tempfile
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# 1. Initialize & Secure Environment
load_dotenv()

def get_secret(key):
    """Retrieve secret from Streamlit Secrets or Environment variables."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, "")

google_api_key = get_secret("GOOGLE_API_KEY")
groq_api_key = get_secret("GROQ_API_KEY")
rapidapi_key_secret = get_secret("RAPIDAPI_KEY")

os.environ["GOOGLE_API_KEY"] = google_api_key
os.environ["GROQ_API_KEY"] = groq_api_key

# 2. Career Agent Class
class CareerAgent:
    def __init__(self, g_key="", gr_key=""):
        self.vector_db = None
        self.retriever = None
        self.llm = None
        self.embeddings = None

        if gr_key:
            self.llm = ChatGroq(
                groq_api_key=gr_key,
                model_name="llama3-70b-8192",
                temperature=0.3
            )

        if g_key:
            self.embeddings = GoogleGenerativeAIEmbeddings(
                google_api_key=g_key,
                model="models/embedding-001"
            )

    def search_jobs(self, title, location, rapid_key):
        """Tool 1: Real-time Job Search via JSearch API"""
        clean_key = str(rapid_key).strip().strip("'").strip('"')
        if not clean_key:
            st.warning("⚠️ RapidAPI Key is empty.")
            return []

        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {
            "query": f"{title} in {location}",
            "page": "1",
            "num_pages": "1"
        }
        headers = {
            "x-rapidapi-key": clean_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            res_json = response.json()

            if response.status_code != 200:
                st.error(f"RapidAPI Error ({response.status_code}): {res_json.get('message', response.text)}")
                return []

            # Handle both possible response formats:
            # 1. {"data": {"jobs": [...]}}
            # 2. {"data": [...]}
            data_content = res_json.get("data", [])
            if isinstance(data_content, dict):
                return data_content.get("jobs", [])
            elif isinstance(data_content, list):
                return data_content

            return []
        except Exception as e:
            st.error(f"Network error: {e}")
            return []

    def setup_rag(self, pdf_path):
        """Tool 2: RAG Pipeline (Document Ingestion)"""
        if not self.embeddings:
            return False, "Embeddings not configured. Please verify your GOOGLE_API_KEY in Secrets."

        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            
            if not docs:
                return False, "Uploaded PDF appears to be empty or unreadable."

            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
            splits = splitter.split_documents(docs)
            
            self.vector_db = Chroma.from_documents(documents=splits, embedding=self.embeddings)
            self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 2})
            return True, "Knowledge base initialized successfully!"
        except Exception as e:
            return False, f"Failed to ingest document: {e}"

    def ask_agent(self, query):
        """Tool 3: Modern RAG Retrieval Chain"""
        if not self.llm:
            return "LLM not configured. Please verify your GROQ_API_KEY in Secrets."
        if not self.retriever:
            return "Please upload a document to analyze first."
        
        system_prompt = (
            "You are an expert career assistant. Use the following pieces of retrieved "
            "context from the candidate's document to accurately answer the question.\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        try:
            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            rag_chain = create_retrieval_chain(self.retriever, question_answer_chain)
            response = rag_chain.invoke({"input": query})
            return response.get("answer", "No answer generated.")
        except Exception as e:
            return f"Error analyzing document: {e}"

# 3. Streamlit Application UI
st.set_page_config(page_title="Pro Career Agent", layout="wide", page_icon="🚀")

# Maintain session state
if "agent" not in st.session_state:
    st.session_state.agent = CareerAgent(g_key=google_api_key, gr_key=groq_api_key)

agent = st.session_state.agent

st.title("🚀 Career AI Agent")

# Show configuration warnings only if backend keys are absent
if not google_api_key or not groq_api_key:
    st.warning("⚠️ `GOOGLE_API_KEY` or `GROQ_API_KEY` is missing in Secrets. The Resume Optimizer tab requires these to function.")

tab1, tab2 = st.tabs(["🔍 Job Discovery", "📄 Resume & Doc Optimizer"])

# --- TAB 1: Live Job Search ---
with tab1:
    st.subheader("Live Job Search")
    
    # If RAPIDAPI_KEY is in Streamlit Secrets, use it automatically; otherwise show input box
    if rapidapi_key_secret:
        user_rapid_key = rapidapi_key_secret
    else:
        user_rapid_key = st.text_input("RapidAPI Key", type="password", help="Subscribe to JSearch on RapidAPI to get your key.")

    col1, col2 = st.columns(2)
    with col1:
        job_title = st.text_input("Job Title", "Software Engineer")
    with col2:
        job_location = st.text_input("Location", "Bangalore")

    if st.button("Search Jobs", type="primary"):
        with st.spinner("Fetching latest job listings..."):
            results = agent.search_jobs(job_title, job_location, user_rapid_key)
            
            if results:
                st.success(f"Found {len(results)} jobs matching your criteria.")
                for job in results:
                    employer = job.get("employer_name", "Unknown Employer")
                    title = job.get("job_title", "Untitled Role")
                    apply_link = job.get("job_apply_link", "#")
                    city = job.get("job_city", "")
                    country = job.get("job_country", "")
                    loc_str = f"{city}, {country}".strip(", ")

                    with st.container(border=True):
                        st.markdown(f"### {title}")
                        st.markdown(f"**Company:** {employer}  |  **Location:** {loc_str or 'Not specified'}")
                        st.link_button("Apply Directly", apply_link)
            elif user_rapid_key:
                st.info("No matching jobs found. Try adjusting your search query or location.")

# --- TAB 2: Resume / Doc Optimizer ---
with tab2:
    st.subheader("Resume & Job Description Analysis")
    uploaded_file = st.file_uploader("Upload Resume / Job Spec (PDF format)", type=["pdf"])

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        with st.spinner("Processing document embeddings..."):
            success, message = agent.setup_rag(tmp_path)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)  # Cleanup temp storage

        if success:
            st.success(message)
        else:
            st.error(message)

    query_input = st.text_input(
        "Ask questions about your uploaded document:",
        placeholder="e.g., 'What are the candidate's top technical skills?' or 'Summarize experience for a Backend Engineer role.'"
    )

    if st.button("Analyze Document", type="primary"):
        if not query_input.strip():
            st.warning("Please enter a question first.")
        else:
            with st.spinner("Analyzing document with Groq LLM..."):
                answer = agent.ask_agent(query_input)
                st.markdown("### Analysis Result")
                st.write(answer)