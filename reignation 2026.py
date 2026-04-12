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

# --- 3. جلب البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
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
    
    # --- قسم البحث العام المعتمد ---
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

    # --- قسم البحث التاريخي الجديد المعتمد ---
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
                # جلب آخر حالة من العمود المطلوب
                status_val = full_history.iloc[-1].get('حالة الموظف', 'N/A')
                c2.metric("الحالة الحالية", status_val)
                
                st.write("📂 **بيانات الإكسل الكاملة:**")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # 📊 الإحصائيات المرنة مع ميزة التصدير
    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة (فلترة وتصدير)")
        st.sidebar.divider()
        st.sidebar.subheader("🎯 فلاتر متقدمة")

        base_df = df.copy()
        
        # الفلاتر الديناميكية
        cols_to_filter = ['Main Position', 'Project', 'EmpGender', 'Skill Level']
        for col in cols_to_filter:
            if col in base_df.columns:
                options = sorted(base_df[col].unique())
                sel = st.sidebar.multiselect(f"{col}:", options)
                if sel:
                    base_df = base_df[base_df[col].isin(sel)]

        f_df = base_df.copy()
        total_filtered = len(f_df)

        if not f_df.empty:
            c1, c2, c3, c4 = st.columns(4)
            males = len(f_df[f_df['EmpGender'] == 'Male']) if 'EmpGender' in f_df.columns else 0
            females = len(f_df[f_df['EmpGender'] == 'Female']) if 'EmpGender' in f_df.columns else 0
            
            c1.metric("إجمالي الفئة", total_filtered)
            c2.metric("ذكور 👨", males)
            c3.metric("إناث 👩", females)
            c4.metric("نسبة الإناث", f"{(females/total_filtered*100 if total_filtered > 0 else 0):.1f}%")

            st.divider()
            st.subheader("📥 تصدير التقرير المفلتر")
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                f_df.to_excel(writer, index=False, sheet_name='Report')
            
            st.download_button(
                label="📄 تحميل التقرير (Excel)",
                data=output.getvalue(),
                file_name=f"HR_Report_{datetime.date.today()}.xlsx",
                mime="application/vnd.ms-excel"
            )

            col1, col2 = st.columns(2)
            with col1:
                if 'Main Position' in f_df.columns:
                    fig1 = px.bar(f_df['Main Position'].value_counts().head(10), orientation='h', title="أعلى المسميات")
                    st.plotly_chart(fig1, use_container_width=True)
            with col2:
                if 'Project' in f_df.columns:
                    fig2 = px.pie(f_df, names='Project', title="توزيع المشاريع")
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("⚠️ لا توجد نتائج.")

    # 🚫 القائمة السوداء
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 سجل الحالات المحظورة")
        if 'حالة الموظف' in df.columns:
            bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)]
            st.dataframe(bl_df, use_container_width=True) if not bl_df.empty else st.success("✅ القائمة نظيفة.")

    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث قاعدة البيانات"):
        st.cache_data.clear()
        st.rerun()
