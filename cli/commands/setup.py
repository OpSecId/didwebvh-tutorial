import click
import json
from did_webvh.core.date_utils import make_timestamp
from did_webvh.core.state import DocumentState
from .utils import (
    insert_placeholder, 
    insert_scid, 
    setup_files, 
    write_document, 
    origin_to_did, 
    create_key, 
    add_also_known_as,
    initial_state
)
from ..main import DID_CORE_CONTEXT, WEBVH_METHODS, SCID_PLACEHOLDER

@click.command('new-did-config')
@click.option('--origin', help='The DID location URL.')
def new_did_config(origin):
    """Configure the base did document from a DID location URL."""
    
    if not origin:
        raise click.ClickException('Missing DID location URL.')
        
    setup_files()
    
    did_doc = {
        "@context": [DID_CORE_CONTEXT],
        "id": origin_to_did(origin)
    }
    
    click.echo(write_document('did', did_doc))

@click.command('set-parameters')
@click.option('--method', default='1.0', help='Method to use.')
def set_parameters(update_key, method):
    """Set the DID parameters and update key."""
    
    if method not in WEBVH_METHODS:
        raise click.ClickException('Invalid method version.')
    
    parameters = {
        "scid": SCID_PLACEHOLDER,
        "method": f'did:webvh:{method}',
        "updateKeys": [create_key().get('multikey')]
    }
    
    click.echo(write_document('parameters', parameters))

@click.command('gen-scid-input')
@click.option('--version-time', help='The version time.')
def gen_scid_input(version_time):
    """Generate the scid input."""

    with open('outputs/did.json', 'r') as f:
        did_doc = json.loads(f.read())
        
    with open('outputs/parameters.json', 'r') as f:
        parameters = json.loads(f.read())
        
    scid_input = {
        "versionTime": version_time or make_timestamp()[1],
        "parameters": parameters,
        "state": insert_placeholder(did_doc)
    }
    
    click.echo(write_document('scid_input', scid_input))

@click.command('gen-scid-value')
def gen_scid_value():
    """Generate the SCID value from the input and add alsoKnownAs reference to DID doducment."""
    
    with open('outputs/scid_input.json', 'r') as f:
        scid_input = json.loads(f.read())
        
    # genesis = DocumentState.initial(
    #     params=scid_input.get('parameters'),
    #     document=scid_input.get('state'),
    #     timestamp=scid_input.get('versionTime')
    # )
        
    genesis = initial_state(scid_input)
    add_also_known_as(genesis.document.get('id'))
    draft_log_entry = insert_scid(scid_input, genesis.scid)
    
    click.echo(write_document('draft_log_entry', draft_log_entry))