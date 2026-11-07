import html
import os
import requests
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# =========================================================
# F1 LIVE PIT WALL — OPENF1 REAL-TIME (POLLING) + DEMO REPLAY
# Put this file in a `pages/` folder next to app.py.
# =========================================================
st.set_page_config(
    page_title="F1 // Live Pit Wall",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

OPENF1_BASE_URL = "https://api.openf1.org/v1"
OPENF1_TOKEN_URL = "https://api.openf1.org/token"

BG = "#07090c"
BORDER = "#1f2732"
RED = "#e10600"
CYAN = "#51d5e5"
GREEN = "#42d49b"
MUTED = "#7d8997"
WHITE = "#eef2f6"
GOLD = "#e5bd62"
PURPLE = "#b28cff"
GRID = "#151c26"
MONO = "JetBrains Mono, ui-monospace, monospace"
COMPOUND_COLOURS = {
    "SOFT": "#ff3b30", "MEDIUM": "#ffd12e", "HARD": "#f2f2f2",
    "INTERMEDIATE": "#43b02a", "WET": "#2a7de1",
}
FLAG_COLOURS = {
    "GREEN": GREEN, "CLEAR": GREEN, "YELLOW": GOLD, "DOUBLE YELLOW": GOLD,
    "RED": RED, "BLUE": CYAN, "CHEQUERED": "#ffffff", "BLACK AND WHITE": "#cfd7e0",
}

# ------------------------- VISUAL SYSTEM -------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700;800&display=swap');
:root{--bg:#07090c;--border:#1f2732;--red:#e10600;--cyan:#51d5e5;--green:#42d49b;--muted:#7d8997;--white:#eef2f6;--gold:#e5bd62;--purple:#b28cff;}
html, body, [class*="css"]{font-family:Inter,sans-serif;}
.stApp{background:radial-gradient(1100px 520px at 88% -8%,rgba(225,6,0,.17),transparent 62%),radial-gradient(800px 480px at -8% 108%,rgba(81,213,229,.06),transparent 60%),var(--bg);color:var(--white);}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"]{visibility:hidden;display:none;}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1900px;padding:1rem 2.2rem 3rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b0f15,#090c11);border-right:1px solid var(--border);}
h1,h2,h3{font-family:'Barlow Condensed',sans-serif !important;letter-spacing:1px !important;color:var(--white) !important;}
h1{font-size:2.8rem !important;}
[data-testid="stSelectbox"] > div > div{background:#0e141b;border:1px solid #27313d;border-radius:6px;}
[data-testid="stSelectbox"] label, [data-testid="stSlider"] label, [data-testid="stTextInput"] label, [data-testid="stRadio"] label{color:#8a96a4 !important;font-family:'JetBrains Mono',monospace !important;font-size:.62rem !important;font-weight:700 !important;letter-spacing:1.6px;}
[data-testid="stSlider"] [role="slider"]{background:var(--red) !important;}
[data-testid="stAlert"]{background:#10161e;border:1px solid var(--border);border-radius:8px;}
[data-testid="stCaptionContainer"]{color:#6f7c8a;font-size:10.5px;font-family:'JetBrains Mono',monospace;}

div[class*="st-key-panel-"]{background:linear-gradient(180deg,#0e1319,#0a0d12);border:1px solid var(--border);border-radius:12px;padding:16px 18px 12px;box-shadow:inset 0 1px 0 rgba(255,255,255,.035),0 18px 40px -22px rgba(0,0,0,.8);}
.panel-head{display:flex;justify-content:space-between;align-items:center;margin:0 0 10px;}
.panel-title{font-family:'Barlow Condensed',sans-serif;font-size:20px;font-weight:800;letter-spacing:1.2px;color:#e8edf2;display:flex;align-items:center;gap:9px;}
.panel-title:before{content:"";width:7px;height:7px;background:var(--red);box-shadow:0 0 10px var(--red);display:inline-block;}
.panel-tag{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:1.4px;color:var(--muted);border:1px solid var(--border);padding:4px 8px;border-radius:4px;}

.topbar{display:flex;align-items:center;gap:18px;padding:11px 16px;border:1px solid #3a0f0d;border-radius:10px;background:linear-gradient(90deg,rgba(225,6,0,.10),rgba(13,17,23,.9) 40%);box-shadow:0 0 0 1px rgba(225,6,0,.12),0 12px 36px -18px rgba(225,6,0,.55);margin-bottom:16px;flex-wrap:wrap;}
.live{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:800;letter-spacing:1.6px;color:var(--green);display:flex;align-items:center;gap:8px;}
.live i{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.6s infinite;display:inline-block;}
.live.red{color:#ff4b42;} .live.red i{background:#ff2a1f;animation:pulsered 1.2s infinite;}
.live.idle{color:var(--muted);} .live.idle i{background:var(--muted);animation:none;}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(66,212,155,.6);}70%{box-shadow:0 0 0 9px rgba(66,212,155,0);}100%{box-shadow:0 0 0 0 rgba(66,212,155,0);}}
@keyframes pulsered{0%{box-shadow:0 0 0 0 rgba(255,42,31,.7);}70%{box-shadow:0 0 0 10px rgba(255,42,31,0);}100%{box-shadow:0 0 0 0 rgba(255,42,31,0);}}
.tb-div{width:1px;height:26px;background:var(--border);}
.tb-title{font-weight:700;font-size:15px;color:var(--white);line-height:1.1;}
.tb-title small{display:block;font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:500;color:var(--muted);letter-spacing:1.1px;margin-top:3px;}
.chips{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;}
.chip{font-family:'JetBrains Mono',monospace;font-size:9.5px;font-weight:700;letter-spacing:1.1px;color:#aab4c0;border:1px solid var(--border);background:#0b1016;padding:6px 10px;border-radius:5px;}
.chip b{color:var(--white);}
.eyebrow{font-family:'JetBrains Mono',monospace;color:var(--red);font-size:9.5px;font-weight:800;letter-spacing:2.6px;}
.hero-title{font-family:'Barlow Condensed',sans-serif;font-size:58px;line-height:.92;font-weight:900;letter-spacing:1.5px;color:var(--white);margin-top:4px;}
.hero-sub{font-family:'JetBrains Mono',monospace;color:#8d99a8;font-size:10px;letter-spacing:1.6px;margin:12px 0 18px;font-weight:600;}
.muted-note{color:var(--muted);font-size:10px;font-family:'JetBrains Mono',monospace;line-height:1.5;}

.kpi{position:relative;background:linear-gradient(160deg,#131921,#0d1117);border:1px solid var(--border);border-top:2px solid var(--accent,#2a3441);border-radius:10px;padding:14px 16px 12px;min-height:96px;overflow:hidden;}
.kpi-l{font-family:'JetBrains Mono',monospace;color:var(--muted);font-size:9.5px;font-weight:700;letter-spacing:1.6px;}
.kpi-v{font-family:'Barlow Condensed',sans-serif;font-size:36px;font-weight:800;line-height:1.05;color:var(--white);margin-top:6px;}
.kpi-u{font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:700;letter-spacing:1.2px;color:var(--accent,#8a96a4);margin-top:3px;}

/* HUD */
.hud{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;}
.hud-speed{font-family:'Barlow Condensed',sans-serif;font-size:118px;font-weight:900;line-height:.82;color:#fff;letter-spacing:-1px;}
.hud-speed small{font-size:15px;letter-spacing:2px;color:var(--muted);font-family:'JetBrains Mono',monospace;margin-left:8px;font-weight:700;}
.hud-gear{width:108px;height:108px;border:2px solid var(--team,#e10600);border-radius:14px;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(255,255,255,.03);box-shadow:0 0 30px -8px var(--team,#e10600);}
.hud-gear b{font-family:'Barlow Condensed',sans-serif;font-size:76px;line-height:.9;color:#fff;font-weight:900;}
.hud-gear span{font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:1.6px;}
.lights{display:flex;gap:6px;margin:18px 0 14px;}
.led{flex:1;height:11px;border-radius:6px;background:#161e28;}
.led.g{background:#42d49b;box-shadow:0 0 12px #42d49b;}
.led.r{background:#ff3b30;box-shadow:0 0 12px #ff3b30;}
.led.b{background:#7b93ff;box-shadow:0 0 12px #7b93ff;}
.bars{display:grid;gap:10px;}
.barrow{display:grid;grid-template-columns:84px 1fr 56px;align-items:center;gap:10px;font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);letter-spacing:1.2px;}
.barrow b{color:var(--white);text-align:right;font-size:11px;}
.bar{height:11px;border-radius:6px;background:#131a23;overflow:hidden;}
.bar i{display:block;height:100%;border-radius:6px;}
.hud-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;}

/* tower */
.tower{max-height:372px;overflow:auto;border:1px solid var(--border);border-radius:8px;background:#0a0e13;}
.tw-row{display:grid;grid-template-columns:28px 5px 44px 1fr 62px 84px 74px;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid #121820;font-family:'JetBrains Mono',monospace;font-size:11px;color:#c8d0da;}
.tw-head{position:sticky;top:0;background:#0d1219;color:var(--muted);font-size:9px;letter-spacing:1.4px;font-weight:700;z-index:2;}
.tw-row.focus{background:linear-gradient(90deg,rgba(225,6,0,.18),transparent);box-shadow:inset 2px 0 0 var(--red);}
.tw-bar{width:4px;height:18px;border-radius:2px;}
.tw-code{font-weight:800;color:var(--white);letter-spacing:.8px;}
.tw-r{text-align:right;color:#c8d0da;}

.ins{border-left:2px solid var(--c,#51d5e5);padding:9px 12px;background:#0a0f15;margin-bottom:8px;border-radius:0 8px 8px 0;}
.ins-t{font-family:'JetBrains Mono',monospace;font-size:9px;font-weight:800;letter-spacing:1.5px;color:var(--c,#51d5e5);}
.ins-b{font-size:12.5px;color:#cfd7e0;margin-top:3px;line-height:1.45;}
.ins-b b{color:#fff;}

.feed{max-height:560px;overflow:auto;}
.feed-i{display:grid;grid-template-columns:58px 1fr;gap:10px;padding:9px 2px;border-bottom:1px solid #121820;font-size:12px;color:#cfd7e0;line-height:1.4;}
.feed-t{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);}
.feed-f{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:8.5px;font-weight:800;letter-spacing:1.2px;padding:2px 6px;border-radius:3px;margin-right:6px;border:1px solid var(--fc,#2a3441);color:var(--fc,#8a96a4);}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------- DATA ACCESS -------------------------
def api_get(endpoint, params=None, token=None, timeout=15):
    headers = {"accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(f"{OPENF1_BASE_URL}/{endpoint}", params=params or {},
                            headers=headers, timeout=timeout)
    if response.status_code == 404:
        return pd.DataFrame()
    if response.status_code in (401, 403):
        raise PermissionError("OpenF1 refused the request: real-time access needs a valid account token.")
    if response.status_code == 429:
        raise RuntimeError("OpenF1 rate limit hit (HTTP 429). Increase the refresh interval or sign in.")
    response.raise_for_status()
    payload = response.json()
    return pd.DataFrame(payload if isinstance(payload, list) else [])


@st.cache_data(ttl=3000, show_spinner=False)
def fetch_token(username, password):
    response = requests.post(OPENF1_TOKEN_URL, data={"username": username, "password": password}, timeout=20)
    response.raise_for_status()
    return response.json()["access_token"]


@st.cache_data(ttl=3600, show_spinner=False)
def openf1_get(endpoint, params=None):
    response = requests.get(f"{OPENF1_BASE_URL}/{endpoint}", params=params or {}, timeout=45)
    if response.status_code == 404:
        return pd.DataFrame()
    response.raise_for_status()
    return pd.DataFrame(response.json())


@st.cache_data(ttl=3600, show_spinner=False)
def get_openf1_meetings(year):
    data = openf1_get("meetings", {"year": int(year)})
    return data if data.empty else data.drop_duplicates("meeting_key").sort_values("date_start")


@st.cache_data(ttl=3600, show_spinner=False)
def get_openf1_sessions(meeting_key):
    data = openf1_get("sessions", {"meeting_key": int(meeting_key)})
    return data if data.empty else data.sort_values("date_start")


@st.cache_data(ttl=3600, show_spinner=False)
def get_openf1_drivers(session_key):
    data = openf1_get("drivers", {"session_key": int(session_key)})
    if data.empty:
        return data
    if "driver_number" in data:
        data = data.drop_duplicates("driver_number").sort_values("driver_number")
    return data


@st.cache_data(ttl=1800, show_spinner=False)
def get_openf1_laps(session_key, driver_number=None):
    params = {"session_key": int(session_key)}
    if driver_number is not None:
        params["driver_number"] = int(driver_number)
    return openf1_get("laps", params)


def driver_label(row):
    acronym = str(row.get("name_acronym", "") or "").strip()
    full_name = str(row.get("full_name", "") or "").strip()
    number = str(row.get("driver_number", "")).strip()
    team = str(row.get("team_name", "") or "").strip()
    label = acronym or full_name or f"CAR {number}"
    if full_name and full_name != label:
        label += f" — {full_name}"
    if team:
        label += f" ({team})"
    return label


@st.cache_data(ttl=1800, show_spinner="Loading fastest-lap telemetry from OpenF1...")
def load_openf1_telemetry(session_key, driver_number):
    """Fastest valid lap telemetry (used by DEMO REPLAY). Distance is estimated."""
    laps = get_openf1_laps(session_key, driver_number)
    if laps.empty or not {"lap_duration", "date_start"}.issubset(laps.columns):
        return pd.DataFrame()
    laps["lap_duration"] = pd.to_numeric(laps["lap_duration"], errors="coerce")
    valid = laps.dropna(subset=["lap_duration", "date_start"]).copy()
    if "is_pit_out_lap" in valid.columns:
        valid = valid[valid["is_pit_out_lap"].fillna(False) == False]
    if valid.empty:
        return pd.DataFrame()
    fastest = valid.loc[valid["lap_duration"].idxmin()]
    lap_start = pd.to_datetime(fastest["date_start"], utc=True)
    lap_end = lap_start + pd.to_timedelta(float(fastest["lap_duration"]), unit="s")
    car = openf1_get("car_data", {
        "session_key": int(session_key), "driver_number": int(driver_number),
        "date>": lap_start.isoformat(), "date<": lap_end.isoformat(),
    })
    if car.empty:
        return pd.DataFrame()
    car["Date"] = pd.to_datetime(car["date"], utc=True, errors="coerce")
    car = car.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    car = car.rename(columns={"speed": "Speed", "throttle": "Throttle", "brake": "Brake",
                              "rpm": "RPM", "n_gear": "nGear", "drs": "DRS"})
    for col in ["Speed", "Throttle", "Brake", "RPM", "nGear", "DRS"]:
        if col in car:
            car[col] = pd.to_numeric(car[col], errors="coerce")
    if "Speed" not in car:
        return pd.DataFrame()
    if "Brake" not in car:
        car["Brake"] = 0
    car["Brake"] = car["Brake"].fillna(0).gt(0)
    car["Elapsed"] = (car["Date"] - car["Date"].iloc[0]).dt.total_seconds()
    dt = car["Elapsed"].diff().fillna(0).clip(lower=0)
    previous_speed = car["Speed"].shift(1)
    car["Distance"] = ((((previous_speed + car["Speed"]) / 2) / 3.6).fillna(0) * dt).cumsum()
    car["LapNumber"] = int(fastest.get("lap_number", 0) or 0)
    car["LapDuration"] = float(fastest["lap_duration"])
    location = openf1_get("location", {
        "session_key": int(session_key), "driver_number": int(driver_number),
        "date>": lap_start.isoformat(), "date<": lap_end.isoformat(),
    })
    if not location.empty:
        location["Date"] = pd.to_datetime(location["date"], utc=True, errors="coerce")
        location = location.dropna(subset=["Date"]).sort_values("Date")
        location = location.rename(columns={"x": "X", "y": "Y", "z": "Z"})
        loc_cols = ["Date"] + [c for c in ["X", "Y"] if c in location]
        if len(loc_cols) > 1:
            car = pd.merge_asof(car.sort_values("Date"), location[loc_cols].sort_values("Date"),
                                on="Date", direction="nearest", tolerance=pd.Timedelta(seconds=1.5))
    return car.reset_index(drop=True)


# ------------------------- LIVE PREP HELPERS -------------------------
def prep_car(df):
    car = df.copy()
    car["Date"] = pd.to_datetime(car["date"], utc=True, errors="coerce")
    car = car.dropna(subset=["Date"]).rename(columns={
        "speed": "Speed", "throttle": "Throttle", "brake": "Brake",
        "rpm": "RPM", "n_gear": "nGear", "drs": "DRS"})
    for col in ["Speed", "Throttle", "Brake", "RPM", "nGear", "DRS"]:
        if col in car:
            car[col] = pd.to_numeric(car[col], errors="coerce")
    if "Brake" not in car:
        car["Brake"] = 0
    car["Brake"] = car["Brake"].fillna(0).gt(0)
    keep = [c for c in ["Date", "Speed", "Throttle", "Brake", "RPM", "nGear", "DRS"] if c in car]
    return car[keep]


def prep_location(df):
    if df.empty or not {"date", "x", "y"}.issubset(df.columns):
        return pd.DataFrame(columns=["Date", "X", "Y", "driver_number"])
    loc = df.copy()
    loc["Date"] = pd.to_datetime(loc["date"], utc=True, errors="coerce")
    loc = loc.rename(columns={"x": "X", "y": "Y"})
    for col in ["X", "Y"]:
        loc[col] = pd.to_numeric(loc[col], errors="coerce")
    loc = loc.dropna(subset=["Date", "X", "Y"])
    # (0,0) samples are placeholders from the feed
    loc = loc[~((loc["X"] == 0) & (loc["Y"] == 0))]
    cols = [c for c in ["Date", "X", "Y", "driver_number"] if c in loc]
    return loc[cols].sort_values("Date")


# ------------------------- UI HELPERS -------------------------
def esc(value):
    return html.escape(str(value))


def team_colour(row, fallback):
    raw = str(row.get("team_colour", "") or "").strip().lstrip("#")
    return f"#{raw}" if len(raw) == 6 else fallback


def rgba(hex_colour, alpha):
    h = hex_colour.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def panel(name):
    return st.container(key=f"panel-{name}")


def panel_head(title, tag=None):
    tag_html = f'<span class="panel-tag">{esc(tag)}</span>' if tag else ""
    st.markdown(f'<div class="panel-head"><span class="panel-title">{esc(title)}</span>{tag_html}</div>',
                unsafe_allow_html=True)


def kpi_row(items, accents=None):
    cols = st.columns(len(items))
    accents = accents or [None] * len(items)
    for col, (label, value, unit), accent in zip(cols, items, accents):
        col.markdown(
            f'<div class="kpi" style="--accent:{accent or "#2a3441"}"><div class="kpi-l">{esc(label)}</div>'
            f'<div class="kpi-v">{esc(value)}</div><div class="kpi-u">{esc(unit)}</div></div>',
            unsafe_allow_html=True)


def insight_html(tag, text, colour):
    return (f'<div class="ins" style="--c:{colour}"><div class="ins-t">{esc(tag)}</div>'
            f'<div class="ins-b">{text}</div></div>')


def plot_layout(fig, height=320, legend=False, hover="x unified"):
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=26 if legend else 10, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=MONO, color=MUTED, size=10), hovermode=hover,
        hoverlabel=dict(bgcolor="#0b0f14", bordercolor=BORDER, font=dict(family=MONO, size=11, color=WHITE)),
        showlegend=legend,
        legend=dict(orientation="h", y=1.1, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color=WHITE, size=10)),
        uirevision="live",
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER, tickfont=dict(size=9))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=BORDER, tickfont=dict(size=9))
    return fig


def num(row, col, default=0.0):
    if col not in row.index:
        return default
    value = pd.to_numeric(row[col], errors="coerce")
    return default if pd.isna(value) else float(value)


def format_gap(value, leader=False):
    if leader:
        return "LEADER"
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    try:
        return f"+{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def hud_html(speed, gear, rpm, rpm_max, throttle, brake, drs, long_g, colour):
    lit = int(round(15 * min(max((rpm - 8500) / max(rpm_max - 8500, 1), 0), 1)))
    leds = []
    for i in range(15):
        cls = ("g" if i < 5 else "r" if i < 10 else "b") if i < lit else ""
        leds.append(f'<span class="led {cls}"></span>')
    drs_txt = "DRS OPEN" if int(drs) in (10, 12, 14) else "DRS READY" if int(drs) == 8 else "DRS OFF"
    drs_col = GREEN if drs_txt == "DRS OPEN" else GOLD if drs_txt == "DRS READY" else MUTED
    g_col = GREEN if long_g > 0.15 else RED if long_g < -0.15 else MUTED
    gear_txt = "N" if int(gear) == 0 else str(int(gear))
    return (
        f'<div class="hud"><div class="hud-speed">{speed:.0f}<small>KM/H</small></div>'
        f'<div class="hud-gear" style="--team:{colour}"><b>{gear_txt}</b><span>GEAR</span></div></div>'
        f'<div class="lights">{"".join(leds)}</div>'
        f'<div class="bars">'
        f'<div class="barrow"><span>THROTTLE</span><div class="bar"><i style="width:{min(max(throttle,0),100):.0f}%;background:{GREEN}"></i></div><b>{throttle:.0f}%</b></div>'
        f'<div class="barrow"><span>BRAKE</span><div class="bar"><i style="width:{100 if brake else 0}%;background:{RED}"></i></div><b>{"ON" if brake else "OFF"}</b></div>'
        f'<div class="barrow"><span>RPM</span><div class="bar"><i style="width:{min(rpm / max(rpm_max,1) * 100, 100):.0f}%;background:{GOLD}"></i></div><b>{rpm:,.0f}</b></div>'
        f'</div>'
        f'<div class="hud-tags"><span class="chip" style="color:{drs_col}">{drs_txt}</span>'
        f'<span class="chip">LONG G <b style="color:{g_col}">{long_g:+.2f}</b></span></div>'
    )


def live_tower_html(slow, drivers_by_num, focus_number):
    pos = slow.get("position", pd.DataFrame())
    if pos.empty or not {"driver_number", "position", "date"}.issubset(pos.columns):
        return None
    pos = pos.sort_values("date").drop_duplicates("driver_number", keep="last")
    pos["position"] = pd.to_numeric(pos["position"], errors="coerce")
    pos = pos.dropna(subset=["position"]).sort_values("position")

    iv = slow.get("intervals", pd.DataFrame())
    iv_map = {}
    if not iv.empty and {"driver_number", "date"}.issubset(iv.columns):
        iv = iv.sort_values("date").drop_duplicates("driver_number", keep="last")
        iv_map = {int(r["driver_number"]): r for r in iv.to_dict("records")}

    st_df = slow.get("stints", pd.DataFrame())
    stint_map = {}
    if not st_df.empty and {"driver_number", "stint_number"}.issubset(st_df.columns):
        st_df = st_df.sort_values("stint_number").drop_duplicates("driver_number", keep="last")
        stint_map = {int(r["driver_number"]): r for r in st_df.to_dict("records")}

    laps = slow.get("laps", pd.DataFrame())
    cur_lap = {}
    if not laps.empty and {"driver_number", "lap_number"}.issubset(laps.columns):
        laps = laps.copy()
        laps["lap_number"] = pd.to_numeric(laps["lap_number"], errors="coerce")
        cur_lap = laps.groupby("driver_number")["lap_number"].max().to_dict()

    rows = ['<div class="tw-row tw-head"><span>POS</span><span></span><span>CAR</span><span>DRIVER</span>'
            '<span class="tw-r">TYRE</span><span class="tw-r">GAP</span><span class="tw-r">INT</span></div>']
    for rank, r in enumerate(pos.to_dict("records"), start=1):
        num_ = int(r["driver_number"])
        d = drivers_by_num.get(num_, {})
        code = str(d.get("name_acronym") or num_)
        colour = team_colour(d, "#5b6776")
        i = iv_map.get(num_, {})
        tyre = "—"
        s = stint_map.get(num_)
        if s:
            comp = str(s.get("compound") or "").upper()
            lap_start = pd.to_numeric(s.get("lap_start"), errors="coerce")
            age0 = pd.to_numeric(s.get("tyre_age_at_start"), errors="coerce")
            age = ""
            if num_ in cur_lap and not pd.isna(lap_start):
                age = f"·{int((0 if pd.isna(age0) else age0) + max(0, cur_lap[num_] - lap_start))}"
            if comp:
                tyre = f'<span style="color:{COMPOUND_COLOURS.get(comp, MUTED)};font-weight:800">{comp[0]}</span>{age}'
        focus = " focus" if num_ == focus_number else ""
        rows.append(
            f'<div class="tw-row{focus}"><span>{int(r["position"])}</span>'
            f'<span class="tw-bar" style="background:{colour}"></span><span>#{num_}</span>'
            f'<span class="tw-code">{esc(code)}</span><span class="tw-r">{tyre}</span>'
            f'<span class="tw-r">{esc(format_gap(i.get("gap_to_leader"), leader=int(r["position"]) == 1))}</span>'
            f'<span class="tw-r">{esc(format_gap(i.get("interval"), leader=int(r["position"]) == 1))}</span></div>'
        )
    return f'<div class="tower">{"".join(rows)}</div>'


def feed_html(race_control):
    if race_control.empty or "message" not in race_control.columns:
        return None
    rc = race_control.copy()
    if "date" in rc:
        rc["_d"] = pd.to_datetime(rc["date"], utc=True, errors="coerce")
        rc = rc.sort_values("_d")
    items = []
    for r in rc.tail(10).iloc[::-1].to_dict("records"):
        t = ""
        if "_d" in r and not pd.isna(r["_d"]):
            t = r["_d"].strftime("%H:%M:%S")
        flag = str(r.get("flag") or "").upper()
        tag = ""
        if flag and flag != "NONE":
            tag = f'<span class="feed-f" style="--fc:{FLAG_COLOURS.get(flag, MUTED)}">{esc(flag)}</span>'
        items.append(f'<div class="feed-i"><span class="feed-t">{t}</span><span>{tag}{esc(r.get("message", ""))}</span></div>')
    return f'<div class="feed">{"".join(items)}</div>'


# ------------------------- FIGURES -------------------------
def map_figure(snap, focus_colour):
    fig = go.Figure()
    outline = snap["outline"]
    if outline is not None and len(outline) > 2:
        fig.add_trace(go.Scatter(x=outline["X"], y=outline["Y"], mode="lines", hoverinfo="skip",
                                 line=dict(color="rgba(255,255,255,.05)", width=20), showlegend=False))
        fig.add_trace(go.Scatter(x=outline["X"], y=outline["Y"], mode="lines", hoverinfo="skip",
                                 line=dict(color="#263140", width=9), showlegend=False))
    trail = snap["trail"]
    if trail is not None and len(trail) > 1:
        fig.add_trace(go.Scatter(x=trail["X"], y=trail["Y"], mode="lines", hoverinfo="skip",
                                 line=dict(color=focus_colour, width=4), name="TRAIL", showlegend=False))
    for car in snap["cars"]:
        if car["focus"]:
            continue
        fig.add_trace(go.Scatter(
            x=[car["X"]], y=[car["Y"]], mode="markers+text", text=[car["code"]], textposition="top center",
            textfont=dict(family=MONO, size=9, color=WHITE),
            marker=dict(size=10, color=car["colour"], line=dict(color="white", width=.8)),
            hovertemplate=f'{car["code"]}<extra></extra>', showlegend=False))
    for car in snap["cars"]:
        if not car["focus"]:
            continue
        fig.add_trace(go.Scatter(x=[car["X"]], y=[car["Y"]], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=30, color=rgba(car["colour"], .22))))
        fig.add_trace(go.Scatter(
            x=[car["X"]], y=[car["Y"]], mode="markers+text", text=[car["code"]], textposition="top center",
            textfont=dict(family=MONO, size=11, color=WHITE),
            marker=dict(size=15, color=car["colour"], line=dict(color="white", width=2)),
            hovertemplate=f'{car["code"]}<extra></extra>', showlegend=False))
    plot_layout(fig, height=520, hover="closest")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    return fig


def rolling_figure(buf, rival_buf, focus_colour, rival_colour, rival_code, window):
    specs = [("SPEED", "KM/H"), ("THROTTLE / BRAKE", "%"), ("GEAR", ""), ("RPM", "")]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.035)
    fig.add_trace(go.Scatter(x=buf["T"], y=buf["Speed"], mode="lines", name="SPEED",
                             line=dict(color=focus_colour, width=2),
                             hovertemplate="%{y:.0f} km/h<extra></extra>"), row=1, col=1)
    if rival_buf is not None and not rival_buf.empty:
        fig.add_trace(go.Scatter(x=rival_buf["T"], y=rival_buf["Speed"], mode="lines", name=rival_code,
                                 line=dict(color=rival_colour, width=1.6, dash="dot"),
                                 hovertemplate=f"{rival_code}: %{{y:.0f}} km/h<extra></extra>"), row=1, col=1)
    if "Throttle" in buf:
        fig.add_trace(go.Scatter(x=buf["T"], y=buf["Throttle"], mode="lines", name="THROTTLE",
                                 line=dict(color=GREEN, width=1.6), fill="tozeroy",
                                 fillcolor="rgba(66,212,155,.12)",
                                 hovertemplate="THR %{y:.0f}%<extra></extra>"), row=2, col=1)
    fig.add_trace(go.Scatter(x=buf["T"], y=buf["Brake"].astype(int) * 100, mode="lines", name="BRAKE",
                             line=dict(color=RED, width=1.4, shape="hv"), fill="tozeroy",
                             fillcolor="rgba(225,6,0,.22)",
                             hovertemplate="BRAKE %{y:.0f}<extra></extra>"), row=2, col=1)
    if "nGear" in buf:
        fig.add_trace(go.Scatter(x=buf["T"], y=buf["nGear"], mode="lines", name="GEAR",
                                 line=dict(color=PURPLE, width=1.6, shape="hv"),
                                 hovertemplate="GEAR %{y:.0f}<extra></extra>"), row=3, col=1)
    if "RPM" in buf:
        fig.add_trace(go.Scatter(x=buf["T"], y=buf["RPM"], mode="lines", name="RPM",
                                 line=dict(color=GOLD, width=1.6),
                                 hovertemplate="%{y:,.0f} rpm<extra></extra>"), row=4, col=1)
    for i, (label, _) in enumerate(specs, start=1):
        fig.update_yaxes(title_text=label, title_font=dict(size=9), row=i, col=1)
    fig.update_xaxes(range=[-window, 0], title_text="SECONDS AGO", row=4, col=1)
    fig.update_xaxes(showspikes=True, spikemode="across", spikethickness=1, spikecolor="#6b7888", spikedash="solid")
    plot_layout(fig, height=560, legend=True)
    return fig


# ------------------------- SIDEBAR -------------------------
def env_or_secret(name):
    value = os.environ.get(name, "")
    if not value:
        try:
            value = st.secrets.get(name, "")
        except Exception:
            value = ""
    return value


with st.sidebar:
    st.markdown('<div class="eyebrow">F1 PERFORMANCE SYSTEM</div>', unsafe_allow_html=True)
    st.title("LIVE PIT WALL")
    st.caption("REAL-TIME POLLING / OPENF1")
    st.divider()

    env_token = env_or_secret("OPENF1_TOKEN")
    with st.expander("OPENF1 LIVE ACCESS", expanded=False):
        st.caption("Real-time data needs an OpenF1 account. Credentials stay in this session only.")
        user_in = st.text_input("USERNAME / EMAIL", value=env_or_secret("OPENF1_USERNAME"))
        pass_in = st.text_input("PASSWORD", value=env_or_secret("OPENF1_PASSWORD"), type="password")
        token_in = st.text_input("OR ACCESS TOKEN", value=env_token, type="password")

    token = token_in.strip() or None
    token_error = None
    if not token and user_in and pass_in:
        try:
            token = fetch_token(user_in, pass_in)
        except Exception as error:
            token_error = f"Sign-in failed: {error}"
    if token_error:
        st.error(token_error)

    mode = st.radio("MODE", ["LIVE (OPENF1)", "DEMO REPLAY"], index=0 if token else 1, key="mode")
    paused = st.toggle("PAUSE", value=False)
    interval = st.slider("REFRESH (SECONDS)", 1.0, 10.0, 2.0 if mode.startswith("LIVE") else 1.0, 0.5)
    window = st.slider("CHART WINDOW (SECONDS)", 20, 120, 60, 10)
    if mode == "DEMO REPLAY":
        replay_speed = st.slider("REPLAY SPEED (×)", 0.5, 4.0, 1.0, 0.5)
    else:
        replay_speed = 1.0
    st.divider()

    drivers_rows, focus_number, rival_number = [], None, None
    session_key, session_row, meeting_title = None, {}, ""
    sidebar_error = None

    try:
        if mode.startswith("LIVE"):
            sess = api_get("sessions", {"session_key": "latest"}, token)
            if sess.empty:
                sidebar_error = "OpenF1 returned no session."
            else:
                session_row = sess.iloc[-1].to_dict()
                session_key = int(session_row["session_key"])
                meet = api_get("meetings", {"meeting_key": int(session_row["meeting_key"])}, token) if "meeting_key" in session_row else pd.DataFrame()
                meeting_title = str(meet.iloc[-1].get("meeting_name")) if not meet.empty else str(session_row.get("country_name", ""))
                drivers_df = api_get("drivers", {"session_key": session_key}, token)
                if not drivers_df.empty:
                    drivers_df = drivers_df.drop_duplicates("driver_number").sort_values("driver_number")
                    drivers_rows = drivers_df.to_dict("records")
        else:
            years = list(range(2026, 2022, -1))
            year = st.selectbox("SEASON", years, index=2)
            meetings = get_openf1_meetings(year)
            if meetings.empty:
                sidebar_error = "No meetings for this season."
            else:
                meeting_rows = meetings.to_dict("records")
                meeting_labels = [str(r.get("meeting_name") or r.get("country_name")) for r in meeting_rows]
                meeting_label = st.selectbox("GRAND PRIX", meeting_labels)
                meeting_row = meeting_rows[meeting_labels.index(meeting_label)]
                meeting_title = meeting_label
                sessions = get_openf1_sessions(int(meeting_row["meeting_key"]))
                session_rows = sessions.to_dict("records")
                session_labels = [str(r.get("session_name") or "Session") for r in session_rows]
                session_label = st.selectbox("SESSION", session_labels)
                session_row = session_rows[session_labels.index(session_label)]
                session_key = int(session_row["session_key"])
                drivers_rows = get_openf1_drivers(session_key).to_dict("records")
    except PermissionError as error:
        sidebar_error = str(error)
    except Exception as error:
        sidebar_error = f"Could not load session: {error}"

    if drivers_rows:
        labels = [driver_label(r) for r in drivers_rows]
        preferred = next((i for i, r in enumerate(drivers_rows) if str(r.get("name_acronym", "")) == "VER"), 0)
        focus_label = st.selectbox("FOCUS DRIVER", labels, index=preferred)
        focus_row = drivers_rows[labels.index(focus_label)]
        focus_number = int(focus_row["driver_number"])
        if mode == "DEMO REPLAY":
            rivals = [r for r in drivers_rows if int(r["driver_number"]) != focus_number]
            rival_labels = [driver_label(r) for r in rivals]
            default_rival = next((i for i, r in enumerate(rivals) if str(r.get("name_acronym", "")) == "NOR"), 0)
            rival_label = st.selectbox("GHOST RIVAL", rival_labels, index=default_rival)
            rival_row = rivals[rival_labels.index(rival_label)]
            rival_number = int(rival_row["driver_number"])

    st.divider()
    st.markdown("**DATA SOURCE**")
    st.caption("OpenF1 · REST polling" if mode.startswith("LIVE") else "OpenF1 · historical lap replayed as live")
    st.caption("Python / Pandas / Plotly / Streamlit")

# ------------------------- HERO -------------------------
st.markdown('<div class="eyebrow">MOTORSPORT DATA ENGINEERING / 02</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">LIVE <span style="color:#e10600">//</span> PIT WALL</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="hero-sub">{esc((meeting_title or "NO SESSION").upper())} &nbsp; / &nbsp; '
    f'{esc(str(session_row.get("session_name", "")).upper())} &nbsp; / &nbsp; '
    f'{"REAL-TIME POLLING" if mode.startswith("LIVE") else "DEMO REPLAY"}</div>',
    unsafe_allow_html=True,
)

if sidebar_error:
    st.warning(sidebar_error)
    if mode.startswith("LIVE"):
        st.info(
            "OpenF1 only serves real-time data (from 30 minutes before a session to 30 minutes after it) to "
            "signed-in sponsor accounts. Outside that window the latest session is free. "
            "Add your credentials under OPENF1 LIVE ACCESS, or switch MODE to DEMO REPLAY."
        )
    st.stop()
if not drivers_rows or focus_number is None:
    st.info("No driver list is available yet. If a session is live, sign in under OPENF1 LIVE ACCESS; otherwise try DEMO REPLAY.")
    st.stop()

drivers_by_num = {int(r["driver_number"]): r for r in drivers_rows}
focus_colour = team_colour(drivers_by_num[focus_number], RED)
focus_code = str(drivers_by_num[focus_number].get("name_acronym") or focus_number)
rival_colour, rival_code = CYAN, ""
if rival_number is not None:
    rival_colour = team_colour(drivers_by_num[rival_number], CYAN)
    if rival_colour.lower() == focus_colour.lower():
        rival_colour = CYAN
    rival_code = str(drivers_by_num[rival_number].get("name_acronym") or rival_number)

# demo telemetry
demo_tel, demo_rival = pd.DataFrame(), pd.DataFrame()
if mode == "DEMO REPLAY":
    try:
        demo_tel = load_openf1_telemetry(session_key, focus_number)
        demo_rival = load_openf1_telemetry(session_key, rival_number) if rival_number else pd.DataFrame()
    except Exception as error:
        st.error(f"Could not load replay telemetry: {error}")
        st.stop()
    if demo_tel.empty:
        st.warning("No usable telemetry for this driver in this session. Try another driver or session.")
        st.stop()


# ------------------------- SNAPSHOTS -------------------------
SLOW_EVERY = 4


def live_snapshot():
    ss = st.session_state
    now = pd.Timestamp.now(tz="UTC")
    ctx = ("live", session_key, focus_number)
    if ss.get("ctx") != ctx:
        ss["ctx"] = ctx
        ss["buf"] = pd.DataFrame()
        ss["trail"] = pd.DataFrame()
        ss["outline"] = pd.DataFrame()
        ss["slow"] = {}
        ss["tick"] = 0
        ss["peak"] = 0.0
        seed = api_get("location", {"session_key": session_key, "driver_number": focus_number,
                                    "date>": (now - pd.Timedelta(seconds=240)).isoformat()}, token)
        ss["outline"] = prep_location(seed)
    ss["tick"] += 1

    buf = ss["buf"]
    cursor = buf["Date"].max() if not buf.empty else now - pd.Timedelta(seconds=40)
    car = api_get("car_data", {"session_key": session_key, "driver_number": focus_number,
                               "date>": cursor.isoformat()}, token)
    if not car.empty:
        buf = pd.concat([buf, prep_car(car)], ignore_index=True)
        buf = buf.drop_duplicates("Date").sort_values("Date")
        buf = buf[buf["Date"] >= buf["Date"].max() - pd.Timedelta(seconds=130)].reset_index(drop=True)
        ss["buf"] = buf

    locs = prep_location(api_get("location", {"session_key": session_key,
                                              "date>": (now - pd.Timedelta(seconds=6)).isoformat()}, token))
    cars = []
    if not locs.empty and "driver_number" in locs:
        latest = locs.sort_values("Date").drop_duplicates("driver_number", keep="last")
        for r in latest.to_dict("records"):
            n = int(r["driver_number"])
            d = drivers_by_num.get(n, {})
            cars.append({"code": str(d.get("name_acronym") or n), "colour": team_colour(d, "#5b6776"),
                         "X": r["X"], "Y": r["Y"], "focus": n == focus_number})
        mine = locs[locs["driver_number"] == focus_number]
        if not mine.empty:
            ss["trail"] = pd.concat([ss["trail"], mine], ignore_index=True).drop_duplicates("Date").sort_values("Date").tail(160)
            ss["outline"] = pd.concat([ss["outline"], mine], ignore_index=True).drop_duplicates("Date").sort_values("Date").tail(4000)

    if ss["tick"] == 1 or ss["tick"] % SLOW_EVERY == 0:
        slow = {}
        for key, endpoint in [("position", "position"), ("intervals", "intervals"), ("laps", "laps"),
                              ("stints", "stints"), ("race_control", "race_control"), ("weather", "weather")]:
            try:
                slow[key] = api_get(endpoint, {"session_key": session_key}, token)
            except PermissionError:
                raise
            except Exception:
                slow[key] = ss["slow"].get(key, pd.DataFrame())
        ss["slow"] = slow

    out = ss["buf"].copy()
    age = None
    if not out.empty:
        out["T"] = (out["Date"] - out["Date"].max()).dt.total_seconds()
        age = (now - out["Date"].max()).total_seconds()
    return {"mode": "LIVE", "buf": out, "rival_buf": None, "trail": ss["trail"], "outline": ss["outline"],
            "cars": cars, "slow": ss["slow"], "age": age, "gap_m": None, "lap": None}


def demo_snapshot(step):
    ss = st.session_state
    ctx = ("demo", session_key, focus_number, rival_number)
    if ss.get("ctx") != ctx:
        ss["ctx"] = ctx
        ss["demo_t"] = 0.0
        ss["peak"] = 0.0
        ss["tick"] = 0
    lap_len = float(demo_tel["LapDuration"].iloc[0])
    ss["demo_t"] = (ss["demo_t"] + step) % max(lap_len, 1.0)
    t = ss["demo_t"]
    ss["tick"] += 1

    def slice_at(tel):
        upto = tel[tel["Elapsed"] <= t]
        if upto.empty:
            upto = tel.iloc[:1]
        win = upto[upto["Elapsed"] > t - 130].copy()
        win["T"] = win["Elapsed"] - float(upto["Elapsed"].iloc[-1])
        return upto, win

    upto, buf = slice_at(demo_tel)
    cars = []
    if {"X", "Y"}.issubset(upto.columns) and upto[["X", "Y"]].dropna().shape[0]:
        p = upto[["X", "Y"]].dropna().iloc[-1]
        cars.append({"code": focus_code, "colour": focus_colour, "X": p["X"], "Y": p["Y"], "focus": True})
    gap_m, rival_buf = None, None
    if not demo_rival.empty:
        r_upto, rival_buf = slice_at(demo_rival)
        if {"X", "Y"}.issubset(r_upto.columns) and r_upto[["X", "Y"]].dropna().shape[0]:
            p = r_upto[["X", "Y"]].dropna().iloc[-1]
            cars.append({"code": rival_code, "colour": rival_colour, "X": p["X"], "Y": p["Y"], "focus": False})
        gap_m = float(upto["Distance"].iloc[-1] - r_upto["Distance"].iloc[-1])
    trail = upto[["X", "Y"]].dropna().tail(60) if {"X", "Y"}.issubset(upto.columns) else pd.DataFrame()
    outline = demo_tel[["X", "Y"]].dropna() if {"X", "Y"}.issubset(demo_tel.columns) else pd.DataFrame()
    return {"mode": "DEMO", "buf": buf, "rival_buf": rival_buf, "trail": trail, "outline": outline,
            "cars": cars, "slow": {}, "age": 0.0, "gap_m": gap_m,
            "lap": int(demo_tel["LapNumber"].iloc[0]), "t": t, "lap_len": lap_len}


# ------------------------- LIVE VIEW (auto-refreshing fragment) -------------------------
fragment = getattr(st, "fragment", None) or getattr(st, "experimental_fragment")


@fragment(run_every=None if paused else float(interval))
def live_view():
    try:
        snap = live_snapshot() if mode.startswith("LIVE") else demo_snapshot(interval * replay_speed)
    except PermissionError as error:
        st.warning(str(error))
        st.info("Add credentials under OPENF1 LIVE ACCESS, or switch MODE to DEMO REPLAY.")
        return
    except Exception as error:
        st.error(f"Live update failed: {error}")
        return

    ss = st.session_state
    buf = snap["buf"]
    slow = snap["slow"]
    is_live = snap["mode"] == "LIVE"

    # status chips
    stale = is_live and (snap["age"] is None or snap["age"] > 20)
    if not is_live:
        badge = '<span class="live"><i></i>DEMO REPLAY</span>'
    elif stale:
        badge = '<span class="live idle"><i></i>STANDBY · NO LIVE DATA</span>'
    else:
        badge = '<span class="live red"><i></i>LIVE</span>'
    chips = []
    wx = slow.get("weather", pd.DataFrame()) if slow else pd.DataFrame()
    if not wx.empty:
        last_wx = wx.iloc[-1]
        for col, label, unit in [("track_temperature", "TRACK", "°C"), ("air_temperature", "AIR", "°C"),
                                 ("wind_speed", "WIND", "M/S")]:
            v = pd.to_numeric(last_wx.get(col), errors="coerce")
            if not pd.isna(v):
                chips.append(f'<span class="chip">{label} <b>{v:.1f}{unit}</b></span>')
        rain = pd.to_numeric(last_wx.get("rainfall"), errors="coerce")
        if not pd.isna(rain) and rain > 0:
            chips.append('<span class="chip" style="color:#ff6b63;border-color:#4a1512">RAIN</span>')
    rc = slow.get("race_control", pd.DataFrame()) if slow else pd.DataFrame()
    if not rc.empty and "flag" in rc.columns:
        flags = rc[rc["flag"].notna()]
        if not flags.empty:
            f = str(flags.iloc[-1]["flag"]).upper()
            chips.append(f'<span class="chip" style="color:{FLAG_COLOURS.get(f, MUTED)}">FLAG <b style="color:{FLAG_COLOURS.get(f, WHITE)}">{esc(f)}</b></span>')
    chips.append(f'<span class="chip">FOCUS <b>#{focus_number} / {esc(focus_code)}</b></span>')
    st.markdown(
        f'<div class="topbar">{badge}<span class="tb-div"></span>'
        f'<div class="tb-title">{esc(meeting_title)}<small>{esc(str(session_row.get("session_name", "")).upper())}'
        f' · REFRESH {interval:g}s</small></div><div class="chips">{"".join(chips)}</div></div>',
        unsafe_allow_html=True,
    )

    if buf.empty:
        st.info("Waiting for car data… If the session is not live, this panel stays empty — try DEMO REPLAY.")
        return

    last = buf.iloc[-1]
    speed = num(last, "Speed")
    ss["peak"] = max(ss.get("peak", 0.0), speed)
    gear, rpm, throttle = num(last, "nGear"), num(last, "RPM"), num(last, "Throttle")
    brake = bool(last["Brake"]) if "Brake" in last.index else False
    drs = num(last, "DRS")
    rpm_max = max(12000.0, float(pd.to_numeric(buf.get("RPM", pd.Series([0])), errors="coerce").max() or 0))

    long_g = 0.0
    tail = buf.tail(8)
    if len(tail) >= 2:
        dt = float(tail["T"].iloc[-1] - tail["T"].iloc[0])
        if dt > 0.1:
            long_g = ((float(tail["Speed"].iloc[-1]) - float(tail["Speed"].iloc[0])) / 3.6) / dt / 9.81

    lap_val = "—"
    if is_live:
        laps = slow.get("laps", pd.DataFrame())
        if not laps.empty and {"driver_number", "lap_number"}.issubset(laps.columns):
            mine = pd.to_numeric(laps.loc[laps["driver_number"] == focus_number, "lap_number"], errors="coerce").max()
            if not pd.isna(mine):
                lap_val = f"{int(mine)}"
    else:
        lap_val = f"{snap['lap']} (FASTEST)"

    latency = f"{snap['age']:.1f}" if snap["age"] is not None else "—"
    kpi_row(
        [
            ("CURRENT LAP", lap_val, "FOCUS CAR"),
            ("PEAK SPEED", f"{ss['peak']:.0f}", "KM/H · THIS WATCH"),
            ("LONGITUDINAL G", f"{long_g:+.2f}", "ACCEL / BRAKE · FROM SPEED"),
            ("SAMPLES BUFFERED", f"{len(buf):,}", "CAR DATA ROWS"),
            ("DATA LATENCY" if is_live else "LAP PROGRESS", f"{latency}" if is_live else f"{snap['t'] / snap['lap_len'] * 100:.0f}",
             "SECONDS BEHIND NOW" if is_live else "% OF LAP"),
        ],
        accents=[focus_colour, CYAN, GREEN if long_g >= 0 else RED, PURPLE, GOLD],
    )
    st.write("")

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        with panel("livemap"):
            panel_head("LIVE CIRCUIT MAP", f"{len(snap['cars'])} CARS" if snap["cars"] else "TRACKING")
            if snap["cars"] or (snap["outline"] is not None and len(snap["outline"]) > 2):
                st.plotly_chart(map_figure(snap, focus_colour), use_container_width=True,
                                key="live_map", config={"displayModeBar": False})
            else:
                st.info("No location samples yet.")
    with right:
        with panel("hud"):
            panel_head(f"DRIVER HUD / {focus_code}", "CAR DATA")
            st.markdown(hud_html(speed, gear, rpm, rpm_max, throttle, brake, drs, long_g, focus_colour),
                        unsafe_allow_html=True)
        st.write("")
        with panel("side"):
            if is_live:
                panel_head("TIMING TOWER", "POSITION · GAP · TYRE")
                tower = live_tower_html(slow, drivers_by_num, focus_number)
                if tower:
                    st.markdown(tower, unsafe_allow_html=True)
                else:
                    st.info("Timing data is not available yet for this session.")
            else:
                panel_head("GHOST BATTLE", f"{focus_code} VS {rival_code}")
                gap_m = snap["gap_m"]
                if gap_m is not None:
                    ms = max(speed / 3.6, 1.0)
                    ahead = gap_m >= 0
                    st.markdown(
                        insight_html("LIVE GAP", f"<b>{abs(gap_m):.0f} m</b> {'ahead of' if ahead else 'behind'} <b>{esc(rival_code)}</b> "
                                     f"(≈ {abs(gap_m) / ms:.2f} s at current speed).", GREEN if ahead else RED)
                        + insight_html("REPLAY", "Both cars run their fastest lap from the same session, started together at t = 0.", CYAN),
                        unsafe_allow_html=True)
                else:
                    st.info("Pick a ghost rival in the sidebar.")

    st.write("")
    c1, c2 = st.columns([3, 1], gap="large")
    with c1:
        with panel("rolling"):
            panel_head("ROLLING TELEMETRY", f"LAST {window}s")
            st.plotly_chart(
                rolling_figure(buf, snap["rival_buf"], focus_colour, rival_colour, rival_code, window),
                use_container_width=True, key="rolling", config={"displayModeBar": False})
    with c2:
        with panel("feed"):
            panel_head("RACE CONTROL", "MESSAGES")
            feed = feed_html(rc) if is_live else None
            if feed:
                st.markdown(feed, unsafe_allow_html=True)
            elif is_live:
                st.info("No race control messages yet.")
            else:
                st.markdown('<div class="muted-note">Race control messages appear here in LIVE mode.</div>',
                            unsafe_allow_html=True)


live_view()

st.markdown(
    '<hr><div class="muted-note" style="text-align:center;letter-spacing:1.4px;">'
    'F1 LIVE PIT WALL &nbsp; / &nbsp; OPENF1 REAL-TIME POLLING &nbsp; / &nbsp; BUILT WITH PYTHON</div>',
    unsafe_allow_html=True,
)
