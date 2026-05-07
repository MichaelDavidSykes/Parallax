# Parallax Engine

Prefect orchestration for Parallax, modeled after `LunarEngine/lunar_engine_prefect`.

## Local

```bash
cd ParallaxEngine
python -m parallax_engine_prefect ingest --market-limit 80 --min-edge 0.04
python -m parallax_engine_prefect backtest --initial-cash 10000
```

The CLI runs as plain Python if Prefect is not installed, and uses Prefect decorators automatically inside a Prefect environment. Set `PARALLAX_BACKEND_URL` when the backend is not on `http://localhost:8010`.

For a worker/deployment environment:

```bash
python -m venv .venv_prefect
. .venv_prefect/bin/activate
pip install -r requirements-prefect.txt
```
