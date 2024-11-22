import click

from linernodes.backend.mpd_client import MPDController


@click.group()
def cli():
    pass


@cli.command()
def play():
    """Start playing music."""
    controller = MPDController()
    controller.play()
    click.echo("Music started playing.")


@cli.command()
def pause():
    """Pause music playback."""
    controller = MPDController()
    controller.pause()
    click.echo("Music paused.")


@cli.command()
@click.argument("file_path")
def add(file_path):
    """Add a file to the playlist."""
    controller = MPDController()
    controller.add_to_playlist(file_path)
    click.echo(f"Added {file_path} to the playlist.")


@cli.command()
def current():
    """Show current playing song."""
    controller = MPDController()
    song = controller.get_current_song()
    click.echo(
        f"Now playing: {song.get('title', 'Unknown')} by {song.get('artist', 'Unknown')}"
    )
