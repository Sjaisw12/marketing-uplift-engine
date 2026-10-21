# Static deployment proposal — approval required

No hosting registration, infrastructure, public push, PR, release or deployment
was performed. The site is a static artifact, with no backend or secrets.

## Recommended later method

Use existing GitHub repository + GitHub Pages **after** owner review and explicit
publication approval. Node 24, working directory `web`, `npm ci`, `npm run build`;
upload only `web/dist` as the Pages deployment artifact. No research commands,
Python datasets, fitted models, frozen memberships or checkpoint operations.
A free static host such as Cloudflare Pages is also technically suitable, but
would require separately approved account/project setup. Do not create either now.

Vite uses `base: './'`; resource URLs are relative. Navigation uses fragment anchors
(`#study`, `#science`, etc.), so no SPA history rewrite is required. A secure HTTPS
host or localhost is required for Web Crypto checksum verification. Serve the
snapshot with lossless bytes: text transformations or line-ending changes fail closed.
Enable normal HTTP gzip/Brotli compression and caching without changing decoded bytes.
Keep data and build assets versioned together; avoid stale-cache mixing.

## Prepublication operator checklist

- [ ] Owner reviews desktop/mobile screenshots and the complete-stranger checklist.
- [ ] Owner approves the exact source commit, production build and public disclosure.
- [ ] Verify snapshot SHA-256 and package lock, then run check/tests/format/build.
- [ ] Review `dist/`: only index, built assets, favicon and approved aggregate JSON.
- [ ] Preserve visible Criteo CC BY-NC-SA 4.0 attribution/noncommercial terms; MIT only for software.
- [ ] Owner separately authorizes public source push/PR and any hosting workflow.
- [ ] Configure Pages and read-only build / narrowly scoped deployment permissions.
- [ ] Deploy only the reviewed static artifact; no credentials in JS or repository files.
- [ ] Verify HTTPS, hash loading, every hash link, keyboard controls, mobile layouts and failure state.
- [ ] Verify primary no targeting, illustrative financial labels, saved scenario bounds and 765-family qualifications.
- [ ] Add a real live URL to the repository only after successful separately approved deployment.

No analytics, cookies, authentication, environment variables or paid services are
required. The only application fetch is the same-origin public aggregate JSON,
with credentials omitted. External research links open only on visitor action.
For optional host hardening, review CSP/Referrer-Policy/nosniff headers with that
host before enabling them; no untested policy is claimed enforced. Do not route
this static site to any private research/execution service.

## Final quality-gate additions

See `FINAL_REVIEW.md` for the current gate evidence and remaining checks. The
historical verification report is retained unchanged. The exact author identity
is in `site.config.json`; LinkedIn remains omitted by owner instruction.

`productionUrl: null` is the explicit review-only state. It omits canonical,
`og:url` and absolute social-image URLs; it does not emit a fake public URL.
After the owner chooses an exact host, review an HTTPS URL ending in `/`, including
the repository subpath for Pages. Review the configuration-bound metadata tests,
run `npm run build` and `npm run release:check`. The latter intentionally exits 2
until configured and rebuilt; a passing check never grants publication permission.
Synthetic tests cover Pages-style subpaths, but no host has been registered/tested.

The deployment artifact now includes `social-preview.png` (1200×630) and its SVG
source in addition to index, bundled assets, favicon and approved aggregate JSON.
The public and distribution allowlists reject unexpected additions. Serve the PNG
at its configured absolute HTTPS URL; verify it with LinkedIn Post Inspector only
after authorized deployment. No social crawler can inspect an unpublished localhost
site. No LinkedIn profile link is required for sharing metadata.
