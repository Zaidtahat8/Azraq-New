import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# 1. إعدادات الصفحة (تظهر كعنوان في المتصفح)
st.set_page_config(page_title="سجل القائمة السوداء - مخيم الأزرق", layout="wide")

# 2. تحسين المظهر وإضافة طبقة حماية للنصوص
st.markdown("""
    <style>
    .stApp { background-color: #fff5f5; } /* خلفية مائلة للاحمرار للتنبيه */
    [data-testid="stElementToolbar"] { display: none; }
    .main { background-color: rgba(255, 255, 255, 0.9); padding: 25px; border-radius: 15px; }
    </style>
""", unsafe_allow_html=True)

# 3. دالة جلب البيانات من SharePoint
@st.cache_data(ttl=600)
def load_data():
    URL = "https://bdcjoorg-my.sharepoint.com/:x:/g/personal/zaltahat_bdc_org_jo/IQABP_FEs97DRZNQFxtFvyRGAe2xdQxDW6L3jTRC3S803SU?download=1"
    try:
        res = requests.get(URL)
        data = pd.read_excel(BytesIO(res.content))
        return data.astype(str)
    except:
        return None

df = load_data()

# 4. محتوى الصفحة
st.error("🚫 سجل القائمة السوداء (الأسماء المحظورة من التوظيف)")
st.info("هذا السجل يحتوي على الأشخاص الذين تم إنهاء خدماتهم لأسباب إدارية أو سلوكية.")

if df is not None:
    # الفلترة بناءً على ملاحظات المنع (تأكد من كتابة 'منقطع' أو 'Blacklist' في عمود Notes بالإكسل)
    bl_keywords = ['منقطع', 'انهاء', 'موقوف', 'blacklist', 'terminat']
    blacklist_df = df[df['Notes'].str.contains('|'.join(bl_keywords), case=False, na=False)]

    search_q = st.text_input("🔍 ابحث عن اسم للتحقق من حالته في القائمة السوداء")

    if search_q:
        results = blacklist_df[blacklist_df.astype(str).apply(lambda x: x.str.contains(search_q, case=False, na=False)).any(axis=1)]
        if not results.empty:
            st.warning(f"⚠️ تحذير: تم العثور على {len(results)} سجل في قائمة المنع!")
            # عرض الجدول بلون أحمر تحذيري
            st.dataframe(results.style.set_properties(**{'background-color': '#fee2e2', 'color': '#b91c1c'}), use_container_width=True)
        else:
            st.success("✅ هذا الاسم غير مدرج في القائمة السوداء حالياً.")
    else:
        st.write("عرض كافة السجلات المحظورة:")
        st.dataframe(blacklist_df, use_container_width=True)
else:
    st.error("⚠️ فشل في الاتصال بقاعدة البيانات.")

