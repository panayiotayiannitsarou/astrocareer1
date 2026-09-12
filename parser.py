import io
import re

import pdfplumber

from astrology import SIGN_CODES, absolute, house_of, opposite_node, orb_weight, south_node_aspects
from models import Aspect, Chart, Point

POINT_NAMES = {"A":"Ήλιος", "B":"Σελήνη", "C":"Ερμής", "D":"Αφροδίτη", "E":"Άρης", "F":"Δίας", "G":"Κρόνος", "O":"Ουρανός", "I":"Ποσειδώνας", "J":"Πλούτωνας", "L":"Βόρειος Δεσμός", "N":"Χείρωνας", "Q":"Ωροσκόπος", "T":"Μεσουράνημα"}
ASPECT_GLYPHS = {"m":"Σύνοδος", "q":"Εξάγωνο", "o":"Τετράγωνο", "p":"Τρίγωνο", "s":"Χιαστί όψη 150°", "n":"Αντίθεση"}
LONG_RE = re.compile(r"(\d{1,2})°\s*(\d{1,2})'\s*(\d{1,2})\"")


def _point(code, name, sign_code, d, m, s, house=None, retro=False, kind="planet"):
    sign = SIGN_CODES[sign_code]
    return Point(code, name, sign, int(d), int(m), int(s), absolute(sign, int(d), int(m), int(s)), int(house) if house else None, retro, kind)


def _metadata(text, filename):
    name, date, time, place = filename.rsplit(".", 1)[0], "", "", ""
    for line in text.splitlines()[:14]:
        if "Time" in line and not time:
            left, right = line.split("Time", 1)
            name = re.sub(r"^[D\s]+", "", left).strip() or name
            match = re.search(r"(\d{1,2}:\d{2}\s*[ap]\.m\.)", right)
            time = match.group(1) if match else ""
        if "born on" in line:
            date = line.split("born on", 1)[1].split("Univ.Time", 1)[0].strip()
        if line.strip().startswith("in "):
            place = line.strip()[3:].split("Sid. Time", 1)[0].strip()
    return name, date, time, place, "Placidus" if "Houses (Plac.)" in text else "Δεν αναγνωρίστηκε"


def _parse_positions(page):
    words = page.extract_words(x_tolerance=1, y_tolerance=2, keep_blank_chars=False)
    rows = {}
    for word in words:
        rows.setdefault(round(word["top"], 1), []).append(word)
    points, cusp_order = [], []
    wanted = ["A","B","C","D","E","F","G","O","I","J","K","L","N"]
    for y, ws in sorted(rows.items()):
        code = next((w["text"] for w in ws if w["text"] in wanted and 30 <= w["x0"] < 45), None)
        if not code:
            continue
        sign_word = next((w for w in ws if w["text"] in SIGN_CODES and 100 < w["x0"] < 120), None)
        cusp_sign = next((w for w in ws if w["text"] in SIGN_CODES and 440 < w["x0"] < 460), None)
        data = next((ws2 for y2, ws2 in rows.items() if 3 < y2 - y < 7), [])
        if not sign_word or not data:
            continue
        longitude = "".join(w["text"] for w in sorted(data, key=lambda z:z["x0"]) if 120 < w["x0"] < 178)
        lm = LONG_RE.search(longitude)
        house_word = next((w for w in data if 184 < w["x0"] < 207 and w["text"].isdigit()), None)
        if lm and house_word and code in POINT_NAMES:
            negative_motion = any(w["text"] == "-" and 210 < w["x0"] < 250 for w in data)
            retrograde = any(w["text"] == "#" for w in ws) or negative_motion
            points.append(_point(code, POINT_NAMES[code], sign_word["text"], *lm.groups(), house_word["text"], retrograde, "node" if code == "L" else "planet"))
        if cusp_sign:
            cusp_long = "".join(w["text"] for w in sorted(data, key=lambda z:z["x0"]) if 460 < w["x0"] < 510)
            cm = LONG_RE.search(cusp_long)
            if cm:
                cusp_order.append((cusp_sign["text"], *cm.groups()))
    cusps = [_point(f"H{i}", f"{i}ος Οίκος", sg, d, mi, se, kind="cusp") for i, (sg, d, mi, se) in enumerate(cusp_order[:12], 1)]
    return points, cusps


def _parse_aspects(page, points_by_code):
    words = page.extract_words(x_tolerance=1, y_tolerance=2, keep_blank_chars=False)
    marker = next((w for w in words if w["text"] == "Aspects"), None)
    if not marker:
        return []
    rows = {}
    for word in words:
        if word["top"] > marker["top"] + 12:
            rows.setdefault(round(word["top"], 1), []).append(word)
    row_codes = [c for c in ["B","C","D","E","F","G","O","I","J","L","N","Q","T"] if c in points_by_code]
    col_codes = [c for c in ["A","B","C","D","E","F","G","O","I","J","L","N","Q"] if c in points_by_code]
    col_x = [56 + 41.4 * i for i in range(len(col_codes))]
    result = []
    for y, ws in sorted(rows.items()):
        row_code = next((w["text"] for w in ws if w["text"] in row_codes and w["x0"] < 45), None)
        if not row_code:
            continue
        orb_words = [w for y2, ws2 in rows.items() if 3 < y2-y < 7 for w in ws2 if re.match(r"^-?\d+°\d{2}[as]$", w["text"])]
        for glyph in [w for w in ws if w["text"] in ASPECT_GLYPHS]:
            idx = min(range(len(col_x)), key=lambda i: abs((glyph["x0"] + glyph["x1"]) / 2 - col_x[i]))
            if col_codes[idx] == row_code:
                continue
            orb_word = min(orb_words, key=lambda w: abs((w["x0"] + w["x1"]) / 2 - (col_x[idx] + 21)), default=None)
            if not orb_word:
                continue
            mo = re.match(r"(-?)(\d+)°(\d{2})([as])", orb_word["text"])
            orb = int(mo.group(2)) + int(mo.group(3)) / 60
            result.append(Aspect(points_by_code[col_codes[idx]].name, points_by_code[row_code].name,
                                 ASPECT_GLYPHS[glyph["text"]], orb, f"{int(mo.group(2))}°{int(mo.group(3)):02d}′",
                                 orb_weight(orb), "Πίνακας Astrodienst", mo.group(4) == "a"))
    return result


def parse_astrodienst_pdf(data, filename):
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        page = pdf.pages[0]
        text = page.extract_text(layout=True) or ""
        name, date, time, place, method = _metadata(text, filename)
        points, cusps = _parse_positions(page)
        if len(cusps) != 12 or len(points) < 10:
            raise ValueError("Δεν αναγνωρίστηκε πλήρες Astrodienst Natal Chart Data Sheet.")
        for point in points:
            point.house = house_of(point.absolute, cusps)
        points += [Point("Q", "Ωροσκόπος", cusps[0].sign, cusps[0].degree, cusps[0].minute, cusps[0].second, cusps[0].absolute, kind="angle"),
                   Point("T", "Μεσουράνημα", cusps[9].sign, cusps[9].degree, cusps[9].minute, cusps[9].second, cusps[9].absolute, kind="angle")]
        node = next((p for p in points if p.name == "Βόρειος Δεσμός"), None)
        if node:
            south = opposite_node(node)
            south.house = house_of(south.absolute, cusps)
            points.append(south)
        by_code = {p.code:p for p in points}
        aspects = _parse_aspects(page, by_code)
        if node:
            aspects.extend(south_node_aspects(aspects))
        if not aspects:
            raise ValueError("Δεν αναγνωρίστηκε ο πίνακας όψεων. Το πρόγραμμα σταμάτησε για να μην παραχθεί ανακριβές αποτέλεσμα.")
        return Chart(name, date, time, place, method, points, cusps, aspects, [])
