import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime, os, csv, bcrypt

st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

# --- إعدادات CSS للواجهة ---
st.markdown("""
    <style>
    div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    .stButton>button { width: 100%; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- نظام تسجيل الدخول ---
LOG_FILE = "login_logs.csv"
USERS = {"zaid": bcrypt.hashpw("11111".encode(), bcrypt.gensalt())}

def log_login(username: str):
    now = datetime.datetime.now()
    log_entry = {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M:%S"), "username": username}
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "time", "username"])
        if not file_exists: writer.writeheader()
        writer.writerow(log_entry)

def load_logs() -> pd.DataFrame:
    return pd.read_csv(LOG_FILE, encoding="utf-8") if os.path.isfile(LOG_FILE) else pd.DataFrame(columns=["date","time","username"])

# --- تحميل البيانات مع تحقق من الأعمدة ---
REQUIRED_COLS = ["Name", "Individual Number", "EmpGender"]

@st.cache_data(ttl=300, show_spinner="جاري تحميل البيانات...")
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/...download=1"
    try:
        res = requests.get(URL, timeout=30)
        df = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
        # تحقق من الأعمدة المطلوبة
        missing = [col for col in REQUIRED_COLS if col not in df.columns]
        if missing:
            st.error(f"⚠️ الأعمدة التالية مفقودة: {missing}")
            return None
        return df
    except requests.exceptions.Timeout:
        st.error("⏳ انتهت مهلة الاتصال، حاول مرة أخرى.")
        return None
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

# --- واجهة تسجيل الدخول ---
if "password_correct" not in st.session_state:
    st.title("🔐 بوابة إدارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u in USERS and bcrypt.checkpw(p.encode(), USERS[u]):
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u
            log_login(u)
            st.rerun()
        else:
            st.error("بيانات الدخول خاطئة")
    st.stop()

# --- تحميل البيانات ---
df = load_data()
if df is not None:
    st.sidebar.image("bdc_logo.png", width=150)
    current_user = st.session_state.get("current_user", "مجهول")
    st.sidebar.success(f"مرحباً، **{current_user}**")

    menu = st.sidebar.radio("📂 القائمة الرئيسية", [
        "🔍 البحث العام", 
        "📜 محرك البحث التاريخي", 
        "📊 الاحصائيات المرنة", 
        "🚫 القائمة السوداء", 
        "🔑 سجل الدخولات"
    ])

    # --- 🔍 البحث العام (تحسين الأداء باستخدام query) ---
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        if q:
            query_str = " | ".join([f"`{col}`.str.contains(@q, case=False, na=False)" for col in df.columns if col in ["Name","Individual Number","رقم الهاتف"]])
            results = df.query(query_str) if query_str else pd.DataFrame()
            st.dataframe(results if not results.empty else pd.DataFrame(), use_container_width=True)

    # --- 📊 الإحصائيات المرنة (واجهة محسّنة باستخدام Tabs) ---
    elif menu == "📊 الاحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة")
        st.sidebar.subheader("⚙️ فلاتر التقرير")
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

        total_filtered = len(base_df)
        if total_filtered > 0:
            males = len(base_df[base_df['EmpGender'] == 'Male'])
            females = len(base_df[base_df['EmpGender'] == 'Female'])
            ratio_text = f"{(females/total_filtered*100):.1f}%"

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("إجمالي الموظفين", total_filtered)
            c2.metric("ذكور 👨", males)
            c3.metric("إناث 👩", females)
            c4.metric("نسبة الإناث", ratio_text)

            st.divider()
            tabs = st.tabs(["📊 المسميات الوظيفية", "📈 المشاريع"])
            with tabs[0]:
                if 'Main Position' in base_df.columns:
                    counts = base_df['Main Position'].value_counts().head(10).reset_index()
                    counts.columns = ['Position', 'Count']
                    st.plotly_chart(px.bar(counts, x='Count', y='Position', orientation='h', title="أعلى 10 مسميات", color='Count', color_continuous_scale='Viridis'), use_container_width=True)
            with tabs[1]:
                if 'Project' in base_df.columns:
                    st.plotly_chart(px.pie(base_df, names='Project', title="توزيع الموظفين حسب المشروع", hole=0.4), use_container_width=True)
        else:
            st.warning("⚠️ لا توجد نتائج مطابقة.")
