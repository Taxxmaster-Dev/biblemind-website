#!/usr/bin/env python3
"""Check that website-only notices remain separate from mobile-app legal pages.

This is a structural/coverage test, NOT a legal translation review.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
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
LOCALIZED_TEXT = {
    "ro": {
    "privacy": "Politica de confidențialitate a aplicației mobile",
    "terms": "Termenii de utilizare ai aplicației mobile",
    "data-deletion": "Solicitarea ștergerii datelor BibleMind",
    "copyright": "Drepturi de autor și proprietate intelectuală",
    },
    "es": {
        "privacy": "Política de privacidad de la aplicación móvil",
        "terms": "Condiciones de uso de la aplicación móvil",
        "data-deletion": "Solicitud de eliminación de datos de BibleMind",
        "copyright": "Derechos de autor y propiedad intelectual",
    },
    "hu": {
        "privacy": "A mobilalkalmazás adatvédelmi szabályzata",
        "terms": "A mobilalkalmazás felhasználási feltételei",
        "data-deletion": "BibleMind-adatok törlésének kérelmezése",
        "copyright": "Szerzői jogok és szellemi tulajdon",
    },
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
    status = json.loads((ROOT / "app/legal-locale-coverage.json").read_text(encoding="utf-8"))
    assert status["app_supported_languages"] == 18
    assert set(status["translation_status"]) == set(APP_LANGUAGES)
    for lang in APP_LANGUAGES:
        coverage = status["translation_status"][lang]["coverage"]
        if lang == "en":
            assert coverage == "english_source"
        else:
            assert coverage == "draft_full_translation"
    for lang in APP_LANGUAGES:
        assert f"'{lang}'" in router, f"Missing locale route: {lang}"
    assert "const available = new Set([" in router
    for lang in APP_LANGUAGES:
        assert lang == "en" or f"'{lang}'" in router
      for name in ENGLISH:
        en_file = ROOT / "app" / f"{name}.html"
        assert en_file.is_file(), name
        en = en_file.read_text(encoding="utf-8")
        en_p = LegalParser()
        en_p.feed(en)
        assert en_p.lang == "en", name
        assert len(en_p.headings) == EXPECTED_SECTIONS[name], name
        assert '/app/legal-locale-router.js' in en, name
        assert "Oraculum Digital Labs Ltd" in en
        assert "office@biblemind.eu" in en

        for locale in APP_LANGUAGES:
            if locale == "en":
                continue
            titles = LOCALIZED_TEXT.get(locale, {})
            translated_file = ROOT / "app" / locale / f"{name}.html"
            assert translated_file.is_file(), (locale, name)
            translated = translated_file.read_text(encoding="utf-8")
            parsed = LegalParser()
            parsed.feed(translated)
            assert parsed.lang == ("zh" if locale.startswith("zh-") else locale), (locale, name)
            if locale.startswith("zh-"):
                assert f'data-script="{ "Hans" if locale == "zh-hans" else "Hant" }"' in translated
            assert len(parsed.headings) == EXPECTED_SECTIONS[name], (
                locale, name, len(parsed.headings)
            )
            if name in titles:
                assert titles[name] in translated, (locale, name)
            assert "Oraculum Digital Labs Ltd" in translated
            assert "office@biblemind.eu" in translated
            for sibling in ENGLISH:
                assert f"/app/{locale}/{sibling}.html" in translated, (
                    locale, name, sibling
                )

        if name == "privacy":
            assert "site-ului" in (ROOT / "app/ro/privacy.html").read_text()
        if name == "terms":
            assert "legislația Republicii Cipru" in (ROOT / "app/ro/terms.html").read_text()

    # Original website-only legal notices remain untouched by the app-locales feature.
    assert (ROOT / "ro/privacy.html").is_file()
    assert (ROOT / "ro/terms.html").is_file()
    print(
        f"PASS: 4 English + {(len(APP_LANGUAGES)-1)*4} localized "
        f"mobile-app legal pages, 18 locale routes audited."
    )
    print("NOTE: all non-English translations require independent legal proofreading.")


if __name__ == "__main__":
    check()
