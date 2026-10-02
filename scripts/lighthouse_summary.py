#!/usr/bin/env python3
"""Summarise Lighthouse JSON reports and enforce the accessibility floor.

  python3 scripts/lighthouse_summary.py report1.json [report2.json ...]

Prints each page's category scores (and appends them to the GitHub job
summary when $GITHUB_STEP_SUMMARY is set). Fails if accessibility is below
ACCESSIBILITY_MIN on any page. Performance is reported, not enforced:
shared CI runners vary too much from run to run for a hard floor to mean
anything, so a drop is a prompt to look, not a red build.
"""
import json
import os
import sys

ACCESSIBILITY_MIN = 95
PERFORMANCE_WARN = 90


def main(paths):
    rows, failures = [], []
    for p in paths:
        report = json.load(open(p))
        scores = {k: round(v["score"] * 100) for k, v in report["categories"].items()
                  if v.get("score") is not None}
        form = report["configSettings"]["formFactor"]
        url = report["finalDisplayedUrl"]
        rows.append((url, form, scores))
        if scores.get("accessibility", 0) < ACCESSIBILITY_MIN:
            failed = [a["id"] for a in report["audits"].values()
                      if a.get("score") == 0 and a["id"] in
                      {r["id"] for r in report["categories"]["accessibility"]["auditRefs"]}]
            failures.append(f"{url} ({form}): accessibility {scores.get('accessibility')} "
                            f"< {ACCESSIBILITY_MIN}; failing audits: {failed}")
        if scores.get("performance", 100) < PERFORMANCE_WARN:
            print(f"::warning::{url} ({form}): performance {scores['performance']} < {PERFORMANCE_WARN}")
    cats = ["performance", "accessibility", "best-practices", "seo"]
    lines = ["| Page | Device | " + " | ".join(cats) + " |",
             "|---|---|" + "---|" * len(cats)]
    for url, form, scores in rows:
        lines.append(f"| {url} | {form} | " + " | ".join(str(scores.get(c, "-")) for c in cats) + " |")
    table = "\n".join(lines)
    print(table)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as fh:
            fh.write("### Lighthouse\n\n" + table +
                     "\n\nSEO is low by design while every page is `noindex`.\n")
    if failures:
        print("\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
