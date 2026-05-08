#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 转 Markdown 主程序"""

import sys
import os
import yaml
from pathlib import Path
from pdf_processor import pdf_to_images, cleanup_images
from quality_checker import QualityChecker
from config_validator import validate_config
from cache_manager import CacheManager
from pipeline_utils import (
    build_vision_model,
    build_cache_manager,
    create_image_dir,
    resolve_output_path,
    run_pending_pages,
    join_markdown_pages,
    print_failure_summary,
    print_processing_summary,
    is_failed_markdown_page,
    should_retry_markdown_cache,
    print_resume_mode_banner,
)

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main(pdf_path: str, output_path: str = None, resume: bool = False):
    """主函数

    Args:
        pdf_path: PDF 文件路径
        output_path: 输出 Markdown 文件路径（可选）
        resume: 是否仅补处理失败页和未完成页
    """
    # 检查文件是否存在
    if not Path(pdf_path).exists():
        print(f"❌ 文件不存在：{pdf_path}")
        return

    # 加载配置
    config = validate_config(load_config())

    # 初始化模型
    print(f"🤖 使用模型：{config['model']['name']}")
    if resume:
        print_resume_mode_banner()
    chunk_size = config.get("chunk_size", 10)
    concurrency = config["processing"]["concurrency"]
    model = build_vision_model(config)

    rendering = config["rendering"]
    cache_config = config["cache"]
    cache_manager = build_cache_manager(config)
    image_dir = create_image_dir()

    try:
        # 转换 PDF 为图片
        images = pdf_to_images(
            pdf_path,
            image_dir,
            dpi=config["pdf"]["dpi"],
            image_format=rendering["image_format"],
            jpeg_quality=rendering["jpeg_quality"],
        )
        total_pages = len(images)

        # 调用模型处理
        print(f"🚀 开始调用大模型处理（共 {total_pages} 页）...\n")
        markdown_pages = [None] * total_pages
        failed_pages = []
        pending_pages = []
        cached_pages = 0
        context = ""

        for i, img_path in enumerate(images, 1):
            if i > 1 and (i - 1) % chunk_size == 0:
                context = ""
                print(f"\n✂️  分段 {(i - 1) // chunk_size} 完成，开始下一段...\n")

            cache_key = None
            markdown = None
            if cache_manager is not None:
                cache_key = cache_manager.get_cache_key(
                    pdf_path=pdf_path,
                    page_num=i,
                    model_name=config["model"]["name"],
                    output_mode="markdown",
                    dpi=config["pdf"]["dpi"],
                    image_format=rendering["image_format"],
                    prompt_version=cache_config["prompt_version"],
                )
                markdown = cache_manager.load_text(cache_key)
                if markdown is not None:
                    print(f"♻️  第 {i}/{total_pages} 页命中缓存")
                    cached_pages += 1

            if markdown is not None and not should_retry_markdown_cache(markdown, resume):
                markdown_pages[i - 1] = markdown
                if is_failed_markdown_page(markdown):
                    failed_pages.append({"page": i, "reason": markdown})
                context = markdown[-200:] if len(markdown) > 200 else markdown
                continue

            pending_pages.append(
                {
                    "page_num": i,
                    "image_path": img_path,
                    "cache_key": cache_key,
                    "context": context,
                }
            )
            context = ""

        print_processing_summary(total_pages, cached_pages, len(pending_pages))

        if pending_pages:
            results = run_pending_pages(
                pending_pages,
                concurrency,
                total_pages,
                lambda page: _process_markdown_page(model, page),
            )

            for result in results:
                page_num = result["page_num"]
                markdown = result["markdown"]
                markdown_pages[page_num - 1] = markdown
                if cache_manager is not None and not is_failed_markdown_page(markdown):
                    cache_manager.save_text(result["cache_key"], markdown)
                if is_failed_markdown_page(markdown):
                    failed_pages.append({"page": page_num, "reason": markdown})
        else:
            print("✅ 所有页面均已命中缓存，无需重新请求模型。")

        markdown = join_markdown_pages(
            markdown_pages,
            config["output"]["add_page_separator"],
        )

        # 保存结果
        output_path = resolve_output_path(pdf_path, output_path, ".md")
        output_path.write_text(markdown, encoding="utf-8")
        print(f"\n✅ 转换完成！")
        print(f"📝 输出文件：{output_path.absolute()}")

        # 质量检查
        if config.get("quality_check", True):
            checker = QualityChecker()
            result = checker.check(markdown, total_pages)
            checker.print_report(result)

            if not result["passed"]:
                print("⚠️  质量检查未通过，建议检查生成的 Markdown 文件")

        if failed_pages:
            print_failure_summary([item["page"] for item in failed_pages])
    finally:
        if config["output"]["cleanup_images"]:
            cleanup_images(image_dir)
        else:
            print(f"📁 临时图片保留在：{image_dir}")


def _process_markdown_page(model, page: dict) -> dict:
    markdown = model.process_page(page["image_path"], page["context"])
    return {
        "page_num": page["page_num"],
        "cache_key": page["cache_key"],
        "markdown": markdown,
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    resume = False
    if "--resume" in args:
        args.remove("--resume")
        resume = True

    if len(args) < 1:
        print("用法：python main.py <PDF文件路径> [输出路径] [--resume]")
        print("示例：python main.py test.pdf")
        print("示例：python main.py test.pdf output.md")
        print("示例：python main.py test.pdf --resume")
        sys.exit(1)

    pdf_file = args[0]
    output_file = args[1] if len(args) > 1 else None

    main(pdf_file, output_file, resume=resume)


