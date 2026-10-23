#!/usr/bin/env python3
"""Normalize approved full mobile-app legal translations, without touching website notices."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = (
    "hu", "es", "pt", "ro", "de", "it", "pl", "fr", "nl",
    "zh-hans", "zh-hant", "vi", "hi", "th", "uk", "ru", "el",
)
DOCUMENTS = ("privacy", "terms", "data-deletion", "copyright")
CATEGORIES = {
    "privacy": "Privacy",
    "terms": "Terms",
    "data-deletion": "Data deletion",
    "copyright": "Copyright & IP",
}
changed = []
for locale in LANGUAGES:
    for document in DOCUMENTS:
        path = ROOT / "app" / locale / f"{document}.html"
        if not path.is_file():
            raise SystemExit(f"Missing approved legal page: {path}")
        source = path.read_text(encoding="utf-8")
        revised = re.sub(
            r"(?is)\A(<!doctype html>)[^<]{0,100}<html\b",
            r"\1\n<html",
            source,
            count=1,
        )
        if not revised.startswith("<!doctype html>\n<html"):
            raise SystemExit(f"Malformed legal HTML start: {path}: {revised[:60]!r}")
        if "legal-doc-navigation" not in revised:
            links = " · ".join(
                '<a href="/app/{locale}/{name}.html">{label}</a>'.format(
                    locale=locale, name=name, label=label
                )
                for name, label in CATEGORIES.items()
            )
            navigation = (
                '\n<nav class="legal-doc-navigation" '
                'aria-label="BibleMind mobile legal documents">'
                + links + "</nav>\n"
            )
            if "</article>" not in revised:
                raise SystemExit(f"No legal article close tag: {path}")
            revised = revised.replace("</article>", navigation + "</article>", 1)
        for sibling in DOCUMENTS:
            if f"/app/{locale}/{sibling}.html" not in revised:
                raise SystemExit(f"Broken local legal link: {path} -> {sibling}")
        if revised != source:
            path.write_text(revised, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))

print(f"PASS: Validated {len(LANGUAGES)*len(DOCUMENTS)} mobile-app translations.")
print(f"Normalized: {len(changed)}")
for path in changed:
    print("REPAIRED:", path)
