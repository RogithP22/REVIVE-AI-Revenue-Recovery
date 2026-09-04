import json
import hashlib
import pandas as pd
from engine.config import AUDIT_FILE

class AuditStore:
    @staticmethod
    def append_record(decision_dict: dict, exec_result: dict | None = None) -> dict:
        records = AuditStore.get_all_records()
        prev_hash = records[-1]["hash"] if records else "0000000000000000"
        
        record = {
            "decision_id": f"DEC_{len(records)+1:05d}",
            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_id": decision_dict["transaction_id"],
            "customer_id": decision_dict["customer_id"],
            "amount": float(decision_dict["amount"]),
            "failure_reason": decision_dict["failure_reason"],
            "selected_action": decision_dict["winning_action"]["display_name"],
            "action_key": decision_dict["winning_action"]["action_key"],
            "ml_probability": float(round(decision_dict["winning_action"]["probability"], 3)),
            "action_cost": float(decision_dict["winning_action"]["cost"]),
            "expected_net_recovery": float(round(decision_dict["winning_action"]["expected_net_recovery"], 2)),
            "policy_status": decision_dict["winning_action"]["policy_status"],
            "execution_status": exec_result.get("status") if exec_result else "EVALUATED_READY",
            "idempotency_key": exec_result.get("idempotency_key") if exec_result else None,
            "prev_hash": prev_hash
        }
        
        record_str = json.dumps(record, sort_keys=True)
        record["hash"] = hashlib.sha256(record_str.encode()).hexdigest()[:16]
        
        records.append(record)
        with open(AUDIT_FILE, "w") as f:
            json.dump(records, f, indent=2)
        return record

    @staticmethod
    def get_all_records() -> list[dict]:
        if not AUDIT_FILE.exists():
            return []
        try:
            with open(AUDIT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []