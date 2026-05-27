import streamlit as st
import pandas as pd
from typing import List
from backend.database.models import VitalsRecord

def render_vitals_charts(vitals_history: List[VitalsRecord]):
    if not vitals_history:
        st.info("No vitals history available.")
        return

    # Convert to pandas dataframe
    data = []
    for v in vitals_history:
        d = {
            "timestamp": pd.to_datetime(v.timestamp),
            "SpO2": v.spo2,
            "Heart Rate": v.heart_rate,
            "Temperature": v.temperature,
            "Systolic BP": v.systolic_bp,
            "Diastolic BP": v.diastolic_bp,
            "Respiratory Rate": v.respiratory_rate
        }
        data.append(d)
        
    df = pd.DataFrame(data).set_index("timestamp")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### SpO2 (%)")
        if df["SpO2"].dropna().empty:
            st.write("No data")
        else:
            st.line_chart(df["SpO2"].dropna(), use_container_width=True)
            
        st.markdown("#### Temperature (°F)")
        if df["Temperature"].dropna().empty:
            st.write("No data")
        else:
            st.line_chart(df["Temperature"].dropna(), use_container_width=True)
            
    with col2:
        st.markdown("#### Heart Rate (bpm)")
        if df["Heart Rate"].dropna().empty:
            st.write("No data")
        else:
            st.line_chart(df["Heart Rate"].dropna(), use_container_width=True)
            
        st.markdown("#### Blood Pressure (mmHg)")
        bp_df = df[["Systolic BP", "Diastolic BP"]].dropna()
        if bp_df.empty:
            st.write("No data")
        else:
            st.line_chart(bp_df, use_container_width=True)
