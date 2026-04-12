import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
import datetime
from fpdf import FPDF
import os

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- دالة إنشاء تقرير PDF مع الرسومات ---
def generate_pdf_report(dataframe, total, males, females):
    pdf = FPDF()
    pdf.add_page()
    
    # إعداد الخط (تأكد من وجود خط يدعم العربية أو استخدم الإنجليزية للعناوين حالياً لتجنب مشاكل المكتبة)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="HR Workforce Report - Azraq 2026", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    # ملخص الأرقام
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(190, 10, txt="Statistical Summary", ln=True, fill=True)
    pdf.cell(190, 10, txt=f"Total Staff: {total}", ln=True)
    pdf.cell(190, 10, txt=f"Males: {males}", ln=True)
    pdf.cell(190, 10, txt=f"Females: {females}", ln=True)
    pdf.ln(10)

    # إضافة الرسم البياني الأول (توزيع المشاريع)
    if 'Project' in dataframe.columns:
        fig = px.pie(dataframe, names='Project', title="Project Distribution")
        fig.write_image("temp_chart1.png")
        pdf.image("temp_chart1.png", x=10, y=None, w=180)
        os.remove("temp_chart1.png")
    
    return pdf.output(dest='S').encode('latin-1')

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
        res = requests.get(URL, timeout=10)
        if res.status_code == 200:
            data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
            for col in data.columns:
                data[col] = data[col].astype(str).str.strip().replace('nan', '')
            return data
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

df = load_data()

# --- 4. إدارة الواجهة ---
if df is not None:
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية", ["🔍 البحث العام", "🔍 محرك البحث التاريخي", "📊 الإحصائيات المرنة"])

    if menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة وتصدير PDF")
        
        # الفلاتر
        base_df = df.copy()
        sel_proj = st.sidebar.multiselect("المشروع:", sorted(base_df['Project'].unique()) if 'Project' in base_df.columns else [])
        if sel_proj: base_df = base_df[base_df['Project'].isin(sel_proj)]
        
        f_df = base_df.copy()
        
        if not f_df.empty:
            total = len(f_df)
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي", total)
            c2.metric("ذكور", males)
            c3.metric("إناث", females)
            
            st.divider()
            
            # --- زر تصدير PDF الجديد ---
            st.subheader("📥 تصدير التقرير النهائي")
            try:
                pdf_data = generate_pdf_report(f_df, total, males, females)
                st.download_button(
                    label="📄 تحميل التقرير كـ PDF (مع الرسوم)",
                    data=pdf_data,
                    file_name=f"HR_Full_Report_{datetime.date.today()}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.info("💡 ملاحظة: لتفعيل تصدير الرسوم لـ PDF، تأكد من تثبيت مكتبة 'kaleido' (pip install kaleido).")

            # عرض الرسوم في الصفحة
            st.plotly_chart(px.pie(f_df, names='Project', title="توزيع المشاريع"), use_container_width=True)
        else:
            st.warning("⚠️ لا توجد نتائج.")

    # (باقي الأقسام المعتمدة سابقاً تظل كما هي)
    elif menu == "🔍 البحث العام":
        # ... كود البحث العام المعتمد ...
        pass
