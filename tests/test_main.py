from pathlib import Path

from main import main
from helpers import RecordingCacheManager, make_valid_config


class FakeMarkdownModel:
    failed_pages = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def process_page(self, image_path, context=""):
        if image_path == "bad.png":
            return "[处理失败：bad.png]"
        return "# 标题\n正文"


class CacheHitOnlyModel:
    calls = 0

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def process_page(self, image_path, context=""):
        type(self).calls += 1
        return "should not be used"


class OrderedMarkdownModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def process_page(self, image_path, context=""):
        return f"content {Path(image_path).stem}"


class ResumeAwareMarkdownModel:
    calls = 0

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def process_page(self, image_path, context=""):
        type(self).calls += 1
        return f"recovered {Path(image_path).stem}"



def test_main_prints_failed_page_summary(tmp_path, monkeypatch, capsys):
    pdf_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "output.md"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr("main.load_config", lambda: make_valid_config(
        quality_check=False,
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "bad.png"])
    monkeypatch.setattr("main.build_vision_model", lambda config: FakeMarkdownModel())
    monkeypatch.setattr("main.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), str(output_path))

    captured = capsys.readouterr()
    assert "以下页面处理失败：2" in captured.out
    assert output_path.read_text(encoding="utf-8") == "# 标题\n正文\n\n---\n\n[处理失败：bad.png]"



def test_main_uses_cached_pages_without_calling_model(tmp_path, monkeypatch):
    pdf_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "output.md"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {
        "page-1": "cached page 1",
        "page-2": "cached page 2",
    }
    RecordingCacheManager.saved = {}
    CacheHitOnlyModel.calls = 0

    monkeypatch.setattr("main.load_config", lambda: make_valid_config(
        quality_check=False,
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "b.png"])
    monkeypatch.setattr("main.build_vision_model", lambda config: CacheHitOnlyModel())
    monkeypatch.setattr("main.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), str(output_path))

    assert CacheHitOnlyModel.calls == 0
    assert output_path.read_text(encoding="utf-8") == "cached page 1\n\n---\n\ncached page 2"
    assert RecordingCacheManager.saved == {}



def test_main_respects_add_page_separator_flag(tmp_path, monkeypatch):
    pdf_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "output.md"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {}
    RecordingCacheManager.saved = {}

    monkeypatch.setattr("main.load_config", lambda: make_valid_config(
        quality_check=False,
        output={"cleanup_images": False, "add_page_separator": False},
    ))
    monkeypatch.setattr("main.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "b.png"])
    monkeypatch.setattr("main.build_vision_model", lambda config: OrderedMarkdownModel())
    monkeypatch.setattr("main.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), str(output_path))

    assert output_path.read_text(encoding="utf-8") == "content a\n\ncontent b"



def test_main_processes_only_uncached_pages_and_reports_summary(tmp_path, monkeypatch, capsys):
    pdf_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "output.md"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {
        "page-1": "cached page 1",
    }
    RecordingCacheManager.saved = {}
    CacheHitOnlyModel.calls = 0

    monkeypatch.setattr("main.load_config", lambda: make_valid_config(
        quality_check=False,
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "b.png"])
    monkeypatch.setattr("main.build_vision_model", lambda config: CacheHitOnlyModel())
    monkeypatch.setattr("main.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), str(output_path))

    captured = capsys.readouterr()
    assert "页面统计：总页数=2，缓存命中=1，待处理=1" in captured.out
    assert CacheHitOnlyModel.calls == 1
    assert output_path.read_text(encoding="utf-8") == "cached page 1\n\n---\n\nshould not be used"
    assert RecordingCacheManager.saved == {"page-2": "should not be used"}



def test_main_resume_retries_failed_cached_pages(tmp_path, monkeypatch, capsys):
    pdf_path = tmp_path / "sample.pdf"
    output_path = tmp_path / "output.md"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {
        "page-1": "cached page 1",
        "page-2": "[处理失败：bad.png]",
    }
    RecordingCacheManager.saved = {}
    ResumeAwareMarkdownModel.calls = 0

    monkeypatch.setattr("main.load_config", lambda: make_valid_config(
        quality_check=False,
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "bad.png"])
    monkeypatch.setattr("main.build_vision_model", lambda config: ResumeAwareMarkdownModel())
    monkeypatch.setattr("main.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), str(output_path), resume=True)

    captured = capsys.readouterr()
    assert "恢复模式：仅补处理失败页和未完成页，成功缓存页将自动跳过。" in captured.out
    assert "页面统计：总页数=2，缓存命中=2，待处理=1" in captured.out
    assert ResumeAwareMarkdownModel.calls == 1
    assert output_path.read_text(encoding="utf-8") == "cached page 1\n\n---\n\nrecovered bad"
    assert RecordingCacheManager.saved == {"page-2": "recovered bad"}
