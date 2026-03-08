import streamlit as st
import google.generativeai as genai
import sqlite3
import os
import requests
import pandas as pd
import hashlib
import smtplib 
import random
import time 
from datetime import datetime, date
from email.message import EmailMessage
from PIL import Image

# --- 🛡️ SAFETY IMPORTS ---
try:
    from streamlit_lottie import st_lottie
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

try:
    from streamlit_mic_recorder import speech_to_text
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False

# --- 🎬 INITIALIZE GLOBALS ---
lottie_orb = None 

# ==========================================
# 🏷️ APP CONFIGURATION
# ==========================================
APP_NAME = "SymptoSense"
APP_ICON = "🟣" 

# ==========================================
# 👇👇 REPLACE THESE WITH YOUR REAL DETAILS 👇👇
SENDER_EMAIL = "dyaswanthgslv@gmail.com"  
APP_PASSWORD = "cmjb igal whua ofml"       
# ==========================================

# --- 🎨 CONFIGURATION ---
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🛠️ SETUP ---
try:
    my_api_key = st.secrets["GOOGLE_API_KEY"]
except:
    my_api_key = "AIzaSyBhW-bRbkg3qPFXNUlCnKuLwBMsCn8LdHg"

genai.configure(api_key=my_api_key)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medical_history.db')

# --- 🎬 ANIMATIONS ---
def load_lottieurl(url):
    if not LOTTIE_AVAILABLE: return None
    try:
        r = requests.get(url, timeout=3)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_orb = load_lottieurl("https://lottie.host/5a889496-5273-41c0-827d-78363717df3f/M387N9O2Q2.json")

# --- 🎨 ADVANCED CSS (Clean Search Bar) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FFFFFF; }
    .stApp { background-color: #FFFFFF; }

    /* Hide standard Streamlit header/footer elements */
    header {visibility: visible; background: transparent;}
    [data-testid="stHeader"] {background-color: rgba(0,0,0,0);}
    footer {visibility: hidden;}

    /* 🟢 VERTICAL SKETCH BUTTONS (Main Menu) */
    .sketch-btn button {
        width: 100% !important;
        border-radius: 20px !important;
        border: 2px solid #333 !important;
        background-color: #FFFFFF !important;
        color: #000 !important;
        font-weight: 600 !important;
        font-size: 18px !important;
        padding: 10px 0px !important;
        box-shadow: 2px 2px 0px rgba(0,0,0,0.1) !important;
        margin-bottom: 8px !important;
    }
    
    /* 🔴 SOS Button */
    div.stButton > button[kind="primary"] {
        background-color: #EF4444 !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 8px rgba(239, 68, 68, 0.4) !important;
    }

    /* 💬 Chat Bubbles */
    .stChatMessage[data-testid="stChatMessageUser"] { 
        background-color: #E3F2FD; 
        color: #000; 
        border-radius: 15px 15px 0px 15px;
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] { 
        background-color: #FFFFFF; 
        border: 1px solid #E0E0E0;
        color: #000; 
        border-radius: 15px 15px 15px 0px;
    }

    /* ------------------------------------------------ */
    /* 🚀 THE MAGIC: UNIFIED SEARCH BAR STYLING */
    /* ------------------------------------------------ */
    
    /* 1. The Container that acts as the "Bar" (Rounded & Bordered) */
    .search-container {
        border: 2px solid #333; 
        border-radius: 30px;
        background-color: white;
        padding: 2px 5px;
        margin-bottom: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); /* Soft shadow */
    }

    /* 2. Remove default Streamlit input styling so it blends in */
    div[data-testid="stTextInput"] input {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        padding-left: 15px;
        font-size: 16px;
    }
    
    /* 3. Style the Icons (Cam/Mic) to look like they are inside the bar */
    div[data-testid="stBottomBlock"] [data-testid="stHorizontalBlock"] button {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        color: #555 !important;
        font-size: 22px !important;
        width: 40px !important;
        height: 40px !important;
    }
    div[data-testid="stBottomBlock"] [data-testid="stHorizontalBlock"] button:hover {
        background: #f0f0f0 !important;
        border-radius: 50% !important;
    }
    
    /* Remove labels/padding above search bar components */
    [data-testid="stBottomBlock"] label { display: none !important; }
    [data-testid="stBottomBlock"] div[data-testid="stVerticalBlock"] > div { padding: 0 !important; }

    /* 4. Language Selector Styling (Above Footer) */
    .lang-container div[data-testid="stSelectbox"] > div > div {
        border-radius: 20px !important;
        border: 2px solid #333 !important;
        background-color: white !important;
    }

    /* 📱 FOOTER POSITIONING */
    div[data-testid="stBottomBlock"] {
        padding-bottom: 20px;
        background-color: white;
        border-top: 1px solid #f0f0f0;
    }

</style>
""", unsafe_allow_html=True)

# --- 🛠️ DATABASE FUNCTIONS ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age TEXT, symptom TEXT, advice TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
        c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, email TEXT, name TEXT, age TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, medicine_name TEXT, reminder_time TEXT, status TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS prescriptions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, extracted_text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
        c.execute('''CREATE TABLE IF NOT EXISTS gamification (
            username TEXT PRIMARY KEY, 
            points INTEGER DEFAULT 0, 
            water_today INTEGER DEFAULT 0, 
            meds_taken_today INTEGER DEFAULT 0,
            last_updated TEXT)''')
        conn.commit()

def get_user_history_list(username):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, symptom, advice, timestamp FROM patients WHERE name=? ORDER BY id DESC LIMIT 15", (username,))
        return c.fetchall()

def get_medical_history_context(username):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT symptom, advice, timestamp FROM patients WHERE name=? ORDER BY timestamp DESC LIMIT 3", (username,))
        data = c.fetchall()
        if data: return "\n".join([f"- {row[2]}: {row[0]}" for row in reversed(data)])
        return ""

def save_to_db(name, age, symptom, advice):
    try: 
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO patients (name, age, symptom, advice) VALUES (?, ?, ?, ?)', (name, age, symptom, advice))
            conn.commit()
        return True
    except: return False

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password, email, name, age):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO users(username, password, email, name, age) VALUES (?,?,?,?,?)', (username, make_hashes(password), email, name, age))
        c.execute('INSERT OR IGNORE INTO gamification (username, points, water_today, meds_taken_today, last_updated) VALUES (?, 0, 0, 0, ?)', (username, date.today().isoformat()))
        conn.commit()

def login_user(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username =? AND password = ?', (username, make_hashes(password)))
        return c.fetchall()

def get_user_email(username):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT email FROM users WHERE username =?', (username,))
        data = c.fetchone()
        return data[0] if data else None

def update_password(username, new_password):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('UPDATE users SET password =? WHERE username =?', (make_hashes(new_password), username))
        conn.commit()

def update_user_age(username, new_age):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('UPDATE users SET age = ? WHERE username = ?', (new_age, username))
        conn.commit()

def send_otp_email(target_email, otp):
    try:
        msg = EmailMessage(); msg.set_content(f"Your {APP_NAME} Password Reset Code is: {otp}"); msg['Subject'] = f'{APP_NAME} Security Code'; msg['From'] = SENDER_EMAIL; msg['To'] = target_email
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465); server.login(SENDER_EMAIL, APP_PASSWORD); server.send_message(msg); server.quit(); return True
    except: return False

def add_reminder(username, med_name, med_time):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO reminders (username, medicine_name, reminder_time, status) VALUES (?, ?, ?, ?)', (username, med_name, med_time, "Active"))
        conn.commit()

def get_reminders(username):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT medicine_name, reminder_time FROM reminders WHERE username=? AND status='Active'", (username,))
        return c.fetchall()

def send_reminder_email(username, med_name):
    email = get_user_email(username)
    if email:
        try:
            msg = EmailMessage(); msg.set_content(f"⏰ It is time to take your medicine: {med_name}\n\nStay Healthy!\n- {APP_NAME}"); msg['Subject'] = f'💊 Medicine Reminder: {med_name}'; msg['From'] = SENDER_EMAIL; msg['To'] = email
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465); server.login(SENDER_EMAIL, APP_PASSWORD); server.send_message(msg); server.quit(); return True
        except: return False
    return False

def send_sos_alert(username):
    email = get_user_email(username)
    if email:
        try:
            msg = EmailMessage(); msg.set_content(f"🚨 EMERGENCY ALERT!\n\nThe user '{username}' has triggered an SOS alert on {APP_NAME}.\n\nPlease contact them immediately.\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M')}"); msg['Subject'] = '🚨 SOS: MEDICAL ALERT'; msg['From'] = SENDER_EMAIL; msg['To'] = email
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465); server.login(SENDER_EMAIL, APP_PASSWORD); server.send_message(msg); server.quit(); return True
        except: return False
    return False

def save_prescription(username, extracted_text):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO prescriptions (username, extracted_text) VALUES (?, ?)', (username, extracted_text))
            conn.commit()
        return True
    except: return False

def get_prescriptions(username):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT extracted_text, timestamp FROM prescriptions WHERE username=? ORDER BY timestamp DESC", (username,))
        return c.fetchall()

# --- GAMIFICATION FUNCTIONS ---
def get_user_stats(username):
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('INSERT OR IGNORE INTO gamification (username, points, water_today, meds_taken_today, last_updated) VALUES (?, 0, 0, 0, ?)', (username, today))
        conn.commit()
        c.execute('SELECT points, water_today, meds_taken_today, last_updated FROM gamification WHERE username=?', (username,))
        row = c.fetchone()
        if row[3] != today:
            c.execute('UPDATE gamification SET water_today=0, meds_taken_today=0, last_updated=? WHERE username=?', (today, username))
            conn.commit()
            return row[0], 0, 0
        return row[0], row[1], row[2]

def update_points(username, points_add, water=False, med=False):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        if water:
            c.execute('UPDATE gamification SET points = points + ?, water_today = water_today + 1 WHERE username=?', (points_add, username))
        elif med:
            c.execute('UPDATE gamification SET points = points + ?, meds_taken_today = 1 WHERE username=?', (points_add, username))
        else:
            c.execute('UPDATE gamification SET points = points + ? WHERE username=?', (points_add, username))
        conn.commit()

# --- ADMIN FUNCTIONS ---
def admin_add_user(username, password, email, name, age):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO users(username, password, email, name, age) VALUES (?,?,?,?,?)', 
                     (username, make_hashes(password), email, name, age))
            c.execute('INSERT OR IGNORE INTO gamification (username, points, water_today, meds_taken_today, last_updated) VALUES (?, 0, 0, 0, ?)', (username, date.today().isoformat()))
            conn.commit()
        return True
    except: return False

def admin_delete_user(username):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()
        return True
    except: return False

def admin_update_user_details(username, new_name, new_age):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET name=?, age=? WHERE username=?", (new_name, new_age, username))
            conn.commit()
        return True
    except: return False

def admin_delete_log(log_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM patients WHERE id=?", (log_id,))
            conn.commit()
        return True
    except: return False

init_db()

# --- SESSION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = ""
if "name" not in st.session_state: st.session_state.name = ""
if "age" not in st.session_state: st.session_state.age = ""
if "otp_sent" not in st.session_state: st.session_state.otp_sent = False
if "real_otp" not in st.session_state: st.session_state.real_otp = 0
if "show_camera" not in st.session_state: st.session_state.show_camera = False
if "messages" not in st.session_state: st.session_state.messages = []
if "user_query" not in st.session_state: st.session_state.user_query = ""
if "pending_image" not in st.session_state: st.session_state.pending_image = None

# --- MODALS ---
@st.dialog("🏆 Health Streak")
def gamification_modal():
    points, water, meds_done = get_user_stats(st.session_state.username)
    level = "🌱 Health Novice"
    if points > 100: level = "🥉 Bronze Achiever"
    if points > 300: level = "🥈 Silver Wellness"
    if points > 600: level = "🥇 Gold Guardian"
    st.metric("Total Points", points, f"Level: {level}")
    st.progress(min(points % 100, 100))
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"💧 **Water:** {water}/8 Cups")
        if water < 8:
            st.button("Drink Cup (+5 pts)", on_click=update_points, args=(st.session_state.username, 5, True, False))
        else: st.success("Daily Goal Met! 🎉")
    with c2:
        st.write("💊 **Daily Meds**")
        if meds_done: st.success("Taken! (+10 pts)")
        else: st.button("Mark Taken (+10 pts)", on_click=update_points, args=(st.session_state.username, 10, False, True))

@st.dialog("🚨 EMERGENCY SOS")
def sos_modal():
    st.error("⚠️ **EMERGENCY MODE ACTIVATED** ⚠️")
    st.write("Call Emergency Services Immediately:")
    col1, col2 = st.columns(2)
    with col1: st.markdown("[📞 **112 (General)**](tel:112)", unsafe_allow_html=True)
    with col2: st.markdown("[🚑 **108 (Ambulance)**](tel:108)", unsafe_allow_html=True)
    st.divider()
    st.write("### 🏥 Instant AI Guide")
    c1, c2, c3, c4 = st.columns(4)
    condition = None
    if c1.button("❤️ Heart Attack"): condition = "Heart Attack First Aid"
    if c2.button("🧠 Stroke"): condition = "Stroke First Aid"
    if c3.button("🩸 Bleeding"): condition = "Severe Bleeding First Aid"
    if c4.button("🔥 Burns"): condition = "Severe Burns First Aid"
    if condition:
        with st.spinner("Fetching steps..."):
            model = genai.GenerativeModel('gemini-2.5-flash')
            resp = model.generate_content(f"Provide immediate, bullet-point first aid instructions for {condition}. Urgent tone. Keep it under 50 words.")
            st.warning(resp.text)
    st.divider()
    if st.button("🔔 Send Alert to Family (Email)", type="primary", use_container_width=True):
        if send_sos_alert(st.session_state.username): st.success("Alert Sent!")
        else: st.error("Failed to send alert.")

@st.dialog("📄 Prescription Digitizer")
def prescription_modal():
    st.write("Upload a clear photo of your prescription:")
    up_file = st.file_uploader("Choose Image", type=['jpg', 'png', 'jpeg'])
    if up_file:
        st.image(up_file, caption="Preview", width=200)
        if st.button("🔍 Digitize & Save"):
            with st.spinner("Reading handwriting..."):
                try:
                    img = Image.open(up_file)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    prompt = "Analyze this prescription image. Extract the list of medicines, their dosages, and frequency. Format cleanly."
                    response = model.generate_content([prompt, img])
                    extracted_data = response.text
                    save_prescription(st.session_state.username, extracted_data)
                    st.success("Digitization Complete!")
                    st.write(extracted_data)
                except Exception as e: st.error(f"Error: {e}")
    st.divider()
    st.write("### 📂 Saved Prescriptions")
    saved = get_prescriptions(st.session_state.username)
    if saved:
        for p in saved:
            with st.expander(f"📅 {p[1]}"): st.write(p[0])
    else: st.caption("No saved prescriptions.")

@st.dialog("⚖️ BMI Calculator")
def bmi_modal():
    st.write("Enter your details:")
    with st.form("bmi_form"):
        w = st.number_input("Weight (kg)", min_value=1.0, max_value=300.0, value=70.0)
        h = st.number_input("Height (cm)", min_value=1.0, max_value=300.0, value=170.0)
        if st.form_submit_button("Calculate"):
            bmi = w / ((h/100)**2)
            if bmi < 18.5: category = "Underweight"; color = "#3B82F6"
            elif 18.5 <= bmi < 24.9: category = "Healthy (Fit)"; color = "#10B981"
            elif 25 <= bmi < 29.9: category = "Overweight"; color = "#F59E0B"
            else: category = "Obese"; color = "#EF4444"
            st.session_state.current_bmi = bmi
            st.session_state.current_bmi_category = category
            st.markdown(f"### Your BMI: **{bmi:.1f}**")
            st.markdown(f"### Status: <span style='color:{color}; font-weight:bold; font-size:20px;'>{category}</span>", unsafe_allow_html=True)
    if "current_bmi" in st.session_state:
        st.divider(); st.info("💡 Want a personalized plan?")
        if st.button("📝 Generate AI Health Plan"):
            with st.spinner("Creating Plan..."):
                hist = get_medical_history_context(st.session_state.username)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Create a 7-Day Health Plan for Age: {st.session_state.age}, BMI: {st.session_state.current_bmi:.1f}, History: {hist}. Include Diet & Workout."
                response = model.generate_content(prompt)
                st.markdown(response.text)

@st.dialog("🥗 AI Health Planner")
def health_plan_modal():
    st.write("## 🥦 Your Personal AI Coach")
    with st.form("health_plan_form"):
        c1, c2 = st.columns(2)
        w = c1.number_input("Weight (kg)", min_value=1.0, value=70.0)
        h = c2.number_input("Height (cm)", min_value=1.0, value=170.0)
        goal = st.selectbox("Goal", ["Lose Weight", "Maintain", "Build Muscle"])
        if st.form_submit_button("✨ Generate Plan"):
            bmi = w / ((h/100)**2)
            with st.spinner("Consulting AI..."):
                hist = get_medical_history_context(st.session_state.username)
                model = genai.GenerativeModel('gemini-2.5-flash')
                prompt = f"Create a 7-Day Health Plan. Age: {st.session_state.age}, BMI: {bmi:.1f}, Goal: {goal}, History: {hist}. Include Diet & Workout."
                response = model.generate_content(prompt)
                st.markdown(response.text)

@st.dialog("💊 Medicine Reminder")
def medicine_modal():
    st.write("Set Alert:")
    st.caption("We will send an email when you log in at this time.")
    with st.form("med_form"):
        m_name = st.text_input("Drug Name"); m_time = st.time_input("Time")
        if st.form_submit_button("Save"):
            add_reminder(st.session_state.username, m_name, m_time.strftime("%H:%M")); st.success("Saved!"); time.sleep(1); st.rerun()

@st.dialog("🚑 First Aid")
def first_aid_modal():
    topic = st.selectbox("Situation", ["CPR", "Choking", "Burns", "Bleeding"])
    if topic == "CPR": st.error("Call 112. Push hard in center of chest.")
    elif topic == "Choking": st.warning("5 Back Blows. 5 Abdominal Thrusts.")
    elif topic == "Burns": st.info("Cool with water for 20 mins.")
    elif topic == "Bleeding": st.error("Apply pressure. Elevate.")

@st.dialog("📜 Past Conversation")
def history_modal(symptom, advice, date):
    st.markdown(f"**Date:** {date}")
    st.markdown(f"**Symptom:** {symptom}")
    st.divider()
    st.markdown(advice)

@st.dialog("📚 Full History")
def full_history_modal():
    st.write("### Your Consultation Logs")
    history_items = get_user_history_list(st.session_state.username)
    if history_items:
        for item in history_items:
            with st.expander(f"📅 {item[3]} - {item[1][:30]}..."):
                st.markdown(f"**Symptom:** {item[1]}"); st.info(f"**Advice:**\n{item[2]}")
    else: st.info("No history found.")

@st.dialog("👤 User Profile")
def profile_modal():
    st.write(f"**User:** {st.session_state.username}")
    st.write(f"**Name:** {st.session_state.name}")
    tab1, tab2 = st.tabs(["Edit Age", "Change Password"])
    with tab1:
        current_age_val = int(st.session_state.age) if st.session_state.age and st.session_state.age.isdigit() else 18
        new_age = st.number_input("Update Age", min_value=1, max_value=120, value=current_age_val)
        if st.button("Save Age"):
            update_user_age(st.session_state.username, str(new_age)); st.session_state.age = str(new_age); st.success("Updated!"); time.sleep(1); st.rerun()
    with tab2:
        curr_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        conf_pass = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            if not curr_pass or not new_pass: st.warning("Please fill fields.")
            elif new_pass != conf_pass: st.error("New passwords do not match.")
            else:
                if login_user(st.session_state.username, curr_pass):
                    update_password(st.session_state.username, new_pass); st.success("Updated!")
                else: st.error("Current password incorrect.")

# --- LOGIN SCREEN ---
def login_screen():
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        # FIXED: Safety check for lottie
        if LOTTIE_AVAILABLE and lottie_orb: 
            st_lottie(lottie_orb, height=120, key="login_anim")
            
        st.markdown(f"<h2 style='text-align: center;'>Welcome to {APP_NAME}</h2>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["Login", "Sign Up", "Reset"])
        with t1:
            u = st.text_input("User", key="l_u"); p = st.text_input("Pass", type="password", key="l_p")
            if st.button("Login", key="l_b", use_container_width=True):
                if u == "admin" and p == "1234":
                    st.session_state.logged_in = True; st.session_state.username = "Administrator"; st.session_state.name = "Administrator"; st.session_state.age = "99"; st.rerun()
                else:
                    res = login_user(u, p)
                    if res: 
                        st.session_state.logged_in=True; st.session_state.username=res[0][0]
                        db_name = res[0][3]
                        st.session_state.name = db_name if db_name and str(db_name).strip() else res[0][0]
                        st.session_state.age=res[0][4]; st.rerun()
                    else: st.error("Invalid")
        with t2:
            nu = st.text_input("User", key="s_u"); ne = st.text_input("Email", key="s_e"); np = st.text_input("Pass", type="password", key="s_p"); nn = st.text_input("Name", key="s_n"); na = st.text_input("Age", key="s_a")
            if st.button("Create", key="s_b", use_container_width=True):
                if nu and np and nn and na:
                    try: add_user(nu, np, ne, nn, na); st.success("Created! Please Login.")
                    except: st.warning("User exists")
                else: st.error("Please fill ALL fields.")
        with t3:
            ru = st.text_input("User", key="r_u")
            if st.button("Send Code", key="r_b", use_container_width=True):
                em = get_user_email(ru)
                if em: otp = random.randint(100000, 999999); st.session_state.real_otp = otp; send_otp_email(em, otp); st.success("Sent"); st.session_state.otp_sent = True
                else: st.error("No user found or Email failed.")
            if st.session_state.otp_sent:
                otp_in = st.text_input("Code", key="r_o"); new_p = st.text_input("New Pass", key="r_np")
                if st.button("Update", key="r_up"):
                    if str(otp_in) == str(st.session_state.real_otp): update_password(ru, new_p); st.success("Updated!"); st.session_state.otp_sent=False
                    else: st.error("Wrong Code")

# --- PATIENT APP ---
def patient_app():
    # --- SIDEBAR (IMAGE DETAILS MENU) ---
    with st.sidebar:
        st.markdown(f"### {APP_ICON} **{APP_NAME}**")
        side_name = st.session_state.name if st.session_state.name else st.session_state.username
        st.caption(f"User: {side_name}")
        
        # Details inside the "Double Arrow" menu
        if st.button("👤 My Profile", use_container_width=True): profile_modal()
        if st.button("📜 Full History", use_container_width=True): full_history_modal()
        if st.button("🚨 SOS EMERGENCY", type="primary", use_container_width=True): sos_modal()
        
        st.markdown("---")
        if st.button("Log Out", use_container_width=True): 
            st.session_state.messages = []; st.session_state.logged_in = False; st.rerun()

    # --- MAIN CONTENT AREA ---
    
    # 1. CENTERED HEADER (Sketch Style)
    if not st.session_state.messages:
        st.markdown(f"""
        <div style="text-align: center; padding-top: 10px; margin-bottom: 20px;">
            <h1 style='color: #000; font-size: 2.5rem; font-family: "Courier New", monospace; margin-bottom: 0;'>Hello, {st.session_state.name.split()[0]}</h1>
            <h3 style='color: #333; font-weight: 400; font-size: 1.2rem; font-family: "Courier New", monospace; margin-top: 5px;'>How can I assist you today?</h3>
        </div>
        """, unsafe_allow_html=True)

    # 2. CHAT HISTORY
    chat_container = st.container()
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): 
                st.write(m["content"])
                if "https://www.google.com/maps/search/SPECIALIST_TYPE+near+me" in m["content"] and m["role"] == "assistant":
                    st.link_button("📍 Find Specialist Near Me", m["content"].split("(")[-1].split(")")[0])

    # 3. VERTICAL BUTTONS (SKETCH STYLE)
    # Only show if no chat messages
    if not st.session_state.messages:
        # Narrow column to match sketch width
        c_left, c_mid, c_right = st.columns([0.5, 3, 0.5])
        with c_mid:
            # Add custom class for sketch styling
            st.markdown('<div class="sketch-btn">', unsafe_allow_html=True)
            if st.button("💊 Medicine"): medicine_modal()
            if st.button("⚖️ BMI Calculator"): bmi_modal()
            if st.button("🚑 First Aid"): first_aid_modal()
            if st.button("📄 Digitizer"): prescription_modal()
            if st.button("🥗 Health Plan"): health_plan_modal()
            if st.button("🏆 Streak"): gamification_modal()
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SPACER ---
    st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)

    # --- LOGIC FOR INPUT ---
    def handle_user_input():
        if st.session_state.user_query.strip():
            st.session_state.messages.append({"role": "user", "content": st.session_state.user_query})
            st.session_state.user_query = "" 

    # --- 5. STICKY FOOTER & LANGUAGE (CLEAN STYLE) ---
    
    with st.container(border=False):
        # Wrapper to hold floating language & search bar
        st.markdown('<div class="footer-wrapper">', unsafe_allow_html=True)
        
        # 1. LANGUAGE BUTTON (Floating Right, above input)
        c_spacer, c_lang = st.columns([3, 1.5])
        with c_lang:
             sel_lang = st.selectbox("Language", ["English", "Hindi", "Tamil", "Telugu"], key="lang_select", label_visibility="collapsed")
             lang_map = {"English":"en-US", "Hindi":"hi-IN", "Tamil":"ta-IN", "Telugu":"te-IN"}
             actual_lang_code = lang_map[sel_lang]

        # 2. UNIFIED SEARCH BAR (Input + Cam + Mic)
        # We use a container with a border to mimic the single box look
        # NO PLUS BUTTON HERE
        with st.container():
            st.markdown('<div class="search-container">', unsafe_allow_html=True)
            
            # Layout: [ Input (Very Wide) ] [ Cam ] [ Mic ]
            c_input, c_cam, c_mic = st.columns([5, 0.5, 0.5])
            
            with c_input:
                st.text_input("Msg...", placeholder=f"Ask {APP_NAME}...", key="user_query", label_visibility="collapsed", on_change=handle_user_input)
            
            with c_cam:
                if st.button("📷", key="cam_btn"): st.session_state.show_camera = not st.session_state.show_camera; st.rerun()
            
            with c_mic:
                if MIC_AVAILABLE:
                    v_txt = speech_to_text(language='en', start_prompt="🎙️", stop_prompt="🛑", just_once=True, key='STT')
                else:
                    v_txt = None
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- PROCESS INPUTS ---
    external_input = None
    if v_txt: external_input = v_txt
    elif st.session_state.show_camera:
        st.info("Camera Mode")
        cam = st.camera_input("Take Photo")
        if cam: 
            st.session_state.pending_image = cam
            external_input = "Analyze this medical image"

    if external_input:
        st.session_state.messages.append({"role": "user", "content": external_input})
        with chat_container:
            with st.chat_message("user"): st.write(external_input)

    # --- GENERATE AI RESPONSE ---
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_msg = st.session_state.messages[-1]["content"]
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        hist = get_medical_history_context(st.session_state.username)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        prompt = f"""
                        Act as {APP_NAME}, a medical expert. Patient: {st.session_state.name}.
                        History: {hist}. Query: {user_msg}.
                        Output Language: {sel_lang} (Translate response).
                        If medical: Give Cause, Precautions, OTC Meds, Doctor Type.
                        If casual: Just chat nicely.
                        """
                        if "Analyze this medical image" in user_msg and st.session_state.pending_image:
                            img = Image.open(st.session_state.pending_image)
                            response = model.generate_content([prompt, img])
                            st.session_state.pending_image = None 
                        else:
                            response = model.generate_content(prompt)
                        
                        full_resp = response.text
                        st.write(full_resp)
                        save_to_db(st.session_state.name, st.session_state.age, user_msg, full_resp)
                        st.session_state.messages.append({"role": "assistant", "content": full_resp})
                    except Exception as e:
                        st.error(f"Error: {e}")

    # --- ALERTS ---
    now_str = datetime.now().strftime("%H:%M"); active = get_reminders(st.session_state.username)
    if active:
        for r in active:
            if r[1] == now_str:
                st.toast(f"🔔 Take {r[0]}!", icon="💊")
                if f"sent_{r[0]}_{now_str}" not in st.session_state: 
                    send_reminder_email(st.session_state.username, r[0])
                    st.session_state[f"sent_{r[0]}_{now_str}"] = True

# --- ADMIN DASHBOARD ---
def admin_dashboard():
    st.sidebar.markdown(f"### 🛡️ Admin")
    if st.sidebar.button("Log Out"): st.session_state.logged_in = False; st.rerun()
    st.title("🛡️ Admin Dashboard")
    tab1, tab2, tab3 = st.tabs(["👥 Manage Users", "➕ Add User", "🩺 Medical Logs"])
    with tab1:
        st.write("Current Users:")
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query("SELECT username, email, name, age FROM users", conn)
        st.dataframe(df, use_container_width=True)
        c_fix, c_del = st.columns(2)
        with c_fix:
            st.subheader("✏️ Update User Details")
            all_users = df['username'].tolist()
            u_to_fix = st.selectbox("Select User", [""] + all_users)
            new_n = st.text_input("New Name")
            new_a = st.text_input("New Age")
            if st.button("Update Details"):
                if u_to_fix and new_n and new_a:
                    if admin_update_user_details(u_to_fix, new_n, new_a):
                        st.success("Updated!"); time.sleep(1); st.rerun()
                else: st.warning("Fill all fields.")
        with c_del:
            st.subheader("🗑️ Delete User")
            target_user = st.selectbox("Delete User", [""] + all_users, key="del_u")
            if st.button("Confirm Delete"):
                if target_user and admin_delete_user(target_user):
                    st.success(f"Deleted {target_user}"); time.sleep(1); st.rerun()
    with tab2:
        st.subheader("Add New User")
        with st.form("add_user_form"):
            c1, c2 = st.columns(2)
            new_u = c1.text_input("Username")
            new_p = c2.text_input("Password", type="password")
            new_e = c1.text_input("Email")
            new_n = c2.text_input("Full Name")
            new_a = st.text_input("Age")
            if st.form_submit_button("➕ Add"):
                if new_u and new_p and new_n and new_a:
                    if admin_add_user(new_u, new_p, new_e, new_n, new_a):
                        st.success(f"Added {new_u}"); time.sleep(1); st.rerun()
                    else: st.error("Exists.")
                else: st.error("Name and Age are required.")
    with tab3:
        st.subheader("Consultation History")
        with sqlite3.connect(DB_PATH) as conn:
            logs_df = pd.read_sql_query("SELECT * FROM patients ORDER BY timestamp DESC", conn)
        st.dataframe(logs_df, use_container_width=True)
        st.divider()
        st.subheader("🗑️ Delete Log")
        if not logs_df.empty:
            log_options = {f"ID {row['id']} - {row['symptom'][:30]}... ({row['name']})": row['id'] for i, row in logs_df.iterrows()}
            selected_option = st.selectbox("Select Log", [""] + list(log_options.keys()))
            if st.button("❌ Delete"):
                if selected_option:
                    if admin_delete_log(log_options[selected_option]):
                        st.success("Deleted."); time.sleep(1); st.rerun()

# --- MAIN CONTROLLER ---
if st.session_state.logged_in:
    if st.session_state.username == "Administrator":
        admin_dashboard()
    else:
        patient_app()
else:
    login_screen()