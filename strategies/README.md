# 独立变体入口

系列仅分类；每个变体独立提示词、初始化与账户。当前均未正式启用。

|变体|完整基线提示词|新模拟使用的完整版本|独立持仓|初始化|改进计数|
|---|---|---|---|---|---|
|A01|[完整基线](A/variants/A01/prompt.md)|[当前模拟版](A/variants/A01/prompt.md)|[holdings](A/variants/A01/holdings.json)|[init](A/variants/A01/init.json)|[最多10轮](A/variants/A01/improvement_state.json)|
|A02|[完整基线](A/variants/A02/prompt.md)|[当前模拟版](A/variants/A02/prompt_versions/v001.md)|[holdings](A/variants/A02/holdings.json)|[init](A/variants/A02/init.json)|[最多10轮](A/variants/A02/improvement_state.json)|
|A03|[完整基线](A/variants/A03/prompt.md)|[当前模拟版](A/variants/A03/prompt.md)|[holdings](A/variants/A03/holdings.json)|[init](A/variants/A03/init.json)|[最多10轮](A/variants/A03/improvement_state.json)|
|C01|[完整基线](C/variants/C01/prompt.md)|[当前模拟版](C/variants/C01/prompt.md)|[holdings](C/variants/C01/holdings.json)|[init](C/variants/C01/init.json)|[最多10轮](C/variants/C01/improvement_state.json)|
|C02|[完整基线](C/variants/C02/prompt.md)|[当前模拟版](C/variants/C02/prompt.md)|[holdings](C/variants/C02/holdings.json)|[init](C/variants/C02/init.json)|[最多10轮](C/variants/C02/improvement_state.json)|
|C03|[完整基线](C/variants/C03/prompt.md)|[当前模拟版](C/variants/C03/prompt.md)|[holdings](C/variants/C03/holdings.json)|[init](C/variants/C03/init.json)|[最多10轮](C/variants/C03/improvement_state.json)|
|D01|[完整基线](D/variants/D01/prompt.md)|[当前模拟版](D/variants/D01/prompt.md)|[holdings](D/variants/D01/holdings.json)|[init](D/variants/D01/init.json)|[最多10轮](D/variants/D01/improvement_state.json)|
|D02|[完整基线](D/variants/D02/prompt.md)|[当前模拟版](D/variants/D02/prompt.md)|[holdings](D/variants/D02/holdings.json)|[init](D/variants/D02/init.json)|[最多10轮](D/variants/D02/improvement_state.json)|
|D03|[完整基线](D/variants/D03/prompt.md)|[当前模拟版](D/variants/D03/prompt.md)|[holdings](D/variants/D03/holdings.json)|[init](D/variants/D03/init.json)|[最多10轮](D/variants/D03/improvement_state.json)|
|E01|[完整基线](E/variants/E01/prompt.md)|[当前模拟版](E/variants/E01/prompt.md)|[holdings](E/variants/E01/holdings.json)|[init](E/variants/E01/init.json)|[最多10轮](E/variants/E01/improvement_state.json)|
|E02|[完整基线](E/variants/E02/prompt.md)|[当前模拟版](E/variants/E02/prompt.md)|[holdings](E/variants/E02/holdings.json)|[init](E/variants/E02/init.json)|[最多10轮](E/variants/E02/improvement_state.json)|
|E03|[完整基线](E/variants/E03/prompt.md)|[当前模拟版](E/variants/E03/prompt.md)|[holdings](E/variants/E03/holdings.json)|[init](E/variants/E03/init.json)|[最多10轮](E/variants/E03/improvement_state.json)|
|F01|[完整基线](F/variants/F01/prompt.md)|[当前模拟版](F/variants/F01/prompt.md)|[holdings](F/variants/F01/holdings.json)|[init](F/variants/F01/init.json)|[最多10轮](F/variants/F01/improvement_state.json)|

历史回放账户在各变体simulations/<test_id>/内，互不混用。旧系列根持仓文件仅作迁移前记录，不再参与执行。

改进后的完整候选放improvements/best_prompt.md及prompt_versions/，不自动启用正式版本。

[运行说明](../docs/variant-execution.md)
