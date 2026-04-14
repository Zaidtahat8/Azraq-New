import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime
import os

st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

# --- دالة PDF ---
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

    return pdf.output(dest='S').encode('latin-1', errors='replace')


# --- Login ---
if "password_correct" not in st.session_state:
    st.title("🔐 تسجيل الدخول")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ خطأ")

    st.stop()


# --- Load Data ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL, timeout=10)
        data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        data = data.fillna('')
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip()
        return data
    except:
        st.error("خطأ في تحميل البيانات")
        return None


df = load_data()

# --- UI ---
if df is not None:

    menu = st.sidebar.radio("القائمة", [
        "🔍 البحث العام",
        "🔍 البحث التاريخي",
        "📊 الإحصائيات",
        "🚫 القائمة السوداء"
    ])

    # =========================
    # 🔍 البحث العام
    # =========================
    if menu == "🔍 البحث العام":
        st.header("🔍 البحث")

        q = st.text_input("بحث")
        if q:
            q = q.strip()
            cols = ['Name', 'Individual Number', 'رقم الهاتف']
            cols = [c for c in cols if c in df.columns]

            mask = df[cols].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            res = df[mask]

            st.dataframe(res)

    # =========================
    # 🔍 البحث التاريخي
    # =========================
    elif menu == "🔍 البحث التاريخي":
        st.header("🔍 السجل الوظيفي")

        q = st.text_input("بحث تاريخي")

        if q:
            q = q.strip()

            cols = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            cols = [c for c in cols if c in df.columns]

            mask = df[cols].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                main_id = results.iloc[0].get('Individual Number', '')

                if 'Individual Number' in df.columns:
                    history = df[df['Individual Number'] == main_id]
                else:
                    st.error("العمود غير موجود")
                    st.stop()

                st.dataframe(history)
            else:
                st.warning("لا نتائج")

    # =========================
    # 📊 الإحصائيات
    # =========================
    elif menu == "📊 الإحصائيات":
        st.header("📊 التحليل")

        total = len(df)
        males = len(df[df['EmpGender'] == 'Male'])
        females = len(df[df['EmpGender'] == 'Female'])

        ratio = f"{(females/total*100 if total else 0):.1f}%"

        st.metric("Total", total)
        st.metric("Males", males)
        st.metric("Females", females)
        st.metric("Ratio", ratio)

        if st.button("PDF"):
            pdf = create_pdf_report(df, total, males, females, ratio)
            st.download_button("Download", pdf, "report.pdf")

    # =========================
    # 🚫 القائمة السوداء
    # =========================
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 Blacklist")

        if 'حالة الموظف' in df.columns:
            bl = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)]
            st.dataframe(bl)
        else:
            st.error("العمود غير موجود")
