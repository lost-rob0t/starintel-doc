"""Plan an explicit, deterministic one-to-many migration; never perform writes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from . import validate_document, stringify_json
from .migration import canonicalize_document

ORACLE = json.loads((Path(__file__).parent / '_compatibility/person-legacy-oracle.json').read_text())

def digest(value):
    encoded = stringify_json(value, sort_keys=True)
    return hashlib.sha256(encoded.encode()).hexdigest()

def plan_person_identifier_bundle(document, *, existing_documents=None):
    """Return a checked write plan, with preconditions for caller-owned atomic apply.

Existing state must be a snapshot supplied by the caller. Applying these writes
requires a transaction which checks every expected hash before changing anything.
This function neither reads a database nor applies any part of the plan.
"""
    if not isinstance(document,dict) or document.get('dtype') != 'person' or 'schemaVersion' in document:
        raise ValueError('an explicit legacy person envelope is required')
    data=document.get('data')
    Draft202012Validator(ORACLE['personData'],format_checker=FormatChecker()).validate(data)
    records=data.get('external_ids', [])
    source=deepcopy(document)
    source['data'].pop('external_ids',None)
    person=canonicalize_document(source)
    person.setdefault('extensions',{}).setdefault('legacy',{}).setdefault('original',{})['data']=deepcopy(data)
    personschema='org.starintel/core@1/person'
    idschema='org.starintel/core@1/person-identifier'
    planned={}; refs=deepcopy(person.get("identifiers", []))
    for record in records:
        identity=[person['id'],record['scheme'],record['value'],record.get('issuer'),record.get('jurisdiction')]
        identity_id='person-identifier:sha256:'+digest(identity)
        child={'id':identity_id,'dataset':person['dataset'],'dtype':'person-identifier','schemaVersion':'0.10.1',
               'person':{'schema':personschema,'id':person['id']},'scheme':record['scheme'],'value':record['value'],
               'sensitive':True,'extensions':{'legacyIdentifier':{'original':deepcopy(record),
                   'sourcePersonId':person['id'],'sourceField':'data.external_ids'}},
               'provenance':{'migration':'explicit-person-identifiers','sourceDocumentId':person['id']}}
        # Only fields with matching declared meaning are emitted natively.
        # canonical!=primary; valid-from strings/confidence precision stay original.
        for key in ['issuer','jurisdiction']:
            if key in record:child[key]=record[key]
        for key in ['visibility','sensitivity','accessControl']:
            if key in person:child[key]=deepcopy(person[key])
        validate_document(child)
        if identity_id in planned and planned[identity_id]!=child:
            raise ValueError('conflicting source identifiers share a stable identity')
        planned[identity_id]=child
        ref={'schema':idschema,'id':identity_id}
        if ref not in refs:refs.append(ref)
    if refs:person['identifiers']=refs
    validate_document(person)
    planned[person['id']]=person
    existing_documents=existing_documents or {}
    writes=[]
    for identity_id,value in sorted(planned.items()):
        previous=existing_documents.get(identity_id)
        if previous is not None and previous!=value and not (identity_id==person['id'] and previous==document):
            raise ValueError('existing document collision: '+identity_id)
        writes.append({'id':identity_id,'expectedSha256':None if previous is None else digest(previous),
                       'document':deepcopy(value)})
    return {'atomicRequired':True,'sourceSha256':digest(document),'writes':writes}
