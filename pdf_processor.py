from typing import List
from pathlib import Path
import fitz  # PyMuPDF


IMAGE_SUFFIX_MAP = {
    "png": ".png",
    "jpeg": ".jpg",
}


def pdf_to_images(
    pdf_path: str,
    output_dir: str,
    dpi: int = 150,
    image_format: str = "png",
    jpeg_quality: int = 85,
) -> List[str]:
    """将 PDF 转换为高清图片

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        dpi: 分辨率（150=标准，300=高清）
        image_format: 输出图片格式（png 或 jpeg）
        jpeg_quality: JPEG 压缩质量

    Returns:
        图片路径列表
    """
    doc = fitz.open(pdf_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    image_paths = []
    total_pages = len(doc)
    suffix = IMAGE_SUFFIX_MAP[image_format]

    print(f"📚 PDF 共 {total_pages} 页，开始转换...")

    for i, page in enumerate(doc, 1):
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)

        img_path = output_path / f"page_{i:03d}{suffix}"
        if image_format == "jpeg":
            pix.save(str(img_path), output="jpeg", jpg_quality=jpeg_quality)
        else:
            pix.save(str(img_path))
        image_paths.append(str(img_path))

        print(f"  ✓ 第 {i}/{total_pages} 页")

    print(f"✅ 转换完成，共 {len(image_paths)} 张图片\n")
    return image_paths


def cleanup_images(image_dir: str):
    """清理临时图片文件"""
    import shutil

    path = Path(image_dir)
    if path.exists():
        shutil.rmtree(path)
        print(f"🧹 已清理临时文件：{image_dir}")
