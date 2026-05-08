from copy import deepcopy


DEFAULT_CONFIG = {
    "model": {
        "type": "openai_compatible",
        "name": "your-model-name",
        "api_key": "your-api-key-here",
        "base_url": "https://api.example.com/v1",
    },
    "pdf": {"dpi": 150},
    "rendering": {
        "image_format": "png",
        "jpeg_quality": 85,
    },
    "chunk_size": 10,
    "processing": {
        "concurrency": 1,
    },
    "cache": {
        "enabled": True,
        "prompt_version": "v1",
    },
    "quality_check": True,
    "debug": False,
    "api": {
        "timeout": 60,
        "max_retries": 2,
        "retry_delay": 1,
    },
    "output": {
        "cleanup_images": True,
        "add_page_separator": True,
    },
}


def get_default_config() -> dict:
    return deepcopy(DEFAULT_CONFIG)


def build_config_for_profile(profile: dict) -> dict:
    config = get_default_config()
    config["model"]["name"] = profile["model"]
    config["model"]["api_key"] = profile["api_key"]
    config["model"]["base_url"] = profile["api_url"]
    config["pdf"]["dpi"] = profile.get("dpi", config["pdf"]["dpi"])
    config["chunk_size"] = profile.get("chunk_size", config["chunk_size"])
    return config
