import logging
from typing import Any, Tuple

from dash.dash import no_update

logger = logging.getLogger(__name__)


class ModalService:
    """Service managing modal open/close logic for the upload page."""

    def handle_dialogs(
        self,
        verify_clicks: int | None,
        classify_clicks: int | None,
        confirm_clicks: int | None,
        cancel_col_clicks: int | None,
        cancel_dev_clicks: int | None,
        trigger_id: str,
    ) -> Tuple[Any, Any, Any]:
        if "verify-columns-btn-simple" in trigger_id and verify_clicks:
            return no_update, True, no_update

        if "classify-devices-btn" in trigger_id and classify_clicks:
            return no_update, no_update, True

        if "column-verify-confirm" in trigger_id and confirm_clicks:
            return no_update, False, no_update

        if "column-verify-cancel" in trigger_id or "device-verify-cancel" in trigger_id:
            return no_update, False, False

        return no_update, no_update, no_update


__all__ = ["ModalService"]
