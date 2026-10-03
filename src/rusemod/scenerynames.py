"""Plain-English names for the map's scenery types (trees, props, buildings), which the game names only in its
editor's code, mostly French: "Cotentin_PanierOsier1" -> "Wicker basket 1 (Cotentin)", "Bouleau_02_G" -> "Birch 2,
winter look". The game has no text for them, so the names are made from the code's words (WORDS, every word the
shipped maps' placeable types use: tests/test_scenerynames.py checks none is left out) and what its editor files it
under (KINDS)."""
from __future__ import annotations

import re

# two words that read as one thing, in English order
PHRASES = {
    ("panier", "osier"): "wicker basket", ("valise", "osier"): "wicker suitcase", ("champs", "pierres"): "stony field",
    ("sac", "sable"): "sandbag", ("tas", "foin"): "haystack", ("tas", "feuilles"): "leaf pile", ("bac", "a"): "planter",
    ("tas", "planches"): "pile of planks", ("tas", "bois"): "woodpile", ("champs", "bles"): "wheat field",
    ("champs", "fleurs"): "flower field", ("champs", "verts"): "green field", ("figuier", "barbarie"): "prickly pear",
    ("herbes", "marais"): "marsh grass", ("herbe", "haute"): "tall grass", ("pommes", "au"): "apples on the",
    ("chateau", "d"): "water tower", ("tonneau", "vert"): "green barrel", ("bidon", "lait"): "milk can",
    ("metier", "a"): "loom", ("four", "a"): "bread oven", ("salon", "the"): "tea room", ("mont", "cassin"): "Monte Cassino",
    ("monte", "cassin"): "Monte Cassino", ("filet", "peche"): "fishing net", ("echoppe", "epices"): "spice stall",
    ("petit", "muret"): "low wall", ("en", "bois"): "wooden", ("de", "bois"): "wooden", ("maison", "ville"): "town house",
    ("plot", "beton"): "concrete bollard", ("borne", "incendie"): "fire hydrant", ("muret", "a"): "low wall A", ("muret", "pierre"): "stone wall", ("pierre", "cultures"): "field-stone",
}

WORDS = {
    # trees, plants, crops
    "arbre": "tree", "arbres": "trees", "bouleau": "birch", "chene": "oak", "charme": "hornbeam",
    "chataigner": "chestnut tree", "hetre": "beech", "orme": "elm", "epicea": "spruce", "sapin": "fir", "cypres": "cypress",
    "olivier": "olive tree", "oranger": "orange tree", "pommier": "apple tree", "figuier": "fig tree", "palmier": "palm",
    "palmiers": "palms", "buisson": "bush", "veget": "bush", "herbe": "grass", "herbes": "grasses", "roseaux": "reeds",
    "lavande": "lavender", "salade": "lettuce", "vigne": "vine", "vignes": "vineyard", "fleurs": "flowers",
    "fleur": "flower", "tige": "stem", "tete": "head", "bles": "wheat", "cultures": "crops", "champs": "field",
    "vegetaux": "plants", "vegetauxsur": "plants on", "eau": "water", "marais": "marsh", "rosier": "rose bush",
    "feuilles": "leaves", "coupe": "cut", "olives": "olives", "olive": "olive", "oranges": "oranges",
    "aoranges": "orange", "pommes": "apples", "piment": "chili peppers", "foin": "hay", "paille": "straw",
    "fagot": "bundle of sticks", "buches": "logs", "rondins": "logs", "bois": "wood", "osier": "wicker",
    "rocher": "rock", "rochelow": "low rock", "rochemax": "big rock", "rocaille": "rockery", "caillou": "pebble",
    "pierre": "stone", "pierres": "stones", "terre": "earth", "sable": "sand", "sol": "ground",
    # farm and animals
    "ferme": "farm", "grange": "barn", "grangeardennes": "barn", "grangedebois": "wooden barn", "etable": "cowshed",
    "etables": "cowsheds", "ecurie": "stable", "porcherie": "pigsty", "clapier": "rabbit hutch", "moulin": "mill",
    "meule": "haystack", "stockfoin": "hay store", "silo": "silo", "puits": "well", "puit": "well",
    "abreuvoir": "drinking trough", "charue": "plough", "charette": "cart", "charrette": "cart", "cariole": "cart",
    "caleche": "carriage", "brouette": "wheelbarrow", "tracteur": "tractor", "fourche": "pitchfork", "pelle": "shovel",
    "rateau": "rake", "hache": "axe", "fleau": "flail", "faux": "scythe", "serpe": "billhook", "seau": "bucket",
    "arrosoir": "watering can", "epouventail": "scarecrow", "fumier": "manure", "outils": "tools",
    "vache": "cow", "cheval": "horse", "horse": "horse", "mulet": "mule", "chevre": "goat", "mouton": "sheep",
    "cochon": "pig", "poule": "hen", "chien": "dog", "dromadaire": "camel", "berger": "shepherd", "lait": "milk",
    "bidonlait": "milk can", "panier": "basket", "paniers": "baskets", "linge": "washing", "draps": "sheets",
    # buildings
    "maison": "house", "maisonville": "town house", "petitemaison": "small house", "grandemaison": "big house",
    "house": "house", "cottage": "cottage", "batiment": "building", "batimentporche": "building with porch",
    "batisse": "big house", "eglise": "church", "church": "church", "chateau": "castle", "chateaudeau": "water tower",
    "mairie": "town hall", "ecole": "school", "cafe": "café", "kofeeshop": "coffee shop", "salonthe": "tea room",
    "gare": "station", "hangar": "hangar", "hangard": "hangar", "entrepot": "warehouse",
    "entrepotardennes": "warehouse", "depot": "depot", "store": "shop", "market": "market", "marche": "market",
    "echoppe": "stall", "kiosque": "kiosk", "cordonnerie": "shoemaker's", "tannerie": "tannery",
    "pigeonnier": "dovecote", "cabane": "hut", "cabanon": "shed", "abri": "shelter", "toit": "roof", "toits": "roofs",
    "colombages": "half-timbered", "devanture": "shop front", "enseigne": "shop sign", "porte": "door",
    "door": "door", "portail": "gate", "portal": "gate", "entree": "entrance", "entrance": "entrance",
    "escalier": "stairs", "stairway": "stairs", "etage": "upper floor", "fondation": "foundation", "arche": "arch",
    "arches": "arches", "arch": "arch", "coupole": "dome", "cloitre": "cloister", "colonne": "column",
    "minaret": "minaret", "phare": "lighthouse", "tour": "tower", "tower": "tower", "mirador": "watchtower",
    "muraille": "rampart", "mur": "wall", "muret": "low wall", "wall": "wall", "stonewall": "stone wall",
    "barriere": "fence", "loture": "fence", "cloture": "fence", "piquet": "fence post", "poteau": "post",
    "post": "post", "plot": "bollard", "plots": "bollards", "borne": "milestone", "monument": "monument",
    "memorial": "memorial", "tombe": "grave", "tomb": "grave", "fontaine": "fountain", "fountain": "fountain",
    "administration": "administration", "administratif": "administrative", "caserne": "barracks",
    "baraquement": "barracks", "barak": "barracks", "qg": "headquarters", "hq": "headquarters",
    "factory": "factory", "factorytank": "tank factory", "fact": "factory", "bunker": "bunker", "casse": "broken",
    "ruine": "ruin", "ruins": "ruins", "quai": "quay", "port": "port", "ponton": "pontoon", "pont": "bridge",
    "bridge": "bridge", "berge": "riverbank", "couloir": "corridor", "structure": "structure",
    "colisee": "colosseum", "cheminee": "chimney", "transformateur": "transformer", "eoliene": "wind pump",
    # town props
    "banc": "bench", "chaise": "chair", "table": "table", "tabouret": "stool", "pliant": "folding", "lit": "bed",
    "lampadaire": "street lamp", "lampe": "lamp", "murale": "wall", "sirene": "siren", "panneau": "sign",
    "tenturesuspendues": "hanging drapes", "toile": "canvas", "tendue": "stretched", "tendus": "stretched",
    "suspendue": "hanging", "suspendus": "hanging", "parasol": "parasol", "pare": "sun", "soleil": "shade",
    "jarre": "jar", "amphore": "amphora", "pot": "pot", "tonneau": "barrel", "tonneauvert": "green barrel",
    "caisse": "crate", "caissen": "crates", "malle": "trunk", "valise": "suitcase", "bidon": "can",
    "bidons": "cans", "huile": "oil", "jerrican": "jerrycan", "jerricans": "jerrycans", "citerne": "tank",
    "gazol": "diesel", "fuel": "fuel", "sac": "bag", "sacs": "bags", "sacsable": "sandbag", "tas": "pile",
    "planches": "planks", "planche": "plank", "clouees": "nailed", "echelle": "ladder",
    "echaffaudage": "scaffolding", "corde": "rope", "cordages": "ropes", "chaine": "chain", "chain": "chain",
    "tuyau": "pipe", "cables": "cables", "fil": "wire", "electrique": "electric", "electric": "electric",
    "elec": "electric", "metallique": "metal", "metal": "metal", "beton": "concrete", "betons": "concrete",
    "briques": "bricks", "gravats": "rubble", "dechets": "rubbish", "coussin": "cushion", "tapis": "carpet",
    "epice": "spice", "epices": "spices", "poissons": "fish", "thon": "tuna", "pain": "bread", "biere": "beer",
    "rotissoire": "spit roast", "poele": "stove", "four": "oven", "fourapain": "bread oven",
    "baignoire": "bathtub", "bassine": "basin", "balai": "broom", "machine": "machine", "presse": "press",
    "metier": "loom", "tisser": "weaving", "grue": "crane", "montecharge": "goods lift", "tramway": "tram",
    "velo": "bicycle", "tricycle": "tricycle", "tricyclebordeaux": "tricycle, wine red",
    "tricyclecreme": "tricycle, cream", "roue": "wheel", "pneu": "tyre", "musique": "music",
    "carcasse": "wreck", "deco": "decoration", "reclames": "adverts", "filet": "net", "peche": "fishing",
    "barque": "rowing boat", "peniche": "barge", "barge": "barge", "incendie": "fire",
    # vehicles and military
    "camion": "truck", "fourgon": "van", "voiture": "car", "car": "car", "cart": "cart", "remorque": "trailer",
    "decapotable": "convertible", "traction": "Traction Avant", "avant": "(front-drive)", "topolino": "Topolino",
    "fiat": "Fiat", "opel": "Opel", "blitz": "Blitz", "gmc": "GMC", "jeep": "jeep", "willys": "Willys",
    "kubelwagen": "Kübelwagen", "dovunque": "Dovunque", "carro": "tank", "tank": "tank", "panzer": "Panzer",
    "sherman": "Sherman", "stuart": "Stuart", "pershing": "Pershing", "chafee": "Chaffee", "lee": "Lee",
    "cromwell": "Cromwell", "matilda": "Matilda", "sdk": "Sd.Kfz.", "fz": "", "iii": "III", "iv": "IV",
    "avion": "plane", "canon": "gun", "artillerie": "artillery", "dca": "anti-aircraft", "bazooka": "bazooka",
    "fusil": "rifle", "casque": "helmet", "munitions": "ammunition", "ammo": "ammunition", "wpn": "weapons",
    "mg": "machine gun", "nest": "nest", "barbele": "barbed wire", "barbeles": "barbed wire",
    "herisson": "hedgehog", "tcheque": "(Czech)", "defense": "defence", "def": "defence", "position": "position",
    "checkpoint": "checkpoint", "camo": "camouflage", "tente": "tent", "materiel": "equipment",
    "mobilier": "furniture", "militaire": "military", "radio": "radio", "antenna": "antenna",
    "generator": "generator", "generateur": "generator", "power": "power", "command": "command",
    "research": "research", "intel": "intelligence", "infantry": "infantry", "pad": "pad", "pharma": "medical",
    "brancard": "stretcher", "boite": "box", "paper": "papers", "bottes": "boots", "trapeacharbon": "coal hatch",
    "corps": "body",
    # shapes, parts, colours, sizes
    "angle": "corner", "corner": "corner", "coin": "corner", "droit": "straight", "straight": "straight",
    "droite": "right", "right": "right", "gauche": "left", "left": "left", "courbe": "curved",
    "milieu": "middle", "millieu": "middle", "center": "middle", "bout": "end", "fin": "end", "debut": "start",
    "partie": "part", "part": "part", "morceau": "piece", "section": "section", "ensemble": "set", "groupe": "group",
    "bordure": "edge", "bas": "low", "haut": "high", "haute": "high", "long": "long", "petit": "small",
    "petite": "small", "little": "small", "small": "small", "grand": "big", "grande": "big", "big": "big",
    "moyen": "medium", "medium": "medium", "vieil": "old", "vieille": "old", "vieux": "old", "plat": "flat",
    "carre": "square", "rond": "round", "ouvert": "open", "ouverte": "open", "close": "closed", "vide": "empty",
    "empiles": "stacked", "couche": "lying", "couchee": "lying", "renverse": "overturned",
    "couvrenverse": "lid overturned", "retournee": "upturned", "roule": "rolled", "ecroule": "collapsed",
    "dest": "destroyed", "detruit": "destroyed", "detuit": "destroyed", "rouge": "red", "red": "red",
    "vert": "green", "verts": "green", "bleu": "blue", "blanc": "white", "blanche": "white", "white": "white",
    "jaune": "yellow", "jaunes": "yellow", "gris": "grey", "brun": "brown", "marron": "brown", "beige": "beige",
    "orange": "orange", "violet": "purple", "clair": "light", "bright": "bright", "sec": "dry", "charge": "loaded",
    "sans": "without", "couv": "lid", "type": "type", "bis": "bis", "generique": "generic", "base": "base",
    "propsbase": "", "plateau": "flat-bed", "range": "row", "run": "run", "walk": "walkway", "stand": "stand",
    "bloc": "block", "x": "x", "chaise_": "chair", "loin": "far", "nu": "bare", "grid": "grille",
    "cher": "Cher", "bourg": "bourg", "el": "El", "djem": "Djem", "pieu": "stake", "bar": "bar", "place": "square",
    "farm": "farm", "town": "town", "village": "village", "ville": "town", "german": "German",
    "en": "in", "de": "of", "et": "and", "au": "on the", "pour": "for", "sur": "on", "com": "comms",
    "ent": "entrance", "bat": "building", "routier": "road", "parc": "park", "tangeant": "", "floor": "with walkable deck",
    "mont": "Mount", "monte": "Monte", "cassin": "Cassino", "stone": "stone", "barbarie": "prickly", "bac": "tub",
    "cargo": "cargo", "cana": "Cana", "bitume": "asphalt",
}

# region and theatre words: shown after the name, in brackets
REGIONS = {
    "cotentin": "Cotentin", "normandie": "Normandy", "normande": "Normandy", "cherbourg": "Cherbourg",
    "italie": "Italy", "ita": "Italy", "tunisie": "Tunisia", "hollande": "Holland", "arnhem": "Arnhem",
    "ardennes": "Ardennes", "ardennnes": "Ardennes", "allemagne": "Germany", "ger": "Germany", "france": "France",
    "fr": "France", "eu": "Europe", "us": "US", "uk": "UK", "urss": "USSR", "colditz": "Colditz",
    "coc": "", "kasserine": "Kasserine",
}

# what the game's editor files a type under (its Classement), last folder first
KINDS = [("arbres", "tree"), ("buissons", "bush"), ("cultures", "crop"), ("fleurs", "flowers"), ("divers", "plant"),
         ("murets", "wall"), ("cimetiere", "cemetery"), ("reclames", "shop front"), ("outils", "farm tool"),
         ("animaux", "animal"), ("vehicules", "vehicle"), ("mobiliermilitaire", "military"), ("ponts", "bridge"),
         ("barrieres", "fence"), ("clotures", "fence"), ("landmarks", "landmark"), ("toits", "roof"),
         ("dest", "destroyed"), ("batiments_fermes", "farm building"), ("batiments_villes", "town building"),
         ("batiments_ville", "town building"), ("batimentsvillage", "village building"),
         ("batiments_cherbourg", "town building"), ("batiments_plages", "beach building"),
         ("batimentsmorceaux", "building piece"), ("petitsbatiments", "small building"), ("montcassin", "landmark"),
         ("detailsol", "ground detail"), ("objets fleuve", "river object"), ("ferme", "farm prop"),
         ("ville", "town prop"), ("givre", "winter prop"), ("vegetation", "plant"), ("props", "prop"),
         ("decors", "prop")]

ADJECTIVES = {"dry", "wooden", "stretched", "stacked", "nailed", "open", "empty", "old", "flat", "broken", "lying",
              "overturned", "upturned", "rolled", "collapsed", "loaded", "low", "high", "long", "light", "generic", "big",
              "small", "medium", "curved", "square", "round", "hanging", "folding", "red", "green", "blue", "white",
              "yellow", "grey", "brown", "beige", "orange", "purple", "bright", "metal", "concrete", "electric",
              "military", "closed", "tall"}

_TOKENS = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+")


def words(code: str) -> list[str]:
    """A code name's words as they're written (digits kept): "Cotentin_PanierOsier1" -> Cotentin Panier Osier 1."""
    return _TOKENS.findall(code.replace("_", " "))


def unknown(code: str) -> list[str]:
    """The words of a code name no table knows (empty: it reads in English)."""
    out = []
    for w in words(code):
        low = w.lower()
        if not (w.isdigit() or len(w) == 1 or low in WORDS or low in REGIONS):
            out.append(w)
    return out


def kind(category: str) -> str:
    """What a type is, from the game editor's folder for it ("Vegetation/Arbres" -> "tree")."""
    c = (category or "").lower().replace("\\", "/")
    parts = [p for p in c.split("/") if p]
    for p in reversed(parts):
        for key, name in KINDS:
            if p == key or p.startswith(key):
                return name
    return ""


def plain(code: str, category: str = "") -> str:
    """A type's name in English: "Cotentin_PanierOsier1" -> "Wicker basket 1 (Cotentin)", "Bouleau_02_G" ->
    "Birch 2, winter look", "veget_EU_022" -> "Bush 22 (Europe)". Words no table knows stay as they are."""
    ws = words(code)
    winter = len(ws) > 1 and ws[-1] in ("G", "g")  # _G: the winter maps' frosted copy (filed under Givre, frost)
    if winter:
        ws = ws[:-1]
    out, regions, i = [], [], 0
    while i < len(ws):
        w, low = ws[i], ws[i].lower()
        pair = (low, ws[i + 1].lower()) if i + 1 < len(ws) else None
        if pair in PHRASES:
            out.append(PHRASES[pair])
            i += 2
            continue
        if low in REGIONS:
            if REGIONS[low] and REGIONS[low] not in regions:
                regions.append(REGIONS[low])
        elif w.isdigit():
            out.append(str(int(w)))
        elif len(w) == 1:
            out.append(w.upper())
        elif low in WORDS:
            if WORDS[low]:
                out.append(WORDS[low])
        else:
            out.append(w)
        i += 1
    for k in range(1, len(out)):  # French puts most adjectives after the noun: "Buisson sec" -> "Dry bush"
        if out[k] in ADJECTIVES and out[k - 1] not in ADJECTIVES and not out[k - 1].isdigit() and len(out[k - 1]) > 1:
            out[k - 1], out[k] = out[k], out[k - 1]
    text = " ".join(out).strip() or code
    text = re.sub(r"\s+", " ", text)
    text = text[0].upper() + text[1:]
    if winter:
        text += ", winter look"
    if regions:
        text += f" ({', '.join(regions)})"
    return text
