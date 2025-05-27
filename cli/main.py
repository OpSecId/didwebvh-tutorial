import click
import os
import json
import requests
from did_webvh.core.state import DocumentState
from did_webvh.core.date_utils import make_timestamp
from did_webvh.core.hash_utils import DEFAULT_HASH, HashInfo

ISSUER_ID = os.environ.get("ISSUER_ID", "did:key:z6MkgKA7yrw5kYSiDuQFcye4bMaJpcfHFry3Bx45pdWh3s8i")
AGENT_ENDPOINT = os.environ.get("AGENT_ENDPOINT", "http://agent.webvh-tutorial.localhost/")

SCID_PLACEHOLDER = r"{SCID}"
SUPPORTED_WEBVH_METHODS = ['0.5', '1.0']
DID_CORE_CONTEXT = "https://www.w3.org/ns/did/v1"
MULTIKEY_CONTEXT = "https://w3id.org/security/multikey/v1"
LOG_ENTRY_PROOF_OPTIONS = {
    'type': 'DataIntegrityProof',
    'cryptosuite': 'eddsa-jcs-2022',
    'proofPurpose': 'assertionMethod',
}
HASH_INFO = HashInfo.from_name(DEFAULT_HASH)
    
@click.group()
def webvh_cli():
    """WebVH Tutorial"""
    pass

@click.command('new-did')
@click.option('--auto', is_flag=True, default=False, help='Automate creation.')
@click.option('--origin', help='The DID location URL.')
def new_did(auto, origin):
    """Configure the base did document from a DID location URL."""
    
    if not origin:
        raise click.ClickException('Missing DID location URL.')
        
    setup_files()
    
    did_doc = {
        "@context": [DID_CORE_CONTEXT],
        "id": insert_placeholder(origin_to_did(origin))
    }
    if auto:
        update_key = create_key().get('multikey')
        
        state = DocumentState.initial(
            params={
                "scid": SCID_PLACEHOLDER,
                "method": 'did:webvh:0.5',
                "updateKeys": [update_key]
            },
            document=did_doc,
            timestamp=timestamp()
        )
        
        first_log_entry = sign_document(
            state.history_line(), 
            LOG_ENTRY_PROOF_OPTIONS | {'verificationMethod': f'did:key:{update_key}#{update_key}'}
        ).get('securedDocument')
        add_line(first_log_entry)
        
        state = DocumentState.load_history_line(first_log_entry, None)
        
        did_doc = state.document
        did_doc = append_vm(
            did_doc,
            bind_signing_key(
                did_doc.get('id'), 
                create_key().get('multikey')
            )
        )
        state = state.create_next(
            did_doc,
            {},
            timestamp()
        )
        
        second_log_entry = sign_document(
            state.history_line(), 
            LOG_ENTRY_PROOF_OPTIONS | {'verificationMethod': f'did:key:{update_key}#{update_key}'}
        ).get('securedDocument')
        add_line(second_log_entry)
            
        write_document('did', parallel_did(state.document))
            
    else:
        click.echo(write_document('did', did_doc))

@click.command('new-key')
def new_key():
    """Create new key pair."""
    multikey = create_key().get('multikey')
    click.echo(f'Public Multikey: {multikey}')

@click.command('did-params')
@click.option('--method', default='1.0', help='Method to use.')
@click.option('--update-key', help='Provided update key value to use.')
def set_parameters(method, update_key):
    """Set the DID parameters and update key."""
    
    if method not in SUPPORTED_WEBVH_METHODS:
        raise click.ClickException('Invalid method version.')
    
    parameters = {
        "scid": SCID_PLACEHOLDER,
        "method": f'did:webvh:{method}',
        "updateKeys": [update_key or create_key().get('multikey')]
    }
    
    click.echo(write_document('parameters', parameters))

@click.command('gen-scid-input')
@click.option('--version-time', help='The version time.')
def gen_scid_input(version_time):
    """Generate the scid input."""
        
    scid_input = {
        "versionId": SCID_PLACEHOLDER,
        "versionTime": version_time or timestamp()
    }

    with open('outputs/did.json', 'r') as f:
        scid_input['state'] = json.loads(f.read())
        
    with open('outputs/parameters.json', 'r') as f:
        scid_input['parameters'] = json.loads(f.read())
    
    click.echo(write_document('scid_input', scid_input))

@click.command('gen-scid-value')
def gen_scid_value():
    """Generate the SCID value from the input."""
    
    with open('outputs/scid_input.json', 'r') as f:
        scid_input = json.loads(f.read())
    
    state = DocumentState.initial(
        params=scid_input.get('parameters'),
        document=scid_input.get('state'),
        timestamp=scid_input.get('versionTime')
    )
    write_document('draft_log_entry', state.history_line())
    click.echo(f'Calculated SCID: {state.scid}')
    

def bind_signing_key(controller_id, multikey):
    signing_key = multikey or create_key().get('multikey')
    signing_key_id = f'{controller_id}#{signing_key}'
    update_kid(signing_key, signing_key_id)
    return {
        "id": signing_key_id,
        "type": "Multikey",
        "controller": controller_id,
        "publicKeyMultibase": signing_key
    }
    
@click.command('add-vm')
@click.option('--multikey', help='The Public Multikey value to add.')
def add_vm(multikey):
    """Add a verification method to the did document."""
    
    with open('outputs/draft_log_entry.json', 'r') as f:
        draft_log_entry = json.loads(f.read())
    
    
    verification_method = bind_signing_key(
        draft_log_entry.get('state').get('id'), 
        create_key().get('multikey')
    )
    
    draft_log_entry['state'] = append_vm(draft_log_entry.get('state'), verification_method)
    click.echo(write_document('draft_log_entry', draft_log_entry))

@click.command('gen-version-id')
def gen_version_id():
    """Generate the version ID."""
    
    with open('outputs/did.jsonl', 'r') as f:
        log_entries = [line for line in f.read().split('\n') if line != '']
    
    with open('outputs/draft_log_entry.json', 'r') as f:
        draft_log_entry = json.loads(f.read())
    
    if len(log_entries) == 0:
        scid = draft_log_entry.get('parameters').get('scid')
        state = DocumentState.initial(
            params=insert_placeholder(draft_log_entry.get('parameters'), scid),
            document=insert_placeholder(draft_log_entry.get('state'), scid),
            timestamp=draft_log_entry.get('versionTime')
        )
    else:
        state = next_state(log_entries, draft_log_entry)
        
    write_document('draft_log_entry', state.history_line())
    click.echo(write_document('log_entry', state.history_line()))

@click.command('add-proof')
@click.option('--update-key', help='The update key to use.')
def sign_log_entry(update_key):
    """Add a Data Integrity Proof to the log entry with a provided update key."""
    
    with open('outputs/log_entry.json', 'r') as f:
        log_entry = json.loads(f.read())
        
        
    log_entry.pop('proof', None)

    update_key = update_key or current_state().params.get('updateKeys')[0]
    signed_log_entry = sign_document(
        log_entry, 
        LOG_ENTRY_PROOF_OPTIONS | {'verificationMethod': f'did:key:{update_key}#{update_key}'}
    ).get('securedDocument')
    
    click.echo(write_document('log_entry', signed_log_entry))
        
@click.command('new-line')
def add_log_line():
    """Append line to log file and add alsoKnownAs reference to DID doducment"""
    
    with open('outputs/did.jsonl', 'r') as f:
        log_entries = [line for line in f.read().split('\n') if line != '']
    
    with open('outputs/log_entry.json', 'r') as f:
        log_entry = json.loads(f.read())
        
    version_number = int(log_entry['versionId'].split('-')[0])
        
    if len(log_entries) == version_number-1:
        add_line(log_entry)
        click.echo('New log line added to log file!')
    else:
        click.echo('No log line to add.')
    
    write_document('did', parallel_did(log_entry.get('state')))
        

webvh_cli.add_command(new_did)
webvh_cli.add_command(new_key)
webvh_cli.add_command(set_parameters)
webvh_cli.add_command(gen_scid_input)
webvh_cli.add_command(gen_scid_value)
webvh_cli.add_command(gen_version_id)
webvh_cli.add_command(sign_log_entry)
webvh_cli.add_command(add_log_line)
webvh_cli.add_command(add_vm)
    

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

def insert_placeholder(document, scid=None):
    if scid:
        return json.loads(json.dumps(document).replace(scid, SCID_PLACEHOLDER))
    return json.loads(json.dumps(document).replace('did:web:', f'did:webvh:{SCID_PLACEHOLDER}:'))

def insert_scid(document, scid):
    return json.loads(json.dumps(document).replace(SCID_PLACEHOLDER, scid))
    
def initial_state(state_input):
    return DocumentState(
        params=state_input.get('parameters'),
        params_update=state_input.get('parameters'),
        document=state_input.get('state'),
        timestamp=state_input.get('versionTime'),
        timestamp_raw=state_input.get('versionTime'),
        version_id=state_input.get('versionId') or "",
        last_version_id="",
        version_number=0,
    )

def next_state(previous_log_entries, draft_log_entry):
    state = None
    for log_entry in previous_log_entries:
        state = DocumentState.load_history_line(json.loads(log_entry), state)
    return state.create_next(
        draft_log_entry.get('state'),
        draft_log_entry.get('parameters'),
        make_timestamp()[1]
    )

def current_state():
    state = None
    with open('outputs/did.jsonl', 'r') as f:
        for log_entry in [line for line in f.read().split('\n') if line != '']:
            state = DocumentState.load_history_line(json.loads(log_entry), state)
    return state

def timestamp():
    return make_timestamp()[1]

def parallel_did(state):
    scid = state.get('id').split(':')[2]
    did_doc = json.loads(json.dumps(state).replace(f'did:webvh:{scid}:', 'did:web:'))
    did_doc['alsoKnownAs'] = [state.get('id')]
    return did_doc

def add_line(data):
    with open('outputs/did.jsonl', 'a+') as f:
        f.write(f'{json.dumps(data)}\n')

def create_vm(did_doc, vm):
    return

def append_vm(did_doc, vm):
    
    did_doc['@context'].append(MULTIKEY_CONTEXT)
    did_doc['@context'] = list(set(did_doc['@context']))
    
    did_doc['authentication'] = did_doc.get('authentication', [])
    did_doc['authentication'].append(vm['id'])
    
    did_doc['assertionMethod'] = did_doc.get('assertionMethod', [])
    did_doc['assertionMethod'].append(vm['id'])
    
    did_doc['verificationMethod'] = did_doc.get('verificationMethod', [])
    did_doc['verificationMethod'].append(vm)

    return did_doc