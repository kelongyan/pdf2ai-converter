#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 转 Markdown 主程序"""

import sys
import os
import yaml
from pathlib import Path
from pdf_processor import pdf_to_images, cleanup_images
from models import OpenAICompatibleModel
from quality_checker import QualityChecker

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main(pdf_path: str, output_path: str = None):
    """主函数

    Args:
        pdf_path: PDF 文件路径
        output_path: 输出 Markdown 文件路径（可选）
    """
    # 检查文件是否存在
    if not Path(pdf_path).exists():
        print(f"❌ 文件不存在：{pdf_path}")
        return

    # 加载配置
    config = load_config()

    # 初始化模型
    print(f"🤖 使用模型：{config['model']['name']}")
    chunk_size = config.get("chunk_size", 10)
    model = OpenAICompatibleModel(
        api_key=config["model"]["api_key"],
        base_url=config["model"]["base_url"],
        model=config["model"]["name"],
        chunk_size=chunk_size,
    )

    # 转换 PDF 为图片
    images = pdf_to_images(pdf_path, dpi=config["pdf"]["dpi"])
    total_pages = len(images)

    # 调用模型处理
    print(f"🚀 开始调用大模型处理（共 {total_pages} 页）...\n")
    markdown = model.process_batch(images)

    # 保存结果
    if output_path is None:
        output_path = Path(pdf_path).with_suffix(".md")
    else:
        output_path = Path(output_path)

    output_path.write_text(markdown, encoding="utf-8")
    print(f"\n✅ 转换完成！")
    print(f"📝 输出文件：{output_path.absolute()}")

    # 质量检查
    if config.get("quality_check", True):
        checker = QualityChecker()
        result = checker.check(markdown, total_pages)
        checker.print_report(result)

        # 如果质量不合格，提示用户
        if not result["passed"]:
            print("⚠️  质量检查未通过，建议检查生成的 Markdown 文件")

    # 清理临时文件
    if config["output"]["cleanup_images"]:
        cleanup_images()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python main.py <PDF文件路径> [输出路径]")
        print("示例：python main.py test.pdf")
        print("示例：python main.py test.pdf output.md")
        sys.exit(1)

    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    main(pdf_file, output_file)
