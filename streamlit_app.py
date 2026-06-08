import streamlit as st
import os

st.set_page_config(
    page_title="Platform Moved",
    page_icon="⚠️",
    layout="centered",
)

st.error("### 🚀 THE FRONTEND HAS BEEN UPGRADED")
st.markdown("""
The Streamlit interface has been fully replaced with a premium, state-of-the-art **HTML/JS** dashboard as per the provided design specifications.

### How to access the new application:
1. Open your terminal.
2. Stop this Streamlit server (Ctrl+C).
3. Run the unified platform script:
```bash
./run_platform.sh
```
4. Open **[http://localhost:8000](http://localhost:8000)** in your browser to see the new fully functional UI!

> **Note:** The new frontend natively hits the FastAPI backend and uses Vite for compilation. The Streamlit code has been archived.
""")
