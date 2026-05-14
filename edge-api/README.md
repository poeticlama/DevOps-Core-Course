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

### Live Deployment

Your Worker is deployed and accessible at:
**https://edge-api.poeticlama.workers.dev**

### Available Endpoints

- `GET /` - App metadata
- `GET /health` - Health check
- `GET /edge` - Edge location and metadata
- `GET /counter` - Get and increment visit counter
- `POST /counter` - Reset counter to 0
- `GET /info` - Deployment information

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

