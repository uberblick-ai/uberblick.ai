# Writing for uberblick.ai

This repository is the product site. [README.md](README.md) covers the build,
the layout and deploying. This file covers the words: who we write for, what
each kind of page is for, and when to stop and ask.

## Before you write

Ask the maintainer you work for about a page's structure whenever you are
unsure: which sections it has, what it leaves out, where it sits in the
sidebar. Ask before drafting, not after. A page in the wrong shape costs more
to fix than the question.

## Who we write for

Small teams, open-source minded and hands-on, from a hacking culture. They
read the site to decide whether Uberblick fits how they work, and they notice
pitch language at once. Uberblick is a knowledge base for humans and agents
alike. It does not track tasks or delivery; that lives on GitHub.

## Voice

- Plain and human. Write as "we", the people who build Uberblick and use it
  every day. Say why we built something, not how great it is.
- Concrete over abstract: a real situation, a real page, a real number.
- Never describe the obvious. If a button needs explaining, the UI is wrong.
  File an issue on uberblick-2 instead of documenting around it.
- When a maintainer gives you text, keep its intent and its points. Use the
  words nearly verbatim only when asked to; otherwise find your own.
- Spell it "Uberblick", never "Überblick". Avoid "LLM wiki", "second brain"
  and "use cases" (the site has guides).
- A workspace without a hub is a "local-only workspace". Don't say it
  "stays on your laptop": a hub workspace lives there too.

## What each kind of page is for

| Pages | What they hold | What they leave out |
| --- | --- | --- |
| Home (`/`) | What Uberblick is and why it exists, in a few short sections. | Sidebars, feature lists, setup steps. |
| Docs, Core concepts (`/docs/documents`, `/docs/history`, …) | The intent, the motivation and the benefit of a feature: the problem it solves and what you gain. A video or a screenshot shows the UI. | UI walkthroughs, button names, step lists, tool and API names, timing constants and other technical details. |
| Docs, Get started | What you need and the shortest path to a working setup. | Background a guide already tells. |
| Docs, reference (CLI, Custom Markdown) | Exact usage: syntax, flags, one example per command or block. This is where technical detail belongs. | Motivation beyond a sentence. |
| Guides (`/guides/…`) | One job walked through from start to finish, with the steps a person takes. | Reference tables. Link to them instead. |
| Blog | One story or lesson from building Uberblick, told by us. | Release notes. The changelog holds those. |
| FAQ, Compare | Short, direct answers to the questions people actually ask. | Claims about other products we cannot back. |

One page owns each fact. Link to the owner instead of repeating it.

## Ahead of the product

The site reflects what the product does today. It may run ahead of it on
purpose, to describe where the product is going. When a page says something
the product doesn't do yet, file issues on uberblick-2 to close the gap, and
agree on them with the maintainer you work for first: what the page promises,
how it should behave, and which milestone it lands in. Never leave a promise
on the site without an issue behind it.

## Images and video

Screenshots are WebP in a light and dark pair (`.shot` with `img.l` and
`img.d`), carry width, height and real alt text, and load lazily below the
fold. Videos come as a light and dark MP4 pair on one `<video data-light
data-dark>`, played by `static/js/video.js`. Show the real product on a real
page, never a mock-up passed off as one.

Keep what a re-cut needs next to the site, unpublished: the recording
script, the storyline, the setup and the encode settings go in
`videos/<name>/`.
