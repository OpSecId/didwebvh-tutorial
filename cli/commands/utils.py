import requests
import json
from did_webvh.core.state import DocumentState
from did_webvh.core.date_utils import make_timestamp
from ..main import AGENT_ENDPOINT, SCID_PLACEHOLDER

def setup_files():
    with open('outputs/did.json', 'w+') as f:
        f.write('')
    with open('outputs/did.jsonl', 'w+') as f:
        f.write('')
    with open('outputs/parameters.json', 'w+') as f:
        f.write('')
    with open('outputs/scid_input.json', 'w+') as f:
        f.write('')
    with open('outputs/draft_log_entry.json', 'w+') as f:
        f.write('')
    with open('outputs/log_entry.json', 'w+') as f:
        f.write('')
    return

def origin_to_did(origin):
    return ':'.join(origin.replace('https://', 'did:web:').lstrip('/').split('/'))
    # return ':'.join(origin.removeprefix('https://').removesuffix('/').split('/'))

def add_also_known_as(did):
    with open('outputs/did.json', 'r') as f:
        did_doc = json.loads(f.read())
        
    did_doc['alsoKnownAs'] = [did]
    write_document('did', did_doc)

def write_document(filename, data):
    
    data = json.dumps(data, indent=4)
    with open(f'outputs/{filename}.json', 'w+') as f:
        f.write(data)
    return data

def create_key(kid=None):
    r = requests.post(
        f"{AGENT_ENDPOINT}/wallet/keys",
        json={"kid": kid} if kid else {}
    )
    return r.json()

def update_kid(multikey, kid):
    r = requests.put(
        f"{AGENT_ENDPOINT}/wallet/keys",
        json={
            "kid": kid,
            "multikey": multikey
        }
    )

def sign_document(document, options):
    r = requests.post(
        f"{AGENT_ENDPOINT}/vc/di/add-proof",
        json={"document": document, 'options': options}
    )
    return r.json()

def insert_placeholder(document):
    return json.loads(json.dumps(document).replace('did:web:', f'did:webvh:{SCID_PLACEHOLDER}:'))

def insert_scid(document, scid):
    return json.loads(json.dumps(document).replace(SCID_PLACEHOLDER, scid))

def initial_state(draft_log_entry):
    return DocumentState(
        params=draft_log_entry.get('parameters'),
        params_update=draft_log_entry.get('parameters').copy(),
        document=draft_log_entry.get('state'),
        timestamp=draft_log_entry.get('versionTime'),
        timestamp_raw=draft_log_entry.get('versionTime'),
        version_id="",
        last_version_id="",
        version_number=0,
    )

def next_state(previous_log_entry, draft_log_entry):
    state = DocumentState.load_history_line(previous_log_entry)
    return state.create_next(
        draft_log_entry.get('state'),
        draft_log_entry.get('parameters'),
        make_timestamp()[1]
    )

def timestamp():
    return make_timestamp()[1]