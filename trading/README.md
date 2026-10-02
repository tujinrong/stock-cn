# 正式模拟交易文件

本目录只用于获授权的正式Paper Trading，不是真实券商交易。**目前只有说明文件，没有已开账户、成交或收益。**

策略确认并实际运行后按策略资金池建立 A/、B/ 等，包含 account.json、events/、prompts/ 与 daily/YYYY-MM-DD/。同系列不同变体不能各自盲写一个正式账户。

用户看 daily/.../summary.md 理解当日为什么买卖或不操作；看 result.json 核对订单/成交，closing.json 看净值与估值时点，prompts/<run_id>.md 看当时使用的完整项目投资提示词。

已提交事件是事实，账户与报表为可重建视图。一次决策相关文件一致提交；重试按唯一ID去重。历史修订保留原记录，不追补不存在的交易。未运行、数据失败和AI判断HOLD分开。

不保存原始行情库，不导入用户真实股票账户、真实成本、个人信息或密钥。字段与并发保障见 [file-layout](../docs/file-layout.md)。
