# Parallax

Parallax is LunarChain's quantitative trading platform. It starts with Polymarket data, simulated trading, arbitrage scanning against external statistical signals, and modular backtesting.

## Shape

This mirrors the LunarChain setup:

- `ParallaxFrontend`: Angular 17 app, Firebase hosting config, environment-specific API URLs.
- `ParallaxBackend`: FastAPI service, Docker/Doppler deployment, local SQLite paper-trading database.
- `ParallaxEngine`: Prefect flows for recurring ingestion, opportunity scans, and backtest runs.
- `deploy`: Hetzner deployment helper and production notes.

## Local Backend

```bash
cd ParallaxBackend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8010
```

Then seed the system:

```bash
curl -X POST 'http://localhost:8010/api/v1/markets/sync?limit=40'
curl -X POST http://localhost:8010/api/v1/opportunities/scan \
  -H 'content-type: application/json' \
  -d '{"market_limit":40,"min_edge":0.04,"refresh_markets":false}'
```

## Local Frontend

```bash
cd ParallaxFrontend
npm install
npm run start:local -- --port 4202
```

The app will use `http://localhost:8010/api/v1`.

## Prefect

```bash
cd ParallaxEngine
python -m parallax_engine_prefect ingest --market-limit 80 --min-edge 0.04
python -m parallax_engine_prefect backtest --initial-cash 10000
```

## Integration Points

External statistical signals are intentionally modular:

- Production frontend: `https://parallax-lunarchain.web.app`
- Production API fallback hostname: `https://parallax-api.46.62.157.149.nip.io`
- `DRAFT_API_URL` should expose a `/probabilities` endpoint returning `fair_probability`, `confidence`, and optional `rationale`.
- `LUNARCHAIN_API_URL` should expose `/api/v1/signals/polymarket`.
- If neither is configured, Parallax uses a low-confidence local statistical prior so the app stays usable.

Custom strategy models belong under `ParallaxBackend/backend/strategies` and are registered in `BacktestService._strategy_for`.
