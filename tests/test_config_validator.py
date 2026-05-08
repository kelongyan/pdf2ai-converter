from config_validator import validate_config
from helpers import make_valid_config


def test_validate_config_accepts_valid_config():
    config = validate_config(make_valid_config())

    assert config["model"]["name"] == "demo-model"
    assert config["api"]["timeout"] == 60.0
    assert config["rendering"]["image_format"] == "png"
    assert config["cache"]["enabled"] is True
    assert config["output"]["cleanup_images"] is True



def test_validate_config_rejects_missing_api_key():
    config = make_valid_config()
    config["model"]["api_key"] = ""

    try:
        validate_config(config)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "model.api_key" in str(exc)



def test_validate_config_rejects_invalid_dpi():
    config = make_valid_config()
    config["pdf"]["dpi"] = 0

    try:
        validate_config(config)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "pdf.dpi" in str(exc)



def test_validate_config_rejects_invalid_cleanup_images():
    config = make_valid_config()
    config["output"]["cleanup_images"] = "yes"

    try:
        validate_config(config)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "output.cleanup_images" in str(exc)



def test_validate_config_rejects_invalid_image_format():
    config = make_valid_config()
    config["rendering"]["image_format"] = "webp"

    try:
        validate_config(config)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "rendering.image_format" in str(exc)
