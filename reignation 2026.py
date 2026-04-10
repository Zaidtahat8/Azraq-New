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

# --- 3. جلب البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except: return None

df = load_data()

if df is not None:
    # --- 4. الشريط الجانبي ---
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية:", ["🔍 محرك البحث التاريخي", "📊 الإحصائيات المرنة", "🚫 القائمة السوداء"])
    
    if menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q = st.text_input("ابحث بـ (الاسم، رقم الكيس، الرقم الفردي، الرقم الأمني، الهاتف)")
        
        if q:
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                main_id = results.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                
                st.subheader(f"👤 ملف الموظف: {results.iloc[0].get('Name', 'N/A')}")
                
                # عرض الإحصائيات (مع معالجة خطأ KeyError)
                c1, c2, c3 = st.columns(3)
                c1.metric("إجمالي مرات التوظيف", f"{len(full_history)} عقود")
                
                # التحقق من وجود عمود السنة أو التاريخ
                year_col = 'Year' if 'Year' in full_history.columns else None
                if year_col:
                    years = sorted(full_history[year_col].unique())
                    c2.metric("أول سنة تعاقد", years[0])
                    c3.metric("آخر سنة تعاقد", years[-1])
                else:
                    c2.metric("الحالة", full_history.iloc[-1].get('حالة الموظف', 'N/A'))

                st.divider()
                st.write("📅 **تفاصيل الفترات والمشاريع:**")
                
                # اختيار أعمدة العرض المتاحة فقط
                display_cols = ['Year', 'Project', 'Main Position', 'Start Date', 'End Date', 'حالة الموظف']
                actual_display = [c for c in display_cols if c in full_history.columns]
                
                st.table(full_history[actual_display])
            else:
                st.warning("⚠️ لا توجد نتائج.")

    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        
        # استخراج خيارات الفلترة
        all_projs = sorted(df['Project'].unique().tolist()) if 'Project' in df.columns else []
        all_gens = sorted(df['EmpGender'].unique().tolist()) if 'EmpGender' in df.columns else []
        
        st.sidebar.subheader("🎯 تخصيص العرض")
        sel_proj = st.sidebar.multiselect("المشاريع:", all_projs, default=all_projs)
        sel_gen = st.sidebar.multiselect("الجنس:", all_gens, default=all_gens)

        f_df = df[(df['Project'].isin(sel_proj)) & (df['EmpGender'].isin(sel_gen))]

        if not f_df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("العدد المفلتر", len(f_df))
            c2.metric("إناث 👩", len(f_df[f_df['EmpGender'].str.contains('Female', case=False)]))
            c3.metric("ذكور 👨", len(f_df[f_df['EmpGender'].str.contains('Male', case=False)]))
            
            st.plotly_chart(px.pie(f_df, names='Project', title="توزيع المشاريع"), use_container_width=True)
        else:
            st.info("💡 اختر من القائمة الجانبية لتحديث البيانات.")

    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 المحظورون")
        bl_df = df[df['حالة الموظف'].str.contains('Blacklist', case=False, na=False)]
        st.dataframe(bl_df)

    # أزرار التحكم
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
