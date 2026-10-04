import importlib.util
import json
from pathlib import Path
import unittest
from starintel_canonical import RELEASE_ROOT, validate_document

from starintel_canonical.migration import canonicalize_document as convert

class MigrationTests(unittest.TestCase):
    def test_all_added_workflow_payloads_and_complete_envelope_preserved(self):
        fixtures = json.loads((RELEASE_ROOT/'supported-workflow-fixtures.json').read_text())
        for case in fixtures:
            dtype = case['document']['dtype']
            before = {'_id': 'fixture:'+dtype, 'dtype': dtype, 'dataset': 'migration-test',
                      'schema_version':'0.9.0', 'version':4,
                      'date_added':'2026-10-04T01:02:03.456789+01:00',
                      'date_updated':'2026-10-04T01:03:03.456789+01:00',
                      'sources':[{'url':'https://example.test/source','confidence':0.75}, {'kind':'tool','name':'subfinder'}],
                      'evidence':[{'quote':'Original observation','verified':False}],
                      'assessment':{'confidence':0.75},
                      'handling':{'visibility':'private','access_groups':['analysts'],'pii':True},
                      'extensions':{'example.test':{'false_value':False,'null_value':None}},
                      'data':case['legacyData']}
            with self.subTest(dtype=dtype):
                after = convert(before)
                validate_document(after)
                original = after['extensions']['legacy']['original']
                self.assertEqual(original['data'],before['data'])
                for key in ['date_added','date_updated','sources','evidence','assessment','handling','version']:
                    self.assertEqual(original[key],before[key])
                self.assertEqual(after['extensions']['example.test'],before['extensions']['example.test'])
                self.assertEqual(after['visibility'],'private')
                self.assertEqual(after['accessControl']['legacyHandling'],before['handling'])
                self.assertEqual(convert(after),after)

    def test_notes_urls_and_normalized_envelope_collisions(self):
        before={'_id':'a','dtype':'person','dataset':'fixture','schema_version':'0.9.0',
                'notes':['first','second'], 'source_urls':['https://example.test/a'],
                'sources':[{'url':'https://example.test/b'},{'url':'https://example.test/a'}],
                'date_added':'2026-10-04T00:00:00Z','data':{'fname':'Ada'}}
        after=convert(before)
        self.assertNotIn('notes',after)
        self.assertEqual(after['extensions']['legacy']['original']['notes'],before['notes'])
        self.assertEqual(after['sourceUrls'],['https://example.test/a','https://example.test/b'])
        before['created_at']='2026-10-04T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'normalized envelope collision'):convert(before)

    def test_invalid_containers_and_policy_are_rejected(self):
        for key,item in [('data',[]),('extensions',[]),('handling',[]),('handling',{'visibility':'restricted'})]:
            before={'_id':'a','dtype':'person','dataset':'fixture','schema_version':'0.9.0','data':{}}
            before[key]=item
            with self.subTest(key=key,item=item):
                with self.assertRaises(ValueError):convert(before)

    def test_person_explicit_full_name_does_not_get_overwritten_by_label(self):
        before={'_id':'a','dtype':'person','dataset':'fixture','schema_version':'0.9.0',
                'data':{'name':'A. Lovelace','full_name':'Ada Lovelace'}}
        after=convert(before)
        self.assertEqual(after['fullName'],'Ada Lovelace')
        self.assertEqual(after['extensions']['legacy']['original']['data'],before['data'])

    def test_no_reference_dtype_guesses(self):
        before={'_id':'r','dtype':'relation','dataset':'fixture','schema_version':'0.9.0',
                'data':{'subject':'starintel:person:a','object':'starintel:person:b','predicate':'knows'}}
        with self.assertRaisesRegex(ValueError,'ambiguous legacy reference'):
            convert(before)
        after=convert(before,dtype_registry={'starintel:person:a':'person','starintel:person:b':'person'})
        self.assertEqual(after['source']['schema'],'org.starintel/core@1/person')
        self.assertEqual(after['destination']['id'],'starintel:person:b')

    def test_collision_and_unknown_current_fields_fail(self):
        before={'id':'a','dataset':'fixture','dtype':'person','schemaVersion':'0.10.1','data':{}}
        with self.assertRaises(ValueError):convert(before)
        old={'_id':'a','dataset':'fixture','dtype':'person','schema_version':'0.9.0',
             'data':{'schema_version':'0.10.1'}}
        with self.assertRaisesRegex(ValueError,'collision'):convert(old)

if __name__=='__main__':unittest.main()

class OptionalOverlapTests(unittest.TestCase):
    def test_valid_old_identifier_array_is_retained_without_fake_native_map(self):
        old={'_id':'person:1','dataset':'test','dtype':'person','schema_version':'0.9.0',
             'data':{'fname':'Ada','external_ids':[{'scheme':'registry','value':'001','canonical':False}]}}
        new=convert(old)
        self.assertNotIn('externalIds',new)
        self.assertNotIn('identifiers',new)
        self.assertEqual(new['extensions']['legacy']['original']['data'],old['data'])
        self.assertEqual(new['extensions']['legacy']['unmappedDataFields'][0]['field'],'external_ids')
        old['data']['external_ids']=[{'scheme':'registry'}]
        with self.assertRaises(Exception):convert(old)

    def test_missing_required_reference_remains_a_blocker(self):
        old={'_id':'loc:1','dataset':'test','dtype':'location','schema_version':'0.9.0',
             'data':{'geometry':{'type':'Point','coordinates':[0,0]}}}
        with self.assertRaisesRegex(ValueError,'ambiguous legacy reference'):convert(old)


class FiniteJsonMigrationTests(unittest.TestCase):
    def test_nonfinite_values_are_not_laundered_in_preserved_legacy(self):
        for value in [float('nan'), float('inf'), float('-inf')]:
            old={'_id':'person:x','dtype':'person','dataset':'test','schema_version':'0.9.0',
                 'data':{'fname':'Ada'},'assessment':{'confidence':value}}
            with self.assertRaisesRegex(ValueError,'finite JSON'):convert(old)
