import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
import tempfile
import shutil
from pathlib import Path

from src.linernodes.cli.commands import cli


class TestCLICommands:
    """Test CLI command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test main CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "LinerNodes CLI" in result.output
        assert "interface" in result.output
        assert "mpd" in result.output
        assert "knowledge" in result.output
    
    def test_interface_help(self):
        """Test interface subcommand help."""
        result = self.runner.invoke(cli, ['interface', '--help'])
        assert result.exit_code == 0
        assert "Launch different LinerNodes interfaces" in result.output
        assert "tui" in result.output
        assert "web" in result.output
        assert "mcp" in result.output
        assert "graph" in result.output
    
    def test_mpd_help(self):
        """Test MPD subcommand help."""
        result = self.runner.invoke(cli, ['mpd', '--help'])
        assert result.exit_code == 0
        assert "MPD server management" in result.output
        assert "setup" in result.output
        assert "status" in result.output
    
    def test_knowledge_help(self):
        """Test knowledge subcommand help."""
        result = self.runner.invoke(cli, ['knowledge', '--help'])
        assert result.exit_code == 0
        assert "Manage the music knowledge graph" in result.output
        assert "import-release" in result.output
        assert "search" in result.output
        assert "stats" in result.output
    
    @patch('src.linernodes.cli.commands.ConfigManager')
    def test_config_get_all(self, mock_config_class):
        """Test config get command without arguments."""
        mock_config = Mock()
        mock_config.get_all.return_value = {
            "mpd": {"host": "localhost", "port": 6600},
            "audio": {"volume": 70}
        }
        mock_config_class.return_value = mock_config
        
        result = self.runner.invoke(cli, ['config', 'get'])
        assert result.exit_code == 0
        assert "Current configuration" in result.output
        assert "localhost" in result.output
        assert "6600" in result.output
    
    @patch('src.linernodes.cli.commands.ConfigManager')
    def test_config_get_section(self, mock_config_class):
        """Test config get command with section."""
        mock_config = Mock()
        mock_config.get_all.return_value = {
            "mpd": {"host": "localhost", "port": 6600}
        }
        mock_config_class.return_value = mock_config
        
        result = self.runner.invoke(cli, ['config', 'get', 'mpd'])
        assert result.exit_code == 0
        assert "[mpd]" in result.output
        assert "localhost" in result.output
    
    @patch('src.linernodes.cli.commands.ConfigManager')
    def test_config_get_key(self, mock_config_class):
        """Test config get command with section and key."""
        mock_config = Mock()
        mock_config.get.return_value = "localhost"
        mock_config_class.return_value = mock_config
        
        result = self.runner.invoke(cli, ['config', 'get', 'mpd', 'host'])
        assert result.exit_code == 0
        assert "mpd.host = localhost" in result.output
    
    @patch('src.linernodes.cli.commands.ConfigManager')
    def test_config_set(self, mock_config_class):
        """Test config set command."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        result = self.runner.invoke(cli, ['config', 'set', 'mpd', 'host', 'newhost'])
        assert result.exit_code == 0
        assert "Configuration updated: mpd.host = newhost" in result.output
        mock_config.set.assert_called_once_with('mpd', 'host', 'newhost')
    
    @patch('src.linernodes.cli.commands.ConfigManager')
    def test_config_set_boolean(self, mock_config_class):
        """Test config set command with boolean values."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        # Test true
        result = self.runner.invoke(cli, ['config', 'set', 'audio', 'random', 'true'])
        assert result.exit_code == 0
        mock_config.set.assert_called_with('audio', 'random', True)
        
        # Test false
        result = self.runner.invoke(cli, ['config', 'set', 'audio', 'repeat', 'false'])
        assert result.exit_code == 0
        mock_config.set.assert_called_with('audio', 'repeat', False)
    
    @patch('src.linernodes.cli.commands.ConfigManager')
    def test_config_set_integer(self, mock_config_class):
        """Test config set command with integer values."""
        mock_config = Mock()
        mock_config_class.return_value = mock_config
        
        result = self.runner.invoke(cli, ['config', 'set', 'mpd', 'port', '7700'])
        assert result.exit_code == 0
        mock_config.set.assert_called_with('mpd', 'port', 7700)
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_play_command(self, mock_controller_class):
        """Test play command."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['play'])
        assert result.exit_code == 0
        assert "Music started playing" in result.output
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_pause_command(self, mock_controller_class):
        """Test pause command."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['pause'])
        assert result.exit_code == 0
        assert "Music paused" in result.output
        mock_controller.pause.assert_called_once()
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_current_command(self, mock_controller_class):
        """Test current song command."""
        mock_controller = Mock()
        mock_controller.get_current_song.return_value = {
            'title': 'Test Song',
            'artist': 'Test Artist'
        }
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['current'])
        assert result.exit_code == 0
        assert "Now playing: Test Song by Test Artist" in result.output
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_add_command(self, mock_controller_class):
        """Test add to playlist command."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['add', 'test.mp3'])
        assert result.exit_code == 0
        assert "Added test.mp3 to the playlist" in result.output
        mock_controller.add_to_playlist.assert_called_once_with('test.mp3')


class TestMPDCommands:
    """Test MPD management commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_mpd_setup_success(self, mock_controller_class):
        """Test successful MPD setup."""
        mock_controller = Mock()
        mock_controller.mpd_config_file = Path("/test/mpd.conf")
        mock_controller.music_dir = "/test/music"
        mock_controller.custom_socket = "/test/mpd.socket"
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['mpd', 'setup'])
        assert result.exit_code == 0
        assert "Setting up MPD configuration" in result.output
        assert "Setup complete!" in result.output
        mock_controller._generate_mpd_config.assert_called_once()
        mock_controller._ensure_mpd_running.assert_called_once()
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_mpd_setup_failure(self, mock_controller_class):
        """Test MPD setup failure."""
        mock_controller_class.side_effect = Exception("Setup failed")
        
        result = self.runner.invoke(cli, ['mpd', 'setup'])
        assert result.exit_code == 0  # CLI handles exceptions gracefully
        assert "Setup failed: Setup failed" in result.output
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_mpd_status_success(self, mock_controller_class):
        """Test successful MPD status check."""
        mock_controller = Mock()
        mock_controller.client.status.return_value = {
            'state': 'play',
            'volume': '85'
        }
        mock_controller.get_current_song.return_value = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album'
        }
        mock_controller_class.return_value = mock_controller
        
        result = self.runner.invoke(cli, ['mpd', 'status'])
        assert result.exit_code == 0
        assert "Connected" in result.output
        assert "Play" in result.output
        assert "85%" in result.output
        assert "Test Song" in result.output
    
    @patch('src.linernodes.cli.commands.MpdController')
    def test_mpd_status_failure(self, mock_controller_class):
        """Test MPD status check failure."""
        mock_controller_class.side_effect = Exception("Connection failed")
        
        result = self.runner.invoke(cli, ['mpd', 'status'])
        assert result.exit_code == 0
        assert "Failed to connect to MPD" in result.output
        assert "Try running: linernodes mpd setup" in result.output


class TestKnowledgeCommands:
    """Test knowledge graph management commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('src.linernodes.cli.commands.KnowledgeGraphDB')
    @patch('src.linernodes.cli.commands.MusicBrainzIntegration')
    def test_import_release_success(self, mock_mb_integration_class, mock_kg_db_class):
        """Test successful release import."""
        # Mock successful import
        mock_integration = Mock()
        mock_album = Mock()
        mock_album.artist_credit = "Test Artist"
        mock_album.name = "Test Album"
        mock_integration.search_and_import_release.return_value = [mock_album]
        mock_mb_integration_class.return_value = mock_integration
        
        result = self.runner.invoke(cli, ['knowledge', 'import-release', 'test query'])
        assert result.exit_code == 0
        assert "Searching MusicBrainz for: test query" in result.output
        assert "Imported 1 albums" in result.output
        assert "Test Artist - Test Album" in result.output
    
    @patch('src.linernodes.cli.commands.KnowledgeGraphDB')
    @patch('src.linernodes.cli.commands.MusicBrainzIntegration')
    def test_import_release_failure(self, mock_mb_integration_class, mock_kg_db_class):
        """Test release import failure."""
        mock_integration = Mock()
        mock_integration.search_and_import_release.side_effect = Exception("Import failed")
        mock_mb_integration_class.return_value = mock_integration
        
        result = self.runner.invoke(cli, ['knowledge', 'import-release', 'test query'])
        assert result.exit_code == 0
        assert "Import failed: Import failed" in result.output
    
    @patch('src.linernodes.cli.commands.KnowledgeGraphDB')
    def test_knowledge_stats(self, mock_kg_db_class):
        """Test knowledge graph statistics."""
        mock_db = Mock()
        mock_db.conn.execute.return_value.fetchone.side_effect = [
            [5],  # albums
            [3],  # artists  
            [2],  # persons
            [4],  # genres
            [1],  # labels
            [15], # recordings
            [0],  # works
            [25]  # relationships
        ]
        mock_kg_db_class.return_value = mock_db
        
        result = self.runner.invoke(cli, ['knowledge', 'stats'])
        assert result.exit_code == 0
        assert "Knowledge Graph Statistics" in result.output
        assert "Album" in result.output and "5" in result.output
        assert "Artist" in result.output and "3" in result.output
        assert "Relationships" in result.output and "25" in result.output
    
    @patch('src.linernodes.cli.commands.KnowledgeGraphDB')
    def test_knowledge_search(self, mock_kg_db_class):
        """Test knowledge graph search."""
        mock_db = Mock()
        mock_entity = Mock()
        mock_entity.entity_type.value = "album"
        mock_entity.name = "Test Album"
        mock_entity.id = "12345678-1234-1234-1234-123456789012"
        mock_db.search_entities.return_value = [mock_entity]
        mock_kg_db_class.return_value = mock_db
        
        result = self.runner.invoke(cli, ['knowledge', 'search', 'test'])
        assert result.exit_code == 0
        assert "Search Results for 'test'" in result.output
        assert "Album" in result.output
        assert "Test Album" in result.output
    
    @patch('src.linernodes.cli.commands.KnowledgeGraphDB')
    def test_knowledge_search_no_results(self, mock_kg_db_class):
        """Test knowledge graph search with no results."""
        mock_db = Mock()
        mock_db.search_entities.return_value = []
        mock_kg_db_class.return_value = mock_db
        
        result = self.runner.invoke(cli, ['knowledge', 'search', 'nonexistent'])
        assert result.exit_code == 0
        assert "No results found for: nonexistent" in result.output
    
    @patch('src.linernodes.cli.commands.KnowledgeGraphDB')
    @patch('src.linernodes.cli.commands.MarkdownCardGenerator')
    def test_knowledge_show(self, mock_card_gen_class, mock_kg_db_class):
        """Test showing entity details."""
        # Mock entity
        mock_entity = Mock()
        mock_entity.name = "Test Album"
        mock_entity.entity_type.value = "album"
        mock_entity.id = "test-id"
        mock_entity.mbid = "test-mbid"
        
        # Mock database
        mock_db = Mock()
        mock_db.get_entity.return_value = mock_entity
        mock_db.get_relationships.return_value = []
        mock_kg_db_class.return_value = mock_db
        
        # Mock card generator
        mock_card_gen = Mock()
        mock_card_gen.generate_card.return_value = Path("/test/card.md")
        mock_card_gen_class.return_value = mock_card_gen
        
        result = self.runner.invoke(cli, ['knowledge', 'show', 'test-id'])
        assert result.exit_code == 0
        assert "Test Album" in result.output
        assert "Album" in result.output
        assert "test-id" in result.output
        assert "test-mbid" in result.output
        assert "Generated: /test/card.md" in result.output
    
    @patch('src.linernodes.cli.commands.KnowledgeGraphDB')
    def test_knowledge_show_not_found(self, mock_kg_db_class):
        """Test showing non-existent entity."""
        mock_db = Mock()
        mock_db.get_entity.return_value = None
        mock_kg_db_class.return_value = mock_db
        
        result = self.runner.invoke(cli, ['knowledge', 'show', 'nonexistent'])
        assert result.exit_code == 0
        assert "Entity not found: nonexistent" in result.output


class TestInterfaceCommands:
    """Test interface launch commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    @patch('subprocess.run')
    def test_interface_web(self, mock_subprocess):
        """Test web interface launch."""
        result = self.runner.invoke(cli, ['interface', 'web'])
        assert result.exit_code == 0
        assert "Starting LinerNodes web interface" in result.output
        assert "Access at: http://localhost:8501" in result.output
        mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_interface_web_custom_port(self, mock_subprocess):
        """Test web interface launch with custom port."""
        result = self.runner.invoke(cli, ['interface', 'web', '--port', '9000'])
        assert result.exit_code == 0
        assert "port 9000" in result.output
        assert "localhost:9000" in result.output
    
    @patch('subprocess.run')
    def test_interface_graph(self, mock_subprocess):
        """Test graph explorer launch."""
        result = self.runner.invoke(cli, ['interface', 'graph'])
        assert result.exit_code == 0
        assert "knowledge graph explorer" in result.output
        assert "localhost:8502" in result.output
        mock_subprocess.assert_called_once()
    
    @patch('uvicorn.run')
    @patch('src.linernodes.cli.commands.create_app')
    def test_interface_mcp(self, mock_create_app, mock_uvicorn):
        """Test MCP server launch."""
        mock_app = Mock()
        mock_create_app.return_value = mock_app
        
        result = self.runner.invoke(cli, ['interface', 'mcp'])
        assert result.exit_code == 0
        assert "Starting LinerNodes MCP server" in result.output
        assert "0.0.0.0:8000" in result.output
        mock_uvicorn.assert_called_once_with(mock_app, host="0.0.0.0", port=8000)
    
    @patch('src.linernodes.cli.commands.run_tui')
    def test_interface_tui(self, mock_run_tui):
        """Test TUI launch."""
        result = self.runner.invoke(cli, ['interface', 'tui'])
        assert result.exit_code == 0
        assert "Starting LinerNodes TUI" in result.output
        mock_run_tui.assert_called_once()


@pytest.fixture
def temp_config_dir():
    """Provide a temporary config directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    @patch.dict('os.environ', {'XDG_CONFIG_HOME': ''})
    def test_cli_with_real_config(self, temp_config_dir):
        """Test CLI with real configuration (mocked paths)."""
        with patch('pathlib.Path.home', return_value=Path(temp_config_dir)):
            runner = CliRunner()
            
            # Test config creation and retrieval
            result = runner.invoke(cli, ['config', 'get'])
            assert result.exit_code == 0
            assert "mpd" in result.output
            
            # Test config setting
            result = runner.invoke(cli, ['config', 'set', 'mpd', 'host', 'testhost'])
            assert result.exit_code == 0
            
            # Verify the change
            result = runner.invoke(cli, ['config', 'get', 'mpd', 'host'])
            assert result.exit_code == 0
            assert "testhost" in result.output