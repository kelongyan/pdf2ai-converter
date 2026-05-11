# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

PDF2AI Converter renders PDF pages to images, sends them to an OpenAI-compatible vision model, and writes Markdown (`.md`) or Word (`.docx`) output. It ships three interfaces: two CLI pipelines (`main.py`, `main_word.py`), a Rich/Tkinter interactive launcher (`launcher.py`), and a Web UI backed by FastAPI + React.

The project is Windows-oriented: PowerShell scripts bootstrap the environment, and Python entrypoints switch the console to UTF-8 before printing progress.

## Common commands

```powershell
# Create and activate the virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt

# Start the interactive CLI launcher
.\start.ps1

# Start the Web UI (FastAPI + built React frontend)
.\start_web.ps1

# Start the Web UI in dev mode (hot-reload, no browser auto-open)
python server.py --dev

# Frontend dev server (proxies /api to localhost:8000)
cd web && npm install && npm run dev

# Convert a PDF to Markdown
python main.py paper.pdf
python main.py paper.pdf output.md
python main.py paper.pdf --resume

# Convert a PDF to Word
python main_word.py paper.pdf
python main_word.py paper.pdf output.docx precise
python main_word.py paper.pdf output.docx fast
python main_word.py paper.pdf output.docx precise --resume

# Run the full test suite
python -m pytest tests

# Run a single test file
python -m pytest tests\test_main.py

# Run a single test case
python -m pytest tests\test_main_word.py -k cached_pages

# Basic syntax check for first-party Python files
python -m compileall main.py main_word.py launcher.py config_manager.py config_defaults.py config_validator.py cache_manager.py pipeline_utils.py pdf_processor.py quality_checker.py models tests api server.py
```

No committed formatter or linter configuration exists. Verification is test-first: run the targeted pytest file(s), then use `python -m compileall` if you touched entrypoints or import wiring.

## Configuration

Runtime configuration is read from `config.yaml`; `config.yaml.example` is the template. `config_validator.py` normalizes and validates values against defaults from `config_defaults.py`, so new config fields must be added in both places.

Important config groups:

- `model.type`, `model.name`, `model.api_key`, `model.base_url` — vision model connection.
- `pdf.dpi` — PyMuPDF render resolution.
- `rendering.image_format`, `rendering.jpeg_quality` — page image encoding.
- `processing.concurrency` — parallel page processing.
- `cache.enabled`, `cache.prompt_version` — page-level cache invalidation.
- `api.timeout`, `api.max_retries`, `api.retry_delay` — model request behavior.
- `output.cleanup_images`, `output.add_page_separator` — artifact management.

The launcher stores named API profiles in `.config.json` via `ConfigManager`, then writes the selected profile into `config.yaml` through `build_config_for_profile()`. The stored API key is only base64-encoded; treat `.config.json` and `config.yaml` as sensitive local files.

## Architecture

### CLI pipelines share core helpers

`main.py` (Markdown) and `main_word.py` (Word) follow the same flow:

1. Load and validate `config.yaml`.
2. Render PDF into per-page images via `pdf_processor.pdf_to_images()`.
3. Build a vision model via `pipeline_utils.build_vision_model()`.
4. Reuse page-level cache entries through `cache_manager.CacheManager`.
5. Process uncached pages (optionally in parallel) via `pipeline_utils.run_pending_pages()`.
6. Write final output and optionally clean up temp images.

If behavior must stay consistent across both outputs, check both entrypoints.

### Centralized plumbing in pipeline_utils.py

- `build_vision_model()` wires config into `OpenAICompatibleModel`.
- `build_cache_manager()` toggles caching on/off.
- `run_pending_pages()` handles serial vs threaded execution and re-sorts results by page order.
- Failure detection: `is_failed_markdown_page()` checks for `[处理失败：` prefix; `is_failed_word_page()` checks for `[第 N 页处理失败` in a single-element page payload.
- Resume gates (`should_retry_*`) depend on these markers. If you change failure payloads or cache formats, update both detection and retry helpers.

### Model adapter has two prompt styles

`models/openai_compatible.py` (the only concrete `VisionModel`) exposes:

- `process_page(image_path, context="")` — Markdown conversion with continuity context.
- `process_page_with_prompt(image_path, prompt)` — Word extraction with caller-supplied JSON prompt.

Keep both paths working when changing model abstractions.

### Word generation is two-stage

`models/word_generator.py`:

1. Asks the vision model for structured JSON per page.
2. Converts JSON into a Word document with `python-docx`.

`fast` mode extracts content structure only. `precise` mode adds style metadata (font, size, color, alignment). If precise-mode JSON parsing fails, it falls back to the fast-mode prompt for that page.

### Cache key semantics

Cache keys incorporate: PDF file hash, page number, model name, output mode (`markdown` / `word-fast` / `word-precise`), DPI, image format, and `prompt_version`. If you change prompt semantics or output structure, bump `cache.prompt_version`.

### Web UI (Phase 1 + Phase 2)

The Web UI is a separate interface layer that reuses the same CLI pipeline functions:

**Backend** (`api/`): FastAPI app created in `api/app.py`, mounted via `server.py` (uvicorn). Routes:
- `POST /api/upload` — accepts PDF, stores in `uploads/{file_id}/input.pdf`.
- `POST /api/convert` — creates a task, runs conversion in background via `asyncio.create_task`.
- `GET/DELETE /api/tasks/{id}` — task CRUD.
- `GET /api/tasks/{id}/download` — serves result file.
- `GET /api/tasks/{id}/preview` — returns Markdown content.
- `CRUD /api/config/profiles` — manages API profiles (same `ConfigManager`).
- `POST /api/config/test-connection` — validates API key by sending a minimal chat completion.
- `WS /api/ws/progress` — broadcasts real-time per-page progress events.

Task state is in-memory (`api/services/task_manager.py`). The task manager constructs a `progress_callback` and passes it to `main()` / `main_word.main()` via `asyncio.to_thread()`. The callback uses `asyncio.run_coroutine_threadsafe()` to broadcast from the worker thread back to the event loop.

**Frontend** (`web/`): React 19 + TypeScript + Vite + Tailwind CSS 4 + Zustand + Framer Motion. The Vite dev server proxies `/api` to `localhost:8000`. Production builds go to `web/dist/` and are served as static files by FastAPI.

Key Phase 2 frontend features:
- Spring-physics progress bar with ETA estimation (sliding window of recent page times).
- Markdown preview panel (react-markdown + remark-gfm + rehype-katex + rehype-highlight).
- Dark/light theme toggle (localStorage-persisted, inline script prevents flash).
- Connection test UI on settings page.
- Framer Motion animations: stagger entrance, AnimatePresence panel transitions.

### Progress callback contract

Both `main.py` and `main_word.py` accept an optional `progress_callback` parameter. When provided, it is called with a dict at key points:

```python
progress_callback({
    "type": "rendering_done" | "page_done" | "writing" | "all_done",
    "phase": "processing" | "writing" | "done",
    "current_page": int,
    "total_pages": int,
    "cached_pages": int,
    "failed_pages": list[int],
    "message": str,
})
```

`pipeline_utils.run_pending_pages()` accepts `on_page_done(page_num, total_pages)` to fire after each page completes. CLI callers pass no callback; behavior is unchanged.

### Launcher is a thin orchestrator

`launcher.py` manages profiles, file/folder pickers, and shells out to `main.py` / `main_word.py` using the virtualenv Python. `tests/test_launcher.py` locks down the orchestration contract (output suffix, skip logic, resume flag forwarding).

### Profile storage only materializes part of runtime config

Launcher-managed profiles override model credentials plus `dpi` and `chunk_size`. Most runtime settings come from defaults or direct `config.yaml` edits. If you add a user-facing config option, wire it through both profile storage and config materialization.

## Tests

The pytest suite covers pipeline behavior, not end-to-end API calls:

- `tests/test_main.py` — Markdown pipeline ordering, cache hits, resume, failed-page reporting.
- `tests/test_main_word.py` — Word pipeline behavior.
- `tests/test_launcher.py` — launcher orchestration contract.
- `tests/test_word_generator.py` — prompt selection, JSON cleanup, fallback.
- `tests/test_openai_compatible.py` — retry behavior, failed-page tracking.
- `tests/test_config_validator.py`, `tests/test_cache_manager.py` — config normalization, cache keys.
- `tests/test_quality_and_cleanup.py` — quality checker, temp-image cleanup.

Most tests monkeypatch model, cache, and renderer layers. Keep those seams injectable.

## Implementation notes

- Keep CLI behavior aligned with README examples and PowerShell-first setup.
- Avoid treating `venv/`, `.claude/worktrees/`, `web/node_modules/`, or `uploads/` as source.
- Temporary page images use `tempfile.mkdtemp()`, deleted only when `output.cleanup_images` is true.
- `quality_checker.py` only applies to Markdown output; Word has no parallel quality-pass stage.
- The Web UI task manager writes `config.yaml` before each conversion (from the last-used profile), so concurrent Web UI tasks can race on config. This is a known limitation.
- `progress_callback` runs in a worker thread; any async broadcast must use `asyncio.run_coroutine_threadsafe()`.
- The `on_page_done` parameter in `run_pending_pages()` is optional and backward-compatible; existing tests pass without it.
