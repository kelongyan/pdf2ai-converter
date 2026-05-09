import base64
import time
from openai import OpenAI
from .base import VisionModel


class OpenAICompatibleModel(VisionModel):
    """OpenAI 兼容接口的模型适配器（支持 GPT-4V、国内大模型等）"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "gpt-4o",
        chunk_size: int = 10,
        timeout: float = 60,
        max_retries: int = 2,
        retry_delay: float = 1,
        debug: bool = False,
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self.model = model
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.debug = debug

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _send_image_prompt(self, image_path: str, prompt: str) -> str:
        image_base64 = self._encode_image(image_path)

        for attempt in range(self.max_retries + 1):
            try:
                if self.debug:
                    print(
                        f"🔍 调试：请求模型={self.model} timeout={self.timeout}s attempt={attempt + 1}/{self.max_retries + 1}"
                    )

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
                if not self._should_retry(e, attempt):
                    raise
                delay = self.retry_delay * (2 ** attempt)
                if self.debug:
                    print(f"🔍 调试：请求失败，将在 {delay:.1f}s 后重试，原因：{e}")
                time.sleep(delay)

        raise RuntimeError("请求失败：已达到最大重试次数")

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False

        status_code = getattr(error, "status_code", None)
        if status_code == 429 or (isinstance(status_code, int) and 500 <= status_code < 600):
            return True

        error_name = error.__class__.__name__.lower()
        if "timeout" in error_name:
            return True

        message = str(error).lower()
        return "timeout" in message

    def process_page(self, image_path: str, context: str = "") -> str:
        """处理单页 PDF 图片"""
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
            return self._send_image_prompt(image_path, prompt)
        except Exception as e:
            print(f"❌ 处理失败：{e}")
            return f"[处理失败：{image_path}]"

    def process_page_with_prompt(self, image_path: str, prompt: str) -> str:
        """使用自定义提示词处理单页 PDF 图片"""
        try:
            return self._send_image_prompt(image_path, prompt)
        except Exception as e:
            print(f"❌ 处理失败：{e}")
            return f"[处理失败：{image_path}]"
