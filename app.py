import streamlit as st
import requests, os, pandas as pd
import time

# ================= SESSION STATE =================
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ================= BRAND CONFIG =================
PRIMARY = "#4F8BF9"
ACCENT = "#22C55E"
BG = "#0e1117"

SUPPORTED_DRUGS = [
    "Aspirin", "Paracetamol", "Metformin",
    "Ibuprofen", "Amoxicillin"
]

st.set_page_config(page_title="Mediscan AI", layout="wide")

# ================= GLOBAL STYLES =================
st.markdown(f"""
<style>
body {{
    background-color: {BG};
}}
.section-card {{
    background-color: #161b22;
    padding: 25px;
    border-radius: 16px;
    margin-bottom: 22px;
    animation: fadeIn 0.6s ease-in-out;
}}
.metric-card {{
    background-color: #161b22;
    padding: 20px;
    border-radius: 16px;
    text-align: center;
}}
.brand {{
    font-size: 32px;
    font-weight: 800;
    color: {PRIMARY};
}}
.sub-brand {{
    color: #9da5b4;
}}
@keyframes fadeIn {{
    from {{opacity: 0; transform: translateY(8px);}}
    to {{opacity: 1; transform: translateY(0);}}
}}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
st.sidebar.markdown("<div class='brand'>🧬 Mediscan AI</div>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='sub-brand'>Intelligent Drug Research Platform</div>", unsafe_allow_html=True)
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "🔬 Drug Analysis", "🔁 Comparison", "📊 Impact Analytics", "🌍 Community"]
)

# =====================================================
# 🏠 DASHBOARD
# =====================================================
if page == "🏠 Dashboard":
    st.markdown("<h1>Research Dashboard</h1>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("<div class='metric-card'><h3>Supported Drugs</h3><h2>20+</h2></div>", unsafe_allow_html=True)
    c2.markdown("<div class='metric-card'><h3>AI Agents</h3><h2>4</h2></div>", unsafe_allow_html=True)
    c3.markdown("<div class='metric-card'><h3>Gov Sources</h3><h2>2</h2></div>", unsafe_allow_html=True)
    c4.markdown("<div class='metric-card'><h3>Report Type</h3><h2>PDF</h2></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='section-card'>
    <h3>🧠 Platform Overview</h3>
    Mediscan AI integrates multi-agent research modules with
    government drug databases to provide structured,
    explainable, and academic-ready drug analysis.
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# 🔬 DRUG ANALYSIS
# =====================================================
if page == "🔬 Drug Analysis":
    st.markdown("<h1>Drug Intelligence Module</h1>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)

    drug = st.selectbox("Select Drug", [""] + SUPPORTED_DRUGS)
    manual = st.text_input("Or enter manually")

    if manual.strip():
        drug = manual.strip()

    analyze = st.button("🚀 Analyze Drug")
    st.markdown("</div>", unsafe_allow_html=True)

    if analyze:
        if not drug:
            st.warning("Please select a drug.")
        else:
            with st.spinner("Running AI research agents..."):
                time.sleep(1)
                res = requests.post(
                    "http://127.0.0.1:8000/analyze",
                    json={"drug": drug}
                ).json()

            st.session_state.last_result = res

            # Metrics
            c1, c2, c3 = st.columns(3)
            c1.metric("Drug", res["drug"])
            c2.metric("Confidence", res["confidence"])
            c3.metric("Agents Used", len(res["agent_progress"]))

            # Agent Flow
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.subheader("🤖 Agent Processing Flow")
            for step in res["agent_progress"]:
                st.success(step)
            st.markdown("</div>", unsafe_allow_html=True)

            # Findings
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.subheader("🔬 Key Findings")
            for f in res["findings"]:
                st.write("•", f)
            st.markdown("</div>", unsafe_allow_html=True)

            # Government Data
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            st.subheader("🏛 Government Data Reference")
            st.json(res["clinical_trials"])
            st.json(res["openfda"])
            st.markdown("</div>", unsafe_allow_html=True)

            # PDF Download
            if os.path.exists(res["pdf"]):
                with open(res["pdf"], "rb") as f:
                    st.download_button("📄 Download Full PDF Report", f)

# =====================================================
# 🔁 DRUG COMPARISON
# =====================================================
if page == "🔁 Comparison":
    st.markdown("<h1>Multi-Drug Comparison</h1>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    d1 = c1.selectbox("Drug A", [""] + SUPPORTED_DRUGS)
    d2 = c2.selectbox("Drug B", [""] + SUPPORTED_DRUGS)
    d3 = c3.selectbox("Drug C (optional)", [""] + SUPPORTED_DRUGS)

    if st.button("📊 Compare Drugs"):
        drugs = [d for d in [d1, d2, d3] if d]

        if len(drugs) < 2:
            st.warning("Select at least two drugs.")
        else:
            rows = []
            for d in drugs:
                r = requests.post(
                    "http://127.0.0.1:8000/analyze",
                    json={"drug": d}
                ).json()

                rows.append({
                    "Drug": d,
                    "Confidence": int(r["confidence"].replace("%", "")),
                    "Market Maturity": r["market"]["market_maturity"]
                })

            df = pd.DataFrame(rows)
            st.table(df)
            st.bar_chart(df.set_index("Drug")["Confidence"])

# =====================================================
# 📊 IMPACT ANALYTICS (WRITTEN + CHART)
# =====================================================
if page == "📊 Impact Analytics":
    st.markdown("<h1>Impact Analytics</h1>", unsafe_allow_html=True)

    if not st.session_state.last_result:
        st.warning("Please analyze a drug first.")
    else:
        res = st.session_state.last_result

        def map_score(value):
            mapping = {
                "Extremely High": 100,
                "Very High": 95,
                "High": 85,
                "Moderate": 70,
                "Medium": 65,
                "Low": 50,
                "Very Low": 40,
                "Mature": 85,
                "Highly Mature": 95,
                "Developing": 60
            }
            return mapping.get(value, 70)

        # Patient
        patient = res["patient_impact"]
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("👥 Patient Impact")
        st.markdown(f"""
        **Target Population:** {patient['target_population']}  
        **Accessibility:** {patient['accessibility']}  
        **Public Health Relevance:** {patient['public_health_relevance']}
        """)
        st.bar_chart(pd.DataFrame({
            "Metric": ["Accessibility"],
            "Score": [map_score(patient["accessibility"])]
        }).set_index("Metric"))
        st.markdown("</div>", unsafe_allow_html=True)

        # Literature
        literature = res["literature"]
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("📚 Literature Insights")
        st.markdown(f"""
        **Research Volume:** {literature['research_volume']}  
        **Recent Focus:** {literature['recent_focus']}  
        **Academic Interest:** {literature['academic_interest']}
        """)
        st.bar_chart(pd.DataFrame({
            "Metric": ["Research Volume"],
            "Score": [map_score(literature["research_volume"])]
        }).set_index("Metric"))
        st.markdown("</div>", unsafe_allow_html=True)

        # Market
        market = res["market"]
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        st.subheader("📈 Market Analysis")
        st.markdown(f"""
        **Market Maturity:** {market['market_maturity']}  
        **Estimated Cost Range:** {market['estimated_cost_range']}  
        **Repurposing Feasibility:** {market['repurposing_feasibility']}
        """)
        st.bar_chart(pd.DataFrame({
            "Metric": ["Market Maturity"],
            "Score": [map_score(market["market_maturity"])]
        }).set_index("Metric"))
        st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# 🌍 COMMUNITY
# =====================================================
if page == "🌍 Community":
    st.markdown("<h1>Community Engagement</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div class='section-card'>
    Mediscan AI promotes research awareness and supports
    community-level understanding of drug accessibility,
    public health relevance, and market feasibility.
    </div>
    """, unsafe_allow_html=True)

# ================= FOOTER =================
st.divider()
st.markdown("""
**Disclaimer:**  
This is an academic prototype. All analytics are simulated for educational use only.
""")
