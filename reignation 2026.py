import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime
import os
import csv
import hashlib

# ---------------- إعدادات الصفحة ----------------
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    .stButton>button { width: 100%; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# ---------------- متغيرات عامة ----------------
LOG_FILE = "login_logs.csv"
DATA_URL = "ضع هنا رابط التحميل المباشر الصحيح"  # ضع رابط التحميل المباشر (xlsx أو csv)
REQUIRED_COLS = ["Name", "Individual Number", "EmpGender"]

# ---------------- دوال مساعدة ----------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

# مثال: قاعدة مستخدمين بسيطة (يمكن استبدالها بقاعدة حقيقية لاحقًا)
USERS = {
    "zaid": hash_password("11111")
}

def check_password(username: str, password: str) -> bool:
    return USERS.get(username) == hash_password(password)

def log_login(username: str):
    now = datetime.datetime.now()
    entry = {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S"), "username": username}
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "time", "username"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(entry)

def load_logs() -> pd.DataFrame:
    if os.path.isfile(LOG_FILE):
        return pd.read_csv(LOG_FILE, encoding="utf-8")
    return pd.DataFrame(columns=["date", "time", "username"])

# ---------------- توليد تقرير PDF محسّن ----------------
def create_pdf_report(df: pd.DataFrame, total: int, males: int, females: int, ratio: str, logo_path: str = None):
    pdf = FPDF()
    pdf.add_page()
    # شعار إن وجد
    if logo_path and os.path.exists(logo_path):
        pdf.image(logo_path, x=10, y=8, w=25)
        pdf.set_xy(40, 10)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "HR Workforce Report - 2026", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(6)

    # ملخص إحصائي
    pdf.set_fill_color(230, 230, 250)
    pdf.cell(0, 8, "Statistical Summary", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", size=10)
    pdf.cell(95, 8, f"Total Filtered: {total}", border=1)
    pdf.cell(95, 8, f"Female Ratio: {ratio}", border=1, ln=True)
    pdf.cell(95, 8, f"Males: {males}", border=1)
    pdf.cell(95, 8, f"Females: {females}", border=1, ln=True)
    pdf.ln(6)

    # جدول ملخص أول 10 صفوف (إن وجدت)
    try:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, "Sample Records (up to 10)", ln=True)
        pdf.set_font("Arial", size=9)
        sample = df.head(10)
        cols = list(sample.columns[:6])  # نعرض حتى 6 أعمدة في التقرير لتجنب التكدس
        col_width = 190 / len(cols)
        # رؤوس الأعمدة
        for c in cols:
            pdf.cell(col_width, 6, str(c)[:15], border=1)
        pdf.ln()
        # بيانات
        for _, row in sample.iterrows():
            for c in cols:
                text = str(row.get(c, ""))[:15]
                pdf.cell(col_width, 6, text, border=1)
            pdf.ln()
    except Exception:
        pass

    output = pdf.output(dest='S')
    return bytes(output) if isinstance(output, (bytes, bytearray)) else output.encode('latin-1', errors='replace')

# ---------------- تحميل البيانات مع تحقق من النوع والأعمدة ----------------
@st.cache_data(ttl=300, show_spinner="⏳ جاري تحميل البيانات...")
def load_data(url: str):
    try:
        res = requests.get(url, timeout=30)
        content_type = res.headers.get("Content-Type", "").lower()
        # تحديد نوع الملف بناءً على الهيدر أو امتداد الرابط
        if "excel" in content_type or url.lower().endswith(".xlsx") or url.lower().endswith(".xls"):
            df = pd.read_excel(BytesIO(res.content), engine="openpyxl")
        elif "csv" in content_type or url.lower().endswith(".csv") or "text/csv" in content_type:
            df = pd.read_csv(BytesIO(res.content), encoding="utf-8")
        else:
            # محاولة قراءة كـ excel أولاً ثم csv كنسخة احتياطية
            try:
                df = pd.read_excel(BytesIO(res.content), engine="openpyxl")
            except Exception:
                try:
                    df = pd.read_csv(BytesIO(res.content), encoding="utf-8")
                except Exception as e:
                    raise ValueError("الملف المحمّل ليس Excel أو CSV صالح.") from e

        # تنظيف القيم وتحويلها إلى نصوص مقطوعة
        df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
        # التحقق من الأعمدة المطلوبة
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"الأعمدة التالية مفقودة: {missing}")
        # إنشاء عمود بحث مُجمّع لتحسين الأداء في عمليات البحث المتكررة
        search_cols = [c for c in df.columns if df[c].dtype == object]
        if search_cols:
            df["_search_str"] = df[search_cols].agg(" ".join, axis=1).str.lower()
        else:
            df["_search_str"] = ""
        return df
    except Exception as e:
        # نعيد الخطأ كنص لعرضه في الواجهة
        return {"__error__": str(e)}

# ---------------- واجهة تسجيل الدخول ----------------
if "password_correct" not in st.session_state:
    st.title("🔐 بوابة إدارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if check_password(u, p):
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u
            log_login(u)
            st.experimental_rerun()
        else:
            st.error("بيانات الدخول خاطئة")
    st.stop()

# ---------------- جلب البيانات ----------------
data_loaded = load_data(DATA_URL)
if isinstance(data_loaded, dict) and "__error__" in data_loaded:
    st.error(f"خطأ في تحميل البيانات: {data_loaded['__error__']}")
    st.stop()
df = data_loaded

# ---------------- الشريط الجانبي والخيارات العامة ----------------
try:
    st.sidebar.image("bdc_logo.png", width=150)
except Exception:
    st.sidebar.markdown("### BDC | HR System")

current_user = st.session_state.get("current_user", "مجهول")
st.sidebar.success(f"مرحباً، **{current_user}**")

if st.sidebar.button("🔄 تحديث قاعدة البيانات"):
    st.cache_data.clear()
    st.experimental_rerun()

menu = st.sidebar.radio("📂 القائمة الرئيسية", [
    "🔍 البحث العام",
    "📜 محرك البحث التاريخي",
    "📊 الاحصائيات المرنة",
    "🚫 القائمة السوداء",
    "🔑 سجل الدخولات"
])

st.sidebar.divider()
if st.sidebar.button("🚪 تسجيل الخروج"):
    del st.session_state["password_correct"]
    st.experimental_rerun()

# ---------------- البحث العام (سريع باستخدام عمود البحث المجمّع) ----------------
if menu == "🔍 البحث العام":
    st.header("🔍 محرك البحث عن المتطوعين")
    q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
    if q:
        q_norm = q.strip().lower()
        mask = df["_search_str"].str.contains(q_norm, na=False)
        results = df[mask].drop(columns=["_search_str"], errors="ignore")
        if not results.empty:
            st.dataframe(results, use_container_width=True)
        else:
            st.warning("لا توجد نتائج مطابقة.")

# ---------------- محرك البحث التاريخي ----------------
elif menu == "📜 محرك البحث التاريخي":
    st.header("🔍 السجل الوظيفي والخط الزمني")
    q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، الهاتف، أو الرقم الأمني)")
    if q_hist:
        qh = q_hist.strip().lower()
        mask = df["_search_str"].str.contains(qh, na=False)
        results_hist = df[mask]
        if not results_hist.empty:
            # نأخذ الرقم الفردي لأول نتيجة للبحث عن التاريخ الكامل
            main_id = results_hist.iloc[0].get("Individual Number", "")
            full_history = df[df["Individual Number"] == main_id].drop(columns=["_search_str"], errors="ignore").copy()
            st.subheader(f"👤 ملف الموظف: {results_hist.iloc[0].get('Name', 'N/A')}")
            c1, c2 = st.columns(2)
            c1.metric("إجمالي مرات التوظيف", f"{len(full_history)} عقود")
            c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A') if not full_history.empty else "N/A")
            st.write("📂 **بيانات الإكسل الكاملة:**")
            st.dataframe(full_history, use_container_width=True)
        else:
            st.warning("⚠️ لا توجد نتائج.")

# ---------------- الإحصائيات المرنة (Tabs + تحسينات) ----------------
elif menu == "📊 الاحصائيات المرنة":
    st.header("📊 تحليل القوى العاملة")
    st.sidebar.subheader("⚙️ فلاتر التقرير")
    base_df = df.drop(columns=["_search_str"], errors="ignore").copy()

    # فلاتر
    if 'Main Position' in base_df.columns:
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(base_df['Main Position'].dropna().unique()))
        if sel_pos:
            base_df = base_df[base_df['Main Position'].isin(sel_pos)]

    if 'Project' in base_df.columns:
        sel_proj = st.sidebar.multiselect("المشروع:", sorted(base_df['Project'].dropna().unique()))
        if sel_proj:
            base_df = base_df[base_df['Project'].isin(sel_proj)]

    if 'EmpGender' in base_df.columns:
        base_df['EmpGender'] = base_df['EmpGender'].astype(str).str.strip().str.capitalize()
        sel_gender = st.sidebar.multiselect("الجنس:", sorted(base_df['EmpGender'].dropna().unique()))
        if sel_gender:
            base_df = base_df[base_df['EmpGender'].isin(sel_gender)]

    total_filtered = len(base_df)
    if total_filtered == 0:
        st.warning("⚠️ لا توجد نتائج مطابقة.")
    else:
        males = int((base_df['EmpGender'] == 'Male').sum()) if 'EmpGender' in base_df.columns else 0
        females = int((base_df['EmpGender'] == 'Female').sum()) if 'EmpGender' in base_df.columns else 0
        ratio_text = f"{(females/total_filtered*100):.1f}%" if total_filtered > 0 else "0%"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي الموظفين", total_filtered)
        c2.metric("ذكور 👨", males)
        c3.metric("إناث 👩", females)
        c4.metric("نسبة الإناث", ratio_text)

        st.divider()
        # زر إنشاء تقرير PDF
        if st.button("📥 إنشاء تقرير PDF"):
            pdf_bytes = create_pdf_report(base_df, total_filtered, males, females, ratio_text, logo_path="bdc_logo.png")
            st.download_button("تحميل ملف PDF", pdf_bytes, "HR_Report.pdf", "application/pdf")

        # تبويبات للرسوم
        tabs = st.tabs(["📊 المسميات الوظيفية", "📈 المشاريع", "📋 جدول البيانات"])
        with tabs[0]:
            if 'Main Position' in base_df.columns:
                counts = base_df['Main Position'].value_counts().head(10).reset_index()
                counts.columns = ['Position', 'Count']
                fig = px.bar(counts, x='Count', y='Position', orientation='h', title="أعلى 10 مسميات", color='Count', color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("لا توجد بيانات للمسميات الوظيفية.")
        with tabs[1]:
            if 'Project' in base_df.columns:
                fig2 = px.pie(base_df, names='Project', title="توزيع الموظفين حسب المشروع", hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("لا توجد بيانات للمشاريع.")
        with tabs[2]:
            st.dataframe(base_df, use_container_width=True)

# ---------------- القائمة السوداء ----------------
elif menu == "🚫 القائمة السوداء":
    st.header("🚫 إدارة الحالات المحظورة")
    search_query = st.text_input("ابحث في القائمة السوداء...")
    if 'حالة الموظف' in df.columns:
        bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)].copy()
        if search_query:
            ql = search_query.strip().lower()
            bl_df = bl_df[bl_df["_search_str"].str.contains(ql, na=False)]
        if not bl_df.empty:
            st.error(f"تنبيه: تم العثور على {len(bl_df)} حالة.")
            st.dataframe(bl_df.drop(columns=["_search_str"], errors="ignore"), use_container_width=True)
            # خيار تصدير CSV
            csv_bytes = bl_df.drop(columns=["_search_str"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
            st.download_button("تصدير القائمة السوداء (CSV)", csv_bytes, "blacklist.csv", "text/csv")
        else:
            st.success("لا توجد حالات محظورة.")
    else:
        st.info("عمود 'حالة الموظف' غير موجود في البيانات.")

# ---------------- سجل الدخولات ----------------
elif menu == "🔑 سجل الدخولات":
    st.header("🔑 سجل نشاط المستخدمين")
    logs_df = load_logs()
    if not logs_df.empty:
        st.dataframe(logs_df.sort_values(["date", "time"], ascending=False), use_container_width=True)
    else:
        st.info("لا توجد سجلات.")

# ---------------- نهاية ----------------
