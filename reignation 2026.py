import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    [data-testid="stElementToolbar"] { display: none; }
    .main { background-color: rgba(255, 255, 255, 0.95); border-radius: 12px; padding: 25px; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-right: 5px solid #007bff;
    }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #007bff; }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام تسجيل الدخول ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 تسجيل الدخول للنظام")
        u = st.text_input("اسم المستخدم", key="username")
        p = st.text_input("كلمة المرور", type="password", key="password")
        if st.button("دخول"):
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
        except: return None

    df = load_data()

    if df is not None:
        # --- 4. الفلترة المرنة في الشريط الجانبي ---
        st.sidebar.image("bdc_logo.png", width=150)
        st.sidebar.title("🛠️ فلاتر التحكم")
        
        # اختيار القسم الرئيسي
        menu = st.sidebar.radio("انتقل إلى:", ["📊 لوحة التحليل الذكية", "🔍 البحث التفصيلي", "🚫 القائمة السوداء"])
        
        st.sidebar.divider()
        st.sidebar.subheader("🎯 تخصيص النتائج")
        
        # فلاتر متعددة الخيارات (Multi-select) لمرونة كاملة
        selected_gender = st.sidebar.multiselect("النوع الاجتماعي:", options=df['EmpGender'].unique(), default=df['EmpGender'].unique())
        selected_skill = st.sidebar.multiselect("مستوى المهارة:", options=df['Skill Level'].unique(), default=df['Skill Level'].unique())
        selected_position = st.sidebar.multiselect("المسمى الوظيفي:", options=df['Main Position'].unique(), default=df['Main Position'].unique())

        # تطبيق الفلترة على البيانات
        filtered_df = df[
            (df['EmpGender'].isin(selected_gender)) & 
            (df['Skill Level'].isin(selected_skill)) & 
            (df['Main Position'].isin(selected_position))
        ]

        if menu == "📊 لوحة التحليل الذكية":
            st.header("📊 تحليل بيانات القوى العاملة (نتائج مفلترة)")
            
            # صف البطاقات الرقمية
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("إجمالي المختارين", len(filtered_df))
            m2.metric("ذكور 👨", len(filtered_df[filtered_df['EmpGender'] == 'Male']))
            m3.metric("إناث 👩", len(filtered_df[filtered_df['EmpGender'] == 'Female']))
            m4.metric("نسبة الإناث", f"{(len(filtered_df[filtered_df['EmpGender'] == 'Female'])/len(filtered_df)*100 if len(filtered_df)>0 else 0):.1f}%")

            st.divider()

            # الرسوم البيانية الموضحة
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📍 التوزيع حسب المسمى الوظيفي")
                pos_chart = px.bar(filtered_df['Main Position'].value_counts().reset_index(), 
                                   x='Main Position', y='index', orientation='h', 
                                   text_auto=True, color='index', color_discrete_sequence=px.colors.qualitative.Set3)
                pos_chart.update_layout(showlegend=False, yaxis_title=None, xaxis_title="العدد")
                st.plotly_chart(pos_chart, use_container_width=True)

            with col2:
                st.subheader("📈 مستويات المهارة")
                skill_chart = px.pie(filtered_df, names='Skill Level', hole=0.5, 
                                     color_discrete_sequence=px.colors.sequential.RdBu)
                st.plotly_chart(skill_chart, use_container_width=True)

            st.divider()
            
            # جدول تفصيلي دقيق للأرقام
            st.subheader("📑 جدول إحصائي ملخص")
            summary_table = filtered_df.groupby(['Main Position', 'EmpGender']).size().reset_index(name='العدد')
            st.table(summary_table)

        elif menu == "🔍 البحث التفصيلي":
            st.header("🔍 محرك البحث (البيانات المفلترة)")
            st.info(f"أنت تبحث الآن ضمن {len(filtered_df)} سجل بناءً على خيارات الفلترة.")
            q = st.text_input("ابحث بالاسم أو الرقم الفردي...")
            if q:
                search_res = filtered_df[filtered_df.astype(str).apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)]
                st.dataframe(search_res, use_container_width=True)
            else:
                st.dataframe(filtered_df, use_container_width=True)

        elif menu == "🚫 القائمة السوداء":
            st.header("🚫 سجل المحظورين والمستقيلين")
            # الاعتماد على العمود الجديد "حالة الموظف"
            bl_df = df[df['حالة الموظف'].isin(['Blacklist', 'مستقيل'])]
            st.error(f"يوجد حالياً {len(bl_df)} سجل تحت حالة (محظور/مستقيل)")
            st.dataframe(bl_df.style.set_properties(**{'background-color': '#fff1f1', 'color': '#990000'}), use_container_width=True)

        # زر الخروج والتحديث في الأسفل
        st.sidebar.divider()
        if st.sidebar.button("🔄 تحديث البيانات"):
            st.cache_data.clear()
            st.rerun()
        if st.sidebar.button("🚪 خروج"):
            del st.session_state["password_correct"]
            st.rerun()
