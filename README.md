# ThesisGuard 个人交易模型与交易系统

当前最新交易系统文档是 [个人交易系统 v1.2：正常仓与实验仓分轨执行版](/Users/qianduoduo/Desktop/AI_app/tradingModel/个人交易系统_v1.2_基于ThesisGuard_v1.3.md)，编制于2026-09-14。本次以模型v1.3和系统v1.1为修订基线；“最新文档”不表示账户已经启用、已提交交易，或实验规则已被证明有效。

| 文件 | 用途与版本关系 |
|---|---|
| [模型 v1.3](/Users/qianduoduo/Desktop/AI_app/tradingModel/ThesisGuard_个人交易模型_v1.3_个人适配草案.md) | 当前模型依据；固定六维权重20/25/20/15/10/10；原文保留 |
| [系统 v1.2](/Users/qianduoduo/Desktop/AI_app/tradingModel/个人交易系统_v1.2_基于ThesisGuard_v1.3.md) | 最新执行与风控文档；第1—11节为共同规则及NORMAL基线，第12节为实验仓；附录A包含四张可复制表 |
| [实验仓验收案例](/Users/qianduoduo/Desktop/AI_app/tradingModel/实验仓_v1.2_验收案例.md) | 8个必测案例、36项边界清单、测试范围与结果 |
| [合成规则验收脚本](/Users/qianduoduo/Desktop/AI_app/tradingModel/tests/experimental_position_rule_cases.py) | 标准库测试；仅检查给定门禁状态、风险算术与若干转换不变量，不接行情或券商 |
| [系统 v1.1](/Users/qianduoduo/Desktop/AI_app/tradingModel/个人交易系统_v1.1_基于ThesisGuard_v1.3.md) | 本次完整修订基线，保留供对照 |
| [系统 v1.0](/Users/qianduoduo/Desktop/AI_app/tradingModel/个人交易系统_v1.0_基于ThesisGuard_v1.3.md)与[审查报告](/Users/qianduoduo/Desktop/AI_app/tradingModel/个人交易系统_v1.0_审查与优化建议_2026-09-14.md) | 历史材料，不能与v1.2混用参数 |
| [生益科技旧仓风险卡](/Users/qianduoduo/Desktop/AI_app/tradingModel/生益科技_持仓风险卡_2026-09-14.md) | 独立旧仓历史快照；本次未修改，也不自动改成实验仓 |

使用时先查看v1.2第2节决策顺序，拟单填写附录A1，随后维护A2持仓订单表、A3账户账本与A4退出复盘。实验仓只允许市场过滤明确FAIL、其余全部条件通过的候选；评分缺锚点或证据UNKNOWN、市场RED、账户暂停及待退出订单都不能用小仓位豁免。当前仓库没有现实候选已核验的完整评分规约；真实申请前须按原六维模型补齐并冻结评分依据，不能拿合成80分测试数据代替证据。

规则优先级以每笔事前登记的版本为准。v1.2是对v1.3执行层的显式扩展；NORMAL原市场过滤和账户额度保留，实验70分、半预算及一次性升级按v1.2。外部技能若仍指向v1.1，只能作历史参照，不能覆盖此版本的实验规则。历史暂停、净值高点、原R0与既有订单不因换版重置。

合成验收可在项目目录执行：

```bash
python3 tests/experimental_position_rule_cases.py
```

新增内容均属于本次实验仓机制；不建立实盘自动交易程序。真实行情重演、券商执行验证和至少20笔独立完整实验样本的后续评估，需要另行积累记录。
