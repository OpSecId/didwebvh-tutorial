# WebVH Tutorial

## Task 1: Set Up Your Environment

### GH Page & Repository

Create a new repo from this [template](https://github.com/new?template_name=didwebvh-tutorial&template_owner=OpSecId)
Enable GH pages Settings -> Pages
Set the source to Deploy from a branch
Deploy from the main branch `/(root)` directory

### Docker & CLI

```bash
# Clone tutorial repo and cd into root directory
git clone https://github.com/opsecid/didwebvh-tutorial
cd didwebvh-tutorial

# Ensure docker is properly configured
docker compose version

# Build and start the tutorial containers
docker compose up -d --build

# To clear the agent wallet and restart
docker compose up -d --build --force-recreate

# Confirm cli container is functional
docker exec webvh-tutorial-cli webvh

# Create cli alias
alias webvh-cli="docker exec webvh-tutorial-cli webvh"

# Confirm alias is registered
webvh-cli --help

```

## Task 2: Create the first log entry

```bash
# Run the new-did command, using the gh-page url as the origin value
webvh-cli new-did --origin https://example.com

# Create the authorization key pair
webvh-cli new-key

# Define the DID parameters
webvh-cli did-params --update-key <multikey> --method 0.5

# Generate the SCID input file with a current timestamp
webvh-cli gen-scid-input --version-time <datetime>

```

## Task 3: Generate the SCID (Self-Certifying Identifier)

```bash
# Run the following command to generate the scid value and add an alsoKnownAs reference to our DID document:
webvh-cli gen-scid-value

```

## Task 4: Generate the Version ID (Entry Hash)

Run the following command to generate the version ID:
`webvh-cli gen-version-id`

## Task 5: Generate the Data Integrity Proof

Run the following command to sign the log entry with the update key, and add the line to our log file:
`webvh-cli add-proof --update-key <>`

## Task 6: Publish the DID Log Entry

Use the new-line command to add the current line to the log file
`webvh-cli new-line`

Commit the `did.json` and `did.jsonl` files and their content at the root of the repository you created at step one.

## Task 7: Resolve the DID

Resolve your DID with the tutorial agent
http://agent.webvh-tutorial.localhost/api/doc#/resolver/get_resolver_resolve__did_

You can also visit https://uniresolver.io

You can resolve both the webvh and web did.

## Task 8: Update the DID

```bash
# Create a keypair and add a verification method
webvh-cli new-key
webvh-cli add-vm --multikey <>

# Generate the new version ID and sign the log entry
webvh-cli gen-version-id
webvh-cli add-proof --update-key <>

# Add to the log file
webvh-cli new-line

```

Resolve your DID again.



## Commands
```bash
_________________________________________________________________
Usage: webvh [OPTIONS] COMMAND [ARGS]...

  WebVH Tutorial

Options:
  --help  Show this message and exit.

Commands:
  add-proof       Add a Data Integrity Proof to the log entry with a...
  add-vm          Add a verification method to the did document.
  did-params      Set the DID parameters and update key.
  gen-scid-input  Generate the scid input.
  gen-scid-value  Generate the SCID value from the input.
  gen-version-id  Generate the version ID.
  new-did         Configure the base did document from a DID location URL.
  new-key         Create new key pair.
  new-line        Append line to log file and add alsoKnownAs reference...
_________________________________________________________________
Usage: webvh new-did [OPTIONS]

  Configure the base did document from a DID location URL.

Options:
  --auto         Automate creation.
  --origin TEXT  The DID location URL.
_________________________________________________________________
Usage: webvh did-params [OPTIONS]

  Set the DID parameters and update key.

Options:
  --method TEXT      Method to use.
  --update-key TEXT  Provided update key value to use.
_________________________________________________________________
Usage: webvh gen-scid-input [OPTIONS]

  Generate the scid input.

Options:
  --version-time TEXT  The version time.
_________________________________________________________________
Usage: webvh add-proof [OPTIONS]

  Add a Data Integrity Proof to the log entry with a provided update key.

Options:
  --update-key TEXT  The update key to use.
_________________________________________________________________
```