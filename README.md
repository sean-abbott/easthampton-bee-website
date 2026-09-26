Easthampton BEES Committee site, migrated from WordPress. Edited with
[beedance-ssg-editor](../beedance-ssg-editor) — point it here with
`just set-site /path/to/easthamptonbees-ssg` from that repo.

Dual-licensed: code (templates, scripts, config) under MIT (`LICENSE-CODE`),
written content under `content/` under CC BY 4.0 (`LICENSE-CONTENT`).

No theme is vendored yet — `templates/*.html` are hand-written (a real green/
nature color palette and layout, verified WCAG-AAA contrast, but not a
`just add-theme` theme). Nothing stops adding a real theme later; these
templates would just move to `themes/<name>/templates/` and get a
`theme = "<name>"` line in `config.toml`.

# Deployment

Deployed to Cloudflare (Workers static-assets flow — `wrangler.toml` in this
repo declares the static output, no Worker script). Staging URL is not the
real `easthamptonbees.org` domain yet — that stays on the existing
WordPress site until there's a real cutover decision.

# Structure

- `content/` — pages (`about/`, `biodiversity/` with 4 child pages, `news/`,
  `plant-safari/`, `privacy-policy/` (draft)) and `content/blog/` (posts).
- `content/events/` — not hand-maintained. `_index.md` (list) and
  `calendar.md` (month-grouped view) both pull every post tagged `event` via
  Zola's taxonomy system (`get_taxonomy_term(kind="tags", term="event")`).
  To make a post show up as an event: add `event` to its `[taxonomies]
  tags = [...]` list, and set `extra.event_date` (the actual event date -
  may differ from the post's publish `date`, e.g. a rain-date change). Add
  `extra.event_cancelled = true` if it was cancelled.
- `static/plant-safari/` — synced from the `iNat-place-safari` project via
  `just sync-plant-safari`, not hand-edited here.
- `scripts/migrate-from-wordpress.py` — the one-time WXR-export-to-markdown
  converter used to bootstrap `content/`. Conservative: paragraphs/headings/
  lists become real markdown, everything else (images, tables, nested
  layout/column blocks) is left as raw HTML. Kept around in case content
  needs re-extracting from a fresher export, not meant to be perfect or
  re-run routinely.

# Known rough-pass gaps

- Images still point at the original `easthamptonbees.org` / WordPress-CDN
  URLs rather than local `static/` files - fine while the WordPress site
  stays up, needs a real download-and-relink pass before that site goes away.
  A few (in `content/blog/september-coffee-and-invasive-removal.md`) point at
  a `wzn.bla.mybluehost.me` *staging* domain specifically - those may not
  stay reachable at all.
- The WordPress export's Resources, Events, and Contact pages were dropped
  entirely - they were unedited WordPress/theme starter placeholder content
  (fake address, `hi@example.com`, stock photos, `href="#"` buttons), not
  real material. Contact info and a real Resources page still need writing.
  About and Home also had similar generic filler stripped out (a boilerplate
  "Ways to Get Involved"/"Key Initiatives" block, a stock-photo gallery) -
  only the real, specific text was kept.
- Events calendar is a grouped-by-month list, not an actual calendar grid -
  a deliberate first-pass simplification.
