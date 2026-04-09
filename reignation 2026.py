import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتصميم (تباين عالٍ للوضوح) ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    div[data-testid="stMetric"] {
        background-color: #0f172a !important;
        border: 2px solid #1e293b !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #00f2ff !important;
        font-weight: 800 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام تسجيل الدخول ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 بوابة إدارة الموارد البشرية")
        u = st.text_input("اسم المستخدم", key="u_v3")
        p = st.text_input("كلمة المرور", type="password", key="p_v3")
        if st.button("دخول", key="b_v3"):
            if u == "zaid" and p == "11111":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("❌ بيانات الدخول غير صحيحة")
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
        # --- 4. الشريط الجانبي ---
        st.sidebar.image("bdc_logo.png", width=150)
        menu = st.sidebar.radio("القسم:", ["🔍 البحث التاريخي", "📊 الإحصائيات", "🚫 Blacklist"])

        if menu == "🔍 البحث التاريخي":
            st.header("🔍 محرك البحث والسجل التاريخي")
            
            # مسميات البحث المطلوبة
            search_query = st.text_input("ابحث عن طريق (Name, Case Number, Individual Number, الرقم الأمني, رقم الهاتف)", key="search_field")

            if search_query:
                # البحث في الأعمدة المحددة فقط
                search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
                # التأكد من وجود هذه الأعمدة في الملف
                available_cols = [c for c in search_cols if c in df.columns]
                
                # تصفية النتائج الأولية
                results = df[df[available_cols].apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]

                if not results.empty:
                    # نعتمد الـ Individual Number كمعرف أساسي لجلب التاريخ
                    ind_num = results.iloc[0]['Individual Number']
                    history_df = df[df['Individual Number'] == ind_num].copy()
                    
                    # عرض بطاقة المعلومات الأساسية
                    st.subheader(f"👤 الملف الوظيفي: {results.iloc[0]['Name']}")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("مرات التوظيف", len(history_df))
                    c2.metric("الحالة الحالية", history_df.iloc[-1].get('حالة الموظف', 'غير محدد'))
                    c3.metric("الرقم الفردي", ind_num)
                    c4.metric("رقم الهاتف", history_df.iloc[-1].get('رقم الهاتف', 'N/A'))

                    st.divider()

                    # عرض جدول التاريخ الوظيفي
                    st.subheader("🗓️ السجل الزمني للعقود")
                    # اختيار أعمدة العرض الأساس
