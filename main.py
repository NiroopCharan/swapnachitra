# main.py
import os
import io
import uuid
import json
import urllib.parse
import concurrent.futures
import requests
import random
import streamlit as st
import speech_recognition as sr
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()

# --- LOCAL CORE IMPORTS ---
from core.agent import ForensicAgent
from core.database import DreamDatabase

try:
    from utils.pdf_generator import generate_case_pdf
except ImportError:
    generate_case_pdf = None

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SWAPNA CHITRA | Dream Reconstruction Unit",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

os.makedirs("generated_images", exist_ok=True)

# --- MODERN TECH UI STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap');

    :root { color-scheme: dark !important; }
    html, body, .stApp {
        background-color: #03050a !important;
        background-image: 
            linear-gradient(rgba(0, 240, 255, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.04) 1px, transparent 1px) !important;
        background-size: 32px 32px !important;
        font-family: 'Rajdhani', sans-serif !important;
        color: #e0f2fe !important;
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    section[data-testid="stSidebar"] {
        background-color: #060913 !important;
        border-right: 1px solid rgba(0, 240, 255, 0.25) !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.6);
    }
    div[data-testid="stBottom"], div[data-testid="stBottom"] > div {
        background: #03050a !important;
        border-top: 1px solid rgba(0, 240, 255, 0.2) !important;
    }
    div[data-testid="stChatInput"] > div {
        background-color: rgba(10, 15, 29, 0.95) !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        border-radius: 6px !important;
        box-shadow: 0 0 12px rgba(0, 240, 255, 0.15) !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #00f0ff !important;
        font-family: 'Share Tech Mono', monospace !important;
    }
    div[data-testid="stAudioInput"] {
        background: rgba(10, 15, 29, 0.9) !important;
        border: 1px solid rgba(0, 240, 255, 0.3) !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }
    .hud-header {
        padding-bottom: 15px;
        border-bottom: 2px solid rgba(0, 240, 255, 0.3);
        margin-bottom: 30px;
        position: relative;
    }
    .hud-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 180px;
        height: 2px;
        background: #00f0ff;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
    }
    .title-glitch {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.2rem;
        font-weight: 900;
        color: #ffffff;
        text-shadow: 0 0 8px rgba(0, 240, 255, 0.6);
        margin: 0;
        line-height: 1;
        letter-spacing: 2px;
    }
    .subtitle-tech {
        font-family: 'Share Tech Mono', monospace;
        font-size: 0.95rem;
        color: #7dd3fc;
        letter-spacing: 3px;
        margin-top: 8px;
    }
    [data-testid="stChatMessage"] {
        background: rgba(10, 15, 29, 0.75) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 14px;
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.15rem;
        backdrop-filter: blur(8px);
    }
    [data-testid="chatAvatarIcon-user"] { background-color: #00f0ff !important; color: #03050a !important; }
    [data-testid="chatAvatarIcon-assistant"] { background-color: #bc13fe !important; color: #ffffff !important; }
    div.stButton > button {
        background: rgba(0, 240, 255, 0.06) !important;
        color: #00f0ff !important;
        border: 1px solid #00f0ff !important;
        border-radius: 4px !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.9rem !important;
        letter-spacing: 1.2px !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button:hover {
        background: #00f0ff !important;
        color: #03050a !important;
        box-shadow: 0 0 18px #00f0ff !important;
    }
    div[data-testid="stExpander"] {
        background: rgba(5, 8, 15, 0.7) !important;
        border: 1px solid rgba(0, 240, 255, 0.25) !important;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    div[data-testid="stProgress"] > div > div > div > div {
        background-color: #00f0ff !important;
        box-shadow: 0 0 12px #00f0ff !important;
    }
    .forensic-label {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.85rem;
        color: #bc13fe;
        text-align: center;
        letter-spacing: 2px;
        margin-top: 10px;
        text-transform: uppercase;
        text-shadow: 0 0 5px rgba(188, 19, 254, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- STATE INITIALIZATION ---
if "db" not in st.session_state:
    st.session_state.db = DreamDatabase()

# --- AUTHENTICATION GATEWAY ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown("<h2 class='title-glitch' style='font-size: 2.2rem; text-align: center;'>SECURE TERMINAL</h2>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-family: Share Tech Mono; color: #7dd3fc; margin-bottom: 20px;'>AUTHENTICATION REQUIRED</div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["LOGIN", "REGISTER"])
        with tab1:
            login_id = st.text_input("Agent ID", placeholder="Enter ID...", key="login_id")
            login_pass = st.text_input("Passcode", type="password", placeholder="Enter Passcode...", key="login_pass")
            if st.button("AUTHORIZE UPLINK", width="stretch"):
                if st.session_state.db.verify_user(login_id, login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = login_id
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: Credentials not recognized.")
                    
        with tab2:
            reg_id = st.text_input("New Agent ID", placeholder="Choose an ID...", key="reg_id")
            reg_pass = st.text_input("New Passcode", type="password", placeholder="Create a Passcode...", key="reg_pass")
            if st.button("REGISTER NEW AGENT", width="stretch"):
                if len(reg_id) < 3 or len(reg_pass) < 3:
                    st.warning("Agent ID and Passcode must be at least 3 characters long.")
                elif st.session_state.db.register_user(reg_id, reg_pass):
                    st.success("REGISTRATION SUCCESSFUL. You may now login via the LOGIN tab.")
                else:
                    st.error("REGISTRATION FAILED: Agent ID already exists.")
                    
    st.stop()

# --- SESSION VARIABLES ---
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
if "session_title" not in st.session_state:
    st.session_state.session_title = "New Dream Session"
if "agent" not in st.session_state:
    st.session_state.agent = ForensicAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_images" not in st.session_state:
    st.session_state.active_images = []
if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = ""
if "last_dream" not in st.session_state:
    st.session_state.last_dream = ""
if "confidence_score" not in st.session_state:
    st.session_state.confidence_score = 0
if "processed_audio_hash" not in st.session_state:
    st.session_state.processed_audio_hash = None

# --- PARALLEL IMAGE FETCHING HELPER ---
def fetch_pollinations_image(prompt: str) -> str:
    if not prompt:
        return ""
    unique_name = f"generated_images/{uuid.uuid4().hex}.jpg"
    encoded_prompt = urllib.parse.quote(prompt)
    seed = random.randint(1, 999999) 
    # Removed premium modifiers (&nologo=true&model=flux) to bypass the 402 Payment Required block
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&seed={seed}"
    try:
        headers = {"User-Agent": f"SwapnaChitraApp/1.{random.randint(0, 999)}"}
        response = requests.get(url, headers=headers, timeout=50)
        response.raise_for_status()
        with open(unique_name, "wb") as f:
            f.write(response.content)
        return unique_name
    except Exception as exc:
        print(f"Image generation error: {exc}")
        return ""

def generate_dual_panel_images(realistic_p: str, surreal_p: str) -> list:
    prompts = [realistic_p, surreal_p]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(fetch_pollinations_image, prompts))
    return results

# --- SIDEBAR: THREADED SESSIONS ---
with st.sidebar:
    st.markdown(f"<div style='font-family: Orbitron; color: #00ff66; border: 1px solid #00ff66; padding: 5px; text-align: center; border-radius: 4px; margin-bottom: 20px;'>LOGGED IN: {st.session_state.username.upper()}</div>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='font-family: Orbitron; color: #fff; font-size: 1.1rem;'>Actions</h3>", unsafe_allow_html=True)
    
    if st.button("New Dream Analysis", width="stretch"):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.session_title = "New Dream Session"
        st.session_state.agent = ForensicAgent()
        st.session_state.messages = []
        st.session_state.active_images = []
        st.session_state.last_analysis = ""
        st.session_state.last_dream = ""
        st.session_state.confidence_score = 0
        st.session_state.processed_audio_hash = None
        st.rerun()

    st.markdown("<br><h3 style='font-family: Orbitron; color: #fff; font-size: 1.1rem;'>Dream Journal</h3>", unsafe_allow_html=True)
    
    sessions_list = st.session_state.db.fetch_sessions(username=st.session_state.username, limit=20)
    
    if sessions_list:
        for sess in sessions_list:
            is_active = sess["session_id"] == st.session_state.current_session_id
            badge = "▶ " if is_active else ""
            
            with st.expander(f"{badge}{sess['title']}"):
                st.caption(f"**Updated:** {sess.get('updated_at', '')}")
                c_load, c_del = st.columns([0.7, 0.3])
                with c_load:
                    if st.button("View", key=f"open_{sess['session_id']}", width="stretch"):
                        st.session_state.current_session_id = sess["session_id"]
                        st.session_state.session_title = sess["title"]
                        st.session_state.messages = sess["messages"]
                        st.session_state.active_images = sess["image_paths"]
                        st.session_state.last_analysis = sess["analysis"]
                        st.session_state.confidence_score = sess["confidence_score"]
                        st.session_state.last_dream = sess["messages"][-2]["content"] if len(sess["messages"]) >= 2 else ""
                        st.session_state.agent = ForensicAgent()
                        st.session_state.agent.load_history(sess["messages"])
                        st.rerun()
                
                with c_del:
                    if st.button("Del", key=f"del_{sess['session_id']}", width="stretch"):
                        st.session_state.db.delete_session(sess["session_id"], st.session_state.username)
                        if is_active:
                            st.session_state.current_session_id = str(uuid.uuid4())
                            st.session_state.messages = []
                        st.rerun()
    else:
        st.markdown("<span style='color:#64748b; font-family: Share Tech Mono;'>No saved conversations yet.</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("LOGOUT", width="stretch"):
        st.session_state.clear()
        st.rerun()

# --- TOP HEADER ---
st.markdown("""
<div class="hud-header">
    <h1 class="title-glitch">SWAPNA CHITRA</h1>
    <div class="subtitle-tech">AI-Powered Dream Reconstruction & Visualization</div>
</div>
""", unsafe_allow_html=True)

# --- DISPLAY CHAT STREAM ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- DISPLAY CONFIDENCE & VISUAL RECONSTRUCTION ---
if st.session_state.confidence_score > 0:
    st.progress(
        st.session_state.confidence_score / 100.0,
        text=f"Detail & Clarity Score: {st.session_state.confidence_score}% (Needs 75%+ to reconstruct)"
    )

valid_images = [img for img in st.session_state.active_images if img and os.path.exists(img)]

if len(valid_images) == 2:
    st.markdown("<h3 style='font-family: Orbitron; color: #00f0ff; border-bottom: 1px solid rgba(0,240,255,0.2); padding-bottom: 10px; margin-top: 20px;'>Reconstructed Dream Panels</h3>", unsafe_allow_html=True)
    cols = st.columns(2)
    panel_titles = ["1. REALISTIC", "2. SURREAL"]
    
    for i, col in enumerate(cols):
        img_path = valid_images[i]
        with col:
            st.markdown(f"<div style='border: 1px solid rgba(188,19,254,0.3); padding: 5px; border-radius: 5px; background: rgba(0,0,0,0.5);'>", unsafe_allow_html=True)
            st.image(img_path, use_container_width=True)
            st.markdown(f"<div class='forensic-label'>{panel_titles[i]}</div></div>", unsafe_allow_html=True)
            
            with open(img_path, "rb") as f:
                st.download_button(
                    label=f"⬇ Download {panel_titles[i]}",
                    data=f,
                    file_name=f"SwapnaChitra_{panel_titles[i].split('.')[1].strip().lower()}_{uuid.uuid4().hex[:6]}.jpg",
                    mime="image/jpeg",
                    width="stretch",
                    key=f"dl_img_{i}_{st.session_state.current_session_id}"
                )

    if generate_case_pdf and st.session_state.last_analysis and st.session_state.last_dream:
        st.markdown("<br>", unsafe_allow_html=True)
        pdf_path = generate_case_pdf(
            case_id=abs(hash(st.session_state.current_session_id)) % 10000,
            dream_text=st.session_state.last_dream,
            analysis=st.session_state.last_analysis,
            image_paths=valid_images
        )
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    label="Download Full Dream Report (PDF)",
                    data=pdf_file,
                    file_name=f"SwapnaChitra_Report_{uuid.uuid4().hex[:6]}.pdf",
                    mime="application/pdf",
                    width="stretch"
                )

# --- INPUT SECTION ---
st.markdown("<br><br>", unsafe_allow_html=True)
c_voice, c_hint = st.columns([0.4, 0.6])
with c_voice:
    audio_data = st.audio_input("🎙️ Record Your Dream", key=f"audio_{st.session_state.current_session_id}")

text_prompt = st.chat_input("Describe your dream or answer Morpheus's questions...")
incoming_text = None

if audio_data is not None:
    audio_bytes = audio_data.read()
    current_audio_hash = hash(audio_bytes)
    
    if current_audio_hash != st.session_state.processed_audio_hash:
        st.session_state.processed_audio_hash = current_audio_hash
        with st.spinner("Processing audio locally..."):
            try:
                recognizer = sr.Recognizer()
                with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
                    recorded_audio = recognizer.record(source)
                    incoming_text = recognizer.recognize_google(recorded_audio)
            except sr.UnknownValueError:
                st.error("Could not clearly understand audio. Please speak clearly or type below.")
            except Exception as e:
                st.error(f"Voice processing error: {e}")

if not incoming_text and text_prompt:
    incoming_text = text_prompt

# --- PROCESSING & PERSISTENCE ---
if incoming_text:
    if not st.session_state.messages:
        words = incoming_text.strip().split()
        st.session_state.session_title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
    
    st.session_state.messages.append({"role": "user", "content": incoming_text})
    st.session_state.last_dream = incoming_text
    
    with st.chat_message("user"):
        st.write(incoming_text)

    with st.chat_message("assistant"):
        with st.spinner("Detective Morpheus is analyzing your narrative..."):
            try:
                recon = st.session_state.agent.process_input(incoming_text)
                
                st.write(recon.response_message)
                st.session_state.messages.append({"role": "assistant", "content": recon.response_message})
                st.session_state.last_analysis = recon.response_message
                st.session_state.confidence_score = recon.confidence_score

                if recon.ready_for_reconstruction and recon.confidence_score >= 75:
                    with st.spinner("Clarity threshold reached! Synthesizing 2 visual perspectives..."):
                        saved_paths = generate_dual_panel_images(
                            recon.prompt_realistic or "",
                            recon.prompt_surreal or ""
                        )
                        st.session_state.active_images = saved_paths

                st.session_state.db.save_session(
                    session_id=st.session_state.current_session_id,
                    username=st.session_state.username,
                    title=st.session_state.session_title,
                    messages=st.session_state.messages,
                    analysis=st.session_state.last_analysis,
                    image_paths=st.session_state.active_images,
                    confidence_score=st.session_state.confidence_score
                )
                
                st.rerun()

            except Exception as e:
                st.error(f"Analysis encounter: {str(e)}")