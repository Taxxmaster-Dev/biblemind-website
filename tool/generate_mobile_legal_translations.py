#!/usr/bin/env python3
"""Generate full DRAFT mobile-app legal translations from the reviewed English HTML.

The English source is canonical. Do not publish machine translations without
legal/linguistic verification. Never translate website-only legal documents.
"""
from __future__ import annotations

import argparse
import urllib.parse
import urllib.request
import json
import os
from pathlib import Path
import re
import sys
import time

from bs4 import BeautifulSoup, NavigableString, Comment

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("privacy", "terms", "data-deletion", "copyright")
TARGETS = {
    "es": "es", "pt": "pt", "de": "de", "it": "it", "pl": "pl",
    "fr": "fr", "nl": "nl", "zh-hans": "zh-CN", "zh-hant": "zh-TW",
    "vi": "vi", "hi": "hi", "th": "th", "uk": "uk", "ru": "ru", "el": "el",
}
UNTRANSLATABLE = {"BibleMind", "Oraculum Digital Labs Ltd", "office@biblemind.eu"}


def translate_text(translator, text, *, label):
    if not text.strip() or text.strip() in UNTRANSLATABLE:
        return text
    # Never silently use the original English after a failed translation.
    last_error = None
    for attempt in range(8):
        try:
            query = urllib.parse.urlencode({
                "client": "gtx", "sl": "en", "tl": translator,
                "dt": "t", "q": text,
            })
            req = urllib.request.Request(
                "https://translate.googleapis.com/translate_a/single?" + query,
                headers={"User-Agent": "Mozilla/5.0 (compatible; BibleMindLocalizationAudit/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=35) as response:
                data = json.loads(response.read().decode("utf-8"))
            value = "".join(
                str(segment[0] or "") for segment in data[0]
                if isinstance(segment, list) and segment
            )
            if value and value.strip():
                time.sleep(1.15)
                return value.strip()
            raise ValueError("Translation returned an empty string")
        except Exception as exc:
            last_error = exc
            time.sleep(min(90, 3 * 2 ** attempt + 1))
    raise RuntimeError(f"Translation failed for {label}: {last_error}")


def translate_batch(translator, values, *, label):
    # Group text nodes into bounded requests, preserving each original HTML
    # node and its markup. Numeric markers are validated after translation.
    output = []
    cursor = 0
    while cursor < len(values):
        group = []
        length = 0
        while cursor + len(group) < len(values):
            value = values[cursor + len(group)]
            extra = len(value) + 28
            if group and length + extra > 1350:
                break
            group.append(value)
            length += extra
        markers = [f"[[BMT{index:04d}]]" for index in range(len(group))]
        combined = "\n".join(f"{mark} {value}" for mark, value in zip(markers, group))
        try:
            translated = translate_text(translator, combined, label=label)
            parts = re.split(r"\[\[\s*BMT(\d{4})\s*\]\]", translated)
            found = {}
            for i in range(1, len(parts) - 1, 2):
                found[int(parts[i])] = parts[i + 1].strip()
            if len(found) != len(group) or set(found) != set(range(len(group))):
                raise ValueError("Machine translation modified segment markers")
            output.extend(found[i] for i in range(len(group)))
        except Exception:
            # If the provider changes markers, use slower but safer
            # individual requests rather than mismatching legal paragraphs.
            output.extend(
                translate_text(translator, item, label=f"{label}/{i}")
                for i, item in enumerate(group)
            )
        cursor += len(group)
        time.sleep(0.2)
    return output


def build(locale):
    translator = TARGETS[locale]
    target_dir = ROOT / "app" / locale
    target_dir.mkdir(parents=True, exist_ok=True)

    for name in NAMES:
        source = (ROOT / "app" / f"{name}.html").read_text(encoding="utf-8")
        soup = BeautifulSoup(source, "html.parser")
        soup.html["lang"] = "zh" if locale.startswith("zh-") else locale
        if locale.startswith("zh-"):
            soup.html["data-script"] = "Hans" if locale == "zh-hans" else "Hant"

        nodes = [
            node for node in soup.find_all(string=True)
            if isinstance(node, NavigableString)
            and not isinstance(node, Comment)
            and node.parent.name not in {"script", "style"}
            and node.strip()
        ]
        translatable = [node for node in nodes if node.strip() not in UNTRANSLATABLE]
        values = [str(node).strip() for node in translatable]
        translated = translate_batch(translator, values, label=f"{locale}/{name}")
        if len(values) != len(translated):
            raise AssertionError("Lost HTML text nodes during translation")
        for node, value in zip(translatable, translated):
            if not value.strip():
                raise AssertionError("Empty translated legal paragraph")
            leading = re.match(r"^\s*", str(node)).group(0)
            trailing = re.search(r"\s*$", str(node)).group(0)
            node.replace_with(NavigableString(leading + value + trailing))

        for a in soup.select("a[href]"):
            href = a.get("href", "")
            if href in {f"/app/{n}.html" for n in NAMES}:
                a["href"] = f"/app/{locale}/" + href.split("/")[-1]
        for meta in soup.select('meta[name="description"]'):
            meta["content"] = translate_text(
                translator, meta.get("content", ""), label=f"{locale}/{name}/description"
            )
        meta = soup.new_tag("meta")
        meta["name"] = "translation-status"
        meta["content"] = "draft-machine-translation"
        soup.head.append(meta)
        canonical = soup.new_tag("link", rel="canonical")
        canonical["href"] = f"https://biblemind.eu/app/{locale}/{name}.html"
        soup.head.append(canonical)
        # Ensure legally significant organisation identifiers survive even
        # when the translation provider rewrites the copyright footer.
        footer_copyright = soup.select_one("footer .footer-meta span")
        if footer_copyright is not None:
            footer_copyright.string = "© 2026 Oraculum Digital Labs Ltd"

        # Preserve a direct English-language reference for legal comparison.
        english = soup.new_tag("a", href=f"/app/{name}.html?lang=en")
        english["lang"] = "en"
        english.string = "English"
        bar = soup.new_tag("p")
        bar["class"] = "meta"
        bar.append(english)
        heading = soup.select_one("article.paper h1")
        if heading:
            heading.insert_after(bar)

        result = "<!doctype html>\n" + str(soup)
        check = BeautifulSoup(result, "html.parser")
        original = BeautifulSoup(source, "html.parser")
        for tag in ("h1", "h2", "li", "p"):
            if len(check.select(f"article.paper {tag}")) < len(original.select(f"article.paper {tag}")):
                raise AssertionError(f"Missing {tag} after translating {locale}/{name}")
        for required in ("BibleMind", "Oraculum Digital Labs Ltd", "office@biblemind.eu"):
            if required not in result:
                raise AssertionError(f"Lost required identifier {required} in {locale}/{name}")
        (target_dir / f"{name}.html").write_text(result, encoding="utf-8")
        print(f"OK: {locale}/{name}.html ({len(result)} chars)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", required=True, choices=TARGETS)
    args = parser.parse_args()
    build(args.language)
