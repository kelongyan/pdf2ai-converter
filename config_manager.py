"""配置管理模块"""

import json
import base64
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """管理 API 配置"""

    def __init__(self, config_file: str = ".config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        """保存配置文件"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def _encrypt_key(self, key: str) -> str:
        """简单加密 API Key（Base64）"""
        return base64.b64encode(key.encode()).decode()

    def _decrypt_key(self, encrypted: str) -> str:
        """解密 API Key"""
        return base64.b64decode(encrypted.encode()).decode()

    def save_profile(
        self, name: str, api_url: str, api_key: str, model: str, **kwargs
    ):
        """保存配置"""
        self.config[name] = {
            "api_url": api_url,
            "api_key": self._encrypt_key(api_key),
            "model": model,
            **kwargs,
        }
        self.config["last_used"] = name
        self._save_config()

    def get_profile(self, name: str) -> Optional[Dict]:
        """获取配置"""
        if name not in self.config:
            return None

        profile = self.config[name].copy()
        profile["api_key"] = self._decrypt_key(profile["api_key"])
        return profile

    def get_last_profile(self) -> Optional[Dict]:
        """获取上次使用的配置"""
        last_name = self.config.get("last_used")
        if last_name:
            return self.get_profile(last_name)
        return None

    def list_profiles(self) -> list:
        """列出所有配置"""
        return [k for k in self.config.keys() if k != "last_used"]

    def delete_profile(self, name: str):
        """删除配置"""
        if name in self.config:
            del self.config[name]
            self._save_config()
