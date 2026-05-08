from models.openai_compatible import OpenAICompatibleModel


class FakeRetryableError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class FakeCompletions:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    def create(self, **kwargs):
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


class FakeChoice:
    def __init__(self, content):
        self.message = type("Message", (), {"content": content})()


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeClient:
    def __init__(self, responses):
        self.chat = type("Chat", (), {"completions": FakeCompletions(responses)})()


def make_model(monkeypatch, responses, debug=False):
    model = OpenAICompatibleModel(
        api_key="key",
        base_url="https://example.test/v1",
        model="demo-model",
        chunk_size=2,
        timeout=10,
        max_retries=2,
        retry_delay=0.01,
        debug=debug,
    )
    model.client = FakeClient(responses)
    monkeypatch.setattr(model, "_encode_image", lambda image_path: "encoded")
    return model


def test_send_image_prompt_retries_then_succeeds(monkeypatch):
    model = make_model(
        monkeypatch,
        [FakeRetryableError("rate limit", status_code=429), FakeResponse("ok")],
    )
    monkeypatch.setattr("models.openai_compatible.time.sleep", lambda seconds: None)

    result = model.process_page("page.png")

    assert result == "ok"


def test_process_batch_collects_failed_pages(monkeypatch):
    model = make_model(monkeypatch, [FakeResponse("page1"), FakeResponse("page2")])
    monkeypatch.setattr(
        model,
        "process_page",
        lambda image_path, context="": "[处理失败：page.png]" if image_path == "bad.png" else "ok",
    )

    result = model.process_batch(["good.png", "bad.png"])

    assert "ok" in result
    assert model.get_failed_pages() == [{"page": 2, "reason": "[处理失败：page.png]"}]


def test_process_batch_debug_outputs_page_logs(monkeypatch, capsys):
    model = make_model(monkeypatch, [FakeResponse("ok")], debug=True)
    monkeypatch.setattr(model, "process_page", lambda image_path, context="": "ok")

    model.process_batch(["only.png"])

    captured = capsys.readouterr()
    assert "开始处理第 1 页" in captured.out
