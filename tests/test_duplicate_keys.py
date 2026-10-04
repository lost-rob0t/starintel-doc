"""Shared raw-text fixtures enter real public parsers before keys can be lost."""
import json
from decimal import Decimal
from pathlib import Path
import unittest

import starintel_doc as public
import starintel_canonical as canonical

CASES = json.loads((Path(__file__).parent / 'fixtures/raw-json-unique-keys.json').read_text())['cases']


class DuplicateKeyTests(unittest.TestCase):
    def test_raw_public_parsers_reject_every_duplicate(self):
        for case in CASES:
            for parse in [public.parse_json, canonical.parse_json]:
                for source in [case['wire'], case['wire'].encode(), bytearray(case['wire'].encode())]:
                    with self.subTest(case=case['name'], parser=parse, input=type(source)):
                        if case['valid']:
                            actual = parse(source)
                            self.assertEqual(actual, json.loads(case['wire'], parse_float=Decimal))
                        else:
                            with self.assertRaises(public.ValidationError) as caught:
                                parse(source)
                            self.assertEqual(caught.exception.category, 'duplicate_key')

    def test_document_json_boundaries_do_not_erase_duplicates(self):
        for case in CASES:
            for document in [public.Document, canonical.Document]:
                with self.subTest(case=case['name'], document=document):
                    if case['valid']:
                        encoded = document.from_json(case['wire']).to_json()
                        self.assertEqual(public.parse_json(encoded), public.parse_json(case['wire']))
                    else:
                        with self.assertRaises(public.ValidationError) as caught:
                            document.from_json(case['wire'])
                        self.assertEqual(caught.exception.category, 'duplicate_key')


if __name__ == '__main__':
    unittest.main()
