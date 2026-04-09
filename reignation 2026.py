import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتصميم الاحترافي (تباين عالي) ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    
    /* حل مشكلة البطاقات البيضاء: خلفية داكنة ونصوص ساطعة */
    div[data-testid="stMetric"] {
        background-color: #0f172a !important; /* كحلي غامق جداً */
        border: 2px solid #1e293b !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #00f2ff !important; /* لون فسفوري بارز للأرقام */
        font-weight: 800 !important;
        font-size: 2.5rem !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #cbd5e1 !important; /* رمادي فاتح للعناوين */
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام الدخول الآمن ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 بوابة الدخول - نظام HR الأزرق")
        u = st.text_input("اسم المستخدم", key="hr_user")
        p = st.text_input("كلمة المرور", type="password", key="hr_pass")
        if st.button("دخول", key="hr_submit"):
            if u == "zaid" and p == "1111":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("❌ البيانات المدخلة غير صحيحة")
        return False
    return True

if check_password():
    # --- 3. تحميل البيانات ---
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
        # --- 4. شريط الفلترة الجانبي ---
        st.sidebar.image("bdc_logo.png", width=150)
        st.sidebar.title("إدارة العمليات")
        
        menu = st.sidebar.radio("انتقل إلى:", ["📈 لوحة الإحصائيات", "🔍 البحث والمتابعة", "🚫 قائمة Blacklist"])
        
        st.sidebar.divider()
        st.sidebar.subheader("🎯 فلاتر العرض")
        sel_gen = st.sidebar.multiselect("النوع الاجتماعي:", df['EmpGender'].unique(), default=df['EmpGender'].unique(), key="g1")
        sel_skill = st.sidebar.multiselect("مستوى المهارة:", df['Skill Level'].unique(), default=df['Skill Level'].unique(), key="s1")
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", df['Main Position'].unique(), default=df['Main Position'].unique(), key="p1")

        # بيانات مفلترة للبحث والإحصائيات
        f_df = df[(df['EmpGender'].isin(sel_gen)) & (df['Skill Level'].isin(sel_skill)) & (df['Main Position'].isin(sel_pos))]

        if menu == "📈 لوحة الإحصائيات":
            st.header("📊 تحليل بيانات الكوادر")
            
            # البطاقات بتنسيق الوضوح العالي
            c1, c2, c3, c4 = st.columns(4)
            total = len(f_df)
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            
            c1.metric("إجمالي الكادر", total)
            c2.metric("الذكور 👨", males)
            c3.metric("الإناث 👩", females)
            c4.metric("نسبة الإناث", f"{(females/total*100 if total>0 else 0):.1f}%")

            st.divider()

            # الرسوم البيانية المحسنة
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📍 التوزيع الوظيفي")
                if not f_df.empty:
                    pos_count = f_df['Main Position'].value_counts().reset_index()
                    pos_count.columns = ['المسمى', 'العدد']
                    fig1 = px.bar(pos_count, x='العدد', y='المسمى', orientation='h', color='العدد', color_continuous_scale='Viridis')
                    st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.subheader("📋 حالة المهارات")
                if not f_df.empty:
                    skill_count = f_df['Skill Level'].value_counts().reset_index()
                    skill_count.columns = ['المهارة', 'العدد']
                    fig2 = px.pie(skill_count, names='المهارة', values='العدد', hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

        elif menu == "🔍 البحث والمتابعة":
            st.header("🔍 محرك بحث الموظفين")
            q = st.text_input("ابحث بالاسم أو الرقم الفردي...", key="search_box")
            if q:
                res = f_df[f_df.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)]
                st.dataframe(res, use_container_width=True)
            else:
                st.dataframe(f_df, use_container_width=True)

        elif menu == "🚫 قائمة Blacklist":
            st.header("🚫 سجل المحظورين (Blacklist)")
            st.info("تعرض هذه الصفحة فقط الأسماء المدرجة تحت حالة 'Blacklist' رسمياً.")
            
            # التعديل المطلوب: الفلترة على Blacklist فقط بغض النظر عن أي حالة أخرى
            blacklist_only = df[df['حالة الموظف'] == 'Blacklist']
            
            if not blacklist_only.empty:
                st.error(f"تنبيه: تم العثور على {len(blacklist_only)} سجل في قائمة المحظورين.")
                # عرض الجدول بتنسيق أحمر للتحذير
                st.dataframe(blacklist_only.style.set_properties(**{'background-color': '#fef2f2', 'color': '#991b1b', 'border-color': '#f87171'}), use_container_width=True)
            else:
                st.success("✅ لا توجد أسماء مدرجة في القائمة السوداء حالياً.")

        # أزرار التحكم
        st.sidebar.divider()
        if st.sidebar.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()
        if st.sidebar.button("🚪 تسجيل الخروج"):
            del st.session_state["password_correct"]
            st.rerun()
