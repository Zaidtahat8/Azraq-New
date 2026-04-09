import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. التصميم عالي التباين ---
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

# --- 2. التحقق من الدخول ---
if "password_correct" not in st.session_state:
    st.title("🔐 تسجيل الدخول")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ البيانات خاطئة")
    st.stop()

# --- 3. تحميل البيانات مع تنظيف الأعمدة ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        # تنظيف البيانات لضمان عمل الفلاتر والبحث
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}")
        return None

df = load_data()

if df is not None:
    # --- 4. القائمة الجانبية ---
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية:", ["🔍 محرك البحث التاريخي", "📊 الإحصائيات العامة", "🚫 القائمة السوداء"])
    
    # تعريف القيم الافتراضية للفلاتر لضمان عمل الإحصائيات
    all_genders = sorted(df['EmpGender'].unique().tolist()) if 'EmpGender' in df.columns else []
    all_positions = sorted(df['Main Position'].unique().tolist()) if 'Main Position' in df.columns else []

    if menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 البحث عن السجل الوظيفي")
        query = st.text_input("ابحث بـ (Name, Case Number, Individual Number, الرقم الأمني, رقم الهاتف)", key="search_input")
        
        if query:
            # الأعمدة المحددة للبحث
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_search = [c for c in search_cols if c in df.columns]
            
            # البحث عن التطابق
            mask = df[available_search].apply(lambda x: x.str.contains(query, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                # جلب التاريخ الكامل بناءً على الرقم الفردي لأول نتيجة تظهر
                main_id = results.iloc[0].get('Individual Number', '')
                # إصلاح السطر الذي سبب الخطأ في الصورة
                full_history = df[df['Individual Number'] == main_id]
                
                st.subheader(f"👤 السجل الخاص بـ: {results.iloc[0].get('Name', 'غير معروف')}")
                
                # بطاقات ملخصة باللون الداكن
                c1, c2, c3 = st.columns(3)
                c1.metric("عدد مرات التوظيف", len(full_history))
                c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A'))
                c3.metric("رقم الهاتف", full_history.iloc[-1].get('رقم الهاتف', 'N/A'))

                st.write("📋 **البيانات التاريخية المستخرجة:**")
                # إظهار جدول الشخص المبحوث عنه فقط كما طلبت
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج مطابقة.")

    elif menu == "📊 الإحصائيات العامة":
        st.header("📊 تحليل بيانات الكوادر")
        # فلاتر لضمان عدم اختفاء النتائج
        sel_gen = st.sidebar.multiselect("الجنس:", all_genders, default=all_genders)
        
        stat_df = df[df['EmpGender'].isin(sel_gen)]
        
        if not stat_df.
