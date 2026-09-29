# Prompt: Build my company and applications portfolio website

Copy everything between **BEGIN PROMPT** and **END PROMPT** into your AI website builder or coding assistant. Replace the Markdown content in the example files with your own details when you are ready.

---

## BEGIN PROMPT

You are a senior web designer and front-end developer. Design and build a polished, production-ready **static website** for my company and my collection of applications. The site should make it easy for visitors to understand who I am, browse the apps I have made, open a running app, and visit its source repository.

### 1. Content comes from my Markdown files

Use these two Markdown files as the single source of truth for all personal, company, and app information:

- `content/profile.md` — my name, company name, role, short introduction, biography, contact information, and social links.
- `content/projects.md` — every application I want to display, with its live URL, GitHub repository, description, status, and optional technology tags or image.

Read and render the Markdown at **build time**. Do not require a database, server, login, external API, GitHub token, or browser-side Markdown fetch. Keep the result suitable for static hosting, including GitHub Pages. If the project already has a framework or build setup, inspect and use it rather than replacing it unnecessarily. Otherwise, prefer a lightweight static-first setup such as Astro, with JavaScript only for useful interactions.

Create both Markdown files if they do not exist. Use the schemas below and explain in a short README how I can edit them and rebuild the site. Do not invent my company details, biography, app names, features, awards, technologies, or URLs. If information is missing, leave a clear editable placeholder in the content file or show a graceful empty state. Never label an app “Running” unless its status in the Markdown says it is running/live.

#### `content/profile.md` format

```markdown
---
name: "YOUR NAME"
company_name: "YOUR COMPANY NAME"
role: "YOUR ROLE OR TITLE"
tagline: "A short line about what you build"
location: "OPTIONAL LOCATION"
email: "OPTIONAL CONTACT EMAIL"
website: "OPTIONAL PERSONAL OR COMPANY WEBSITE"
socials:
  github: "OPTIONAL GITHUB PROFILE URL"
  linkedin: "OPTIONAL LINKEDIN URL"
  x: "OPTIONAL X / OTHER SOCIAL URL"
---

# About

Write a short introduction about yourself, your company, what you do, and the kinds of problems your applications solve. This text can be as short or detailed as needed.
```

Treat empty values and example placeholders like `YOUR NAME` as missing content. Do not print them on the live page. The company name should be easy to change in this file and should appear in the site title, header, and footer where appropriate.

#### `content/projects.md` format

Each project starts with a second-level Markdown heading. Use the labels shown below; optional fields can be omitted. The site should support any number of project entries.

```markdown
## Applications

## PocketLedger

- status: Running
- url: https://github.com/your-account/pocket-ledger
- repository: https://github.com/your-account/pocket-ledger
- description: An offline-first personal finance application designed for seamless local expense tracking and budget management without requiring constant internet connectivity.
- technologies: React Native, JavaScript, Supabase
- category: Productivity
- featured: true
- image: /images/pocket-ledger.webp

## Project Nexus

- status: Running
- url: https://github.com/your-account/project-nexus
- repository: https://github.com/your-account/project-nexus
- description: A full-screen living room media hub application built for Fedora Linux, integrating custom media playback and backend service orchestration.
- technologies: Python, FastAPI, LibVLC, HTML/CSS
- category: Media & Entertainment
- featured: true
- image: /images/project-nexus.webp

## The Pink Whisk

- status: Running
- url: https://github.com/your-account/the-pink-whisk
- repository: https://github.com/your-account/the-pink-whisk
- description: A full-featured website and interactive feature layout designed and built for a boutique bakery brand.
- technologies: Penpot, HTML, CSS, JavaScript
- category: Design & Web
- featured: false
- image: /images/the-pink-whisk.webp

## Grimoire Astral Architect

- status: Running
- url: https://github.com/your-account/grimoire-astral-architect
- repository: https://github.com/your-account/grimoire-astral-architect
- description: A software repository featuring automated CI/CD build and release workflows configured via GitHub Actions.
- technologies: GitHub Actions, Shell, CI/CD
- category: Developer Tools
- featured: false
- image: /images/grimoire-astral-architect.webp
```

The example values above are **illustrative placeholders only**. Do not leave them presented as real projects. If no real project data has been supplied yet, show an honest empty state such as “Your applications will appear here. Add entries to `content/projects.md` to get started.”

### 2. Visual direction

Create an original, high-craft **editorial product portfolio**: confident typography, clear hierarchy, strong composition, and a distinctive but professional visual identity. It should feel designed for a real company, not like a generic template or a default component-library dashboard.

Use the company name, profile, and any real brand assets in the Markdown or repository to inform the visual direction. If no brand identity is supplied, establish one with a restrained dark-ink and warm-light base, one bold accent color, careful spacing, and a subtle texture or graphic motif. Keep contrast readable. Use CSS to create the visual system and layouts; reserve heavier animation or 3D for an optional enhancement that genuinely supports the brand. Do not use fabricated screenshots, stock imagery, fake statistics, or decorative effects that compete with the applications.

The site should feel visually distinctive while staying quick to scan. Applications are the main content, so do not hide them behind an elaborate intro or excessive scroll animation.

### 3. Page structure and behavior

Build a responsive homepage with these sections:

1. **Header:** company name or logo/wordmark, simple navigation to Applications and About, plus an optional contact link if the profile contains one.
2. **Hero:** company name, my name/role when provided, a concise tagline, and one clear link or button to browse the applications.
3. **Applications:** a well-designed responsive grid or similarly clear layout showing all Markdown project entries. Each app should display its name, short description, status badge, category if present, and technology tags if present. Give featured entries visual priority without hiding the rest.
4. **Useful discovery controls:** add client-side search and category filters when there is enough project data to make them useful. They must work with the locally rendered project data and should not require an API. Include a helpful no-results state and an obvious way to clear filters.
5. **App actions:** show a prominent **Open app** link when a live URL exists and a **View source** link when a repository URL exists. Do not render buttons that point nowhere. Open external links safely. Make it clear which action launches the app and which opens GitHub.
6. **About:** render my Markdown biography and company information. Show only contact and social links that have real values.
7. **Footer:** company name, optional contact/social links, and a quiet copyright line. Do not invent a founding year.

Use a recognisable visual treatment for each project card, but use only supplied project images. If there is no image, create a tasteful CSS-based graphic or monogram from the project name rather than pretending to show an app screenshot. Keep statuses truthful and visually distinguish live/running, in-development, archived, or other supplied states.

### 4. Craft, accessibility, and performance requirements

- Use semantic HTML for headings, navigation, main content, sections, links, and buttons.
- All navigation, search, filters, and project actions must work with a keyboard. Preserve a visible focus indicator; do not create a keyboard trap.
- Keep text readable and contrast strong. Do not rely on color alone to communicate status.
- Make the layout responsive and usable on mobile, tablet, and desktop. Support browser zoom and content reflow without making ordinary text require horizontal scrolling.
- Respect the `prefers-reduced-motion` setting. Any motion should be subtle, optional, and nonessential; provide a calm experience when reduced motion is requested.
- Prefer efficient CSS and small amounts of JavaScript. Use responsive image sizes and lazy-load only below-the-fold images; do not delay the main hero content unnecessarily.
- Ensure the site still has meaningful content if JavaScript is unavailable. The project list and About text should be present in the generated HTML.
- Use local fonts/assets or system fallbacks where practical. Avoid adding dependencies for effects that can be done cleanly with CSS.
- Do not autoplay sound or video.

### 5. GitHub Pages and project URLs

Make the portfolio itself deployable as a static site to GitHub Pages. Account for a configurable base path if the chosen framework needs one. Do not assume the portfolio’s own URL is the same as any individual app URL. The app launcher must use the exact live URL supplied in `content/projects.md`; the source link must use the exact repository URL supplied there.

Do not call GitHub or any other service at runtime to discover repositories. I will maintain the app list in Markdown. Do not assume that every repository has GitHub Pages enabled or that every app URL remains active.

### 6. Deliver a working project, not just a mockup

Inspect the repository and existing setup first. Then implement the site, install only necessary dependencies, and run the available build or tests. Fix errors you encounter. Provide:

- the working source code;
- `content/profile.md` and `content/projects.md` ready for me to edit;
- a README that explains how to add, edit, and remove apps, how to update company/about details, how to run locally, how to build, and how to deploy to GitHub Pages;
- a short summary of what was built and any assumptions or fields I still need to fill in.

Do not claim deployment succeeded unless you actually deployed it. Do not overwrite unrelated existing work.

## END PROMPT

---

### Quick way to use it

1. Paste the prompt into your AI coding tool while the website repository is open.
2. Let it create the site and the two Markdown content files.
3. Fill in `content/profile.md` with your company and biography.
4. Add one section per app in `content/projects.md`. Use the exact live URL and GitHub repository URL for each app.
5. Rebuild and deploy the static site using the instructions in its README.
