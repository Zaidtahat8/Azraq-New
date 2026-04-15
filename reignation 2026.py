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

# --- نظام تسجيل الدخول ---
LOG_FILE = "login_logs.csv"
def log_login(username):
    now = datetime.datetime.now()
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "time", "username"])
        if not file_exists: writer.writeheader()
        writer.writerow({"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S"), "username": username})

# --- دالة توليد PDF (تم تصحيح ترميز اللغة) ---
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
    
    try:
        fig_pdf = px.pie(dataframe, names='Project', title="Project Distribution")
        fig_pdf.update_layout(paper_bgcolor='white', plot_bgcolor='white')
        img_path = "temp_chart.png"
        fig_pdf.write_image(img_path, engine="kaleido")
        pdf.image(img_path, x=20, y=None, w=150)
        if os.path.exists(img_path): os.remove(img_path)
    except: pass

    # ملاحظة: تم استخدام latin-1 مع ignore لتجنب تعليق النظام بسبب الأسماء العربية
    return pdf.output(dest='S').encode('latin-1', errors='ignore')

# --- نظام الدخول ---
if "password_correct" not in st.session_state:
    st.title("🔐 بوابة إدارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"], st.session_state["current_user"] = True, u
            log_login(u)
            st.rerun()
        else: st.error("بيانات الدخول خاطئة")
    st.stop()

# --- جلب البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL, timeout=30)
        data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        return data.fillna('')
    except: return None

df = load_data()

if df is not None:
    st.sidebar.success(f"مرحباً، **{st.session_state.current_user}**")
    menu = st.sidebar.radio("القائمة", ["البحث العام", "الاحصائيات المرنة", "القائمة السوداء"])

    # --- 🔍 البحث العام (تم تصحيح مشكلة DeltaGenerator) ---
    if menu == "البحث العام":
        st.header("🔍 محرك البحث")
        q = st.text_input("ابحث بالاسم أو الرقم")
        if q:
            mask = df.astype(str).apply(lambda x: x.str.contains(q, case=False)).any(axis=1)
            results = df[mask]
            if not results.empty:
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("لا توجد نتائج")

    # --- 📊 الإحصائيات (تم تصحيح التصدير) ---
    elif menu == "الاحصائيات المرنة":
        st.header("📊 التحليل")
        # فلاتر... (توضع هنا فلاتر المسمى والجنس)
        f_df = df.copy() # تبسيط للمثال
        total, males, females = len(f_df), len(f_df[f_df['EmpGender']=='Male']), len(f_df[f_df['EmpGender']=='Female'])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي", total)
        c2.metric("ذكور", males)
        c3.metric("إناث", females)

        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            if st.button("📥 تقرير PDF"):
                pdf_bytes = create_pdf_report(f_df, total, males, females, f"{(females/total*100):.1f}%")
                st.download_button("تحميل PDF", pdf_bytes, "HR_Report.pdf", "application/pdf")
        
        with col_ex2:
            # إضافة تصدير Excel (حل مشكلة xlsxwriter)
            output_excel = BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                f_df.to_excel(writer, index=False, sheet_name='Sheet1')
            st.download_button("📥 تحميل Excel", output_excel.getvalue(), "HR_Data.xlsx")

    # --- 🚫 القائمة السوداء (تم تصحيح مشكلة DeltaGenerator) ---
    elif menu == "القائمة السوداء":
        st.header("🚫 الحالات المحظورة")
        if 'حالة الموظف' in df.columns:
            bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)]
            if not bl_df.empty:
                st.error(f"تم العثور على {len(bl_df)} حالة")
                st.dataframe(bl_df, use_container_width=True)
            else:
                st.success("لا توجد حالات محظورة")
