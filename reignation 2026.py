import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

# --- 1. دالة إنشاء تقرير PDF (أساسية) ---
def create_pdf_report(dataframe, total, males, females, ratio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Workforce Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total: {total}", ln=True)
    pdf.cell(200, 10, txt=f"Males: {males}", ln=True)
    pdf.cell(200, 10, txt=f"Females: {females}", ln=True)
    pdf.cell(200, 10, txt=f"Female Ratio: {ratio}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="نظام إدارة المتطوعين", layout="wide")

# --- 3. تحميل البيانات (بيانات تجريبية - استبدلها بملفك) ---
@st.cache_data
def load_data():
    # هنا يمكنك استخدام pd.read_excel("file.xlsx")
    data = {
        'EmpNo': [6527, 6528, 6529, 6530],
        'Name': ['يونس جروان سلامه', 'أحمد علي محمد', 'سارة محمود', 'ليلى خالد'],
        'Project': ['Makani', 'Village 5', 'Makani', 'Village 4'],
        'EmpGender': ['Male', 'Male', 'Female', 'Female'],
        'Main Position': ['Security Guard', 'Teacher', 'Coordinator', 'Security Guard'],
        'Status': ['مستقيل', 'على رأس العمل', 'على رأس العمل', 'مستقيل']
    }
    return pd.DataFrame(data)

df = load_data()

# --- 4. القائمة الجانبية ---
st.sidebar.title("📌 القائمة الرئيسية")
menu = st.sidebar.radio("انتقل إلى:", ["محرك البحث", "الاحصائيات المرنة"])

# --- 5. محرك البحث عن المتطوعين ---
if menu == "محرك البحث":
    st.header("🔍 محرك البحث عن المتطوعين")
    search_query = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")

    if search_query:
        # البحث في الاسم أو الرقم (تحويل الرقم لنص للمطابقة)
        results = df[
            df['Name'].str.contains(search_query, na=False) | 
            df['EmpNo'].astype(str).str.contains(search_query, na=False)
        ]
        
        # --- تصحيح الخطأ الذي ظهر في الصورة ---
        if not results.empty:
            st.success(f"تم العثور على {len(results)} نتيجة")
            # تنظيف عرض الأرقام (إزالة الفواصل العشرية)
            display_df = results.copy()
            display_df['EmpNo'] = display_df['EmpNo'].astype(str)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.warning("⚠️ لا توجد نتائج مطابقة")
    else:
        st.info("يرجى إدخال بيانات في حقل البحث")

# --- 6. الاحصائيات المرنة ---
elif menu == "الاحصائيات المرنة":
    st.header("📊 تحليل القوى العاملة")
    st.sidebar.subheader("فلاتر التقرير")

    f_df = df.copy()

    # فلاتر اختيارية
    if 'Main Position' in f_df.columns:
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(f_df['Main Position'].unique()))
        if sel_pos:
            f_df = f_df[f_df['Main Position'].isin(sel_pos)]

    if 'Project' in f_df.columns:
        sel_proj = st.sidebar.multiselect("المشروع:", sorted(f_df['Project'].unique()))
        if sel_proj:
            f_df = f_df[f_df['Project'].isin(sel_proj)]

    if 'EmpGender' in f_df.columns:
        sel_gender = st.sidebar.multiselect("الجنس:", sorted(f_df['EmpGender'].unique()))
        if sel_gender:
            f_df = f_df[f_df['EmpGender'].isin(sel_gender)]

    total_filtered = len(f_df)

    if total_filtered > 0:
        # الحسابات
        males = len(f_df[f_df['EmpGender'].str.strip().str.capitalize() == 'Male'])
        females = len(f_df[f_df['EmpGender'].str.strip().str.capitalize() == 'Female'])
        ratio_text = f"{(females/total_filtered*100):.1f}%"

        # عرض الكروت
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي", total_filtered)
        c2.metric("ذكور", males)
        c3.metric("إناث", females)
        c4.metric("نسبة الإناث", ratio_text)

        st.divider()

        # زر PDF
        if st.button("📥 إنشاء تقرير PDF"):
            pdf_bytes = create_pdf_report(f_df, total_filtered, males, females, ratio_text)
            st.download_button("تحميل الملف", data=pdf_bytes, file_name="Report.pdf", mime="application/pdf")

        st.divider()

        # الرسوم البيانية
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(f_df['Main Position'].value_counts().head(10), title="أعلى المسميات")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.pie(f_df, names='Project', title="توزيع المشاريع")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ لا توجد بيانات لعرضها بناءً على الفلاتر")
