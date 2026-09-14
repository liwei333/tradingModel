#!/usr/bin/env python3
"""T_OVERLAY Candidate 的纯规则合成测试。

本文件不连接行情或券商，不产生订单。25% 是 v1.3-candidate-2 的主影子
情景，50% 只在验证计划中作敏感性对照；两者都不是实盘授权。
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Optional
import unittest


D = Decimal


@dataclass(frozen=True)
class TPlan:
    core_class: str = "NORMAL"
    core_shares: int = 500
    core_entry: Decimal = D("90")
    current_price: Decimal = D("100")
    core_effective_stop: Decimal = D("90")
    thesis: str = "VALID"
    core_action: str = "MANAGE_ONLY"
    red: str = "CLEAR"
    account_state: str = "NORMAL"
    historical_regime: str = "CONSOLIDATION"
    historical_confidence: str = "MEDIUM"
    sellable_shares: Optional[int] = 500
    t_shares: int = 100
    legal_lot: int = 100
    t_entry: Decimal = D("100")
    t_stop: Decimal = D("98")
    t_target: Decimal = D("102")
    all_costs_and_slippage: Decimal = D("10")
    normal_single_trade_budget: Decimal = D("5000")
    combined_active_risk_after: Decimal = D("9000")
    combined_active_risk_limit: Decimal = D("10000")
    cash_gate: str = "PASS"
    market_value_gate: str = "PASS"


@dataclass(frozen=True)
class TDecision:
    state: str
    assessment: str
    reason: str
    t_risk: Optional[Decimal] = None
    expected_edge_after_cost: Optional[Decimal] = None


def _primary_share_cap(plan: TPlan) -> int:
    raw = plan.core_shares * 25 // 100
    return raw // plan.legal_lot * plan.legal_lot


def evaluate_t_plan(plan: TPlan) -> TDecision:
    """Return an SHADOW eligibility result, never an execution permission."""
    if plan.core_shares <= 0:
        return TDecision("T_INVALIDATED", "FAIL", "NO_CORE")
    if plan.core_class != "NORMAL":
        return TDecision("T_INVALIDATED", "FAIL", "EXPERIMENTAL_OR_OTHER_CLASS")
    if plan.thesis != "VALID":
        return TDecision("T_INVALIDATED", "FAIL", "THESIS_INVALID")
    if plan.core_action == "EXIT_PENDING":
        return TDecision("T_INVALIDATED", "FAIL", "CORE_EXIT_PENDING")
    if plan.red != "CLEAR":
        return TDecision("T_INVALIDATED", "FAIL", "RED_BLOCKS_NEW_T")
    if plan.account_state != "NORMAL":
        return TDecision("T_SKIPPED", "FAIL", "ACCOUNT_STATE")
    if (plan.historical_regime != "CONSOLIDATION"
            or plan.historical_confidence not in ("HIGH", "MEDIUM")):
        return TDecision("T_SKIPPED", "FAIL", "REGIME_NOT_ELIGIBLE")
    if plan.current_price <= plan.core_entry:
        return TDecision("T_INVALIDATED", "FAIL", "AVERAGING_DOWN_RISK")
    if plan.sellable_shares is None:
        return TDecision("T_SKIPPED", "UNKNOWN", "SELLABLE_QUANTITY_UNKNOWN")
    if (plan.legal_lot <= 0 or plan.t_shares <= 0
            or plan.t_shares % plan.legal_lot != 0):
        return TDecision("T_SKIPPED", "FAIL", "ILLEGAL_T_QUANTITY")
    if (plan.t_shares > _primary_share_cap(plan)
            or plan.t_shares > plan.sellable_shares):
        return TDecision("T_SKIPPED", "FAIL", "T_SHARE_CAP")
    if not (plan.core_effective_stop <= plan.t_stop < plan.t_entry):
        return TDecision("T_SKIPPED", "FAIL", "INVALID_T_STOP")

    planned_t_risk = (
        plan.t_shares * (plan.t_entry - plan.t_stop)
        + plan.all_costs_and_slippage
    )
    stress_t_risk = (
        plan.t_shares * (plan.t_entry - plan.core_effective_stop)
        + plan.all_costs_and_slippage
    )
    t_risk = max(planned_t_risk, stress_t_risk)
    if t_risk > D("0.25") * plan.normal_single_trade_budget:
        return TDecision("T_SKIPPED", "FAIL", "T_RISK_CAP", t_risk)
    if plan.combined_active_risk_after > plan.combined_active_risk_limit:
        return TDecision("T_SKIPPED", "FAIL", "COMBINED_RISK", t_risk)
    if plan.cash_gate != "PASS" or plan.market_value_gate != "PASS":
        return TDecision("T_SKIPPED", "FAIL", "SHARED_ACCOUNT_GATE", t_risk)

    edge = (
        plan.t_shares * (plan.t_target - plan.t_entry)
        - plan.all_costs_and_slippage
    )
    if edge <= 0:
        return TDecision("T_SKIPPED", "FAIL", "NO_POSITIVE_NET_EDGE", t_risk, edge)
    return TDecision("T_READY", "COMPLETE", "SHADOW_ONLY", t_risk, edge)


def reconcile_end_shares(strategic_shares: int, actual_end_shares: int) -> TDecision:
    if actual_end_shares != strategic_shares:
        return TDecision("T_INVENTORY_OPEN", "FAIL", "STRATEGIC_SHARE_ANOMALY")
    return TDecision("T_CLOSED", "COMPLETE", "SHARES_RECONCILED")


def handle_core_exit(t_state: str, acquired_today: int) -> TDecision:
    """Core exit always cancels or exits T; today's new shares remain T+1 pending."""
    if acquired_today > 0:
        return TDecision("T_INVENTORY_OPEN", "FAIL", "EXIT_PENDING_T1")
    if t_state in ("T_READY", "T_TRIGGERED", "T_SKIPPED"):
        return TDecision("T_INVALIDATED", "FAIL", "CORE_EXIT_CANCEL_T")
    return TDecision("T_CLOSED", "COMPLETE", "CORE_EXIT_FORCES_T_CLOSE")


class TOverlayRuleCases(unittest.TestCase):
    def test_no_core_is_forbidden(self):
        result = evaluate_t_plan(TPlan(core_shares=0, sellable_shares=0))
        self.assertEqual(("T_INVALIDATED", "NO_CORE"), (result.state, result.reason))

    def test_invalid_thesis_is_forbidden(self):
        result = evaluate_t_plan(TPlan(thesis="INVALID"))
        self.assertEqual("THESIS_INVALID", result.reason)

    def test_exit_pending_is_forbidden(self):
        result = evaluate_t_plan(TPlan(core_action="EXIT_PENDING"))
        self.assertEqual("CORE_EXIT_PENDING", result.reason)

    def test_red_blocks_new_t(self):
        result = evaluate_t_plan(TPlan(red="RED"))
        self.assertEqual(("T_INVALIDATED", "RED_BLOCKS_NEW_T"),
                         (result.state, result.reason))

    def test_primary_quantity_cap_is_enforced(self):
        # 500 Core shares -> 125 raw -> 100 shares after legal-lot floor.
        result = evaluate_t_plan(TPlan(t_shares=200))
        self.assertEqual("T_SHARE_CAP", result.reason)

    def test_t_risk_cap_is_enforced_including_cost(self):
        # 100 * (100 - 90) + 10 = 1010 > 25% * 4000 = 1000.
        result = evaluate_t_plan(TPlan(normal_single_trade_budget=D("4000")))
        self.assertEqual(D("1010"), result.t_risk)
        self.assertEqual("T_RISK_CAP", result.reason)

    def test_buying_when_core_is_losing_is_averaging_down_risk(self):
        result = evaluate_t_plan(
            TPlan(core_entry=D("105"), current_price=D("100"))
        )
        self.assertEqual(("T_INVALIDATED", "AVERAGING_DOWN_RISK"),
                         (result.state, result.reason))

    def test_core_exit_forces_t_to_cancel_or_exit(self):
        result = handle_core_exit("T_TRIGGERED", acquired_today=0)
        self.assertEqual(("T_INVALIDATED", "CORE_EXIT_CANCEL_T"),
                         (result.state, result.reason))
        pending = handle_core_exit("T_EXECUTED", acquired_today=100)
        self.assertEqual(("T_INVENTORY_OPEN", "EXIT_PENDING_T1"),
                         (pending.state, pending.reason))

    def test_end_strategic_share_anomaly_fails(self):
        result = reconcile_end_shares(strategic_shares=500, actual_end_shares=600)
        self.assertEqual(("T_INVENTORY_OPEN", "FAIL", "STRATEGIC_SHARE_ANOMALY"),
                         (result.state, result.assessment, result.reason))

    def test_unknown_sellable_quantity_is_unknown(self):
        result = evaluate_t_plan(TPlan(sellable_shares=None))
        self.assertEqual(("T_SKIPPED", "UNKNOWN", "SELLABLE_QUANTITY_UNKNOWN"),
                         (result.state, result.assessment, result.reason))

    def test_experimental_position_is_forbidden(self):
        result = evaluate_t_plan(TPlan(core_class="EXPERIMENTAL"))
        self.assertEqual("EXPERIMENTAL_OR_OTHER_CLASS", result.reason)

    def test_no_positive_net_edge_means_no_t(self):
        result = evaluate_t_plan(TPlan(t_target=D("100.10")))
        self.assertEqual(D("0.00"), result.expected_edge_after_cost)
        self.assertEqual(("T_SKIPPED", "NO_POSITIVE_NET_EDGE"),
                         (result.state, result.reason))

    def test_t_stop_is_independent_and_cannot_be_below_core_stop(self):
        result = evaluate_t_plan(TPlan(t_stop=D("89.99")))
        self.assertEqual("INVALID_T_STOP", result.reason)

    def test_valid_inputs_only_reach_shadow_ready(self):
        result = evaluate_t_plan(TPlan())
        self.assertEqual(("T_READY", "COMPLETE", "SHADOW_ONLY"),
                         (result.state, result.assessment, result.reason))

    def test_combined_risk_still_applies(self):
        result = evaluate_t_plan(
            TPlan(combined_active_risk_after=D("10000.01"))
        )
        self.assertEqual("COMBINED_RISK", result.reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
