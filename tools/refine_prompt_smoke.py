"""One structural prompt improvement, not an AI-return/statistical-model test."""
from pathlib import Path
from stock_cn.variant_prompts import PromptLab, read, stable_patch, validate_prompt, write

repo = Path(__file__).resolve().parents[1]
root = repo / 'strategies/A/variants/A02'
state = read(root / 'improvement_state.json')
if state['rounds_used'] == 0:
    baseline = (root / 'prompt.md').read_text(encoding='utf-8')
    def evaluate(candidate):
        validate_prompt(candidate, baseline)
        return {'purpose': 'STABILITY', 'passed': True, 'level': 'STRUCTURAL_CONTRACT_ONLY',
                'real_model_repetition_tested': False, 'uses_future_returns': False}
    result = PromptLab(repo, 'A02').run(stable_patch, evaluate,
        ['STRICT_JSON', 'IDENTITY', 'NONREADY', 'CAUSALITY', 'PROVENANCE'], max_rounds=10)
    write(root / 'improvements/summary.json', result)
    print(result)
else:
    print('Existing improvement counter retained; no unnecessary repeat or reset.')
