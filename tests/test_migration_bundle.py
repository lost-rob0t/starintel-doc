from copy import deepcopy
import unittest
from starintel_canonical.migration_bundle import plan_person_identifier_bundle

class IdentifierBundleTests(unittest.TestCase):
    def source(self):
        return {'_id':'person:test','dataset':'test','dtype':'person','schema_version':'0.9.0',
                'handling':{'visibility':'private'},'data':{'fname':'Fixture','external_ids':[
                {'scheme':'public-registry','value':'00123','issuer':'Fixture issuer','canonical':False,
                 'confidence':0.123456,'valid_from':'2026-10-04T01:02:03.456789+01:00','valid_to':None}]}}

    def test_deterministic_lossless_bundle_and_explicit_atomic_plan(self):
        source=self.source();original=deepcopy(source)
        first=plan_person_identifier_bundle(source);second=plan_person_identifier_bundle(source)
        self.assertEqual(first,second);self.assertEqual(source,original)
        self.assertTrue(first['atomicRequired']);self.assertEqual(len(first['writes']),2)
        docs={w['document']['dtype']:w['document'] for w in first['writes']}
        self.assertEqual(docs['person']['identifiers'][0]['id'],docs['person-identifier']['id'])
        self.assertEqual(docs['person-identifier']['extensions']['legacyIdentifier']['original'],source['data']['external_ids'][0])
        self.assertNotIn('primary',docs['person-identifier'])
        self.assertEqual(docs['person-identifier']['visibility'],'private')
        self.assertEqual(docs['person']['extensions']['legacy']['original']['data'],source['data'])

    def test_collision_aborts_whole_plan_without_mutation(self):
        source=self.source();plan=plan_person_identifier_bundle(source)
        child=next(w['document'] for w in plan['writes'] if w['document']['dtype']=='person-identifier')
        changed=deepcopy(child);changed['value']='conflict';store={child['id']:changed};before=deepcopy(store)
        with self.assertRaises(ValueError):plan_person_identifier_bundle(source,existing_documents=store)
        self.assertEqual(store,before)
        source['data']['external_ids'].append({**source['data']['external_ids'][0],'confidence':0.5})
        with self.assertRaises(ValueError):plan_person_identifier_bundle(source)

    def test_idempotent_existing_documents_and_source_precondition(self):
        source=self.source();plan=plan_person_identifier_bundle(source)
        existing={w['id']:w['document'] for w in plan['writes']}
        replay=plan_person_identifier_bundle(source,existing_documents=existing)
        self.assertTrue(all(w['expectedSha256'] for w in replay['writes']))
        original=plan_person_identifier_bundle(source,existing_documents={source['_id']:source})
        self.assertTrue(next(w['expectedSha256'] for w in original['writes'] if w['id']==source['_id']))
