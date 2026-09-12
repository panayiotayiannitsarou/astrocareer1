from models import Aspect, Point

SIGNS = ["Κριός", "Ταύρος", "Δίδυμοι", "Καρκίνος", "Λέων", "Παρθένος", "Ζυγός", "Σκορπιός", "Τοξότης", "Αιγόκερως", "Υδροχόος", "Ιχθύες"]
SIGN_CODES = dict(zip("abcdefghijkl", SIGNS))


def absolute(sign, degree, minute, second):
    return SIGNS.index(sign) * 30 + degree + minute / 60 + second / 3600


def house_of(value, cusps):
    for i in range(12):
        start, end = cusps[i].absolute, cusps[(i + 1) % 12].absolute
        if (start < end and start <= value < end) or (start >= end and (value >= start or value < end)):
            return i + 1
    raise ValueError("Δεν ήταν δυνατός ο υπολογισμός του Οίκου.")


def orb_weight(orb):
    if orb < 2:
        return "Στενή/ισχυρή"
    if orb < 4:
        return "Κανονική"
    if orb <= 7:
        return "Πλατιά αλλά έγκυρη"
    return "Πολύ πλατιά/δευτερεύουσα"


def opposite_node(node):
    value = (node.absolute + 180) % 360
    si = int(value // 30)
    rem = value - si * 30
    degree = int(rem)
    minute = int((rem - degree) * 60)
    second = round((((rem - degree) * 60) - minute) * 60)
    return Point("SN", "Νότιος Δεσμός", SIGNS[si], degree, minute, second, value,
                 retrograde=node.retrograde, kind="node")


def south_node_aspects(aspects):
    opposite_map = {"Σύνοδος": "Αντίθεση", "Αντίθεση": "Σύνοδος", "Τετράγωνο": "Τετράγωνο", "Τρίγωνο": "Εξάγωνο", "Εξάγωνο": "Τρίγωνο"}
    result = []
    for aspect in aspects:
        if "Βόρειος Δεσμός" not in (aspect.first, aspect.second):
            continue
        derived = opposite_map.get(aspect.aspect)
        if derived:
            other = aspect.second if aspect.first == "Βόρειος Δεσμός" else aspect.first
            result.append(Aspect("Νότιος Δεσμός", other, derived, aspect.orb, aspect.orb_text,
                                 aspect.weight, "Μαθηματική παραγωγή από τον άξονα Δεσμών", aspect.applying))
    return result
