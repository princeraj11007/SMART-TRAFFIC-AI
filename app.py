import streamlit as st
import matplotlib.pyplot as plt
import time
import random
from sklearn.linear_model import LinearRegression

# ===== PAGE CONFIG =====
st.set_page_config(page_title="SmartFlow AI Traffic", layout="wide")

# ===== SESSION STATE =====
if "running" not in st.session_state:
    st.session_state.running = False

if "lanes" not in st.session_state:
    st.session_state.lanes = [20, 20, 20, 20]

if "locked_lanes" not in st.session_state:
    st.session_state.locked_lanes = None

if "traffic_plan" not in st.session_state:
    st.session_state.traffic_plan = [0,1,2,3]

if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False

if "start_time" not in st.session_state:
    st.session_state.start_time = 0

# NEW: traffic history
if "history" not in st.session_state:
    st.session_state.history = []

# ===== SIDEBAR =====
st.sidebar.header("🚥 Controls")

names = ["North", "South", "East", "West"]

lanes_input = [st.sidebar.slider(x, 0, 100, st.session_state.lanes[i]) for i, x in enumerate(names)]

emergency = st.sidebar.radio("🚑 Emergency Lane", ["None"] + names)

# NEW: traffic intensity (simulating API)
traffic_factor = st.sidebar.slider("🌍 Traffic Intensity (API Sim)", 0.5, 2.0, 1.0)

if st.sidebar.button("▶ Start Simulation"):
    st.session_state.running = True
    st.session_state.locked_lanes = lanes_input.copy()
    st.session_state.start_time = time.time()
    st.session_state.plan_generated = False
    st.session_state.history = []

if st.sidebar.button("⏹ Stop Simulation"):
    st.session_state.running = False
    st.session_state.locked_lanes = None
    st.session_state.plan_generated = False

if st.sidebar.button("📸 AI Camera Detect"):
    st.session_state.lanes = [random.randint(20, 100) for _ in range(4)]
    st.sidebar.success("Vehicles detected!")

# ===== DATA LOCK =====
if st.session_state.running and st.session_state.locked_lanes:
    lanes = st.session_state.locked_lanes
else:
    lanes = lanes_input

# APPLY TRAFFIC FACTOR (API SIMULATION)
lanes = [int(x * traffic_factor) for x in lanes]

st.session_state.lanes = lanes

# ===== ML MODEL =====
if "model" not in st.session_state:
    X, y = [], []
    for _ in range(300):
        l = [random.randint(0, 100) for _ in range(4)]
        total = sum(l)+1
        X.append(l)
        y.append([(i/total)*120 for i in l])

    st.session_state.model = LinearRegression().fit(X, y)

model = st.session_state.model
green_times = model.predict([lanes])[0]
green_times = [max(10, min(120, t)) for t in green_times]

# Emergency Override
if emergency != "None":
    idx = names.index(emergency)
    green_times = [0]*4
    green_times[idx] = 120

# ===== PLAN GENERATION =====
if st.session_state.running and not st.session_state.plan_generated:
    plan = sorted(range(4), key=lambda i: lanes[i], reverse=True)
    st.session_state.traffic_plan = plan
    st.session_state.plan_generated = True

plan = st.session_state.traffic_plan

# ===== SIGNAL LOGIC =====
cycle_times = green_times
yellow_time = 3

elapsed = time.time() - st.session_state.start_time

current_lights = ["🔴 RED"] * 4
remaining_time = 0
active_lane = None

if st.session_state.running:

    t = elapsed % (sum(cycle_times) + 4*yellow_time)

    for i in range(4):
        lane = plan[i]

        if t <= cycle_times[lane]:
            current_lights[lane] = "🟢 GREEN"
            active_lane = lane
            remaining_time = int(cycle_times[lane] - t)

            next_lane = plan[(i+1)%4]
            current_lights[next_lane] = "🟡 YELLOW"
            break

        t -= cycle_times[lane]

        if t <= yellow_time:
            current_lights[lane] = "🟡 YELLOW"
            active_lane = lane
            remaining_time = int(yellow_time - t)
            break

        t -= yellow_time

# ===== STORE HISTORY =====
if st.session_state.running:
    st.session_state.history.append(sum(lanes))

# ===== TITLE =====
st.title("🚦 SmartFlow AI Traffic System")

# ===== TABS =====
tab1, tab2 = st.tabs(["🚦 Dashboard", "📊 Analytics"])

# ===== DASHBOARD =====
with tab1:
    st.subheader("🚦 Live Traffic")
    cols = st.columns(4)

    for i in range(4):
        if current_lights[i] == "🟢 GREEN":
            color = "#00FF00"; dot="🟢"
        elif current_lights[i] == "🟡 YELLOW":
            color = "#FFFF00"; dot="🟡"
        else:
            color = "#FF0000"; dot="🔴"

        display_time = remaining_time if i == active_lane else round(green_times[i],1)

        cols[i].markdown(f"""
        <div style="padding:20px;border-radius:15px;background:#111;color:white;text-align:center;">
        <h3>{names[i]}</h3>
        <h2 style='color:{color}'>{dot} {current_lights[i]}</h2>
        <p>🚗 {lanes[i]} Vehicles</p>
        <h3>{display_time} sec</h3>
        </div>
        """, unsafe_allow_html=True)

# ===== ANALYTICS =====
with tab2:
    st.subheader("📊 Signal Chart")
    fig, ax = plt.subplots()
    ax.bar(names, green_times)
    st.pyplot(fig)

    st.subheader("📈 Traffic vs Time")
    fig2, ax2 = plt.subplots()
    ax2.plot(st.session_state.history)
    st.pyplot(fig2)

    if len(st.session_state.history) > 5:
        peak = max(st.session_state.history)
        st.warning(f"⚠ Peak Traffic Detected: {peak} vehicles")

# ===== PERFORMANCE =====
st.subheader("🚀 Smart Performance")

total = sum(green_times)
avg = total/4

c1,c2,c3 = st.columns(3)
c1.metric("🚀 Throughput", "100%")
c2.metric("⏳ Avg Wait", f"{round(avg,1)} sec")
c3.metric("🚗 Total Vehicles", sum(lanes))

# ===== 🌱 ENVIRONMENT IMPACT =====
st.subheader("🌱 Environmental Impact")

total_vehicles = sum(lanes)
avg_wait_time = sum(green_times) / 4
wait_minutes = avg_wait_time / 60

fuel_per_vehicle = 0.02
fuel_consumed = total_vehicles * wait_minutes * fuel_per_vehicle
fuel_saved = fuel_consumed * 0.3
co2_reduced = fuel_saved * 2.31
money_saved = fuel_saved * 100

e1, e2, e3, e4 = st.columns(4)
e1.metric("⛽ Fuel Saved (L)", round(fuel_saved, 2))
e2.metric("🌍 CO₂ Reduced (kg)", round(co2_reduced, 2))
e3.metric("💰 Money Saved (₹)", int(money_saved))
e4.metric("⏱️ Avg Wait Time (s)", int(avg_wait_time))

st.info("💡 AI reduces idle time → saves fuel & reduces pollution")

# ===== ALERT =====
if emergency != "None":
    st.error("🚑 EMERGENCY MODE ACTIVATED")

# ===== AUTO REFRESH =====
if st.session_state.running:
    time.sleep(1)
    st.rerun()
