from abc import ABC, abstractmethod
from typing import List

class VisionModel(ABC):
    """视觉模型抽象基类"""

    @abstractmethod
    def process_page(self, image_path: str, context: str = "") -> str:
        """处理单页 PDF 图片，返回 Markdown

        Args:
            image_path: 图片路径
            context: 上文内容（用于保持连贯性）

        Returns:
            Markdown 格式的文本
        """
        pass

    @abstractmethod
    def process_page_with_prompt(self, image_path: str, prompt: str) -> str:
        """使用自定义提示词处理单页 PDF 图片"""
        pass

    @abstractmethod
    def process_batch(self, images: List[str]) -> str:
        """批量处理多页，保持上下文连贯

        Args:
            images: 图片路径列表

        Returns:
            完整的 Markdown 文档
        """
        pass
