"""Render the frozen experiment's outcomes; never used in AI preparation."""
import argparse
from pathlib import Path
from statistics import mean
import xml.etree.ElementTree as ET

from stock_cn.experiments import require_all_decisions_locked
from stock_cn.performance import comparison_markdown
from stock_cn.simulation import Store, read_json


def render(repo, experiment_id):
    root = repo / 'runs/experiments' / experiment_id
    manifest = read_json(root / 'manifest.json')
    require_all_decisions_locked(repo, manifest)
    comparison = read_json(root / 'comparison.json')
    rows = comparison['rows']
    accepted = [x['variant'] for x in comparison['variant_summary']
                if x['result'] == 'OBSERVED_IMPROVEMENT_WITHOUT_WORSE_DRAWDOWN']
    scored = sum(a['score']['status'] == 'SCORED' for r in rows for a in r['arms'].values())
    unavailable = sum(a['score']['status'] == 'DECISION_UNAVAILABLE' for r in rows for a in r['arms'].values())
    fills = sum(a['execution']['status'] == 'FILLED' for r in rows for a in r['arms'].values())
    def pct(value):
        return '—' if value is None else f'{float(value):+.4f}%'
    observations = []
    for variant in accepted:
        cases = [r for r in rows if r['variant'] == variant and r['phase'] == 'HOLDOUT']
        before = mean(float(r['arms']['baseline']['score']['actual_return_pct']) for r in cases)
        after = mean(float(r['arms']['candidate']['score']['actual_return_pct']) for r in cases)
        description = '减亏，仍未盈利' if after < 0 else '有限样本收益提升'
        observations.append(f'{variant}两段独立留出平均从{pct(before)}变为{pct(after)}，属于{description}。')
    worse_returns = [s['variant'] for s in comparison['variant_summary'] if
                     s['mean_holdout_return_change_percentage_points'] is not None and
                     float(s['mean_holdout_return_change_percentage_points']) < 0]
    more_risk = [s['variant'] for s in comparison['variant_summary'] if
                s['mean_holdout_return_change_percentage_points'] is not None and
                float(s['mean_holdout_return_change_percentage_points']) > 0 and s['any_holdout_drawdown_worse']]
    if worse_returns:
        observations.append('、'.join(worse_returns) + '候选收益更差。')
    if more_risk:
        observations.append('、'.join(more_risk) + '候选收益略升但回撤增大，未通过要求。')
    pytest_path = repo / f'runs/simulations/{experiment_id}-validation/pytest.xml'
    test_note = '尚无最终回归记录。'
    if pytest_path.exists():
        suites = list(ET.parse(pytest_path).iter('testsuite'))
        tests = sum(int(s.attrib['tests']) for s in suites)
        failures = sum(int(s.attrib['failures']) + int(s.attrib['errors']) for s in suites)
        test_note = f'最终回归{tests}项，失败或错误{failures}项。'
    lines = ['# 2026年A–E测试与改进报告', '',
        f'已完成12个现有变体、原版与候选两组、三个历史时点的72项真实AI判断锁定。可评分{scored}项，资料不足{unavailable}项，模拟成交{fills}笔。', '',
        '候选通过本轮“两段留出平均收益提升且任一留出日频回撤不恶化”要求的变体：' + ('、'.join(accepted) if accepted else '无') + '。这是本次有限样本的观察，正式与默认模拟提示词均未切换。', '',
        '## 范围与口径', '',
        '- A01–A03、C01–C03、D01–D03、E01–E03全部尝试；B为RESERVED，没有变体、账户或可测试提示词。',
        '- 2026真实价格覆盖1月5日至9月30日，181个交易日。D/E只研究事先确定的10股候选池；A/C使用原5股固定池。不能称全A股回测。',
        '- 开发点：1月9日→3月17日；留出点：4月30日→7月2日、7月31日→9月29日。每个点独立20万元，前收盘判断、下一交易日开盘代理成交，随后保持账户。每段资本间隔41个交易日，不能相乘或拼成年内连续实绩。',
        '- 使用现有完整策略意图与共同交易校验/费用/T+1核心。候选仅加资金配置、持仓理由及现金机会成本复核，不设置买卖阈值、不强迫交易或满仓。全部候选在评分前冻结，所有判断先锁定，再打开后续价格评分。',
        '- 年化=(1+区间收益)^(252/41)-1，仅为数学换算，不是下一年收益预测。总收益扣模拟交易费用，包含官方核实的现金红利权益及统一20%红利税款保守预留；另保留预留前收益。这不代表真实个人股息税已结算。',
        '- HOLD基准为保持相同隔离期初账户，包含同口径红利。A基准保留五股；C/D/E基准为现金，不能当沪深指数收益。超额收益为相同起点收益差的百分点。',
        '- 单点买入后未卖出不能计算已实现胜率；A假定期初持股也没有真实历史取得成本。因此胜率保留为空。资料不足不填0%收益，不冒充HOLD。',
        '- 输入与来源时间通过锁定及历史前缀核对。历史新闻默认忽略；两份4月30日只有日期精度的长电、大秦报告被扣除，无法证明收盘前公开。模型训练知识及固定池幸存者偏差仍无法完全消除。', '',
        '## 两段留出对照', '',
        ''.join(observations), '',
        '下表只比较两段均可评分的变体。独立点收益取算术平均，回撤列为两段中较大值，不是连续账户回撤。', '',
        '|变体|可比留出点|原版平均收益|候选平均收益|提升（百分点）|原版最大回撤|候选最大回撤|本轮结论|',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for summary in comparison['variant_summary']:
        cases = [r for r in rows if r['variant'] == summary['variant'] and r['phase'] == 'HOLDOUT']
        valid = [r for r in cases if r['comparable']]
        complete = len(valid) == len(cases)
        def arm_mean(arm):
            return mean(float(r['arms'][arm]['score']['actual_return_pct']) for r in valid) if complete else None
        def arm_dd(arm):
            return max(float(r['arms'][arm]['score']['max_daily_drawdown_pct']) for r in valid) if complete else None
        label = ('观察到收益改善且回撤未恶化' if summary['variant'] in accepted else
                 '未通过收益/回撤要求' if complete else '资料不足，不能验证改善')
        change = summary['mean_holdout_return_change_percentage_points']
        delta = '—' if change is None else f'{float(change):+.4f}'
        lines.append(f"|{summary['variant']}|{len(valid)}/{len(cases)}|{pct(arm_mean('baseline'))}|{pct(arm_mean('candidate'))}|"
                     f"{delta}|{pct(arm_dd('baseline'))}|{pct(arm_dd('candidate'))}|{label}|")
    lines += ['', '## 完整结果', '', '开发点与留出点分别列出；原版、候选各自保留账户、输入、决定和评分。', '']
    for arm, label in (('baseline', '原版'), ('candidate', '候选')):
        metric_rows = read_json(repo / f'runs/evaluations/{experiment_id}-{arm}/comparison.json')
        lines += [f'### {label}', '', comparison_markdown(metric_rows), '']
    lines += ['## 修改文件', '',
        '|文件或目录|修改用途|', '|---|---|',
        '|src/stock_cn/evaluation.py、experiments.py|按锁定提示词执行与评分、两组完整锁定门禁、候选冻结与留出比较|',
        '|src/stock_cn/point_dividends.py|官方纯现金红利权益、登记日股数、除息应收与税款假设|',
        '|src/stock_cn/prompt_payload.py|完整JSON无损共享编码与解码|',
        '|src/stock_cn/evidence.py、research_bundle.py、research_inputs.py|完整财报识别、来源/事实披露时间校验、独立研究目录|',
        '|src/stock_cn/sim_data.py、universe.py|保留接口权益标记，避免现金分红被静默丢弃|',
        '|src/stock_cn/simulation.py、sim_variants.py、time_travel.py|同核提示词选择、可选无损渲染、连续权益阻止与目录隔离检查|',
        '|tools/run_2026_experiment.py、lock_experiment_choices.py、report_2026_experiment.py、run_evaluation_plan.py|2026准备/评分、人工AI选择文件锁定、报告生成与来源防覆盖|',
        '|tests/、.github/workflows/simulation-validation.yml|时间边界、候选隔离、权益、压缩、目录与重复运行回归及触发路径|',
        '|strategies/*/variants/*/experiment-prompts、improvements、simulations|完整实验提示词、累计轮次与隔离模拟档案|',
        '|research-inputs/ae-2026-v3、runs/experiments、runs/evaluations、evaluation-answers、reports/performance|因果研究、锁定判断、来源哈希、评分与统一结果|',
        '|README.md、docs/time-travel.md、docs/simulation-guide.md|真实能力、口径、运行方式和未完成边界|', '',
        '## 缺口与回归', '',
        'E02需要财报外经营先行证据，E03需要行业供需、库存、价差等同期证据；仅有季度财务和个股K线不能冒充这些资料。其余状态与具体反证见锁定判断。', '',
        '首次v1输入因重复字段超预算而在AI阶段前失败；v2因同日披露日期精度问题在评分前撤回。旧输入、判断与失败记录全部保留。v3对未受影响的已锁定判断核对因果资料等价后导入，并记录来源哈希；受影响日期使用修正输入重新判断。三个准备轮次均消耗原有改进预算，累计不超过10轮。', '',
        '回归覆盖完整压缩输入的未来尾部不变性、财报/事实时间、同日日期精度拒绝、所有判断锁定后才读结果、提示词及锁定篡改拒绝、官方纯现金红利估值、登记日权益、税款假设冻结、重复评分/恢复、模拟与正式预览同核以及账户隔离。测试证据见 runs/simulations/ae-2026-v3-validation/，源数据与报告原文件存放在仓库外。', '',
        test_note + '首次完整回归出现一次Windows并发目录边界拒绝，单独复测通过；保留失败记录，随后将目录核验锚定到已存在父目录并补测试中间目录/账户链接逃逸，最终完整回归通过。未声称已稳定复现该偶发问题的根因。研究目录另增加整批写前一致性检查和已锁决定前置拒绝，误重跑不得覆盖旧研究来源。', '',
        '本轮支持评估这些独立历史判断，尚不能证明全年每天决策或未来稳定收益；连续账户的分红/送转处理仍需完善。', '']
    Store(repo / 'reports/performance').write('ae-2026.md', '\n'.join(lines))
    return {'scored': scored, 'unavailable': unavailable, 'fills': fills, 'observed_improvement': accepted}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', default='.')
    parser.add_argument('--experiment-id', default='ae-2026-v3')
    args = parser.parse_args()
    print(render(Path(args.repo).resolve(), args.experiment_id))
