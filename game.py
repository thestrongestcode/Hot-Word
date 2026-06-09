import streamlit as st
from streamlit_autorefresh import st_autorefresh
import json
import os
import re
import contextlib
import time
import random
import string
import math
import unicodedata
import html

# ─── Constants ────────────────────────────────────────────────────────────────

WORDS_FILE         = "words_alpha.txt"
SPANISH_WORDS_FILE = "words_spanish.txt"
FRENCH_WORDS_FILE  = "words_french.txt"
ROOMS_DIR          = "rooms"
STARTING_TIMER     = 30
MIN_TURN_FLOOR     = 5
TIMER_SHRINK       = 2
MIN_STARTING_TIMER = 8
LIVES              = 3
ROOM_EXPIRY        = 300
REMATCH_TIMEOUT    = 15

ROOM_CODE_RE = re.compile(r"^(P-)?[A-Z]{4}$")

def is_valid_room_code(code):
    return bool(ROOM_CODE_RE.fullmatch(str(code).strip().upper()))


# ─── English combos ───────────────────────────────────────────────────────────

EASY_COMBOS = [
    "TH","CH","SH","TR","PR","BR","CR","ST","SP","SK",
    "LY","FT","ER","NT","ND","ES","EN","OU","GH","WH",
    "IN","AN","ON","TI","AT","TE","AL","RA","AR","RE",
    "LE","IC","IS","RI","NE","OR","LI","RO","IT","LA",
    "CA","CO","MA","IO","TO","TA","DE","SS","ME","NG",
    "US","IA","LO","EL","NI","HE","OL","SE","IL","NA",
    "ET","LL","SI","PE","AC","DI","AS","MI","ED","VE",
    "HA","OM","HO","CE","EA","UR","NO","GE","UN","HI",
    "AM","OS","MO","PH","AB","UL","OT","PA","EC","NC",
]

MEDIUM_COMBOS = [
    "ING","NCE","STR","GHT","OUN","PLE","ENT","OUS","ATE","EAR",
    "OWN","AIN","EAD","OOK","ALL","ORT","OOD","EEL","ION","ARD",
    "ESS","TER","ATI","TIO","NES","IST","INE","TIC","ICA","ANT",
    "CAL","TOR","ALI","PER","MEN","CON","VER","ITY","BLE","MAN",
    "TRA","STI","ISM","IAN","LIT","RAT","AND","HER","LIN","TRI",
    "GRA","ERI","ABL","STE","RAN","TIN","THE","ENE","ATO","ARI",
    "DER","NTI","IVE","ERA","RES","NTE","LAT","STA","OLO","LOG",
    "ONI","EST","ILL","PRO","AST","RIN","ONA","INT","MIN","ILI",
]

HARD_COMBOS = [
    "SCR","THR","NCH","TCH","QUA","DGE","SQU","NGU","NGL",
    "MBL","CKL","RPH","NGS","STH","NDL","PSY","GNI","MPT","LVE","XTR","PHR",
    "SPL","STL","GGL","RCH","NST","RST","NTH","SKI","NCL","NCT","RSH",
    "TION","NESS","ATIO","ICAL","ABLE","OLOG","MENT","ATOR","LITY","INES",
    "STIC","OVER","NTER","ENES","STER","RAPH","TIVE","GRAP","OGRA","NDER",
    "ILIT","LESS","TING","IONA","INTE","THER","ALLY","ALIS","TICA","ONAL",
    "ISTI","BILI","ANTI","LOGI","ENCE","IOUS","RATI","IGHT","ANCE","ETER",
    "LIST","SION","TRIC","TATI","LING","RING","ROUS","ENTA","ICAT","MATI",
    "STRA","TORY","ABIL","ATIC","CENT","UNDE","INAT","LECT","ERAT","RESS",
    "LAND","IZAT","TRAN","RIAN","NIST","EMEN","TTER","RIST","ALIZ","ECTI",
    "COMP","OMET","ULAT","NISM","EOUS","NATE","CULA","ETIC","PRES","OGEN",
    "CONS","ATIV","PARA","FORM","LISM","RANS","ULAR","ONIC","LIZE","METE",
    "ARCH","CONT","MINA","SHIP","HEAD","TABL","COMM","ACTI","DING","KING",
    "SIVE","SCEN","STRI","OUND","ANIS","NALI","ELEC","ETTE","RIAL",
]

# ─── Spanish combos ───────────────────────────────────────────────────────────

SPANISH_EASY_COMBOS = [
    "DE","ES","EN","EL","LA","LO","LE","LAS","LOS","UN",
    "AR","ER","IR","OR","AL","AN","IN","ON","AS","OS",
    "IA","IO","IE","EI","AI","AU","EU","UA","UE","UI",
    "CA","CE","CI","CO","CU","GA","GE","GI","GO","GU",
    "RA","RE","RI","RO","TA","TE","TI","TO","SA","SE",
    "SI","SO","PA","PE","PI","PO","MA","ME","MI","MO",
    "NA","NE","NI","NO","DA","DE","DI","DO","VA","VE",
    "VI","VO","PR","TR","BR","CR","GR","PL","CL","BL",
    "FL","FR","DR","CH","LL","QU","RR","NT","ST","ND",
]

SPANISH_MEDIUM_COMBOS = [
    "CON","DES","ENT","EST","QUE","ACI","ION","ADO","ADA","IDO",
    "IDA","ERA","ERO","OSA","OSO","ANT","PAR","PRO","PRE","TRA",
    "TER","ARI","RIA","RIO","INA","INO","ELA","ELO","ALE","ARA",
    "ORE","RES","COM","MEN","PER","STA","TAR","CAR","CER","CIR",
    "DAD","BLE","BRE","BRA","CLA","CLO","CRE","CRI","DOR","DRA",
    "DRO","GRA","GRO","MAR","MER","MOR","NTE","NTO","RON","SAR",
    "SER","SIO","TAD","TOS","TOR","TUR","VAL","VAR","VEN","VER",
    "VID","VIR","CAL","COL","COR","CUR","GEN","GER","GIN","NAL",
    "LES","LAS","LOS","NES","DOS","DAS","MOS","MIS","SOL","SAL",
]

SPANISH_HARD_COMBOS = [
    "CION","ACION","NCIA","ANTE","ENTE","MENT","MIEN","IENT","ADOR","ABLE",
    "IBLE","ISTA","ISMO","ARIO","ARIA","ERIA","IDAD","EDAD","ADES","ALES",
    "ADOS","ADAS","IDOS","IDAS","ORES","ORAS","EROS","ERAS","OSOS","OSAS",
    "CONS","CONT","COMP","COND","CONF","CONV","CONC","CONO","CORA","CORD",
    "DESA","DESC","DESP","DEST","DERE","DIST","DISP","DICI","DORA","DURA",
    "PREN","PRES","PRET","PRED","PROC","PROD","PROP","PROF","PROM","PROV",
    "PRIM","TRAN","TRAS","TRAC","TRES","TRIB","TRON","ESTA","ESTE","ESTI",
    "ESTO","ESTR","ENTA","ENTO","ANTI","ANCI","ARIO","ARIA","INTE","INTR",
    "INCI","INDI","INFO","INST","INSP","INFL","IMPR","EXTR","EXPE","EXPR",
    "EXIS","SUBS","SOBR","SENT","SENC","SERV","SEGU","CIEN","CIAS","CIOS",
    "CIAL","CION","TICA","TICO","TURA","SION","RACI","LACI","DOCI","NACI",
]

# ─── French combos ────────────────────────────────────────────────────────────

FRENCH_EASY_COMBOS = [
    "DE","LE","RE","ES","EN","ON","OU","AI","AN","ER",
    "NT","TE","LA","SE","ME","NE","EL","ET","IT","IE",
    "QU","CH","AU","EU","OI","UI","IN","IS","AR","OR",
    "IL","CE","UN","US","VE","MA","TA","RA","SA","LI",
    "UR","UT","AV","VO","FA","FI","RO","LO","PE","PL",
    "GR","BR","TR","DR","PR","CR","CL","BL","FL","FR",
    "GN","GE","GI","GA","GO","GU","AM","EM","OM","IM",
    "AC","EC","OC","UC","AP","EP","OP","UP","RS","RT",
    "ST","SP","SC","SM","SN","SL","NC","ND","NG","NS",
]

FRENCH_MEDIUM_COMBOS = [
    "ENT","QUE","ION","LES","DES","AIT","EUR","ANT","OUR","DAN",
    "PAR","COM","TRA","TIO","MEN","TER","RES","CON","PRO","ATI",
    "EST","UNE","AVA","ELA","IRE","OUS","TRE","NTE","AGE","AIS",
    "SON","NCE","USE","EAU","AIL","OIR","TRE","LLE","ATI","IER",
    "EUR","EME","AIS","AIT","ONS","ONT","ERA","ERE","EES","EUX",
    "AUX","CHE","CHA","CHO","CHE","ECH","GNE","IGN","TTE","RAI",
    "RON","RAN","TIN","RIS","RIE","NTE","NTS","TES",
]

FRENCH_HARD_COMBOS = [
    "TION","MENT","IQUE","ABLE","AIRE","ELLE","ENCE","EUSE",
    "ISME","OIRE","ATION","EMENT","ANTE","ENTE","IONS",
    "IVES","ALES","ELLES","TEUR","TRICE","AINS","AINE",
    "EAUX","ERIE","ERES","ETTE","ETTES","DANS","POUR",
    "AVEC","PLUS","TOUS","TOUT","PRES","VERS","SEUL","MAIN",
    "MENT","ISTE","TION","SION","ANCE","ENCE",
    "IQUE","OIRE","AIRE","IBLE","ABLE",
]

# ─── Bad words filter ─────────────────────────────────────────────────────────

BAD_WORDS = {
    "fuck","shit","cunt","cock","dick","ass","bitch","bastard","damn","crap",
    "piss","fag","slut","whore","nigger","nigga","retard","faggot","twat",
    "joder","mierda","puta","puto","coño","cono","hostia","cabron","cabrón",
    "polla","culo","gilipollas","capullo","follar","verga","pendejo","chinga",
    "chingada","cagar","cagada","maricon","maricón","mamada","mamadas",
    "chingadera","chingaderas","putada","putadas","putazo","putazos",
    "hijoputa","hijoputas","me cago","ostia",
    "pene","ano","prostituta","zorra","perra","subnormal","retrasado",
    "imbecil","estupido","idiota","mongolo",
    "merde","putain","connard","salope","connasse","foutre","enculer","baiser",
    "chier","cul","bite","couille","couilles","couillon","nichons","nichon",
    "bordel","branler","branleur","pédé","pede","nique","niquer","va te faire",
}

NORMALIZED_BAD_WORDS = None

def is_bad_word(word):
    return normalize(word) in NORMALIZED_BAD_WORDS

# ─── Accent normalization ─────────────────────────────────────────────────────

def normalize(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )

NORMALIZED_BAD_WORDS = {normalize(w) for w in BAD_WORDS}

def esc(s):
    return html.escape(str(s), quote=True)

# ─── Word validation ──────────────────────────────────────────────────────────

@st.cache_resource
def load_words():
    english = set()
    spanish = set()
    french  = set()

    if not os.path.exists(WORDS_FILE):
        st.error(f"Missing required word list: {WORDS_FILE}")
        return english, spanish, french

    with open(WORDS_FILE, encoding="utf-8") as f:
        for w in f:
            word = w.strip().lower()
            if word:
                english.add(word)

    if os.path.exists(SPANISH_WORDS_FILE):
        with open(SPANISH_WORDS_FILE, encoding="utf-8") as f:
            for w in f:
                word = w.strip().lower()
                if word:
                    spanish.add(word)
                    spanish.add(normalize(word))

    if os.path.exists(FRENCH_WORDS_FILE):
        with open(FRENCH_WORDS_FILE, encoding="utf-8") as f:
            for w in f:
                word = w.strip().lower()
                if word:
                    french.add(word)
                    french.add(normalize(word))

    return english, spanish, french

def is_valid_play(word, combo, used_words, language="en"):
    w          = word.lower().strip()
    w_norm     = normalize(w)
    combo_norm = normalize(combo.lower())

    if not w:
        if language == "fr":
            return False, "Veuillez saisir un mot."
        return False, "Type a word first." if language == "en" else "Escribe una palabra primero."

    if is_bad_word(w):
        if language == "fr":
            return False, "Ce mot est inapproprié. Veuillez saisir une réponse adéquate."
        return False, ("That word is inappropriate. Please enter an appropriate response."
                       if language == "en" else
                       "Esa palabra es inapropiada. Por favor escribe una respuesta adecuada.")

    if combo_norm not in w_norm:
        if language == "fr":
            return False, f'"{word}" ne contient pas "{combo}".'
        return False, (f'"{word}" doesn\'t contain "{combo}".' if language == "en"
                       else f'"{word}" no contiene "{combo}".')

    english, spanish, french = load_words()

    if language == "es":
        valid_word = w in spanish or w_norm in spanish
    elif language == "fr":
        valid_word = w in french or w_norm in french
    else:
        valid_word = w in english

    if not valid_word:
        if language == "fr":
            return False, f'"{word}" n\'est pas un mot valide.'
        return False, (f'"{word}" isn\'t a valid word.' if language == "en"
                       else f'"{word}" no es una palabra válida.')

    if w_norm in [normalize(u) for u in used_words]:
        if language == "fr":
            return False, f'"{word}" a déjà été utilisé.'
        return False, (f'"{word}" was already used.' if language == "en"
                       else f'"{word}" ya fue usada.')

    return True, "ok"

# ─── Combo selection ──────────────────────────────────────────────────────────

def pick_combo(round_num, used_combos, language="en"):
    if language == "fr":
        if round_num <= 5:
            pool = FRENCH_EASY_COMBOS
        elif round_num <= 12:
            pool = FRENCH_EASY_COMBOS + FRENCH_MEDIUM_COMBOS
        else:
            pool = FRENCH_MEDIUM_COMBOS + FRENCH_HARD_COMBOS
    elif language == "es":
        if round_num <= 5:
            pool = SPANISH_EASY_COMBOS
        elif round_num <= 12:
            pool = SPANISH_EASY_COMBOS + SPANISH_MEDIUM_COMBOS
        else:
            pool = SPANISH_MEDIUM_COMBOS + SPANISH_HARD_COMBOS
    else:
        if round_num <= 5:
            pool = EASY_COMBOS
        elif round_num <= 12:
            pool = EASY_COMBOS + MEDIUM_COMBOS
        else:
            pool = MEDIUM_COMBOS + HARD_COMBOS

    available = [c for c in pool if c not in used_combos]
    if not available:
        available = pool
    return random.choice(available)

# ─── File lock ────────────────────────────────────────────────────────────────

@contextlib.contextmanager
def room_file_lock(code, timeout=3.0, poll_interval=0.05):
    code = str(code).strip().upper()
    if not is_valid_room_code(code):
        raise ValueError("Invalid room code.")
    os.makedirs(ROOMS_DIR, exist_ok=True)
    lock_path = os.path.join(ROOMS_DIR, f"{code}.lock")
    start = time.time()
    fd = None
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            break
        except FileExistsError:
            if time.time() - start > timeout:
                raise TimeoutError("Room is busy. Try again.")
            time.sleep(poll_interval)
    try:
        yield
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.remove(lock_path)
        except FileNotFoundError:
            pass

def mutate_room(code, mutator):
    with room_file_lock(code):
        state = load_room(code)
        if state is None:
            return None
        mutator(state)
        save_room(code, state)
        return state

# ─── Room helpers ─────────────────────────────────────────────────────────────

def room_path(code):
    code = str(code).strip().upper()
    if not is_valid_room_code(code):
        raise ValueError("Invalid room code.")
    os.makedirs(ROOMS_DIR, exist_ok=True)
    return os.path.join(ROOMS_DIR, f"{code}.json")

def load_room(code):
    p = room_path(code)
    if not os.path.exists(p):
        return None
    for _ in range(3):
        try:
            with open(p) as f:
                content = f.read()
            if not content.strip():
                time.sleep(0.05)
                continue
            return json.loads(content)
        except (json.JSONDecodeError, OSError):
            time.sleep(0.05)
    return None

def save_room(code, state):
    p = room_path(code)
    tmp = p + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, p)
    except OSError:
        with open(p, "w") as f:
            json.dump(state, f)

def create_room(code, name, private, same_device=False, player2_name=None):
    players = [{"name": name, "lives": LIVES, "alive": True}]
    if same_device and player2_name:
        players.append({"name": player2_name, "lives": LIVES, "alive": True})
    state = {
        "players": players,
        "host": name, "is_private": private,
        "started": False, "finished": False, "winner": None,
        "current_player_idx": 0, "current_combo": "",
        "used_combos": [], "used_words": [], "round": 1,
        "timer_start": None, "timer_duration": STARTING_TIMER,
        "last_message": "", "created_at": time.time(),
        "language": "en",
        "same_device": same_device,
        "rematch_votes": [],
        "rematch_deadline": None,
        "rematch_started": False,
    }
    save_room(code, state)
    return state

def join_room(code, name):
    state = load_room(code)
    if state is None:         return None, "Room not found."
    if state["started"]:      return None, "Game already started."
    if state.get("same_device"): return None, "This is a same-device room."
    existing_names = [p["name"].strip().casefold() for p in state["players"]]
    if name.strip().casefold() in existing_names:
                              return None, "Name already taken."
    if len(state["players"]) >= 8:
                              return None, "Room is full (max 8)."
    state["players"].append({"name": name, "lives": LIVES, "alive": True})
    save_room(code, state)
    return state, "ok"

def gen_code(private=False):
    return ("P-" if private else "") + "".join(random.choices(string.ascii_uppercase, k=4))

def gen_unique_code(private=False):
    for _ in range(20):
        code = gen_code(private)
        if not os.path.exists(room_path(code)):
            return code
    raise RuntimeError("Could not generate a unique room code after 20 attempts.")

def leave_room(code, name):
    state = load_room(code)
    if state is None: return
    if state["host"] == name:
        p = room_path(code)
        if os.path.exists(p): os.remove(p)
    else:
        state["players"] = [p for p in state["players"] if p["name"] != name]
        save_room(code, state)

def kick_player(code, host_name, target_name):
    state = load_room(code)
    if state is None: return False, "Room not found."
    if state["host"] != host_name: return False, "Only the host can kick."
    if state.get("started"): return False, "Can't kick after game starts."
    if target_name == host_name: return False, "Can't kick yourself."
    state["players"] = [p for p in state["players"] if p["name"] != target_name]
    save_room(code, state)
    return True, "ok"

def set_room_language(code, language):
    state = load_room(code)
    if state is None: return False
    state["language"] = language
    save_room(code, state)
    return True

def cleanup_rooms():
    if not os.path.exists(ROOMS_DIR): return
    now = time.time()
    for fname in os.listdir(ROOMS_DIR):
        if not fname.endswith(".json"): continue
        p = os.path.join(ROOMS_DIR, fname)
        try:
            with open(p) as f:
                s = json.load(f)
            if s.get("finished"):
                deadline = s.get("rematch_deadline")
                if deadline and now > deadline + 5:
                    os.remove(p)
                continue
            if not s.get("started") and now - s.get("created_at", now) > ROOM_EXPIRY:
                os.remove(p); continue
            if s.get("started") and s.get("timer_start") and now - s["timer_start"] > 600:
                os.remove(p)
        except Exception:
            pass

def list_public_rooms():
    cleanup_rooms()
    if not os.path.exists(ROOMS_DIR): return []
    rooms = []
    for fname in os.listdir(ROOMS_DIR):
        if not fname.endswith(".json"): continue
        code = fname[:-5]
        try:
            s = load_room(code)
            if s is None: continue
            if not s.get("is_private") and not s.get("started") and not s.get("finished") and not s.get("same_device"):
                rooms.append({"code": code, "host": s["host"],
                               "players": len(s["players"]), "created_at": s.get("created_at", 0)})
        except Exception:
            continue
    return sorted(rooms, key=lambda r: r["created_at"], reverse=True)

# ─── Rematch helpers ──────────────────────────────────────────────────────────

def cast_rematch_vote(code, name):
    try:
        with room_file_lock(code):
            state = load_room(code)
            if state is None or not state.get("finished"):
                return state
            votes = state.get("rematch_votes", [])
            if name not in votes:
                votes.append(name)
                state["rematch_votes"] = votes
            save_room(code, state)
            return state
    except TimeoutError:
        return load_room(code)

def check_rematch_or_expire(code):
    try:
        with room_file_lock(code):
            state = load_room(code)
            if state is None:
                return None
            if not state.get("finished"):
                return state

            now      = time.time()
            deadline = state.get("rematch_deadline")
            votes    = state.get("rematch_votes", [])
            total    = len(state["players"])

            if deadline is None:
                state["rematch_deadline"] = now + REMATCH_TIMEOUT
                save_room(code, state)
                return state

            all_voted    = len(votes) == total
            enough_voted = len(votes) >= 2
            time_up      = now >= deadline

            if all_voted or (time_up and enough_voted):
                _reset_for_rematch(state)
                save_room(code, state)
                return state

            if time_up and not enough_voted:
                # For same-device: also allow single-player rematch vote
                if state.get("same_device") and len(votes) >= 1:
                    _reset_for_rematch(state)
                    save_room(code, state)
                    return state
                p = room_path(code)
                if os.path.exists(p):
                    os.remove(p)
                return None

            save_room(code, state)
            return state
    except TimeoutError:
        return load_room(code)

def _reset_for_rematch(state):
    for p in state["players"]:
        p["lives"] = LIVES
        p["alive"] = True
    lang  = state.get("language", "en")
    combo = pick_combo(1, [], lang)
    state.update(
        started=True,
        finished=False,
        winner=None,
        current_player_idx=0,
        current_combo=combo,
        used_combos=[combo],
        used_words=[],
        round=2,
        timer_start=time.time(),
        timer_duration=STARTING_TIMER,
        last_message="",
        rematch_votes=[],
        rematch_deadline=None,
        rematch_started=True,
    )

# ─── Game logic ───────────────────────────────────────────────────────────────

def alive_players(state):
    return [p for p in state["players"] if p["alive"]]

def start_game(code, state):
    lang = state.get("language", "en")
    combo = pick_combo(1, [], lang)
    state.update(
        started=True,
        current_combo=combo,
        used_combos=[combo],
        timer_start=time.time(),
        current_player_idx=0,
        round=2,
    )
    save_room(code, state)

def advance_turn_state(state, remaining_time):
    alive = alive_players(state)
    if len(alive) <= 1:
        return
    cur_name    = state["players"][state["current_player_idx"]]["name"]
    alive_names = [p["name"] for p in alive]
    cur_idx     = alive_names.index(cur_name) if cur_name in alive_names else 0
    next_name   = alive_names[(cur_idx + 1) % len(alive_names)]
    for i, p in enumerate(state["players"]):
        if p["name"] == next_name:
            state["current_player_idx"] = i
            break
    guaranteed = max(remaining_time, MIN_TURN_FLOOR)
    state["timer_start"] = time.time() - (state["timer_duration"] - guaranteed)
    lang  = state.get("language", "en")
    combo = pick_combo(state["round"], state["used_combos"], lang)
    state["current_combo"] = combo
    state["used_combos"].append(combo)
    state["round"] += 1

def check_timer_state(state):
    if not state["started"] or state["finished"]:
        return state

    elapsed = time.time() - state["timer_start"]
    if elapsed < state["timer_duration"]:
        return state

    lang  = state.get("language", "en")
    is_es = lang == "es"
    is_fr = lang == "fr"

    cp = state["players"][state["current_player_idx"]]
    cp["lives"] -= 1

    if cp["lives"] <= 0:
        cp["alive"] = False
        if is_fr:
            state["last_message"] = f'eliminated:{esc(cp["name"])} a été éliminé.'
        elif is_es:
            state["last_message"] = f'eliminated:{esc(cp["name"])} fue eliminado.'
        else:
            state["last_message"] = f'eliminated:{esc(cp["name"])} was eliminated.'
    else:
        if is_fr:
            lives_word = "vie" if cp["lives"] == 1 else "vies"
            state["last_message"] = f'timeout:{esc(cp["name"])} a manqué de temps — {cp["lives"]} {lives_word} restante{"" if cp["lives"] == 1 else "s"}.'
        elif is_es:
            lives_word = "vida" if cp["lives"] == 1 else "vidas"
            state["last_message"] = f'timeout:{esc(cp["name"])} se quedó sin tiempo — {cp["lives"]} {lives_word} restantes.'
        else:
            lives_word_en = "life" if cp["lives"] == 1 else "lives"
            state["last_message"] = f'timeout:{esc(cp["name"])} ran out of time — {cp["lives"]} {lives_word_en} left.'

    state["timer_duration"] = max(MIN_STARTING_TIMER, state["timer_duration"] - TIMER_SHRINK)

    alive = alive_players(state)

    if len(alive) == 1:
        state["finished"] = True
        state["winner"]   = alive[0]["name"]
    elif len(alive) == 0:
        state["finished"] = True
        state["winner"]   = "Personne" if is_fr else ("Nadie" if is_es else "Nobody")
    else:
        n_all          = len(state["players"])
        cur_global_idx = state["current_player_idx"]
        for offset in range(1, n_all + 1):
            candidate_idx = (cur_global_idx + offset) % n_all
            if state["players"][candidate_idx]["alive"]:
                state["current_player_idx"] = candidate_idx
                break
        combo = pick_combo(state["round"], state["used_combos"], lang)
        state["current_combo"] = combo
        state["used_combos"].append(combo)
        state["round"] += 1

    state["timer_start"] = time.time()
    return state

def check_timer(code, state=None):
    try:
        with room_file_lock(code):
            fresh_state = load_room(code)
            if fresh_state is None:
                return state
            check_timer_state(fresh_state)
            save_room(code, fresh_state)
            return fresh_state
    except TimeoutError:
        return state if state is not None else load_room(code)

def submit_word(code, state, name, word):
    try:
        with room_file_lock(code):
            fresh_state = load_room(code)
            if fresh_state is None:
                return state, "Room not found."
            if fresh_state.get("finished"):
                return fresh_state, "Game already finished."

            cp = fresh_state["players"][fresh_state["current_player_idx"]]
            if cp["name"] != name:
                lang = fresh_state.get("language", "en")
                if lang == "fr":
                    return fresh_state, "Ce n'est pas votre tour."
                return fresh_state, ("No es tu turno." if lang == "es" else "Not your turn.")

            lang = fresh_state.get("language", "en")
            valid, msg = is_valid_play(word, fresh_state["current_combo"],
                                       fresh_state["used_words"], lang)
            if not valid:
                return fresh_state, msg

            elapsed   = time.time() - fresh_state["timer_start"]
            remaining = max(0, fresh_state["timer_duration"] - elapsed)

            fresh_state["used_words"].append(normalize(word.lower()))

            if lang == "fr":
                fresh_state["last_message"] = f'good:{esc(name)} a joué "{esc(word)}"'
            elif lang == "es":
                fresh_state["last_message"] = f'good:{esc(name)} jugó "{esc(word)}"'
            else:
                fresh_state["last_message"] = f'good:{esc(name)} played "{esc(word)}"'

            advance_turn_state(fresh_state, remaining)
            save_room(code, fresh_state)
            return fresh_state, "ok"

    except TimeoutError:
        return state, "Room is busy. Try again."


# ─── CSS ─────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500&display=swap');

:root {
    --ink:    #0f0f0f;
    --paper:  #faf9f6;
    --amber:  #e8a020;
    --amber2: #fbbf24;
    --muted:  #888;
    --border: #e0ddd6;
    --card:   #ffffff;
    --danger: #c0392b;
    --success:#1a7a3f;
}

.stApp, [data-testid="stAppViewContainer"] {
    background: var(--paper) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--ink);
}
[data-testid="stHeader"], footer, header, #MainMenu { visibility: hidden; }

h1, h2, h3 { font-family: 'DM Serif Display', serif !important; color: var(--ink); }

.stTextInput input {
    background: var(--card) !important;
    color: var(--ink) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.55rem 0.9rem !important;
    transition: border-color 0.15s !important;
}
.stTextInput input:focus {
    border-color: var(--ink) !important;
    box-shadow: none !important;
}

.stButton button, [data-testid="stFormSubmitButton"] button {
    background: var(--ink) !important;
    color: var(--paper) !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 1.4rem !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.15s !important;
}
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    opacity: 0.82 !important;
}

.btn-ghost .stButton button {
    background: transparent !important;
    color: var(--ink) !important;
    border: 1.5px solid var(--border) !important;
}
.btn-ghost .stButton button:hover {
    border-color: var(--ink) !important;
    opacity: 1 !important;
}

.btn-amber .stButton button {
    background: var(--amber) !important;
    color: #3a1f00 !important;
}
.btn-amber .stButton button:hover {
    opacity: 0.88 !important;
}

.btn-rematch .stButton button {
    background: var(--amber) !important;
    color: #3a1f00 !important;
    font-size: 1rem !important;
    padding: 0.7rem 2rem !important;
}
.btn-rematch .stButton button:hover {
    opacity: 0.88 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1.5px solid var(--border);
    padding: 0;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: var(--muted);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    padding: 0.5rem 1.2rem;
    border-radius: 0;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    background: transparent !important;
    border-bottom: 2px solid var(--ink) !important;
    font-weight: 500 !important;
}

.stAlert { border-radius: 6px !important; font-family: 'DM Sans', sans-serif !important; }
.stCheckbox label { font-family: 'DM Sans', sans-serif !important; color: var(--ink) !important; }
hr { border-color: var(--border) !important; }

.wb-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3rem;
    color: var(--ink);
    letter-spacing: -0.02em;
    line-height: 1;
    margin-bottom: 0.2rem;
}
.wb-subtitle {
    font-family: 'DM Sans', sans-serif;
    color: var(--muted);
    font-size: 0.95rem;
    margin-bottom: 2rem;
}
.wb-section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.5rem;
}
.wb-room-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    margin-bottom: 0.4rem;
    background: var(--card);
}
.wb-room-code {
    font-family: 'DM Mono', monospace;
    font-size: 1rem;
    font-weight: 500;
    color: var(--ink);
    letter-spacing: 0.1em;
}
.wb-room-meta { font-size: 0.82rem; color: var(--muted); }
.wb-player-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 1rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 0.35rem;
    background: var(--card);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
}
.wb-lobby-code {
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    font-weight: 500;
    letter-spacing: 0.25em;
    color: var(--ink);
    background: var(--card);
    border: 1.5px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 1.5rem;
    display: inline-block;
    margin: 0.5rem 0;
}
.wb-msg {
    text-align: center;
    padding: 0.55rem 1rem;
    border-radius: 6px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 500;
    margin: 0.5rem 0 1rem;
    letter-spacing: 0.01em;
}
.wb-msg-good { background: #edf7f1; color: var(--success); border: 1px solid #b8dfc8; }
.wb-msg-bad  { background: #fdf0ee; color: var(--danger);  border: 1px solid #f0c4be; }
.wb-turn-label {
    text-align: center;
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--amber);
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.wb-waiting-label {
    text-align: center;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    color: var(--muted);
    padding: 1rem 0;
}

.wb-how-card {
    background: var(--card);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 1.6rem 1.8rem;
    margin-top: 0.5rem;
}
.wb-how-card p {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    color: var(--ink);
    line-height: 1.65;
    margin: 0 0 1rem 0;
}
.wb-how-card p:last-child { margin-bottom: 0; }
.wb-how-rule {
    display: flex;
    gap: 0.85rem;
    align-items: flex-start;
    margin-bottom: 0.75rem;
}
.wb-how-rule-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--amber);
    letter-spacing: 0.08em;
    min-width: 1.4rem;
    padding-top: 0.18rem;
}
.wb-how-rule-text {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.93rem;
    color: var(--ink);
    line-height: 1.55;
}
.wb-how-combo-demo {
    display: inline-block;
    background: var(--amber);
    color: #3a1f00;
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    padding: 0.18rem 0.55rem;
    border-radius: 4px;
    margin: 0 0.15rem;
    vertical-align: middle;
}
.wb-how-combo-word {
    font-family: 'DM Mono', monospace;
    font-size: 0.88rem;
    color: var(--ink);
    background: #f3f1ec;
    border: 1px solid var(--border);
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    margin: 0 0.1rem;
    vertical-align: middle;
}
.wb-how-heart { color: #c0392b; font-size: 0.9rem; }
.wb-how-divider { border: none; border-top: 1px solid var(--border); margin: 1.1rem 0; }

/* How to play lang selector */
.wb-lang-btn-wrap {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding-top: 0.15rem;
}
.wb-lang-btn {
    display: block;
    width: 100%;
    padding: 0.45rem 0.5rem;
    border-radius: 6px;
    border: 1.5px solid var(--border);
    background: var(--card);
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: var(--ink);
    cursor: pointer;
    text-align: center;
    transition: all 0.12s;
}
.wb-lang-btn:hover { border-color: var(--ink); }
.wb-lang-btn.active {
    background: var(--ink) !important;
    color: var(--paper) !important;
    border-color: var(--ink) !important;
}
.wb-lang-btn.disabled {
    opacity: 0.4;
    cursor: not-allowed;
    pointer-events: none;
}

/* Same-device badge */
.wb-same-device-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #fff8ec;
    border: 1.5px solid #f0cc80;
    color: #7a4800;
    border-radius: 6px;
    padding: 0.35rem 0.8rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.06em;
    font-weight: 500;
    margin-bottom: 0.8rem;
}
.wb-active-player-banner {
    text-align: center;
    padding: 0.6rem 1rem;
    border-radius: 8px;
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: #fffbf0;
    border: 1.5px solid var(--amber);
    color: #7a4800;
    margin-bottom: 1rem;
}

/* Rematch countdown bar */
.wb-countdown-wrap { margin: 1.2rem 0 0.5rem; }
.wb-countdown-bar-bg {
    background: var(--border);
    border-radius: 99px;
    height: 6px;
    width: 100%;
    overflow: hidden;
}
.wb-countdown-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: var(--amber);
    transition: width 1s linear;
}
.wb-countdown-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--muted);
    letter-spacing: 0.08em;
    text-align: center;
    margin-top: 0.35rem;
}
.wb-vote-status {
    text-align: center;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    color: var(--muted);
    margin: 0.6rem 0 1rem;
}
.wb-vote-name {
    display: inline-block;
    background: #edf7f1;
    color: var(--success);
    border: 1px solid #b8dfc8;
    border-radius: 4px;
    padding: 0.1rem 0.5rem;
    font-size: 0.82rem;
    margin: 0.15rem 0.2rem;
    font-family: 'DM Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ─── How to Play content per language ────────────────────────────────────────

HOW_TO_PLAY = {
    "en": {
        "basics_title": "THE BASICS",
        "basics_text": "Hot Word is a multiplayer word game where everyone sits around a ticking bomb. Each round, a letter combo appears on the bomb — your job is to type any real word that <em>contains</em> that combo before the timer hits zero.",
        "round_title": "HOW A ROUND WORKS",
        "rules": [
            ("01", 'A combo lights up on the bomb — for example <span class="wb-how-combo-demo">STR</span>. It\'s your turn to defuse it.'),
            ("02", 'Type any valid English word that contains those letters in order. <span class="wb-how-combo-word">street</span>, <span class="wb-how-combo-word">strong</span>, and <span class="wb-how-combo-word">destroy</span> would all work. Made-up words and words already used this game don\'t count.'),
            ("03", 'Submit before the clock runs out. If you don\'t, you lose a life <span class="wb-how-heart">♥</span>. Lose all three and you\'re eliminated.'),
            ("04", "Play passes to the next person. The timer gets a little shorter each round, so the pressure builds the longer the game goes."),
        ],
        "winning_title": "WINNING",
        "winning_text": "Last player with at least one life remaining wins. Good luck — and think fast.",
    },
    "es": {
        "basics_title": "LO BÁSICO",
        "basics_text": "Hot Word es un juego de palabras multijugador donde todos rodean una bomba a punto de explotar. Cada ronda, aparece una combinación de letras en la bomba — tu misión es escribir cualquier palabra real que <em>contenga</em> esa combinación antes de que el temporizador llegue a cero.",
        "round_title": "CÓMO FUNCIONA UNA RONDA",
        "rules": [
            ("01", 'Aparece una combinación en la bomba — por ejemplo <span class="wb-how-combo-demo">STR</span>. Es tu turno de desactivarla.'),
            ("02", 'Escribe cualquier palabra válida en español que contenga esas letras en orden. <span class="wb-how-combo-word">estrés</span>, <span class="wb-how-combo-word">estrella</span> y <span class="wb-how-combo-word">destruir</span> servirían. Las palabras inventadas o ya usadas no cuentan.'),
            ("03", 'Envía antes de que se acabe el tiempo. Si no lo haces, pierdes una vida <span class="wb-how-heart">♥</span>. Pierde las tres y quedas eliminado.'),
            ("04", "El turno pasa a la siguiente persona. El temporizador se acorta un poco cada ronda, así que la presión aumenta cuanto más dura el juego."),
        ],
        "winning_title": "CÓMO GANAR",
        "winning_text": "Gana el último jugador con al menos una vida. Buena suerte — y piensa rápido.",
    },
    "fr": {
        "basics_title": "LES BASES",
        "basics_text": "Hot Word est un jeu de mots multijoueur où tout le monde est assis autour d'une bombe qui tic-tac. Chaque tour, une combinaison de lettres apparaît sur la bombe — votre mission est de taper n'importe quel mot réel qui <em>contient</em> cette combinaison avant que le minuteur atteigne zéro.",
        "round_title": "COMMENT SE DÉROULE UN TOUR",
        "rules": [
            ("01", 'Une combinaison s\'allume sur la bombe — par exemple <span class="wb-how-combo-demo">STR</span>. C\'est votre tour de la désamorcer.'),
            ("02", 'Tapez n\'importe quel mot français valide contenant ces lettres dans l\'ordre. <span class="wb-how-combo-word">street</span>, <span class="wb-how-combo-word">structure</span> et <span class="wb-how-combo-word">construire</span> fonctionneraient. Les mots inventés et les mots déjà utilisés ne comptent pas.'),
            ("03", 'Soumettez avant que le temps ne soit écoulé. Sinon, vous perdez une vie <span class="wb-how-heart">♥</span>. Perdez les trois et vous êtes éliminé.'),
            ("04", "Le tour passe à la personne suivante. Le minuteur raccourcit un peu à chaque tour, donc la pression monte au fil du jeu."),
        ],
        "winning_title": "COMMENT GAGNER",
        "winning_text": "Le dernier joueur avec au moins une vie restante gagne. Bonne chance — et pensez vite.",
    },
}

def render_how_to_play(spanish_available, french_available):
    if "how_lang" not in st.session_state:
        st.session_state.how_lang = "en"

    col_langs, col_content = st.columns([1, 5])

    with col_langs:
        lang_options = [
            ("en", "🇺🇸", "En", True),
            ("es", "🇪🇸", "Es", spanish_available),
            ("fr", "🇫🇷", "Fr", french_available),
        ]
        for lang_code, flag, short, available in lang_options:
            is_active = st.session_state.how_lang == lang_code
            active_cls = "active" if is_active else ""
            disabled_cls = "" if available else "disabled"
            label = f"{flag} {short}"
            if available:
                if st.button(label, key=f"how_lang_btn_{lang_code}",
                             use_container_width=True):
                    st.session_state.how_lang = lang_code
                    st.rerun()
                # Manually style via markdown hack — inject active state visually
                if is_active:
                    st.markdown(
                        f"<style>div[data-testid='stButton']:has(button[kind='secondary']) "
                        f"button {{ }}</style>",
                        unsafe_allow_html=True
                    )
            else:
                # Disabled — render as grayed-out non-interactive
                st.markdown(
                    f"<div class='wb-lang-btn disabled' title='Word list not available'>"
                    f"{label}</div>",
                    unsafe_allow_html=True
                )

    with col_content:
        hl = st.session_state.how_lang
        # Fallback if chosen lang became unavailable
        if hl == "es" and not spanish_available:
            hl = "en"
        if hl == "fr" and not french_available:
            hl = "en"

        content = HOW_TO_PLAY[hl]

        # If unavailable lang was previously selected, show note
        orig = st.session_state.how_lang
        if (orig == "es" and not spanish_available) or (orig == "fr" and not french_available):
            lang_name = "Spanish" if orig == "es" else "French"
            st.markdown(
                f"<div class='wb-msg wb-msg-bad' style='margin-bottom:1rem;'>"
                f"⚠️ {lang_name} word list not available — showing English.</div>",
                unsafe_allow_html=True
            )

        st.markdown(f"""
<div class="wb-how-card">
  <div class="wb-section-label">{content['basics_title']}</div>
  <p>{content['basics_text']}</p>

  <hr class="wb-how-divider">

  <div class="wb-section-label">{content['round_title']}</div>
  {''.join(f"""
  <div class="wb-how-rule">
    <span class="wb-how-rule-num">{num}</span>
    <span class="wb-how-rule-text">{text}</span>
  </div>""" for num, text in content['rules'])}

  <hr class="wb-how-divider">

  <div class="wb-section-label">{content['winning_title']}</div>
  <p>{content['winning_text']}</p>
</div>
""", unsafe_allow_html=True)


# ─── Circle renderer ──────────────────────────────────────────────────────────

def render_circle(state, my_name):
    players  = state["players"]
    n        = len(players)
    cur_idx  = state["current_player_idx"]

    elapsed   = time.time() - state["timer_start"] if state["timer_start"] else 0
    remaining = max(0, state["timer_duration"] - elapsed)
    secs      = int(remaining)
    pct       = remaining / state["timer_duration"] if state["timer_duration"] else 1

    if pct > 0.5:    tcol = "#1a7a3f"
    elif pct > 0.25: tcol = "#e8a020"
    else:            tcol = "#c0392b"

    # Scale radius and canvas height based on player count to avoid scrolling
    if n <= 2:
        R  = 140
        CH = 460
    elif n <= 3:
        R  = 160
        CH = 520
    elif n <= 4:
        R  = 180
        CH = 560
    else:
        R  = 210
        CH = 620

    CX, CY       = 300, int(CH * 0.53)
    CW           = 600
    CRD_W, CRD_H = 76, 90

    positions = []
    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        px = CX + R * math.cos(angle)
        py = CY + R * math.sin(angle)
        positions.append((px, py))

    apx, apy = positions[cur_idx]
    dx   = apx - CX
    dy   = apy - CY
    dist = math.hypot(dx, dy) or 1
    bomb_r = 62
    card_r = 50
    ax1 = CX + (dx / dist) * bomb_r
    ay1 = CY + (dy / dist) * bomb_r
    ax2 = CX + (dx / dist) * (dist - card_r)
    ay2 = CY + (dy / dist) * (dist - card_r)

    combo = state.get("current_combo", "??")

    P0 = (CX,       CY - 70)
    P1 = (CX + 18,  CY - 88)
    P2 = (CX + 65,  CY - 118)
    P3 = (CX + 72,  CY - 158)
    P4 = (CX + 78,  CY - 192)
    P5 = (CX + 54,  CY - 224)
    P6 = (CX + 22,  CY - 244)

    fuse_path = (
        f"M{P0[0]},{P0[1]} "
        f"C{P1[0]},{P1[1]} {P2[0]},{P2[1]} {P3[0]},{P3[1]} "
        f"C{P4[0]},{P4[1]} {P5[0]},{P5[1]} {P6[0]},{P6[1]}"
    )

    def bezier_point(t, p0, p1, p2, p3):
        u = 1 - t
        x = u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0]
        y = u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1]
        return (x, y)

    def approx_bezier_length(p0, p1, p2, p3, steps=40):
        pts = [bezier_point(i / steps, p0, p1, p2, p3) for i in range(steps + 1)]
        return sum(math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(steps))

    seg1_len = approx_bezier_length(P0, P1, P2, P3)
    seg2_len = approx_bezier_length(P3, P4, P5, P6)
    FUSE_L   = seg1_len + seg2_len

    fuse_dashoffset = FUSE_L * (1.0 - pct)
    fuse_delta = (FUSE_L / state["timer_duration"]) if state["timer_duration"] else 0
    fuse_next  = min(FUSE_L, fuse_dashoffset + fuse_delta)

    lit_dist = FUSE_L * pct

    if lit_dist <= seg1_len:
        t_approx = lit_dist / seg1_len if seg1_len > 0 else 0
        for _ in range(4):
            steps = 40
            pts = [bezier_point(j / steps, P0, P1, P2, P3) for j in range(steps + 1)]
            cum = [0.0]
            for j in range(steps):
                cum.append(cum[-1] + math.hypot(pts[j+1][0]-pts[j][0], pts[j+1][1]-pts[j][1]))
            target = lit_dist
            for j in range(steps):
                if cum[j+1] >= target:
                    frac = (target - cum[j]) / (cum[j+1] - cum[j] + 1e-9)
                    t_approx = (j + frac) / steps
                    break
        sx, sy = bezier_point(t_approx, P0, P1, P2, P3)
    else:
        dist_into_seg2 = lit_dist - seg1_len
        t_approx = dist_into_seg2 / seg2_len if seg2_len > 0 else 0
        steps = 40
        pts = [bezier_point(j / steps, P3, P4, P5, P6) for j in range(steps + 1)]
        cum = [0.0]
        for j in range(steps):
            cum.append(cum[-1] + math.hypot(pts[j+1][0]-pts[j][0], pts[j+1][1]-pts[j][1]))
        target = dist_into_seg2
        for j in range(steps):
            if cum[j+1] >= target:
                frac = (target - cum[j]) / (cum[j+1] - cum[j] + 1e-9)
                t_approx = (j + frac) / steps
                break
        sx, sy = bezier_point(t_approx, P3, P4, P5, P6)

    spark_x, spark_y = sx, sy

    if pct > 0.5:
        spark_core  = "#ffe066"
        spark_outer = "#f0a020"
    elif pct > 0.25:
        spark_core  = "#ffaa30"
        spark_outer = "#e05010"
    else:
        spark_core  = "#ff6030"
        spark_outer = "#cc2000"

    bomb_flash_class = "bomb-flash" if secs == 0 else ""

    if pct > 0.02:
        spark_svg = f"""
        <circle cx="{spark_x:.1f}" cy="{spark_y:.1f}" r="11" fill="{spark_outer}" opacity="0.3" class="spark-halo"/>
        <circle cx="{spark_x:.1f}" cy="{spark_y:.1f}" r="5.5" fill="{spark_core}" class="spark-core"/>
        <line x1="{spark_x:.1f}"     y1="{spark_y-7:.1f}"  x2="{spark_x-3:.1f}"  y2="{spark_y-15:.1f}" stroke="{spark_core}"  stroke-width="2"   stroke-linecap="round" class="spark-ray"/>
        <line x1="{spark_x+7:.1f}"   y1="{spark_y-4:.1f}"  x2="{spark_x+13:.1f}" y2="{spark_y-10:.1f}" stroke="{spark_outer}" stroke-width="1.8" stroke-linecap="round" class="spark-ray"/>
        <line x1="{spark_x+4:.1f}"   y1="{spark_y-8:.1f}"  x2="{spark_x+8:.1f}"  y2="{spark_y-16:.1f}" stroke="{spark_core}"  stroke-width="1.5" stroke-linecap="round" class="spark-ray"/>
        <line x1="{spark_x-6:.1f}"   y1="{spark_y-3:.1f}"  x2="{spark_x-12:.1f}" y2="{spark_y-7:.1f}"  stroke="{spark_outer}" stroke-width="1.5" stroke-linecap="round" class="spark-ray"/>
        <line x1="{spark_x-3:.1f}"   y1="{spark_y+5:.1f}"  x2="{spark_x-7:.1f}"  y2="{spark_y+12:.1f}" stroke="{spark_outer}" stroke-width="1.4" stroke-linecap="round" class="spark-ray"/>
        """
    else:
        spark_svg = ""

    cards_svg = ""
    same_device = state.get("same_device", False)

    for i, p in enumerate(players):
        px, py = positions[i]
        cx0 = px - CRD_W / 2
        cy0 = py - CRD_H / 2

        is_active = (i == cur_idx)
        # In same-device mode, both cards show "you" feel since it's one screen
        is_me     = p["name"] == my_name or same_device
        is_dead   = not p["alive"]
        lives     = p["lives"]

        if same_device:
            raw_name_disp = p["name"]
        else:
            raw_name_disp = p["name"] + (" ·you" if p["name"] == my_name else "")

        if len(raw_name_disp) > 9:
            raw_name_disp = raw_name_disp[:8] + "…"
        name_disp = esc(raw_name_disp)

        pips = ""
        for j in range(LIVES):
            pip_x = cx0 + 12 + j * 20
            pip_y = cy0 + CRD_H - 22
            if j < lives:
                fill = "#c0392b" if not is_dead else "#ccc"
            else:
                fill = "none"
            stroke = "#c0392b" if not is_dead else "#ccc"
            hx, hy = pip_x, pip_y
            pips += f'<path d="M{hx},{hy+3} C{hx},{hy} {hx-6},{hy} {hx-6},{hy-3} C{hx-6},{hy-8} {hx},{hy-8} {hx},{hy-4} C{hx},{hy-8} {hx+6},{hy-8} {hx+6},{hy-3} C{hx+6},{hy} {hx},{hy} {hx},{hy+3}Z" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'

        if is_dead:
            card_fill    = "#f5f5f5"
            card_stroke  = "#ddd"
            name_fill    = "#bbb"
            card_opacity = "0.45"
        elif is_active:
            card_fill    = "#fffbf0"
            card_stroke  = "#e8a020"
            name_fill    = "#0f0f0f"
            card_opacity = "1"
        else:
            card_fill    = "#ffffff"
            card_stroke  = "#e0ddd6"
            name_fill    = "#0f0f0f"
            card_opacity = "1"

        ring = ""
        if is_active:
            ring = f'<rect x="{cx0-4}" y="{cy0-4}" width="{CRD_W+8}" height="{CRD_H+8}" rx="12" fill="none" stroke="#e8a020" stroke-width="1.5" stroke-dasharray="4 3"/>'

        badge = ""
        if is_active:
            pill_w = max(52, len(combo) * 13 + 24)
            pill_x = px - pill_w / 2
            pill_y = cy0 - 42
            badge  = f'<rect x="{pill_x}" y="{pill_y}" width="{pill_w}" height="26" rx="5" fill="#e8a020"/>'
            badge += f'<text x="{px}" y="{pill_y+18}" text-anchor="middle" font-family="DM Mono, monospace" font-size="15" font-weight="500" fill="#3a1f00" letter-spacing="3">{combo}</text>'

        div_y = cy0 + 34

        elim = ""
        if is_dead:
            elim = f'<line x1="{cx0+8}" y1="{cy0+8}" x2="{cx0+CRD_W-8}" y2="{cy0+CRD_H-8}" stroke="#ccc" stroke-width="1"/><line x1="{cx0+CRD_W-8}" y1="{cy0+8}" x2="{cx0+8}" y2="{cy0+CRD_H-8}" stroke="#ccc" stroke-width="1"/>'

        cards_svg += f"""
        <g opacity="{card_opacity}">
            {ring}
            {badge}
            <rect x="{cx0}" y="{cy0}" width="{CRD_W}" height="{CRD_H}" rx="8"
                  fill="{card_fill}" stroke="{card_stroke}" stroke-width="1.5"/>
            <text x="{px}" y="{cy0+22}" text-anchor="middle"
                  font-family="DM Sans, sans-serif" font-size="12" font-weight="500"
                  fill="{name_fill}">{name_disp}</text>
            <line x1="{cx0+10}" y1="{div_y}" x2="{cx0+CRD_W-10}" y2="{div_y}"
                  stroke="{card_stroke}" stroke-width="0.8"/>
            {pips}
            {elim}
        </g>"""

    bomb_svg = f"""
    <defs>
        <radialGradient id="bombGloss" cx="38%" cy="32%" r="60%">
            <stop offset="0%"   stop-color="#555" stop-opacity="1"/>
            <stop offset="40%"  stop-color="#222" stop-opacity="1"/>
            <stop offset="100%" stop-color="#0a0a0a" stop-opacity="1"/>
        </radialGradient>
        <radialGradient id="bombShine" cx="35%" cy="28%" r="35%">
            <stop offset="0%"   stop-color="#ffffff" stop-opacity="0.18"/>
            <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
        </radialGradient>
    </defs>
    <style>
      @keyframes bomb-timeout-flash {{
        0%   {{ opacity: 1; }}
        20%  {{ opacity: 0.1; }}
        50%  {{ opacity: 0.7; }}
        100% {{ opacity: 1; }}
      }}
      .bomb-flash {{ animation: bomb-timeout-flash 0.5s ease-out forwards; }}

      @keyframes fuse-tick {{
        from {{ stroke-dashoffset: {fuse_dashoffset:.2f}; }}
        to   {{ stroke-dashoffset: {fuse_next:.2f}; }}
      }}
      #fuse-path {{
        animation: fuse-tick 1s linear forwards;
      }}

      @keyframes spark-flicker {{
        0%   {{ opacity: 1;    transform: scale(1); }}
        25%  {{ opacity: 0.55; transform: scale(0.75); }}
        55%  {{ opacity: 1;    transform: scale(1.2); }}
        80%  {{ opacity: 0.7;  transform: scale(0.9); }}
        100% {{ opacity: 1;    transform: scale(1); }}
      }}
      .spark-core, .spark-halo {{
        transform-origin: {spark_x:.1f}px {spark_y:.1f}px;
        animation: spark-flicker 0.35s ease-in-out infinite;
      }}
      .spark-halo {{
        animation-duration: 0.5s;
        animation-delay: -0.1s;
      }}
      @keyframes ray-flicker {{
        0%   {{ opacity: 1; }}
        40%  {{ opacity: 0.3; }}
        70%  {{ opacity: 0.9; }}
        100% {{ opacity: 0.6; }}
      }}
      .spark-ray {{
        animation: ray-flicker 0.3s ease-in-out infinite;
      }}
    </style>
    <g class="{bomb_flash_class}">
        <ellipse cx="{CX}" cy="{CY + 58}" rx="42" ry="8" fill="#000" opacity="0.18"/>
        <circle cx="{CX}" cy="{CY}" r="54" fill="url(#bombGloss)"/>
        <circle cx="{CX}" cy="{CY}" r="54" fill="url(#bombShine)"/>
        <circle cx="{CX - 16}" cy="{CY - 18}" r="7" fill="#ffffff" opacity="0.09"/>
        <circle cx="{CX}" cy="{CY}" r="54" fill="none" stroke="#333" stroke-width="1" opacity="0.4"/>
        <rect x="{CX - 6}" y="{CY - 70}" width="12" height="16" rx="4" fill="#6b4c0e"/>
        <rect x="{CX - 6}" y="{CY - 70}" width="12" height="4" rx="2" fill="#a07820" opacity="0.7"/>
        <path id="fuse-path"
              d="{fuse_path}"
              fill="none"
              stroke="#8b6914" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"
              stroke-dasharray="{FUSE_L} {FUSE_L}"
              stroke-dashoffset="{fuse_dashoffset:.2f}"/>
        <path d="{fuse_path}"
              fill="none"
              stroke="#c49a2a" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"
              stroke-dasharray="{FUSE_L} {FUSE_L}"
              stroke-dashoffset="{fuse_dashoffset:.2f}"
              opacity="0.5"/>
        {spark_svg}
        <rect x="{CX - 34}" y="{CY - 14}" width="68" height="26" rx="5" fill="#e8a020"/>
        <text x="{CX}" y="{CY + 6}" text-anchor="middle"
              font-family="DM Mono, monospace" font-size="14" font-weight="500"
              fill="#3a1f00" letter-spacing="3">{combo}</text>
        <text x="{CX}" y="{CY + 42}" text-anchor="middle"
              font-family="DM Mono, monospace" font-size="30" font-weight="500"
              fill="{tcol}">{secs}s</text>
    </g>"""

    arrow_svg = f"""
    <defs>
      <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L7,3 z" fill="#e8a020"/>
      </marker>
    </defs>
    <line x1="{ax1:.1f}" y1="{ay1:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}"
          stroke="#e8a020" stroke-width="1.5" stroke-dasharray="5 4"
          marker-end="url(#arrowhead)" opacity="0.9"/>"""

    orbit_svg = f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="#e0ddd6" stroke-width="0.8" stroke-dasharray="3 6"/>'

    full_html = f"""
    <div style="background:#faf9f6;padding:0;margin:0;">
    <svg width="100%" viewBox="0 0 {CW} {CH}" xmlns="http://www.w3.org/2000/svg"
         style="display:block;max-width:{CW}px;margin:0 auto;">
        {arrow_svg}
        {orbit_svg}
        {cards_svg}
        {bomb_svg}
    </svg>
    </div>
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
    """
    st.components.v1.html(full_html, height=CH)


# ─── App ──────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Hot Word", page_icon="💣", layout="centered")
inject_css()

for key, default in [
    ("screen", "home"), ("room_code", None),
    ("player_name", None), ("form_key", 0), ("last_error", ""),
    ("voted_rematch", False), ("how_lang", "en"),
]:
    if key not in st.session_state:
        st.session_state[key] = default

spanish_available = os.path.exists(SPANISH_WORDS_FILE)
french_available  = os.path.exists(FRENCH_WORDS_FILE)

english_available = os.path.exists(WORDS_FILE)
if not english_available:
    st.error(f"Missing required word list: {WORDS_FILE}. The game cannot run without it.")
    st.stop()

LANG_OPTIONS = ["en"]
if spanish_available:
    LANG_OPTIONS.append("es")
if french_available:
    LANG_OPTIONS.append("fr")

LANG_LABELS = {
    "en": ("🇺🇸", "English"),
    "es": ("🇪🇸", "Español"),
    "fr": ("🇫🇷", "Français"),
}

LANG_HINTS = {
    "en": "Combos and validation are in English.",
    "es": "Los combos y la validación son en español.",
    "fr": "Les combinaisons et la validation sont en français.",
}

LANG_FORMAT = {
    "en": "🇺🇸  English",
    "es": "🇪🇸  Español",
    "fr": "🇫🇷  Français",
}

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.screen == "home":

    st.markdown("<div class='wb-title'>Hot Word</div>", unsafe_allow_html=True)
    st.markdown("<div class='wb-subtitle'>Type a word containing the combo before the bomb goes off.</div>", unsafe_allow_html=True)

    if "home_name" not in st.session_state:
        st.session_state.home_name = ""

    st.markdown("<div class='wb-section-label'>Your name</div>", unsafe_allow_html=True)
    st.text_input("Your name", max_chars=16, placeholder="Enter your name…",
                  key="home_name", label_visibility="collapsed")
    name = st.session_state.home_name

    st.markdown("<br>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["Public rooms", "Join private", "Create room", "How to play"])

    with tab1:
        rooms = list_public_rooms()
        if not rooms:
            st.markdown("<p style='color:#888;font-size:0.9rem;padding:1rem 0;'>No open rooms right now.</p>",
                        unsafe_allow_html=True)
        for r in rooms:
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.markdown(f"""
                <div class="wb-room-row">
                    <div>
                        <span class="wb-room-code">{esc(r['code'])}</span>
                        <span class="wb-room-meta">&ensp;·&ensp;{esc(r['host'])}</span>
                    </div>
                    <span class="wb-room-meta">{r['players']}/8</span>
                </div>""", unsafe_allow_html=True)
            with col_btn:
                if st.button("Join", key=f"j_{r['code']}"):
                    if not name.strip():
                        st.error("Enter your name first.")
                    else:
                        s, msg = join_room(r["code"], name.strip())
                        if s:
                            st.session_state.room_code   = r["code"]
                            st.session_state.player_name = name.strip()
                            st.session_state.screen      = "lobby"
                            st.rerun()
                        else:
                            st.error(msg)

    with tab2:
        st.markdown("<div class='wb-section-label'>Room code</div>", unsafe_allow_html=True)
        with st.form("join_private_form"):
            code_in   = st.text_input("Room code", placeholder="e.g. P-ABCD",
                                      label_visibility="collapsed")
            submitted = st.form_submit_button("Join room")
        if submitted:
            n = st.session_state.home_name.strip()
            c = code_in.upper().strip()
            if not n:
                st.error("Enter your name first.")
            elif not c:
                st.error("Enter a room code.")
            elif not is_valid_room_code(c):
                st.error("Invalid room code.")
            else:
                s, msg = join_room(c, n)
                if s:
                    st.session_state.room_code   = c
                    st.session_state.player_name = n
                    st.session_state.screen      = "lobby"
                    st.rerun()
                else:
                    st.error(msg)

    with tab3:
        if "create_same_device" not in st.session_state:
            st.session_state.create_same_device = False
        if "create_p2_name" not in st.session_state:
            st.session_state.create_p2_name = ""

        with st.form("create_room_form"):
            private     = st.checkbox("Private room")
            same_device = st.checkbox(
                "📱 Same device (1v1)",
                help="Play against someone on the same screen. Online multiplayer is disabled in this mode."
            )
            submitted_create = st.form_submit_button("Create room")

        if submitted_create:
            n = st.session_state.home_name.strip()
            if not n:
                st.error("Enter your name first.")
            elif same_device:
                # Store intent and show P2 name input
                st.session_state.create_same_device = True
                st.session_state.create_private     = private
                st.session_state.create_p1_name     = n
            else:
                code = gen_unique_code(private)
                create_room(code, n, private, same_device=False)
                st.session_state.room_code        = code
                st.session_state.player_name      = n
                st.session_state.screen           = "lobby"
                st.session_state.create_same_device = False
                st.rerun()

        # ── Same-device P2 name prompt ────────────────────────────────────────
        if st.session_state.create_same_device:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(
                "<div class='wb-same-device-badge'>📱 SAME DEVICE MODE</div>",
                unsafe_allow_html=True
            )
            st.markdown("<div class='wb-section-label'>Player 2 name</div>", unsafe_allow_html=True)

            with st.form("p2_name_form"):
                p2_name   = st.text_input("Player 2 name", max_chars=16,
                                          placeholder="Enter player 2's name…",
                                          label_visibility="collapsed")
                col_cancel, col_go = st.columns([1, 2])
                with col_cancel:
                    cancel = st.form_submit_button("Cancel")
                with col_go:
                    go = st.form_submit_button("Start →")

            if cancel:
                st.session_state.create_same_device = False
                st.rerun()

            if go:
                p1 = st.session_state.get("create_p1_name", "").strip()
                p2 = p2_name.strip()
                priv = st.session_state.get("create_private", False)
                if not p2:
                    st.error("Enter player 2's name.")
                elif p2.casefold() == p1.casefold():
                    st.error("Player 2 must have a different name.")
                else:
                    code = gen_unique_code(private=True)  # same-device rooms are always private
                    create_room(code, p1, priv, same_device=True, player2_name=p2)
                    st.session_state.room_code          = code
                    st.session_state.player_name        = p1  # P1 is "the user" for session
                    st.session_state.screen             = "lobby"
                    st.session_state.create_same_device = False
                    st.rerun()

    with tab4:
        render_how_to_play(spanish_available, french_available)

    st_autorefresh(interval=3000, key="home_refresh", limit=None)

# ══════════════════════════════════════════════════════════════════════════════
# LOBBY
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.screen == "lobby":
    if not st.session_state.get("room_code"):
        st.session_state.screen = "home"; st.rerun(); st.stop()
    state = load_room(st.session_state.room_code)
    if state is None:
        st.session_state.screen = "home"; st.rerun(); st.stop()
    if state.get("started"):
        st.session_state.screen = "game"; st.rerun(); st.stop()

    code        = st.session_state.room_code
    same_device = state.get("same_device", False)

    my_names = [p["name"] for p in state["players"]]
    if st.session_state.player_name not in my_names:
        st.warning("You were removed from the room.")
        st.session_state.screen    = "home"
        st.session_state.room_code = None
        st.rerun(); st.stop()

    is_host      = st.session_state.player_name == state["host"]
    current_lang = state.get("language", "en")
    is_es        = current_lang == "es"
    is_fr        = current_lang == "fr"

    if is_fr:
        privacy_label = "Privée" if state["is_private"] else "Publique"
        lobby_title   = "Salon d'attente"
        share_hint    = "Partagez ce code avec vos amis"
        players_label = "JOUEURS"
    elif is_es:
        privacy_label = "Privada" if state["is_private"] else "Pública"
        lobby_title   = "Sala de espera"
        share_hint    = "Comparte este código con tus amigos"
        players_label = "JUGADORES"
    else:
        privacy_label = "Private" if state["is_private"] else "Public"
        lobby_title   = "Lobby"
        share_hint    = "Share this code with friends"
        players_label = "PLAYERS"

    st.markdown(f"<div class='wb-title' style='font-size:2rem;'>{lobby_title}</div>", unsafe_allow_html=True)

    if same_device:
        st.markdown(
            "<div class='wb-same-device-badge'>📱 SAME DEVICE MODE</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"<div class='wb-section-label'>{privacy_label} room</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='wb-lobby-code'>{esc(code)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#888;font-size:0.82rem;margin-bottom:1.2rem;'>{share_hint}</div>",
                    unsafe_allow_html=True)

    # Language selector — host only, not in same-device (no need to share)
    if is_host:
        if current_lang == "es" and not spanish_available:
            set_room_language(code, "en")
            current_lang = "en"
        if current_lang == "fr" and not french_available:
            set_room_language(code, "en")
            current_lang = "en"

        lang_idx = LANG_OPTIONS.index(current_lang) if current_lang in LANG_OPTIONS else 0
        chosen = st.radio(
            "Language",
            options=LANG_OPTIONS,
            index=lang_idx,
            key="lang_radio",
            format_func=lambda x: LANG_FORMAT[x],
            help="Choose which language combos players must match.",
        )
        if chosen != current_lang:
            set_room_language(code, chosen)
            st.rerun()
        st.caption(LANG_HINTS.get(current_lang, ""))

        if not spanish_available:
            st.caption("⚠️ Spanish mode unavailable: words_spanish.txt is missing.")
        if not french_available:
            st.caption("⚠️ French mode unavailable: words_french.txt is missing.")
    else:
        flag, label = LANG_LABELS.get(current_lang, ("", current_lang))
        st.caption(f"{flag} {label}")

    st.markdown(f"<div class='wb-section-label'>{players_label}</div>", unsafe_allow_html=True)
    for idx, p in enumerate(state["players"]):
        crown = " 👑" if p["name"] == state["host"] else ""
        if same_device:
            you = f" · P{idx+1}"
        elif is_fr:
            you = " · vous" if p["name"] == st.session_state.player_name else ""
        elif is_es:
            you = " · tú" if p["name"] == st.session_state.player_name else ""
        else:
            you = " · you" if p["name"] == st.session_state.player_name else ""

        can_kick = is_host and p["name"] != st.session_state.player_name and not same_device
        st.markdown(
            f"<div class='wb-player-row'>"
            f"<span>{esc(p['name'])}{crown}</span>"
            f"<span style='color:#888;font-size:0.82rem;'>{you}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if can_kick:
            if is_fr:
                kick_label = "Expulser"
            elif is_es:
                kick_label = "Expulsar"
            else:
                kick_label = "Remove"
            if st.button(kick_label, key=f"kick_{idx}"):
                kick_player(code, st.session_state.player_name, p["name"])
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_leave, col_start = st.columns([1, 2])

    with col_leave:
        st.markdown("<div class='btn-ghost'>", unsafe_allow_html=True)
        if is_fr:
            leave_label = "Quitter"
        elif is_es:
            leave_label = "Salir"
        else:
            leave_label = "Leave"
        if st.button(leave_label):
            leave_room(code, st.session_state.player_name)
            st.session_state.screen    = "home"
            st.session_state.room_code = None
            st.rerun(); st.stop()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_start:
        if is_host:
            if len(state["players"]) < 2:
                if is_fr:
                    need_msg = "Il faut au moins 2 joueurs."
                elif is_es:
                    need_msg = "Se necesitan al menos 2 jugadores."
                else:
                    need_msg = "Need at least 2 players."
                st.markdown(f"<p style='color:#888;font-size:0.88rem;padding-top:0.5rem;'>{need_msg}</p>",
                            unsafe_allow_html=True)
            else:
                if is_fr:
                    start_label = "Démarrer →"
                elif is_es:
                    start_label = "Iniciar partida →"
                else:
                    start_label = "Start game →"
                if st.button(start_label):
                    state = load_room(code)
                    start_game(code, state)
                    st.session_state.screen = "game"
                    st.rerun()
        else:
            if is_fr:
                waiting_msg = f"En attente de {esc(state['host'])} pour démarrer…"
            elif is_es:
                waiting_msg = f"Esperando a {esc(state['host'])} para iniciar…"
            else:
                waiting_msg = f"Waiting for {esc(state['host'])} to start…"
            st.markdown(f"<p style='color:#888;font-size:0.88rem;padding-top:0.5rem;'>{waiting_msg}</p>",
                        unsafe_allow_html=True)

    if not same_device:
        st_autorefresh(interval=2000, key="lobby_refresh")

# ══════════════════════════════════════════════════════════════════════════════
# GAME
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.screen == "game":
    if not st.session_state.get("room_code"):
        st.session_state.screen = "home"; st.rerun(); st.stop()
    state = load_room(st.session_state.room_code)
    if state is None:
        st.error("Room lost.")
        st.session_state.screen = "home"; st.rerun()

    state       = check_timer(st.session_state.room_code, state)
    my_name     = st.session_state.player_name
    lang        = state.get("language", "en")
    is_es       = lang == "es"
    is_fr       = lang == "fr"
    same_device = state.get("same_device", False)

    # ── END SCREEN ─────────────────────────────────────────────────────────────
    if state["finished"]:
        code  = st.session_state.room_code
        state = check_rematch_or_expire(code)

        if state is None:
            st.session_state.screen       = "home"
            st.session_state.room_code    = None
            st.session_state.voted_rematch = False
            st.rerun(); st.stop()

        if not state["finished"]:
            st.session_state.voted_rematch = False
            st.rerun(); st.stop()

        st.balloons()

        if is_fr:
            winner_label = "gagne."
        elif is_es:
            winner_label = "gana."
        else:
            winner_label = "wins."
        st.markdown(f"<div class='wb-title'>{esc(state['winner'])} {winner_label}</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

        for p in state["players"]:
            if p["name"] == state["winner"]:
                icon = "—"
            elif is_fr:
                icon = "éliminé"
            elif is_es:
                icon = "eliminado"
            else:
                icon = "out"
            st.markdown(
                f"<div class='wb-player-row'><span>{esc(p['name'])}</span>"
                f"<span style='color:#888;font-size:0.82rem;'>{icon}</span></div>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        deadline    = state.get("rematch_deadline")
        now_t       = time.time()
        time_left   = max(0.0, (deadline - now_t)) if deadline else float(REMATCH_TIMEOUT)
        pct_left    = time_left / REMATCH_TIMEOUT
        bar_width   = int(pct_left * 100)
        secs_left   = int(math.ceil(time_left))

        votes       = state.get("rematch_votes", [])
        total       = len(state["players"])
        voted_names_html = "".join(
            f'<span class="wb-vote-name">{esc(v)}</span>' for v in votes
        )

        if is_fr:
            countdown_txt = f"La salle se ferme dans {secs_left}s"
            vote_info     = f"{len(votes)}/{total} ont voté pour rejouer"
            rematch_btn   = "Rejouer"
            home_btn      = "Retour à l'accueil"
            already_voted = "Vous avez voté pour rejouer !"
            need_two      = "Il faut au moins 2 joueurs pour rejouer."
        elif is_es:
            countdown_txt = f"La sala se cierra en {secs_left}s"
            vote_info     = f"{len(votes)}/{total} votaron por revancha"
            rematch_btn   = "Revancha"
            home_btn      = "Volver al inicio"
            already_voted = "¡Ya votaste por revancha!"
            need_two      = "Se necesitan al menos 2 jugadores para una revancha."
        else:
            countdown_txt = f"Room closes in {secs_left}s"
            vote_info     = f"{len(votes)}/{total} voted to rematch"
            rematch_btn   = "Rematch"
            home_btn      = "Back to home"
            already_voted = "You've voted for a rematch!"
            need_two      = "Need at least 2 players to rematch."

        st.markdown(f"""
<div class="wb-countdown-wrap">
  <div class="wb-countdown-bar-bg">
    <div class="wb-countdown-bar-fill" style="width:{bar_width}%;"></div>
  </div>
  <div class="wb-countdown-label">{countdown_txt}</div>
</div>
""", unsafe_allow_html=True)

        if same_device:
            # In same-device mode a single "Play Again" button handles rematch
            already = my_name in votes or st.session_state.voted_rematch
            if already:
                st.markdown(f"<p style='color:#1a7a3f;font-size:0.88rem;text-align:center;'>✓ {already_voted}</p>",
                            unsafe_allow_html=True)
            else:
                col_r, col_h = st.columns([1, 1])
                with col_r:
                    st.markdown("<div class='btn-rematch'>", unsafe_allow_html=True)
                    if st.button(rematch_btn, key="rematch_vote_btn"):
                        # Cast vote for both players in same-device
                        for p in state["players"]:
                            cast_rematch_vote(code, p["name"])
                        st.session_state.voted_rematch = True
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                with col_h:
                    st.markdown("<div class='btn-ghost'>", unsafe_allow_html=True)
                    if st.button(home_btn, key="end_home_btn"):
                        st.session_state.screen        = "home"
                        st.session_state.room_code     = None
                        st.session_state.voted_rematch = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            if votes:
                st.markdown(
                    f"<div class='wb-vote-status'>{vote_info} — {voted_names_html}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='wb-vote-status'>{vote_info}</div>",
                    unsafe_allow_html=True,
                )

            col_rematch, col_home = st.columns([1, 1])

            with col_rematch:
                if st.session_state.voted_rematch or (my_name in votes):
                    st.markdown(f"<p style='color:#1a7a3f;font-size:0.88rem;padding-top:0.6rem;text-align:center;'>✓ {already_voted}</p>",
                                unsafe_allow_html=True)
                elif total < 2:
                    st.markdown(f"<p style='color:#888;font-size:0.88rem;padding-top:0.6rem;'>{need_two}</p>",
                                unsafe_allow_html=True)
                else:
                    st.markdown("<div class='btn-rematch'>", unsafe_allow_html=True)
                    if st.button(rematch_btn, key="rematch_vote_btn"):
                        updated = cast_rematch_vote(code, my_name)
                        st.session_state.voted_rematch = True
                        if updated is not None:
                            state = updated
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

            with col_home:
                st.markdown("<div class='btn-ghost'>", unsafe_allow_html=True)
                if st.button(home_btn, key="end_home_btn"):
                    st.session_state.screen        = "home"
                    st.session_state.room_code     = None
                    st.session_state.voted_rematch = False
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        st_autorefresh(interval=1000, key="end_refresh")
        st.stop()

    # ── ACTIVE GAME ────────────────────────────────────────────────────────────
    cp         = state["players"][state["current_player_idx"]]
    is_my_turn = cp["name"] == my_name or same_device  # In same-device, always show input

    # In same-device mode, show whose turn it is as a banner
    if same_device:
        st.markdown(
            f"<div class='wb-active-player-banner'>🎮 {esc(cp['name'])}'s turn</div>",
            unsafe_allow_html=True,
        )

    render_circle(state, my_name)

    msg = state.get("last_message", "")
    if msg:
        if msg.startswith("good:"):
            text = msg[5:]
            st.markdown(f"<div class='wb-msg wb-msg-good'>{text}</div>", unsafe_allow_html=True)
        elif msg.startswith("eliminated:") or msg.startswith("timeout:"):
            text = msg.split(":", 1)[1]
            st.markdown(f"<div class='wb-msg wb-msg-bad'>{text}</div>", unsafe_allow_html=True)

    combo = state["current_combo"]

    if is_fr:
        turn_label = "Votre tour — saisissez un mot contenant"
    elif is_es:
        turn_label = "Tu turno &mdash; escribe una palabra que contenga"
    else:
        turn_label = "Your turn &mdash; type a word containing"

    st.markdown(
        f"<div class='wb-turn-label'>{turn_label} "
        f"<span style='font-size:1.1rem;letter-spacing:0.12em;color:#e8a020;'>{combo}</span></div>",
        unsafe_allow_html=True,
    )

    if st.session_state.last_error:
        st.markdown(f"<div class='wb-msg wb-msg-bad'>{esc(st.session_state.last_error)}</div>",
                    unsafe_allow_html=True)

    if is_fr:
        placeholder  = f"{combo} · saisissez votre mot ici…"
        submit_label = "Valider →"
    elif is_es:
        placeholder  = f"{combo} · escribe tu palabra aquí…"
        submit_label = "Enviar →"
    else:
        placeholder  = f"{combo} · type your word here…"
        submit_label = "Submit →"

    # In same-device mode always show form for the active player
    with st.form(key=f"wf_{st.session_state.form_key}", clear_on_submit=True):
        word      = st.text_input("word", label_visibility="collapsed", placeholder=placeholder)
        submitted = st.form_submit_button(submit_label)

    if submitted and word.strip():
        # In same-device mode, submit as the current active player
        submit_name = cp["name"] if same_device else my_name
        state, result = submit_word(st.session_state.room_code, state, submit_name, word.strip())
        if result == "ok":
            st.session_state.form_key  += 1
            st.session_state.last_error = ""
        else:
            st.session_state.last_error = result
        st.rerun()

    st.components.v1.html("""
    <script>
    function focusInput() {
        const doc = window.parent.document;
        const inputs = doc.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) {
            const inp = inputs[inputs.length - 1];
            inp.focus();
            // Move cursor to end
            const val = inp.value;
            inp.value = '';
            inp.value = val;
        }
    }

    // Try immediately, then retry a few times to catch slow renders
    focusInput();
    setTimeout(focusInput, 100);
    setTimeout(focusInput, 300);
    setTimeout(focusInput, 600);
    setTimeout(focusInput, 1000);

    // Re-focus if user clicks anywhere that isn't an input
    window.parent.document.addEventListener('click', function(e) {
        const tag = e.target.tagName;
        if (tag !== 'INPUT' && tag !== 'TEXTAREA' && tag !== 'BUTTON') {
            setTimeout(focusInput, 50);
        }
    });

    // Re-focus on every keypress if nothing is focused
    window.parent.document.addEventListener('keydown', function(e) {
        const active = window.parent.document.activeElement;
        const isTyping = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA');
        if (!isTyping) {
            if (e.key === 'c') { e.stopPropagation(); }
            focusInput();
        }
    }, true);
    </script>
    """, height=0)

    st_autorefresh(interval=1000, key="game_refresh")
