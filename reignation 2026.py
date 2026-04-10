if menu == "🔍 محرك البحث التاريخي":
        st.header("🔍 البحث الشامل والسجل التاريخي")
        q = st.text_input("ابحث بـ (Name, Case Number, Individual Number, الرقم الأمني, رقم الهاتف)")
        
        if q:
            # تحديد أعمدة البحث
            search_cols = ['Name', 'Case Number', 'Individual Number', 'الرقم الأمني', 'رقم الهاتف']
            available = [c for c in search_cols if c in df.columns]
            
            mask = df[available].apply(lambda x: x.str.contains(q, case=False, na=False)).any(axis=1)
            results = df[mask]

            if not results.empty:
                # الاعتماد على Individual Number لجلب كل السجلات التاريخية
                main_id = results.iloc[0].get('Individual Number', '')
                # تصفية الجدول الأصلي لجلب كل عقود هذا الشخص
                full_history = df[df['Individual Number'] == main_id].copy()
                
                # تحويل التواريخ لتنسيق واضح (إذا كانت متوفرة)
                date_cols = ['Start Date', 'End Date']
                for col in date_cols:
                    if col in full_history.columns:
                        full_history[col] = pd.to_view(full_history[col]).fillna('غير محدد')

                st.subheader(f"👤 ملف الموظف: {results.iloc[0].get('Name', 'N/A')}")
                
                # بطاقات تفصيلية
                c1, c2, c3 = st.columns(3)
                num_contracts = len(full_history)
                c1.metric("إجمالي مرات التوظيف", f"{num_contracts} مرات")
                c2.metric("أول تاريخ تعاقد", full_history.sort_values('Year').iloc[0].get('Start Date', 'N/A'))
                c3.metric("آخر تاريخ تعاقد", full_history.sort_values('Year').iloc[-1].get('Start Date', 'N/A'))

                st.divider()
                
                # عرض التواريخ والمسميات في جدول مخصص
                st.write("📅 **تفاصيل التوظيف التاريخية (بالتواريخ):**")
                
                # اختيار أعمدة محددة للعرض لتركيز الانتباه
                display_cols = ['Year', 'Project', 'Main Position', 'Start Date', 'End Date', 'حالة الموظف']
                actual_display = [c for c in display_cols if c in full_history.columns]
                
                # عرض الجدول مرتباً من الأحدث للقديم
                st.table(full_history[actual_display].sort_values(by='Year', ascending=False))
                
                with st.expander("🔍 عرض كافة بيانات السجل (Dataframe)"):
                    st.dataframe(full_history, use_container_width=True)
            else:
                st.warning("⚠️ لم يتم العثور على موظف بهذه البيانات.")
