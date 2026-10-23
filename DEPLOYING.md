# Deploying uberblick.ai

The site is a Cloudflare Worker with static assets, described in
`wrangler.jsonc`. Every push to `main` runs `.github/workflows/deploy.yml`,
which builds `out/` and runs `wrangler deploy`. The first deploy creates the
Worker `uberblick-ai` and its routes `uberblick.ai/*` and `www.uberblick.ai/*`
in the uberblick.ai zone. Nothing is configured in the Cloudflare dashboard;
the dashboard only shows what wrangler deployed.

## The two secrets

| Name | What it is | Where it lives |
| --- | --- | --- |
| `CLOUDFLARE_ACCOUNT_ID` | The account that owns the uberblick.ai zone. Not secret, but kept beside the token so the workflow has one place to look. | GitHub repository secret |
| `CLOUDFLARE_API_TOKEN` | A token wrangler uses to upload the Worker and set its routes. | GitHub repository secret |

The account id is on the right of the zone's Overview page in the Cloudflare
dashboard, and in the URL of every dashboard page as the first path segment.

### Creating the token

1. Cloudflare dashboard → profile menu → **My Profile** → **API Tokens** →
   **Create Token** → **Create Custom Token**.
2. Name it `uberblick.ai deploy` and give it exactly these permissions:
   - Account › **Workers Scripts** › Edit
   - Zone › **Workers Routes** › Edit, with Zone Resources set to the single
     zone `uberblick.ai`
3. Leave client IP filtering and the TTL empty, unless you want the rotation
   below to be forced on a date.
4. **Continue to summary** → **Create Token**, and copy the value once. It is
   not shown again.

The token can deploy Workers and change Worker routes in this one zone. It
cannot read or change DNS, the WAF rules, Pages projects or the hub's records,
so the legacy app and hub.uberblick.ai are outside its reach.

### Storing it

GitHub: repository **Settings → Secrets and variables → Actions → New
repository secret**, once for `CLOUDFLARE_API_TOKEN` and once for
`CLOUDFLARE_ACCOUNT_ID`.

Nowhere else. A deploy from a laptop needs no copy of the token: `npx wrangler
login` once opens the browser and stores wrangler's own login under
`~/.config/.wrangler`, then `mise run deploy` builds and deploys.

## Rotating the token

1. Create a new token as above. The old one keeps working meanwhile.
2. Replace the value of the GitHub secret `CLOUDFLARE_API_TOKEN`
   (**Settings → Secrets and variables → Actions**, pencil icon). Laptops
   need nothing; they use their own wrangler login.
3. Prove the new token works: **Actions → deploy → Run workflow** on `main`,
   and wait for the green run.
4. Revoke the old token: **My Profile → API Tokens**, the row's menu, **Delete**.
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
- Everything back to the legacy app: delete the Worker's two routes
  (**Workers & Pages → uberblick-ai → Settings → Domains & Routes**) or run
  `wrangler delete`. The DNS record still points at the legacy origin, so the
  old site returns at once.
