import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="AyushBot Cloud — Central Analytics",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Outfit', sans-serif;
    background-color: #0A0E17;
    color: #E2E8F0;
}

.header-container {
    background: linear-gradient(135deg, rgba(31, 41, 55, 0.5) 0%, rgba(17, 24, 39, 0.8) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 25px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.header-title {
    background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
}

.header-subtitle {
    color: #94A3B8;
    font-size: 1.05rem;
    margin-top: 5px;
}

.glass-card {
    background: rgba(30, 41, 59, 0.35);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
}

.glass-card:hover {
    transform: translateY(-3px);
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 8px 30px 0 rgba(99, 102, 241, 0.15);
}

.metric-val {
    font-size: 1.8rem;
    font-weight: 700;
    margin: 5px 0;
    letter-spacing: -0.05em;
}
.val-cyan { color: #06B6D4; text-shadow: 0 0 10px rgba(6, 182, 212, 0.3); }
.val-indigo { color: #6366F1; text-shadow: 0 0 10px rgba(99, 102, 241, 0.3); }
.val-emerald { color: #10B981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.3); }
.val-rose { color: #F43F5E; text-shadow: 0 0 10px rgba(244, 63, 94, 0.3); }
.val-amber { color: #F59E0B; text-shadow: 0 0 10px rgba(245, 158, 11, 0.3); }

.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}
.badge-online { background-color: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-idle { background-color: rgba(245, 158, 11, 0.15); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-offline { background-color: rgba(244, 63, 94, 0.15); color: #F87171; border: 1px solid rgba(244, 63, 94, 0.3); }

.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
    background-color: rgba(30, 41, 59, 0.25);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px 8px 0px 0px;
    padding: 8px 24px;
    font-weight: 600;
    color: #94A3B8;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(99, 102, 241, 0.15) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: #A5B4FC !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIMULATED DATA
# ==========================================
np.random.seed(42)

GATEWAYS = {
    "PHC-01 (Dharwad, Karnataka)": {
        "lat": 15.4589, "lon": 75.0078,
        "status": "Online", "sync_time": "Synced 8 mins ago",
        "fw_ver": "v2.4.1", "batt": 91, "temp": 31.2,
        "region": "North Karnataka", "triage_rate": 92, "drift": 0.05
    },
    "PHC-02 (Haveri, Karnataka)": {
        "lat": 14.7955, "lon": 75.3988,
        "status": "Online", "sync_time": "Synced 35 mins ago",
        "fw_ver": "v2.4.1", "batt": 78, "temp": 33.7,
        "region": "North Karnataka", "triage_rate": 74, "drift": 0.08
    },
    "PHC-03 (Ranebennur, Karnataka)": {
        "lat": 14.6218, "lon": 75.6372,
        "status": "Idle", "sync_time": "Synced 3 hours ago",
        "fw_ver": "v2.4.1", "batt": 55, "temp": 35.1,
        "region": "North Karnataka", "triage_rate": 58, "drift": 0.13
    },
    "PHC-04 (Gadag, Karnataka)": {
        "lat": 15.4310, "lon": 75.6229,
        "status": "Idle", "sync_time": "Synced 6 hours ago",
        "fw_ver": "v2.4.0", "batt": 42, "temp": 36.8,
        "region": "North Karnataka", "triage_rate": 46, "drift": 0.17
    },
    "PHC-05 (Shiggaon, Karnataka)": {
        "lat": 14.9834, "lon": 75.2225,
        "status": "Offline", "sync_time": "Synced 5 days ago",
        "fw_ver": "v2.3.9", "batt": 8, "temp": 38.2,
        "region": "North Karnataka", "triage_rate": 38, "drift": 0.25
    }
}

PLOT_COLORS = ["#38BDF8", "#F59E0B", "#F43F5E", "#10B981", "#A78BFA"]

PLOT_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font_color="#E2E8F0",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
)


@st.cache_data
def generate_timeseries_data(days=30):
    date_list = [datetime.now() - timedelta(days=x) for x in range(days)]
    date_list.reverse()

    # Gradual linear battery decay profiles (start_level, daily_loss)
    battery_profiles = {
        "Dharwad":    (97, 0.15),   # Town grid — barely drains
        "Haveri":     (94, 0.35),   # Semi-urban, slow drain
        "Ranebennur": (90, 0.65),   # Rural, moderate drain
        "Gadag":      (85, 0.95),   # Semi-arid, noticeable drain
        "Shiggaon":   (78, 1.40),   # Remote solar only, steady decline
    }

    data = []
    for g_id, g_meta in GATEWAYS.items():
        base_triage = g_meta["triage_rate"]
        drift_rate = g_meta["drift"]
        village = next((k for k in battery_profiles if k in g_id), "Dharwad")
        batt_start, batt_loss = battery_profiles[village]

        for i, dt in enumerate(date_list):
            # Smooth battery: linear decay + tiny daily noise (±1%)
            batt_val = max(5, batt_start - (i * batt_loss) + np.random.uniform(-1.0, 1.0))

            # Triage count: small daily variation (±4 cases)
            triage_count = int(base_triage + np.random.randint(-4, 5))
            if "Shiggaon" in g_id and i % 7 == 0:
                triage_count = int(triage_count * 0.3)  # Soft dip, not zero

            # Model drift: gentle sine wave + tiny noise
            current_drift = drift_rate * (1 + 0.05 * np.sin(i / 4.0)) + np.random.uniform(0.0, 0.01)

            # Privacy epsilon: smooth cumulative
            eps = 0.15 * i + (triage_count * 0.005)

            data.append({
                "Date": dt, "Node": g_id,
                "TriageCount": triage_count,
                "BatteryCharge": round(batt_val, 1),
                "ModelDrift": round(current_drift, 4),
                "PrivacyEpsilon": round(eps, 2),
                "LatencyMs": int(120 + np.random.randint(-8, 9) + (g_meta["temp"] * 1.5))
            })
    return pd.DataFrame(data)


@st.cache_data
def generate_epidemiological_distribution():
    conditions = ["Fever / Dengue / Malaria", "Acute Diarrhea", "Respiratory (TB/COPD)",
                   "Skin / Fungal Infections", "Hypertension / Diabetes"]
    node_weights = {
        "Dharwad":    [0.18, 0.15, 0.30, 0.20, 0.17],
        "Haveri":     [0.25, 0.22, 0.25, 0.18, 0.10],
        "Ranebennur": [0.30, 0.28, 0.18, 0.15, 0.09],
        "Gadag":      [0.35, 0.20, 0.20, 0.18, 0.07],
        "Shiggaon":   [0.28, 0.35, 0.16, 0.14, 0.07],
    }
    rows = []
    for g_id in GATEWAYS:
        key = next((k for k in node_weights if k in g_id), None)
        weights = node_weights.get(key, [0.20] * 5)
        for cond, w in zip(conditions, weights):
            rows.append({"Node": g_id, "Condition": cond,
                          "Cases": int(w * 350 + np.random.randint(-20, 20))})
    return pd.DataFrame(rows)


@st.cache_data
def generate_risk_distribution():
    risks = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    node_weights = {
        "Dharwad":    [0.52, 0.28, 0.14, 0.06],
        "Haveri":     [0.45, 0.32, 0.16, 0.07],
        "Ranebennur": [0.38, 0.36, 0.18, 0.08],
        "Gadag":      [0.32, 0.38, 0.20, 0.10],
        "Shiggaon":   [0.25, 0.38, 0.24, 0.13],
    }
    rows = []
    for g_id in GATEWAYS:
        key = next((k for k in node_weights if k in g_id), None)
        weights = node_weights.get(key, [0.25, 0.35, 0.25, 0.15])
        for r, w in zip(risks, weights):
            rows.append({"Node": g_id, "RiskLevel": r,
                          "Count": int(w * 500 + np.random.randint(-15, 15))})
    return pd.DataFrame(rows)


df_ts = generate_timeseries_data()
df_epi = generate_epidemiological_distribution()
df_risk = generate_risk_distribution()

# ==========================================
# HEADER
# ==========================================
st.markdown("""
<div class="header-container">
    <h1 class="header-title">☁️ AyushBot Cloud Analytics</h1>
    <p class="header-subtitle">Federated Learning Aggregator & Edge Fleet Telemetry — North Karnataka Cluster</p>
</div>
""", unsafe_allow_html=True)

# ==========================================
# TABS
# ==========================================
tab_fleet, tab_compare, tab_fl = st.tabs([
    "🛰️ Edge Fleet Status",
    "⚖️ Node Comparison",
    "🧠 Global Federated Learning"
])

# ------------------------------------------
# TAB 1: FLEET STATUS
# ------------------------------------------
with tab_fleet:
    st.subheader("Karnataka PHC Grid — North Karnataka Cluster")

    online_count = sum(1 for m in GATEWAYS.values() if m["status"] == "Online")
    total_count = len(GATEWAYS)
    total_triages = int(df_ts["TriageCount"].sum())
    critical_count = int(df_risk[df_risk["RiskLevel"] == "CRITICAL"]["Count"].sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        badge_cls = "online" if online_count == total_count else "idle"
        badge_txt = "All Operational" if online_count == total_count else f"{total_count - online_count} Node(s) Down"
        st.markdown(f"""
        <div class="glass-card">
            <p style="color:#94A3B8;font-size:0.9rem;margin:0;">ACTIVE EDGE SYSTEMS</p>
            <p class="metric-val val-cyan">{online_count} / {total_count} Nodes</p>
            <span class="badge badge-{badge_cls}">{badge_txt}</span>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="glass-card">
            <p style="color:#94A3B8;font-size:0.9rem;margin:0;">TOTAL TRIAGES (30D)</p>
            <p class="metric-val val-indigo">{total_triages:,} cases</p>
            <span style="color:#10B981;font-size:0.8rem;font-weight:600;">North Karnataka Grid</span>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="glass-card">
            <p style="color:#94A3B8;font-size:0.9rem;margin:0;">GLOBAL ACCURACY (v2.4)</p>
            <p class="metric-val val-emerald">91.82%</p>
            <span class="badge badge-online">Model Synced</span>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="glass-card">
            <p style="color:#94A3B8;font-size:0.9rem;margin:0;">CRITICAL REFERRALS</p>
            <p class="metric-val val-rose">{critical_count:,} cases</p>
            <span style="color:#F43F5E;font-size:0.8rem;font-weight:600;">Immediate action required</span>
        </div>""", unsafe_allow_html=True)

    # Map and table
    map_col, tbl_col = st.columns([3, 2])
    with map_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write("🌍 **Geospatial Node Deployment — North Karnataka**")
        map_df = pd.DataFrame([
            {"Name": n, "Latitude": m["lat"], "Longitude": m["lon"],
             "Status": m["status"], "Temp": m["temp"]}
            for n, m in GATEWAYS.items()
        ])
        fig_map = px.scatter_map(
            map_df, lat="Latitude", lon="Longitude", text="Name", color="Status",
            color_discrete_map={"Online": "#10B981", "Idle": "#F59E0B", "Offline": "#F43F5E"},
            zoom=7.5, center={"lat": 15.1, "lon": 75.3}, height=360,
        )
        fig_map.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_map, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tbl_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write("📊 **Edge Device Telemetry**")
        telemetry_rows = []
        for name, meta in GATEWAYS.items():
            telemetry_rows.append({
                "PHC Gateway": name.split(" (")[0],
                "Status": meta["status"],
                "Sync": meta["sync_time"],
                "FW": meta["fw_ver"],
                "Batt": f"{meta['batt']}%",
                "Temp": f"{meta['temp']}°C"
            })
        st.dataframe(pd.DataFrame(telemetry_rows), hide_index=True, use_container_width=True)
        st.markdown("""
**Warnings:**
- 🔴 **PHC-05 (Shiggaon)** OFFLINE 5+ days. Firmware `v2.3.9`. Battery `8%`. Solar diagnostic required.
- 🟡 **PHC-04 (Gadag)** firmware `v2.4.0` — upgrade to `v2.4.1` recommended.
- 🟡 **PHC-03 (Ranebennur)** battery `55%`. Moderate connectivity instability.
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------
# TAB 2: NODE COMPARISON
# ------------------------------------------
with tab_compare:
    st.subheader("Interactive Node Comparison")

    nodes = list(GATEWAYS.keys())
    selected_nodes = st.multiselect(
        "Select Karnataka PHC Gateways to Compare (2 to 5):",
        options=nodes,
        default=nodes[:3]
    )

    if len(selected_nodes) < 2 or len(selected_nodes) > 5:
        st.warning("⚠️ Please select between 2 and 5 nodes to compare.")
    else:
        # Filter datasets
        df_ts_comp = df_ts[df_ts["Node"].isin(selected_nodes)]
        df_epi_comp = df_epi[df_epi["Node"].isin(selected_nodes)]
        df_risk_comp = df_risk[df_risk["Node"].isin(selected_nodes)]

        plot_col1, plot_col2 = st.columns(2)

        with plot_col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write("📈 **Triage Encounter Volume (30 Days)**")
            fig_vol = px.line(
                df_ts_comp, x="Date", y="TriageCount", color="Node",
                color_discrete_sequence=PLOT_COLORS, line_shape="spline", height=320
            )
            fig_vol.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig_vol, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write("🦠 **Condition Distribution**")
            fig_epi = px.bar(
                df_epi_comp, x="Condition", y="Cases", color="Node",
                barmode="group", color_discrete_sequence=PLOT_COLORS, height=320
            )
            fig_epi.update_layout(**{**PLOT_LAYOUT, "xaxis": dict(showgrid=False)})
            st.plotly_chart(fig_epi, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with plot_col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write("🧠 **Model Drift from Global Consensus**")
            fig_drift = px.line(
                df_ts_comp, x="Date", y="ModelDrift", color="Node",
                color_discrete_sequence=PLOT_COLORS, height=320
            )
            fig_drift.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig_drift, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write("🔋 **Battery Decay Comparison**")
            fig_batt = px.line(
                df_ts_comp, x="Date", y="BatteryCharge", color="Node",
                color_discrete_sequence=PLOT_COLORS, height=320
            )
            fig_batt.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig_batt, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Bottom row
        st.write("### Triage Risks & Privacy Budgets")
        bot_col1, bot_col2 = st.columns(2)
        with bot_col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write("⚠️ **Patient Risk Allocation**")
            fig_risk_chart = px.bar(
                df_risk_comp, x="RiskLevel", y="Count", color="Node",
                barmode="group", color_discrete_sequence=PLOT_COLORS, height=300
            )
            fig_risk_chart.update_layout(**{**PLOT_LAYOUT, "xaxis": dict(showgrid=False)})
            st.plotly_chart(fig_risk_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with bot_col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.write(r"🔐 **Privacy Budget Epsilon ($\epsilon$) Spending**")
            fig_eps = px.area(
                df_ts_comp, x="Date", y="PrivacyEpsilon", color="Node",
                color_discrete_sequence=PLOT_COLORS, height=300
            )
            fig_eps.update_layout(**PLOT_LAYOUT)
            st.plotly_chart(fig_eps, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------
# TAB 3: GLOBAL FL
# ------------------------------------------
with tab_fl:
    st.subheader("Global Model Aggregation Performance")

    fl_col1, fl_col2 = st.columns(2)
    with fl_col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write("🧠 **Global XGBoost Accuracy (Rounds 1-20)**")
        rounds = list(range(1, 21))
        global_acc = [0.72 + (0.92 - 0.72) * (1 - np.exp(-r / 6.0)) + np.random.uniform(-0.01, 0.01) for r in rounds]
        fig_accuracy = go.Figure()
        fig_accuracy.add_trace(go.Scatter(
            x=rounds, y=global_acc, mode='lines+markers',
            line=dict(color='#818CF8', width=3),
            marker=dict(size=8, color='#C084FC')
        ))
        fig_accuracy.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color="#E2E8F0",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(title="FL Round", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title="Validation Accuracy", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
            height=320, margin=dict(t=10, b=10, l=10, r=10)
        )
        st.plotly_chart(fig_accuracy, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with fl_col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.write("🛠️ **Aggregation Strategy**")
        st.markdown("""
The cloud server uses Flower framework with **Trimmed Mean (Byzantine-Resilient)** strategy:
* **Model**: XGBoost Classifier (`agent_intake`)
* **Latest**: `ayushbot-global-intake-v2.4.1`
* **Strategy**: `FedTrimmedMean` (drops worst 20% outlier updates)
* **mTLS**: Active
        """)
        st.write("🔄 **Actions**")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Trigger Manual FL Round", type="primary"):
                st.info("Initiating FL aggregation round...")
        with col_btn2:
            st.button("Rollback to v2.3.9")
        st.markdown('</div>', unsafe_allow_html=True)
