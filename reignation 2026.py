import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتصميم (نسخة الوضوح العالي) ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    div[data-testid="stMetric"] {
        background-color: #0f172a !important;
        border: 2px solid #1e293b !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricValue"] {
        color: #00f2ff !important;
        font-weight: 800 !important;
    }
    .history-card {
        background-color: #f1f5f9;
        border-right: 5px solid #007bff;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام تسجيل الدخول ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 بوابة إدارة الموارد البشرية")
        u = st.text_input("اسم المستخدم", key="u_v2")
        p = st.text_input("كلمة المرور", type="password", key="p_v2")
        if st.button("دخول", key="b_v2"):
            if u == "zaid" and p == "1111":
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("❌ بيانات الدخول غير صحيحة")
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
            # تحويل جميع البيانات لنصوص لضمان دقة البحث
            for col in data.columns:
                data[col] = data[col].astype(str).str.replace('.0', '', regex=False).str.strip()
            return data
        except: return None

    df = load_data()

    if df is not None:
        # --- 4. الشريط الجانبي ---
        st.sidebar.image("bdc_logo.png", width=150)
        st.sidebar.title("إدارة الكادر")
        menu = st.sidebar.radio("القسم:", ["🔍 محرك البحث التاريخي", "📊 الإحصائيات", "🚫 Blacklist"])

        if menu == "🔍 محرك البحث التاريخي":
            st.header("🔍 البحث عن الموظفين والسجل الوظيفي")
            search_query = st.text_input("أدخل (الاسم، رقم الهاتف، الرقم الفردي، أو رقم المفوضية)", key="main_search")

            if search_query:
                # 1. البحث عن كل السجلات التي تطابق الاستعلام
                results = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)]

                if not results.empty:
                    # 2. تحديد الشخص الفريد (بناءً على الرقم الفردي أو الهاتف)
                    # هنا نفترض أن 'Individual Number' هو المعرف الفريد
                    unique_id = results.iloc[0]['Individual Number'] 
                    
                    # جلب كل تاريخ هذا الشخص من قاعدة البيانات كاملة
                    history_df = df[df['Individual Number'] == unique_id].copy()
                    
                    # 3. عرض بطاقة المعلومات الأساسية
                    st.subheader(f"👤 الملف الشخصي: {results.iloc[0]['EmpName']}")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("عدد مرات التوظيف", len(history_df))
                    c2.metric("الحالة الحالية", history_df.iloc[-1]['حالة الموظف'])
                    c3.metric("الموقع الأخير", history_df.iloc[-1]['Main Position'])

                    st.divider()

                    # 4. عرض التاريخ الوظيفي المفصل
                    st.subheader("🗓️ السجل الزمني للتعاقدات")
                    
                    # تنظيف وتنسيق أعمدة التاريخ (تأكد من مسمياتها في الإكسل)
                    # سنعرض الأعمدة المهمة فقط للتاريخ
                    display_cols = ['Year', 'Start Date', 'End Date', 'Main Position', 'حالة الموظف']
                    # التحقق من وجود الأعمدة لتجنب الأخطاء
                    existing_cols = [c for c in display_cols if c in history_df.columns]
                    
                    st.table(history_df[existing_cols].sort_values(by='Year', ascending=False))

                    with st.expander("👁️ عرض البيانات الكاملة لكل العقود"):
                        st.dataframe(history_df, use_container_width=True)
                else:
                    st.warning("⚠️ لا توجد نتائج مطابقة للبحث.")
            else:
                st.info("💡 نصيحة: البحث بالرقم الفردي أو رقم الهاتف يعطي نتائج أدق للسجل التاريخي.")

        elif menu == "📊 الإحصائيات":
            # (نفس كود الإحصائيات السابق مع التصميم الداكن)
            st.header("📊 الإحصائيات العامة")
            st.write("استخدم الفلاتر الجانبية لتخصيص النتائج.")
            # ... كود الإحصائيات ...

        elif menu == "🚫 Blacklist":
            st.header("🚫 قائمة المحظورين (Blacklist Only)")
            bl_only = df[df['حالة الموظف'] == 'Blacklist']
            st.error(f"يوجد {len(bl_only)} اسم محظور في النظام.")
            st.dataframe(bl_only, use_container_width=True)

        # أزرار النظام
        st.sidebar.divider()
        if st.sidebar.button("🔄 تحديث"):
            st.cache_data.clear()
            st.rerun()
        if st.sidebar.button("🚪 خروج"):
            del st.session_state["password_correct"]
            st.rerun()
