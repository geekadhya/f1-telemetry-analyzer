import numpy as np
import pandas as pd
import streamlit as st
import tif1
import matplotlib.pyplot as plt

# =========================================================
# PAGE + VISUAL SYSTEM
# =========================================================
st.set_page_config(
    page_title="F1 // Telemetry Control",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG = "#080a0e"
PANEL = "#11151c"
PANEL_2 = "#171c25"
BORDER = "#29313d"
RED = "#e10600"
CYAN = "#42d6e8"
GREEN = "#38d996"
MUTED = "#84909e"
WHITE = "#f3f5f7"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap');
    :root {{
      --bg:{BG}; --panel:{PANEL}; --panel2:{PANEL_2};
      --border:{BORDER}; --red:{RED}; --cyan:{CYAN};
      --green:{GREEN}; --muted:{MUTED}; --white:{WHITE};
    }}
    html, body, [class*="css"] {{ font-family:Inter,sans-serif; }}
    .stApp {{ background:var(--bg); color:var(--white); }}
    .block-container {{ max-width:1800px; padding:1.15rem 2rem 2.5rem; }}
    [data-testid="stSidebar"] {{ background:#0d1118; border-right:1px solid var(--border); }}
    h1,h2,h3 {{ font-family:'Barlow Condensed',sans-serif !important; letter-spacing:1px !important; color:var(--white) !important; }}
    h1 {{ font-size:2.8rem !important; }}
    h2 {{ font-size:1.8rem !important; }}
    h3 {{ font-size:1.25rem !important; }}
    [data-testid="stMetric"] {{ background:var(--panel); border:1px solid var(--border); border-radius:4px; padding:13px 15px; }}
    [data-testid="stMetricLabel"] {{ color:var(--muted) !important; font-size:.68rem !important; letter-spacing:1.2px; }}
    [data-testid="stMetricValue"] {{ color:var(--white) !important; font-family:'Barlow Condensed',sans-serif !important; font-size:2rem !important; }}
    [data-testid="stTabs"] button {{ color:#aeb8c5 !important; font-weight:700; letter-spacing:.8px; }}
    [data-testid="stTabs"] button[aria-selected="true"] {{ color:white !important; border-bottom:2px solid var(--red) !important; }}
    [data-testid="stSelectbox"] > div > div, [data-testid="stMultiSelect"] > div > div {{ background:var(--panel); border-color:var(--border); }}
    .stButton button,.stDownloadButton button {{ background:var(--red); color:white; border:1px solid var(--red); border-radius:3px; font-weight:800; }}
    hr {{ border-color:var(--border) !important; }}
    .eyebrow {{ color:var(--red); font-size:10px; font-weight:800; letter-spacing:2.5px; }}
    .hero-title {{ font-family:'Barlow Condensed',sans-serif; font-size:42px; line-height:1; font-weight:900; letter-spacing:1.2px; color:var(--white); }}
    .hero-sub {{ color:var(--muted); font-size:11px; letter-spacing:1.4px; margin-top:7px; }}
    .status {{ color:var(--green); font-size:10px; font-weight:800; letter-spacing:1.5px; border:1px solid #285844; padding:7px 10px; }}
    .section-kicker {{ color:var(--red); font-size:10px; font-weight:800; letter-spacing:2px; margin:10px 0 3px; }}
    .panel-title {{ font-family:'Barlow Condensed',sans-serif; font-size:20px; font-weight:800; letter-spacing:1px; margin:0 0 10px; }}
    .mini-label {{ color:var(--muted); font-size:9px; font-weight:700; letter-spacing:1.2px; }}
    .tower {{ width:100%; border-collapse:collapse; font-size:11px; }}
    .tower th {{ color:var(--muted); background:var(--panel2); text-align:left; padding:9px 8px; font-size:9px; letter-spacing:1px; }}
    .tower td {{ padding:10px 8px; border-bottom:1px solid #222a34; }}
    .tower tr:last-child td {{ border-bottom:0; }}
    .tower .driver {{ color:var(--white); font-weight:800; letter-spacing:1px; }}
    .muted-note {{ color:var(--muted); font-size:10px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# DATA ACCESS
# =========================================================
@st.cache_data(show_spinner=False)
def get_event_names(year):
    events = tif1.get_events(year)
    if "EventName" not in events.columns:
        return []
    return events["EventName"].dropna().astype(str).tolist()


@st.cache_data(show_spinner=False)
def get_session_names(year, event_name):
    return list(tif1.get_sessions(year, event_name))


@st.cache_data(show_spinner=False)
def get_driver_codes(year, event_name, session_name):
    session = tif1.get_session(year, event_name, session_name)
    laps = session.laps
    if laps.empty or "Driver" not in laps.columns:
        return []
    return sorted(laps["Driver"].dropna().astype(str).unique().tolist())


@st.cache_data(show_spinner=False)
def load_telemetry(year, event_name, session_name, driver_code):
    session = tif1.get_session(year, event_name, session_name)
    driver = session.get_driver(driver_code)
    data = pd.DataFrame(driver.get_fastest_lap_tel()).copy()
    # Duplicate labels can make data["Speed"] return a DataFrame.
    data = data.loc[:, ~data.columns.duplicated()].copy()
    for col in ("Distance", "Speed", "Throttle", "RPM", "nGear", "X", "Y"):
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    if "Brake" in data.columns:
        data["Brake"] = data["Brake"].fillna(False).astype(bool)
    if "Distance" in data.columns:
        data = data.sort_values("Distance").reset_index(drop=True)
    return data


def clean_trace(data, columns):
    data = data.loc[:, ~data.columns.duplicated()].copy()
    keep = [c for c in columns if c in data.columns]
    if len(keep) != len(columns):
        return pd.DataFrame()
    out = data[keep].copy()
    for col in columns:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.dropna().sort_values(columns[0])


def style_axis(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(PANEL)
    if title:
        ax.set_title(title, loc="left", color=WHITE, fontsize=10, fontweight="bold", pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTED, fontsize=8)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, fontsize=8)
    ax.tick_params(colors=MUTED, labelsize=7)
    ax.grid(True, color=BORDER, linewidth=.5, alpha=.7)
    for spine in ax.spines.values():
        spine.set_color(BORDER)


# =========================================================
# SIDEBAR — SESSION CONTROL
# =========================================================
with st.sidebar:
    st.markdown('<div class="eyebrow">F1 PERFORMANCE SYSTEM</div>', unsafe_allow_html=True)
    st.title("RACE CONTROL")
    st.caption("SESSION CONFIGURATION")
    st.divider()

    available_years = [2026, 2025, 2024, 2023, 2022, 2021]
    year = st.selectbox("SEASON", available_years, index=2)

    try:
        events = get_event_names(year)
        if not events:
            st.error("No events found for this season.")
            st.stop()
        default_event = events.index("Bahrain Grand Prix") if "Bahrain Grand Prix" in events else 0
        event_name = st.selectbox("GRAND PRIX", events, index=default_event)

        sessions = get_session_names(year, event_name)
        if not sessions:
            st.error("No sessions found for this event.")
            st.stop()
        default_session = sessions.index("Qualifying") if "Qualifying" in sessions else 0
        session_name = st.selectbox("SESSION", sessions, index=default_session)

        driver_codes = get_driver_codes(year, event_name, session_name)
        if not driver_codes:
            st.error("No driver data found for this session.")
            st.stop()
        default_driver = driver_codes.index("VER") if "VER" in driver_codes else 0
        driver_code = st.selectbox("FOCUS DRIVER", driver_codes, index=default_driver)
    except Exception as error:
        st.error(f"Could not load session options: {error}")
        st.stop()

    st.divider()
    st.markdown("**DATA SOURCE**")
    st.caption("Fastest-lap telemetry")
    st.caption("Python · Pandas · Matplotlib · Streamlit")

# =========================================================
# LOAD FOCUS DRIVER
# =========================================================
try:
    with st.spinner(f"Loading {driver_code} telemetry..."):
        telemetry = load_telemetry(year, event_name, session_name, driver_code)
except Exception as error:
    st.error(f"Telemetry could not be loaded: {error}")
    st.stop()

if telemetry.empty:
    st.warning("No telemetry is available for this driver.")
    st.stop()

required = ["Distance", "Speed"]
missing = [c for c in required if c not in telemetry.columns]
if missing:
    st.error(f"Telemetry is missing required channels: {missing}")
    st.stop()

# Defensive numeric series
distance = pd.to_numeric(telemetry["Distance"], errors="coerce")
speed = pd.to_numeric(telemetry["Speed"], errors="coerce")
valid_speed = speed.dropna()
if valid_speed.empty:
    st.error("No valid speed samples were returned.")
    st.stop()

top_speed = float(valid_speed.max())
avg_speed = float(valid_speed.mean())
max_rpm = float(pd.to_numeric(telemetry["RPM"], errors="coerce").max()) if "RPM" in telemetry else np.nan
avg_throttle = float(pd.to_numeric(telemetry["Throttle"], errors="coerce").mean()) if "Throttle" in telemetry else np.nan
brake_pct = float(telemetry["Brake"].fillna(False).astype(bool).mean() * 100) if "Brake" in telemetry else np.nan
coverage = float(distance.max() - distance.min()) if distance.notna().any() else np.nan

# =========================================================
# RACE HEADER + KPI RAIL
# =========================================================
head_l, head_r = st.columns([5, 1])
with head_l:
    st.markdown('<div class="eyebrow">MOTORSPORT DATA ENGINEERING / 01</div><div class="hero-title">PIT WALL <span style="color:#e10600">//</span> TELEMETRY</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">{event_name.upper()} &nbsp; / &nbsp; {year} &nbsp; / &nbsp; {session_name.upper()} &nbsp; / &nbsp; FOCUS: {driver_code}</div>', unsafe_allow_html=True)
with head_r:
    st.markdown('<div style="text-align:right;padding-top:14px"><span class="status">● DATA LOADED</span></div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
kpis = st.columns(6)
kpi_items = [
    ("FOCUS DRIVER", driver_code, "FASTEST LAP"),
    ("TOP SPEED", f"{top_speed:.1f}", "KM/H"),
    ("AVERAGE SPEED", f"{avg_speed:.1f}", "KM/H"),
    ("MAX RPM", f"{max_rpm:,.0f}" if np.isfinite(max_rpm) else "—", "RPM"),
    ("THROTTLE MEAN", f"{avg_throttle:.1f}" if np.isfinite(avg_throttle) else "—", "%"),
    ("BRAKE SAMPLES", f"{brake_pct:.1f}" if np.isfinite(brake_pct) else "—", "% OF SAMPLES"),
]
for col, (label, value, help_text) in zip(kpis, kpi_items):
    col.metric(label, value, help_text)

# =========================================================
# RACE OVERVIEW — MAP + TIMING TOWER
# =========================================================
st.markdown('<div class="section-kicker">01 / RACE OVERVIEW</div>', unsafe_allow_html=True)
left, right = st.columns([1.35, 1], gap="large")

with left:
    st.markdown('<div class="panel-title">CIRCUIT POSITION / SPEED TRACE</div>', unsafe_allow_html=True)
    if {"X", "Y", "Speed"}.issubset(telemetry.columns):
        track = telemetry[["X", "Y", "Speed"]].copy()
        track["X"] = pd.to_numeric(track["X"], errors="coerce")
        track["Y"] = pd.to_numeric(track["Y"], errors="coerce")
        track["Speed"] = pd.to_numeric(track["Speed"], errors="coerce")
        track = track.dropna()
        if len(track) > 2:
            fig, ax = plt.subplots(figsize=(8, 5))
            fig.patch.set_facecolor(BG)
            ax.set_facecolor(BG)
            ax.plot(track["X"], track["Y"], color="#303946", linewidth=7, alpha=.75, zorder=1)
            points = ax.scatter(track["X"], track["Y"], c=track["Speed"], cmap="turbo", s=13, zorder=2)
            if "Brake" in telemetry.columns:
                brake_mask = telemetry["Brake"].fillna(False).astype(bool)
                brake_track = telemetry.loc[brake_mask, ["X", "Y"]].dropna()
                if not brake_track.empty:
                    ax.scatter(brake_track["X"], brake_track["Y"], color=RED, s=12, alpha=.85, label="Brake")
            ax.scatter(track["X"].iloc[0], track["Y"].iloc[0], color="white", marker="s", s=45, zorder=3, label="Start / finish")
            ax.set_aspect("equal", adjustable="datalim")
            ax.axis("off")
            cb = fig.colorbar(points, ax=ax, fraction=.035, pad=.02)
            cb.set_label("SPEED KM/H", color=MUTED, fontsize=8)
            cb.ax.yaxis.set_tick_params(color=MUTED, labelsize=7)
            plt.setp(cb.ax.get_yticklabels(), color=MUTED)
            fig.tight_layout(pad=.2)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
        else:
            st.info("Not enough coordinate samples to draw the circuit.")
    else:
        st.info("Circuit coordinates are not available in this session.")

with right:
    st.markdown('<div class="panel-title">SESSION TIMING TOWER</div>', unsafe_allow_html=True)
    timing_rows = []
    for code in driver_codes:
        try:
            d = load_telemetry(year, event_name, session_name, code)
            if d.empty or "Speed" not in d.columns:
                continue
            s = pd.to_numeric(d["Speed"], errors="coerce").dropna()
            if s.empty:
                continue
            lap_time = "—"
            if "Time" in d.columns:
                t = pd.to_timedelta(d["Time"], errors="coerce").dropna()
                if not t.empty:
                    secs = t.max().total_seconds()
                    lap_time = f"{int(secs // 60)}:{secs % 60:06.3f}"
            timing_rows.append({"DRIVER": code, "LAP TIME": lap_time, "TOP SPEED": f"{s.max():.1f}"})
        except Exception:
            continue

    if timing_rows:
        # This is a telemetry-derived display, not an official classification.
        timing_df = pd.DataFrame(timing_rows)
        timing_df["_sort"] = pd.to_timedelta(timing_df["LAP TIME"], errors="coerce")
        timing_df = timing_df.sort_values("_sort", na_position="last").drop(columns="_sort")
        html = '<table class="tower"><thead><tr><th>POS</th><th>DRIVER</th><th>FASTEST LAP*</th><th>TOP SPEED</th></tr></thead><tbody>'
        for pos, row in enumerate(timing_df.to_dict("records"), start=1):
            html += f'<tr><td>{pos:02}</td><td class="driver">{row["DRIVER"]}</td><td>{row["LAP TIME"]}</td><td>{row["TOP SPEED"]}</td></tr>'
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)
        st.markdown('<div class="muted-note">*Derived from each driver telemetry time series; not official timing classification.</div>', unsafe_allow_html=True)
    else:
        st.info("Timing tower data is unavailable.")

# =========================================================
# WORKSPACE TABS — NO MORE LONG STACK OF PANELS
# =========================================================
st.markdown('<div class="section-kicker">02 / ENGINEERING WORKSPACE</div>', unsafe_allow_html=True)
tab_overview, tab_telemetry, tab_battle, tab_braking, tab_corners, tab_export = st.tabs(
    ["OVERVIEW", "TELEMETRY", "DRIVER BATTLE", "BRAKING", "CORNER ANALYSIS", "EXPORT"]
)

# ---------------------------------------------------------
# OVERVIEW TAB
# ---------------------------------------------------------
with tab_overview:
    st.markdown('<div class="panel-title">CAR SYSTEMS / FASTEST LAP CHANNELS</div>', unsafe_allow_html=True)
    channel_specs = [
        ("SPEED", "Speed", "KM/H", CYAN),
        ("THROTTLE", "Throttle", "%", GREEN),
        ("BRAKE", "Brake", "ON / OFF", RED),
        ("ENGINE RPM", "RPM", "RPM", "#e5bd55"),
        ("GEAR", "nGear", "GEAR", "#b28cff"),
        ("DRS", "DRS", "STATE", "#84909e"),
    ]
    fig, axes = plt.subplots(3, 2, figsize=(13, 7), sharex=True)
    fig.patch.set_facecolor(BG)
    for ax, (label, column, unit, color) in zip(axes.flat, channel_specs):
        style_axis(ax, label, "DISTANCE (M)" if ax in axes[-1] else None, unit)
        if column not in telemetry.columns:
            ax.text(.5, .5, "CHANNEL UNAVAILABLE", transform=ax.transAxes, ha="center", color=MUTED)
            continue
        frame = pd.DataFrame({
            "Distance": pd.to_numeric(telemetry["Distance"], errors="coerce"),
            "Value": telemetry[column],
        })
        if column == "Brake":
            frame["Value"] = frame["Value"].fillna(False).astype(bool).astype(int)
        else:
            frame["Value"] = pd.to_numeric(frame["Value"], errors="coerce")
        frame = frame.dropna().sort_values("Distance")
        if frame.empty:
            ax.text(.5, .5, "NO VALID DATA", transform=ax.transAxes, ha="center", color=MUTED)
            continue
        ax.plot(frame["Distance"], frame["Value"], color=color, linewidth=1.15)
        if column == "Brake":
            ax.fill_between(frame["Distance"], 0, frame["Value"], color=color, alpha=.16)
        ax.text(.98, .88, f"{frame['Value'].iloc[-1]:.0f} {unit}", transform=ax.transAxes,
                ha="right", color=WHITE, fontsize=8, fontweight="bold")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    rail = st.columns(6)
    rail_data = [
        ("AVG SPEED", f"{avg_speed:.1f}", "KM/H"),
        ("TOP SPEED", f"{top_speed:.1f}", "KM/H"),
        ("AVG THROTTLE", f"{avg_throttle:.1f}" if np.isfinite(avg_throttle) else "—", "%"),
        ("MAX RPM", f"{max_rpm:.0f}" if np.isfinite(max_rpm) else "—", "RPM"),
        ("BRAKE ACTIVITY", f"{brake_pct:.1f}" if np.isfinite(brake_pct) else "—", "%"),
        ("LAP COVERAGE", f"{coverage:.0f}" if np.isfinite(coverage) else "—", "M"),
    ]
    for col, (label, value, unit) in zip(rail, rail_data):
        col.metric(label, value, unit)

# ---------------------------------------------------------
# TELEMETRY TAB
# ---------------------------------------------------------
with tab_telemetry:
    st.markdown('<div class="panel-title">TELEMETRY CHANNEL EXPLORER</div>', unsafe_allow_html=True)
    available_channels = [c for c in ["Speed", "Throttle", "Brake", "RPM", "nGear", "DRS", "AccelerationX", "AccelerationY"] if c in telemetry.columns]
    selected_channel = st.selectbox("SELECT CHANNEL", available_channels, key="explorer_channel")
    if selected_channel:
        x = pd.to_numeric(telemetry["Distance"], errors="coerce")
        y = telemetry[selected_channel]
        if selected_channel == "Brake":
            y = y.fillna(False).astype(bool).astype(int)
        else:
            y = pd.to_numeric(y, errors="coerce")
        chart_data = pd.DataFrame({"Distance": x, "Value": y}).dropna().sort_values("Distance")
        fig, ax = plt.subplots(figsize=(13, 4))
        fig.patch.set_facecolor(BG)
        style_axis(ax, selected_channel.upper(), "DISTANCE (M)", selected_channel.upper())
        ax.plot(chart_data["Distance"], chart_data["Value"], color=CYAN, linewidth=1.5)
        if selected_channel == "Brake":
            ax.fill_between(chart_data["Distance"], 0, chart_data["Value"], color=RED, alpha=.18)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    st.markdown('<div class="panel-title">SPEED PROFILE / BRAKING ZONES</div>', unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(13, 4))
    fig.patch.set_facecolor(BG)
    style_axis(ax, "SPEED THROUGH LAP", "DISTANCE (M)", "SPEED (KM/H)")
    trace = pd.DataFrame({"Distance": distance, "Speed": speed}).dropna().sort_values("Distance")
    ax.plot(trace["Distance"], trace["Speed"], color=CYAN, linewidth=1.5)
    if "Brake" in telemetry.columns:
        brake_points = telemetry.loc[telemetry["Brake"].fillna(False).astype(bool), ["Distance", "Speed"]].dropna()
        if not brake_points.empty:
            ax.scatter(brake_points["Distance"], brake_points["Speed"], color=RED, s=9, label="Brake active")
            ax.legend(frameon=False, labelcolor=WHITE, fontsize=8)
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# ---------------------------------------------------------
# DRIVER BATTLE TAB
# ---------------------------------------------------------
with tab_battle:
    st.markdown('<div class="panel-title">DRIVER BATTLE / FASTEST LAP COMPARISON</div>', unsafe_allow_html=True)
    rivals = [d for d in driver_codes if d != driver_code]
    if rivals:
        rival_driver = st.selectbox("COMPARISON DRIVER", rivals, key="battle_driver")
        try:
            rival = load_telemetry(year, event_name, session_name, rival_driver)
            rival_speed = pd.to_numeric(rival["Speed"], errors="coerce").dropna()
            focus_trace = clean_trace(telemetry, ["Distance", "Speed"]).drop_duplicates("Distance")
            rival_trace = clean_trace(rival, ["Distance", "Speed"]).drop_duplicates("Distance")
            if len(focus_trace) >= 2 and len(rival_trace) >= 2:
                lo = max(focus_trace["Distance"].min(), rival_trace["Distance"].min())
                hi = min(focus_trace["Distance"].max(), rival_trace["Distance"].max())
                common_x = np.linspace(lo, hi, 500)
                focus_y = np.interp(common_x, focus_trace["Distance"], focus_trace["Speed"])
                rival_y = np.interp(common_x, rival_trace["Distance"], rival_trace["Speed"])
                delta = focus_y - rival_y

                m1, m2, m3, m4 = st.columns(4)
                m1.metric(f"{driver_code} TOP SPEED", f"{top_speed:.1f} KM/H")
                m2.metric(f"{rival_driver} TOP SPEED", f"{rival_speed.max():.1f} KM/H")
                m3.metric("MEAN SPEED DELTA", f"{np.mean(delta):+.1f} KM/H")
                m4.metric("MAX ADVANTAGE", f"{np.max(np.abs(delta)):.1f} KM/H")

                fig, ax = plt.subplots(figsize=(13, 4))
                fig.patch.set_facecolor(BG)
                style_axis(ax, f"SPEED DELTA / {driver_code} MINUS {rival_driver}", "DISTANCE (M)", "DELTA (KM/H)")
                ax.axhline(0, color=MUTED, linewidth=.8)
                ax.plot(common_x, delta, color=CYAN, linewidth=1.5)
                ax.fill_between(common_x, 0, delta, where=delta >= 0, color=GREEN, alpha=.18)
                ax.fill_between(common_x, 0, delta, where=delta < 0, color=RED, alpha=.18)
                fig.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

                fig, ax = plt.subplots(figsize=(13, 4))
                fig.patch.set_facecolor(BG)
                style_axis(ax, "PACE OVER LAP DISTANCE", "DISTANCE (M)", "SPEED (KM/H)")
                ax.plot(focus_trace["Distance"], focus_trace["Speed"], color=RED, label=driver_code, linewidth=1.4)
                ax.plot(rival_trace["Distance"], rival_trace["Speed"], color=CYAN, label=rival_driver, linewidth=1.4)
                ax.legend(frameon=False, labelcolor=WHITE)
                fig.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)
            else:
                st.warning("Not enough overlapping distance samples to compare these drivers.")
        except Exception as error:
            st.error(f"Could not compare drivers: {error}")
    else:
        st.info("No other drivers are available for comparison.")

# ---------------------------------------------------------
# BRAKING TAB
# ---------------------------------------------------------
with tab_braking:
    st.markdown('<div class="panel-title">BRAKING EVENT ANALYSIS</div>', unsafe_allow_html=True)
    if "Brake" not in telemetry.columns:
        st.info("Brake channel unavailable.")
    else:
        brake_frame = pd.DataFrame({
            "Distance": pd.to_numeric(telemetry["Distance"], errors="coerce"),
            "Speed": pd.to_numeric(telemetry["Speed"], errors="coerce"),
            "Brake": telemetry["Brake"].fillna(False).astype(bool),
        }).dropna(subset=["Distance", "Speed"])
        brake_frame["Event"] = (brake_frame["Brake"] != brake_frame["Brake"].shift()).cumsum()
        events = brake_frame[brake_frame["Brake"]].groupby("Event").agg(
            Start_Distance=("Distance", "min"),
            End_Distance=("Distance", "max"),
            Entry_Speed=("Speed", "first"),
            Exit_Speed=("Speed", "last"),
            Samples=("Speed", "size"),
        )
        if not events.empty:
            events["Distance_m"] = events["End_Distance"] - events["Start_Distance"]
            events["Speed_Reduction"] = events["Entry_Speed"] - events["Exit_Speed"]
            events = events.sort_values("Speed_Reduction", ascending=False)
            st.dataframe(events.round(2), use_container_width=True)
            fig, ax = plt.subplots(figsize=(13, 4))
            fig.patch.set_facecolor(BG)
            style_axis(ax, "SPEED REDUCTION BY BRAKING EVENT", "EVENT", "SPEED REDUCTION (KM/H)")
            ax.bar(range(1, len(events) + 1), events["Speed_Reduction"], color=RED, width=.65)
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.caption("Events are contiguous brake-active telemetry samples, not official braking zones.")
        else:
            st.info("No brake-active events were detected.")

# ---------------------------------------------------------
# CORNER ANALYSIS TAB
# ---------------------------------------------------------
with tab_corners:
    st.markdown('<div class="panel-title">CORNER / TRACK SECTION INSPECTOR</div>', unsafe_allow_html=True)
    if "Distance" in telemetry and "Speed" in telemetry:
        valid = pd.DataFrame({"Distance": distance, "Speed": speed}).dropna().sort_values("Distance")
        if len(valid) >= 3:
            start = float(valid["Distance"].min())
            end = float(valid["Distance"].max())
            c1, c2 = st.columns(2)
            with c1:
                section_start = st.slider("SECTION START (M)", start, end, float(start), key="corner_start")
            with c2:
                section_end = st.slider("SECTION END (M)", start, end, float(end), key="corner_end")
            if section_start < section_end:
                section = valid[valid["Distance"].between(section_start, section_end)]
                if not section.empty:
                    apex = section.loc[section["Speed"].idxmin()]
                    a, b, c = st.columns(3)
                    a.metric("MINIMUM SPEED", f"{apex['Speed']:.1f} KM/H")
                    b.metric("APEX DISTANCE", f"{apex['Distance']:.0f} M")
                    c.metric("SECTION SAMPLES", len(section))
                    fig, ax = plt.subplots(figsize=(13, 4))
                    fig.patch.set_facecolor(BG)
                    style_axis(ax, "SELECTED TRACK SECTION", "DISTANCE (M)", "SPEED (KM/H)")
                    ax.plot(section["Distance"], section["Speed"], color=CYAN, linewidth=1.5)
                    ax.scatter([apex["Distance"]], [apex["Speed"]], color=RED, s=45, zorder=3)
                    fig.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
            else:
                st.info("Section end must be greater than section start.")
        else:
            st.info("Not enough samples for section analysis.")
    else:
        st.info("Distance or speed data is unavailable.")

# ---------------------------------------------------------
# EXPORT TAB
# ---------------------------------------------------------
with tab_export:
    st.markdown('<div class="panel-title">DATA EXPORT</div>', unsafe_allow_html=True)
    st.write("Download the selected driver's fastest-lap telemetry and the detected braking events.")
    st.download_button(
        "DOWNLOAD TELEMETRY CSV",
        data=telemetry.to_csv(index=False).encode("utf-8"),
        file_name=f"{year}_{event_name.replace(' ', '_')}_{session_name}_{driver_code}_telemetry.csv",
        mime="text/csv",
        use_container_width=True,
    )
    if "Brake" in telemetry.columns:
        export_brakes = telemetry.loc[telemetry["Brake"].fillna(False).astype(bool)].copy()
        st.download_button(
            "DOWNLOAD BRAKE SAMPLES CSV",
            data=export_brakes.to_csv(index=False).encode("utf-8"),
            file_name=f"{driver_code}_brake_samples.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.markdown(
    '<hr><div class="muted-note" style="text-align:center;letter-spacing:1px;">F1 TELEMETRY CONTROL &nbsp; / &nbsp; FASTEST-LAP DATA &nbsp; / &nbsp; BUILT WITH PYTHON</div>',
    unsafe_allow_html=True,
)
