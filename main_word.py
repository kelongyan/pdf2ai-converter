#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 转 Word 主程序"""

import sys
import os
import yaml
from pathlib import Path
from pdf_processor import pdf_to_images, cleanup_images
from models import WordGenerator
from config_validator import validate_config
from cache_manager import CacheManager
from pipeline_utils import (
    build_vision_model,
    build_cache_manager,
    create_image_dir,
    resolve_output_path,
    run_pending_pages,
    print_failure_summary,
    print_processing_summary,
    is_failed_word_page,
    should_retry_word_cache,
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


def main(pdf_path: str, output_path: str = None, mode: str = "precise", resume: bool = False):
    """主函数

    Args:
        pdf_path: PDF 文件路径
        output_path: 输出 Word 文件路径（可选）
        mode: 转换模式 ("fast" 或 "precise")
        resume: 是否仅补处理失败页和未完成页
    """
    if not Path(pdf_path).exists():
        print(f"❌ 文件不存在：{pdf_path}")
        return

    config = validate_config(load_config())

    print(f"🤖 使用模型：{config['model']['name']}")
    print(f"📋 转换模式：{'精确模式（保留样式）' if mode == 'precise' else '快速模式（仅内容）'}")
    if resume:
        print_resume_mode_banner()

    vision_model = build_vision_model(config)
    word_generator = WordGenerator(vision_model, mode=mode)

    rendering = config["rendering"]
    cache_config = config["cache"]
    concurrency = config["processing"]["concurrency"]
    cache_manager = build_cache_manager(config)
    image_dir = create_image_dir()

    try:
        images = pdf_to_images(
            pdf_path,
            image_dir,
            dpi=config["pdf"]["dpi"],
            image_format=rendering["image_format"],
            jpeg_quality=rendering["jpeg_quality"],
        )
        total_pages = len(images)

        print(f"\n🚀 开始处理（共 {total_pages} 页）...\n")
        pages_data = [None] * total_pages
        failed_pages = []
        output_mode = f"word-{mode}"
        pending_pages = []
        cached_pages = 0

        for i, img_path in enumerate(images, 1):
            cache_key = None
            page_data = None
            if cache_manager is not None:
                cache_key = cache_manager.get_cache_key(
                    pdf_path=pdf_path,
                    page_num=i,
                    model_name=config["model"]["name"],
                    output_mode=output_mode,
                    dpi=config["pdf"]["dpi"],
                    image_format=rendering["image_format"],
                    prompt_version=cache_config["prompt_version"],
                )
                page_data = cache_manager.load_json(cache_key)
                if page_data is not None:
                    print(f"♻️  第 {i}/{total_pages} 页命中缓存")
                    cached_pages += 1

            if page_data is not None and not should_retry_word_cache(page_data, i, resume):
                pages_data[i - 1] = page_data
                if is_failed_word_page(page_data, i):
                    failed_pages.append(i)
                continue

            pending_pages.append(
                {
                    "page_num": i,
                    "image_path": img_path,
                    "cache_key": cache_key,
                }
            )

        print_processing_summary(total_pages, cached_pages, len(pending_pages))

        if pending_pages:
            results = run_pending_pages(
                pending_pages,
                concurrency,
                total_pages,
                lambda page: _process_word_page(word_generator, page),
            )

            for result in results:
                page_num = result["page_num"]
                page_data = result["page_data"]
                pages_data[page_num - 1] = page_data
                if cache_manager is not None and not is_failed_word_page(page_data, page_num):
                    cache_manager.save_json(result["cache_key"], page_data)
                if is_failed_word_page(page_data, page_num):
                    failed_pages.append(page_num)
        else:
            print("✅ 所有页面均已命中缓存，无需重新请求模型。")

        output_path = resolve_output_path(pdf_path, output_path, ".docx")
        word_generator.generate_word(pages_data, str(output_path))

        print(f"\n✅ 转换完成！")
        print(f"📝 输出文件：{output_path.absolute()}")
        if failed_pages:
            print_failure_summary(failed_pages)
    finally:
        if config["output"]["cleanup_images"]:
            cleanup_images(image_dir)
        else:
            print(f"📁 临时图片保留在：{image_dir}")


def _process_word_page(word_generator, page: dict) -> dict:
    page_data = word_generator.process_page_to_word(page["image_path"], page["page_num"])
    return {
        "page_num": page["page_num"],
        "cache_key": page["cache_key"],
        "page_data": page_data,
    }


def _is_failed_word_page(page_data: dict, page_num: int) -> bool:
    return is_failed_word_page(page_data, page_num)


def print_usage():
    """打印使用说明"""
    print("""
PDF 转 Word 工具

用法：
  python main_word.py <PDF文件路径> [输出路径] [模式] [--resume]

参数：
  PDF文件路径    必需，要转换的 PDF 文件
  输出路径       可选，输出的 Word 文件路径（默认：同名 .docx）
  模式          可选，转换模式：
                  fast    - 快速模式，只保留内容结构
                  precise - 精确模式，尽可能保留样式（默认）
  --resume      可选，仅补处理失败页和未完成页

示例：
  python main_word.py paper.pdf
  python main_word.py paper.pdf output.docx
  python main_word.py paper.pdf output.docx fast
  python main_word.py paper.pdf output.docx precise
  python main_word.py paper.pdf output.docx precise --resume

注意：
  - 精确模式会尝试保留字体、颜色、对齐等样式，但处理时间较长
  - 快速模式只保留内容结构，速度更快，成本更低
  - 首次使用请确保已配置 config.yaml 中的 API 信息
""")


if __name__ == "__main__":
    args = sys.argv[1:]
    resume = False
    if "--resume" in args:
        args.remove("--resume")
        resume = True

    if len(args) < 1:
        print_usage()
        sys.exit(1)

    pdf_file = args[0]
    output_file = args[1] if len(args) > 1 else None
    mode = args[2] if len(args) > 2 else "precise"

    if mode not in ["fast", "precise"]:
        print(f"❌ 无效的模式：{mode}")
        print("   模式必须是 'fast' 或 'precise'")
        sys.exit(1)

    try:
        main(pdf_file, output_file, mode, resume=resume)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
