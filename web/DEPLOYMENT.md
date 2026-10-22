# Static deployment proposal — approval required

Source is published for review in PR #16. No hosting registration, infrastructure,
merge of that PR or public deployment is performed by this preparation. The site
is a static artifact, with no backend or secrets.

## Intended later target: Vercel (not configured)

The current target is a static Vercel project with **Root Directory `web`**, Vite,
Node.js **24.x**, `npm ci`, build command `npm run build`, output directory `dist`.
No Python runtime, serverless function, model server, environment secret or research
command is required. Verify Node 24 is offered by the intended account before
launch; if unavailable, stop for a reviewed compatibility change, not a silent
runtime substitution. No Vercel project, account integration or domain was created.

PR #16 publishes source for review; it does not grant hosting approval. Do not import
or connect the Git repository yet: those actions can trigger automatic deployment.
GitHub Pages/Cloudflare are alternatives only, not configured deployment paths.

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
- [ ] Only after hosting approval, configure the Vercel settings and deployment controls below.
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

## Exact future Vercel operator sequence

1. Owner reviews and approves the source commit and remaining human/accessibility
   checks, then separately approves PR merge and the hosting operation. No merge
   or deployment is implied by a passing build.
2. Owner chooses the exact production HTTPS hostname. Keep `productionUrl: null`
   until that choice; no fake URL or preview-host canonical is appropriate. Prepare
   a reviewed presentation-only metadata commit with the root ending in `/`, run
   metadata tests/build and `npm run release:check`. Do not change frozen research.
3. Only after explicit hosting approval, import the public repository into Vercel.
   Use Vite, root `web`, Node 24.x, `npm ci`, `npm run build`, output `dist`. Set
   the owner-approved production branch; verify whether Git imports/updates create
   automatic preview/production deployments before enabling that integration.
4. Deploy only the approved source revision/static output. No credentials, Python
   dependencies, private paths or data-upload steps belong in this app. Read the
   actual build log and verify the deployed commit; do not assume successful launch.
5. Check HTTPS, aggregate byte hash, direct chapter links/refresh/history, keyboard
   and mobile rendering, no-targeting default, licensing, scenario controls and
   hypothetical-budget labels on the live domain. Confirm no private/external app
   resource requests and no unexpectedly transformed/stale aggregate bytes.
6. Verify canonical/OG/image URLs and 1200×630 social-image reachability; inspect
   LinkedIn Post Inspector after authorized deployment. Resolve actual cache or
   crawler errors before promotion. Update the root README's Live URL location
   only with the verified production URL; never call a local preview a deployment.

No deployment token, cloud resource, paid plan or account permission was requested.
The static app needs no paid backend; confirm current provider plan/terms and Criteo
noncommercial/share-alike restrictions with the owner before publication. This is
a configuration checklist, not verification of a live Vercel account or service.
