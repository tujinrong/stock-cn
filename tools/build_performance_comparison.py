"""Rebuild outcome summaries from saved scores, without reading market data or changing decisions."""
import argparse
from pathlib import Path
from stock_cn.evaluation import summarize
from stock_cn.simulation import Store, read_json
from stock_cn.performance import comparison_markdown


def build(repo):
    repo = Path(repo).resolve()
    rows = []
    for folder in sorted((repo / 'runs/evaluations').iterdir()):
        if not (folder / 'scores').is_dir():
            continue
        summarize(repo, folder.name)
        for row in read_json(folder / 'comparison.json'):
            row.update(eval_id=folder.name, source_path=f'runs/evaluations/{folder.name}/comparison.json')
            rows.append(row)
    Store(repo).write('reports/performance/comparison.json', rows)
    # Each evaluation remains separate; overlapping samples are not independent.
    groups = []
    for eid in sorted({r['eval_id'] for r in rows}):
        groups.append(f'## {eid}\n\n' + comparison_markdown([r for r in rows if r['eval_id'] == eid and r['completed_days'] == 41]))
    Store(repo).write('reports/performance/comparison.md',
        '# 历史锁定判断统一比较\n\n仅比较点决策后保持账户的结果，不是40日连续每日AI回放。旧评分的40日标签从成交日起后移40日，资本起点为前一日收盘，年化实际分母41。旧记录无每日净值时回撤留空，胜率无平仓配对时留空。重复历史时点不拼接、不重复当作独立样本。候选池不是全A股，未来数据检查仅覆盖输入锁定及历史前缀；模型训练知识无法完全排除。\n\n' + '\n'.join(groups))
    return rows


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',default='.')
    args=parser.parse_args()
    rows=build(args.repo)
    print(f'{len(rows)} scored/attempted horizon rows; {len({r["variant"] for r in rows})} variants')
