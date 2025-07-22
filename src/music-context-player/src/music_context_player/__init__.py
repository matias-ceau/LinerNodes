import click
from fastmcp import FastMCP
from rich.console import Console
from textual.app import App

console = Console()

@click.group()
@click.version_option()
def main():
    """Music Context Player - A CLI/TUI/Web music player with MPD integration"""
    pass

@main.group()
def mpd():
    """MPD server management commands"""
    pass

@mpd.command()
def setup():
    """Setup MPD configuration and service"""
    import os
    import subprocess
    from pathlib import Path
    
    console.print("[bold green]Setting up MPD configuration...[/bold green]")
    
    # Create MPD directories
    mpd_dir = Path.home() / ".mpd"
    config_dir = Path.home() / ".config" / "mpd"
    
    mpd_dir.mkdir(exist_ok=True)
    (mpd_dir / "playlists").mkdir(exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # MPD configuration
    mpd_config = '''music_directory "/mnt/hdd4t/MEGA/UnifiedLibrary/music/"
playlist_directory "~/.mpd/playlists"
db_file "~/.mpd/database"
log_file "~/.mpd/log"
pid_file "~/.mpd/pid"
state_file "~/.mpd/state"
sticker_file "~/.mpd/sticker.sql"

user "matias"
bind_to_address "localhost"
port "6600"

input {
    plugin "curl"
}

audio_output {
    type "pulse"
    name "pulse audio"
}

audio_output {
    type "fifo"
    name "my_fifo"
    path "/tmp/mpd.fifo"
    format "44100:16:2"
}

decoder {
    plugin "hybrid_dsd"
    enabled "no"
}

replaygain "auto"
volume_normalization "yes"'''
    
    # Write configuration
    config_file = config_dir / "mpd.conf"
    config_file.write_text(mpd_config)
    
    console.print(f"[green]✓[/green] Created MPD configuration at {config_file}")
    
    # Create systemd service
    systemd_dir = Path.home() / ".config" / "systemd" / "user"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    
    service_content = '''[Unit]
Description=Music Player Daemon
Documentation=man:mpd(1) man:mpd.conf(5)
After=network.target sound.target

[Service]
Type=notify
ExecStart=/usr/bin/mpd --no-daemon ~/.config/mpd/mpd.conf
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target'''
    
    service_file = systemd_dir / "mpd.service"
    service_file.write_text(service_content)
    
    console.print(f"[green]✓[/green] Created systemd service at {service_file}")
    
    # Enable and start service
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "mpd"], check=True)
        subprocess.run(["systemctl", "--user", "start", "mpd"], check=True)
        console.print("[green]✓[/green] MPD service enabled and started")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗[/red] Failed to enable/start MPD service: {e}")
    
    console.print("\n[bold]Setup complete![/bold]")
    console.print("Use 'mpc update' to update the music database")

@main.command()
def tui():
    """Launch the Textual TUI interface"""
    from .tui import MusicPlayerApp
    app = MusicPlayerApp()
    app.run()

@main.command()
def web():
    """Launch the Streamlit web interface"""
    import subprocess
    subprocess.run(["streamlit", "run", "src/music_context_player/web.py"])

@main.command()
def server():
    """Start the FastMCP server"""
    from .server import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
