# {{ cookiecutter.course_name }} Coursework

A Zetteldev-powered study workspace for {{ cookiecutter.course_name }} coursework.

## Overview

This project transforms lecture notes and class materials into interactive study materials:
- **Study notebooks**: Transcribed and augmented lecture content
- **Practice notebooks**: Exercises with conceptual questions, coding problems, and solutions
- **Automated workflows**: Snakemake-powered rendering and processing

## Getting Started

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Create a new lecture folder**:
   ```bash
   just create-lecture
   ```

3. **Add lecture notes**: Place the PDF in the lecture folder as `notes.pdf`

4. **Work with Claude**: From within a lecture folder:
   ```bash
   just claude
   ```

## Project Structure

```
.
├── lectures/              # One folder per lecture/topic
│   └── 01-example/
│       ├── notes.pdf      # Original lecture materials
│       ├── study.ipynb    # Transcribed study notebook
│       ├── practice.ipynb # Practice questions
│       ├── Snakefile      # Workflow automation
│       └── processed_data/
├── {{ cookiecutter.project_slug }}/          # Shared Python utilities
├── .zetteldev/            # Scaffolding tools
├── pyproject.toml         # Dependencies
└── justfile               # Task runner
```

## Common Commands

| Command | Description |
|---------|-------------|
| `just notebooks` | Launch Jupyter Lab |
| `just create-lecture` | Create new lecture folder |
| `just render-notebook <in> <out>` | Render notebook to PDF |
| `just test` | Run tests |
| `just hugdata status` | Check HuggingFace sync status |

## Workflow

1. **Phase 1 - Transcription**: Claude reads lecture PDF and creates `study.ipynb`
2. **Phase 2 - Augmentation**: Claude generates `practice.ipynb` with exercises
3. **Phase 3 - Review**: Refine materials and export final PDFs

See `CLAUDE.md` for detailed workflow instructions.
