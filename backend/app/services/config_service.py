import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ConfigService:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "config/config.json")
        
        self.config_path = Path(__file__).parent.parent / config_path
        self._config = None
    
    def load_config(self) -> list[dict]:
        try:
            with open(self.config_path) as f:
                self._config = json.load(f)
                logger.info(f"Config loaded from {self.config_path}")
                return self._config
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return []
    
    def get_config(self) -> list[dict]:
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def get_feature_config(self, feature_id: str) -> Optional[dict]:
        config = self.get_config()
        for feature in config:
            if feature.get("id") == feature_id:
                return feature
        logger.warning(f"Feature not found: {feature_id}")
        return None
    
    def reload_config(self) -> list[dict]:
        self._config = None
        return self.load_config()


config_service = ConfigService()
