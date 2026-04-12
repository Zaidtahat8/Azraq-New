import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime
import os
import tempfile

# --- إعدادات الصفحة ---
st.set_page_config(page_title="HR System Azraq 2026", layout="wide")

st.markdown("""
<style>
div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

# --- بيانات الدخول (استخدم secrets) ---
USER = st.secrets.get("username", "admin")
PASS = st.secrets.get("password", "1234")

# --- PDF ---
def create_pdf_report(dataframe, total, males, females, ratio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)

    pdf.cell(200, 10, txt="HR Workforce Report - 2026", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)

    pdf.cell(190, 10, txt="Statistical Summary", ln=True)
    pdf.cell(95, 10, txt=f"Total: {total}", border=1)
    pdf.cell(95, 10, txt=f"Female Ratio: {ratio}", border=1, ln=True)
    pdf.cell(95, 10, txt=f"Males: {males}", border=1)
    pdf.cell(95, 10, txt=f"Females: {females}", border=1, ln=True)
    pdf.ln(10)

    try:
        if 'Project' in dataframe.columns:
            fig = px.pie(dataframe, names='Project')
            fig.update_layout(template="plotly_white")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                fig.write_image(tmp.name, scale=2)
                pdf.image(tmp.name, x=20, w=150)

    except Exception as e:
        pdf.cell(190, 10, txt=f"Chart error: {str(e)}", ln=True)

    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- تسجيل الدخول ---
if "auth" not in st.session_state:
    st.title("🔐 HR Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == USER and p == PASS:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Wrong credentials")
    st.stop()

# --- تحميل البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL, timeout=10)
        res.raise_for_status()

        df = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        df = df.astype(str).apply(lambda x: x.str.strip())
        df.replace({'nan': '', 'None': ''}, inplace=True)

        if 'EmpGender' in df.columns:
            df['EmpGender'] = df['EmpGender'].str.lower()

        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

with st.spinner("Loading data..."):
    df = load_data()

if df is None:
    st.stop()

# --- Sidebar ---
menu = st.sidebar.radio("Menu", [
    "Search",
    "History",
    "Analytics",
    "Blacklist"
])

if st.sidebar.button("Reset Filters"):
    st.rerun()

# --- SEARCH ---
if menu == "Search":
    st.header("Search Employees")
    q = st.text_input("Search...")

    if q:
        cols = [c for c in ['Name', 'Individual Number', 'رقم الهاتف'] if c in df.columns]
        q = q.lower()
        mask = df[cols].apply(lambda col: col.str.lower().str.contains(q, na=False)).any(axis=1)
        res = df[mask]

        if not res.empty:
            st.success(f"{len(res)} results")
            st.dataframe(res, use_container_width=True)
        else:
            st.warning("No results")

# --- HISTORY ---
elif menu == "History":
    st.header("Employee History")
    q = st.text_input("Search history...")

    if q:
        cols = [c for c in ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف'] if c in df.columns]
        q = q.lower()
        mask = df[cols].apply(lambda col: col.str.lower().str.contains(q, na=False)).any(axis=1)
        res = df[mask]

        if not res.empty:
            emp_id = res.iloc[0]['Individual Number']
            history = df[df['Individual Number'] == emp_id]

            st.dataframe(history, use_container_width=True)
        else:
            st.warning("No results")

# --- ANALYTICS ---
elif menu == "Analytics":
    st.header("Analytics")

    f_df = df.copy()

    if 'Main Position' in f_df.columns:
        pos = st.sidebar.multiselect("Position", sorted(f_df['Main Position'].unique()))
        if pos:
            f_df = f_df[f_df['Main Position'].isin(pos)]

    if 'Project' in f_df.columns:
        proj = st.sidebar.multiselect("Project", sorted(f_df['Project'].unique()))
        if proj:
            f_df = f_df[f_df['Project'].isin(proj)]

    total = len(f_df)

    if total > 0:
        males = len(f_df[f_df['EmpGender'].isin(['male', 'm', 'ذكر'])])
        females = len(f_df[f_df['EmpGender'].isin(['female', 'f', 'انثى'])])
        ratio = f"{(females/total*100):.1f}%"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", total)
        c2.metric("Males", males)
        c3.metric("Females", females)
        c4.metric("Female %", ratio)

        if st.button("Export PDF"):
            pdf = create_pdf_report(f_df, total, males, females, ratio)
            st.download_button("Download", pdf, "report.pdf")

        if st.button("Export Excel"):
            output = BytesIO()
            f_df.to_excel(output, index=False)
            st.download_button("Download Excel", output.getvalue(), "data.xlsx")

        col1, col2 = st.columns(2)

        with col1:
            if 'Main Position' in f_df.columns:
                fig1 = px.bar(f_df['Main Position'].value_counts().head(10).sort_values(), orientation='h')
                st.plotly_chart(fig1, use_container_width=True)

        with col2:
            if 'Project' in f_df.columns:
                fig2 = px.pie(f_df, names='Project')
                st.plotly_chart(fig2, use_container_width=True)

# --- BLACKLIST ---
elif menu == "Blacklist":
    st.header("Blacklist")

    q = st.text_input("Search blacklist...")

    if 'حالة الموظف' in df.columns:
        bl = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)]

        if q:
            cols = [c for c in ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف'] if c in bl.columns]
            q = q.lower()
            mask = bl[cols].apply(lambda col: col.str.lower().str.contains(q, na=False)).any(axis=1)
            bl = bl[mask]

        if not bl.empty:
            st.warning(f"{len(bl)} records")
            st.dataframe(bl, use_container_width=True)
        else:
            st.success("No blacklist records")
    else:
        st.error("Column not found")
