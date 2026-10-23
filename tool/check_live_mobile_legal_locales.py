#!/usr/bin/env python3
"""Verify that all approved app-only legal translations are actually live.

This deliberately never checks or changes website-only privacy/terms notices.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from urllib.request import Request, urlopen

BASE = "https://biblemind.eu"
RENDER = "https://biblemind-website-v3.onrender.com"
LANGUAGES = (
    "en", "hu", "es", "pt", "ro", "de", "it", "pl", "fr", "nl",
    "zh-hans", "zh-hant", "vi", "hi", "th", "uk", "ru", "el",
)
DOCUMENTS = ("privacy", "terms", "data-deletion", "copyright")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.language = None
        self.heading_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.language = attrs.get("lang")
        if tag == "h2":
            self.heading_count += 1


def check(item):
    origin, language, document = item
    path = (f"/app/{document}.html" if language == "en"
            else f"/app/{language}/{document}.html")
    url = origin + path
    with urlopen(
        Request(url, headers={"User-Agent": "BibleMind-legal-launch-check/1.0"}),
        timeout=25,
    ) as response:
        status = response.status
        html = response.read(130_000).decode("utf-8")
    parsed = Page()
    parsed.feed(html)
    expected_lang = "zh" if language.startswith("zh-") else language
    expected_count = {"privacy": 15, "terms": 13,
                      "data-deletion": 4, "copyright": 5}[document]
    if (status != 200 or parsed.language != expected_lang
            or parsed.heading_count != expected_count
            or "Oraculum Digital Labs Ltd" not in html
            or "office@biblemind.eu" not in html):
        raise AssertionError(
            f"Unexpected legal notice: {url}, HTTP={status}, "
            f"lang={parsed.language}, headings={parsed.heading_count}"
        )
    return f"PASS {language}/{document} at {origin}"


def main():
    targets = [(BASE, lang, document)
               for lang in LANGUAGES for document in DOCUMENTS]
    targets += [(RENDER, lang, doc) for lang, doc in
                (("ro", "privacy"), ("hu", "terms"),
                 ("zh-hant", "terms"), ("el", "copyright"))]
    failed = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        jobs = {pool.submit(check, item): item for item in targets}
        for job in as_completed(jobs):
            try:
                print(job.result(), flush=True)
            except Exception as exc:
                print(f"FAIL {jobs[job]}: {exc}", flush=True)
                failed.append(jobs[job])
    if failed:
        raise SystemExit(f"FAIL: {len(failed)} of {len(targets)} live page checks")
    print(f"PASS: all {len(targets)} live BibleMind mobile legal URLs")


if __name__ == "__main__":
    main()
