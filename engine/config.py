from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
AUDIT_FILE = BASE_DIR / "data" / "audit_log.json"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

ACTION_REGISTRY = {
    "RETRY_NOW": {
        "display_name": "Instant Retry",
        "description": "Immediate background gateway retry for transient drops.",
        "cost": 0.50,
        "cooldown_minutes": 0,
        "max_attempts": 2,
        "eligible_rails": ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"],
        "category": "AUTOMATED_GATEWAY"
    },
    "RETRY_LATER": {
        "display_name": "Scheduled Smart Retry",
        "description": "Queued retry scheduled after 4-12 hours for account balance replenishment.",
        "cost": 1.00,
        "cooldown_minutes": 240,
        "max_attempts": 3,
        "eligible_rails": ["UPI", "Credit Card", "Debit Card", "Net Banking"],
        "category": "AUTOMATED_GATEWAY"
    },
    "PAYMENT_LINK": {
        "display_name": "Smart Payment Link",
        "description": "Direct dynamic checkout link dispatched over SMS or WhatsApp.",
        "cost": 2.50,
        "cooldown_minutes": 60,
        "max_attempts": 3,
        "eligible_rails": ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"],
        "category": "CUSTOMER_ENGAGEMENT"
    },
    "ALTERNATE_PAYMENT": {
        "display_name": "Alternate Rail Prompt",
        "description": "Prompts customer to switch from failing card/bank rail to UPI or alternate bank.",
        "cost": 5.00,
        "cooldown_minutes": 30,
        "max_attempts": 2,
        "eligible_rails": ["Credit Card", "Debit Card", "Net Banking"],
        "category": "CHECKOUT_INTERVENTION"
    },
    "REMINDER": {
        "display_name": "Push Reminder",
        "description": "Push notification reminding user of pending checkout.",
        "cost": 0.50,
        "cooldown_minutes": 180,
        "max_attempts": 3,
        "eligible_rails": ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"],
        "category": "CUSTOMER_ENGAGEMENT"
    },
    "INCENTIVE": {
        "display_name": "Fee Waiver Incentive",
        "description": "Instant fee waiver or small discount to convert high-value dropped payment.",
        "cost": 25.00,
        "cooldown_minutes": 720,
        "max_attempts": 1,
        "eligible_rails": ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"],
        "category": "FINANCIAL_INCENTIVE"
    },
    "HUMAN_ESCALATION": {
        "display_name": "Operations Escalation",
        "description": "Direct phone recovery outreach by merchant operations desk.",
        "cost": 65.00,
        "cooldown_minutes": 1440,
        "max_attempts": 1,
        "eligible_rails": ["UPI", "Credit Card", "Debit Card", "Net Banking"],
        "category": "MANUAL_OPS"
    }
}

FAILURE_AFFINITIES = {
    "BANK_SERVER_DOWN": {"RETRY_NOW": 0.82, "RETRY_LATER": 0.78, "PAYMENT_LINK": 0.40, "ALTERNATE_PAYMENT": 0.65, "REMINDER": 0.30, "INCENTIVE": 0.20, "HUMAN_ESCALATION": 0.15},
    "INSUFFICIENT_FUNDS": {"RETRY_NOW": 0.08, "RETRY_LATER": 0.72, "PAYMENT_LINK": 0.55, "ALTERNATE_PAYMENT": 0.68, "REMINDER": 0.45, "INCENTIVE": 0.75, "HUMAN_ESCALATION": 0.50},
    "AUTH_TIMEOUT": {"RETRY_NOW": 0.65, "RETRY_LATER": 0.50, "PAYMENT_LINK": 0.70, "ALTERNATE_PAYMENT": 0.62, "REMINDER": 0.58, "INCENTIVE": 0.35, "HUMAN_ESCALATION": 0.20},
    "EXPIRED_CARD": {"RETRY_NOW": 0.01, "RETRY_LATER": 0.05, "PAYMENT_LINK": 0.82, "ALTERNATE_PAYMENT": 0.85, "REMINDER": 0.40, "INCENTIVE": 0.40, "HUMAN_ESCALATION": 0.60},
    "NETWORK_ERROR": {"RETRY_NOW": 0.80, "RETRY_LATER": 0.68, "PAYMENT_LINK": 0.50, "ALTERNATE_PAYMENT": 0.55, "REMINDER": 0.45, "INCENTIVE": 0.30, "HUMAN_ESCALATION": 0.10}
}