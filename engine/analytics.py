import pandas as pd
import numpy as np
from engine.decision_engine import DecisionEngine
from engine.config import ACTION_REGISTRY

class AnalyticsEngine:
    @staticmethod
    def run_batch_simulation(txns_df: pd.DataFrame, custs_df: pd.DataFrame, hist_df: pd.DataFrame, engine: DecisionEngine) -> dict:
        failed_txns = txns_df[txns_df["status"] == "FAILED"].copy()
        if failed_txns.empty:
            return {}
            
        total_at_risk = failed_txns["amount"].sum()
        
        baseline_cost_per_retry = ACTION_REGISTRY["RETRY_NOW"]["cost"]
        baseline_total_cost = len(failed_txns) * baseline_cost_per_retry
        
        baseline_success_count = 0
        baseline_recovered_val = 0.0
        futile_retries_prevented = 0
        expired_card_reroutes = 0
        sub_economic_stops = 0
        
        for _, txn in failed_txns.iterrows():
            r = txn["failure_reason"]
            p = 0.40 if r in ["BANK_SERVER_DOWN", "NETWORK_ERROR"] else (0.00 if r == "EXPIRED_CARD" else 0.15)
            if np.random.rand() < p:
                baseline_success_count += 1
                baseline_recovered_val += txn["amount"]
                
        baseline_net = baseline_recovered_val - baseline_total_cost
        
        revive_expected_val = 0.0
        revive_simulated_recovered = 0.0
        revive_total_cost = 0.0
        revive_success_count = 0
        blocked_actions_count = 0
        
        for _, txn in failed_txns.iterrows():
            decision = engine.evaluate_transaction(txn, custs_df, hist_df)
            win = decision["winning_action"]
            
            revive_expected_val += win["expected_net_recovery"]
            revive_total_cost += win["cost"]
            
            if txn["failure_reason"] == "EXPIRED_CARD" and win["action_key"] in ["ALTERNATE_PAYMENT", "PAYMENT_LINK"]:
                expired_card_reroutes += 1
            if txn["failure_reason"] in ["EXPIRED_CARD", "INSUFFICIENT_FUNDS"]:
                futile_retries_prevented += 1
            if win["action_key"] == "STOP_RECOVERY":
                sub_economic_stops += 1
                
            blocked = len([c for c in decision["all_candidates"] if not c["is_approved"]])
            blocked_actions_count += blocked
            
            if win["action_key"] != "STOP_RECOVERY":
                if np.random.rand() < win["probability"]:
                    revive_success_count += 1
                    revive_simulated_recovered += txn["amount"]
                    
        revive_net = revive_simulated_recovered - revive_total_cost
        
        return {
            "total_failed_txns": len(failed_txns),
            "total_at_risk_value": total_at_risk,
            "baseline_recovered_value": baseline_recovered_val,
            "baseline_cost": baseline_total_cost,
            "baseline_net_recovery": baseline_net,
            "baseline_recovery_rate": (baseline_success_count / len(failed_txns) * 100),
            "baseline_cost_per_rec": baseline_total_cost / max(baseline_success_count, 1),
            "revive_recovered_value": revive_simulated_recovered,
            "revive_cost": revive_total_cost,
            "revive_net_recovery": revive_net,
            "revive_recovery_rate": (revive_success_count / len(failed_txns) * 100),
            "revive_cost_per_rec": revive_total_cost / max(revive_success_count, 1),
            "net_uplift": revive_net - baseline_net,
            "blocked_actions_total": blocked_actions_count,
            "futile_retries_prevented": futile_retries_prevented,
            "expired_card_reroutes": expired_card_reroutes,
            "sub_economic_stops": sub_economic_stops
        }