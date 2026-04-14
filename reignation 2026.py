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
    </style>
""", unsafe_allow_html=True)


# ============================================================
# --- [إضافة جديدة] نظام تسجيل الدخول (Logging) ---
# ============================================================

LOG_FILE = "login_logs.csv"

def log_login(username: str):
    """
    تسجل كل عملية دخول ناجحة في ملف CSV.
    الأعمدة: التاريخ، الوقت، اسم المستخدم
    """
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
    """تحميل ملف السجل وإعادته كـ DataFrame."""
    if os.path.isfile(LOG_FILE):
        return pd.read_csv(LOG_FILE, encoding="utf-8")
    return pd.DataFrame(columns=["date", "time", "username"])

# ============================================================


# --- دالة توليد تقرير PDF (حل مشكلة Unicode) ---
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
            fig_pdf.update_layout(
                template="plotly_white",
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(color="black")
            )
            img_path = "temp_pie_chart.png"
            fig_pdf.write_image(img_path, scale=2)
            pdf.image(img_path, x=20, y=None, w=150)
            if os.path.exists(img_path):
                os.remove(img_path)
    except Exception as e:
        pdf.set_font("Arial", size=10)
        pdf.cell(190, 10, txt=f"Note: Colors could not be rendered perfectly. Error: {str(e)}", ln=True)

    output = pdf.output(dest='S')
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    else:
        return output.encode('latin-1', errors='replace')


# --- 2. نظام الدخول ---
if "password_correct" not in st.session_state:
    st.title("بوابة ادارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u   # [إضافة] حفظ اسم المستخدم في الجلسة
            log_login(u)                            # [إضافة] تسجيل الدخول فور النجاح
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
    except Exception:
        st.sidebar.markdown("**BDC | HR System**")

    # [إضافة] عرض اسم المستخدم الحالي في الـ Sidebar
    current_user = st.session_state.get("current_user", "مجهول")
    st.sidebar.caption(f"مرحباً، **{current_user}**")

    menu = st.sidebar.radio("القائمة الرئيسية", [
        "البحث العام",
        "محرك البحث التاريخي",
        "الاحصائيات المرنة",
        "القائمة السوداء",
        "سجل الدخولات",          # [إضافة] قسم جديد
    ])

    # --- قسم البحث العام ---
    if menu == "البحث العام":
        st.header("محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        if q:
            search_cols = ['Name', 'Individual Number', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]
            if not results.empty:
                st.success(f"تم العثور على {len(results)} سجل.")
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("لا توجد نتائج.")

    # --- قسم البحث التاريخي ---
    elif menu == "محرك البحث التاريخي":
        st.header("السجل الوظيفي والخط الزمني")
        q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، الهاتف، أو الرقم الأمني)")
        if q_hist:
            search_cols_hist = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_hist = [c for c in search_cols_hist if c in df.columns]
            mask_hist = df[available_hist].apply(lambda x: x.str.contains(q_hist, case=False, na=False)).any(axis=1)
            results_hist = df[mask_hist]

            if not results_hist.empty:
                main_id = results_hist.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                st.subheader(f"ملف الموظف: {results_hist.iloc[0].get('Name', 'N/A')}")
                c1, c2 = st.columns(2)
                c1.metric("إجمالي مرات التوظيف", f"{len(full_history)} عقود")
                c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A'))
                st.write("**بيانات الاكسل الكاملة:**")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("لا توجد نتائج.")

    # --- الإحصائيات المرنة ---
    elif menu == "الاحصائيات المرنة":
        st.header("تحليل القوى العاملة (فلترة ذكية متقدمة)")
        st.sidebar.divider()
        st.sidebar.subheader("فلاتر متقدمة")

        base_df = df.copy()

        if 'Main Position' in base_df.columns:
            sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(base_df['Main Position'].unique()))
            if sel_pos: base_df = base_df[base_df['Main Position'].isin(sel_pos)]

        if 'Project' in base_df.columns:
            sel_proj = st.sidebar.multiselect("المشروع:", sorted(base_df['Project'].unique()))
            if sel_proj: base_df = base_df[base_df['Project'].isin(sel_proj)]

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

            if st.button("انشاء تقرير PDF"):
                with st.spinner("جاري إنشاء التقرير..."):
                    pdf_bytes = create_pdf_report(f_df, total_filtered, males, females, ratio_text)
                    st.session_state["pdf_bytes"] = pdf_bytes

            if "pdf_bytes" in st.session_state:
                st.download_button(
                    label="تحميل الملف",
                    data=st.session_state["pdf_bytes"],
                    file_name="HR_Report.pdf",
                    mime="application/pdf"
                )

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
            st.warning("لا توجد نتائج حسب الفلاتر")

    # --- قسم القائمة السوداء ---
    elif menu == "القائمة السوداء":
        st.header("إدارة وسجل الحالات المحظورة")
        search_query = st.text_input("ابحث في القائمة السوداء (الاسم، الرقم الفردي، الرقم الأمني، أو الهاتف)")

        if 'حالة الموظف' in df.columns:
            bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)].copy()

            if search_query:
                search_cols = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
                available_search_cols = [col for col in search_cols if col in bl_df.columns]
                mask = bl_df[available_search_cols].apply(
                    lambda x: x.str.contains(search_query, case=False, na=False)
                ).any(axis=1)
                bl_df = bl_df[mask]

            if not bl_df.empty:
                st.warning(f"تم العثور على {len(bl_df)} حالة محظورة.")
                st.dataframe(bl_df, use_container_width=True)
            else:
                if search_query:
                    st.info("لا توجد نتائج تطابق بحثك في القائمة السوداء.")
                else:
                    st.success("لا توجد حالات محظورة مسجلة حالياً.")
        else:
            st.error("عمود 'حالة الموظف' غير موجود في قاعدة البيانات.")


    # ============================================================
    # --- [إضافة جديدة] قسم سجل الدخولات ---
    # ============================================================
    elif menu == "سجل الدخولات":
        st.header("سجل الدخولات - من دخل ومتى")

        logs_df = load_logs()

        if logs_df.empty:
            st.info("لا توجد سجلات دخول حتى الآن.")
        else:
            # --- إحصائيات سريعة ---
            total_logins   = len(logs_df)
            unique_users   = logs_df["username"].nunique()
            last_login_row = logs_df.iloc[-1]
            last_login_str = f"{last_login_row['date']}  {last_login_row['time']}"

            m1, m2, m3 = st.columns(3)
            m1.metric("إجمالي عمليات الدخول", total_logins)
            m2.metric("عدد المستخدمين الفريدين", unique_users)
            m3.metric("آخر دخول", last_login_str)

            st.divider()

            # --- فلتر بالتاريخ ---
            st.subheader("تصفية السجل")
            col_f1, col_f2 = st.columns(2)

            with col_f1:
                filter_user = st.text_input("بحث باسم المستخدم")
            with col_f2:
                unique_dates = sorted(logs_df["date"].unique(), reverse=True)
                filter_date = st.selectbox("تصفية بالتاريخ", options=["الكل"] + list(unique_dates))

            filtered_logs = logs_df.copy()

            if filter_user:
                filtered_logs = filtered_logs[
                    filtered_logs["username"].str.contains(filter_user, case=False, na=False)
                ]
            if filter_date != "الكل":
                filtered_logs = filtered_logs[filtered_logs["date"] == filter_date]

            # عرض الجدول مع ترتيب من الأحدث للأقدم
            st.dataframe(
                filtered_logs.sort_values(["date", "time"], ascending=False).reset_index(drop=True),
                use_container_width=True,
                column_config={
                    "date":     st.column_config.TextColumn("التاريخ"),
                    "time":     st.column_config.TextColumn("الوقت"),
                    "username": st.column_config.TextColumn("اسم المستخدم"),
                }
            )

            st.divider()

            # --- رسم بياني: عدد الدخولات لكل يوم ---
            if len(logs_df) >= 2:
                daily_counts = logs_df.groupby("date").size().reset_index(name="count")
                fig_log = px.bar(
                    daily_counts,
                    x="date",
                    y="count",
                    title="عدد الدخولات يومياً",
                    labels={"date": "التاريخ", "count": "عدد الدخولات"},
                )
                st.plotly_chart(fig_log, use_container_width=True)

            # --- تصدير السجل كـ CSV ---
            st.divider()
            csv_data = logs_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="تحميل السجل الكامل (CSV)",
                data=csv_data,
                file_name="login_logs.csv",
                mime="text/csv",
            )
    # ============================================================
