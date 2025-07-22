import streamlit as st
from pathlib import Path
import time
import sys
from typing import Optional, Dict, Any

# Handle imports for both direct execution and package import
try:
    from ..backend.player.mpd_controller import MpdController
    from ..config.config_manager import ConfigManager
    from ..backend.database.models import DatabaseManager
except ImportError:
    # Handle direct execution by adding parent directory to path
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from linernodes.backend.player.mpd_controller import MpdController
    from linernodes.config.config_manager import ConfigManager
    from linernodes.backend.database.models import DatabaseManager

class WebInterface:
    """Streamlit web interface for LinerNodes music player."""
    
    def __init__(self):
        self.controller: Optional[MpdController] = None
        self.config = ConfigManager()
        self.db_manager = DatabaseManager()
        self.initialize_controller()
        
    def initialize_controller(self):
        """Initialize MPD controller with error handling."""
        try:
            self.controller = MpdController()
        except Exception as e:
            st.error(f"Failed to connect to MPD: {e}")
            self.controller = None

    def get_player_status(self) -> Dict[str, Any]:
        """Get current player status safely."""
        if not self.controller:
            return {"state": "disconnected", "current_song": None}
            
        try:
            status = self.controller.client.status()
            current_song = self.controller.get_current_song()
            return {
                "state": status.get('state', 'stop'),
                "volume": int(status.get('volume', 0)),
                "current_song": current_song
            }
        except Exception:
            return {"state": "error", "current_song": None}

    def render_header(self):
        """Render the page header."""
        st.set_page_config(
            page_title="LinerNodes Music Player",
            page_icon="🎵",
            layout="wide"
        )
        
        st.title("🎵 LinerNodes Music Player")
        st.markdown("**Modular MPD Web Interface**")

    def render_connection_status(self):
        """Show connection status."""
        if self.controller:
            st.success("✅ Connected to MPD")
        else:
            st.error("❌ Not connected to MPD")
            if st.button("Reconnect"):
                self.initialize_controller()
                st.rerun()

    def render_player_status(self):
        """Display current player status."""
        status = self.get_player_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            state_emoji = {"play": "▶️", "pause": "⏸️", "stop": "⏹️"}.get(status.get("state", "stop"), "❓")
            st.metric("Status", f"{state_emoji} {status.get('state', 'Unknown').title()}")
        
        with col2:
            st.metric("Volume", f"{status.get('volume', 0)}%")
            
        with col3:
            if status.get("current_song"):
                song = status["current_song"]
                title = song.get('title', 'Unknown')
                artist = song.get('artist', 'Unknown')
                st.metric("Current Track", f"{title}")
                st.caption(f"by {artist}")
            else:
                st.metric("Current Track", "None")

    def render_player_controls(self):
        """Render player control buttons."""
        if not self.controller:
            st.warning("MPD not connected - controls disabled")
            return
            
        st.subheader("Player Controls")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("⏮️ Previous", use_container_width=True):
                try:
                    self.controller.client.previous()
                    st.success("⏮️ Previous track")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col2:
            if st.button("⏯️ Play/Pause", use_container_width=True):
                try:
                    status = self.controller.client.status()
                    if status.get('state') == 'play':
                        self.controller.pause()
                        st.success("⏸️ Paused")
                    else:
                        self.controller.play()
                        st.success("▶️ Playing")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col3:
            if st.button("⏭️ Next", use_container_width=True):
                try:
                    self.controller.client.next()
                    st.success("⏭️ Next track")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col4:
            if st.button("⏹️ Stop", use_container_width=True):
                try:
                    self.controller.client.stop()
                    st.success("⏹️ Stopped")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col5:
            if st.button("🔄 Update DB", use_container_width=True):
                try:
                    self.controller.client.update()
                    st.success("🔄 Database update started")
                except Exception as e:
                    st.error(f"Error: {e}")

    def render_volume_control(self):
        """Render volume slider."""
        if not self.controller:
            return
            
        try:
            current_volume = int(self.controller.client.status().get('volume', 70))
            new_volume = st.slider("Volume", 0, 100, current_volume)
            
            if new_volume != current_volume:
                self.controller.client.setvol(new_volume)
                st.success(f"Volume set to {new_volume}%")
        except Exception as e:
            st.error(f"Volume control error: {e}")

    def render_playlist(self):
        """Display current playlist."""
        if not self.controller:
            return
            
        st.subheader("Current Playlist")
        
        try:
            playlist = self.controller.client.playlistinfo()
            if playlist:
                for i, song in enumerate(playlist):
                    title = song.get('title', 'Unknown')
                    artist = song.get('artist', 'Unknown')
                    album = song.get('album', 'Unknown')
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{i+1}.** {title} - {artist}")
                        st.caption(f"Album: {album}")
                    with col2:
                        if st.button("▶️", key=f"play_{i}"):
                            self.controller.client.play(i)
                            st.success(f"Playing track {i+1}")
                            st.rerun()
            else:
                st.info("Playlist is empty")
        except Exception as e:
            st.error(f"Playlist error: {e}")

    def render_music_library_info(self):
        """Display music library information."""
        st.subheader("Music Library")
        
        music_dir = self.config.get("mpd", "music_dir", "~/music")
        music_path = Path(music_dir).expanduser()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Location:** {music_path}")
            
        with col2:
            if music_path.exists():
                st.success("✅ Library found")
            else:
                st.error("❌ Library not found")

    def render_search(self):
        """Render music search functionality."""
        if not self.controller:
            return
            
        st.subheader("Search Music")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input("Search for music:", placeholder="Enter title, artist, or album...")
        
        with col2:
            search_type = st.selectbox("Search in:", ["any", "title", "artist", "album"])
        
        if search_query:
            try:
                results = self.controller.client.search(search_type, search_query)
                
                if results:
                    st.write(f"Found {len(results)} results:")
                    for song in results[:20]:  # Limit to first 20 results
                        title = song.get('title', 'Unknown')
                        artist = song.get('artist', 'Unknown')
                        file_path = song.get('file', '')
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{title}** - {artist}")
                            st.caption(file_path)
                        with col2:
                            if st.button("Add", key=f"add_{file_path}"):
                                self.controller.add_to_playlist(file_path)
                                st.success("Added to playlist")
                                st.rerun()
                else:
                    st.info("No results found")
            except Exception as e:
                st.error(f"Search error: {e}")

    def run(self):
        """Main method to render the complete interface."""
        self.render_header()
        
        # Auto-refresh every 5 seconds
        if st.checkbox("Auto-refresh", value=True):
            time.sleep(5)
            st.rerun()
        
        self.render_connection_status()
        
        if self.controller:
            self.render_player_status()
            
            st.divider()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                self.render_player_controls()
            
            with col2:
                self.render_volume_control()
            
            st.divider()
            
            tab1, tab2, tab3 = st.tabs(["Playlist", "Search", "Library"])
            
            with tab1:
                self.render_playlist()
            
            with tab2:
                self.render_search()
            
            with tab3:
                self.render_music_library_info()

def run_web():
    """Entry point to run the web interface."""
    web = WebInterface()
    web.run()

# Run the interface when script is executed directly
if __name__ == "__main__":
    run_web()