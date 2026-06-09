"""
pages/2_Run_Audit.py
Audit runner page — configure, execute, and stream results.
"""

import streamlit as st
import pandas as pd
import json, time, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import DOMAINS, DOMAIN_ICONS, RISK_COLORS, LLM_MODELS
from auditor.scorer import score_response
from auditor.llm_runner import call_llm
from auditor.caigs import compute_caigs

# ── Page setup ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Run Audit | AI Hallucination Auditor",
                   page_icon="🧪", layout="wide")
st.title("🧪 Run Hallucination Audit")
st.caption("Test LLM outputs against verified ground truth for Indian business domains.")

# ── Load ground truth ─────────────────────────────────────────────────────────
@st.cache_data
def load_ground_truth():
    gt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "data", "ground_truth.json")
    with open(gt_path) as f:
        return json.load(f)

ground_truth = load_ground_truth()

# ── Sidebar config ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Audit Configuration")

    st.subheader("API Keys")
    openai_key     = st.text_input("OpenAI API Key",    type="password",
                                   placeholder="sk-...")
    anthropic_key  = st.text_input("Anthropic API Key", type="password",
                                   placeholder="sk-ant-...")
    google_key     = st.text_input("Google API Key",    type="password",
                                   placeholder="AIza...")

    st.subheader("Domains")
    selected_domains = st.multiselect(
        "Select domains to audit",
        options=DOMAINS,
        default=["Finance", "Legal"],
        format_func=lambda d: f"{DOMAIN_ICONS.get(d, '')} {d}",
    )

    st.subheader("LLM Models")
    available_models = []
    if openai_key:
        available_models += ["GPT-4o", "GPT-3.5"]
    if anthropic_key:
        available_models += ["Claude Sonnet", "Claude Haiku"]
    if google_key:
        available_models += ["Gemini Pro", "Gemini Flash"]

    if available_models:
        selected_models = st.multiselect(
            "Models to test",
            options=available_models,
            default=available_models[:1],
        )
    else:
        st.warning("Enter at least one API key to enable models.")
        selected_models = []

    st.subheader("Test Scope")
    prompts_per_domain = st.slider("Prompts per domain", 1, 10, 5)
    risk_filter = st.multiselect(
        "Risk levels to include",
        options=["critical", "high", "medium", "low"],
        default=["critical", "high", "medium", "low"],
    )

# ── Main panel ────────────────────────────────────────────────────────────────
total_tests = len(selected_domains) * len(selected_models) * prompts_per_domain

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.info(f"Ready to run **{total_tests} tests** "
            f"({len(selected_domains)} domains × "
            f"{len(selected_models) or '?'} model(s) × "
            f"{prompts_per_domain} prompts each)")

with col_btn:
    run_btn = st.button(
        "▶ Start Audit",
        type="primary",
        use_container_width=True,
        disabled=(not selected_models or not selected_domains),
    )

if run_btn:
    if not selected_models:
        st.error("Enter at least one API key and select a model.")
        st.stop()

    api_keys = {
        "openai":    openai_key,
        "anthropic": anthropic_key,
        "google":    google_key,
    }

    results = []
    overall_progress = st.progress(0, text="Starting audit…")
    status_box       = st.empty()

    processed = 0

    for domain in selected_domains:
        domain_prompts = [
            p for p in ground_truth.get(domain, [])
            if p["risk_level"] in risk_filter
        ][:prompts_per_domain]

        st.markdown(f"### {DOMAIN_ICONS.get(domain, '')} {domain}")
        domain_expander = st.expander("Live results", expanded=True)

        for prompt_obj in domain_prompts:
            for model_key in selected_models:

                status_box.markdown(
                    f"**Testing:** `{model_key}` | **Domain:** {domain} | "
                    f"**Prompt:** _{prompt_obj['prompt'][:80]}…_"
                )

                # ── Call LLM ──────────────────────────────────────────────────
                llm_result = call_llm(
                    prompt_obj["prompt"], model_key, api_keys
                )

                # ── Score response ────────────────────────────────────────────
                if llm_result["success"]:
                    scores = score_response(
                        response       = llm_result["response"],
                        ground_truth   = prompt_obj["ground_truth"],
                        risk_level     = prompt_obj["risk_level"],
                        domain_keywords= prompt_obj.get("keywords", []),
                    )
                else:
                    scores = {
                        "composite_score": 0, "is_hallucinated": True,
                        "verdict": "API ERROR", "confidence": "high",
                        "semantic_similarity": 0, "numerical_accuracy": 0,
                        "rouge_l": 0, "keyword_coverage": 0,
                        "error": llm_result["error"],
                    }

                row = {
                    "domain":       domain,
                    "prompt_id":    prompt_obj["id"],
                    "prompt":       prompt_obj["prompt"],
                    "ground_truth": prompt_obj["ground_truth"],
                    "risk_level":   prompt_obj["risk_level"],
                    "source":       prompt_obj.get("source", ""),
                    "financial_impact": prompt_obj.get("financial_impact", ""),
                    "llm":          model_key,
                    "response":     llm_result.get("response", ""),
                    "tokens_used":  llm_result.get("tokens_used", 0),
                    **scores,
                }
                results.append(row)

                # ── Show live result ──────────────────────────────────────────
                verdict_color = (
                    "#FF4B2B" if scores["is_hallucinated"]
                    else "#20BF6B"
                )
                verdict_label = scores.get("verdict", "UNKNOWN")
                with domain_expander:
                    st.markdown(
                        f"""<div style='padding:10px;margin-bottom:8px;
                            border-left:4px solid {verdict_color};
                            background:{verdict_color}11;border-radius:4px'>
                            <strong>[{model_key}]</strong>
                            <span style='color:{verdict_color};font-weight:700;
                                        margin-left:10px'>{verdict_label}</span>
                            <span style='color:#888;font-size:12px;
                                        margin-left:10px'>
                                Score: {scores['composite_score']:.1f}% |
                                Risk: {prompt_obj['risk_level'].upper()}
                            </span>
                            <br/><small style='color:#aaa'>
                                Q: {prompt_obj['prompt'][:100]}…</small>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                processed += 1
                pct = processed / max(total_tests, 1)
                overall_progress.progress(pct, text=f"Progress: {processed}/{total_tests}")

    # ── Save results ──────────────────────────────────────────────────────────
    df = pd.DataFrame(results)
    st.session_state["results_df"] = df
    st.session_state["caigs"]      = compute_caigs(df)
    overall_progress.progress(1.0, text="✅ Audit complete!")
    status_box.success(f"Audit complete! {len(df)} results recorded.")

    # ── Quick summary ─────────────────────────────────────────────────────────
    hall_count = int(df["is_hallucinated"].sum())
    hall_rate  = df["is_hallucinated"].mean() * 100
    st.success(
        f"**{hall_count}** hallucinations detected out of **{len(df)}** tests "
        f"(**{hall_rate:.1f}%** hallucination rate). "
        f"Navigate to 📊 Dashboard or 🏛 CAIGS Framework for full analysis."
    )

# ── Show existing results if available ────────────────────────────────────────
elif "results_df" in st.session_state and not st.session_state["results_df"].empty:
    st.success("Previous audit data loaded. Press **▶ Start Audit** to run a new audit.")
    df = st.session_state["results_df"]
    st.dataframe(
        df[["domain", "llm", "risk_level", "verdict", "composite_score", "prompt"]].head(20),
        use_container_width=True,
    )
