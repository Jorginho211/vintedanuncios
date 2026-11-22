from __future__ import annotations

from ...shared.models import Listing, PublishResult


class DryRunListingPublisher:
    """Simula la publicación sin navegador ni escritura en Vinted."""

    def publish(self, listing: Listing) -> PublishResult:
        return PublishResult(ok=True, message=f"[dry-run] {listing.folder} -> {listing.title}")
