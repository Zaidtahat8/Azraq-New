import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والوضوح ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

# منع تحميل الملفات وتحسين خلفية النصوص لضمان الوضوح
st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    .main { background-color: rgba(255, 255, 255, 0.95); border-radius: 10px; padding: 20px; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- 2. جلب البيانات ---
@st.cache_data(ttl=600)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        # تنظيف البيانات وتحويلها لنصوص
        for col in data.columns:
            data[col] = data[col].astype(str).str.replace('.0', '', regex=False).str.strip()
        return data
    except: return None

df = load_data()

if df is not None:
    # --- 3. الشريط الجانبي (Sidebar) ---
    st.sidebar.image("bdc_logo.png", width=150) # إضافة الشعار في الإعدادات
    st.sidebar.title("⚙️ التحكم والنظام")
    
    # خيارات النظام تحت الإعدادات كما طلبت
    menu = st.sidebar.selectbox("اختر القسم المراد استعراضه:", 
                                ["🔍 البحث العام", "📊 الإحصائيات التفصيلية", "🚫 القائمة السوداء (Blacklist)"])
    
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

    # --- 4. معالجة الصفحات بناءً على اختيارك من الإعدادات ---
    
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        
        # استثناء المحظورين من البحث العام
        bl_keywords = ['منقطع', 'انهاء', 'موقوف', 'blacklist']
        active_df = df[~df['Notes'].str.contains('|'.join(bl_keywords), case=False, na=False)]
        
        if q:
            res = active_df[active_df.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)]
            st.success(f"تم العثور على {len(res)} سجل نشط")
            st.dataframe(res, use_container_width=True)
        else:
            st.dataframe(active_df.head(20), use_container_width=True)

    elif menu == "📊 الإحصائيات التفصيلية":
        st.header("📊 تحليل القوى العاملة بالتفصيل")
        
        # الصف الأول: الأرقام الإجمالية
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("إجمالي المتطوعين", len(df))
        m2.metric("الذكور 👨", len(df[df['EmpGender'] == 'Male']))
        m3.metric("الإناث 👩", len(df[df['EmpGender'] == 'Female']))
        m4.metric("المشاريع النشطة", df['Project'].nunique())

        st.divider()

        # الصف الثاني: الرسوم البيانية التفصيلية
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("👫 توزيع النوع الاجتماعي")
            fig_gen = px.pie(df, names='EmpGender', color='EmpGender', 
                             color_discrete_map={'Male':'#007bff','Female':'#e83e8c'},
                             hole=0.4)
            st.plotly_chart(fig_gen, use_container_width=True)

        with c2:
            st.subheader("🛠️ توزيع مستويات المهارة")
            skill_counts = df['Skill Level'].value_counts().reset_index()
            skill_counts.columns = ['Level', 'Total']
            fig_skill = px.bar(skill_counts, x='Level', y='Total', color='Level', text_auto=True)
            st.plotly_chart(fig_skill, use_container_width=True)

        st.divider()
        
        # الصف الثالث: تفاصيل المشاريع والمسميات الوظيفية
        st.subheader("📂 أعداد المتطوعين حسب المشروع")
        proj_df = df['Project'].value_counts().reset_index()
        proj_df.columns = ['Project Name', 'Count']
        st.table(proj_df) # عرض جدول بسيط للأعداد الدقيقة

    elif menu == "🚫 القائمة السوداء (Blacklist)":
        st.header("🚫 سجل القائمة السوداء (Blacklist)")
        st.error("بيانات الأشخاص المحظورين من التوظيف لأسباب إدارية")
        
        bl_keywords = ['منقطع', 'انهاء', 'موقوف', 'blacklist']
        blacklist_df = df[df['Notes'].str.contains('|'.join(bl_keywords), case=False, na=False)]
        
        search_bl = st.text_input("🔍 ابحث عن اسم في سجل المنع")
        if search_bl:
            blacklist_df = blacklist_df[blacklist_df.astype(str).apply(lambda x: x.str.contains(search_bl, case=False, na=False)).any(axis=1)]
        
        st.dataframe(blacklist_df.style.set_properties(**{'background-color': '#fff5f5', 'color': '#b31b1b'}), use_container_width=True)

else:
    st.error("⚠️ فشل في تحميل البيانات من SharePoint. تأكد من اتصال الإنترنت أو رابط الملف.")