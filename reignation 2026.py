import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

# منع التحميل وتحسين الرؤية
st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    .main { background-color: rgba(255, 255, 255, 0.95); border-radius: 10px; padding: 20px; }
    .stMetric { background-color: #f1f3f5; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام تسجيل الدخول (Authentication) ---
def check_password():
    """ترجع True إذا كان المستخدم قد سجل الدخول بنجاح."""
    def password_entered():
        # يمكنك تغيير اسم المستخدم وكلمة المرور هنا
        if st.session_state["username"] == "zaid" and st.session_state["password"] == "11111":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # مسح كلمة المرور من الذاكرة
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # شاشة تسجيل الدخول الأولى
        st.title("🔐 نظام إدارة HR - تسجيل الدخول")
        st.text_input("اسم المستخدم", key="username")
        st.text_input("كلمة المرور", type="password", key="password")
        st.button("دخول", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # إذا كانت البيانات خاطئة
        st.title("🔐 نظام إدارة HR - تسجيل الدخول")
        st.text_input("اسم المستخدم", key="username")
        st.text_input("كلمة المرور", type="password", key="password")
        st.button("دخول", on_click=password_entered)
        st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        return False
    else:
        return True

# --- تنفيذ البرنامج بعد التحقق من الهوية ---
if check_password():
    
    # --- 3. جلب البيانات من SharePoint ---
    @st.cache_data(ttl=600)
    def load_data():
        URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
        try:
            res = requests.get(URL)
            data = pd.read_excel(BytesIO(res.content))
            # تنظيف البيانات وتحويلها لنصوص لسهولة البحث
            for col in data.columns:
                data[col] = data[col].astype(str).str.replace('.0', '', regex=False).str.strip()
            return data
        except: return None

    df = load_data()

    if df is not None:
        # --- 4. الشريط الجانبي (Sidebar) ---
        st.sidebar.image("bdc_logo.png", width=150)
        st.sidebar.title(f"مرحباً، {st.session_state.get('username', 'علاء')}")
        
        menu = st.sidebar.selectbox("القائمة الرئيسية:", 
                                    ["🔍 البحث عن الموظفين", "📊 الإحصائيات العامة", "🚫 القائمة السوداء والمستقيلين"])
        
        st.sidebar.divider()
        if st.sidebar.button("🔄 تحديث قاعدة البيانات"):
            st.cache_data.clear()
            st.rerun()
            
        if st.sidebar.button("🚪 تسجيل الخروج"):
            st.session_state["password_correct"] = False
            st.rerun()

        # --- 5. معالجة الصفحات بناءً على عمود "حالة الموظف" ---
        
        # تعريف الكلمات التي تعني الحظر أو الاستقالة بناءً على طلبك
        blacklist_terms = ['Blacklist', 'مستقيل']

        if menu == "🔍 البحث عن الموظفين":
            st.header("🔍 محرك البحث عن الكوادر النشطة")
            
            # عرض الموظفين الذين حالتهم ليست Blacklist وليست مستقيل
            active_df = df[~df['حالة الموظف'].isin(blacklist_terms)]
            
            q = st.text_input("ابحث بالاسم، الرقم الفردي، أو رقم الهاتف")
            if q:
                res = active_df[active_df.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)]
                st.success(f"تم العثور على {len(res)} موظف نشط")
                st.dataframe(res, use_container_width=True)
            else:
                st.write("📌 عينة من الموظفين النشطين حالياً:")
                st.dataframe(active_df.head(15), use_container_width=True)

        elif menu == "📊 الإحصائيات العامة":
            st.header("📊 التحليل الإحصائي للبيانات")
            
            # تفصيل الإعداد (الذكور والإناث)
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي السجلات", len(df))
            c2.metric("عدد الذكور 👨", len(df[df['EmpGender'] == 'Male']))
            c3.metric("عدد الإناث 👩", len(df[df['EmpGender'] == 'Female']))
            
            st.divider()
            
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("👫 النوع الاجتماعي")
                fig_gen = px.pie(df, names='EmpGender', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_gen, use_container_width=True)
            
            with col_chart2:
                st.subheader("📋 حالة الموظفين")
                fig_status = px.bar(df['حالة الموظف'].value_counts().reset_index(), x='index', y='حالة الموظف', 
                                    labels={'index': 'الحالة', 'حالة الموظف': 'العدد'}, color='index')
                st.plotly_chart(fig_status, use_container_width=True)

        elif menu == "🚫 القائمة السوداء والمستقيلين":
            st.header("🚫 سجل المحظورين والمستقيلين")
            st.warning("هذه الصفحة تعرض الأسماء المدرجة تحت حالة 'Blacklist' أو 'مستقيل' فقط.")
            
            # تصفية البيانات لتشمل فقط المحظورين والمستقيلين
            blacklist_df = df[df['حالة الموظف'].isin(blacklist_terms)]
            
            search_bl = st.text_input("🔍 ابحث عن اسم للتحقق من حالته الإدارية")
            if search_bl:
                res_bl = blacklist_df[blacklist_df.astype(str).apply(lambda x: x.str.contains(search_bl, case=False, na=False)).any(axis=1)]
                if not res_bl.empty:
                    st.error(f"⚠️ تنبيه: تم العثور على {len(res_bl)} سجل مطابق")
                    st.dataframe(res_bl.style.set_properties(**{'background-color': '#fee2e2', 'color': '#b91c1c'}), use_container_width=True)
                else:
                    st.success("✅ الاسم غير موجود في قائمة المحظورين أو المستقيلين.")
            else:
                st.dataframe(blacklist_df, use_container_width=True)

    else:
        st.error("⚠️ فشل في تحميل البيانات. يرجى التأكد من تسمية عمود 'حالة الموظف' بشكل صحيح في ملف الإكسل.")
