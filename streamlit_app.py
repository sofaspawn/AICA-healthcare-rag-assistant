import streamlit as st
import requests
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"  # Adjust if needed

st.set_page_config(page_title="Healthcare RAG Assistant", layout="wide")

st.title(":hospital: Healthcare RAG Assistant")

# Sidebar: Patient selection
patient_id = st.sidebar.text_input("Patient ID", value=os.getenv("DEFAULT_PATIENT", "patient_001"))

# File type selection
file_type = st.sidebar.selectbox(
    "Upload Type",
    ["Document", "Prescription", "Lab Report", "Medical Image", "Audio", "Video"],
)

# Mapping to backend endpoints
endpoint_map = {
    "Document": "/upload/document",
    "Prescription": "/upload/prescription",
    "Lab Report": "/upload/lab-report",
    "Medical Image": "/upload/image",
    "Audio": "/upload/audio",
    "Video": "/upload/video",
}

endpoint = endpoint_map[file_type]

uploaded_file = st.file_uploader(f"Upload a {file_type.lower()}", type=None)
if uploaded_file:
    # Streamlit provides a BytesIO – we need to send as multipart
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    params = {"patient_id": patient_id}
    url = f"{BACKEND_URL}{API_PREFIX}{endpoint}"
    try:
        with st.spinner(f"Sending {uploaded_file.name} to backend …"):
            response = requests.post(url, params=params, files=files)
        response.raise_for_status()
        data = response.json()
        st.success(data.get("message", "File processed successfully"))
        # Show any additional info
        if "summary" in data:
            st.write(data["summary"])  # placeholder for backend specifics
    except Exception as e:
        st.error(f"Error communicating with backend: {e}")

st.markdown("---")
st.subheader(":speech_balloon: Chat with the assistant")
query = st.text_area("Enter your clinical question", height=150)
if st.button("Send"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        chat_url = f"{BACKEND_URL}{API_PREFIX}/chat"
        payload = {"query": query, "patient_id": patient_id}
        try:
            with st.spinner("Waiting for response …"):
                resp = requests.post(chat_url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            st.write(result.get("response", "No response"))
            # Optional: display alerts, vitals badge, etc.
            if result.get("alerts"):
                st.warning("**Alerts:**")
                for alert in result["alerts"]:
                    st.write(f"- {alert}")
        except Exception as e:
            st.error(f"Chat error: {e}")

st.caption("Run this app with `streamlit run streamlit_app.py`. Make sure the FastAPI backend is reachable at the URL defined in `BACKEND_URL`.")
