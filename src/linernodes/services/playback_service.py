"""
PlaybackService: thin facade over MpdController.

No behavior changes. Methods forward to the controller and return its results.
Logging is performed via linernodes.logging.setup.get_logger when available.
"""

from __future__ import annotations

from typing import List, Dict, Optional

# Lightweight logging (safe import)
try:
    from linernodes.logging.setup import get_logger  # type: ignore

    _logger = get_logger("services.playback")
except Exception:  # pragma: no cover
    import logging as _fallback_logging

    _logger = _fallback_logging.getLogger("services.playback")

from linernodes.backend.player.mpd_controller import MpdController


class PlaybackService:
    """
    Application service for playback interactions.

    This class wraps MpdController to provide a stable API for higher layers.
    It intentionally avoids any additional side-effects beyond the controller.
    """

    def __init__(self, controller: Optional[MpdController] = None) -> None:
        self._controller = controller or MpdController()
        _logger.debug(
            "PlaybackService initialized", extra={"operation": "playback_init"}
        )

    # Simple forwards
    def play(self, pos: Optional[int] = None) -> None:
        _logger.debug("play called", extra={"operation": "play"})
        self._controller.play(pos)

    def pause(self) -> None:
        _logger.debug("pause called", extra={"operation": "pause"})
        self._controller.pause()

    def stop(self) -> None:
        _logger.debug("stop called", extra={"operation": "stop"})
        self._controller.stop()

    def next(self) -> None:
        _logger.debug("next called", extra={"operation": "next"})
        self._controller.next()

    def previous(self) -> None:
        _logger.debug("previous called", extra={"operation": "previous"})
        self._controller.previous()

    def set_volume(self, volume: int) -> None:
        _logger.debug(
            "set_volume called", extra={"operation": "set_volume", "volume": volume}
        )
        self._controller.set_volume(volume)

    # Thin wrappers
    def status(self) -> Dict:
        _logger.debug("status called", extra={"operation": "status"})
        return self._controller.get_status()

    def playlist(self) -> List[Dict]:
        _logger.debug("playlist called", extra={"operation": "playlist"})
        return self._controller.get_playlist()

    def add_file(self, path: str) -> None:
        _logger.debug("add_file called", extra={"operation": "add_file", "path": path})
        self._controller.add_to_playlist(path)

    def add_album(self, album_path: str) -> List[str]:
        _logger.debug(
            "add_album called",
            extra={"operation": "add_album", "album_path": album_path},
        )
        return self._controller.add_album_to_playlist(album_path)

    def load_random_albums(self, count: int) -> List[str]:
        _logger.debug(
            "load_random_albums called",
            extra={"operation": "load_random_albums", "count": count},
        )
        return self._controller.load_random_albums(count)
