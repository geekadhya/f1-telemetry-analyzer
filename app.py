import numpy as np
import streamlit as st
import tif1
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="F1 Telemetry Analyzer",
    page_icon="🏎️",
    layout="wide"
)

BG = "#0e1117"
BLUE = "#38bdf8"
RED = "#ff4545"
MUTED = "#555b66"

def style_chart(ax, title, xlabel, ylabel):
    ax.set_facecolor("#0e1117")

    ax.set_title(title, color="white", fontsize=14,
                 fontweight="bold", pad=15)

    ax.set_xlabel(xlabel, color="#aab2c0")
    ax.set_ylabel(ylabel, color="#aab2c0")
    ax.tick_params(colors="#aab2c0")

    ax.grid(True, color="#343a46", linestyle="--",
            linewidth=0.6, alpha=0.6)

    for spine in ax.spines.values():
        spine.set_color("#343a46")

# =========================================================
# DASHBOARD DESIGN SYSTEM
# =========================================================

st.markdown("""
<style>

/* Main application */
.stApp {
    background: #090b10;
    color: #f5f5f5;
}

/* Main content spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #10131a;
    border-right: 1px solid #252a35;
}

/* Main headings */
h1, h2, h3 {
    color: #f5f5f5 !important;
    font-weight: 750 !important;
    letter-spacing: -0.8px;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #141821;
    border: 1px solid #292f3b;
    border-radius: 10px;
    padding: 18px;
}

/* Metric labels */
[data-testid="stMetricLabel"] {
    color: #929baa !important;
    font-size: 13px;
}

/* Metric values */
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 750;
}

/* Select boxes */
[data-testid="stSelectbox"] {
    margin-bottom: 12px;
}

/* Dividers */
hr {
    border-color: #292f3b !important;
}

/* Buttons */
.stDownloadButton button {
    background: #e10600;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 650;
}

.stDownloadButton button:hover {
    background: #ff2922;
    color: white;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid #292f3b;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data(show_spinner=False)
def get_event_names(year):
    events = tif1.get_events(year)
    return events["EventName"].dropna().tolist()


@st.cache_data(show_spinner=False)
def get_session_names(year, event_name):
    return tif1.get_sessions(year, event_name)


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
    telemetry = driver.get_fastest_lap_tel()

    # Return a plain pandas DataFrame for Streamlit caching.
    return pd.DataFrame(telemetry).copy()


# =========================================================
# SIDEBAR: SESSION SELECTORS
# =========================================================

with st.sidebar:
    st.title("🏎️ F1 ANALYTICS")
    st.caption("RACE PERFORMANCE SYSTEM")
    st.divider()

    st.markdown("### Select a session")

    available_years = [2026, 2025, 2024, 2023, 2022, 2021]
    year = st.selectbox(
        "Season",
        available_years,
        index=2
    )

    try:
        event_names = get_event_names(year)

        if not event_names:
            st.error("No events were returned for this season.")
            st.stop()

        default_event = (
            event_names.index("Bahrain Grand Prix")
            if "Bahrain Grand Prix" in event_names
            else 0
        )

        event_name = st.selectbox(
            "Grand Prix",
            event_names,
            index=default_event
        )

        session_names = get_session_names(year, event_name)

        if not session_names:
            st.error("No sessions are listed for this event.")
            st.stop()

        default_session = (
            session_names.index("Qualifying")
            if "Qualifying" in session_names
            else 0
        )

        session_name = st.selectbox(
            "Session",
            session_names,
            index=default_session
        )

        driver_codes = get_driver_codes(
            year,
            event_name,
            session_name
        )

        if not driver_codes:
            st.error("No driver data is available for this session.")
            st.stop()

        default_driver = (
            driver_codes.index("VER")
            if "VER" in driver_codes
            else 0
        )

        driver_code = st.selectbox(
            "Driver",
            driver_codes,
            index=default_driver
        )

    except Exception as error:
        st.error(f"Could not load the session options: {error}")
        st.stop()

    st.divider()
    st.markdown("### Analysis Modules")
    st.caption("01 · Speed and telemetry")
    st.caption("02 · Driver inputs")
    st.caption("03 · Gear and RPM")
    st.caption("04 · Braking analysis")
    st.caption("05 · Corner inspector")
    st.caption("06 · Section comparison")
    st.divider()
    st.caption("Built with Python · Pandas · Streamlit")


# =========================================================
# LOAD SELECTED DRIVER TELEMETRY
# =========================================================

try:
    with st.spinner(
        f"Loading {driver_code} telemetry for {event_name}..."
    ):
        telemetry = load_telemetry(
            year,
            event_name,
            session_name,
            driver_code
        )

except Exception as error:
    st.error(
        "Telemetry could not be loaded for this selection. "
        "Try another session or driver."
    )
    st.exception(error)
    st.stop()

if telemetry.empty:
    st.warning("The selected driver has no telemetry for this session.")
    st.stop()

required_columns = [
    "Distance", "Speed", "Throttle", "Brake", "RPM",
    "nGear", "X", "Y", "SessionTime"
]

missing_columns = [
    column for column in required_columns
    if column not in telemetry.columns
]

if missing_columns:
    st.error(f"Telemetry is missing required columns: {missing_columns}")
    st.stop()

telemetry = telemetry.sort_values("Distance").reset_index(drop=True)


# =========================================================
# DASHBOARD HEADER
# =========================================================

st.markdown("""
<div style="margin-bottom: 5px;">
    <span style="
        color: #e10600;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 3px;
    ">
        MOTORSPORT INTELLIGENCE
    </span>
</div>

<h1 style="
    font-size: 42px;
    font-weight: 850;
    letter-spacing: -2px;
    margin: 0;
">
    TELEMETRY <span style="color:#e10600;">//</span> ANALYZER
</h1>

<p style="
    color: #929baa;
    font-size: 14px;
    margin-top: 8px;
">
    Race performance · Driver behaviour · Circuit intelligence
</p>
""", unsafe_allow_html=True)
st.caption(
    f"{event_name.upper()} | {year} | "
    f"{session_name.upper()} | DRIVER: {driver_code}"
)
st.divider()


# =========================================================
# TOP PERFORMANCE METRICS
# =========================================================

metric_cols = st.columns(4)

metric_cols[0].metric(
    "Top Speed",
    f"{telemetry['Speed'].max():.1f} km/h"
)

metric_cols[1].metric(
    "Average Speed",
    f"{telemetry['Speed'].mean():.1f} km/h"
)

metric_cols[2].metric(
    "Maximum RPM",
    f"{telemetry['RPM'].max():,.0f}"
)

metric_cols[3].metric(
    "Telemetry Points",
    f"{len(telemetry):,}"
)


# =========================================================
# SPEED ANALYSIS
# =========================================================

st.subheader("Speed Analysis")

fig, ax = plt.subplots(figsize=(13, 4))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.plot(
    telemetry["Distance"],
    telemetry["Speed"],
    color=BLUE,
    linewidth=1.8
)
# Highlight braking points
braking_points = telemetry[
    telemetry["Brake"] == True
]

ax.scatter(
    braking_points["Distance"],
    braking_points["Speed"],
    color="#e10600",
    s=12,
    label="Braking zones",
    zorder=3
)

ax.legend(
    facecolor="#141821",
    edgecolor="#343a46",
    labelcolor="white"
)

style_chart(
    ax,
    "SPEED PROFILE",
    "Distance (metres)",
    "Speed (km/h)"
)

ax.set_xlabel("Distance (metres)", color="white")
ax.set_ylabel("Speed (km/h)", color="white")
ax.set_title("Speed Profile", color="white")
ax.tick_params(colors="white")
ax.grid(alpha=0.2)

for spine in ax.spines.values():
    spine.set_color("#444b56")

fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)



# =========================================================
# INTERACTIVE TELEMETRY EXPLORER
# =========================================================

st.subheader("Telemetry Explorer")

available_channels = [
    column for column in [
        "Speed", "Throttle", "RPM", "nGear",
        "AccelerationX", "AccelerationY", "AccelerationZ",
        "DRS"
    ]
    if column in telemetry.columns
]

selected_channel = st.selectbox(
    "Select telemetry channel",
    available_channels
)

st.line_chart(
    telemetry,
    x="Distance",
    y=selected_channel,
    x_label="Distance (metres)",
    y_label=selected_channel
)


# =========================================================
# THROTTLE & BRAKING ANALYSIS
# =========================================================

st.divider()
st.subheader("Throttle & Braking Analysis")

brake_data = telemetry["Brake"].fillna(False).astype(bool)

fig, ax = plt.subplots(figsize=(14, 5))

ax.plot(
    telemetry["Distance"],
    telemetry["Throttle"],
    label="Throttle (%)",
    color="#22c55e",
    linewidth=1.6
)

ax.fill_between(
    telemetry["Distance"],
    0,
    brake_data.astype(int) * 100,
    step="mid",
    alpha=0.2,
    color="#ef4444",
    label="Brake applied"
)

ax.set_xlabel("Distance (metres)")
ax.set_ylabel("Throttle (%)")
ax.set_ylim(0, 105)
ax.set_title("Driver Throttle and Braking Behaviour")
ax.legend()
ax.grid(alpha=0.25)

st.pyplot(fig)
plt.close(fig)
# =========================================================
# RPM & GEAR ANALYSIS
# =========================================================

st.divider()
st.subheader("RPM & Gear Analysis")

fig, ax1 = plt.subplots(figsize=(14, 5))

ax1.plot(
    telemetry["Distance"],
    telemetry["RPM"],
    color="#38bdf8",
    linewidth=1.5,
    label="RPM"
)

ax1.set_xlabel("Distance (metres)")
ax1.set_ylabel("Engine RPM")
ax1.grid(alpha=0.25)

ax2 = ax1.twinx()

ax2.step(
    telemetry["Distance"],
    telemetry["nGear"],
    where="mid",
    color="#f59e0b",
    linewidth=1.4,
    label="Gear"
)

ax2.set_ylabel("Gear")
ax2.set_yticks(range(1, 9))

ax1.set_title("Engine RPM and Gear Changes")

fig.legend(loc="upper right", bbox_to_anchor=(0.9, 0.9))

st.pyplot(fig)
plt.close(fig)
# =========================================================
# BRAKING EVENT DETECTION
# =========================================================

st.divider()
st.subheader("Braking Event Analysis")

braking_data = telemetry.copy()

braking_data["Brake"] = (
    braking_data["Brake"]
    .fillna(False)
    .astype(bool)
)

braking_data["Brake_Event"] = (
    braking_data["Brake"]
    .ne(braking_data["Brake"].shift())
    .cumsum()
)

braking_only = braking_data[
    braking_data["Brake"]
].copy()

braking_summary = (
    braking_only.groupby("Brake_Event")
    .agg(
        Start_Distance=("Distance", "first"),
        End_Distance=("Distance", "last"),
        Start_Speed=("Speed", "first"),
        End_Speed=("Speed", "last"),
        Readings=("Speed", "count")
    )
)

braking_summary["Braking_Distance"] = (
    braking_summary["End_Distance"]
    - braking_summary["Start_Distance"]
)

braking_summary = braking_summary.round(2)

st.dataframe(
    braking_summary,
    use_container_width=True
)

st.caption(
    "Events are identified from consecutive brake-active telemetry samples. "
    "Distances are measured between the first and last brake-active readings."
)

# =========================================================
# DRIVER COMPARISON
# =========================================================

st.divider()
st.subheader("🏁 Driver Performance Comparison")

comparison_drivers = [
    driver for driver in driver_codes
    if driver != driver_code
]

if comparison_drivers:

    comparison_driver = st.selectbox(
        "Select another driver",
        comparison_drivers,
        key="comparison_driver_select"
    )

    try:
        with st.spinner(f"Loading {comparison_driver} telemetry..."):

            
            second_telemetry = load_telemetry(
             year,
             event_name,
             session_name,
             comparison_driver
            )
        if not second_telemetry.empty:

            # Normalize distance to lap progress (0–100%)
            def get_lap_progress(data):
                if "RelativeDistance" in data.columns:
                    return data["RelativeDistance"] * 100

                distance = data["Distance"]
                lap_length = distance.max() - distance.min()

                return (
                    (distance - distance.min()) / lap_length
                ) * 100

            first_progress = get_lap_progress(telemetry)
            second_progress = get_lap_progress(second_telemetry)

            # Speed comparison
            fig, ax = plt.subplots(figsize=(14, 5))

            ax.plot(
                first_progress,
                telemetry["Speed"],
                label=driver_code,
                linewidth=1.8,
                color="#38bdf8"
            )

            ax.plot(
                second_progress,
                second_telemetry["Speed"],
                label=comparison_driver,
                linewidth=1.8,
                color="#f59e0b"
            )

            ax.set_title("Driver Speed Comparison")
            ax.set_xlabel("Lap Progress (%)")
            ax.set_ylabel("Speed (km/h)")
            ax.legend()
            ax.grid(alpha=0.25)

            st.pyplot(fig)
            plt.close(fig)
            # =========================================================
            # SPEED DIFFERENCE ANALYSIS
            # =========================================================

            st.subheader("Speed Difference Analysis")

            # Align both drivers by lap progress
           # Prepare first driver's data
            comparison_data = pd.DataFrame({
                "Lap_Progress": np.asarray(first_progress, dtype=float),
                "Driver_1_Speed": telemetry["Speed"].to_numpy(dtype=float)
            })

            # Prepare second driver's data
            second_data = pd.DataFrame({
                "Lap_Progress": np.asarray(second_progress, dtype=float),
                "Driver_2_Speed": second_telemetry["Speed"].to_numpy(dtype=float)
            })

            # Remove invalid readings
            second_data = second_data.replace(
                [np.inf, -np.inf], np.nan
            ).dropna()

            # Sort and combine duplicate progress values
            second_data = (
                second_data.groupby("Lap_Progress", as_index=False)
                ["Driver_2_Speed"].mean()
                .sort_values("Lap_Progress")
            )

            # Interpolate second driver's speed at first driver's progress points
            comparison_data["Driver_2_Speed"] = np.interp(
                comparison_data["Lap_Progress"],
                second_data["Lap_Progress"],
                second_data["Driver_2_Speed"]
            )

            # Calculate speed difference
            comparison_data["Speed_Difference"] = (
                comparison_data["Driver_1_Speed"]
                - comparison_data["Driver_2_Speed"]
            )

            fig, ax = plt.subplots(figsize=(14, 5))

            ax.plot(
                comparison_data["Lap_Progress"],
                comparison_data["Speed_Difference"],
                color="#38bdf8",
                linewidth=1.6
            )

            ax.axhline(0, color="white", linewidth=1, alpha=0.5)

            ax.fill_between(
                comparison_data["Lap_Progress"],
                comparison_data["Speed_Difference"],
                0,
                where=comparison_data["Speed_Difference"] >= 0,
                color="#22c55e",
                alpha=0.25
            )

            ax.fill_between(
                comparison_data["Lap_Progress"],
                comparison_data["Speed_Difference"],
                0,
                where=comparison_data["Speed_Difference"] < 0,
                color="#ef4444",
                alpha=0.25
            )

            ax.set_title(
                f"Speed Difference: {driver_code} vs {comparison_driver}"
            )
            ax.set_xlabel("Lap Progress (%)")
            ax.set_ylabel("Speed Difference (km/h)")
            ax.grid(alpha=0.25)

            st.pyplot(fig)
            plt.close(fig)
            # =========================================================
            # DRIVER ADVANTAGE SUMMARY
            # =========================================================

            st.subheader("Driver Advantage Summary")

            average_difference = comparison_data[
                "Speed_Difference"
            ].mean()

            max_advantage = comparison_data[
                "Speed_Difference"
            ].max()

            max_deficit = comparison_data[
                "Speed_Difference"
            ].min()

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Average Speed Difference",
                f"{average_difference:+.2f} km/h",
                help="Positive means the selected driver has higher average speed."
            )

            col2.metric(
                f"Maximum Advantage ({driver_code})",
                f"{max_advantage:+.2f} km/h"
            )

            col3.metric(
                f"Maximum Advantage ({comparison_driver})",
                f"{abs(max_deficit):.2f} km/h"
            )

            

                        
                        


            # Compare performance metrics
            st.subheader("Performance Metrics")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**{driver_code}**")
                st.metric(
                    "Top Speed",
                    f"{telemetry['Speed'].max():.1f} km/h"
                )
                st.metric(
                    "Average Speed",
                    f"{telemetry['Speed'].mean():.1f} km/h"
                )

            with col2:
                st.markdown(f"**{comparison_driver}**")
                st.metric(
                    "Top Speed",
                    f"{second_telemetry['Speed'].max():.1f} km/h"
                )
                st.metric(
                    "Average Speed",
                    f"{second_telemetry['Speed'].mean():.1f} km/h"
                )

        else:
            st.warning("No telemetry available for this driver.")

    except Exception as error:
        st.error(f"Driver comparison failed: {error}")

else:
    st.info("No second driver is available for comparison.")


# =========================================================
# DRIVER INPUT ANALYSIS
# =========================================================

st.subheader("Driver Input Analysis")

fig, ax = plt.subplots(figsize=(13, 4))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

ax.plot(
    telemetry["Distance"],
    telemetry["Throttle"],
    color=BLUE,
    linewidth=1.5,
    label="Throttle (%)"
)

brake_signal = telemetry["Brake"].astype(bool).astype(int) * 100

ax.step(
    telemetry["Distance"],
    brake_signal,
    where="post",
    color=RED,
    linewidth=1.4,
    label="Brake (ON/OFF)"
)

ax.set_xlabel("Distance (metres)", color="white")
ax.set_ylabel("Input (%)", color="white")
ax.set_title("Throttle and Brake Inputs", color="white")
ax.set_ylim(-5, 105)
ax.set_yticks([0, 25, 50, 75, 100])
ax.tick_params(colors="white")
ax.grid(alpha=0.2)
ax.legend(facecolor="#17191e", labelcolor="white")

for spine in ax.spines.values():
    spine.set_color("#444b56")

fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)


# =========================================================
# GEAR AND RPM ANALYSIS
# =========================================================

st.subheader("Gear & RPM Analysis")

fig, ax1 = plt.subplots(figsize=(13, 4))
fig.patch.set_facecolor(BG)
ax1.set_facecolor(BG)

ax1.plot(
    telemetry["Distance"],
    telemetry["RPM"],
    color=BLUE,
    linewidth=1.4,
    label="RPM"
)

ax1.set_xlabel("Distance (metres)", color="white")
ax1.set_ylabel("RPM", color=BLUE)
ax1.tick_params(axis="x", colors="white")
ax1.tick_params(axis="y", colors=BLUE)

ax2 = ax1.twinx()
ax2.step(
    telemetry["Distance"],
    telemetry["nGear"],
    where="post",
    color=RED,
    linewidth=1.4,
    label="Gear"
)

ax2.set_ylabel("Gear", color=RED)
ax2.set_yticks(range(1, 9))
ax2.tick_params(axis="y", colors=RED)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(
    lines1 + lines2,
    labels1 + labels2,
    facecolor="#17191e",
    labelcolor="white"
)

ax1.set_title("Engine RPM and Gear Selection", color="white")
ax1.grid(alpha=0.2)

for axis in [ax1, ax2]:
    for spine in axis.spines.values():
        spine.set_color("#444b56")

fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)

gear_changes = (
    telemetry["nGear"].diff().ne(0)
    & telemetry["nGear"].shift().notna()
)

st.metric("Gear Changes", int(gear_changes.sum()))


# =========================================================
# BRAKING PERFORMANCE ANALYSIS
# =========================================================

st.subheader("Braking Performance Analysis")

brake_data = telemetry.copy()
brake_data["Brake"] = brake_data["Brake"].astype(bool)

brake_data["Brake_Event"] = (
    brake_data["Brake"] != brake_data["Brake"].shift()
).cumsum()

braking = brake_data[brake_data["Brake"]]

braking_summary = braking.groupby("Brake_Event").agg(
    Start_Distance=("Distance", "first"),
    End_Distance=("Distance", "last"),
    Start_Speed=("Speed", "first"),
    End_Speed=("Speed", "last"),
    Start_Time=("SessionTime", "first"),
    End_Time=("SessionTime", "last"),
    Readings=("Speed", "count")
)

if not braking_summary.empty:
    braking_summary["Braking_Distance"] = (
        braking_summary["End_Distance"]
        - braking_summary["Start_Distance"]
    )

    braking_summary["Speed_Reduction"] = (
        braking_summary["Start_Speed"]
        - braking_summary["End_Speed"]
    )

    braking_summary["Duration"] = (
        braking_summary["End_Time"] - braking_summary["Start_Time"]
    ).dt.total_seconds()

    braking_summary["Avg_Deceleration"] = (
        (
            braking_summary["End_Speed"]
            - braking_summary["Start_Speed"]
        ) / 3.6
    ) / braking_summary["Duration"].where(
        braking_summary["Duration"] > 0
    )

    braking_summary["Avg_Deceleration"] = (
        braking_summary["Avg_Deceleration"].abs()
    )

    display_data = braking_summary[
        [
            "Start_Speed",
            "End_Speed",
            "Braking_Distance",
            "Speed_Reduction",
            "Duration",
            "Avg_Deceleration",
            "Readings"
        ]
    ].round(2)

    st.dataframe(
        display_data,
        use_container_width=True
    )

    st.metric(
        "Detected Braking Events",
        len(braking_summary)
    )

    st.caption(
        "Braking distance and deceleration are calculated between "
        "the first and last sampled brake-ON readings in each event."
    )

    st.subheader("Braking Event Comparison")

    event_labels = [
        f"Event {i + 1}"
        for i in range(len(braking_summary))
    ]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor(BG)

    for ax in axes:
        ax.set_facecolor(BG)
        ax.tick_params(colors="white")
        ax.grid(axis="x", alpha=0.2)

        for spine in ax.spines.values():
            spine.set_color("#444b56")

    axes[0].barh(
        event_labels,
        braking_summary["Speed_Reduction"],
        color=BLUE
    )
    axes[0].set_title("Speed Reduction", color="white")
    axes[0].set_xlabel("Speed lost (km/h)", color="white")
    axes[0].invert_yaxis()

    axes[1].barh(
        event_labels,
        braking_summary["Braking_Distance"],
        color=RED
    )
    axes[1].set_title("Braking Distance", color="white")
    axes[1].set_xlabel("Distance (metres)", color="white")
    axes[1].invert_yaxis()

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

else:
    st.info("No brake-ON events were found in this telemetry.")


# =========================================================
# CORNER / SECTION INSPECTOR
# =========================================================

st.subheader("Corner Performance Analyzer")

min_distance = float(telemetry["Distance"].min())
max_distance = float(telemetry["Distance"].max())

default_end = min(min_distance + 300, max_distance)

selected_range = st.slider(
    "Select circuit section (metres)",
    min_value=min_distance,
    max_value=max_distance,
    value=(min_distance, default_end),
    step=10.0
)

corner_data = telemetry[
    telemetry["Distance"].between(*selected_range)
].copy()

if not corner_data.empty:
    apex_index = corner_data["Speed"].idxmin()
    apex = corner_data.loc[apex_index]

    cols = st.columns(4)
    cols[0].metric(
        "Minimum Speed",
        f"{corner_data['Speed'].min():.1f} km/h"
    )
    cols[1].metric(
        "Maximum Speed",
        f"{corner_data['Speed'].max():.1f} km/h"
    )
    cols[2].metric(
        "Average Throttle",
        f"{corner_data['Throttle'].mean():.1f}%"
    )
    cols[3].metric(
        "Brake ON Readings",
        int(corner_data["Brake"].astype(bool).sum())
    )

    st.write(
        f"**Minimum-speed point:** {apex['Distance']:.1f} metres"
    )

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.plot(
        corner_data["Distance"],
        corner_data["Speed"],
        color=BLUE,
        linewidth=2,
        label="Speed"
    )
    ax.scatter(
        apex["Distance"],
        apex["Speed"],
        color=RED,
        s=90,
        zorder=5,
        label="Minimum-speed point"
    )

    ax.set_xlabel("Distance (metres)", color="white")
    ax.set_ylabel("Speed (km/h)", color="white")
    ax.set_title("Selected Section - Speed Profile", color="white")
    ax.tick_params(colors="white")
    ax.grid(alpha=0.2)
    ax.legend(facecolor="#17191e", labelcolor="white")

    for spine in ax.spines.values():
        spine.set_color("#444b56")

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
else:
    st.warning("No telemetry readings in this selected section.")


# =========================================================
# SECTION A VS SECTION B
# =========================================================

st.divider()
st.subheader("Circuit Section Comparison")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### Section A")
    range_a = st.slider(
        "Select Section A",
        min_value=min_distance,
        max_value=max_distance,
        value=(
            min_distance,
            min(min_distance + 300, max_distance)
        ),
        step=10.0,
        key="section_a"
    )

with col_b:
    st.markdown("### Section B")
    start_b = min(min_distance + 800, max_distance)
    end_b = min(start_b + 300, max_distance)

    if end_b <= start_b:
        start_b = min_distance
        end_b = max_distance

    range_b = st.slider(
        "Select Section B",
        min_value=min_distance,
        max_value=max_distance,
        value=(start_b, end_b),
        step=10.0,
        key="section_b"
    )

section_a = telemetry[
    telemetry["Distance"].between(*range_a)
]
section_b = telemetry[
    telemetry["Distance"].between(*range_b)
]

if not section_a.empty and not section_b.empty:
    comparison = pd.DataFrame({
        "Metric": [
            "Minimum Speed (km/h)",
            "Maximum Speed (km/h)",
            "Average Speed (km/h)",
            "Average Throttle (%)",
            "Brake ON Readings"
        ],
        "Section A": [
            section_a["Speed"].min(),
            section_a["Speed"].max(),
            section_a["Speed"].mean(),
            section_a["Throttle"].mean(),
            section_a["Brake"].astype(bool).sum()
        ],
        "Section B": [
            section_b["Speed"].min(),
            section_b["Speed"].max(),
            section_b["Speed"].mean(),
            section_b["Throttle"].mean(),
            section_b["Brake"].astype(bool).sum()
        ]
    })

    st.dataframe(
        comparison.round(2),
        use_container_width=True,
        hide_index=True
    )

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.plot(
        section_a["Distance"] - range_a[0],
        section_a["Speed"],
        color=BLUE,
        label="Section A"
    )
    ax.plot(
        section_b["Distance"] - range_b[0],
        section_b["Speed"],
        color=RED,
        label="Section B"
    )

    ax.set_xlabel("Distance from section start (metres)", color="white")
    ax.set_ylabel("Speed (km/h)", color="white")
    ax.set_title("Speed Profile Comparison", color="white")
    ax.tick_params(colors="white")
    ax.grid(alpha=0.2)
    ax.legend(facecolor="#17191e", labelcolor="white")

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
else:
    st.warning("One or both selected sections have no readings.")


# =========================================================
# TRACK MAP
# =========================================================
track_data = telemetry[
    ["X", "Y", "Speed", "Brake"]
].copy()

track_data = track_data.dropna(
    subset=["X", "Y"]
)
if not track_data.empty:

    fig, ax = plt.subplots(figsize=(10, 7))

    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    # Racing line
    ax.plot(
        track_data["X"],
        track_data["Y"],
        color="#38bdf8",
        linewidth=2.2,
        alpha=0.9,
        label="Racing line"
    )

    # Start point
    ax.scatter(
        track_data["X"].iloc[0],
        track_data["Y"].iloc[0],
        color="white",
        s=70,
        label="Start",
        zorder=5
    )

    # Braking locations
    braking_points = track_data[
        track_data["Brake"] == True
    ]

    ax.scatter(
        braking_points["X"],
        braking_points["Y"],
        color="#e10600",
        s=12,
        label="Braking zones",
        zorder=4
    )

    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")

    ax.legend(
        facecolor="#141821",
        edgecolor="#343a46",
        labelcolor="white",
        loc="upper right"
    )

    st.pyplot(fig)
    plt.close(fig)

else:
    st.warning("Track data is not available.")

# =========================================================
# DOWNLOAD REPORTS
# =========================================================

st.divider()
st.subheader("Export Telemetry Reports")

download_cols = st.columns(2)

telemetry_csv = telemetry.to_csv(index=False).encode("utf-8")

download_cols[0].download_button(
    label="Download Full Telemetry CSV",
    data=telemetry_csv,
    file_name=(
        f"{year}_{event_name.replace(' ', '_')}_"
        f"{session_name.replace(' ', '_')}_{driver_code}_telemetry.csv"
    ),
    mime="text/csv"
)

if not braking_summary.empty:
    braking_csv = (
        braking_summary.reset_index().to_csv(index=False).encode("utf-8")
    )

    download_cols[1].download_button(
        label="Download Braking Analysis CSV",
        data=braking_csv,
        file_name=(
            f"{year}_{event_name.replace(' ', '_')}_"
            f"{driver_code}_braking_analysis.csv"
        ),
        mime="text/csv"
    )
else:
    download_cols[1].info("No braking report is available.")
