import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# --- 1. إعدادات التصميم (التباين العالي) ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #0f172a !important;
        border: 2px solid #1e293b !important;
        padding: 20px !important;
        border-radius: 15px !important;
    }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. نظام الدخول ---
if "password_correct" not in st.session_state:
    st.title("🔐 بوابة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ البيانات خاطئة")
    st.stop()

# --- 3. جلب البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except: return None

df = load_data()

if df is not None:
    # --- 4. القائمة الجانبية والفلاتر ---
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة:", ["🔍 البحث التاريخي", "📊 الإحصائيات المرنة", "🚫 Blacklist"])
    
    # استخراج الخيارات للفلاتر
    all_genders = sorted(df['EmpGender'].unique().tolist()) if 'EmpGender' in df.columns else []
    all_positions = sorted(df['Main Position'].unique().tolist()) if 'Main Position' in df.columns else []
    all_skills = sorted(df['Skill Level'].unique().tolist()) if 'Skill Level' in df.columns else []
    # إضافة خيارات المشاريع
    all_projects = sorted(df['Project'].unique().tolist()) if 'Project' in df.columns else []

    if menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 البحث الشامل والسجل التاريخي")
        q = st.text_input("ابحث بـ (Name, Case Number, Individual Number, الرقم الأمني, رقم الهاتف)")
        
        if q:
            # تحديد أعمدة البحث
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                # الاعتماد على Individual Number لجلب كل السجلات التاريخية
                main_id = results.iloc[0].get('Individual Number', '')
                # تصفية الجدول الأصلي لجلب كل عقود هذا الشخص
                full_history = df[df['Individual Number'] == main_id].copy()
                
                # تحويل التواريخ لتنسيق واضح (إذا كانت متوفرة)
                date_cols = ['Start Date', 'End Date']
                for col in date_cols:
                    if col in full_history.columns:
                        full_history[col] = pd.to_view(full_history[col]).fillna('غير محدد')

                st.subheader(f"👤 ملف الموظف: {results.iloc[0].get('Name', 'N/A')}")
                
                # بطاقات تفصيلية
                c1, c2, c3 = st.columns(3)
                num_contracts = len(full_history)
                c1.metric("إجمالي مرات التوظيف", f"{num_contracts} مرات")
                c2.metric("أول تاريخ تعاقد", full_history.sort_values('Year').iloc[0].get('Start Date', 'N/A'))
                c3.metric("آخر تاريخ تعاقد", full_history.sort_values('Year').iloc[-1].get('Start Date', 'N/A'))

                st.divider()
                
                # عرض التواريخ والمسميات في جدول مخصص
                st.write("📅 **تفاصيل التوظيف التاريخية (بالتواريخ):**")
                
                # اختيار أعمدة محددة للعرض لتركيز الانتباه
                display_cols = ['Year', 'Project', 'Main Position', 'Start Date', 'End Date', 'حالة الموظف']
                actual_display = [c for c in display_cols if c in full_history.columns]
                
                # عرض الجدول مرتباً من الأحدث للقديم
                st.table(full_history[actual_display].sort_values(by='Year', ascending=False))
                
                with st.expander("🔍 عرض كافة بيانات السجل (Dataframe)"):
                    st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لم يتم العثور على موظف بهذه البيانات.")
    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة (فلترة مرنة)")
        
        st.sidebar.divider()
        st.sidebar.subheader("🎯 تخصيص العرض")
        
        # إضافة فلتر المشروع الجديد
        sel_proj = st.sidebar.multiselect("المشروع (Project):", all_projects, default=all_projects)
        sel_gen = st.sidebar.multiselect("الجنس:", all_genders, default=all_genders)
        sel_skill = st.sidebar.multiselect("مستوى المهارة:", all_skills, default=all_skills)
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", all_positions, default=all_positions[:5] if len(all_positions)>5 else all_positions)

        # تطبيق الفلترة المرنة شاملة المشروع
        f_df = df[(df['Project'].isin(sel_proj)) & 
                  (df['EmpGender'].isin(sel_gen)) & 
                  (df['Skill Level'].isin(sel_skill)) & 
                  (df['Main Position'].isin(sel_pos))]

        if not f_df.empty:
            # البطاقات بتنسيق الوضوح العالي
            c1, c2, c3, c4 = st.columns(4)
            total = len(f_df)
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            
            c1.metric("إجمالي الفئة المختارة", total)
            c2.metric("الذكور 👨", males)
            c3.metric("الإناث 👩", females)
            c4.metric("نسبة الإناث", f"{(females/total*100 if total>0 else 0):.1f}%")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📍 التوزيع حسب المسمى")
                pos_counts = f_df['Main Position'].value_counts().reset_index()
                pos_counts.columns = ['المسمى', 'العدد']
                fig1 = px.bar(pos_counts.head(10), x='العدد', y='المسمى', orientation='h', color='العدد', color_continuous_scale='Blues')
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.subheader("🏗️ التوزيع حسب المشروع")
                proj_counts = f_df['Project'].value_counts().reset_index()
                proj_counts.columns = ['المشروع', 'العدد']
                fig2 = px.pie(proj_counts, names='المشروع', values='العدد', hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("⚠️ الرجاء اختيار الخيارات من القائمة الجانبية لعرض النتائج.")

    elif menu == "🚫 Blacklist":
        st.header("🚫 سجل المحظورين")
        bl_df = df[df['حالة الموظف'].str.contains('Blacklist', case=False, na=False)]
        if not bl_df.empty:
            st.error(f"يوجد {len(bl_df)} سجل محظور.")
            st.dataframe(bl_df, use_container_width=True)
        else: st.success("✅ القائمة نظيفة.")

    # أزرار النظام
    st.sidebar.divider()
    if st.sidebar.button("🔄 تحديث البيانات"):
        st.cache_data.clear()
        st.rerun()

