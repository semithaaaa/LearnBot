# LearnBot

A lightweight hybrid AI educational platform — convert documents into concise summaries, interactive quizzes, flashcards, and voice-assisted tutoring. This repository contains the Python backend, evaluation tools, and a small static frontend UI for demoing features locally.

--

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start (Windows)](#quick-start-windows)
	- [Create a virtual environment](#create-a-virtual-environment)
	- [Run the API server](#run-the-api-server)
	- [Open the UI](#open-the-ui)
- [API Reference](#api-reference)
- [Data, Models & Configuration](#data-models--configuration)
- [Directory Structure](#directory-structure)
- [CI & Publishing](#ci--publishing)
- [Contributing](#contributing)
- [License](#license)

--

## Project Overview

`LearnBot` provides tools to summarize long texts/PDFs, generate multiple question formats (MCQs, True/False, Fill-in-the-blank, Flashcards) from source material, and expose an optional Gemini-backed voice/chat interface when a `GEMINI_API_KEY` is configured.

The project is useful for educators, students, and writers who want fast study aids and automated evaluation tooling.

## Features

- Abstractive summarization (Transformer-based, BART by default)
- Multi-format quiz generation via `QuizGenerator` (`quiz_generation.py`)
- Simple voice/chat endpoint powered by Google Gemini (optional; requires `GEMINI_API_KEY`)
- File upload support (PDF -> text extraction) and image OCR (Gemini or EasyOCR)
- Evaluation/benchmarking scripts with plotting in `evaluate_models.py`
- Minimal, responsive demo UI in `ui/` (static HTML/CSS/JS)

## Tech Stack

- Python 3.8+
- FastAPI (backend HTTP API)
- Hugging Face Transformers (BART / mT5 models)
- spaCy + PyTextRank for extractive baselines and NLP preprocessing
- Optional: EasyOCR for local OCR; Google Gemini (via `google.genai`) for cloud features
- Frontend: Vanilla HTML/JS with Tailwind CSS (static)

## Quick Start (Windows)

Prerequisites: Python 3.8+, Git. For UI work you only need a browser; Node is optional.

### Create a virtual environment

Open PowerShell in the repository root and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
# (optional) Create a requirements.txt if it doesn't exist
# pip freeze > requirements.txt
if (Test-Path requirements.txt) { pip install -r requirements.txt }
```

### Run the API server

Start the FastAPI app (development mode):

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs to explore the API with the built-in Swagger UI.

### Open the UI

The UI is static and located in the `ui/` folder. To test locally simply open `ui/index.html` in your browser, or run a quick static server (recommended):

```powershell
cd ui
python -m http.server 8001
# then open http://127.0.0.1:8001 in your browser
```

The UI expects the API at `http://127.0.0.1:8000` by default (see `ui/app.js`).

## API Reference

Key endpoints (all `POST`):

- `/summarize` — Provide `text` (form field) or a PDF file (multipart `file`) to receive an abstractive summary.
	- Example (curl):

```bash
curl -X POST -F "text=Your long text here" http://127.0.0.1:8000/summarize
```

- `/generate-quizzes` — Provide `text` or `file` and optional form counts: `num_mcq`, `num_tf`, `num_fib`, `num_flash`.

- `/api/voice-chat` — Chat/voice assistant using Gemini. Requires `GEMINI_API_KEY` environment variable.

- `/extract-image` — Upload an image and get extracted text (supports `ocr_model` form field: `gemini` or `easyocr`).

See the interactive API docs at `/docs` for complete schemas and examples.

## Data, Models & Configuration

- Model artifacts: the code looks for a local summarization model at `output/saved_summarization_model` (or `./saved_summarization_model`). If not found, the code falls back to `facebook/bart-large-cnn` from Hugging Face.
- Environment variables:
	- `GEMINI_API_KEY` — (optional) Gemini API key used by voice/image endpoints. If unset, those features will raise a warning and remain disabled.

Notes on resources: transformer models are large — running them on CPU can be slow. Use a CUDA-enabled GPU for reasonable throughput.

## Directory Structure

Top-level layout (important files):

- `main.py` — FastAPI application exposing summarization, quiz generation, voice/chat and OCR endpoints.
- `quiz_generation.py` — `QuizGenerator` class: generates MCQs, True/False, Fill-in-the-blank, and flashcards using spaCy + a seq2seq model.
- `evaluate_models.py` — scripts to benchmark summarization and quiz generation, save CSV/JSON outputs, and generate plots (uses local `OUTPUT_DIR`).
- `code.ipynb` — exploratory notebook and demos.
- `ui/` — static demo UI: `index.html`, `app.js`, `style.css`.
- `output/` — runtime outputs and evaluation artifacts (CSV/JSON/plots).
- `publish.ps1` — helper PowerShell script that uses GitHub CLI (`gh`) to create a repo and push the current code.
- `.github/workflows/python-app.yml` — GitHub Actions workflow for basic CI testing.

## CI & Publishing

- A basic GitHub Actions workflow is included at `.github/workflows/python-app.yml` to run tests/validation on pushes and PRs.
- To create and push a GitHub repository automatically (requires `gh`):

```powershell
.\publish.ps1 -repoName "my-learnbot" -visibility public -description "LearnBot project"
```

Or create a repo manually and push your `main` branch.

## Contributing

Contributions are welcome. A suggested workflow:

1. Fork the repo and create a feature branch.
2. Add or update tests where appropriate.
3. Submit a pull request with a clear description of changes.

If you plan to add heavy-weight models or new external data paths, please update `README.md` and add notes about expected resources.

## License

This project is licensed under the MIT License — see the `LICENSE` file.

--

If you'd like, I can also:

- Add a `requirements.txt` inferred from the code.
- Generate a short demo script that runs a local example through `/summarize` and `/generate-quizzes`.
- Expand the API docs inside this README with live example requests for PowerShell.

Tell me which of the above you want next, or suggest edits to the wording/layout.
