from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile

from cache_manager import CacheManager
from models import OpenAICompatibleModel


RESUME_MODE_MESSAGE = "🔁 恢复模式：仅补处理失败页和未完成页，成功缓存页将自动跳过。"


def build_vision_model(config: dict) -> OpenAICompatibleModel:
    return OpenAICompatibleModel(
        api_key=config["model"]["api_key"],
        base_url=config["model"]["base_url"],
        model=config["model"]["name"],
        chunk_size=config.get("chunk_size", 10),
        timeout=config["api"]["timeout"],
        max_retries=config["api"]["max_retries"],
        retry_delay=config["api"]["retry_delay"],
        debug=config["debug"],
    )


def build_cache_manager(config: dict):
    return CacheManager() if config["cache"]["enabled"] else None


def create_image_dir() -> str:
    return tempfile.mkdtemp(prefix="pdf2md_")


def resolve_output_path(pdf_path: str, output_path: str, suffix: str) -> Path:
    if output_path:
        return Path(output_path)
    return Path(pdf_path).with_suffix(suffix)


def join_markdown_pages(markdown_pages: list, add_page_separator: bool) -> str:
    separator = "\n\n---\n\n" if add_page_separator else "\n\n"
    return separator.join(markdown_pages)


def is_failed_markdown_page(markdown: str) -> bool:
    return markdown.startswith("[处理失败：")


def is_failed_word_page(page_data: dict, page_num: int) -> bool:
    elements = page_data.get("elements", [])
    if len(elements) != 1:
        return False

    element = elements[0]
    if element.get("type") != "paragraph":
        return False

    content = element.get("content", "")
    return content.startswith(f"[第 {page_num} 页处理失败")


def should_retry_markdown_cache(markdown: str, resume: bool) -> bool:
    return resume and is_failed_markdown_page(markdown)


def should_retry_word_cache(page_data: dict, page_num: int, resume: bool) -> bool:
    return resume and is_failed_word_page(page_data, page_num)


def print_resume_mode_banner():
    print(RESUME_MODE_MESSAGE)


def print_failure_summary(failed_pages, noun: str = "页面"):
    if not failed_pages:
        return

    failed_page_numbers = ", ".join(str(page) for page in failed_pages)
    print(f"⚠️  以下{noun}处理失败：{failed_page_numbers}")
    print("🔁 再次运行时会自动跳过已成功缓存的页面，仅补处理未完成页面。")


def print_processing_summary(total_pages: int, cached_pages: int, pending_pages: int):
    print(
        f"📊 页面统计：总页数={total_pages}，缓存命中={cached_pages}，待处理={pending_pages}"
    )


def run_pending_pages(
    pending_pages: list,
    concurrency: int,
    total_pages: int,
    process_page,
):
    if not pending_pages:
        return []

    if concurrency > 1 and len(pending_pages) > 1:
        print(f"⚡ 并发处理未命中缓存页面：{len(pending_pages)} 页，并发数={concurrency}")
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            results = list(executor.map(process_page, pending_pages))
    else:
        results = []
        for page in pending_pages:
            print(f"📄 处理第 {page['page_num']}/{total_pages} 页...")
            results.append(process_page(page))

    return sorted(results, key=lambda item: item["page_num"])
