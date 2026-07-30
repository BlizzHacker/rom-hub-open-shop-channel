"""Turn an Open Shop Channel slug into a FetchPlan.

The catalogue is re-read and the slug **matched exactly**, rather than
trusting the `SearchResult` handed back. That result left this process --
the host serialised it, the operator's command chose it, and it arrives
as a dict this plugin did not construct -- so believing its `url` would
mean fetching a URL that made a round trip through somewhere else. The
host would still check that URL against the allowlist, but the allowlist
is a host check and this is a correctness one: the plan should fetch the
package the operator named.

Exact match, not nearest. Importing "the closest thing to what you asked
for" is the failure this codebase refuses everywhere else.

The payload is the package's own `.zip`, which is what the Open Shop
Channel distributes: a Wii homebrew title is a directory of files
(`boot.dol`, `meta.xml`, an icon) rather than a single ROM, and the zip
is the unit the archive publishes and the unit a Wii's SD card wants.
"""

from rom_hub_sdk import FetchFile, FetchPlan, ImportProvider, SearchResult

from . import api
from .filenames import safe_filename
from .platforms import WII

DEFAULT_COLLECTION = "Open Shop Channel"


class ImportRefused(Exception):
    """This package cannot be imported, and the message says why."""


class Importer(ImportProvider):
    def plan(self, result: SearchResult) -> FetchPlan:
        slug = (result.source_id or "").strip()
        if not slug:
            raise ImportRefused(
                "the search result carries no Open Shop Channel slug"
            )

        package = self._package(slug)

        return FetchPlan(
            files=[
                FetchFile(
                    url=package.zip_url,
                    filename=safe_filename(
                        f"{package.slug}.zip", fallback="homebrew.zip"
                    ),
                    size_bytes=package.zip_bytes,
                )
            ],
            platform=WII,
            collection=self._collection(),
        )

    # -- lookup -----------------------------------------------------------

    def _package(self, slug: str):
        response = self.ctx.http.get(api.API)
        if response.status_code != 200:
            raise ImportRefused(
                f"{api.API} answered HTTP {response.status_code}"
            )
        packages = api.parse_contents(response.text)

        for package in packages:
            if package.slug == slug:
                break
        else:
            raise ImportRefused(
                f"no Open Shop Channel package has the slug {slug!r}. The "
                f"catalogue carries {len(packages)} packages; this plugin "
                f"matches a slug exactly rather than importing the nearest "
                f"thing to it."
            )

        if not package.is_game:
            # Reachable when a slug is passed straight to `import` without
            # a search, which is a supported thing to do.
            raise ImportRefused(
                f"Open Shop Channel package {slug!r} is in the "
                f"{package.category!r} category, and this plugin offers "
                f"only {api.GAME_CATEGORY!r}. An emulator or a utility is a "
                f"program that runs content, not content."
            )
        return package

    def _collection(self) -> str | None:
        raw = self.ctx.config.get("collection")
        if raw is None:
            return DEFAULT_COLLECTION
        collection = str(raw).strip()
        return collection or None
