from cache_manager import CacheManager


def test_cache_manager_text_roundtrip(tmp_path):
    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4")
    cache = CacheManager(str(tmp_path))
    key = cache.get_cache_key(
        pdf_path=str(sample_pdf),
        page_num=1,
        model_name="demo-model",
        output_mode="markdown",
        dpi=150,
        image_format="png",
        prompt_version="v1",
    )
    cache.save_text(key, "hello")

    assert cache.load_text(key) == "hello"



def test_cache_manager_json_roundtrip(tmp_path):
    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4")
    cache = CacheManager(str(tmp_path))
    key = cache.get_cache_key(
        pdf_path=str(sample_pdf),
        page_num=2,
        model_name="demo-model",
        output_mode="word-precise",
        dpi=150,
        image_format="jpeg",
        prompt_version="v1",
    )

    payload = {"page": 2, "elements": [{"type": "paragraph", "content": "hi"}]}
    cache.save_json(key, payload)

    assert cache.load_json(key) == payload



def test_cache_manager_prompt_version_changes_key(tmp_path):
    sample_pdf = tmp_path / "sample.pdf"
    sample_pdf.write_bytes(b"%PDF-1.4")
    cache = CacheManager(str(tmp_path))

    key_v1 = cache.get_cache_key(
        pdf_path=str(sample_pdf),
        page_num=1,
        model_name="demo-model",
        output_mode="markdown",
        dpi=150,
        image_format="png",
        prompt_version="v1",
    )
    key_v2 = cache.get_cache_key(
        pdf_path=str(sample_pdf),
        page_num=1,
        model_name="demo-model",
        output_mode="markdown",
        dpi=150,
        image_format="png",
        prompt_version="v2",
    )

    assert key_v1 != key_v2
