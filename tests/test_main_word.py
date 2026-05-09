from pathlib import Path

from main_word import main
from helpers import RecordingCacheManager, make_valid_config


class FakeWordGenerator:
    last_output_path = None

    def __init__(self, vision_model, mode="precise"):
        self.vision_model = vision_model
        self.mode = mode

    def process_page_to_word(self, image_path, page_num):
        return {"page": page_num, "elements": []}

    def generate_word(self, pages_data, output_path):
        FakeWordGenerator.last_output_path = output_path


class FakeModel:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class CacheAwareWordGenerator:
    calls = 0
    last_pages_data = None

    def __init__(self, vision_model, mode="precise"):
        self.vision_model = vision_model
        self.mode = mode

    def process_page_to_word(self, image_path, page_num):
        type(self).calls += 1
        return {
            "page": page_num,
            "elements": [{"type": "paragraph", "content": f"generated {page_num}"}],
        }

    def generate_word(self, pages_data, output_path):
        type(self).last_pages_data = pages_data


class OrderedWordGenerator:
    last_pages_data = None

    def __init__(self, vision_model, mode="precise"):
        self.vision_model = vision_model
        self.mode = mode

    def process_page_to_word(self, image_path, page_num):
        return {
            "page": page_num,
            "elements": [{"type": "paragraph", "content": f"content {Path(image_path).stem}"}],
        }

    def generate_word(self, pages_data, output_path):
        type(self).last_pages_data = pages_data


class ResumeAwareWordGenerator:
    calls = 0
    last_pages_data = None

    def __init__(self, vision_model, mode="precise"):
        self.vision_model = vision_model
        self.mode = mode

    def process_page_to_word(self, image_path, page_num):
        type(self).calls += 1
        return {
            "page": page_num,
            "elements": [{"type": "paragraph", "content": f"recovered {page_num}"}],
        }

    def generate_word(self, pages_data, output_path):
        type(self).last_pages_data = pages_data



def test_main_word_empty_output_path_uses_default_docx(tmp_path, monkeypatch):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {}
    RecordingCacheManager.saved = {}

    monkeypatch.setattr("main_word.load_config", lambda: make_valid_config(
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main_word.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["page.png"])
    monkeypatch.setattr("main_word.build_vision_model", lambda config: FakeModel())
    monkeypatch.setattr("main_word.WordGenerator", FakeWordGenerator)
    monkeypatch.setattr("main_word.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main_word.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), "", "fast")

    assert FakeWordGenerator.last_output_path == str(Path(pdf_path).with_suffix(".docx"))



def test_main_word_uses_cached_pages_without_calling_generator(tmp_path, monkeypatch):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {
        "page-1": {"page": 1, "elements": [{"type": "paragraph", "content": "cached 1"}]},
        "page-2": {"page": 2, "elements": [{"type": "paragraph", "content": "cached 2"}]},
    }
    RecordingCacheManager.saved = {}
    CacheAwareWordGenerator.calls = 0
    CacheAwareWordGenerator.last_pages_data = None

    monkeypatch.setattr("main_word.load_config", lambda: make_valid_config(
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main_word.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "b.png"])
    monkeypatch.setattr("main_word.build_vision_model", lambda config: FakeModel())
    monkeypatch.setattr("main_word.WordGenerator", CacheAwareWordGenerator)
    monkeypatch.setattr("main_word.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main_word.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), None, "precise")

    assert CacheAwareWordGenerator.calls == 0
    assert CacheAwareWordGenerator.last_pages_data == [
        {"page": 1, "elements": [{"type": "paragraph", "content": "cached 1"}]},
        {"page": 2, "elements": [{"type": "paragraph", "content": "cached 2"}]},
    ]
    assert RecordingCacheManager.saved == {}



def test_main_word_concurrency_keeps_output_order(tmp_path, monkeypatch):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {}
    RecordingCacheManager.saved = {}
    OrderedWordGenerator.last_pages_data = None

    monkeypatch.setattr("main_word.load_config", lambda: make_valid_config(
        processing={"concurrency": 3},
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr(
        "main_word.pdf_to_images",
        lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["page3.png", "page1.png", "page2.png"],
    )
    monkeypatch.setattr("main_word.build_vision_model", lambda config: FakeModel())
    monkeypatch.setattr("main_word.WordGenerator", OrderedWordGenerator)
    monkeypatch.setattr("main_word.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main_word.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), None, "precise")

    assert OrderedWordGenerator.last_pages_data == [
        {"page": 1, "elements": [{"type": "paragraph", "content": "content page3"}]},
        {"page": 2, "elements": [{"type": "paragraph", "content": "content page1"}]},
        {"page": 3, "elements": [{"type": "paragraph", "content": "content page2"}]},
    ]



def test_main_word_processes_only_uncached_pages_and_reports_summary(tmp_path, monkeypatch, capsys):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {
        "page-1": {"page": 1, "elements": [{"type": "paragraph", "content": "cached 1"}]},
    }
    RecordingCacheManager.saved = {}
    CacheAwareWordGenerator.calls = 0
    CacheAwareWordGenerator.last_pages_data = None

    monkeypatch.setattr("main_word.load_config", lambda: make_valid_config(
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main_word.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "b.png"])
    monkeypatch.setattr("main_word.build_vision_model", lambda config: FakeModel())
    monkeypatch.setattr("main_word.WordGenerator", CacheAwareWordGenerator)
    monkeypatch.setattr("main_word.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main_word.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), None, "precise")

    captured = capsys.readouterr()
    assert "页面统计：总页数=2，缓存命中=1，待处理=1" in captured.out
    assert CacheAwareWordGenerator.calls == 1
    assert CacheAwareWordGenerator.last_pages_data == [
        {"page": 1, "elements": [{"type": "paragraph", "content": "cached 1"}]},
        {"page": 2, "elements": [{"type": "paragraph", "content": "generated 2"}]},
    ]
    assert RecordingCacheManager.saved == {
        "page-2": {"page": 2, "elements": [{"type": "paragraph", "content": "generated 2"}]}
    }



def test_main_word_prints_failure_summary_with_resume_hint(tmp_path, monkeypatch, capsys):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    class FailingWordGenerator:
        def __init__(self, vision_model, mode="precise"):
            self.vision_model = vision_model
            self.mode = mode

        def process_page_to_word(self, image_path, page_num):
            return {
                "page": page_num,
                "elements": [{"type": "paragraph", "content": f"[第 {page_num} 页处理失败] timeout"}],
            }

        def generate_word(self, pages_data, output_path):
            return None

    RecordingCacheManager.initial_cache = {}
    RecordingCacheManager.saved = {}

    monkeypatch.setattr("main_word.load_config", lambda: make_valid_config(
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main_word.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["bad.png"])
    monkeypatch.setattr("main_word.build_vision_model", lambda config: FakeModel())
    monkeypatch.setattr("main_word.WordGenerator", FailingWordGenerator)
    monkeypatch.setattr("main_word.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main_word.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), None, "precise")

    captured = capsys.readouterr()
    assert "以下页面处理失败：1" in captured.out
    assert "再次运行时会自动跳过已成功缓存的页面，仅补处理未完成页面。" in captured.out



def test_main_word_resume_retries_failed_cached_pages(tmp_path, monkeypatch, capsys):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    RecordingCacheManager.initial_cache = {
        "page-1": {"page": 1, "elements": [{"type": "paragraph", "content": "cached 1"}]},
        "page-2": {"page": 2, "elements": [{"type": "paragraph", "content": "[第 2 页处理失败] timeout"}]},
    }
    RecordingCacheManager.saved = {}
    ResumeAwareWordGenerator.calls = 0
    ResumeAwareWordGenerator.last_pages_data = None

    monkeypatch.setattr("main_word.load_config", lambda: make_valid_config(
        output={"cleanup_images": False, "add_page_separator": True},
    ))
    monkeypatch.setattr("main_word.pdf_to_images", lambda pdf_path, output_dir, dpi, image_format, jpeg_quality: ["a.png", "bad.png"])
    monkeypatch.setattr("main_word.build_vision_model", lambda config: FakeModel())
    monkeypatch.setattr("main_word.WordGenerator", ResumeAwareWordGenerator)
    monkeypatch.setattr("main_word.build_cache_manager", lambda config: RecordingCacheManager())
    monkeypatch.setattr("main_word.cleanup_images", lambda image_dir: None)

    main(str(pdf_path), None, "precise", resume=True)

    captured = capsys.readouterr()
    assert "恢复模式：仅补处理失败页和未完成页，成功缓存页将自动跳过。" in captured.out
    assert "页面统计：总页数=2，缓存命中=2，待处理=1" in captured.out
    assert ResumeAwareWordGenerator.calls == 1
    assert ResumeAwareWordGenerator.last_pages_data == [
        {"page": 1, "elements": [{"type": "paragraph", "content": "cached 1"}]},
        {"page": 2, "elements": [{"type": "paragraph", "content": "recovered 2"}]},
    ]
    assert RecordingCacheManager.saved == {
        "page-2": {"page": 2, "elements": [{"type": "paragraph", "content": "recovered 2"}]}
    }
