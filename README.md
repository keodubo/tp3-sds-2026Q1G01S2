# tp3-sds-2026Q1G01S2

Persistent wiki plus Python foundation for `Sistema 1` of SDS TP3.

## Repo Layers
- `docs/raw/`: immutable source material.
- `docs/wiki/`: synthesized markdown wiki maintained by the agent.
- `src/tp3_sds/`: Python package with wiki helpers and the `Sistema 1` event-driven engine foundation.
- `configs/`: example simulation configs.

## Local Usage
Run directly from the repo root without installing:

```bash
PYTHONPATH=src python3 -m tp3_sds wiki search "scanning rate"
PYTHONPATH=src python3 -m tp3_sds wiki refresh-index
PYTHONPATH=src python3 -m tp3_sds wiki lint
PYTHONPATH=src python3 -m tp3_sds system1 validate-config --config configs/system1.example.toml
PYTHONPATH=src python3 -m tp3_sds system1 run --config configs/system1.example.toml
```

If you want the `tp3` command directly, install the package in editable mode inside your preferred environment:

```bash
python3 -m pip install -e .
```

## Tests

```bash
pytest -q
```
