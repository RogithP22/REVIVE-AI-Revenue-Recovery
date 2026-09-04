import pandas as pd

FEATURE_NAMES = [
    "amount", "attempt_number", "customer_ltv", "customer_hist_rate",
    "action_RETRY_NOW", "action_RETRY_LATER", "action_PAYMENT_LINK",
    "action_ALTERNATE_PAYMENT", "action_REMINDER", "action_INCENTIVE", "action_HUMAN_ESCALATION",
    "reason_BANK_SERVER_DOWN", "reason_INSUFFICIENT_FUNDS", "reason_AUTH_TIMEOUT", "reason_EXPIRED_CARD", "reason_NETWORK_ERROR",
    "rail_UPI", "rail_Credit_Card", "rail_Debit_Card", "rail_Net_Banking", "rail_Wallet",
    "risk_Low", "risk_Medium", "risk_High"
]

def build_feature_vector(
    amount: float,
    attempt_number: int,
    action: str,
    failure_reason: str,
    payment_method: str,
    customer_risk: str,
    customer_ltv: float,
    customer_hist_rate: float
) -> pd.DataFrame:
    row = {col: 0.0 for col in FEATURE_NAMES}
    row["amount"] = float(amount)
    row["attempt_number"] = float(attempt_number)
    row["customer_ltv"] = float(customer_ltv)
    row["customer_hist_rate"] = float(customer_hist_rate)
    
    if f"action_{action}" in row: row[f"action_{action}"] = 1.0
    
    clean_reason = str(failure_reason).upper()
    if f"reason_{clean_reason}" in row: row[f"reason_{clean_reason}"] = 1.0
    
    clean_rail = str(payment_method).replace(" ", "_")
    if f"rail_{clean_rail}" in row: row[f"rail_{clean_rail}"] = 1.0
    
    clean_risk = str(customer_risk).capitalize()
    if f"risk_{clean_risk}" in row: row[f"risk_{clean_risk}"] = 1.0
    
    return pd.DataFrame([row])