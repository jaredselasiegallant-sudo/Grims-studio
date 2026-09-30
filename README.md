# Grims Studio — Portfolio Site

Three-page static portfolio for **Jared Selasie Gallant / Grims Studio** — *Clear Diagnosis, Clean Cure.*

Built with a tiny Python static generator (no database, no API, no runtime fetch). Content lives in Markdown, output in `docs/` is ready for GitHub Pages (branch source: `main` + `/docs`).

Pages: `index.html` (Home) · `applications.html` (all 7 apps + search/filter) · `about.html` (biography + contact) · `404.html`.

## Quick start

```bash
python3 build.py
python3 -m http.server 8000 --directory docs
# open http://localhost:8000
```

Requirements: Python 3 + `markdown` + `yaml` (if missing: `pip install markdown pyyaml`).

## Edit content

### `content/profile.md` — name, company, bio (About page)

Frontmatter (titles, header, footer, hero, contact):

```yaml
name: "Jared Selasie Gallant"
company_name: "Grims Studio"
role: "Biomedical Sciences Researcher & Lead Developer"
tagline: "Clear Diagnosis, Clean Cure."
location: "Cape Coast, Ghana"
email: "jaredselasiegallant@gmail.com"
socials:
  linkedin: "https://linkedin.com/in/jared-gallant"
```

Leave unknown fields empty — they are hidden automatically. Body sections (`# About`, `## Research`, `## Leadership`, `## Skills`, `## Design Work`) render on the About page. Edit freely, then rebuild.

### `content/projects.md` — apps (Applications page + Home featured)

One `## App Name` section per app. To add an app, copy a section; to remove one, delete its section. No page markup needs editing — cards, filters, and featured links generate from this file.

```markdown
## PocketLedger

- status: Active
- description: Offline-first personal finance platform…
- technologies: Flutter, Dart, SQLite
- category: Productivity
- featured: true
# optional — omit if unknown, never invent:
# - features: offline ledger; monthly budgets
# - repository: https://github.com/… (GitHub button)
# - url: https://… (Live demo button)
# - download: https://… (Download button)
# - image: ./screenshots/pocket-ledger.webp
```

Rules:

- `status` must be one of `Active`, `In development`, `Planned`, `Concept`, `Completed` (per repo). Anything else renders as `TODO: Confirm status`.
- Omit `repository` / `url` / `download` when unknown. Buttons render only for real `https://` URLs — no dead links.
- `featured: true` puts the app on the Home page (currently PocketLedger, Project Nexus, Grimoire).
- `category` drives the filter buttons (plus an `All` option). Search matches name + description + category + tech + features + status.
- Missing screenshots/features render as labeled TODO placeholders in the UI.

## Build / deploy

- Build: `python3 build.py` → `docs/index.html`, `docs/applications.html`, `docs/about.html`, `docs/404.html`, `docs/style.css`, `docs/app.js`, `docs/.nojekyll`
- Local preview: any static server over `docs/`
- GitHub Pages: Settings → Pages → Deploy from branch → `main` + `/docs`. All internal links/assets are relative, verified under the `/Grims-studio/` subpath.

## What was built

- `build.py` — shared `site_header()` / `site_footer()` partials (active page via `aria-current`), per-page titles/descriptions/OG tags, fragment-anchored app cards (`applications.html#project-nexus`), Active/Completed-first stable sort
- `assets/style.css` — unchanged Clinical Lab theme + mobile nav menu, screenshot placeholders, `:target` highlight, `prefers-reduced-motion` respected
- `assets/app.js` — unchanged search/filter + keyboard-accessible mobile nav toggle (Esc closes); all content present with JS disabled
- Accessibility: skip link, landmarks, labeled controls, `aria-pressed` filters, `aria-live` result count, icon+text status badges, visible focus

## Still needed from you (TODO checklist)

- [ ] Screenshots/mockups for all 7 apps (or confirm placeholders stay)
- [ ] Key `features:` per app in `content/projects.md` (currently TODO in UI)
- [ ] Verified GitHub / Live demo / Download URLs per app (currently no buttons — correct)
- [ ] Open Graph preview image → save as `docs/og-preview.png` (meta tag already points there relatively)
- [ ] Confirm email + LinkedIn are the public contact points (from repo frontmatter)
