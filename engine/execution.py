import json
import hashlib
import numpy as np
import pandas as pd
from engine.config import AUDIT_FILE

class ExecutionSimulator:
    def __init__(self):
        self.lock_table: set = set()
        self._load_locks()

    def _load_locks(self):
        if AUDIT_FILE.exists():
            try:
                with open(AUDIT_FILE, "r") as f:
                    records = json.load(f)
                    for r in records:
                        self.lock_table.add(r.get("idempotency_key"))
            except Exception:
                pass

    def execute(self, decision_dict: dict) -> dict:
        txn_id = decision_dict["transaction_id"]
        action = decision_dict["winning_action"]["action_key"]
        attempt = decision_dict["attempt_number"]
        
        raw_key = f"{txn_id}:{action}:{attempt}"
        idempotency_key = hashlib.sha256(raw_key.encode()).hexdigest()[:16]
        
        if idempotency_key in self.lock_table:
            return {
                "success": False,
                "status": "REJECTED_DUPLICATE",
                "idempotency_key": idempotency_key,
                "message": f"Action {action} on {txn_id} attempt {attempt} has already been executed."
            }
            
        prob = decision_dict["winning_action"]["probability"]
        simulated_success = bool(np.random.rand() < prob) if action != "STOP_RECOVERY" else False
        
        self.lock_table.add(idempotency_key)
        
        return {
            "success": True,
            "status": "SUCCESS" if simulated_success else "FAILED",
            "idempotency_key": idempotency_key,
            "recovered_amount": decision_dict["amount"] if simulated_success else 0.0,
            "cost_incurred": decision_dict["winning_action"]["cost"],
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"Execution finished with status {simulated_success}"
        }