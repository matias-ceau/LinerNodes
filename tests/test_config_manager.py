import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import yaml

from src.linernodes.config.config_manager import ConfigManager


class TestConfigManager:
    """Test suite for ConfigManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "linernodes" / "config.yaml"
        
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch.dict('os.environ', {'XDG_CONFIG_HOME': ''})
    @patch('pathlib.Path.home')
    def test_config_path_default(self, mock_home):
        """Test default config path when XDG_CONFIG_HOME is not set."""
        mock_home.return_value = Path(self.temp_dir)
        
        config_manager = ConfigManager()
        expected_path = Path(self.temp_dir) / ".config" / "linernodes" / "config.yaml"
        assert config_manager.config_file == expected_path
    
    def test_config_path_xdg(self):
        """Test config path when XDG_CONFIG_HOME is set."""
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': self.temp_dir}):
            config_manager = ConfigManager()
            expected_path = Path(self.temp_dir) / "linernodes" / "config.yaml"
            assert config_manager.config_file == expected_path
    
    def test_create_default_config(self):
        """Test creation of default configuration."""
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': self.temp_dir}):
            config_manager = ConfigManager()
            
            # Check that config file was created
            assert config_manager.config_file.exists()
            
            # Check default config structure
            assert "mpd" in config_manager.config
            assert "audio" in config_manager.config
            assert config_manager.config["mpd"]["host"] == "localhost"
            assert config_manager.config["mpd"]["port"] == 6600
    
    def test_get_all(self):
        """Test get_all method."""
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': self.temp_dir}):
            config_manager = ConfigManager()
            all_config = config_manager.get_all()
            
            assert isinstance(all_config, dict)
            assert "mpd" in all_config
            assert "audio" in all_config
    
    def test_get_section_key(self):
        """Test get method with section and key."""
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': self.temp_dir}):
            config_manager = ConfigManager()
            
            # Test existing values
            assert config_manager.get("mpd", "host") == "localhost"
            assert config_manager.get("mpd", "port") == 6600
            
            # Test default values
            assert config_manager.get("mpd", "nonexistent", "default") == "default"
            assert config_manager.get("nonexistent", "key", "default") == "default"
    
    def test_set_and_save(self):
        """Test set method and configuration persistence."""
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': self.temp_dir}):
            config_manager = ConfigManager()
            
            # Set new value
            config_manager.set("mpd", "test_key", "test_value")
            assert config_manager.get("mpd", "test_key") == "test_value"
            
            # Set new section
            config_manager.set("new_section", "new_key", "new_value")
            assert config_manager.get("new_section", "new_key") == "new_value"
            
            # Check persistence by creating new instance
            config_manager2 = ConfigManager()
            assert config_manager2.get("mpd", "test_key") == "test_value"
            assert config_manager2.get("new_section", "new_key") == "new_value"
    
    def test_load_existing_config(self):
        """Test loading existing configuration file."""
        # Create config file manually
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        test_config = {
            "mpd": {"host": "testhost", "port": 1234},
            "custom": {"key": "value"}
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': self.temp_dir}):
            config_manager = ConfigManager()
            
            assert config_manager.get("mpd", "host") == "testhost"
            assert config_manager.get("mpd", "port") == 1234
            assert config_manager.get("custom", "key") == "value"
    
    def test_invalid_yaml_handling(self):
        """Test handling of invalid YAML configuration."""
        # Create invalid YAML file
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with patch.dict('os.environ', {'XDG_CONFIG_HOME': self.temp_dir}):
            # Should handle gracefully and create default config
            with pytest.raises(yaml.YAMLError):
                ConfigManager()