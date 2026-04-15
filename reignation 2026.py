import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="نظام إدارة المتطوعين", layout="wide", page_icon="🔍")

# --- 2. دالة إنشاء تقرير PDF (مبسطة) ---
def create_pdf_report(total, males, females, ratio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Workforce Analysis Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Total Employees: {total}", ln=True)
    pdf.cell(200, 10, txt=f"Males: {males}", ln=True)
    pdf.cell(200, 10, txt=f"Females: {females}", ln=True)
    pdf.cell(200, 10, txt=f"Female Ratio: {ratio}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. تحميل البيانات ---
# ملاحظة: استبدل هذا الجزء بالكود الخاص بك لتحميل ملف Excel أو CSV
# df = pd.read_excel("your_file.xlsx")
@st.cache_data
def get_sample_data():
    data = {
        'EmpNo': [6527, 6528, 6529, 6530, 6531],
        'Name': ['يونس جروان سلامه', 'أحمد علي محمد', 'سارة محمود', 'ليلى خالد', 'عمر ياسين'],
        'Project': ['Makani', 'Village 5', 'Makani', 'Village 4', 'Makani'],
        'EmpGender': ['Male', 'Male', 'Female', 'Female', 'Male'],
        'Main Position': ['Security Guard', 'Teacher', 'Coordinator', 'Security Guard', 'Manager'],
        'Status': ['مستقيل', 'على رأس العمل', 'على رأس العمل', 'مستقيل', 'على رأس العمل']
    }
    return pd.DataFrame(data)

df = get_sample_data()

# --- 4. القائمة الجانبية للتنقل ---
st.sidebar.title("📑 القائمة الرئيسية")
menu = st.sidebar.selectbox("اختر الصفحة:", ["محرك البحث", "الاحصائيات المرنة"])

# --- 5. صفحة محرك البحث ---
if menu == "محرك البحث":
    st.header("🔍 محرك البحث عن المتطوعين")
    search_query = st.text_input("ابحث بالاسم، الرقم الوظيفي، أو المشروع:", placeholder="اكتب هنا...")

    if search_query:
        # فلترة البيانات بناءً على البحث في عدة أعمدة
        results = df[
            df['Name'].str.contains(search_query, na=False, case=False) | 
            df['EmpNo'].astype(str).str.contains(search_query, na=False) |
            df['Project'].str.contains(search_query, na=False, case=False)
        ].copy()

        # ✅ الحل الصحيح للخطأ الذي ظهر في صورتك:
        if not results.empty:
            st.success(f"✅ تم العثور على {len(results)} نتيجة")
            
            # تنظيف عرض الأرقام الوظيفية (إزالة .0)
            results['EmpNo'] = results['EmpNo'].astype(str).str.replace(r'\.0$', '', regex=True)
            
            # عرض الجدول
            st.dataframe(results, use_container_width=True)
        else:
            st.error("⚠️ لا توجد نتائج تطابق بحثك")
    else:
        st.info("💡 أدخل أي معلومة في مربع البحث أعلاه لعرض النتائج.")

# --- 6. صفحة الاحصائيات المرنة ---
elif menu == "الاحصائيات المرنة":
    st.header("📊 تحليل القوى العاملة")
    st.sidebar.subheader("فلاتر التقرير")

    f_df = df.copy()

    # فلاتر اختيارية في القائمة الجانبية
    if 'Main Position' in f_df.columns:
        sel_pos = st.sidebar.multiselect("المسمى الوظيفي:", sorted(f_df['Main Position'].unique()))
        if sel_pos:
            f_df = f_df[f_df['Main Position'].isin(sel_pos)]

    if 'Project' in f_df.columns:
        sel_proj = st.sidebar.multiselect("المشروع:", sorted(f_df['Project'].unique()))
        if sel_proj:
            f_df = f_df[f_df['Project'].isin(sel_proj)]

    if 'EmpGender' in f_df.columns:
        sel_gender = st.sidebar.multiselect("الجنس:", ["Male", "Female"])
        if sel_gender:
            f_df = f_df[f_df['EmpGender'].isin(sel_gender)]

    total_filtered = len(f_df)

    if total_filtered > 0:
        # حساب الحصائيات
        males = len(f_df[f_df['EmpGender'] == 'Male'])
        females = len(f_df[f_df['EmpGender'] == 'Female'])
        ratio_val = (females / total_filtered * 100) if total_filtered > 0 else 0
        ratio_text = f"{ratio_val:.1f}%"

        # عرض الكروت الرقمية
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("إجمالي الموظفين", total_filtered)
        c2.metric("عدد الذكور 👨", males)
        c3.metric("عدد الإناث 👩", females)
        c4.metric("نسبة الإناث", ratio_text)

        st.divider()

        # زر تحميل التقرير
        if st.button("📥 إنشاء تقرير PDF"):
            try:
                pdf_bytes = create_pdf_report(total_filtered, males, females, ratio_text)
                st.download_button("تحميل الملف الآن", data=pdf_bytes, file_name="HR_Report.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"حدث خطأ أثناء إنشاء PDF: {e}")

        st.divider()

        # الرسوم البيانية
        col1, col2 = st.columns(2)
        with col1:
            if not f_df['Main Position'].empty:
                fig1 = px.bar(f_df['Main Position'].value_counts().head(10), 
                             orientation='h', title="أعلى المسميات الوظيفية",
                             labels={'value': 'العدد', 'index': 'المسمى'})
                st.plotly_chart(fig1, use_container_width=True)

        with col2:
            if not f_df['Project'].empty:
                fig2 = px.pie(f_df, names='Project', title="توزيع الموظفين حسب المشاريع", hole=0.3)
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ لا توجد بيانات لعرضها بناءً على الفلاتر المختارة.")

# --- 7. تذييل الصفحة ---
st.sidebar.markdown("---")
st.sidebar.caption("تم التطوير بواسطة ذكاء اصطناعي مساعد 🤖")
