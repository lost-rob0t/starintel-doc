import json
import unittest
import starintel_doc as public
from starintel_doc.canonical import DOCUMENT_TYPES
from test_canonical import document

class PublicDefaultsTests(unittest.TestCase):
    def test_all_root_document_families_emit_canonical_json(self):
        self.assertEqual((public.SPEC_VERSION, public.RELEASE_VERSION, public.PROFILE_VERSION), ('0.10.1',)*3)
        self.assertNotIn('profile_schema', public.__all__)
        self.assertIn('legacy_profile_schema', public.__all__)
        for dtype in DOCUMENT_TYPES:
            with self.subTest(dtype=dtype):
                original=document(dtype)
                emitted=json.loads(public.Document.from_dict(original).to_json())
                self.assertEqual(emitted,original)
                self.assertNotIn('_id',emitted)
                self.assertNotIn('data',emitted)
                self.assertEqual(emitted['schemaVersion'],'0.10.1')

    def test_root_capture_defaults_and_explicit_legacy_profile(self):
        common={'dataset':'fixture','url':'https://example.test/'}
        http=public.build_http_transaction(**common,method='GET',response_status=200)
        web=public.build_web_capture(**common,screenshot_uri='artifact://capture/1',screenshot_hash='sha256:fixture')
        for doc in [http,web]:
            public.validate_document(doc)
            self.assertEqual(doc['schemaVersion'],'0.10.1')
            self.assertNotIn('data',doc)
        legacy=public.legacy_profile_schema()
        self.assertIn('data',legacy['properties'])

    def test_direct_constructor_and_mutated_serialization_cannot_bypass_validation(self):
        with self.assertRaises(public.ValidationError):
            public.Document({'_id':'legacy','dtype':'person','schema_version':'0.9.0','data':{}})
        original=document('person')
        value=public.Document(original)
        original['fname']='outside mutation'
        self.assertNotIn('fname',value.value)
        value.value['data']={}
        with self.assertRaises(public.ValidationError):value.to_dict()
        with self.assertRaises(public.ValidationError):value.to_json()

    def test_every_public_document_factory_and_serializer_rejects_invalid_wire(self):
        invalid=document('person')
        invalid['unexpectedField']=False
        for call in [lambda:public.Document(invalid),
                     lambda:public.Document.from_dict(invalid),
                     lambda:public.Document.from_json(json.dumps(invalid)),
                     lambda:public.validate_document(invalid),
                     lambda:public.roundtrip_document(invalid),
                     lambda:public.network_capture_to_jsonld(invalid)]:
            with self.subTest(call=call):
                with self.assertRaises(public.ValidationError):call()
        value=public.Document(document('person'))
        value.value['unexpectedField']=None
        for call in [value.validate,value.to_dict,value.to_json]:
            with self.assertRaises(public.ValidationError):call()
        for call in [lambda:public.build_http_transaction(dataset='fixture',method='GET',url='https://example.test/',response_status=200,fields={'unexpectedField':False}),
                     lambda:public.build_web_capture(dataset='fixture',url='https://example.test/',screenshot_uri='artifact://1',screenshot_hash='sha256:fixture',fields={'unexpectedField':None})]:
            with self.assertRaises((ValueError,public.ValidationError)):call()
