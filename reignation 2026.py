import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime
import os
import csv

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    /* خلفية عامة */
    .stApp { background-color: #0b1220; color: #e6eef8; }
    /* شريط جانبي */
    .css-1d391kg { background-color: #071028 !important; }
    /* بطاقات المقياس */
    .metric-card {
        background: linear-gradient(135deg,#071a2b 0%, #0f2a3f 100%);
        border: 1px solid rgba(255,255,255,0.06);
        padding: 14px;
        border-radius: 12px;
        color: #e6eef8;
        text-align: center;
    }
    .metric-value { font-size: 22px; font-weight: 800; color: #00f2ff; }
    .metric-label { font-size: 13px; color: #9fb6c9; margin-top:6px; }
    /* أزرار */
    .stButton>button { background: linear-gradient(90deg,#0ea5a4,#06b6d4); color: #021124; font-weight:700; border-radius:10px; padding:8px 12px; }
    /* جداول */
    .stDataFrame table { background: rgba(255,255,255,0.02); color: #e6eef8; }
    </style>
""", unsafe_allow_html=True)

# --- نظام تسجيل الدخول (Logging) ---
LOG_FILE = "login_logs.csv"

def log_login(username: str):
    now = datetime.datetime.now()
    log_entry = {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S"), "username": username}
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "time", "username"])
        if not file_exists: writer.writeheader()
        writer.writerow(log_entry)

def load_logs() -> pd.DataFrame:
    if os.path.isfile(LOG_FILE): return pd.read_csv(LOG_FILE, encoding="utf-8")
    return pd.DataFrame(columns=["date", "time", "username"])

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
    
    try:
        if 'Project' in dataframe.columns:
            fig_pdf = px.pie(dataframe, names='Project', title="Project Distribution")
            fig_pdf.update_layout(template="plotly_white", paper_bgcolor='white', plot_bgcolor='white')
            img_path = "temp_pie_chart.png"
            fig_pdf.write_image(img_path, engine="kaleido")
            pdf.image(img_path, x=20, y=None, w=150)
            if os.path.exists(img_path): os.remove(img_path)
    except:
        pass

    output = pdf.output(dest='S')
    return bytes(output) if isinstance(output, (bytes, bytearray)) else output.encode('latin-1', errors='replace')

# --- نظام الدخول ---
if "password_correct" not in st.session_state:
    st.title("🔐 بوابة إدارة الموارد البشرية")
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

# --- جلب البيانات ---
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

# --- إدارة الواجهة والقوائم ---
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

    menu = st.sidebar.radio("القائمة الرئيسية", ["🔍 البحث العام", "📜 محرك البحث التاريخي", "📊 الاحصائيات المرنة", "🚫 القائمة السوداء", "🔑 سجل الدخولات"])

    st.sidebar.divider()
    if st.sidebar.button("🚪 تسجيل الخروج"):
        del st.session_state["password_correct"]
        st.rerun()

    # --- 🔍 البحث العام ---
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        if q:
            search_cols = ['Name', 'Individual Number', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]
            if not results.empty:
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("لا توجد نتائج مطابقة.")

    # --- 📜 محرك البحث التاريخي (التعديل الجديد المطلوب) ---
    elif menu == "📜 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، الهاتف، أو الرقم الأمني)")
        if q_hist:
            search_cols_hist = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_hist = [c for c in search_cols_hist if c in df.columns]
            mask_hist = df[available_hist].apply(lambda x: x.str.contains(q_hist, case=False, na=False)).any(axis=1)
            results_hist = df[mask_hist]

            if not results_hist.empty:
                main_id = results_hist.iloc[0].get('Individual Number', '')
                full_history = df[df['Individual Number'] == main_id].copy()
                st.subheader(f"👤 ملف الموظف: {results_hist.iloc[0].get('Name', 'N/A')}")
                
                c1, c2 = st.columns(2)
                c1.metric("إجمالي مرات التوظيف", f"{len(full_history)} عقود")
                c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A'))
                
                st.write("📂 **بيانات الإكسل الكاملة:**")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # --- 📊 الإحصائيات المرنة ---
    elif menu == "📊 الاحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        st.sidebar.subheader("فلاتر التقرير")
        base_df = df.copy()

        if 'Main Position' in base_df.columns:
            sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(base_df['Main Position'].unique()))
            if sel_pos: base_df = base_df[base_df['Main Position'].isin(sel_pos)]

        if 'Project' in base_df.columns:
            sel_proj = st.sidebar.multiselect("المشروع:", sorted(base_df['Project'].unique()))
            if sel_proj: base_df = base_df[base_df['Project'].isin(sel_proj)]

        if 'EmpGender' in base_df.columns:
            base_df['EmpGender'] = base_df['EmpGender'].astype(str).str.strip().str.capitalize()
            sel_gender = st.sidebar.multiselect("الجنس:", sorted(base_df['EmpGender'].unique()))
            if sel_gender: base_df = base_df[base_df['EmpGender'].isin(sel_gender)]

        f_df = base_df.copy()
        total_filtered = len(f_df)

        if total_filtered > 0:
            males = len(f_df[f_df['EmpGender'] == 'Male'])
            females = len(f_df[f_df['EmpGender'] == 'Female'])
            ratio_text = f"{(females/total_filtered*100):.1f}%"
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("إجمالي الموظفين", total_filtered)
            c2.metric("ذكور 👨", males)
            c3.metric("إناث 👩", females)
            c4.metric("نسبة الإناث", ratio_text)

            st.divider()
            if st.button("📥 إنشاء تقرير PDF"):
                pdf_bytes = create_pdf_report(f_df, total_filtered, males, females, ratio_text)
                st.download_button("تحميل ملف PDF", pdf_bytes, "HR_Report.pdf", "application/pdf")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                if 'Main Position' in f_df.columns:
                    counts = f_df['Main Position'].value_counts().head(10).reset_index()
                    counts.columns = ['Position', 'Count']
                    st.plotly_chart(px.bar(counts, x='Count', y='Position', orientation='h', title="أعلى 10 مسميات", color='Count', color_continuous_scale='Viridis'), use_container_width=True)
            with col2:
                if 'Project' in f_df.columns:
                    st.plotly_chart(px.pie(f_df, names='Project', title="توزيع الموظفين حسب المشروع", hole=0.4), use_container_width=True)

        else:
            st.warning("⚠️ لا توجد نتائج مطابقة.")

    # --- 🚫 القائمة السوداء ---
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 إدارة الحالات المحظورة")
        search_query = st.text_input("ابحث في القائمة السوداء...")
        if 'حالة الموظف' in df.columns:
            bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)].copy()
            if search_query:
                search_cols = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
                available_search_cols = [col for col in search_cols if col in bl_df.columns]
                mask = bl_df[available_search_cols].apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                bl_df = bl_df[mask]
            
            if not bl_df.empty:
                st.error(f"تنبيه: تم العثور على {len(bl_df)} حالة.")
                st.dataframe(bl_df, use_container_width=True)
            else:
                st.success("لا توجد حالات محظورة.")

    # --- 🔑 سجل الدخولات ---
    elif menu == "🔑 سجل الدخولات":
        st.header("🔑 سجل نشاط المستخدمين")
        logs_df = load_logs()
        if not logs_df.empty:
            st.dataframe(logs_df.sort_values(["date", "time"], ascending=False), use_container_width=True)
        else:
            st.info("لا توجد سجلات.")
