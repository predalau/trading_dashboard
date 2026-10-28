"""Venue factory. Only 'paper' is wired today; 'solana' lands in Phase 4."""
from app.execution.base import ExecutionVenue, OrderRequest, OrderResult
from app.execution.paper import PaperVenue

SUPPORTED_MODES = {"paper"}


def get_venue(mode: str) -> ExecutionVenue:
    if mode == "paper":
        return PaperVenue()
    raise ValueError(f"Unsupported execution mode: {mode}")


__all__ = ["ExecutionVenue", "OrderRequest", "OrderResult", "get_venue", "SUPPORTED_MODES"]
