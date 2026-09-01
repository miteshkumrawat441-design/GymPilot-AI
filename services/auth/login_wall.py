import streamlit as st
import os
import base64
from services.persistence.exercise_repository import get_or_create_user


def get_base64_image(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""


def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    logo_b64 = get_base64_image(os.path.join(os.getcwd(), "static", "gympilot_logo.png"))
    athlete_b64 = get_base64_image(os.path.join(os.getcwd(), "static", "athlete_visual.png"))
    wave_b64 = get_base64_image(os.path.join(os.getcwd(), "static", "session_waveform.png"))
    icon_rep_b64 = get_base64_image(os.path.join(os.getcwd(), "static", "icon_rep.png"))
    icon_form_b64 = get_base64_image(os.path.join(os.getcwd(), "static", "icon_form.png"))
    icon_voice_b64 = get_base64_image(os.path.join(os.getcwd(), "static", "icon_voice.png"))

    # 2-column layout matching the target mockup
    col_left, col_right = st.columns([1.18, 0.95], gap="large")

    with col_left:
        logo_html = f'<img src="{logo_b64}" height="36" alt="GymPilot AI" style="margin-bottom: 1.25rem; display: block;">' if logo_b64 else '<span class="gp-brand-name">GYMPILOT <span>AI</span></span>'
        athlete_html = f'<div class="gp-athlete-visual-box"><img src="{athlete_b64}" alt="Pose Analysis" style="width: 100%; max-width: 380px; border-radius: 12px;"></div>' if athlete_b64 else ''

        rep_img = f'<img src="{icon_rep_b64}" width="42" height="42" style="border-radius: 50%; display: block;" alt="Reps">' if icon_rep_b64 else '<div class="gp-feature-circle">🏋️</div>'
        form_img = f'<img src="{icon_form_b64}" width="42" height="42" style="border-radius: 50%; display: block;" alt="Form">' if icon_form_b64 else '<div class="gp-feature-circle">🧘</div>'
        voice_img = f'<img src="{icon_voice_b64}" width="42" height="42" style="border-radius: 50%; display: block;" alt="Voice">' if icon_voice_b64 else '<div class="gp-feature-circle">🎙️</div>'

        st.html(f"""
<div class="gp-hero-left">
    <!-- GymPilot AI Brand Logo -->
    <div class="gp-login-brand">
        {logo_html}
    </div>

    <!-- Main Headline -->
    <h1 class="gp-hero-headline">
        Train smarter.<br>
        <span class="gp-green-text">Move stronger.</span>
    </h1>

    <p class="gp-hero-desc">
        Your AI-powered workout companion that counts every rep and helps you improve your form in real time.
    </p>

    <!-- 3 Core Feature Rows -->
    <div class="gp-feature-rows">
        <div class="gp-feature-row">
            {rep_img}
            <div>
                <div class="gp-feature-title">Real-time rep counting</div>
                <div class="gp-feature-sub">Accurate reps with live tracking</div>
            </div>
        </div>

        <div class="gp-feature-row">
            {form_img}
            <div>
                <div class="gp-feature-title">Form feedback</div>
                <div class="gp-feature-sub">Get instant form correction</div>
            </div>
        </div>

        <div class="gp-feature-row">
            {voice_img}
            <div>
                <div class="gp-feature-title">AI coaching</div>
                <div class="gp-feature-sub">Voice guidance that keeps you going</div>
            </div>
        </div>
    </div>

    <!-- Center Glowing Athlete Pose Wireframe Artwork -->
    {athlete_html}

    <!-- Bottom Privacy Badge -->
    <div class="gp-privacy-badge">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <path d="M9 12l2 2 4-4"/>
        </svg>
        <div>
            <div class="gp-privacy-title">Your privacy matters</div>
            <div class="gp-privacy-sub">100% secure. Your data stays with you.</div>
        </div>
    </div>
</div>
""")

    with col_right:
        wave_html = f'<img src="{wave_b64}" alt="Waveform" style="width: 100%; height: 28px; object-fit: contain;">' if wave_b64 else '<svg width="100%" height="24" viewBox="0 0 300 24" fill="none"><path d="M0 12H70 Q85 12 95 6 T115 18 T135 4 T155 20 T175 6 T195 16 T210 12 H300" stroke="#22C55E" stroke-width="2.2"/></svg>'

        # Top Card: Session Access with Audio/Sensor Waveform
        st.html(f"""
<div class="gp-session-access-card">
    <div class="gp-session-access-header">
        <span class="gp-session-access-title">SESSION ACCESS</span>
        <span class="gp-ready-badge"><span class="gp-ready-dot"></span>READY</span>
    </div>
    <div class="gp-waveform-box">
        {wave_html}
    </div>
</div>
""")

        # Main Login Form Card
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("YOUR NAME", placeholder="👤  Enter your name")
            submit_button = st.form_submit_button("➔  Start Training", width="stretch")

        # Bottom Footer & 3 Clean Outlined Icons
        st.html("""
<div class="gp-login-footer">
    <div class="gp-login-footer-text">Your camera. Your movement. Your coach.</div>
    <div class="gp-login-footer-icons">
        <!-- Camera Icon -->
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
            <circle cx="12" cy="13" r="4"/>
        </svg>
        <span class="gp-icon-divider">|</span>
        <!-- Athlete Icon -->
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="4" r="2.5"/>
            <path d="M12 7l-2 5 3 2-2 6M10 12l-4-1M13 14l4 4"/>
        </svg>
        <span class="gp-icon-divider">|</span>
        <!-- Headphones Icon -->
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 18v-6a9 9 0 0 1 18 0v6"/>
            <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
        </svg>
    </div>
</div>
""")

    if submit_button:
        if not username:
            st.error("Name cannot be empty.")
            return False
        
        # Clean user string if user copied placeholder prefix
        cleaned_username = username.replace("👤", "").strip()
        if not cleaned_username:
            st.error("Name cannot be empty.")
            return False

        user = get_or_create_user(cleaned_username)
    
        st.session_state["user_id"] = user["id"]
        st.session_state["username"] = user["username"]

        st.rerun()

    return False