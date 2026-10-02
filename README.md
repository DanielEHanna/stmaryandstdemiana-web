# St. Mary & St. Demiana Coptic Orthodox Church, Bray — website

A static site (plain HTML, CSS and JavaScript; no build step) served by
Firebase Hosting from the `project-b14e4945-5820-4d6e-808` project (shared
with the Sunday School portal; see `KNOWN_GAPS.md`).

See `KNOWN_GAPS.md` for what the site does not yet handle.

## Working on the site

- Edit the files in `public/` directly. There is no build step.
- After changing anything under `public/assets/`, run
  `python3 scripts/stamp_assets.py`. It updates the `?v=` content hash on
  every reference to that file, so browsers fetch the new version. Assets
  are cached for a year, so a stale stamp would serve the old file. CI fails
  if a stamp is stale.
- Before pushing, run `python3 scripts/check_site.py`. Before launch, run it
  with `--launch` too; it fails on any `[PLACEHOLDER]` or `noindex`.
- Pull requests deploy to a preview channel, and `main` deploys to live.
  Both are checked from their public URL by `scripts/verify_deploy.py`.
