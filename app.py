import streamlit as st
from generator import generate
from orientation import build_prompt, docx_text, prompt_docx, validate_result
from parser import parse_astrodienst_pdf

st.set_page_config(page_title="Career Orientation", page_icon="✦", layout="wide")
st.markdown("""<style>.stApp{background:#faf7fc}.block-container{max-width:1100px;padding-top:3.8rem}.hero{background:linear-gradient(135deg,#76538c,#ad83c2);color:white;border-radius:24px;padding:30px 34px;margin:8px 0 20px}.hero h1{margin:0;font-family:Georgia;font-size:38px}.hero p{color:#f5ebfa}.ok{padding:13px 15px;background:#f0e7f5;border-left:5px solid #76538c;border-radius:9px}.warn{padding:13px 15px;background:#fff1dd;border-left:5px solid #b7791f;border-radius:9px}.stButton>button[kind="primary"]{background:#76538c;border-color:#76538c}</style>""", unsafe_allow_html=True)

EL={"title":"Επαγγελματικός Προσανατολισμός","subtitle":"Από το Astrodienst PDF σε ελεγμένη, απλή και πρακτική διερεύνηση δυνατοτήτων.","new":"Νέα περίπτωση","clear":"Καθαρισμός όλων","privacy":"Τα στοιχεία παραμένουν μόνο στην τρέχουσα συνεδρία της εφαρμογής.","tabs":["1 · PDF","2 · Επιλογές","3 · Δημιουργία","4 · Έλεγχος Word"],"upload":"Ανέβασε το Astrodienst Natal Chart Data Sheet","read":"Ανάγνωση PDF","bad":"Το αρχείο δεν αναγνωρίστηκε ως πλήρες Astrodienst Data Sheet.","details":"Τεχνική λεπτομέρεια","loaded":"✓ Το PDF φορτώθηκε επιτυχώς. Συνέχισε στην Καρτέλα 2 · Επιλογές.","replace":"Αντικατάσταση με άλλο PDF","first":"Πρώτα ανέβασε το PDF στην Καρτέλα 1.","name":"Όνομα στο τελικό έγγραφο","service":"Υπηρεσία","child":"Παιδί/έφηβος","adult":"Ενήλικας σε αλλαγή επαγγελματικής πορείας","presentation":"Παρουσίαση","simple":"Απλή και πρακτική","analytical":"Αναλυτική με αστρολογική τεκμηρίωση","cyprus":"Φοιτά στο κυπριακό εκπαιδευτικό σύστημα;","yes":"Ναι","no":"Όχι","two":"Στην απλή παρουσίαση θα παραχθούν δύο Word: το καθαρό κείμενο του πελάτη και το εσωτερικό τεχνικό δελτίο.","need":"Χρειάζεται πρώτα ένα έγκυρο PDF στην Καρτέλα 1.","prompt":"Λήψη πλήρους εντολής για ChatGPT ή Claude","preview":"Προεπισκόπηση εντολής","auto":"Προαιρετική αυτόματη δημιουργία","create":"Δημιουργία κειμένου","created":"Η δημιουργία ολοκληρώθηκε. Αντέγραψε το κείμενο σε Word και έλεγξέ το στην Καρτέλα 4.","failed":"Η αυτόματη δημιουργία απέτυχε.","generated":"Παραγόμενο κείμενο","nocase":"Δεν υπάρχει ενεργή περίπτωση.","result":"Καθαρό τελικό Word","audit":"Εσωτερικό τεχνικό δελτίο","check":"Έλεγχος τελικού αποτελέσματος","passed":"✓ Το Word πέρασε τον βασικό έλεγχο δομής.","download":"Λήψη ελεγμένου Word","fix":"Το Word χρειάζεται διορθώσεις."}
EN={"title":"Career Orientation","subtitle":"From an Astrodienst PDF to a verified, clear and practical exploration of potential.","new":"New case","clear":"Clear all","privacy":"Data remains only in the current application session.","tabs":["1 · PDF","2 · Options","3 · Create","4 · Word Review"],"upload":"Upload the Astrodienst Natal Chart Data Sheet","read":"Read PDF","bad":"The file was not recognised as a complete Astrodienst Data Sheet.","details":"Technical details","loaded":"✓ The PDF was uploaded successfully. Continue to Tab 2 · Options.","replace":"Replace with another PDF","first":"Upload the PDF in Tab 1 first.","name":"Name on the final document","service":"Service","child":"Child/teenager","adult":"Adult considering a career change","presentation":"Presentation","simple":"Clear and practical","analytical":"Detailed with astrological evidence","cyprus":"Does the child attend the Cyprus education system?","yes":"Yes","no":"No","two":"The clear presentation produces two Word files: the client document and a separate internal technical record.","need":"A valid PDF is required in Tab 1 first.","prompt":"Download full instructions for ChatGPT or Claude","preview":"Instruction preview","auto":"Optional automatic creation","create":"Create text","created":"Creation is complete. Copy the text into Word and review it in Tab 4.","failed":"Automatic creation failed.","generated":"Generated text","nocase":"There is no active case.","result":"Final client Word file","audit":"Internal technical record","check":"Review final result","passed":"✓ The Word file passed the basic structure review.","download":"Download reviewed Word file","fix":"The Word file needs corrections."}

_, lang_col=st.columns([6,1.6])
with lang_col:
    language=st.selectbox("Γλώσσα / Language",["Ελληνικά","English"],key="site_language")
lang="el" if language=="Ελληνικά" else "en"; t=EL if lang=="el" else EN
st.markdown(f'<div class="hero"><h1>{t["title"]}</h1><p>{t["subtitle"]}</p></div>',unsafe_allow_html=True)

defaults={"chart":None,"generation":0,"validation":None,"result_bytes":None,"result_name":""}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k]=v
def new_case():
    generation=st.session_state.generation+1
    for k in ("client_name","service","presentation","cyprus_answer","generated_text"): st.session_state.pop(k,None)
    for k,v in defaults.items(): st.session_state[k]=v
    st.session_state.generation=generation

with st.sidebar:
    st.header(t["new"])
    if st.button(t["clear"],use_container_width=True): new_case(); st.rerun()
    st.caption(t["privacy"])

tab1,tab2,tab3,tab4=st.tabs(t["tabs"])
with tab1:
    chart=st.session_state.chart
    if not chart:
        st.subheader(t["upload"]); pdf=st.file_uploader("PDF",type=["pdf"],key=f"pdf_{st.session_state.generation}")
        if pdf and st.button(t["read"],type="primary"):
            try:
                chart=parse_astrodienst_pdf(pdf.getvalue(),pdf.name); new_case(); st.session_state.chart=chart; st.rerun()
            except Exception as exc:
                st.error(t["bad"])
                with st.expander(t["details"]): st.code(str(exc))
    else:
        st.markdown(f'<div class="ok">{t["loaded"]}</div>',unsafe_allow_html=True)

with tab2:
    chart=st.session_state.chart
    if not chart: st.warning(t["first"])
    else:
        st.text_input(t["name"],value=chart.name,key="client_name")
        st.radio(t["service"],["child","adult"],format_func=lambda x:t[x],key="service")
        st.radio(t["presentation"],["simple","analytical"],format_func=lambda x:t[x],key="presentation")
        if st.session_state.service=="child": st.radio(t["cyprus"],[True,False],format_func=lambda x:t["yes"] if x else t["no"],horizontal=True,key="cyprus_answer")
        st.info(t["two"])

with tab3:
    chart=st.session_state.chart
    if not chart: st.warning(t["need"])
    else:
        name=st.session_state.get("client_name",chart.name); sid=st.session_state.get("service","child"); pid=st.session_state.get("presentation","simple")
        service="Παιδί/έφηβος" if sid=="child" else "Ενήλικας σε αλλαγή επαγγελματικής πορείας"
        presentation="Απλή και πρακτική" if pid=="simple" else "Αναλυτική με αστρολογική τεκμηρίωση"
        output_language="Ελληνικά" if lang=="el" else "English"; cyprus=sid=="child" and st.session_state.get("cyprus_answer",True)
        prompt=build_prompt(chart,name,service,presentation,output_language,cyprus)
        st.download_button(t["prompt"],prompt_docx(name,t[sid],prompt),file_name="career_orientation_prompt.docx",use_container_width=True)
        with st.expander(t["preview"]): st.text_area("",prompt,height=300,label_visibility="collapsed")
        st.divider(); st.markdown(f'#### {t["auto"]}'); api=st.text_input("OpenAI API key",type="password",placeholder="sk-...")
        if st.button(t["create"],type="primary",disabled=not api):
            try: st.session_state.generated_text=generate(api,prompt); st.success(t["created"])
            except Exception as exc:
                st.error(t["failed"])
                with st.expander(t["details"]): st.code(str(exc))
        if st.session_state.get("generated_text"): st.text_area(t["generated"],st.session_state.generated_text,height=360)

with tab4:
    chart=st.session_state.chart
    if not chart: st.warning(t["nocase"])
    else:
        sid=st.session_state.get("service","child"); pid=st.session_state.get("presentation","simple")
        service="Παιδί/έφηβος" if sid=="child" else "Ενήλικας σε αλλαγή επαγγελματικής πορείας"; presentation="Απλή και πρακτική" if pid=="simple" else "Αναλυτική με αστρολογική τεκμηρίωση"; output_language="Ελληνικά" if lang=="el" else "English"
        result=st.file_uploader(t["result"],type=["docx"],key=f"result_{st.session_state.generation}"); audit=st.file_uploader(t["audit"],type=["docx"],key=f"audit_{st.session_state.generation}") if pid=="simple" else None
        ready=bool(result) and (pid!="simple" or bool(audit))
        if st.button(t["check"],type="primary",disabled=not ready):
            data=result.getvalue(); errors=validate_result(docx_text(data),service,presentation,output_language,docx_text(audit.getvalue()) if audit else "")
            st.session_state.validation=errors; st.session_state.result_bytes=data; st.session_state.result_name=result.name
        errors=st.session_state.validation
        if errors==[]:
            st.markdown(f'<div class="ok">{t["passed"]}</div>',unsafe_allow_html=True); st.download_button(t["download"],st.session_state.result_bytes,file_name=st.session_state.result_name,use_container_width=True)
        elif errors:
            st.markdown(f'<div class="warn">{t["fix"]}</div>',unsafe_allow_html=True)
            for error in errors: st.write("•",error)
