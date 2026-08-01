# Open Shop Channel plugin for ROM Hub

> Part of **[Cartridge](https://github.com/BlizzHacker/rom-hub/blob/master/BRAND.md)** by MoveWeight — a **[ROMarr](https://github.com/BlizzHacker/romarr)** / ROM Hub plugin. Unofficial; not affiliated with RomM, Gaseous or Retrom.

Implements the RPP v1 `search` and `importer` capabilities against the
[Open Shop Channel](https://oscwii.org/) — the Wii homebrew repository the
Homebrew Browser and OSC-DL read.

| Capability | Endpoint | Does |
|---|---|---|
| `search` | `/api/v3/contents` | one request fetches the catalogue; matching happens here |
| `importer` | `/api/contents/<slug>/<slug>.zip` | names the package zip; the **Hub** fetches it |

## Install

    rom-hub plugin install open-shop-channel
    rom-hub search "newo"
    rom-hub import open-shop-channel NewoShooter

## Why this material is legitimate

**The Open Shop Channel distributes homebrew its authors submitted to it.**
It is the repository the Wii homebrew community publishes through, and
every package in it is there because its developer put it there. Nothing
in this plugin's reach is commercial Nintendo software; there are no
retail titles in the catalogue to reach.

Individual packages carry their authors' own terms. The plugin surfaces
`author` and `version` on every result so the attribution travels with
the entry rather than living only here.

`oscwii.org/robots.txt` does not disallow the API, and this plugin reads
one documented endpoint rather than crawling anything.

## The host is `hbb1.oscwii.org`, not `api.oscwii.org`

This is the most important thing about this plugin, and it was measured
on 2026-07-30.

**`api.oscwii.org` answers HTTP 200 with `text/html` and a fixed 380,975
bytes for every path** — including paths it never served. `/v4/contents`
returns byte-for-byte what `/api/v3/contents` returns. It is a
documentation site. A plugin pointed at it would receive 200 and an HTML
page, forever, and a status-code check would call that success.

`hbb1.oscwii.org/api/v3/contents` answers `application/json`. That is the
API, and it is the one OSC-DL uses.

So this plugin **does not treat a status code as evidence a source is
alive.** `open_shop_channel/api.py` requires the body to parse as JSON, to
*be a list*, and for entries to carry the keys it reads. This is the same
guard `nointro-archive` grew after Myrient shut down and began answering
200 with an identical notice for every path — and the test for it replays
the real `api.oscwii.org` page, not a hand-written approximation.

`api.oscwii.org` is deliberately absent from `manifest.toml`, so the
broker would refuse the request even if a future version tried it.

## Games only, and why

The catalogue is mostly not game content. Measured across its 293
packages:

| Category | Count | Offered |
|---|---|---|
| utilities | 135 | no |
| **games** | **82** | **yes** |
| emulators | 52 | no |
| demos | 15 | no |
| media | 9 | no |

**Emulators are the clearest exclusion and the most tempting to get
wrong.** An emulator is a program that runs ROMs, not a ROM; filing
Snes9x GX as a Wii game would file a tool as content. Utilities and media
are the same argument with less temptation, and `demos` here means
demoscene productions rather than playable games.

Passing a non-game slug straight to `import` is refused by name, with the
category in the message, because that is a supported thing to do and the
refusal should say why.

## Search

There is no query API and none is needed. The whole catalogue is one
359 KB JSON document — comfortably inside the 4 MiB `ctx.http` allows — so
a search is **one request** and a match in memory. That is both faster
than walking pages and more honest: nothing depends on the answer being
in the pages that happened to be fetched.

Matching is a case-folded substring over name, slug and summary. Ranking
is exact name, then name-prefix, then everything else, and it is
deliberately dumb — a cleverer one would be a heuristic nobody could
predict from outside. An empty query enumerates the catalogue, which is a
reasonable thing to want from a source this size.

## Platforms

Everything here is `wii`. That slug was read off the six plugins in this
repository that already use it rather than chosen.

**vWii and Wii mini are not separate platforms.** Every package declares
`supported_platforms`, and across the 82 games it reads `wii` 82 times,
`vwii` 74 and `wii_mini` 74. Those are not three consoles — vWii is the
Wii mode inside a Wii U, and Wii mini is a cost-cut Wii. A library that
holds Wii software holds all three, so mapping them separately would
invent two platforms no library has in order to express a compatibility
note. `supported_platforms` is read as compatibility metadata, not as a
filing decision.

A `--platform` this archive has nothing for returns an empty list
**without a request**. That is not an error; it is a reasonable question
with a boring answer, and answering it for free beats answering it
slowly.

## What gets imported

The package's own `.zip`, which is the unit the archive publishes. A Wii
homebrew title is a directory — `boot.dol`, `meta.xml`, an icon — rather
than a single ROM file, and the zip is also the shape a Wii's SD card
wants.

The importer **re-reads the catalogue and matches the slug exactly**
rather than trusting the search result handed back to it. That result
left this process, so believing its URL would mean fetching something
that made a round trip through somewhere else. A near miss is refused
rather than imported: importing "the closest thing to what you asked for"
is the failure this codebase refuses everywhere else.

## Config

| Key | Type | Default | Meaning |
|---|---|---|---|
| `collection` | `str` | `"Open Shop Channel"` | collection to file imports under |

Empty means no collection, which is the right answer on a backend that
has none — the import still completes and the skip is reported.

No credentials. The host is public and unauthenticated, and this plugin
sends nothing but a GET.

## Network

`hbb1.oscwii.org` — declared in this plugin's own `manifest.toml`, which
is what the broker enforces. Verified 2026-07-30: all 293 packages carry
both their `zip` and their `icon` URL on that host and no other, so there
is no second host to declare and no redirect off it.

## Licence

MIT (this plugin's own code). The homebrew it imports carries its
authors' own terms.
