"""Real SDK JSON boundaries preserve arbitrary precision before validation."""
import json
import subprocess
import sys
import unittest
from decimal import Decimal, localcontext

import starintel_doc as public
import starintel_canonical as canonical


BASE = '{"id":"person:numeric","dataset":"test","dtype":"person","schemaVersion":"0.10.1"'
FRACTION = '0.12345678901234567890123456789'
TOKENS = [FRACTION, '9223372036854775808', '-9223372036854775809',
          '9007199254740993', '1.2345678901234567890123456789e400',
          '1e10000', '1e-10000', '-0.0', '0.00000000000000000000000000001']


def wire(token):
    return BASE + ',"deleted":false,"extensions":{"probe":{"number":' + token + ',"items":[null,false,"Grüße 🌍",{}],"numericText":"' + token + '"}}}'


class NumericWireTests(unittest.TestCase):
    def assert_exact(self, text, original):
        self.assertEqual(json.loads(text, parse_float=Decimal), json.loads(original, parse_float=Decimal))
        self.assertNotIn('fname', json.loads(text))

    def test_all_public_json_boundaries_preserve_exact_numbers(self):
        for token in TOKENS:
            with self.subTest(token=token):
                source = wire(token)
                value = public.parse_json(source)
                self.assert_exact(public.stringify_json(public.roundtrip_document(value)), source)
                self.assert_exact(public.Document.from_json(source).to_json(), source)
                self.assert_exact(public.Document.from_json(source).to_json(pretty=True), source)
                self.assert_exact(public.Document.from_dict(value).to_json(), source)
                self.assert_exact(public.Document(value).to_json(), source)
                self.assert_exact(canonical.Document.from_json(source).to_json(), source)
        self.assertIn(FRACTION, public.Document.from_json(wire(FRACTION)).to_json())

    def test_integer_tokens_beyond_host_string_digit_limit(self):
        token = '1234567890' * 500
        for source in [token, '-' + token]:
            parsed = public.parse_json(source)
            self.assertIsInstance(parsed, int)
            self.assertEqual(public.stringify_json(parsed), source)
            self.assertIn(source, public.Document.from_json(wire(source)).to_json())

    def test_decimal_precision_context_cannot_round_wire_values(self):
        with localcontext() as context:
            context.prec = 2
            emitted = public.Document.from_json(wire(FRACTION)).to_json()
        self.assertIn(FRACTION, emitted)

    def test_decimal_host_values_are_numbers_not_quoted_strings(self):
        value = public.parse_json(wire('0'))
        value['extensions']['probe']['number'] = Decimal(FRACTION)
        emitted = public.Document.from_dict(value).to_json()
        self.assertIn(': ' + FRACTION, public.stringify_json(value, pretty=True))
        self.assertIn('"number":' + FRACTION, emitted)
        self.assertIsInstance(public.parse_json(emitted)['extensions']['probe']['number'], Decimal)

    def test_canonical_cli_parses_numbers_before_any_rounding(self):
        for token in TOKENS:
            with self.subTest(token=token):
                source = wire(token)
                response = subprocess.run([sys.executable, '-m', 'starintel_doc.conformance_adapter'],
                                          input='{"command":"roundtrip","document":' + source + '}',
                                          capture_output=True, text=True)
                self.assertEqual(response.returncode, 0, response.stdout + response.stderr)
                result = public.parse_json(response.stdout)
                self.assertEqual(result['document'], public.parse_json(source))

    def test_exact_integer_schema_semantics_without_float_coercion(self):
        for token in ['1', '1.0', '1e0', '9223372036854775808', '1e400']:
            source = BASE + ',"createdAt":' + token + '}'
            with self.subTest(valid=token):
                self.assert_exact(public.Document.from_json(source).to_json(), source)
        for token in ['1.00000000000000000000000000001', '1e-400', '-1e-400', 'true']:
            source = BASE + ',"createdAt":' + token + '}'
            with self.subTest(invalid=token), self.assertRaises(public.ValidationError):
                public.Document.from_json(source)

    def test_existing_decimal_string_contract_is_not_weakened(self):
        with self.assertRaises(public.ValidationError):
            public.Document.from_json(BASE + ',"confidence":0.5}')
        with self.assertRaises(public.ValidationError):
            public.Document.from_json(BASE + ',"confidence":"0.12345"}')
        public.Document.from_json(BASE + ',"confidence":"0.1234"}')

    def test_nonfinite_and_non_json_host_values_still_rejected(self):
        for token in ['NaN', 'Infinity', '-Infinity', '+1', '01', '1.', '.1', '1e', '1e+', '1e--2']:
            with self.subTest(token=token), self.assertRaises((public.ValidationError, json.JSONDecodeError)):
                public.Document.from_json(wire(token))
        for value in [Decimal('NaN'), Decimal('sNaN'), Decimal('Infinity'), Decimal('-Infinity'),
                      float('nan'), float('inf'), object(), {1: 'invalid key'}]:
            with self.subTest(value=value), self.assertRaises(public.ValidationError):
                public.stringify_json(value)
        cycle = []; cycle.append(cycle)
        with self.assertRaises(public.ValidationError):
            public.stringify_json(cycle)

    def test_current_document_migration_and_digest_accept_exact_values(self):
        from starintel_canonical.migration import canonicalize_document
        from starintel_canonical.migration_bundle import digest
        original = public.parse_json(wire(FRACTION))
        self.assertEqual(canonicalize_document(original), original)
        self.assertNotEqual(digest(original), digest(public.parse_json(wire('0.12345678901234568'))))

    def test_exponents_outside_decimal_domain_remain_exact_raw_numbers(self):
        exponent = '999999999999999999999'
        for token in ['1e' + exponent, '-1e' + exponent, '1e-' + exponent,
                      '-1e-' + exponent, '0e' + exponent, '0.000e-' + exponent,
                      '1e' + '9' * 5000]:
            with self.subTest(token=token[:50]):
                parsed = public.parse_json(token)
                self.assertIsInstance(parsed, public.RawJsonNumber)
                self.assertEqual(public.stringify_json(parsed), token)
                self.assertIn('"number":' + token, public.Document.from_json(wire(token)).to_json())
                response = subprocess.run([sys.executable, '-m', 'starintel_doc.conformance_adapter'],
                                          input='{"command":"roundtrip","document":' + wire(token) + '}',
                                          capture_output=True, text=True)
                self.assertEqual(response.returncode, 0, response.stdout + response.stderr)
                self.assertIn('"number":' + token, response.stdout)

    def test_raw_integer_and_bound_validation_is_exact_without_expansion(self):
        exponent = '999999999999999999999'
        for token in ['1e' + exponent, '0e-' + exponent]:
            public.Document.from_json(BASE + ',"createdAt":' + token + '}')
        for token in ['-1e' + exponent, '1e-' + exponent, '-1e-' + exponent]:
            with self.subTest(token=token), self.assertRaises(public.ValidationError):
                public.Document.from_json(BASE + ',"createdAt":' + token + '}')
        schema = public.load_schema()
        schema['$defs']['Person']['properties']['age'] = {'type': 'number', 'minimum': -1, 'maximum': 1}
        for token in ['1e-' + exponent, '-1e-' + exponent]:
            public.validate_document(public.parse_json(BASE + ',"age":' + token + '}'), schema)
        for token in ['1e' + exponent, '-1e' + exponent]:
            with self.assertRaises(public.ValidationError):
                public.validate_document(public.parse_json(BASE + ',"age":' + token + '}'), schema)

    def test_raw_number_comparison_and_constructor_are_strict(self):
        raw = public.RawJsonNumber
        for token in ['', '1e', '01', '+1', '1.2garbage', 'NaN', '1\\n']:
            with self.subTest(token=token), self.assertRaises(ValueError):
                raw(token)
        self.assertEqual(raw('1.20'), Decimal('1.2'))
        self.assertEqual(raw('-0e999999999999999999999'), 0)
        self.assertNotEqual(raw('1'), True)
        for a, b in [('1.2', '1.23'), ('-1.23', '-1.2'), ('0.0001', '0.001'),
                     ('1e999999999999999999999', '2e999999999999999999999'),
                     ('-2e999999999999999999999', '-1e999999999999999999999')]:
            self.assertLess(raw(a), raw(b))
        self.assertTrue(raw('10e-1').is_integer())
        self.assertFalse(raw('10e-2').is_integer())

    def test_mutated_document_still_revalidates(self):
        value = public.Document.from_json(wire(FRACTION))
        value.value['createdAt'] = Decimal(FRACTION)
        with self.assertRaises(public.ValidationError):
            value.to_json()


if __name__ == '__main__':
    unittest.main()
