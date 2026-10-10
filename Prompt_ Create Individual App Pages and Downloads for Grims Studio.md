# Prompt: Create Individual App Pages and Downloads for Grims Studio

Update my existing static portfolio so the **Applications page is a catalog** and **each of my seven applications has its own individual detail and download page**. Do not treat this as one long page with expandable cards: every app must have a separate, directly accessible page with its own URL.

- **Live site:** `https://jaredselasiegallant-sudo.github.io/Grims-studio/`
- **Repository:** `jaredselasiegallant-sudo/Grims-studio`
- **GitHub Pages project subpath:** `/Grims-studio/`
- **Existing site:** inspect the repository to confirm its routes and build system before making changes.

## Required site structure

Keep the existing Home, Applications, and About pages. Turn the Applications page into a browsable catalog and add one separate page for each app, for **seven individual app pages**. The completed site should therefore have the existing main pages plus seven app-detail pages and the existing custom 404 page, if present.

Create individual pages for:

1. PocketLedger
2. Project Nexus
3. Grimoire: Astral Architect
4. Artwork Portfolio App
5. Gamified Book Reader
6. Personal AI Assistant
7. The Pink Whisk

Use the repository's existing page-generation conventions. Choose clear, stable, lowercase URL slugs consistent with the current project, such as `apps/pocketledger.html`, or an equivalent route if the build system already uses another convention. Ensure each app page can be opened directly, refreshed, bookmarked, and reached from the Applications catalog. Avoid root-relative links; all internal page and local asset references must work under `/Grims-studio/`.

## Inspect first and preserve project conventions

Before editing, inspect the repository structure, build scripts, content files, templates, existing Applications page, styles, scripts, app source folders, screenshots, existing download/release links, and GitHub Pages configuration. Follow the existing build and content workflow. Do not replace the framework or build system unless necessary; explain any exception and make the smallest compatible change.

Preserve the Grims Studio visual identity, typography, colors, header/footer, responsive design, and theme behavior. Keep changes focused on the app catalog, new app pages, and required supporting content or styles.

Do not invent app descriptions, features, status, screenshots, supported platforms, minimum requirements, version numbers, release dates, technologies, file sizes, checksums, or URLs. Use verified repository information. When a detail is unknown, omit it or use a clearly marked TODO in the project content and report it in the handoff.

## Applications catalog page

Keep the Applications page as the overview/catalog for all seven apps. Each app card should include the app name, a concise verified description, accurate status/category information where available, an existing screenshot or clearly labeled placeholder, and a prominent **View app details** link to that app's dedicated page.

Retain and make functional the existing search and category filter, if present. Ensure they work together and provide an empty-results message. Preserve or implement sorting that places verified Active and Completed projects first without guessing statuses. Do not overload the catalog with all the detail-page content; its primary purpose is helping visitors discover an app and navigate to its page.

## Individual app detail/download pages

Each of the seven apps must have its own page, generated using a reusable template or shared component where practical. Do not duplicate all page markup manually if the existing build system supports data-driven pages. Each page should have a consistent structure, adapted to the information actually available for that app:

- App name, verified status, category, concise summary, and longer description.
- Screenshot/gallery area using supplied repository assets; otherwise show a designed placeholder marked `TODO: Add screenshot for [app name]`.
- Key features, technologies, and supported platforms only when documented.
- A dedicated **Downloads** section showing verified, real installable artifacts, organized by platform or build where applicable.
- For each actual artifact, show a clear platform-specific download link, file type, verified version/release date, file size, minimum requirements, and checksum only when those details are known and verified.
- Separate, accurately named links for **View source**, **Live demo**, or **Release notes** only where working URLs exist.
- Breadcrumbs or a clear link back to the Applications catalog, plus consistent site navigation/footer.
- A contextual “More applications” or related-app navigation only if it can be done without inventing relationships.

Every app page must be a meaningful standalone page, even if its download is not available yet. When there is no verified installable build, state **Download not available yet** or a similarly clear status; optionally show a verified source/demo link. Add a TODO naming exactly what is missing, such as `TODO: Provide a tested Android APK for Project Nexus`. Do not render a dead, placeholder, or misleading Download button.

Do not equate a source repository, source archive, project page, or live demo with an installable build. If only source code is available, label it **View source** or **Download source code** and explain what it is. Do not imply visitors can install it directly unless that is verified.

If app source and documented build instructions are available, you may assess whether builds can be produced locally. Do not guess commands or claim a build works unless you actually build and test it. Do not publish releases, upload binaries, push changes, or deploy the site unless specifically authorized. If real binaries or external release hosting are missing, list what is needed and recommend an appropriate next step without pretending it is complete.

## Data model and static hosting

Use the existing content/data format where practical. Keep each app's metadata in one maintainable source and render both the catalog card and dedicated detail page from it if the current build system supports that approach. Support multiple download artifacts per app, with optional fields for platform, label, version, release date, file path or URL, file type, file size, checksum, and requirements. Do not populate unknown fields with invented defaults.

The site is static and hosted on GitHub Pages. Do not add a backend. Local files must be included in the generated site and referenced using paths that work under `/Grims-studio/`. External release assets may use verified absolute URLs. Avoid committing large binaries unless the current repository already uses that approach and the file sizes are appropriate; recommend GitHub Releases or suitable artifact hosting if needed.

## SEO, accessibility, and quality

Give every app page a unique, accurate HTML title and meta description, plus Open Graph metadata. Use an existing suitable image for social previews when available; otherwise mark the missing image as a TODO. Ensure paths resolve correctly when deployed beneath `/Grims-studio/`.

Use semantic headings and landmarks, accessible breadcrumbs, descriptive link labels, visible keyboard focus, sufficient contrast, meaningful image alt text, and text labels for statuses (not color alone). Any new-tab external links must include appropriate security attributes. Ensure the pages are responsive and the download controls are easy to use on mobile.

## Verification

1. Run the existing build and relevant tests/checks; fix issues caused by the changes.
2. Confirm that the build produces all seven individual app pages at their intended routes, in addition to the existing main pages.
3. Confirm every catalog card links to the correct app page and every app page links back to the catalog.
4. Verify that every displayed Download link points to a real, reachable artifact and that local artifacts are present in the generated output. Check file type and size when practical. Do not execute downloaded application files.
5. Verify all internal links and assets under the `/Grims-studio/` subpath, not only at the domain root.
6. Test catalog search and filtering, direct loading and refreshing of each detail page, desktop/mobile layouts, keyboard navigation, and theme behavior if applicable.
7. Check for broken links, missing assets, console errors, misleading download labels, and accessibility issues.
8. Do not claim that the live deployment or release assets were verified unless you actually check them. Do not imply changes were pushed, uploaded, released, or deployed if they were not.

## Deliverables

Provide the updated Applications catalog and **seven individual app detail/download pages**, plus any required templates, app data, styles, scripts, metadata, and local assets. In the handoff, summarize the architecture and changes, report build/test commands and results, and provide an app-by-app table listing each page route, verified availability/status, platforms, real download artifact/URL if available, and missing information or files. Clearly state which screenshots, binaries, release URLs, platform requirements, versions, checksums, or other details I still need to provide or confirm. State whether the live site and actual downloads were verified, and list remaining deployment/release steps without implying they were completed.
