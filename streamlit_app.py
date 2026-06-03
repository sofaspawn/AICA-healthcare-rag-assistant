import streamlit as st
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)

# Import backend modules
from backend.rag.vector_store import get_vector_store
from backend.rag.retriever import retrieve_context
from backend.rag.chat import chat_pipeline
from backend.ingestion.download_dataset import download_and_export
from backend.ingestion.preprocess import preprocess_data
from PyPDF2 import PdfReader
from backend.rag.chunker import chunk_document

from ui.dashboard import render_risk_score_card, render_emergency_banner, render_trend_indicator, render_alert_history
from ui.charts import render_vitals_charts
from backend.clinical.patient_state import get_patient_state, update_patient_state
from backend.database.db import DatabaseManager
from backend.clinical.extraction import extract_clinical_data
from backend.clinical.emergency_rules import EmergencyDetector
from backend.clinical.trend_analysis import TrendAnalyzer
from backend.clinical.scorer import score_patient
from backend.clinical.alert_engine import AlertEngine

PATIENT_ID = "patient_001"

# Page configuration
st.set_page_config(
    page_title="Patient Insights",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS matching Tailwind design
st.markdown("""
<style>
    /* Import Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Newsreader:wght@400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Manrope', sans-serif !important;
        background-color: #fff8f7 !important;
        color: #251817;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Newsreader', serif;
    }

    /* Streamlit overrides */
    .stApp {
        background-color: #fff8f7;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffe9e7 !important;
        border-right: 1px solid rgba(140, 113, 110, 0.2);
    }
    
    /* Sidebar Brand */
    .sidebar-brand {
        font-family: 'Newsreader', serif;
        font-size: 24px;
        font-weight: 700;
        color: #aa312e;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sidebar-subtitle {
        font-size: 12px;
        color: #58413f;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
        margin-top: 4px;
        margin-bottom: 24px;
    }

    /* Topbar */
    .topbar {
        background: #fff8f7;
        border-bottom: 1px solid rgba(140, 113, 110, 0.2);
        padding: 16px 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 24px;
        margin-top: -60px; /* Offset Streamlit's default top padding */
    }
    .topbar-title {
        font-family: 'Newsreader', serif;
        font-size: 24px;
        font-weight: 600;
        color: #251817;
    }
    .topbar-nav {
        display: flex;
        gap: 32px;
    }
    .topbar-nav a {
        color: #58413f;
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        font-family: 'Manrope', sans-serif;
    }
    .topbar-nav a.active {
        color: #aa312e;
        border-bottom: 2px solid #aa312e;
        padding-bottom: 4px;
    }

    /* AI Welcome Card */
    .ai-welcome {
        background-color: #ffffff;
        border-left: 4px solid #d4e896;
        border-radius: 12px;
        padding: 24px;
        display: flex;
        gap: 16px;
        margin-bottom: 32px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .ai-icon-wrapper {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: rgba(212, 232, 150, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .ai-icon {
        color: #546521;
        font-family: 'Material Symbols Outlined';
    }
    .ai-welcome-title {
        font-size: 10px;
        color: #546521;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .ai-welcome-heading {
        font-family: 'Newsreader', serif;
        font-size: 28px;
        font-weight: 500;
        color: #251817;
        margin-bottom: 12px;
        line-height: 1.2;
    }
    .ai-disclaimer-box {
        background-color: rgba(212, 232, 150, 0.1);
        border: 1px solid rgba(84, 101, 33, 0.1);
        border-radius: 8px;
        padding: 12px;
        font-size: 14px;
        color: #58413f;
    }

    /* My custom bubbles */
    .bubble {
        padding: 16px;
        max-width: 80%;
        font-size: 16px;
        line-height: 1.6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 16px;
        font-family: 'Manrope', sans-serif;
    }
    .bubble-user {
        background-color: #ffffff;
        border: 1px solid rgba(140, 113, 110, 0.2);
        border-radius: 16px 16px 0 16px;
        margin-left: auto;
    }
    .bubble-assistant {
        background-color: #ffe9e7;
        border: 1px solid rgba(140, 113, 110, 0.2);
        border-radius: 16px 16px 16px 0;
        margin-right: auto;
    }
    
    /* SOS Alert */
    .sos-alert {
        background-color: #ba1a1a;
        color: #ffffff;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        font-weight: 600;
    }

    /* Chat Input Box (styling st.chat_input) */
    [data-testid="stChatInput"] {
        background-color: #ffffff !important;
        border: 1px solid rgba(140, 113, 110, 0.2) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(14,4,4,0.02) !important;
    }
    [data-testid="stChatInput"] button {
        background-color: #aa312e;
        color: white;
        border-radius: 8px;
    }
    
    /* Buttons in sidebar */
    .stButton > button {
        background-color: rgba(204, 73, 68, 0.05);
        color: #aa312e;
        border: 1px solid rgba(170, 49, 46, 0.2);
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: rgba(204, 73, 68, 0.1);
        border-color: #aa312e;
        color: #aa312e;
    }
    
    /* Hide Top Header of Streamlit */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: #e0bfbc;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #8c716e;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vector_store_ready" not in st.session_state:
    st.session_state.vector_store_ready = False
if "uploaded_sources" not in st.session_state:
    st.session_state.uploaded_sources = []
if "patient_id" not in st.session_state:
    st.session_state.patient_id = PATIENT_ID
if "latest_patient_data" not in st.session_state:
    st.session_state.latest_patient_data = None

def check_vector_store():
    try:
        store = get_vector_store()
        results = store.similarity_search("health", k=1)
        return len(results) > 0
    except:
        return False

def process_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def ingest_file(file_content, filename):
    try:
        chunks = chunk_document(file_content)
        texts = []
        metadatas = []
        ids = []
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            metadatas.append({"source": filename, "chunk_index": i})
            ids.append(f"{filename}_{i}")
        store = get_vector_store()
        store.add_raw_texts(texts=texts, metadatas=metadatas, ids=ids)
        return True, f"Successfully ingested {len(texts)} chunks from {filename}"
    except Exception as e:
        return False, f"Error ingesting file: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            AICA
        </div>
        <div class="sidebar-subtitle">
            Institutional Portal
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Control Panel")
    
    if st.button("Download & Ingest Dataset", use_container_width=True):
        with st.spinner("Downloading and processing dataset..."):
            try:
                download_and_export()
                st.success("Dataset downloaded")
                
                with st.spinner("Preprocessing..."):
                    processed_file_path = preprocess_data()
                    with open(processed_file_path, "r", encoding="utf-8") as f:
                        documents = json.load(f)
                    
                    store = get_vector_store()
                    store.add_documents(documents)
                    st.session_state.vector_store_ready = True
                    st.success(f"Successfully ingested {len(documents)} records")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    
    st.markdown("### Document Upload")
    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"], label_visibility="collapsed")
    
    if uploaded_file:
        if st.button("Upload Document", use_container_width=True):
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    if uploaded_file.type == "application/pdf":
                        content = process_pdf(uploaded_file)
                    else:
                        content = uploaded_file.read().decode("utf-8")
                    
                    success, message = ingest_file(content, uploaded_file.name)
                    if success:
                        st.session_state.vector_store_ready = True
                        if uploaded_file.name not in st.session_state.uploaded_sources:
                            st.session_state.uploaded_sources.append(uploaded_file.name)
                        st.success(message)
                        
                        # Process uploaded document for vitals/state
                        with st.spinner("Syncing patient state with new document..."):
                            extracted_data = extract_clinical_data(content[:8000])
                            state = update_patient_state(st.session_state.patient_id, extracted_data)
                            emergency_result = EmergencyDetector.detect(content[:8000], extracted_data.symptoms)
                            trend_result = TrendAnalyzer.analyze(state.vitals_history)
                            score_result = score_patient(state, trend_result["score_modifier"], emergency_result["score_modifier"])
                            all_alerts = list(set(score_result["alerts"] + trend_result["details"] + emergency_result["matched_symptoms"]))
                            AlertEngine.process_alerts(st.session_state.patient_id, score_result["severity"], score_result["score"], all_alerts)
                            
                            st.session_state.latest_patient_data = {
                                "is_emergency": emergency_result["is_emergency"],
                                "emergency_symptoms": emergency_result["matched_symptoms"],
                                "risk_score": score_result["score"],
                                "severity": score_result["severity"],
                                "trend": trend_result,
                                "alerts": all_alerts
                            }
                            
                            from backend.database.models import PatientHistoryRecord
                            history_record = PatientHistoryRecord(
                                patient_id=st.session_state.patient_id,
                                interaction_text=f"Uploaded document: {uploaded_file.name}",
                                extracted_symptoms=extracted_data.symptoms,
                                risk_score=score_result["score"],
                                severity=score_result["severity"]
                            )
                            DatabaseManager.insert_history(history_record)
                            
                            st.rerun() # Refresh UI with new score
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
    
    st.divider()
    
    st.markdown("### Base Dataset Status")
    if check_vector_store():
        st.success("Vector store ready")
    else:
        st.warning("Vector store empty - ingest data first")

# --- TABS ---
tab_overview, tab_vitals, tab_trends, tab_alerts = st.tabs(["Overview", "Vitals History", "Trend Analysis", "Alerts History"])

with tab_overview:
    col1, col2 = st.columns([2, 1])
    
    with col2:
        # Risk Score and active emergency banner on the side
        if st.session_state.latest_patient_data:
            data = st.session_state.latest_patient_data
            render_emergency_banner(data.get("is_emergency", False), data.get("emergency_symptoms", []))
            render_risk_score_card(data.get("risk_score", 0), data.get("severity", "LOW"))
        else:
            render_risk_score_card(0, "LOW")

    with col1:
        # AI Welcome Card
        if len(st.session_state.messages) == 0:
            st.markdown("""
            <div class="ai-welcome">
                <div class="ai-icon-wrapper">
                    <span class="ai-icon material-symbols-outlined">info</span>
                </div>
                <div>
                    <div class="ai-welcome-title">System Initialization</div>
                    <div class="ai-welcome-heading">Hello! I am your AI Healthcare Assistant.<br>How can I help you today?</div>
                    <div class="ai-disclaimer-box">
                        Please remember I am an AI, not a doctor. Always consult a healthcare professional for medical advice or diagnostic confirmation.
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Display chat history
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="bubble bubble-user">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bubble bubble-assistant">{message["content"]}</div>', unsafe_allow_html=True)
                if "retrieved_context" in message:
                    with st.expander("View Retrieved Context"):
                        unique_sources = []
                        for ctx in message["retrieved_context"]:
                            source = ctx.get('source', 'N/A')
                            if source not in unique_sources:
                                unique_sources.append(source)
                        
                        for i, source in enumerate(unique_sources, 1):
                            st.markdown(f"**Document {i}:**")
                            st.markdown(f"Source: {source}")
                            st.divider()

        # Chat input
        user_input = st.chat_input("Ask a health-related question... (e.g., 'What are the symptoms of asthma?')")

        if user_input:
            # Append to state and display immediately
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.pending_query = user_input
            st.rerun() # Ensure user input is displayed immediately before processing

# Process input if needed (we do this outside the main block so it executes even if rerendered)
if st.session_state.get("pending_query"):
    query_to_process = st.session_state.pending_query
    st.session_state.pending_query = None # Clear it so it doesn't loop
    
    try:
        with st.spinner("Processing clinical query..."):
            chat_result = chat_pipeline(query_to_process, st.session_state.patient_id, st.session_state.uploaded_sources)
            
            st.session_state.latest_patient_data = {
                "is_emergency": chat_result["is_emergency"],
                "emergency_symptoms": chat_result["emergency_symptoms"],
                "risk_score": chat_result["risk_score"],
                "severity": chat_result["severity"],
                "trend": chat_result["trend"],
                "alerts": chat_result["alerts"]
            }
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": chat_result["response"],
                "retrieved_context": chat_result["retrieved_context"]
            })
            st.rerun()
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")


with tab_vitals:
    st.markdown("### Vitals History")
    state = get_patient_state(st.session_state.patient_id)
    render_vitals_charts(state.vitals_history)

with tab_trends:
    st.markdown("### Trend Analysis")
    if st.session_state.latest_patient_data and "trend" in st.session_state.latest_patient_data:
        render_trend_indicator(st.session_state.latest_patient_data["trend"])
    else:
        st.info("No recent interactions to analyze trends.")

with tab_alerts:
    st.markdown("### Alert History")
    alerts = DatabaseManager.get_alerts(st.session_state.patient_id)
    render_alert_history(alerts)

