from pathlib import Path

from launcher import MARKDOWN_SUFFIX, PDFConverter, WORD_SUFFIX


class FakeCompletedProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode


class FakeProfileManager:
    def __init__(self):
        self.saved_profiles = []


class DummyPrompt:
    responses = []

    @classmethod
    def ask(cls, *args, **kwargs):
        return cls.responses.pop(0)


class RecordingConsole:
    def __init__(self):
        self.messages = []

    def print(self, message="", *args, **kwargs):
        self.messages.append(str(message))


class ConverterHarness(PDFConverter):
    def __init__(self):
        self.config_manager = FakeProfileManager()
        self.current_profile = {
            "name": "demo",
            "api_url": "https://example.test/v1",
            "api_key": "secret",
            "model": "demo-model",
            "dpi": 150,
            "chunk_size": 10,
        }
        self.updated = 0

    def update_config_file(self):
        self.updated += 1



def test_get_output_path_uses_format_suffix(tmp_path):
    converter = ConverterHarness()
    pdf_path = tmp_path / "sample.pdf"

    assert converter.get_output_path(str(pdf_path), "markdown") == str(pdf_path.with_suffix(MARKDOWN_SUFFIX))
    assert converter.get_output_path(str(pdf_path), "word") == str(pdf_path.with_suffix(WORD_SUFFIX))



def test_should_skip_output_checks_existing_file(tmp_path):
    converter = ConverterHarness()
    pdf_path = tmp_path / "sample.pdf"
    output_path = pdf_path.with_suffix(MARKDOWN_SUFFIX)
    pdf_path.write_bytes(b"%PDF-1.4")

    assert converter.should_skip_output(str(pdf_path), "markdown") is False

    output_path.write_text("done", encoding="utf-8")
    assert converter.should_skip_output(str(pdf_path), "markdown") is True



def test_process_file_markdown_returns_success_result(tmp_path, monkeypatch):
    converter = ConverterHarness()
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    commands = []

    monkeypatch.setattr("launcher.subprocess.run", lambda cmd, check=True: commands.append(cmd) or FakeCompletedProcess())

    result = converter.process_file(str(pdf_path), "markdown")

    expected_output = str(pdf_path.with_suffix(MARKDOWN_SUFFIX))
    assert converter.updated == 1
    assert commands == [[str(Path("venv/Scripts/python.exe")), "main.py", str(pdf_path), expected_output]]
    assert result == {
        "status": "success",
        "pdf_path": str(pdf_path),
        "output_path": expected_output,
        "mode": None,
    }



def test_process_file_markdown_resume_appends_flag(tmp_path, monkeypatch):
    converter = ConverterHarness()
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    commands = []

    monkeypatch.setattr("launcher.subprocess.run", lambda cmd, check=True: commands.append(cmd) or FakeCompletedProcess())

    result = converter.process_file(str(pdf_path), "markdown", resume=True)

    expected_output = str(pdf_path.with_suffix(MARKDOWN_SUFFIX))
    assert commands == [[str(Path("venv/Scripts/python.exe")), "main.py", str(pdf_path), expected_output, "--resume"]]
    assert result == {
        "status": "success",
        "pdf_path": str(pdf_path),
        "output_path": expected_output,
        "mode": None,
    }



def test_process_file_word_uses_selected_mode(tmp_path, monkeypatch):
    converter = ConverterHarness()
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    commands = []
    DummyPrompt.responses = ["1"]

    monkeypatch.setattr("launcher.Prompt", DummyPrompt)
    monkeypatch.setattr("launcher.subprocess.run", lambda cmd, check=True: commands.append(cmd) or FakeCompletedProcess())

    result = converter.process_file(str(pdf_path), "word")

    expected_output = str(pdf_path.with_suffix(WORD_SUFFIX))
    assert commands == [[str(Path("venv/Scripts/python.exe")), "main_word.py", str(pdf_path), expected_output, "fast"]]
    assert result == {
        "status": "success",
        "pdf_path": str(pdf_path),
        "output_path": expected_output,
        "mode": "fast",
    }



def test_process_file_word_resume_appends_flag(tmp_path, monkeypatch):
    converter = ConverterHarness()
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")
    commands = []
    DummyPrompt.responses = ["2"]

    monkeypatch.setattr("launcher.Prompt", DummyPrompt)
    monkeypatch.setattr("launcher.subprocess.run", lambda cmd, check=True: commands.append(cmd) or FakeCompletedProcess())

    result = converter.process_file(str(pdf_path), "word", resume=True)

    expected_output = str(pdf_path.with_suffix(WORD_SUFFIX))
    assert commands == [[str(Path("venv/Scripts/python.exe")), "main_word.py", str(pdf_path), expected_output, "precise", "--resume"]]
    assert result == {
        "status": "success",
        "pdf_path": str(pdf_path),
        "output_path": expected_output,
        "mode": "precise",
    }



def test_process_folder_skips_existing_outputs_and_prints_summary(tmp_path, monkeypatch):
    converter = ConverterHarness()
    console = RecordingConsole()
    pdf1 = tmp_path / "a.pdf"
    pdf2 = tmp_path / "b.pdf"
    pdf3 = tmp_path / "c.pdf"
    for pdf in [pdf1, pdf2, pdf3]:
        pdf.write_bytes(b"%PDF-1.4")

    pdf1.with_suffix(MARKDOWN_SUFFIX).write_text("done", encoding="utf-8")

    processed = []

    def fake_process_file(pdf_path, output_format, resume=False):
        processed.append((pdf_path, output_format, resume))
        if Path(pdf_path).name == "b.pdf":
            return {
                "status": "success",
                "pdf_path": pdf_path,
                "output_path": str(Path(pdf_path).with_suffix(MARKDOWN_SUFFIX)),
                "mode": None,
            }
        return {
            "status": "failed",
            "pdf_path": pdf_path,
            "output_path": str(Path(pdf_path).with_suffix(MARKDOWN_SUFFIX)),
            "mode": None,
            "error": "boom",
        }

    monkeypatch.setattr("launcher.console", console)
    monkeypatch.setattr(ConverterHarness, "process_file", staticmethod(fake_process_file))

    results = converter.process_folder(str(tmp_path), "markdown")

    assert [item["status"] for item in results] == ["skipped", "success", "failed"]
    assert processed == [
        (str(pdf2), "markdown", False),
        (str(pdf3), "markdown", False),
    ]
    joined = "\n".join(console.messages)
    assert "跳过已完成文件：a.md" in joined
    assert "汇总：总数=3，成功=1，跳过=1，失败=1" in joined
    assert "失败文件：" in joined
    assert "c.pdf: boom" in joined



def test_process_folder_resume_does_not_skip_existing_outputs(tmp_path, monkeypatch):
    converter = ConverterHarness()
    console = RecordingConsole()
    pdf1 = tmp_path / "a.pdf"
    pdf2 = tmp_path / "b.pdf"
    for pdf in [pdf1, pdf2]:
        pdf.write_bytes(b"%PDF-1.4")

    pdf1.with_suffix(MARKDOWN_SUFFIX).write_text("done", encoding="utf-8")

    processed = []

    def fake_process_file(pdf_path, output_format, resume=False):
        processed.append((pdf_path, output_format, resume))
        return {
            "status": "success",
            "pdf_path": pdf_path,
            "output_path": str(Path(pdf_path).with_suffix(MARKDOWN_SUFFIX)),
            "mode": None,
        }

    monkeypatch.setattr("launcher.console", console)
    monkeypatch.setattr(ConverterHarness, "process_file", staticmethod(fake_process_file))

    results = converter.process_folder(str(tmp_path), "markdown", resume=True)

    assert [item["status"] for item in results] == ["success", "success"]
    assert processed == [
        (str(pdf1), "markdown", True),
        (str(pdf2), "markdown", True),
    ]
    joined = "\n".join(console.messages)
    assert "批量恢复模式" in joined
    assert "跳过已完成文件" not in joined
