from abc import ABC, abstractmethod


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
