import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime
import os
import csv

# --- إعدادات الصفحة ---
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
# --- تسجيل الدخول ---
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

def load_logs():
    if os.path.isfile(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    return pd.DataFrame(columns=["date", "time", "username"])

# ============================================================

# --- PDF ---
def create_pdf_report(dataframe, total, males, females, ratio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)

    pdf.cell(200, 10, txt="HR Workforce Report - 2026", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(190, 10, txt=f"Total: {total}", ln=True)
    pdf.cell(190, 10, txt=f"Males: {males}", ln=True)
    pdf.cell(190, 10, txt=f"Females: {females}", ln=True)
    pdf.cell(190, 10, txt=f"Female Ratio: {ratio}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# ============================================================

# --- Login ---
if "password_correct" not in st.session_state:
    st.title("بوابة HR")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u
            log_login(u)
            st.rerun()
        else:
            st.error("خطأ")
    st.stop()

# ============================================================

@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    res = requests.get(URL)
    df = pd.read_excel(BytesIO(res.content))
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df

df = load_data()

# ============================================================

st.sidebar.success(f"👤 {st.session_state.get('current_user')}")

menu = st.sidebar.radio("القائمة", [
    "البحث",
    "الإحصائيات"
])

# ============================================================

if menu == "البحث":
    st.header("بحث")
    q = st.text_input("بحث")
    if q:
        mask = df.apply(lambda x: x.astype(str).str.contains(q, case=False)).any(axis=1)
        st.dataframe(df[mask])

# ============================================================

elif menu == "الإحصائيات":
    st.header("📊 الإحصائيات")

    base_df = df.copy()

    # فلتر الوظيفة
    if 'Main Position' in base_df.columns:
        pos = st.sidebar.multiselect("الوظيفة", base_df['Main Position'].unique())
        if pos:
            base_df = base_df[base_df['Main Position'].isin(pos)]

    # فلتر المشروع
    if 'Project' in base_df.columns:
        proj = st.sidebar.multiselect("المشروع", base_df['Project'].unique())
        if proj:
            base_df = base_df[base_df['Project'].isin(proj)]

    # ✅ فلتر الجنس (الجديد)
    if 'EmpGender' in base_df.columns:
        gender = st.sidebar.multiselect("الجنس", ["Male", "Female"])
        if gender:
            base_df = base_df[base_df['EmpGender'].isin(gender)]

    f_df = base_df
    total = len(f_df)

    males = len(f_df[f_df['EmpGender'] == 'Male'])
    females = len(f_df[f_df['EmpGender'] == 'Female'])

    ratio = f"{(females/total*100 if total else 0):.1f}%"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("الإجمالي", total)
    c2.metric("ذكور", males)
    c3.metric("إناث", females)
    c4.metric("النسبة", ratio)

    if st.button("PDF"):
        pdf = create_pdf_report(f_df, total, males, females, ratio)
        st.download_button("تحميل", pdf, "report.pdf")

    col1, col2 = st.columns(2)

    with col1:
        if 'Main Position' in f_df.columns:
            fig = px.bar(f_df['Main Position'].value_counts())
            st.plotly_chart(fig)

    with col2:
        if 'Project' in f_df.columns:
            fig = px.pie(f_df, names='Project')
            st.plotly_chart(fig)
```
