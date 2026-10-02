# Known gaps

An honest running list of what this site does not yet handle. Add to it
rather than quietly leaving things out.

## Deployment and infrastructure

- **Every page is `noindex`.** Deliberate while placeholders are visible;
  remove at launch, together with a zero-placeholder check.
- **No preview channels yet.** Pull requests deploy nothing; only `main`
  deploys, straight to live (step 3).
- **Caching is an interim `no-cache` on everything**, CSS, JS, fonts and
  images included. That is correct (browsers always revalidate, so a fix is
  never served stale) but slower than necessary: every page view
  revalidates every asset. Step 3 replaces it with content-hashed asset
  names cached `immutable` for a year, HTML staying `no-cache`.
- **Node 20 actions and `ubuntu-latest`.** GitHub warns that
  `actions/checkout@v4`, `actions/setup-node@v4` and
  `google-github-actions/auth@v2` run on deprecated Node 20, and that
  `ubuntu-latest` moves to Ubuntu 26 from 19 Oct 2026. Bump the actions and
  pin the runner image in step 3.
- **No CI checks** (duplicate functions, missing ids/classes, broken links,
  HTML validation, Lighthouse) yet (step 3). Until then the only checks are
  the ones run by hand before each push.
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

- **Almost every parish fact is a placeholder.** Confirmed by the parish
  and published: established in 1993; the oldest Coptic Orthodox church in
  the Republic of Ireland; inaugurated in 1994 by H.H. Pope Shenouda III.
  Everything else (service times, address and Eircode, contact email,
  clergy, ministries and age groups, diocese name, visiting guidance) shows
  as a dashed `[PLACEHOLDER]`.
- **The design system holds details not yet confirmed here.** Its notes
  list service times, an address, a contact email, a priest's name, a
  Scouts group and the diocese's wording, some taken from the 2021 Google
  Site. None is published until confirmed for step 5.
- **The Ethiopian Orthodox Tewahedo line is left out on purpose**, at the
  parish's request, although the design system suggests it.
- **Term explanations need clergy review.** "Divine Liturgy", "Coptic",
  "Midnight Praises" and "Sunday School" carry short generic definitions
  from the design system, with every parish-specific detail (days, times)
  removed. The wording is not the parish's own yet.
- **Events, news, resources and ministries are empty states.** There is no
  content source for them yet. The design's sample events and news were
  illustrative and are not used.
- **No photos.** Arched frames show "to be supplied". Children's photos
  need recorded parental consent before any are added.
- **English only.** No Arabic pages or language switch until a native
  speaker can review the Arabic copy. Arabic fonts are not loaded.

## Design and features

- **Breakpoints differ from the design system on purpose.** The design uses
  720px and 960px; this site uses the three ranges agreed for the project
  (<768, >=768, >=1280). The full navigation therefore appears only from
  1280px; tablets up to 1279px use the Menu button and the bottom action bar.
- **No Give button.** The design has one, but no donation method is
  confirmed.
- **No contact form.** A static site has nowhere to send it; needs a decision
  (a form service, or email only).
- **No map, and Get directions is a placeholder.** Needs the confirmed
  address; a map embed would also need cookie consent.
- **No Privacy, Cookie or Safeguarding pages**, so the footer links the
  design shows are left out. Needed before launch; the site sets no cookies
  today.
- **No favicon.** `/favicon.ico` returns 404. The design system says to ask
  the church for a small-size mark rather than crop the logo, so none is
  made up here.
- **The logo is only legible at large sizes.** Resized copies of the
  supplied PNG (no cropping or recolouring) at 112, 176 and 352px. At 48-56px
  in the header the lettering cannot be read; a simplified mark would help.
- **Mobile menu: Escape closes it, but focus is not trapped while open.** The
  design asks for both. The menu is a native `<details>` so it works without
  JavaScript; trapping focus would need more script.
- **Header and footer are copied into every page** (no build step). A change
  must be made in all ten files; a step 3 check should fail if they drift.
- **No structured data, Open Graph image, sitemap or `robots.txt` yet.**
