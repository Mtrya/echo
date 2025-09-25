import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
import requests

class Config:
    """Configuration management for Echo exam platform"""

    # Model options
    OMNI_MODELS = ["qwen3-omni-flash", "qwen-omni-turbo", "qwen2.5-omni-7b"]
    VISION_MODELS = [
        "qwen3-vl-plus", "qwen3-vl-235b-a22b-thinking", "qwen3-vl-235b-a22b-instruct",
        "qwen3-omni-flash", "qwen-vl-max", "qwen-vl-plus", "qwen-omni-turbo",
        "qvq-max", "qvq-plus", "qwen2.5-vl-72b-instruct", "qwen2.5-vl-32b-instruct",
        "qwen2.5-vl-7b-instruct"
    ]

    # Voice options by model
    VOICE_OPTIONS = {
        "qwen3-omni-flash": ["Cherry", "Ethan", "Nofish", "Jennifer", "Ryan", "Katerina", "Elias", "Jada", "Dylan", "Sunny", "li", "Marcus", "Roy", "Peter", "Rocky", "Kiki", "Eric"],
        "qwen-omni-turbo": ["Cherry", "Serena", "Ethan", "Chelsie"],
        "qwen2.5-omni-7b": ["Ethan", "Chelsie"]
    }

    # Theme options
    THEMES = ["default", "dark", "nature"]

    def __init__(self):
        self.config_file = Path(__file__).parent.parent / "config.yaml"
        self.config = self._load_default_config()
        self.load()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            "api": {
                "dashscope_key": ""
            },
            "models": {
                "omni_model": "qwen3-omni-flash",
                "vision_model": "qwen3-vl-plus",
                "instruction_voice": "Cherry",
                "response_voice": "Cherry"
            },
            "time_limits": {
                "multiple_choice": 30,
                "read_aloud": 15,
                "quick_response": 15,
                "translation": 30
            },
            "ui": {
                "theme": "default"
            }
        }

    def load(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config:
                        # Merge with defaults to ensure all keys exist
                        self._merge_config(self.config, loaded_config)
            except Exception as e:
                print(f"Failed to load config file: {e}")
                print("Using default configuration")

    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save config file: {e}")
            return False

    def get(self, key: str, default=None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()

    def update(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration with validation"""
        errors = self.validate(new_config)
        if errors:
            return {"success": False, "errors": errors}

        self._merge_config(self.config, new_config)
        if self.save():
            return {"success": True, "config": self.config}
        else:
            return {"success": False, "errors": ["Failed to save configuration"]}

    def _merge_config(self, base: Dict, update: Dict):
        """Recursively merge configuration dictionaries"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def validate(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate API key
        if "api" in config:
            if "dashscope_key" in config["api"]:
                api_key = config["api"]["dashscope_key"]
                if api_key and not api_key.startswith("sk-"):
                    errors.append("API key must start with 'sk-'")

        # Validate model selection
        if "models" in config:
            models = config["models"]
            if "omni_model" in models and models["omni_model"] not in self.OMNI_MODELS:
                errors.append(f"Invalid omni model. Must be one of: {', '.join(self.OMNI_MODELS)}")

            if "vision_model" in models and models["vision_model"] not in self.VISION_MODELS:
                errors.append(f"Invalid vision model. Must be one of: {', '.join(self.VISION_MODELS[:5])}...")

            # Validate voice selection
            omni_model = models.get("omni_model", self.config["models"]["omni_model"])
            if "instruction_voice" in models:
                valid_voices = self.VOICE_OPTIONS.get(omni_model, self.VOICE_OPTIONS["qwen3-omni-flash"])
                if models["instruction_voice"] not in valid_voices:
                    errors.append(f"Invalid instruction voice for {omni_model}. Valid options: {', '.join(valid_voices)}")

            if "response_voice" in models:
                valid_voices = self.VOICE_OPTIONS.get(omni_model, self.VOICE_OPTIONS["qwen3-omni-flash"])
                if models["response_voice"] not in valid_voices:
                    errors.append(f"Invalid response voice for {omni_model}. Valid options: {', '.join(valid_voices)}")

        # Validate time limits
        if "time_limits" in config:
            time_limits = config["time_limits"]
            for key, value in time_limits.items():
                if not isinstance(value, int) or value < 5 or value > 300:
                    errors.append(f"Time limit for {key} must be between 5 and 300 seconds")

        # Validate theme
        if "ui" in config and "theme" in config["ui"]:
            if config["ui"]["theme"] not in self.THEMES:
                errors.append(f"Invalid theme. Must be one of: {', '.join(self.THEMES)}")

        return errors

    def test_api_connection(self, api_key: str) -> Dict[str, Any]:
        """Test API connection with provided key"""
        if not api_key:
            return {"success": False, "error": "API key is required"}

        if not api_key.startswith("sk-"):
            return {"success": False, "error": "API key must start with 'sk-'"}

        try:
            # Simple test API call to Dashscope
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            test_payload = {
                "model": "qwen3-omni-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": "connection test. Return 'copy'."
                        }]
                    }
                ],
                "stream": True,
                "modalities": ["text"]
            }

            response = requests.post(
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=10
            )

            if response.status_code == 200:
                return {"success": True, "message": "API connection successful"}
            else:
                return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": f"Connection failed: {str(e)}"}

    def get_available_voices(self, omni_model: str) -> List[str]:
        """Get available voices for a specific omni model"""
        return self.VOICE_OPTIONS.get(omni_model, self.VOICE_OPTIONS["qwen3-omni-flash"])


# Global config instance
config = Config()