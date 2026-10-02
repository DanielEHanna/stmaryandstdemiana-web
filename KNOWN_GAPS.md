# Known gaps

An honest running list of what this site does not yet handle. Add to it
rather than quietly leaving things out.

## Deployment and infrastructure

- **Every page is `noindex`.** Deliberate while placeholders are visible;
  remove at launch, together with a zero-placeholder check.
- **Preview URLs are public.** Each pull request deploys to
  `stmaryandstdemiana-church--pr-<n>-<hash>.web.app` for 7 days. Anyone with
  the link can see unreleased pages; they are `noindex` but not private.
- **Assets are cached for a year by URL; the safety net is the stamp check.**
  `/assets/**` is `public, max-age=31536000, immutable`, which is only safe
  because every reference carries a `?v=` content hash that CI verifies.
  A reference added without a stamp would also be cached for a year
  unchanged: `check_site.py` fails on it, so it cannot reach `main`.
- **Lighthouse performance is reported, not enforced.** Shared CI runners
  vary too much for a hard floor; accessibility is enforced (>= 95).
- **Any branch in this repo can obtain the deploy identity, and that
  identity can release to live.** Preview deploys need the same Hosting
  Admin role as live ones (IAM cannot limit a role to preview channels), so
  splitting into two service accounts would not stop a pull request from
  publishing to live. The workflow only deploys live from `main`, but
  someone with push access could change the workflow on a branch. The real
  controls are who has write access to this repository and a protected
  `main` branch (not yet set; a GitHub setting, not code).
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
- **Confirmed on 2 Oct 2026, not yet published (step 5):** the service
  times, the address at 4-5 The Pines, Herbert Road, Bray,
  contact-us@stmaryandstdemiana.ie, Fr. Theophilous Avamina, the 20th
  Wicklow Scouts, and the diocese's name as written on the logo. The
  Eircode and a public phone number are still unconfirmed.
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
  must be made in all ten files; `check_site.py` fails if any page differs.
- **No structured data, Open Graph image, sitemap or `robots.txt` yet.**
- **No Content-Security-Policy header.** Everything is self-hosted, so a
  strict one is easy to add; deferred so it can be tested on a preview
  first. `nosniff` and a `Referrer-Policy` are set.
