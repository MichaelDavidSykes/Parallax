# Parallax Backend

FastAPI service for the simplified Parallax trading platform.

Current product surface:

- Trading 212 account summary through `/api/v1/trading212/summary`.
- Trading 212 trade-derived chart data through `/api/v1/trading212/chart`.
- Trading 212 market order proxy through `/api/v1/trading212/orders/market`.
- Empty automation registry through `/api/v1/automations`.

## Local

```bash
cd ParallaxBackend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8010
```

## Trading 212

Set these in the backend environment:

```bash
TRADING212_ENV=demo
TRADING212_API_KEY=...
TRADING212_API_SECRET=...
```

Use `TRADING212_ENV=live` only when you want real Trading 212 live-account access.
