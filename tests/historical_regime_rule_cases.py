#!/usr/bin/env python3
"""Historical Regime Candidate 的纯规则合成测试。

本文件只验证时点化、UNKNOWN/FAIL 传播和权限隔离。它不下载行情、不判断
真实证券、不计算买点，也不允许 Historical Regime 覆盖 v1.2 的正式门禁。
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple
import unittest


@dataclass(frozen=True)
class RegimeCardInput:
    cutoff: datetime
    observations_available_at: Tuple[datetime, ...]
    required_data_complete: bool
    comparable_periods: Tuple[str, ...]
    comparisons_valid: bool = True


@dataclass(frozen=True)
class StudyDecision:
    status: str
    reason: str
    trade_permission: str = "NONE"


def evaluate_regime_card(card: RegimeCardInput) -> StudyDecision:
    """Evaluate research integrity only; never return a trading permission."""
    if any(available_at > card.cutoff for available_at in card.observations_available_at):
        return StudyDecision("FAIL", "FUTURE_DATA")
    if not card.required_data_complete:
        return StudyDecision("UNKNOWN", "DATA_INSUFFICIENT")
    if not card.comparisons_valid:
        return StudyDecision("UNKNOWN", "INVALID_COMPARISON")
    if not card.comparable_periods:
        return StudyDecision("UNKNOWN", "NO_VALID_COMPARABLE_PERIOD")
    return StudyDecision("COMPLETE", "CONTEXT_RECORDED")


@dataclass(frozen=True)
class ActiveBaselineInput:
    thesis: str = "PASS"
    setup: str = "PASS"
    red: str = "CLEAR"
    risk: str = "PASS"
    exit_pending: bool = False


def apply_context_without_override(
    _study: StudyDecision, baseline: ActiveBaselineInput
) -> str:
    """Historical output is intentionally unable to grant ALLOW."""
    if baseline.exit_pending:
        return "EXIT_PENDING"
    if baseline.red != "CLEAR":
        return "NO_TRADE:RED"
    if baseline.thesis != "PASS":
        return "NO_TRADE:THESIS"
    if baseline.setup != "PASS":
        return "NO_TRADE:SETUP"
    if baseline.risk != "PASS":
        return "NO_TRADE:RISK"
    return "DEFER_TO_V12_ACTIVE_BASELINE"


class HistoricalRegimeRuleCases(unittest.TestCase):
    def setUp(self):
        self.cutoff = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)
        self.valid = RegimeCardInput(
            cutoff=self.cutoff,
            observations_available_at=(
                datetime(2026, 9, 14, 14, 59, tzinfo=timezone.utc),
            ),
            required_data_complete=True,
            comparable_periods=("2024_BASE",),
        )

    def test_insufficient_data_is_unknown(self):
        card = RegimeCardInput(
            cutoff=self.cutoff,
            observations_available_at=(),
            required_data_complete=False,
            comparable_periods=(),
        )
        result = evaluate_regime_card(card)
        self.assertEqual(("UNKNOWN", "DATA_INSUFFICIENT", "NONE"),
                         (result.status, result.reason, result.trade_permission))

    def test_future_data_is_fail(self):
        card = RegimeCardInput(
            cutoff=self.cutoff,
            observations_available_at=(
                datetime(2026, 9, 15, 9, 0, tzinfo=timezone.utc),
            ),
            required_data_complete=True,
            comparable_periods=("2024_BASE",),
        )
        result = evaluate_regime_card(card)
        self.assertEqual(("FAIL", "FUTURE_DATA"), (result.status, result.reason))

    def test_no_comparable_history_is_allowed_unknown(self):
        card = RegimeCardInput(
            cutoff=self.cutoff,
            observations_available_at=(self.cutoff,),
            required_data_complete=True,
            comparable_periods=(),
        )
        result = evaluate_regime_card(card)
        self.assertEqual(("UNKNOWN", "NO_VALID_COMPARABLE_PERIOD"),
                         (result.status, result.reason))
        self.assertEqual("NONE", result.trade_permission)

    def test_historical_similarity_cannot_override_setup_fail(self):
        study = evaluate_regime_card(self.valid)
        self.assertEqual("COMPLETE", study.status)
        result = apply_context_without_override(
            study, ActiveBaselineInput(setup="FAIL")
        )
        self.assertEqual("NO_TRADE:SETUP", result)

    def test_red_cannot_be_overridden_by_historical_similarity(self):
        study = evaluate_regime_card(self.valid)
        result = apply_context_without_override(
            study, ActiveBaselineInput(red="RED")
        )
        self.assertEqual("NO_TRADE:RED", result)

    def test_complete_context_still_cannot_return_allow(self):
        study = evaluate_regime_card(self.valid)
        result = apply_context_without_override(study, ActiveBaselineInput())
        self.assertEqual("DEFER_TO_V12_ACTIVE_BASELINE", result)
        self.assertNotIn("ALLOW", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
