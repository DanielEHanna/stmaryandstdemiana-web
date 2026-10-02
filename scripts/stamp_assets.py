#!/usr/bin/env python3
"""Stamp every /assets/ reference with a hash of the file it points to.

Each reference in public/*.html and public/assets/css/*.css becomes
  /assets/css/site.css?v=<first 12 hex of the file's SHA-256>
so the URL changes exactly when the file's bytes change. Browsers may then
cache assets for a year (firebase.json marks /assets/** immutable): a changed
file gets a new URL, an unchanged one keeps its URL and stays cached.

  python3 scripts/stamp_assets.py          rewrite stamps in place
  python3 scripts/stamp_assets.py --check  change nothing; exit 1 if any
                                            stamp is missing or stale

This is not a build step. The stamped files are committed and deployed as
they are; CI runs --check so a stale stamp can never reach users. CSS is
stamped before HTML because the CSS's own hash depends on the font stamps
inside it.
"""
import hashlib
import os
import pathlib
import re
import sys

# SITE_ROOT lets the self-test run this against a scratch copy of the site.
ROOT = pathlib.Path(os.environ.get("SITE_ROOT") or
                    pathlib.Path(__file__).resolve().parent.parent / "public")
# /assets/<path> with an optional ?v=..., ending at a quote, paren, space or comma.
REF = re.compile(r"(/assets/[A-Za-z0-9_./-]+?)(\?v=[0-9a-f]*)?(?=[\"')\s,])")


def file_version(asset_path):
    data = (ROOT / asset_path.lstrip("/")).read_bytes()
    return hashlib.sha256(data).hexdigest()[:12]


def restamp(text, problems, source):
    def replace(match):
        path, old = match.group(1), match.group(2)
        target = ROOT / path.lstrip("/")
        if not target.is_file():
            problems.append(f"{source}: references missing file {path}")
            return match.group(0)
        new = "?v=" + file_version(path)
        if old != new:
            problems.append(f"{source}: {path}{old or ''} should be {path}{new}")
        return path + new
    return REF.sub(replace, text)


def main(check_only):
    problems = []
    files = sorted((ROOT / "assets" / "css").glob("*.css")) + sorted(ROOT.glob("*.html"))
    for f in files:
        source = str(f.relative_to(ROOT))
        text = f.read_text(encoding="utf-8")
        updated = restamp(text, problems, source)
        if not check_only and updated != text:
            f.write_text(updated, encoding="utf-8")
    if check_only:
        if problems:
            print("Asset version stamps are missing or stale "
                  "(run: python3 scripts/stamp_assets.py):")
            print("\n".join("  " + p for p in problems))
            return 1
        print(f"Asset stamps OK in {len(files)} files.")
        return 0
    missing = [p for p in problems if "missing file" in p]
    print(f"Restamped {len(problems) - len(missing)} reference(s) in {len(files)} files.")
    if missing:
        print("\n".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv[1:]))
