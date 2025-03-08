import click
from typing import Any, Optional

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


@cli.command()
@click.pass_context
def play(ctx: click.Context) -> None:
    """Start playing music."""
    controller = MpdController(...)  # Pass the appropriate MPDConfig instance
    controller.client.play()  # Adjust method call if needed
    click.echo("Music started playing.")


@cli.command()
@click.pass_context
def pause(ctx: click.Context) -> None:
    """Pause music playback."""
    controller = MpdController()
    controller.pause()
    click.echo("Music paused.")


@cli.command()
@click.argument("file_path")
@click.pass_context
def add(ctx: click.Context, file_path: str) -> None:
    """Add a file to the playlist."""
    controller = MpdController()
    controller.add_to_playlist(file_path)
    click.echo(f"Added {file_path} to the playlist.")


@cli.command()
@click.pass_context
def current(ctx: click.Context) -> None:
    """Show current playing song."""
    controller = MpdController()
    song = controller.get_current_song()
    click.echo(
        f"Now playing: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}"
    )


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
