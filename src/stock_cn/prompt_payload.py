"""Lossless JSON sharing for rendered AI inputs, without removing any evidence.

``$ref`` resolves through ``__shared`` or ``source_urls`` in the enclosing codec
document. Original dictionaries containing reserved keys use ``$literal`` pairs,
so source data that itself contains a ``$ref`` remains ordinary source data.
This codec changes presentation only; accounts, requests and facts stay intact.
"""
from __future__ import annotations

import copy
import json
import math
import re
from collections import Counter

CODEC = 'stock-cn-shared-json-v1'
INSTRUCTIONS = (
    '本JSON只做无损共享，所有账户、规则、K线和事实完整保留。'
    '$ref指向本块__shared或source_urls中的同名ID；source_urls列出完整来源地址。'
    '$object=[字段表ID,值序列]，$table=[字段表ID,多行值序列]；'
    '字段表在__shared[k...]，每行值按字段表顺序一一映射，数字/字符串/布尔/null类型不改变。'
    '$literal为原始对象的键值对数组，其中$ref等原始字段是普通证据，不是注册引用。'
    '同一事实的共享引用不代表重复证据或额外交易权限。'
)
RESERVED_KEYS = {'$ref', '$literal', '$object', '$table'}


def _dump(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def _is_url(value):
    return isinstance(value, str) and value.startswith(('https://', 'http://'))


def _json_types(value, active=None):
    """Reject inputs that cannot survive ordinary JSON without value changes."""
    active = set() if active is None else active
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('prompt payload contains a non-finite number')
        return
    if not isinstance(value, (dict, list)):
        raise ValueError('prompt payload must contain JSON values only')
    if id(value) in active:
        raise ValueError('prompt payload contains a cycle')
    active.add(id(value))
    try:
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError('prompt payload object keys must be strings')
                _json_types(item, active)
        else:
            for item in value:
                _json_types(item, active)
    finally:
        active.remove(id(value))


def encode(value, *, min_string_length=80, min_node_length=256):
    """Return a self-contained JSON document that decodes to exactly ``value``.

    URLs appear once in ``source_urls``. Other repeated long strings and repeated
    large objects/arrays appear once in ``__shared``. Repeated object key layouts
    use ``$object``/``$table`` with a shared ordered field list and complete values.
    IDs depend only on this supplied value: no repository, market data or global
    registry is consulted.
    """
    for threshold in (min_string_length, min_node_length):
        if type(threshold) is not int or threshold < 1:
            raise ValueError('sharing thresholds must be positive integers')
    _json_types(value)
    strings = Counter()
    nodes = Counter()
    shapes = Counter()
    canonical = {}

    def node_key(item):
        if id(item) not in canonical:
            canonical[id(item)] = json.dumps(
                item, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
        return canonical[id(item)]

    def count(item):
        if isinstance(item, str):
            strings[item] += 1
        elif isinstance(item, (dict, list)):
            key = node_key(item)
            if len(key) >= min_node_length:
                nodes[key] += 1
            if isinstance(item, dict) and not RESERVED_KEYS & item.keys():
                shapes[tuple(sorted(item))] += 1
            for child in item.values() if isinstance(item, dict) else item:
                count(child)

    count(value)
    shared = {}
    urls = {}
    registered_strings = {}
    registered_nodes = {}
    registered_shapes = {}
    counters = {'s': 0, 'u': 0, 'n': 0, 'k': 0}

    def new_id(prefix):
        counters[prefix] += 1
        return f'{prefix}{counters[prefix]:03d}'

    def schema(keys):
        if keys not in registered_shapes:
            ref = new_id('k')
            registered_shapes[keys] = ref
            shared[ref] = list(keys)
        return registered_shapes[keys]

    def inline(item):
        if isinstance(item, dict):
            if RESERVED_KEYS & item.keys():
                return {'$literal': [[key, visit(child)] for key, child in item.items()]}
            keys = tuple(sorted(item))
            key_cost = sum(len(_dump(key)) + 1 for key in keys)
            if shapes[keys] > 1 and len(keys) >= 3 and key_cost > 30:
                return {'$object': [schema(keys), [visit(item[key]) for key in keys]]}
            return {key: visit(child) for key, child in item.items()}
        if isinstance(item, list):
            if len(item) >= 3 and all(isinstance(row, dict) and
                    not RESERVED_KEYS & row.keys() for row in item):
                keys = tuple(sorted(item[0]))
                if len(keys) >= 2 and all(tuple(sorted(row)) == keys and
                        nodes[node_key(row)] <= 1 for row in item):
                    return {'$table': [schema(keys),
                            [[visit(row[key]) for key in keys] for row in item]]}
            return [visit(child) for child in item]
        return item

    def visit(item):
        if isinstance(item, str) and (_is_url(item) or
                (len(item) >= min_string_length and strings[item] > 1)):
            if item not in registered_strings:
                url = _is_url(item)
                ref = new_id('u' if url else 's')
                registered_strings[item] = ref
                (urls if url else shared)[ref] = item
            return {'$ref': registered_strings[item]}
        if isinstance(item, (dict, list)):
            key = node_key(item)
            if nodes[key] > 1:
                if key not in registered_nodes:
                    ref = new_id('n')
                    registered_nodes[key] = ref
                    shared[ref] = inline(item)
                return {'$ref': registered_nodes[key]}
        return inline(item)

    payload = visit(value)
    return {'__codec': CODEC, '__instructions': INSTRUCTIONS,
            'payload': payload, '__shared': shared, 'source_urls': urls}


def decode(document):
    """Decode a codec document, rejecting missing, cyclic or ambiguous references."""
    if not isinstance(document, dict) or set(document) != {
            '__codec', '__instructions', 'payload', '__shared', 'source_urls'} or document['__codec'] != CODEC or document['__instructions'] != INSTRUCTIONS:
        raise ValueError('invalid shared prompt document')
    _json_types(document)
    shared, urls = document['__shared'], document['source_urls']
    if not isinstance(shared, dict) or not isinstance(urls, dict):
        raise ValueError('shared prompt registries must be objects')
    if set(shared) & set(urls):
        raise ValueError('duplicate shared prompt reference')
    registry = {**shared, **urls}
    for ref, item in registry.items():
        if not re.fullmatch(r'[snuk][0-9]+', ref):
            raise ValueError('invalid shared prompt reference ID')
        if ref in urls and not _is_url(item):
            raise ValueError('source URL registry must contain full URL strings')
    active = set()
    resolved = {}

    def fields(ref):
        if not isinstance(ref, str) or not re.fullmatch(r'k[0-9]+', ref):
            raise ValueError('invalid shared prompt field schema')
        keys = reference(ref)
        if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys) or len(keys) != len(set(keys)):
            raise ValueError('invalid shared prompt field schema')
        return keys

    def object_row(keys, values):
        if not isinstance(values, list) or len(values) != len(keys):
            raise ValueError('shared prompt row does not match its field schema')
        return {key: restore(child) for key, child in zip(keys, values)}

    def reference(ref):
        if not isinstance(ref, str) or ref not in registry:
            raise ValueError('missing shared prompt reference')
        if ref in active:
            raise ValueError('cyclic shared prompt reference')
        if ref not in resolved:
            active.add(ref)
            try:
                resolved[ref] = restore(registry[ref])
            finally:
                active.remove(ref)
        # Sharing is a wire representation, not shared mutable account state.
        return copy.deepcopy(resolved[ref])

    def restore(item):
        if isinstance(item, list):
            return [restore(child) for child in item]
        if isinstance(item, dict):
            if '$ref' in item:
                if set(item) != {'$ref'}:
                    raise ValueError('ambiguous shared prompt reference')
                return reference(item['$ref'])
            if '$object' in item or '$table' in item:
                marker = '$object' if '$object' in item else '$table'
                row = item[marker]
                if set(item) != {marker} or not isinstance(row, list) or len(row) != 2:
                    raise ValueError('invalid shared prompt object/table')
                keys = fields(row[0])
                if marker == '$object':
                    return object_row(keys, row[1])
                if not isinstance(row[1], list):
                    raise ValueError('invalid shared prompt table rows')
                return [object_row(keys, values) for values in row[1]]
            if '$literal' in item:
                if set(item) != {'$literal'} or not isinstance(item['$literal'], list):
                    raise ValueError('invalid literal prompt object')
                result = {}
                for pair in item['$literal']:
                    if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str):
                        raise ValueError('invalid literal prompt object pair')
                    if pair[0] in result:
                        raise ValueError('duplicate literal prompt object key')
                    result[pair[0]] = restore(pair[1])
                return result
            return {key: restore(child) for key, child in item.items()}
        return item

    # Validate the complete registry, including entries not reached by payload.
    for ref in registry:
        reference(ref)
    return restore(document['payload'])


def render_prompt_json(value, **thresholds):
    """Render compact UTF-8 JSON with a complete visible reference registry."""
    return _dump(encode(value, **thresholds))
