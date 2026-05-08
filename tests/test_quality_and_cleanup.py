from pathlib import Path

from pdf_processor import cleanup_images
from quality_checker import QualityChecker


def test_cleanup_images_removes_target_directory(tmp_path):
    image_dir = tmp_path / "temp_images"
    image_dir.mkdir()
    (image_dir / "page_001.png").write_bytes(b"image")

    cleanup_images(str(image_dir))

    assert not image_dir.exists()


def test_quality_checker_detects_basic_valid_markdown():
    markdown = "\n".join([
        "# 标题",
        "正文内容",
        "## 小节",
        "- 项目",
        "| A | B |",
        "| - | - |",
        "| 1 | 2 |",
    ] * 4)

    result = QualityChecker().check(markdown, pdf_pages=1)

    assert result["passed"] is True
    assert result["stats"]["headers"] > 0
    assert result["stats"]["tables"] > 0
