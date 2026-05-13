# edge-api

Cloudflare Workers Edge API - DevOps Core Course Lab 17

## Quick Start

```bash
npm install
npx wrangler dev
```

## Deployment

```bash
npx wrangler deploy
```

## Configuration

Create secrets:
```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

Create KV namespace:
```bash
npx wrangler kv namespace create SETTINGS
```

Update `wrangler.jsonc` with namespace IDs.

## Routes

- `GET /` - App information
- `GET /health` - Health check
- `GET /edge` - Edge metadata
- `GET /counter` - Increment counter
- `POST /counter` - Reset counter
- `GET /info` - Deployment info

## Documentation

See `WORKERS.md` for complete Lab 17 documentation.

