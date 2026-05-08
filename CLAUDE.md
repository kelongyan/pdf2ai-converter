# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is a Python CLI tool that renders PDF pages to images, sends them to an OpenAI-compatible vision model, and writes either Markdown (`.md`) or Word (`.docx`) output. The project is Windows-oriented: the documented setup uses PowerShell, `start.ps1` bootstraps the launcher from `venv\Scripts\python.exe`, and the Python entrypoints switch the Windows console to UTF-8 before printing progress.

## Common commands

```powershell
# Create and activate the virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all dependencies, including pytest
pip install -r requirements.txt

# Start the interactive launcher
.\start.ps1

# Convert a PDF to Markdown
python main.py paper.pdf
python main.py paper.pdf output.md

# Convert a PDF to Word
python main_word.py paper.pdf
python main_word.py paper.pdf output.docx precise
python main_word.py paper.pdf output.docx fast

# Run the full test suite
python -m pytest tests

# Run a single test file
python -m pytest tests\test_main.py

# Run a single test case
python -m pytest tests\test_main_word.py -k cached_pages

# Basic syntax check for first-party Python files
python -m compileall main.py main_word.py launcher.py config_manager.py config_defaults.py config_validator.py cache_manager.py pipeline_utils.py pdf_processor.py quality_checker.py models tests
```

The repository now includes a pytest suite under `tests/`. There is still no committed formatter or linter configuration, so verification is test-first: run the targeted pytest file(s), then use `python -m compileall ...` if you touched entrypoints or import wiring.

## Configuration

Runtime configuration is read from `config.yaml`; `config.yaml.example` is the current template. `config_validator.py` normalizes and validates config values against defaults from `config_defaults.py`, so new config fields must usually be added in both places.

Important config groups:

- `model.type`, `model.name`, `model.api_key`, `model.base_url` for the OpenAI-compatible vision model.
- `pdf.dpi` for PyMuPDF render resolution.
- `rendering.image_format` and `rendering.jpeg_quality` for generated page images.
- `processing.concurrency` for parallel processing of uncached pages.
- `cache.enabled` and `cache.prompt_version` for page-level cache invalidation.
- `api.timeout`, `api.max_retries`, `api.retry_delay` for model request behavior.
- `output.cleanup_images` and `output.add_page_separator` for generated artifacts.

The interactive launcher stores named API profiles in `.config.json` via `ConfigManager`, then writes the selected profile into `config.yaml` through `build_config_for_profile()`. The stored API key is only base64-encoded, not securely encrypted; treat `.config.json` and `config.yaml` as sensitive local files.

## Architecture

### Two CLI pipelines sharing the same core helpers

There are two user-facing entrypoints:

- `main.py` runs the Markdown pipeline.
- `main_word.py` runs the Word pipeline.

Both entrypoints follow the same high-level flow:

1. Load and validate `config.yaml`.
2. Render the PDF into per-page images with `pdf_processor.pdf_to_images()`.
3. Build a vision model with `pipeline_utils.build_vision_model()`.
4. Optionally reuse page-level cache entries through `cache_manager.CacheManager`.
5. Process uncached pages, optionally in parallel, through `pipeline_utils.run_pending_pages()`.
6. Write the final output and optionally clean up the temporary image directory.

If behavior needs to stay consistent across Markdown and Word output, check both entrypoints before changing shared assumptions.

### Rendering, caching, and concurrency are centralized

`pdf_processor.py` is only responsible for PDF-to-image conversion and directory cleanup; it does not know anything about AI prompts or output formats.

`pipeline_utils.py` holds the shared plumbing that both pipelines depend on:

- `build_vision_model()` wires config values into `OpenAICompatibleModel`.
- `build_cache_manager()` toggles caching on/off from config.
- `create_image_dir()` allocates a temp directory with `tempfile.mkdtemp()`.
- `resolve_output_path()` applies default `.md` / `.docx` naming.
- `run_pending_pages()` handles serial vs threaded execution and always re-sorts results back into page order.

`cache_manager.py` caches each page independently using a key derived from the PDF file hash plus page number, model name, output mode, DPI, image format, and `prompt_version`. If you change prompt semantics or output structure, bump `cache.prompt_version` or cached results may be reused incorrectly.

### Model adapter contract has two prompt styles

`models/base.py` defines the vision-model interface. `models/openai_compatible.py` is the only concrete implementation here and uses the OpenAI Python SDK chat completions API with image data URLs.

That adapter exposes two distinct call patterns:

- `process_page(image_path, context="")` for Markdown conversion, where the second argument is continuity context from the previous page.
- `process_page_with_prompt(image_path, prompt)` for Word extraction, where the caller provides the full JSON-extraction prompt.

This split is important because older code in this project passed non-context prompts through `process_page()`. Keep both paths working when changing model abstractions.

### Word generation is a two-stage pipeline

`models/word_generator.py` does more than write `.docx` files:

1. It asks the vision model for structured JSON per page.
2. It converts that JSON into a Word document with `python-docx`.

`fast` mode only extracts content structure (headings, paragraphs, tables, lists). `precise` mode asks for additional style metadata such as font, size, color, and alignment, then applies a subset of that styling when building the document. If precise-mode JSON parsing fails, the generator deliberately falls back to the fast-mode extraction prompt for that page.

### Launcher behavior is config-driven shell orchestration

`launcher.py` is a Rich/Tkinter wrapper around the two CLI pipelines, not a separate conversion implementation. It:

- manages saved API profiles through `ConfigManager`,
- materializes the selected profile into `config.yaml`,
- chooses Markdown vs Word and single-file vs batch mode,
- then shells out to `main.py` or `main_word.py` using the virtualenv Python.

If you change CLI arguments, config fields, or output defaults in the main entrypoints, update launcher behavior too or the interactive flow will drift.

## Tests

The pytest suite is focused on pipeline behavior rather than end-to-end API calls:

- `tests/test_main.py` covers Markdown pipeline ordering, cache hits, and failed-page reporting.
- `tests/test_main_word.py` covers the analogous Word pipeline behavior.
- `tests/test_word_generator.py` covers prompt selection, JSON cleanup, and fallback behavior.
- `tests/test_openai_compatible.py` covers retry behavior and failed-page tracking in the OpenAI-compatible adapter.
- `tests/test_config_validator.py` and `tests/test_cache_manager.py` cover config normalization and cache-key behavior.
- `tests/test_quality_and_cleanup.py` covers the quality checker and temp-image cleanup.

Most tests monkeypatch the model, cache, and renderer layers, so when adding new shared pipeline behavior, keep those seams injectable rather than hard-coding external calls.

## Implementation notes

- Keep CLI behavior aligned with the README examples and PowerShell-first setup.
- Avoid treating `venv/` or `.claude/worktrees/` as source when searching the repository.
- Temporary page images are created in a fresh temp directory via `tempfile.mkdtemp()`, then deleted only when `output.cleanup_images` is true.
- The cached Word output mode is part of the cache key (`word-fast` vs `word-precise`), so mode-specific output changes should preserve that distinction.
- `quality_checker.py` only applies to Markdown output; Word conversion does not have a parallel quality-pass stage.
