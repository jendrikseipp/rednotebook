import subprocess
import sys
from pathlib import Path


def test_generate_help_script():
    script = Path(__file__).resolve().parents[1] / "dev" / "generate-help.py"
    html = subprocess.check_output([sys.executable, str(script)], text=True)
    assert "<!DOCTYPE html>" in html
    assert "RedNotebook Documentation" in html
    assert 'href="#format"' in html
