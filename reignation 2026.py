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
        st.error(f"خطأ في الاتصال: {e}")
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
    
    # 🔍 قسم البحث العام
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        if q:
            search_cols = ['Name', 'Individual Number', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]
            st.dataframe(results, use_container_width=True) if not results.empty else st.warning("⚠️ لا توجد نتائج.")

    # 🔍 محرك البحث التاريخي
    elif menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، أو الهاتف)")
        if q_hist:
            mask_hist = df[['Name', 'Individual Number', 'رقم الهاتف']].apply(lambda x: x.str.contains(q_hist, case=False, na=False)).any(axis=1)
            results_hist = df[mask_hist]
            if not results_hist.empty:
                main_id = results_hist.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                st.subheader(f"👤 ملف الموظف: {results_hist.iloc[0].get('Name', 'N/A')}")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # 📊 الإحصائيات المرنة (الفلترة الذكية المتقدمة المستبدلة)
    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة (فلترة ذكية متقدمة)")
        st.sidebar.divider()
        st.sidebar.subheader("🎯 فلاتر متقدمة")

        base_df = df.copy()

        # الفلاتر الديناميكية
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(base_df['Main Position'].unique()))
        if sel_pos: base_df = base_df[base_df['Main Position'].isin(sel_pos)]

        sel_proj = st.sidebar.multiselect("المشروع:", sorted(base_df['Project'].unique()))
        if sel_proj: base_df = base_df[base_df['Project'].isin(sel_proj)]

        sel_gen = st.sidebar.multiselect("الجنس:", sorted(base_df['EmpGender'].unique()))
        if sel_gen: base_df = base_df[base_df['EmpGender'].isin(sel_gen)]

        sel_skill = st.sidebar.multiselect("مستوى المهارة:", sorted(base_df['Skill Level'].unique()))
        if sel_skill: base_df = base_df[base_df['Skill Level'].isin(sel_skill)]

        f_df = base_df.copy()

        search_inside = st.text_input("🔎 بحث داخل النتائج")
        if search_inside:
            mask_inside = f_df.apply(lambda row: row.astype(str).str.contains(search_inside, case=False).any(), axis=1)
            f_df = f_df[mask_inside]

        total_all = len(df)
        total_filtered = len(f_df)
        st.markdown(f"📌 النتائج: **{total_filtered}** من أصل **{total_all}**")

        if not f_df.empty:
            c1, c2, c3, c4 = st.columns(4)
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            c1.metric("إجمالي", total_filtered)
            c2.metric("ذكور 👨", males)
            c3.metric("إناث 👩", females)
            c4.metric("نسبة الإناث", f"{(females/total_filtered*100 if total_filtered > 0 else 0):.1f}%")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                pos_counts = f_df['Main Position'].value_counts().reset_index()
                pos_counts.columns = ['المسمى', 'العدد']
                fig1 = px.bar(pos_counts.head(10), x='العدد', y='المسمى', orientation='h', color='العدد')
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                proj_counts = f_df['Project'].value_counts().reset_index()
                proj_counts.columns = ['المشروع', 'العدد']
                fig2 = px.pie(proj_counts, names='المشروع', values='العدد', hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)

            st.subheader("📋 البيانات المفلترة")
            st.dataframe(f_df, use_container_width=True)
        else:
            st.warning("⚠️ لا توجد نتائج حسب الفلاتر")

    # 🚫 القائمة السوداء
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 سجل الحالات المحظورة")
        if 'حالة الموظف' in df.columns:
            bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)]
            st.dataframe(bl_df, use_container_width=True) if not bl_df.empty else st.success("✅ لا توجد حالات محظورة.")

    # أزرار التحكم
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
