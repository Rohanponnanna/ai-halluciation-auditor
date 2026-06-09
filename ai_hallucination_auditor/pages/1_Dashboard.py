"""
pages/1_Dashboard.py
Overview dashboard — KPI cards, domain heat map, LLM comparison.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DOMAIN_COLORS, DOMAIN_ICONS, RISK_COLORS

st.set_page_config(page_title="Dashboard | AI Hallucination Auditor",
                   page_icon="📊", layout="wide")

st.title("📊 Audit Dashboard")

if "results_df" not in st.session_state or st.session_state["results_df"].empty:
    st.info("👈 No audit data yet. Go to **🧪 Run Audit** in the sidebar to start testing.")
    st.stop()

df = st.session_state["results_df"]

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Tests Run",         len(df))
k2.metric("LLMs Tested",       df["llm"].nunique() if "llm" in df.columns else "—")
k3.metric("Hallucinations",    int(df["is_hallucinated"].sum()),
          delta=f"{df['is_hallucinated'].mean()*100:.1f}% rate", delta_color="inverse")
k4.metric("Avg Accuracy",      f"{df['composite_score'].mean():.1f}%")
k5.metric("Domains Tested",    df["domain"].nunique())

st.divider()

col_left, col_right = st.columns([1, 1])

# ── Domain hallucination bar chart ────────────────────────────────────────────
with col_left:
    st.subheader("Hallucination Rate by Domain")
    domain_summary = (
        df.groupby("domain")
          .agg(hall_rate=("is_hallucinated", "mean"),
               avg_score=("composite_score", "mean"),
               count=("is_hallucinated", "count"))
          .reset_index()
    )
    domain_summary["hall_pct"] = (domain_summary["hall_rate"] * 100).round(1)
    domain_summary["color"] = domain_summary["domain"].map(DOMAIN_COLORS)

    fig = px.bar(
        domain_summary, x="domain", y="hall_pct",
        color="domain",
        color_discrete_map=DOMAIN_COLORS,
        text="hall_pct",
        labels={"hall_pct": "Hallucination Rate (%)", "domain": "Domain"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        showlegend=False, height=350,
        yaxis_range=[0, min(100, domain_summary["hall_pct"].max() + 15)],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Accuracy heatmap (domain × risk) ─────────────────────────────────────────
with col_right:
    st.subheader("Accuracy Score: Domain × Risk Level")
    pivot = (
        df.groupby(["domain", "risk_level"])["composite_score"]
          .mean()
          .reset_index()
          .pivot(index="domain", columns="risk_level", values="composite_score")
    )
    # Ensure consistent column order
    for col in ["critical", "high", "medium", "low"]:
        if col not in pivot.columns:
            pivot[col] = None
    pivot = pivot[["critical", "high", "medium", "low"]]

    fig2 = px.imshow(
        pivot,
        color_continuous_scale="RdYlGn",
        zmin=0, zmax=100,
        text_auto=".1f",
        labels={"color": "Avg Accuracy (%)"},
    )
    fig2.update_layout(height=350,
                       plot_bgcolor="rgba(0,0,0,0)",
                       paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── LLM comparison (if multiple models tested) ────────────────────────────────
if "llm" in df.columns and df["llm"].nunique() > 1:
    st.subheader("LLM Performance Comparison")
    llm_summary = (
        df.groupby("llm")
          .agg(hall_rate=("is_hallucinated", "mean"),
               avg_score=("composite_score", "mean"),
               count=("is_hallucinated", "count"))
          .reset_index()
    )
    llm_summary["hall_pct"] = (llm_summary["hall_rate"] * 100).round(1)

    c1, c2 = st.columns(2)
    with c1:
        fig3 = px.bar(llm_summary, x="llm", y="hall_pct",
                      color="hall_pct", color_continuous_scale="RdYlGn_r",
                      title="Hallucination Rate by LLM (%)",
                      text="hall_pct")
        fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig3.update_layout(showlegend=False, height=300,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig3, use_container_width=True)
    with c2:
        fig4 = px.bar(llm_summary, x="llm", y="avg_score",
                      color="avg_score", color_continuous_scale="RdYlGn",
                      title="Average Accuracy Score by LLM (%)",
                      text="avg_score")
        fig4.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig4.update_layout(showlegend=False, height=300,
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig4, use_container_width=True)

# ── Risk-level breakdown ──────────────────────────────────────────────────────
st.divider()
st.subheader("Risk-Level Breakdown")
if "risk_level" in df.columns:
    risk_summary = (
        df.groupby("risk_level")
          .agg(hall_rate=("is_hallucinated", "mean"),
               count=("is_hallucinated", "count"))
          .reset_index()
    )
    risk_summary["hall_pct"] = (risk_summary["hall_rate"] * 100).round(1)
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    risk_summary["order"] = risk_summary["risk_level"].map(risk_order)
    risk_summary = risk_summary.sort_values("order")

    r_cols = st.columns(len(risk_summary))
    for i, (_, row) in enumerate(risk_summary.iterrows()):
        color = RISK_COLORS.get(row["risk_level"], "#888")
        r_cols[i].markdown(
            f"""<div style='text-align:center; padding:16px; border-radius:10px;
                border: 1px solid {color}44; background:{color}11'>
                <div style='font-size:11px;color:{color};font-weight:700;
                            letter-spacing:2px;text-transform:uppercase'>
                    {row['risk_level']}</div>
                <div style='font-size:32px;font-weight:800;color:{color}'>
                    {row['hall_pct']:.0f}%</div>
                <div style='font-size:12px;color:#888'>{int(row['count'])} tests</div>
            </div>""",
            unsafe_allow_html=True,
        )
