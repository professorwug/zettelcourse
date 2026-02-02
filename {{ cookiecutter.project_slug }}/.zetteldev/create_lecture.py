#!/usr/bin/env python3
"""Create a new lecture folder with template files.

Usage:
    python create_lecture.py [lecture-name]

If no name is provided, prompts interactively.
"""

import json
import shutil
import sys
from pathlib import Path

try:
    import questionary
except ImportError:
    questionary = None

# Constants
REPO_ROOT = Path(__file__).parent.parent
LECTURES_DIR = REPO_ROOT / "lectures"
TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_next_lecture_number() -> int:
    """Get the next lecture number based on existing folders."""
    if not LECTURES_DIR.exists():
        return 1

    existing = []
    for folder in LECTURES_DIR.iterdir():
        if folder.is_dir():
            try:
                # Extract number from folder names like "01-intro" or "12-advanced"
                num = int(folder.name.split("-")[0])
                existing.append(num)
            except (ValueError, IndexError):
                pass

    return max(existing, default=0) + 1


def slugify(name: str) -> str:
    """Convert a name to a valid folder slug."""
    return name.lower().replace(" ", "-").replace("_", "-")


def create_lecture(name: str) -> Path:
    """Create a new lecture folder with template files."""
    lecture_num = get_next_lecture_number()
    slug = slugify(name)
    folder_name = f"{lecture_num:02d}-{slug}"
    lecture_path = LECTURES_DIR / folder_name

    if lecture_path.exists():
        print(f"Error: Folder already exists: {lecture_path}")
        sys.exit(1)

    # Create directories
    lecture_path.mkdir(parents=True)
    (lecture_path / "processed_data").mkdir()
    (lecture_path / "figures").mkdir()

    # Copy template notebooks if they exist
    study_template = TEMPLATES_DIR / "study_template.ipynb"
    practice_template = TEMPLATES_DIR / "practice_template.ipynb"

    if study_template.exists():
        shutil.copy(study_template, lecture_path / "study.ipynb")
    else:
        # Create minimal study notebook
        create_minimal_notebook(lecture_path / "study.ipynb", name, "study")

    if practice_template.exists():
        shutil.copy(practice_template, lecture_path / "practice.ipynb")
    else:
        # Create minimal practice notebook
        create_minimal_notebook(lecture_path / "practice.ipynb", name, "practice")

    # Create Snakefile
    create_snakefile(lecture_path, folder_name)

    print(f"Created lecture folder: {lecture_path}")
    print(f"  - study.ipynb (transcription template)")
    print(f"  - practice.ipynb (exercises template)")
    print(f"  - Snakefile (workflow automation)")
    print(f"  - processed_data/ (outputs)")
    print(f"  - figures/ (visualizations)")
    print(f"\nNext steps:")
    print(f"  1. Add your lecture PDF as: {lecture_path}/notes.pdf")
    print(f"  2. cd {lecture_path} && just claude")

    return lecture_path


def create_minimal_notebook(path: Path, title: str, notebook_type: str) -> None:
    """Create a minimal Jupyter notebook."""
    if notebook_type == "study":
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# {title}\n", "\n", "## Learning Objectives\n", "\n", "- [ ] Objective 1\n", "- [ ] Objective 2\n"]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["#|default_exp study"],
                "execution_count": None,
                "outputs": []
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## Key Concepts\n", "\n", "*Transcribe lecture content here...*"]
            }
        ]
    else:  # practice
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# Practice: {title}\n", "\n", "Work through these exercises to reinforce your understanding."]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["#|default_exp practice"],
                "execution_count": None,
                "outputs": []
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## Conceptual Questions\n", "\n", "### Question 1\n", "\n", "*Question text here...*"]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## Coding Exercises\n", "\n", "### Exercise 1\n", "\n", "*Instructions here...*"]
            },
            {
                "cell_type": "code",
                "metadata": {},
                "source": ["# Your solution here\n", "pass"],
                "execution_count": None,
                "outputs": []
            }
        ]

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    with open(path, "w") as f:
        json.dump(notebook, f, indent=1)


def create_snakefile(lecture_path: Path, folder_name: str) -> None:
    """Create a Snakefile for the lecture."""
    snakefile_content = f'''# Snakefile for {folder_name}

rule all:
    input:
        "study.pdf",
        "practice.pdf"

rule render_study:
    input:
        "study.ipynb"
    output:
        "study.pdf"
    shell:
        "uv run python ../../.zetteldev/render_notebook.py {{input}} {{output}}"

rule render_practice:
    input:
        "practice.ipynb"
    output:
        "practice.pdf"
    shell:
        "uv run python ../../.zetteldev/render_notebook.py {{input}} {{output}}"
'''
    (lecture_path / "Snakefile").write_text(snakefile_content)


def main():
    if len(sys.argv) > 1:
        name = " ".join(sys.argv[1:])
    elif questionary:
        name = questionary.text("Lecture name:").ask()
        if not name:
            print("Cancelled.")
            sys.exit(0)
    else:
        name = input("Lecture name: ").strip()
        if not name:
            print("Cancelled.")
            sys.exit(0)

    create_lecture(name)


if __name__ == "__main__":
    main()
