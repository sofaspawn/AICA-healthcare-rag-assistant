import streamlit as st
from typing import List, Dict, Any
from backend.database.models import AlertRecord

def render_risk_score_card(score: int, severity: str):
    """Renders the main risk score card."""
    
    color_map = {
        "LOW": "#4caf50",       # Green
        "MEDIUM": "#ff9800",    # Orange/Yellow
        "HIGH": "#f44336",      # Red
        "CRITICAL": "#b71c1c"   # Dark Red
    }
    color = color_map.get(severity, "#4caf50")
    
    st.markdown(f"""
    <div style="background-color: white; border: 1px solid rgba(140, 113, 110, 0.2); border-radius: 12px; padding: 24px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; color: #58413f; font-family: 'Newsreader', serif;">Current Risk Profile</h3>
        <div style="font-size: 64px; font-weight: 700; color: {color}; line-height: 1;">{score}</div>
        <div style="font-size: 18px; font-weight: 600; color: {color}; letter-spacing: 0.05em; margin-top: 8px;">{severity} RISK</div>
    </div>
    """, unsafe_allow_html=True)

def render_emergency_banner(is_emergency: bool, matched_symptoms: List[str]):
    if is_emergency:
        symptoms_str = ", ".join(matched_symptoms)
        st.markdown(f"""
        <div style="background-color: #ba1a1a; color: white; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; font-weight: 600; display: flex; align-items: center; gap: 12px;">
            <span class="material-symbols-outlined" style="font-size: 32px;">emergency</span>
            <div>
                <div style="font-size: 18px;">EMERGENCY DETECTED</div>
                <div style="font-size: 14px; font-weight: 400;">Symptoms: {symptoms_str}. Recommend immediate medical escalation.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_trend_indicator(trend_data: Dict[str, Any]):
    trend_state = trend_data.get("trend_state", "STABLE")
    details = trend_data.get("details", [])
    
    icon_map = {
        "IMPROVING": "trending_down", # Down is usually better for HR, fever etc. But depends. We'll use simple icons.
        "STABLE": "trending_flat",
        "DECLINING": "trending_up"
    }
    
    color_map = {
        "IMPROVING": "#4caf50",
        "STABLE": "#ff9800",
        "DECLINING": "#f44336"
    }
    
    st.markdown(f"""
    <div style="background-color: white; border: 1px solid rgba(140, 113, 110, 0.2); border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <h3 style="margin: 0; color: #58413f; font-family: 'Newsreader', serif;">Trend Analysis</h3>
            <span class="material-symbols-outlined" style="color: {color_map[trend_state]}; font-size: 32px;">{icon_map[trend_state]}</span>
        </div>
        <div style="font-size: 24px; font-weight: 700; color: {color_map[trend_state]}; margin-top: 16px;">{trend_state}</div>
        <div style="font-size: 14px; color: #8c716e; margin-top: 8px;">{", ".join(details) if details else "No significant recent changes"}</div>
    </div>
    """, unsafe_allow_html=True)

def render_alert_history(alerts: List[AlertRecord]):
    if not alerts:
        st.info("No active alerts for this patient.")
        return
        
    for alert in alerts:
        color = "#f44336" if alert.severity == "CRITICAL" else "#ff9800"
        st.markdown(f"""
        <div style="border-left: 4px solid {color}; background-color: white; padding: 16px; margin-bottom: 12px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 700; color: {color};">{alert.severity} ALERT</span>
                <span style="font-size: 12px; color: #8c716e;">{alert.timestamp[:16]}</span>
            </div>
            <div style="font-size: 14px; font-weight: 500;">Score: {alert.score}</div>
            <div style="font-size: 14px; color: #58413f; margin-top: 4px;">{", ".join(alert.alerts)}</div>
        </div>
        """, unsafe_allow_html=True)
