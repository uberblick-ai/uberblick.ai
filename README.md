# uberblick.ai

The product site, built from this repository into `out` and served by
Cloudflare Pages. The product itself lives in
[uberblick-2](https://github.com/uberblick-ai/uberblick-2); the site reads its
`CHANGELOG.md` and newest release tag from GitHub at build time. The intent behind it is the corpus page "Website:
uberblick.ai" (b243d85e-4c29-4a38-9b78-2636bc7e22f6): which pages exist, what
each holds, and the web UI conventions the site shares with the app.

```sh
python3 build.py                             # standard-library Python, no dependencies
python3 -m http.server 8000 --directory out  # then open http://127.0.0.1:8000/
npx -y @biomejs/biome@2.5.9 lint --error-on-warnings .   # what CI runs on the CSS
```

- `pages/<path>.html` is the page served at `/<path>`: a `<head>` block with
  the title, description and the page's own stylesheet, then the page's main
  content. The build adds the shell every page shares (top bar with the newest
  release tag, the docs sidebar, the "Who builds this" footer); the sidebar
  links and the footer text live in `build.py`. `pages/index.html` is `/`;
  `pages/404.html` is the not-found page.
- `static/` is copied as it is: `shared.css` (the look the site shares with
  agents.uberblick.ai and skills.uberblick.ai: IBM Plex from Google Fonts, the
  violet accent, the shell, the block frame), `css/` (one stylesheet per page
  kind), `fonts/` (the web app's Geist and Fraunces files with their licences,
  used only by the landing page's demo frame, which shows the editor as it is),
  the favicon and touch icon (the same files as the web app's in
  `packages/web/public`) and `_headers`.
- The home page's Recent changes list is built from uberblick-2's
  `CHANGELOG.md`: the five newest release sections, each with its date and
  summary paragraph. Edit the changelog there, not the page. A `CHANGELOG.md`
  in the parent directory is used instead when one exists, so a checkout
  beside uberblick-2 builds offline.
- Links are root-relative, so serve the output rather than opening the files.
  The build lists links to pages that are not written yet.

The three sites share one layout and one footer text; agents.uberblick.ai and
skills.uberblick.ai carry their own copies of the stylesheet until they switch
to linking this one.

## Deploying

`.github/workflows/deploy.yml` builds the site and deploys it as the Cloudflare
Worker in `wrangler.jsonc` on every push to `main`, and by hand from the Actions
tab. The Worker serves `out/` as static assets; the routes `uberblick.ai/*`
and `www.uberblick.ai/*` that put it in front of the domain are Terraform's,
in uberblick-infra (www and next redirect to the apex). `worker/index.js` passes
the legacy Rails app's paths, such as `/app`, `/mcp` and the OAuth endpoints,
to the origin behind the uberblick.ai DNS record, so that app keeps working
until it is shut down; the list of paths lives in that file, and the landing
page's "Legacy login" button in `build.py` goes with it. DNS and the WAF rules
stay as they are. Removing the routes in uberblick-infra puts the legacy app
back in front of everything.

The workflow deploys with two repository secrets, `CLOUDFLARE_ACCOUNT_ID` and
`CLOUDFLARE_API_TOKEN`. [DEPLOYING.md](DEPLOYING.md) says how to create,
rotate and check them, and how to deploy from a laptop.

A release in uberblick-2 does not trigger a deploy here, so the home page's
Recent changes list catches up with the next push to this repository or a
manual run of the deploy workflow. Unknown paths get `404.html`; `/<path>/`
redirects to `/<path>`, which the build writes as `out/<path>/index.html`.
`SITE_URL` and `SITE_NOINDEX` (see the top of `build.py`) are build-time
settings for a second host.

## Working locally

[mise](https://mise.jdx.dev) installs Node and Python from `mise.toml`:

```sh
mise trust mise.toml
mise run serve   # build, then serve on http://localhost:8787 with the Worker's routing
mise run lint    # Biome, then a wrangler dry run
mise run ci      # build, then lint: what CI runs
```

The legacy paths have no origin on localhost; everything else behaves as on
uberblick.ai, including the 404 page and the redirects from `static/_redirects`.
