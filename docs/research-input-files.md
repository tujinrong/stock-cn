# 决策研究输入文件格式

用途：把AI对财务/新闻的研究结果，以可审计文件形式交给正式或模拟决策流程。文件是研究输入，不是交易授权。

建议目录（每个变体、每个决策日独立）：

```text
research-inputs/
  <variant_id>/
    YYYY-MM-DD/
      financial-reviews.json
      news-research.json
      official-disclosure-pack.json   # 可引用runs/research/evidence中的已核实元数据
      candidate-research-pack.json
      universe-scope.json
      manifest.json
```

## financial-reviews.json

顶层为股票代码到复核对象的映射。

```json
{
  "600036.SH": {
    "status": "REVIEWED",
    "symbol": "600036.SH",
    "as_of": "2026-10-08T10:50:00+08:00",
    "source_report": "https://static.cninfo.com.cn/...PDF",
    "source_official": true,
    "period": "2026H1",
    "facts": [
      {
        "name": "营业收入",
        "value": "...",
        "source": "2026年半年度报告第X页/对应表格"
      }
    ],
    "summary": "AI对已披露财务资料的简短综合解释",
    "data_gaps": []
  }
}
```

要求：

- `status` 必须是 `REVIEWED` 才算完成；
- `as_of` 不能晚于决策时点；
- `source_report` 必须是实际阅读的报告；
- `source_official=true`；
- 每个事实必须有来源；
- 不允许把媒体转述冒充正式财报事实；
- 缺口写入 `data_gaps`。

## news-research.json

```json
{
  "status": "SEARCHED",
  "searched_at": "2026-10-08T10:55:00+08:00",
  "items": [
    {
      "symbols": ["600036.SH"],
      "title": "...",
      "published_at": "2026-10-08T09:00:00+08:00",
      "source": "...",
      "url": "...",
      "material_fact": false,
      "official_recheck_status": null
    }
  ]
}
```

允许状态：

- `SEARCHED`
- `NO_RELEVANT_RECENT_NEWS`
- `UNAVAILABLE`
- `NOT_CHECKED`

前两者才算近期新闻已核验。后两者只是数据缺口。

若 `material_fact=true`，必须给出 `official_recheck_status`，例如：

- `CONFIRMED_BY_OFFICIAL_DISCLOSURE`
- `NO_MATCHING_OFFICIAL_DISCLOSURE_FOUND`
- `OFFICIAL_RECHECK_UNAVAILABLE`

程序不根据该字段自动判断利好/利空，只用于证据可信度和缺口提示。

## manifest.json

记录本次研究输入的身份：

```json
{
  "variant_id": "D02",
  "mode": "FORMAL",
  "decision_date": "2026-10-08",
  "information_cutoff": "2026-10-08T11:00:00+08:00",
  "source_commit": "...",
  "formal_execution": false,
  "note": "research input only"
}
```

研究文件和账户文件分离。修改研究输入不能直接改变持仓；只有随后通过AI决策契约、交易前置核验和Paper成交规则后，账户才会变化。
