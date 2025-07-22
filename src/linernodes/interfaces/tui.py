from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, ProgressBar, Label, DataTable
from textual.binding import Binding
from textual.reactive import reactive
from textual import work
import asyncio
from datetime import datetime
from typing import Optional

from ..backend.player.mpd_controller import MpdController

class PlayerStatus(Static):
    """Widget to display current player status"""
    
    current_track = reactive("No track playing")
    player_state = reactive("stopped")
    volume = reactive(0)
    
    def compose(self) -> ComposeResult:
        yield Label(self.current_track, id="track-info")
        yield Label(f"State: {self.player_state} | Volume: {self.volume}%", id="status-info")
        with Horizontal():
            yield ProgressBar(total=100, show_eta=False, id="position-bar")

class PlayerControls(Container):
    """Widget for player control buttons"""
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("⏮", id="prev", variant="primary")
            yield Button("⏯", id="play_pause", variant="success")
            yield Button("⏭", id="next", variant="primary")  
            yield Button("⏹", id="stop", variant="error")
            yield Button("🔄", id="update", variant="default")

class PlaylistView(Container):
    """Widget to display current playlist"""
    
    def compose(self) -> ComposeResult:
        yield Label("Current Playlist")
        table = DataTable()
        table.add_columns("Title", "Artist", "Album")
        yield table

class MusicPlayerTUI(App[None]):
    """A comprehensive Textual TUI for LinerNodes music player."""
    
    TITLE = "LinerNodes Music Player"
    SUB_TITLE = "MPD Controller Interface"
    
    CSS = """
    Screen {
        layout: grid;
        grid-size: 1 4;
        grid-rows: auto 1fr auto auto;
    }
    
    #player-status {
        height: 6;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    #player-controls {
        height: 3;
        margin: 1;
    }
    
    #playlist-view {
        border: solid $secondary;
        margin: 1;
        padding: 1;
    }
    
    #track-info {
        text-style: bold;
        text-align: center;
    }
    
    #status-info {
        text-align: center;
        margin-top: 1;
    }
    
    Button {
        margin: 0 1;
        min-width: 8;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("space", "toggle_play", "Play/Pause"), 
        Binding("n", "next_track", "Next"),
        Binding("p", "prev_track", "Previous"),
        Binding("s", "stop_playback", "Stop"),
        Binding("u", "update_db", "Update DB"),
        Binding("r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        self.controller: Optional[MpdController] = None
        self.status_widget: Optional[PlayerStatus] = None
        
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        self.status_widget = PlayerStatus(id="player-status")
        yield self.status_widget
        yield PlayerControls(id="player-controls")
        yield PlaylistView(id="playlist-view")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize MPD controller and start status updates."""
        try:
            self.controller = MpdController()
            self.start_status_updates()
        except Exception as e:
            self.notify(f"Failed to connect to MPD: {e}", severity="error")

    @work(exclusive=True)
    async def start_status_updates(self):
        """Continuously update player status."""
        while True:
            if self.controller and self.status_widget:
                try:
                    await self.update_status()
                except Exception as e:
                    self.notify(f"Status update error: {e}", severity="warning")
            await asyncio.sleep(1)

    async def update_status(self):
        """Update the status display with current MPD info."""
        if not self.controller or not self.status_widget:
            return
            
        try:
            current_song = self.controller.get_current_song()
            status = self.controller.client.status()
            
            if current_song:
                title = current_song.get('title', 'Unknown')
                artist = current_song.get('artist', 'Unknown')
                self.status_widget.current_track = f"{title} - {artist}"
            else:
                self.status_widget.current_track = "No track playing"
                
            self.status_widget.player_state = status.get('state', 'stop')
            self.status_widget.volume = int(status.get('volume', 0))
            
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if not self.controller:
            self.notify("MPD not connected", severity="error")
            return
            
        button_id = event.button.id
        
        try:
            if button_id == "play_pause":
                self.action_toggle_play()
            elif button_id == "next":
                self.action_next_track()
            elif button_id == "prev":
                self.action_prev_track()
            elif button_id == "stop":
                self.action_stop_playback()
            elif button_id == "update":
                self.action_update_db()
        except Exception as e:
            self.notify(f"Action failed: {e}", severity="error")

    def action_toggle_play(self) -> None:
        """Toggle play/pause."""
        if self.controller:
            status = self.controller.client.status()
            if status.get('state') == 'play':
                self.controller.pause()
                self.notify("Paused")
            else:
                self.controller.play()
                self.notify("Playing")

    def action_next_track(self) -> None:
        """Skip to next track."""
        if self.controller:
            self.controller.client.next()
            self.notify("Next track")

    def action_prev_track(self) -> None:
        """Skip to previous track."""
        if self.controller:
            self.controller.client.previous()
            self.notify("Previous track")

    def action_stop_playback(self) -> None:
        """Stop playback."""
        if self.controller:
            self.controller.client.stop()
            self.notify("Stopped")

    def action_update_db(self) -> None:
        """Update music database."""
        if self.controller:
            self.controller.client.update()
            self.notify("Database update started")

    def action_refresh(self) -> None:
        """Force refresh of status display."""
        self.notify("Refreshing...")

def run_tui():
    """Entry point to run the TUI."""
    app = MusicPlayerTUI()
    app.run()