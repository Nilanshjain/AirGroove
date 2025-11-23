"""
Configuration Loader for AirGroove
Loads and validates settings from config.yaml
"""

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    print("WARNING: PyYAML not installed. Using default configuration.")

import os
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load and manage configuration from YAML file."""

    def __init__(self, config_path: str = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to config.yaml. If None, searches in project root.
        """
        if config_path is None:
            # Search for config.yaml in project root
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not YAML_AVAILABLE:
            # Return minimal default config if YAML not available
            return self._get_default_config()

        if not self.config_path.exists():
            print(f"WARNING: Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"WARNING: Error loading config: {e}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'camera': {'width': 640, 'height': 480, 'fps': 30, 'device_index': 0},
            'gestures': {
                'mediapipe': {'max_num_hands': 2, 'min_detection_confidence': 0.7, 'min_tracking_confidence': 0.5, 'model_complexity': 1},
                'smoothing': {'buffer_size': 4, 'confidence_threshold': 0.7, 'stability_threshold': 0.6, 'state_change_cooldown': 0.2},
                'swap_hands': True,
                'thresholds': {
                    'finger_fold_threshold': 0.10,
                    'pinch_threshold': 0.04,
                    'thumbs_up': {'thumb_extension_min': 0.15, 'thumb_separation_min': 0.10, 'other_fingers_folded_max': 0.08},
                    'thumbs_down': {'thumb_extension_min': 0.15, 'thumb_separation_min': 0.10, 'other_fingers_folded_max': 0.08},
                    'swipe': {'distance_threshold': 0.30, 'time_window': 0.5, 'min_frames': 5, 'velocity_threshold': 0.4, 'dead_zone_radius': 0.05, 'cooldown': 0.3},
                    'tap': {'velocity_threshold': 0.5, 'distance_min': 0.10, 'distance_max': 0.25, 'time_window': 0.2, 'cooldown': 0.2}
                }
            },
            'audio': {},
            'modes': {},
            'ui': {},
            'performance': {},
            'websocket': {'host': 'localhost', 'port': 8765},
            'profiles': {'active': 'intermediate'}
        }

    def _validate_config(self):
        """Validate that required config sections exist."""
        # Make validation lenient - just check for basic structure
        if not isinstance(self.config, dict):
            print("WARNING: Config is not a dictionary, using defaults")
            self.config = self._get_default_config()
            return

        # Ensure minimum required sections exist (add if missing)
        required_sections = ['camera', 'gestures', 'audio', 'modes', 'ui', 'performance', 'websocket', 'profiles']
        for section in required_sections:
            if section not in self.config:
                print(f"WARNING: Missing config section '{section}', using defaults")
                if section not in self.config:
                    self.config[section] = self._get_default_config().get(section, {})

    def reload(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        self._validate_config()

    def get(self, *keys, default=None):
        """
        Get nested configuration value.

        Args:
            *keys: Nested keys to traverse (e.g., 'gestures', 'smoothing', 'buffer_size')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            config.get('gestures', 'smoothing', 'buffer_size')  # Returns 4
        """
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def get_camera_config(self) -> Dict[str, Any]:
        """Get camera configuration."""
        return self.config.get('camera', {})

    def get_gesture_config(self) -> Dict[str, Any]:
        """Get gesture configuration."""
        return self.config.get('gestures', {})

    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration."""
        return self.config.get('audio', {})

    def get_mode_config(self, mode: str = None) -> Dict[str, Any]:
        """Get mode configuration."""
        modes = self.config.get('modes', {})
        if mode:
            return modes.get(mode, {})
        return modes

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return self.config.get('ui', {})

    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration."""
        return self.config.get('performance', {})

    def get_websocket_config(self) -> Dict[str, Any]:
        """Get WebSocket configuration."""
        return self.config.get('websocket', {})

    def get_active_profile(self) -> str:
        """Get active user profile name."""
        return self.config.get('profiles', {}).get('active', 'intermediate')

    def get_profile_config(self, profile: str = None) -> Dict[str, Any]:
        """Get user profile configuration."""
        if profile is None:
            profile = self.get_active_profile()

        profiles = self.config.get('profiles', {})
        return profiles.get(profile, profiles.get('intermediate', {}))

    def apply_profile_multipliers(self, profile: str = None):
        """
        Apply profile multipliers to gesture settings.

        Args:
            profile: Profile name. If None, uses active profile.
        """
        profile_config = self.get_profile_config(profile)

        # Get multipliers
        cooldown_mult = profile_config.get('cooldown_multiplier', 1.0)
        hold_time_mult = profile_config.get('hold_time_multiplier', 1.0)
        sensitivity_mult = profile_config.get('gesture_sensitivity', 1.0)

        # Apply to cooldowns
        cooldowns = self.get('gestures', 'cooldowns', default={})
        for key in cooldowns:
            cooldowns[key] *= cooldown_mult

        # Apply to hold times
        hold_times = self.get('gestures', 'hold_times', default={})
        for key in hold_times:
            hold_times[key] *= hold_time_mult

        # Apply sensitivity to thresholds (inverse relationship)
        thresholds = self.get('gestures', 'thresholds', default={})
        if 'swipe' in thresholds:
            swipe = thresholds['swipe']
            if 'velocity_threshold' in swipe:
                swipe['velocity_threshold'] *= sensitivity_mult

    def get_smoothing_buffer_size(self) -> int:
        """Get smoothing buffer size."""
        return self.get('gestures', 'smoothing', 'buffer_size', default=4)

    def get_smoothing_confidence(self) -> float:
        """Get smoothing confidence threshold."""
        return self.get('gestures', 'smoothing', 'confidence_threshold', default=0.7)

    def get_smoothing_stability(self) -> float:
        """Get smoothing stability threshold."""
        return self.get('gestures', 'smoothing', 'stability_threshold', default=0.6)

    def get_gesture_cooldown(self, gesture: str) -> float:
        """Get cooldown time for specific gesture."""
        return self.get('gestures', 'cooldowns', gesture, default=0.5)

    def get_gesture_hold_time(self, gesture: str) -> float:
        """Get hold time for specific gesture."""
        return self.get('gestures', 'hold_times', gesture, default=0.3)

    def get_gesture_threshold(self, *keys) -> Any:
        """Get gesture detection threshold."""
        return self.get('gestures', 'thresholds', *keys, default=0.1)

    def __repr__(self):
        return f"ConfigLoader(config_path='{self.config_path}')"


# Global config instance
_global_config = None


def get_config(config_path: str = None) -> ConfigLoader:
    """
    Get global configuration instance.

    Args:
        config_path: Path to config file (optional, only used on first call)

    Returns:
        ConfigLoader instance
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader(config_path)

    return _global_config


def reload_config():
    """Reload global configuration from file."""
    global _global_config

    if _global_config is not None:
        _global_config.reload()


# Convenience function for getting config values
def get_setting(*keys, default=None):
    """
    Quick access to configuration values.

    Example:
        get_setting('gestures', 'smoothing', 'buffer_size')
    """
    config = get_config()
    return config.get(*keys, default=default)
