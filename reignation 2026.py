import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. دالة إنشاء تقرير PDF (دعم اللغة العربية يتطلب خطوطاً خاصة، هنا نستخدم تنسيقاً أساسياً) ---
def create_pdf_report(dataframe, total, males, females, ratio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # عنوان التقرير
    pdf.cell(200, 10, txt="Workforce Analysis Report", ln=True, align='C')
    pdf.ln(10)
    
    # الإحصائيات
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total Employees: {total}", ln=True)
    pdf.cell(200, 10, txt=f"Males: {males}", ln=True)
    pdf.cell(200, 10, txt=f"Females: {females}", ln=True)
    pdf.cell(200, 10, txt=f"Female Ratio: {ratio}", ln=True)
    
    # تحويل الـ PDF إلى Bytes
    return pdf.output(dest='S').encode('latin-1')

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="نظام تحليل الموارد البشرية", layout="wide")

# --- 3. بيانات تجريبية (قم بحذف هذا الجزء واستخدم df الخاص بك) ---
if 'df' not in locals():
    data = {
        'Main Position': ['Manager', 'Developer', 'Designer', 'Developer', 'Manager', 'Analyst'],
        'Project': ['Alpha', 'Beta', 'Alpha', 'Gamma', 'Beta', 'Alpha'],
        'EmpGender': ['Male', 'Female', 'Female', 'Male', 'Male', 'Female']
    }
    df = pd.DataFrame(data)

# --- 4. القائمة الجانبية ---
menu = st.sidebar.selectbox("القائمة الرئيسية", ["الرئيسية", "الاحصائيات المرنة"])

# --- 5. منطق الإحصائيات المرنة ---
if menu == "الاحصائيات المرنة":
    st.header("📊 تحليل القوى العاملة")
    st.sidebar.subheader("فلاتر التقرير")

    base_df = df.copy()

    # فلتر المسمى الوظيفي
    if 'Main Position' in base_df.columns:
        options_pos = sorted(base_df['Main Position'].dropna().unique())
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", options_pos)
        if sel_pos:
            base_df = base_df[base_df['Main Position'].isin(sel_pos)]

    # فلتر المشروع
    if 'Project' in base_df.columns:
        options_proj = sorted(base_df['Project'].dropna().unique())
        sel_proj = st.sidebar.multiselect("المشروع:", options_proj)
        if sel_proj:
            base_df = base_df[base_df['Project'].isin(sel_proj)]

    # فلتر الجنس
    if 'EmpGender' in base_df.columns:
        # تنظيف البيانات لضمان دقة الفلترة
        base_df['EmpGender'] = base_df['EmpGender'].astype(str).str.strip().str.capitalize()
        options_gender = sorted(base_df['EmpGender'].unique())
        sel_gender = st.sidebar.multiselect("الجنس:", options_gender)
        if sel_gender:
            base_df = base_df[base_df['EmpGender'].isin(sel_gender)]

    f_df = base_df.copy()
    total_filtered = len(f_df)

    if total_filtered > 0:
        # حساب المقاييس
        males = len(f_df[f_df['EmpGender'] == 'Male'])
        females = len(f_df[f_df['EmpGender'] == 'Female'])
        ratio_val = (females / total_filtered) * 100
        ratio_text = f"{ratio_val:.1f}%"

        # عرض الكروت الرقمية
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي الموظفين", total_filtered)
        c2.metric("ذكور 👨", males)
        c3.metric("إناث 👩", females)
        c4.metric("نسبة الإناث", ratio_text)

        st.divider()

        # زر تصدير PDF
        if st.button("📥 إنشاء تقرير PDF"):
            try:
                pdf_bytes = create_pdf_report(f_df, total_filtered, males, females, ratio_text)
                st.download_button(
                    label="تحميل ملف PDF",
                    data=pdf_bytes,
                    file_name="HR_Report.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"خطأ في إنشاء التقرير: {e}")

        st.divider()

        # الرسوم البيانية
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Main Position' in f_df.columns and not f_df['Main Position'].empty:
                counts = f_df['Main Position'].value_counts().head(10).reset_index()
                counts.columns = ['Position', 'Count']
                fig1 = px.bar(counts, x='Count', y='Position', orientation='h', 
                             title="أعلى 10 مسميات وظيفية",
                             color='Count', color_continuous_scale='Viridis')
                st.plotly_chart(fig1, use_container_width=True)

        with col2:
            if 'Project' in f_df.columns and not f_df['Project'].empty:
                fig2 = px.pie(f_df, names='Project', title="توزيع الموظفين حسب المشروع",
                             hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)

        # عرض جدول البيانات المفلترة اختياريًا
        with st.expander("👁️ عرض البيانات المفلترة"):
            st.dataframe(f_df, use_container_width=True)

    else:
        st.warning("⚠️ لا توجد نتائج مطابقة للفلاتر المختارة.")

else:
    st.title("👋 مرحباً بك في نظام الإدارة")
    st.info("يرجى اختيار 'الاحصائيات المرنة' من القائمة الجانبية لبدء التحليل.")
