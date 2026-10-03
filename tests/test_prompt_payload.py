"""Lossless sharing never drops holdings, rules, provenance or causal facts."""
import copy
import json

import pytest

from stock_cn.prompt_payload import encode, decode, render_prompt_json


def payload():
    url = 'https://static.cninfo.com.cn/finalpage/2026-04-30/' + 'report-' * 12 + '.pdf'
    review = {
        'source': url, 'source_report': url, 'as_of': '2026-05-15T15:00:00+08:00',
        'facts': [{'name': 'operating_cash_flow', 'value': '123456789.00', 'source': url}],
        'data_gaps': ['A sourced fact is evidence, not an automatic purchase rule.'],
    }
    return {
        'context': {'date': '2026-05-15', 'cash_cny': '200000.00', 'rules': {'max_orders': 1}},
        'holdings': [{'symbol': '600036.SH', 'quantity': 100, 'sellable_quantity': 100}],
        'reviews': [copy.deepcopy(review) for _ in range(12)],
        'nested': {'report': review, 'lists': [[review], [review]]},
        'values': [None, True, False, 0, -12, 1.25, '', '中文事实'],
    }


def test_nested_roundtrip_shares_urls_and_large_nodes_without_mutating_input():
    value = payload()
    original = copy.deepcopy(value)
    document = encode(value)
    rendered = render_prompt_json(value)
    assert decode(json.loads(rendered)) == original
    assert decode(document) == original
    assert value == original
    assert len(document['source_urls']) == 1
    assert any(ref.startswith('n') for ref in document['__shared'])
    assert len(rendered) < len(json.dumps(value, ensure_ascii=False, separators=(',', ':'))) / 2
    url = value['reviews'][0]['source']
    assert rendered.count(url) == 1
    assert '200000.00' in rendered and 'max_orders' in rendered and 'sellable_quantity' in rendered


def test_literal_reference_fields_and_codec_registry_names_survive_collision():
    value = {
        '$ref': 'u001', '$literal': [['$ref', 'n001']],
        '$object': ['k001', [1, 2]], '$table': ['k001', [[1, 2]]],
        '__codec': 'source-owned', '__shared': {'s001': 'source-owned'},
        'source_urls': {'u001': 'source-owned'},
        'nested': [{'$ref': 'n001'}, {'$literal': [1, {'$ref': 's001'}]},
                   {'$ref': 'https://example.com/actual-source', 'fact': 0}],
        'url': 'https://example.com/actual-source',
    }
    assert decode(encode(value)) == value


def test_repeated_long_strings_and_nested_literal_nodes_are_lossless():
    text = 'source provenance ' * 30
    node = {'$ref': 'n001', 'fact': text, '$literal': {'unchanged': text}}
    value = [copy.deepcopy(node), copy.deepcopy(node), {'fact': text}]
    encoded = encode(value)
    assert any(ref.startswith('s') for ref in encoded['__shared'])
    assert any(ref.startswith('n') for ref in encoded['__shared'])
    assert decode(encoded) == value


def test_decoded_repeated_nodes_have_independent_mutable_state():
    original = payload()
    restored = decode(encode(original))
    restored['reviews'][0]['facts'][0]['value'] = 'changed'
    assert restored['reviews'][1]['facts'][0]['value'] == original['reviews'][1]['facts'][0]['value']


def test_unique_market_rows_share_schema_and_preserve_all_value_types():
    rows = [{'date': f'2026-01-{i:02d}', 'open': i, 'close': i + 0.5,
             'volume': str(i * 100), 'suspended': i == 2, 'missing': None}
            for i in range(1, 15)]
    value = {'daily': rows, 'field_fact': {'$object': 'ordinary fact'}}
    document = encode(value)
    assert '$table' in json.dumps(document)
    assert any(ref.startswith('k') for ref in document['__shared'])
    restored = decode(document)
    assert restored == value
    assert type(restored['daily'][0]['open']) is int
    assert type(restored['daily'][0]['close']) is float
    assert type(restored['daily'][0]['volume']) is str
    assert type(restored['daily'][0]['suspended']) is bool


@pytest.mark.parametrize('payload,registry,message', [
    ({'$object': ['k001', [1]]}, {'k001': ['one', 'two']}, 'does not match'),
    ({'$table': ['k001', [[1, 2]]]}, {'k001': ['same', 'same']}, 'field schema'),
    ({'$table': ['k001', 1]}, {'k001': ['one']}, 'table rows'),
    ({'$object': ['k001', [1]]}, {'k001': {'$ref': 'n001'},
                               'n001': {'$object': ['k001', [1]]}}, 'cyclic'),
])
def test_schema_shape_mismatch_and_cycles_are_rejected(payload, registry, message):
    document = encode({})
    document['payload'] = payload
    document['__shared'] = registry
    with pytest.raises(ValueError, match=message):
        decode(document)


def test_future_dataset_changes_do_not_change_encoding_of_same_prefix():
    prefix = payload()
    one = {'visible': copy.deepcopy(prefix), 'future': {'price': 42, 'news': 'later announcement'}}
    two = copy.deepcopy(one)
    two['future'] = {'price': 999999, 'news': 'future winner secret', 'url': 'https://future.example.com'}
    expected = render_prompt_json(one['visible'])
    render_prompt_json(two)  # An unrelated invocation cannot pollute a global registry.
    assert expected == render_prompt_json(two['visible'])
    assert 'future winner secret' not in render_prompt_json(two['visible'])


def test_time_travel_prefix_encoding_is_invariant_to_future_ohlcv_and_news():
    from test_evaluation import history
    from stock_cn.time_travel import build_time_travel_context
    one = history()
    two = copy.deepcopy(one)
    target = one['sessions'][8]
    for day in two['sessions'][9:]:
        for bar in two['bars'][day].values():
            bar.update(open='900.00', close='901.00', high='902.00', low='899.00', volume='999999999')
    two['evidence'] = [{'published_at': '2025-12-31T15:00:00+08:00',
                        'source': 'TEST_ONLY', 'text': 'future winner secret'}]
    before = build_time_travel_context(one, target, target)
    after = build_time_travel_context(two, target, target)
    assert render_prompt_json(before) == render_prompt_json(after)
    assert decode(encode(after)) == before


@pytest.mark.parametrize('value', [None, True, 0, -1.5, 'plain', [], {}, 'https://example.com/source'])
def test_top_level_json_values_roundtrip(value):
    assert decode(encode(value)) == value


@pytest.mark.parametrize('value', [float('nan'), float('inf'), (1, 2), {1: 'non-string key'}])
def test_non_json_or_lossy_inputs_are_rejected(value):
    with pytest.raises(ValueError):
        encode(value)


def test_input_cycles_are_rejected():
    value = []
    value.append(value)
    with pytest.raises(ValueError, match='cycle'):
        encode(value)


@pytest.mark.parametrize('mutation,message', [
    (lambda d: d.update(payload={'$ref': 'missing'}), 'missing'),
    (lambda d: d['__shared'].update(n999={'$ref': 'n999'}), 'cyclic'),
    (lambda d: d.update(payload={'$ref': 'u001', 'fact': True}), 'ambiguous'),
    (lambda d: d['__shared'].update(u001='collision'), 'duplicate'),
    (lambda d: d.update(payload={'$literal': [['same', 1], ['same', 2]]}), 'duplicate literal'),
])
def test_damaged_encoded_references_are_rejected(mutation, message):
    document = encode(payload())
    mutation(document)
    with pytest.raises(ValueError, match=message):
        decode(document)
