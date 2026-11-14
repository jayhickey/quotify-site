#!/usr/bin/env python3
"""Static checks for /guides pages. Run from the repo root: python3 -I _checks/guides.py

Jekyll skips underscore directories, so this file is not published.
"""
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, parse_qs

ROOT = pathlib.Path(__file__).resolve().parent.parent
APP_STORE = "https://apps.apple.com/app/apple-store/id1626937020?pt=958359&ct={}&mt=8"
# Each guide's single primary CTA and the tag it must carry.
CTA = {
    "guides/index.html": APP_STORE.format("guide-index"),
    "guides/best-apps-to-save-quotes/index.html": APP_STORE.format("guide-best-apps"),
    "guides/best-quote-apps-iphone/index.html": APP_STORE.format("guide-best-iphone"),
    "guides/readwise-alternatives/index.html": APP_STORE.format("guide-readwise"),
    "guides/save-quotes-from-kindle/index.html": APP_STORE.format("guide-kindle"),
    "guides/save-quotes-from-books/index.html": APP_STORE.format("guide-books"),
    "guides/quote-widget-iphone/index.html": APP_STORE.format("guide-widget"),
    "guides/save-quotes-from-instagram/index.html": APP_STORE.format("guide-instagram"),
    "guides/save-quotes-from-x/index.html": APP_STORE.format("guide-x"),
    "guides/mcp/claude/index.html": "https://mcp.quotify.to/?ref=guide-claude#apps",
    "guides/mcp/chatgpt/index.html": "https://mcp.quotify.to/?ref=guide-chatgpt#apps",
    "guides/mcp/cursor/index.html": "https://mcp.quotify.to/?ref=guide-cursor#apps",
}
CAMPAIGN = re.compile(r"^[a-z0-9-]{1,40}$")
BANNED = re.compile(r"Premium|\$\d|Quotify 2\.0|waitlist|Unsplash", re.I)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.links, self.ctas, self.ids, self.navcurrent = [], [], [], set(), []
        self._in_bar = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "header" and "bar" in a.get("class", ""):
            self._in_bar = 1
        for key in ("href", "src"):
            if key in a:
                self.links.append(a[key])
        if tag == "a" and "guideCTA" in a.get("class", ""):
            self.ctas.append(a.get("href"))
        if tag == "a" and self._in_bar and a.get("aria-current") == "page":
            self.navcurrent.append(a.get("href"))

    def handle_endtag(self, tag):
        if tag == "header":
            self._in_bar = 0


def main():
    errors = []
    sitemap = (ROOT / "sitemap.xml").read_text()
    canonicals = {}
    pages = sorted(p for p in (ROOT / "guides").rglob("index.html"))
    for path in pages:
        rel = str(path.relative_to(ROOT))
        src = path.read_text()
        page = Page()
        page.feed(src)
        err = lambda msg: errors.append(f"{rel}: {msg}")
        count = lambda pred: sum(1 for t, a in page.tags if pred(t, a))
        if count(lambda t, a: t == "h1") != 1:
            err("needs exactly one <h1>")
        if count(lambda t, a: t == "title") != 1:
            err("needs exactly one <title>")
        if count(lambda t, a: t == "meta" and a.get("name") == "description") != 1:
            err("needs exactly one meta description")
        canon = [a.get("href") for t, a in page.tags if t == "link" and a.get("rel") == "canonical"]
        if len(canon) != 1:
            err("needs exactly one canonical")
        else:
            expected = "https://quotify.to/" + rel[: -len("index.html")]
            if canon[0] != expected:
                err(f"canonical {canon[0]} != {expected}")
            if canon[0] in canonicals:
                err(f"duplicate canonical with {canonicals[canon[0]]}")
            canonicals[canon[0]] = rel
            if f"<loc>{canon[0]}</loc>" not in sitemap:
                err("canonical missing from sitemap.xml")
        if "content" not in page.ids or not any(l == "#content" for l in page.links):
            err("skip link or #content target missing")
        if page.navcurrent != ["/guides/"]:
            err(f"Guides nav link must be aria-current, got {page.navcurrent}")
        if "https://finalbits.io" not in page.links:
            err("footer must link Final Bits")
        if page.ctas != [CTA.get(rel)]:
            err(f"primary CTA {page.ctas} != [{CTA.get(rel)}]")
        for link in page.links:
            u = urlsplit(link)
            if u.netloc == "apps.apple.com" and "1626937020" in u.path:
                q = parse_qs(u.query)
                ct = q.get("ct", [""])[0]
                if not CAMPAIGN.match(ct) or q.get("pt") != ["958359"]:
                    err(f"untagged or malformed App Store link {link}")
            if u.netloc == "mcp.quotify.to" and u.path in ("", "/"):
                ref = parse_qs(u.query).get("ref", [""])[0]
                if not ref.startswith("guide-"):
                    err(f"untagged Connect link {link}")
            if not u.scheme and not u.netloc and u.path:
                target = ROOT / u.path.lstrip("/")
                if u.path.endswith("/"):
                    target = target / "index.html"
                elif not target.exists() and target.with_suffix(".html").exists():
                    target = target.with_suffix(".html")
                if not target.exists():
                    err(f"broken local link {link}")
        text = re.sub(r"<[^>]+>", " ", src)
        if m := BANNED.search(text):
            err(f"banned copy: {m.group(0)!r}")
    for rel in CTA:
        if not (ROOT / rel).exists():
            errors.append(f"{rel}: expected page missing")
    print("\n".join(errors) or f"OK: {len(pages)} guide pages")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
