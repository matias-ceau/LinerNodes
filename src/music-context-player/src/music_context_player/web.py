import streamlit as st
import subprocess
from pathlib import Path

st.set_page_config(
    page_title="Music Context Player",
    page_icon="🎵",
    layout="wide"
)

st.title("🎵 Music Context Player")

st.sidebar.header("Controls")

# MPD Status
if st.sidebar.button("Check MPD Status"):
    try:
        result = subprocess.run(["systemctl", "--user", "status", "mpd"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            st.sidebar.success("MPD is running")
        else:
            st.sidebar.error("MPD is not running")
    except Exception as e:
        st.sidebar.error(f"Error checking MPD: {e}")

# Music library info
st.header("Music Library")
music_dir = Path("/mnt/hdd4t/MEGA/UnifiedLibrary/music/")
if music_dir.exists():
    st.success(f"Music library found at: {music_dir}")
    # Could add library browsing functionality here
else:
    st.error(f"Music library not found at: {music_dir}")

# Placeholder for player controls
st.header("Player Controls")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("⏮️ Previous"):
        st.info("Previous track (not implemented)")

with col2:
    if st.button("⏯️ Play/Pause"):
        st.info("Play/Pause (not implemented)")

with col3:
    if st.button("⏭️ Next"):
        st.info("Next track (not implemented)")

with col4:
    if st.button("⏹️ Stop"):
        st.info("Stop (not implemented)")

# Placeholder for playlist/queue
st.header("Current Queue")
st.info("Queue display not yet implemented")

# Placeholder for library browser
st.header("Music Library Browser")
st.info("Library browser not yet implemented")