from models.word_generator import WordGenerator


class PromptOnlyModel:
    def __init__(self, response):
        self.response = response
        self.prompt_calls = []
        self.context_calls = []

    def process_page(self, image_path, context=""):
        self.context_calls.append((image_path, context))
        return ""

    def process_page_with_prompt(self, image_path, prompt):
        self.prompt_calls.append((image_path, prompt))
        return self.response


def test_word_generator_uses_custom_prompt_for_fast_mode():
    model = PromptOnlyModel('{"elements": []}')
    generator = WordGenerator(model, mode="fast")

    result = generator.process_page_to_word("page.png", 3)

    assert result == {"elements": [], "page": 3}
    assert len(model.prompt_calls) == 1
    assert model.context_calls == []
    assert "返回 JSON 格式" in model.prompt_calls[0][1]


def test_word_generator_strips_json_code_fence():
    model = PromptOnlyModel('```json\n{"elements": [{"type": "paragraph", "content": "正文"}]}\n```')
    generator = WordGenerator(model, mode="fast")

    result = generator.process_page_to_word("page.png", 1)

    assert result["page"] == 1
    assert result["elements"] == [{"type": "paragraph", "content": "正文"}]


def test_word_generator_falls_back_when_precise_json_invalid():
    model = PromptOnlyModel("not json")
    generator = WordGenerator(model, mode="precise")

    result = generator.process_page_to_word("page.png", 2)

    assert result["page"] == 2
    assert result["elements"][0]["content"] == "[第 2 页处理失败]"
    assert len(model.prompt_calls) == 2
