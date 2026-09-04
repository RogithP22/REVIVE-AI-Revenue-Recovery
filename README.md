# REVIVE — AI Revenue Recovery

**REVIVE** is an AI-based revenue recovery engine for failed payments.

Instead of blindly retrying a failed payment, REVIVE looks at the transaction, failure reason, customer history, recovery probability, action cost, and policy rules before deciding what to do.

> **Goal: recover more money while avoiding unnecessary, unsafe, or uneconomic recovery attempts.**

---

## Live Demo

**Try REVIVE Live:**  
https://revive-ai-revenue-recovery.streamlit.app/

### What to Try

1. Open **Transaction Decision** and select a failed transaction.
2. Inspect the failure reason, customer context, recovery probability, recommended action, and expected net recovery.
3. Execute an approved recovery action.
4. Attempt the same action again and observe the idempotency protection.
5. Open **Batch Simulation** and compare the baseline with REVIVE.
6. Open **Decision Audit** and trace the decision and execution record.

---

## The Idea

A failed payment does not always mean lost revenue.

An expired card may be better handled through an alternate payment method. A temporary bank failure may justify a scheduled retry. Repeated failures may make another attempt uneconomic.

REVIVE answers three questions:

1. **What happened?**
2. **What is the best recovery action?**
3. **Is that action actually worth executing?**

The approved action is passed through a bounded execution simulator and recorded in a SHA-256 hash-chained audit ledger.

---

## How REVIVE Works

```text
Failed Payment
      ↓
Failure Diagnosis
      ↓
Customer + Transaction Context
      ↓
Recovery Probability Engine
      ↓
Candidate Recovery Actions
      ↓
Policy & Safety Checks
      ↓
Expected Net Recovery Optimization
      ↓
Bounded Execution
      ↓
Idempotency Check
      ↓
Hash-Chained Audit Ledger
The ML model does not directly control execution.

The decision passes through deterministic policy checks before an action can be executed.

AI / ML Architecture
REVIVE uses a Random Forest classifier to estimate recovery probability.

The model evaluates features such as:

Transaction amount

Attempt number

Customer lifetime value

Customer historical recovery rate

Failure reason

Payment rail

Customer risk level

Candidate recovery action

The ML pipeline is implemented in:


engine/model.py
Feature construction is handled by:


engine/features.py
Historical recovery outcomes are stored in:


data/recovery_history.csv
Demonstration Dataset
200 transactions

50 customer profiles

150 historical recovery outcomes

Decision Engine & Unit Economics
REVIVE does not choose an action based only on recovery probability.

For each candidate action:


Expected Recovery
= Transaction Amount × Recovery Probability
Then:


Expected Net Recovery
= Expected Recovery − Action Cost
This allows the engine to compare the potential recovery value against the cost of the intervention.

A recovery action can have a reasonable probability of success and still be a poor decision if the intervention cost is too high.

Candidate Recovery Actions
REVIVE can evaluate multiple recovery strategies:

Action	Key	Cost
Instant Retry	RETRY_NOW	₹0.50
Scheduled Smart Retry	RETRY_LATER	₹1.00
Smart Payment Link	PAYMENT_LINK	₹2.50
Alternate Rail Prompt	ALTERNATE_PAYMENT	₹5.00
Push Reminder	REMINDER	₹0.50
Fee Waiver Incentive	INCENTIVE	₹25.00
Operations Escalation	HUMAN_ESCALATION	₹65.00
Cease Recovery	STOP_RECOVERY	₹0.00

Safety & Deterministic Policy Controls
The ML model proposes probabilities. The deterministic Policy Engine controls the recovery boundaries.

REVIVE includes:

Failure-Specific Rules: Certain recovery actions are blocked for incompatible failure types.

Anti-Fatigue Guard: Customer notification limits prevent excessive payment links or reminders.

Economic Floors: Expensive operational escalations are restricted for low-value transactions.

Economic Stopping Rules: Recovery can stop when approved actions do not provide positive expected net value.

The policy guard is implemented in:


engine/policy_engine.py
The decision flow is:


AI Recommendation
        ↓
Policy Validation
        ↓
Economic Evaluation
        ↓
Execution
Idempotency Guard
A recovery action should not accidentally execute twice.

REVIVE generates a deterministic SHA-256 idempotency key from:


Transaction ID
      +
Action Key
      +
Attempt Number
The execution flow is:


First Execution
      ↓
SUCCESS
      ↓
Same Action Attempted Again
      ↓
REJECTED_DUPLICATE
The execution simulator is implemented in:


engine/execution.py
This prevents duplicate recovery execution for the same transaction and action attempt.

Hash-Chained Audit Ledger
Every decision and execution outcome is recorded in:


data/audit_log.json
Audit records contain information such as:


decision_id
timestamp
transaction_id
customer_id
amount
failure_reason
selected_action
ml_probability
action_cost
expected_net_recovery
policy_status
execution_status
actual_recovered_amount
idempotency_key
prev_hash
hash
Each record is linked to the previous record using SHA-256 hashing:


Record 1
   ↓
Hash 1
   ↓
Record 2
   ↓
Hash 2
   ↓
Record 3
   ↓
Hash 3
This provides a tamper-evident chain of audit records.

Batch Simulation
REVIVE is evaluated across 154 failed demonstration transactions using a deterministic simulation:

Python


Run
np.random.default_rng(42)
Using a fixed seed makes the demonstration results reproducible across Streamlit reruns.

Demonstration Results
Metric	Baseline	REVIVE	Impact
Recovery Success Rate	22.1%	63.0%	+40.9%
Gross Recovered Value	₹157,976	₹428,422	+₹270,446
Intervention Cost	₹77	₹419	+₹342
Cost per Successful Recovery	₹2.26	₹4.32	—
Net Money Recovered	₹157,899	₹428,003	+₹270,104

Incremental Net Recovery
+₹270,104

Recovery Drivers
16 expired-card transactions were salvaged through alternate payment links.

66 futile retries were suppressed on hard declines.

5 sub-economic actions were halted where the expected economics did not justify the intervention.

460 candidate actions were filtered by the Policy Guard before optimization.

The objective is not:


MAXIMIZE RETRIES
It is:


MAXIMIZE USEFUL NET RECOVERY
Try the Complete Workflow

01  Command Center
        ↓
02  Transaction Decision
        ↓
03  Policy Evaluation
        ↓
04  Execute Recovery
        ↓
05  Attempt Duplicate
        ↓
06  Batch Simulation
        ↓
07  Decision Audit
Command Center
View the overall revenue-at-risk and recovery metrics.

Transaction Decision
Inspect:

Failure reason

Customer context

Recovery probability

Recommended action

Action cost

Expected net recovery

Policy decision

Bounded Execution
Execute an approved recovery action through the execution simulator.

Idempotency
Attempt the same action again and observe:


REJECTED_DUPLICATE
Batch Simulation
Compare the baseline recovery strategy with REVIVE:


₹157,899
     ↓
₹428,003

+₹270,104 incremental net recovery
Decision Audit
Trace the decision, policy status, execution status, idempotency key, and hash chain.

Project Structure

REVIVE/
│
├── app.py
│
├── data/
│   ├── audit_log.json
│   ├── customers.csv
│   ├── recovery_history.csv
│   └── transactions.csv
│
├── engine/
│   ├── analytics.py
│   ├── audit.py
│   ├── config.py
│   ├── customer_memory.py
│   ├── data_loader.py
│   ├── decision_engine.py
│   ├── execution.py
│   ├── features.py
│   ├── model.py
│   └── policy_engine.py
│
├── models/
│   └── recovery_model.joblib
│
├── tests/
│   ├── __init__.py
│   └── run_all_tests.py
│
├── requirements.txt
├── README.md
└── .gitignore
Run Locally
Install Dependencies
Bash

pip install -r requirements.txt
Run Tests
Bash

python tests/run_all_tests.py
Expected output:


ALL TESTS PASSED
Launch REVIVE
Bash

streamlit run app.py
The application will be available at:


http://localhost:8501
Verification
The current test suite covers:


✓ Data Integrity
✓ Model Training
✓ Policy Guards
✓ Decision Engine Net-Recovery Calculation
✓ Idempotency Behavior
The complete verification command is:

Bash

python tests/run_all_tests.py
Why This Design?
REVIVE separates prediction from execution.


AI Model
   ↓
Recovery Probability
   ↓
Decision Engine
   ↓
Policy Engine
   ↓
Economic Evaluation
   ↓
Bounded Execution
   ↓
Idempotency Guard
   ↓
Audit Ledger
The model recommends.

The policy layer controls.

The economic layer evaluates.

The execution layer acts within bounds.

The audit layer records what happened.

Limitations
REVIVE is a demonstration system.

All transaction, customer, and recovery data are synthetic.

The execution layer is simulated.

No real money is moved.

The system is not connected to a live payment gateway.

Batch results are demonstration results produced from the included dataset.

The deterministic simulation uses a fixed random seed for reproducibility.

Built For
Razorpay AI Buildathon 2026 — AI Revenue Recovery Track

REVIVE is built around a simple idea:

A failed payment is not necessarily lost revenue.

Detect the opportunity.

Choose the right intervention.

Check whether it is worth doing.

Execute within boundaries.

Prevent duplicates.

And leave evidence behind.

REVIVE
Don't just retry. Recover intelligently.