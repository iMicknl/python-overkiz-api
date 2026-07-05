"""Models for the Somfy BOB back-office site directory.

BOB is a separate service from the Overkiz enduser API, with its own payload
shapes (``siteOID``, ``subSites``, ``externalOID``). It therefore gets its own
tiny cattrs converter here rather than sharing ``pyoverkiz.converter``, which is
scoped to the enduser API and its camelCase convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cattrs
from cattrs.gen import make_dict_structure_fn, override

from pyoverkiz.auth.base import GatewayCandidate


@dataclass(slots=True)
class BobGateway:
    """A gateway entry under a sub-site."""

    gateway_id: str


@dataclass(slots=True)
class BobSubSite:
    """A sub-site (setup) grouping one or more gateways."""

    external_id: str | None = None
    gateways: list[BobGateway] = field(default_factory=list)


@dataclass(slots=True)
class BobSite:
    """A site (home) the account owns or was invited to."""

    site_oid: str
    name: str | None = None
    country: str | None = None
    sub_sites: list[BobSubSite] = field(default_factory=list)


@dataclass(slots=True)
class BobSitesResponse:
    """The ``/sites`` listing, flattened on demand to gateway candidates."""

    results: list[BobSite] = field(default_factory=list)

    def gateway_candidates(self) -> list[GatewayCandidate]:
        """Flatten the site -> sub-site -> gateway tree into candidates."""
        return [
            GatewayCandidate(
                gateway_id=gateway.gateway_id,
                home_id=site.site_oid,
                label=site.name,
                external_id=sub.external_id,
                country=site.country,
            )
            for site in self.results
            for sub in site.sub_sites
            for gateway in sub.gateways
        ]


def _make_bob_converter() -> cattrs.Converter:
    # Converter (not GenConverter) so unknown BOB keys are dropped for forward-compat.
    c = cattrs.Converter()
    c.register_structure_hook(
        BobGateway,
        make_dict_structure_fn(BobGateway, c, gateway_id=override(rename="gatewayId")),
    )
    c.register_structure_hook(
        BobSubSite,
        make_dict_structure_fn(
            BobSubSite, c, external_id=override(rename="externalOID")
        ),
    )
    c.register_structure_hook(
        BobSite,
        make_dict_structure_fn(
            BobSite,
            c,
            site_oid=override(rename="siteOID"),
            sub_sites=override(rename="subSites"),
        ),
    )
    return c


bob_converter = _make_bob_converter()
