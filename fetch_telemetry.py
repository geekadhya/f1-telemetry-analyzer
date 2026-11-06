import tif1
def get_lap_summary(telemetry):

    summary = {
        "total_readings": len(telemetry),
        "minimum_speed": round(telemetry["Speed"].min(), 2),
        "maximum_speed": round(telemetry["Speed"].max(), 2),
        "average_speed": round(telemetry["Speed"].mean(), 2),
        "minimum_rpm": round(telemetry["RPM"].min(), 2),
        "maximum_rpm": round(telemetry["RPM"].max(), 2),
        "average_throttle": round(telemetry["Throttle"].mean(), 2),
        "brake_readings": int(telemetry["Brake"].sum())
    }

    return summary
def get_braking_summary(telemetry):

    data = telemetry.copy()

    # Identify changes in brake state
    data["Brake_Event"] = (
        data["Brake"] != data["Brake"].shift()
    ).cumsum()

    # Keep only brake-ON readings
    braking = data[data["Brake"] == True]

    # Group readings into braking events
    summary = braking.groupby("Brake_Event").agg(
        Start_Distance=("Distance", "first"),
        End_Distance=("Distance", "last"),
        Start_Speed=("Speed", "first"),
        End_Speed=("Speed", "last"),
        Start_Time=("SessionTime", "first"),
        End_Time=("SessionTime", "last"),
        Readings=("Speed", "count")
    )

    # Calculate braking metrics
    summary["Braking_Distance"] = (
        summary["End_Distance"] - summary["Start_Distance"]
    )

    summary["Speed_Reduction"] = (
        summary["Start_Speed"] - summary["End_Speed"]
    )

    summary["Duration"] = (
        summary["End_Time"] - summary["Start_Time"]
    ).dt.total_seconds()

    # Convert km/h to m/s before calculating deceleration
    summary["Deceleration"] = (
        (summary["End_Speed"] - summary["Start_Speed"]) / 3.6
    ) / summary["Duration"].where(summary["Duration"] > 0)

    summary["Deceleration_Magnitude"] = (
        summary["Deceleration"].abs()
    )

    return summary

# Select the Bahrain qualifying session
session = tif1.get_session(
    2024,
    "Bahrain Grand Prix",
    "Qualifying"
)

# Select Max Verstappen
driver = session.get_driver("VER")

# Retrieve his fastest lap telemetry
telemetry = driver.get_fastest_lap_tel()

# Display the first five readings
print(telemetry.head())

# Display available telemetry columns
print("\nAvailable columns:")
print(telemetry.columns.tolist())
print("\nTelemetry summary:")
print(telemetry[["Speed", "Throttle", "Brake", "RPM"]].describe())
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))

plt.plot(telemetry["Distance"], telemetry["Speed"])

plt.title("Max Verstappen - Bahrain 2024 Qualifying")
plt.xlabel("Distance (metres)")
plt.ylabel("Speed (km/h)")

plt.grid(True)
plt.show()
slowest_point = telemetry["Speed"].idxmin()

print("\nSlowest point:")
print(telemetry.loc[slowest_point, ["Distance", "Speed", "Throttle", "Brake"]])
print("\nTelemetry around the slowest point:")

print(
    telemetry.loc[75:87, ["Distance", "Speed", "Throttle", "Brake"]]
)
corner_data = telemetry.loc[75:87]

plt.figure(figsize=(12, 5))

plt.plot(
    corner_data["Distance"],
    corner_data["Throttle"],
    label="Throttle"
)

plt.xlabel("Distance (metres)")
plt.ylabel("Throttle (%)")
plt.title("Throttle Input Around the Slowest Point")
plt.legend()
plt.grid(True)

plt.show()
plt.figure(figsize=(12, 5))

plt.plot(
    corner_data["Distance"],
    corner_data["Brake"],
    label="Brake",
    drawstyle="steps-post"
)

plt.title("Brake Input Around the Slowest Point")
plt.xlabel("Distance (metres)")
plt.ylabel("Brake (0 = Off, 1 = On)")

plt.yticks([0, 1], ["Off", "On"])
plt.grid(True)
plt.legend()

plt.show()
print("\nSpeed, Gear and RPM around the slowest point:")

print(
    corner_data[
        ["Distance", "Speed", "nGear", "RPM"]
    ].to_string(index=False)
)
plt.figure(figsize=(12, 5))

plt.plot(
    corner_data["Distance"],
    corner_data["RPM"],
    label="Engine RPM"
)

plt.title("Engine RPM Around the Slowest Point")
plt.xlabel("Distance (metres)")
plt.ylabel("RPM")

plt.grid(True)
plt.legend()

plt.show()
fig, axes = plt.subplots(4, 1, figsize=(12, 12), sharex=True)

# Speed
axes[0].plot(corner_data["Distance"], corner_data["Speed"])
axes[0].set_ylabel("Speed (km/h)")
axes[0].set_title("Corner Telemetry Analysis")

# Throttle
axes[1].plot(corner_data["Distance"], corner_data["Throttle"])
axes[1].set_ylabel("Throttle (%)")

# Brake
axes[2].step(
    corner_data["Distance"],
    corner_data["Brake"].astype(int),
    where="post"
)
axes[2].set_ylabel("Brake")
axes[2].set_yticks([0, 1], ["Off", "On"])

# RPM
axes[3].plot(corner_data["Distance"], corner_data["RPM"])
axes[3].set_ylabel("RPM")
axes[3].set_xlabel("Distance (metres)")

for ax in axes:
    ax.grid(True)

plt.tight_layout()
plt.show()
print("\n===== CORNER PERFORMANCE SUMMARY =====")

print("Minimum Speed:", round(corner_data["Speed"].min(), 2), "km/h")
print("Maximum Speed:", round(corner_data["Speed"].max(), 2), "km/h")

print("Minimum RPM:", round(corner_data["RPM"].min(), 2))
print("Maximum RPM:", round(corner_data["RPM"].max(), 2))

print("Average Throttle:", round(corner_data["Throttle"].mean(), 2), "%")

print("Brake ON readings:", corner_data["Brake"].sum())
print("\n===== FULL LAP PERFORMANCE SUMMARY =====")

print("Total telemetry readings:", len(telemetry))

print("Minimum Speed:", round(telemetry["Speed"].min(), 2), "km/h")
print("Maximum Speed:", round(telemetry["Speed"].max(), 2), "km/h")
print("Average Speed:", round(telemetry["Speed"].mean(), 2), "km/h")

print("Minimum RPM:", round(telemetry["RPM"].min(), 2))
print("Maximum RPM:", round(telemetry["RPM"].max(), 2))

print("Average Throttle:", round(telemetry["Throttle"].mean(), 2), "%")

print("Brake ON readings:", telemetry["Brake"].sum())
fastest_point = telemetry["Speed"].idxmax()
slowest_point = telemetry["Speed"].idxmin()

print("\n===== SPEED ANALYSIS =====")

print("\nFastest point:")
print(
    telemetry.loc[
        fastest_point,
        ["Distance", "Speed", "nGear", "RPM"]
    ]
)

print("\nSlowest point:")
print(
    telemetry.loc[
        slowest_point,
        ["Distance", "Speed", "nGear", "RPM"]
    ]
)
braking_data = telemetry[telemetry["Brake"] == True]

print("\n===== BRAKING ANALYSIS =====")

print("Total braking readings:", len(braking_data))

print("\nFirst 10 braking readings:")

print(
    braking_data[
        ["Distance", "Speed", "Throttle", "Brake", "nGear"]
    ].head(10).to_string(index=False)
)
braking_data = telemetry[telemetry["Brake"] == True].copy()

braking_data["Distance_Gap"] = braking_data["Distance"].diff()

print("\n===== BRAKING DISTANCE GAPS =====")

print(
    braking_data[
        ["Distance", "Speed", "Distance_Gap"]
    ].head(15).to_string(index=False)
)
# Detect continuous braking events
telemetry["Brake_Change"] = (
    telemetry["Brake"] != telemetry["Brake"].shift()
)

telemetry["Brake_Event"] = telemetry["Brake_Change"].cumsum()

# Keep only rows where braking is active
braking_events = telemetry[telemetry["Brake"] == True]

print("\n===== BRAKING EVENTS =====")

event_summary = braking_events.groupby("Brake_Event").agg(
    Start_Distance=("Distance", "first"),
    End_Distance=("Distance", "last"),
    Start_Speed=("Speed", "first"),
    End_Speed=("Speed", "last"),
    Readings=("Speed", "count")
)

print(event_summary.to_string())
event_summary["Braking_Distance"] = (
    event_summary["End_Distance"] -
    event_summary["Start_Distance"]
)

print("\n===== BRAKING DISTANCE ANALYSIS =====")

print(
    event_summary[
        ["Start_Speed", "End_Speed", "Braking_Distance", "Readings"]
    ].round(2).to_string()
)
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 5))

plt.bar(
    event_summary.index,
    event_summary["Braking_Distance"]
)

plt.title("Braking Distance Comparison")
plt.xlabel("Braking Event")
plt.ylabel("Braking Distance (metres)")

plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
event_times = braking_events.groupby("Brake_Event").agg(
    Start_Time=("SessionTime", "first"),
    End_Time=("SessionTime", "last")
)

event_summary = event_summary.join(event_times)

event_summary["Duration"] = (
    event_summary["End_Time"] - event_summary["Start_Time"]
).dt.total_seconds()

print("\n===== BRAKING EVENT DURATIONS =====")

print(
    event_summary[
        ["Start_Time", "End_Time", "Duration"]
    ].to_string()
)
# Convert speeds from km/h to m/s
event_summary["Start_Speed_ms"] = (
    event_summary["Start_Speed"] / 3.6
)

event_summary["End_Speed_ms"] = (
    event_summary["End_Speed"] / 3.6
)

# Calculate average deceleration
event_summary["Deceleration"] = (
    (event_summary["End_Speed_ms"] -
     event_summary["Start_Speed_ms"])
    / event_summary["Duration"]
)

print("\n===== AVERAGE DECELERATION ANALYSIS =====")

print(
    event_summary[
        ["Start_Speed", "End_Speed", "Duration", "Deceleration"]
    ].round(2).to_string()
)
plt.figure(figsize=(10, 5))

plt.bar(
    event_summary.index,
    event_summary["Deceleration"].abs()
)

plt.title("Average Braking Deceleration")
plt.xlabel("Braking Event")
plt.ylabel("Deceleration (m/s²)")

plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.show()
# Inspect Event 3 and the readings immediately before and after it
event_3_data = telemetry[
    telemetry["Brake_Event"].between(5, 7)
]

print("\n===== EVENT 3 INVESTIGATION =====")

print(
    event_3_data[
        ["Distance", "Speed", "Brake", "Throttle",
         "nGear", "RPM", "SessionTime"]
    ].to_string(index=True)
)
# Calculate time difference between consecutive readings
telemetry["Time_Diff"] = (
    telemetry["SessionTime"].diff().dt.total_seconds()
)

# Calculate speed difference in m/s
telemetry["Speed_Diff"] = (
    telemetry["Speed"].diff() / 3.6
)

# Calculate instantaneous acceleration
telemetry["Instant_Acceleration"] = (
    telemetry["Speed_Diff"] / telemetry["Time_Diff"]
)

# Inspect Event 3 and its surrounding readings
print("\n===== INSTANTANEOUS ACCELERATION: EVENT 3 =====")

print(
    telemetry.loc[228:233, [
        "Distance",
        "Speed",
        "Brake",
        "Time_Diff",
        "Instant_Acceleration"
    ]].round(2).to_string()
)
print("\n===== ACCELERATION CHANNEL =====")

print(
    telemetry.loc[228:233, [
        "Distance",
        "Speed",
        "Brake",
        "AccelerationX",
        "AccelerationY",
        "AccelerationZ"
    ]].round(3).to_string()
)
print("\n===== ACCELERATION COMPARISON =====")

print(
    telemetry.loc[228:233, [
        "Distance",
        "Speed",
        "Brake",
        "Instant_Acceleration",
        "AccelerationX"
    ]].round(3).to_string(index=False)
)
# Plot acceleration channels around Event 3

fig, ax = plt.subplots(figsize=(12, 5))

ax.plot(event_3_data["Distance"], event_3_data["AccelerationX"],
        label="Acceleration X")

ax.plot(event_3_data["Distance"], event_3_data["AccelerationY"],
        label="Acceleration Y")

ax.plot(event_3_data["Distance"], event_3_data["AccelerationZ"],
        label="Acceleration Z")

ax.set_title("Acceleration Channels – Event 3")
ax.set_xlabel("Distance (metres)")
ax.set_ylabel("Acceleration (source units)")
ax.legend()
ax.grid(True)

plt.tight_layout()
plt.show()
print("\n===== ACCELERATION CORRELATION =====")

print(
    telemetry[
        ["Instant_Acceleration",
         "AccelerationX",
         "AccelerationY",
         "AccelerationZ"]
    ].corr().round(3)
)
# ===== TRACK MAP WITH BRAKING POINTS =====

track_data = telemetry[["X", "Y", "Speed"]].dropna()

braking_data = telemetry[
    (telemetry["Brake"] == True)
].dropna(subset=["X", "Y"])

plt.figure(figsize=(12, 9))

# Track coloured by speed
scatter = plt.scatter(
    track_data["X"],
    track_data["Y"],
    c=track_data["Speed"],
    cmap="turbo",
    s=12
)

# Circuit path
plt.plot(
    track_data["X"],
    track_data["Y"],
    linewidth=0.7,
    alpha=0.3
)

# Braking points
plt.scatter(
    braking_data["X"],
    braking_data["Y"],
    color="black",
    marker="x",
    s=35,
    label="Brake Applied"
)

plt.colorbar(scatter, label="Speed (km/h)")

plt.title("Bahrain GP 2024 – Track Map & Braking Zones")
plt.xlabel("X Position (source units)")
plt.ylabel("Y Position (source units)")

plt.axis("equal")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
# ===== BRAKING EVENT LOCATIONS =====

braking_event_points = (
    braking_events.groupby("Brake_Event")
    .agg(
        Start_X=("X", "first"),
        Start_Y=("Y", "first"),
        End_X=("X", "last"),
        End_Y=("Y", "last"),
        Start_Speed=("Speed", "first"),
        End_Speed=("Speed", "last")
    )
)

print("\n===== BRAKING ZONE LOCATIONS =====")

print(braking_event_points.round(2).to_string())
plt.figure(figsize=(12, 9))

# Track
plt.plot(
    telemetry["X"],
    telemetry["Y"],
    color="grey",
    linewidth=1,
    label="Circuit Path"
)

# Braking starts
plt.scatter(
    braking_event_points["Start_X"],
    braking_event_points["Start_Y"],
    color="red",
    marker="o",
    s=65,
    label="Braking Start"
)

# Braking ends
plt.scatter(
    braking_event_points["End_X"],
    braking_event_points["End_Y"],
    color="blue",
    marker="s",
    s=65,
    label="Braking End"
)

plt.title("Bahrain GP – Braking Zone Locations")
plt.xlabel("X Position")
plt.ylabel("Y Position")

plt.axis("equal")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
# ===== BRAKING PERFORMANCE COMPARISON =====

event_summary["Speed_Reduction"] = (
    event_summary["Start_Speed"] -
    event_summary["End_Speed"]
)

event_summary["Deceleration_Magnitude"] = (
    event_summary["Deceleration"].abs()
)

columns = [
    "Start_Speed",
    "End_Speed",
    "Speed_Reduction",
    "Braking_Distance",
    "Duration",
    "Deceleration_Magnitude"
]

print("\n===== BRAKING PERFORMANCE COMPARISON =====")

print(
    event_summary[columns]
    .round(2)
    .to_string()
)
plt.figure(figsize=(11, 5))

plt.bar(
    event_summary.index.astype(str),
    event_summary["Deceleration_Magnitude"]
)

plt.title("Average Deceleration by Braking Event")
plt.xlabel("Braking Event")
plt.ylabel("Average Deceleration Magnitude (m/s²)")
plt.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.show()
# ===== AUTOMATED BRAKING INSIGHTS =====

highest_deceleration = event_summary[
    "Deceleration_Magnitude"
].idxmax()

longest_braking = event_summary[
    "Braking_Distance"
].idxmax()

largest_speed_drop = event_summary[
    "Speed_Reduction"
].idxmax()

shortest_duration = event_summary[
    "Duration"
].idxmin()

print("\n===== AUTOMATED RACE INSIGHTS =====")

print(
    f"Highest average deceleration: Event {highest_deceleration}"
)

print(
    f"Longest braking distance: Event {longest_braking}"
)

print(
    f"Largest speed reduction: Event {largest_speed_drop}"
)

print(
    f"Shortest braking duration: Event {shortest_duration}"
)
lap_summary = get_lap_summary(telemetry)

print("\n===== LAP PERFORMANCE SUMMARY =====")

for metric, value in lap_summary.items():
    print(f"{metric}: {value}")
    braking_summary = get_braking_summary(telemetry)

print("\n===== BRAKING PERFORMANCE SUMMARY =====")

print(
    braking_summary.round(2).to_string()
)