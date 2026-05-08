from config_defaults import get_default_config


def validate_config(config: dict) -> dict:
    """校验运行配置并返回规范化结果"""
    if not isinstance(config, dict):
        raise ValueError("配置文件格式错误：顶层必须是对象")

    defaults = get_default_config()
    model = config.get("model")
    if not isinstance(model, dict):
        raise ValueError("配置缺失：model")

    pdf = config.get("pdf")
    if not isinstance(pdf, dict):
        raise ValueError("配置缺失：pdf")

    output = config.get("output")
    if not isinstance(output, dict):
        raise ValueError("配置缺失：output")

    normalized = {
        "model": {
            "api_key": _require_non_empty_string(model.get("api_key"), "model.api_key"),
            "base_url": _require_non_empty_string(model.get("base_url"), "model.base_url"),
            "name": _require_non_empty_string(model.get("name"), "model.name"),
            "type": model.get("type", defaults["model"]["type"]),
        },
        "pdf": {
            "dpi": _require_positive_int(pdf.get("dpi"), "pdf.dpi"),
        },
        "chunk_size": _require_positive_int(config.get("chunk_size", defaults["chunk_size"]), "chunk_size"),
        "quality_check": _require_bool(config.get("quality_check", defaults["quality_check"]), "quality_check"),
        "debug": _require_bool(config.get("debug", defaults["debug"]), "debug"),
        "api": _normalize_api_config(config.get("api", {}), defaults["api"]),
        "rendering": _normalize_rendering_config(config.get("rendering", {}), defaults["rendering"]),
        "processing": _normalize_processing_config(config.get("processing", {}), defaults["processing"]),
        "cache": _normalize_cache_config(config.get("cache", {}), defaults["cache"]),
        "output": {
            "cleanup_images": _require_bool(output.get("cleanup_images"), "output.cleanup_images"),
            "add_page_separator": _require_bool(output.get("add_page_separator", defaults["output"]["add_page_separator"]), "output.add_page_separator"),
        },
    }

    return normalized


def _normalize_api_config(api_config: dict, defaults: dict) -> dict:
    if not isinstance(api_config, dict):
        raise ValueError("配置错误：api 必须是对象")

    return {
        "timeout": _require_positive_number(api_config.get("timeout", defaults["timeout"]), "api.timeout"),
        "max_retries": _require_non_negative_int(api_config.get("max_retries", defaults["max_retries"]), "api.max_retries"),
        "retry_delay": _require_positive_number(api_config.get("retry_delay", defaults["retry_delay"]), "api.retry_delay"),
    }


def _normalize_rendering_config(rendering_config: dict, defaults: dict) -> dict:
    if not isinstance(rendering_config, dict):
        raise ValueError("配置错误：rendering 必须是对象")

    image_format = rendering_config.get("image_format", defaults["image_format"])
    if image_format not in {"png", "jpeg"}:
        raise ValueError("配置错误：rendering.image_format 必须是 'png' 或 'jpeg'")

    return {
        "image_format": image_format,
        "jpeg_quality": _require_int_in_range(
            rendering_config.get("jpeg_quality", defaults["jpeg_quality"]),
            "rendering.jpeg_quality",
            1,
            100,
        ),
    }


def _normalize_processing_config(processing_config: dict, defaults: dict) -> dict:
    if not isinstance(processing_config, dict):
        raise ValueError("配置错误：processing 必须是对象")

    return {
        "concurrency": _require_positive_int(
            processing_config.get("concurrency", defaults["concurrency"]),
            "processing.concurrency",
        ),
    }


def _normalize_cache_config(cache_config: dict, defaults: dict) -> dict:
    if not isinstance(cache_config, dict):
        raise ValueError("配置错误：cache 必须是对象")

    return {
        "enabled": _require_bool(cache_config.get("enabled", defaults["enabled"]), "cache.enabled"),
        "prompt_version": _require_non_empty_string(
            cache_config.get("prompt_version", defaults["prompt_version"]),
            "cache.prompt_version",
        ),
    }


def _require_non_empty_string(value, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"配置错误：{field_name} 不能为空")
    return value.strip()



def _require_positive_int(value, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"配置错误：{field_name} 必须是大于 0 的整数")
    return value



def _require_non_negative_int(value, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"配置错误：{field_name} 必须是大于等于 0 的整数")
    return value



def _require_int_in_range(value, field_name: str, min_value: int, max_value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not (min_value <= value <= max_value):
        raise ValueError(f"配置错误：{field_name} 必须在 {min_value} 到 {max_value} 之间")
    return value



def _require_positive_number(value, field_name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"配置错误：{field_name} 必须是大于 0 的数字")
    return float(value)



def _require_bool(value, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"配置错误：{field_name} 必须是布尔值")
    return value
