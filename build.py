#!/usr/bin/env python3
"""Grims Studio static site builder.

Reads content/profile.md and content/projects.md at build time
and emits docs/index.html, docs/applications.html, docs/about.html,
docs/404.html + assets. No database, no API, no runtime fetch.
Suitable for GitHub Pages (branch source: main + /docs).

Usage:
    python3 build.py [--out docs]
"""
import argparse
import html
import re
import shutil
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"

STATUS_ICONS = {
    "running": "●",
    "live": "●",
    "active": "●",
    "in development": "◐",
    "in-development": "◐",
    "planned": "○",
    "concept": "◌",
    "completed": "✓",
    "archived": "■",
}

# Statuses confirmed by repository content. Anything else is not rendered
# as a verified status.
KNOWN_STATUSES = {"active", "in development", "planned", "concept", "completed"}

# Sort verified shipped work first. Stable: original file order kept
# within each group. Statuses are never changed by sorting.
STATUS_RANK = {"active": 0, "completed": 0}

PLACEHOLDER_RE = re.compile(r"YOUR |EXAMPLE|your-account|example\.com", re.I)


def is_real(value: str | None) -> bool:
    if not value:
        return False
    v = str(value).strip()
    if not v:
        return False
    if PLACEHOLDER_RE.search(v):
        return False
    return True


def read_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return meta, body
    return {}, text


def parse_projects(path: Path):
    """Parse ## Title + '- key: value' entries. Returns list of dicts.

    Supported keys: status, description, technologies (comma-separated),
    category, featured (true/false), features (semicolon-separated),
    url / demo (live demo), repository / github (source), download, image.
    Optional keys may be omitted.
    """
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    projects = []
    current = None
    for line in lines:
        h = re.match(r"^##\s+(.+)\s*$", line)
        if h:
            title = h.group(1).strip()
            if title.lower() == "applications":
                current = None
                continue
            current = {"name": title}
            projects.append(current)
            continue
        if current is None:
            continue
        m = re.match(r"^\s*-\s*([A-Za-z_]+)\s*:\s*(.+)\s*$", line)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            if key in ("technologies",):
                current[key] = [t.strip() for t in re.split(r",", val) if t.strip()]
            elif key in ("features",):
                current[key] = [f.strip() for f in re.split(r";", val) if f.strip()]
            elif key in ("featured",):
                current[key] = val.lower() in ("true", "yes", "1")
            else:
                current[key] = val
    # drop entries with placeholder names
    return [p for p in projects if is_real(p.get("name"))]


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "app"


def monogram(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "GS"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def status_icon(status: str) -> str:
    return STATUS_ICONS.get((status or "").strip().lower(), "•")


def split_profile_sections(body_md: str):
    """Split body into intro (# About) + ## sections."""
    sections = {}
    current_key = "about"
    buf = []
    for line in body_md.splitlines():
        h2 = re.match(r"^##\s+(.+)\s*$", line)
        h1 = re.match(r"^#\s+(.+)\s*$", line)
        if h2:
            sections[current_key] = "\n".join(buf).strip()
            current_key = h2.group(1).strip().lower()
            buf = []
        elif h1:
            # skip the top-level title, keep content under current
            continue
        else:
            buf.append(line)
    sections[current_key] = "\n".join(buf).strip()
    return sections


def md_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["extra"])


# --------------------------------------------------------------------------
# Shared partials (single source: no duplicated header/footer markup)
# --------------------------------------------------------------------------

NAV_ITEMS = [
    ("index.html", "Home"),
    ("applications.html", "Applications"),
    ("about.html", "About"),
]


def site_header(company: str, tagline: str, email: str, active: str) -> str:
    links = []
    for href, label in NAV_ITEMS:
        is_active = href == active
        attr = ' class="active" aria-current="page"' if is_active else ""
        links.append(f'<a href="./{href}"{attr}>{label}</a>')
    contact_active = ' class="nav-cta active" aria-current="page"' if active == "contact" else ' class="nav-cta"'
    links.append(f'<a href="./about.html#contact"{contact_active}>Contact</a>')
    return f"""<header class="site-header">
    <div class="header-inner">
      <a class="wordmark" href="./index.html" aria-label="{html.escape(company)} home">
        <img class="wordmark-logo" src="./grims-mark.svg" alt="" width="34" height="34" />
        <span>{html.escape(company)}<small>{html.escape(tagline) if tagline else "Portfolio"}</small></span>
      </a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="primary-nav" aria-label="Menu">
        <span aria-hidden="true">☰</span>
      </button>
      <nav class="site-nav" id="primary-nav" aria-label="Primary">
        {''.join(links)}
      </nav>
    </div>
  </header>"""


def site_footer(company: str, email: str, socials: dict) -> str:
    footer_links = []
    if email:
        footer_links.append(f'<a href="mailto:{html.escape(email)}">Email</a>')
    if socials.get("linkedin"):
        footer_links.append(
            f'<a href="{html.escape(socials["linkedin"])}" target="_blank" rel="noopener noreferrer">LinkedIn</a>'
        )
    return f"""<footer class="footer">
    <div class="wrap footer-inner">
      <img class="footer-logo" src="./grims-logo-horizontal.svg" alt="{html.escape(company)}" height="30" />
      <nav aria-label="Footer">
        <a href="./index.html">Home</a>
        <a href="./applications.html">Applications</a>
        <a href="./about.html">About</a>
        {''.join(footer_links)}
      </nav>
      <span class="quiet" style="margin-left:auto">© 2026 {html.escape(company)} · Static site</span>
    </div>
  </footer>"""


def base_page(*, title: str, description: str, company: str, tagline: str,
              email: str, socials: dict, active: str, body: str,
              scripts: bool = True) -> str:
    scripts_html = '  <script src="./app.js" defer></script>' if scripts else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}" />
  <meta property="og:title" content="{html.escape(title)}" />
  <meta property="og:description" content="{html.escape(description)}" />
  <meta property="og:type" content="website" />
  <!-- TODO: supply an Open Graph preview image as docs/og-preview.png and replace the content below -->
  <meta property="og:image" content="./og-preview.png" />
  <link rel="stylesheet" href="./style.css" />
  <link rel="icon" href="./grims-mark.svg" type="image/svg+xml" />
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
{site_header(company, tagline, email, active)}
  <main id="main">
{body}
  </main>
{site_footer(company, email, socials)}
{scripts_html}
</body>
</html>"""


# --------------------------------------------------------------------------
# App cards (shared by home featured section + applications page)
# --------------------------------------------------------------------------

def status_badge(status: str) -> str:
    if status and status.strip().lower() in KNOWN_STATUSES:
        return (
            f'<span class="badge status"><span aria-hidden="true">'
            f"{status_icon(status)}</span> {html.escape(status.strip())}</span>"
        )
    return '<span class="badge status"><span aria-hidden="true">?</span> TODO: Confirm status</span>'


def app_links(p: dict) -> str:
    """Render GitHub / Live demo / Download buttons only for real URLs."""
    buttons = []
    repo = p.get("repository", p.get("github", ""))
    demo = p.get("url", p.get("demo", ""))
    download = p.get("download", "")
    if is_real(repo) and repo.startswith("http"):
        buttons.append(
            f'<a class="action-src" href="{html.escape(repo)}" target="_blank" rel="noopener noreferrer">GitHub</a>'
        )
    if is_real(demo) and demo.startswith("http"):
        buttons.append(
            f'<a class="action-open" href="{html.escape(demo)}" target="_blank" rel="noopener noreferrer">Live demo ↗</a>'
        )
    if is_real(download) and download.startswith("http"):
        buttons.append(
            f'<a class="action-src" href="{html.escape(download)}" target="_blank" rel="noopener noreferrer">Download</a>'
        )
    return f'<div class="card-actions">{"".join(buttons)}</div>' if buttons else ""


def app_card(p: dict, *, detailed: bool = False) -> str:
    pname = p.get("name", "Untitled")
    slug = slugify(pname)
    status = p.get("status", "").strip() if is_real(p.get("status")) else ""
    desc = p.get("description", "") if is_real(p.get("description")) else ""
    cat = p.get("category", "").strip() if is_real(p.get("category")) else ""
    techs = p.get("technologies", []) if isinstance(p.get("technologies"), list) else []
    feats = p.get("features", []) if isinstance(p.get("features"), list) else []
    featured = bool(p.get("featured"))
    image = p.get("image", "") if is_real(p.get("image")) else ""
    search_blob = " ".join([pname, desc, cat, " ".join(techs), " ".join(feats), status])

    if image:
        shot_html = f'<img src="{html.escape(image)}" alt="{html.escape(pname)} screenshot" loading="lazy" />'
    else:
        shot_html = (
            f'<div class="shot-placeholder" role="img" '
            f'aria-label="Screenshot placeholder for {html.escape(pname)}">'
            f"TODO: Add screenshot/mockup for {html.escape(pname)}</div>"
        )

    badges = status_badge(status)
    if cat:
        badges += f'<span class="badge cat">{html.escape(cat)}</span>'

    tags_html = ""
    if techs:
        tags_html = '<div class="tags">' + "".join(f"<span>{html.escape(t)}</span>" for t in techs) + "</div>"

    if detailed:
        if feats:
            feats_html = "<ul>" + "".join(f"<li>{html.escape(f)}</li>" for f in feats) + "</ul>"
        else:
            feats_html = f"<ul><li class=\"todo\">TODO: Add key features for {html.escape(pname)}</li></ul>"
        extra = f"""<h4>Key features</h4>
          {feats_html}"""
    else:
        extra = f'<p><a href="./applications.html#{slug}">View on Applications page →</a></p>'

    return f"""
        <article class="card project-card{' featured' if featured else ''}" id="{slug}" data-category="{html.escape(cat)}" data-search="{html.escape(search_blob)}">
          <div class="card-top">
            <div class="monogram" aria-hidden="true">{html.escape(monogram(pname))}</div>
            <h3>{html.escape(pname)}</h3>
          </div>
          {shot_html}
          <div class="card-badges">{badges}</div>
          <p class="desc">{html.escape(desc) if desc else f'<span class="todo">TODO: Add description for {html.escape(pname)}</span>'}</p>
          {tags_html}
          {extra}
          {app_links(p)}
        </article>"""


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def home_page(ctx: dict) -> str:
    featured = [p for p in ctx["projects"] if p.get("featured")]
    cards = "\n".join(app_card(p) for p in featured)
    contact = ctx["contact_links"]
    return f"""<section class="hero" aria-label="Welcome">
      <div class="wrap hero-grid">
        <div>
          <span class="eyebrow"><i aria-hidden="true"></i> Welcome to {html.escape(ctx['company'])}</span>
          <h1>{html.escape(ctx['company'])}</h1>
          <p class="tagline">“{html.escape(ctx['tagline'])}”</p>
          <p class="lede">Hello — I'm {html.escape(ctx['name'])}, a biomedical sciences researcher and lead developer. {html.escape(ctx['company'])} builds offline-first, privacy-conscious apps with scientific precision: diagnosing real-world friction and engineering targeted, durable cures.</p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="./applications.html">View Applications</a>
            <a class="btn btn-ghost" href="./about.html">About Me</a>
          </div>
        </div>
        <aside class="hero-card" aria-label="Why trust this work">
          <h2>Field notes</h2>
          <dl class="specimen">
            <div><dt>Research-backed</dt><dd>UCC Biomedical Science</dd></div>
            <div><dt>Offline-first</dt><dd>Local-first apps</dd></div>
            <div><dt>Clean design</dt><dd>Privacy-conscious UX</dd></div>
          </dl>
        </aside>
      </div>
    </section>

    <section class="block" aria-label="Featured applications">
      <div class="wrap">
        <div class="section-head"><h2>Featured Apps</h2><p>Start here.</p></div>
        <div class="grid">
          {cards}
        </div>
      </div>
    </section>

    <section class="block" aria-label="Contact">
      <div class="wrap">
        <div class="section-head"><h2>Say hello</h2><p>Direct line, no forms.</p></div>
        <div class="prose contact-box">
          {''.join(contact) if contact else "<p>No public contact listed yet.</p>"}
        </div>
      </div>
    </section>"""


def applications_page(ctx: dict) -> str:
    # Verified shipped work first; original order otherwise. Statuses unchanged.
    ordered = sorted(ctx["projects"], key=lambda p: STATUS_RANK.get((p.get("status") or "").strip().lower(), 1))
    cards = "\n".join(app_card(p, detailed=True) for p in ordered)
    categories = sorted({p.get("category", "").strip() for p in ordered if is_real(p.get("category"))})
    filters = ['<button class="filter-btn" data-filter="all" aria-pressed="true">All</button>']
    for c in categories:
        filters.append(
            f'<button class="filter-btn" data-filter="{html.escape(c)}" aria-pressed="false">{html.escape(c)}</button>'
        )
    grid = cards if cards else "<div class=\"prose\"><p>No applications listed yet.</p></div>"
    return f"""<section class="block" aria-label="Applications">
      <div class="wrap">
        <div class="section-head">
          <h2>Applications</h2>
          <p>Every app, honestly labeled.</p>
          <span class="count-pill" id="result-count" aria-live="polite"></span>
        </div>
        <div class="controls" role="search">
          <div class="search-wrap">
            <label for="app-search">Search apps</label>
            <input type="search" id="app-search" placeholder="Search apps, categories, tech…" autocomplete="off" />
          </div>
          <div class="filter-row" role="group" aria-label="Filter by category">
            {''.join(filters)}
          </div>
          <button class="clear-btn" id="clear-filters" type="button">Clear filters</button>
        </div>
        <div class="grid" id="app-grid">
          {grid}
        </div>
        <div class="no-results" id="no-results">
          <p><strong>No apps match your search or filters.</strong></p>
          <p class="quiet">Try a different search term or choose “All”.</p>
        </div>
      </div>
    </section>"""


def about_page(ctx: dict) -> str:
    s = ctx["sections"]
    story = md_to_html(s.get("about", ""))
    research = md_to_html(s.get("research", ""))
    leadership = md_to_html(s.get("leadership", ""))
    skills = md_to_html(s.get("skills", ""))
    design = md_to_html(s.get("design work", s.get("design", "")))
    contact = ctx["contact_links"]
    return f"""<section class="block" aria-label="About">
      <div class="wrap">
        <div class="section-head"><h2>About Me</h2><p>{html.escape(ctx['role'])}</p></div>
        <div class="prose">
          <h3>{html.escape(ctx['name'])}</h3>
          <p class="quiet">{html.escape(ctx['location'])}</p>
        </div>
      </div>
    </section>

    <section class="block" aria-label="Story">
      <div class="wrap">
        <div class="section-head"><h2>Story</h2><p>Clear Diagnosis, Clean Cure.</p></div>
        <div class="prose">{story}</div>
      </div>
    </section>

    <section class="block" aria-label="Research">
      <div class="wrap">
        <div class="section-head"><h2>Research</h2><p>BSc Biomedical Science, 2026, UCC.</p></div>
        <div class="two-col">
          <div class="mini"><h3>Research</h3>{research if research else '<p class="todo">TODO: Add research details.</p>'}</div>
          <div class="mini"><h3>Leadership</h3>{leadership if leadership else '<p class="todo">TODO: Add leadership details.</p>'}</div>
        </div>
      </div>
    </section>

    <section class="block" aria-label="Skills and design work">
      <div class="wrap">
        <div class="section-head"><h2>Skills &amp; Design</h2><p>Tools of the trade.</p></div>
        <div class="two-col">
          <div class="mini"><h3>Skills</h3>{skills if skills else '<p class="todo">TODO: Add skills.</p>'}</div>
          <div class="mini"><h3>Design work</h3>{design if design else '<p class="todo">TODO: Add design examples.</p>'}</div>
        </div>
      </div>
    </section>

    <section class="block" id="contact" aria-label="Contact">
      <div class="wrap">
        <div class="section-head"><h2>Contact</h2><p>Direct line, no forms.</p></div>
        <div class="prose contact-box">
          {''.join(contact) if contact else "<p class=\"todo\">TODO: Add email and LinkedIn links.</p>"}
        </div>
      </div>
    </section>"""


def not_found_page(ctx: dict) -> str:
    return """<section class="block" aria-label="Page not found">
      <div class="wrap">
        <div class="section-head"><h2>Not found</h2><p>Diagnosis: missing page.</p></div>
        <div class="prose">
          <p>Sorry — there's nothing at this address. It may have moved.</p>
          <p><a class="btn btn-primary" href="./index.html">Back to Home</a></p>
        </div>
      </div>
    </section>"""


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def build(out_dir: Path):
    profile_path = CONTENT / "profile.md"
    projects_path = CONTENT / "projects.md"
    if not profile_path.exists():
        raise SystemExit("content/profile.md missing")
    meta, body_md = read_frontmatter(profile_path)
    projects = parse_projects(projects_path)

    name = meta.get("name", "") if is_real(meta.get("name")) else ""
    company = meta.get("company_name", "Grims Studio") if is_real(meta.get("company_name")) else "Grims Studio"
    role = meta.get("role", "") if is_real(meta.get("role")) else ""
    tagline = meta.get("tagline", "") if is_real(meta.get("tagline")) else ""
    location = meta.get("location", "") if is_real(meta.get("location")) else ""
    email = meta.get("email", "") if is_real(meta.get("email")) else ""
    socials = meta.get("socials", {}) or {}
    socials = {k: v for k, v in socials.items() if is_real(v)}
    sections = split_profile_sections(body_md)

    contact_links = []
    if email:
        contact_links.append(f'<a class="btn btn-ghost" href="mailto:{html.escape(email)}">Email</a>')
    if socials.get("linkedin"):
        contact_links.append(
            f'<a class="btn btn-ghost" href="{html.escape(socials["linkedin"])}" target="_blank" rel="noopener noreferrer">LinkedIn</a>'
        )
    if socials.get("github"):
        contact_links.append(
            f'<a class="btn btn-ghost" href="{html.escape(socials["github"])}" target="_blank" rel="noopener noreferrer">GitHub</a>'
        )

    ctx = {
        "name": name, "company": company, "role": role, "tagline": tagline,
        "location": location, "email": email, "socials": socials,
        "sections": sections, "projects": projects, "contact_links": contact_links,
    }

    pages = [
        ("index.html", "Home", f"{company} — {tagline} {name}",
         f"{company}: {tagline} Offline-first, privacy-conscious apps by {name}, {role}.",
         "index.html", home_page(ctx), True),
        ("applications.html", "Applications", f"Applications — {company}",
         f"Browse all {company} applications: offline-first apps, games, and design work by {name}.",
         "applications.html", applications_page(ctx), True),
        ("about.html", "About", f"About {name} — {company}",
         f"About {name}, {role} based in {location}: biomedical research, leadership, skills, and contact.",
         "about.html", about_page(ctx), True),
        ("404.html", "Not found", f"Page not found — {company}",
         f"The requested {company} page could not be found.",
         "", not_found_page(ctx), False),
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, _label, title, desc, active, body, scripts in pages:
        page = base_page(title=title, description=desc, company=company,
                         tagline=tagline, email=email, socials=socials,
                         active=active, body=body, scripts=scripts)
        (out_dir / filename).write_text(page, encoding="utf-8")
    for asset in ("style.css", "app.js", "grims-mark.svg", "grims-logo-horizontal.svg",
                  "googlee8fcbc5f56b1ecd1.html"):
        src = ROOT / "assets" / asset
        if src.exists():
            shutil.copy(src, out_dir / asset)
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {len(pages)} pages with {len(projects)} projects into {out_dir}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs")
    args = ap.parse_args()
    build(ROOT / args.out)


if __name__ == "__main__":
    main()
