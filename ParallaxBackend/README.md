# Parallax Backend

FastAPI service for the Parallax quantitative trading platform.

It follows the LunarSurfaceBackend shape:

- `backend/main.py` wires the API, CORS, request metadata, and startup database setup.
- `backend/api/endpoints` owns route modules.
- `backend/services` owns trading, scanning, portfolios, and backtesting workflows.
- `backend/integrations` owns Polymarket, LunarChain, and Draft API adapters.
- Binance Spot market data is read-only and public by default.
- Trading 212 account data is read-only until `TRADING212_API_KEY` and `TRADING212_API_SECRET` are configured.
- `backend/strategies` is where custom model-backed strategies can be added.

## Local

```bash
cd ParallaxBackend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8010
```

The default database is `./data/parallax.db`.

## Docker

```bash
docker compose -f docker-compose.local.yml up --build
```

Production mirrors LunarChain's Doppler + Cloudflare origin cert pattern:

```bash
docker compose up --build -d
```

## Key API Calls

```bash
curl http://localhost:8010/api/v1/health
curl -X POST 'http://localhost:8010/api/v1/markets/sync?limit=25'
curl -X POST http://localhost:8010/api/v1/opportunities/scan \
  -H 'content-type: application/json' \
  -d '{"market_limit":25,"min_edge":0.04,"refresh_markets":true}'
```
