"""Idempotently materialize complete variant files and route the simulation CLI.

Does not initialize formal accounts or modify existing simulation history.
"""
from pathlib import Path
from stock_cn.variant_prompts import materialize, read, write

repo = Path(__file__).resolve().parents[1]
registry = materialize(repo)
cli_path = repo / 'src/stock_cn/sim_cli.py'
text = cli_path.read_text(encoding='utf-8')
marker = 'from .sim_variants import VariantSimulation as Simulation'
if marker not in text:
    anchor = 'from .simulation import Simulation, Store, ValidationError, digest, dumps, identifier, read_json, require'
    if anchor not in text:
        raise RuntimeError('CLI changed; refusing blind source rewrite')
    text = text.replace(anchor, anchor + '\n' + marker)
    old = 'root = repo / "strategies" / variant[0] / "simulations" / test_id / variant'
    new = 'root = repo / "strategies" / variant[0] / "variants" / variant / "simulations" / test_id'
    text = text.replace(old, new)
    text = text.replace('require(root.resolve().is_relative_to(repo / "strategies" / variant[0] / "simulations"), "path escape")',
                        'require(root.resolve().is_relative_to(repo / "strategies" / variant[0] / "variants" / variant), "path escape")')
    text = text.replace('for pat in ("strategies/*/holdings.json",', 'for pat in ("strategies/*/variants/*/holdings.json", "strategies/*/variants/*/holdings.md", "strategies/*/variants/*/init.json", "strategies/*/holdings.json",')
    write(cli_path, text)
rows = ['# 独立变体入口', '', '系列仅分类；每个变体独立提示词、初始化与账户。当前均未正式启用。', '',
        '|变体|完整基线提示词|新模拟使用的完整版本|独立持仓|初始化|改进计数|', '|---|---|---|---|---|---|']
for item in registry:
    v = item['variant_id']; p = f'{v[0]}/variants/{v}'
    pointer = read(repo / 'strategies' / p / 'simulation_prompt.json')
    rows.append(f"|{v}|[完整基线]({p}/prompt.md)|[当前模拟版]({p}/{pointer['path']})|[holdings]({p}/holdings.json)|[init]({p}/init.json)|[最多10轮]({p}/improvement_state.json)|")
rows += ['', '历史回放账户在各变体simulations/<test_id>/内，互不混用。旧系列根持仓文件仅作迁移前记录，不再参与执行。',
         '', '改进后的完整候选放improvements/best_prompt.md及prompt_versions/，不自动启用正式版本。',
         '', '[运行说明](../docs/variant-execution.md)']
write(repo / 'strategies/README.md', '\n'.join(rows) + '\n')
ag = repo / 'AGENTS.md'
text = ag.read_text(encoding='utf-8')
text = text.replace('每系列计划独立20万元总资产。', '每个变体计划独立20万元总资产，系列仅作分类。')
text = text.replace('每系列1–5个参数或定性偏好变体。正式默认一个active_variant管理一个资金池；隔离对照测试可各有虚拟起点，不重复计算成正式出资。', '每系列1–5个参数或定性偏好变体；每个变体有独立完整提示词、资金和账户，可并行运行，不共用系列余额。')
text = text.replace('每系列/隔离账户每个市场交易日', '每变体/隔离账户每个市场交易日')
heading = '## 最新补充：独立变体与最多10轮提示词改进'
if heading not in text:
    text += '\n\n' + heading + '\n\n系列只作分类；每个变体是独立执行、独立20万元模拟起点、独立持仓和绩效的单位。多个变体可同时运行，不再限定每系列一个active_variant。正式账户仍未授权启用。\n\n每个变体的完整提示词、初始化和当前持仓位于strategies/<系列>/variants/<变体>/。旧系列根文件不再参与新执行；历史测试记录保留。模拟文件单独在该变体simulations/<test_id>/。\n\n每变体提示词稳定性改进累计最多10轮，失败及中断也计入，不因重启或换批次归零。保留完整旧新提示词、校验记录和计数；合格候选只供新隔离模拟，不自动正式升级。不以未来收益作为修订当天提示词的反馈。\n\n模拟每天均视后续变化未知：输入仅含截止时刻以前的价格、已公布财务和新闻；未来价格/新闻变化不得改变相同历史前缀的AI输入。提示词改进也不得使用后验价格、赢家或期末收益。模型预训练可能含后来知识，不能因此声称回放绝对无前视偏差。\n'
write(ag, text)
print(f'Materialized {len(registry)} independent variants; no formal account initialized.')
