# ThesisGuard 个人交易模型与交易系统

本仓库保存个人 A 股产业趋势波段交易的模型、正式系统、候选规则、验收材料与测试。仓库状态与账户运行状态分开管理：文件标为 `ACTIVE`，只表示它是仓库当前正式规则基线；是否已在真实账户启用，仍以交易系统中的启用登记和券商记录为准。

## 状态定义

| 状态 | 定义 | 是否能改变当前订单或持仓管理 |
|---|---|---|
| `ACTIVE` | 仓库当前正式规则或其正式验收基线 | 只有完成账户启用登记后，才进入真实账户执行 |
| `CANDIDATE` | 可审阅、可验证的下一版本候选；尚未获准替代正式规则 | 否 |
| `SHADOW` | 按冻结口径平行记录结果，不下单、不改变真实保护价 | 否 |
| `DEPRECATED` | 已停止用于新记录或新交易；保留兼容说明时使用 | 否 |
| `HISTORICAL` | 历史版本、审查或研究记录，仅供追溯 | 否 |

`DEFER` 是排期决定，不是生命周期状态。被延后的可计算模块标为 `SHADOW（DEFER）`；尚未建立影子记录口径的模块标为 `CANDIDATE（DEFER）`。

## 当前版本与验收入口

| 类别 | 文件 | 状态 | 版本关系与用途 |
|---|---|---|---|
| 当前正式交易模型 | 暂无独立标为 `ACTIVE` 的模型文件 | — | [ThesisGuard v1.3 个人适配草案](./last/ThesisGuard_个人交易模型_v1.3_个人适配草案.md)是系统 v1.2 引用的模型依据，但该文件自身明确为未自动生效的 `CANDIDATE`；系统 v1.2 已写入的六维权重与共同规则以系统正文为准 |
| 当前正式交易系统 v1.2 | [个人交易系统 v1.2：正常仓与实验仓分轨执行版](./last/个人交易系统_v1.2_基于ThesisGuard_v1.3.md) | `ACTIVE` | 当前唯一正式执行基线；Setup B、NORMAL、EXPERIMENTAL、RED、账户风控与退出均以本文为准 |
| v1.2 实验仓验收 | [实验仓 v1.2 验收案例](./实验仓_v1.2_验收案例.md) | `ACTIVE` | 记录 8 个必测案例、36 项文本边界及自动测试范围；不替代 v1.2 正文 |
| v1.2 产业趋势波段审计 | [v1.2 产业趋势中短期波段适配审计](./个人交易系统_v1.2_产业趋势中短期波段适配审计_2026-09-14.md) | `CANDIDATE` | 审计结论及 v1.3 建议来源；其中建议不自动生效 |
| v1.3 Candidate | [个人交易系统 v1.3 产业趋势波段版 Candidate](./IterationRecord/个人交易系统_v1.3_产业趋势波段版_CANDIDATE.md) | `CANDIDATE` | 建立下一版本框架；不替代 v1.2，不是正式实盘系统 |
| v1.3 验证计划 | [v1.3 validation plan](./v1.3_validation_plan.md) | `CANDIDATE` | 保存 A/B/C 信号、退出平行结果、MFE、MAE、Expectancy、Profit Factor 与 20/60 日结果 |
| 组合容量决议 | [ADR-001：主动股票容量与 Replacement PK](./decisions/ADR-001-portfolio-capacity.md) | `CANDIDATE` | 采纳与不采纳方案均待人工确认；当前不生效 |

当前模型治理存在一个已披露状态：模型 v1.3 文件名和正文均为草案，因此本轮不把它擅自标为 `ACTIVE`。正式系统 v1.2 已经明确引用并固化的模型规则继续有效；模型文件本身是否升为正式版本，需另行决议。

历史或候选的交易系统、交易模型文档统一收录在 [IterationRecord 迭代版本索引](./IterationRecord/README.md)，当前交易模型和正式交易系统统一放在 `last/`。README、验证计划、风险卡、审查、审计、验收、tests 和 ADR 等其他类型文件保持原有位置。

## v1.3 Candidate 的当前边界

| 模块 | 组件状态 | 本轮约束 |
|---|---|---|
| Setup B | `ACTIVE BASELINE` | 完整继承 v1.2，不改条件、预算、订单或退出规则 |
| Setup A | `SHADOW` | 只记录信号和假设成交，不下单 |
| Setup C | `SHADOW（DEFER）` | 只保留影子定义，暂缓实盘评估 |
| Trend Hold | `SHADOW` | 与 v1.2 当前退出平行计算，不改变真实保护价 |
| NORMAL 市场过滤 | `ACTIVE BASELINE` | 保持 v1.2 |
| EXPERIMENTAL | `ACTIVE BASELINE` | 保持 v1.2 |
| RED | `ACTIVE BASELINE` | 保持 v1.2 |
| 亏损补仓 | `ACTIVE BASELINE` | 继续禁止 |
| 普通盈利加仓 | `CANDIDATE（DEFER）` | 当前不建立实盘入口；v1.2 实验仓一次升级仍按其原规则处理 |
| 最多 4 只与第 5 只 Replacement PK | `CANDIDATE` | 仅在 ADR-001 讨论，未经人工确认不生效 |

## 历史版本与辅助材料

| 文件 | 状态 | 用途 |
|---|---|---|
| [ThesisGuard 模型 v1.2 可测量版](./IterationRecord/ThesisGuard_个人交易模型_v1.2_可测量版.md) | `HISTORICAL` | 原始模型基线 |
| [v1.2 适配评估与访谈记录](./ThesisGuard_v1.2_适配评估与访谈记录_2026-09-14.md) | `HISTORICAL` | 模型适配过程与已知限制 |
| [个人交易系统 v1.1](./IterationRecord/个人交易系统_v1.1_基于ThesisGuard_v1.3.md) | `HISTORICAL` | v1.2 的完整修订基线，不得与 v1.2 混用参数 |
| [个人交易系统 v1.0](./IterationRecord/个人交易系统_v1.0_基于ThesisGuard_v1.3.md) | `HISTORICAL` | 初始系统版本 |
| [v1.0 审查与优化建议](./个人交易系统_v1.0_审查与优化建议_2026-09-14.md) | `HISTORICAL` | v1.0 审查记录 |
| [生益科技旧仓风险卡](./生益科技_持仓风险卡_2026-09-14.md) | `ACTIVE` | 独立旧仓管理卡；是否启用仍以卡片与账户登记为准 |

## Tests

| 测试 | 状态 | 覆盖范围 |
|---|---|---|
| [experimental_position_rule_cases.py](./tests/experimental_position_rule_cases.py) | `ACTIVE` | v1.2 实验仓的合成门禁、风险算术、转换不变量；不接行情或券商 |
| [version_governance_cases.py](./tests/version_governance_cases.py) | `ACTIVE` | 版本文件、状态、相对链接、v1.2 规则文本指纹及 ADR 未生效约束 |

在项目根目录执行全部标准库测试：

```bash
python3 -m unittest discover -s tests -p '*_cases.py' -v
```

所有规则优先级以每笔交易事前登记的版本为准。历史暂停、净值高点、原始 R0、既有订单和已锁定退出事件不因阅读 Candidate、切换文档或运行测试而重置。
