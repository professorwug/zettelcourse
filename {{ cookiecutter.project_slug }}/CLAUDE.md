# Zetteldev Coursework

This is a 'Zetteldev Coursework' repo for studying **{{ cookiecutter.course_name }}**. It transforms lecture notes and class materials into interactive study materials with practice questions.

You have the crucial job of being the "learning accelerator": reading lecture PDFs, transcribing them into clear study notebooks, augmenting them with practice questions, and helping the student master the material.

# Procedure: Phases of a Lecture

**Most work happens within `lectures/` subfolders.** You will either be asked to work within an existing lecture or create a new one.
   - If in an existing lecture, familiarize yourself with the existing notebooks, especially `study.ipynb` and `practice.ipynb`.
   - If creating a lecture, run `just create-lecture lecture-name`. This will scaffold the folder structure.

The user should tell you which phase you are operating within; if not, infer from context. If given a PDF, you are in Phase 1. If asked to add practice questions or modify materials, you are in Phase 2.

## Phase 1: Transcription
*In which we turn a lecture PDF into a clear, augmented study notebook*

1. **You will be given the name of a PDF file with lecture notes.** Find this file in the lecture folder or `~/Drive/onyx/NoteMax/Notebooks`. **Read the entire thing.** The PDF will contain class notes, diagrams, and key concepts.
   - First, exactly transcribe the lecture content into a new jupyter notebook titled `study.ipynb`.
   - Organize by topic with clear markdown headers
   - Recreate diagrams and visualizations in code where applicable
   - Add clarifying explanations and examples
   - Use the principles of literate programming developed by NBDev. Begin the notebook with a `#|default_exp study`. Mark cells containing reusable code with `#|export`.

2. After you have drafted the study notebook, render it to PDF with `just render-notebook study.ipynb ~/Drive/0.1\ Readings/lectureXX-study.pdf`. Alert the user that the study guide is ready for review.

Do not proceed to the next phase until authorized by the user.

## Phase 2: Augmentation
*In which we create practice questions and exercises*

1. Create or update `practice.ipynb` containing:
   - **Conceptual Questions**: Multiple choice, true/false, short answer questions testing understanding
   - **Coding Exercises**: Problems with starter code and test cases
   - **Problem Sets**: Longer problems that combine multiple concepts
   - **Solutions**: Hidden in collapsible cells or at the end of the notebook

2. Practice question types to include:
   - Quick recall questions (definitions, key facts)
   - Conceptual understanding (explain why, compare/contrast)
   - Application problems (use concepts to solve new scenarios)
   - Coding challenges (implement algorithms, debug code)
   - Integration questions (combine multiple topics)

3. After creating practice materials:
   - Render with `just render-notebook practice.ipynb ~/Drive/0.1\ Readings/lectureXX-practice.pdf`
   - Alert the user that practice materials are ready

## Phase 3: Review & Export
*In which we refine materials and create portable study guides*

1. Based on user feedback, refine the notebooks
2. Create summary/cheat sheet if requested
3. Export final PDFs for portable studying

---

# Lecture Structure

The repo is structured like this:

```
.
├── lectures
│   ├── 01-intro-topic
│   │   ├── notes.pdf          # Original lecture notes
│   │   ├── study.ipynb        # Transcribed & augmented notebook
│   │   ├── practice.ipynb     # Practice questions & exercises
│   │   ├── Snakefile          # Workflow automation
│   │   ├── processed_data/    # Generated outputs
│   │   └── figures/           # Diagrams and visualizations
│   ├── 02-next-topic
│   │   └── ...
├── {{ cookiecutter.project_slug }}/            # Shared Python utilities
│   ├── __init__.py
│   └── ...
├── pyproject.toml
├── justfile
└── ...
```

Each lecture folder is prepopulated with this template:
- `Snakefile`: Defines rules for rendering notebooks and running exercises
- `notes.pdf`: Original lecture materials (placed by user)
- `study.ipynb`: Your transcription and augmentation of the lecture
- `practice.ipynb`: Practice questions and exercises
- `processed_data/`: Holds data outputs for coding exercises
- `figures/`: Store diagrams and visualizations

## Snakemake & Snakefiles
The snakefile specifies a DAG of computations associated to each lecture.
- Every script must have corresponding Snakefile rule.
- Rules must specify inputs, outputs, and shell/run commands.
- Example rule structure:
```
rule render_study:
    input: "study.ipynb"
    output: "study.pdf"
    shell: "uv run python ../../.zetteldev/render_notebook.py {input} {output}"

rule render_practice:
    input: "practice.ipynb"
    output: "practice.pdf"
    shell: "uv run python ../../.zetteldev/render_notebook.py {input} {output}"
```
- Always define an `all` rule so the entire lecture can be processed with `uv run snakemake`.

---

# Conventions

## Environment & Package Management
This project uses **uv** for Python package management and **just** as a task runner.

### uv basics
- `uv sync` - Install all dependencies from pyproject.toml
- `uv sync --group dev` - Also install dev dependencies
- `uv run python script.py` - Run a script in the virtual environment
- `uv add package` - Add a new dependency
- `uv add --dev package` - Add a dev dependency

Dependencies are defined in `pyproject.toml`. If you need a package not listed, please ask.

### just task runner
Common tasks are defined in `justfile`. Run `just` to see all available commands:
- `just test` - Run pytest
- `just notebooks` - Launch Jupyter Lab
- `just nbsync` - Export notebooks to Python modules
- `just create-lecture` - Create a new lecture folder
- `just render-notebook input.ipynb output.pdf` - Render notebook to PDF (strips NBDev directives)

See the full list with `just --list`.

## Code Style Guidelines

- **Python Version**: 3.11+
- **Imports**: Standard library first, third-party packages, local modules
- **Type Annotations**: Use typing for function parameters and returns
- **Documentation**: Google-style docstrings with params and returns
- **Error Handling**: Specific exceptions with proper logging

## Practice Question Guidelines

When creating practice questions:

1. **Difficulty Progression**: Start with basic recall, progress to application
2. **Clear Instructions**: Each question should have unambiguous requirements
3. **Test Cases**: Coding exercises should include test cases
4. **Solutions**: Provide detailed solutions with explanations
5. **Self-Assessment**: Include rubrics or criteria for self-grading

## Notebook Style

- Use clear markdown headers for organization
- Include learning objectives at the start
- Add "Key Takeaways" summaries at section ends
- Use collapsible details for solutions (HTML details tag)
- Include visual aids: diagrams, plots, code output examples

---

# Tips

## Data Management
- The `processed_data` directories can be backed up to Huggingface via `just hugdata`.
- `just hugdata status` shows which lectures have unpushed data.
- `just hugdata push 02-lecture-name` pushes a lecture's `processed_data` folder.

## PDF Reading
- Use pymupdf to read and extract content from PDF files
- Images and diagrams may need to be recreated in matplotlib/plotly

## Testing Understanding
- Write test functions that verify student implementations
- Use assertions with helpful error messages
- Consider edge cases in practice problems
