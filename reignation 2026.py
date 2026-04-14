import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px
from fpdf import FPDF
import datetime
import os

# ملاحظة: لعمل التصدير بشكل صحيح، تأكد من إضافة fpdf و openpyxl لملف requirements.txt

# --- 1. إعدادات الصفحة والتنسيق ---
st.set_page_config(page_title="نظام HR مخيم الأزرق 2026", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] { background-color: #0f172a !important; border: 2px solid #1e293b !important; padding: 20px !important; border-radius: 15px !important; }
    div[data-testid="stMetricValue"] { color: #00f2ff !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] { color: #cbd5e1 !important; }
    </style>
""", unsafe_allow_html=True)

# --- دالة توليد تقرير PDF (حل مشكلة Unicode) ---
def create_pdf_report(dataframe, total, males, females, ratio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # 1. عنوان التقرير (يظل كما هو)
    pdf.cell(200, 10, txt="HR Workforce Report - 2026", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    # 2. ملخص البيانات الرقمية (يظل كما هو)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(190, 10, txt="Statistical Summary", ln=True, fill=True)
    pdf.cell(95, 10, txt=f"Total Filtered: {total}", border=1)
    pdf.cell(95, 10, txt=f"Female Ratio: {ratio}", border=1, ln=True)
    pdf.cell(95, 10, txt=f"Males: {males}", border=1)
    pdf.cell(95, 10, txt=f"Females: {females}", border=1, ln=True)
    pdf.ln(10)

    # 3. إضافة الرسومات البيانية بالألوان الكاملة (التعديل الجديد)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, txt="Visual Analytics - Project Distribution", ln=True)
    pdf.ln(5)

    try:
        # إنشاء الرسم البياني
        if 'Project' in dataframe.columns:
            fig_pdf = px.pie(dataframe, names='Project', title="Project Distribution")
            
            # --- التعديل الجوهري لحل مشكلة الألوان ---
            # إجبار التنسيق على الوضع الفاتح وبخلفية بيضاء تماماً ليتناسب مع ورق الطباعة
            fig_pdf.update_layout(
                template="plotly_white",  # استخدام التنسيق الأبيض
                paper_bgcolor='white',    # لونه الخلفية الورقية بيضاء
                plot_bgcolor='white',     # لون خلفية الرسم بيضاء
                font=dict(color="black")  # تحديد لون الخط بالأسود ليكون واضحاً
            )
            
            # حفظ الرسم كصورة مؤقتة بدقة عالية
            img_path = f"temp_{datetime.datetime.now().timestamp()}.png"
            fig_pdf.write_image(img_path, scale=2) # scale=2 لزيادة الدقة
            
            # إدراج الصورة في الـ PDF
            pdf.image(img_path, x=20, y=None, w=150)
            
            # مسح الصورة المؤقتة
            if os.path.exists(img_path):
                os.remove(img_path)
                
    except Exception as e:
        pdf.set_font("Arial", size=10)
        pdf.cell(190, 10, txt=f"Note: Colors could not be rendered perfectly. Error: {str(e)}", ln=True)

    return pdf.output(dest='S').encode('latin-1', errors='replace')
# --- 2. نظام الدخول ---
if "password_correct" not in st.session_state:
    st.title("🔐 بوابة إدارة الموارد البشرية")
    u = st.text_input("اسم المستخدم")
    p = st.text_input("كلمة المرور", type="password")
    if st.button("دخول"):
        if u == "zaid" and p == "11111":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ بيانات الدخول خاطئة")
    st.stop()

# --- 3. جلب البيانات ---
@st.cache_data(ttl=300)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    
    try:
        res = requests.get(URL, timeout=10)
        data = pd.read_excel(BytesIO(res.content), engine='openpyxl')
        
        # تنظيف البيانات
        data = data.fillna('')
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip()
        
        return data

    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

# --- 4. إدارة الواجهة والقوائم ---
if df is not None:
    st.sidebar.image("bdc_logo.png", width=150)
    menu = st.sidebar.radio("القائمة الرئيسية", [
        "🔍 البحث العام", 
        "🔍 محرك البحث التاريخي", 
        "📊 الإحصائيات المرنة", 
        "🚫 القائمة السوداء"
    ])
    
    # --- قسم البحث العام ---
    if menu == "🔍 البحث العام":
        st.header("🔍 محرك البحث عن المتطوعين")
        q = st.text_input("ابحث بالاسم، الرقم الفردي، أو الهاتف")
        q = q.strip()
        if q:
            search_cols = ['Name', 'Individual Number', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]
            if not results.empty:
                st.success(f"تم العثور على {len(results)} سجل.")
                st.dataframe(results, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # --- قسم البحث التاريخي ---
    elif menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 السجل الوظيفي والخط الزمني")
        q_hist = st.text_input("ابحث بـ (الاسم، الرقم الفردي، الهاتف، أو الرقم الأمني)")
        if q_hist:
            search_cols_hist = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available_hist = [c for c in search_cols_hist if c in df.columns]
            mask_hist = df[available_hist].apply(lambda x: x.str.contains(q_hist, case=False, na=False)).any(axis=1)
            results_hist = df[mask_hist]

            if not results_hist.empty:
                main_id = results_hist.iloc[0].get('Individual Number', '')
if 'Individual Number' in df.columns:
    full_history = df[df['Individual Number'] == main_id].copy()
else:
    st.error("⚠️ عمود Individual Number غير موجود")
else:
    st.error("⚠️ عمود Individual Number غير موجود")
                st.subheader(f"👤 ملف الموظف: {results_hist.iloc[0].get('Name', 'N/A')}")
                
                c1, c2 = st.columns(2)
                c1.metric("إجمالي مرات التوظيف", f"{len(full_history)} عقود")
                c2.metric("الحالة الحالية", full_history.iloc[-1].get('حالة الموظف', 'N/A'))
                
                st.write("📂 **بيانات الإكسل الكاملة:**")
                st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لا توجد نتائج.")

    # 📊 الإحصائيات المرنة
    elif menu == "📊 الإحصائيات المرنة":
        st.header("📊 تحليل القوى العاملة (فلترة ذكية متقدمة)")
        st.sidebar.divider()
        st.sidebar.subheader("🎯 فلاتر متقدمة")

        base_df = df.copy()

        # الفلاتر
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
            c2.metric("ذكور 👨", males)
            c3.metric("إناث 👩", females)
            c4.metric("نسبة الإناث", ratio_text)

            st.divider()
            # زر تصدير PDF
            if st.button("📥 إنشاء تقرير PDF", use_container_width=True):
                pdf_bytes = create_pdf_report(f_df, total_filtered, males, females, ratio_text)
                st.download_button(label="تحميل الملف", data=pdf_bytes, file_name="HR_Report.pdf", mime="application/pdf")

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
            st.warning("⚠️ لا توجد نتائج حسب الفلاتر")

# --- قسم القائمة السوداء المطور ---
    elif menu == "🚫 القائمة السوداء":
        st.header("🚫 إدارة وسجل الحالات المحظورة")
        
        # 1. إضافة خانة البحث المخصص داخل القائمة السوداء
        search_query = st.text_input("🔍 ابحث في القائمة السوداء (الاسم، الرقم الفردي، الرقم الأمني، أو الهاتف)")

        if 'حالة الموظف' in df.columns:
            # تصفية البيانات الأساسية للقائمة السوداء أولاً
            bl_df = df[df['حالة الموظف'].str.contains('Blacklist|منع', case=False, na=False)].copy()
            
            # 2. تطبيق البحث إذا قام المستخدم بإدخال نص
            if search_query:
                # تحديد الأعمدة التي سيتم البحث فيها
                search_cols = ['Name', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
                # التأكد من وجود هذه الأعمدة في الملف لتجنب الأخطاء
                available_search_cols = [col for col in search_cols if col in bl_df.columns]
                
                # إجراء عملية البحث (تجاهل حالة الأحرف)
                mask = bl_df[available_search_cols].apply(
                    lambda x: x.str.contains(search_query, case=False, na=False)
                ).any(axis=1)
                bl_df = bl_df[mask]

            # 3. عرض النتائج
            if not bl_df.empty:
                st.warning(f"⚠️ تم العثور على {len(bl_df)} حالة محظورة.")
                st.dataframe(bl_df, use_container_width=True)
            else:
                if search_query:
                    st.info("ℹ️ لا توجد نتائج تطابق بحثك في القائمة السوداء.")
                else:
                    st.success("✅ لا توجد حالات محظورة مسجلة حالياً.")
        else:
            st.error("⚠️ عمود 'حالة الموظف' غير موجود في قاعدة البيانات.")
