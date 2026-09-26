"""Compile exported local attachments and inspect their PDF destinations."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from rednotebook.util.markup import convert


@pytest.fixture(scope="module")
def pdflatex():
    pdflatex = shutil.which("pdflatex")
    kpsewhich = shutil.which("kpsewhich")
    if pdflatex is None or kpsewhich is None:
        pytest.skip("A TeX installation is required to verify exported LaTeX")
    for package in ("graphicx.sty", "xcolor.sty", "ulem.sty", "hyperref.sty"):
        result = subprocess.run([kpsewhich, package], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            pytest.skip(f"The LaTeX package {package} is unavailable")
    return pdflatex


@pytest.fixture
def compile_pdf(tmp_path, pdflatex):
    def compile_pdf(source):
        document = convert(source, "tex", tmp_path)
        # Leave PDF objects readable so launch destinations can be checked.
        document = "\\pdfcompresslevel=0\\pdfobjcompresslevel=0\n" + document
        (tmp_path / "export.tex").write_text(document, encoding="utf-8")
        result = subprocess.run(
            [
                pdflatex,
                "-no-shell-escape",
                "-interaction=nonstopmode",
                "-halt-on-error",
                "export.tex",
            ],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout
        return (tmp_path / "export.pdf").read_bytes()

    return compile_pdf


@pytest.mark.parametrize(
    "filename", ["100%photo.png", "hash#photo.png", "brace{photo.png", "brace}photo.png"]
)
def test_image_paths_compile(tmp_path, compile_pdf, filename):
    image = tmp_path / filename
    shutil.copyfile(Path(__file__).parents[1] / "rednotebook/images/picture.png", image)
    compile_pdf(f"![photo]({image.as_uri()}?50)")


@pytest.mark.parametrize(
    "filename",
    [
        "100%notes.txt",
        "hash#notes.txt",
        "brace{notes.txt",
        "brace}notes.txt",
        pytest.param(
            "back\\notes.txt",
            marks=pytest.mark.skipif(os.name == "nt", reason="Backslashes separate Windows paths"),
        ),
    ],
)
def test_local_links_preserve_pdf_launch_destinations(tmp_path, compile_pdf, filename):
    attachment = tmp_path / filename
    attachment.touch()
    pdf = compile_pdf(f"[notes]({attachment.as_uri()})")
    expected = attachment.as_posix().encode().replace(b"\\", b"\\\\")
    assert b"/F(" + expected + b")" in pdf
