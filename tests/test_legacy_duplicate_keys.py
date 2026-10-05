"""The SDK's historical raw readers reject ambiguity before model decoding."""
import inspect
import json
from decimal import Decimal
from pathlib import Path
import unittest

from dataclasses import dataclass
from dataclasses_json import DataClassJsonMixin, dataclass_json

import starintel_doc as public
from starintel_doc import v090
from test_v090 import document


CASES = json.loads((Path(__file__).parent / 'fixtures/raw-json-unique-keys.json').read_text())['cases']
LEGACY_MODULES = [getattr(public, 'legacy_' + name) for name in (
    'documents', 'entities', 'hosts', 'locations', 'manifest', 'phones',
    'relations', 'social_media', 'targets', 'web',
)]
LEGACY_MODELS = [model for module in LEGACY_MODULES for model in vars(module).values()
                 if inspect.isclass(model) and model.__module__ == module.__name__
                 and hasattr(model, 'from_json')]


class LegacyDuplicateKeyTests(unittest.TestCase):
    def test_v090_raw_reader_rejects_shared_duplicates(self):
        for case in CASES:
            value = document()
            value['extensions'] = None
            wire = json.dumps(value).replace('"extensions": null', '"extensions": ' + case['wire'])
            for source in [wire, wire.encode(), bytearray(wire.encode())]:
                with self.subTest(case=case['name'], input=type(source)):
                    if case['valid']:
                        self.assertEqual(v090.Document.from_json(source).to_dict(), json.loads(wire))
                    else:
                        with self.assertRaises(public.ValidationError) as caught:
                            v090.Document.from_json(source)
                        self.assertEqual(caught.exception.category, 'duplicate_key')

    def test_every_legacy_alias_rejects_shared_duplicates_before_model_decoding(self):
        self.assertEqual(len(LEGACY_MODELS), 22)
        for model in LEGACY_MODELS:
            for case in CASES:
                if case['valid']:
                    continue
                for source in [case['wire'], case['wire'].encode(), bytearray(case['wire'].encode())]:
                    with self.subTest(model=model, case=case['name'], input=type(source)):
                        with self.assertRaises(public.ValidationError) as caught:
                            model.from_json(source)
                        self.assertEqual(caught.exception.category, 'duplicate_key')

    def test_unique_controls_preserve_legacy_model_decoding(self):
        # Includes separately decorated models and an inherited-only web model.
        for model in [public.legacy_documents.Document, public.legacy_entities.Person,
                      public.legacy_manifest.ActorManifest, public.legacy_web.Email]:
            for case in CASES:
                if not case['valid']:
                    continue
                with self.subTest(model=model, case=case['name']):
                    wire = case['wire'][:-1] + ',"dateAdded":1,"dateUpdated":1}'
                    original = DataClassJsonMixin.from_json.__func__(model, wire)
                    actual = model.from_json(wire)
                    self.assertEqual(actual, original)

    def test_all_aliases_keep_existing_unique_input_behavior(self):
        required = {
            'Domain': {'recordType': 'A', 'record': 'example.test'},
            'Service': {'port': 443, 'name': 'https'},
            'Network': {'asn': 64512, 'subnet': '192.0.2.0/24'},
            'Host': {'hostname': 'example.test', 'ip': '192.0.2.1'},
            'Url': {'url': 'https://example.test/'},
            'Address': {'city': 'Example', 'state': 'EX', 'postal': '1',
                        'country': 'XX', 'street': 'Example Street'},
            'Phone': {'number': '+15555550100'},
            'Target': {'actor': 'test', 'target': 'example.test'},
            'Scope': {'description': 'test'},
            'User': {'url': 'https://example.test/', 'name': 'example', 'platform': 'test'},
        }
        for model in LEGACY_MODELS:
            wire = json.dumps({'dateAdded': 1, 'dateUpdated': 1, **required.get(model.__name__, {})})
            with self.subTest(model=model):
                # Scope and EmailMessage have pre-existing model decode errors.
                # A wire-ambiguity fix must neither mask nor fix those errors.
                try:
                    expected = DataClassJsonMixin.from_json.__func__(model, wire)
                except (AttributeError, TypeError) as original:
                    self.assertIn(model.__name__, {'Scope', 'EmailMessage'})
                    with self.assertRaises(type(original)) as actual:
                        model.from_json(s=wire)
                    self.assertEqual(str(actual.exception), str(original))
                else:
                    self.assertEqual(model.from_json(s=wire), expected)

    def test_signature_and_third_party_decorator_are_unchanged(self):
        for model in LEGACY_MODELS:
            self.assertEqual(inspect.signature(model.from_json), inspect.signature(DataClassJsonMixin.from_json))

        @dataclass_json
        @dataclass
        class External:
            value: int

        self.assertEqual(External.from_json('{"value": 1, "value": 2}').value, 2)

    def test_caller_numeric_hooks_run_once_and_keep_legacy_types(self):
        seen = []

        def parse_int(token):
            seen.append(('int', token))
            return int(token) + 1

        def parse_float(token):
            seen.append(('float', token))
            return Decimal(token)

        def parse_constant(token):
            seen.append(('constant', token))
            return token

        wire = '{"actor":"test","target":"test","options":[1,1.25,NaN]}'
        value = public.legacy_targets.Target.from_json(
            wire, parse_int=parse_int, parse_float=parse_float, parse_constant=parse_constant)
        self.assertEqual(value.options, [2, Decimal('1.25'), 'NaN'])
        self.assertEqual(seen, [('int', '1'), ('float', '1.25'), ('constant', 'NaN')])
        default = public.legacy_targets.Target.from_json(wire)
        self.assertIsInstance(default.options[0], int)
        self.assertIsInstance(default.options[1], float)

    def test_caller_object_hooks_and_precedence_are_preserved(self):
        seen = []

        def pairs_hook(pairs):
            seen.append(('pairs', pairs))
            return dict(pairs)

        def object_hook(value):
            seen.append(('object', value))
            if 'content' in value:
                value['content'] += ' mapped'
            return value

        model = public.legacy_social_media.Message
        wire = '{"content":"hello","extra":{"value":1}}'
        self.assertEqual(model.from_json(wire, object_hook=object_hook).content, 'hello mapped')
        self.assertEqual([kind for kind, _ in seen], ['object', 'object'])
        seen.clear()
        self.assertEqual(model.from_json(wire, object_hook=object_hook, object_pairs_hook=pairs_hook).content, 'hello')
        self.assertEqual([kind for kind, _ in seen], ['pairs', 'pairs'])
        for options in [{'object_hook': object_hook}, {'object_pairs_hook': pairs_hook},
                        {'object_hook': object_hook, 'object_pairs_hook': pairs_hook}]:
            with self.subTest(options=options):
                with self.assertRaises(public.ValidationError) as caught:
                    model.from_json('{"content":"one","content":"two"}', **options)
                self.assertEqual(caught.exception.category, 'duplicate_key')

    def test_strict_and_infer_missing_options_are_preserved(self):
        value = public.legacy_social_media.Message.from_json(
            '{"content":"raw\ttext"}', strict=False, infer_missing=True)
        self.assertEqual(value.content, 'raw\ttext')
        with self.assertRaises(public.ValidationError) as caught:
            public.legacy_social_media.Message.from_json(
                '{"content":"raw\ttext","content":null}', strict=False)
        self.assertEqual(caught.exception.category, 'duplicate_key')
        with self.assertRaises(KeyError):
            public.legacy_hosts.Domain.from_json('{}')
        with self.assertWarns(RuntimeWarning):
            missing = public.legacy_hosts.Domain.from_json('{}', infer_missing=True)
        self.assertIsNone(missing.record)
        self.assertIsNone(missing.record_type)

    def test_unsupported_decoder_override_keeps_original_error(self):
        # dataclasses-json uses a non-positional-only parameter named cls, so
        # passing JSONDecoder via cls already conflicts with its classmethod.
        model = public.legacy_documents.Document
        with self.assertRaises(TypeError) as original:
            DataClassJsonMixin.from_json.__func__(model, '{}', cls=json.JSONDecoder)
        with self.assertRaises(TypeError) as actual:
            model.from_json('{}', cls=json.JSONDecoder)
        self.assertEqual(str(actual.exception), str(original.exception))

    def test_v090_rejects_top_level_equal_and_escaped_names(self):
        wire = json.dumps(document())
        for repeated_name in ['_id', r'\u005fid']:
            repeated = wire[:-1] + ',"' + repeated_name + '":"starintel:person:python-test"}'
            with self.subTest(name=repeated_name):
                with self.assertRaises(public.ValidationError) as caught:
                    v090.Document.from_json(repeated)
                self.assertEqual(caught.exception.category, 'duplicate_key')

    def test_v090_preserves_numeric_and_schema_behavior(self):
        value = document()
        value['extensions']['example.test']['number'] = 1.125
        self.assertIsInstance(v090.Document.from_json(json.dumps(value)).value['extensions']['example.test']['number'], float)
        schema = v090.load_schema()
        self.assertEqual(v090.Document.from_json(json.dumps(value), schema).value, value)
        value['schema_version'] = '0.8.0'
        with self.assertRaises(public.UnsupportedVersion):
            v090.Document.from_json(json.dumps(value))


if __name__ == '__main__':
    unittest.main()
