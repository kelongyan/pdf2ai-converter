from copy import deepcopy

from config_defaults import get_default_config


class RecordingCacheManager:
    initial_cache = {}
    saved = {}

    def __init__(self):
        self.storage = deepcopy(self.initial_cache)

    def get_cache_key(self, **kwargs):
        return f"page-{kwargs['page_num']}"

    def load_text(self, cache_key):
        return self.storage.get(cache_key)

    def save_text(self, cache_key, content):
        self.storage[cache_key] = content
        type(self).saved[cache_key] = content

    def load_json(self, cache_key):
        return self.storage.get(cache_key)

    def save_json(self, cache_key, content):
        self.storage[cache_key] = content
        type(self).saved[cache_key] = content


def make_valid_config(**overrides):
    config = get_default_config()
    config["model"].update(
        {
            "name": "demo-model",
            "api_key": "secret",
            "base_url": "https://example.test/v1",
        }
    )
    _deep_update(config, overrides)
    return config


def _deep_update(target: dict, overrides: dict):
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
