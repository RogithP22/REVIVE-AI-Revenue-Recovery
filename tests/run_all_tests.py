import sys
import site
from pathlib import Path

user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.insert(0, user_site)

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from engine.data_loader import load_data
from engine.model import RecoveryModelPipeline
from engine.decision_engine import DecisionEngine
from engine.policy_engine import PolicyGuard
from engine.execution import ExecutionSimulator

def run_tests():
    # 1. Data Integrity Check
    txns, custs, hist, diag = load_data()
    assert not txns.empty
    assert not custs.empty
    assert not hist.empty
    assert diag["integrity_verified"] is True
    
    # 2. Model Training Check
    pipeline = RecoveryModelPipeline()
    pipeline.train(hist, txns, custs)
    assert pipeline.is_trained is True
    assert pipeline.training_samples > 0
    
    # 3. Deterministic Policy Checks
    status, _ = PolicyGuard.evaluate("RETRY_NOW", 1000.0, "Credit Card", "EXPIRED_CARD", "Low", 1, 0.0)
    assert status == "BLOCKED"
    
    status, _ = PolicyGuard.evaluate("HUMAN_ESCALATION", 500.0, "UPI", "AUTH_TIMEOUT", "Low", 1, 0.0)
    assert status == "BLOCKED"
    
    # 4. Decision Engine Mathematical Formulation
    engine = DecisionEngine(pipeline)
    test_txn = txns[txns["status"] == "FAILED"].iloc[0]
    decision = engine.evaluate_transaction(test_txn, custs, hist)
    win = decision["winning_action"]
    
    calculated_net = round(win["expected_recovery"] - win["cost"], 2)
    assert round(win["expected_net_recovery"], 2) == calculated_net
    
    if win["action_key"] != "STOP_RECOVERY":
        assert win["policy_status"] == "APPROVED"
        
    # 5. Idempotency Execution & Deduplication Check
    sim = ExecutionSimulator()
    test_decision = decision.copy()
    test_decision["transaction_id"] = "TEST_TXN_VERIFY_9999"
    test_decision["attempt_number"] = 99
    
    # Reset lock table for isolated test key
    sim.lock_table.discard(f"{test_decision['transaction_id']}:{test_decision['winning_action']['action_key']}:{test_decision['attempt_number']}")
    
    res1 = sim.execute(test_decision)
    assert res1["success"] is True, f"Execution failed: {res1.get('message')}"
    
    res2 = sim.execute(test_decision)
    assert res2["status"] == "REJECTED_DUPLICATE", "Idempotency collision was not detected."
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()