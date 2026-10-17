"""Packs everything for the defence into dist/exam-planner-submission.zip.

Run from the project folder: python3 docs/build/build_submission.py
Contains: code, tests, examples, sample data (data/), presentation, report, speech, screenshots.
Skipped: .venv, .git, caches, the author's real data, build scripts of the documents.
"""
import shutil
import sys
import tempfile
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from demo import sample_planner  # noqa: E402
from planner.storage import Storage  # noqa: E402

CODE = ["planner", "ui", "tests", "examples"]
FILES = ["main.py", "demo.py", "screenshots.py", "README.md", "pytest.ini", "requirements-dev.txt"]
DOCS = ["Презентация_Планировщик_экзаменов.pptx", "Отчёт_Планировщик_экзаменов.docx", "Речь_для_выступления.md"]


def main():
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    target = dist / "exam-planner-submission.zip"
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "exam-planner"
        for name in CODE:
            shutil.copytree(ROOT / name, stage / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in FILES:
            shutil.copy2(ROOT / name, stage / name)
        Storage(stage / "data").save(sample_planner(date.today()))  # sample data file for the demo
        docs = stage / "docs"
        docs.mkdir()
        for name in DOCS:
            if (ROOT / "docs" / name).exists():
                shutil.copy2(ROOT / "docs" / name, docs / name)
        if (ROOT / "docs" / "screens").exists():
            shutil.copytree(ROOT / "docs" / "screens", docs / "screens")
        shutil.copy2(ROOT / "docs" / "io_examples.txt", docs / "io_examples.txt")
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    archive.write(path, Path("exam-planner") / path.relative_to(stage))
    print("written", target)


if __name__ == "__main__":
    main()
