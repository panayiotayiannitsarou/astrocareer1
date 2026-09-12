import streamlit as st
import pandas as pd

from generator import generate
from orientation import build_prompt, docx_text, prompt_docx, validate_result
from parser import parse_astrodienst_pdf

st.set_page_config(page_title="Επαγγελματικός Προσανατολισμός", page_icon="✦", layout="wide")
st.markdown("""<style>
.stApp{background:#faf7fc}.block-container{max-width:1100px;padding-top:2rem}.hero{background:linear-gradient(135deg,#76538c,#ad83c2);color:white;border-radius:24px;padding:30px 34px;margin-bottom:20px}.hero h1{margin:0;font-family:Georgia;font-size:38px}.hero p{color:#f5ebfa}.ok{padding:13px 15px;background:#f0e7f5;border-left:5px solid #76538c;border-radius:9px}.warn{padding:13px 15px;background:#fff1dd;border-left:5px solid #b7791f;border-radius:9px}div[data-testid="stMetric"]{background:white;border:1px solid #e5d9eb;padding:10px;border-radius:12px}.stButton>button[kind="primary"]{background:#76538c;border-color:#76538c}</style>""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>Επαγγελματικός Προσανατολισμός</h1><p>Από το Astrodienst PDF σε ελεγμένη, απλή και πρακτική διερεύνηση δυνατοτήτων.</p></div>', unsafe_allow_html=True)

defaults = {"chart":None, "generation":0, "validation":None, "result_bytes":None, "result_name":""}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def new_case():
    generation = st.session_state.generation + 1
    for key in ("client_name", "service", "output_language", "presentation", "cyprus_answer", "generated_text"):
        st.session_state.pop(key, None)
    for key, value in defaults.items():
        st.session_state[key] = value
    st.session_state.generation = generation


with st.sidebar:
    st.header("Νέα περίπτωση")
    if st.button("Καθαρισμός όλων", use_container_width=True):
        new_case()
        st.rerun()
    st.caption("Τα στοιχεία παραμένουν μόνο στην τρέχουσα συνεδρία της εφαρμογής.")

tab1, tab2, tab3, tab4 = st.tabs(["1 · PDF και αυτόματος έλεγχος", "2 · Επιλογές", "3 · Δημιουργία", "4 · Έλεγχος Word"])

with tab1:
    chart = st.session_state.chart
    if not chart:
        st.subheader("Ανέβασε το Astrodienst Natal Chart Data Sheet")
        pdf = st.file_uploader("PDF", type=["pdf"], key=f"pdf_{st.session_state.generation}")
        if pdf and st.button("Ανάγνωση PDF", type="primary"):
            try:
                chart = parse_astrodienst_pdf(pdf.getvalue(), pdf.name)
                new_case()
                st.session_state.chart = chart
                st.rerun()
            except Exception as exc:
                st.error("Το αρχείο δεν αναγνωρίστηκε ως πλήρες Astrodienst Data Sheet.")
                with st.expander("Τεχνική λεπτομέρεια"):
                    st.code(str(exc))
    else:
        st.markdown(
            f'<div class="ok">✓ Το PDF της/του <b>{chart.name}</b> είναι ήδη φορτωμένο. '
            'Ο αυτόματος τεχνικός έλεγχος ολοκληρώθηκε και μπορείς να πας απευθείας στην Καρτέλα 2.</div>',
            unsafe_allow_html=True,
        )
        a, b, c = st.columns(3)
        a.metric("Πλανήτες και σημεία", len(chart.points))
        b.metric("Ακμές Οίκων", len(chart.cusps))
        c.metric("Όψεις", len(chart.aspects))
        st.write({"Όνομα":chart.name, "Ημερομηνία":chart.date, "Ώρα":chart.time, "Τόπος":chart.place})
        hard = [x for x in chart.aspects if x.aspect in ("Τετράγωνο", "Αντίθεση")]
        with st.expander("Έλεγχος βασικών όψεων", expanded=True):
            st.dataframe(pd.DataFrame([{"Ζεύγος":f"{x.first}–{x.second}", "Όψη":x.aspect, "Orb":x.orb_text, "Βαρύτητα":x.weight} for x in hard]), use_container_width=True, hide_index=True)
        st.caption("✓ Αυτόματος έλεγχος: 12 ακμές, πλήρης κατάλογος σημείων και αναγνωρισμένος πίνακας όψεων.")
        if st.button("Αντικατάσταση με άλλο PDF"):
            new_case()
            st.rerun()

with tab2:
    chart = st.session_state.chart
    if not chart:
        st.warning("Πρώτα ανέβασε το PDF στην Καρτέλα 1.")
    else:
        name = st.text_input("Όνομα στο τελικό έγγραφο", value=chart.name, key="client_name")
        service = st.radio("Υπηρεσία", ["Παιδί/έφηβος", "Ενήλικας σε αλλαγή επαγγελματικής πορείας"], key="service")
        language = st.radio("Γλώσσα τελικού κειμένου", ["Ελληνικά", "English"], horizontal=True, key="output_language")
        presentation = st.radio("Παρουσίαση", ["Απλή και πρακτική", "Αναλυτική με αστρολογική τεκμηρίωση"], key="presentation")
        cyprus = False
        if service == "Παιδί/έφηβος":
            cyprus_answer = st.radio("Φοιτά στο κυπριακό εκπαιδευτικό σύστημα;", ["Ναι", "Όχι"], horizontal=True, key="cyprus_answer")
            cyprus = cyprus_answer == "Ναι"
        st.info("Στην απλή παρουσίαση θα χρειαστούν δύο Word: το καθαρό κείμενο του πελάτη και το εσωτερικό τεχνικό δελτίο.")

with tab3:
    chart = st.session_state.chart
    if not chart:
        st.warning("Χρειάζεται πρώτα ένα έγκυρο PDF στην Καρτέλα 1.")
    else:
        name = st.session_state.get("client_name", chart.name)
        service = st.session_state.get("service", "Παιδί/έφηβος")
        language = "Ελληνικά" if st.session_state.get("output_language", "Ελληνικά") == "Ελληνικά" else "English"
        presentation = st.session_state.get("presentation", "Απλή και πρακτική")
        cyprus = service == "Παιδί/έφηβος" and st.session_state.get("cyprus_answer", "Ναι") == "Ναι"
        prompt = build_prompt(chart, name, service, presentation, language, cyprus)
        st.download_button("Λήψη πλήρους εντολής για ChatGPT ή Claude", prompt_docx(name, service, prompt), file_name="career_orientation_prompt.docx", use_container_width=True)
        with st.expander("Προεπισκόπηση εντολής"):
            st.text_area("", prompt, height=300, label_visibility="collapsed")
        st.divider()
        st.markdown("#### Προαιρετική αυτόματη δημιουργία")
        api_key = st.text_input("OpenAI API key", type="password", placeholder="sk-...")
        if st.button("Δημιουργία κειμένου", type="primary", disabled=not api_key):
            try:
                st.session_state.generated_text = generate(api_key, prompt)
                st.success("Η δημιουργία ολοκληρώθηκε. Αντέγραψε το κείμενο σε Word και έλεγξέ το στην Καρτέλα 4.")
            except Exception as exc:
                st.error("Η αυτόματη δημιουργία απέτυχε.")
                with st.expander("Τεχνική λεπτομέρεια"):
                    st.code(str(exc))
        if st.session_state.get("generated_text"):
            st.text_area("Παραγόμενο κείμενο", st.session_state.generated_text, height=360)

with tab4:
    chart = st.session_state.chart
    if not chart:
        st.warning("Δεν υπάρχει ενεργή περίπτωση.")
    else:
        service = st.session_state.get("service", "Παιδί/έφηβος")
        language = "Ελληνικά" if st.session_state.get("output_language", "Ελληνικά") == "Ελληνικά" else "English"
        presentation = st.session_state.get("presentation", "Απλή και πρακτική")
        result_file = st.file_uploader("Καθαρό τελικό Word", type=["docx"], key=f"result_{st.session_state.generation}")
        audit_file = None
        if presentation == "Απλή και πρακτική":
            audit_file = st.file_uploader("Εσωτερικό τεχνικό δελτίο", type=["docx"], key=f"audit_{st.session_state.generation}")
        ready = bool(result_file) and (presentation != "Απλή και πρακτική" or bool(audit_file))
        if st.button("Έλεγχος τελικού αποτελέσματος", type="primary", disabled=not ready):
            result_bytes = result_file.getvalue()
            text = docx_text(result_bytes)
            audit_text = docx_text(audit_file.getvalue()) if audit_file else ""
            errors = validate_result(text, service, presentation, language, audit_text)
            st.session_state.validation = errors
            st.session_state.result_bytes = result_bytes
            st.session_state.result_name = result_file.name
        errors = st.session_state.validation
        if errors == []:
            st.markdown('<div class="ok">✓ Το Word πέρασε τον βασικό έλεγχο δομής.</div>', unsafe_allow_html=True)
            st.download_button("Λήψη ελεγμένου Word", st.session_state.result_bytes, file_name=st.session_state.result_name, use_container_width=True)
        elif errors:
            st.markdown('<div class="warn">Το Word χρειάζεται διορθώσεις.</div>', unsafe_allow_html=True)
            for error in errors:
                st.write("•", error)
