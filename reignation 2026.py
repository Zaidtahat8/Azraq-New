# =============================================================
# نظام HR مخيم الأزرق 2026 - النسخة المحدّثة الشاملة
# =============================================================
# requirements.txt يجب أن يحتوي على:
#   streamlit, pandas, requests, plotly, fpdf2, openpyxl, kaleido
#
# secrets.toml (مجلد .streamlit):
#   [users]
#   zaid = {password = "11111", role = "admin"}
#   viewer1 = {password = "view123", role = "viewer"}
# =============================================================

import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import datetime
import os

# ==============================================================
# 1. إعدادات الصفحة
# ==============================================================
st.set_page_config(
    page_title="نظام HR - مخيم الأزرق 2026",
    page_icon="logo.png" if os.path.exists("logo.png") else "🏕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================
# 2. CSS مخصص
# ==============================================================
st.markdown("""
<style>
/* بطاقات الإحصاء */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0f172a, #1e293b) !important;
    border: 1px solid #334155 !important;
    border-left: 4px solid #00f2ff !important;
    padding: 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(0,242,255,0.1) !important;
}
div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; font-size: 2rem !important; }
div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-size: 0.85rem !important; }
div[data-testid="stMetricDelta"] { color: #34d399 !important; }

/* عناوين القسم */
h1, h2, h3 { color: #e2e8f0 !important; }

/* زر الخروج */
.logout-btn { color: #f87171 !important; border: 1px solid #f87171 !important; }
</style>
""", unsafe_allow_html=True)

# ==============================================================
# 3. دوال المساعدة
# ==============================================================

def get_users():
    """جلب المستخدمين من secrets أو fallback للتطوير"""
    try:
        return st.secrets["users"]
    except Exception:
        # Fallback للتطوير المحلي فقط - يُحذف في الإنتاج
        return {
            "zaid": {"password": "11111", "role": "admin"},
            "viewer": {"password": "view123", "role": "viewer"}
        }


def create_pdf_report(dataframe, total, males, females, ratio):
    """توليد تقرير PDF محسّن"""
    pdf = FPDF()
    pdf.add_page()

    # --- العنوان ---
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(0, 242, 255)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(200, 20, txt="", ln=False)  # spacer
    pdf.set_y(10)
    pdf.cell(200, 10, txt="HR Workforce Report - Azraq Camp 2026", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(200, 220, 240)
    pdf.cell(200, 10, txt=f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    pdf.ln(15)

    # --- الإحصاء ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 13)
    pdf.set_fill_color(220, 235, 255)
    pdf.cell(190, 10, txt="  Statistical Summary", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    pdf.set_fill_color(240, 248, 255)

    stats = [
        ("Total Staff (Filtered)", str(total)),
        ("Males", str(males)),
        ("Females", str(females)),
        ("Female Ratio", ratio),
        ("Report Date", str(datetime.date.today())),
    ]
    for label, val in stats:
        pdf.cell(100, 9, txt=f"  {label}", border=1, fill=True)
        pdf.cell(90, 9, txt=f"  {val}", border=1, ln=True)
    pdf.ln(8)

    # --- الرسوم البيانية ---
    charts_added = 0
    chart_configs = []

    if 'Project' in dataframe.columns and dataframe['Project'].nunique() > 0:
        chart_configs.append(
            (px.pie(dataframe, names='Project', title="Project Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set2), "Project Distribution")
        )

    if 'Main Position' in dataframe.columns:
        pos_counts = dataframe['Main Position'].value_counts().head(8).reset_index()
        pos_counts.columns = ['Position', 'Count']
        chart_configs.append(
            (px.bar(pos_counts, x='Count', y='Position', orientation='h',
                    title="Top Positions", color='Count',
                    color_continuous_scale='Blues'), "Top Positions")
        )

    if 'EmpGender' in dataframe.columns:
        gender_counts = dataframe['EmpGender'].value_counts().reset_index()
        gender_counts.columns = ['Gender', 'Count']
        chart_configs.append(
            (px.pie(gender_counts, names='Gender', values='Count',
                    title="Gender Distribution",
                    color_discrete_map={'Male': '#3b82f6', 'Female': '#ec4899'}), "Gender Distribution")
        )

    for fig, title in chart_configs:
        try:
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(230, 240, 255)
            pdf.cell(190, 9, txt=f"  {title}", ln=True, fill=True)
            pdf.ln(3)

            fig.update_layout(
                template="plotly_white",
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(color="black", size=12),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            img_path = f"temp_chart_{charts_added}.png"
            fig.write_image(img_path, scale=2, width=700, height=400)
            pdf.image(img_path, x=15, y=None, w=170)
            pdf.ln(5)

            if os.path.exists(img_path):
                os.remove(img_path)
            charts_added += 1
        except Exception as e:
            pdf.set_font("Arial", size=9)
            pdf.cell(190, 8, txt=f"Note: Chart rendering skipped. {str(e)[:60]}", ln=True)

    # --- تذييل ---
    pdf.set_y(-20)
    pdf.set_font("Arial", 'I', 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(190, 10, txt="BDC - Jordan | Azraq Camp HR System | Confidential", align='C')

    return pdf.output(dest='S').encode('latin-1', errors='replace')


def export_excel(dataframe):
    """تصدير البيانات كملف Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        dataframe.to_excel(writer, index=False, sheet_name="HR Data")
    return output.getvalue()


@st.cache_data(ttl=300, show_spinner="جاري تحميل البيانات...")
def load_data():
    """جلب البيانات من SharePoint"""
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL, timeout=30)
        res.raise_for_status()
        data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip().replace({'nan': '', 'None': ''})
        return data, None
    except requests.exceptions.Timeout:
        return None, "انتهت مهلة الاتصال بالخادم. تحقق من الإنترنت."
    except requests.exceptions.ConnectionError:
        return None, "تعذّر الاتصال. تحقق من رابط SharePoint."
    except Exception as e:
        return None, f"خطأ غير متوقع: {str(e)}"


# ==============================================================
# 4. نظام تسجيل الدخول (متعدد المستخدمين)
# ==============================================================
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None
    st.session_state["role"] = None

if not st.session_state["authenticated"]:
    col_c, col_form, col_c2 = st.columns([1, 1.2, 1])
    with col_form:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("bdc_logo.png", width=160) if os.path.exists("bdc_logo.png") else st.title("BDC - HR System")
        st.subheader("بوابة إدارة الموارد البشرية")
        st.caption("مخيم الأزرق 2026")
        st.divider()
        username = st.text_input("اسم المستخدم", placeholder="أدخل اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password", placeholder="أدخل كلمة المرور")

        if st.button("دخول", use_container_width=True, type="primary"):
            users = get_users()
            if username in users and users[username]["password"] == password:
                st.session_state["authenticated"] = True
                st.session_state["current_user"] = username
                st.session_state["role"] = users[username]["role"]
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة. حاول مجدداً.")
    st.stop()

# ==============================================================
# 5. الشريط الجانبي
# ==============================================================
with st.sidebar:
    if os.path.exists("bdc_logo.png"):
        st.image("bdc_logo.png", width=140)
    
    st.caption(f"مرحباً، **{st.session_state['current_user']}**")
    role_badge = "🛡️ مدير النظام" if st.session_state["role"] == "admin" else "👁️ مشاهد"
    st.caption(role_badge)
    st.divider()

    menu = st.radio("القائمة الرئيسية", [
        "لوحة التحكم",
        "البحث العام",
        "السجل الوظيفي",
        "الإحصائيات والتقارير",
        "القائمة السوداء"
    ])

    st.divider()

    # زر التحديث اليدوي
    if st.button("تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.success("تم تحديث البيانات!")
        st.rerun()

    # زر تسجيل الخروج
    if st.button("تسجيل الخروج", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.sidebar.caption(f"آخر تحديث: {datetime.datetime.now().strftime('%H:%M')}")

# ==============================================================
# 6. جلب البيانات
# ==============================================================
df, error_msg = load_data()

if error_msg:
    st.error(f"خطأ في تحميل البيانات: {error_msg}")
    st.info("يمكنك المحاولة مجدداً بالضغط على 'تحديث البيانات' في الشريط الجانبي.")
    st.stop()

if df is None or df.empty:
    st.warning("البيانات فارغة أو غير متاحة.")
    st.stop()

# ==============================================================
# 7. لوحة التحكم الرئيسية (Dashboard)
# ==============================================================
if menu == "لوحة التحكم":
    st.title("لوحة التحكم الرئيسية")
    st.caption(f"نظرة عامة على القوى العاملة | تاريخ اليوم: {datetime.date.today()}")
    st.divider()

    total = len(df)
    males = len(df[df.get('EmpGender', pd.Series(dtype=str)) == 'Male']) if 'EmpGender' in df.columns else 0
    females = len(df[df.get('EmpGender', pd.Series(dtype=str)) == 'Female']) if 'EmpGender' in df.columns else 0
    blacklist_count = 0
    if 'حالة الموظف' in df.columns:
        blacklist_count = len(df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)])
    projects_count = df['Project'].nunique() if 'Project' in df.columns else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("إجمالي الموظفين", f"{total:,}")
    c2.metric("ذكور", f"{males:,}", delta=f"{(males/total*100 if total else 0):.1f}%")
    c3.metric("إناث", f"{females:,}", delta=f"{(females/total*100 if total else 0):.1f}%")
    c4.metric("عدد المشاريع", projects_count)
    c5.metric("القائمة السوداء", blacklist_count, delta="تحتاج مراجعة" if blacklist_count > 0 else "نظيف")

    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        if 'EmpGender' in df.columns:
            gender_data = df['EmpGender'].value_counts().reset_index()
            gender_data.columns = ['Gender', 'Count']
            fig_gender = px.pie(
                gender_data, names='Gender', values='Count',
                title="توزيع الجنس",
                color_discrete_map={'Male': '#3b82f6', 'Female': '#ec4899'},
                hole=0.4
            )
            fig_gender.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            st.plotly_chart(fig_gender, use_container_width=True)

    with col2:
        if 'Project' in df.columns:
            proj_data = df['Project'].value_counts().head(8).reset_index()
            proj_data.columns = ['Project', 'Count']
            fig_proj = px.bar(
                proj_data, x='Count', y='Project', orientation='h',
                title="توزيع المشاريع", color='Count',
                color_continuous_scale='Blues'
            )
            fig_proj.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0', showlegend=False)
            st.plotly_chart(fig_proj, use_container_width=True)

    with col3:
        if 'Main Position' in df.columns:
            pos_data = df['Main Position'].value_counts().head(8).reset_index()
            pos_data.columns = ['Position', 'Count']
            fig_pos = px.bar(
                pos_data, x='Count', y='Position', orientation='h',
                title="أعلى المسميات الوظيفية", color='Count',
                color_continuous_scale='Teal'
            )
            fig_pos.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0', showlegend=False)
            st.plotly_chart(fig_pos, use_container_width=True)

    # --- مقارنة حسب المشروع والجنس (Heatmap بديل) ---
    if 'Project' in df.columns and 'EmpGender' in df.columns:
        st.divider()
        st.subheader("توزيع الجنس حسب المشروع")
        pivot = df.groupby(['Project', 'EmpGender']).size().unstack(fill_value=0)
        st.dataframe(
            pivot.style.background_gradient(cmap='Blues', axis=None),
            use_container_width=True
        )

# ==============================================================
# 8. البحث العام
# ==============================================================
elif menu == "البحث العام":
    st.title("محرك البحث العام")
    st.caption("ابحث في قاعدة بيانات الموظفين")

    col_s, col_f = st.columns([3, 1])
    with col_s:
        q = st.text_input("كلمة البحث", placeholder="الاسم، الرقم الفردي، الهاتف...")
    with col_f:
        search_mode = st.selectbox("نوع البحث", ["يحتوي على", "يبدأ بـ", "مطابقة تامة"])

    if q:
        search_cols = ['Name', 'Individual Number', 'رقم الهاتف', 'الرقم الأمني']
        available = [c for c in search_cols if c in df.columns]

        def apply_search(series, query, mode):
            if mode == "يحتوي على":
                return series.str.contains(query, case=False, na=False)
            elif mode == "يبدأ بـ":
                return series.str.startswith(query, na=False)
            else:
                return series.str.lower() == query.lower()

        mask = df[available].apply(lambda x: apply_search(x, q, search_mode)).any(axis=1)
        results = df[mask]

        if not results.empty:
            st.success(f"تم العثور على **{len(results)}** سجل.")

            # تصدير النتائج
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                excel_data = export_excel(results)
                st.download_button("تحميل Excel", data=excel_data,
                                   file_name=f"search_{q}_{datetime.date.today()}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.dataframe(results, use_container_width=True)
        else:
            st.warning(f"لا توجد نتائج لـ '{q}' بنمط '{search_mode}'.")

# ==============================================================
# 9. السجل الوظيفي التاريخي
# ==============================================================
elif menu == "السجل الوظيفي":
    st.title("السجل الوظيفي والخط الزمني")
    st.caption("تتبع تاريخ الموظف الكامل داخل المنظمة")

    q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، الهاتف، أو الرقم الأمني)")

    if q_hist:
        search_cols_hist = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
        available_hist = [c for c in search_cols_hist if c in df.columns]
        mask_hist = df[available_hist].apply(lambda x: x.str.contains(q_hist, case=False, na=False)).any(axis=1)
        results_hist = df[mask_hist]

        if not results_hist.empty:
            main_id = results_hist.iloc[0].get('Individual Number', '')
            full_history = df[df['Individual Number'] == main_id].copy().reset_index(drop=True)

            emp_name = results_hist.iloc[0].get('Name', 'N/A')
            emp_status = full_history.iloc[-1].get('حالة الموظف', 'N/A') if 'حالة الموظف' in full_history.columns else 'N/A'
            emp_gender = full_history.iloc[-1].get('EmpGender', 'N/A') if 'EmpGender' in full_history.columns else 'N/A'
            emp_position = full_history.iloc[-1].get('Main Position', 'N/A') if 'Main Position' in full_history.columns else 'N/A'
            emp_project = full_history.iloc[-1].get('Project', 'N/A') if 'Project' in full_history.columns else 'N/A'

            # بطاقة الموظف
            st.subheader(f"ملف الموظف: {emp_name}")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("عدد العقود", f"{len(full_history)}")
            c2.metric("الحالة الحالية", emp_status)
            c3.metric("الجنس", emp_gender)
            c4.metric("المسمى الحالي", emp_position)
            c5.metric("المشروع الحالي", emp_project)

            st.divider()

            # تحقق من وجود حالة محظورة
            if 'حالة الموظف' in full_history.columns:
                if full_history['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False).any():
                    st.error("تحذير: هذا الموظف مُدرج في القائمة السوداء!")

            # الجدول الكامل مع تصدير
            st.subheader("بيانات العقود الكاملة")
            excel_data = export_excel(full_history)
            st.download_button("تحميل السجل الكامل (Excel)", data=excel_data,
                               file_name=f"history_{emp_name}_{datetime.date.today()}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.dataframe(full_history, use_container_width=True)
        else:
            st.warning(f"لا توجد نتائج لـ '{q_hist}'.")

# ==============================================================
# 10. الإحصائيات والتقارير
# ==============================================================
elif menu == "الإحصائيات والتقارير":
    st.title("تحليل القوى العاملة - فلترة ذكية متقدمة")

    st.sidebar.divider()
    st.sidebar.subheader("فلاتر متقدمة")

    base_df = df.copy()

    if 'Main Position' in base_df.columns:
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(base_df['Main Position'].dropna().unique()))
        if sel_pos:
            base_df = base_df[base_df['Main Position'].isin(sel_pos)]

    if 'Project' in base_df.columns:
        sel_proj = st.sidebar.multiselect("المشروع:", sorted(base_df['Project'].dropna().unique()))
        if sel_proj:
            base_df = base_df[base_df['Project'].isin(sel_proj)]

    if 'EmpGender' in base_df.columns:
        sel_gender = st.sidebar.multiselect("الجنس:", sorted(base_df['EmpGender'].dropna().unique()))
        if sel_gender:
            base_df = base_df[base_df['EmpGender'].isin(sel_gender)]

    if 'حالة الموظف' in base_df.columns:
        sel_status = st.sidebar.multiselect("الحالة الوظيفية:", sorted(base_df['حالة الموظف'].dropna().unique()))
        if sel_status:
            base_df = base_df[base_df['حالة الموظف'].isin(sel_status)]

    f_df = base_df.copy()
    total_filtered = len(f_df)

    if not f_df.empty:
        males = len(f_df[f_df['EmpGender'] == 'Male']) if 'EmpGender' in f_df.columns else 0
        females = len(f_df[f_df['EmpGender'] == 'Female']) if 'EmpGender' in f_df.columns else 0
        ratio_text = f"{(females / total_filtered * 100 if total_filtered > 0 else 0):.1f}%"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي (مفلتر)", f"{total_filtered:,}", delta=f"{total_filtered - len(df):,} من الكل")
        c2.metric("ذكور", f"{males:,}")
        c3.metric("إناث", f"{females:,}")
        c4.metric("نسبة الإناث", ratio_text)

        st.divider()

        # خيارات التصدير
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            excel_data = export_excel(f_df)
            st.download_button(
                "تحميل Excel",
                data=excel_data,
                file_name=f"HR_Export_{datetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        with col_e2:
            # فقط للمديرين
            if st.session_state["role"] == "admin":
                if st.button("إنشاء تقرير PDF", use_container_width=True):
                    with st.spinner("جاري إنشاء التقرير..."):
                        try:
                            pdf_bytes = create_pdf_report(f_df, total_filtered, males, females, ratio_text)
                            st.download_button(
                                "تحميل PDF",
                                data=pdf_bytes,
                                file_name=f"HR_Report_{datetime.date.today()}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        except Exception as e:
                            st.error(f"خطأ في إنشاء PDF: {str(e)}")
            else:
                st.info("تصدير PDF متاح للمديرين فقط.")

        st.divider()

        # الرسوم البيانية
        col1, col2 = st.columns(2)
        with col1:
            if 'Main Position' in f_df.columns:
                pos_df = f_df['Main Position'].value_counts().head(10).reset_index()
                pos_df.columns = ['Position', 'Count']
                fig1 = px.bar(pos_df, x='Count', y='Position', orientation='h',
                              title="أعلى 10 مسميات وظيفية",
                              color='Count', color_continuous_scale='Blues')
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig1, use_container_width=True)

        with col2:
            if 'Project' in f_df.columns:
                fig2 = px.pie(f_df, names='Project', title="توزيع المشاريع",
                              color_discrete_sequence=px.colors.qualitative.Set2)
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig2, use_container_width=True)

        # رسم إضافي: توزيع الجنس حسب المشروع
        if 'Project' in f_df.columns and 'EmpGender' in f_df.columns:
            st.subheader("توزيع الجنس حسب المشروع")
            gender_proj = f_df.groupby(['Project', 'EmpGender']).size().reset_index(name='Count')
            fig3 = px.bar(gender_proj, x='Project', y='Count', color='EmpGender',
                          barmode='group', title="مقارنة الجنس حسب المشروع",
                          color_discrete_map={'Male': '#3b82f6', 'Female': '#ec4899'})
            fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            st.plotly_chart(fig3, use_container_width=True)

        # عرض البيانات المفلترة
        with st.expander("عرض البيانات الكاملة المفلترة"):
            st.dataframe(f_df, use_container_width=True)
    else:
        st.warning("لا توجد نتائج حسب الفلاتر المحددة.")

# ==============================================================
# 11. القائمة السوداء
# ==============================================================
elif menu == "القائمة السوداء":
    st.title("إدارة وسجل الحالات المحظورة")

    col_s, col_f = st.columns([3, 1])
    with col_s:
        search_query = st.text_input("ابحث في القائمة السوداء (الاسم، الرقم الفردي، الرقم الأمني، الهاتف)")
    with col_f:
        st.metric("إجمالي الحالات", 
                  len(df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)]) 
                  if 'حالة الموظف' in df.columns else 0)

    if 'حالة الموظف' in df.columns:
        bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)].copy()

        if search_query:
            search_cols = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_search_cols = [col for col in search_cols if col in bl_df.columns]
            if available_search_cols:
                mask = bl_df[available_search_cols].apply(
                    lambda x: x.str.contains(search_query, case=False, na=False)
                ).any(axis=1)
                bl_df = bl_df[mask]

        if not bl_df.empty:
            st.error(f"تم العثور على **{len(bl_df)}** حالة محظورة.")

            # تصدير القائمة السوداء
            if st.session_state["role"] == "admin":
                excel_bl = export_excel(bl_df)
                st.download_button(
                    "تحميل القائمة السوداء (Excel)",
                    data=excel_bl,
                    file_name=f"Blacklist_{datetime.date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.dataframe(bl_df, use_container_width=True)

            # رسم بياني للقائمة السوداء حسب المشروع
            if 'Project' in bl_df.columns:
                st.subheader("توزيع المحظورين حسب المشروع")
                bl_proj = bl_df['Project'].value_counts().reset_index()
                bl_proj.columns = ['Project', 'Count']
                fig_bl = px.bar(bl_proj, x='Project', y='Count',
                                title="الحالات المحظورة حسب المشروع",
                                color='Count', color_continuous_scale='Reds')
                fig_bl.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig_bl, use_container_width=True)
        else:
            if search_query:
                st.info(f"لا توجد نتائج تطابق '{search_query}' في القائمة السوداء.")
            else:
                st.success("لا توجد حالات محظورة مسجلة حالياً.")
    else:
        st.error("عمود 'حالة الموظف' غير موجود في قاعدة البيانات.")
