"""
pages/3_Results_Log.py
Detailed, filterable results log with CSV/Excel export.
"""

import streamlit as st
import pandas as pd
import io, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DOMAINS, RISK_COLORS, DOMAIN_COLORS

st.set_page_config(page_title="Results Log | AI Hallucination Auditor",
                   page_icon="📋", layout="wide")
st.title("📋 Audit Results Log")

if "results_df" not in st.session_state or st.session_state["results_df"].empty:
    st.info("No results yet. Run an audit from **🧪 Run Audit**.")
    st.stop()

df = st.session_state["results_df"].copy()

# ── Filters ───────────────────────────────────────────────────────────────────
st.subheader("Filters")
f1, f2, f3, f4 = st.columns(4)

domain_filter  = f1.multiselect("Domain",     ["All"] + DOMAINS,          default=["All"])
risk_filter    = f2.multiselect("Risk Level", ["All", "critical", "high",
                                               "medium", "low"],           default=["All"])
verdict_filter = f3.selectbox("Verdict",      ["All", "HALLUCINATED", "ACCURATE"])
llm_filter     = f4.multiselect("LLM",        ["All"] + sorted(df["llm"].unique().tolist()),
                                               default=["All"])

# Apply filters
filtered = df.copy()
if "All" not in domain_filter:
    filtered = filtered[filtered["domain"].isin(domain_filter)]
if "All" not in risk_filter:
    filtered = filtered[filtered["risk_level"].isin(risk_filter)]
if verdict_filter != "All":
    filtered = filtered[filtered["verdict"] == verdict_filter]
if "All" not in llm_filter:
    filtered = filtered[filtered["llm"].isin(llm_filter)]

st.caption(f"Showing **{len(filtered)}** of **{len(df)}** results")

# ── Summary metrics for filtered set ─────────────────────────────────────────
if not filtered.empty:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Filtered Tests",     len(filtered))
    m2.metric("Hallucinations",     int(filtered["is_hallucinated"].sum()))
    m3.metric("Hallucination Rate", f"{filtered['is_hallucinated'].mean()*100:.1f}%")
    m4.metric("Avg Accuracy",       f"{filtered['composite_score'].mean():.1f}%")
    st.divider()

# ── Display table ─────────────────────────────────────────────────────────────
display_cols = [
    "domain", "llm", "risk_level", "verdict",
    "composite_score", "semantic_similarity", "numerical_accuracy",
    "rouge_l", "prompt",
]
available_cols = [c for c in display_cols if c in filtered.columns]

# Color the verdict column
def color_verdict(val):
    if val == "HALLUCINATED":
        return "background-color: #FF4B2B22; color: #FF4B2B; font-weight: bold"
    elif val == "ACCURATE":
        return "background-color: #20BF6B22; color: #20BF6B; font-weight: bold"
    return ""

def color_score(val):
    try:
        v = float(val)
        if v >= 80: return "color: #20BF6B"
        if v >= 55: return "color: #F7B731"
        return "color: #FF4B2B"
    except:
        return ""

styled = (
    filtered[available_cols]
    .style
    .applymap(color_verdict, subset=["verdict"])
    .applymap(color_score, subset=[c for c in ["composite_score",
              "semantic_similarity", "numerical_accuracy", "rouge_l"]
              if c in available_cols])
    .format({c: "{:.1f}" for c in ["composite_score", "semantic_similarity",
             "numerical_accuracy", "rouge_l"] if c in available_cols})
)

st.dataframe(styled, use_container_width=True, height=450)

# ── Detailed row viewer ───────────────────────────────────────────────────────
st.divider()
st.subheader("🔎 Detailed Response Inspector")
if not filtered.empty:
    row_idx = st.selectbox(
        "Select a result to inspect",
        options=range(len(filtered)),
        format_func=lambda i: (
            f"[{filtered.iloc[i]['llm']}] {filtered.iloc[i]['domain']} — "
            f"{filtered.iloc[i]['verdict']} — "
            f"{filtered.iloc[i]['prompt'][:60]}…"
        ),
    )
    row = filtered.iloc[row_idx]

    vcol = RISK_COLORS.get(row["risk_level"], "#888")
    st.markdown(f"""
    <div style='background:{vcol}11;border:1px solid {vcol}44;
                border-radius:10px;padding:20px;margin-bottom:16px'>
        <b style='color:{vcol}'>{row['verdict']}</b>
        &nbsp;|&nbsp; {row['domain']} &nbsp;|&nbsp; {row['llm']}
        &nbsp;|&nbsp; Risk: <b>{row['risk_level'].upper()}</b>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**📝 Prompt**")
        st.info(row["prompt"])
        st.markdown("**✅ Ground Truth**")
        st.success(row["ground_truth"])
        if row.get("source"):
            st.caption(f"Source: {row['source']}")
    with c2:
        st.markdown("**🤖 LLM Response**")
        verdict_color = "#FF4B2B" if row["is_hallucinated"] else "#20BF6B"
        st.markdown(
            f"<div style='background:{verdict_color}11;border:1px solid {verdict_color}33;"
            f"border-radius:8px;padding:12px'>{row.get('response','No response')}</div>",
            unsafe_allow_html=True,
        )
        st.markdown("**📊 Score Breakdown**")
        score_df = pd.DataFrame({
            "Metric": ["Composite", "Semantic Sim", "Numerical Acc", "ROUGE-L", "Keyword Cov"],
            "Score":  [
                row.get("composite_score", 0),
                row.get("semantic_similarity", 0),
                row.get("numerical_accuracy", 0),
                row.get("rouge_l", 0),
                row.get("keyword_coverage", 0),
            ],
        })
        for _, sr in score_df.iterrows():
            col_a, col_b = st.columns([2, 3])
            col_a.write(sr["Metric"])
            v = float(sr["Score"])
            color = "#20BF6B" if v >= 80 else "#F7B731" if v >= 55 else "#FF4B2B"
            col_b.progress(int(v), text=f"{v:.1f}%")

    if row.get("financial_impact"):
        st.warning(f"⚠️ **Financial Impact:** {row['financial_impact']}")

# ── Export ────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("⬇ Export Results")
ec1, ec2 = st.columns(2)

with ec1:
    csv_data = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📄 Download CSV",
        data=csv_data,
        file_name="hallucination_audit_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

with ec2:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        filtered.to_excel(writer, sheet_name="Audit Results", index=False)
        # Summary sheet
        summary = filtered.groupby(["domain", "risk_level"]).agg(
            tests=("is_hallucinated", "count"),
            hallucinated=("is_hallucinated", "sum"),
            hall_rate=("is_hallucinated", "mean"),
            avg_score=("composite_score", "mean"),
        ).reset_index()
        summary.to_excel(writer, sheet_name="Summary", index=False)
    st.download_button(
        "📊 Download Excel",
        data=excel_buffer.getvalue(),
        file_name="hallucination_audit_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
