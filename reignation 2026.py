import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات التصميم (الوضوح العالي) ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #0f172a !important;
        border: 2px solid #1e293b !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. الدخول الآمن ---
if "password_correct" not in st.session_state:
    st.title("🔐 دخول النظام")
    u = st.text_input("اسم المستخدم", key="u_v4")
    p = st.text_input("كلمة المرور", type="password", key="p_v4")
    if st.button("دخول"):
        if u == "alaa" and p == "azraq2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ خطأ في البيانات")
    st.stop()

# --- 3. جلب وتنظيف البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        # تنظيف شامل للبيانات لمنع اختفاء النتائج
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except: return None

df = load_data()

if df is not None:
    # --- 4. الشريط الجانبي ---
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة:", ["🔍 محرك البحث التاريخي", "📊 الإحصائيات العامة", "🚫 القائمة السوداء"])
    
    # تحديث الفلاتر الجانبية لضمان عمل الإحصائيات
    st.sidebar.divider()
    all_genders = df['EmpGender'].unique().tolist()
    all_skills = df['Skill Level'].unique().tolist()
    all_positions = df['Main Position'].unique().tolist()

    if menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 البحث عن موظف (السجل الكامل)")
        q = st.text_input("ابحث بـ (Name, Case Number, Individual Number, الرقم الأمني, رقم الهاتف)", key="s_v4")
        
        if q:
            # البحث في الأعمدة المطلوبة فقط
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            valid_search_cols = [c for c in search_cols if c in df.columns]
            
            # فلترة النتائج بناءً على النص المدخل
            results = df[df[valid_search_cols].apply(lambda row: row.str.contains(q, case=False, na=False).any(), axis=1)]

            if not results.empty:
                # عرض بطاقة سريعة لأول نتيجة
                main_ind = results.iloc[0]['Individual Number']
                full_history = df[df['Individual Number'] == main
