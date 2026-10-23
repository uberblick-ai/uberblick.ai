# Deploying uberblick.ai

The site is a Cloudflare Worker with static assets, described in
`wrangler.jsonc`. Every push to `main` runs `.github/workflows/deploy.yml`,
which builds `out/` and runs `wrangler deploy`. The first deploy creates the
Worker `uberblick-ai`; every later one updates its script and assets. The
routes that put it in front of `uberblick.ai/*` and `www.uberblick.ai/*` are
Terraform's, in [uberblick-infra](https://github.com/uberblick-ai/uberblick-infra)
(`cloudflare/website.tf`), so going live and rolling back are an apply there.
Nothing is configured in the Cloudflare dashboard.

## The two secrets

| Name | What it is | Where it lives |
| --- | --- | --- |
| `CLOUDFLARE_ACCOUNT_ID` | The account that owns the uberblick.ai zone. Not secret, but kept beside the token so the workflow has one place to look. | GitHub organisation secret |
| `CLOUDFLARE_API_TOKEN` | A token wrangler uses to upload the Worker. | GitHub organisation secret |

The account id is on the right of the zone's Overview page in the Cloudflare
dashboard, and in the URL of every dashboard page as the first path segment.

### Creating the token

Cloudflare grants Workers access through roles since September 2026, and the
roles decide what wrangler may do. The deploy needs the **Editor** role on the
**Workers product** (all Workers in the account); a token scoped to specified
Workers fails with "No access to the specified service", and the legacy
"Workers Scripts Edit" permission is not what the dashboard offers any more.

1. Cloudflare dashboard → **Manage Account** → **Account API Tokens** →
   **Create Token** → **Create Custom Token**. An account-owned token stays
   with the account when people come and go; a token under My Profile belongs
   to one person.
2. Name it `uberblick.ai deploy` and give it exactly one permission:
   **Workers**, scope **All Workers**, role **Editor**.
3. Leave client IP filtering and the TTL empty, unless you want the rotation
   below to be forced on a date.
4. **Continue to summary** → **Create Token**, and copy the value once. It is
   not shown again.

Editor deploys an existing Worker. Creating a Worker that does not exist yet
needs the **Admin** role once; the Worker `uberblick-ai` exists, so the deploy
token does not need it. The token can deploy Workers in the account and
nothing else: no routes, no DNS, no WAF rules, no Pages projects, so the
legacy app, hub.uberblick.ai and which domain the Worker answers on are
outside its reach.

### Storing it

GitHub: organisation **Settings → Secrets and variables → Actions → New
organization secret**, once for `CLOUDFLARE_API_TOKEN` and once for
`CLOUDFLARE_ACCOUNT_ID`, with repository access **Selected repositories**
and only this repository picked. The token can edit every Worker in the
Cloudflare account, so a secret open to all repositories would let any
workflow in the organisation deploy any Worker. A repository secret of the
same name would win over the organisation one; keep none, so there is one
place to rotate.

Nowhere else. A deploy from a laptop needs no copy of the token: `npx wrangler
login` once opens the browser and stores wrangler's own login under
`~/.config/.wrangler`, then `mise run deploy` builds and deploys.

## Rotating the token

1. Create a new token as above. The old one keeps working meanwhile.
2. Replace the value of the organisation secret `CLOUDFLARE_API_TOKEN`
   (organisation **Settings → Secrets and variables → Actions**, pencil icon). Laptops
   need nothing; they use their own wrangler login.
3. Prove the new token works: **Actions → deploy → Run workflow** on `main`,
   and wait for the green run.
4. Revoke the old token: **Manage Account → Account API Tokens**, the row's menu, **Delete**.
   Deleting first and checking later leaves no way to deploy until a new token
   is in place, so keep this order.

Rotate immediately when a token may have leaked (a pasted log, a lost laptop,
a fork of this repository with Actions enabled), and otherwise once a year.
The account id does not rotate; it changes only when the zone moves to another
Cloudflare account.

## Checking a deploy

```sh
curl -sI https://uberblick.ai/ | head -1               # 200, the site
curl -sI https://uberblick.ai/docs/install | head -1   # 200, a page
curl -sI https://uberblick.ai/nothing-here | head -1   # 404, the site's 404.html
curl -sI https://uberblick.ai/app | head -1            # the legacy app answers (302 to sign-in when logged out)
curl -s  https://uberblick.ai/.well-known/oauth-protected-resource | head -c 200   # the legacy MCP discovery JSON
```

The Worker's own logs are under **Workers & Pages → uberblick-ai → Logs** in
the dashboard; `wrangler.jsonc` turns observability on.

## Rolling back

- A bad page: revert the commit on `main`; the push deploys the previous site.
- A broken Worker: **Workers & Pages → uberblick-ai → Deployments → Rollback**
  to the previous version, then fix forward.
- Everything back to the legacy app: remove the two routes in uberblick-infra
  (`cloudflare/website.tf`, then `mise run cf-apply` there). The DNS record
  still points at the legacy origin, so the old site returns at once; the
  Worker stays deployed but unreachable.
