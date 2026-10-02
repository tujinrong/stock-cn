# 调试与历史模拟入口

当前没有测试账户或回测成绩。按最新目录要求，本根目录只导航；实际测试数据放在各系列下面：

```text
strategies/<系列>/simulations/<test_id>/<variant_id>/
  manifest.json
  init.json
  holdings.json
  holdings.md
  events/
  daily/<虚拟市场日期>/
    ai_input.md
    holdings_before.json
    decision.json
    execution.json
    holdings_after.json
    closing.json
    summary.md
```

各变体有独立账户、初始化/提示词快照和连续日记录，不写回系列根下正式holdings.json。同一账户历史日期按顺序推进，不同系列/隔离变体可平行研究。初始20万元是虚拟实验资金，不重复计算正式出资。

优先真实历史行情及当时公开财务、公告、新闻，可回放几天、几周、两个月。缺分钟/历史版本须披露近似或降级，不用假数据报告真实收益；TEST_ONLY仅用于明确流程测试。

临时策略可以测试，但不自动转正式。微调重跑新test_id保留旧结果；报告实际完成范围和证据局限，不能将测试收益拼入正式净值。见[完整AI输入/当前账户入口](../strategies/README.md)和[AI契约](../docs/ai-decision-contract.md)。
