import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
import datetime

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

# --- 3. جلب البيانات (معالجة مشكلة Zip File) ---
@st.cache_data(ttl=300)
def load_data():
    # الرابط المباشر للتحميل من OneDrive
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL, timeout=10)
        # التحقق من أن الاستجابة ناجحة
        if res.status_code == 200:
            data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
            for col in data.columns:
                data[col] = data[col].astype(str).str.strip().replace('nan', '')
            return data
        else:
            st.error("⚠️ فشل الوصول للملف، يرجى التحقق من رابط OneDrive.")
            return None
    except Exception as e:
        st.error(f"خطأ في الاتصال أو الملف: {e}")
        return None

df = load_data()

# --- 4. إدارة الواجهة والقوائم ---
if df is not None:
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "🔍 البحث العام", 
        "🔍 محرك البحث التاريخي", 
        "📊 الإحصائيات المرنة", 
        "🚫 القائمة السوداء"
    ])
    
    # --- قسم البحث العام ---
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        if q:
            search_cols = ['Name', 'Individual Number', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]
            if not results.empty:
                st.success(f"تم العثور على {len(results)} سجل.")
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # --- قسم البحث التاريخي المحدث ---
    elif menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، الهاتف، أو الرقم الأمني)")
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
                c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A'))
                
                st.write("📂 **بيانات الإكسل الكاملة:**")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # --- قسم الإحصائيات (معالجة مشكلة التصدير) ---
    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة (فلترة وتصدير)")
        st.sidebar.divider()
        st.sidebar.subheader("🎯 فلاتر متقدمة")

        base_df = df.copy()
        
        # الفلاتر
        cols_filter = ['Main Position', 'Project', 'EmpGender']
        for col in cols_filter:
            if col in base_df.columns:
                sel = st.sidebar.multiselect(f"{col}:", sorted(base_df[col].unique()))
                if sel:
                    base_df = base_df[base_df[col].isin(sel)]

        f_df = base_df.copy()
        
        if not f_df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي الفئة", len(f_df))
            c2.metric("ذكور", len(f_df[f_df['EmpGender'] == 'Male']))
            c3.metric("إناث", len(f_df[f_df['EmpGender'] == 'Female']))

            st.divider()
            st.subheader("📥 تصدير التقرير")
            
            # تصدير كملف CSV (لضمان العمل دون مشاكل مكتبات Excel)
            csv = f_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تحميل النتائج المفلترة (CSV)",
                data=csv,
                file_name=f"HR_Report_{datetime.date.today()}.csv",
                mime="text/csv"
            )

            # رسوم بيانية سريعة
            if 'Project' in f_df.columns:
                st.plotly_chart(px.pie(f_df, names='Project', title="توزيع المشاريع"), use_container_width=True)
        else:
            st.warning("⚠️ لا توجد نتائج.")

    # --- قسم القائمة السوداء (معالجة مشكلة الإزاحة) ---
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 سجل الحالات المحظورة")
        if 'حالة الموظف' in df.columns:
            bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)]
            if not bl_df.empty:
                st.dataframe(bl_df, use_container_width=True)
            else:
                st.success("✅ لا توجد حالات محظورة حالياً.")

    # زر التحديث
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث قاعدة البيانات"):
        st.cache_data.clear()
        st.rerun()
