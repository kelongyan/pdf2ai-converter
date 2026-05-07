from typing import List
import base64
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from .base import VisionModel


class OpenAICompatibleModel(VisionModel):
    """OpenAI 兼容接口的模型适配器（支持 GPT-4V、国内大模型等）"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "gpt-4o",
        chunk_size: int = 10,
    ):
        """初始化模型

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
            chunk_size: 分段处理大小（每次处理多少页）
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.chunk_size = chunk_size

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def process_page(self, image_path: str, context: str = "") -> str:
        """处理单页 PDF 图片"""
        image_base64 = self._encode_image(image_path)

        prompt = """请将这页 PDF 内容转换为 Markdown 格式，要求：

1. **去除无关内容**：删除页眉、页脚、页码、水印等
2. **保留关键信息**：正文、标题、列表、表格、图片说明
3. **格式规范**：
   - 标题用 # ## ### 表示层级
   - 列表用 - 或 1. 2. 3.
   - 表格用 Markdown 表格语法
   - 代码块用 ```
   - 公式用 LaTeX 语法（$...$）
4. **保持连贯**：如果段落被截断，不要添加额外的分隔符

直接输出 Markdown，不要添加任何解释或说明。"""

        if context:
            prompt += f"\n\n**上文末尾内容**（用于判断是否需要续接）：\n{context}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                },
                            },
                        ],
                    }
                ],
                max_tokens=4096,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ 处理失败：{e}")
            return f"[处理失败：{image_path}]"

    def process_batch(self, images: List[str]) -> str:
        """批量处理多页，支持分段和进度条"""
        total_pages = len(images)
        results = []
        context = ""

        # 判断是否需要分段
        if total_pages > self.chunk_size:
            print(
                f"📦 文档较长（{total_pages} 页），将分 {(total_pages + self.chunk_size - 1) // self.chunk_size} 段处理\n"
            )

        # 使用 tqdm 进度条
        with tqdm(total=total_pages, desc="🚀 处理进度", unit="页") as pbar:
            for i, img_path in enumerate(images):
                # 每处理完一个分段，清空上下文（避免上下文过长）
                if i > 0 and i % self.chunk_size == 0:
                    context = ""
                    print(f"\n✂️  分段 {i // self.chunk_size} 完成，开始下一段...\n")

                markdown = self.process_page(img_path, context)
                results.append(markdown)

                # 更新上下文（保留最后 200 字符）
                context = markdown[-200:] if len(markdown) > 200 else markdown

                # 更新进度条
                pbar.update(1)

        return "\n\n---\n\n".join(results)
