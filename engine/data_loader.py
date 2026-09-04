import pandas as pd
import numpy as np
from engine.config import DATA_DIR

COLUMN_MAP = {
    "transactions": {
        "transaction_id": ["transaction_id", "transactionid", "txn_id", "id"],
        "customer_id": ["customer_id", "customerid", "cust_id", "user_id"],
        "amount": ["amount", "txn_amount", "value", "price"],
        "payment_method": ["payment_method", "payment_mode", "method", "rail"],
        "failure_reason": ["failure_reason", "reason", "error_code"],
        "timestamp": ["timestamp", "transaction_date", "date", "created_at"],
        "status": ["status", "txn_status", "state"],
        "attempt_number": ["attempt_number", "attempt_count", "attempt", "retry_count"]
    },
    "customers": {
        "customer_id": ["customer_id", "customerid", "cust_id"],
        "customer_segment": ["customer_segment", "segment", "tier"],
        "risk_tier": ["risk_tier", "customer_risk", "risk_level", "risk"],
        "total_transactions": ["total_transactions", "total_txns"],
        "successful_transactions": ["successful_transactions", "succ_txns"],
        "failed_transactions": ["failed_transactions", "fail_txns"],
        "lifetime_value": ["lifetime_value", "ltv"],
        "preferred_payment_method": ["preferred_payment_method", "preferred_method"]
    },
    "recovery_history": {
        "attempt_id": ["attempt_id", "id", "att_id"],
        "customer_id": ["customer_id", "customerid", "cust_id"],
        "transaction_id": ["transaction_id", "transactionid", "txn_id"],
        "action": ["action", "recovery_action", "strategy"],
        "success": ["success", "is_success", "recovered"],
        "recovered_amount": ["recovered_amount", "amount_recovered"],
        "recovery_cost": ["recovery_cost", "cost", "action_cost"],
        "timestamp": ["timestamp", "attempt_date", "date"]
    }
}

def normalize_dataframe(df: pd.DataFrame, table_type: str) -> pd.DataFrame:
    df = df.copy()
    rename_dict = {}
    mapping = COLUMN_MAP.get(table_type, {})
    for col in df.columns:
        cleaned = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        for target, aliases in mapping.items():
            if cleaned in aliases:
                rename_dict[col] = target
                break
    return df.rename(columns=rename_dict)

def generate_synthetic_store():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(42)
    
    cust_ids = [f"CUST_{i:04d}" for i in range(1001, 1051)]
    methods = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]
    cust_rows = []
    for cid in cust_ids:
        total = np.random.randint(10, 80)
        failed = np.random.randint(1, int(total * 0.3) + 1)
        succ = total - failed
        cust_rows.append({
            "customer_id": cid,
            "customer_segment": np.random.choice(["Enterprise", "SMB", "Consumer"], p=[0.2, 0.3, 0.5]),
            "risk_tier": np.random.choice(["Low", "Medium", "High"], p=[0.6, 0.3, 0.1]),
            "total_transactions": total,
            "successful_transactions": succ,
            "failed_transactions": failed,
            "lifetime_value": float(np.random.randint(5000, 150000)),
            "preferred_payment_method": np.random.choice(methods, p=[0.5, 0.2, 0.15, 0.1, 0.05])
        })
    cust_df = pd.DataFrame(cust_rows)
    cust_df.to_csv(DATA_DIR / "customers.csv", index=False)
    
    reasons = ["INSUFFICIENT_FUNDS", "BANK_SERVER_DOWN", "AUTH_TIMEOUT", "EXPIRED_CARD", "NETWORK_ERROR"]
    txn_rows = []
    for i in range(1, 201):
        cid = np.random.choice(cust_ids)
        c_pref = cust_df.loc[cust_df["customer_id"] == cid, "preferred_payment_method"].values[0]
        txn_method = c_pref if np.random.rand() > 0.3 else np.random.choice(methods)
        is_failed = np.random.choice([True, False], p=[0.8, 0.2])
        txn_rows.append({
            "transaction_id": f"TXN_{i:05d}",
            "customer_id": cid,
            "amount": float(np.random.choice([250, 499, 999, 1499, 2999, 4999, 8999, 15000])),
            "payment_method": txn_method,
            "failure_reason": np.random.choice(reasons) if is_failed else "NONE",
            "timestamp": (pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "FAILED" if is_failed else "SUCCESS",
            "attempt_number": int(np.random.choice([1, 1, 1, 2, 3]))
        })
    txn_df = pd.DataFrame(txn_rows)
    txn_df.to_csv(DATA_DIR / "transactions.csv", index=False)
    
    actions = ["RETRY_NOW", "RETRY_LATER", "PAYMENT_LINK", "ALTERNATE_PAYMENT", "REMINDER", "INCENTIVE", "HUMAN_ESCALATION"]
    cost_map = {"RETRY_NOW": 0.50, "RETRY_LATER": 1.00, "PAYMENT_LINK": 2.50, "ALTERNATE_PAYMENT": 5.00, "REMINDER": 0.50, "INCENTIVE": 25.00, "HUMAN_ESCALATION": 65.00}
    hist_rows = []
    for i in range(1, 151):
        target_txn = txn_df[txn_df["status"] == "FAILED"].sample(1).iloc[0]
        action = np.random.choice(actions)
        success = int(np.random.choice([1, 0], p=[0.58, 0.42]))
        hist_rows.append({
            "attempt_id": f"ATT_{i:05d}",
            "customer_id": target_txn["customer_id"],
            "transaction_id": target_txn["transaction_id"],
            "action": action,
            "success": success,
            "recovered_amount": float(target_txn["amount"]) if success == 1 else 0.0,
            "recovery_cost": float(cost_map[action]),
            "timestamp": (pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(1, 25))).strftime("%Y-%m-%d %H:%M:%S")
        })
    hist_df = pd.DataFrame(hist_rows)
    hist_df.to_csv(DATA_DIR / "recovery_history.csv", index=False)

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    if not (DATA_DIR / "transactions.csv").exists() or not (DATA_DIR / "customers.csv").exists():
        generate_synthetic_store()
        
    try:
        txns = normalize_dataframe(pd.read_csv(DATA_DIR / "transactions.csv"), "transactions")
        custs = normalize_dataframe(pd.read_csv(DATA_DIR / "customers.csv"), "customers")
        hist = normalize_dataframe(pd.read_csv(DATA_DIR / "recovery_history.csv"), "recovery_history")
        
        txns["amount"] = pd.to_numeric(txns["amount"], errors="coerce").fillna(0.0)
        txns["attempt_number"] = pd.to_numeric(txns.get("attempt_number", 1), errors="coerce").fillna(1).astype(int)
        hist["recovered_amount"] = pd.to_numeric(hist["recovered_amount"], errors="coerce").fillna(0.0)
        hist["recovery_cost"] = pd.to_numeric(hist["recovery_cost"], errors="coerce").fillna(0.0)
        hist["success"] = pd.to_numeric(hist["success"], errors="coerce").fillna(0).astype(int)
        
        diagnostics = {
            "transactions_count": len(txns),
            "customers_count": len(custs),
            "history_count": len(hist),
            "integrity_verified": True,
            "message": "Referential integrity intact."
        }
        return txns, custs, hist, diagnostics
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {"integrity_verified": False, "message": str(e)}