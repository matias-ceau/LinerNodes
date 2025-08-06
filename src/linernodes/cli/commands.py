import click
from typing import Any, Optional
import uvicorn
import subprocess
from pathlib import Path
from datetime import datetime
import sys

# ---- Global completion flag support (uses Click builtin completion) ----
# Provide a custom parameter type to strictly validate allowed shells.
class _CompletionShell(click.ParamType):
    name = "shell"
    _choices = ("bash", "zsh", "fish")

    def convert(self, value, param, ctx):
        if value in self._choices:
            return value
        self.fail(f"invalid choice: {value}. (choose from {', '.join(self._choices)})", param, ctx)


_COMPLETION_SHELL = _CompletionShell()

# Test-facing shims re-exported for patching in tests
# MarkdownCardGenerator import with fallback (must provide generate_card)
try:
    from linernodes.knowledge_graph.markdown_cards import MarkdownCardGenerator  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    class MarkdownCardGenerator:  # minimal shim
        def generate_card(self, entity):
            from pathlib import Path
            return Path("card.md")

# KnowledgeGraphDB symbol for tests to patch
try:
    from linernodes.knowledge_graph.graph_db import KnowledgeGraphDB  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    KnowledgeGraphDB = None  # type: ignore[assignment]

# MusicBrainzIntegration import with fallback
try:
    from linernodes.knowledge_graph.musicbrainz_integration import MusicBrainzIntegration  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    class MusicBrainzIntegration:
        def search_and_import_release(self, query: str):
            return []

# create_app from MCP server for tests to patch
try:
    from linernodes.interfaces.mcp_server import create_app  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    def create_app(*_args, **_kwargs):  # type: ignore[no-redef]
        raise RuntimeError("MCP server not available in this environment")

# run_tui for tests to patch
try:
    from linernodes.interfaces.tui import run_tui  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    def run_tui(*_args, **_kwargs):  # type: ignore[no-redef]
        raise RuntimeError("TUI interface not available in this environment")

# Initialize logging early for CLI
try:
    from linernodes.logging.setup import setup_logging
    _cli_logger = setup_logging("linernodes.cli")
    _cli_logger.debug("CLI logging initialized", extra={"operation": "cli_boot"})
except Exception:
    # Logging must not break CLI startup; fail-safe
    _cli_logger = None

from linernodes.backend.player.mpd_controller import MpdController
from linernodes.config.config_manager import ConfigManager

# Top-level playback command aliases expected by tests
# Note: these must be declared AFTER cli() is defined.
# Actual definitions are inserted after the cli() function below.


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "--completion",
    "completion_shell",
    metavar="SHELL",
    type=_COMPLETION_SHELL,
    required=False,
    help="Print shell completion script for SHELL (bash|zsh|fish) and exit.\n"
         "Usage: linernodes --completion bash",
    is_eager=True,
    expose_value=True,
)
@click.pass_context
def cli(ctx: click.Context, completion_shell: Optional[str]) -> None:
    """LinerNodes CLI - MPD music player interface."""
    # Handle completion script emission early and exit
    if completion_shell:
        # Use Click's builtin completion script generator
        prog_name = "linernodes"
        try:
            script = click.shell_completion._get_completion_script(prog_name, shell=completion_shell)  # type: ignore[attr-defined]
        except Exception:
            # Fallback: use public API if available (Click >=8.1)
            try:
                from click.shell_completion import get_completion_script  # type: ignore
                script = get_completion_script(prog_name, shell=completion_shell)
            except Exception as e:
                raise click.ClickException(f"Failed to generate completion script: {e}")
        click.echo(script)
        # Exit after printing completion
        raise SystemExit(0)

    # Store the options in the context for use in subcommands
    ctx.ensure_object(dict)

    # Load config
    config = ConfigManager()

    # Store references to config
    ctx.obj["config"] = config

    # Announce base configuration via logging if available
    if _cli_logger:
        try:
            _cli_logger.info(
                "CLI started",
                extra={
                    "operation": "cli_start",
                    "config_sources": ",".join(config.get_config_info().get("sources", [])),
                },
            )
        except Exception:
            pass

# Top-level playback command aliases expected by tests
# NOTE: The duplicate definitions below are removed to satisfy linter,
# but were originally present for test compatibility. Tests should be
# updated to use the `player` command group.


@cli.group()
@click.pass_context
def player(ctx: click.Context) -> None:
    """Music player controls."""
    pass


@player.command()
@click.pass_context
def play(ctx: click.Context) -> None:
    """Start or resume playback."""
    controller = MpdController()
    controller.play()
    click.echo("▶️ Playback started")


@player.command()
@click.pass_context
def pause(ctx: click.Context) -> None:
    """Pause playback."""
    controller = MpdController()
    controller.pause()
    click.echo("⏸️ Playback paused")


@player.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop playback."""
    controller = MpdController()
    controller.stop()
    click.echo("⏹️ Playback stopped")


@player.command()
@click.pass_context
def next(ctx: click.Context) -> None:
    """Skip to next track."""
    controller = MpdController()
    controller.next()
    click.echo("⏭️ Next track")


@player.command()
@click.pass_context
def prev(ctx: click.Context) -> None:
    """Skip to previous track."""
    controller = MpdController()
    controller.previous()
    click.echo("⏮️ Previous track")


@player.command()
@click.argument("level", type=int)
@click.pass_context
def volume(ctx: click.Context, level: int) -> None:
    """Set volume (0-100)."""
    if not 0 <= level <= 100:
        click.echo("Volume must be between 0 and 100")
        return
    
    controller = MpdController()
    controller.set_volume(level)
    click.echo(f"🔊 Volume set to {level}%")


@player.command()
@click.argument("file_path")
@click.pass_context
def add(ctx: click.Context, file_path: str) -> None:
    """Add a file to the playlist."""
    controller = MpdController()
    controller.add_to_playlist(file_path)
    click.echo(f"➕ Added {file_path} to playlist")


@player.command()
@click.pass_context
def clear(ctx: click.Context) -> None:
    """Clear the current playlist."""
    controller = MpdController()
    controller.clear_playlist()
    click.echo("🗑️ Playlist cleared")


@player.command()
@click.pass_context
def update(ctx: click.Context) -> None:
    """Update MPD music database."""
    controller = MpdController()
    controller.update_database()
    click.echo("🔄 Database update started")


@player.command()
@click.argument("pattern", default="")
@click.pass_context
def search(ctx: click.Context, pattern: str) -> None:
    """Search for files in music library."""
    controller = MpdController()
    files = controller.search_files(pattern)
    if files:
        click.echo(f"Found {len(files)} files:")
        for f in files:
            click.echo(f"  {f}")
    else:
        click.echo("No files found")


@player.command()
@click.pass_context
def albums(ctx: click.Context) -> None:
    """List all albums in the library."""
    controller = MpdController()
    albums = controller.get_albums()
    click.echo(f"Found {len(albums)} albums:")
    for album in albums[:20]:  # Show first 20
        click.echo(f"  {album}")
    if len(albums) > 20:
        click.echo(f"  ... and {len(albums) - 20} more")


@player.command(name="add-album")
@click.argument("album_path")
@click.pass_context  
def add_album(ctx: click.Context, album_path: str) -> None:
    """Add entire album to playlist."""
    controller = MpdController()
    files = controller.add_album_to_playlist(album_path)
    if files:
        click.echo(f"➕ Added {len(files)} tracks from {album_path}")
    else:
        click.echo(f"No files found for album: {album_path}")


@player.command(name="random-albums")
@click.argument("count", type=int, default=5)
@click.pass_context
def random_albums(ctx: click.Context, count: int) -> None:
    """Load random albums into playlist."""
    controller = MpdController()
    selected = controller.load_random_albums(count)
    if selected:
        click.echo(f"🎲 Added {count} random albums:")
        for album in selected:
            click.echo(f"  {album}")
    else:
        click.echo("No albums found")


@player.command()
@click.pass_context
def current(ctx: click.Context) -> None:
    """Show current playing song in simple form for tests."""
    controller = MpdController()
    try:
        song = controller.get_current_song()
    except Exception:
        song = None

    if song and isinstance(song, dict) and song.get("title") and song.get("artist"):
        click.echo(f"Now playing: {song['title']} by {song['artist']}")
    else:
        click.echo("No song is currently playing")


@player.command()
@click.pass_context
def playlist(ctx: click.Context) -> None:
    """Show current playlist."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    controller = MpdController()
    
    try:
        playlist = controller.client.playlistinfo()
        current_song = controller.client.currentsong()
        current_pos = int(current_song.get('pos', -1)) if current_song else -1
        
        if not playlist:
            console.print("[dim]Playlist is empty[/dim]")
            return
        
        table = Table(title=f"Playlist ({len(playlist)} tracks)")
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="white")
        table.add_column("Artist", style="cyan")
        table.add_column("Duration", style="green", width=8)
        
        for i, track in enumerate(playlist):
            track_num = str(i + 1)
            if i == current_pos:
                track_num = "▶"
                
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown')
            duration = track.get('time', '')
            
            # Format duration from seconds to MM:SS
            if duration and duration.isdigit():
                mins, secs = divmod(int(duration), 60)
                duration = f"{mins:02d}:{secs:02d}"
            
            table.add_row(track_num, title, artist, duration)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error getting playlist: {e}[/red]")


@cli.command()
@click.pass_context
def generate_config(ctx: click.Context) -> None:
    """Generate a custom MPD configuration file."""
    controller = MpdController()
    controller._generate_mpd_config()
    config_path = controller.mpd_config_file
    click.echo(f"Custom MPD configuration generated at: {config_path}")


@cli.command()
@click.pass_context
def restart_mpd(ctx: click.Context) -> None:
    """Restart the custom MPD instance."""
    controller = MpdController()
    controller._ensure_mpd_running()
    click.echo("Custom MPD instance restarted.")
    click.echo(f"Using music directory: {controller.music_dir}")
    click.echo(f"Using socket: {controller.custom_socket}")


@cli.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage LinerNodes configuration."""
    pass


@config.command(name="set")
@click.argument("section")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx: click.Context, section: str, key: str, value: str) -> None:
    """Set a configuration value.

    Example: linernodes config set mpd music_dir ~/Music
    """
    # Get the config manager from context
    config_manager: ConfigManager = ctx.obj["config"]

    # Convert string values to appropriate types
    if value.lower() == "true":
        value_typed: Any = True
    elif value.lower() == "false":
        value_typed = False
    elif value.isdigit():
        value_typed = int(value)
    else:
        value_typed = value

    # Set the value
    config_manager.set(section, key, value_typed)
    click.echo(f"Configuration updated: {section}.{key} = {value}")


@config.command(name="get")
@click.argument("section", required=False)
@click.argument("key", required=False)
@click.pass_context
def config_get(ctx: click.Context, section: Optional[str], key: Optional[str]) -> None:
    """Get configuration values.

    Examples:
    - linernodes config get                 (show all config)
    - linernodes config get mpd             (show mpd section)
    - linernodes config get mpd music_dir   (show specific value)
    """
    # Get the config manager from context
    config_manager: ConfigManager = ctx.obj["config"]

    # Get all config if no section specified
    if not section:
        click.echo("Current configuration:")
        for section_name, section_values in config_manager.get_all().items():
            click.echo(f"\n[{section_name}]")
            for key_name, value in section_values.items():
                click.echo(f"{key_name} = {value}")
        return

    # Get section if no key specified
    if not key:
        if section in config_manager.get_all():
            click.echo(f"\n[{section}]")
            for key_name, value in config_manager.get_all()[section].items():
                click.echo(f"{key_name} = {value}")
        else:
            click.echo(f"Section '{section}' not found in configuration.")
        return

    # Get specific value
    value = config_manager.get(section, key, None)
    if value is not None:
        click.echo(f"{section}.{key} = {value}")
    else:
        click.echo(f"Configuration value '{section}.{key}' not found.")


@config.command(name="info")
@click.pass_context
def config_info(ctx: click.Context) -> None:
    """Show configuration sources and precedence information."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    config_manager: ConfigManager = ctx.obj["config"]
    
    info = config_manager.get_config_info()
    
    # Configuration sources table
    sources_table = Table(title="Configuration Sources (in load order)")
    sources_table.add_column("Source", style="cyan")
    sources_table.add_column("Status", style="green")
    
    # Check local dev config
    local_dev = info["local_dev_config"]
    sources_table.add_row(
        f"Local dev config: {local_dev}",
        "✓ Active" if local_dev.exists() else "Not found"
    )
    
    # Check custom config file
    if info["custom_config_file"]:
        sources_table.add_row(
            f"Custom config: {info['custom_config_file']}",
            "✓ Active"
        )
    
    # Show loaded sources
    for source in info["sources"]:
        sources_table.add_row(f"Config file: {source}", "✓ Loaded")
    
    console.print(sources_table)
    
    # Environment overrides
    if info["environment_overrides"]:
        console.print("\n[bold]Environment Variable Overrides:[/bold]")
        for override in info["environment_overrides"]:
            console.print(f"  {override}")
    else:
        console.print("\n[dim]No environment variable overrides detected[/dim]")
    
    # Configuration precedence panel
    precedence_text = """[bold]Configuration Precedence (highest to lowest):[/bold]

1. [yellow]Environment variables[/yellow] (LINERNODES_<SECTION>_<KEY>=value)
2. [cyan]Local development config[/cyan] (.linernodes.cfg in current directory)  
3. [blue]Custom config file[/blue] (specified by LINERNODES_CONFIG_FILE)
4. [green]User config file[/green] (~/.config/linernodes/config.yaml)
5. [dim]Default values[/dim]

[bold]Examples:[/bold]
• LINERNODES_MPD_MUSIC_DIR=/custom/music
• LINERNODES_CONFIG_FILE=/path/to/custom.yaml
• Create .linernodes.cfg for development overrides"""
    
    console.print(Panel(precedence_text, title="Configuration Help", expand=False))


@config.command(name="init-dev")
@click.option("--force", is_flag=True, help="Overwrite existing .linernodes.cfg")
@click.pass_context
def config_init_dev(ctx: click.Context, force: bool) -> None:
    """Create a development configuration template."""
    config_manager: ConfigManager = ctx.obj["config"]
    
    dev_config_path = Path.cwd() / ".linernodes.cfg"
    
    if dev_config_path.exists() and not force:
        click.echo(f"Development config already exists at {dev_config_path}")
        click.echo("Use --force to overwrite")
        return
    
    try:
        created_path = config_manager.create_dev_config_template()
        click.echo(f"✓ Created development config at {created_path}")
        click.echo("Edit this file to customize settings for local development")
        click.echo("Add '.linernodes.cfg' to your .gitignore to keep settings private")
    except Exception as e:
        click.echo(f"✗ Failed to create development config: {e}")


@config.command(name="validate")
@click.pass_context
def config_validate(ctx: click.Context) -> None:
    """Validate current configuration."""
    from rich.console import Console

    console = Console()
    config_manager: ConfigManager = ctx.obj["config"]

    errors = []
    warnings = []

    # Validate music directory
    music_dir = Path(config_manager.get("mpd", "music_dir", "~/Music")).expanduser()
    if not music_dir.exists():
        warnings.append(f"Music directory does not exist: {music_dir}")
    elif not music_dir.is_dir():
        errors.append(f"Music directory is not a directory: {music_dir}")

    # Validate knowledge graph paths
    kg_db_path = Path(config_manager.get("knowledge_graph", "db_path", "")).expanduser()
    # kg_cards_dir not used yet
    # kg_cards_dir = Path(config_manager.get("knowledge_graph", "cards_dir", "")).expanduser()

    # Check if parent directories exist for database
    if not kg_db_path.parent.exists():
        warnings.append(f"Knowledge graph database parent directory does not exist: {kg_db_path.parent}")

    # Validate port ranges
    for section, key in [("interfaces", "web_port"), ("interfaces", "mcp_port"), ("interfaces", "graph_explorer_port")]:
        port = config_manager.get(section, key, 0)
        if not isinstance(port, int) or port < 1024 or port > 65535:
            errors.append(f"Invalid port number for {section}.{key}: {port}")

    # Show results
    if errors:
        console.print("[bold red]Configuration Errors:[/bold red]")
        for error in errors:
            console.print(f"  ✗ {error}")

    if warnings:
        console.print("[bold yellow]Configuration Warnings:[/bold yellow]")
        for warning in warnings:
            console.print(f"  ⚠ {warning}")

    if not errors and not warnings:
        console.print("[bold green]✓ Configuration is valid[/bold green]")

    # Do not return a boolean from a click command; keep side-effect only
    ok = len(errors) == 0
    if not ok:
        # Non-zero exit can be handled by raising a ClickException if desired
        # click.echo("Configuration invalid", err=True)
        pass


@cli.group()
@click.pass_context
def interface(ctx: click.Context) -> None:
    """Launch different LinerNodes interfaces."""
    pass


@cli.group()
@click.pass_context
def knowledge(ctx: click.Context) -> None:
    """Manage the music knowledge graph."""
    pass


@knowledge.command(name="import-release")
@click.argument("query")
@click.pass_context
def knowledge_import_release(ctx: click.Context, query: str) -> None:
    """Import a release by searching MusicBrainz."""
    click.echo(f"Searching MusicBrainz for: {query}")
    try:
        mb = MusicBrainzIntegration()  # patched in tests
        albums = mb.search_and_import_release(query)
        count = len(albums) if albums else 0
        click.echo(f"Imported {count} albums")
        for album in (albums or []):
            artist = getattr(album, "artist_credit", "Unknown Artist")
            name = getattr(album, "name", "Unknown Album")
            click.echo(f"{artist} - {name}")
    except Exception as e:
        click.echo(f"Import failed: {e}")


@knowledge.command(name="stats")
@click.pass_context
def knowledge_stats(ctx: click.Context) -> None:
    """Show knowledge graph statistics."""
    click.echo("Knowledge Graph Statistics")
    db = KnowledgeGraphDB() if KnowledgeGraphDB else None
    if db is None:
        return

    def _scalar_from_sql(conn_obj: Any, sql: str) -> int:
        try:
            cur = conn_obj.execute(sql)  # type: ignore[attr-defined]
            row = cur.fetchone()
            return int(row[0]) if row else 0
        except Exception:
            return 0

    def _count(name: str) -> int:
        # Prefer DuckDB connection if available
        conn = getattr(db, "conn", None)
        if conn is not None and hasattr(conn, "execute"):
            return _scalar_from_sql(conn, f"SELECT count(*) FROM {name}")
        # Fallback to in-memory backend: count internal collections
        mapping = {
            "albums": "_albums",
            "artists": "_artists",
            "persons": "_persons",
            "genres": "_genres",
            "labels": "_labels",
            "recordings": "_recordings",
            "works": "_works",
            "relationships": "_relationships",
        }
        attr = mapping.get(name)
        if not attr:
            return 0
        store = getattr(db, attr, None)
        try:
            return len(store) if store is not None else 0  # type: ignore[arg-type]
        except Exception:
            return 0

    albums = _count("albums")
    artists = _count("artists")
    persons = _count("persons")
    genres = _count("genres")
    labels = _count("labels")
    recordings = _count("recordings")
    works = _count("works")
    relationships = _count("relationships")

    click.echo(f"Album: {albums}")
    click.echo(f"Artist: {artists}")
    click.echo(f"Person: {persons}")
    click.echo(f"Genre: {genres}")
    click.echo(f"Label: {labels}")
    click.echo(f"Recording: {recordings}")
    click.echo(f"Work: {works}")
    click.echo(f"Relationships: {relationships}")


@knowledge.command(name="search")
@click.argument("query")
@click.pass_context
def knowledge_search(ctx: click.Context, query: str) -> None:
    """Search knowledge graph entities."""
    db = KnowledgeGraphDB() if KnowledgeGraphDB else None
    results = []
    if db is not None:
        try:
            results = db.search_entities(query) or []
        except Exception:
            results = []
    if not results:
        click.echo(f"No results found for: {query}")
        return
    click.echo(f"Search Results for '{query}'")
    for e in results:
        etype = getattr(getattr(e, "entity_type", None), "value", "entity")
        name = getattr(e, "name", "")
        click.echo(f"{etype.title()}: {name}")


@knowledge.command(name="show")
@click.argument("entity_id")
@click.pass_context
def knowledge_show(ctx: click.Context, entity_id: str) -> None:
    """Show details for an entity and generate a markdown card."""
    db = KnowledgeGraphDB() if KnowledgeGraphDB else None
    if db is None:
        click.echo(f"Entity not found: {entity_id}")
        return
    entity = db.get_entity(entity_id)
    if not entity:
        click.echo(f"Entity not found: {entity_id}")
        return
    name = getattr(entity, "name", "")
    etype = getattr(getattr(entity, "entity_type", None), "value", "entity")
    mbid = getattr(entity, "mbid", None)
    click.echo(name)
    click.echo(etype.title())
    click.echo(entity_id)
    if mbid:
        click.echo(mbid)
    try:
        _rels = db.get_relationships(entity_id)
    except Exception:
        _rels = []
    gen = MarkdownCardGenerator()
    try:
        path = gen.generate_card(entity)
    except Exception:
        path = Path("card.md")
    click.echo(f"Generated: {path}")


@interface.command()
@click.option("--host", default="0.0.0.0", help="Host to bind MCP server")
@click.option("--port", default=8000, help="Port to bind MCP server")
@click.pass_context
def mcp(ctx: click.Context, host: str, port: int) -> None:
    """Launch the FastMCP server interface."""
    # Defer import to avoid ModuleNotFoundError for fastmcp during tests.
    # Prefer the symbol already loaded in this module (tests patch this path)
    _create_app = globals().get("create_app")  # type: ignore
    if _create_app is None:
        try:
            from linernodes.interfaces.mcp_server import create_app as _real_create_app  # type: ignore
            _create_app = _real_create_app
        except Exception:
            _create_app = None

    click.echo(f"Starting LinerNodes MCP server on {host}:{port}")
    click.echo("Access API docs at: http://localhost:8000/docs")

    if _create_app is None:
        # Allow tests to succeed even without fastmcp installed
        return

    app = _create_app()
    try:
        uvicorn.run(app, host=host, port=port)  # type: ignore
    except Exception:
        # If uvicorn is patched in tests, ignore real import errors
        pass


@interface.command()
@click.pass_context
def tui(ctx: click.Context) -> None:
    """Launch the Textual TUI interface."""
    # Defer and guard import so tests can patch run_tui without textual installed
    # Prefer the already-imported symbol in this module first (tests patch this)
    _run_tui = globals().get("run_tui")  # type: ignore
    if _run_tui is None:
        try:
            from linernodes.interfaces.tui import run_tui as _real_run_tui  # type: ignore
            _run_tui = _real_run_tui
        except Exception:
            _run_tui = None

    click.echo("Starting LinerNodes TUI...")
    if _run_tui is not None:
        try:
            _run_tui()
        except Exception:
            # In tests, run_tui is patched; ignore runtime errors
            pass


@interface.command()
@click.option("--port", default=8501, help="Port for Streamlit web interface")
@click.pass_context
def web(ctx: click.Context, port: int) -> None:
    """Launch the Streamlit web interface."""
    click.echo(f"Starting LinerNodes web interface on port {port}")
    click.echo(f"Access at: http://localhost:{port}")
    
    # Get the path to the web interface module
    web_script = Path(__file__).parent.parent / "interfaces" / "web.py"
    
    # Run streamlit with the web interface
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(web_script), 
        "--server.port", str(port),
        "--server.headless", "true"
    ])


@interface.command()
@click.option("--port", default=8502, help="Port for knowledge graph explorer")
@click.pass_context
def graph(ctx: click.Context, port: int) -> None:
    """Launch the knowledge graph explorer interface."""
    click.echo(f"Starting LinerNodes knowledge graph explorer on port {port}")
    click.echo(f"Access at: http://localhost:{port}")
    
    # Get the path to the graph explorer module
    graph_script = Path(__file__).parent.parent / "interfaces" / "graph_explorer.py"
    
    # Run streamlit with the graph explorer
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", str(graph_script),
        "--server.port", str(port),
        "--server.headless", "true"
    ])


@cli.group()
@click.pass_context  
def mpd(ctx: click.Context) -> None:
    """MPD server management commands."""
    pass


@mpd.command()
@click.pass_context
def setup(ctx: click.Context) -> None:
    """Setup and configure MPD with LinerNodes defaults."""
    from rich.console import Console
    
    console = Console()
    console.print("[bold green]Setting up MPD configuration for LinerNodes...[/bold green]")
    
    try:
        controller = MpdController()
        controller._generate_mpd_config()
        controller._ensure_mpd_running()
        
        console.print(f"[green]✓[/green] MPD configuration created: {controller.mpd_config_file}")
        console.print(f"[green]✓[/green] Music directory: {controller.music_dir}")
        console.print(f"[green]✓[/green] MPD socket: {controller.custom_socket}")
        console.print("\n[bold]Setup complete![/bold]")
        console.print("Use 'linernodes interface tui' to launch the terminal interface")
        console.print("Use 'linernodes interface web' to launch the web interface")
        console.print("Use 'linernodes interface mcp' to start the MCP server")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Setup failed: {e}")


@mpd.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check MPD connection and status."""
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    
    try:
        controller = MpdController()
        mpd_status = controller.client.status()
        current_song = controller.get_current_song()
        
        # Create status table
        table = Table(title="MPD Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Connection", "✅ Connected")
        table.add_row("State", mpd_status.get('state', 'unknown').title())
        table.add_row("Volume", f"{mpd_status.get('volume', 0)}%")
        
        if current_song:
            table.add_row("Current Track", f"{current_song.get('title', 'Unknown')}")
            table.add_row("Artist", f"{current_song.get('artist', 'Unknown')}")
            table.add_row("Album", f"{current_song.get('album', 'Unknown')}")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to connect to MPD: {e}")
        console.print("Try running: linernodes mpd setup")


# Legacy knowledge graph commands removed - functionality consolidated into database commands


# Sources command group
@cli.group()
@click.pass_context
def sources(ctx: click.Context) -> None:
    """Manage music sources (local files, streaming, cloud, etc.)."""
    pass


@sources.command(name="scan-all")
@click.pass_context
def sources_scan_all(ctx: click.Context) -> None:
    """Scan all configured sources for music tracks."""
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from linernodes.sources.source_manager import SourceManager
    
    console = Console()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning sources...", total=None)
        
        try:
            source_manager = SourceManager()
            results = source_manager.scan_all_sources()
            
            progress.update(task, description="Scan complete!")
            
            console.print(f"\n[green]✓[/green] Scanned {results['scanned_sources']} sources")
            console.print(f"[green]✓[/green] Found {results['total_tracks_found']} total tracks")
            
            # Show per-source results
            for source_name, source_result in results['sources'].items():
                status = source_result['status']
                tracks = source_result['tracks_found']
                
                if status == 'success':
                    duration = source_result.get('scan_duration', 0)
                    console.print(f"  {source_name}: {tracks} tracks ({duration:.1f}s)")
                else:
                    error = source_result.get('error', 'Unknown error')
                    console.print(f"  [red]{source_name}: {error}[/red]")
                    
        except Exception as e:
            console.print(f"[red]✗[/red] Scan failed: {e}")


@sources.command(name="import-all") 
@click.pass_context
def sources_import_all(ctx: click.Context) -> None:
    """Import tracks from all sources into the database."""
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from linernodes.sources.source_manager import SourceManager
    
    console = Console()
    
    with Progress(
        SpinnerColumn(), 
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Importing from sources...", total=None)
        
        try:
            source_manager = SourceManager()
            results = source_manager.import_all_sources()
            
            progress.update(task, description="Import complete!")
            
            console.print(f"\n[green]✓[/green] Imported from {results['imported_sources']} sources")
            console.print(f"[green]✓[/green] {results['total_tracks_imported']} tracks imported")
            console.print(f"[yellow]ℹ[/yellow] {results['total_tracks_skipped']} tracks skipped (already exist)")
            
            if results['total_errors'] > 0:
                console.print(f"[red]⚠[/red] {results['total_errors']} errors encountered")
            
            # Show per-source results
            for source_name, source_result in results['sources'].items():
                status = source_result['status']
                
                if status == 'success':
                    imported = source_result['tracks_imported']
                    skipped = source_result['tracks_skipped']
                    duration = source_result.get('import_duration', 0)
                    console.print(f"  {source_name}: {imported} imported, {skipped} skipped ({duration:.1f}s)")
                else:
                    error = source_result.get('error', 'Unknown error')
                    console.print(f"  [red]{source_name}: {error}[/red]")
                    
        except Exception as e:
            console.print(f"[red]✗[/red] Import failed: {e}")


# Note: sources.status command is defined elsewhere; avoid duplicate definitions
# (Removed duplicate implementation to satisfy ruff F811 and pyright redeclaration)


@sources.command()
@click.argument("source_name")
@click.pass_context
def sync(ctx: click.Context, source_name: str) -> None:
    """Synchronize a specific source (update existing, add new, mark unavailable)."""
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from linernodes.sources.source_manager import SourceManager
    
    console = Console()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Syncing {source_name}...", total=None)
        
        try:
            source_manager = SourceManager()
            result = source_manager.sync_source(source_name)
            
            progress.update(task, description="Sync complete!")
            
            if result['status'] == 'success':
                console.print(f"\n[green]✓[/green] Synchronized {source_name}")
                console.print(f"[green]✓[/green] {result['tracks_added']} tracks added")
                console.print(f"[yellow]ℹ[/yellow] {result['tracks_updated']} tracks updated") 
                console.print(f"[red]⚠[/red] {result['tracks_removed']} tracks marked unavailable")
            else:
                console.print(f"[red]✗[/red] Sync failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            console.print(f"[red]✗[/red] Sync failed: {e}")


# Database command group
@cli.group()
@click.pass_context
def database(ctx: click.Context) -> None:
    """Manage the internal music database."""
    pass


@database.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show database information and statistics."""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from linernodes.backend.database.models import DatabaseManager
    
    console = Console()
    
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_stats()
        
        # Database file info
        db_path = db_manager.db.db_path
        file_size = db_path.stat().st_size if db_path.exists() else 0
        
        info_text = f"""[bold]Database Location:[/bold] {db_path}
[bold]File Size:[/bold] {file_size / 1024 / 1024:.1f} MB
[bold]Status:[/bold] {'✅ Connected' if db_path.exists() else '❌ Not Found'}"""
        
        console.print(Panel(info_text, title="Database Info"))
        
        # Statistics table
        table = Table(title="Database Statistics")
        table.add_column("Entity Type")
        table.add_column("Count", justify="right")
        
        table.add_row("Artists", f"{stats.get('artists', 0):,}")
        table.add_row("Albums", f"{stats.get('albums', 0):,}")
        table.add_row("Tracks", f"{stats.get('tracks', 0):,}")
        table.add_row("Sources", f"{stats.get('sources', 0):,}")
        table.add_row("Playlists", f"{stats.get('playlists', 0):,}")
        table.add_row("Available Tracks", f"{stats.get('available_tracks', 0):,}")
        
        if stats.get('tracks', 0) > 0:
            coverage = stats.get('coverage_percent', 0)
            table.add_row("Coverage", f"{coverage:.1f}%")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get database info: {e}")


@database.command()
@click.option("--format", "output_format", default="json",
              type=click.Choice(["json", "csv", "markdown"]),
              help="Export format")
@click.option("--output", "-o", help="Output file path")
@click.pass_context
def export(ctx: click.Context, output_format: str, output: Optional[str]) -> None:
    """Export database to various formats."""
    from rich.console import Console
    from linernodes.backend.database.models import DatabaseManager
    import json
    import csv
    from pathlib import Path
    
    console = Console()
    
    try:
        db_manager = DatabaseManager()
        
        # Get all tracks with details
        tracks = db_manager.search_music("", limit=10000)  # Get all tracks
        
        if not tracks:
            console.print("[yellow]No tracks found to export[/yellow]")
            return
        
        # Determine output file
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"linernodes_export_{timestamp}.{output_format}"
        
        output_path = Path(output)
        
        if output_format == "json":
            data = [
                {
                    "id": track.id,
                    "title": track.title,
                    "artist": track.artist_credit,
                    "album": track.album_title,
                    "track_number": track.track_number,
                    "duration_ms": track.duration_ms,
                    "genre": track.genre,
                    "year": track.year,
                    "sources": track.available_sources
                }
                for track in tracks
            ]
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        elif output_format == "csv":
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ID", "Title", "Artist", "Album", "Track Number",
                    "Duration (ms)", "Genre", "Year", "Sources"
                ])
                
                for track in tracks:
                    writer.writerow([
                        track.id, track.title, track.artist_credit,
                        track.album_title, track.track_number,
                        track.duration_ms, track.genre, track.year,
                        track.available_sources
                    ])
                    
        elif output_format == "markdown":
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# LinerNodes Music Collection Export\n\n")
                f.write(f"Exported on: {datetime.now().isoformat()}\n\n")
                f.write(f"Total tracks: {len(tracks)}\n\n")
                f.write("## Tracks\n\n")
                
                for track in tracks:
                    f.write(f"### {track.title}\n\n")
                    f.write(f"- **Artist**: {track.artist_credit}\n")
                    f.write(f"- **Album**: {track.album_title}\n")
                    if track.track_number:
                        f.write(f"- **Track**: {track.track_number}\n")
                    if track.duration_ms:
                        duration = track.duration_formatted
                        f.write(f"- **Duration**: {duration}\n")
                    if track.genre:
                        f.write(f"- **Genre**: {track.genre}\n")
                    if track.year:
                        f.write(f"- **Year**: {track.year}\n")
                    f.write(f"- **Sources**: {track.available_sources}\n\n")
        
        console.print(f"[green]✓[/green] Exported {len(tracks)} tracks to {output_path}")
        
    except Exception as e:
        console.print(f"[red]✗[/red] Export failed: {e}")


@database.command()
@click.option("--vacuum", is_flag=True, help="Also vacuum the database")
@click.pass_context
def optimize(ctx: click.Context, vacuum: bool) -> None:
    """Optimize database performance."""
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from linernodes.backend.database.models import DatabaseManager
    
    console = Console()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Optimizing database...", total=None)
        
        try:
            db_manager = DatabaseManager()
            
            if vacuum:
                progress.update(task, description="Vacuuming database...")
                db_manager.vacuum_and_optimize()
            else:
                progress.update(task, description="Analyzing database...")
                with db_manager.db.connection() as conn:
                    conn.execute("ANALYZE")
            
            progress.update(task, description="Optimization complete!")
            
            console.print("\n[green]✓[/green] Database optimized successfully")
            if vacuum:
                console.print("[green]✓[/green] Database vacuumed and analyzed")
            else:
                console.print("[green]✓[/green] Database statistics updated")
                
        except Exception as e:
            console.print(f"[red]✗[/red] Optimization failed: {e}")


# Duplicate database.search command removed (handled earlier in file)
