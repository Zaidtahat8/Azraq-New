import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتصميم ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    .main { background-color: rgba(255, 255, 255, 0.95); border-radius: 12px; }
    .stMetric { 
        background-color: #ffffff; padding: 15px; border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-right: 5px solid #007bff;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام تسجيل الدخول المحسن ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 تسجيل الدخول للنظام")
        # إضافة keys فريدة لمنع خطأ التكرار
        u = st.text_input("اسم المستخدم", key="login_user")
        p = st.text_input("كلمة المرور", type="password", key="login_pass")
        if st.button("دخول", key="login_btn"):
            if u == "zaid" and p == "11111":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("❌ بيانات الدخول خاطئة")
        return False
    return True

if check_password():
    # --- 3. جلب البيانات ---
    @st.cache_data(ttl=600)
    def load_data():
        URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
        try:
            res = requests.get(URL)
            data = pd.read_excel(BytesIO(res.content))
            for col in data.columns:
                data[col] = data[col].astype(str).str.replace('.0', '', regex=False).str.strip()
            return data
        except Exception as e:
            return None

    df = load_data()

    if df is not None:
        # --- 4. شريط الفلترة المرنة ---
        st.sidebar.image("bdc_logo.png", width=150)
        st.sidebar.title("🛠️ لوحة التحكم")
        
        menu = st.sidebar.radio("القسم:", ["📊 التحليل الإحصائي", "🔍 البحث والتدقيق", "🚫 الحالات الخاصة"])
        
        st.sidebar.divider()
        st.sidebar.subheader("🎯 فلترة ذكية")
        
        # استخراج القيم الفريدة للفلترة
        genders = df['EmpGender'].unique().tolist()
        skills = df['Skill Level'].unique().tolist()
        positions = df['Main Position'].unique().tolist()

        sel_gen = st.sidebar.multiselect("النوع الاجتماعي:", genders, default=genders, key="f_gen")
        sel_skill = st.sidebar.multiselect("مستوى المهارة:", skills, default=skills, key="f_skill")
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", positions, default=positions, key="f_pos")

        # تطبيق الفلترة التراكمية
        mask = (df['EmpGender'].isin(sel_gen)) & (df['Skill Level'].isin(sel_skill)) & (df['Main Position'].isin(sel_pos))
        f_df = df[mask]

        if menu == "📊 التحليل الإحصائي":
            st.header("📊 نتائج تحليل القوى العاملة")
            
            # البطاقات الرقمية الواضحة
            c1, c2, c3, c4 = st.columns(4)
            total = len(f_df)
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            
            c1.metric("إجمالي الفئة المختارة", total)
            c2.metric("ذكور 👨", males)
            c3.metric("إناث 👩", females)
            c4.metric("التوازن", f"{(females/total*100 if total>0 else 0):.1f}% إناث")

            st.divider()

            # إصلاح خطأ الرسوم البيانية
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📍 التوزيع الوظيفي")
                if not f_df.empty:
                    # نستخدم value_counts ونعيد تسمية الأعمدة يدوياً لتجنب ValueError
                    pos_data = f_df['Main Position'].value_counts().reset_index()
                    pos_data.columns = ['المسمى', 'العدد']
                    fig1 = px.bar(pos_data, x='العدد', y='المسمى', orientation='h', 
                                 color='العدد', color_continuous_scale='Blues', text_auto=True)
                    st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.subheader("📈 مستويات المهارة")
                if not f_df.empty:
                    skill_data = f_df['Skill Level'].value_counts().reset_index()
                    skill_data.columns = ['المهارة', 'العدد']
                    fig2 = px.pie(skill_data, names='المهارة', values='العدد', hole=0.4)
                    st.plotly_chart(fig2, use_container_width=True)

            st.subheader("📑 تفاصيل الأعداد")
            st.table(f_df.groupby(['Main Position', 'EmpGender']).size().reset_index(name='العدد'))

        elif menu == "🔍 البحث والتدقيق":
            st.header("🔍 محرك البحث (ضمن الفلترة الحالية)")
            search = st.text_input("ابحث عن اسم أو رقم فردي...", key="main_search")
            if search:
                res = f_df[f_df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]
                st.dataframe(res, use_container_width=True)
            else:
                st.dataframe(f_df, use_container_width=True)

        elif menu == "🚫 الحالات الخاصة":
            st.header("🚫 سجل المحظورين والمستقيلين")
            # الفلترة بناءً على العمود الجديد "حالة الموظف"
            bl_list = df[df['حالة الموظف'].isin(['Blacklist', 'مستقيل'])]
            st.dataframe(bl_list.style.set_properties(**{'background-color': '#fff5f5', 'color': '#b31b1b'}), use_container_width=True)

        # أزرار النظام في الأسفل
        st.sidebar.divider()
        if st.sidebar.button("🔄 تحديث البيانات", key="sys_refresh"):
            st.cache_data.clear()
            st.rerun()
        if st.sidebar.button("🚪 خروج", key="sys_logout"):
            del st.session_state["password_correct"]
            st.rerun()
    else:
        # إصلاح خطأ السنتكس هنا
        st.error("⚠️ فشل في تحميل البيانات. تأكد من اتصال الإنترنت أو رابط SharePoint.")
