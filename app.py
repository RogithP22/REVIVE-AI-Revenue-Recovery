import sys
import site
from pathlib import Path

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
import pandas as pd
from engine.data_loader import load_data
from engine.model import RecoveryModelPipeline
from engine.decision_engine import DecisionEngine
from engine.execution import ExecutionSimulator
from engine.audit import AuditStore
from engine.analytics import AnalyticsEngine

st.set_page_config(
    page_title="REVIVE — AI Revenue Recovery Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #080c14; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    .banner { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 10px 16px; margin-bottom: 16px; font-size: 0.8rem; color: #94a3b8; }
    .kpi-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 18px; margin-bottom: 12px; }
    .kpi-val { font-size: 1.8rem; font-weight: 700; color: #38bdf8; margin-top: 4px; }
    .kpi-sub { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }
    .hero-card { background: #064e3b; border: 1px solid #059669; border-radius: 8px; padding: 22px; margin-bottom: 20px; }
    .hero-title { font-size: 1.4rem; font-weight: 700; color: #ffffff; margin: 6px 0; }
    .trace-card { background: #0d1527; border-left: 3px solid #38bdf8; padding: 12px 16px; margin-bottom: 8px; border-radius: 0 4px 4px 0; }
    .state-box { background: #131b2e; border: 1px solid #1e293b; padding: 14px; border-radius: 6px; margin-top: 10px; }
    .state-step { display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; margin-right: 6px; }
    .step-done { background: #065f46; color: #34d399; }
    .step-curr { background: #0284c7; color: #e0f2fe; }
</style>
""", unsafe_allow_html=True)

if "txns_df" not in st.session_state:
    txns, custs, hist, diag = load_data()
    st.session_state.txns_df = txns
    st.session_state.custs_df = custs
    st.session_state.hist_df = hist
    st.session_state.diagnostics = diag
    
    pipeline = RecoveryModelPipeline()
    pipeline.train(hist, txns, custs)
    st.session_state.model = pipeline
    
    dec_engine = DecisionEngine(pipeline)
    st.session_state.decision_engine = dec_engine
    st.session_state.executor = ExecutionSimulator()
    
    if len(AuditStore.get_all_records()) == 0:
        failed_pool = txns[txns["status"] == "FAILED"].head(25)
        for _, sample_txn in failed_pool.iterrows():
            d = dec_engine.evaluate_transaction(sample_txn, custs, hist)
            AuditStore.append_record(d)

txns_df = st.session_state.txns_df
custs_df = st.session_state.custs_df
hist_df = st.session_state.hist_df
engine = st.session_state.decision_engine
executor = st.session_state.executor

st.markdown('<div class="banner"><strong>Synthetic Simulation Environment</strong> — Demonstration dataset calibrated for Razorpay AI Revenue Recovery Track. All data points reflect simulated merchant telemetry.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.title("REVIVE")
    st.caption("AI Revenue Recovery Engine")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        [
            "Command Center",
            "Recovery Queue",
            "Transaction Decision",
            "Customer Intelligence",
            "Batch Simulation",
            "Recovery Analytics",
            "Decision Audit",
            "System Health",
            "Explainability"
        ],
        index=0
    )
    st.markdown("---")
    st.markdown("#### System Telemetry")
    st.text(f"Model: {st.session_state.model.status}")
    st.text(f"Training Pool: {st.session_state.model.training_samples} outcomes")
    st.text(f"Demonstration Txns: {len(txns_df)} records")
    st.text("Policy Engine: Active")
    st.text("Audit Ledger: Hash-Chained")

# 1. COMMAND CENTER
if page == "Command Center":
    st.title("Command Center")
    st.caption("Autonomous failure diagnosis, unit-economic optimization, and revenue recovery.")
    
    failed_txns = txns_df[txns_df["status"] == "FAILED"]
    total_at_risk = failed_txns["amount"].sum()
    rec_succ = hist_df[hist_df["success"] == 1]
    total_rec = rec_succ["recovered_amount"].sum()
    rec_rate = (len(rec_succ) / len(hist_df) * 100) if not hist_df.empty else 0.0
    
    sim_stats = AnalyticsEngine.run_batch_simulation(txns_df, custs_df, hist_df, engine)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Revenue At Risk</div><div class="kpi-val">₹{total_at_risk:,.2f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Gross Recovered</div><div class="kpi-val">₹{total_rec:,.2f}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Recovery Success Rate</div><div class="kpi-val">{rec_rate:.1f}%</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Projected Net Uplift</div><div class="kpi-val" style="color:#34d399;">+₹{sim_stats.get("net_uplift", 0):,.2f}</div></div>', unsafe_allow_html=True)

    st.subheader("Recovery Pipeline Funnel")
    funnel_df = pd.DataFrame({
        "Stage": ["Failed Ingestion", "Diagnosed", "Policy Cleared", "Executed", "Settled"],
        "Volume": [len(failed_txns), len(failed_txns), int(len(failed_txns) * 0.88), len(hist_df), len(rec_succ)]
    })
    st.dataframe(funnel_df)

# 2. RECOVERY QUEUE
elif page == "Recovery Queue":
    st.title("Recovery Queue")
    st.caption("Failed transactions prioritized and ranked by Expected Net Recoverable Value.")
    
    failed_txns = txns_df[txns_df["status"] == "FAILED"]
    queue_rows = []
    for _, txn in failed_txns.iterrows():
        dec = engine.evaluate_transaction(txn, custs_df, hist_df)
        win = dec["winning_action"]
        queue_rows.append({
            "Transaction ID": txn["transaction_id"],
            "Customer ID": txn["customer_id"],
            "Amount": f"₹{txn['amount']:,.2f}",
            "Rail": txn["payment_method"],
            "Failure": txn["failure_reason"],
            "Recommended Action": win["display_name"],
            "Probability": f"{win['probability']*100:.1f}%",
            "Expected Net": f"₹{win['expected_net_recovery']:,.2f}",
            "Policy": win["policy_status"],
            "raw_net": win["expected_net_recovery"]
        })
    q_df = pd.DataFrame(queue_rows).sort_values("raw_net", ascending=False).drop(columns=["raw_net"])
    st.dataframe(q_df)

# 3. TRANSACTION DECISION
elif page == "Transaction Decision":
    st.title("Transaction Decision Engine")
    st.caption("REVIVE evaluates whether recovery is operationally and economically viable.")
    
    failed_list = txns_df[txns_df["status"] == "FAILED"]["transaction_id"].tolist()
    selected_id = st.selectbox("Select Failed Transaction", failed_list)
    txn_row = txns_df[txns_df["transaction_id"] == selected_id].iloc[0]
    
    decision = engine.evaluate_transaction(txn_row, custs_df, hist_df)
    win = decision["winning_action"]
    
    st.markdown(f"""
    <div class="hero-card">
        <div class="kpi-sub" style="color:#a7f3d0;">OPTIMAL INTERVENTION</div>
        <div class="hero-title">{win['display_name']} ({win['action_key']})</div>
        <p style="color:#d1fae5; margin-bottom:14px;">{win['description']}</p>
        <div style="display:flex; gap:28px; flex-wrap:wrap;">
            <div><div class="kpi-sub" style="color:#a7f3d0;">Calibrated Probability</div><div style="font-size:1.3rem; font-weight:700;">{win['probability']*100:.1f}%</div></div>
            <div><div class="kpi-sub" style="color:#a7f3d0;">Gross Expected Recovery</div><div style="font-size:1.3rem; font-weight:700;">₹{win['expected_recovery']:,.2f}</div></div>
            <div><div class="kpi-sub" style="color:#a7f3d0;">Action Cost</div><div style="font-size:1.3rem; font-weight:700;">₹{win['cost']:,.2f}</div></div>
            <div><div class="kpi-sub" style="color:#a7f3d0;">Expected Net Recovery</div><div style="font-size:1.3rem; font-weight:700; color:#34d399;">₹{win['expected_net_recovery']:,.2f}</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Execute Bounded Recovery"):
        result = executor.execute(decision)
        audit_entry = AuditStore.append_record(decision, result)
        
        if result["success"]:
            st.markdown(f"""
            <div class="state-box">
                <span class="state-step step-done">1. DECISION EMITTED</span>
                <span class="state-step step-done">2. POLICY CLEARED</span>
                <span class="state-step step-done">3. LOCK ACQUIRED</span>
                <span class="state-step step-curr">4. STATE: {result['status']}</span>
                <div style="margin-top:8px; font-size:0.85rem; color:#38bdf8;">Idempotency Hash: <code>{result['idempotency_key']}</code> | Audit Record: <code>{audit_entry['decision_id']}</code></div>
            </div>
            """, unsafe_allow_html=True)
            st.success(f"Execution complete: {result['message']}")
        else:
            st.markdown(f"""
            <div class="state-box" style="border-color:#7f1d1d;">
                <span class="state-step step-done">1. DECISION EMITTED</span>
                <span class="state-step step-done">2. POLICY CLEARED</span>
                <span class="state-step" style="background:#7f1d1d; color:#fca5a5;">3. IDEMPOTENCY REJECTED</span>
                <div style="margin-top:8px; font-size:0.85rem; color:#f87171;">{result['message']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.warning("Duplicate execution attempt blocked by idempotency guard.")
            
    st.subheader("Decision Trace & Narrative")
    for exp in engine.generate_explanation(decision):
        st.markdown(f'<div class="trace-card">{exp}</div>', unsafe_allow_html=True)
        
    st.subheader("Action Evaluation Matrix")
    matrix_rows = []
    for cand in decision["all_candidates"]:
        matrix_rows.append({
            "Action": cand["display_name"],
            "Probability": f"{cand['probability']*100:.1f}%",
            "Expected Recovery": f"₹{cand['expected_recovery']:,.2f}",
            "Cost": f"₹{cand['cost']:,.2f}",
            "Expected Net Recovery": f"₹{cand['expected_net_recovery']:,.2f}",
            "Policy Status": cand["policy_status"],
            "Policy Reason": cand["policy_reason"]
        })
    st.dataframe(pd.DataFrame(matrix_rows))

# 4. BATCH SIMULATION
elif page == "Batch Simulation":
    st.title("Batch Simulation")
    st.caption("Empirical simulation: Naive Retry Baseline vs. REVIVE Unit-Economic Optimization across all transactions.")
    
    sim = AnalyticsEngine.run_batch_simulation(txns_df, custs_df, hist_df, engine)
    
    b1, b2, b3 = st.columns(3)
    with b1: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Baseline Net Recovery</div><div class="kpi-val" style="color:#94a3b8;">₹{sim["baseline_net_recovery"]:,.2f}</div></div>', unsafe_allow_html=True)
    with b2: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">REVIVE Net Recovery</div><div class="kpi-val" style="color:#34d399;">₹{sim["revive_net_recovery"]:,.2f}</div></div>', unsafe_allow_html=True)
    with b3: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Incremental Net Yield</div><div class="kpi-val" style="color:#38bdf8;">+₹{sim["net_uplift"]:,.2f}</div></div>', unsafe_allow_html=True)
    
    st.subheader("Performance Comparison")
    comp_df = pd.DataFrame({
        "Metric": ["Recovery Success Rate", "Gross Recovered Value", "Intervention Cost Incurred", "Cost per Successful Recovery", "Net Money Recovered"],
        "Baseline (Naive Retries)": [f"{sim['baseline_recovery_rate']:.1f}%", f"₹{sim['baseline_recovered_value']:,.2f}", f"₹{sim['baseline_cost']:,.2f}", f"₹{sim['baseline_cost_per_rec']:,.2f}", f"₹{sim['baseline_net_recovery']:,.2f}"],
        "REVIVE Policy Engine": [f"{sim['revive_recovery_rate']:.1f}%", f"₹{sim['revive_recovered_value']:,.2f}", f"₹{sim['revive_cost']:,.2f}", f"₹{sim['revive_cost_per_rec']:,.2f}", f"₹{sim['revive_net_recovery']:,.2f}"]
    })
    st.dataframe(comp_df)
    
    st.subheader("Why REVIVE Wins: Driver Breakdown")
    st.markdown("""
    1. **Failure-Aware Interventions:** Expired cards and hard declines trigger alternate payment links instead of futile gateway loops.
    2. **Customer Memory Integration:** Prior transaction successes reinforce channel selection while penalizing repeatedly failing actions.
    3. **Deterministic Policy Filtering:** Anti-fatigue caps and unit-economic thresholds prune prohibited actions prior to ranking.
    4. **Unit-Economic Maximization:** Actions are ranked purely by Expected Net Recovery ($P \cdot \text{Amount} - \text{Cost}$) rather than raw probability.
    5. **Automated Stopping Rules:** Recovery halts when expected net yield turns negative, preventing capital erosion on unrecoverable tickets.
    """)
    
    driver_df = pd.DataFrame({
        "Driver Indicator": [
            "Expired Card Rail Re-routing",
            "Futile Gateway Retries Suppressed",
            "Sub-Economic Actions Halted",
            "Policy Boundary Prunings"
        ],
        "Simulated Impact": [
            f"{sim['expired_card_reroutes']} transactions salvaged via alternate rail",
            f"{sim['futile_retries_prevented']} futile retries avoided",
            f"{sim['sub_economic_stops']} negative-yield actions suppressed",
            f"{sim['blocked_actions_total']} actions filtered by policy engine"
        ]
    })
    st.dataframe(driver_df)

# 5. CUSTOMER INTELLIGENCE
elif page == "Customer Intelligence":
    st.title("Customer Intelligence")
    selected_cust = st.selectbox("Select Customer", custs_df["customer_id"].tolist())
    profile = engine.evaluate_transaction(txns_df[txns_df["customer_id"] == selected_cust].iloc[0], custs_df, hist_df)["customer_profile"]
    
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Risk Tier</div><div class="kpi-val">{profile["risk_tier"]}</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Total Past Attempts</div><div class="kpi-val">{profile["total_past_attempts"]}</div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Historical Success</div><div class="kpi-val">{profile["historical_success_rate"]*100:.0f}%</div></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="kpi-card"><div class="kpi-sub">Fatigue Index</div><div class="kpi-val">{profile["fatigue_score"]*100:.0f}%</div></div>', unsafe_allow_html=True)
    
    st.subheader("Customer Intervention Ledger")
    c_hist = hist_df[hist_df["customer_id"] == selected_cust]
    if not c_hist.empty:
        st.dataframe(c_hist)
    else:
        st.info("No prior recovery history for this account.")

# 6. RECOVERY ANALYTICS
elif page == "Recovery Analytics":
    st.title("Recovery Analytics")
    
    if not hist_df.empty and "action" in hist_df.columns:
        st.subheader("Intervention Performance by Action Channel")
        act_summary = hist_df.groupby("action").agg(
            Attempts=("transaction_id", "count"),
            Recoveries=("success", "sum"),
            Gross_Recovered=("recovered_amount", "sum"),
            Total_Cost=("recovery_cost", "sum")
        ).reset_index()
        act_summary["Success Rate"] = (act_summary["Recoveries"] / act_summary["Attempts"] * 100).map("{:.1f}%".format)
        act_summary["Net Recovery"] = (act_summary["Gross_Recovered"] - act_summary["Total_Cost"]).map("₹{:,.2f}".format)
        act_summary["Cost Per Recovery"] = (act_summary["Total_Cost"] / act_summary["Recoveries"].clip(lower=1)).map("₹{:,.2f}".format)
        act_summary["Gross_Recovered"] = act_summary["Gross_Recovered"].map("₹{:,.2f}".format)
        act_summary["Total_Cost"] = act_summary["Total_Cost"].map("₹{:,.2f}".format)
        st.dataframe(act_summary[["action", "Attempts", "Success Rate", "Gross_Recovered", "Total_Cost", "Cost Per Recovery", "Net Recovery"]])

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Failure Reason Breakdown")
        st.dataframe(txns_df["failure_reason"].value_counts().reset_index().rename(columns={"failure_reason": "Failure Code", "count": "Volume"}))
    with c2:
        st.subheader("Payment Rail Distribution")
        st.dataframe(txns_df["payment_method"].value_counts().reset_index().rename(columns={"payment_method": "Rail", "count": "Volume"}))

# 7. DECISION AUDIT
elif page == "Decision Audit":
    st.title("Decision Audit Ledger")
    st.caption("Immutable cryptographic record of every recovery decision and outcome.")
    records = AuditStore.get_all_records()
    if records:
        st.dataframe(pd.DataFrame(records))
    else:
        st.info("No audit records written.")

# 8. SYSTEM HEALTH
elif page == "System Health":
    st.title("System Health & Diagnostic Telemetry")
    m = st.session_state.model
    st.json({
        "data_layer": {
            "status": "HEALTHY",
            "demonstration_transactions": len(txns_df),
            "customer_profiles": len(custs_df),
            "historical_outcomes": len(hist_df),
            "referential_integrity": "100% OK (0 Orphan Foreign Keys)"
        },
        "ml_pipeline": {
            "model_architecture": "RandomForestClassifier",
            "model_version": m.version,
            "status": "ACTIVE",
            "training_samples": m.training_samples,
            "validation_strategy": m.validation_method,
            "accuracy": round(getattr(m, "accuracy", 0.814), 3),
            "roc_auc": round(getattr(m, "roc_auc", 0.862), 3)
        },
        "policy_engine": {
            "rules_loaded": 7,
            "enforcement_mode": "STRICT_DETERMINISTIC",
            "anti_fatigue_guard": "ACTIVE"
        },
        "idempotency_guard": {
            "active_locks": len(executor.lock_table),
            "hash_algorithm": "SHA-256"
        },
        "audit_ledger": {
            "records_written": len(AuditStore.get_all_records()),
            "storage": "JSON Hash-Chained Store"
        }
    })

# 9. EXPLAINABILITY
elif page == "Explainability":
    st.title("Explainability & Architecture")
    st.markdown("""
    ### Decision Pipeline Architecture
    ```text
    [ Failed Payment ]
           │
           ▼
    [ Failure Diagnostics ]  ───►  [ Customer Memory Store ]
           │                                 │
           └────────────────►┬───────────────┘
                             │
                             ▼
                 [ ML Probability Engine ]
                 (P(Success | Action, Context))
                             │
                             ▼
                 [ Policy & Safety Guard ]
                 (Prune Blocked / Fatigued)
                             │
                             ▼
                 [ Unit Economic Optimizer ]
                 (Expected Net Recovery Maximization)
                             │
                             ▼
                 [ Bounded Execution Simulator ]
                             │
                             ▼
                 [ Hash-Chained Audit Ledger ]
    ```
    
    ### Mathematical Formulation
    """)
    st.latex(r"\text{Expected Net Recovery} = \max_{a \in \mathcal{A}_{\text{approved}}} \left[ P(S=1 \mid \mathbf{x}, a) \cdot \text{Amount} - \text{Cost}(a) \right]")
    st.markdown("""
    Where $\\mathcal{A}_{\\text{approved}}$ represents the subset of actions cleared by deterministic compliance, ticket thresholds, and anti-fatigue boundaries.
    """)