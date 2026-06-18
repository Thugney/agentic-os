# Validation

Validation for the Agentic OS product-direction, Capability manifest, Spaces, and view-only Canvas update.

## Commands run on fresh branch clone

```bash
python -m compileall backend
pytest -q
npm --prefix frontend install
npm --prefix frontend audit --audit-level=moderate
npm --prefix frontend run build
```

## Results

- `python -m compileall backend`: passed.
- `pytest -q`: passed, 3 tests.
- `npm --prefix frontend install`: passed.
- `npm --prefix frontend audit --audit-level=moderate`: passed; npm reported `found 0 vulnerabilities`.
- `npm --prefix frontend run build`: passed; Vite produced `frontend/dist` assets.
- Docker validation could not run in this execution environment because `docker: command not found`.

## Functional coverage added

- `/api/settings/effective` returns capabilities and spaces from YAML.
- Frontend Canvas page builds a view-only graph from effective settings.
