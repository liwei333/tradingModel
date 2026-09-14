#!/usr/bin/env python3
"""ThesisGuard v1.2 的标准库 unittest 合成文档验收参考。

运行：python3 tests/experimental_position_rule_cases.py

仅处理明确提供、已标准化的门禁状态和 Decimal 合成金额。本文件不是生产
交易引擎，不接行情、券商、数据库，不发订单、不变更实验槽，不执行回测。
PASS/TRIGGERED/CLEAR 是夹具输入，不表示真实评分、Setup、OHLC、过热或
RED 行情指标已被本脚本计算、核实。组合/现金/退出/证据也仅检查输入门禁，
不在这里重建账户。完整规则以同项目系统 v1.2 第 12 节为准。

数值验收：动态正常预算、含费风险、RR、0.5R、合法数量、升级合并风险。
门禁验收：未知/否决传播、路径选择、已标准化的信号/证据/槽位/升级条件。
不覆盖：真实数据生成、订单竞态执行、成交归因、Time Stop 行情计算、
盈利/净值序列和策略优势。冻结历史账本等不变量仍需文档与实际账本核查。
"""

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Mapping, Optional, Tuple
import unittest


D = Decimal
WEIGHTS = (D("20"), D("25"), D("20"), D("15"), D("10"), D("10"))
COMMON_GATES = (
    "scope_eligible", "research", "events", "execution", "accept_loss",
    "account_allows_new", "active_risk_known", "orders_reconciled",
    "no_exit_pending", "combination", "cash", "liquidity",
    "entry_window", "price_signal_valid",
)


@dataclass(frozen=True)
class CampaignSlot:
    reservation_active: bool
    experiment_shares: int
    promotion_shares: int
    all_orders_terminal: bool
    late_reports_reconciled: bool

    def occupied(self) -> bool:
        return (self.reservation_active or self.experiment_shares != 0
                or self.promotion_shares != 0 or not self.all_orders_terminal
                or not self.late_reports_reconciled)


@dataclass(frozen=True)
class Plan:
    equity: Decimal
    account_state: str
    recovery_headroom: Optional[Decimal]
    market_filter: str
    red_status: str
    setup_status: str
    gates: Mapping[str, str]
    same_security_clear: str
    price_limit: Decimal
    stop: Decimal
    target: Decimal
    quantity: int
    minimum_quantity: int
    quantity_step: int
    loss_cost: Decimal
    target_cost: Decimal
    score_parts: Tuple[Optional[Decimal], ...]
    score_evidence_status: str
    stock_class: str
    b_extra_evidence: str
    relative_strength_status: str
    overheated_status: str
    slot: CampaignSlot


@dataclass(frozen=True)
class HoldingReview:
    quantity: int
    current_price: Decimal
    structure_stop: Decimal
    target: Decimal
    exit_loss_cost: Decimal
    exit_target_cost: Decimal


@dataclass(frozen=True)
class Promotion:
    plan: Plan
    old_current_h: Decimal
    old_net_liquidation_pnl: Decimal
    old_effective_stop: Decimal
    proposed_old_effective_stop: Decimal
    normal_card_status: str
    new_signal_after_first_buy: str
    thesis_status: str
    own_experiment_status: str
    old_orders_reconciled: str
    no_latched_exit: str
    completed_promotions: int
    holding_review: Optional[HoldingReview] = None


@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    normal_budget: Optional[Decimal] = None
    planned_risk: Optional[Decimal] = None
    rr: Optional[Decimal] = None
    planned_risk_r: Optional[Decimal] = None


def normal_risk(plan: Plan) -> Decimal:
    """Account state is supplied; this does not calculate D or clear a pause."""
    if not _finite(plan.equity) or plan.equity <= 0:
        return D("0")
    factor = {"NORMAL": D("0.005"), "WARNING": D("0.0025"),
              "CONTRACTED": D("0.00125"), "RECOVERY": D("0.00125")}.get(plan.account_state)
    if factor is None:
        return D("0")
    amount = plan.equity * factor
    if plan.account_state == "RECOVERY":
        if not _finite(plan.recovery_headroom) or plan.recovery_headroom < 0:
            return D("0")
        amount = min(amount, plan.recovery_headroom)
    return amount


def _finite(value) -> bool:
    return isinstance(value, Decimal) and value.is_finite()


def _shared_rejection(plan: Plan) -> Optional[str]:
    for gate in COMMON_GATES:
        if plan.gates.get(gate) != "PASS":
            return "GATE:" + gate
    if plan.red_status != "CLEAR":
        return "MARKET_RED_OR_UNKNOWN"
    if plan.market_filter not in ("PASS", "FAIL"):
        return "MARKET_FILTER_UNKNOWN"
    if plan.setup_status != "TRIGGERED":
        return "SETUP"
    if normal_risk(plan) <= 0:
        return "ACCOUNT_BUDGET"
    return None


def _planned_order(plan: Plan) -> Decision:
    """Validate a synthetic requested quantity, not an actual board/order API."""
    budget = normal_risk(plan)
    numbers = (plan.price_limit, plan.stop, plan.target, plan.loss_cost, plan.target_cost)
    if (not all(_finite(value) for value in numbers)
            or not (plan.target > plan.price_limit > plan.stop > 0)
            or plan.loss_cost < 0 or plan.target_cost < 0):
        return Decision("NO_TRADE", "NUMERIC_INPUT", budget)
    quantities = (plan.quantity, plan.minimum_quantity, plan.quantity_step)
    if (any(type(value) is not int or value <= 0 for value in quantities)
            or plan.quantity < plan.minimum_quantity
            or (plan.quantity - plan.minimum_quantity) % plan.quantity_step != 0):
        return Decision("NO_TRADE", "LEGAL_QUANTITY", budget)
    risk = plan.quantity * (plan.price_limit - plan.stop) + plan.loss_cost
    rr = (plan.quantity * (plan.target - plan.price_limit) - plan.target_cost) / risk
    return Decision("EVALUATED", "ORDER_NUMERICS", budget, risk, rr, risk / budget)


def evaluate_entry(plan: Plan) -> Decision:
    """Pure admission result; ALLOW never reserves a slot or submits an order."""
    reason = _shared_rejection(plan)
    if reason:
        return Decision("NO_TRADE", reason, normal_risk(plan))
    if plan.same_security_clear != "PASS":
        return Decision("NO_TRADE", "EXISTING_SAME_SECURITY", normal_risk(plan))
    result = _planned_order(plan)
    if result.action == "NO_TRADE":
        return result
    is_experiment = plan.market_filter == "FAIL"
    if is_experiment:
        reason = None
        if plan.score_evidence_status != "PASS":
            reason = "SCORE_EVIDENCE"
        elif (len(plan.score_parts) != 6
              or any(not _finite(score) or score < 0 or score > weight
                     for score, weight in zip(plan.score_parts, WEIGHTS))
              or sum(plan.score_parts) < D("70")):
            reason = "SCORE"
        elif plan.stock_class not in ("A", "B"):
            reason = "STOCK_CLASS"
        elif plan.stock_class == "B" and plan.b_extra_evidence != "PASS":
            reason = "B_EXTRA_EVIDENCE"
        elif plan.relative_strength_status != "PASS":
            reason = "RELATIVE_STRENGTH"
        elif plan.overheated_status != "CLEAR":
            reason = "OVERHEATED_OR_UNKNOWN"
        elif plan.quantity > 100:
            reason = "EXPERIMENTAL_QUANTITY_CAP"
        elif plan.slot.occupied():
            reason = "EXPERIMENTAL_SLOT"
        if reason:
            return replace(result, action="NO_TRADE", reason=reason)
    cap = result.normal_budget * (D("0.5") if is_experiment else D("1"))
    if result.planned_risk > cap:
        return replace(result, action="NO_TRADE", reason="RISK_BUDGET")
    if result.rr < 2:
        return replace(result, action="NO_TRADE", reason="RR")
    return replace(result, action="EXPERIMENTAL_ENTRY" if is_experiment else "NORMAL_ENTRY",
                   reason="ALL_REQUIRED_GATES_PASS")


def evaluate_promotion(promotion: Promotion) -> Decision:
    """An eligible decision only: actual fills, IDs and immutable ledgers are external."""
    plan = promotion.plan
    budget = normal_risk(plan)
    reason = _shared_rejection(plan)
    if reason:
        return Decision("NO_TRADE", reason, budget)
    if plan.market_filter != "PASS":
        return Decision("NO_TRADE", "PROMOTION_MARKET_PASS_REQUIRED", budget)
    for gate in ("normal_card_status", "new_signal_after_first_buy", "thesis_status",
                 "own_experiment_status", "old_orders_reconciled", "no_latched_exit"):
        if getattr(promotion, gate) != "PASS":
            return Decision("NO_TRADE", "PROMOTION_GATE:" + gate, budget)
    if (plan.slot.experiment_shares <= 0 or not plan.slot.all_orders_terminal
            or not plan.slot.late_reports_reconciled):
        return Decision("NO_TRADE", "PROMOTION_ORIGINAL_POSITION_UNKNOWN", budget)
    if promotion.completed_promotions != 0:
        return Decision("NO_TRADE", "PROMOTION_ALREADY_USED", budget)
    values = (promotion.old_current_h, promotion.old_net_liquidation_pnl,
              promotion.old_effective_stop, promotion.proposed_old_effective_stop)
    if (not all(_finite(value) for value in values) or promotion.old_current_h < 0
            or promotion.old_effective_stop <= 0):
        return Decision("NO_TRADE", "PROMOTION_NUMERIC_INPUT", budget)
    if promotion.old_net_liquidation_pnl <= 0:
        return Decision("NO_TRADE", "PROMOTION_NOT_PROFITABLE", budget)
    if promotion.proposed_old_effective_stop < promotion.old_effective_stop:
        return Decision("NO_TRADE", "OLD_STOP_WIDENED", budget)
    if plan.quantity == 0:
        hold = promotion.holding_review
        if hold is None:
            return Decision("NO_TRADE", "HOLDING_REVIEW_REQUIRED", budget)
        numbers = (hold.current_price, hold.structure_stop, hold.target,
                   hold.exit_loss_cost, hold.exit_target_cost, plan.price_limit)
        if (not all(_finite(value) for value in numbers)
                or type(hold.quantity) is not int or hold.quantity <= 0
                or hold.quantity != plan.slot.experiment_shares
                or hold.exit_loss_cost < 0 or hold.exit_target_cost < 0
                or hold.structure_stop <= 0):
            return Decision("NO_TRADE", "HOLDING_REVIEW_INPUT", budget)
        stop_eval = max(promotion.old_effective_stop, hold.structure_stop)
        if not (hold.target > hold.current_price > stop_eval
                and hold.current_price <= plan.price_limit):
            return Decision("NO_TRADE", "HOLDING_REVIEW_PRICE", budget)
        risk_hold = hold.quantity * (hold.current_price - stop_eval) + hold.exit_loss_cost
        rr = (hold.quantity * (hold.target - hold.current_price) - hold.exit_target_cost) / risk_hold
        result = Decision("EVALUATED", "HOLDING_REVIEW", budget, D("0"), rr, D("0"))
        if rr < 2:
            return replace(result, action="NO_TRADE", reason="RR_HOLD")
    else:
        result = _planned_order(plan)
        if result.action == "NO_TRADE":
            return result
        if result.rr < 2:
            return replace(result, action="NO_TRADE", reason="RR")
    # Use already effective old H, never savings from an unimplemented higher stop.
    if promotion.old_current_h + result.planned_risk > budget:
        return replace(result, action="NO_TRADE", reason="PROMOTION_COMBINED_RISK")
    return replace(result, action="PROMOTE_TO_NORMAL", reason="ALL_REQUIRED_GATES_PASS")


def fixture(**changes) -> Plan:
    """Only this explicit synthetic fixture supplies PASS values by default."""
    base = Plan(
        equity=D("140000"), account_state="NORMAL", recovery_headroom=None,
        market_filter="FAIL", red_status="CLEAR", setup_status="TRIGGERED",
        gates={name: "PASS" for name in COMMON_GATES}, same_security_clear="PASS",
        price_limit=D("100"), stop=D("97.50"), target=D("110"),
        quantity=100, minimum_quantity=100, quantity_step=100,
        loss_cost=D("30"), target_cost=D("30"),
        score_parts=(D("16"), D("20"), D("16"), D("12"), D("8"), D("8")),
        score_evidence_status="PASS", stock_class="A", b_extra_evidence="UNKNOWN",
        relative_strength_status="PASS", overheated_status="CLEAR",
        slot=CampaignSlot(False, 0, 0, True, True),
    )
    return replace(base, **changes)


def promotion_fixture(**changes) -> Promotion:
    base = Promotion(
        plan=fixture(
            market_filter="PASS", price_limit=D("104"), stop=D("100"),
            target=D("114"), same_security_clear="FAIL",
            slot=CampaignSlot(False, 100, 0, True, True),
        ),
        old_current_h=D("200"), old_net_liquidation_pnl=D("370"),
        old_effective_stop=D("102.15"), proposed_old_effective_stop=D("102.15"),
        normal_card_status="PASS", new_signal_after_first_buy="PASS",
        thesis_status="PASS", own_experiment_status="PASS",
        old_orders_reconciled="PASS", no_latched_exit="PASS", completed_promotions=0,
    )
    return replace(base, **changes)


class RequiredCases(unittest.TestCase):
    """The eight user cases; Case 8 covers both routes in subtests."""

    def test_case_01_market_pass_allows_normal(self):
        result = evaluate_entry(fixture(market_filter="PASS"))
        self.assertEqual(result.action, "NORMAL_ENTRY")
        self.assertEqual(result.planned_risk, D("280"))
        self.assertEqual(result.rr, D("970") / D("280"))

    def test_case_02_market_fail_allows_04r_experiment(self):
        result = evaluate_entry(fixture())
        self.assertEqual(result.action, "EXPERIMENTAL_ENTRY")
        self.assertEqual(result.normal_budget, D("700"))
        self.assertEqual(result.planned_risk, D("280"))
        self.assertEqual(result.planned_risk_r, D("0.4"))
        self.assertEqual(result.rr, D("970") / D("280"))

    def test_case_03_score_65_rejected(self):
        scores = tuple(map(D, ("13", "16", "13", "10", "6", "7")))
        self.assertEqual(evaluate_entry(fixture(score_parts=scores)).reason, "SCORE")

    def test_case_04_overheated_rejected(self):
        # 3-day +15.00% -> OVERHEATED is supplied by the documented upstream rule.
        self.assertEqual(evaluate_entry(fixture(overheated_status="OVERHEATED")).reason,
                         "OVERHEATED_OR_UNKNOWN")

    def test_case_05_08r_rejected_even_with_valid_rr(self):
        result = evaluate_entry(fixture(stop=D("94.70"), target=D("112")))
        self.assertEqual(result.action, "NO_TRADE")
        self.assertEqual(result.reason, "RISK_BUDGET")
        self.assertEqual(result.planned_risk, D("560"))
        self.assertEqual(result.planned_risk_r, D("0.8"))
        self.assertEqual(result.rr, D("1170") / D("560"))

    def test_case_06_second_experiment_rejected(self):
        slot = CampaignSlot(False, 100, 0, True, True)
        self.assertEqual(evaluate_entry(fixture(slot=slot)).reason, "EXPERIMENTAL_SLOT")

    def test_case_07_one_promotion_with_630_combined_risk(self):
        promotion = promotion_fixture()
        result = evaluate_promotion(promotion)
        self.assertEqual(result.action, "PROMOTE_TO_NORMAL")
        self.assertEqual(result.planned_risk, D("430"))
        self.assertEqual(result.rr, D("970") / D("430"))
        self.assertEqual(promotion.old_current_h + result.planned_risk, D("630"))

    def test_case_08_red_rejects_both_paths(self):
        for market in ("PASS", "FAIL"):
            with self.subTest(market=market):
                result = evaluate_entry(fixture(market_filter=market, red_status="RED"))
                self.assertEqual(result.reason, "MARKET_RED_OR_UNKNOWN")


class EntryBoundaries(unittest.TestCase):
    def test_normal_does_not_inherit_experimental_only_requirements(self):
        plan = fixture(
            market_filter="PASS", quantity=200, score_parts=(),
            score_evidence_status="UNKNOWN", relative_strength_status="UNKNOWN",
            overheated_status="OVERHEATED", slot=CampaignSlot(False, 100, 0, True, True),
        )
        result = evaluate_entry(plan)
        self.assertEqual(result.action, "NORMAL_ENTRY")
        self.assertEqual(result.planned_risk, D("530"))

    def test_normal_same_security_cannot_add_outside_promotion(self):
        self.assertEqual(evaluate_entry(fixture(market_filter="PASS",
                                               same_security_clear="FAIL")).reason,
                         "EXISTING_SAME_SECURITY")

    def test_unknown_market_or_red_never_routes_to_experiment(self):
        for changes in ({"market_filter": "UNKNOWN"}, {"red_status": "UNKNOWN"}):
            with self.subTest(changes=changes):
                self.assertEqual(evaluate_entry(fixture(**changes)).action, "NO_TRADE")

    def test_only_triggered_setup_is_executable_on_either_route(self):
        for market in ("PASS", "FAIL"):
            for setup in ("READY", "WATCH", "OVERHEATED", "REJECT", "EXPIRED", "INVALIDATED", "UNKNOWN"):
                with self.subTest(market=market, setup=setup):
                    self.assertEqual(evaluate_entry(fixture(market_filter=market,
                                                           setup_status=setup)).reason, "SETUP")

    def test_score_70_is_inclusive(self):
        scores = tuple(map(D, ("14", "18", "14", "10", "7", "7")))
        self.assertEqual(evaluate_entry(fixture(score_parts=scores)).action, "EXPERIMENTAL_ENTRY")

    def test_score_evidence_unknown_blocks_valid_total(self):
        self.assertEqual(evaluate_entry(fixture(score_evidence_status="UNKNOWN")).reason,
                         "SCORE_EVIDENCE")

    def test_missing_out_of_range_and_nonfinite_score_parts_fail(self):
        for scores in ((None,) * 6, (D("20"),) * 6, (), (D("NaN"),) * 6):
            with self.subTest(scores=scores):
                self.assertEqual(evaluate_entry(fixture(score_parts=scores)).reason, "SCORE")

    def test_a_b_c_types_and_b_extra_evidence(self):
        cases = (("A", "UNKNOWN", True), ("B", "PASS", True),
                 ("B", "UNKNOWN", False), ("C", "PASS", False), ("UNKNOWN", "PASS", False))
        for stock, evidence, allowed in cases:
            with self.subTest(stock=stock, evidence=evidence):
                result = evaluate_entry(fixture(stock_class=stock, b_extra_evidence=evidence))
                self.assertEqual(result.action == "EXPERIMENTAL_ENTRY", allowed)

    def test_relative_strength_and_heat_unknown_fail_closed(self):
        for changes in ({"relative_strength_status": "FAIL"},
                        {"relative_strength_status": "UNKNOWN"}, {"overheated_status": "UNKNOWN"}):
            with self.subTest(changes=changes):
                self.assertEqual(evaluate_entry(fixture(**changes)).action, "NO_TRADE")

    def test_half_budget_includes_fees_exactly(self):
        boundary = fixture(stop=D("96.80"))  # 320 + 30 = 350.
        self.assertEqual(evaluate_entry(boundary).action, "EXPERIMENTAL_ENTRY")
        self.assertEqual(evaluate_entry(boundary).planned_risk_r, D("0.5"))
        self.assertEqual(evaluate_entry(replace(boundary, loss_cost=D("30.01"))).reason,
                         "RISK_BUDGET")

    def test_fees_cannot_be_omitted(self):
        result = evaluate_entry(fixture(stop=D("96.60")))
        self.assertEqual(result.planned_risk, D("370"))
        self.assertEqual(result.reason, "RISK_BUDGET")

    def test_rr_two_inclusive_and_below_two_rejected(self):
        exact = fixture(target=D("105.90"))  # (590 - 30) / 280 = 2.
        self.assertEqual(evaluate_entry(exact).rr, D("2"))
        self.assertEqual(evaluate_entry(exact).action, "EXPERIMENTAL_ENTRY")
        self.assertEqual(evaluate_entry(replace(exact, target=D("105.89"))).reason, "RR")

    def test_dynamic_account_budgets_and_warning_rejection(self):
        for state, expected in (("NORMAL", "700"), ("WARNING", "350"), ("CONTRACTED", "175")):
            with self.subTest(state=state):
                self.assertEqual(normal_risk(fixture(account_state=state)), D(expected))
        result = evaluate_entry(fixture(account_state="WARNING"))
        self.assertEqual(result.normal_budget, D("350"))
        self.assertEqual(result.reason, "RISK_BUDGET")  # Experimental cap now 175.

    def test_recovery_budget_limited_by_headroom_then_halved(self):
        plan = fixture(account_state="RECOVERY", recovery_headroom=D("120"),
                       stop=D("99.60"), loss_cost=D("20"))
        self.assertEqual(normal_risk(plan), D("120"))
        self.assertEqual(evaluate_entry(plan).action, "EXPERIMENTAL_ENTRY")
        self.assertEqual(evaluate_entry(replace(plan, loss_cost=D("20.01"))).reason, "RISK_BUDGET")

    def test_paused_unknown_and_missing_recovery_headroom_fail(self):
        for state in ("PAUSED_DD", "UNKNOWN", "RECOVERY"):
            with self.subTest(state=state):
                self.assertEqual(evaluate_entry(fixture(account_state=state)).reason, "ACCOUNT_BUDGET")

    def test_quantity_cap_and_board_legal_set_both_apply(self):
        for changes in ({"minimum_quantity": 200}, {"minimum_quantity": 200, "quantity": 200},
                        {"quantity": 99}, {"quantity": 101}, {"quantity": 0}):
            with self.subTest(changes=changes):
                self.assertEqual(evaluate_entry(fixture(**changes)).action, "NO_TRADE")

    def test_existing_normal_can_use_legal_200_share_minimum(self):
        self.assertEqual(evaluate_entry(fixture(market_filter="PASS", minimum_quantity=200,
                                               quantity_step=1, quantity=200)).action, "NORMAL_ENTRY")

    def test_all_shared_gates_fail_or_unknown_reject_both_routes(self):
        for market in ("PASS", "FAIL"):
            for gate in COMMON_GATES:
                for status in ("FAIL", "UNKNOWN"):
                    with self.subTest(market=market, gate=gate, status=status):
                        plan = fixture(market_filter=market)
                        result = evaluate_entry(replace(plan, gates={**plan.gates, gate: status}))
                        self.assertEqual(result.reason, "GATE:" + gate)

    def test_missing_shared_gate_is_not_default_pass(self):
        plan = fixture()
        gates = dict(plan.gates)
        del gates["cash"]
        self.assertEqual(evaluate_entry(replace(plan, gates=gates)).reason, "GATE:cash")

    def test_invalid_decimal_and_negative_cost_are_rejected(self):
        for changes in ({"loss_cost": D("-1")}, {"target_cost": D("-1")},
                        {"price_limit": D("NaN")}, {"stop": D("100")},
                        {"equity": D("Infinity")}):
            with self.subTest(changes=changes):
                self.assertEqual(evaluate_entry(fixture(**changes)).action, "NO_TRADE")


class SlotBoundaries(unittest.TestCase):
    def test_inflight_cancellation_promotion_and_late_reports_occupy_slot(self):
        cases = (
            CampaignSlot(True, 0, 0, True, True),
            CampaignSlot(False, 0, 0, False, True),
            CampaignSlot(False, 100, 0, True, True),
            CampaignSlot(False, 0, 100, True, True),
            CampaignSlot(False, 0, 0, True, False),
        )
        for slot in cases:
            with self.subTest(slot=slot):
                self.assertTrue(slot.occupied())
                self.assertEqual(evaluate_entry(fixture(slot=slot)).reason, "EXPERIMENTAL_SLOT")

    def test_only_flat_terminal_reconciled_unreserved_campaign_is_free(self):
        slot = CampaignSlot(False, 0, 0, True, True)
        self.assertFalse(slot.occupied())
        self.assertEqual(evaluate_entry(fixture(slot=slot)).action, "EXPERIMENTAL_ENTRY")


class PromotionBoundaries(unittest.TestCase):
    def test_old_h_plus_new_risk_cannot_exceed_normal_budget(self):
        self.assertEqual(evaluate_promotion(promotion_fixture(old_current_h=D("270"))).action,
                         "PROMOTE_TO_NORMAL")  # 270 + 430 = 700 inclusive.
        for old_h in (D("270.01"), D("280")):
            with self.subTest(old_h=old_h):
                self.assertEqual(evaluate_promotion(promotion_fixture(old_current_h=old_h)).reason,
                                 "PROMOTION_COMBINED_RISK")

    def test_new_card_new_signal_and_other_upgrade_gates_required(self):
        fields = ("normal_card_status", "new_signal_after_first_buy", "thesis_status",
                  "own_experiment_status", "old_orders_reconciled", "no_latched_exit")
        for field in fields:
            for status in ("FAIL", "UNKNOWN"):
                with self.subTest(field=field, status=status):
                    self.assertEqual(evaluate_promotion(promotion_fixture(**{field: status})).action,
                                     "NO_TRADE")

    def test_original_leg_must_be_profitable_now(self):
        for pnl in (D("0"), D("-1")):
            with self.subTest(pnl=pnl):
                self.assertEqual(evaluate_promotion(promotion_fixture(old_net_liquidation_pnl=pnl)).reason,
                                 "PROMOTION_NOT_PROFITABLE")

    def test_new_leg_stop_may_be_lower_but_old_stop_cannot_be_lowered(self):
        self.assertEqual(evaluate_promotion(promotion_fixture()).action, "PROMOTE_TO_NORMAL")
        self.assertEqual(evaluate_promotion(promotion_fixture(
            proposed_old_effective_stop=D("100"))).reason, "OLD_STOP_WIDENED")

    def test_only_one_effective_promotion_even_after_subleg_exit(self):
        for count in (1, 2):
            with self.subTest(count=count):
                self.assertEqual(evaluate_promotion(promotion_fixture(completed_promotions=count)).reason,
                                 "PROMOTION_ALREADY_USED")

    def test_promotion_requires_market_pass_triggered_nonred(self):
        for changes in ({"market_filter": "FAIL"}, {"market_filter": "UNKNOWN"},
                        {"setup_status": "READY"}, {"red_status": "RED"}, {"red_status": "UNKNOWN"}):
            with self.subTest(changes=changes):
                p = promotion_fixture()
                self.assertEqual(evaluate_promotion(replace(p, plan=replace(p.plan, **changes))).action,
                                 "NO_TRADE")

    def test_promotion_inherits_shared_account_cash_combination_vetoes(self):
        p = promotion_fixture()
        for gate in COMMON_GATES:
            with self.subTest(gate=gate):
                plan = replace(p.plan, gates={**p.plan.gates, gate: "FAIL"})
                self.assertEqual(evaluate_promotion(replace(p, plan=plan)).reason, "GATE:" + gate)

    def test_promotion_uses_current_downgraded_budget(self):
        p = promotion_fixture()
        result = evaluate_promotion(replace(p, plan=replace(p.plan, account_state="WARNING")))
        self.assertEqual(result.action, "NO_TRADE")
        self.assertEqual(result.normal_budget, D("350"))

    def test_management_only_upgrade_has_no_new_order_risk(self):
        p = promotion_fixture()
        review = HoldingReview(100, D("104"), D("100"), D("114"), D("30"), D("30"))
        result = evaluate_promotion(replace(p, plan=replace(p.plan, quantity=0), holding_review=review))
        self.assertEqual(result.action, "PROMOTE_TO_NORMAL")
        self.assertEqual(result.planned_risk, D("0"))
        self.assertEqual(result.rr, D("970") / D("215"))

    def test_management_only_still_requires_holding_rr_and_current_old_h(self):
        p = promotion_fixture()
        p = replace(p, plan=replace(p.plan, quantity=0))
        self.assertEqual(evaluate_promotion(p).action, "NO_TRADE")
        bad_rr = HoldingReview(100, D("104"), D("100"), D("106"), D("30"), D("30"))
        self.assertEqual(evaluate_promotion(replace(p, holding_review=bad_rr)).reason, "RR_HOLD")
        proposed_tighter = replace(bad_rr, structure_stop=D("103.95"), target=D("114"))
        self.assertEqual(evaluate_promotion(replace(p, old_current_h=D("701"),
                                                   holding_review=proposed_tighter)).reason,
                         "PROMOTION_COMBINED_RISK")

    def test_evaluating_promotion_does_not_release_slot_or_mutate_inputs(self):
        p = promotion_fixture()
        original = p
        self.assertEqual(evaluate_promotion(p).action, "PROMOTE_TO_NORMAL")
        self.assertEqual(p, original)
        self.assertTrue(p.plan.slot.occupied())
        self.assertEqual(evaluate_entry(fixture(slot=p.plan.slot)).reason, "EXPERIMENTAL_SLOT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
