# Zettelcourse

A [cookiecutter](https://cookiecutter.readthedocs.io/) template for creating Zetteldev-powered coursework study workspaces.

## Features

- **Lecture-based organization**: Each lecture/topic gets its own folder with study and practice notebooks
- **PDF transcription workflow**: Claude reads lecture PDFs and creates augmented study materials
- **Practice questions**: Generate conceptual questions, coding exercises, and problem sets
- **Snakemake automation**: Reproducible rendering and processing workflows
- **HuggingFace sync**: Back up processed data to HuggingFace datasets
- **Full ML stack**: PyTorch, JAX, transformers, and more included by default

## Usage

```bash
# Install cookiecutter if needed
pip install cookiecutter

# Create a new coursework project
cookiecutter gh:professorwug/zettelcourse

# Or from local path
cookiecutter path/to/zettelcourse
```

You'll be prompted for:
- `course_name`: The name of your course (e.g., "Reinforcement Learning")
- `project_slug`: Auto-generated from course name (e.g., "reinforcement_learning")
- `project_description`: A brief description
- `author`: Your name
- `github`: Your GitHub username
- `email`: Your email

## Project Structure

The generated project will have this structure:

```
my_course/
├── CLAUDE.md                    # Workflow instructions for Claude
├── justfile                     # Task runner
├── pyproject.toml               # Dependencies
├── README.md                    # Project overview
├── .zetteldev/
│   ├── create_lecture.py        # Scaffold new lectures
│   ├── render_notebook.py       # PDF rendering
│   ├── hf_data.py               # HuggingFace sync
│   └── templates/               # Notebook templates
├── lectures/                    # One folder per lecture
│   └── 01-example/
│       ├── notes.pdf            # Input: lecture notes
│       ├── study.ipynb          # Transcribed study notebook
│       ├── practice.ipynb       # Practice problems
│       └── Snakefile            # Workflow automation
├── my_course/                   # Shared Python utilities
│   └── __init__.py
└── processed_data/              # Global outputs
```

## Workflow

1. **Create a lecture**: `just create-lecture`
2. **Add PDF notes**: Place the lecture PDF in the folder
3. **Work with Claude**: `just claude` to transcribe and augment
4. **Generate practice**: Claude creates exercises and solutions
5. **Export PDFs**: `just render-notebook` for portable study guides

See the generated `CLAUDE.md` for detailed instructions.
