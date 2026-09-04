from engine.config import ACTION_REGISTRY

class PolicyGuard:
    @staticmethod
    def evaluate(
        action: str,
        amount: float,
        payment_method: str,
        failure_reason: str,
        customer_risk: str,
        attempt_number: int,
        customer_fatigue_score: float
    ) -> tuple[str, str]:
        reg = ACTION_REGISTRY.get(action, {})
        clean_reason = str(failure_reason).upper()
        clean_risk = str(customer_risk).lower()
        
        if payment_method not in reg.get("eligible_rails", []):
            return "BLOCKED", f"Action not supported on {payment_method} rails."
            
        if action in ["RETRY_NOW", "RETRY_LATER"] and clean_reason == "EXPIRED_CARD":
            return "BLOCKED", "Gateway retries unavailable on expired cards."
            
        if action == "HUMAN_ESCALATION" and amount < 2500:
            return "BLOCKED", f"Ops escalation cost exceeds limits for tickets below 2500."
            
        if action == "INCENTIVE" and clean_risk == "high":
            return "BLOCKED", "Incentives prohibited for high-risk customer profiles."
            
        if action == "INCENTIVE" and amount < 500:
            return "BLOCKED", "Transaction amount below incentive threshold."
            
        if attempt_number > reg.get("max_attempts", 3):
            return "BLOCKED", "Maximum attempts reached for this action."
            
        if customer_fatigue_score > 0.85 and action in ["REMINDER", "PAYMENT_LINK"]:
            return "BLOCKED", "Customer notification fatigue limit reached."

        return "APPROVED", "Policy checks passed."