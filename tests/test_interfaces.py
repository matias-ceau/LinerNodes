import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Test the interface modules - we'll mock external dependencies


class TestMCPServer:
    """Test MCP server interface."""
    
    @patch('src.linernodes.interfaces.mcp_server.MpdController')
    def test_get_player_status_no_song(self, mock_controller_class):
        """Test player status when no song is playing."""
        from src.linernodes.interfaces.mcp_server import get_player_status
        
        # Mock controller
        mock_controller = Mock()
        mock_controller.get_current_song.return_value = None
        mock_controller_class.return_value = mock_controller
        
        status = get_player_status()
        
        assert status.state == "stop"
        assert status.current_track is None
    
    @patch('src.linernodes.interfaces.mcp_server.MpdController')
    def test_get_player_status_with_song(self, mock_controller_class):
        """Test player status with current song."""
        from src.linernodes.interfaces.mcp_server import get_player_status
        
        # Mock controller and current song
        mock_controller = Mock()
        mock_song = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album',
            'time': '240',
            'file': 'test.mp3'
        }
        mock_controller.get_current_song.return_value = mock_song
        mock_controller.client.status.return_value = {
            'state': 'play',
            'volume': '85',
            'time': '1:23'
        }
        mock_controller_class.return_value = mock_controller
        
        status = get_player_status()
        
        assert status.state == "play"
        assert status.volume == 85
        assert status.current_track.title == "Test Song"
        assert status.current_track.artist == "Test Artist"
    
    @patch('src.linernodes.interfaces.mcp_server.MpdController')
    def test_player_play(self, mock_controller_class):
        """Test play command."""
        from src.linernodes.interfaces.mcp_server import player_play
        
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        
        result = player_play()
        
        mock_controller.play.assert_called_once()
        assert result == "Playback started"
    
    @patch('src.linernodes.interfaces.mcp_server.MpdController')
    def test_player_play_error(self, mock_controller_class):
        """Test play command with error."""
        from src.linernodes.interfaces.mcp_server import player_play
        
        mock_controller = Mock()
        mock_controller.play.side_effect = Exception("Test error")
        mock_controller_class.return_value = mock_controller
        
        result = player_play()
        
        assert "Error: Test error" in result


class TestWebInterface:
    """Test web interface components."""
    
    @patch('src.linernodes.interfaces.web.MpdController')
    @patch('src.linernodes.interfaces.web.ConfigManager')
    def test_web_interface_init(self, mock_config_class, mock_controller_class):
        """Test web interface initialization."""
        from src.linernodes.interfaces.web import WebInterface
        
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        # Test successful initialization
        mock_controller_class.return_value = Mock()
        web = WebInterface()
        assert web.controller is not None
        
        # Test initialization with controller error
        mock_controller_class.side_effect = Exception("Connection failed")
        web = WebInterface()
        assert web.controller is None
    
    @patch('src.linernodes.interfaces.web.MpdController')
    def test_get_player_status_success(self, mock_controller_class):
        """Test getting player status successfully."""
        from src.linernodes.interfaces.web import WebInterface
        
        mock_controller = Mock()
        mock_controller.client.status.return_value = {'state': 'play', 'volume': '70'}
        mock_controller.get_current_song.return_value = {'title': 'Test', 'artist': 'Artist'}
        mock_controller_class.return_value = mock_controller
        
        web = WebInterface()
        status = web.get_player_status()
        
        assert status['state'] == 'play'
        assert status['volume'] == 70
        assert status['current_song']['title'] == 'Test'
    
    @patch('src.linernodes.interfaces.web.MpdController')
    def test_get_player_status_no_controller(self, mock_controller_class):
        """Test getting player status without controller."""
        from src.linernodes.interfaces.web import WebInterface
        
        mock_controller_class.side_effect = Exception("No connection")
        web = WebInterface()
        status = web.get_player_status()
        
        assert status['state'] == 'disconnected'
        assert status['current_song'] is None


class TestTUIInterface:
    """Test TUI interface components."""
    
    @patch('src.linernodes.interfaces.tui.MpdController')
    def test_music_player_tui_init(self, mock_controller_class):
        """Test TUI initialization."""
        from src.linernodes.interfaces.tui import MusicPlayerTUI
        
        app = MusicPlayerTUI()
        assert app.controller is None  # Initially None
        assert app.status_widget is None
    
    @patch('src.linernodes.interfaces.tui.MpdController')
    def test_tui_actions_without_controller(self, mock_controller_class):
        """Test TUI actions when controller is not available."""
        from src.linernodes.interfaces.tui import MusicPlayerTUI
        
        app = MusicPlayerTUI()
        app.controller = None
        
        # These should handle gracefully
        app.action_toggle_play()
        app.action_next_track()
        app.action_prev_track()
        app.action_stop_playback()


class TestGraphExplorer:
    """Test graph explorer interface."""
    
    @patch('src.linernodes.interfaces.graph_explorer.KnowledgeGraphDB')
    @patch('src.linernodes.interfaces.graph_explorer.MarkdownCardGenerator')
    def test_graph_explorer_init(self, mock_card_gen, mock_kg_db):
        """Test graph explorer initialization."""
        from src.linernodes.interfaces.graph_explorer import GraphExplorer
        
        explorer = GraphExplorer()
        assert explorer.kg_db is not None
        assert explorer.card_generator is not None
        mock_kg_db.assert_called_once()
        mock_card_gen.assert_called_once()
    
    @patch('networkx.Graph')
    def test_build_networkx_graph_empty(self, mock_graph):
        """Test building NetworkX graph with no entities."""
        from src.linernodes.interfaces.graph_explorer import GraphExplorer
        from src.linernodes.knowledge_graph.models import EntityType
        
        # Mock empty graph
        mock_g = Mock()
        mock_g.number_of_nodes.return_value = 0
        mock_graph.return_value = mock_g
        
        with patch('src.linernodes.interfaces.graph_explorer.KnowledgeGraphDB'):
            explorer = GraphExplorer()
            result = explorer.build_networkx_graph([EntityType.ALBUM], 100, 2)
            
            # Should return the mocked graph
            assert result is not None


class TestMarkdownCardIntegration:
    """Integration tests for markdown card generation."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from src.linernodes.knowledge_graph.markdown_cards import MarkdownCardGenerator
        
        generator = MarkdownCardGenerator()
        
        # Test various problematic characters
        test_cases = [
            ("Normal Name", "Normal Name"),
            ("Name/With/Slashes", "Name-With-Slashes"),
            ("Name:With:Colons", "Name-With-Colons"),
            ("Name?With?Questions", "NameWithQuestions"),
            ("Name*With*Stars", "NameWithStars"),
            ("Name|With|Pipes", "Name-With-Pipes"),
            ('Name"With"Quotes', "NameWithQuotes"),
            ("Name<With>Brackets", "NameWithBrackets"),
        ]
        
        for input_name, expected in test_cases:
            result = generator._sanitize_filename(input_name)
            assert result == expected
    
    def test_format_duration(self):
        """Test duration formatting."""
        from src.linernodes.knowledge_graph.markdown_cards import MarkdownCardGenerator
        
        generator = MarkdownCardGenerator()
        
        test_cases = [
            (0, "00:00"),
            (30000, "00:30"),  # 30 seconds
            (60000, "01:00"),  # 1 minute
            (90000, "01:30"),  # 1 minute 30 seconds
            (240000, "04:00"), # 4 minutes
            (3661000, "61:01"), # 61 minutes 1 second
        ]
        
        for input_ms, expected in test_cases:
            result = generator._format_duration(input_ms)
            assert result == expected


@pytest.fixture
def mock_streamlit():
    """Mock streamlit for testing."""
    with patch.multiple(
        'streamlit',
        set_page_config=Mock(),
        title=Mock(),
        markdown=Mock(),
        success=Mock(),
        error=Mock(),
        info=Mock(),
        warning=Mock(),
        columns=Mock(return_value=[Mock(), Mock(), Mock()]),
        button=Mock(return_value=False),
        slider=Mock(return_value=50),
        selectbox=Mock(return_value="option1"),
        text_input=Mock(return_value=""),
        checkbox=Mock(return_value=True),
        subheader=Mock(),
        metric=Mock(),
        caption=Mock(),
        divider=Mock(),
        tabs=Mock(return_value=[Mock(), Mock(), Mock()]),
        rerun=Mock(),
    ):
        yield


class TestStreamlitIntegration:
    """Test streamlit integration aspects."""
    
    def test_mock_streamlit_functions(self, mock_streamlit):
        """Test that streamlit functions are properly mocked."""
        import streamlit as st
        
        st.title("Test")
        st.success("Success")
        st.error("Error")
        
        # Should not raise any errors
        cols = st.columns(3)
        assert len(cols) == 3