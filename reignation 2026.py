import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتصميم العالي التباين ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    
    /* تحسين البطاقات لتكون داكنة والنص فاتح جداً للوضوح */
    div[data-testid="stMetric"] {
        background-color: #1e293b !important; /* لون كحلي داكن */
        border: 1px solid #334155 !important;
        padding: 20px !important;
        border-radius: 15px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3) !important;
    }
    /* الأرقام باللون السماوي لتبدو بارزة */
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important; 
        font-weight: 800 !important;
        font-size: 2.5rem !important;
    }
    /* العناوين باللون الأبيض الصافي */
    div[data-testid="stMetricLabel"] {
        color: #f1f5f9 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام تسجيل الدخول ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 دخول النظام الآمن")
        u = st.text_input("اسم المستخدم", key="u_login")
        p = st.text_input("كلمة المرور", type="password", key="p_login")
        if st.button("تسجيل الدخول", key="b_login"):
            if u == "zaid" and p == "1111":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("❌ البيانات غير صحيحة")
        return False
    return True

if check_password():
    # --- 3. جلب البيانات من SharePoint ---
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
        # --- 4. شريط التحكم الجانبي ---
        # استخدام أسماء الملفات كما تظهر في مستودعك
        st.sidebar.image("bdc_logo.png", width=160)
        st.sidebar.title("📊 لوحة التحكم")
        
        menu = st.sidebar.radio("القسم الحالي:", ["📈 لوحة الإحصائيات", "🔍 البحث المتقدم", "🚫 القائمة السوداء"])
        
        st.sidebar.divider()
        st.sidebar.subheader("🎯 فلترة دقيقة")
        sel_gen = st.sidebar.multiselect("الجنس:", df['EmpGender'].unique(), default=df['EmpGender'].unique(), key="g_sel")
        sel_skill = st.sidebar.multiselect("المهارة:", df['Skill Level'].unique(), default=df['Skill Level'].unique(), key="s_sel")
        sel_pos = st.sidebar.multiselect("الوظيفة:", df['Main Position'].unique(), default=df['Main Position'].unique(), key="p_sel")

        # تطبيق الفلترة التراكمية
        f_df = df[(df['EmpGender'].isin(sel_gen)) & (df['Skill Level'].isin(sel_skill)) & (df['Main Position'].isin(sel_pos))]

        if menu == "📈 لوحة الإحصائيات":
            st.header("📈 تحليل القوى العاملة (الأرقام الحالية)")
            
            # عرض البطاقات بنمط التباين العالي الجديد
            c1, c2, c3, c4 = st.columns(4)
            total = len(f_df)
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            
            c1.metric("إجمالي المختارين", total)
            c2.metric("عدد الذكور 👨", males)
            c3.metric("عدد الإناث 👩", females)
            c4.metric("نسبة التوطين", f"{(females/total*100 if total>0 else 0):.1f}% إناث")

            st.divider()

            # الرسوم البيانية مع إصلاح خطأ التسمية
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📍 التوزيع حسب المسمى")
                if not f_df.empty:
                    pos_data = f_df['Main Position'].value_counts().reset_index()
                    pos_data.columns = ['المسمى', 'العدد']
                    fig = px.bar(pos_data, x='العدد', y='المسمى', orientation='h', color='العدد', color_continuous_scale='GnBu')
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("📊 مستويات المهارة")
                if not f_df.empty:
                    skill_data = f_df['Skill Level'].value_counts().reset_index()
                    skill_data.columns = ['المهارة', 'العدد']
                    fig2 = px.pie(skill_data, names='المهارة', values='العدد', hole=0.5)
                    st.plotly_chart(fig2, use_container_width=True)

        elif menu == "🔍 البحث المتقدم":
            st.header("🔍 محرك البحث الذكي")
            search_q = st.text_input("ابحث بالاسم أو الرقم الفردي...", key="main_search")
            if search_q:
                res = f_df[f_df.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)]
                st.dataframe(res, use_container_width=True)
            else:
                st.dataframe(f_df, use_container_width=True)

        elif menu == "🚫 القائمة السوداء":
            st.header("🚫 السجل الإداري للحالات الخاصة")
            # الاعتماد على عمود "حالة الموظف" كما طلبت
            bl = df[df['حالة الموظف'].isin(['Blacklist', 'مستقيل'])]
            st.error(f"تنبيه: تم تسجيل {len(bl)} حالة (محظور/مستقيل)")
            st.dataframe(bl, use_container_width=True)

        # أزرار النظام
        st.sidebar.divider()
        if st.sidebar.button("🔄 تحديث البيانات", key="sys_ref"):
            st.cache_data.clear()
            st.rerun()
        if st.sidebar.button("🚪 خروج", key="sys_out"):
            del st.session_state["password_correct"]
            st.rerun()
