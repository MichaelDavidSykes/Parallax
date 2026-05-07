# Cloudflare Access

Parallax should be protected behind Cloudflare Access once it has a Cloudflare-managed hostname, for example:

```text
parallax.lunarchain.net
api.parallax.lunarchain.net
```

The current Firebase `web.app` URL cannot be protected by Cloudflare Access directly. Add the custom hostname in Firebase Hosting, proxy it through Cloudflare, then apply the Access application.

## Apply

```bash
export CLOUDFLARE_API_TOKEN=...
export CLOUDFLARE_ACCOUNT_ID=...
export PARALLAX_ACCESS_DOMAIN=parallax.lunarchain.net
export PARALLAX_ALLOWED_EMAILS=you@example.com

python3 deploy/cloudflare/apply-zero-trust.py
```

The API token needs Cloudflare Zero Trust Access app/policy write permission.

For the backend hostname, run the script again with:

```bash
export PARALLAX_ACCESS_DOMAIN=api.parallax.lunarchain.net
python3 deploy/cloudflare/apply-zero-trust.py
```
