import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والتصميم الداكن ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    /* حل مشكلة البطاقات البيضاء: خلفية داكنة ونصوص فسفورية */
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
    st.title("🔐 نظام إدارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "alaa" and p == "azraq2026":
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# --- 3. جلب البيانات وتنظيفها ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        # تنظيف البيانات من الفراغات
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except Exception as e:
        st.error(f"فشل تحميل البيانات: {e}")
        return None

df = load_data()

if df is not None:
    # --- 4. القائمة الجانبية ---
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("انتقل إلى:", ["🔍 البحث التاريخي", "📊 الإحصائيات", "🚫 القائمة السوداء"])
    
    if menu == "🔍 البحث التاريخي":
        st.header("🔍 محرك البحث والسجل الوظيفي")
        # مسميات البحث المطلوبة
        q = st.text_input("ابحث بـ (Name, Case Number, Individual Number, الرقم الأمني, رقم الهاتف)", key="search_q")
        
        if q:
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_cols = [c for c in search_cols if c in df.columns]
            
            # فلترة البحث
            mask = df[available_cols].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                # عرض السجل بناءً على Individual Number لأول نتيجة
                main_id = results.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id]
                
                st.subheader(f"👤 السجل الكامل للموظف: {results.iloc[0].get('Name', 'N/A')}")
                
                c1, c2, c3 = st.columns(3)
                c1.metric("مرات التوظيف", len(full_history))
                c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A'))
                c3.metric("الموقع الحالي", full_history.iloc[-1].get('Main Position', 'N/A'))

                st.write("📋 **تفاصيل العقود والسنوات:**")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("🔎 لا توجد نتائج مطابقة.")

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
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 قائمة المحظورين (Blacklist)")
        # فلترة دقيقة للقائمة السوداء
        bl_df = df[df['حالة الموظف'].str.contains('Blacklist', case=False, na=False)]
        
        if not bl_df.empty:
            st.error(f"تنبيه: تم العثور على {len(bl_df)} سجل محظور.")
            st.dataframe(bl_df, use_container_width=True)
        else:
            st.success("✅ لا توجد أسماء في القائمة السوداء.")

    # أزرار التحكم
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("🚪 خروج"):
        del st.session_state["password_correct"]
        st.rerun()
