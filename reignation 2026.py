import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات التصميم عالي التباين ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #0f172a !important;
        border: 2px solid #1e293b !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام الدخول ---
if "password_correct" not in st.session_state:
    st.title("🔐 بوابة إدارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "alaa" and p == "azraq2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ بيانات الدخول خاطئة")
    st.stop()

# --- 3. جلب البيانات وتنظيفها ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        # تنظيف البيانات لضمان دقة الربط التاريخي
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

df = load_data()

if df is not None:
    # --- 4. الشريط الجانبي ---
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية:", ["🔍 محرك البحث التاريخي", "📊 الإحصائيات المرنة", "🚫 القائمة السوداء"])
    
    # تحضير خيارات الفلاتر
    all_projects = sorted(df['Project'].unique().tolist()) if 'Project' in df.columns else []
    all_genders = sorted(df['EmpGender'].unique().tolist()) if 'EmpGender' in df.columns else []
    all_positions = sorted(df['Main Position'].unique().tolist()) if 'Main Position' in df.columns else []

    if menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 البحث الشامل وتفاصيل العقود")
        q = st.text_input("ابحث بـ (الاسم، رقم الكيس، الرقم الفردي، الرقم الأمني، الهاتف)")
        
        if q:
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                # تجميع التاريخ بناءً على Individual Number لضمان شمولية السجل
                main_id = results.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                
                st.subheader(f"👤 ملف الموظف: {results.iloc[0].get('Name', 'N/A')}")
                
                # بطاقات الحالة التاريخية (الميزة المطلوبة)
                c1, c2, c3 = st.columns(3)
                num_contracts = len(full_history)
                c1.metric("إجمالي مرات التوظيف", f"{num_contracts} عقود")
                
                # تحديد أول وآخر فترة تعاقد
                years = sorted(full_history['Year'].unique())
                c2.metric("أول ظهور في المخيم", years[0] if years else "N/A")
                c3.metric("آخر ظهور في المخيم", years[-1] if years else "N/A")

                st.divider()
                
                # عرض جدول التواريخ التفصيلي (الخط الزمني)
                st.write("📅 **الجدول الزمني للتعاقدات (من الأحدث للقديم):**")
                display_cols = ['Year', 'Project', 'Main Position', 'Start Date', 'End Date', 'حالة الموظف']
                actual_cols = [c for c in display_cols if c in full_history.columns]
                
                # استخدام st.table لعرض التواريخ بشكل ثابت وواضح
                st.table(full_history[actual_cols].sort_values(by='Year', ascending=False))
                
                with st.expander("🔎 عرض ملف البيانات الكامل"):
                    st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد سجلات مطابقة لهذا البحث.")

    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        # فلاتر الإحصائيات
        st.sidebar.divider()
        st.sidebar.subheader("🎯 تخصيص العرض")
        sel_proj = st.sidebar.multiselect("المشاريع:", all_projects, default=all_projects)
        sel_gen = st.
