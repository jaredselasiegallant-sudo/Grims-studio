#!/usr/bin/env python3
"""Grims Studio static site builder.

Reads content/profile.md and content/projects.md at build time
and emits docs/index.html + assets. No database, no API, no runtime fetch.
Suitable for GitHub Pages.

Usage:
    python3 build.py [--base-path /repo-name] [--out docs]
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
    """Parse ## Title + '- key: value' entries. Returns list of dicts."""
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
            elif key in ("featured",):
                current[key] = val.lower() in ("true", "yes", "1")
            else:
                current[key] = val
    # drop entries with placeholder names
    return [p for p in projects if is_real(p.get("name"))]


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
    about_html = md_to_html(sections.get("about", body_md))

    # Render research/leadership/skills/design blocks if present
    extra_keys = ["research", "leadership", "skills", "design work", "design"]
    extras = []
    for key in extra_keys:
        if sections.get(key):
            title = "Design Work" if key.startswith("design") else key.capitalize()
            extras.append((title, key, md_to_html(sections[key])))

    categories = sorted({p.get("category", "").strip() for p in projects if is_real(p.get("category"))})

    # Build cards (server-rendered so content exists without JS)
    cards_html = []
    for p in projects:
        pname = p.get("name", "Untitled")
        status = p.get("status", "").strip() if is_real(p.get("status")) else ""
        desc = p.get("description", "") if is_real(p.get("description")) else ""
        cat = p.get("category", "").strip() if is_real(p.get("category")) else ""
        techs = p.get("technologies", []) if isinstance(p.get("technologies"), list) else []
        featured = bool(p.get("featured"))
        url = p.get("url", "") if is_real(p.get("url")) else ""
        repo = p.get("repository", p.get("repo", "")) if is_real(p.get("repository", p.get("repo"))) else ""
        image = p.get("image", "") if is_real(p.get("image")) else ""
        search_blob = " ".join([pname, desc, cat, " ".join(techs), status])

        actions = []
        if url and url.startswith("http"):
            actions.append(
                f'<a class="action-open" href="{html.escape(url)}" target="_blank" rel="noopener noreferrer">Open app ↗</a>'
            )
        if repo and repo.startswith("http"):
            actions.append(
                f'<a class="action-src" href="{html.escape(repo)}" target="_blank" rel="noopener noreferrer">View source</a>'
            )
        actions_html = f'<div class="card-actions">{"".join(actions)}</div>' if actions else ""

        img_html = ""
        if image:
            img_html = f'<img src="{html.escape(image)}" alt="" loading="lazy" />'

        badges = ""
        if status:
            badges += f'<span class="badge status"><span aria-hidden="true">{status_icon(status)}</span> {html.escape(status)}</span>'
        if cat:
            badges += f'<span class="badge cat">{html.escape(cat)}</span>'

        tags_html = ""
        if techs:
            tags_html = '<div class="tags">' + "".join(f"<span>{html.escape(t)}</span>" for t in techs) + "</div>"

        cards_html.append(f"""
        <article class="card project-card{' featured' if featured else ''}" data-category="{html.escape(cat)}" data-search="{html.escape(search_blob)}">
          <div class="card-top">
            <div class="monogram" aria-hidden="true">{html.escape(monogram(pname))}</div>
            <h3>{html.escape(pname)}</h3>
          </div>
          {img_html}
          <div class="card-badges">{badges}</div>
          <p class="desc">{html.escape(desc)}</p>
          {tags_html}
          {actions_html}
        </article>""")

    if cards_html:
        grid_html = "\n".join(cards_html)
    else:
        grid_html = '<div class="prose"><p>Your applications will appear here. Add entries to <code>content/projects.md</code> to get started.</p></div>'

    filter_buttons = ['<button class="filter-btn" data-filter="all" aria-pressed="true">All</button>']
    for c in categories:
        filter_buttons.append(
            f'<button class="filter-btn" data-filter="{html.escape(c)}" aria-pressed="false">{html.escape(c)}</button>'
        )

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

    extras_html = ""
    if extras:
        blocks = []
        for title, key, body_html in extras:
            anchor = re.sub(r"\s+", "-", key)
            blocks.append(f'<div class="mini" id="{anchor}"><h3>{html.escape(title)}</h3>{body_html}</div>')
        extras_html = f"""
        <section class="block" id="research" aria-label="Research and background">
          <div class="wrap">
            <div class="section-head"><h2>Research &amp; Leadership</h2><p>Diagnosis first.</p></div>
            <div class="two-col">{''.join(blocks)}</div>
          </div>
        </section>"""

    title = f"{company} — {name}" if name else company
    hero_name = f"<h1>{html.escape(name)} <span>/ {html.escape(company)}</span></h1>" if name else f"<h1>{html.escape(company)}</h1>"

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(tagline + ' ' + role)}" />
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <a class="skip-link" href="#applications">Skip to applications</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="wordmark" href="#top" aria-label="{html.escape(company)} home">
        <span class="wordmark-mark" aria-hidden="true">GS</span>
        <span>{html.escape(company)}<small>{html.escape(tagline) if tagline else "Portfolio"}</small></span>
      </a>
      <nav class="site-nav" aria-label="Primary">
        <a href="#applications">Applications</a>
        <a href="#about">About</a>
        <a href="#research">Research</a>
        {f'<a class="nav-cta" href="mailto:{html.escape(email)}">Contact</a>' if email else '<a class="nav-cta" href="#contact">Contact</a>'}
      </nav>
    </div>
  </header>

  <main id="top">
    <section class="hero" aria-label="Introduction">
      <div class="wrap hero-grid">
        <div>
          <span class="eyebrow"><i aria-hidden="true"></i> {html.escape(company)} · Portfolio</span>
          {hero_name}
          {f'<p class="role-line">{html.escape(role)}</p>' if role else ""}
          {f'<p class="tagline">“{html.escape(tagline)}”</p>' if tagline else ""}
          <p class="lede">Biomedical researcher and lead developer diagnosing real-world friction — from heavy-metal tissue damage to unreliable connectivity — and engineering targeted, durable cures: offline-first apps, clean interfaces, local-first performance.</p>
          <div class="hero-actions">
            <a class="btn btn-primary" href="#applications">View Apps</a>
            <a class="btn btn-ghost" href="#research">Research &amp; Leadership</a>
          </div>
          <div class="hero-meta">
            {f'<span>📍 {html.escape(location)}</span>' if location else ""}
            {f'<span>✉️ {html.escape(email)}</span>' if email else ""}
          </div>
        </div>
        <aside class="hero-card" aria-label="Profile at a glance">
          <h2>Specimen card</h2>
          <dl class="specimen">
            <div><dt>Name</dt><dd>{html.escape(name) if name else "—"}</dd></div>
            <div><dt>Role</dt><dd>{html.escape(role) if role else "—"}</dd></div>
            <div><dt>Studio</dt><dd>{html.escape(company)}</dd></div>
            <div><dt>Base</dt><dd>{html.escape(location) if location else "—"}</dd></div>
            <div><dt>Focus</dt><dd>Offline-first · Privacy</dd></div>
          </dl>
        </aside>
      </div>
    </section>

    <section class="block" id="applications" aria-label="Applications">
      <div class="wrap">
        <div class="section-head">
          <h2>Applications</h2>
          <p>Prescribed software. {len(projects)} entries from <code>content/projects.md</code>.</p>
          <span class="count-pill" id="result-count" aria-live="polite"></span>
        </div>
        <div class="controls" role="search">
          <div class="search-wrap">
            <label for="app-search">Search</label>
            <input type="search" id="app-search" placeholder="Search apps, categories, tech…" autocomplete="off" />
          </div>
          <div class="filter-row" role="group" aria-label="Filter by category">
            {''.join(filter_buttons)}
          </div>
          <button class="clear-btn" id="clear-filters" type="button">Clear filters</button>
        </div>
        <div class="grid" id="app-grid">
          {grid_html}
        </div>
        <div class="no-results" id="no-results">
          <p><strong>No apps match your filters.</strong></p>
          <p class="quiet">Try a different search term or category.</p>
        </div>
      </div>
    </section>

    <section class="block" id="about" aria-label="About">
      <div class="wrap">
        <div class="section-head"><h2>About</h2><p>Clear diagnosis, clean cure.</p></div>
        <div class="prose">
          {about_html}
        </div>
      </div>
    </section>

    {extras_html}

    <section class="block" id="contact" aria-label="Contact">
      <div class="wrap">
        <div class="section-head"><h2>Contact</h2><p>Direct line, no forms.</p></div>
        <div class="prose contact-box">
          {''.join(contact_links) if contact_links else "<p>No public contact listed yet.</p>"}
        </div>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="wrap footer-inner">
      <strong>{html.escape(company)}</strong>
      <nav aria-label="Footer">
        {f'<a href="mailto:{html.escape(email)}">Email</a>' if email else ""}
        {f'<a href="{html.escape(socials["linkedin"])}" target="_blank" rel="noopener noreferrer">LinkedIn</a>' if socials.get("linkedin") else ""}
      </nav>
      <span class="quiet" style="margin-left:auto">© 2026 {html.escape(company)} · Static site · Edit <code>content/*.md</code> to update</span>
    </div>
  </footer>

  <script src="./app.js" defer></script>
</body>
</html>"""

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")
    for asset in ("style.css", "app.js"):
        src = ROOT / "assets" / asset
        if src.exists():
            shutil.copy(src, out_dir / asset)
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Built {out_dir / 'index.html'} with {len(projects)} projects.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs")
    ap.add_argument("--base-path", default="")
    args = ap.parse_args()
    build(ROOT / args.out)


if __name__ == "__main__":
    main()
