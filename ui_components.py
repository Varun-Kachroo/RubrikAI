"""
ui_components.py
Reusable UI components for professional interface
"""

import streamlit as st

def render_header():
    """Render clean, professional header - DARK THEME"""
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0 3rem 0;'>
            <h1 style='font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #818CF8 0%, #A78BFA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem;'>
                📊 RubriqAI
            </h1>
            <p style='font-size: 1.125rem; color: #9CA3AF; font-weight: 400; margin: 0;'>
                AI-Powered Assignment Evaluation
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_section_header(icon, title, subtitle=None):
    """Render a clean section header - DARK THEME"""
    subtitle_html = f"<p style='color: #9CA3AF; font-size: 0.875rem; margin: 0;'>{subtitle}</p>" if subtitle else ""
    
    st.markdown(f"""
        <div style='padding: 1rem 0; border-bottom: 2px solid #374151; margin-bottom: 1.5rem;'>
            <div style='display: flex; align-items: center; gap: 0.75rem;'>
                <span style='font-size: 1.5rem;'>{icon}</span>
                <div>
                    <h2 style='margin: 0; font-size: 1.5rem; font-weight: 600; color: #F9FAFB;'>{title}</h2>
                    {subtitle_html}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_info_card(title, content, icon="ℹ️", color="blue"):
    """Render an information card - DARK THEME"""
    colors = {
        "blue": {"bg": "#1E3A8A", "border": "#3B82F6", "text": "#DBEAFE"},
        "green": {"bg": "#064E3B", "border": "#10B981", "text": "#D1FAE5"},
        "yellow": {"bg": "#78350F", "border": "#F59E0B", "text": "#FEF3C7"},
        "red": {"bg": "#7F1D1D", "border": "#EF4444", "text": "#FEE2E2"},
        "purple": {"bg": "#581C87", "border": "#8B5CF6", "text": "#E9D5FF"}
    }
    
    c = colors.get(color, colors["blue"])
    
    st.markdown(f"""
        <div style='background: {c["bg"]}; border-left: 4px solid {c["border"]}; border-radius: 0.75rem; padding: 1rem 1.25rem; margin: 1rem 0;'>
            <div style='display: flex; gap: 0.75rem; align-items: start;'>
                <span style='font-size: 1.25rem;'>{icon}</span>
                <div style='flex: 1;'>
                    <p style='font-weight: 600; color: {c["text"]}; margin: 0 0 0.25rem 0; font-size: 0.875rem;'>{title}</p>
                    <p style='color: {c["text"]}; margin: 0; font-size: 0.875rem; line-height: 1.5;'>{content}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_stat_card(label, value, icon, trend=None):
    """Render a statistics card"""
    trend_html = ""
    if trend:
        trend_color = "#10B981" if trend >= 0 else "#EF4444"
        trend_icon = "↑" if trend >= 0 else "↓"
        trend_html = f"<span style='color: {trend_color}; font-size: 0.875rem; margin-left: 0.5rem;'>{trend_icon} {abs(trend)}%</span>"
    
    st.markdown(f"""
        <div style='background: white; border: 1px solid #E5E7EB; border-radius: 0.75rem; padding: 1.25rem; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <p style='font-size: 0.75rem; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; margin: 0 0 0.5rem 0;'>{label}</p>
                    <p style='font-size: 1.875rem; font-weight: 700; color: #4F46E5; margin: 0;'>{value}{trend_html}</p>
                </div>
                <span style='font-size: 2rem; opacity: 0.5;'>{icon}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_mode_selector():
    """Render clean evaluation mode selector - DARK THEME"""
    st.markdown("""
        <div style='background: #374151; border-radius: 0.75rem; padding: 1.25rem; margin: 1.5rem 0;'>
            <p style='font-weight: 600; color: #F9FAFB; margin: 0 0 0.75rem 0; font-size: 0.875rem;'>⚙️ Evaluation Mode</p>
        </div>
    """, unsafe_allow_html=True)
    
    mode = st.selectbox(
        "Select evaluation strictness",
        ["Moderate", "Strict", "Lenient"],
        help="Choose how strictly to evaluate answers",
        label_visibility="collapsed"
    )
    
    mode_info = {
        "Strict": ("🔴", "High standards - Minimal partial credit", "red"),
        "Moderate": ("🟡", "Balanced approach - Fair partial credit", "yellow"),
        "Lenient": ("🟢", "Generous grading - Focuses on strengths", "green")
    }
    
    icon, desc, color = mode_info[mode]
    render_info_card(f"{icon} {mode} Mode", desc, icon, color)
    
    return mode


def render_empty_state(icon, title, description, action_text=None):
    """Render empty state placeholder - DARK THEME"""
    action_html = f"<p style='color: #818CF8; font-weight: 500; margin-top: 1rem; font-size: 0.875rem;'>{action_text}</p>" if action_text else ""
    
    st.markdown(f"""
        <div style='text-align: center; padding: 3rem 2rem; background: #374151; border-radius: 0.75rem; border: 2px dashed #4B5563;'>
            <div style='font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;'>{icon}</div>
            <h3 style='font-size: 1.125rem; font-weight: 600; color: #F9FAFB; margin: 0 0 0.5rem 0;'>{title}</h3>
            <p style='color: #9CA3AF; margin: 0; font-size: 0.875rem;'>{description}</p>
            {action_html}
        </div>
    """, unsafe_allow_html=True)


def render_sidebar_section(title, icon=""):
    """Render sidebar section header - DARK THEME"""
    st.markdown(f"""
        <div style='margin: 1.5rem 0 0.75rem 0; padding-left: 0.5rem; border-left: 3px solid #818CF8;'>
            <h3 style='margin: 0; font-size: 0.9375rem; font-weight: 600; color: #F9FAFB;'>
                {icon} {title}
            </h3>
        </div>
    """, unsafe_allow_html=True)


def render_feature_grid(features):
    """Render grid of feature cards"""
    cols = st.columns(len(features))
    
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
                <div style='text-align: center; padding: 1.5rem 1rem; background: white; border: 1px solid #E5E7EB; border-radius: 0.75rem; height: 100%;'>
                    <div style='font-size: 2rem; margin-bottom: 0.75rem;'>{icon}</div>
                    <p style='font-weight: 600; color: #1F2937; margin: 0 0 0.5rem 0; font-size: 0.875rem;'>{title}</p>
                    <p style='color: #6B7280; margin: 0; font-size: 0.75rem; line-height: 1.4;'>{desc}</p>
                </div>
            """, unsafe_allow_html=True)


def render_badge(text, color="primary"):
    """Render a badge"""
    colors = {
        "primary": {"bg": "#EEF2FF", "text": "#4F46E5"},
        "success": {"bg": "#ECFDF5", "text": "#10B981"},
        "warning": {"bg": "#FFFBEB", "text": "#F59E0B"},
        "danger": {"bg": "#FEF2F2", "text": "#EF4444"},
        "secondary": {"bg": "#F3F4F6", "text": "#6B7280"}
    }
    
    c = colors.get(color, colors["primary"])
    
    return f"""
        <span style='display: inline-block; padding: 0.25rem 0.75rem; background: {c["bg"]}; color: {c["text"]}; 
        border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>
            {text}
        </span>
    """
