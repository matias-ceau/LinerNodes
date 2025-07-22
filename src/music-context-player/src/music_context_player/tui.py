from textual.app import App
from textual.containers import Container
from textual.widgets import Header, Footer, Static

class MusicPlayerApp(App):
    """A Textual TUI for the music context player."""
    
    CSS = """
    .header {
        dock: top;
        height: 3;
    }
    
    .footer {
        dock: bottom;
        height: 3;
    }
    
    .main {
        height: 1fr;
        align: center middle;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]
    
    def compose(self):
        yield Header()
        yield Container(
            Static("Music Context Player TUI", classes="main"),
            id="main"
        )
        yield Footer()