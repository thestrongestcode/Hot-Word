import streamlit as st
from streamlit_autorefresh import st_autorefresh
import json
import os
import time
import random
import string
import math

# ─── Constants ────────────────────────────────────────────────────────────────

WORDS_FILE         = "words_alpha.txt"
ROOMS_DIR          = "rooms"
STARTING_TIMER     = 30
MIN_TURN_FLOOR     = 5
TIMER_SHRINK       = 2
MIN_STARTING_TIMER = 8
LIVES              = 3
ROOM_EXPIRY        = 300

EASY_COMBOS = [
    "TH","CH","SH","TR","PR","BR","CR","ST","SP","SK",
    "LY","FT","ER","NT","ND","ES","EN","OU","GH","WH",
]
MEDIUM_COMBOS = [
    "ING","NCE","STR","GHT","OUN","PLE","ENT","OUS","ATE","EAR",
    "OWN","AIN","EAD","OOK","ALL","ORT","OOD","EEL","ION","ARD",
]
HARD_COMBOS = [
    "SCR","THR","NCH","TCH","QUA","DGE","SQU","NGU","NGL",
    "MBL","CKL","RPH","NGS","STH","NDL","PSY","GNI","MPT",
    "LVE","XTR","PHR","SPL","STL","GGL","RCH","NST",
    "RST","NTH","SKI","NCL","NCT","RSH",
]

# ─── Word validation ──────────────────────────────────────────────────────────

@st.cache_resource
def load_words():
    with open(WORDS_FILE) as f:
        return set(w.strip().lower() for w in f)

def is_valid_play(word, combo, used_words):
    w = word.lower().strip()
    if not w:
        return False, "Type a word first."
    if combo.lower() not in w:
        return False, f'"{word}" doesn\'t contain "{combo}".'
    if w not in load_words():
        return False, f'"{word}" isn\'t a valid word.'
    if w in used_words:
        return False, f'"{word}" was already used.'
    return True, "ok"

# ─── Combo selection ──────────────────────────────────────────────────────────

def pick_combo(round_num, used_combos):
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

# ─── Room helpers ─────────────────────────────────────────────────────────────

def room_path(code):
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
        # os.replace can fail across filesystems; fall back to direct write
        with open(p, "w") as f:
            json.dump(state, f)

def create_room(code, name, private):
    state = {
        "players": [{"name": name, "lives": LIVES, "alive": True}],
        "host": name, "is_private": private,
        "started": False, "finished": False, "winner": None,
        "current_player_idx": 0, "current_combo": "",
        "used_combos": [], "used_words": [], "round": 1,
        "timer_start": None, "timer_duration": STARTING_TIMER,
        "last_message": "", "created_at": time.time(),
    }
    save_room(code, state)
    return state

def join_room(code, name):
    state = load_room(code)
    if state is None:         return None, "Room not found."
    if state["started"]:      return None, "Game already started."
    if name in [p["name"] for p in state["players"]]:
                              return None, "Name already taken."
    if len(state["players"]) >= 8:
                              return None, "Room is full (max 8)."
    state["players"].append({"name": name, "lives": LIVES, "alive": True})
    save_room(code, state)
    return state, "ok"

def gen_code(private=False):
    return ("P-" if private else "") + "".join(random.choices(string.ascii_uppercase, k=4))

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

def cleanup_rooms():
    if not os.path.exists(ROOMS_DIR): return
    now = time.time()
    for fname in os.listdir(ROOMS_DIR):
        if not fname.endswith(".json"): continue
        p = os.path.join(ROOMS_DIR, fname)
        try:
            with open(p) as f:
                s = json.load(f)
            if s.get("finished"): os.remove(p); continue
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
            if not s.get("is_private") and not s.get("started") and not s.get("finished"):
                rooms.append({"code": code, "host": s["host"],
                               "players": len(s["players"]), "created_at": s.get("created_at", 0)})
        except Exception:
            continue
    return sorted(rooms, key=lambda r: r["created_at"], reverse=True)

# ─── Game logic ───────────────────────────────────────────────────────────────

def alive_players(state):
    return [p for p in state["players"] if p["alive"]]

def start_game(code, state):
    combo = pick_combo(1, [])
    state.update(started=True, current_combo=combo, used_combos=[combo],
                 timer_start=time.time(), current_player_idx=0)
    save_room(code, state)

def advance_turn(code, state, remaining_time):
    alive = alive_players(state)
    if len(alive) <= 1: return

    cur_name = state["players"][state["current_player_idx"]]["name"]
    alive_names = [p["name"] for p in alive]
    cur_idx = alive_names.index(cur_name) if cur_name in alive_names else 0
    next_name = alive_names[(cur_idx + 1) % len(alive_names)]

    for i, p in enumerate(state["players"]):
        if p["name"] == next_name:
            state["current_player_idx"] = i
            break

    guaranteed = max(remaining_time, MIN_TURN_FLOOR)
    state["timer_start"] = time.time() - (state["timer_duration"] - guaranteed)

    combo = pick_combo(state["round"], state["used_combos"])
    state["current_combo"] = combo
    state["used_combos"].append(combo)
    state["round"] += 1
    save_room(code, state)

def check_timer(code, state):
    if not state["started"] or state["finished"]: return state
    elapsed = time.time() - state["timer_start"]
    if elapsed < state["timer_duration"]: return state

    cp = state["players"][state["current_player_idx"]]
    cp["lives"] -= 1
    if cp["lives"] <= 0:
        cp["alive"] = False
        state["last_message"] = f'eliminated:{cp["name"]} was eliminated.'
    else:
        state["last_message"] = f'timeout:{cp["name"]} ran out of time — {cp["lives"]} {"life" if cp["lives"]==1 else "lives"} left.'

    state["timer_duration"] = max(MIN_STARTING_TIMER, state["timer_duration"] - TIMER_SHRINK)

    alive = alive_players(state)
    if len(alive) == 1:
        state["finished"] = True
        state["winner"] = alive[0]["name"]
    elif len(alive) == 0:
        state["finished"] = True
        state["winner"] = "Nobody"
    else:
        n_all = len(state["players"])
        cur_global_idx = state["current_player_idx"]
        next_global_idx = None
        for offset in range(1, n_all + 1):
            candidate_idx = (cur_global_idx + offset) % n_all
            if state["players"][candidate_idx]["alive"]:
                next_global_idx = candidate_idx
                break
        if next_global_idx is not None:
            state["current_player_idx"] = next_global_idx

        combo = pick_combo(state["round"], state["used_combos"])
        state["current_combo"] = combo
        state["used_combos"].append(combo)
        state["round"] += 1

    state["timer_start"] = time.time()
    save_room(code, state)
    return state

def submit_word(code, state, name, word):
    cp = state["players"][state["current_player_idx"]]
    if cp["name"] != name: return state, "Not your turn."
    valid, msg = is_valid_play(word, state["current_combo"], state["used_words"])
    if not valid: return state, msg

    elapsed   = time.time() - state["timer_start"]
    remaining = max(0, state["timer_duration"] - elapsed)

    state["used_words"].append(word.lower())
    state["last_message"] = f'good:{name} played "{word}"'
    advance_turn(code, state, remaining)
    save_room(code, state)
    return state, "ok"

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

/* ── typography ── */
h1, h2, h3 { font-family: 'DM Serif Display', serif !important; color: var(--ink); }

/* ── inputs ── */
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

/* ── primary button ── */
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

/* danger/secondary variant — applied via wrapping div.btn-ghost */
.btn-ghost .stButton button {
    background: transparent !important;
    color: var(--ink) !important;
    border: 1.5px solid var(--border) !important;
}
.btn-ghost .stButton button:hover {
    border-color: var(--ink) !important;
    opacity: 1 !important;
}

/* ── tabs ── */
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

/* ── alerts ── */
.stAlert { border-radius: 6px !important; font-family: 'DM Sans', sans-serif !important; }

/* ── checkbox ── */
.stCheckbox label { font-family: 'DM Sans', sans-serif !important; color: var(--ink) !important; }

/* ── divider ── */
hr { border-color: var(--border) !important; }

/* ── custom components ── */
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
/* lobby kick button: strip Streamlit block margin */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > div:has(button[kind="secondary"]) {
    margin-top: -0.4rem;
    margin-bottom: 0.35rem;
}
</style>
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

    # SVG canvas
    CX, CY   = 300, 330
    R        = 200       # orbit radius
    CW, CH   = 600, 660

    # card dimensions
    CRD_W, CRD_H = 80, 96

    # compute player positions
    positions = []
    for i in range(n):
        angle = (2 * math.pi * i / n) - math.pi / 2
        px = CX + R * math.cos(angle)
        py = CY + R * math.sin(angle)
        positions.append((px, py))

    # arrow: from bomb edge toward active player
    apx, apy = positions[cur_idx]
    dx = apx - CX
    dy = apy - CY
    dist = math.hypot(dx, dy) or 1
    bomb_r = 62
    card_r = 50  # stop near card edge
    ax1 = CX + (dx / dist) * bomb_r
    ay1 = CY + (dy / dist) * bomb_r
    ax2 = CX + (dx / dist) * (dist - card_r)
    ay2 = CY + (dy / dist) * (dist - card_r)

    combo = state.get("current_combo", "??")

    # build player cards SVG
    cards_svg = ""
    for i, p in enumerate(players):
        px, py = positions[i]
        cx0 = px - CRD_W / 2
        cy0 = py - CRD_H / 2

        is_active = (i == cur_idx)
        is_me     = p["name"] == my_name
        is_dead   = not p["alive"]
        lives     = p["lives"]
        name_disp = p["name"] + (" ·you" if is_me else "")

        # truncate long names
        if len(name_disp) > 9:
            name_disp = name_disp[:8] + "…"

        # pip hearts
        pips = ""
        for j in range(LIVES):
            pip_x = cx0 + 12 + j * 20
            pip_y = cy0 + CRD_H - 22
            if j < lives:
                fill = "#c0392b" if not is_dead else "#ccc"
            else:
                fill = "none"
            stroke = "#c0392b" if not is_dead else "#ccc"
            # small heart path centered at pip_x, pip_y
            hx, hy = pip_x, pip_y
            pips += f'<path d="M{hx},{hy+3} C{hx},{hy} {hx-6},{hy} {hx-6},{hy-3} C{hx-6},{hy-8} {hx},{hy-8} {hx},{hy-4} C{hx},{hy-8} {hx+6},{hy-8} {hx+6},{hy-3} C{hx+6},{hy} {hx},{hy} {hx},{hy+3}Z" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'

        if is_dead:
            card_fill   = "#f5f5f5"
            card_stroke = "#ddd"
            name_fill   = "#bbb"
            card_opacity = "0.45"
        elif is_active:
            card_fill   = "#fffbf0"
            card_stroke = "#e8a020"
            name_fill   = "#0f0f0f"
            card_opacity = "1"
        else:
            card_fill   = "#ffffff"
            card_stroke = "#e0ddd6"
            name_fill   = "#0f0f0f"
            card_opacity = "1"

        # active outer ring
        ring = ""
        if is_active:
            ring = f'<rect x="{cx0-4}" y="{cy0-4}" width="{CRD_W+8}" height="{CRD_H+8}" rx="12" fill="none" stroke="#e8a020" stroke-width="1.5" stroke-dasharray="4 3"/>'

        # combo pill + "your turn" label above active card
        badge = ""
        if is_active:
            pill_w = max(52, len(combo) * 13 + 24)
            pill_x = px - pill_w / 2
            pill_y = cy0 - 42
            badge  = f'<rect x="{pill_x}" y="{pill_y}" width="{pill_w}" height="26" rx="5" fill="#e8a020"/>'
            badge += f'<text x="{px}" y="{pill_y+18}" text-anchor="middle" font-family="DM Mono, monospace" font-size="15" font-weight="500" fill="#3a1f00" letter-spacing="3">{combo}</text>'
            if is_me:
                badge += f'<text x="{px}" y="{cy0-48}" text-anchor="middle" font-family="DM Mono, monospace" font-size="9" fill="#e8a020" letter-spacing="1">YOUR TURN</text>'

        # divider line
        div_y = cy0 + 34

        # eliminated X
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

    # bomb body
    bomb_svg = f"""
    <g>
        <!-- body -->
        <circle cx="{CX}" cy="{CY}" r="54" fill="#111"/>
        <!-- shine -->
        <circle cx="{CX-14}" cy="{CY-14}" r="9" fill="#222"/>
        <!-- fuse tube -->
        <rect x="{CX-5}" y="{CY-66}" width="10" height="16" rx="5" fill="#7a5a10"/>
        <!-- fuse wire -->
        <path d="M{CX} {CY-66} Q{CX+20} {CY-84} {CX+14} {CY-98} Q{CX+8} {CY-112} {CX+24} {CY-120}"
              fill="none" stroke="#7a5a10" stroke-width="3" stroke-linecap="round"/>
        <!-- spark -->
        <circle cx="{CX+24}" cy="{CY-121}" r="5" fill="#e8a020"/>
        <line x1="{CX+24}" y1="{CY-128}" x2="{CX+20}" y2="{CY-134}" stroke="#e8a020" stroke-width="2" stroke-linecap="round"/>
        <line x1="{CX+30}" y1="{CY-126}" x2="{CX+35}" y2="{CY-131}" stroke="#e8a020" stroke-width="2" stroke-linecap="round"/>
        <line x1="{CX+27}" y1="{CY-129}" x2="{CX+29}" y2="{CY-136}" stroke="#e8a020" stroke-width="2" stroke-linecap="round"/>
        <!-- combo pill -->
        <rect x="{CX-34}" y="{CY-14}" width="68" height="26" rx="5" fill="#e8a020"/>
        <text x="{CX}" y="{CY+6}" text-anchor="middle"
              font-family="DM Mono, monospace" font-size="14" font-weight="500"
              fill="#3a1f00" letter-spacing="3">{combo}</text>
        <!-- timer -->
        <text x="{CX}" y="{CY+40}" text-anchor="middle"
              font-family="DM Mono, monospace" font-size="30" font-weight="500"
              fill="{tcol}">{secs}s</text>
    </g>"""

    # dashed arrow
    arrow_svg = f"""
    <defs>
      <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L0,6 L7,3 z" fill="#e8a020"/>
      </marker>
    </defs>
    <line x1="{ax1:.1f}" y1="{ay1:.1f}" x2="{ax2:.1f}" y2="{ay2:.1f}"
          stroke="#e8a020" stroke-width="1.5" stroke-dasharray="5 4"
          marker-end="url(#arrowhead)" opacity="0.9"/>"""

    # orbit ring
    orbit_svg = f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="#e0ddd6" stroke-width="0.8" stroke-dasharray="3 6"/>'

    full_html = f"""
    <div style="background:#faf9f6;padding:0;margin:0;">
    <svg width="100%" viewBox="0 0 {CW} {CH}" xmlns="http://www.w3.org/2000/svg"
         style="display:block;max-width:{CW}px;margin:0 auto;">
        {arrow_svg}
        {orbit_svg}
        {bomb_svg}
        {cards_svg}
    </svg>
    </div>
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
    """
    st.components.v1.html(full_html, height=CH + 10)


# ─── App ──────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Hot Word", page_icon="💣", layout="centered")
inject_css()

for key, default in [
    ("screen", "home"), ("room_code", None),
    ("player_name", None), ("form_key", 0), ("last_error", ""),
]:
    if key not in st.session_state:
        st.session_state[key] = default

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
    tab1, tab2, tab3 = st.tabs(["Public rooms", "Join private", "Create room"])

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
                        <span class="wb-room-code">{r['code']}</span>
                        <span class="wb-room-meta">&ensp;·&ensp;{r['host']}</span>
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
                            st.session_state.room_code = r["code"]
                            st.session_state.player_name = name.strip()
                            st.session_state.screen = "lobby"
                            st.rerun()
                        else:
                            st.error(msg)

    with tab2:
        st.markdown("<div class='wb-section-label'>Room code</div>", unsafe_allow_html=True)
        with st.form("join_private_form"):
            code_in = st.text_input("Room code", placeholder="e.g. P-ABCD",
                                    label_visibility="collapsed")
            submitted = st.form_submit_button("Join room")
        if submitted:
            n = st.session_state.home_name.strip()
            c = code_in.upper().strip()
            if not n: st.error("Enter your name first.")
            elif not c: st.error("Enter a room code.")
            else:
                s, msg = join_room(c, n)
                if s:
                    st.session_state.room_code = c
                    st.session_state.player_name = n
                    st.session_state.screen = "lobby"
                    st.rerun()
                else:
                    st.error(msg)

    with tab3:
        with st.form("create_room_form"):
            private = st.checkbox("Private room")
            if st.form_submit_button("Create room"):
                n = st.session_state.home_name.strip()
                if not n:
                    st.error("Enter your name first.")
                else:
                    code = gen_code(private)
                    create_room(code, n, private)
                    st.session_state.room_code = code
                    st.session_state.player_name = n
                    st.session_state.screen = "lobby"
                    st.rerun()

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

    code = st.session_state.room_code

    my_names = [p["name"] for p in state["players"]]
    if st.session_state.player_name not in my_names:
        st.warning("You were removed from the room.")
        st.session_state.screen = "home"
        st.session_state.room_code = None
        st.rerun(); st.stop()

    is_host = st.session_state.player_name == state["host"]
    privacy_label = "Private" if state["is_private"] else "Public"

    st.markdown("<div class='wb-title' style='font-size:2rem;'>Lobby</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='wb-section-label'>{privacy_label} room</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='wb-lobby-code'>{code}</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#888;font-size:0.82rem;margin-bottom:1.2rem;'>Share this code with friends</div>",
                unsafe_allow_html=True)

    st.markdown("<div class='wb-section-label'>Players</div>", unsafe_allow_html=True)
    for p in state["players"]:
        crown = " 👑" if p["name"] == state["host"] else ""
        you   = " · you" if p["name"] == st.session_state.player_name else ""
        can_kick = is_host and p["name"] != st.session_state.player_name
        # render the name row as plain HTML — no columns, no Streamlit padding fights
        st.markdown(
            f"<div class='wb-player-row'>"
            f"<span>{p['name']}{crown}</span>"
            f"<span style='color:#888;font-size:0.82rem;'>{you}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if can_kick:
            if st.button("Remove", key=f"kick_{p['name']}"):
                kick_player(code, st.session_state.player_name, p["name"])
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    col_leave, col_start = st.columns([1, 2])

    with col_leave:
        st.markdown("<div class='btn-ghost'>", unsafe_allow_html=True)
        if st.button("Leave"):
            leave_room(code, st.session_state.player_name)
            st.session_state.screen = "home"
            st.session_state.room_code = None
            st.rerun(); st.stop()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_start:
        if is_host:
            if len(state["players"]) < 2:
                st.markdown("<p style='color:#888;font-size:0.88rem;padding-top:0.5rem;'>Need at least 2 players.</p>",
                            unsafe_allow_html=True)
            else:
                if st.button("Start game →"):
                    state = load_room(code)
                    start_game(code, state)
                    st.session_state.screen = "game"
                    st.rerun()
        else:
            st.markdown(f"<p style='color:#888;font-size:0.88rem;padding-top:0.5rem;'>Waiting for {state['host']} to start…</p>",
                        unsafe_allow_html=True)

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

    state   = check_timer(st.session_state.room_code, state)
    my_name = st.session_state.player_name
    cp      = state["players"][state["current_player_idx"]]
    is_my_turn = cp["name"] == my_name and not state["finished"]

    if state["finished"]:
        st.balloons()
        st.markdown(f"<div class='wb-title'>{state['winner']} wins.</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        for p in state["players"]:
            icon = "—" if p["name"] == state["winner"] else "out"
            st.markdown(
                f"<div class='wb-player-row'><span>{p['name']}</span>"
                f"<span style='color:#888;font-size:0.82rem;'>{icon}</span></div>",
                unsafe_allow_html=True
            )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Back to home"):
            st.session_state.screen = "home"
            st.session_state.room_code = None
            st.rerun()
        st.stop()

    render_circle(state, my_name)

    # message banner
    msg = state.get("last_message", "")
    if msg:
        if msg.startswith("good:"):
            text = msg[5:]
            st.markdown(f"<div class='wb-msg wb-msg-good'>{text}</div>", unsafe_allow_html=True)
        elif msg.startswith("eliminated:") or msg.startswith("timeout:"):
            text = msg.split(":", 1)[1]
            st.markdown(f"<div class='wb-msg wb-msg-bad'>{text}</div>", unsafe_allow_html=True)

    if is_my_turn:
        combo = state["current_combo"]
        st.markdown(
            f"<div class='wb-turn-label'>Your turn &mdash; type a word containing "
            f"<span style='font-size:1.1rem;letter-spacing:0.12em;color:#e8a020;'>{combo}</span></div>",
            unsafe_allow_html=True,
        )

        if st.session_state.last_error:
            st.markdown(f"<div class='wb-msg wb-msg-bad'>{st.session_state.last_error}</div>",
                        unsafe_allow_html=True)

        with st.form(key=f"wf_{st.session_state.form_key}", clear_on_submit=True):
            word = st.text_input(
                "word", label_visibility="collapsed",
                placeholder=f"{combo} · type your word here…",
            )
            submitted = st.form_submit_button("Submit →")

        if submitted and word.strip():
            state, result = submit_word(st.session_state.room_code, state, my_name, word.strip())
            if result == "ok":
                st.session_state.form_key += 1
                st.session_state.last_error = ""
            else:
                st.session_state.last_error = result
            st.rerun()
    else:
        st.markdown(
            f"<div class='wb-waiting-label'>Waiting for <strong>{cp['name']}</strong>…</div>",
            unsafe_allow_html=True
        )
        st.session_state.last_error = ""

    st.components.v1.html("""
    <script>
    setTimeout(() => {
        const inputs = window.parent.document.querySelectorAll('input[type="text"]');
        if (inputs.length > 0) inputs[inputs.length - 1].focus();
    }, 200);
    </script>
    """, height=0)

    st_autorefresh(interval=1000, key="game_refresh")