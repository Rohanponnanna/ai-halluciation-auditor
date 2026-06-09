"""
pages/4_CAIGS_Framework.py
Corporate AI Integrity Governance Scorecard — full framework page.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    DOMAINS, DOMAIN_COLORS, DOMAIN_ICONS,
    RISK_COLORS, CAIGS_GRADES, DOMAIN_WEIGHTS
)
from auditor.caigs import compute_caigs

st.set_page_config(
    page_title="CAIGS Framework | AI Hallucination Auditor",
    page_icon="🏛", layout="wide"
)
st.title("🏛 CAIGS — Corporate AI Integrity Governance Scorecard")
st.caption("India Business Context | v1.0")

# ── Recompute or use cached CAIGS ─────────────────────────────────────────────
if "results_df" not in st.session_state or st.session_state["results_df"].empty:
    caigs = None
else:
    caigs = compute_caigs(st.session_state["results_df"])

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CAIGS Score Card
# ═══════════════════════════════════════════════════════════════════════════════
st.header("1. Overall CAIGS Score")

if caigs:
    grade      = caigs["grade"]
    grade_meta = caigs["grade_meta"]
    score      = caigs["caigs_score"]

    g_col = grade_meta["color"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(
        f"""<div style='text-align:center;padding:20px;border-radius:12px;
            border:2px solid {g_col};background:{g_col}18'>
            <div style='font-size:11px;color:{g_col};letter-spacing:2px;
                        text-transform:uppercase;margin-bottom:8px'>CAIGS Grade</div>
            <div style='font-size:56px;font-weight:900;color:{g_col}'>{grade}</div>
            <div style='font-size:13px;color:{g_col};font-weight:600'>
                {grade_meta['label']}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    c2.metric("CAIGS Score",          f"{score}/100")
    c3.metric("Overall Hall. Rate",   f"{caigs['overall_hallucination_rate']}%")
    c4.metric("Avg Accuracy",         f"{caigs['overall_avg_accuracy']}%")
    c5.metric("Est. Financial Risk",  f"₹{caigs['estimated_financial_risk_lakhs']}L")

    st.markdown(
        f"""<div style='margin-top:16px;padding:14px 20px;border-radius:8px;
            background:{g_col}18;border-left:4px solid {g_col}'>
            <b>Recommended Action:</b> {grade_meta['action']}
        </div>""",
        unsafe_allow_html=True,
    )
else:
    st.info("Run an audit from **🧪 Run Audit** to generate your CAIGS score.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Domain Breakdown
# ═══════════════════════════════════════════════════════════════════════════════
st.header("2. Domain-Level Risk Breakdown")

if caigs and caigs["domain_stats"]:
    ds = caigs["domain_stats"]
    rows = []
    for d, s in ds.items():
        rows.append({
            "Domain": f"{DOMAIN_ICONS.get(d,'')} {d}",
            "Tests": s["total_tests"],
            "Hallucinated": s["hallucinated"],
            "Hall. Rate %": s["hallucination_rate"],
            "W. Hall. Rate %": s["weighted_hall_rate"],
            "Avg Accuracy %": s["avg_accuracy"],
            "Domain Weight": f"{s['domain_weight']*100:.0f}%",
        })
    domain_df = pd.DataFrame(rows)

    st.dataframe(
        domain_df.style
            .background_gradient(subset=["Hall. Rate %"],  cmap="RdYlGn_r", vmin=0, vmax=100)
            .background_gradient(subset=["Avg Accuracy %"], cmap="RdYlGn",   vmin=0, vmax=100)
            .format({"Hall. Rate %": "{:.1f}", "W. Hall. Rate %": "{:.1f}",
                     "Avg Accuracy %": "{:.1f}"}),
        use_container_width=True,
    )

    # Radar chart of domain accuracy
    domains_list  = list(ds.keys())
    accuracy_vals = [ds[d]["avg_accuracy"] for d in domains_list]
    hall_vals     = [ds[d]["hallucination_rate"] for d in domains_list]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=accuracy_vals + [accuracy_vals[0]],
        theta=domains_list + [domains_list[0]],
        fill="toself", name="Avg Accuracy",
        line_color="#20BF6B", fillcolor="rgba(32,191,107,0.15)"
    ))
    fig.add_trace(go.Scatterpolar(
        r=hall_vals + [hall_vals[0]],
        theta=domains_list + [domains_list[0]],
        fill="toself", name="Hall. Rate %",
        line_color="#FF4B2B", fillcolor="rgba(255,75,43,0.15)"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True, height=400,
        title="Domain Accuracy vs Hallucination Rate (Radar)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No domain data yet.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — LLM Comparison
# ═══════════════════════════════════════════════════════════════════════════════
st.header("3. LLM Performance Comparison")

if caigs and caigs.get("llm_stats"):
    ls = caigs["llm_stats"]
    llm_rows = []
    for llm, s in ls.items():
        llm_rows.append({
            "LLM": llm,
            "Tests": s["total"],
            "Hallucinated": s["hallucinated"],
            "Hall. Rate %": s["hall_rate"],
            "Avg Score %": s["avg_score"],
            "Best Domain": s["best_domain"],
            "Worst Domain": s["worst_domain"],
        })
    llm_df = pd.DataFrame(llm_rows)
    st.dataframe(
        llm_df.style
            .background_gradient(subset=["Hall. Rate %"], cmap="RdYlGn_r", vmin=0, vmax=100)
            .background_gradient(subset=["Avg Score %"],  cmap="RdYlGn",   vmin=0, vmax=100)
            .format({"Hall. Rate %": "{:.1f}", "Avg Score %": "{:.1f}"}),
        use_container_width=True,
    )
else:
    st.info("Test multiple LLMs to see comparison data.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Recommendations
# ═══════════════════════════════════════════════════════════════════════════════
st.header("4. Governance Recommendations")

if caigs and caigs["recommendations"]:
    for rec in caigs["recommendations"]:
        if rec.startswith("🚨") or rec.startswith("🔴"):
            st.error(rec)
        elif rec.startswith("⚠️") or rec.startswith("🟠"):
            st.warning(rec)
        elif rec.startswith("🟡"):
            st.warning(rec)
        else:
            st.info(rec)
else:
    st.info("Run an audit to generate recommendations.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Five Pillars Framework (always visible)
# ═══════════════════════════════════════════════════════════════════════════════
st.header("5. CAIGS Five Pillars Framework")

pillars = [
    {
        "icon": "🔍", "title": "Pillar 1: Detection",
        "color": "#FF4B2B",
        "items": [
            "Domain-specific hallucination testing suite (500 prompts)",
            "Automated fact-checking vs verified India-specific ground truth",
            "Composite scoring: semantic similarity + numerical accuracy + ROUGE-L",
            "Risk-weighted error classification (Critical / High / Medium / Low)",
            "Continuous regression testing as LLM versions update",
        ]
    },
    {
        "icon": "⚖️", "title": "Pillar 2: Classification",
        "color": "#6C63FF",
        "items": [
            "Critical risk: Finance/Legal decisions with ₹50L+ exposure",
            "High risk: HR compliance, ops regulations, SEBI/RBI guidelines",
            "Medium risk: Marketing claims, general market data",
            "Low risk: Background research, non-regulatory information",
            "Financial harm estimation model per domain × risk combination",
        ]
    },
    {
        "icon": "🛡️", "title": "Pillar 3: Governance",
        "color": "#F7B731",
        "items": [
            "AI Output Verification Checklist (AOVC) — mandatory for Critical/High",
            "Human-in-loop protocol: CA sign-off for Finance, Lawyer for Legal",
            "Audit trail with timestamp, LLM version, prompt hash, and score",
            "Board-level AI Risk Report template (quarterly)",
            "Vendor/LLM procurement due diligence scorecard",
        ]
    },
    {
        "icon": "📈", "title": "Pillar 4: Monitoring",
        "color": "#20BF6B",
        "items": [
            "CAIGS dashboard with real-time hallucination rate tracking",
            "Domain-level trending charts (weekly/monthly/quarterly)",
            "LLM version comparison to detect model regression",
            "Incident log: all hallucinations that caused business harm",
            "Regulatory change alerts: auto-update ground truth library",
        ]
    },
    {
        "icon": "🏢", "title": "Pillar 5: Culture",
        "color": "#2D98DA",
        "items": [
            "Mandatory AI literacy training for all decision-makers",
            "Prompt engineering standards and approved prompt library",
            "Clear AI Acceptable Use Policy (AUP) with disciplinary clauses",
            "Whistleblower mechanism for reporting AI errors without penalty",
            "Annual AI Ethics review by Board / Audit Committee",
        ]
    },
]

p_cols = st.columns(len(pillars))
for i, (col, pillar) in enumerate(zip(p_cols, pillars)):
    with col:
        st.markdown(
            f"""<div style='border:1px solid {pillar['color']}44;
                border-radius:12px;padding:16px;height:100%;
                background:{pillar['color']}08'>
                <div style='font-size:28px;margin-bottom:8px'>{pillar['icon']}</div>
                <div style='font-size:13px;font-weight:700;color:{pillar['color']};
                            margin-bottom:12px'>{pillar['title']}</div>
                {''.join(f"<div style='font-size:11px;color:#888;margin-bottom:6px;display:flex;gap:6px'><span style='color:{pillar['color']}'>→</span><span>{item}</span></div>" for item in pillar['items'])}
            </div>""",
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Domain Risk Matrix Table
# ═══════════════════════════════════════════════════════════════════════════════
st.header("6. Domain Risk Classification Matrix")

matrix_data = [
    {
        "Domain": "💰 Finance",
        "Hallucination Risk": "🔴 Critical",
        "Typical Financial Exposure": "₹10L – ₹10Cr per incident",
        "Key Regulations": "GST Act, Income Tax Act, SEBI, RBI",
        "Recommended Control": "Mandatory CA / CFO sign-off before action",
        "Max Penalty": "₹50L+ / prosecution",
    },
    {
        "Domain": "⚖️ Legal",
        "Hallucination Risk": "🔴 Critical",
        "Typical Financial Exposure": "₹50L+ litigation exposure",
        "Key Regulations": "IBC 2016, Companies Act 2013, DPDP Act 2023",
        "Recommended Control": "Use as first draft only; Lawyer mandatory",
        "Max Penalty": "Injunction + damages",
    },
    {
        "Domain": "👥 HR",
        "Hallucination Risk": "🟠 High",
        "Typical Financial Exposure": "₹5L – ₹50L liability",
        "Key Regulations": "Labour Codes 2020, EPF Act, POSH Act",
        "Recommended Control": "HR specialist verification required",
        "Max Penalty": "Back wages + reinstatement",
    },
    {
        "Domain": "⚙️ Operations",
        "Hallucination Risk": "🟠 High",
        "Typical Financial Exposure": "₹1L – ₹10L per violation",
        "Key Regulations": "Factories Act, FSSAI, GFR 2017, Companies Act",
        "Recommended Control": "Ops manager cross-check before implementation",
        "Max Penalty": "Premises sealing / prosecution",
    },
    {
        "Domain": "📣 Marketing",
        "Hallucination Risk": "🟡 Medium",
        "Typical Financial Exposure": "₹50K – ₹5L per campaign",
        "Key Regulations": "ASCI Code, Consumer Protection Act 2019, TRAI",
        "Recommended Control": "Brand team spot-check on regulatory claims",
        "Max Penalty": "₹50L (misleading ads)",
    },
]

st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Research Novelty
# ═══════════════════════════════════════════════════════════════════════════════
st.header("7. Research Contributions & Novelty")

novelty_items = [
    ("01", "First MBA-level hallucination quantification framework for Indian business context",
     "Existing research is purely NLP/technical; zero management analytics perspective"),
    ("02", "Financial harm estimation methodology by domain × risk level",
     "Maps hallucination incidents to actual INR exposure using Indian regulatory benchmarks"),
    ("03", "Corporate Governance structure for AI output verification",
     "Board-level reporting template; AOVC checklist; domain-specific human-in-loop protocols"),
    ("04", "Regulatory mapping of AI risks to existing Indian law",
     "DPDP Act 2023, IBC 2016, Labour Codes 2020, SEBI, RBI, GST Council mapped to AI risk tiers"),
    ("05", "CAIGS Scorecard enabling cross-company AI risk benchmarking",
     "Standardised A–D grading system comparable across Indian enterprises"),
    ("06", "500-prompt domain-specific test suite for Indian business context",
     "Covers GST, EPF, POSH, IBC, ASCI, GeM — verified against primary regulatory sources"),
]

for num, title, detail in novelty_items:
    with st.expander(f"**{num}.** {title}"):
        st.write(detail)
