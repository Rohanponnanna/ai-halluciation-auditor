"""
auditor/caigs.py
Corporate AI Integrity Governance Scorecard (CAIGS) v1.0
Computes overall and domain-level risk scores from audit results.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from config import (
    DOMAINS, DOMAIN_WEIGHTS, RISK_MULTIPLIERS,
    FINANCIAL_HARM_ESTIMATES, CAIGS_GRADES
)


def compute_caigs(df: pd.DataFrame) -> Dict:
    """
    Compute CAIGS from a results DataFrame.

    Required columns:
        domain, risk_level, is_hallucinated, composite_score,
        llm (model name)

    Returns a rich dict with overall score, grade, domain breakdown,
    LLM comparison, financial risk, and recommendations.
    """
    if df.empty:
        return _empty_caigs()

    # ── 1. Domain-level stats ─────────────────────────────────────────────────
    domain_stats = {}
    for domain in DOMAINS:
        d_df = df[df["domain"] == domain]
        if d_df.empty:
            continue

        total   = len(d_df)
        hall    = int(d_df["is_hallucinated"].sum())
        hall_rt = d_df["is_hallucinated"].mean() * 100
        avg_acc = d_df["composite_score"].mean()

        # Risk-weighted hallucination rate
        w_hall = 0.0
        for _, row in d_df.iterrows():
            mult = RISK_MULTIPLIERS.get(row["risk_level"], 1.0)
            w_hall += float(row["is_hallucinated"]) * mult
        w_hall_rate = (w_hall / total) * 100

        # Per-risk breakdown
        risk_breakdown = {}
        for rl in ["critical", "high", "medium", "low"]:
            rl_df = d_df[d_df["risk_level"] == rl]
            if not rl_df.empty:
                risk_breakdown[rl] = {
                    "count": len(rl_df),
                    "hallucinated": int(rl_df["is_hallucinated"].sum()),
                    "hall_rate": round(rl_df["is_hallucinated"].mean() * 100, 1),
                    "avg_score": round(rl_df["composite_score"].mean(), 1),
                }

        domain_stats[domain] = {
            "total_tests":          total,
            "hallucinated":         hall,
            "hallucination_rate":   round(hall_rt, 1),
            "weighted_hall_rate":   round(w_hall_rate, 1),
            "avg_accuracy":         round(avg_acc, 1),
            "domain_weight":        DOMAIN_WEIGHTS.get(domain, 0.2),
            "risk_breakdown":       risk_breakdown,
        }

    # ── 2. Overall CAIGS score ────────────────────────────────────────────────
    weighted_hall_sum = sum(
        s["weighted_hall_rate"] * s["domain_weight"]
        for s in domain_stats.values()
    )
    total_weight = sum(
        DOMAIN_WEIGHTS.get(d, 0.2) for d in domain_stats
    )
    normalised_hall = weighted_hall_sum / total_weight if total_weight else 0
    caigs_score = max(0.0, min(100.0, 100.0 - normalised_hall))

    # ── 3. Grade ──────────────────────────────────────────────────────────────
    grade = "D"
    for g, meta in CAIGS_GRADES.items():
        if caigs_score >= meta["min"]:
            grade = g
            break

    # ── 4. LLM comparison ─────────────────────────────────────────────────────
    llm_stats = {}
    if "llm" in df.columns:
        for llm_name in df["llm"].unique():
            l_df = df[df["llm"] == llm_name]
            llm_stats[llm_name] = {
                "total":           len(l_df),
                "hallucinated":    int(l_df["is_hallucinated"].sum()),
                "hall_rate":       round(l_df["is_hallucinated"].mean() * 100, 1),
                "avg_score":       round(l_df["composite_score"].mean(), 1),
                "best_domain":     _best_domain(l_df),
                "worst_domain":    _worst_domain(l_df),
            }

    # ── 5. Financial risk estimate ────────────────────────────────────────────
    total_financial_risk = 0.0
    hall_df = df[df["is_hallucinated"] == True]
    for _, row in hall_df.iterrows():
        key = (row["domain"], row["risk_level"])
        total_financial_risk += FINANCIAL_HARM_ESTIMATES.get(key, 2.0)

    # ── 6. Recommendations ────────────────────────────────────────────────────
    recs = _build_recommendations(grade, domain_stats, df)

    return {
        "caigs_score":                  round(caigs_score, 1),
        "grade":                        grade,
        "grade_meta":                   CAIGS_GRADES[grade],
        "overall_hallucination_rate":   round(df["is_hallucinated"].mean() * 100, 1),
        "total_tests":                  len(df),
        "total_hallucinated":           int(df["is_hallucinated"].sum()),
        "overall_avg_accuracy":         round(df["composite_score"].mean(), 1),
        "domain_stats":                 domain_stats,
        "llm_stats":                    llm_stats,
        "estimated_financial_risk_lakhs": round(total_financial_risk, 1),
        "recommendations":              recs,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _best_domain(l_df: pd.DataFrame) -> str:
    if l_df.empty:
        return "N/A"
    d = l_df.groupby("domain")["composite_score"].mean()
    return d.idxmax() if not d.empty else "N/A"


def _worst_domain(l_df: pd.DataFrame) -> str:
    if l_df.empty:
        return "N/A"
    d = l_df.groupby("domain")["composite_score"].mean()
    return d.idxmin() if not d.empty else "N/A"


def _build_recommendations(grade: str, domain_stats: Dict,
                            df: pd.DataFrame) -> List[str]:
    recs = []

    if grade == "D":
        recs.append("🚨 CRITICAL: Immediately suspend AI-only decision-making across all domains. Implement mandatory human oversight.")
    elif grade == "C":
        recs.append("⚠️ HIGH PRIORITY: Restrict AI use to draft generation only. All outputs require domain expert review before action.")

    for domain, stats in domain_stats.items():
        hr = stats["hallucination_rate"]
        if hr > 50:
            recs.append(f"🔴 {domain}: Hallucination rate {hr:.0f}% — PROHIBIT autonomous AI decisions. Require CA/lawyer/specialist sign-off.")
        elif hr > 30:
            recs.append(f"🟠 {domain}: Hallucination rate {hr:.0f}% — Implement dual verification protocol before acting on AI outputs.")
        elif hr > 15:
            recs.append(f"🟡 {domain}: Hallucination rate {hr:.0f}% — Spot-check AI outputs against primary regulatory sources.")

    # Critical-risk hallucinations always need special mention
    if "risk_level" in df.columns:
        crit_hall = df[(df["risk_level"] == "critical") & df["is_hallucinated"]]
        if not crit_hall.empty:
            recs.append(f"🔴 {len(crit_hall)} CRITICAL-risk hallucination(s) detected — immediate review of impacted business processes required.")

    recs.append("📅 Schedule quarterly CAIGS re-assessment as LLM versions and Indian regulations change frequently.")
    recs.append("📚 Implement AI Literacy Programme for all staff using LLMs for business decisions.")
    recs.append("📋 Adopt the AI Output Verification Checklist (AOVC) for Finance, Legal, and HR decisions.")

    return recs


def _empty_caigs() -> Dict:
    return {
        "caigs_score": 0,
        "grade": "N/A",
        "grade_meta": {"label": "No Data", "color": "#888", "action": "Run audit first"},
        "overall_hallucination_rate": 0,
        "total_tests": 0,
        "total_hallucinated": 0,
        "overall_avg_accuracy": 0,
        "domain_stats": {},
        "llm_stats": {},
        "estimated_financial_risk_lakhs": 0,
        "recommendations": ["Run an audit to generate CAIGS recommendations."],
    }
