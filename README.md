# Grims Studio — Portfolio Site

Static portfolio for **Jared Selasie Gallant / Grims Studio** — *Clear Diagnosis, Clean Cure.*

Built with a tiny Python static generator (no database, no API, no runtime fetch). Content lives in Markdown, output in `docs/` is ready for GitHub Pages.

## Quick start

```bash
python3 build.py
python3 -m http.server 8000 --directory docs
# open http://localhost:8000
```

Requirements: Python 3 + `markdown` + `yaml` (both already available on Fedora 44; if missing: `pip install markdown pyyaml`).

## Edit content

### `content/profile.md` — name, company, bio

Frontmatter (site title, header, footer, hero, contact):

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

Leave unknown fields empty — they are hidden automatically. Never put `YOUR NAME`-style placeholders; they are treated as missing.

Body is Markdown (`# About`, `## Research`, `## Leadership`, `## Skills`, `## Design Work`). Edit freely, then rebuild.

### `content/projects.md` — apps

One `## App Name` section per app:

```markdown
## PocketLedger

- status: Active
- description: Offline-first personal finance platform…
- technologies: Flutter, Dart, SQLite
- category: Productivity
- featured: true
# optional — omit if unknown:
# - url: https://… (live app — shows “Open app”)
# - repository: https://github.com/… (shows “View source”)
# - image: /images/pocket-ledger.webp
```

Rules (per spec):

- `status` is truthful — never `Running` unless the app is actually live. Current values: `Active`, `In development`, `Planned`, `Concept`, `Completed`.
- Omit `url` / `repository` when unknown. Buttons are only rendered when a real `https://` URL exists — no dead buttons.
- `featured: true` gives visual priority (PocketLedger, Project Nexus, Grimoire).
- `category` drives the filter buttons. Search matches name + description + category + tech + status.
- To remove an app, delete its `## …` section. To add, copy a section.

## Build / deploy

- Build: `python3 build.py` → `docs/index.html`, `docs/style.css`, `docs/app.js`, `docs/.nojekyll`
- Local preview: any static server over `docs/`
- GitHub Pages:
  1. Push this folder to a repo
  2. Settings → Pages → Deploy from branch → `main` + `/docs`
  3. No base-path config needed — all asset links are relative (`./style.css`)

No GitHub API calls at runtime. The app list is only what you maintain in Markdown.

## What was built

- `build.py` — reads Markdown at build time, renders semantic HTML
- `assets/style.css` — Clinical Lab theme: dark ink `#121417`, warm paper `#FAF7F2`, lab-teal `#0E7C6B`, system fonts, CSS grid motif, responsive, `prefers-reduced-motion` respected
- `assets/app.js` — search + category filters, no-results state, clear button, `aria-live` count; content works with JS disabled
- Sections: Header → Hero (View Apps / Research & Leadership) → Applications grid → About → Research & Leadership → Contact → Footer
- Cards show monogram (no fake screenshots), status badge with icon + text (not color alone), category, tech tags; featured cards highlighted

## Still needed from you

- [ ] Live URLs + GitHub repo URLs for each app (add `url:` / `repository:` in `content/projects.md` to enable Open app / View source)
- [ ] Project images (optional — drop in `docs/images/` and set `image:`)
- [ ] `[Grims Studio logo]` / `[app store link]` placeholders if you want branding
- [ ] No metrics, awards, or users invented — add only real ones
