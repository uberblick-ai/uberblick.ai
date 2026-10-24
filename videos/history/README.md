# Document history video

The recording on `/docs/history` (`static/video/history-{light,dark}.mp4`,
posters `static/img/history-{light,dark}.webp`). This folder is not
published; it holds what a re-cut needs, for example after the history UI
changes.

## Storyline

About 38 s, under a minute, the same beats in light and dark:

1. All documents, then open **Web UI system** from the sidebar.
2. `‹` beside the revision id opens the history on 1 of 9. Rest a moment.
3. `‹` to 2 of 9, `‹` to 3 of 9. No hovering over the ruler or the sidebar.
4. At 3 of 9, click the bar of unchanged blocks above the change ("18
   unchanged blocks" in the take), then scroll gently until the change is in
   view.
5. `‹` once more to 4 of 9 and rest.
6. **Back to now**, and a calm live frame to the end.

No Collapse unchanged, no previous/next change buttons. The page is Web UI
system (`622ca00f-3dbd-4f65-b749-e46a81e704c4`) in the workspace we build
Uberblick in (`722007fa-8921-45ee-a580-e20311030fef`); its revisions change a
sentence or a short section each. When the page gains revisions, every step
lands one later and the bar's count changes: pick the bar nearest the change
and update the `filter` in `record.mjs`.

## Recording without touching the workspace

History comes from the hub, so the take runs against the real workspace, but
on a copy so nothing is written:

1. Copy the replica with `sqlite3 <ws>.sqlite ".backup <copy>"` from a
   read-only open, and `cp -Rp ~/.config/uberblick` into a scratch folder.
2. From a uberblick-2 checkout with the web bundle built:
   `XDG_DATA_HOME=<scratch>/data XDG_CONFIG_HOME=<scratch>/config
   UB_WORKSPACE_ID=722007fa-8921-45ee-a580-e20311030fef
   UB_HUB_URL=wss://hub.uberblick.ai/ws BROWSER=none
   mise exec -- ub open --no-browser --port 5199`
3. Exchange the launch link once in Playwright and save the storage state.
4. `node record.mjs <playwright index.mjs> <storageState.json> <outDir> light`,
   then again with `dark`. It writes a WebM per run and `timing.json` with the
   beat log; `start` is the time to trim off the front.
5. Delete the scratch config copy afterwards: it holds credentials.

Edit, name or restore nothing during the run.

## Encoding

Trim `start` seconds (about 1.85), then for the site:

```sh
ffmpeg -ss <start> -i <raw>.webm -an -c:v libx264 -preset slow -crf 26 \
  -pix_fmt yuv420p -movflags +faststart -r 25 history-light.mp4
```

Both takes should come out the same length (37.92 s last time). The poster is
the frame at video 10.56 s, once 1 of 9 has settled and the cursor has left
the fold bar, saved with `cwebp -q 82`.

## The JSON comparison screenshot

`static/img/history-json-{light,dark}.webp` comes from a throwaway Playwright
spec in uberblick-2's `packages/web/e2e` harness (`setupHarness` with an
admin role). It created a page "Agent loop settings" holding a paragraph, a
JSON tree and a closing paragraph; the earlier revision had roles implementer
and reviewer, the later one adds preparer, raises the reviewer's
`lease_minutes` from 30 to 45 and adds "browser e2e" to the required checks.
It mocked `**/api/revisions?**` with two revisions (hex ids, so the header
shows a real-looking rev), opened history and took a 1440×900 page screenshot
per theme, converted to WebP at quality 82.
