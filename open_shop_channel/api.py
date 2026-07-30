"""One endpoint, read once, and checked for being what it claims.

The Open Shop Channel publishes its whole catalogue as a single JSON
document -- 293 packages, about 359 KB, comfortably inside the 4 MiB
`ctx.http` allows. There is no query API and none is needed: a search is
"fetch the catalogue and match names in it", which costs one request.

## Why the host is `hbb1.oscwii.org` and not `api.oscwii.org`

This is the important thing about this plugin, and it was measured.

`api.oscwii.org` answers **HTTP 200 with `text/html` and a fixed 380,975
bytes for every path**, including paths it never served -- `/v4/contents`
returns byte-for-byte what `/api/v3/contents` returns. It is a
documentation site. A plugin pointed at it would receive 200 and a page,
forever, and a status-code check would call that success.

`hbb1.oscwii.org/api/v3/contents` answers `application/json`. That is the
API, and it is the one the Open Shop Channel Downloader uses.

This is the same failure `nointro-archive` carries a parser guard for
after Myrient shut down and began answering 200 with an identical notice
for every path. So `parse_contents` below does not trust a status code:
it requires the body to parse as JSON, to *be a list*, and for entries to
carry the keys this plugin reads. A source that stops being itself fails
loudly instead of returning nothing and looking like a quiet day.
"""

import json
from dataclasses import dataclass

#: The catalogue. One GET answers everything this plugin does.
API = "https://hbb1.oscwii.org/api/v3/contents"

#: What this plugin offers. The Open Shop Channel is mostly *not* game
#: content: measured 2026-07-30, its 293 packages are 135 utilities, 82
#: games, 52 emulators, 15 demos and 9 media. A ROM library wants the 82.
#:
#: Emulators are the tempting one to include and the clearest to exclude:
#: an emulator is a program that runs ROMs, not a ROM, and filing Snes9x
#: GX as a Wii game would be filing a tool as content. Utilities and
#: media are the same argument with less temptation. Demos here are
#: demoscene productions rather than playable games.
GAME_CATEGORY = "games"


class SourceChanged(Exception):
    """The endpoint answered something that is not this API."""


@dataclass(frozen=True)
class Package:
    """One Open Shop Channel package, as this plugin reads it."""

    slug: str
    name: str
    category: str
    author: str
    summary: str
    zip_url: str
    zip_bytes: int | None
    version: str

    @property
    def is_game(self) -> bool:
        return self.category == GAME_CATEGORY


def _text(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def parse_contents(body: str) -> list[Package]:
    """Every package in the catalogue, or `SourceChanged` saying why not.

    Entries missing a slug or a zip URL are skipped rather than fatal: one
    malformed record in a community catalogue should not take the whole
    search down. A *body* that is not this API is fatal, because that is
    the difference between a bad row and a source that has been replaced
    by a landing page.
    """
    try:
        payload = json.loads(body)
    except ValueError as exc:
        raise SourceChanged(
            f"{API} did not answer JSON ({exc}). `api.oscwii.org` serves an "
            f"HTML documentation site with HTTP 200 for every path, so a "
            f"status code is not evidence this endpoint is alive."
        ) from None

    if not isinstance(payload, list):
        raise SourceChanged(
            f"{API} answered JSON that is not a list of packages but "
            f"{type(payload).__name__}; this plugin reads the v3 contents "
            f"array."
        )

    packages: list[Package] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        slug = _text(entry.get("slug"))
        urls = entry.get("url")
        zip_url = _text(urls.get("zip")) if isinstance(urls, dict) else ""
        if not slug or not zip_url:
            continue

        description = entry.get("description")
        summary = ""
        if isinstance(description, dict):
            summary = _text(description.get("short"))

        sizes = entry.get("file_size")
        zip_bytes = None
        if isinstance(sizes, dict):
            raw = sizes.get("zip_compressed")
            if isinstance(raw, int) and raw >= 0:
                zip_bytes = raw

        packages.append(
            Package(
                slug=slug,
                name=_text(entry.get("name")) or slug,
                category=_text(entry.get("category")),
                author=_text(entry.get("author")),
                summary=summary,
                zip_url=zip_url,
                zip_bytes=zip_bytes,
                version=_text(entry.get("version")),
            )
        )

    if not packages:
        raise SourceChanged(
            f"{API} answered a JSON list carrying no readable packages; "
            f"this plugin reads `slug` and `url.zip` from each entry."
        )
    return packages


def games(packages: list[Package]) -> list[Package]:
    return [p for p in packages if p.is_game]
