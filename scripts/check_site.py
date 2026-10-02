#!/usr/bin/env python3
"""Static checks for the site. No dependencies beyond Python 3.

Each check exists because the same class of bug shipped before:
  - duplicate function declarations in a JS file (a second `function
    fullName` silently replaced the first and printed "undefined")
  - an element id or class the script reaches for that no page contains
  - a CSS class used in HTML with no rule anywhere
  - an internal link or #anchor that points at nothing
  - asset ?v= stamps that don't match the file (cache-busting that isn't)
  - header / footer / action bar drifting apart between pages, which are
    copied into every file because there is no build step
  - more than one h1, a missing alt, duplicate ids

  python3 scripts/check_site.py            development checks
  python3 scripts/check_site.py --launch   also fail on any [PLACEHOLDER]
                                           or noindex (run before go-live)
"""
import html.parser
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
PUBLIC = REPO / "public"


class Page(html.parser.HTMLParser):
    """Collects what the checks need from one HTML file."""

    SHARED = ("header", "footer")  # plus nav.sm-actionbar, captured below
    # Void elements never get an end tag, so they must not change the depth.
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
            "meta", "source", "track", "wbr"}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.ids, self.classes, self.refs, self.imgs = [], set(), [], []
        self.h1 = 0
        self.placeholders = 0
        self.noindex = False
        self._capture = None  # (name, depth) while inside a shared block
        self._depth = 0
        self.shared = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._depth += 1
        if "id" in a:
            self.ids.append(a["id"])
        cls = (a.get("class") or "").split()
        self.classes.update(cls)
        if "sm-placeholder" in cls:
            self.placeholders += 1
        for key in ("href", "src"):
            if a.get(key):
                self.refs.append(a[key])
        if a.get("srcset"):
            self.refs += [part.split()[0] for part in a["srcset"].split(",")]
        if tag == "img":
            self.imgs.append(a)
        if tag == "h1":
            self.h1 += 1
        if tag == "meta" and a.get("name") == "robots" and "noindex" in (a.get("content") or ""):
            self.noindex = True
        name = tag if tag in self.SHARED else ("actionbar" if "sm-actionbar" in cls else None)
        if name and self._capture is None:
            self._capture = (name, self._depth)
            self.shared[name] = []
        if self._capture:
            # aria-current legitimately differs per page; ignore it.
            kept = [(k, v) for k, v in attrs if k != "aria-current"]
            self.shared[self._capture[0]].append(("start", tag, tuple(kept)))
        if tag in self.VOID:
            self._depth -= 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if self._capture:
            self.shared[self._capture[0]].append(("end", tag))
            if self._depth == self._capture[1]:
                self._capture = None
        self._depth -= 1

    def handle_data(self, data):
        if self._capture and data.strip():
            self.shared[self._capture[0]].append(("text", data.strip()))


def strip_js_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(^|[^:])//.*", r"\1", src)


def css_class_rules(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"url\([^)]*\)", "", css)
    # Class names in selectors only (property values cannot contain ".name").
    selectors = re.findall(r"([^{}]+)\{", css)
    return {c for sel in selectors for c in re.findall(r"\.([A-Za-z_][\w-]*)", sel)}


def resolve(ref):
    """Map an internal URL to the file Firebase Hosting would serve (cleanUrls)."""
    path = ref.split("#")[0].split("?")[0]
    if path in ("", "/"):
        return PUBLIC / "index.html"
    target = PUBLIC / path.lstrip("/")
    for cand in (target, target.with_name(target.name + ".html"), target / "index.html"):
        if cand.is_file():
            return cand
    return None


def main(launch):
    errors, notes = [], []
    pages = {p.name: p for p in sorted(PUBLIC.glob("*.html"))}
    parsed = {}
    for name, path in pages.items():
        pg = Page()
        pg.feed(path.read_text(encoding="utf-8"))
        parsed[name] = pg

    all_ids, all_classes = set(), set()
    for name, pg in parsed.items():
        all_ids.update(pg.ids)
        all_classes |= pg.classes
        dup = sorted({i for i in pg.ids if pg.ids.count(i) > 1})
        if dup:
            errors.append(f"{name}: duplicate id(s) {dup}")
        if pg.h1 != 1:
            errors.append(f"{name}: has {pg.h1} <h1> elements, expected exactly 1")
        for img in pg.imgs:
            if "alt" not in img:
                errors.append(f"{name}: <img src={img.get('src')}> has no alt attribute")
        for ref in pg.refs:
            if not ref.startswith("/") or ref.startswith("//"):
                continue  # external, mailto:, tel: and same-page links are not checked here
            target = resolve(ref)
            if target is None:
                errors.append(f"{name}: link to {ref} points at a page or file that does not exist")
                continue
            if "#" in ref and target.suffix == ".html":
                frag = ref.split("#", 1)[1]
                if frag and frag not in parsed[target.name].ids:
                    errors.append(f"{name}: link to {ref}: no id=\"{frag}\" in {target.name}")
        if launch and pg.placeholders:
            errors.append(f"{name}: {pg.placeholders} [PLACEHOLDER](s) still on the page")
        if launch and pg.noindex:
            errors.append(f"{name}: still marked noindex")
        if pg.placeholders:
            notes.append(f"{name}: {pg.placeholders} placeholder(s)")

    # Shared blocks must be identical on every page.
    reference = parsed.get("index.html")
    for name, pg in parsed.items():
        for block in ("header", "footer", "actionbar"):
            if block not in pg.shared:
                errors.append(f"{name}: has no {block}")
            elif reference and pg.shared[block] != reference.shared.get(block):
                errors.append(f"{name}: {block} differs from index.html's (copy the shared markup to every page)")

    # CSS: every class used in HTML has a rule.
    css_rules = set()
    for css in (PUBLIC / "assets" / "css").glob("*.css"):
        css_rules |= css_class_rules(css.read_text(encoding="utf-8"))
    missing = sorted(all_classes - css_rules)
    if missing:
        errors.append(f"class(es) used in HTML with no CSS rule: {missing}")

    # JS: no duplicate function declarations; every id/class it reaches for exists.
    for js in sorted((PUBLIC / "assets" / "js").glob("*.js")):
        src = strip_js_comments(js.read_text(encoding="utf-8"))
        rel = js.relative_to(REPO)
        names = re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", src)
        names += re.findall(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)", src)
        dups = sorted({n for n in names if names.count(n) > 1})
        if dups:
            errors.append(f"{rel}: function(s) declared more than once: {dups}")
        for wanted in re.findall(r"getElementById\(\s*[\"']([^\"']+)[\"']\s*\)", src):
            if wanted not in all_ids:
                errors.append(f"{rel}: getElementById('{wanted}') but no page has id=\"{wanted}\"")
        for sel in re.findall(r"querySelector(?:All)?\(\s*[\"']([^\"']+)[\"']\s*\)", src):
            for wanted in re.findall(r"#([\w-]+)", sel):
                if wanted not in all_ids:
                    errors.append(f"{rel}: selector '{sel}' wants id \"{wanted}\" which no page has")
            for wanted in re.findall(r"\.([\w-]+)", sel):
                if wanted not in all_classes:
                    errors.append(f"{rel}: selector '{sel}' wants class \"{wanted}\" which no page uses")

    # Cache-busting stamps.
    stamp = subprocess.run([sys.executable, str(REPO / "scripts" / "stamp_assets.py"), "--check"],
                           capture_output=True, text=True)
    if stamp.returncode != 0:
        errors.append(stamp.stdout.strip())

    print(f"Checked {len(parsed)} pages, {len(all_classes)} classes, "
          f"{len(list((PUBLIC / 'assets' / 'js').glob('*.js')))} script(s).")
    if notes and not launch:
        print(f"Placeholders remaining (allowed before launch): {sum(p.placeholders for p in parsed.values())}")
    if errors:
        print(f"\n{len(errors)} problem(s):")
        print("\n".join("  - " + e for e in errors))
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main("--launch" in sys.argv[1:]))
