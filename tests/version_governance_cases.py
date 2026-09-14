#!/usr/bin/env python3
"""WP-V13-01 的文档版本治理验收。

本测试只检查仓库文档、链接、状态和冻结文本，不计算交易信号、不连接行情或
券商，也不把 Candidate/Shadow 规则变成交易许可。
"""

from hashlib import sha256
from pathlib import Path
import re
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
V12 = ROOT / "个人交易系统_v1.2_基于ThesisGuard_v1.3.md"
CANDIDATE = ROOT / "个人交易系统_v1.3_产业趋势波段版_CANDIDATE.md"
VALIDATION_PLAN = ROOT / "v1.3_validation_plan.md"
ADR = ROOT / "decisions" / "ADR-001-portfolio-capacity.md"

# master 823c5b5 中正式 v1.2 的原始文件 SHA。WP-V13-01 只把其中的本地链接
# 目标从 /Users/... 改为相对路径，所以原始文件 SHA 会变化。把所有本地链接
# 目标规范成同一占位符后，其余完整文本必须继续匹配这个冻结指纹。
V12_PRE_WP_RAW_SHA256 = (
    "b572de156b9254a473f3d924c601ef41b2d6786d2affd13e522f38b5775f0a2d"
)
V12_RULE_TEXT_SHA256 = (
    "d55c55754a28e9cf98fdfa4caf53b6216d6ef392b55973f8081a96bda26a4c9f"
)

MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)\n]+)\)")
ABSOLUTE_USER_LINK = re.compile(r"\]\((?:file://)?/Users/")
LOCAL_LINK_TARGET = re.compile(r"\]\((?!https?://|mailto:|#)[^)\n]+\)")


def markdown_files():
    return sorted(path for path in ROOT.rglob("*.md") if ".git" not in path.parts)


def canonical_rule_text(text: str) -> str:
    """Remove only local link destinations; preserve labels and all rule prose."""
    return LOCAL_LINK_TARGET.sub("](<LOCAL_LINK>)", text)


class VersionGovernanceCases(unittest.TestCase):
    def test_required_files_exist(self):
        required = [
            ROOT / "README.md",
            V12,
            ROOT / "实验仓_v1.2_验收案例.md",
            ROOT / "个人交易系统_v1.2_产业趋势中短期波段适配审计_2026-09-14.md",
            CANDIDATE,
            VALIDATION_PLAN,
            ADR,
            ROOT / "tests" / "experimental_position_rule_cases.py",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        self.assertEqual([], missing)

    def test_no_absolute_users_markdown_links(self):
        findings = []
        for path in markdown_files():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if ABSOLUTE_USER_LINK.search(line):
                    findings.append(f"{path.relative_to(ROOT)}:{number}")
        self.assertEqual([], findings)

    def test_all_relative_markdown_links_resolve(self):
        broken = []
        for path in markdown_files():
            text = path.read_text(encoding="utf-8")
            for raw_target in MARKDOWN_LINK.findall(text):
                target = raw_target.strip()
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = unquote(target.split("#", 1)[0])
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    broken.append(f"{path.relative_to(ROOT)} -> {raw_target}")
        self.assertEqual([], broken)

    def test_readme_declares_status_vocabulary_and_catalog(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for status in ("ACTIVE", "CANDIDATE", "SHADOW", "DEPRECATED", "HISTORICAL"):
            self.assertIn(f"`{status}`", readme)
        for required_name in (
            "个人交易系统_v1.2_基于ThesisGuard_v1.3.md",
            "实验仓_v1.2_验收案例.md",
            "个人交易系统_v1.2_产业趋势中短期波段适配审计_2026-09-14.md",
            "个人交易系统_v1.3_产业趋势波段版_CANDIDATE.md",
            "v1.3_validation_plan.md",
            "ADR-001-portfolio-capacity.md",
            "experimental_position_rule_cases.py",
        ):
            self.assertIn(required_name, readme)

    def test_v12_rule_text_fingerprint_is_unchanged(self):
        current = V12.read_text(encoding="utf-8")
        digest = sha256(canonical_rule_text(current).encode("utf-8")).hexdigest()
        self.assertEqual(V12_RULE_TEXT_SHA256, digest)

    def test_candidate_is_not_active_and_preserves_baselines(self):
        text = CANDIDATE.read_text(encoding="utf-8")
        self.assertRegex(text, r"文档状态：`CANDIDATE`")
        expectations = (
            "Setup B | `ACTIVE BASELINE`",
            "Setup A | `SHADOW`",
            "Setup C | `SHADOW（DEFER）`",
            "Trend Hold | `SHADOW`",
            "NORMAL 市场过滤 | `ACTIVE BASELINE`",
            "EXPERIMENTAL | `ACTIVE BASELINE`",
            "RED | `ACTIVE BASELINE`",
            "禁止亏损补仓 | `ACTIVE BASELINE`",
            "普通盈利加仓 | `CANDIDATE（DEFER）`",
        )
        for expectation in expectations:
            self.assertIn(expectation, text)
        self.assertIn("本文不是正式实盘系统", text)
        self.assertIn("正式系统持续为 v1.2", text)

    def test_adr_requires_human_decision(self):
        text = ADR.read_text(encoding="utf-8")
        self.assertRegex(text, r"状态：`CANDIDATE`")
        self.assertIn("决议状态：等待人工确认", text)
        self.assertIn("方案 A：采纳", text)
        self.assertIn("方案 B：不采纳", text)
        self.assertIn("两个方案都不改变 ACTIVE 规则", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
