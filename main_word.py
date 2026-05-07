#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 转 Word 主程序"""

import sys
import os
import yaml
from pathlib import Path
from pdf_processor import pdf_to_images, cleanup_images
from models import OpenAICompatibleModel, WordGenerator

# 设置 Windows 控制台 UTF-8 编码
if sys.platform == "win32":
    os.system("chcp 65001 > nul")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main(pdf_path: str, output_path: str = None, mode: str = "precise"):
    """主函数

    Args:
        pdf_path: PDF 文件路径
        output_path: 输出 Word 文件路径（可选）
        mode: 转换模式 ("fast" 或 "precise")
    """
    # 检查文件是否存在
    if not Path(pdf_path).exists():
        print(f"❌ 文件不存在：{pdf_path}")
        return

    # 加载配置
    config = load_config()

    # 初始化模型
    print(f"🤖 使用模型：{config['model']['name']}")
    print(f"📋 转换模式：{'精确模式（保留样式）' if mode == 'precise' else '快速模式（仅内容）'}")

    vision_model = OpenAICompatibleModel(
        api_key=config["model"]["api_key"],
        base_url=config["model"]["base_url"],
        model=config["model"]["name"],
        chunk_size=config.get("chunk_size", 10),
    )

    # 初始化 Word 生成器
    word_generator = WordGenerator(vision_model, mode=mode)

    # 转换 PDF 为图片
    images = pdf_to_images(pdf_path, dpi=config["pdf"]["dpi"])
    total_pages = len(images)

    # 处理每一页
    print(f"\n🚀 开始处理（共 {total_pages} 页）...\n")
    pages_data = []

    for i, img_path in enumerate(images, 1):
        print(f"📄 处理第 {i}/{total_pages} 页...")
        page_data = word_generator.process_page_to_word(img_path, i)
        pages_data.append(page_data)

    # 生成 Word 文档
    if output_path is None:
        output_path = Path(pdf_path).with_suffix(".docx")
    else:
        output_path = Path(output_path)

    word_generator.generate_word(pages_data, str(output_path))

    print(f"\n✅ 转换完成！")
    print(f"📝 输出文件：{output_path.absolute()}")

    # 清理临时文件
    if config["output"]["cleanup_images"]:
        cleanup_images()


def print_usage():
    """打印使用说明"""
    print("""
PDF 转 Word 工具

用法：
  python main_word.py <PDF文件路径> [输出路径] [模式]

参数：
  PDF文件路径    必需，要转换的 PDF 文件
  输出路径       可选，输出的 Word 文件路径（默认：同名 .docx）
  模式          可选，转换模式：
                  fast    - 快速模式，只保留内容结构
                  precise - 精确模式，尽可能保留样式（默认）

示例：
  python main_word.py paper.pdf
  python main_word.py paper.pdf output.docx
  python main_word.py paper.pdf output.docx fast
  python main_word.py paper.pdf output.docx precise

注意：
  - 精确模式会尝试保留字体、颜色、对齐等样式，但处理时间较长
  - 快速模式只保留内容结构，速度更快，成本更低
  - 首次使用请确保已配置 config.yaml 中的 API 信息
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    pdf_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    mode = sys.argv[3] if len(sys.argv) > 3 else "precise"

    # 验证模式参数
    if mode not in ["fast", "precise"]:
        print(f"❌ 无效的模式：{mode}")
        print("   模式必须是 'fast' 或 'precise'")
        sys.exit(1)

    try:
        main(pdf_file, output_file, mode)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
