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

# Read from st.secrets on Cloud, fallback to .env locally
google_api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

os.environ["GOOGLE_API_KEY"] = google_api_key or ""
os.environ["GROQ_API_KEY"] = groq_api_key or ""

class CareerAgent:
    def __init__(self, g_key=None, gr_key=None):
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
        """Tool 1: Real-time Job Search"""
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {"query": f"{title} in {location}", "page": "1", "num_pages": "1"}
        headers = {"x-rapidapi-key": rapid_key, "x-rapidapi-host": "jsearch.p.rapidapi.com"}
        try:
            response = requests.get(url, headers=headers, params=querystring)
            return response.json().get("data", [])
        except Exception as e:
            st.error(f"Error fetching jobs: {e}")
            return []

    def setup_rag(self, pdf_path):
        """Tool 2: RAG Pipeline (Document Ingestion)"""
        if not self.embeddings:
            return "Embeddings not configured. Please set GOOGLE_API_KEY."

        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        splits = splitter.split_documents(docs)
        
        self.vector_db = Chroma.from_documents(documents=splits, embedding=self.embeddings)
        self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 2})
        return "Knowledge base initialized successfully."

    def ask_agent(self, query):
        """Tool 3: Modern RAG Retrieval Chain"""
        if not self.llm:
            return "LLM not configured. Please set GROQ_API_KEY."
        if not self.retriever:
            return "Please upload a document to analyze first."
        
        system_prompt = (
            "You are an expert career assistant. Use the following pieces of retrieved "
            "context from the user's document to answer the question.\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        rag_chain = create_retrieval_chain(self.retriever, question_answer_chain)
        
        response = rag_chain.invoke({"input": query})
        return response.get("answer", "No answer generated.")

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Career Agent", layout="wide")

if "agent" not in st.session_state:
    st.session_state.agent = CareerAgent(g_key=google_api_key, gr_key=groq_api_key)

agent = st.session_state.agent

st.title("🚀 Career AI Agent (Production Build)")

if not google_api_key or not groq_api_key:
    st.warning("⚠️ `GOOGLE_API_KEY` or `GROQ_API_KEY` is missing from Streamlit Secrets. The Doc Optimizer tab will require these keys to function.")

tab1, tab2 = st.tabs(["Job Discovery", "Resume/Doc Optimizer"])

with tab1:
    st.subheader("Live Job Search")
    key = st.text_input("RapidAPI Key", type="password", help="Needed for live job search")
    t = st.text_input("Job Title", "Software Engineer")
    l = st.text_input("Location", "Bangalore")
    if st.button("Search Jobs"):
        if not key:
            st.warning("Please provide a RapidAPI key.")
        else:
            results = agent.search_jobs(t, l, key)
            if not results:
                st.info("No jobs found or invalid API key.")
            for job in results:
                st.write(f"### {job.get('job_title')} | {job.get('employer_name')}")
                st.link_button("Apply", job.get('job_apply_link', '#'))

with tab2:
    st.subheader("Resume/Job Description Analysis")
    uploaded = st.file_uploader("Upload PDF", type="pdf")
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        
        status = agent.setup_rag(tmp_path)
        os.remove(tmp_path)
        st.success(status)

    q = st.text_input("Ask a question about your doc (e.g., 'Does my resume fit this role?')")
    if st.button("Analyze"):
        if q:
            ans = agent.ask_agent(q)
            st.write(ans)
        else:
            st.warning("Please enter a question.")