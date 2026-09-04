import pandas as pd
import numpy as np
from engine.config import ACTION_REGISTRY, FAILURE_AFFINITIES
from engine.features import build_feature_vector
from engine.model import RecoveryModelPipeline
from engine.policy_engine import PolicyGuard
from engine.customer_memory import CustomerMemoryEngine

class DecisionEngine:
    def __init__(self, model_pipeline: RecoveryModelPipeline):
        self.model = model_pipeline

    def evaluate_transaction(self, txn_row: pd.Series, custs_df: pd.DataFrame, history_df: pd.DataFrame) -> dict:
        cid = txn_row.get("customer_id", "UNKNOWN")
        amount = float(txn_row.get("amount", 0.0))
        reason = str(txn_row.get("failure_reason", "NETWORK_ERROR"))
        method = str(txn_row.get("payment_method", "UPI"))
        attempt_num = int(txn_row.get("attempt_number", 1))
        
        cust_profile = CustomerMemoryEngine.extract_profile(cid, custs_df, history_df)
        
        candidates = []
        for action_key, meta in ACTION_REGISTRY.items():
            feat_vec = build_feature_vector(
                amount=amount,
                attempt_number=attempt_num,
                action=action_key,
                failure_reason=reason,
                payment_method=method,
                customer_risk=cust_profile["risk_tier"],
                customer_ltv=cust_profile["lifetime_value"],
                customer_hist_rate=cust_profile["historical_success_rate"]
            )
            rf_prob = self.model.predict_probability(feat_vec)
            
            aff_prior = FAILURE_AFFINITIES.get(reason, {}).get(action_key, 0.50)
            hist_boost = 0.05 if cust_profile["best_historical_action"] == action_key else 0.0
            
            combined_prob = float(np.clip((0.60 * rf_prob) + (0.25 * aff_prior) + (0.15 * cust_profile["historical_success_rate"]) + hist_boost, 0.02, 0.98))
            
            expected_recovery = float(combined_prob * amount)
            cost = float(meta["cost"])
            expected_net = float(expected_recovery - cost)
            
            policy_status, policy_reason = PolicyGuard.evaluate(
                action=action_key,
                amount=amount,
                payment_method=method,
                failure_reason=reason,
                customer_risk=cust_profile["risk_tier"],
                attempt_number=attempt_num,
                customer_fatigue_score=cust_profile["fatigue_score"]
            )
            
            candidates.append({
                "action_key": action_key,
                "display_name": meta["display_name"],
                "description": meta["description"],
                "probability": combined_prob,
                "expected_recovery": expected_recovery,
                "cost": cost,
                "expected_net_recovery": expected_net,
                "policy_status": policy_status,
                "policy_reason": policy_reason,
                "is_approved": (policy_status == "APPROVED")
            })
            
        ranked = sorted(candidates, key=lambda x: (x["is_approved"], x["expected_net_recovery"]), reverse=True)
        
        approved_actions = [a for a in ranked if a["is_approved"]]
        if not approved_actions or approved_actions[0]["expected_net_recovery"] <= 0:
            winning_action = {
                "action_key": "STOP_RECOVERY",
                "display_name": "Cease Recovery",
                "description": "Actions violate risk policy or produce negative expected net economic yield.",
                "probability": 0.0,
                "expected_recovery": 0.0,
                "cost": 0.0,
                "expected_net_recovery": 0.0,
                "policy_status": "APPROVED",
                "policy_reason": "Negative net yield.",
                "is_approved": True
            }
        else:
            winning_action = approved_actions[0]
            
        return {
            "transaction_id": txn_row.get("transaction_id"),
            "customer_id": cid,
            "amount": amount,
            "payment_method": method,
            "failure_reason": reason,
            "attempt_number": attempt_num,
            "customer_profile": cust_profile,
            "winning_action": winning_action,
            "all_candidates": ranked
        }

    def generate_explanation(self, decision_dict: dict) -> list[str]:
        win = decision_dict["winning_action"]
        cust = decision_dict["customer_profile"]
        
        if win["action_key"] == "STOP_RECOVERY":
            return [
                "Stopping Rule Activated: Actions produce negative net recovery or breach policy.",
                "Suppressed execution to prevent unrecoverable overhead."
            ]
            
        return [
            f"Optimizes Net Value: {win['display_name']} delivers the highest net yield ({win['expected_net_recovery']:.2f}) from expected recovery of {win['expected_recovery']:.2f} less {win['cost']:.2f} cost.",
            f"Failure Alignment: Matched with {decision_dict['failure_reason']} on {decision_dict['payment_method']} with {win['probability']*100:.1f}% estimated success rate.",
            f"Risk Adjusted: Profiled for {cust['risk_tier']} tier customer.",
            f"Compliance Verified: Passed all operational and anti-fatigue limits."
        ]