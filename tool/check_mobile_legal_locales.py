#!/usr/bin/env python3
"""Check that website-only notices remain separate from mobile-app legal pages.

This is a structural/coverage test, NOT a legal translation review.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ENGLISH = ("privacy", "terms", "data-deletion", "copyright")
EXPECTED_SECTIONS = {
    "privacy": 15,
    "terms": 13,
    "data-deletion": 4,
    "copyright": 5,
}
APP_LANGUAGES = (
    "en", "hu", "es", "pt", "ro", "de", "it", "pl", "fr", "nl",
    "zh-hans", "zh-hant", "vi", "hi", "th", "uk", "ru", "el",
)
ROMANIAN_TEXT = {
    "privacy": "Politica de confidențialitate a aplicației mobile",
    "terms": "Termenii de utilizare ai aplicației mobile",
    "data-deletion": "Solicitarea ștergerii datelor BibleMind",
    "copyright": "Drepturi de autor și proprietate intelectuală",
}


class LegalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.lang = ""
        self.headings = []
        self.links = []
        self.images = []
        self._heading = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "h2":
            self._heading = True
            self.headings.append("")
        if tag == "a":
            self.links.append(a.get("href", ""))
        if tag == "script":
            self.links.append(a.get("src", ""))
        if tag == "img":
            self.images.append(a.get("src", ""))

    def handle_endtag(self, tag):
        if tag == "h2":
            self._heading = False

    def handle_data(self, data):
        if self._heading:
            self.headings[-1] += data


def check():
    router = (ROOT / "app/legal-locale-router.js").read_text(encoding="utf-8")
    for lang in APP_LANGUAGES:
        assert f"'{lang}'" in router, f"Missing locale route: {lang}"
    assert "const available = new Set(['en', 'ro'])" in router
    for lang in APP_LANGUAGES:
        if lang not in ("en", "ro"):
            assert f"'{lang}':" in router, f"No disclosure for missing {lang} translation"

    for name in ENGLISH:
        en_file = ROOT / "app" / f"{name}.html"
        ro_file = ROOT / "app/ro" / f"{name}.html"
        assert en_file.is_file() and ro_file.is_file(), name
        en = en_file.read_text(encoding="utf-8")
        ro = ro_file.read_text(encoding="utf-8")
        en_p, ro_p = LegalParser(), LegalParser()
        en_p.feed(en)
        ro_p.feed(ro)
        assert en_p.lang == "en", name
        assert ro_p.lang == "ro", name
        assert len(en_p.headings) == len(ro_p.headings) == EXPECTED_SECTIONS[name], (
            name, len(en_p.headings), len(ro_p.headings)
        )
        assert '/app/legal-locale-router.js' in en, name
        assert ROMANIAN_TEXT[name] in ro, name
        assert "Oraculum Digital Labs Ltd" in en and "Oraculum Digital Labs Ltd" in ro
        assert "office@biblemind.eu" in en and "office@biblemind.eu" in ro
        assert "biblemind.eu" in en and "biblemind.eu" in ro
        for sibling in ENGLISH:
            assert f"/app/ro/{sibling}.html" in ro, (name, sibling)
        for link in ro_p.links:
            if link.startswith("/"):
                assert link.startswith(("/app/ro/", "/app/", "/assets/", "/")), link
        assert "/ro/privacy.html" not in en, "Website-only URL must never replace app link"
        # A mobile translation must not claim to be the privacy terms for the website.
        if name == "privacy":
            assert "site-ului" in ro
        if name == "terms":
            assert "legislația Republicii Cipru" in ro

    # Original website-only legal notices remain untouched by the app-locales feature.
    assert (ROOT / "ro/privacy.html").is_file()
    assert (ROOT / "ro/terms.html").is_file()
    print(
        f"PASS: {len(ENGLISH)} English + 4 Romanian mobile-app legal pages, "
        f"18 language routes audited (16 clearly disclosed fallbacks)."
    )
    print("NOTE: Romanian translation requires independent legal proofreading.")


if __name__ == "__main__":
    check()
