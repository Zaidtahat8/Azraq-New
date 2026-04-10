import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- نظام الدخول ---
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

# --- جلب البيانات ---
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

# --- القوائم الرئيسية (تمت إضافة البحث العام) ---
if df is not None:
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية:", [
        "🔍 البحث العام", 
        "🔍 محرك البحث التاريخي", 
        "📊 الإحصائيات المرنة", 
        "🚫 القائمة السوداء"
    ])
    
    # 1. قسم البحث العام (الطلب الجديد)
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        
        if q:
            # معايير البحث المحددة
            search_cols = ['Name', 'Individual Number', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]
            
            if not results.empty:
                st.success(f"تم العثور على {len(results)} سجل.")
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # 2. قسم البحث التاريخي
    elif menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q_hist = st.text_input("ابحث بـ (الاسم، رقم الكيس، الرقم الفردي، الرقم الأمني، الهاتف)")
        
        if q_hist:
            search_cols_hist = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_hist = [c for c in search_cols_hist if c in df.columns]
            
            mask_hist = df[available_hist].apply(lambda x: x.str.contains(q_hist, case=False, na=False)).any(axis=1)
            results_hist = df[mask_hist]

            if not results_hist.empty:
                main_id = results_hist.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                
                st.subheader(f"👤 ملف الموظف: {results_hist.iloc[0].get('Name', 'N/A')}")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("إجمالي مرات التوظيف", f"{len(full_history)} عقود")
                
                # التحقق من عمود السنة لتفادي KeyError
                year_col = 'Year' if 'Year' in full_history.columns else None
                if year_col:
                    years = sorted(full_history[year_col].unique())
                    c2.metric("أول سنة تعاقد", years[0])
                    c3.metric("آخر سنة تعاقد", years[-1])
                else:
                    last_status = full_history.iloc[-1].get('حالة الموظف', 'N/A')
                    c2.metric("الحالة الأخيرة", last_status)

                st.divider()
                st.write("📂 **بيانات الإكسل الكاملة للموظف:**")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # 3. الإحصائيات
    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        all_projs = sorted(df['Project'].unique().tolist()) if 'Project' in df.columns else []
        sel_proj = st.sidebar.multiselect("المشاريع:", all_projs, default=all_projs)
        
        f_df = df[df['Project'].isin(sel_proj)]
        if not f_df.empty:
            st.metric("إجمالي العدد", len(f_df))
            st.plotly_chart(px.pie(f_df, names='Project', title="توزيع المشاريع"), use_container_width=True)

    # 4. القائمة السوداء
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 المحظورون")
        bl_df = df[df['حالة الموظف'].str.contains('Blacklist', case=False, na=False)]
        st.dataframe(bl_df, use_container_width=True)

    # أزرار التحديث في الشريط الجانبي
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
