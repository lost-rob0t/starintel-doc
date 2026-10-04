import copy
import json
import unittest
import starintel_doc as public
from starintel_canonical import RELEASE_ROOT

class InstalledSemanticBoundaryTests(unittest.TestCase):
    def fixtures(self):
        return {f['document']['dtype']: f['document'] for f in json.loads((RELEASE_ROOT/'supported-workflow-fixtures.json').read_text())}

    def test_calendar_and_clock_values_require_real_valid_instants(self):
        baseline=self.fixtures()['research-node']
        for stamp in ['2026-02-30T12:00:00Z','2026-10-04T25:00:00Z','2026-10-04T12:61:00Z','2026-10-04T12:00:00']:
            value=copy.deepcopy(baseline);value['history'][0]['at']=stamp
            with self.subTest(stamp=stamp), self.assertRaises(public.ValidationError):public.validate_document(value)
        for date in ['2026-02-29','2026-13-01','2026-04-31']:
            value={'id':'person:test','dataset':'test','dtype':'person','schemaVersion':'0.10.1','dob':date}
            with self.subTest(date=date), self.assertRaises(public.ValidationError):public.validate_document(value)

    def test_decimal_bounds_scale_and_reference_shapes(self):
        fixtures=self.fixtures()
        values=[]
        node=copy.deepcopy(fixtures['research-node']);node['limits']['maxCost']='-0.01';values.append(node)
        analysis=copy.deepcopy(fixtures['analysis']);analysis['payloadConfidence']='1.1';values.append(analysis)
        base={'id':'person:test','dataset':'test','dtype':'person','schemaVersion':'0.10.1'}
        values += [{**base,'confidence':'0.12345'}, {**base,'confidence':'1.01'},
                   {**base,'identifiers':[{'schema':'org.starintel/core@1/person-identifier','id':7}]},
                   {**base,'identifiers':[{'schema':'x','id':'i','unknown':False}]}, {**base,'data':{}}]
        for value in values:
            with self.subTest(value=value), self.assertRaises(public.ValidationError):public.validate_document(value)

    def test_opaque_maps_still_require_finite_json_values(self):
        base={'id':'person:x','dataset':'test','dtype':'person','schemaVersion':'0.10.1'}
        invalid=[float('nan'),float('inf'),{1:'not a JSON key'},object()]
        cycle=[];cycle.append(cycle);invalid.append(cycle)
        for value in invalid:
            with self.assertRaises(public.ValidationError):
                public.validate_document({**base,'extensions':{'opaque':value}})
