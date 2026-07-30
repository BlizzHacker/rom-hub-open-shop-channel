"""This source's platform, and the one library slug it maps to.

The Open Shop Channel is a Wii homebrew archive and nothing else, so this
table has one row. It is still a table, and still exact-match with no
fallback, because the value of the rule is that it does not bend when a
second row shows up.

`wii` was **read off this project**, not chosen. Five plugins already use
it -- `hasheous`, `libretro-content`, `libretro-database`,
`libretro-thumbnails`, `openvgdb` and `retroachievements`. Agreeing costs
nothing; disagreeing would file Wii homebrew where nothing else looks.

## vWii and Wii mini are not separate platforms here

Every package declares `supported_platforms`, and across the 82 games it
reads `wii` 82 times, `vwii` 74 and `wii_mini` 74. Those are not three
consoles: vWii is the Wii mode inside a Wii U and Wii mini is a cost-cut
Wii, and a library that holds Wii software holds all three. Mapping them
separately would invent two platforms no library has, to express a
compatibility note rather than a filing decision.

So `supported_platforms` is not read as a platform at all. It is
compatibility metadata about one platform's software, and every game here
runs on a Wii.
"""

#: Library platform slug for everything this source carries.
WII = "wii"


class NeedsMapping(Exception):
    """A platform this plugin has nothing for."""


def is_supported(platform: str) -> bool:
    """Whether a `--platform` this source could answer for.

    A RomM platform this archive has nothing for is not an error -- it is
    a reasonable question with a boring answer, and `search` returns an
    empty list for it *without a request*, the way `homebrew` does.
    """
    return (platform or "").strip().casefold() == WII
