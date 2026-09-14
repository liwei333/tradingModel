# WP-V13-02｜Historical Regime 与 T_OVERLAY 审计及 Candidate 落地报告

审计日期：2026-09-14
审查基线：`ae60122fade25236b176d7a93c70a3a443f33dee`（master / origin/master）
正式 v1.2 审查前 SHA-256：`149a8d410f536c4fe4198d13858e0ae9541240fe935284ae77ae27c2a0077688`
报告状态：`CANDIDATE`
实盘权限影响：`NO`

## 1. 仓库现状

当前唯一正式交易系统是[个人交易系统 v1.2](./last/个人交易系统_v1.2_基于ThesisGuard_v1.3.md)，组件状态为 `ACTIVE`。当前交易模型文档是[ThesisGuard v1.3 个人适配草案](./last/ThesisGuard_个人交易模型_v1.3_个人适配草案.md)，正文仍为候选性质。下一系统版本集中在[个人交易系统 v1.3 Candidate](./IterationRecord/个人交易系统_v1.3_产业趋势波段版_CANDIDATE.md)，没有第二份并行 Candidate。

审查开始时，工作树中的 6 份非模型/系统文档物理位置与 HEAD、README 和 `AGENTS.md` 所规定的一级目录位置不一致，导致既有 51 项 unittest 中 3 项版本治理测试失败。已将验证计划、审计、验收、评估和风险卡恢复到一级目录；它们的正文规则未因目录恢复改变。`last/` 仍只包含当前模型与正式 v1.2；`IterationRecord/` 仍只包含历史/候选模型、系统及索引。

## 2. Historical Regime 审计

```text
Historical Regime Study：ADD（SHADOW）
模块性质：Research Context + Holding Context
次要用途：Trend Hold 验证分层
正式准入影响：NONE
```

它有真实价值，因为当前系统能定义 Setup B 和风险，却没有统一记录“个股在不同产业阶段的波动、回撤、筑底时长与趋势恢复行为”。它主要减少两个问题：把该股正常的高波动误当成所有股票的通用噪声，以及只凭一张当前图主观类比历史。

它也会显著增加过拟合风险。事后选择周期、只统计最终恢复的回撤、用后来年报解释早期行情、挑最像的一段以及把历史支撑当成当前支撑，都会产生 hindsight bias 和 regime mismatch。解决办法不是让 Historical Regime 变成新门禁，而是强制 cutoff、AvailableAt、分类版本、事后切分标识、无效比较原因、UNKNOWN 和未见 20/60 日验证。

独立判断是：Historical Regime 不应直接决定“可以买/不能买”。它不能覆盖 Thesis、Setup、RED、AccountRiskState、S0、RR、Position Size、EXIT_PENDING 或逻辑退出。若最终只产生“感觉像 2019”之类不可复现描述，应拒绝该模块，而不是继续增加字段。

## 3. T_OVERLAY 审计

```text
T_OVERLAY：ADD（SHADOW）
初始方向：仅正 T SHADOW
反 T：DEFER
真实下单：PROHIBITED
未来 ACTIVE 讨论：DEFER，等待多证券历史与前瞻验证
```

T_OVERLAY 对该交易者只有有限适配性。它的潜在收益来源是明确整理区间内的均值回归，且必须在全部成本后改善整个 Campaign。券商成本价下降、交易次数增加和单次 T 盈利都不是有效收益来源。

最大风险依次是：卖出后错过核心主升、买入腿后第二腿失败造成战术库存、用“做 T”掩盖亏损补仓、为等待 T 解套延迟 Core 退出，以及更高的盘中决策负担。这些风险会直接削弱趋势持有能力，恰好击中该交易者止损和主观等待方面的短板。

正 T 先买战术股份、再卖昨日可卖底仓，较容易在日终保持战略数量；但仍有临时风险与第二腿失败。反 T 先卖 Core 后等待买回，突破时会直接丢失核心敞口，因此初始 Candidate 不纳入。25% Core 数量是保守主影子情景，50% 只按 v1.2 附录上限做敏感性对照；必须在至少 3 只证券、2 个独立整理期验证，不能根据兆易创新拟合。

## 4. 与 v1.2 冲突分析

| 冲突点 | 结论与处理 |
|---|---|
| Historical Regime 与 Setup B | Historical 不形成第二套买点；Setup B 继续是 ACTIVE BASELINE |
| Historical 回撤与 S0/退出 | 历史回撤分布不能放宽 S0、下移保护价或延迟 EXIT_PENDING |
| T 与 Trend Hold | Core 真实保护、逻辑退出和账户退出优先；反 T DEFER，正 T 期末战略数量必须恢复 |
| T 与“不加仓” | 战术买入腿是临时新增风险，必须独立受限；日终数量增加即执行失败，不得改名 Core |
| T 与亏损补仓 | Core 浮亏或拟买价不高于 Entry0 时，初始 Shadow 判 `AVERAGING_DOWN_RISK` |
| T 与 EXPERIMENTAL | EXPERIMENTAL 禁止 T；一次升级不自动取得 T 资格 |
| T 与 RED | RED 撤销未开 T 并禁止新买腿；只允许闭合、降低风险或服从 Core 退出 |
| T 与 AccountRiskState | 仅 NORMAL 可进入影子资格；WARNING、CONTRACTED、RECOVERY、PAUSED、UNKNOWN 不新开 |
| T 与 T+1 | 只能卖券商确认的昨日可卖批次；未知即跳过；当日新买股份在 Core 退出时保持 EXIT_PENDING 到首个可卖时点 |
| T 与核心统计 | OriginalEntry、OriginalR0、OriginalS0、Thesis、CampaignStartDate 均不可重置；TTradeID 独立记账 |

本轮没有修改 v1.2 正文、数值阈值、Setup B、真实退出、账户风控或统计含义。

## 5. 与 v1.3 Candidate 关系

遵照单一候选规则源的治理要求，没有创建第二份 v1.3 系统文档。现有 Candidate 从 `v1.3-candidate-1` 扩展为 `v1.3-candidate-2`，新增两节：Historical Regime 研究卡与 T_OVERLAY 正 T 影子状态机。

Setup B、NORMAL、EXPERIMENTAL、RED、账户风险和禁止亏损补仓继续引用 v1.2；Setup A/C、Trend Hold、Historical Regime、T_OVERLAY 都只保存在独立 SHADOW 账本。普通盈利加仓仍为 `CANDIDATE（DEFER）`，组合容量仍等待 ADR-001 人工决定。

## 6. 是否建议实施

建议实施**影子研究与验证基础设施**，不建议实施任何真实交易权限。

- Historical Regime 值得进入 v1.3 Candidate，因为它能把历史行为基准变成可审计语境；只有在 cutoff、版本、无效类比和 UNKNOWN 被强制记录时才保留。
- T_OVERLAY 值得进入 Shadow，因为问题能通过 CORE ONLY / CORE + T 配对验证回答；在净成本收益、临时风险、核心敞口、执行错误和时间负担证据出现前，不适合该交易者真实使用。
- 如果多证券验证不能证明增量信息，Historical Regime 应退回研究资料，T_OVERLAY 应 `REJECT` 或长期 `DEFER`，而不是为了功能完整升版。

## 7. 实际修改文件

修改：

- `AGENTS.md`：登记两个新 SHADOW 组件的治理事实。
- `README.md`：增加审计、案例、组件状态和测试入口。
- `IterationRecord/README.md`：更新唯一 v1.3 Candidate 的 SHADOW 模块说明。
- `IterationRecord/个人交易系统_v1.3_产业趋势波段版_CANDIDATE.md`：升级到 `v1.3-candidate-2`，加入 Historical Regime 与 T_OVERLAY。
- `v1.3_validation_plan.md`：加入两模块的数据表、字段、配对基线、压力情景和评审门槛。
- `tests/version_governance_cases.py`：把新文档、案例、测试和 Candidate 状态加入治理验收。

新增：

- `Historical_Regime_TOverlay_审计与实现报告_2026-09-14.md`
- `case_studies/兆易创新_603986_Historical_Regime_Study.md`
- `tests/historical_regime_rule_cases.py`
- `tests/t_overlay_rule_cases.py`

删除：0。`.gitignore` 未修改。正式 v1.2 与当前模型文档未修改。

## 8. 新增测试

`historical_regime_rule_cases.py` 覆盖：数据不足为 UNKNOWN、未来数据为 FAIL、无有效可比期允许 UNKNOWN、历史相似不能覆盖 Setup FAIL、RED 不可覆盖，以及完整研究仍不能产生 ALLOW。

`t_overlay_rule_cases.py` 覆盖：无 Core、Thesis 失效、EXIT_PENDING、RED、25%数量上限、独立风险上限、亏损状态的 Averaging Down 风险、Core 退出优先、期末战略数量异常、可卖数量 UNKNOWN、EXPERIMENTAL 禁止、成本后空间不正、组合风险和合法 SHADOW READY。

这些测试使用标准库、`Decimal` 和合成输入；不接行情、券商或真实订单，不证明策略盈利。

## 9. 测试结果

最终验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p '*_cases.py' -v
```

结果：`Ran 72 tests — OK`，0 failure、0 error。

同时通过：`git diff --check`、全仓库相对 Markdown 链接解析、Markdown 代码围栏配对、`last/` 与 `IterationRecord/` 目录边界。本机用户目录绝对 Markdown 链接剩余 0。正式 v1.2 审查后 SHA-256 仍为 `149a8d410f536c4fe4198d13858e0ae9541240fe935284ae77ae27c2a0077688`，与审查前一致。

测试通过只证明文档门禁和版本治理可重复，不证明净成本优势。

## 10. 仍未解决的问题

1. 尚无多证券、时点化的历史分类数据集，Historical Regime 的稳定性和增量信息未知。
2. 兆易创新案例使用当前下载的前复权序列；历史 cutoff 的原始复权因子和完整公告 `AvailableAt` 库尚未建立。
3. 产业指数、估值分位和共识预期的历史时点数据仍缺失，当前可比期置信度较低。
4. T_OVERLAY 的 20 日区间、下 1/4、30 分钟确认、中点目标和 25%主情景均未证明有效。
5. 最低佣金、印花税、券商可卖批次、拒单和迟到回报尚未用真实券商只读记录验证。
6. 反 T 的 CoreExposureLoss 只保留合成负例口径，不进入初始 Shadow 信号。
7. ADR-001 的 4 只股票容量与 Replacement PK 仍待人工确认。
8. 当前模型文件自身仍是草案状态，未被单独批准为 ACTIVE。

## 11. 哪些规则仍为 ACTIVE

- 正式交易系统 v1.2。
- Setup B、NORMAL 双指数市场过滤、EXPERIMENTAL、RED。
- v1.2 的单笔/组合/产业/现金/订单风险和 AccountRiskState。
- v1.2 当前真实价格、逻辑、账户退出与 T+1 异常处理。
- 禁止亏损补仓、禁止普通正常仓加仓、NORMAL 与 EXPERIMENTAL 不做 T。
- v1.2 已定义的一次 EXPERIMENTAL→NORMAL 升级。

这些是仓库组件状态；真实账户是否启用仍以启用登记和券商记录为准。

## 12. 哪些为 CANDIDATE

- `个人交易系统 v1.3 产业趋势波段版` 整体。
- 产业 Thesis 增强接口和 IndustryConfirm 设计。
- 普通盈利加仓议题，状态 `CANDIDATE（DEFER）`。
- ADR-001 的“最多 4 只／第 5 只 Replacement PK”，等待人工确认。
- Historical Regime 与 T_OVERLAY 的字段、状态机、验证和未来评审条件；这些 Candidate 定义的实际运行状态仍是 SHADOW。

## 13. 哪些为 SHADOW

- Setup A。
- Setup C（DEFER）。
- IndustryConfirm。
- Trend Hold。
- Historical Regime。
- T_OVERLAY：仅正 T 影子；反 T DEFER。

所有 SHADOW 只记录，不下单，不改变真实保护价，不重写历史 TradeID/R0/Thesis，不占用或释放 v1.2 的真实风险与实验槽位。

本次修改是否改变当前真实交易权限：NO
