# Parallax Models

Each model lives in its own folder with:

- `model.json` for registry metadata.
- `Dockerfile` for the model image.
- `model.py` or equivalent runtime entrypoint.

The first model, `stat_arb_v1`, mirrors the built-in strategy and defines the contract custom models should follow: read one JSON payload from stdin and write `{ "signals": [...] }` to stdout.
