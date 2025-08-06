import click
from typing import Any, Optional
import uvicorn
import subprocess
from pathlib import Path
from datetime import datetime
import sys

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


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """LinerNodes CLI - MPD music player interface."""
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
    """Show current playing song with detailed info."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    
    console = Console()
    controller = MpdController()
    
    try:
        song = controller.get_current_song()
        status = controller.client.status()
        
        if not song:
            console.print("[dim]No track currently playing[/dim]")
            return
        
        # Format track info
        title = song.get('title', 'Unknown Title')
        artist = song.get('artist', 'Unknown Artist')
        album = song.get('album', 'Unknown Album')
        track_num = song.get('track', '')
        duration = song.get('time', '')
        
        # Format status info
        state = status.get('state', 'unknown')
        volume = status.get('volume', '0')
        position = status.get('time', '0:00/0:00')
        
        # Create display
        track_info = Text()
        track_info.append(f"🎵 {title}\n", style="bold white")
        track_info.append(f"👤 {artist}\n", style="cyan")
        track_info.append(f"💿 {album}", style="blue")
        
        if track_num:
            track_info.append(f" (Track {track_num})")
        
        status_info = f"State: {state.title()} | Volume: {volume}% | Position: {position}"
        if duration:
            status_info += f" | Duration: {duration}"
        
        panel = Panel(
            track_info,
            title="🎶 Now Playing",
            subtitle=status_info,
            expand=False
        )
        
        console.print(panel)
        
    except Exception as e:
        console.print(f"[red]Error getting current track: {e}[/red]")


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
    kg_cards_dir = Path(config_manager.get("knowledge_graph", "cards_dir", "")).expanduser()
    
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
    
    return len(errors) == 0


@cli.group()
@click.pass_context
def interface(ctx: click.Context) -> None:
    """Launch different LinerNodes interfaces."""
    pass


@interface.command()
@click.option("--host", default="0.0.0.0", help="Host to bind MCP server")
@click.option("--port", default=8000, help="Port to bind MCP server")
@click.pass_context
def mcp(ctx: click.Context, host: str, port: int) -> None:
    """Launch the FastMCP server interface."""
    from linernodes.interfaces.mcp_server import create_app
    
    click.echo(f"Starting LinerNodes MCP server on {host}:{port}")
    click.echo("Access API docs at: http://localhost:8000/docs")
    
    app = create_app()
    uvicorn.run(app, host=host, port=port)


@interface.command()
@click.pass_context
def tui(ctx: click.Context) -> None:
    """Launch the Textual TUI interface."""
    from linernodes.interfaces.tui import run_tui
    
    click.echo("Starting LinerNodes TUI...")
    run_tui()


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


@sources.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show status of all configured sources."""
    from rich.console import Console
    from rich.table import Table
    from linernodes.sources.source_manager import SourceManager
    
    console = Console()
    
    try:
        source_manager = SourceManager()
        summary = source_manager.get_summary()
        
        # Summary info
        console.print("[bold]Sources Summary[/bold]")
        console.print(f"Total sources: {summary['total_sources']}")
        console.print(f"Available: {summary['available_sources']}")
        console.print(f"Types: {', '.join(summary['source_types'])}")
        
        # Database stats
        db_stats = summary['database_stats']
        console.print("\n[bold]Database Stats[/bold]")
        console.print(f"Artists: {db_stats.get('artists', 0):,}")
        console.print(f"Albums: {db_stats.get('albums', 0):,}")
        console.print(f"Tracks: {db_stats.get('tracks', 0):,}")
        console.print(f"Available tracks: {db_stats.get('available_tracks', 0):,}")
        
        if db_stats.get('tracks', 0) > 0:
            coverage = db_stats.get('coverage_percent', 0)
            console.print(f"Coverage: {coverage:.1f}%")
        
        # Sources table
        console.print("\n[bold]Source Details[/bold]")
        table = Table(show_header=True)
        table.add_column("Name")
        table.add_column("Type") 
        table.add_column("Status")
        table.add_column("Error")
        
        for source_status in summary['sources']:
            status_icon = "✅" if source_status.available else "❌"
            status_text = f"{status_icon} {'Available' if source_status.available else 'Unavailable'}"
            error_text = source_status.error_message or ""
            
            table.add_row(
                source_status.name,
                source_status.type,
                status_text,
                error_text
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to get source status: {e}")


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
def export(ctx: click.Context, output_format: str, output: str) -> None:
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


@database.command()
@click.argument("query")
@click.option("--type", type=click.Choice(["track", "album", "artist"]), help="Search in specific entity type")
@click.option("--limit", default=20, help="Maximum number of results")
@click.pass_context
def search(ctx: click.Context, query: str, type: str = None, limit: int = 20) -> None:
    """Search for tracks, albums, or artists."""
    from rich.console import Console
    from rich.table import Table
    from linernodes.backend.database.models import DatabaseManager
    
    console = Console()
    
    try:
        db_manager = DatabaseManager()
        
        if type == "track" or type is None:
            tracks = db_manager.search_music(query, limit=limit)
            if tracks:
                table = Table(title=f"Track Search Results for '{query}'")
                table.add_column("Title", style="cyan")
                table.add_column("Artist", style="magenta")
                table.add_column("Album", style="yellow")
                table.add_column("Duration", style="dim")
                
                for track in tracks:
                    table.add_row(
                        track.title,
                        track.artist_credit or "Unknown",
                        track.album_title or "Unknown",
                        track.duration_formatted or "Unknown"
                    )
                console.print(table)
        
        if type == "album" or type is None:
            albums = db_manager.get_all_albums(limit=limit)
            # Simple search filter for albums
            matching_albums = [a for a in albums if query.lower() in a.title.lower()][:limit]
            if matching_albums:
                table = Table(title=f"Album Search Results for '{query}'")
                table.add_column("Title", style="cyan")
                table.add_column("Artist", style="magenta")
                table.add_column("Tracks", style="dim")
                
                for album in matching_albums:
                    track_count = len(db_manager.get_album_tracks(album.id))
                    table.add_row(
                        album.title,
                        album.artist_credit or "Unknown",
                        str(track_count)
                    )
                console.print(table)
        
        if type == "artist" or type is None:
            # Get unique artists from tracks
            artists = db_manager.get_unique_artists()
            matching_artists = [a for a in artists if query.lower() in a.lower()][:limit]
            if matching_artists:
                table = Table(title=f"Artist Search Results for '{query}'")
                table.add_column("Artist", style="magenta")
                
                for artist in matching_artists:
                    table.add_row(artist)
                console.print(table)
        
    except Exception as e:
        console.print(f"[red]✗[/red] Search failed: {e}")
