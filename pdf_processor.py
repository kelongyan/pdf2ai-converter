from typing import List
from pathlib import Path
import fitz  # PyMuPDF


def pdf_to_images(
    pdf_path: str, output_dir: str = "temp_images", dpi: int = 150
) -> List[str]:
    """将 PDF 转换为高清图片

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        dpi: 分辨率（150=标准，300=高清）

    Returns:
        图片路径列表
    """
    doc = fitz.open(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    image_paths = []
    total_pages = len(doc)

    print(f"📚 PDF 共 {total_pages} 页，开始转换...")

    for i, page in enumerate(doc, 1):
        # 提高分辨率（dpi 越高越清晰，但文件越大）
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        img_path = output_path / f"page_{i:03d}.png"
        pix.save(str(img_path))
        image_paths.append(str(img_path))

        print(f"  ✓ 第 {i}/{total_pages} 页")

    print(f"✅ 转换完成，共 {len(image_paths)} 张图片\n")
    return image_paths


def cleanup_images(image_dir: str = "temp_images"):
    """清理临时图片文件"""
    import shutil

    path = Path(image_dir)
    if path.exists():
        shutil.rmtree(path)
        print(f"🧹 已清理临时文件：{image_dir}")
