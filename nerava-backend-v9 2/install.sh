#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
echo "✅ Venv ready. To run: source .venv/bin/activate && bash run.sh"
