# Deployment

## Backend on Hetzner

Parallax follows LunarSurfaceBackend's production model:

- Dockerized FastAPI service.
- Doppler injects production secrets.
- Cloudflare origin certs are mounted from `/etc/ssl/cloudflare`.
- Port `443` on the host forwards to Uvicorn on `8000`.
- Trading 212 credentials are injected by the backend environment.

Set these before deploying:

```bash
export REMOTE=root@your-hetzner-host
export APP_DIR=/opt/parallax
./hetzner-deploy.sh
```

Required remote prerequisites:

- Docker and Docker Compose.
- Doppler token available as `DOPPLER_TOKEN`.
- Cloudflare origin certs at `/etc/ssl/cloudflare/origin.pem` and `/etc/ssl/cloudflare/origin.key`.
- `TRADING212_API_KEY`, `TRADING212_API_SECRET`, and `TRADING212_ENV` available through Doppler or the remote `.env`.

## Frontend on Firebase

`ParallaxFrontend/firebase.json` is set up like LunarSurface. Once the Firebase project/site exists:

```bash
cd ../ParallaxFrontend
npm run deploy:prod
```

The current hosting site placeholder is `parallax-lunarchain`.

## Temporary Production API Hostname

Until `api.parallax.lunarchain.net` exists in DNS, the deployed frontend uses:

```text
https://parallax-api.46.62.157.149.nip.io
```

This hostname resolves to the Hetzner server and is terminated by Caddy in `ParallaxBackend/docker-compose.hetzner.yml`.

## Cloudflare Access

`lunarchain.net` uses Cloudflare nameservers, but `parallax.lunarchain.net` and `api.parallax.lunarchain.net` still need DNS/custom-hosting setup before Access can protect them. The apply script is in `deploy/cloudflare/apply-zero-trust.py`.
