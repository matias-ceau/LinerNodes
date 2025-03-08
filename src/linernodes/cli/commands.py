import click
import os
from xdg import xdg_config_home

from linernodes.backend.mpd_client import MPDController
from linernodes.config.config_manager import ConfigManager


@click.group()
@click.option(
    "--use-system-mpd/--use-custom-mpd",
    default=None,
    help="Use system MPD instance or create a custom LinerNodes MPD instance",
)
@click.option(
    "--use-custom-config",
    is_flag=True,
    help="Use configuration from config.toml file",
)
@click.pass_context
def cli(ctx, use_system_mpd, use_custom_config):
    """LinerNodes CLI - MPD music player interface."""
    # Store the options in the context for use in subcommands
    ctx.ensure_object(dict)
    
    # Load config
    config = ConfigManager()
    
    # Precedence: CLI option > config file > default (system MPD)
    if use_system_mpd is not None:
        # CLI option provided explicitly
        ctx.obj["use_custom_config"] = not use_system_mpd
    elif use_custom_config:
        # Use value from config file
        ctx.obj["use_custom_config"] = config.get("mpd", "use_custom_config", False)
    else:
        # Default to system MPD
        ctx.obj["use_custom_config"] = False
    
    # Store references to config
    ctx.obj["config"] = config
    
    # Show MPD config location if using custom config
    if ctx.obj["use_custom_config"]:
        mpd_config_path = os.path.join(xdg_config_home(), "linernodes", "mpd.conf")
        if os.path.exists(mpd_config_path):
            click.echo(f"Using custom MPD config: {mpd_config_path}")


@cli.command()
@click.pass_context
def play(ctx):
    """Start playing music."""
    controller = MPDController(use_custom_config=ctx.obj["use_custom_config"])
    controller.play()
    click.echo("Music started playing.")


@cli.command()
@click.pass_context
def pause(ctx):
    """Pause music playback."""
    controller = MPDController(use_custom_config=ctx.obj["use_custom_config"])
    controller.pause()
    click.echo("Music paused.")


@cli.command()
@click.argument("file_path")
@click.pass_context
def add(ctx, file_path):
    """Add a file to the playlist."""
    controller = MPDController(use_custom_config=ctx.obj["use_custom_config"])
    controller.add_to_playlist(file_path)
    click.echo(f"Added {file_path} to the playlist.")


@cli.command()
@click.pass_context
def current(ctx):
    """Show current playing song."""
    controller = MPDController(use_custom_config=ctx.obj["use_custom_config"])
    song = controller.get_current_song()
    click.echo(
        f"Now playing: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}"
    )


@cli.command()
@click.pass_context
def generate_config(ctx):
    """Generate a custom MPD configuration file."""
    controller = MPDController(use_custom_config=True)
    config_path = controller.mpd_config_file
    click.echo(f"Custom MPD configuration generated at: {config_path}")
    click.echo("You can now use LinerNodes with --use-custom-mpd flag.")


@cli.command()
@click.pass_context
def restart_mpd(ctx):
    """Restart the custom MPD instance."""
    controller = MPDController(use_custom_config=True)
    controller._ensure_mpd_running()
    click.echo("Custom MPD instance restarted.")
    click.echo(f"Using music directory: {controller.music_dir}")
    click.echo(f"Using socket: {controller.custom_socket}")


@cli.group()
@click.pass_context
def config(ctx):
    """Manage LinerNodes configuration."""
    pass


@config.command(name="set")
@click.argument("section")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx, section, key, value):
    """Set a configuration value.
    
    Example: linernodes config set mpd use_custom_config true
    """
    # Get the config manager from context
    config_manager = ctx.obj["config"]
    
    # Convert string values to appropriate types
    if value.lower() == "true":
        value = True
    elif value.lower() == "false":
        value = False
    elif value.isdigit():
        value = int(value)
    
    # Set the value
    config_manager.set(section, key, value)
    click.echo(f"Configuration updated: {section}.{key} = {value}")


@config.command(name="get")
@click.argument("section", required=False)
@click.argument("key", required=False)
@click.pass_context
def config_get(ctx, section, key):
    """Get configuration values.
    
    Examples:
    - linernodes config get                 (show all config)
    - linernodes config get mpd             (show mpd section)
    - linernodes config get mpd music_dir   (show specific value)
    """
    # Get the config manager from context
    config_manager = ctx.obj["config"]
    
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


@config.command(name="set-default")
@click.option("--custom-mpd/--system-mpd", required=True, help="Which MPD to use by default")
@click.pass_context
def set_default_mpd(ctx, custom_mpd):
    """Set whether to use custom MPD by default."""
    # Get the config manager from context
    config_manager = ctx.obj["config"]
    
    # Set the value
    config_manager.set("mpd", "use_custom_config", custom_mpd)
    
    if custom_mpd:
        click.echo("Default set to use custom MPD installation.")
        click.echo("You can now use 'linernodes' without the --use-custom-mpd flag.")
    else:
        click.echo("Default set to use system MPD installation.")
