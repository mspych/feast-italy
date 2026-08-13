# Feast Italy Price Monitor — Operations

## Canonical Railway project

| Item | Value |
|------|-------|
| **Canonical project** | `feast-italy` |
| **Canonical service** | `feast-italy` |
| **GitHub repo** | `mspych/feast-italy` |
| **Duplicate / do not use** | `determined-magic` (stray worker without Airtable vars) |

Always link and deploy against **`feast-italy`**, never `determined-magic`.

```bash
cd /path/to/feast-italy
railway link --project feast-italy
railway service link feast-italy
railway status
```

## Required environment variables

Set these on the **`feast-italy`** Railway service (Variables tab):

| Variable | Required | Notes |
|----------|----------|-------|
| `AIRTABLE_API_KEY` | yes | Personal access token |
| `AIRTABLE_BASE_ID` | yes | Airtable base ID (`app…`) |
| `AIRTABLE_PRODUCTS_TABLE` | no | Default: `Products` |
| `AIRTABLE_PRICE_HISTORY_TABLE` | no | Default: `Price History` |
| `SHOPIFY_STORE_DOMAIN` | no | Default: `feastitaly.com` |

Do **not** commit secrets. Copy from Railway dashboard or a local `.env` (gitignored).

## Deploy

```bash
# From the feast-italy repo, linked to the feast-italy project
railway link --project feast-italy
railway service link feast-italy

# Preflight against Railway vars (requires CLI auth)
railway run python scripts/preflight.py
# or:
railway run python main.py --check-config

# Push to main (if GitHub auto-deploy is connected), or:
railway up
```

Cron schedule (from `railway.toml`): `0 */6 * * *` (every 6 hours).  
Restart policy: `NEVER` (one-shot worker; failures must not loop).

## Stop / pause

```bash
# Remove the latest deployment (stops the current/crashed run)
railway down -y

# Or disable cron by clearing cronSchedule in railway.toml, push, then
# remove any active deployment with railway down -y
```

## Quarantine: `determined-magic`

`determined-magic` was a duplicate Railway project that auto-deployed this repo **without** Airtable variables, causing crash emails.

**Status (2026-08-13):** GitHub source disconnected, cron cleared, no active deployment. Safe to leave idle or delete the project later.

Policy:

1. Keep **no active deployment** on `determined-magic`.
2. Do not reconnect its GitHub source to this repo.
3. Do **not** copy secrets into it unless you deliberately promote it to replace `feast-italy`.

```bash
railway link --project determined-magic
railway service status --all
# Expected: NO DEPLOYMENT (and no connected repo)
```

## Recovery after a failed deploy

1. Confirm you are on the **canonical** project: `railway status` must show `feast-italy`.
2. Confirm vars exist: `railway variables` (look for `AIRTABLE_API_KEY` / `AIRTABLE_BASE_ID` by name).
3. Keep `restartPolicyType = "NEVER"` so failures exit once.
4. Inspect logs: `railway logs`
5. Fix config or code, redeploy once, verify logs show real product checks.

## Local development

```bash
cp .env.example .env   # fill in Airtable values
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python main.py --check-config
.venv/bin/python main.py
.venv/bin/python sync_products.py   # optional: import collection into Airtable
```
