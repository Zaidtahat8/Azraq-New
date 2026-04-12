import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
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
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ بيانات الدخول خاطئة")
    st.stop()

# --- 3. جلب البيانات (مع إصلاحات الأخطاء الجانبية) ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        # استخدام engine='openpyxl' لحل مشكلة الصيغة (image_32f9e3.png)
        data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

df = load_data()

# --- 4. إدارة الواجهة والقوائم ---
if df is not None:
    # تجهيز القوائم للفلترة بأمان
    all_projects = sorted(df['Project'].unique().tolist()) if 'Project' in df.columns else []
    all_genders = sorted(df['EmpGender'].unique().tolist()) if 'EmpGender' in df.columns else []
    all_skills = sorted(df['Skill Level'].unique().tolist()) if 'Skill Level' in df.columns else []
    all_positions = sorted(df['Main Position'].unique().tolist()) if 'Main Position' in df.columns else []

    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "🔍 البحث العام", 
        "🔍 محرك البحث التاريخي", 
        "📊 الإحصائيات المرنة", 
        "🚫 القائمة السوداء"
    ])
    
    # 🔍 قسم البحث العام
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        if q:
            search_cols = ['Name', 'Individual Number', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]
            if not results.empty:
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # 🔍 قسم البحث التاريخي (حل خطأ Year و Key)
    elif menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، أو الهاتف)")
        if q_hist:
            search_cols_hist = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_hist = [c for c in search_cols_hist if c in df.columns]
            mask_hist = df[available_hist].apply(lambda x: x.str.contains(q_hist, case=False, na=False)).any(axis=1)
            results_hist = df[mask_hist]

            if not results_hist.empty:
                main_id = results_hist.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                st.subheader(f"👤 ملف الموظف: {results_hist.iloc[0].get('Name', 'N/A')}")
                
                c1, c2 = st.columns(2)
                c1.metric("إجمالي مرات التوظيف", f"{len(full_history)} عقود")
                # استخدام get لتجنب KeyError
                c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A'))
                
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # 📊 قسم الإحصائيات (حل أخطاء الفلترة)
    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        st.sidebar.divider()
        sel_proj = st.sidebar.multiselect("المشاريع:", all_projects, default=all_projects)
        sel_gen = st.sidebar.multiselect("الجنس:", all_genders, default=all_genders)
        
        f_df = df[(df['Project'].isin(sel_proj)) & (df['EmpGender'].isin(sel_gen))]
        
        if not f_df.empty:
            total = len(f_df)
            females = len(f_df[f_df['EmpGender'].str.contains('Female', case=False, na=False)])
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي الفئة", total)
            c2.metric("الإناث 👩", females)
            c3.metric("نسبة الإناث", f"{(females/total*100 if total>0 else 0):.1f}%")
            
            st.plotly_chart(px.pie(f_df, names='Project', title="توزيع المتطوعين حسب المشروع"), use_container_width=True)
        else:
            st.info("💡 استخدم القائمة الجانبية لتصفية البيانات.")

    # 🚫 القائمة السوداء (تمت إعادتها وإصلاحها)
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 الحالات المحظورة والمنع")
        # التحقق من وجود العمود أولاً لتجنب الأخطاء الجانبية
        if 'حالة الموظف' in df.columns:
            # البحث عن كلمة Blacklist أو المنع في حالة الموظف
            bl_mask = df['حالة الموظف'].str.contains('Blacklist|منع|محظور', case=False, na=False)
            bl_df = df[bl_mask]
            if not bl_df.empty:
                st.error(f"⚠️ تم العثور على {len(bl_df)} حالة في القائمة السوداء")
                st.dataframe(bl_df, use_container_width=True)
            else:
                st.success("✅ لا توجد حالات محظورة حالياً.")
        else:
            st.warning("⚠️ عمود 'حالة الموظف' غير موجود في الملف.")

    # أزرار التحكم
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
