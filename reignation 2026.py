import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتصميم المحسن للوضوح ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

# تعديل التصميم لحل مشكلة اللون الأبيض
st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    .main { background-color: rgba(255, 255, 255, 0.9); border-radius: 12px; }
    
    /* تحسين شكل البطاقات الإحصائية لتكون واضحة جداً */
    div[data-testid="stMetric"] {
        background-color: #f8fafc !important; /* خلفية رمادية فاتحة جداً */
        border: 1px solid #e2e8f0 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    /* جعل أرقام الإحصائيات داكنة وبارزة */
    div[data-testid="stMetricValue"] {
        color: #1e293b !important; 
        font-weight: bold !important;
        font-size: 2rem !important;
    }
    /* جعل عناوين البطاقات واضحة */
    div[data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام تسجيل الدخول (حل مشكلة التكرار) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 تسجيل الدخول للنظام")
        u = st.text_input("اسم المستخدم", key="auth_user")
        p = st.text_input("كلمة المرور", type="password", key="auth_pass")
        if st.button("دخول", key="auth_submit"):
            if u == "zaid" and p == "11111":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("❌ بيانات الدخول خاطئة")
        return False
    return True

if check_password():
    # --- 3. جلب البيانات ---
    @st.cache_data(ttl=600)
    def load_data():
        URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
        try:
            res = requests.get(URL)
            data = pd.read_excel(BytesIO(res.content))
            for col in data.columns:
                data[col] = data[col].astype(str).str.replace('.0', '', regex=False).str.strip()
            return data
        except: return None

    df = load_data()

    if df is not None:
        # --- 4. شريط التحكم والفلترة ---
        st.sidebar.image("bdc_logo.png", width=150)
        st.sidebar.title
