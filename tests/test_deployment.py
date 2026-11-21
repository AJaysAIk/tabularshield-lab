"""Exercise the configured Vercel import in a copy without the editable source tree."""

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def test_vercel_entrypoint_and_public_assets_work_outside_checkout(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for path in ["src/tabularshield", "data/processed"]:
        shutil.copytree(root / path, tmp_path / path, ignore=shutil.ignore_patterns("__pycache__"))
    for path in ["data/manifest.json", "reports/report.html", "pyproject.toml"]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / path, target)
    entrypoint = tomllib.loads((tmp_path / "pyproject.toml").read_text())["tool"]["vercel"][
        "entrypoint"
    ]
    environment = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    script = """
import importlib
import sys
from pathlib import Path
from fastapi.testclient import TestClient

module, variable = sys.argv[1].split(':')
loaded = importlib.import_module(module)
assert loaded.ROOT == Path.cwd(), 'Assets resolved outside deployment copy'
client = TestClient(getattr(loaded, variable))
assert client.get('/health').json()['status'] == 'ok'
page = client.get('/')
assert page.status_code == 200
assert page.headers['content-type'].startswith('text/html')
assert 'TabularShield' in page.text and 'data:image/png;base64,' in page.text
assert client.get('/docs').status_code == 200
assert len(client.get('/datasets').json()) == 3
for name, measure, dimensions in [
    ('wholesale', 'Fresh', ['Region', 'Channel']),
    ('abalone', 'Whole_weight', ['Sex']),
    ('geonames_gb', 'population', ['admin1']),
]:
    response = client.post('/query', json={'dataset':name,'measure':measure,'group_by':dimensions})
    assert response.status_code == 200, response.text
    assert response.json()['cells']
print('Configured app, homepage, docs, health and three public datasets verified')
"""
    result = subprocess.run(
        [sys.executable, "-c", script, entrypoint],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=40,
    )
    assert result.returncode == 0, result.stdout + result.stderr
