#!/usr/bin/env python3
"""Prove a deploy reached users, by fetching it from the public URL.

"I deployed it" is not "it's live". After every deploy (preview or live)
this fetches, from BASE_URL:
  - every page, and requires it byte-identical to public/ in this commit
    and served with Cache-Control: no-cache;
  - every /assets/ URL the pages and CSS reference (with its ?v= stamp),
    and requires it byte-identical to the file in this commit and served
    with Cache-Control: public, max-age=31536000, immutable;
  - a missing URL, and requires a 404 with our 404.html.
The CDN can briefly serve the previous release, so the whole check is
retried for up to ~2 minutes before failing.

  python3 scripts/verify_deploy.py https://stmaryandstdemiana-church.web.app
"""
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

PUBLIC = pathlib.Path(__file__).resolve().parent.parent / "public"
HTML_CACHE = "no-cache"
ASSET_CACHE = "public, max-age=31536000, immutable"
ATTEMPTS, PAUSE = 12, 10


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "stmaryandstdemiana-deploy-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def page_paths():
    for f in sorted(PUBLIC.glob("*.html")):
        if f.name == "404.html":
            continue
        yield ("/" if f.name == "index.html" else "/" + f.stem), f


def asset_refs():
    refs = set()
    for f in list(PUBLIC.glob("*.html")) + list((PUBLIC / "assets" / "css").glob("*.css")):
        refs |= set(re.findall(r"/assets/[\w./-]+\?v=[0-9a-f]+", f.read_text()))
    return sorted(refs)


def check(base):
    problems = []
    for path, local in page_paths():
        status, headers, body = fetch(base + path)
        if status != 200:
            problems.append(f"{path}: HTTP {status}")
        elif body != local.read_bytes():
            problems.append(f"{path}: served page differs from {local.name} in this commit")
        if headers.get("Cache-Control") != HTML_CACHE:
            problems.append(f"{path}: Cache-Control is {headers.get('Cache-Control')!r}, expected {HTML_CACHE!r}")
    for ref in asset_refs():
        status, headers, body = fetch(base + ref)
        local = PUBLIC / ref.split("?")[0].lstrip("/")
        if status != 200:
            problems.append(f"{ref}: HTTP {status}")
        elif body != local.read_bytes():
            problems.append(f"{ref}: served bytes differ from the file in this commit")
        if headers.get("Cache-Control") != ASSET_CACHE:
            problems.append(f"{ref}: Cache-Control is {headers.get('Cache-Control')!r}, expected {ASSET_CACHE!r}")
    status, _, body = fetch(base + "/this-page-does-not-exist")
    if status != 404 or body != (PUBLIC / "404.html").read_bytes():
        problems.append(f"missing page: got HTTP {status}, expected 404 with our 404.html")
    return problems


def show_headers(base, path):
    status, headers, _ = fetch(base + path)
    print(f"\n$ curl -I {base}{path}\nHTTP {status}")
    for key in ("cache-control", "content-type", "etag", "last-modified",
                "x-content-type-options", "referrer-policy", "x-cache"):
        if headers.get(key):
            print(f"{key}: {headers.get(key)}")


def main(base):
    base = base.rstrip("/")
    for attempt in range(1, ATTEMPTS + 1):
        problems = check(base)
        if not problems:
            pages = len(list(page_paths()))
            print(f"{base}: all {pages} pages and {len(asset_refs())} asset URLs match this "
                  f"commit byte for byte, with the expected Cache-Control (attempt {attempt}).")
            refs = asset_refs()
            show_headers(base, "/")
            show_headers(base, next(r for r in refs if r.startswith("/assets/css/")))
            show_headers(base, next(r for r in refs if r.startswith("/assets/fonts/")))
            return 0
        print(f"attempt {attempt}/{ATTEMPTS}: {len(problems)} problem(s), first: {problems[0]}")
        if attempt < ATTEMPTS:
            time.sleep(PAUSE)
    print("Deploy NOT verified:")
    print("\n".join("  - " + p for p in problems))
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: verify_deploy.py BASE_URL")
    sys.exit(main(sys.argv[1]))
