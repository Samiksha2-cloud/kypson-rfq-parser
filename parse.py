import re
import difflib


multipliers = {
    "k": 1000, "hazaar": 1000, "hajar": 1000, "hazar": 1000, "thousand": 1000,
    "lakh": 100000, "lakhs": 100000, "lac": 100000, "lacs": 100000,
    "crore": 10000000,
}
HINDI_NUM = {"ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "panch": 5, "das": 10}

def to_number(num_str, word=None):
    clean = num_str.replace(",", "")
    value = float(clean)
    multiplier = multipliers.get(word, 1)
    result = value * multiplier
    if result.is_integer():
        return int(result)
    return result

pattern = r"(\d[\d,]*(?:\.\d+)?)\s*(?:(hazaar|hajar|hazar|thousand|lakhs|lakh|lacs|lac|crore|k)\b)?\s*([a-zA-Z]+)?"

COUNT_WORDS = {"pcs", "pc", "pieces", "piece", "bags", "bag", "boxes", "box",
               "nos", "units", "rolls", "pouches"}
KG_WORDS = {"kg", "kgs", "kilo", "kilos", "kilogram", "kilograms"}
TON_WORDS = {"mt", "ton", "tons", "tonne", "tonnes"}

def parse_numbers(text):
    text = text.lower()
    text = re.sub(
        r"\b(ek|do|teen|char|paanch|panch|das)\s+(?=(?:hazaar|hajar|hazar|thousand|lakhs|lakh|lacs|lac|crore)\b)",
        lambda m: str(HINDI_NUM[m.group(1)]) + " ",
        text,
    )
    gsm = None
    micron = None
    candidates = []          # (priority, quantity, unit)

    for m in re.finditer(pattern, text):
        num_str, mult, word = m.groups()
        after = text[m.end():m.end() + 12]
        is_capacity = re.match(r"\s*(capacity|cap\b|bag|bags|sack|sacks)", after)

        if word == "gsm":
            gsm = to_number(num_str)
        elif word in ("mic", "micron", "microns"):
            micron = to_number(num_str)
        elif word in COUNT_WORDS:
            candidates.append((3, to_number(num_str, mult), "pcs"))
        elif word in TON_WORDS:
            if not is_capacity:
                candidates.append((2, to_number(num_str, mult), "mt"))
        elif word in KG_WORDS:
            if not is_capacity:
                candidates.append((1, to_number(num_str, mult), "kg"))
        else:
            candidates.append((2, to_number(num_str, mult), "pcs"))

    best = None
    for c in candidates:
        if best is None or c[0] > best[0]:
            best = c

    quantity = best[1] if best else None
    unit = best[2] if best else None
    return {"quantity": quantity, "unit": unit, "gsm": gsm, "micron": micron}


CATEGORY_RULES = [
    ("fibc",           ["jumbo", "fibc", "bulk bag", "big bag"]),
    ("mono_carton",    ["mono", "monocarton"]),
    ("pouch",          ["pouch", "sachet"]),
    ("film",           ["film", "shrink", "stretch", "wrap"]),
    ("bopp_bag",       ["bopp"]),
    ("woven_sack",     ["woven", "cement", "ad star", "adstar", "hdpe", "sack"]),
    ("corrugated_box", ["corrugated", "box", "carton"]),
    ("woven_sack",     ["bag"]),
]

def has_keyword(text, tokens, kw):
    if " " in kw:
        return kw in text
    for t in tokens:
        if t.startswith(kw):
            return True
        if len(kw) >= 5 and difflib.SequenceMatcher(None, t, kw).ratio() >= 0.8:
            return True
    return False

def get_category(text):
    text = text.lower()
    tokens = re.findall(r"[a-z]+", text)
    for category, keywords in CATEGORY_RULES:
        for kw in keywords:
            if has_keyword(text, tokens, kw):
                return category
    return None


NOT_PLACE = set("""
to at in near for from with and of the a an be me my send give share
chahiye chahie chaiye need needed require required requirement quote quotation rfq
price rate urgent urgently please pls plz hi hello sir bhai kindly supplier
manufacturer order bulk qty quantity mein tak ko se ke liye ka ki aur per each
all sample samples delivery deliver delivered delivering location loc destination
ship shipping dispatch export
pcs pc kg kgs mt ton tons tonne tonnes gsm mic micron microns nos units piece pieces
hazaar hajar lakh lac k roll rolls ply inch cm mm
bag bags box boxes carton cartons pouch pouches film sack sacks jumbo fibc bopp
woven laminated cement shrink stretch wrap hdpe pp corrugated mono capacity cap
size print printed plain new ad star adstar big stand up standup zipper
""".split())

PLACE_FIX = {"uae": "UAE", "usa": "USA", "uk": "UK"}

def take_place_words(tokens):
    place = []
    for t in tokens:
        if not t.isalpha() or t in NOT_PLACE or len(t) < 3 and t not in PLACE_FIX:
            break
        place.append(t)
        if len(place) == 3:
            break
    return place

def get_location(text):
    text = text.lower()
    place = []

    for m in re.finditer(r"\b(?:to|at|in|near|delivery|deliver|location|destination|ship)\b[\s:\-]*", text):
        rest = re.split(r"[,;\n]", text[m.end():])[0]
        place = take_place_words(re.findall(r"[a-z]+|\d+", rest))
        if place:
            break

    if not place:
        for m in re.finditer(r"\b([a-z]{3,})\s+(?:mein|me|tak|ko|ke\s+liye|ke\s+lie)\b", text):
            place = take_place_words([m.group(1)])
            if place:
                break
    if not place:
        for seg in reversed(re.split(r"[,;\n|]", text)):
            tokens = re.findall(r"[a-z]+|\d+", seg)
            if 0 < len(tokens) <= 3 and len(take_place_words(tokens)) == len(tokens):
                place = tokens
                break

    if not place:
        tokens = re.findall(r"[a-z]+|\d+", text)
        while tokens and tokens[-1] in NOT_PLACE:
            tokens.pop()
        if tokens:
            place = take_place_words(tokens[-1:])

    if not place:
        return None
    joined = " ".join(place)
    return PLACE_FIX.get(joined, joined.title())


def parse_rfq(text: str) -> dict:
    if not isinstance(text, str):
        text = ""
    nums = parse_numbers(text)
    return {
        "category": get_category(text),
        "quantity": nums["quantity"],
        "unit": nums["unit"] or "pcs",
        "gsm": nums["gsm"],
        "micron": nums["micron"],
        "location": get_location(text),
    }

if __name__ == "__main__":
    print(parse_rfq("bopp bags chahiye 40 hazaar, 65 gsm, Nagpur"))
    print(parse_rfq("jumbo bag 1000 kg capacity, 500 pcs, Vadodara"))
    print(parse_rfq("need quote for 500 kg shrink wrap 25 mic"))