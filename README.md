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

A Cloudflare Pages project connected to this repository builds the site from
`main` on every push. Its settings, all in the Pages dashboard, are a maintainer
step; no token lives in the repository:

| Setting | Value |
| --- | --- |
| Production branch | `main` |
| Root directory | the repository root |
| Build command | `python3 build.py` |
| Build output directory | `out` |
| Environment variable `SITE_URL` | the origin the project serves, for example `https://next.uberblick.ai`; omitted, the canonical links name `https://uberblick.ai` |
| Environment variable `SITE_NOINDEX` | set to `1` on a host search engines should not index |
| Custom domain | the host name; Cloudflare adds the DNS record when the zone is on Cloudflare, otherwise add a CNAME to the project's `pages.dev` host |

The new site runs on next.uberblick.ai first, from a project with
`SITE_URL=https://next.uberblick.ai` and `SITE_NOINDEX=1`; uberblick.ai stays as
it is until the move. A release in uberblick-2 does not trigger a build here, so
the home page's Recent changes list catches up with the next push to this
repository (or a manual deploy in the Pages dashboard). Pages serves `404.html` for unknown paths and redirects
`/<path>.html` to `/<path>`, which is why the build writes extensionless pages.
