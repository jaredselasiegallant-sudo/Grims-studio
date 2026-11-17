#!/usr/bin/env python3
"""Grims Studio static site builder.

Reads content/profile.md and content/projects.md at build time
and emits docs/index.html, docs/applications.html, docs/about.html,
docs/app-<slug>.html (one per app), docs/404.html + assets. No database, no API, no runtime fetch.
Suitable for GitHub Pages (branch source: main + /docs).

Usage:
    python3 build.py [--out docs]
"""
import argparse
import html
import re
import shutil
from datetime import date
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"

SITE_URL = "https://jaredselasiegallant-sudo.github.io/Grims-studio"

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
    platforms (comma-separated), url / demo (live demo),
    repository / github / repository2 (source), download, release_notes,
    version, release_date, file_size, checksum, requirements, image.
    Optional keys may be omitted; unknown download details stay hidden.
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
        m = re.match(r"^\s*-\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+)\s*$", line)
        if m:
            key = m.group(1).strip().lower()
            val = m.group(2).strip()
            if key in ("technologies", "platforms"):
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


def app_route(p: dict) -> str:
    """Stable flat route for an app detail page (same dir => ./ links work)."""
    return f"app-{slugify(p.get('name', 'app'))}.html"


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

def fox_svg(variant: str = "corner") -> str:
    """Kit the fox mascot. Inline SVG rig (.fx-* groups) animated by fox.js.

    Without JS it renders as a complete static illustration.
    variant 'dig' adds the 404 dirt mound in front of the paws.
    """
    dirt = ""
    if variant == "dig":
        dirt = """<g class="fx-dirt">
          <ellipse cx="160" cy="316" rx="78" ry="11" fill="#C89B6A"/>
          <ellipse cx="118" cy="309" rx="15" ry="6" fill="#9A6E42"/>
          <ellipse cx="205" cy="306" rx="11" ry="5" fill="#9A6E42"/>
        </g>"""
    return f"""<svg class="fox fox-{variant}" viewBox="0 0 320 320" role="img" aria-hidden="true" focusable="false">
      <title>Kit, the Grims Studio fox</title>
      <g class="fx-tail">
        <path d="M218 280 C 272 284 296 238 284 184" fill="none" stroke="#EF7A2C" stroke-width="30" stroke-linecap="round"/>
        <circle cx="284" cy="184" r="16" fill="#FFE9D2"/>
      </g>
      <g class="fx-body">
        <path d="M160 166 C 114 166 86 208 86 252 C 86 290 118 308 160 308 C 202 308 234 290 234 252 C 234 208 206 166 160 166 Z" fill="#FF8A3D"/>
        <ellipse cx="160" cy="264" rx="50" ry="40" fill="#FFE9D2"/>
      </g>
      <g class="fx-paws">
        <rect x="122" y="284" width="32" height="26" rx="13" fill="#FFD9B5" stroke="#EF7A2C" stroke-width="1.5"/>
        <rect x="166" y="284" width="32" height="26" rx="13" fill="#FFD9B5" stroke="#EF7A2C" stroke-width="1.5"/>
      </g>
      {dirt}
      <g class="fx-neck">
        <g class="fx-head">
          <g class="fx-ear fx-ear-l">
            <path d="M120 64 L110 18 L156 46 Z" fill="#FF8A3D" stroke="#FF8A3D" stroke-width="6" stroke-linejoin="round"/>
            <path d="M124 54 L116 30 L148 46 Z" fill="#FFCFA8"/>
          </g>
          <g class="fx-ear fx-ear-r">
            <path d="M200 64 L210 18 L164 46 Z" fill="#FF8A3D" stroke="#FF8A3D" stroke-width="6" stroke-linejoin="round"/>
            <path d="M196 54 L204 30 L172 46 Z" fill="#FFCFA8"/>
          </g>
          <path d="M160 52 C 116 52 94 82 94 114 C 94 150 124 170 160 170 C 196 170 226 150 226 114 C 226 82 204 52 160 52 Z" fill="#FF8A3D"/>
          <path d="M160 104 C 134 104 118 120 118 138 C 118 158 138 170 160 170 C 182 170 202 158 202 138 C 202 120 186 104 160 104 Z" fill="#FFE9D2"/>
          <g class="fx-eyes">
            <g class="fx-eye fx-eye-l">
              <ellipse cx="134" cy="100" rx="12" ry="13" fill="#FFFDF8"/>
              <circle class="fx-pupil" cx="134" cy="103" r="5.5" fill="#3A2A21"/>
              <circle cx="137" cy="96" r="2.2" fill="#FFFFFF"/>
            </g>
            <g class="fx-eye fx-eye-r">
              <ellipse cx="186" cy="100" rx="12" ry="13" fill="#FFFDF8"/>
              <circle class="fx-pupil" cx="186" cy="103" r="5.5" fill="#3A2A21"/>
              <circle cx="189" cy="96" r="2.2" fill="#FFFFFF"/>
            </g>
          </g>
          <g class="fx-squint">
            <path d="M122 100 Q134 90 146 100" fill="none" stroke="#3A2A21" stroke-width="3.5" stroke-linecap="round"/>
            <path d="M174 100 Q186 90 198 100" fill="none" stroke="#3A2A21" stroke-width="3.5" stroke-linecap="round"/>
          </g>
          <ellipse cx="112" cy="124" rx="9" ry="5" fill="#FFB3A7" opacity=".85"/>
          <ellipse cx="208" cy="124" rx="9" ry="5" fill="#FFB3A7" opacity=".85"/>
          <path d="M152 122 Q160 116 168 122 Q164 132 160 133 Q156 132 152 122 Z" fill="#3A2A21"/>
          <path d="M160 133 L160 139 M148 141 Q160 150 172 141" fill="none" stroke="#3A2A21" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
      </g>
    </svg>"""


NAV_ITEMS = [
    ("index.html", "Home"),
    ("applications.html", "Applications"),
    ("studio.html", "Studio"),
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
              canonical: str, scripts: bool = True) -> str:
    # Order matters: anime (lib) -> app.js (nav/search) -> fox.js (mascot rig).
    scripts_html = ""
    if scripts:
        scripts_html = (
            '  <script src="./anime.umd.min.js" defer></script>\n'
            '  <script src="./app.js" defer></script>\n'
            '  <script src="./fox.js" defer></script>'
        )
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
  <link rel="canonical" href="{html.escape(canonical)}" />
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


def shot_html(p: dict, label: str = "screenshot/mockup") -> str:
    pname = p.get("name", "Untitled")
    image = p.get("image", "") if is_real(p.get("image")) else ""
    if image:
        return f'<img src="{html.escape(image)}" alt="{html.escape(pname)} screenshot" loading="lazy" />'
    return (
        f'<div class="shot-placeholder" role="img" aria-label="Screenshot placeholder for {html.escape(pname)}">'
        f'<div class="shot-lett" aria-hidden="true">{html.escape(monogram(pname))}</div>'
        f"<p>No screenshot</p>"
        f'<p class="quiet">Mockup coming soon</p>'
        f"</div>"
    )


def badges_html(p: dict) -> str:
    status = p.get("status", "").strip() if is_real(p.get("status")) else ""
    cat = p.get("category", "").strip() if is_real(p.get("category")) else ""
    badges = status_badge(status)
    if cat:
        badges += f'<span class="badge cat">{html.escape(cat)}</span>'
    return badges


def tags_html(techs: list) -> str:
    if not techs:
        return ""
    return '<div class="tags">' + "".join(f"<span>{html.escape(t)}</span>" for t in techs) + "</div>"


def catalog_card(p: dict) -> str:
    """Slim discovery card: name, badges, short description, detail link."""
    pname = p.get("name", "Untitled")
    slug = slugify(pname)
    desc = p.get("description", "") if is_real(p.get("description")) else ""
    cat = p.get("category", "").strip() if is_real(p.get("category")) else ""
    techs = p.get("technologies", []) if isinstance(p.get("technologies"), list) else []
    feats = p.get("features", []) if isinstance(p.get("features"), list) else []
    featured = bool(p.get("featured"))
    st = p.get("status", "").strip() if is_real(p.get("status")) else ""
    search_blob = " ".join([pname, desc, cat, " ".join(techs), " ".join(feats),
                            st])
    return f"""
        <article class="card project-card{' featured' if featured else ''}" id="{slug}" data-category="{html.escape(cat)}" data-status="{html.escape(st)}" data-search="{html.escape(search_blob)}">
          <div class="card-top">
            <div class="monogram" aria-hidden="true">{html.escape(monogram(pname))}</div>
            <h3>{html.escape(pname)}</h3>
          </div>
          {shot_html(p)}
          <div class="card-badges">{badges_html(p)}</div>
          <p class="desc">{html.escape(desc) if desc else f'<span class="todo">TODO: Add description for {html.escape(pname)}</span>'}</p>
          <p><a class="btn btn-primary" href="./{app_route(p)}">View app details →</a></p>
        </article>"""
def primary_button(p: dict) -> str:
    """Single primary CTA for an app; real URLs only."""
    download = p.get("download", "")
    url = p.get("url", p.get("demo", ""))
    repo = p.get("repository", p.get("github", ""))
    if is_real(download) and str(download).startswith("http"):
        return f'<a class="btn btn-primary" href="{html.escape(download)}" rel="noopener noreferrer">Download →</a>'
    if is_real(url) and str(url).startswith("http"):
        return f'<a class="btn btn-primary" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Open app ↗</a>'
    if is_real(repo) and str(repo).startswith("http"):
        return f'<a class="btn btn-primary" href="{html.escape(repo)}" target="_blank" rel="noopener noreferrer">View source ↗</a>'
    return '<a class="btn btn-primary" href="./applications.html">View applications →</a>'


def platform_cards(p: dict) -> str:
    """Secondary, platform-specific cards (demo / source repo)."""
    rows = []
    url = p.get("url", p.get("demo", ""))
    repo = p.get("repository", p.get("github", ""))
    repo2 = p.get("repository2", "")
    if is_real(url) and str(url).startswith("http"):
        rows.append(
            f'<a class="plat" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">'
            f'<span class="plat-cap">Web</span><span class="plat-desc">Open in browser</span></a>'
        )
    for r in (repo, repo2):
        if is_real(r) and str(r).startswith("http"):
            label = r.rstrip("/").rsplit("/", 1)[-1]
            rows.append(
                f'<a class="plat" href="{html.escape(r)}" target="_blank" rel="noopener noreferrer">'
                f'<span class="plat-cap">GitHub</span><span class="plat-desc">View source · {html.escape(label)}</span></a>'
            )
    if not rows:
        return '<p class="coming-soon">Platform packages coming soon</p>'
    return '<div class="plat-row">' + "".join(rows) + "</div>"


def version_history(p: dict) -> str:
    """Honest, data-driven release list; no invented changelogs."""
    version = p.get("version", "")
    download = p.get("download", "")
    notes = p.get("release_notes", "")
    has = any(is_real(p.get(k)) for k in ("version", "release_notes", "download", "file_size"))
    if not has:
        return '<p class="coming-soon">Release history coming soon</p>'
    rows = []
    if is_real(version) and is_real(download):
        rows.append(
            f"<li><a href='{html.escape(download)}' rel='noopener noreferrer'>v{version}</a>"
            f"<span class='vh-tag'>Latest release</span></li>"
        )
    if is_real(notes):
        rows.append(
            f"<li><a href='{html.escape(notes)}' target='_blank' rel='noopener noreferrer'>Release notes ↗</a></li>"
        )
    if not rows:
        rows.append("<li>No releases published yet</li>")
    return (
        '<div class="vh"><div class="section-head"><h2>Version history</h2>'
        "<p>Older releases are available on GitHub.</p></div><ul>"
        + "".join(rows)
        + "</ul></div>"
    )


def trust_bar(p: dict) -> str:
    """Explicit security & trust signals, placed near the download area."""
    items = []
    repo = p.get("repository", "")
    dl = p.get("download", "")
    url = p.get("url", p.get("demo", ""))
    if is_real(repo):
        items.append(f'<a href="{html.escape(repo)}" target="_blank" rel="noopener noreferrer">Official GitHub release</a>')
    elif is_real(dl):
        items.append(f'<a href="{html.escape(dl)}" rel="noopener noreferrer">Verified download</a>')
    elif is_real(url):
        items.append(f'<a href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Live demo</a>')
    if not items:
        items.append("<span class='quiet'>Official source is linked below</span>")
    return f'<div class="trust-bar"><span class="trust-dots" aria-hidden="true"></span><span class="trust-text">{html.escape(" · ".join(items))}</span></div>'


def privacy_note(p: dict) -> str:
    """Grounded, content-backed offline/privacy statement."""
    feats = " ".join(p.get("features", []) or []).lower()
    desc = (p.get("description", "") or "").lower()
    if "no account or microtransactions" in feats:
        return "100% offline. No account or microtransactions."
    if "offline" in feats or "offline" in desc:
        return "Works fully offline — local data, no cloud sync."
    return None


def faq_block(p: dict) -> str:
    """FAQ answering the conversion-blockers, using only reported facts."""
    plats = p.get("platforms", []) or []
    req = p.get("requirements", "") or ""
    feats = " ".join(p.get("features", []) or []).lower()
    desc = (p.get("description", "") or "").lower()
    release_notes = is_real(p.get("release_notes", ""))
    items = []
    if plats or req:
        items.append(("What do I need to run this?", ", ".join(plats) if plats else "No requirements published yet."))
    if "no account or microtransactions" in feats:
        items.append(("Do I need an account?", "No account is required."))
    elif "offline" in feats or "offline" in desc:
        items.append(("Do I need an account?", "No — it runs fully offline on your device."))
    items.append(("Where do I find older versions?", "Older releases are published on GitHub." if release_notes else "No older releases have been published yet."))
    items.append(("Is this app on the App Store or Google Play?", "Not distributed through a public app store. The official build is linked in the download area."))
    body = "".join(
        f"<li><details class='faq-item'><summary>{html.escape(q)}</summary>"
        f"<p>{html.escape(a)}</p></details></li>"
        for q, a in items
    )
    return f'<ul class="faq-list">{body}</ul>'


def spec_rows(p: dict) -> str:
    """Key/value technical details, honestly filled from the content."""
    rows = []
    plats = p.get("platforms", []) or []
    req = p.get("requirements", "") or ""
    techs = p.get("technologies", []) or []
    if plats:
        rows.append(("Platforms", ", ".join(plats)))
    if req:
        rows.append(("Requirements", html.escape(req)))
    if techs:
        rows.append(("Built with", ", ".join(techs)))
    if not rows:
        return '<p class="coming-soon">Technical details coming soon</p>'
    return (
        '<div class="spec-grid">'
        + "".join(f"<div class='spec'><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
        + "</div>"
    )


def app_detail_body(p: dict, siblings: list) -> str:
    """Standalone detail/download page body for one app."""
    pname = p.get("name", "Untitled")
    desc = p.get("description", "") if is_real(p.get("description")) else ""
    techs = p.get("technologies", []) if isinstance(p.get("technologies"), list) else []
    feats = p.get("features", []) if isinstance(p.get("features"), list) else []
    plats = p.get("platforms", []) if isinstance(p.get("platforms"), list) else []

    if feats:
        feats_html = "<ul>" + "".join(f"<li>{html.escape(f)}</li>" for f in feats) + "</ul>"
    else:
        feats_html = f'<p class="coming-soon">Key features coming soon</p>'
    if plats:
        plats_html = "<ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in plats) + "</ul>"
    else:
        plats_html = f'<p class="coming-soon">Supported platforms coming soon</p>'

    primary = primary_button(p)
    plat_cards = platform_cards(p)
    vh = version_history(p)
    trust = trust_bar(p)
    privacy = privacy_note(p)
    faq_html = faq_block(p)
    specs = spec_rows(p)

    more = ""
    if siblings:
        items = "".join(
            f'<li><a href="./{app_route(q)}">{html.escape(q.get("name", "Untitled"))}</a></li>'
            for q in siblings[:3]
        )
        more = f"""
    <section class="block" aria-label="More applications">
      <div class="wrap">
        <div class="section-head"><h2>More applications</h2><p>Same category.</p></div>
        <div class="prose"><ul>{items}</ul></div>
      </div>
    </section>"""

    return f"""
    <section class="block download-hero hero-load section-fox" aria-label="{html.escape(pname)}">
      <div class="wrap">
        <div class="fox-corner fox-in-hero">{fox_svg("corner")}</div>
        <div class="download-hero-top">
          <div class="card-badges">{badges_html(p)}</div>
          <h1 class="page-title">{html.escape(pname)}</h1>
          <p class="lede">{html.escape(desc) if desc else f'<span class="todo">Coming soon · description to follow</span>'}</p>
        </div>
        <div class="download-hero-actions">
          <div class="primary-wrap">{primary}</div>
          <div class="plat-wrap">{plat_cards}</div>
          {f'<div class="privacy-note">{html.escape(privacy)}</div>' if privacy else ""}
        </div>
        {trust}
      </div>
    </section>

    <section class="block" aria-label="Screenshots">
      <div class="wrap">
        <div class="section-head"><h2>Screenshots</h2></div>
        <div class="shot-frame">{shot_html(p, label="screenshot")}</div>
      </div>
    </section>

    <section class="block" aria-label="Description">
      <div class="wrap">
        <div class="section-head"><h2>About</h2></div>
        <div class="prose">
          <p>{html.escape(desc) if desc else f'<span class="todo">Coming soon · description to follow</span>'}</p>
        </div>
      </div>
    </section>

    <section class="block" aria-label="Requirements">
      <div class="wrap">
        <div class="section-head"><h2>Requirements</h2></div>
        <div class="prose">
          {specs}
        </div>
      </div>
    </section>

    <section class="block" aria-label="Version history">
      <div class="wrap">
        <div class="section-head"><h2>Version history</h2><p>Older releases are available on GitHub.</p></div>
        {vh}
      </div>
    </section>

    <section class="block" aria-label="FAQ">
      <div class="wrap">
        <div class="section-head"><h2>FAQ</h2><p>Quick answers before you download.</p></div>
        <div class="prose">{faq_html}</div>
      </div>
    </section>

    {more}

    <section class="block" aria-label="Back to catalog">
      <div class="wrap">
        <p><a class="btn btn-ghost" href="./applications.html">← All applications</a></p>
      </div>
    </section>
    """
# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def home_page(ctx: dict) -> str:
    featured = [p for p in ctx["projects"] if p.get("featured")]
    cards = "\n".join(catalog_card(p) for p in featured)
    contact = ctx["contact_links"]
    return f"""<section class="hero fox-hero" aria-label="Welcome">
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
          <dl class="hero-notes" aria-label="Why trust this work">
            <div><dt>Research-backed</dt><dd>UCC Biomedical Science</dd></div>
            <div><dt>Offline-first</dt><dd>Local-first apps</dd></div>
            <div><dt>Clean design</dt><dd>Privacy-conscious UX</dd></div>
          </dl>
        </div>
        <div class="fox-stage" aria-hidden="true">
          {fox_svg("hero")}
        </div>
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
    cards = "\n".join(catalog_card(p) for p in ordered)
    categories = sorted({p.get("category", "").strip() for p in ordered if is_real(p.get("category"))})
    statuses = list(dict.fromkeys(p.get("status", "").strip() for p in ordered if p.get("status")))
    chips = ['<button class="filter-btn" data-filter="all" aria-pressed="true">All</button>']
    for c in categories:
        chips.append(
            f'<button class="filter-btn" data-filter="cat:{html.escape(c)}" aria-pressed="false">{html.escape(c)}</button>'
        )
    for st in statuses:
        chips.append(
            f'<button class="filter-btn" data-filter="status:{html.escape(st)}" aria-pressed="false">{html.escape(st)}</button>'
        )
    filters = chips
    grid = cards if cards else "<div class=\"prose\"><p>No applications listed yet.</p></div>"
    return f"""<section class="block section-fox" aria-label="Applications">
      <div class="wrap">
        <div class="fox-corner">{fox_svg("corner")}</div>
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
          <div class="filter-row" role="group" aria-label="Filter by category and status">
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
    name = ctx["name"]; role = ctx["role"]; tagline = ctx["tagline"]
    location = ctx["location"]; contact = ctx["contact_links"]
    story = md_to_html(ctx["sections"].get("about", ""))
    research = md_to_html(ctx["sections"].get("research", ""))
    design = md_to_html(ctx["sections"].get("design work", ctx["sections"].get("design", "")))
    return f"""
    <section class="block section-fox" aria-label="About">
      <div class="wrap">
        <div class="fox-corner">{fox_svg('corner')}</div>
        <div class="section-head"><h2>About</h2><p>{html.escape(tagline)}</p></div>
        <div class="prose">
          <h3>{role}</h3>
          <p class="quiet">{html.escape(location)}</p>
          {story}
        </div>
      </div>
    </section>
    <section class="block" aria-label="Quick reference">
      <div class="wrap">
        <div class="section-head"><h2>Quick reference</h2></div>
        <div class="two-col">
          <div class="mini"><h3>Research</h3>{research if research else '<p class="todo">TODO: Add research details.</p>'}</div>
          <div class="mini"><h3>Design work</h3>{design if design else '<p class="todo">TODO: Add design examples.</p>'}</div>
        </div>
      </div>
    </section>
    <section class="block" id="contact" aria-label="Contact">
      <div class="wrap">
        <div class="section-head"><h2>Contact</h2><p>Direct line, no forms.</p></div>
        <div class="prose contact-box">{''.join(contact) if contact else "<p class='todo'>TODO: Add email and LinkedIn links.</p>"}</div>
      </div>
    </section>"""

def studio_page(ctx: dict) -> str:
    name = ctx["name"]; company = ctx["company"]; role = ctx["role"]
    tagline = ctx["tagline"]; location = ctx["location"]
    email = ctx["email"]; socials = ctx["socials"]
    sections = ctx["sections"]
    contact = ctx["contact_links"]
    story = md_to_html(sections.get("about", ""))
    research = md_to_html(sections.get("research", ""))
    leadership = md_to_html(sections.get("leadership", ""))
    skills = md_to_html(sections.get("skills", ""))
    design = md_to_html(sections.get("design work", sections.get("design", "")))
    return f"""
    <section class="block section-fox" aria-label="Studio">
      <div class="wrap">
        <div class="fox-corner">{fox_svg('corner')}</div>
        <div class="section-head">
          <h2>{html.escape(role)}</h2>
          <p>{html.escape(tagline)}</p>
        </div>
        <div class="prose">
          <h3>{name}</h3>
          <p class="quiet">{html.escape(location)}</p>
          {story}
        </div>
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
    <section class="block" aria-label="Skills + design">
      <div class="wrap">
        <div class="section-head"><h2>Skills &amp; Design</h2><p>Tools of the trade.</p></div>
        <div class="two-col">
          <div class="mini"><h3>Skills</h3>{skills if skills else '<p class="todo">TODO: Add skills.</p>'}</div>
          <div class="mini"><h3>Design Work</h3>{design if design else '<p class="todo">TODO: Add design examples.</p>'}</div>
        </div>
      </div>
    </section>
    <section class="block" id="contact" aria-label="Contact">
      <div class="wrap">
        <div class="section-head"><h2>Contact</h2><p>Direct line, no forms.</p></div>
        <div class="prose contact-box">{''.join(contact) if contact else "<p class='todo'>TODO: Add email and LinkedIn links.</p>"}</div>
      </div>
    </section>"""




def not_found_page(ctx: dict) -> str:
    return f"""<section class="block" aria-label="Page not found">
      <div class="wrap">
        <div class="section-head"><h2>Not found</h2><p>Diagnosis: missing page.</p></div>
        <div class="nf-stage">
          {fox_svg("dig")}
          <p><strong>Kit sniffed through every den — there's nothing at this address.</strong></p>
          <p class="quiet">It may have moved, or the link is wrong.</p>
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
        ("studio.html", "Studio", f"{company} — {tagline}",
         f"{company}: {tagline} Offline-first, privacy-conscious apps by {name}, {role}.",
         "studio.html", studio_page(ctx), True),
        ("about.html", "About", f"About {name} — {company}",
         f"About {name}, {role} based in {location}: biomedical research, leadership, skills, and contact.",
         "about.html", about_page(ctx), True),
        ("404.html", "Not found", f"Page not found — {company}",
         f"The requested {company} page could not be found.",
         "", not_found_page(ctx), True),
    ]

    # One standalone detail/download page per app, data-driven.
    # Siblings share a category (no invented relationships).
    for p in projects:
        pname = p.get("name", "Untitled")
        cat = p.get("category", "").strip() if is_real(p.get("category")) else ""
        siblings = [q for q in projects
                    if q is not p and cat and is_real(q.get("category"))
                    and q.get("category", "").strip() == cat]
        desc = p.get("description", "") if is_real(p.get("description")) else ""
        pages.append(
            (app_route(p), pname, f"{pname} — {company}",
             f"{pname} ({p.get('status', 'status TBD')}) by {company}: {desc[:140]}",
             "applications.html", app_detail_body(p, siblings), True),
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, _label, title, desc, active, body, scripts in pages:
        page = base_page(title=title, description=desc, company=company,
                         tagline=tagline, email=email, socials=socials,
                         active=active, body=body,
                         canonical=f"{SITE_URL}/{filename}" if filename != "404.html" else SITE_URL,
                         scripts=scripts)
        (out_dir / filename).write_text(page, encoding="utf-8")
    for asset in ("style.css", "app.js", "fox.js", "anime.umd.min.js",
                  "grims-mark.svg", "grims-logo-horizontal.svg",
                  "og-preview.png", "googlee8fcbc5f56b1ecd1.html"):
        src = ROOT / "assets" / asset
        if src.exists():
            shutil.copy(src, out_dir / asset)
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    shots_src = ROOT / "assets" / "screenshots"
    if shots_src.is_dir():
        shutil.copytree(shots_src, out_dir / "screenshots", dirs_exist_ok=True)
    # SEO: sitemap + robots for Google indexing (404 excluded from sitemap)
    today = date.today().isoformat()
    sitemap_files = ["index.html", "applications.html", "about.html"]
    sitemap_files += [app_route(p) for p in projects]
    urls = "\n".join(
        f"  <url><loc>{SITE_URL}/{f}</loc><lastmod>{today}</lastmod></url>"
        for f in sitemap_files
    )
    (out_dir / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n',
        encoding="utf-8",
    )
    (out_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    print(f"Built {len(pages)} pages with {len(projects)} projects into {out_dir}.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs")
    args = ap.parse_args()
    build(ROOT / args.out)


if __name__ == "__main__":
    main()
