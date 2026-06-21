"""Configuration loader and management."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable overrides.
    
    Args:
        config_path: Path to config.yaml. If None, uses ./config.yaml
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file not found
        yaml.YAMLError: If config file is invalid YAML
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    # Apply environment variable overrides
    config = _apply_env_overrides(config)
    
    return config


def _apply_env_overrides(config: Dict[str, Any], prefix: str = "AYUSHBOT_CLOUD_") -> Dict[str, Any]:
    """Apply environment variable overrides to configuration.
    
    Environment variables prefixed with AYUSHBOT_CLOUD_ override config values.
    Example: AYUSHBOT_CLOUD_FL_PORT=9090 sets fl.port to 9090
    
    Args:
        config: Configuration dictionary
        prefix: Environment variable prefix
        
    Returns:
        Updated configuration dictionary
    """
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        
        # Convert AYUSHBOT_CLOUD_FL_PORT to fl.port
        config_key = key[len(prefix):].lower()
        
        if "_" in config_key:
            parts = config_key.split("_")
            # Set nested value
            current = config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Parse value (handle booleans, integers, etc.)
            parsed_value = _parse_env_value(value)
            current[parts[-1]] = parsed_value
    
    return config


def _parse_env_value(value: str) -> Any:
    """Parse environment variable value to appropriate type.
    
    Args:
        value: String value from environment variable
        
    Returns:
        Parsed value (bool, int, float, or str)
    """
    if value.lower() in ("true", "yes", "1"):
        return True
    elif value.lower() in ("false", "no", "0"):
        return False
    elif value.isdigit():
        return int(value)
    elif value.replace(".", "", 1).isdigit():
        return float(value)
    else:
        return value


class Config:
    """Configuration object with attribute access."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """Initialize config object.
        
        Args:
            config_dict: Configuration dictionary
        """
        self._config = config_dict
    
    def __getattr__(self, name: str) -> Any:
        """Get configuration value by attribute access.
        
        Args:
            name: Configuration key
            
        Returns:
            Configuration value
            
        Raises:
            AttributeError: If key not found in configuration
        """
        if name.startswith("_"):
            return object.__getattribute__(self, name)
        
        if name in self._config:
            value = self._config[name]
            if isinstance(value, dict):
                return Config(value)
            return value
        
        raise AttributeError(f"Configuration key not found: {name}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default.
        
        Args:
            key: Configuration key (supports nested keys with dots)
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return self._config


def get_config(config_path: Optional[str] = None) -> Config:
    """Load and return configuration object.
    
    Args:
        config_path: Path to config.yaml
        
    Returns:
        Configuration object
    """
    config_dict = load_config(config_path)
    return Config(config_dict)
