import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات التصميم والتباين ---
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
    st.title("🔐 بوابة الموارد البشرية - BDC")
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
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

df = load_data()

if df is not None:
    # --- 4. الشريط الجانبي والفلاتر المرنة ---
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية:", ["🔍 محرك البحث التاريخي", "📊 الإحصائيات المرنة", "🚫 القائمة السوداء"])
    
    # خيارات الفلاتر
    all_projects = sorted(df['Project'].unique().tolist()) if 'Project' in df.columns else []
    all_genders = sorted(df['EmpGender'].unique().tolist()) if 'EmpGender' in df.columns else []
    all_positions = sorted(df['Main Position'].unique().tolist()) if 'Main Position' in df.columns else []

    if menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q = st.text_input("ابحث بـ (الاسم، رقم الكيس، الرقم الفردي، الرقم الأمني، الهاتف)")
        
        if q:
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                # ميزة "كم مرة توظف عنا"
                main_id = results.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                
                st.subheader(f"👤 ملف الموظف: {results.iloc[0].get('Name', 'N/A')}")
                
                # بطاقات التفاصيل التاريخية
                c1, c2, c3 = st.columns(3)
                num_contracts = len(full_history)
                c1.metric("إجمالي مرات التوظيف", f"{num_contracts} عقود")
                
                years = sorted(full_history['Year'].unique())
                c2.metric("أول سنة تعاقد", years[0] if years else "N/A")
                c3.metric("آخر سنة تعاقد", years[-1] if years else "N/A")

                st.divider()
                
                # عرض تواريخ التعاقد بالتفصيل (الميزة المطلوبة)
                st.write("📅 **الخط الزمني للتعاقدات (التواريخ والمشاريع):**")
                display_cols = ['Year', 'Project', 'Main Position', 'Start Date', 'End Date', 'حالة الموظف']
                actual_cols = [c for c in display_cols if c in full_history.columns]
                
                # ترتيب تنازلي من الأحدث للأقدم
                st.table(full_history[actual_cols].sort_values(by='Year', ascending=False))
                
                with st.expander("🔎 عرض ملف البيانات التقنية"):
                    st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد سجلات مطابقة.")

    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        st.sidebar.divider()
        st.sidebar.subheader("🎯 تخصيص العرض")
        sel_proj = st.sidebar.multiselect("المشاريع:", all_projects, default=all_projects)
        sel_gen = st.sidebar.multiselect("الجنس:", all_genders, default=all_genders)
        
        # تطبيق الفلترة المرنة
        f_df = df[(df['Project'].isin(sel_proj)) & (df['EmpGender'].isin(sel_gen))]
        
        if not f_df.empty:
            # نتائج التحليل بتنسيق البطاقات الداكنة
            c1, c2, c3 = st.columns(3)
            total = len(f_df)
            c1.metric("إجمالي الفئة", total)
            c2.metric("ذكور 👨", len(f_df[f_df['EmpGender'].str.contains('Male', case=False)]))
            c3.metric("إناث 👩", len(f_df[f_df['EmpGender'].str.contains('Female', case=False)]))
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.pie(f_df, names='Project', title="توزيع المشاريع المختارة"), use_container_width=True)
            with col2:
                pos_data = f_df['Main Position'].value_counts().reset_index().head(10)
                pos_data.columns = ['المسمى', 'العدد']
                st.plotly_chart(px.bar(pos_data, x='العدد', y='المسمى', orientation='h', title="أعلى 10 مسميات"), use_container_width=True)
        else:
            st.info("💡 استخدم القائمة الجانبية لتحديد المشاريع.")

    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 سجل الحالات المحظورة")
        bl_df = df[df['حالة الموظف'].str.contains('Blacklist', case=False, na=False)]
        if not bl_df.empty:
            st.error(f"تنبيه: تم العثور على {len(bl_df)} سجل محظور.")
            st.dataframe(bl_df, use_container_width=True)
        else:
            st.success("✅ القائمة نظيفة.")

    # أزرار التحكم
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
