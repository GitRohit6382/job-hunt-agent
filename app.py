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
from langchain.chains import RetrievalQA

# 1. Initialize & Secure Environment
load_dotenv()
# Ensure API keys are loaded from system environment (works for local .env or Streamlit Secrets)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")

class CareerAgent:
    def __init__(self):
        # 2. Setup LLM & Embeddings (As per project session guidelines)
        self.llm = ChatGroq(model_name="llama3-70b-8192", temperature=0.3)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.vector_db = None
        self.retriever = None

    def search_jobs(self, title, location, rapid_key):
        """Tool 1: Real-time Job Search"""
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {"query": f"{title} in {location}", "page": "1", "num_pages": "1"}
        headers = {"x-rapidapi-key": rapid_key, "x-rapidapi-host": "jsearch.p.rapidapi.com"}
        response = requests.get(url, headers=headers, params=querystring)
        return response.json().get("data", [])

    def setup_rag(self, pdf_path):
        """Tool 2: RAG Pipeline (Document Ingestion)"""
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        splits = splitter.split_documents(docs)
        
        # Store in Vector DB (Chroma)
        self.vector_db = Chroma.from_documents(documents=splits, embedding=self.embeddings)
        self.retriever = self.vector_db.as_retriever(search_kwargs={"k": 2})
        return "Knowledge base initialized successfully."

    def ask_agent(self, query):
        """Tool 3: RAG Retrieval"""
        if not self.retriever:
            return "Please upload a document to analyze first."
        qa_chain = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.retriever)
        return qa_chain.invoke(query)

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Career Agent", layout="wide")
agent = CareerAgent()

st.title("🚀 Career AI Agent (Production Build)")
tab1, tab2 = st.tabs(["Job Discovery", "Resume/Doc Optimizer"])

with tab1:
    st.subheader("Live Job Search")
    key = st.text_input("RapidAPI Key", type="password", help="Needed for live job search")
    t = st.text_input("Job Title", "Software Engineer")
    l = st.text_input("Location", "Bangalore")
    if st.button("Search Jobs"):
        results = agent.search_jobs(t, l, key)
        for job in results:
            st.write(f"### {job.get('job_title')} | {job.get('employer_name')}")
            st.link_button("Apply", job.get('job_apply_link', '#'))

with tab2:
    st.subheader("Resume/Job Description Analysis")
    uploaded = st.file_uploader("Upload PDF", type="pdf")
    if uploaded:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded.read())
            agent.setup_rag(tmp.name)
            st.success("Document Ingested into Knowledge Base")
            q = st.text_input("Ask a question about your doc (e.g., 'Does my resume fit this role?')")
            if st.button("Analyze"):
                ans = agent.ask_agent(q)
                st.write(ans['result'])