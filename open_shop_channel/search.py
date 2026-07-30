"""Search the Open Shop Channel.

There is no query API, and none is wanted. The whole catalogue is one
359 KB JSON document, so a search is one request and a match in memory --
which is both faster and more honest than walking pages hoping the answer
is in the ones fetched.

Matching is a case-folded substring over the package's name, its slug and
its one-line summary, in that order of preference: an exact name match
sorts first, then a name that starts with the query, then everything
else. That ordering is the whole ranking, and it is deliberately dumb --
a smarter one would be a heuristic nobody could predict from the outside.

An empty query returns the catalogue, bounded by `limit`. That is what
`rom-hub search ""` should do for a source small enough to enumerate.
"""

from rom_hub_sdk import SearchProvider, SearchResult

from . import api
from .platforms import WII, is_supported


class Search(SearchProvider):
    def search(
        self, query: str, platform: str | None, limit: int
    ) -> list[SearchResult]:
        wanted = (platform or "").strip()
        if wanted and not is_supported(wanted):
            # This archive is Wii homebrew and nothing else. Answering
            # for free beats answering slowly.
            return []

        packages = api.games(self._contents())
        needle = (query or "").strip().casefold()
        if needle:
            packages = [p for p in packages if self._matches(p, needle)]
            packages.sort(key=lambda p: self._rank(p, needle))

        results: list[SearchResult] = []
        for package in packages[: max(limit, 0)]:
            results.append(
                SearchResult(
                    source_id=package.slug,
                    title=package.name,
                    platform=WII,
                    size_bytes=package.zip_bytes,
                    url=package.zip_url,
                    extra=self._extra(package),
                )
            )
        return results

    # -- matching ---------------------------------------------------------

    @staticmethod
    def _matches(package, needle: str) -> bool:
        return (
            needle in package.name.casefold()
            or needle in package.slug.casefold()
            or needle in package.summary.casefold()
        )

    @staticmethod
    def _rank(package, needle: str) -> tuple[int, str]:
        name = package.name.casefold()
        if name == needle:
            tier = 0
        elif name.startswith(needle):
            tier = 1
        elif needle in name:
            tier = 2
        else:
            tier = 3
        return tier, name

    @staticmethod
    def _extra(package) -> dict[str, str]:
        extra = {}
        if package.author:
            extra["author"] = package.author
        if package.version:
            extra["version"] = package.version
        if package.summary:
            extra["summary"] = package.summary
        return extra

    # -- the one request --------------------------------------------------

    def _contents(self):
        response = self.ctx.http.get(api.API)
        if response.status_code != 200:
            raise api.SourceChanged(
                f"{api.API} answered HTTP {response.status_code}"
            )
        # A 200 is not evidence on this host's siblings -- see api.py --
        # so the body is what decides.
        return api.parse_contents(response.text)
