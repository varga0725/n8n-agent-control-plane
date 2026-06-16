# Installation

## Requirements
- Python 3.10+ (the runtime uses only the standard library).
- An n8n instance with the Public API enabled and an API key.
- Optional (dev): `pytest`, `pyyaml` for tests and policy parsing.

## Run without installing
The package runs straight from source:

```bash
cd n8n-control-plane
export PYTHONPATH=src
python3 -m n8n_cp doctor
```

## Install as a package (optional)
```bash
pip install -e ".[dev]"      # provides the `n8n-cp` console script
n8n-cp discover
```

## Configure
```bash
cp .env.example .env
# edit .env: set N8N_BASE_URL and N8N_API_KEY
```
The CLI reads configuration from the environment. To load a `.env` automatically,
export the vars in your shell or use a tool like `direnv` / `dotenv`; this package
intentionally does not parse `.env` itself (keeps secrets handling explicit).

## Use the skills with an agent
Point your agent at the `skills/` directory (each subfolder has a `SKILL.md`).
The skills call the CLI (`python3 -m n8n_cp ...`) under the hood, so the package
must be importable (`PYTHONPATH=src` or `pip install -e .`).

## Verify
```bash
export PYTHONPATH=src
python3 -m pytest            # unit + contract tests (offline, mock transport)
python3 -m n8n_cp tools      # should list 80 tools
```
