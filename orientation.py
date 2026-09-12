from io import BytesIO
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


def fmt(point):
    return f"{point.sign} {point.degree}°{point.minute:02d}′{point.second:02d}″"


def technical_source(chart):
    points = "\n".join(f"- {p.name}: {fmt(p)} | Οίκος {p.house or '—'}" for p in chart.points)
    cusps = "\n".join(f"- {i}ος Οίκος: {fmt(c)}" for i, c in enumerate(chart.cusps, 1))
    aspects = "\n".join(f"- {a.first}–{a.second} | {a.aspect} | orb {a.orb_text} | {a.weight} | {a.source}" for a in chart.aspects)
    return f"ΠΛΑΝΗΤΕΣ ΚΑΙ ΣΗΜΕΙΑ\n{points}\n\nΑΚΜΕΣ ΟΙΚΩΝ\n{cusps}\n\nΕΠΙΒΕΒΑΙΩΜΕΝΕΣ ΟΨΕΙΣ\n{aspects}"


def build_prompt(chart, name, service, presentation, language, cyprus_school=False):
    language_rule = "Γράψε ολόκληρο το παραδοτέο στα Ελληνικά." if language == "Ελληνικά" else "Write the complete deliverable in natural, clear English. Translate all headings and labels into English."
    simple = presentation == "Απλή και πρακτική"
    audience = "παιδί/έφηβο" if service == "Παιδί/έφηβος" else "ενήλικο που διερευνά πιθανή αλλαγή επαγγελματικής πορείας"
    adult_rule = "" if service == "Παιδί/έφηβος" else """
ΕΙΔΙΚΟΣ ΚΑΝΟΝΑΣ ΕΝΗΛΙΚΟΥ
Το κείμενο να είναι σύντομο, απλό και πρακτικό. Μην προσθέσεις ξεχωριστές ενότητες «Κατάλληλο εργασιακό περιβάλλον», «Εργασιακά περιβάλλοντα», «Επόμενα βήματα» ή «Σχέδιο 8–12 εβδομάδων». Μην παρουσιάσεις τον ενήλικο ως παιδί. Μην επινοήσεις επάγγελμα, σπουδές, εμπειρία, εισόδημα ή οικογενειακές υποχρεώσεις.
"""
    cyprus_rule = "" if service != "Παιδί/έφηβος" or not cyprus_school else """
Πρόσθεσε απλή ενότητα «Πλαίσιο Εκπαιδευτικού Συστήματος Κύπρου» πριν από την τελική σύνθεση. Εξήγησε συνοπτικά τις τέσσερις ΟΜΠ, σύνδεσε τις επιλογές μόνο με θετικά υποστηριζόμενα ταλέντα και υπενθύμισε ότι μετρούν επίσης οι πραγματικές επιδόσεις, τα ενδιαφέροντα, οι προϋποθέσεις εισαγωγής και η συμβουλή εκπαιδευτικού συμβούλου. Για κάθε τομέα πρόσθεσε χωριστά ενδεικτικά επαγγέλματα και ενδεικτικές πανεπιστημιακές σπουδές ή Τμήματα. Μην επινοήσεις επίσημες προϋποθέσεις και μην εμφανίσεις πηγές στο καθαρό παραδοτέο.
"""
    presentation_rule = """
Το καθαρό παραδοτέο δεν πρέπει να περιέχει ονόματα πλανητών, ζώδια, Οίκους, όψεις, orb ή κατηγορίες βαρύτητας. Μετάφρασε την τεχνική βάση σε καθημερινή, πιθανολογική γλώσσα. Παράδωσε και δεύτερο, χωριστό εσωτερικό τεχνικό δελτίο με πλήρη τεκμηρίωση.
""" if simple else """
Μπορείς να παρουσιάσεις την αστρολογική τεκμηρίωση. Κάθε τεχνική αναφορά πρέπει να συμφωνεί ακριβώς με τα δεδομένα και να περιλαμβάνει σωστό ζεύγος, τύπο όψης, orb και βαρύτητα. Πρόσθεσε Παράρτημα Ελέγχου Τεκμηρίωσης.
"""
    return f"""ΔΕΣΜΕΥΤΙΚΗ ΕΝΤΟΛΗ ΕΠΑΓΓΕΛΜΑΤΙΚΟΥ ΠΡΟΣΑΝΑΤΟΛΙΣΜΟΥ

Όνομα: {name}
Τύπος υπηρεσίας: {service}
Κοινό: {audience}
Τρόπος παρουσίασης: {presentation}
Γλώσσα: {language}

{language_rule}
{presentation_rule}
{adult_rule}
{cyprus_rule}

Χρησιμοποίησε αποκλειστικά τα ελεγμένα τεχνικά δεδομένα που ακολουθούν. Μην χρησιμοποιήσεις μνήμη, προηγούμενες συνομιλίες ή προσωπικά στοιχεία που δεν δόθηκαν. Μην παρουσιάσεις συμβολική ένδειξη ως βεβαιότητα. Η ανάλυση δεν είναι επιστημονικό ή ψυχομετρικό τεστ και δεν αποφασίζει για το άτομο.

ΔΟΜΗ ΚΑΘΑΡΟΥ ΠΑΡΑΔΟΤΕΟΥ
1. Τίτλος και σύντομη εισαγωγή.
2. Προφίλ δυνατοτήτων, με προσεκτική πιθανολογική γλώσσα.
3. Τρία έως πέντε βασικά ταλέντα. Για κάθε ταλέντο χρησιμοποίησε πίνακα δύο στηλών με τέσσερις γραμμές: «Πώς τεκμηριώνεται», «Πώς μπορεί να εμφανίζεται / Πώς μπορεί να εκφράζεται», «Πώς μπορεί να καλλιεργηθεί / Πώς μπορεί να αξιοποιείται», «Δραστηριότητα δοκιμής / Ασφαλής δοκιμή διερεύνησης». Κάθε ταλέντο πρέπει να στηρίζεται σε τουλάχιστον δύο διακριτούς δείκτες.
4. Τέσσερις έως έξι Επαγγελματικοί Τομείς προς Διερεύνηση. Για κάθε τομέα: «Γιατί μπορεί να ταιριάζει», «Τι χρειάζεται επιβεβαίωση», «Δραστηριότητα δοκιμής», «Ενδεικτικά επαγγέλματα». Εξήγησε με μία απλή φράση κάθε άγνωστο επάγγελμα και σύνδεσε τα επαγγέλματα με ταλέντα.
5. Τρόπος μάθησης και δημιουργίας.
6. Δυνατά σημεία που χρειάζονται καλλιέργεια.
7. Πιθανά εμπόδια, χωρίς διάγνωση ή μοιρολατρία.
8. Τελική σύνθεση και υπενθύμιση ότι οι πραγματικές εμπειρίες, τα ενδιαφέροντα, οι δεξιότητες και οι συνθήκες ζωής υπερισχύουν.

ΤΕΧΝΙΚΟ ΔΕΛΤΙΟ
Να έχει αναγνωρίσιμη ενότητα «Παράρτημα Ελέγχου Τεκμηρίωσης». Κατάγραψε την ιεράρχηση βαρύτητας των όψεων, τους δύο ή περισσότερους διακριτούς δείκτες κάθε ταλέντου και πλήρη κάλυψη των πέντε στενότερων όψεων με σωστό ζεύγος, τύπο, orb και βαρύτητα.

ΕΛΕΓΜΕΝΑ ΤΕΧΝΙΚΑ ΔΕΔΟΜΕΝΑ
{technical_source(chart)}
"""


TECHNICAL_TERMS = re.compile(r"\b(?:Ήλιος|Σελήνη|Ερμής|Αφροδίτη|Άρης|Δίας|Κρόνος|Ουρανός|Ποσειδώνας|Πλούτωνας|Χείρωνας|Ωροσκόπος|Μεσουράνημα|orb|Ο[ίι]κος|σύνοδος|τρίγωνο|εξάγωνο|τετράγωνο|αντίθεση)\b|\d{1,2}°\d{1,2}[′']", re.I)


def validate_result(text, service, presentation, language, audit_text=""):
    errors = []
    low = text.lower()
    if len(text.strip()) < 700:
        errors.append("Το κείμενο είναι υπερβολικά σύντομο.")
    greek_terms = ["προφίλ", "ταλέντ", "επαγγελματικ", "τελική σύνθεση"]
    english_terms = ["profile", "talent", "career", "final synthesis"]
    required = greek_terms if language == "Ελληνικά" else english_terms
    for term in required:
        if term not in low:
            errors.append(f"Δεν εντοπίστηκε η βασική ενότητα: {term}.")
    if service != "Παιδί/έφηβος" and re.search(r"8\s*[–-]\s*12\s+(?:εβδομάδ|weeks)|εργασιακ(?:ά|ό)\s+περιβάλλον|work\s+environment", text, re.I):
        errors.append("Η έκδοση ενηλίκου περιέχει ενότητα που έχει αφαιρεθεί από τις προδιαγραφές.")
    if presentation == "Απλή και πρακτική":
        if TECHNICAL_TERMS.search(text):
            errors.append("Η απλή έκδοση περιέχει τεχνική αστρολογική ορολογία.")
        if not audit_text.strip():
            errors.append("Λείπει το εσωτερικό τεχνικό δελτίο.")
        elif not re.search(r"(?:Παράρτημα|Appendix).{0,80}(?:Τεκμηρίωσ|Evidence|Audit)", audit_text, re.I | re.S):
            errors.append("Το τεχνικό δελτίο δεν έχει αναγνωρίσιμη ενότητα ελέγχου.")
    return errors


def docx_text(data):
    document = Document(BytesIO(data))
    blocks = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            blocks.append(" | ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(blocks)


def _shade(cell, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shd)


def prompt_docx(name, service, prompt):
    document = Document()
    sec = document.sections[0]
    sec.top_margin = sec.bottom_margin = Inches(.75)
    sec.left_margin = sec.right_margin = Inches(.8)
    document.styles["Normal"].font.name = "Aptos"
    document.styles["Normal"].font.size = Pt(10.5)
    title = document.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run(service).font.color.rgb = RGBColor.from_string("76538C")
    sub = document.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(name).bold = True
    for line in prompt.splitlines():
        if line.isupper() and len(line) < 100:
            document.add_heading(line, level=1)
        else:
            document.add_paragraph(line)
    bio = BytesIO()
    document.save(bio)
    return bio.getvalue()
