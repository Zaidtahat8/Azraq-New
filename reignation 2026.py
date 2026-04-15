import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime
import os
import csv

# ملاحظة: لعمل التصدير بشكل صحيح، تأكد من إضافة المكتبات التالية لملف requirements.txt:
# streamlit, pandas, requests, plotly, fpdf2, openpyxl, kaleido

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    .stButton>button { width: 100%; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# --- نظام تسجيل الدخول (Logging) ---
# ============================================================

LOG_FILE = "login_logs.csv"

def log_login(username: str):
    now = datetime.datetime.now()
    log_entry = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "username": username,
    }
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "time", "username"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)

def load_logs() -> pd.DataFrame:
    if os.path.isfile(LOG_FILE):
        return pd.read_csv(LOG_FILE, encoding="utf-8")
    return pd.DataFrame(columns=["date", "time", "username"])

# ============================================================

# --- دالة توليد تقرير PDF ---
def create_pdf_report(dataframe, total, males, females, ratio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    pdf.cell(200, 10, txt="HR Workforce Report - 2026", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(190, 10, txt="Statistical Summary", ln=True, fill=True)
    pdf.cell(95, 10, txt=f"Total Filtered: {total}", border=1)
    pdf.cell(95, 10, txt=f"Female Ratio: {ratio}", border=1, ln=True)
    pdf.cell(95, 10, txt=f"Males: {males}", border=1)
    pdf.cell(95, 10, txt=f"Females: {females}", border=1, ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="Visual Analytics - Project Distribution", ln=True)
    pdf.ln(5)

    try:
        if 'Project' in dataframe.columns:
            fig_pdf = px.pie(dataframe, names='Project', title="Project Distribution")
            fig_pdf.update_layout(template="plotly_white", paper_bgcolor='white', plot_bgcolor='white', font=dict(color="black"))
            img_path = "temp_pie_chart.png"
            fig_pdf.write_image(img_path, scale=2)
            pdf.image(img_path, x=20, y=None, w=150)
            if os.path.exists(img_path):
                os.remove(img_path)
    except Exception as e:
        pdf.set_font("Arial", size=10)
        pdf.cell(190, 10, txt=f"Note: Visualization could not be added. Error: {str(e)}", ln=True)

    output = pdf.output(dest='S')
    return bytes(output) if isinstance(output, (bytes, bytearray)) else output.encode('latin-1', errors='replace')

# --- 2. نظام الدخول ---
if "password_correct" not in st.session_state:
    st.title("بوابة ادارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u
            log_login(u)
            st.rerun()
        else:
            st.error("بيانات الدخول خاطئة")
    st.stop()

# --- 3. جلب البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL, timeout=30)
        data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace('nan', '')
        return data
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

df = load_data()

# --- 4. إدارة الواجهة والقوائم ---
if df is not None:
    try:
        st.sidebar.image("bdc_logo.png", width=150)
    except:
        st.sidebar.markdown("### BDC | HR System")

    current_user = st.session_state.get("current_user", "مجهول")
    st.sidebar.success(f"مرحباً، **{current_user}**")
    
    if st.sidebar.button("🔄 تحديث قاعدة البيانات"):
        st.cache_data.clear()
        st.rerun()

    menu = st.sidebar.radio("القائمة الرئيسية", [
        "البحث العام",
        "محرك البحث التاريخي",
        "الاحصائيات المرنة",
        "القائمة السوداء",
        "سجل الدخولات",
    ])

    st.sidebar.divider()
    if st.sidebar.button("🚪 تسجيل الخروج"):
        del st.session_state["password_correct"]
        st.rerun()

    # --- الإحصائيات المرنة ---
    if menu == "الاحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        st.sidebar.subheader("فلاتر التقرير")

        base_df = df.copy()

        if 'Main Position' in base_df.columns:
            sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(base_df['Main Position'].unique()))
            if sel_pos:
                base_df = base_df[base_df['Main Position'].isin(sel_pos)]

        if 'Project' in base_df.columns:
            sel_proj = st.sidebar.multiselect("المشروع:", sorted(base_df['Project'].unique()))
            if sel_proj:
                base_df = base_df[base_df['Project'].isin(sel_proj)]

        # ✅ الإضافة الجديدة: فلتر الجنس
        if 'EmpGender' in base_df.columns:
            sel_gender = st.sidebar.multiselect("الجنس:", ["Male", "Female"])
            if sel_gender:
                base_df = base_df[base_df['EmpGender'].isin(sel_gender)]

        f_df = base_df.copy()
        total_filtered = len(f_df)

        if not f_df.empty:
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            ratio_text = f"{(females/total_filtered*100 if total_filtered > 0 else 0):.1f}%"

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("إجمالي", total_filtered)
            c2.metric("ذكور", males)
            c3.metric("اناث", females)
            c4.metric("نسبة الإناث", ratio_text)

            st.divider()

            if st.button("📥 إنشاء تقرير PDF"):
                pdf_bytes = create_pdf_report(f_df, total_filtered, males, females, ratio_text)
                st.download_button(label="تحميل الملف", data=pdf_bytes, file_name="HR_Report.pdf", mime="application/pdf")

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if 'Main Position' in f_df.columns:
                    fig1 = px.bar(f_df['Main Position'].value_counts().head(10), orientation='h', title="أعلى المسميات")
                    st.plotly_chart(fig1, use_container_width=True)

            with col2:
                if 'Project' in f_df.columns:
                    fig2 = px.pie(f_df, names='Project', title="توزيع المشاريع")
                    st.plotly_chart(fig2, use_container_width=True)

        else:
            st.warning("⚠️ لا توجد نتائج حسب الفلاتر")
