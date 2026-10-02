# Known gaps

An honest running list of what this site does not yet handle. Add to it
rather than quietly leaving things out.

## Deployment and infrastructure

- **Placeholder only.** `public/index.html` is a deployment test with
  `noindex`. There is no real content, styling or logo yet (step 2).
- **No preview channels yet.** Pull requests deploy nothing; only `main`
  deploys, straight to live (step 3).
- **Cache-Control is only partly set.** HTML is `no-cache`; there are no
  CSS/JS/image rules because there are no assets yet. Headers have not been
  checked with `curl -I` against a real deploy (step 3).
- **No CI checks** (duplicate functions, missing ids/classes, broken links,
  HTML validation, Lighthouse) yet (step 3).
- **Actions are pinned by major tag (`@v4`, `@v2`), not commit SHA.**
  firebase-tools is pinned exactly; the actions are not. Could not look up
  SHAs from the build session.
- **Any branch in this repo can currently obtain the deploy identity.** The
  WIF provider only accepts tokens from this repository, but does not check
  the branch, and Hosting Admin can release to live. Someone with push access
  could edit the workflow on a branch and deploy. Decide in step 3 whether to
  restrict live deploys to `refs/heads/main` (e.g. a separate SA bound on
  `attribute.ref`) and protect `main`.
- **WIF condition matches the repository by name, not numeric id.** If this
  repo were deleted and someone recreated the same name under this account,
  the condition would match. Low risk (same owner); could switch to
  `repository_id`.
- **The site ID is `stmaryandstdemiana-church`**, because
  `stmaryandstdemiana-web` is now taken globally by the empty site in
  `stmary-stdemiana`. It only shows in the temporary `.web.app` URL.
- **Deploy-SA roles are unverified.** `firebasehosting.admin` +
  `serviceusage.serviceUsageConsumer` is believed sufficient for
  `firebase deploy --only hosting`; confirmed only once the first deploy
  succeeds.
- **Hosted in the Sunday School portal's project, not the church's.** The
  church's own project (`stmary-stdemiana`) could not be used: the only
  account available lacks permission to grant IAM roles there, and its
  Owner (`it@stmaryandstdemiana.ie`) was not reachable. This reverses the
  original rule that the two share nothing. Mitigations: the site has its
  own deploy service account (Hosting roles only), its own Workload Identity
  pool, and its own Hosting site; it cannot reach the portal's Cloud Run,
  Cloud SQL or data. Remaining risk: a project Owner/Editor of one is an
  Owner/Editor of both, and the church's public website depends on a
  personal organisation. Plan to move it to a church-owned project once
  that project's Owner is reachable.
- **Leftovers in `stmary-stdemiana` from the first attempt.** An empty
  Hosting site `stmaryandstdemiana-web` and a service account
  `hosting-deployer` with no roles. Harmless; delete or reuse later.
- **`link.stmaryandstdemiana.ie` is untouched on purpose.** It still sits on
  the default site of `stmary-stdemiana`, serving the dead Dynamic Links
  config (HTTP 400). What to do with it is an open decision.
- **No custom domain.** `stmaryandstdemiana.ie` / `www` do not resolve (step 4).

## Content

- No parish facts at all yet. The design system's README asserts
  "established in 1993", "oldest Coptic Orthodox church in the Republic of
  Ireland", "inaugurated by H.H. Pope Shenouda III in 1994" and "welcoming
  to Ethiopian Orthodox Tewahedo members". None of these is confirmed by the
  parish; none will be published until it is.
