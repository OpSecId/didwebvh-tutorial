import click
import json
from did_webvh.core.state import DocumentState
from .utils import (write_document, sign_document, initial_state, next_state)
from ..main import HASH_INFO, LOG_ENTRY_PROOF_OPTIONS

@click.command('gen-version-id')
def gen_version_id(next):
    """Generate the version ID."""
    
    with open('outputs/did.jsonl', 'r') as f:
        log_lines = json.loads(f.read().split('\n'))
    
    with open('outputs/draft_log_entry.json', 'r') as f:
        draft_log_entry = json.loads(f.read())
        
    if not log_lines:
        state = initial_state(draft_log_entry)
    else:
        state = next_state(log_lines[-1], draft_log_entry)
        
    log_entry = state.history_line()
    # log_entry = {'versionId': version_id} | draft_log_entry
    
    click.echo(write_document('log_entry', log_entry))

@click.command('sign-log-entry')
@click.option('--key', help='The update key to use.')
@click.option('--insert', is_flag=True, default=False, help='Insert signed log line in log file.')
def sign_log_entry(key, insert):
    """Add a Data Integrity Proof to the log entry with a provided update key."""
    
    with open('outputs/log_entry.json', 'r') as f:
        log_entry = json.loads(f.read())
        
    update_key = key or log_entry.get('parameters').get('updateKeys')[0]
    
    signed_log_entry = sign_document(
        log_entry, 
        LOG_ENTRY_PROOF_OPTIONS | {'verificationMethod': f'did:key:{update_key}#{update_key}'}
    ).get('securedDocument')
    
    if insert:
        with open('outputs/did.jsonl', 'a+') as f:
            f.write(f'{json.dumps(signed_log_entry)}\n')
        
        click.echo('New log line added to log file!')
    
    click.echo(write_document('signed_log_entry', signed_log_entry))
    
    

# @click.command('add-vm')
# @click.option('--key-id', help='The key id.')
# @click.option('--key-alg', default='ed25519', help='The key pair algorithm.')
# @click.option('--key-type', default='multikey', help='The public key type.')
# def add_vm(key_id, key_alg='ed25519', key_type='multikey'):
#     """Add a verification method to the did document."""
    
#     with open('outputs/log_entry.json', 'r') as f:
#         log_entry = json.loads(f.read())

    
#     signing_key = create_key().get('multikey')
#     controller_id = log_entry.get('state').get('id')
#     signing_key_id = f'{controller_id}#{signing_key}'
    
#     update_kid(signing_key, signing_key_id)
#     verification_method = {
#         "id": signing_key_id,
#         "type": "Multikey",
#         "controller": controller_id,
#         "publicKeyMultibase": signing_key
#     }
    
#     did_document = log_entry.get('state')
    
#     did_document['@context'].append(MULTIKEY_CONTEXT)
#     did_document['@context'] = list(set(did_document['@context']))
    
#     did_document['verificationMethod'] = did_document.get('verificationMethod') or []
#     did_document['verificationMethod'].append(verification_method)
    
#     did_document['assertionMethod'] = did_document.get('assertionMethod') or []
#     did_document['assertionMethod'].append(verification_method['id'])
    
#     did_document['authentication'] = did_document.get('authentication') or []
#     did_document['authentication'].append(verification_method['id'])
    
#     log_entry['state'] = did_document
    
#     write_document('log_entry', log_entry)
    
#     click.echo(write_document('log_entry', log_entry))
        

# @click.command('add-log-line')
# @click.option('--new/--existing', default=False, help='Add a log line to a new or existing log file.')
# def add_log_line(new):
    
#     with open('outputs/signed_log_entry.json', 'r') as f:
#         signed_log_entry = json.loads(f.read())
    
#     log_line = f'{json.dumps(signed_log_entry)}\n'
#     mode = 'w+' if new else 'a+'
        
#     with open('outputs/did.jsonl', mode) as f:
#         f.write(log_line)
    
#     click.echo('New log line added to log file!')