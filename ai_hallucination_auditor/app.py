"""
app.py — Main entry point for AI Hallucination Risk Auditor
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import sys, os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    APP_TITLE, APP_SUBTITLE, APP_VERSION, APP_ICON,
    DOMAINS, DOMAIN_COLORS, DOMAIN_ICONS, RISK_COLORS
)

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark sidebar */
    [data-testid="stSidebar"] {background: #0d0d17;}

    /* Main metric cards */
    [data-testid="metric-container"] {
        background: #12121e;
        border: 1px solid #1e1e2e;
        border-radius: 10px;
        padding: 12px 16px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* Remove default padding */
    .block-container {padding-top: 1.5rem;}

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {font-weight: 600;}

    /* Dividers */
    hr {border-color: #1e1e2e;}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center;padding:20px 0 10px'>
        <div style='font-size:40px'>{APP_ICON}</div>
        <div style='font-size:15px;font-weight:700;color:#fff;margin-top:8px'>
            {APP_TITLE}
        </div>
        <div style='font-size:10px;color:#555;letter-spacing:2px;
                    text-transform:uppercase;margin-top:4px'>
            {APP_SUBTITLE}
        </div>
        <div style='margin-top:10px;background:#FF4B2B22;border:1px solid #FF4B2B44;
                    color:#FF4B2B;padding:3px 12px;border-radius:99px;
                    font-size:11px;font-weight:700;display:inline-block'>
            v{APP_VERSION} · CAIGS
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Status indicator
    has_results = (
        "results_df" in st.session_state
        and not st.session_state["results_df"].empty
    )
    if has_results:
        df = st.session_state["results_df"]
        st.success(f"✅ {len(df)} results loaded")
        hall_rate = df["is_hallucinated"].mean() * 100
        st.metric("Hallucination Rate", f"{hall_rate:.1f}%")
        st.metric("Tests Completed",    len(df))
    else:
        st.info("No audit data yet.\nGo to **🧪 Run Audit** to start.")

    st.divider()
    st.caption("**Navigation**")
    st.markdown("""
    - 🏠 **Home** — Overview & quick start
    - 📊 **Dashboard** — Charts & domain analysis
    - 🧪 **Run Audit** — Execute LLM tests
    - 📋 **Results Log** — Filter & export
    - 🏛 **CAIGS Framework** — Governance scorecard
    """)

    st.divider()
    st.caption(f"Built for MBA Research · India Business Context")

# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='background:linear-gradient(135deg,#12121e,#0d0d17);
            border:1px solid #1e1e2e;border-radius:16px;
            padding:36px 40px;margin-bottom:32px'>
    <div style='display:flex;align-items:center;gap:16px;margin-bottom:16px'>
        <span style='font-size:48px'>{APP_ICON}</span>
        <div>
            <h1 style='margin:0;color:#fff;font-size:28px'>{APP_TITLE}</h1>
            <p style='margin:0;color:#555;font-size:14px'>{APP_SUBTITLE}</p>
        </div>
    </div>
    <p style='color:#aaa;font-size:15px;max-width:700px;line-height:1.7;margin:0'>
        The first MBA-level framework to systematically measure, classify, and govern
        AI hallucination risk in Indian business decision-making — across Finance,
        HR, Legal, Marketing, and Operations domains.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Quick-start steps ─────────────────────────────────────────────────────────
st.subheader("🚀 Quick Start")
s1, s2, s3, s4 = st.columns(4)

steps = [
    ("1️⃣", "Add API Keys",
     "Enter your OpenAI / Anthropic / Google API keys in **🧪 Run Audit** sidebar."),
    ("2️⃣", "Select Domains & Models",
     "Choose which business domains and LLMs to test against Indian ground truth."),
    ("3️⃣", "Run Audit",
     "Click **▶ Start Audit** — results stream in real time with live scoring."),
    ("4️⃣", "View CAIGS Score",
     "Get your Corporate AI Integrity Grade (A–D) with financial risk estimates."),
]

for col, (icon, title, desc) in zip([s1, s2, s3, s4], steps):
    col.markdown(
        f"""<div style='background:#12121e;border:1px solid #1e1e2e;
            border-radius:12px;padding:20px;height:160px'>
            <div style='font-size:28px'>{icon}</div>
            <div style='font-weight:700;color:#fff;margin:8px 0 6px'>{title}</div>
            <div style='font-size:13px;color:#888'>{desc}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# ── Domain coverage ───────────────────────────────────────────────────────────
st.subheader("📋 Test Suite Coverage")
st.caption("50 verified prompts across 5 domains (10 per domain) — India-specific regulatory ground truth")

for i, domain in enumerate(DOMAINS):
    color = DOMAIN_COLORS[domain]
    icon  = DOMAIN_ICONS[domain]

    domain_examples = {
        "Finance":    ["GST rates for SaaS services (18%)", "TDS Section 194J rates",
                       "Section 43B(h) MSME payment rules", "EPF contribution split",
                       "Corporate tax rate FY 2024-25"],
        "HR":         ["Gratuity formula under Payment of Gratuity Act",
                       "Maternity leave 26 weeks (2 children rule)",
                       "ESI contribution rates (0.75% / 3.25%)",
                       "POSH Act ICC composition (4 members)",
                       "Bonus payment obligations (8.33% – 20%)"],
        "Legal":      ["Limitation period 3 years for contract disputes",
                       "DPDP Act 2023 compliance requirements",
                       "Non-compete enforceability under Section 27",
                       "IBC CIRP 180-day resolution timeline",
                       "Stamp duty on share purchase agreements"],
        "Marketing":  ["ASCI influencer disclosure (#Ad, #Sponsored)",
                       "FDI 51% multi-brand retail conditions",
                       "SEBI celebrity endorsement guidelines",
                       "Drugs & Magic Remedies Act restrictions",
                       "TRAI TCCCPR email marketing rules"],
        "Operations": ["Factories Act 48-hour work week limit",
                       "CSR 2% spending threshold (₹500Cr net worth)",
                       "FSSAI Central License threshold (₹20Cr)",
                       "Ind AS 2 — LIFO not permitted in India",
                       "GSTR-9 annual return 31 December deadline"],
    }

    with st.expander(f"{icon} **{domain}** — 10 test prompts"):
        for ex in domain_examples.get(domain, []):
            st.markdown(
                f"<div style='padding:6px 12px;margin-bottom:4px;border-left:"
                f"3px solid {color};background:{color}0d;border-radius:0 6px 6px 0;"
                f"font-size:13px;color:#ccc'>→ {ex}</div>",
                unsafe_allow_html=True,
            )

st.divider()

# ── Research context ──────────────────────────────────────────────────────────
st.subheader("🎓 Research Context")

rc1, rc2, rc3 = st.columns(3)
rc1.markdown("""
**Why This Research Matters**
- Indian companies increasingly use ChatGPT, Claude, Gemini for real business decisions
- Finance teams filing GST returns using AI, HR citing wrong labour laws, Legal contracts with hallucinated clauses
- Zero MBA/management research quantifying this risk in Indian context
- CAIGS fills the gap between NLP hallucination papers and corporate governance
""")

rc2.markdown("""
**Research Methodology**
- **500-prompt test suite** across 5 business domains
- **4 LLMs tested**: GPT-4o, Claude, Gemini Pro, GPT-3.5
- **3-component scoring**: Semantic similarity + Numerical accuracy + ROUGE-L
- **Financial harm mapping**: Each hallucination → INR exposure estimate
- **CAIGS Scorecard**: A–D grade for board-level reporting
""")

rc3.markdown("""
**Novel Contributions**
- First India-specific business hallucination benchmark
- Financial harm quantification by domain × risk tier
- Corporate governance framework (5 pillars)
- Regulatory mapping: GST, EPF, IBC, DPDP, Labour Codes
- Replicable audit methodology for other researchers
""")

st.divider()
st.caption(
    "⚠️ **Disclaimer:** Ground truth is based on Indian regulations as of 2024. "
    "Always verify with qualified CA / legal professionals for actual business decisions. "
    "This tool is for research and educational purposes."
)
