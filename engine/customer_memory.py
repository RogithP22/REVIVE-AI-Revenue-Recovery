import pandas as pd
import numpy as np

class CustomerMemoryEngine:
    @staticmethod
    def extract_profile(customer_id: str, custs_df: pd.DataFrame, history_df: pd.DataFrame) -> dict:
        c_match = custs_df[custs_df["customer_id"] == customer_id]
        if c_match.empty:
            return {
                "customer_id": customer_id,
                "risk_tier": "Medium",
                "segment": "Consumer",
                "lifetime_value": 0.0,
                "historical_success_rate": 0.50,
                "total_past_attempts": 0,
                "successful_recoveries": 0,
                "failed_recoveries": 0,
                "fatigue_score": 0.10,
                "best_historical_action": "None"
            }
            
        c_row = c_match.iloc[0]
        c_hist = history_df[history_df["customer_id"] == customer_id] if not history_df.empty else pd.DataFrame()
        
        attempts = len(c_hist)
        succ = len(c_hist[c_hist["success"] == 1]) if attempts > 0 else int(c_row.get("successful_transactions", 0))
        tot = attempts if attempts > 0 else int(c_row.get("total_transactions", 1))
        succ_rate = float(succ / tot) if tot > 0 else 0.50
        
        best_act = "None"
        if not c_hist.empty and succ > 0:
            succ_acts = c_hist[c_hist["success"] == 1]["action"].value_counts()
            if not succ_acts.empty:
                best_act = succ_acts.index[0]
                
        fatigue = float(np.clip(attempts * 0.15, 0.0, 0.95))
        
        return {
            "customer_id": customer_id,
            "risk_tier": str(c_row.get("risk_tier", "Medium")),
            "segment": str(c_row.get("customer_segment", "Consumer")),
            "lifetime_value": float(c_row.get("lifetime_value", 5000.0)),
            "historical_success_rate": succ_rate,
            "total_past_attempts": attempts,
            "successful_recoveries": succ,
            "failed_recoveries": attempts - succ,
            "fatigue_score": fatigue,
            "best_historical_action": best_act
        }