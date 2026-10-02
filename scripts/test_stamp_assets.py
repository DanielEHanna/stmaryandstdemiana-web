#!/usr/bin/env python3
"""Prove the cache-busting stamp moves when, and only when, a file changes.

A version that does not move when its file changes is worse than none: it
looks like cache-busting and isn't. This test works on a scratch copy of
public/, changes one byte in each kind of asset, and asserts that:
  1. --check fails on the changed site (a stale stamp cannot reach CI green),
  2. restamping gives every reference to the changed file a new version,
  3. references to files that did not change keep their version,
  4. a CSS change also moves the CSS version in every page, and a font
     change moves the font's stamp inside the CSS and therefore the CSS's
     own version too.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
STAMP = REPO / "scripts" / "stamp_assets.py"


def run(root, *args):
    env = dict(os.environ, SITE_ROOT=str(root))
    return subprocess.run([sys.executable, str(STAMP), *args], env=env,
                          capture_output=True, text=True)


def versions(root):
    """Map each referenced asset path to the set of versions it is stamped with."""
    found = {}
    for f in list(root.glob("*.html")) + list((root / "assets" / "css").glob("*.css")):
        for path, v in re.findall(r"(/assets/[\w./-]+?)\?v=([0-9a-f]+)", f.read_text()):
            found.setdefault(path, set()).add(v)
    return found


def one_case(asset, also_moves):
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp) / "public"
        shutil.copytree(REPO / "public", root)
        # Stamp the scratch copy first, so the test exercises the stamper
        # itself rather than whatever happens to be committed.
        if run(root).returncode != 0 or run(root, "--check").returncode != 0:
            return [f"{asset}: could not establish a stamped baseline"]
        before = versions(root)
        with open(root / asset.lstrip("/"), "ab") as fh:
            fh.write(b"\n")  # one byte
        if run(root, "--check").returncode == 0:
            failures.append(f"{asset}: --check passed after the file changed")
        if run(root).returncode != 0:
            failures.append(f"{asset}: restamp failed")
        after = versions(root)
        if run(root, "--check").returncode != 0:
            failures.append(f"{asset}: --check still fails after restamping")
        moved = {p for p in before if before[p] != after.get(p)}
        expected = {asset, *also_moves}
        for p in expected - moved:
            failures.append(f"{asset}: version of {p} did not change")
        for p in moved - expected:
            failures.append(f"{asset}: version of {p} changed although it did not")
        for p in expected & moved:
            if len(after[p]) != 1:
                failures.append(f"{asset}: {p} is stamped inconsistently: {after[p]}")
        print(f"{'FAIL' if failures else 'ok  '} change {asset}: versions moved for "
              + ", ".join(f"{p} {sorted(before[p])[0]}->{sorted(after[p])[0]}" for p in sorted(moved)))
    return failures


def main():
    css = "/assets/css/site.css"
    cases = [
        (css, []),
        ("/assets/js/site.js", []),
        ("/assets/img/logo-112.webp", []),
        # A font is referenced from the CSS, so the CSS's bytes change and so must its version.
        ("/assets/fonts/newsreader-latin.woff2", [css]),
    ]
    failures = [f for asset, extra in cases for f in one_case(asset, extra)]
    if failures:
        print("\n".join(failures))
        return 1
    print("Stamps move exactly when files change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
